"""Executable lineage/choice/typed-merge boundaries, without coordinator claims."""

import copy
import json
import unittest

from jsonschema import Draft202012Validator

from core.branch_state import BranchReadView, BranchStatePolicy, _digest, _ordered_union, _presence
from core.branch_state_wrw import qualify_action, qualify_creation, qualify_player_effect, qualify_retention
from core.commit_set_journal import initial_component, _head_of
from core.state_journal import JournalError, TruthScope, _object_bytes
from core.player_state import PlayerStatePolicy
from tests.m4_branch_fixture import (
    BINDING, BOOTSTRAP_PRINCIPAL, MERGE_PRINCIPAL, PLAYER, PRINCIPAL, WORLD,
    fork_case, history, merge_case, qualified, reference, root_case, schemas, scope, step,
)
from tests.m4_player_migration_fixture import build as imported_configuration


def update_record(args, ref, transform):
    row = next(row for row in args[5] if row["ref"] == ref)
    transform(row["document"])
    row["sha256"] = _digest(row["document"])


def rebuild(case, transform, principal=PRINCIPAL):
    args = copy.deepcopy(case["args"])
    transform(args)
    policy = BranchStatePolicy(*args)
    return policy, policy.packet(principal, case["packet"]["request_id"], args[6][0]["proposal_ref"])


def view_like(case, *, before=None, after=None, actions=None, effects=None, retentions=None, snapshots=None, staged_history=None):
    view = case["view"]
    return BranchReadView(WORLD,
        before if before is not None else [json.loads(row) for row in view._before.values()],
        after if after is not None else [json.loads(row) for row in view._after.values()],
        history(snapshots) if snapshots is not None else view._history,
        view.actions() if actions is None else actions, view.effects() if effects is None else effects,
        view.creations(), view.retentions() if retentions is None else retentions,
        [json.loads(row) for row in view._staged_history.values()] if staged_history is None else staged_history)


class BranchStateTests(unittest.TestCase):
    def assert_code(self, code, function, *args, **kwargs):
        with self.assertRaises(JournalError) as caught:
            function(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)

    def reduce(self, case, view=None):
        return case["policy"].reduce(case["policy"].initial_state(), case["packet"], view or case["view"])

    def test_four_additive_schemas_and_shared_typed_values(self):
        for schema in schemas().values():
            Draft202012Validator.check_schema(schema)
        root = root_case()
        validator = root["policy"]._validators["owner"]
        self.assertTrue(validator.is_valid(root["state"]))
        wrong = copy.deepcopy(root["state"])
        wrong["branch"]["current_slots"][0]["value"] = {"kind": "flag", "value": True}
        self.assertFalse(validator.is_valid(wrong))
        wrong = copy.deepcopy(root["state"])
        wrong["branch"]["lineage"]["parents"] = [_head_of(root["world"])]
        self.assertFalse(validator.is_valid(wrong))
        wrong = copy.deepcopy(root["state"])
        wrong["branch"]["unexpected"] = True
        self.assertFalse(validator.is_valid(wrong))

    def test_event_free_root_is_distinct_from_unpublished_reservation(self):
        case = root_case()
        self.assertIsNone(case["policy"].initial_state()["branch"])
        state = case["state"]
        self.assertEqual({}, state["events"])
        self.assertEqual([], state["branch"]["history"]["branch_event_refs"])
        self.assertEqual([], state["branch"]["lineage"]["parents"])
        self.assertIsNone(state["branch"]["lineage"]["event_ref"])
        self.assertIsNone(state["branch"]["active_plane_pressure_ref"])
        self.assertEqual(case["world"]["state"]["facts"], state["branch"]["current_slots"])

    def test_genesis_has_no_synthetic_request_consumption(self):
        case = root_case()
        state = case["policy"].genesis(BOOTSTRAP_PRINCIPAL, "proposal:root", case["view"])
        self.assertEqual([], state["branch"]["consumed"])
        self.assertEqual([], state["branch"]["history"]["occurrences"])
        self.assertEqual({}, state["events"])
        self.assertEqual(1, len(case["state"]["branch"]["consumed"]))
        self.assert_code("UNAUTHORIZED", case["policy"].genesis, PRINCIPAL, "proposal:root", case["view"])

    def test_root_genesis_bytes_do_not_depend_on_player_genesis_hash(self):
        case = root_case()
        original = case["policy"].genesis(BOOTSTRAP_PRINCIPAL, "proposal:root", case["view"])
        player_args = list(case["player_args"])
        player_args[5] = copy.deepcopy(player_args[5])
        next(row for row in player_args[5] if row["ref"] == "diagnostic:initial")["document"]["source_sha256"] = _digest({"different": "qualified diagnostic source"})
        player_policy = PlayerStatePolicy(*player_args)
        player = initial_component(BINDING, "component:player", player_policy.scope, player_policy.policy_id, player_policy.initial_state())
        self.assertNotEqual(player["state_sha256"], case["player"]["state_sha256"])
        args = copy.deepcopy(case["args"])
        update_record(args, "player:creation", lambda value: value.update(source_sha256=player["state_sha256"]))
        heads = [_head_of(case["world"]), _head_of(player)]
        update_record(args, "context:branch:one", lambda value: value.update(read_heads=heads))
        args[6][0]["expected_heads"] = heads
        policy = BranchStatePolicy(*args)
        creation = qualify_creation(player, "player:creation", owner_policy=player_policy)
        view = BranchReadView(WORLD, [case["world"], player], [], history(), [], [], [creation])
        self.assertEqual(original, policy.genesis(BOOTSTRAP_PRINCIPAL, "proposal:root", view))

    def test_root_refuses_missing_creation_and_continuing_reset(self):
        case = root_case()
        view = BranchReadView(WORLD, [case["world"], case["player"]], [], history(), [], [])
        self.assert_code("INVALID_CREATION", self.reduce, case, view)
        fork = fork_case(case)
        self.assert_code("INVALID_CREATION", qualify_creation, fork["before_player"], "creation:again", owner_policy=case["player_policy"])
        existing = view_like(case, before=[case["world"], case["player"], case["component"]])
        self.assert_code("BRANCH_EXISTS", self.reduce, case, existing)

    def test_actual_player_fork_retains_memory_effects_and_parent_unchanged(self):
        root = root_case()
        original = copy.deepcopy(root["state"])
        fork = fork_case(root)
        state = fork["state"]
        self.assertEqual(original, root["state"])
        self.assertEqual([_head_of(root["component"])], state["branch"]["lineage"]["parents"])
        self.assertEqual("branch:left", state["branch_id"])
        namespaces = {row["namespace"] for row in state["branch"]["consumed"]}
        self.assertTrue({"action", "memory", "update", "effect", "branch_event"} <= namespaces)
        actual_actions = fork["after_player"]["state"]["records"]["origin:one"]["document"]["actions"]
        retained_actions = [row for row in state["branch"]["consumed"] if row["namespace"] == "action"]
        self.assertEqual(len(actual_actions), len(retained_actions))
        self.assertEqual(1, next(row for row in state["branch"]["current_slots"] if row["slot_id"] == "count")["value"]["value"])

    def test_labels_and_bookkeeping_without_semantic_effect_refuse(self):
        case = fork_case()
        self.assert_code("UNQUALIFIED_EFFECT", self.reduce, case, view_like(case, effects=[]))
        binding = copy.deepcopy(case["args"][3]["projections"][0])
        binding["target_id"] = "identity_state"
        self.assert_code("UNQUALIFIED_EFFECT", qualify_player_effect, binding, case["before_player"], case["after_player"], "update:left", owner_policy=case["root"]["player_policy"])
        binding["target_id"] = "current_leaf_branch_ref"
        self.assert_code("UNSUPPORTED_PROJECTION", qualify_player_effect, binding, case["before_player"], case["after_player"], "update:left", owner_policy=case["root"]["player_policy"])

    def test_single_option_choice_and_selected_action_mismatch_refuse(self):
        case = fork_case()
        args = copy.deepcopy(case["args"])
        update_record(args, "decision:left", lambda value: value.update(available_actions=["cross_threshold"]))
        self.assert_code("INVALID_POLICY", BranchStatePolicy, *args)
        policy, packet = rebuild(case, lambda args: update_record(args, "decision:left", lambda value: value.update(chosen_action="stay")))
        self.assert_code("UNQUALIFIED_CHOICE", policy.reduce, policy.initial_state(), packet, case["view"])

    def test_wrong_target_action_and_forged_effect_are_rejected(self):
        case = fork_case()
        actions = case["view"].actions()
        actions[0]["target_branch_id"] = "branch:elsewhere"
        self.assert_code("UNQUALIFIED_CHOICE", self.reduce, case, view_like(case, actions=actions))
        effects = case["view"].effects()
        effects[0]["source_occurrence_sha256"] = "0" * 64
        self.assert_code("UNQUALIFIED_EFFECT", self.reduce, case, view_like(case, effects=effects))

    def test_qualified_bridge_requires_real_action_history_and_consequence(self):
        case = fork_case()
        decision = copy.deepcopy(case["decision"])
        decision["chosen_action"] = "stay"
        self.assert_code("UNQUALIFIED_CHOICE", qualify_action, case["args"][3], decision,
            _head_of(case["root"]["component"]), case["before_player"], case["after_player"],
            decision["source_action_ref"], case["root"]["player_args"][7]["action"], owner_policy=case["root"]["player_policy"])
        after = copy.deepcopy(case["after_player"])
        after["state"]["records"]["consequence:left"]["document"]["action_refs"] = []
        after["state_sha256"] = _digest(after["state"])
        with self.assertRaises(JournalError):
            qualify_retention(case["before_player"], after, owner_policy=case["root"]["player_policy"])

    def test_retention_is_required_and_conflicting_origin_is_rejected(self):
        case = fork_case()
        self.assert_code("UNQUALIFIED_RETENTION", self.reduce, case, view_like(case, retentions=[]))
        retentions = case["view"].retentions()
        retentions[0]["consumed"][0]["payload_sha256"] = "0" * 64
        self.assert_code("UNQUALIFIED_RETENTION", self.reduce, case, view_like(case, retentions=retentions))
        retentions = case["view"].retentions()
        retentions[0]["consumed"][0]["origin_component_id"] = "component:foreign"
        self.assert_code("UNQUALIFIED_RETENTION", self.reduce, case, view_like(case, retentions=retentions))

    def test_imported_reservations_keep_anchor_without_invented_receipts(self):
        for adapter in ("closed_reference_v1", "historical_record_v1"):
            with self.subTest(adapter=adapter):
                raw, migration, result, args = imported_configuration(adapter, continuing=True)
                policy = PlayerStatePolicy.from_migration(result, migration, raw, *args)
                before = initial_component(BINDING, "component:player", policy.scope, policy.policy_id, policy.initial_state())
                state = policy.reduce(before["state"], policy.packet(PRINCIPAL, "request:second", "update:second"))
                after = step("component:player", state, policy.policy_id, policy.scope.to_record(), previous=before, request="after-import")
                bundle = qualify_retention(before, after, owner_policy=policy)
                anchor = result["baseline"]["import_baseline"]["import_anchor"]
                reservations = [row for row in bundle["consumed"] if row["origin_request_ref"] == anchor]
                self.assertTrue({"action", "memory", "update", "effect"} <= {row["namespace"] for row in reservations})
                self.assertTrue(all(row["origin_event_ref"] is None for row in reservations))
                self.assertFalse(any(row["origin_request_ref"] == anchor for row in bundle["occurrences"]))
                self.assert_code("INVALID_CREATION", qualify_creation, before, "creation:reset", owner_policy=policy)
    def test_stale_exact_player_head_refuses_even_same_state(self):
        case = fork_case()
        changed = step("component:player", case["before_player"]["state"], case["before_player"]["owner_policy_id"],
            case["before_player"]["scope"], previous=case["before_player"], request="unrelated")
        view = view_like(case, before=[case["root"]["component"], changed, case["root"]["world"]], snapshots=[case["root"]["component"], case["before_player"]])
        self.assert_code("STALE_COMPONENT", self.reduce, case, view)

    def test_foreign_private_and_observer_records_cannot_become_objective(self):
        case = fork_case()
        for source_scope in (scope("player_state", "player:other"), scope("player_perception", "observer:one")):
            args = copy.deepcopy(case["args"])
            next(row for row in args[5] if row["ref"] == "definition:count")["scope"] = source_scope
            policy = BranchStatePolicy(*args)
            self.assert_code("INVALID_SCOPE", policy.packet, PRINCIPAL, "request:probe", "proposal:left")

    def test_sources_grants_and_hostile_principals_do_not_gain_authority(self):
        case = fork_case()
        self.assert_code("UNAUTHORIZED", case["policy"].packet, BOOTSTRAP_PRINCIPAL, "request:x", "proposal:left")
        for principal in ({}, [], None):
            with self.assertRaises(JournalError):
                case["policy"].packet(principal, "request:x", "proposal:left")

    def test_selected_catalog_bytes_bound_but_unrelated_extension_keeps_packet(self):
        case = fork_case()
        args = copy.deepcopy(case["args"])
        args[5].append(reference("unused:ref", "unused"))
        policy = BranchStatePolicy(*args)
        self.assertEqual(case["policy"].policy_id, policy.policy_id)
        self.assertEqual(case["packet"], policy.packet(PRINCIPAL, "request:left", "proposal:left"))
        update_record(args, "location:one", lambda value: value.update(source_sha256="1" * 64))
        changed = BranchStatePolicy(*args)
        self.assert_code("PACKET_MISMATCH", changed.reduce, changed.initial_state(), case["packet"], case["view"])

    def test_detached_inputs_outputs_record_and_late_failure(self):
        case = fork_case()
        initial = case["policy"].initial_state()
        packet = copy.deepcopy(case["packet"])
        output = case["policy"].reduce(initial, packet, case["view"])
        output["branch"]["current_slots"].clear()
        self.assertIsNone(initial["branch"])
        self.assertEqual(case["packet"], packet)
        record = case["policy"].record("decision:left")
        record["document"]["available_actions"].clear()
        self.assertEqual(2, len(case["policy"].record("decision:left")["document"]["available_actions"]))
        retentions = case["view"].retentions()
        retentions[0]["occurrences"][0]["origin_request_ref"] = "forged:request"
        with self.assertRaises(JournalError):
            case["policy"].reduce(initial, packet, view_like(case, retentions=retentions))
        self.assertIsNone(initial["branch"])
        self.assertEqual(case["state"], case["policy"].reduce(initial, packet, case["view"]))

    def test_meaningful_disjoint_merge_is_deterministic_and_deduplicates_originals(self):
        case = merge_case()
        originals = copy.deepcopy([case["left"]["state"], case["right"]["state"]])
        state = self.reduce(case)
        self.assertEqual(state, self.reduce(case))
        self.assertEqual(originals, [case["left"]["state"], case["right"]["state"]])
        self.assertEqual("merge", state["branch"]["lineage"]["kind"])
        self.assertEqual(2, len(state["branch"]["lineage"]["parents"]))
        values = {row["slot_id"]: row["value"] for row in state["branch"]["current_slots"]}
        self.assertEqual({"count": {"kind": "integer", "value": 1}, "gate": {"kind": "token", "token": "open"}}, values)
        first = [row for row in state["branch"]["consumed"] if row["namespace"] == "action" and row["identity_parts"][-1] == "origin:first:action:0"]
        self.assertEqual(1, len(first))
        self.assertEqual({"event:left", "event:right", "event:merge"}, set(state["events"]))

    def test_identical_semantic_values_keep_both_distinct_events(self):
        root = root_case()
        left = fork_case(root, "left")
        right = fork_case(root, "right", {"count": {"kind": "integer", "value": 1}})
        case = merge_case(left, right)
        # Canonical parent order determines the retained equal-value source.
        args = copy.deepcopy(case["args"])
        update_record(args, "event:merge", lambda event: event["changes"][0].update(source_occurrence_ref="delta:left"))
        policy = BranchStatePolicy(*args)
        packet = policy.packet(MERGE_PRINCIPAL, "request:merge", "proposal:merge")
        state = policy.reduce(policy.initial_state(), packet, case["view"])
        self.assertTrue({"event:left", "event:right"} <= set(state["events"]))
        self.assertEqual(1, next(row for row in state["branch"]["current_slots"] if row["slot_id"] == "count")["value"]["value"])

    def test_conflicting_values_require_resolution_not_last_writer_or_average(self):
        root = root_case()
        case = merge_case(fork_case(root, "left"), fork_case(root, "right", {"count": {"kind": "integer", "value": 2}}))
        self.assert_code("MERGE_CONFLICT", self.reduce, case)

    def test_catalog_decision_and_old_slot_do_not_resolve_conflict(self):
        root = root_case()
        case = merge_case(fork_case(root, "left"), fork_case(root, "right", {"count": {"kind": "integer", "value": 2}}))
        args = copy.deepcopy(case["args"])
        decision = copy.deepcopy(case["left"]["decision"])
        decision["decision_ref"] = "decision:resolve"
        resolution = {"slot_id": "count", "base": {"present": True, "value": {"kind": "integer", "value": 0}},
            "left": {"present": True, "value": {"kind": "integer", "value": 1}},
            "right": {"present": True, "value": {"kind": "integer", "value": 2}},
            "result": {"present": True, "value": {"kind": "integer", "value": 1}},
            "reason_refs": ["reason:resolve"], "source_occurrence_ref": "delta:left"}
        args[5] += [qualified("decision:resolve", "decision", decision, scope(subject="branch:merge")),
            qualified("resolution:one", "resolution", resolution, scope(subject="branch:merge")),
            reference("reason:resolve", "reason", source_scope=scope("shared_worldstate", WORLD))]
        args[6][0]["operation"]["resolution_refs"] = ["resolution:one"]
        update_record(args, "event:merge", lambda event: event.update(decision_context="decision:resolve", resolution_refs=["resolution:one"]))
        policy = BranchStatePolicy(*args)
        packet = policy.packet(MERGE_PRINCIPAL, "request:merge", "proposal:merge")
        view = view_like(case, after=[case["left"]["after_world"]])
        self.assert_code("UNQUALIFIED_RESOLUTION", policy.reduce, policy.initial_state(), packet, view)

    def test_missing_and_wrong_common_base_refuse(self):
        case = merge_case()
        before = [case["left"]["component"], case["right"]["component"]]
        self.assert_code("UNAUTHORIZED_READ", self.reduce, case, view_like(case, before=before, snapshots=[]))
        args = copy.deepcopy(case["args"])
        wrong = args[6][0]["operation"]["parent_heads"][0]
        args[6][0]["operation"]["base_head"] = copy.deepcopy(wrong)
        heads = copy.deepcopy(args[6][0]["operation"]["parent_heads"]) + [_head_of(case["root"]["component"])]
        args[6][0]["expected_heads"] = copy.deepcopy(heads)
        update_record(args, "context:branch:merge", lambda context: context.update(read_heads=copy.deepcopy(heads)))
        update_record(args, "event:merge", lambda event: event.update(common_base=copy.deepcopy(wrong), read_heads=copy.deepcopy(heads)))
        policy = BranchStatePolicy(*args)
        packet = policy.packet(MERGE_PRINCIPAL, "request:merge", "proposal:merge")
        self.assert_code("INVALID_COMMON_BASE", policy.reduce, policy.initial_state(), packet, case["view"])

    def test_historical_base_is_not_confused_with_current_component_revision(self):
        case = merge_case()
        old = case["root"]["component"]
        current = step(old["component_id"], old["state"], old["owner_policy_id"], old["scope"], previous=old, request="later-root-head")
        requirements = case["policy"].requirements(case["packet"])
        self.assertEqual([_head_of(old)], requirements["historical_reads"])
        self.assertNotIn(old["component_id"], [head["component_id"] for head in requirements["reads"]])
        view = view_like(case, before=[case["left"]["component"], case["right"]["component"], current], snapshots=[old])
        self.assertEqual(self.reduce(case), self.reduce(case, view))
        missing = view_like(case, before=[case["left"]["component"], case["right"]["component"], current], snapshots=[])
        self.assert_code("UNKNOWN_COMPONENT_HEAD", self.reduce, case, missing)

    def test_current_read_vector_cannot_choose_between_two_heads_for_one_component(self):
        case = fork_case()
        args = copy.deepcopy(case["args"])
        old = _head_of(case["root"]["player"])
        args[6][0]["expected_heads"].append(old)
        update_record(args, "context:branch:left", lambda value: value["read_heads"].append(old))
        update_record(args, "event:left", lambda value: value["read_heads"].append(old))
        policy = BranchStatePolicy(*args)
        packet = policy.packet(PRINCIPAL, "request:left", "proposal:left")
        self.assert_code("INVALID_READ_SET", policy.requirements, packet)

    def test_intermediate_staged_ancestry_requires_authorized_exact_snapshots(self):
        case = merge_case()
        old = case["root"]["component"]
        middle = step(old["component_id"], old["state"], old["owner_policy_id"], old["scope"], previous=old, request="middle")
        current = step(old["component_id"], old["state"], old["owner_policy_id"], old["scope"], previous=middle, request="current")
        staged = copy.deepcopy([old, middle])
        view = view_like(case, before=[case["left"]["component"], case["right"]["component"], current], snapshots=[], staged_history=staged)
        self.assertEqual(self.reduce(case), self.reduce(case, view))
        self.assertEqual(middle, view.component_at(_head_of(middle)))
        staged[0]["state"]["branch"]["current_slots"].clear()
        self.assertEqual(old, view.component_at(_head_of(old)))
        self.assert_code("UNAUTHORIZED_READ", BranchReadView, WORLD, [], [], history(), [], [], staged_history=[old])
        self.assert_code("INVALID_VIEW", BranchReadView, WORLD, [current], [], history(), [], [], staged_history=[old, old])
        malformed = copy.deepcopy(old)
        malformed["state"]["branch"]["current_slots"].clear()
        self.assert_code("INVALID_VALUE", BranchReadView, WORLD, [current], [], history(), [], [], staged_history=[malformed])

    def test_presence_absence_and_empty_values_remain_distinct(self):
        self.assertNotEqual(_presence(None), _presence({"value": {"kind": "boolean", "value": False}}))
        self.assertNotEqual(_presence(None), _presence({"value": {"kind": "integer", "value": 0}}))
        self.assertNotEqual(_presence(None), _presence({"value": {"kind": "references", "refs": []}}))
        case = fork_case()
        args = copy.deepcopy(case["args"])
        args[6][0]["operation"]["changes"][0]["after"] = {"present": False}
        update_record(args, "event:left", lambda event: event["changes"][0].update(after={"present": False}))
        policy = BranchStatePolicy(*args)
        packet = policy.packet(PRINCIPAL, "request:left", "proposal:left")
        with self.assertRaises(JournalError):
            policy.reduce(policy.initial_state(), packet, case["view"])

    def test_occurrence_identity_conflict_and_order_cycle_refuse(self):
        self.assert_code("HISTORY_ORDER_CONFLICT", _ordered_union, ["one", "two"], ["two", "one"])
        self.assert_code("IDENTITY_CONFLICT", _ordered_union, [{"id": "one", "value": 1}],
            [{"id": "one", "value": 2}], lambda row: row["id"])

    def test_full_owner_limit_excludes_component_envelope(self):
        body = {"text": "x" * 65525}
        self.assertEqual(65536, len(_object_bytes(body)))
        component = initial_component(BINDING, "component:large", TruthScope(WORLD, "shared_worldstate", WORLD), "policy:large", body)
        view = BranchReadView(WORLD, [component], [], history([component]), [], [])
        self.assertEqual(component, view.component_at(_head_of(component)))
        self.assertEqual(component, view.before("component:large"))
        too_large = copy.deepcopy(component)
        too_large["state"]["text"] += "x"
        too_large["state_sha256"] = _digest(too_large["state"])
        self.assert_code("VALUE_LIMIT", BranchReadView, WORLD, [too_large], [], history(), [], [])

    def test_hostile_witness_rows_refuse_with_public_error(self):
        for value in (None, [], "not-a-row", {}):
            with self.assertRaises(JournalError):
                BranchReadView(WORLD, [], [], history(), [value], [])

    def test_offline_schema_boundary_rejects_unknown_ref_cycle_and_wrong_id(self):
        root = root_case()
        for change in (lambda s: s["context"]["$defs"].update(Bad={"$ref": "https://unprovided.invalid/schema"}),
                       lambda s: s["context"]["$defs"].update(Bad={"$ref": "#/$defs/Bad"}),
                       lambda s: s["event"].update({"$id": "https://wrong.invalid/schema"})):
            args = copy.deepcopy(root["args"])
            change(args[7])
            self.assert_code("INVALID_SCHEMA", BranchStatePolicy, *args)


if __name__ == "__main__":
    unittest.main()
