"""Offline migration wire boundaries; structural examples confer no authority."""

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from core.player_state import PlayerStateStore
from tests.m4_player_fixture import PRINCIPAL, configuration, provenance
from tests.m4_player_migration_fixture import build


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_NAMES = (
    "m4_player_runtime_state_v3", "m4_player_snapshot_v2", "m4_player_update_v3",
    "m4_player_migration_result", "m4_origin_imported_state", "m4_origin_baseline",
    "m4_player_runtime_state", "m4_player_snapshot", "m4_player_update", "m4_origin_state",
    "celestial_identity_state", "player_agent_state", "player_branch_history",
    "m4_plane_attunement_state", "m4_bloodline_resonance_state", "m4_wolf_resonance_summary",
    "raven_companion_state", "m4_ability_state", "wolf_manifestation_event",
    "player_action_trace", "player_memory_record",
)
COLLECTIONS = (
    "branch_generation_context_refs", "branch_event_refs", "awakening_fragments",
    "narrative_memory_refs", "relationship_state_refs", "faction_stance_refs",
    "unresolved_tension_refs", "active_quest_refs", "completed_resolution_refs",
    "generation_context_refs",
)


class PlayerMigrationWireSchemaTests(unittest.TestCase):
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
        cls.validators = {name: Draft202012Validator(schema, registry=cls.registry)
                          for name, schema in cls.schemas.items()}

    def reject(self, name, value):
        self.assertFalse(self.validators[name].is_valid(value), (name, value))

    def context(self):
        return {
            "state_id": "state:historical", "sequence_id": -7,
            "phase_confidence": {"coefficient": "-12345678901234567891", "exponent": -19},
            "identity_reveal_policy": "reveal_through_play", "origin": "mortal",
            "celestial_memory": "veiled", "active_realm_form": "physical",
            "active_realm_form_ref": "realm:physical:one",
            "wolf_interpretation": "symbiotic_attractors_not_morality_meter",
            **{name: ["context:" + name] for name in COLLECTIONS},
            "perception_state_ref": "perception:one", "last_player_action_trace_ref": None,
            "authority_boundary": {"can_influence_generation_context": False,
                "may_mutate_ash_math": False, "may_rewrite_shared_world_truth": False,
                "may_mutate_base_world_ontology": False, "host_adapter_may_author": False},
            "ash_provenance": {**provenance(), "axiom_diagnostic_refs": ["axiom:one"],
                "pattern_vector_refs": ["pattern:one"], "existence_potential_ref": "potential:one"},
            "update_policy": {"requires_delta": True, "append_first_memory": True,
                "diagnostic_noop_allowed": False, "branch_event_required_for_branch_mutation": True},
        }

    def wire_result(self):
        """Build wire-only examples from a real initial state, without qualification."""
        snapshot = PlayerStateStore(*configuration()).state()
        snapshot["format"] = "ywe.player_aggregate.v2"
        spine = snapshot["spine"]
        spine.update(schema_id="ywe.player_runtime_state.v3", schema_version="3.0.0")
        spine["update_control"]["allowed_update_packet_schema"] = "ywe.player_state_update_packet.v3"
        spine["runtime_context"] = self.context()
        snapshot["records"]["realm:physical:one"] = {"kind": "realm_form", "sha256": "0" * 64,
            "document": {"form_name": "physical", "plane_id": "P1_Physical",
                         "truth_scope": "shared_worldstate", "subject_id": snapshot["world_id"],
                         "source_sha256": "a" * 64}}
        snapshot["import_baseline"] = {"source_sha256": "a" * 64, "import_anchor": "b" * 64,
            "consumed_update_refs": ["update:historical"], "consumed_request_refs": ["request:historical"],
            "consumed_effects": [{"update_ref": "update:historical", "consequence_ref": "consequence:historical",
                                  "effect": ["consequence:historical", "effect:historical", snapshot["player_id"]]}],
            "consumed_manifestation_event_ids": ["manifestation:historical"], "provenance": provenance()}
        origin = snapshot["records"][spine["origin_progression_state_ref"]]["document"]
        origin["format"] = "ywe.origin_progression.v2"
        origin["import_baseline"] = {"source_sha256": "a" * 64, "import_anchor": "b" * 64,
                                     "consumed_action_refs": [], "provenance": provenance()}
        baseline = {"format": "ywe.origin_baseline.v1", **{name: origin[name] for name in
            ("world_id", "player_id", "profile_id", "current_phase", "actions", "memories")},
            **origin["import_baseline"]}
        target_names = ("spine", "celestial", "agent", "branch_history", "plane", "bloodline", "wolf",
                        "raven", "ability", "manifestation", "action", "memory", "origin", "snapshot")
        return {"format": "ywe.player_state_migration.v1", "adapter_id": "historical_record_v1",
            "migration_id": "player.historical_record_v1.v1", "world_id": snapshot["world_id"],
            "player_id": snapshot["player_id"], "source_format": "PlayerRuntimeState", "source_version": "1.0.0",
            "source_sha256": "a" * 64,
            "source_schema_digests": {name: "c" * 64 for name in ("closed_reference_v1", "historical_record_v1")},
            "target_schema_digests": {name: "d" * 64 for name in target_names},
            "qualification_sha256": "e" * 64, "selected_record_sha256": {"celestial:initial": "f" * 64},
            "import_anchor": "b" * 64,
            "source_presence_map": {"/state_id": "present", "/last_player_action_trace_ref": "null"},
            "field_mapping_rows": [{"source_pointer": "/state_id", "target_pointer": "/baseline/spine/runtime_context/state_id", "operation": "copy"}],
            "decimal_conversion_rows": [
                {"source_pointer": "/phase_confidence", "target_pointer": "/baseline/spine/runtime_context/phase_confidence",
                 "source_decimal": "-1.2345678901234567891", "coefficient": "-12345678901234567891", "exponent": -19},
                {"source_pointer": "/realm_attunement/physical", "target_pointer": "/baseline/records/plane:initial/document",
                 "source_decimal": "1.0", "target_q6": 1000000}],
            "origin_baseline": baseline, "baseline": snapshot, "target_sha256": "0" * 64}

    def test_closed_wire_examples_resolve_all_domain_schemas_offline(self):
        result = self.wire_result()
        self.validators["m4_player_migration_result"].validate(result)
        self.validators["m4_player_snapshot_v2"].validate(result["baseline"])
        self.validators["m4_player_runtime_state_v3"].validate(result["baseline"]["spine"])
        self.assertEqual([], self.retrieval_attempts)

    def test_actual_initial_and_continuing_migration_outputs_validate_offline(self):
        for adapter in ("closed_reference_v1", "historical_record_v1"):
            for continuing in (False, True):
                with self.subTest(adapter=adapter, continuing=continuing):
                    raw, migration, result, args = build(adapter, continuing)
                    self.assertTrue(migration.verify(raw, result))
                    self.validators["m4_player_migration_result"].validate(result)
                    owner = PlayerStateStore.from_migration(result, migration, raw, *args)
                    self.assertEqual(result["baseline"], owner.state())
                    self.validators["m4_player_snapshot_v2"].validate(owner.state())
        self.assertEqual([], self.retrieval_attempts)

    def test_actual_imported_continuation_and_replay_keep_new_wire_contracts(self):
        for adapter in ("closed_reference_v1", "historical_record_v1"):
            with self.subTest(adapter=adapter):
                raw, migration, result, args = build(adapter, True)
                owner = PlayerStateStore.from_migration(result, migration, raw, *args)
                update = next(row for row in args[6] if row["update_ref"] == "update:second")
                self.validators["m4_player_update_v3"].validate(update)
                owner.publish(owner.writer(PRINCIPAL), "request:post-import", 0, "update:second")
                snapshot = owner.state()
                self.validators["m4_player_snapshot_v2"].validate(snapshot)
                restored = PlayerStateStore.load_migrated(*owner.checkpoint(), result, migration, raw, *args)
                self.assertEqual(owner.checkpoint(), restored.checkpoint())
                self.validators["m4_player_snapshot_v2"].validate(restored.state())
                self.assertEqual(1, len(snapshot["accepted_updates"]))
                self.assertEqual(["update:first"], snapshot["import_baseline"]["consumed_update_refs"])
                self.reject("m4_player_migration_result", {**result, "baseline": snapshot})

    def test_runtime_context_preserves_absence_null_safe_false_and_exact_decimal(self):
        spine = self.wire_result()["baseline"]["spine"]
        validate = self.validators["m4_player_runtime_state_v3"].validate
        validate(spine)
        absent = copy.deepcopy(spine)
        absent.pop("runtime_context")
        validate(absent)
        for context in ({}, {"last_player_action_trace_ref": None}, {"last_player_action_trace_ref": "action:last"},
                        {"phase_confidence": {"coefficient": "9", "exponent": 10000}},
                        {"sequence_id": -9007199254740991}):
            validate({**spine, "runtime_context": context})

    def test_runtime_context_rejects_unknown_fields_nested_extensions_and_unsafe_authority(self):
        base = self.wire_result()["baseline"]["spine"]
        mutations = [lambda c: c.update(active_extension={"enabled": True}),
            lambda c: c["ash_provenance"].update(unqualified_source="anything"),
            lambda c: c["ash_provenance"].pop("diagnostic_ref"),
            lambda c: c["authority_boundary"].update(host_adapter_may_author=True),
            lambda c: c["authority_boundary"].update(accepted=True),
            lambda c: c["update_policy"].update(append_first_memory=False),
            lambda c: c["update_policy"].pop("requires_delta"),
            lambda c: c.update(celestial_memory="fully_known"),
            lambda c: c.update(perception_state_ref=None),
            lambda c: c.update(sequence_id=9007199254740992),
            lambda c: c.update(active_quest_refs=["same", "same"])]
        for mutate in mutations:
            value = copy.deepcopy(base)
            mutate(value["runtime_context"])
            self.reject("m4_player_runtime_state_v3", value)

    def test_realm_form_name_and_binding_are_present_or_absent_together(self):
        spine = self.wire_result()["baseline"]["spine"]
        for context in ({}, {"active_realm_form": "physical", "active_realm_form_ref": "realm:physical:one"}):
            self.validators["m4_player_runtime_state_v3"].validate({**spine, "runtime_context": context})
        for context in ({"active_realm_form": "physical"}, {"active_realm_form_ref": "realm:physical:one"},
                        {"active_realm_form": "physical", "active_realm_form_ref": None},
                        {"active_realm_form": "physical", "active_realm_form_ref": ""},
                        {"active_realm_form": "physical", "active_realm_form_ref": "realm:physical:one\n"}):
            self.reject("m4_player_runtime_state_v3", {**spine, "runtime_context": context})

    def test_realm_form_records_are_closed_and_only_allow_objective_scopes(self):
        baseline = self.wire_result()["baseline"]
        for scope, subject in (("shared_worldstate", baseline["world_id"]), ("leaf_branch_state", "branch:one")):
            value = copy.deepcopy(baseline)
            value["records"]["realm:physical:one"]["document"].update(truth_scope=scope, subject_id=subject)
            self.validators["m4_player_snapshot_v2"].validate(value)
        for field, bad in (("form_name", ""), ("plane_id", False), ("subject_id", None),
                           ("source_sha256", "a" * 63), ("source_sha256", "A" * 64),
                           ("source_sha256", "a" * 64 + "\n"), ("truth_scope", "player_state"),
                           ("truth_scope", "player_perception"), ("truth_scope", "realm_local"),
                           ("accepted", True)):
            value = copy.deepcopy(baseline)
            value["records"]["realm:physical:one"]["document"][field] = bad
            self.reject("m4_player_snapshot_v2", value)
        for field in ("form_name", "plane_id", "truth_scope", "subject_id", "source_sha256"):
            value = copy.deepcopy(baseline)
            value["records"]["realm:physical:one"]["document"].pop(field)
            self.reject("m4_player_snapshot_v2", value)
        for kind in ("reference", "realm_shift_proposal"):
            value = copy.deepcopy(baseline)
            value["records"]["realm:physical:one"]["kind"] = kind
            self.reject("m4_player_snapshot_v2", value)
        old = PlayerStateStore(*configuration()).state()
        old["records"]["realm:physical:one"] = baseline["records"]["realm:physical:one"]
        self.reject("m4_player_snapshot", old)

    def test_imported_branch_operation_accepts_only_typed_optional_realm_binding(self):
        update = configuration()[6][0]
        origin = update["operations"][0]
        branch = {"kind": "branch", "previous_branch_ref": "branch:one", "next_branch_ref": "branch:two",
                  "next_location_ref": "location:two", "agent_ref": "agent:two", "history_ref": "history:two",
                  "event_ref": "event:two"}
        for operation in (branch, {**branch, "next_realm_form_ref": "realm:physical:two"}):
            self.validators["m4_player_update_v3"].validate({**update, "operations": [origin, operation]})
        bound = {**branch, "next_realm_form_ref": "realm:physical:two"}
        self.reject("m4_player_update", {**update, "operations": [origin, bound]})
        for bad in (None, "", [], {"accepted": True}, "realm:physical:two\n"):
            self.reject("m4_player_update_v3", {**update, "operations": [origin, {**branch, "next_realm_form_ref": bad}]})
        self.reject("m4_player_update_v3", {**update, "operations": [origin, {**bound, "next_realm_form": "physical"}]})

    def test_confidence_requires_canonical_finite_coefficient_and_bounded_exponent(self):
        base = self.wire_result()["baseline"]["spine"]
        values = [{"coefficient": c, "exponent": 0} for c in ("-0", "00", "+1", "10", "1.5", "NaN", "1\n", "9" * 129)]
        values += [{"coefficient": "0", "exponent": 1}, {"coefficient": "1", "exponent": 10001},
                   {"coefficient": "1", "exponent": 0, "rounded": True}]
        for value in values:
            self.reject("m4_player_runtime_state_v3", {**base, "runtime_context": {"phase_confidence": value}})

    def test_context_operation_is_closed_requires_qualified_conditions_and_origin(self):
        base = configuration()[6][0]
        origin = base["operations"][0]
        context = {"kind": "context", "context_ref": "context:quest", "condition_refs": ["evidence:play"]}
        self.validators["m4_player_update_v3"].validate({**base, "operations": [origin, context]})
        for bad in ({"kind": "context", "context_ref": "context:quest"},
                    {**context, "condition_refs": []}, {**context, "path": "/anything"},
                    {**context, "value": {"approved": True}}, {**context, "condition_refs": ["same", "same"]}):
            self.reject("m4_player_update_v3", {**base, "operations": [origin, bad]})
        self.reject("m4_player_update_v3", {**base, "operations": [context]})

    def test_context_record_values_are_typed_by_explicit_mutable_field(self):
        base = self.wire_result()["baseline"]
        values = {name: value for name, value in self.context().items()
                  if name in COLLECTIONS + ("phase_confidence", "celestial_memory", "active_realm_form",
                                            "active_realm_form_ref", "perception_state_ref")}
        for field, value in values.items():
            document = {"field": field, "previous_value": value, "value": value, "phase": "first_stirrings"}
            snapshot = copy.deepcopy(base)
            snapshot["records"]["context:one"] = {"kind": "context", "document": document, "sha256": "0" * 64}
            self.validators["m4_player_snapshot_v2"].validate(snapshot)
            document["value"] = True
            self.reject("m4_player_snapshot_v2", snapshot)
        for document in ({"field": "authority_boundary", "previous_value": {}, "value": {}, "phase": "first_stirrings"},
                         {"field": "active_quest_refs", "previous_value": [], "value": [], "phase": "first_stirrings", "accepted": True},
                         {"field": "active_quest_refs", "value": [], "phase": "first_stirrings"}):
            snapshot = copy.deepcopy(base)
            snapshot["records"]["context:one"] = {"kind": "context", "document": document, "sha256": "0" * 64}
            self.reject("m4_player_snapshot_v2", snapshot)

    def test_only_quest_and_tension_context_records_accept_closed_reasoned_resolution(self):
        base = self.wire_result()["baseline"]
        resolution = {"removed_refs": ["active:old"], "action_refs": ["action:resolution"],
                      "reason_refs": ["evidence:resolution"], "disposition": "resolved"}
        for field in ("active_quest_refs", "unresolved_tension_refs"):
            document = {"field": field, "previous_value": ["active:old"], "value": [],
                        "phase": "first_stirrings", "resolution": resolution}
            value = copy.deepcopy(base)
            value["records"]["context:resolution"] = {"kind": "context", "document": document, "sha256": "0" * 64}
            self.validators["m4_player_snapshot_v2"].validate(value)
            for bad in ({**resolution, "removed_refs": []}, {**resolution, "action_refs": []},
                        {**resolution, "reason_refs": ["same", "same"]}, {**resolution, "disposition": "erase"},
                        {**resolution, "accepted": True}):
                document["resolution"] = bad
                self.reject("m4_player_snapshot_v2", value)
            document["resolution"] = resolution
            document["field"] = "narrative_memory_refs"
            self.reject("m4_player_snapshot_v2", value)

    def test_snapshot_requires_imported_origin_and_preserves_old_dialect_boundary(self):
        old = PlayerStateStore(*configuration()).state()
        new = self.wire_result()["baseline"]
        self.validators["m4_player_snapshot"].validate(old)
        self.reject("m4_player_snapshot_v2", old)
        self.reject("m4_player_snapshot", new)
        origin_ref = new["spine"]["origin_progression_state_ref"]
        new["records"][origin_ref] = old["records"][origin_ref]
        self.reject("m4_player_snapshot_v2", new)

    def test_import_reservations_require_complete_closed_separate_ledgers(self):
        base = self.wire_result()["baseline"]
        mutations = [lambda b: b.pop("consumed_request_refs"), lambda b: b.update(consumed_update_refs=["same", "same"]),
            lambda b: b.update(consumed_manifestation_event_ids=[False]), lambda b: b.update(trusted=True),
            lambda b: b.update(import_anchor="B" * 64), lambda b: b.update(source_sha256="a" * 64 + "\n"),
            lambda b: b["consumed_effects"][0].update(effect=["one", "two"]),
            lambda b: b["consumed_effects"][0].update(reversible=True),
            lambda b: b["consumed_effects"][0].pop("consequence_ref")]
        for mutate in mutations:
            value = copy.deepcopy(base)
            mutate(value["import_baseline"])
            self.reject("m4_player_snapshot_v2", value)

    def test_result_closes_discriminators_digest_tables_and_receipt_fields(self):
        base = self.wire_result()
        mutations = [lambda r: r.update(accepted=True), lambda r: r.pop("origin_baseline"),
            lambda r: r.update(adapter_id="infer_from_source"), lambda r: r.update(source_version="0.1.0"),
            lambda r: r.update(migration_id="player.closed_reference_v1.v1"),
            lambda r: r["source_schema_digests"].pop("closed_reference_v1"),
            lambda r: r["target_schema_digests"].update(unknown="a" * 64),
            lambda r: r["selected_record_sha256"].update({"record:one": "not-a-sha256"}),
            lambda r: r.update(qualification_sha256="a" * 63)]
        for mutate in mutations:
            value = copy.deepcopy(base)
            mutate(value)
            self.reject("m4_player_migration_result", value)

    def test_result_mapping_and_decimal_rows_are_closed_and_unambiguous(self):
        base = self.wire_result()
        mutations = [lambda r: r["source_presence_map"].update({"/field": "absent"}),
            lambda r: r["source_presence_map"].update({"/bad~2escape": "present"}),
            lambda r: r["field_mapping_rows"][0].update(operation="guess"),
            lambda r: r["field_mapping_rows"][0].update(accepted=True),
            lambda r: r["decimal_conversion_rows"][0].update(target_q6=123),
            lambda r: r["decimal_conversion_rows"][0].update(coefficient="10"),
            lambda r: r["decimal_conversion_rows"][0].update(source_decimal="Infinity"),
            lambda r: r["decimal_conversion_rows"][1].update(target_q6=1000001),
            lambda r: r["decimal_conversion_rows"][1].update(target_q6=1.2)]
        for mutate in mutations:
            value = copy.deepcopy(base)
            mutate(value)
            self.reject("m4_player_migration_result", value)
        normalized = copy.deepcopy(base)
        normalized["decimal_conversion_rows"][0].update(source_decimal="9E+10000", coefficient="9", exponent=10000)
        self.validators["m4_player_migration_result"].validate(normalized)


if __name__ == "__main__":
    unittest.main()
