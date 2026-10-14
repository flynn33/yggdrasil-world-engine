"""Offline wire boundaries for profiles, typed updates and actual player snapshots."""

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from core.player_state import PlayerStateStore
from tests.m4_player_fixture import PRINCIPAL, configuration


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_NAMES = (
    "m4_player_profile", "m4_player_update", "m4_player_snapshot", "m4_player_runtime_state",
    "m4_origin_state", "celestial_identity_state", "player_agent_state", "player_branch_history",
    "m4_plane_attunement_state", "m4_bloodline_resonance_state", "m4_wolf_resonance_summary",
    "raven_companion_state", "m4_ability_state", "wolf_manifestation_event",
    "player_action_trace", "player_memory_record",
)


class PlayerWireSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = {name: json.loads((ROOT / "data/schemas" / (name + "_schema.json")).read_text(encoding="utf-8"))
                       for name in SCHEMA_NAMES}
        cls.retrieval_attempts = []

        def deny_retrieval(uri):
            cls.retrieval_attempts.append(uri)
            raise NoSuchResource(ref=uri)

        cls.registry = Registry(retrieve=deny_retrieval).with_resources(
            (schema["$id"], Resource.from_contents(schema)) for schema in cls.schemas.values())
        for schema in cls.schemas.values():
            Draft202012Validator.check_schema(schema)
        cls.validators = {name: Draft202012Validator(cls.schemas["m4_player_" + name], registry=cls.registry)
                          for name in ("profile", "update", "snapshot")}

    def reject(self, kind, value):
        self.assertFalse(self.validators[kind].is_valid(value), (kind, value))

    def snapshots(self):
        args = configuration()
        owner = PlayerStateStore(*args)
        snapshots = [owner.state()]
        for revision, update in enumerate(("update:first", "update:second")):
            owner.publish(owner.writer(PRINCIPAL), "request:" + str(revision), revision, update)
            snapshots.append(owner.state())
        return snapshots

    def test_explicit_offline_registry_validates_real_initial_and_two_committed_snapshots(self):
        args = configuration()
        self.validators["profile"].validate(args[2])
        for update in args[6]:
            self.validators["update"].validate(update)
        snapshots = self.snapshots()
        for snapshot in snapshots:
            self.validators["snapshot"].validate(snapshot)
        self.assertEqual("initial", snapshots[0]["spine"]["state_lifecycle"])
        self.assertEqual(2, len(snapshots[-1]["accepted_updates"]))
        self.assertEqual([], self.retrieval_attempts)

    def test_published_examples_are_actual_admitted_snapshot_and_selected_update(self):
        args = configuration()
        owner = PlayerStateStore(*args)
        for revision, name in enumerate(("first", "second")):
            owner.publish(owner.writer(PRINCIPAL), "request:" + name, revision, "update:" + name)
        snapshot = json.loads((ROOT / "examples/state_journal/player_aggregate.example.json").read_text(encoding="utf-8"))
        update = json.loads((ROOT / "examples/state_journal/player_update.example.json").read_text(encoding="utf-8"))
        self.assertEqual(owner.state(), snapshot)
        self.assertEqual(args[6][0], update)
        self.validators["snapshot"].validate(snapshot)
        self.validators["update"].validate(update)

    def test_profile_is_closed_with_complete_states_matching_reveals_and_forward_edges(self):
        base = configuration()[2]
        mutations = [lambda p: p.update(accepted=True), lambda p: p["ability_states"].pop(),
            lambda p: p["identity_reveal_statuses"].update(veiled="identity_integrated"),
            lambda p: p["identity_transitions"].append({"from_state": "integrated", "to_state": "veiled"}),
            lambda p: p["ability_transitions"].append({"from_state": "latent", "to_state": "latent"}),
            lambda p: p["reversible_slots"].append("celestial")]
        for mutate in mutations:
            value = copy.deepcopy(base)
            mutate(value)
            self.reject("profile", value)
        neutral = {**base, "profile_id": "other:profile", "raven_companion_id": "other:witness",
                   "wolf_companions": ["other:first", "other:second"]}
        self.validators["profile"].validate(neutral)

    def test_typed_update_rejects_generic_patch_flags_missing_conditions_and_unknown_collections(self):
        base = configuration()[6][0]
        operations = [
            {"kind": "patch", "path": "/identity", "value": "integrated"},
            {"kind": "replace", "slot": "celestial", "previous_ref": "old", "next_ref": "new"},
            {"kind": "append", "collection": "authority.engine", "refs": ["value"]},
            {"kind": "ability", "ability_id": "ability:one", "previous_ref": "old", "next_ref": "new", "condition_refs": [], "accepted": True},
        ]
        for operation in operations:
            value = copy.deepcopy(base)
            value["operations"] = [value["operations"][0], operation]
            self.reject("update", value)
        self.reject("update", {**base, "acceptance_status": "accepted"})

    def test_update_requires_one_origin_or_a_single_compensation(self):
        base = configuration()[6][0]
        for operations in ([], base["operations"][1:], [base["operations"][0]] * 2,
                           [base["operations"][0]] * 17):
            self.reject("update", {**base, "operations": operations})
        compensation = {"kind": "compensate", "target_request_ref": "request:prior", "reason_refs": ["reason:qualified"]}
        self.validators["update"].validate({**base, "operations": [compensation]})
        self.reject("update", {**base, "operations": [base["operations"][0], compensation]})
        self.reject("update", {**base, "operations": [{**compensation, "reason_refs": []}]})

    def test_branch_and_companion_operations_require_their_complete_closed_wire_fields(self):
        base = configuration()[6][0]
        operations = [
            {"kind": "branch", "previous_branch_ref": "branch:old", "next_branch_ref": "branch:new",
             "next_location_ref": "location:new", "agent_ref": "agent:new", "history_ref": "history:new", "event_ref": "event:branch"},
            {"kind": "manifest", "event_ref": "event:wolf"},
            {"kind": "dismiss", "event_ref": "event:wolf", "condition_ref": "condition:dismissal"},
        ]
        for operation in operations:
            value = {**base, "operations": [base["operations"][0], operation]}
            self.validators["update"].validate(value)
            missing = copy.deepcopy(operation)
            missing.pop(next(key for key in operation if key != "kind"))
            self.reject("update", {**value, "operations": [base["operations"][0], missing]})
            self.reject("update", {**value, "operations": [base["operations"][0], {**operation, "path": "/arbitrary"}]})
        branch = operations[0].copy()
        branch.pop("next_location_ref")
        self.reject("update", {**base, "operations": [base["operations"][0], branch]})

    def test_update_provenance_scope_and_identifiers_have_wire_boundaries(self):
        base = configuration()[6][0]
        mutations = [lambda p: p.update(player_id="player:one\n"), lambda p: p.update(source_system="host_adapter"),
            lambda p: p.update(evidence_refs=[]), lambda p: p.update(evidence_refs=["same", "same"]),
            lambda p: p["provenance"].pop("diagnostic_ref"),
            lambda p: p["provenance"].update(source_ash_refs=[]),
            lambda p: p["provenance"].update(authenticated=True)]
        for mutate in mutations:
            value = copy.deepcopy(base)
            mutate(value)
            self.reject("update", value)

    def test_snapshot_discriminates_document_kind_and_rejects_malformed_records(self):
        base = self.snapshots()[-1]
        mutations = [lambda p: p["records"]["celestial:initial"].update(kind="ability"),
            lambda p: p["records"]["celestial:initial"].update(document={}),
            lambda p: p["records"]["celestial:initial"].update(sha256="f" * 63),
            lambda p: p["records"]["celestial:initial"].update(sha256="F" * 64),
            lambda p: p["records"]["celestial:initial"].update(sha256="f" * 64 + "\n"),
            lambda p: p["records"]["celestial:initial"].update(accepted=True),
            lambda p: p["records"]["celestial:initial"]["document"].update(schema_version="unknown"),
            lambda p: p["records"]["raven:initial"]["document"].update(version="0.1.0"),
            lambda p: p["records"]["origin:one"]["document"].update(extra=True),
            lambda p: p.update(unknown=True)]
        for mutate in mutations:
            value = copy.deepcopy(base)
            mutate(value)
            self.reject("snapshot", value)

    def test_reference_and_consequence_records_are_closed_and_scoped(self):
        base = self.snapshots()[-1]
        mutations = [lambda p: p["records"]["evidence:play"]["document"].update(truth_scope="base_world_ontology"),
            lambda p: p["records"]["evidence:play"]["document"].update(source_sha256="not-a-digest"),
            lambda p: p["records"]["evidence:play"]["document"].update(accepted=True),
            lambda p: p["records"]["consequence:first"]["document"].pop("effect_id"),
            lambda p: p["records"]["consequence:first"]["document"].update(objective_effects="NONE"),
            lambda p: p["records"]["consequence:first"]["document"].update(action_refs=["same", "same"])]
        for mutate in mutations:
            value = copy.deepcopy(base)
            mutate(value)
            self.reject("snapshot", value)

    def test_effect_receipts_require_exact_shape_and_reversible_changes(self):
        base = self.snapshots()[-1]
        mutations = [lambda r: r.update(effect=["only", "two"]), lambda r: r.update(effect=["one", "two", "three", "four"]),
            lambda r: r.update(effect=["one", "two", False]), lambda r: r.update(accepted=True),
            lambda r: r.update(reversible=1), lambda r: r.update(reversible=True, changes=[]),
            lambda r: r.update(reversible=True, changes=[{"slot": "celestial", "before": "old", "after": "new"}]),
            lambda r: r.update(changes=[{"slot": "plane", "before": "old", "after": "new", "patch": {}}])]
        for mutate in mutations:
            value = copy.deepcopy(base)
            mutate(value["accepted_updates"][0])
            self.reject("snapshot", value)

    def test_compensation_record_is_closed_and_retains_target_and_reasons(self):
        base = self.snapshots()[-1]
        compensation = {"kind": "compensate", "target_request_ref": "request:1", "reason_refs": ["reason:qualified"]}
        value = {**base, "compensations": [compensation]}
        self.validators["snapshot"].validate(value)
        for bad in ({**compensation, "reason_refs": []}, {**compensation, "target_request_ref": None},
                    {**compensation, "erase_history": True}):
            self.reject("snapshot", {**base, "compensations": [bad]})


if __name__ == "__main__":
    unittest.main()
