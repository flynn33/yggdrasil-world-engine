"""Atomic set mechanics and actual pure-owner composition, not multiplayer grants."""

import copy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
import hashlib
import itertools
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

from core import commit_set_journal as cs
from core import core_values as cv
from core.perception_engine.persistence import PerceptionPolicy
from core.perception_engine.perception import PerceptionEngine
from core.player_state import PlayerStatePolicy
from core.state_journal import JournalError, TruthScope, _object_bytes
from tests.m4_player_fixture import configuration, WORLD, PRINCIPAL
from tests.test_m3_core_cosmology_realm import pure_model
from tests.test_m4_player_state import add_compensation


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def head(component):
    return {key: value for key, value in component.items() if key != "state"}


def selected(component, request, packet):
    return {key: component[key] for key in ("component_id", "scope", "owner_policy_id")} | {
        "owner_request_ref": request, "packet": packet}


def proposal(identity, selections=(), *, principal="principal", sequence=0, reads=(), predecessors=(), compensations=()):
    return {"principal": principal, "proposal_id": identity, "sequence": sequence,
        "predecessor_refs": list(predecessors), "reads": list(reads),
        "writes": sorted(row["component_id"] for row in selections),
        "components": list(selections), "compensations": list(compensations)}


def round_packet(identity, revision, proposals):
    return cs.canonical_round_packet({"format": "ywe.closed_round.v1", "round_id": identity,
                                      "sequence": revision, "proposals": list(proposals)})


class SyntheticCoordinator:
    """A deliberately small mechanics fixture; no source-authority claim."""

    def __init__(self, owners=None):
        self.owners = owners or {}
        self.views = []
        self.calls = []
        self.fail_component = None

    def __call__(self, binding, state, packet, history):
        self.views.append(history)
        components = {row["component_id"]: row for row in state["components"]}
        decisions, steps = [], []
        for item in packet["proposals"]:
            prior = history.decision(item["principal"], item["proposal_id"])
            decision = {"principal": item["principal"], "proposal_id": item["proposal_id"],
                        "status": "ACCEPTED", "code": "ACCEPTED", "prior_decision": None, "step_indices": []}
            if prior is not None:
                decision.update(status="DUPLICATE", code="DUPLICATE", prior_decision={
                    key: prior[key] for key in ("round_id", "decision_index", "decision_sha256")})
            elif item["principal"] == "denied":
                decision.update(status="REJECTED", code="DENIED")
            else:
                for row in item["components"]:
                    component_id = row["component_id"]
                    self.calls.append((packet["round_id"], component_id, row["owner_request_ref"]))
                    if component_id == self.fail_component:
                        raise ValueError("private owner failure text")
                    previous = components.get(component_id)
                    prior_state = previous["state"] if previous is not None else {"count": 0}
                    if component_id in self.owners:
                        after = self.owners[component_id].reduce(prior_state, row["packet"])
                    else:
                        after = {"count": prior_state["count"] + row["packet"]["add"]}
                    step = {**row, "principal": item["principal"], "proposal_id": item["proposal_id"],
                            "state_after": after, "create": previous is None}
                    components[component_id], _ = cs.advance_component(binding, packet["round_id"], step, previous)
                    decision["step_indices"].append(len(steps))
                    steps.append(step)
            decisions.append(decision)
        state["components"] = [components[key] for key in sorted(components)]
        return {"decisions": decisions, "component_steps": steps, "state": state}


class CommitSetJournalTests(unittest.TestCase):
    def setUp(self):
        self.binding = cs.CommitSetBinding("world", "container")
        # Equal governing scope deliberately exercises the distinct component key.
        scope = TruthScope("world", "leaf_branch_state", "branch")
        self.components = [cs.initial_component(self.binding, name, scope, "counter.v1", {"count": 0})
                           for name in ("a", "b")]
        self.initial = {"format": "ywe.commit_set_state.v1", "world_id": "world", "components": self.components}
        self.reducer = SyntheticCoordinator()
        self.journal = cs.CommitSetJournal(self.binding, "test.coordinator.v1", self.initial, self.reducer)

    def assert_code(self, code, action):
        with self.assertRaises(JournalError) as caught:
            action()
        self.assertEqual(code, caught.exception.code)

    def packet(self, revision=0, identity=None, selections=None):
        identity = identity or "round." + str(revision)
        rows = selections if selections is not None else [selected(row, "request." + str(revision), {"add": 1})
                                                         for row in self.components]
        return round_packet(identity, revision, [proposal("proposal." + str(revision), rows)])

    def load(self, raw=None, **changes):
        arguments = dict(raw=self.journal.save() if raw is None else raw, binding=self.binding,
            policy_id="test.coordinator.v1", initial_state=self.initial, reducer=self.reducer,
            trusted_head=self.journal.head())
        arguments.update(changes)
        return cs.CommitSetJournal.load(**arguments)

    def test_atomic_two_components_and_independent_hash_reconstruction(self):
        packet = self.packet()
        receipt = self.journal.commit("round.0", 0, packet)
        archive = json.loads(self.journal.save())
        entry = archive["entries"][0]
        header = {key: archive[key] for key in ("format", "binding", "policy_id", "initial_state")}
        self.assertEqual(digest(header), entry["previous_digest"])
        self.assertEqual(digest({key: value for key, value in entry.items() if key != "entry_digest"}), receipt.entry_digest)
        self.assertEqual(digest(entry["decisions"]), receipt.decisions_digest)
        self.assertEqual(digest(self.journal.state()), receipt.state_digest)
        for original, trace, current in zip(self.components, entry["component_steps"], self.journal.state()["components"]):
            body = {"format": "ywe.component_step.v1", "binding": self.binding.to_record(),
                **{key: current[key] for key in ("component_id", "scope", "owner_policy_id")},
                "previous_head": original["head_digest"], "revision": 1, "round_id": "round.0",
                "principal": "principal", "proposal_id": "proposal.0", "owner_request_ref": "request.0",
                "packet_sha256": digest({"add": 1}), "before_state_sha256": digest({"count": 0}),
                "after_state_sha256": digest({"count": 1})}
            self.assertEqual(digest(body), current["head_digest"])
            self.assertEqual(head(current), trace["after"])
            self.assertNotIn("state_after", trace)
        self.assertNotEqual(*[row["head_digest"] for row in self.journal.vector()])
        self.assertEqual(self.journal.checkpoint(), self.load().checkpoint())

    def test_exact_round_retry_precedes_stale_and_capacity_and_does_not_call_policy(self):
        packet = self.packet()
        receipt = self.journal.commit("round.0", 0, packet)
        restored = self.load()
        for journal in (self.journal, restored):
            with patch.object(journal, "_reducer", side_effect=AssertionError("must not run")), patch.object(cs, "MAX_ROUNDS", 1):
                self.assertEqual(receipt, journal.commit("round.0", 0, packet))
        changed = copy.deepcopy(packet)
        changed["proposals"][0]["components"][0]["packet"]["add"] = 2
        before = self.journal.checkpoint()
        self.assert_code("IDENTITY_CONFLICT", lambda: self.journal.commit("round.0", 0, changed))
        self.assert_code("REVISION_CONFLICT", lambda: self.journal.commit("round.1", 0, self.packet(0, "round.1")))
        self.assertEqual(before, self.journal.checkpoint())

    def test_duplicate_proposals_and_rejected_originals_preserve_first_decision(self):
        item = proposal("repeat", [selected(self.components[0], "request", {"add": 1})])
        denied = proposal("denied", principal="denied")
        packet = round_packet("one", 0, [item, denied])
        self.journal.commit("one", 0, packet)
        self.journal.commit("two", 1, round_packet("two", 1, [denied, item]))
        self.journal.commit("three", 2, round_packet("three", 2, [item, denied]))
        self.assertEqual(1, len(self.reducer.calls))
        self.assertEqual(["DUPLICATE", "DUPLICATE"], [row["status"] for row in self.journal.decisions("three")])
        self.assertEqual(["one", "one"], [row["prior_decision"]["round_id"] for row in self.journal.decisions("three")])
        changed = copy.deepcopy(item)
        changed["sequence"] = 1
        self.assert_code("IDENTITY_CONFLICT", lambda: self.journal.commit("four", 3, round_packet("four", 3, [changed])))
        self.assertEqual(self.journal.checkpoint(), self.load().checkpoint())

    def test_request_identity_is_component_local_but_not_reusable_by_new_proposal(self):
        self.journal.commit("round.0", 0, self.packet())
        before = self.journal.checkpoint()
        packet = round_packet("other", 1, [proposal("new", [selected(self.components[0], "request.0", {"add": 1})])])
        self.assert_code("IDENTITY_CONFLICT", lambda: self.journal.commit("other", 1, packet))
        self.assertEqual(before, self.journal.checkpoint())

    def test_late_owner_exception_reserves_no_round_proposal_or_request(self):
        self.reducer.fail_component = "b"
        before = self.journal.checkpoint(), self.journal.vector()
        self.assert_code("POLICY_REJECTED", lambda: self.journal.commit("round.0", 0, self.packet()))
        self.assertEqual(before, (self.journal.checkpoint(), self.journal.vector()))
        self.reducer.fail_component = None
        self.journal.commit("round.0", 0, self.packet())
        self.assertEqual([1, 1], [row["state"]["count"] for row in self.journal.state()["components"]])

    def test_trace_cannot_skip_reorder_misattribute_or_change_a_selected_owner(self):
        corruptions = [lambda r: r["component_steps"].pop(),
            lambda r: r["component_steps"].reverse(),
            lambda r: r["component_steps"][0].update(owner_policy_id="other"),
            lambda r: r["component_steps"][0].update(principal="other"),
            lambda r: r["component_steps"][0]["packet"].update(add=2),
            lambda r: r["state"]["components"].pop(),
            lambda r: r["decisions"][0].update(step_indices=[0, 0]),
            lambda r: r["component_steps"][0].update(create=1)]
        for corrupt in corruptions:
            with self.subTest(corruption=corrupt):
                def reducer(*args):
                    result = self.reducer(*args)
                    corrupt(result)
                    return result
                owner = cs.CommitSetJournal(self.binding, "test", self.initial, reducer)
                before = owner.checkpoint()
                self.assert_code("INVALID_REDUCTION", lambda: owner.commit("round.0", 0, self.packet()))
                self.assertEqual(before, owner.checkpoint())

    def test_input_output_helpers_and_history_are_detached_and_frozen(self):
        packet = self.packet()
        original_packet, original_initial = copy.deepcopy(packet), copy.deepcopy(self.initial)
        self.journal.commit("round.0", 0, packet)
        self.assertEqual(original_packet, packet)
        self.assertEqual(original_initial, self.initial)
        first_view = self.reducer.views[0]
        self.assertIsNone(first_view.decision("principal", "proposal.0"))
        self.journal.commit("round.1", 1, self.packet(1))
        view = self.reducer.views[-1]
        exact = head(self.components[0])
        old = view.component_at(exact)
        old["state"]["count"] = 999
        exact["scope"]["subject_id"] = "changed"
        original_head = head(original_initial["components"][0])
        self.assertEqual(0, view.component_at(original_head)["state"]["count"])
        prior = view.decision("principal", "proposal.0")
        prior["decision"]["code"] = "changed"
        self.assertEqual("ACCEPTED", view.decision("principal", "proposal.0")["decision"]["code"])
        request = view.component_request("a", "request.0")
        request["head"]["revision"] = 123
        self.assertEqual(1, view.component_request("a", "request.0")["head"]["revision"])
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            view._world_id = "other"
        with self.assertRaises(TypeError):
            view._requests[("a", "bad")] = b"{}"
        self.assertIsNone(first_view.component_request("a", "request.0"))
        detached = self.journal.state()
        detached["components"].clear()
        self.assertEqual(2, len(self.journal.vector()))

    def test_history_exact_heads_survive_replay_and_reject_changed_qualifiers(self):
        for i in range(3):
            self.journal.commit("round." + str(i), i, self.packet(i))
        restored = self.load()
        restored.commit("round.3", 3, self.packet(3))
        view = self.reducer.views[-1]
        initial_head = head(self.components[0])
        self.assertEqual(0, view.component_at(initial_head)["state"]["count"])
        first = view.component_request("a", "request.0")
        self.assertEqual(1, view.component_at(first["head"])["state"]["count"])
        for field, value in (("owner_policy_id", "other"), ("state_sha256", "0" * 64), ("revision", 2)):
            changed = copy.deepcopy(first["head"])
            changed[field] = value
            self.assert_code("UNKNOWN_COMPONENT_HEAD", lambda: view.component_at(changed))

    def test_creation_preserves_parent_and_capacity_failure_does_not_partial_fork(self):
        branch = cs.initial_component(self.binding, "child", TruthScope("world", "leaf_branch_state", "child"), "counter.v1", {"count": 0})
        packet = self.packet(selections=[selected(branch, "create", {"add": 3})])
        with patch.object(cs, "MAX_COMPONENTS", 2):
            before = self.journal.checkpoint()
            calls = len(self.reducer.calls)
            self.assert_code("CAPACITY_EXCEEDED", lambda: self.journal.commit("round.0", 0, packet))
            self.assertEqual(before, self.journal.checkpoint())
            self.assertEqual(calls, len(self.reducer.calls))
        self.journal.commit("round.0", 0, packet)
        states = self.journal.state()["components"]
        self.assertEqual(["a", "b", "child"], [row["component_id"] for row in states])
        self.assertEqual(1, states[-1]["revision"])
        self.assertIsNone(json.loads(self.journal.save())["entries"][0]["component_steps"][0]["before"])
        self.assertEqual(self.journal.checkpoint(), self.load().checkpoint())

    def test_compensation_map_requires_exact_accepted_component_admission(self):
        self.journal.commit("round.0", 0, self.packet())
        mapping = {"component_id": "a", "component_request_ref": "undo", "target_round_id": "round.0",
            "target_principal": "principal", "target_proposal_id": "proposal.0",
            "target_component_request_ref": "request.0", "target_component_head": self.journal.vector()[0]}
        item = proposal("undo", [selected(self.components[0], "undo", {"add": -1})], compensations=[mapping])
        for field, value in (("target_round_id", "absent"), ("target_component_request_ref", "imported"),
                             ("target_proposal_id", "other"), ("target_component_head", self.journal.vector()[1])):
            altered = copy.deepcopy(item)
            altered["compensations"][0][field] = value
            before = self.journal.checkpoint()
            self.assert_code("UNKNOWN_COMPENSATION", lambda: self.journal.commit("undo", 1, round_packet("undo", 1, [altered])))
            self.assertEqual(before, self.journal.checkpoint())
        self.journal.commit("undo", 1, round_packet("undo", 1, [item]))
        self.assertEqual([0, 1], [row["state"]["count"] for row in self.journal.state()["components"]])
        self.assertEqual(self.journal.checkpoint(), self.load().checkpoint())

    def test_closed_set_permutations_topological_order_and_bad_dependencies(self):
        one = proposal("z", sequence=2)
        two = proposal("a", sequence=0, predecessors=[{"principal": "principal", "proposal_id": "z"}])
        three = proposal("m", sequence=1)
        archives = []
        for ordering in itertools.permutations([one, two, three]):
            owner = cs.CommitSetJournal(self.binding, "same", self.initial, SyntheticCoordinator())
            packet = round_packet("round", 0, ordering)
            self.assertEqual(["m", "z", "a"], [row["proposal_id"] for row in packet["proposals"]])
            owner.commit("round", 0, packet)
            archives.append(owner.checkpoint())
        self.assertTrue(all(row == archives[0] for row in archives))
        self.assert_code("INVALID_VALUE", lambda: round_packet("round", 0, [two]))
        cyclic = copy.deepcopy(one)
        cyclic["predecessor_refs"] = [{"principal": "principal", "proposal_id": "a"}]
        self.assert_code("INVALID_VALUE", lambda: round_packet("round", 0, [cyclic, two]))
        self.assert_code("INVALID_VALUE", lambda: round_packet("round", 0, [one, one]))

    def test_multiple_predecessor_steps_use_regenerated_staged_heads(self):
        first = proposal("one", [selected(self.components[0], "one", {"add": 2})])
        second = proposal("two", [selected(self.components[0], "two", {"add": 3})],
                          predecessors=[{"principal": "principal", "proposal_id": "one"}])
        packet = round_packet("chain", 0, [second, first])
        self.journal.commit("chain", 0, packet)
        steps = json.loads(self.journal.save())["entries"][0]["component_steps"]
        self.assertEqual(steps[0]["after"], steps[1]["before"])
        self.assertEqual(2, self.journal.vector()[0]["revision"])
        self.assertEqual(5, self.journal.state()["components"][0]["state"]["count"])
        self.assertEqual(self.journal.checkpoint(), self.load().checkpoint())

    def test_full_round_capacity_retains_reads_checkpoint_and_exact_retry(self):
        original = self.packet()
        receipt = self.journal.commit("round.0", 0, original)
        for i in range(1, cs.MAX_ROUNDS):
            self.journal.commit("round." + str(i), i, self.packet(i))
        before = self.journal.checkpoint()
        packet = self.packet(cs.MAX_ROUNDS)
        self.assert_code("CAPACITY_EXCEEDED", lambda: self.journal.commit(packet["round_id"], cs.MAX_ROUNDS, packet))
        self.assertEqual(receipt, self.journal.commit("round.0", 0, original))
        self.assertEqual(before, self.journal.checkpoint())

    def test_reentrant_access_even_with_invalid_input_cannot_be_hidden(self):
        for action in (lambda owner: owner.checkpoint(), lambda owner: owner.decisions(None),
                       lambda owner: owner.commit(None, None, None)):
            def reducer(*args):
                try:
                    action(owner)
                except JournalError:
                    pass
                return self.reducer(*args)
            owner = cs.CommitSetJournal(self.binding, "reentry", self.initial, reducer)
            before = owner.checkpoint()
            self.assert_code("POLICY_REJECTED", lambda: owner.commit("round.0", 0, self.packet()))
            self.assertEqual(before, owner.checkpoint())

    def test_checkpoint_concurrent_with_commit_is_complete_and_replayable(self):
        start = threading.Barrier(2)
        def write():
            start.wait(timeout=5)
            for i in range(8):
                self.journal.commit("round." + str(i), i, self.packet(i))
        def read():
            start.wait(timeout=5)
            for _ in range(8):
                raw, exact = self.journal.checkpoint()
                restored = self.load(raw, trusted_head=exact, reducer=SyntheticCoordinator())
                self.assertEqual((raw, exact), restored.checkpoint())
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(write), pool.submit(read)]
            for future in futures:
                future.result(timeout=20)

    def test_hostile_archives_and_changed_trusted_initial_are_rejected(self):
        self.journal.commit("round.0", 0, self.packet())
        raw = self.journal.save()
        mutations = [raw.replace(b'"revision":1', b'"revision":true', 1),
                     raw.replace(b'"revision":1', b'"revision":1.0', 1),
                     raw.replace(b'"revision":1', b'"revision":9007199254740992', 1),
                     raw.replace(b'"format":', b'"format":"duplicate","format":', 1),
                     b'{"deep":' + b'[' * 1000 + b']' * 1000 + b'}', b'\xff', raw + b'x']
        archive = json.loads(raw)
        for mutate in (lambda a: a["entries"].append(copy.deepcopy(a["entries"][0])),
                       lambda a: a["entries"][0]["component_steps"].pop(),
                       lambda a: a["entries"][0]["decisions"][0].update(code="changed"),
                       lambda a: a["final_state"]["components"][0]["state"].update(count=99)):
            altered = copy.deepcopy(archive)
            mutate(altered)
            mutations.append(canonical(altered))
        before = self.journal.checkpoint()
        for changed in mutations:
            self.assert_code("INVALID_ARCHIVE", lambda: self.load(changed))
        self.assert_code("INVALID_ARCHIVE", lambda: self.load(trusted_head="0" * 64))
        self.assert_code("INVALID_TRUSTED_HEAD", lambda: self.load(trusted_head="bad"))
        altered_initial = copy.deepcopy(self.initial)
        altered_initial["components"][0] = cs.initial_component(self.binding, "a", _scope_for_test(), "counter.v1", {"count": 9})
        self.assert_code("INVALID_ARCHIVE", lambda: self.load(initial_state=altered_initial))
        self.assertEqual(before, self.journal.checkpoint())

    def test_all_archive_shapes_limits_and_depth_preflight_before_any_replay(self):
        for i in range(2):
            self.journal.commit("round." + str(i), i, self.packet(i))
        archive = json.loads(self.journal.save())
        changes = [lambda a: a["entries"][1]["component_steps"][0].update(unknown="field"),
            lambda a: a["entries"][1]["packet"]["proposals"][0]["components"][0].update(packet=_nested(49)),
            lambda a: a["entries"][1]["packet"]["proposals"][0]["components"][0].update(packet={"x": "x" * 65536}),
            lambda a: a["entries"][1]["decisions"][0].update(step_indices=[True])]
        for change in changes:
            candidate = copy.deepcopy(archive)
            change(candidate)
            reducer = SyntheticCoordinator()
            self.assert_code("INVALID_ARCHIVE", lambda: self.load(canonical(candidate), reducer=reducer))
            self.assertEqual([], reducer.views)

    def test_binding_genesis_scope_and_noncanonical_inputs_fail_before_callback(self):
        self.assert_code("INVALID_BINDING", lambda: cs.CommitSetJournal(_scope_for_test(), "p", self.initial, self.reducer))
        forged = copy.deepcopy(self.initial)
        forged["components"][0]["head_digest"] = "0" * 64
        self.assert_code("INVALID_VALUE", lambda: cs.CommitSetJournal(self.binding, "p", forged, self.reducer))
        foreign = self.packet()
        foreign["proposals"][0]["components"][0]["scope"]["world_id"] = "elsewhere"
        self.assert_code("INVALID_SCOPE", lambda: self.journal.commit("round.0", 0, foreign))
        unsorted = self.packet()
        unsorted["proposals"][0]["components"].reverse()
        self.assert_code("INVALID_VALUE", lambda: self.journal.commit("round.0", 0, unsorted))
        for packet in (None, [], {"float": 1.0}, {"surrogate": "\ud800"}):
            self.assert_code("INVALID_VALUE", lambda: self.journal.commit("round.0", 0, packet))
        self.assertEqual([], self.reducer.views)

    def test_exact_owner_byte_node_depth_edges_and_round_packet_limit(self):
        valid = [{"v": "x" * 65528}, {"v": [None] * 4093}, _nested(32)]
        invalid = [{"v": "x" * 65529}, {"v": [None] * 4094}, _nested(33)]
        for value in valid:
            self.assertEqual(value, cs.initial_component(self.binding, "edge", _scope_for_test(), "policy", value)["state"])
        for value in invalid:
            self.assert_code("VALUE_LIMIT", lambda: cs.initial_component(self.binding, "edge", _scope_for_test(), "policy", value))
        selections = []
        for i in range(4):
            row = copy.deepcopy(self.components[0])
            row["component_id"] = "component." + str(i)
            selections.append(selected(row, "r", valid[0]))
        self.assert_code("VALUE_LIMIT", lambda: round_packet("big", 0, [proposal("big", selections)]))
        self.assert_code("VALUE_LIMIT", lambda: round_packet("many", 0, [proposal(str(i)) for i in range(9)]))
        with patch.object(cs, "MAX_STEPS", 1):
            before = self.journal.checkpoint()
            self.assert_code("VALUE_LIMIT", lambda: self.journal.commit("round.0", 0, self.packet()))
            self.assertEqual(before, self.journal.checkpoint())

    def test_duplicate_reference_integer_type_is_exact(self):
        # Make the original decision ordinal 1 so True must not compare equal to it.
        first = proposal("a", principal="denied")
        second = proposal("z")
        self.journal.commit("one", 0, round_packet("one", 0, [first, second]))
        def bad(*args):
            result = self.reducer(*args)
            result["decisions"][0]["prior_decision"]["decision_index"] = True
            return result
        before = self.journal.checkpoint()
        with patch.object(self.journal, "_reducer", side_effect=bad):
            self.assert_code("INVALID_REDUCTION", lambda: self.journal.commit("two", 1, round_packet("two", 1, [second])))
        self.assertEqual(before, self.journal.checkpoint())

    def test_aggregate_bounds_preserve_owner_bounds_and_fail_atomically(self):
        components = [cs.initial_component(self.binding, str(i), _scope_for_test(), "counter.v1", {"text": "x" * 40000})
                      for i in range(3)]
        state = {**self.initial, "components": components}
        owner = cs.CommitSetJournal(self.binding, "large", state, self.reducer)
        self.assertGreater(len(canonical(owner.state())), 65536)
        self.assert_code("VALUE_LIMIT", lambda: _object_bytes(owner.state()))
        for value in ({"text": "x" * 65536}, {"nodes": [0] * 4096}, _nested(33)):
            self.assert_code("VALUE_LIMIT", lambda: cs.initial_component(self.binding, "bad", _scope_for_test(), "counter.v1", value))
        for name, replacement in (("ENTRY_LIMITS", (1, 65536, 44)), ("DECISION_LIMITS", (1, 8192, 16)),
                                  ("REDUCTION_LIMITS", (1, 524288, 44)), ("STATE_LIMITS", (1, 131072, 40)),
                                  ("MAX_ARCHIVE_BYTES", 1)):
            before = self.journal.checkpoint()
            with patch.object(cs, name, replacement):
                self.assert_code("VALUE_LIMIT", lambda: self.journal.commit("round.0", 0, self.packet()))
            self.assertEqual(before, self.journal.checkpoint())
        self.journal.commit("round.0", 0, self.packet())

    def test_schema_validates_wire_example_and_rejects_open_shapes(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "data/schemas/m4_commit_set_journal_schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        example = json.loads((root / "examples/state_journal/commit_set.example.json").read_text(encoding="utf-8"))
        validator.validate(example)
        example_binding = cs.CommitSetBinding(example["binding"]["world_id"], example["binding"]["container_id"])
        restored = cs.CommitSetJournal.load(canonical(example), example_binding, example["policy_id"],
            example["initial_state"], SyntheticCoordinator(), example["entries"][-1]["entry_digest"])
        self.assertEqual(canonical(example), restored.save())
        self.journal.commit("round.0", 0, self.packet())
        archive = json.loads(self.journal.save())
        validator.validate(archive)
        archive["entries"][0]["component_steps"][0]["state_after"] = {}
        self.assertTrue(list(validator.iter_errors(archive)))
        duplicate = copy.deepcopy(example)
        duplicate["entries"][0]["decisions"][0].update(status="DUPLICATE", code="DUPLICATE", step_indices=[])
        self.assertTrue(list(validator.iter_errors(duplicate)))


def _scope_for_test():
    return TruthScope("world", "leaf_branch_state", "branch")


def _nested(depth):
    value = {}
    for _ in range(depth):
        value = {"child": value}
    return value


class ActualOwnerCompositionTests(unittest.TestCase):
    def test_actual_player_and_perception_states_publish_and_replay_together(self):
        player = PlayerStatePolicy(*configuration())
        binding, _ = pure_model()
        truth = cv.TruthInputSnapshot("truth", WORLD, (), ("door",), "DECLARED_INPUT")
        provenance = cv.CoreProvenance("snapshot", "diagnostic", "plan", ("ash",))
        perception = PerceptionPolicy(WORLD, "observer", binding, (), ((truth, provenance),))
        owners = {"a.player": player, "z.perception": perception}
        container = cs.CommitSetBinding(WORLD, "actual.owners")
        components = [cs.initial_component(container, name, owner.scope, owner.policy_id, owner.initial_state())
                      for name, owner in owners.items()]
        initial = {"format": "ywe.commit_set_state.v1", "world_id": WORLD, "components": components}
        packets = [player.packet(PRINCIPAL, "player.request", "update:first"), perception.packet("view.request", "truth")]
        item = proposal("actual", [selected(row, request, packet) for row, request, packet in
            zip(components, ("player.request", "view.request"), packets)], principal=PRINCIPAL)
        packet = round_packet("actual.round", 0, [item])
        coordinator = SyntheticCoordinator(owners)
        journal = cs.CommitSetJournal(container, "actual.fixture.v1", initial, coordinator)
        before = journal.checkpoint()
        with patch.object(PerceptionEngine, "compose_overlay", side_effect=ValueError("late actual observer failure")):
            with self.assertRaises(JournalError) as caught:
                journal.commit("actual.round", 0, packet)
            self.assertEqual("POLICY_REJECTED", caught.exception.code)
        self.assertEqual(before, journal.checkpoint())
        receipt = journal.commit("actual.round", 0, packet)
        for index, owner in enumerate(owners.values()):
            self.assertEqual(owner.reduce(owner.initial_state(), packets[index]), journal.state()["components"][index]["state"])
        restored = cs.CommitSetJournal.load(journal.save(), container, "actual.fixture.v1", initial,
                                            SyntheticCoordinator(owners), journal.head())
        self.assertEqual(journal.checkpoint(), restored.checkpoint())
        with patch.object(PlayerStatePolicy, "reduce", side_effect=AssertionError("must not rerun")), \
                patch.object(PerceptionEngine, "compose_overlay", side_effect=AssertionError("must not rerun")):
            self.assertEqual(receipt, restored.commit("actual.round", 0, packet))

    def test_actual_player_compensation_mapping_and_late_observer_failure(self):
        args = list(configuration())
        add_compensation(args)
        player = PlayerStatePolicy(*args)
        binding, _ = pure_model()
        truth = cv.TruthInputSnapshot("truth", WORLD, (), ("door",), "DECLARED_INPUT")
        provenance = cv.CoreProvenance("snapshot", "diagnostic", "plan", ("ash",))
        perception = PerceptionPolicy(WORLD, "observer", binding, (), ((truth, provenance),))
        owners = {"a.player": player, "z.perception": perception}
        container = cs.CommitSetBinding(WORLD, "actual.compensation")
        components = [cs.initial_component(container, name, owner.scope, owner.policy_id, owner.initial_state())
                      for name, owner in owners.items()]
        initial = {"format": "ywe.commit_set_state.v1", "world_id": WORLD, "components": components}
        journal = cs.CommitSetJournal(container, "actual.fixture.v1", initial, SyntheticCoordinator(owners))
        packets = []
        for i, name in enumerate(("first", "second", "compensation")):
            request = "request:" + name
            mapping = [] if i < 2 else [{"component_id": "a.player", "component_request_ref": request,
                "target_round_id": "round.second", "target_principal": PRINCIPAL, "target_proposal_id": "proposal.second",
                "target_component_request_ref": "request:second", "target_component_head": journal.vector()[0]}]
            selections = [selected(components[0], request, player.packet(PRINCIPAL, request, "update:" + name)),
                selected(components[1], "view." + name, perception.packet("view." + name, "truth"))]
            packet = round_packet("round." + name, i, [proposal("proposal." + name, selections,
                principal=PRINCIPAL, compensations=mapping)])
            packets.append(packet)
            if i == 2:
                before = journal.checkpoint()
                with patch.object(PerceptionEngine, "compose_overlay", side_effect=ValueError("late observer failure")):
                    with self.assertRaises(JournalError) as caught:
                        journal.commit("round." + name, i, packet)
                    self.assertEqual("POLICY_REJECTED", caught.exception.code)
                self.assertEqual(before, journal.checkpoint())
            journal.commit("round." + name, i, packet)
        state = journal.state()["components"][0]["state"]
        self.assertEqual(3, len(state["accepted_updates"]))
        restored = cs.CommitSetJournal.load(journal.save(), container, "actual.fixture.v1", initial,
                                            SyntheticCoordinator(owners), journal.head())
        self.assertEqual(journal.checkpoint(), restored.checkpoint())


if __name__ == "__main__":
    unittest.main()
