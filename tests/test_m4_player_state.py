"""Behavioral checks for one atomic player owner and its trusted catalogs."""

import copy
from concurrent.futures import ThreadPoolExecutor
import json
import threading
import unittest
from unittest.mock import patch

from core.narrative_engine.origin_progression import OriginProgressionPolicy
from core.player_state import PlayerStatePolicy, PlayerStateStore
from core.state_journal import CommitJournal, JournalError, TruthScope, _object_bytes
from tests.m4_player_fixture import (
    BRANCH, PLAYER, PRINCIPAL, SOURCE, WORLD, configuration, consequence,
    document, evidence, provenance, record, reference,
)


def selected(args, ref):
    return next(row for row in args[5] if row["ref"] == ref)


def replace_origin(args, sources):
    args[8] = OriginProgressionPolicy(WORLD, PLAYER,
        document("data/profiles/wrw_origin_progression.json")["profile"],
        {"mortal_identity_ref": "identity:mortal", "identity_status": "veiled", "provenance": provenance()},
        {PRINCIPAL: ["advance", "remember"]}, sources, args[7]["action"], args[7]["memory"])


def origin_sources(args):
    return [args[8].evidence("origin:first"), args[8].evidence("origin:second")]


def add_compensation(args, name="compensation", target="request:second"):
    update_ref = "update:" + name
    reason = "reason:" + name
    args[5].append(reference(reason, "evidence_refs"))
    args[5].append(consequence("consequence:" + name, update_ref, {"actions": []}))
    args[6].append({"update_ref": update_ref, "world_id": WORLD, "player_id": PLAYER,
        "branch_ref": BRANCH, "source_system": SOURCE, "operations": [{"kind": "compensate",
            "target_request_ref": target, "reason_refs": [reason]}], "evidence_refs": [reason],
        "consequence_ref": "consequence:" + name, "provenance": provenance()})
    return update_ref


def add_later_remembrance(args):
    source = evidence("origin:third", "update:third", "first_stirrings", "first_stirrings", 1, "remember")
    plane = copy.deepcopy(selected(args, "plane:remembered")["document"])
    plane["planes"]["P4_Mental"]["score_q6"] = 40000
    args[5].extend([record("plane:third", "plane", plane), consequence("consequence:third", "update:third", source)])
    args[6].append({"update_ref": "update:third", "world_id": WORLD, "player_id": PLAYER,
        "branch_ref": BRANCH, "source_system": SOURCE,
        "operations": [{"kind": "origin", "evidence_ref": "origin:third"}, {"kind": "replace",
            "slot": "plane", "previous_ref": "plane:remembered", "next_ref": "plane:third", "condition_refs": []}],
        "evidence_refs": ["evidence:play"], "consequence_ref": "consequence:third", "provenance": provenance()})
    replace_origin(args, origin_sources(args) + [source])


def add_remembrance_update(args, name, operations, source=None):
    refs = {operation["evidence_ref"] for update in args[6] for operation in update["operations"]
            if operation["kind"] == "origin"}
    sources = [args[8].evidence(ref) for ref in sorted(refs)]
    update_ref = "update:" + name
    source = source or evidence("origin:" + name, update_ref, "first_stirrings", "first_stirrings", 1, "remember")
    args[5].append(consequence("consequence:" + name, update_ref, source))
    args[6].append({"update_ref": update_ref, "world_id": WORLD, "player_id": PLAYER,
        "branch_ref": BRANCH, "source_system": SOURCE,
        "operations": [{"kind": "origin", "evidence_ref": source["evidence_ref"]}] + operations,
        "evidence_refs": ["evidence:play"], "consequence_ref": "consequence:" + name, "provenance": provenance()})
    replace_origin(args, sources + [source])
    return update_ref


def manifestation():
    return {"schema_id": "wolf_manifestation_event_schema", "version": "1.0.0",
        "manifestation_event_id": "manifestation:event:one", "manifesting_companions": ["white_wolf"],
        "manifestation_trigger": {"trigger_type": "branch_threshold_crossed", "trigger_ref": "evidence:play",
            "criteria_met": ["A qualified player action reached the threshold."]},
        "manifestation_duration": {"duration_type": "single_scene", "begins_at": "scene:begin", "ends_at": "scene:end"},
        "allowed_functions": ["guidance"], "dismissal_condition": "The qualified threshold scene ends.",
        "forbidden_interpretations": ["morality_meter"], "source_refs": ["evidence:play"]}


def add_branch_transfer(args):
    source = evidence("origin:branch", "update:branch", "first_stirrings", "first_stirrings", 1, "remember")
    action = source["actions"][0]
    action.update(significance="branch_forming", branch_relevance="branch_event_created", branch_event_ref="event:two")
    agent = copy.deepcopy(selected(args, "agent:initial")["document"])
    agent.update(current_leaf_branch_ref="branch:two", current_location_ref="location:two",
        recent_action_trace_refs=[action["action_trace_id"]], branch_event_refs=["event:two"])
    history = copy.deepcopy(selected(args, "history:initial")["document"])
    history.update(current_leaf_branch_ref="branch:two", entries=[{"branch_event_ref": "event:two",
        "leaf_branch_ref": "branch:two", "parent_branch_ref": BRANCH, "chosen_action": "cross_threshold",
        "source_action_trace_ref": action["action_trace_id"], "resulting_player_state_update_refs": ["update:branch"],
        "resulting_worldstate_delta_refs": [], "source_refs": ["evidence:play"]}])
    ability = copy.deepcopy(selected(args, "ability:latent")["document"])
    ability["branch_ref"] = "branch:two"
    ability["history_refs"].append("evidence:play")
    args[5].extend([
        reference("branch:two", "current_leaf_branch_ref", "leaf_branch_state", "branch:two", "branch:two"),
        reference("location:two", "current_location_ref", "leaf_branch_state", "branch:two", "branch:two"),
        reference("event:two", "branch_event_ref", "leaf_branch_state", "branch:two", "branch:two"),
        record("agent:two", "agent", agent, "branch:two"), record("history:two", "branch_history", history, "branch:two"),
        record("ability:two", "ability", ability, "branch:two"), consequence("consequence:branch", "update:branch", source)])
    args[6].append({"update_ref": "update:branch", "world_id": WORLD, "player_id": PLAYER,
        "branch_ref": BRANCH, "source_system": SOURCE,
        "operations": [{"kind": "origin", "evidence_ref": "origin:branch"}, {"kind": "branch",
            "previous_branch_ref": BRANCH, "next_branch_ref": "branch:two", "next_location_ref": "location:two",
            "agent_ref": "agent:two", "history_ref": "history:two", "event_ref": "event:two"},
            {"kind": "ability", "ability_id": "ability:oath", "previous_ref": "ability:latent",
                "next_ref": "ability:two", "condition_refs": []}],
        "evidence_refs": ["evidence:play"], "consequence_ref": "consequence:branch", "provenance": provenance()})
    replace_origin(args, origin_sources(args) + [source])


class PlayerStateTests(unittest.TestCase):
    def assert_code(self, code, function, *args):
        with self.assertRaises(JournalError) as caught:
            function(*args)
        self.assertEqual(code, caught.exception.code)

    def publish(self, owner, update="update:first", request="request:first", revision=0):
        return owner.publish(owner.writer(PRINCIPAL), request, revision, update)

    def publish_two(self, owner):
        self.publish(owner)
        self.publish(owner, "update:second", "request:second", 1)

    def test_combined_update_is_one_commit_and_exact_replay(self):
        args = configuration()
        external = copy.deepcopy(args[5])
        owner = PlayerStateStore(*args)
        before = owner.state()
        receipt = self.publish(owner)
        after = owner.state()
        self.assertEqual(1, receipt.revision)
        self.assertEqual("continuing", after["spine"]["state_lifecycle"])
        self.assertNotIn("celestial_identity_initial_state", after["spine"]["identity"])
        self.assertEqual("first_stirrings", after["records"]["origin:one"]["document"]["current_phase"])
        self.assertEqual("celestial:suspected", after["spine"]["identity"]["celestial_identity_state_ref"])
        self.assertEqual("plane:stirring", after["spine"]["state_refs"]["plane_attunement_state_ref"])
        self.assertEqual(["ability:latent"], after["spine"]["ability_state_refs"])
        self.assertEqual(2, len(after["spine"]["memory_refs"]["player_action_trace_refs"]))
        self.assertEqual(2, len(after["spine"]["memory_refs"]["player_memory_record_refs"]))
        self.assertEqual(["update:first"], after["spine"]["update_control"]["accepted_update_packet_refs"])
        self.assertEqual(["consequence:first", "consequence:first:effect", PLAYER], after["accepted_updates"][0]["effect"])
        for ref, entry in before["records"].items():
            if ref != "origin:one":
                self.assertEqual(entry, after["records"][ref])
        self.assertEqual(external, args[5])
        raw, head = owner.checkpoint()
        self.assertEqual(1, len(json.loads(raw)["entries"]))
        restored = PlayerStateStore.load(raw, head, *args)
        self.assertEqual(after, restored.state())
        self.assertEqual((raw, head), restored.checkpoint())

    def test_late_bad_consequence_has_no_partial_effect_or_reserved_request(self):
        args = list(configuration())
        bad_source = evidence("origin:bad", "update:bad")
        bad_update = copy.deepcopy(args[6][0])
        bad_update.update(update_ref="update:bad", consequence_ref="consequence:bad")
        bad_update["operations"][0]["evidence_ref"] = "origin:bad"
        bad_consequence = consequence("consequence:bad", "update:bad", bad_source)
        bad_consequence["document"]["action_refs"].pop()
        args[5].append(bad_consequence)
        args[6].append(bad_update)
        replace_origin(args, origin_sources(args) + [bad_source])
        owner = PlayerStateStore(*args)
        before = owner.checkpoint()
        with patch.object(owner._domain, "transition", wraps=owner._domain.transition) as transitions:
            self.assert_code("POLICY_REJECTED", self.publish, owner, "update:bad", "request:retry", 0)
        self.assertEqual(3, transitions.call_count)
        self.assertEqual(before, owner.checkpoint())
        receipt = self.publish(owner, "update:first", "request:retry", 0)
        self.assertEqual(1, receipt.revision)

    def test_exact_retries_do_not_reduce_before_or_after_reload(self):
        args = configuration()
        owner = PlayerStateStore(*args)
        receipt = self.publish(owner)
        self.publish(owner, "update:second", "request:second", 1)
        raw, head = owner.checkpoint()
        restored = PlayerStateStore.load(raw, head, *args)
        with patch.object(OriginProgressionPolicy, "reduce", side_effect=AssertionError("retry reduced")):
            for target in (owner, restored):
                self.assertEqual(receipt, self.publish(target))
                self.assertEqual((raw, head), target.checkpoint())
                self.assert_code("IDENTITY_CONFLICT", self.publish, target, "update:first", "request:first", 1)

    def test_changed_update_identity_and_duplicate_domain_effect_are_rejected(self):
        owner = PlayerStateStore(*configuration())
        self.publish(owner)
        before = owner.checkpoint()
        self.assert_code("IDENTITY_CONFLICT", self.publish, owner, "update:second", "request:first", 0)
        self.assert_code("POLICY_REJECTED", self.publish, owner, "update:first", "request:other", 1)
        self.assertEqual(before, owner.checkpoint())
        args = list(configuration())
        first = selected(args, "consequence:first")["document"]
        duplicate = selected(args, "consequence:second")["document"]
        duplicate.update(consequence_id=first["consequence_id"], effect_id=first["effect_id"])
        owner = PlayerStateStore(*args)
        self.publish(owner)
        before = owner.checkpoint()
        self.assert_code("POLICY_REJECTED", self.publish, owner, "update:second", "request:second", 1)
        self.assertEqual(before, owner.checkpoint())

    def test_capabilities_and_source_grants_cannot_be_forged(self):
        owner, foreign = PlayerStateStore(*configuration()), PlayerStateStore(*configuration())
        writer = owner.writer(PRINCIPAL)
        for invalid in (object(), copy.copy(writer), foreign.writer(PRINCIPAL), PRINCIPAL, {"principal": PRINCIPAL}):
            with self.subTest(writer=type(invalid).__name__):
                self.assert_code("UNAUTHORIZED_WRITER", owner.publish, invalid, "request:first", 0, "update:first")
        args = list(configuration())
        args[6][0]["source_system"] = "realm_engine"
        owner = PlayerStateStore(*args)
        self.assert_code("UNAUTHORIZED_WRITER", self.publish, owner)
        args = list(configuration())
        args[4][PRINCIPAL]["operations"].remove("ability")
        owner = PlayerStateStore(*args)
        before = owner.checkpoint()
        self.assert_code("POLICY_REJECTED", self.publish, owner)
        self.assertEqual(before, owner.checkpoint())
        args[4][PRINCIPAL]["source_system"] = "host_adapter"
        self.assert_code("INVALID_POLICY", PlayerStateStore, *args)

    def test_configuration_and_returned_snapshots_are_detached(self):
        args = list(configuration())
        owner = PlayerStateStore(*args)
        before = owner.checkpoint()
        args[2]["raven_companion_id"] = "changed"
        args[3]["player_id"] = "player:wrong"
        args[4][PRINCIPAL]["operations"].clear()
        selected(args, "plane:stirring")["document"]["planes"]["P4_Mental"]["score_q6"] = 999999
        args[6][0]["operations"].clear()
        args[7]["spine"]["required"].clear()
        args[8].evidence("origin:first")["actions"].clear()
        view = owner.state()
        view["spine"]["state_refs"].clear()
        view["records"]["origin:one"]["document"]["creation"]["provenance"]["source_ash_refs"].clear()
        self.assertEqual(before, owner.checkpoint())
        self.publish(owner)
        self.assertEqual(20000, owner.state()["records"]["plane:stirring"]["document"]["planes"]["P4_Mental"]["score_q6"])

    def test_changed_or_missing_used_catalog_refuses_replay_but_extension_preserves_it(self):
        args = configuration()
        owner = PlayerStateStore(*args)
        self.publish(owner)
        raw, head = owner.checkpoint()
        for kind in ("document", "provenance", "missing"):
            with self.subTest(change=kind):
                changed = list(configuration())
                row = selected(changed, "plane:stirring")
                if kind == "document":
                    row["document"]["planes"]["P4_Mental"]["score_q6"] += 1
                elif kind == "provenance":
                    row["provenance"]["diagnostic_ref"] = "diagnostic:changed"
                else:
                    changed[5].remove(row)
                self.assert_code("INVALID_ARCHIVE", PlayerStateStore.load, raw, head, *changed)
        extended = list(configuration())
        extended[5].append(reference("unused:qualified", "quest_history_refs"))
        self.assertEqual((raw, head), PlayerStateStore.load(raw, head, *extended).checkpoint())

    def test_initial_reveal_missing_raven_and_wrong_bindings_are_rejected(self):
        for defect in ("revealed", "raven", "world", "player", "branch", "subject", "agent", "origin"):
            with self.subTest(defect=defect):
                args = list(configuration())
                if defect == "revealed":
                    selected(args, "celestial:initial")["document"].update(identity_state="suspected",
                        reveal_status="player_suspects", evidence_refs=["evidence:play"])
                elif defect == "raven":
                    del args[3]["state_refs"]["raven_companion_state_ref"]
                elif defect in ("world", "player"):
                    selected(args, "plane:initial")[defect + "_id"] = defect + ":other"
                elif defect == "branch":
                    selected(args, "agent:initial")["branch_ref"] = "branch:other"
                elif defect == "subject":
                    selected(args, BRANCH)["document"]["subject_id"] = "branch:other"
                elif defect == "agent":
                    selected(args, "agent:initial")["document"]["mortal_instance_id"] = "identity:other"
                else:
                    args[3]["identity"]["mortal_identity_ref"] = "identity:other"
                self.assert_code("INVALID_POLICY", PlayerStateStore, *args)

    def test_duplicate_catalog_and_ambiguous_schema_bindings_are_rejected(self):
        args = list(configuration())
        args[5].append(copy.deepcopy(args[5][0]))
        self.assert_code("INVALID_POLICY", PlayerStateStore, *args)
        for defect in ("extra_kind", "wrong_id", "nested_id", "remote", "dynamic", "unknown_local"):
            with self.subTest(defect=defect):
                args = list(configuration())
                schema = args[7]["spine"]
                if defect == "extra_kind":
                    args[7]["other"] = schema
                elif defect == "wrong_id":
                    schema["$id"] = "https://ywe.local/schemas/other_schema.json"
                elif defect == "nested_id":
                    schema["$defs"]["initial_identity"]["$id"] = "https://external.invalid/schema"
                elif defect == "remote":
                    schema["allOf"].append({"$ref": "https://external.invalid/schema"})
                elif defect == "dynamic":
                    schema["$dynamicRef"] = "#/$defs/initial_identity"
                else:
                    schema["allOf"].append({"$ref": "#/$defs/missing"})
                self.assert_code("INVALID_POLICY", PlayerStateStore, *args)

    def test_unlinked_update_evidence_is_not_authorized_by_an_unrelated_action(self):
        args = list(configuration())
        args[5].append(reference("evidence:unrelated", "evidence_refs"))
        args[6][0]["evidence_refs"].append("evidence:unrelated")
        owner = PlayerStateStore(*args)
        before = owner.checkpoint()
        self.assert_code("POLICY_REJECTED", self.publish, owner)
        self.assertEqual(before, owner.checkpoint())

    def test_stale_request_and_competing_publications_leave_one_complete_result(self):
        owner = PlayerStateStore(*configuration())
        self.publish(owner)
        before = owner.checkpoint()
        self.assert_code("REVISION_CONFLICT", self.publish, owner, "update:second", "request:second", 0)
        self.assertEqual(before, owner.checkpoint())
        self.assertEqual(2, self.publish(owner, "update:second", "request:second", 1).revision)
        owner = PlayerStateStore(*configuration())
        barrier = threading.Barrier(2)
        def competing(request):
            barrier.wait()
            try:
                return self.publish(owner, "update:first", request, 0).revision
            except JournalError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(competing, ["race:one", "race:two"]))
        self.assertCountEqual([1, "REVISION_CONFLICT"], outcomes)
        state = owner.state()
        self.assertEqual(1, len(state["accepted_updates"]))
        self.assertEqual(2, len(state["records"]["origin:one"]["document"]["memories"]))
        self.assertEqual(["ability:latent"], state["spine"]["ability_state_refs"])

    def test_complete_aggregate_capacity_refuses_without_evicting_history(self):
        args = list(configuration())
        sources = origin_sources(args)
        sources[0]["memories"][0]["cosmological_tags"] = ["x" * 30000]
        replace_origin(args, sources)
        self.assertLess(len(_object_bytes(sources[0])), 65536)
        component = args[8].reduce(args[8].initial_state(), args[8].packet(PRINCIPAL, "request:first", "origin:first"))
        self.assertLess(len(_object_bytes(component)), 65536)
        owner = PlayerStateStore(*args)
        before = owner.checkpoint()
        self.assert_code("VALUE_LIMIT", owner._reduce, owner._scope, owner.state(),
            owner._packet(PRINCIPAL, "request:first", "update:first"))
        self.assert_code("POLICY_REJECTED", self.publish, owner)
        self.assertEqual(before, owner.checkpoint())

    def test_compensation_preserves_memory_consumed_effects_and_replay(self):
        args = list(configuration())
        update = add_compensation(args)
        owner = PlayerStateStore(*args)
        self.publish_two(owner)
        before = owner.state()
        receipt = self.publish(owner, update, "request:compensation", 2)
        after = owner.state()
        self.assertEqual(3, receipt.revision)
        self.assertEqual("plane:stirring", after["spine"]["state_refs"]["plane_attunement_state_ref"])
        self.assertEqual(before["records"]["origin:one"], after["records"]["origin:one"])
        self.assertEqual(before["spine"]["memory_refs"], after["spine"]["memory_refs"])
        self.assertEqual(before["accepted_updates"], after["accepted_updates"][:2])
        self.assertIn("plane:remembered", after["records"])
        self.assertIn("consequence:second", after["records"])
        self.assertEqual("request:second", after["compensations"][0]["target_request_ref"])
        raw, head = owner.checkpoint()
        self.assertEqual("request:second", json.loads(raw)["entries"][-1]["compensates"])
        restored = PlayerStateStore.load(raw, head, *args)
        self.assertEqual((raw, head), restored.checkpoint())
        self.assertEqual(receipt, self.publish(restored, update, "request:compensation", 2))
        before = owner.checkpoint()
        self.assert_code("POLICY_REJECTED", self.publish, owner, "update:second", "request:reapply", 3)
        self.assertEqual(before, owner.checkpoint())

    def test_compensation_refuses_ineligible_target_stale_poststate_and_repeat(self):
        for defect in ("ineligible", "stale", "repeat"):
            with self.subTest(defect=defect):
                args = list(configuration())
                if defect == "stale":
                    add_later_remembrance(args)
                update = add_compensation(args, target="request:first" if defect == "ineligible" else "request:second")
                repeated = add_compensation(args, "repeated") if defect == "repeat" else None
                owner = PlayerStateStore(*args)
                self.publish_two(owner)
                revision = 2
                if defect == "stale":
                    self.publish(owner, "update:third", "request:third", revision)
                    revision += 1
                if defect == "repeat":
                    self.publish(owner, update, "request:compensation", revision)
                    revision += 1
                    update = repeated
                before = owner.checkpoint()
                self.assert_code("POLICY_REJECTED", self.publish, owner, update, "request:refused", revision)
                self.assertEqual(before, owner.checkpoint())

    def test_authorized_branch_transfer_preserves_portable_state_and_rebinds_ability(self):
        args = list(configuration())
        add_branch_transfer(args)
        sources_before = copy.deepcopy(args[5])
        owner = PlayerStateStore(*args)
        self.publish(owner)
        before = owner.state()
        self.publish(owner, "update:branch", "request:branch", 1)
        after = owner.state()
        self.assertEqual("branch:two", after["spine"]["current_leaf_branch_ref"])
        self.assertEqual("location:two", after["spine"]["current_location_ref"])
        self.assertEqual("agent:two", after["spine"]["state_refs"]["player_agent_state_ref"])
        self.assertEqual("history:two", after["spine"]["state_refs"]["player_branch_history_ref"])
        self.assertEqual(["ability:two"], after["spine"]["ability_state_refs"])
        for ref in ("celestial:suspected", "plane:stirring", "bloodline:initial", "wolf:initial", "raven:initial", BRANCH):
            self.assertEqual(before["records"][ref], after["records"][ref])
        self.assertEqual(BRANCH, after["records"]["origin:branch:action:0"]["document"]["branch_ref"])
        self.assertEqual(sources_before, args[5])
        raw, head = owner.checkpoint()
        self.assertEqual((raw, head), PlayerStateStore.load(raw, head, *args).checkpoint())

    def test_branch_transfer_refuses_wrong_parent_and_missing_player_action(self):
        for field, value in (("parent_branch_ref", "branch:unrelated"),
                             ("source_action_trace_ref", "action:unrelated")):
            with self.subTest(field=field):
                args = list(configuration())
                add_branch_transfer(args)
                selected(args, "history:two")["document"]["entries"][-1][field] = value
                owner = PlayerStateStore(*args)
                self.publish(owner)
                before = owner.checkpoint()
                self.assert_code("POLICY_REJECTED", self.publish, owner, "update:branch", "request:branch", 1)
                self.assertEqual(before, owner.checkpoint())

    def test_branch_ability_rebinding_requires_new_qualified_history(self):
        for history in ([], ["evidence:unrelated"]):
            with self.subTest(history=history):
                args = list(configuration())
                add_branch_transfer(args)
                selected(args, "ability:two")["document"]["history_refs"] = history
                owner = PlayerStateStore(*args)
                self.publish(owner)
                before = owner.checkpoint()
                self.assert_code("POLICY_REJECTED", self.publish, owner, "update:branch", "request:branch", 1)
                self.assertEqual(before, owner.checkpoint())

    def test_remembering_retained_action_appends_memory_without_rewriting_action(self):
        args = list(configuration())
        source = evidence("origin:recollection", "update:recollection", "first_stirrings", "first_stirrings", 1, "remember")
        old_action = args[8].evidence("origin:first")["actions"][0]
        source["actions"] = [old_action]
        source["memories"][0]["source_action_trace_ref"] = old_action["action_trace_id"]
        update = add_remembrance_update(args, "recollection", [], source)
        owner = PlayerStateStore(*args)
        self.publish(owner)
        before = owner.state()
        self.publish(owner, update, "request:recollection", 1)
        after = owner.state()
        self.assertEqual(before["spine"]["memory_refs"]["player_action_trace_refs"],
            after["spine"]["memory_refs"]["player_action_trace_refs"])
        self.assertEqual(before["records"][old_action["action_trace_id"]], after["records"][old_action["action_trace_id"]])
        self.assertEqual(["update:first"], after["records"][old_action["action_trace_id"]]["document"]["resulting_player_state_update_refs"])
        self.assertEqual(3, len(after["spine"]["memory_refs"]["player_memory_record_refs"]))
        raw, head = owner.checkpoint()
        self.assertEqual((raw, head), PlayerStateStore.load(raw, head, *args).checkpoint())

    def test_manifestation_dismissal_retains_event_and_cannot_repeat_consumed_identity(self):
        args = list(configuration())
        event = manifestation()
        args[5].extend([record("manifestation:one", "manifestation", event),
            record("manifestation:alias", "manifestation", event)])
        appear = add_remembrance_update(args, "appear", [{"kind": "manifest", "event_ref": "manifestation:one"}])
        dismiss = add_remembrance_update(args, "dismiss", [{"kind": "dismiss", "event_ref": "manifestation:one",
            "condition_ref": "evidence:play"}])
        repeat = add_remembrance_update(args, "repeat", [{"kind": "manifest", "event_ref": "manifestation:one"}])
        alias = add_remembrance_update(args, "alias", [{"kind": "manifest", "event_ref": "manifestation:alias"}])
        owner = PlayerStateStore(*args)
        self.publish(owner)
        self.assertEqual([], owner.state()["spine"]["state_refs"]["wolf_manifestation_event_refs"])
        self.publish(owner, appear, "request:appear", 1)
        self.assertEqual(["manifestation:one"], owner.state()["spine"]["state_refs"]["wolf_manifestation_event_refs"])
        event_entry = owner.state()["records"]["manifestation:one"]
        self.publish(owner, dismiss, "request:dismiss", 2)
        self.assertEqual([], owner.state()["spine"]["state_refs"]["wolf_manifestation_event_refs"])
        self.assertEqual(event_entry, owner.state()["records"]["manifestation:one"])
        before = owner.checkpoint()
        for update in (repeat, alias):
            with self.subTest(update=update):
                self.assert_code("POLICY_REJECTED", self.publish, owner, update, "request:rejected", 3)
                self.assertEqual(before, owner.checkpoint())
        self.assertEqual(before, PlayerStateStore.load(*before, *args).checkpoint())

    def test_manifestation_requires_criteria_duration_and_dismissal_condition(self):
        for defect in ("criteria", "duration", "dismissal"):
            with self.subTest(defect=defect):
                args = list(configuration())
                event = manifestation()
                if defect == "criteria":
                    event["manifestation_trigger"]["criteria_met"] = []
                elif defect == "duration":
                    event["manifestation_duration"]["ends_at"] = event["manifestation_duration"]["begins_at"]
                else:
                    event["dismissal_condition"] = ""
                args[5].append(record("manifestation:bad", "manifestation", event))
                update = add_remembrance_update(args, "bad_manifest", [{"kind": "manifest", "event_ref": "manifestation:bad"}])
                owner = PlayerStateStore(*args)
                self.publish(owner)
                before = owner.checkpoint()
                self.assert_code("POLICY_REJECTED", self.publish, owner, update, "request:manifest", 1)
                self.assertEqual(before, owner.checkpoint())

    def test_raven_story_separation_requires_conditions_and_retains_persistent_slot(self):
        args = list(configuration())
        separated = copy.deepcopy(selected(args, "raven:initial")["document"])
        separated["runtime_status"] = "story_separated"
        args[5].append(record("raven:separated", "raven", separated))
        operation = {"kind": "replace", "slot": "raven", "previous_ref": "raven:initial",
            "next_ref": "raven:separated", "condition_refs": []}
        refused = add_remembrance_update(args, "unqualified_separation", [copy.deepcopy(operation)])
        operation["condition_refs"] = ["evidence:play"]
        accepted = add_remembrance_update(args, "qualified_separation", [operation])
        owner = PlayerStateStore(*args)
        self.publish(owner)
        before = owner.checkpoint()
        self.assert_code("POLICY_REJECTED", self.publish, owner, refused, "request:separate", 1)
        self.assertEqual(before, owner.checkpoint())
        self.publish(owner, accepted, "request:separate", 1)
        after = owner.state()
        self.assertEqual("raven:separated", after["spine"]["state_refs"]["raven_companion_state_ref"])
        self.assertEqual("always_with_player", after["records"]["raven:separated"]["document"]["presence_rule"])
        self.assertIn("raven:initial", after["records"])
        self.assertEqual(3, len(after["spine"]["memory_refs"]["player_memory_record_refs"]))
        self.assertEqual(owner.checkpoint(), PlayerStateStore.load(*owner.checkpoint(), *args).checkpoint())

    def test_forged_genesis_and_request_envelope_are_rejected_even_with_valid_hashes(self):
        args = configuration()
        owner = PlayerStateStore(*args)
        forged = copy.deepcopy(owner._initial)
        forged["records"]["origin:one"]["document"]["current_phase"] = "world_actor"
        journal = CommitJournal(owner._scope, owner._policy_id, forged, owner._reduce)
        self.assert_code("INVALID_ARCHIVE", PlayerStateStore.load, *journal.checkpoint(), *args)
        journal = CommitJournal(owner._scope, owner._policy_id, owner._initial, owner._reduce)
        journal.commit("outer:request", 0, owner._packet(PRINCIPAL, "inner:request", "update:first"))
        self.assert_code("INVALID_ARCHIVE", PlayerStateStore.load, *journal.checkpoint(), *args)

    def test_forged_compensation_envelope_is_rejected_even_with_valid_hashes(self):
        args = list(configuration())
        update = add_compensation(args)
        owner = PlayerStateStore(*args)
        journal = CommitJournal(owner._scope, owner._policy_id, owner._initial, owner._reduce)
        journal.commit("request:first", 0, owner._packet(PRINCIPAL, "request:first", "update:first"))
        journal.commit("request:second", 1, owner._packet(PRINCIPAL, "request:second", "update:second"))
        journal.commit("request:compensation", 2, owner._packet(PRINCIPAL, "request:compensation", update),
            compensates="request:first")
        self.assert_code("INVALID_ARCHIVE", PlayerStateStore.load, *journal.checkpoint(), *args)


class PlayerStatePolicyTests(unittest.TestCase):
    def assert_code(self, code, function, *args):
        with self.assertRaises(JournalError) as caught:
            function(*args)
        self.assertEqual(code, caught.exception.code)

    def test_pure_policy_matches_store_packets_states_compensation_and_branch_transfer(self):
        args = list(configuration())
        add_compensation(args)
        add_branch_transfer(args)
        policy, owner = PlayerStatePolicy(*args), PlayerStateStore(*args)
        initial = policy.initial_state()
        state = initial
        self.assertEqual(owner._scope, policy.scope)
        self.assertEqual(owner._policy_id, policy.policy_id)
        self.assertEqual(owner.state(), state)
        for revision, name in enumerate(("first", "second", "compensation", "branch")):
            request, update = "request:" + name, "update:" + name
            packet = policy.packet(PRINCIPAL, request, update)
            self.assertEqual(owner._packet(PRINCIPAL, request, update), packet)
            state = policy.reduce(state, packet)
            owner.publish(owner.writer(PRINCIPAL), request, revision, update)
            self.assertEqual(owner.state(), state)
            self.assertEqual(packet, json.loads(owner.checkpoint()[0])["entries"][-1]["packet"])
        self.assertEqual(initial, policy.initial_state())
        self.assertFalse(hasattr(policy, "_journal"))
        self.assertFalse(hasattr(policy, "writer"))
        for attribute, replacement in (("scope", TruthScope(WORLD, "player_state", "player:other")),
                                       ("policy_id", "policy:changed")):
            with self.subTest(attribute=attribute), self.assertRaises(AttributeError):
                setattr(policy, attribute, replacement)
        self.assert_code("POLICY_REJECTED", owner._reduce,
            TruthScope(WORLD, "player_state", "player:other"), initial,
            policy.packet(PRINCIPAL, "request:first", "update:first"))

    def test_pure_inputs_outputs_and_configuration_are_detached(self):
        args = list(configuration())
        policy = PlayerStatePolicy(*args)
        initial = policy.initial_state()
        state = policy.initial_state()
        packet = policy.packet(PRINCIPAL, "request:first", "update:first")
        original_packet = copy.deepcopy(packet)
        expected = policy.reduce(state, packet)
        self.assertEqual(initial, state)
        self.assertEqual(original_packet, packet)
        args[2]["raven_companion_id"] = "changed"
        args[3]["identity"].clear()
        args[4][PRINCIPAL]["operations"].clear()
        selected(args, "plane:stirring")["document"]["planes"]["P4_Mental"]["score_q6"] += 1
        args[6][0]["operations"].clear()
        args[7]["spine"]["required"].clear()
        changed_output = policy.reduce(state, packet)
        changed_output["records"]["origin:one"]["document"]["actions"].clear()
        changed_output["spine"]["state_refs"].clear()
        state["records"]["origin:one"]["document"]["creation"]["provenance"].clear()
        packet["record_sha256"].clear()
        packet["origin_packet"]["evidence_sha256"] = "0" * 64
        self.assertEqual(initial, policy.initial_state())
        self.assertEqual(original_packet, policy.packet(PRINCIPAL, "request:first", "update:first"))
        self.assertEqual(expected, policy.reduce(policy.initial_state(), original_packet))

    def test_late_failed_pure_reduction_preserves_inputs_and_allows_valid_retry(self):
        args = list(configuration())
        bad_source = evidence("origin:bad", "update:bad")
        bad_update = copy.deepcopy(args[6][0])
        bad_update.update(update_ref="update:bad", consequence_ref="consequence:bad")
        bad_update["operations"][0]["evidence_ref"] = "origin:bad"
        bad_consequence = consequence("consequence:bad", "update:bad", bad_source)
        bad_consequence["document"]["action_refs"].pop()
        args[5].append(bad_consequence)
        args[6].append(bad_update)
        replace_origin(args, origin_sources(args) + [bad_source])
        policy, owner = PlayerStatePolicy(*args), PlayerStateStore(*args)
        state = policy.initial_state()
        packet = policy.packet(PRINCIPAL, "request:retry", "update:bad")
        before = copy.deepcopy((state, packet))
        with patch.object(policy._domain, "transition", wraps=policy._domain.transition) as transitions:
            self.assert_code("POLICY_REJECTED", policy.reduce, state, packet)
        self.assertEqual(3, transitions.call_count)
        self.assertEqual(before, (state, packet))
        self.assertEqual(state, policy.initial_state())
        self.assert_code("POLICY_REJECTED", owner.publish,
            owner.writer(PRINCIPAL), "request:retry", 0, "update:bad")
        accepted = policy.reduce(state, policy.packet(PRINCIPAL, "request:retry", "update:first"))
        owner.publish(owner.writer(PRINCIPAL), "request:retry", 0, "update:first")
        self.assertEqual(owner.state(), accepted)

    def test_direct_policy_enforces_aggregate_bound_without_mutating_inputs(self):
        args = list(configuration())
        sources = origin_sources(args)
        sources[0]["memories"][0]["cosmological_tags"] = ["x" * 30000]
        replace_origin(args, sources)
        component = args[8].reduce(args[8].initial_state(),
            args[8].packet(PRINCIPAL, "request:first", "origin:first"))
        self.assertLess(len(_object_bytes(component)), 65536)
        policy = PlayerStatePolicy(*args)
        state, packet = policy.initial_state(), policy.packet(PRINCIPAL, "request:first", "update:first")
        before = copy.deepcopy((state, packet))
        self.assert_code("VALUE_LIMIT", policy.reduce, state, packet)
        self.assertEqual(before, (state, packet))
        self.assertEqual(state, policy.initial_state())

    def test_record_accessor_preserves_qualified_wrapper_and_detaches_nested_values(self):
        args = configuration()
        policy = PlayerStatePolicy(*args)
        expected = copy.deepcopy(selected(args, "plane:stirring"))
        qualified = policy.record("plane:stirring")
        self.assertEqual(expected, qualified)
        self.assertEqual({"ref", "kind", "world_id", "player_id", "branch_ref", "document", "provenance"}, set(qualified))
        qualified["document"]["planes"].clear()
        qualified["provenance"]["source_ash_refs"].clear()
        qualified["branch_ref"] = "branch:foreign"
        self.assertEqual(expected, policy.record("plane:stirring"))
        self.assert_code("UNKNOWN_EVIDENCE", policy.record, "record:missing")
        self.assert_code("UNKNOWN_EVIDENCE", policy.record, "origin:one")

    def test_public_packet_and_reduce_reject_malformed_principals_with_stable_codes(self):
        policy = PlayerStatePolicy(*configuration())
        state = policy.initial_state()
        for principal in ({}, [], None, 12, True, ""):
            with self.subTest(principal=principal):
                self.assert_code("INVALID_VALUE", policy.packet, principal, "request:first", "update:first")
                packet = policy.packet(PRINCIPAL, "request:first", "update:first")
                packet["principal"] = principal
                before = copy.deepcopy((state, packet))
                self.assert_code("INVALID_VALUE", policy.reduce, state, packet)
                self.assertEqual(before, (state, packet))
        self.assert_code("UNAUTHORIZED_WRITER", policy.packet, "principal:foreign", "request:first", "update:first")
        self.assertEqual(policy.initial_state(), state)

    def test_imported_policy_matches_store_initial_and_continuing_admission(self):
        from tests.m4_player_migration_fixture import build

        for adapter in ("closed_reference_v1", "historical_record_v1"):
            for continuing in (False, True):
                with self.subTest(adapter=adapter, continuing=continuing):
                    raw, migration, result, args = build(adapter, continuing)
                    policy = PlayerStatePolicy.from_migration(result, migration, raw, *args)
                    owner = PlayerStateStore.from_migration(result, migration, raw, *args)
                    initial = policy.initial_state()
                    self.assertEqual(result["baseline"], initial)
                    self.assertEqual(owner.state(), initial)
                    self.assertEqual(owner._scope, policy.scope)
                    self.assertEqual(owner._policy_id, policy.policy_id)
                    if continuing:
                        packet = policy.packet(PRINCIPAL, "request:new", "update:second")
                        before_packet = copy.deepcopy(packet)
                        reduced = policy.reduce(initial, packet)
                        owner.publish(owner.writer(PRINCIPAL), "request:new", 0, "update:second")
                        self.assertEqual(owner.state(), reduced)
                        self.assertEqual(before_packet, packet)
                        self.assertEqual(result["baseline"], initial)
                        self.assert_code("POLICY_REJECTED", policy.reduce, initial,
                            policy.packet(PRINCIPAL, "request:historical:first", "update:second"))
                        self.assertEqual(result["baseline"], initial)
                    result["baseline"]["records"].clear()
                    args[3]["state_refs"].clear()
                    self.assertEqual(initial, policy.initial_state())

    def test_imported_policy_factory_reverifies_source_result_and_qualification(self):
        from tests.m4_player_migration_fixture import build

        raw, migration, result, args = build("historical_record_v1", True)
        changed = copy.deepcopy(result)
        changed["baseline"]["spine"]["player_id"] = "player:foreign"
        for candidate, source in ((changed, raw), (result, raw + b" ")):
            self.assert_code("INVALID_MIGRATION", PlayerStatePolicy.from_migration,
                candidate, migration, source, *args)
        with patch.object(type(migration), "verify", return_value=False):
            self.assert_code("INVALID_MIGRATION", PlayerStatePolicy.from_migration,
                result, migration, raw, *args)
        for defect in ("profile", "record", "schema", "origin"):
            with self.subTest(defect=defect):
                modified = list(args)
                if defect == "profile":
                    modified[2] = copy.deepcopy(args[2])
                    modified[2]["profile_id"] = "profile:foreign"
                elif defect == "record":
                    modified[5] = copy.deepcopy(args[5])
                    selected(modified, "plane:stirring")["provenance"]["diagnostic_ref"] = "diagnostic:changed"
                elif defect == "schema":
                    modified[7] = copy.deepcopy(args[7])
                    modified[7]["spine"]["description"] = "Changed qualification."
                else:
                    modified[8] = configuration()[8]
                self.assert_code("INVALID_MIGRATION", PlayerStatePolicy.from_migration,
                    result, migration, raw, *modified)
        self.assert_code("INVALID_POLICY", PlayerStatePolicy, *args)


if __name__ == "__main__":
    unittest.main()
