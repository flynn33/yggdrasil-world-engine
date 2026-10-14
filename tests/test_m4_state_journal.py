from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
from pathlib import Path
import threading
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from core.state_journal import CommitJournal, JournalError, TruthScope, MAX_ENTRIES


def reduce_counter(scope, state, packet):
    """Synthetic owner for journal mechanics, not a player progression adapter."""
    if set(packet) != {"add"} or type(packet["add"]) is not int or abs(packet["add"]) > 10:
        raise ValueError("owner rejected")
    return {"count": state["count"] + packet["add"]}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


class CommitJournalTests(unittest.TestCase):
    def setUp(self):
        self.scope = TruthScope("world.one", "player_state", "player.one")
        self.journal = CommitJournal(self.scope, "test.counter.v1", {"count": 0}, reduce_counter)

    def assert_code(self, code, action):
        with self.assertRaises(JournalError) as caught:
            action()
        self.assertEqual(code, caught.exception.code)

    def load(self, raw=None, **changes):
        args = dict(raw=self.journal.save() if raw is None else raw, scope=self.scope,
                    policy_id="test.counter.v1", reducer=reduce_counter, trusted_head=self.journal.head())
        args.update(changes)
        return CommitJournal.load(**args)

    def test_empty_and_populated_archives_round_trip_exactly(self):
        self.assertEqual(self.journal.save(), self.load().save())
        for i, amount in enumerate((3, -1, 5)):
            self.journal.commit(f"request.{i}", i, {"add": amount})
        restored = self.load()
        self.assertEqual({"count": 7}, restored.state())
        self.assertEqual(self.journal.save(), restored.save())
        self.assertEqual(self.journal.head(), restored.head())

    def test_independent_hash_reconstruction_binds_entire_header_and_entry(self):
        receipt = self.journal.commit("request.one", 0, {"add": 3})
        archive = json.loads(self.journal.save())
        header = {key: archive[key] for key in ("format", "scope", "policy_id", "initial_state")}
        entry = archive["entries"][0]
        self.assertEqual(hashlib.sha256(canonical(header)).hexdigest(), entry["previous_digest"])
        body = {key: value for key, value in entry.items() if key != "entry_digest"}
        self.assertEqual(hashlib.sha256(canonical(body)).hexdigest(), receipt.entry_digest)
        self.assertEqual(hashlib.sha256(b'{"count":0}').hexdigest(), entry["before_state_digest"])
        self.assertEqual(hashlib.sha256(b'{"count":3}').hexdigest(), receipt.state_digest)

    def test_retry_returns_original_receipt_without_reducing_again(self):
        calls = []
        def owner(scope, state, packet):
            calls.append(packet)
            return reduce_counter(scope, state, packet)
        journal = CommitJournal(self.scope, "test.counter.v1", {"count": 0}, owner)
        first = journal.commit("request.one", 0, {"add": 2})
        journal.commit("request.two", 1, {"add": 3})
        self.assertIs(first, journal.commit("request.one", 0, {"add": 2}))
        self.assertEqual(2, len(calls))
        before = journal.save()
        for expected, packet, target in ((1, {"add": 2}, None), (0, {"add": 1}, None),
                                         (0, {"add": 2}, "request.two")):
            self.assert_code("IDENTITY_CONFLICT", lambda: journal.commit("request.one", expected, packet, target))
        self.assertEqual(before, journal.save())

    def test_restored_retry_does_not_repeat_consequences(self):
        first = self.journal.commit("request.one", 0, {"add": 4})
        calls = []
        def owner(scope, state, packet):
            calls.append(1)
            return reduce_counter(scope, state, packet)
        restored = self.load(reducer=owner)
        self.assertEqual(1, len(calls))
        self.assertEqual(first, restored.commit("request.one", 0, {"add": 4}))
        self.assertEqual(1, len(calls))
        self.assertEqual({"count": 4}, restored.state())

    def test_rejection_is_atomic_and_does_not_reserve_identity(self):
        before = self.journal.save()
        self.assert_code("POLICY_REJECTED", lambda: self.journal.commit("request.one", 0, {"add": 11}))
        self.assertEqual(before, self.journal.save())
        self.assertEqual(1, self.journal.commit("request.one", 0, {"add": 1}).revision)
        committed = self.journal.save()
        self.assert_code("REVISION_CONFLICT", lambda: self.journal.commit("request.two", 0, {"add": 2}))
        self.assertEqual(committed, self.journal.save())
        self.journal.commit("request.two", 1, {"add": 2})

    def test_packet_acceptance_label_cannot_bypass_the_owner(self):
        before = self.journal.save()
        self.assert_code("POLICY_REJECTED", lambda: self.journal.commit(
            "request.one", 0, {"add": 1, "acceptance_status": "accepted"}))
        self.assertEqual(before, self.journal.save())

    def test_mutating_then_throwing_owner_cannot_change_committed_state(self):
        def owner(scope, state, packet):
            state["count"] = 999
            packet["secret"] = "not retained"
            raise RuntimeError("private owner detail")
        journal = CommitJournal(self.scope, "test.failure.v1", {"count": 0}, owner)
        before = journal.save()
        with self.assertRaises(JournalError) as caught:
            journal.commit("r1", 0, {"add": 1})
        self.assertEqual("POLICY_REJECTED", str(caught.exception))
        self.assertEqual(before, journal.save())

    def test_input_output_and_owner_aliases_are_detached(self):
        initial = {"items": [1]}
        returned = {"items": [2]}
        journal = CommitJournal(self.scope, "test.alias.v1", initial, lambda *args: returned)
        initial["items"].append(99)
        self.assertEqual({"items": [1]}, journal.state())
        packet = {"items": [3]}
        journal.commit("r1", 0, packet)
        packet["items"].append(4)
        returned["items"].append(5)
        observed = journal.state()
        observed["items"].append(6)
        self.assertEqual({"items": [2]}, journal.state())
        self.assertEqual({"items": [3]}, json.loads(journal.save())["entries"][0]["packet"])

    def test_concurrent_distinct_requests_at_one_revision_have_one_winner(self):
        barrier = threading.Barrier(8)
        def run(index):
            barrier.wait(timeout=5)
            try:
                return self.journal.commit(f"r{index}", 0, {"add": 1}).revision
            except JournalError as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=8) as executor:
            outcomes = list(executor.map(run, range(8)))
        self.assertEqual(1, outcomes.count(1))
        self.assertEqual(7, outcomes.count("REVISION_CONFLICT"))
        self.assertEqual({"count": 1}, self.journal.state())

    def test_concurrent_identical_delivery_commits_once(self):
        with ThreadPoolExecutor(max_workers=8) as executor:
            receipts = list(executor.map(lambda _: self.journal.commit("r1", 0, {"add": 2}), range(32)))
        self.assertTrue(all(receipt == receipts[0] for receipt in receipts))
        self.assertEqual(1, len(json.loads(self.journal.save())["entries"]))
        self.assertEqual({"count": 2}, self.journal.state())

    def test_compensation_appends_without_erasing_history(self):
        self.journal.commit("r1", 0, {"add": 3})
        original = json.loads(self.journal.save())["entries"][0]
        self.assert_code("UNKNOWN_COMPENSATION", lambda: self.journal.commit("r2", 1, {"add": -3}, "missing"))
        self.journal.commit("r2", 1, {"add": -3}, "r1")
        archive = json.loads(self.journal.save())
        self.assertEqual(original, archive["entries"][0])
        self.assertEqual("r1", archive["entries"][1]["compensates"])
        self.assertEqual({"count": 0}, self.load().state())

    def test_reentrant_access_rejects_even_if_reducer_swallows_error(self):
        for operation in (lambda j: j.state(), lambda j: j.save(), lambda j: j.head(),
                          lambda j: j.commit("nested", 0, {"add": 1})):
            with self.subTest(operation=operation):
                def owner(scope, state, packet):
                    try:
                        operation(journal)
                    except JournalError:
                        pass
                    return {"count": 100}
                journal = CommitJournal(self.scope, "test.reentry.v1", {"count": 0}, owner)
                before = journal.save()
                self.assert_code("POLICY_REJECTED", lambda: journal.commit("r1", 0, {}))
                self.assertEqual(before, journal.save())

    def test_capacity_rejects_new_commit_but_retains_retry(self):
        first = self.journal.commit("r0", 0, {"add": 1})
        for index in range(1, MAX_ENTRIES):
            self.journal.commit(f"r{index}", index, {"add": 1})
        before = self.journal.save()
        self.assert_code("CAPACITY_EXCEEDED", lambda: self.journal.commit("extra", MAX_ENTRIES, {"add": 1}))
        self.assertEqual(first, self.journal.commit("r0", 0, {"add": 1}))
        self.assertEqual(before, self.journal.save())
        self.assertEqual(before, self.load().save())

    def test_perception_and_player_scopes_cannot_load_as_shared_truth(self):
        shared = TruthScope("world.one", "shared_worldstate", "world.one")
        for kind in ("player_state", "player_perception", "leaf_branch_state"):
            with self.subTest(kind=kind):
                journal = CommitJournal(TruthScope("world.one", kind, "subject.one"), "test.counter.v1", {"count": 0}, reduce_counter)
                journal.commit("r1", 0, {"add": 3})
                self.assert_code("INVALID_ARCHIVE", lambda: self.load(journal.save(), scope=shared, trusted_head=journal.head()))
        for kind in ("base_world_ontology", "ywe_normative_contract", "host_materialization", "unknown"):
            self.assert_code("INVALID_SCOPE", lambda: TruthScope("world.one", kind, "world.one"))
        self.assert_code("INVALID_SCOPE", lambda: TruthScope("world.one", "shared_worldstate", "player.one"))

    def test_scope_policy_version_and_trusted_head_mismatches_fail(self):
        self.journal.commit("r1", 0, {"add": 1})
        for changes in (dict(scope=TruthScope("world.two", "player_state", "player.one")),
                        dict(scope=TruthScope("world.one", "player_state", "player.two")),
                        dict(policy_id="test.counter.v2"), dict(trusted_head="0" * 64)):
            self.assert_code("INVALID_ARCHIVE", lambda: self.load(**changes))
        archive = json.loads(self.journal.save())
        archive["format"] = "ywe.scoped_commit_journal.v2"
        self.assert_code("INVALID_ARCHIVE", lambda: self.load(canonical(archive)))
        self.assert_code("INVALID_TRUSTED_HEAD", lambda: self.load(trusted_head=None))

    def test_every_entry_field_and_cached_state_is_verified(self):
        self.journal.commit("r1", 0, {"add": 2})
        original = json.loads(self.journal.save())
        changes = {"request_id": "altered", "expected_revision": 1, "packet": {"add": 3},
                   "compensates": "r1", "revision": True, "previous_digest": "0" * 64,
                   "before_state_digest": "0" * 64, "after_state_digest": "0" * 64, "entry_digest": "0" * 64}
        for key, value in changes.items():
            with self.subTest(field=key):
                damaged = copy.deepcopy(original)
                damaged["entries"][0][key] = value
                self.assert_code("INVALID_ARCHIVE", lambda: self.load(canonical(damaged)))
        for key in ("initial_state", "final_state"):
            damaged = copy.deepcopy(original)
            damaged[key] = {"count": 9}
            self.assert_code("INVALID_ARCHIVE", lambda: self.load(canonical(damaged)))

    def test_reordering_omission_duplicate_and_unknown_fields_fail(self):
        self.journal.commit("r1", 0, {"add": 1})
        self.journal.commit("r2", 1, {"add": 2})
        original = json.loads(self.journal.save())
        for entries in (original["entries"][::-1], original["entries"][:1], [],
                        original["entries"] + [original["entries"][-1]]):
            damaged = copy.deepcopy(original)
            damaged["entries"] = entries
            self.assert_code("INVALID_ARCHIVE", lambda: self.load(canonical(damaged)))
        for target in ("archive", "entry"):
            damaged = copy.deepcopy(original)
            (damaged if target == "archive" else damaged["entries"][0])["unknown"] = True
            self.assert_code("INVALID_ARCHIVE", lambda: self.load(canonical(damaged)))

    def test_changed_reducer_cannot_silently_accept_old_state(self):
        self.journal.commit("r1", 0, {"add": 2})
        self.assert_code("INVALID_ARCHIVE", lambda: self.load(reducer=lambda *args: {"count": 3}))
        self.assertEqual({"count": 2}, self.journal.state())

    def test_raw_decoder_rejects_duplicate_keys_floats_nonfinite_and_oversize(self):
        raw = self.journal.save()
        for damaged in (raw.replace(b'"count":0', b'"count":0,"count":1', 1),
                        raw.replace(b'"count":0', b'"count":0.0', 1),
                        raw.replace(b'"count":0', b'"count":NaN', 1),
                        raw.replace(b'"count":0', b'"count":9007199254740992', 1),
                        raw.replace(b'"count":0', b'"count":"\\ud800"', 1),
                        b'[' * 2000 + b']' * 2000, b' ' * (16 * 1024 * 1024 + 1), b'\xff', raw + b'{}'):
            self.assert_code("INVALID_ARCHIVE", lambda: self.load(damaged))

    def test_invalid_values_and_bounds_reject_before_publication(self):
        class IntLike(int):
            pass
        invalid = ({"n": 1.0}, {"n": float("nan")}, {"n": IntLike(1)}, {"n": 9007199254740992},
                   {1: "key"}, {"s": "\ud800"}, {"n": object()}, {"s": "a" * 65536}, {"a": [0] * 4096})
        before = self.journal.save()
        for packet in invalid:
            with self.subTest(kind=type(next(iter(packet.values())))):
                with self.assertRaises(JournalError):
                    self.journal.commit("r1", 0, packet)
                self.assertEqual(before, self.journal.save())
        for revision in (-1, True, 0.0, MAX_ENTRIES + 1):
            self.assert_code("INVALID_VALUE", lambda: self.journal.commit("r1", revision, {}))
        for identifier in ("", "has space", "é", "x" * 129, "valid\n", None):
            self.assert_code("INVALID_VALUE", lambda: self.journal.commit(identifier, 0, {}))
        nested = {}
        for _ in range(33):
            nested = {"child": nested}
        self.assert_code("VALUE_LIMIT", lambda: self.journal.commit("r1", 0, nested))

    def test_maximum_bytes_integer_and_unicode_are_lossless(self):
        state = {"s": "a" * (65536 - len(b'{"s":""}'))}
        journal = CommitJournal(self.scope, "test.bound.v1", state, lambda scope, state, packet: packet)
        packet = {"min": -9007199254740991, "max": 9007199254740991, "text": "雪😀", "nil": None, "flag": True}
        journal.commit("r1", 0, packet)
        restored = CommitJournal.load(journal.save(), self.scope, "test.bound.v1",
                                      lambda scope, state, packet: packet, journal.head())
        self.assertEqual(packet, restored.state())
        self.assertEqual(journal.save(), restored.save())

    def test_invalid_owner_output_is_atomic(self):
        for returned in (None, [], {"n": 1.5}, {"n": float("inf")}, {"s": "x" * 65536}):
            journal = CommitJournal(self.scope, "test.invalid.v1", {"count": 0}, lambda *args: returned)
            before = journal.save()
            self.assert_code("POLICY_REJECTED", lambda: journal.commit("r1", 0, {}))
            self.assertEqual(before, journal.save())


class CommitJournalSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        def deny(uri):
            raise NoSuchResource(ref=uri)
        registry = Registry(retrieve=deny)
        for name in ("common/identifier.schema.json", "m4_commit_journal_schema.json"):
            schema = json.loads((root / "data/schemas" / name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
        cls.validator = Draft202012Validator(schema, registry=registry)
        cls.fixture = json.loads((root / "examples/state_journal/compensated_archive.example.json").read_text(encoding="utf-8"))

    def test_fixture_structure_and_executed_replay_agree(self):
        self.validator.validate(self.fixture)
        journal = CommitJournal.load(canonical(self.fixture), TruthScope(**self.fixture["scope"]),
                                     self.fixture["policy_id"], reduce_counter,
                                     self.fixture["entries"][-1]["entry_digest"])
        self.assertEqual({"count": 0}, journal.state())
        self.assertEqual(canonical(self.fixture), journal.save())

    def test_closed_shapes_require_all_owned_fields(self):
        for target in ("archive", "scope", "entry"):
            original = self.fixture if target == "archive" else self.fixture["scope"] if target == "scope" else self.fixture["entries"][0]
            for field in [*original, "extra"]:
                with self.subTest(target=target, field=field):
                    damaged = copy.deepcopy(self.fixture)
                    node = damaged if target == "archive" else damaged["scope"] if target == "scope" else damaged["entries"][0]
                    if field == "extra":
                        node[field] = 0
                    else:
                        del node[field]
                    self.assertFalse(self.validator.is_valid(damaged))

    def test_schema_rejects_unknown_scope_numeric_boolean_and_integer_overflow(self):
        for field, value in (("truth_scope", "base_world_ontology"), ("world_id", "has space"),
                             ("subject_id", "x" * 129), ("subject_id", "valid\n")):
            damaged = copy.deepcopy(self.fixture)
            damaged["scope"][field] = value
            self.assertFalse(self.validator.is_valid(damaged))
        for field, value in (("revision", True), ("revision", 0), ("expected_revision", 128),
                             ("packet", {"n": 9007199254740992}), ("entry_digest", "g" * 64)):
            damaged = copy.deepcopy(self.fixture)
            damaged["entries"][0][field] = value
            self.assertFalse(self.validator.is_valid(damaged))

    def test_schema_valid_tampering_still_requires_protocol_validation(self):
        damaged = copy.deepcopy(self.fixture)
        damaged["final_state"]["count"] = 100
        self.validator.validate(damaged)
        with self.assertRaises(JournalError):
            CommitJournal.load(canonical(damaged), TruthScope(**damaged["scope"]), damaged["policy_id"],
                               reduce_counter, self.fixture["entries"][-1]["entry_digest"])


if __name__ == "__main__":
    unittest.main()
