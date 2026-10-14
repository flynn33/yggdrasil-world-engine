"""Qualified local fixtures exercise origin admission; no remote trust is claimed."""

import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from core.narrative_engine.origin_progression import OriginProgressionStore
from core.state_journal import CommitJournal, JournalError, _object_bytes


ROOT = Path(__file__).resolve().parents[1]


def document(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def provenance():
    return {"cosmic_pattern_snapshot_ref": "snapshot:origin", "diagnostic_ref": "diagnostic:origin",
            "generation_plan_ref": "plan:origin", "source_ash_refs": ["ash:canonical"]}


def evidence(name, prior="mortal_unknowing", target="first_stirrings", count=2, operation="advance"):
    actions, memories = [], []
    for index in range(count):
        action_id = name + ":action:" + str(index)
        actions.append({"schema_id": "ywe.player_action_trace.v1", "schema_version": "0.1.0",
            "action_trace_id": action_id, "player_id": "player:one", "action_kind": "choice",
            "significance": "meaningful", "branch_relevance": "contextual", "branch_ref": "branch:one",
            "source_refs": ["qualified:action"]})
        memories.append({"schema_id": "ywe.player_memory_record.v1", "schema_version": "0.1.0",
            "memory_id": name + ":memory:" + str(index), "memory_kind": "identity_memory",
            "visibility_state": "felt", "source_action_trace_ref": action_id, "branch_ref": "branch:one",
            "source_refs": ["qualified:memory"]})
    return {"evidence_ref": name, "world_id": "world:one", "player_id": "player:one",
        "operation": operation, "prior_phase": prior, "target_phase": target,
        "actions": actions, "memories": memories, "provenance": provenance()}


def configuration(sources=None):
    profile = document("data/profiles/wrw_origin_progression.json")["profile"]
    creation = {"mortal_identity_ref": "identity:mortal", "identity_status": "veiled", "provenance": provenance()}
    return ["world:one", "player:one", profile, creation,
            {"narrative:owner": ["advance", "remember"], "memory:owner": ["remember"]},
            [evidence("first")] if sources is None else sources,
            document("data/schemas/player_action_trace_schema.json"),
            document("data/schemas/player_memory_record_schema.json")]


class OriginProgressionTests(unittest.TestCase):
    def assert_code(self, code, function, *args):
        with self.assertRaises(JournalError) as raised:
            function(*args)
        self.assertEqual(code, raised.exception.code)

    def publish(self, owner, source="first", request="request:one", revision=0, principal="narrative:owner"):
        return owner.publish(owner.writer(principal), request, revision, source)

    def test_creation_is_veiled_and_cannot_supply_advanced_state(self):
        args = configuration()
        owner = OriginProgressionStore(*args)
        self.assertEqual("mortal_unknowing", owner.state()["current_phase"])
        self.assertEqual("veiled", owner.state()["creation"]["identity_status"])
        self.assertEqual([], owner.state()["memories"])
        for key, value in (("identity_status", "integrated"), ("current_phase", "world_actor")):
            with self.subTest(key=key):
                bad = copy.deepcopy(args)
                bad[3][key] = value
                self.assert_code("INVALID_POLICY", OriginProgressionStore, *bad)

    def test_all_profile_phases_retain_full_actions_memories_and_replay(self):
        args = configuration([])
        for index, edge in enumerate(args[2]["transitions"]):
            args[5].append(evidence("phase:"+str(index), edge["from_phase"], edge["to_phase"], edge["minimum_actions"]))
        owner = OriginProgressionStore(*args)
        for index, source in enumerate(args[5]):
            self.publish(owner, source["evidence_ref"], "request:"+str(index), index)
            self.assertEqual(source["target_phase"], owner.state()["current_phase"])
        self.assertEqual(6, len(owner.state()["memories"]))
        self.assertEqual([row for item in args[5] for row in item["actions"]], owner.state()["actions"])
        raw, head = owner.checkpoint()
        replay = OriginProgressionStore.load(raw, head, *args)
        self.assertEqual(owner.state(), replay.state())
        self.assertEqual((raw, head), replay.checkpoint())

    def test_remember_does_not_advance_and_retains_full_optional_fields(self):
        source = evidence("remember", target="mortal_unknowing", count=1, operation="remember")
        source["memories"][0]["cosmological_tags"] = ["unresolved", "choice"]
        owner = OriginProgressionStore(*configuration([source]))
        self.publish(owner, "remember", principal="memory:owner")
        self.assertEqual("mortal_unknowing", owner.state()["current_phase"])
        self.assertEqual(source["memories"], owner.state()["memories"])
        self.assertEqual([], owner.state()["advances"])

    def test_handle_identity_and_grants_are_required(self):
        owner = OriginProgressionStore(*configuration())
        other = OriginProgressionStore(*configuration())
        handle = owner.writer("narrative:owner")
        for bad in (object(), "narrative:owner", {"principal": "narrative:owner"},
                    copy.copy(handle), other.writer("narrative:owner"), owner.writer("memory:owner")):
            self.assert_code("UNAUTHORIZED_WRITER", owner.publish, bad, "request:one", 0, "first")
        self.assert_code("UNAUTHORIZED_WRITER", owner.writer, "host:adapter")
        self.assertEqual(1, self.publish(owner).revision)

    def test_retry_returns_original_receipt_before_stale_phase_check(self):
        args = configuration()
        owner = OriginProgressionStore(*args)
        receipt = self.publish(owner)
        self.assertEqual(receipt, self.publish(owner, revision=0))
        replay = OriginProgressionStore.load(*owner.checkpoint(), *args)
        self.assertEqual(receipt, self.publish(replay))
        self.assertEqual(2, len(replay.state()["memories"]))

    def test_changed_request_identity_and_stale_new_request_do_not_mutate(self):
        owner = OriginProgressionStore(*configuration([evidence("first"), evidence("other")]))
        self.publish(owner)
        before = owner.checkpoint()
        with self.assertRaises(JournalError):
            self.publish(owner, "other")
        with self.assertRaises(JournalError):
            self.publish(owner, "other", "request:two", 0)
        self.assertEqual(before, owner.checkpoint())

    def test_failed_transition_does_not_reserve_identity(self):
        owner = OriginProgressionStore(*configuration([evidence("skip", target="world_actor"), evidence("first")]))
        before = owner.checkpoint()
        self.assert_code("POLICY_REJECTED", self.publish, owner, "skip")
        self.assertEqual(before, owner.checkpoint())
        self.assertEqual(1, self.publish(owner).revision)

    def test_concurrent_advances_commit_once(self):
        owner = OriginProgressionStore(*configuration([evidence("first"), evidence("other")]))
        def attempt(source):
            try:
                return self.publish(owner, source, "request:"+source)
            except JournalError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, ["first", "other"]))
        self.assertEqual(1, sum(type(item) is not str for item in results))
        self.assertEqual(1, len(owner.state()["advances"]))
        self.assertEqual(2, len(owner.state()["memories"]))

    def test_no_insufficient_repeated_actions_or_phase_skips(self):
        for source in (evidence("few", count=1), evidence("skip", target="chosen_becoming"),
                       evidence("wrong", prior="memory_recovery"),
                       evidence("remember", operation="remember")):
            with self.subTest(source=source["evidence_ref"]):
                owner = OriginProgressionStore(*configuration([source]))
                self.assert_code("POLICY_REJECTED", self.publish, owner, source["evidence_ref"])
                self.assertEqual([], owner.state()["memories"])

    def test_action_cannot_advance_twice_even_with_new_memory(self):
        first = evidence("first")
        second = evidence("second", "first_stirrings", "memory_recovery", 1)
        second["actions"][0] = copy.deepcopy(first["actions"][0])
        second["memories"][0]["source_action_trace_ref"] = first["actions"][0]["action_trace_id"]
        owner = OriginProgressionStore(*configuration([first, second]))
        self.publish(owner)
        before = owner.checkpoint()
        self.assert_code("POLICY_REJECTED", self.publish, owner, "second", "request:two", 1)
        self.assertEqual(before, owner.checkpoint())

    def test_memory_identity_cannot_be_replaced_or_repeated(self):
        first = evidence("remember", target="mortal_unknowing", count=1, operation="remember")
        again = copy.deepcopy(first)
        again["evidence_ref"] = "again"
        for changed in (False, True):
            if changed:
                again["memories"][0]["visibility_state"] = "known_to_player"
            owner = OriginProgressionStore(*configuration([first, again]))
            self.publish(owner, "remember")
            before = owner.checkpoint()
            self.assert_code("POLICY_REJECTED", self.publish, owner, "again", "request:two", 1)
            self.assertEqual(before, owner.checkpoint())

    def test_known_action_identity_cannot_change_content(self):
        first = evidence("remember", target="mortal_unknowing", count=1, operation="remember")
        second = copy.deepcopy(first)
        second["evidence_ref"] = "changed"
        second["actions"][0]["action_kind"] = "oath_made"
        second["memories"][0]["memory_id"] = "memory:new"
        owner = OriginProgressionStore(*configuration([first, second]))
        self.publish(owner, "remember")
        self.assert_code("POLICY_REJECTED", self.publish, owner, "changed", "request:two", 1)

    def test_unknown_evidence_does_not_reserve_identity(self):
        owner = OriginProgressionStore(*configuration())
        self.assert_code("UNKNOWN_EVIDENCE", self.publish, owner, "unknown")
        self.assertEqual(1, self.publish(owner).revision)

    def test_catalog_rejects_cross_scope_minor_actions_and_broken_links(self):
        mutations = [lambda x: x.update(world_id="world:other"), lambda x: x.update(player_id="player:other"),
            lambda x: x["actions"][0].update(player_id="player:other"),
            lambda x: x["actions"][0].update(significance="minor_record"),
            lambda x: x["actions"][0].update(source_refs=[]),
            lambda x: x["actions"][0].update(schema_version="2.0.0"),
            lambda x: x["memories"][0].update(source_action_trace_ref="missing"),
            lambda x: x["memories"][0].update(branch_ref="branch:other"),
            lambda x: x["memories"][0].update(source_refs=[]),
            lambda x: x["memories"].pop(),
            lambda x: x["actions"].append(copy.deepcopy(x["actions"][0])),
            lambda x: x["memories"].append(copy.deepcopy(x["memories"][0])),
            lambda x: x["provenance"].pop("diagnostic_ref"),
            lambda x: x.update(acceptance_status="accepted"),
            lambda x: x["actions"][0].update(unknown=True)]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                source = evidence("first")
                mutate(source)
                self.assert_code("INVALID_POLICY", OriginProgressionStore, *configuration([source]))

    def test_constructor_and_result_aliases_cannot_change_policy_or_state(self):
        args = configuration()
        owner = OriginProgressionStore(*args)
        args[2]["transitions"][0]["minimum_actions"] = 16
        args[3]["identity_status"] = "integrated"
        args[4]["narrative:owner"].clear()
        args[5][0]["memories"][0]["visibility_state"] = "mythologized"
        self.publish(owner)
        state = owner.state()
        state["memories"][0]["visibility_state"] = "public_in_branch"
        self.assertEqual("felt", owner.state()["memories"][0]["visibility_state"])

    def test_changed_or_missing_historical_catalog_refuses_replay_extension_accepts(self):
        args = configuration()
        owner = OriginProgressionStore(*args)
        self.publish(owner)
        for sources in ([], [evidence("different")], [evidence("first", count=1)]):
            bad = configuration(sources)
            with self.assertRaises(JournalError):
                OriginProgressionStore.load(*owner.checkpoint(), *bad)
        args[5].append(evidence("future", "first_stirrings", "memory_recovery", 1))
        loaded = OriginProgressionStore.load(*owner.checkpoint(), *args)
        self.publish(loaded, "future", "request:two", 1)
        self.assertEqual("memory_recovery", loaded.state()["current_phase"])

    def test_policy_scope_schema_and_creation_changes_refuse_replay(self):
        args = configuration()
        owner = OriginProgressionStore(*args)
        self.publish(owner)
        changes = [lambda x: x[2].update(profile_id="profile:other"),
            lambda x: x[3].update(mortal_identity_ref="identity:other"),
            lambda x: x[4].update({"narrative:owner": ["remember"]}),
            lambda x: x[6].update(title="Changed schema"), lambda x: x.__setitem__(0,"world:other")]
        for change in changes:
            bad = copy.deepcopy(args)
            change(bad)
            with self.assertRaises(JournalError):
                OriginProgressionStore.load(*owner.checkpoint(), *bad)

    def test_standalone_schemas_only_and_invalid_policy_bounds(self):
        changes = [lambda x: x[6].update({"$ref": "https://untrusted.invalid/schema"}),
            lambda x: x[7].update({"$dynamicRef": "#node"}),
            lambda x: x[6].update({"$id": "wrong"}),
            lambda x: x[2]["transitions"][0].update(minimum_actions=True),
            lambda x: x[2]["transitions"].append(x[2]["transitions"][0]),
            lambda x: x[2]["phases"].append(x[2]["phases"][0]),
            lambda x: x[4].update({"extra": ["world_write"]}),
            lambda x: x.__setitem__(5, [evidence("first")]*129),
            lambda x: x[5].append(x[5][0])]
        for index, change in enumerate(changes):
            with self.subTest(change=index):
                bad = configuration()
                change(bad)
                self.assert_code("INVALID_POLICY", OriginProgressionStore, *bad)

    def test_neutral_owner_accepts_non_wrw_profile_and_checks_configured_edges(self):
        args = configuration([evidence("custom", "begin", "end", 1)])
        args[2] = {"profile_id": "other:profile", "initial_phase": "begin", "phases": ["begin", "end"],
                   "transitions": [{"from_phase": "begin", "to_phase": "end", "minimum_actions": 1}]}
        owner = OriginProgressionStore(*args)
        self.publish(owner, "custom")
        self.assertEqual("end", owner.state()["current_phase"])

    def test_state_byte_limit_is_atomic_and_preserves_retry_identity(self):
        first = evidence("one", target="mortal_unknowing", count=1, operation="remember")
        second = evidence("two", target="mortal_unknowing", count=1, operation="remember")
        for item in (first, second):
            item["memories"][0]["cosmological_tags"] = ["x"*34000]
            self.assertLess(len(_object_bytes(item)), 65536)
        owner = OriginProgressionStore(*configuration([first, second, evidence("first")]))
        self.publish(owner, "one")
        before = owner.checkpoint()
        with self.assertRaises(JournalError):
            self.publish(owner, "two", "request:two", 1)
        self.assertEqual(before, owner.checkpoint())
        self.assertEqual(2, self.publish(owner, "first", "request:two", 1).revision)

    def test_forged_final_state_and_wrong_trusted_head_refuse_load(self):
        args = configuration()
        owner = OriginProgressionStore(*args)
        empty_head = owner.checkpoint()[1]
        self.publish(owner)
        raw, head = owner.checkpoint()
        with self.assertRaises(JournalError):
            OriginProgressionStore.load(raw, empty_head, *args)
        altered = raw.replace(b'first_stirrings', b'world_actor')
        with self.assertRaises(JournalError):
            OriginProgressionStore.load(altered, head, *args)

    def test_memory_capacity_refusal_is_atomic_and_exact_retry_still_works(self):
        sources = []
        action = evidence("shared", count=1)["actions"][0]
        for index in range(9):
            item = evidence("memory:"+str(index), target="mortal_unknowing", count=1, operation="remember")
            item["actions"] = [copy.deepcopy(action)]
            base = item["memories"][0]
            item["memories"] = [{**base, "memory_id": "memory:"+str(index)+":"+str(n),
                "source_action_trace_ref": action["action_trace_id"]} for n in range(16)]
            sources.append(item)
        args = configuration(sources)
        owner = OriginProgressionStore(*args)
        for index in range(8):
            receipt = self.publish(owner, "memory:"+str(index), "request:"+str(index), index)
        self.assertEqual(128, len(owner.state()["memories"]))
        before = owner.checkpoint()
        with self.assertRaises(JournalError):
            self.publish(owner, "memory:8", "request:8", 8)
        self.assertEqual(before, owner.checkpoint())
        self.assert_code("IDENTITY_CONFLICT", self.publish, owner, "memory:7", "request:7", 0)
        self.assertEqual(receipt, self.publish(owner, "memory:7", "request:7", 7))
        self.assertEqual(owner.state(), OriginProgressionStore.load(*before, *args).state())

    def test_catalog_total_capacity_and_bundle_limits(self):
        sources = []
        for index in range(33):
            item = evidence("large:"+str(index), count=1)
            item["memories"][0]["cosmological_tags"] = ["x"*33000]
            self.assertLess(len(_object_bytes(item)), 65536)
            sources.append(item)
        self.assertGreater(sum(len(_object_bytes(item)) for item in sources), 1048576)
        self.assert_code("INVALID_POLICY", OriginProgressionStore, *configuration(sources))
        self.assert_code("INVALID_POLICY", OriginProgressionStore, *configuration([evidence("many", count=17)]))

    def test_replay_rejects_alternate_genesis_request_identity_and_compensation(self):
        sources = [evidence(name, target="mortal_unknowing", count=1, operation="remember") for name in ("one", "two")]
        args = configuration(sources)
        owner = OriginProgressionStore(*args)
        # A trusted-head match still does not waive this owner's genesis contract.
        altered = {**owner._initial, "current_phase": "world_actor"}
        journal = CommitJournal(owner._scope, owner._policy_id, altered, owner._reduce)
        self.assert_code("INVALID_ARCHIVE", OriginProgressionStore.load, *journal.checkpoint(), *args)
        journal = CommitJournal(owner._scope, owner._policy_id, owner._initial, owner._reduce)
        journal.commit("wrong:request", 0, owner._packet("narrative:owner", "packet:request", "one"))
        self.assert_code("INVALID_ARCHIVE", OriginProgressionStore.load, *journal.checkpoint(), *args)
        journal = CommitJournal(owner._scope, owner._policy_id, owner._initial, owner._reduce)
        journal.commit("one", 0, owner._packet("narrative:owner", "one", "one"))
        journal.commit("two", 1, owner._packet("narrative:owner", "two", "two"), compensates="one")
        self.assert_code("INVALID_ARCHIVE", OriginProgressionStore.load, *journal.checkpoint(), *args)

    def test_checked_in_state_and_profile_validate_and_match_executed_example(self):
        schemas = [document("data/schemas/"+name+"_schema.json") for name in
                   ("m4_origin_state", "m4_origin_profile", "player_action_trace", "player_memory_record")]
        registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas)
        state = document("examples/state_journal/origin_progression.example.json")
        owner = OriginProgressionStore(*configuration())
        self.publish(owner)
        self.assertEqual(owner.state(), state)
        for schema, instance in ((schemas[0],state),(schemas[1],document("data/profiles/wrw_origin_progression.json"))):
            Draft202012Validator(schema, registry=registry).validate(instance)
            bad = {**instance, "unreviewed": True}
            self.assertFalse(Draft202012Validator(schema, registry=registry).is_valid(bad))


if __name__ == "__main__":
    unittest.main()
