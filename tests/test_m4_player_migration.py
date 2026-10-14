"""Lossless source projection and hostile-input boundaries for player imports."""

import copy
from decimal import localcontext
import hashlib
import json
import unittest

from core.player_state_migration import PlayerStateMigration
from core.state_migration import MigrationError
from tests.m4_player_fixture import BRANCH, record, reference
from tests.m4_player_migration_fixture import build, encode, inputs


class PlayerMigrationTests(unittest.TestCase):
    def migration(self, values, raw=None):
        original, sources, targets, resolution, _ = values
        raw = original if raw is None else raw
        resolution["source_sha256"] = hashlib.sha256(raw).hexdigest()
        adapter = "historical_record_v1" if b'"record_type"' in raw else "closed_reference_v1"
        migration = PlayerStateMigration(adapter, sources, targets, resolution)
        return migration, migration.migrate(raw)

    def reject(self, values, raw=None, code=None):
        with self.assertRaises(MigrationError) as caught:
            self.migration(values, raw)
        if code:
            self.assertEqual(code, caught.exception.code)

    def test_both_source_adapters_preserve_initial_and_continuing_live_state(self):
        for adapter in ("closed_reference_v1", "historical_record_v1"):
            for continuing in (False, True):
                with self.subTest(adapter=adapter, continuing=continuing):
                    raw, migration, result, _ = build(adapter, continuing)
                    self.assertTrue(migration.verify(raw, result))
                    origin = result["baseline"]["records"]["origin:one"]["document"]
                    self.assertEqual("veiled", origin["creation"]["identity_status"])
                    self.assertEqual("first_stirrings" if continuing else "mortal_unknowing", origin["current_phase"])
                    self.assertEqual([], origin["advances"])
                    self.assertEqual(2 if continuing else 0, len(origin["actions"]))
                    self.assertEqual([], result["baseline"]["accepted_updates"])
                    self.assertEqual(["update:first"] if continuing else [], result["baseline"]["import_baseline"]["consumed_update_refs"])

    def test_closed_optional_absence_is_not_materialized(self):
        values = inputs()
        source, spine = json.loads(values[0]), values[3]["spine"]
        for key in ("progression_refs", "relationship_links", "manifestation_links", "current_location_ref"):
            source.pop(key)
            spine.pop(key)
        for obj in (source, spine):
            obj["memory_refs"] = {}
            for key in ("pending_update_packet_refs", "accepted_update_packet_refs", "rejected_update_packet_refs"):
                obj["update_control"].pop(key)
            for key in ("recovery_status", "schema_version_history"):
                obj["asp_resilience"].pop(key)
        agent = next(row for row in values[3]["records"] if row["ref"] == "agent:initial")
        agent["document"].pop("current_location_ref")
        _, result = self.migration(values, encode(source))
        self.assertEqual(spine, result["baseline"]["spine"])
        self.assertNotIn("/progression_refs", result["source_presence_map"])
        self.assertNotIn("accepted_update_packet_refs", result["baseline"]["spine"]["update_control"])

    def test_closed_preserves_optional_group_order_and_resilience_history(self):
        values = inputs("closed_reference_v1", True)
        source, resolution = json.loads(values[0]), values[3]
        for obj in (source, resolution["spine"]):
            obj["relationship_links"]["npc_relationship_refs"] = ["relationship:z", "relationship:a"]
            obj["asp_resilience"]["state_integrity_status"] = "requires_review"
            obj["asp_resilience"]["recovery_status"] = "contained_for_review"
            obj["asp_resilience"]["schema_version_history"] = ["0.0.2", "0.0.1", "0.1.0"]
            obj["update_control"]["pending_update_packet_refs"] = ["update:pending"]
            obj["update_control"]["rejected_update_packet_refs"] = ["update:rejected"]
        resolution["records"].extend([reference("relationship:z", "npc_relationship_refs"),
            reference("relationship:a", "npc_relationship_refs"), reference("update:pending", "pending_update_packet_refs"),
            reference("update:rejected", "rejected_update_packet_refs")])
        _, result = self.migration(values, encode(source))
        for group in ("relationship_links", "asp_resilience"):
            self.assertEqual(source[group], result["baseline"]["spine"][group])
        resolution["spine"]["relationship_links"]["npc_relationship_refs"].reverse()
        self.reject(values, encode(source), "INCONSISTENT_BASELINE")

    def test_historical_fields_remain_live_with_exact_collection_order_and_all_provenance(self):
        raw, _, result, _ = build("historical_record_v1", True)
        source, context = json.loads(raw), result["baseline"]["spine"]["runtime_context"]
        for field in ("active_quest_refs", "unresolved_tension_refs", "narrative_memory_refs", "generation_context_refs",
                      "ash_provenance", "authority_boundary", "update_policy", "last_player_action_trace_ref"):
            self.assertEqual(source[field], context[field])
        self.assertEqual(["quest:second", "quest:first"], context["active_quest_refs"])
        self.assertEqual(12, context["sequence_id"])
        self.assertEqual(7, len(context["ash_provenance"]))
        self.assertTrue(set(result["source_presence_map"]) <= {row["source_pointer"] for row in result["field_mapping_rows"]})

    def test_historical_absent_action_is_distinct_from_explicit_null(self):
        values = inputs("historical_record_v1")
        _, original = self.migration(values)
        self.assertIsNone(original["baseline"]["spine"]["runtime_context"]["last_player_action_trace_ref"])
        self.assertEqual("null", original["source_presence_map"]["/last_player_action_trace_ref"])
        source = json.loads(values[0])
        source.pop("last_player_action_trace_ref")
        values[3]["spine"]["runtime_context"].pop("last_player_action_trace_ref")
        _, result = self.migration(values, encode(source))
        self.assertNotIn("last_player_action_trace_ref", result["baseline"]["spine"]["runtime_context"])
        self.assertNotIn("/last_player_action_trace_ref", result["source_presence_map"])

    def test_exact_confidence_is_not_q6_and_ignores_ambient_decimal_precision(self):
        values = inputs("historical_record_v1")
        raw = values[0].replace(b'"phase_confidence":1.0', b'"phase_confidence":-1.234567890123456789e-7')
        values[3]["spine"]["runtime_context"]["phase_confidence"] = {"coefficient": "-1234567890123456789", "exponent": -25}
        with localcontext() as context:
            context.prec = 2
            _, result = self.migration(values, raw)
        self.assertEqual({"coefficient": "-1234567890123456789", "exponent": -25}, result["baseline"]["spine"]["runtime_context"]["phase_confidence"])
        conversion = next(row for row in result["decimal_conversion_rows"] if row["source_pointer"] == "/phase_confidence")
        self.assertEqual("-1.234567890123456789E-7", conversion["source_decimal"])

    def test_negative_zero_confidence_has_exact_canonical_zero(self):
        values = inputs("historical_record_v1")
        raw = values[0].replace(b'"phase_confidence":1.0', b'"phase_confidence":-0.000')
        values[3]["spine"]["runtime_context"]["phase_confidence"] = {"coefficient": "0", "exponent": 0}
        _, result = self.migration(values, raw)
        self.assertEqual({"coefficient": "0", "exponent": 0}, result["baseline"]["spine"]["runtime_context"]["phase_confidence"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), result["source_sha256"])

    def test_confidence_supports_adopted_large_exponents_without_changing_q6(self):
        for exponent in (-10000, 2000, 10000):
            values = inputs("historical_record_v1")
            raw = values[0].replace(b'"phase_confidence":1.0', ('"phase_confidence":1e' + str(exponent)).encode())
            values[3]["spine"]["runtime_context"]["phase_confidence"] = {"coefficient": "1", "exponent": exponent}
            _, result = self.migration(values, raw)
            self.assertEqual(exponent, result["baseline"]["spine"]["runtime_context"]["phase_confidence"]["exponent"])
        values = inputs("historical_record_v1")
        raw = values[0].replace(b'"phase_confidence":1.0', b'"phase_confidence":1e10001')
        self.reject(values, raw, "INVALID_SOURCE")

    def test_integer_spelling_of_exact_confidence_is_not_limited_to_journal_integer_range(self):
        values = inputs("historical_record_v1")
        raw = values[0].replace(b'"phase_confidence":1.0', b'"phase_confidence":10000000000000000')
        values[3]["spine"]["runtime_context"]["phase_confidence"] = {"coefficient": "1", "exponent": 16}
        _, result = self.migration(values, raw)
        self.assertEqual({"coefficient": "1", "exponent": 16}, result["baseline"]["spine"]["runtime_context"]["phase_confidence"])

    def test_hostile_exponent_token_reports_stable_failure_even_with_decimal_trap(self):
        for token in (b"1e" + b"9" * 120, b"1e-" + b"9" * 119):
            values = inputs("historical_record_v1")
            raw = values[0].replace(b'"phase_confidence":1.0', b'"phase_confidence":' + token)
            self.reject(values, raw, "INVALID_SOURCE")

    def test_sparse_scores_require_complete_matching_records_without_filling_omissions(self):
        values = inputs("historical_record_v1")
        source = json.loads(values[0])
        self.assertEqual(2, len(source["realm_attunement"]))
        _, result = self.migration(values)
        self.assertEqual(9, len(result["baseline"]["records"]["plane:initial"]["document"]["planes"]))
        source["realm_attunement"]["physical"] = 0.010001
        self.reject(values, encode(source), "INCONSISTENT_BASELINE")
        source["realm_attunement"]["physical"] = 0.0100001
        self.reject(values, encode(source), "UNREPRESENTABLE_SCORE")
        values[3]["records"] = [row for row in values[3]["records"] if row["ref"] != "plane:initial"]
        self.reject(values, code="UNRESOLVED_REFERENCE")

    def test_explicit_bloodline_sparse_score_map_is_reconciled_and_structured_map_rejected(self):
        values = inputs("historical_record_v1")
        source = json.loads(values[0])
        source["bloodline_resonance"] = {"lineage:seed": 0.01}
        _, result = self.migration(values, encode(source))
        row = next(row for row in result["decimal_conversion_rows"] if row["source_pointer"] == "/bloodline_resonance/lineage:seed")
        self.assertEqual(10000, row["target_q6"])
        source["bloodline_resonance"]["lineage:seed"] = {"score": 0.01}
        self.reject(values, encode(source), "INVALID_SOURCE")

    def test_realm_mapping_is_explicit_and_bound_to_profile(self):
        values = inputs("historical_record_v1")
        values[3]["realm_name_map"]["profile_id"] = "other:profile"
        self.reject(values, code="INVALID_QUALIFICATION")
        values[3]["realm_name_map"]["profile_id"] = values[3]["player_profile"]["profile_id"]
        values[3]["realm_name_map"]["mappings"].pop("physical")
        self.reject(values, code="INVALID_QUALIFICATION")

    def test_unknown_historical_fields_and_nested_extensions_do_not_become_archival_success(self):
        mutations = [lambda source: source.update(active_skill_refs=[]), lambda source: source.update(wolf_interpretation="new"),
            lambda source: source["wolf_resonance"].update(moral_score=0),
            lambda source: source["ash_provenance"].update(extra_ref="extra:active")]
        for mutate in mutations:
            values = inputs("historical_record_v1")
            source = json.loads(values[0])
            mutate(source)
            with self.subTest(source=source.keys()):
                self.reject(values, encode(source), "UNKNOWN_ACTIVE_FIELD")

    def test_safe_false_declarations_are_preserved_but_authority_escalation_is_refused(self):
        values = inputs("historical_record_v1")
        source = json.loads(values[0])
        context = values[3]["spine"]["runtime_context"]
        for obj in (source, context):
            obj["authority_boundary"]["can_influence_generation_context"] = False
            obj["update_policy"]["diagnostic_noop_allowed"] = False
        _, result = self.migration(values, encode(source))
        self.assertFalse(result["baseline"]["spine"]["runtime_context"]["authority_boundary"]["can_influence_generation_context"])
        source["authority_boundary"]["host_adapter_may_author"] = True
        self.reject(values, encode(source), "INVALID_SOURCE")

    def test_historical_label_interpretation_is_explicit_and_matches_current_identity(self):
        values = inputs("historical_record_v1", True)
        source = json.loads(values[0])
        source["celestial_memory"] = "ancient_recalled"
        self.reject(values, encode(source), "INVALID_SOURCE")
        source["celestial_memory"] = "veiled"
        self.reject(values, encode(source), "INCONSISTENT_BASELINE")

    def test_missing_or_mismatched_consumption_qualification_cannot_reset_history(self):
        values = inputs("closed_reference_v1", True)
        values[3].pop("consumed_action_refs")
        self.reject(values, code="INVALID_QUALIFICATION")
        values = inputs("closed_reference_v1", True)
        values[3]["consumed_updates"] = []
        self.reject(values, code="INVALID_QUALIFICATION")
        values = inputs("closed_reference_v1", True)
        values[3]["consumed_action_refs"].append("action:missing")
        self.reject(values, code="INVALID_QUALIFICATION")
        values = inputs("closed_reference_v1", True)
        values[3]["creation"]["identity_status"] = "suspected"
        self.reject(values, code="INVALID_QUALIFICATION")

    def test_source_initial_lifecycle_cannot_smuggle_continuing_history(self):
        values = inputs("closed_reference_v1", True)
        source = json.loads(values[0])
        for obj in (source, values[3]["spine"]):
            obj["state_lifecycle"] = "initial"
            obj["identity"]["celestial_identity_initial_state"] = "veiled"
        self.reject(values, encode(source))

    def test_open_historical_sequence_cannot_alias_boolean_or_decimal_to_integer(self):
        for value in (True, 1.0):
            values = inputs("historical_record_v1")
            source = json.loads(values[0])
            source["sequence_id"] = value
            values[3]["spine"]["runtime_context"]["sequence_id"] = 1
            self.reject(values, encode(source), "INVALID_SOURCE")

    def test_active_context_and_provenance_cannot_promote_perception_records(self):
        for category in ("active_quest_refs", "pattern_vector_refs"):
            values = inputs("historical_record_v1", True)
            row = next(row for row in values[3]["records"] if row["kind"] == "reference" and row["document"]["category"] == category)
            row["document"]["truth_scope"] = "player_perception"
            self.reject(values, code="INVALID_QUALIFICATION")

    def test_invalid_catalog_document_returns_stable_refusal(self):
        values = inputs()
        values[3]["records"][0]["document"] = []
        self.reject(values, code="INVALID_QUALIFICATION")

    def test_duplicate_reference_collection_is_rejected_without_silent_deduplication(self):
        values = inputs("closed_reference_v1", True)
        source = json.loads(values[0])
        for obj in (source, values[3]["spine"]):
            obj["relationship_links"]["npc_relationship_refs"] = ["npc:one", "npc:one"]
        values[3]["records"].append(reference("npc:one", "npc_relationship_refs"))
        self.reject(values, encode(source), "INVALID_QUALIFICATION")

    def test_consumed_consequence_results_match_actions_and_objective_reference_scope(self):
        values = inputs("closed_reference_v1", True)
        resolution = values[3]
        consequence = next(row for row in resolution["records"] if row["ref"] == "consequence:first")["document"]
        consequence["external_result_refs"] = ["result:one"]
        resolution["records"].append(reference("result:one", "worldstate_delta_refs", "leaf_branch_state", BRANCH))
        self.reject(values, code="INVALID_QUALIFICATION")
        action = next(row for row in resolution["records"] if row["ref"] == resolution["action_refs"][0])["document"]
        action["resulting_worldstate_delta_refs"] = ["result:one"]
        _, result = self.migration(values)
        self.assertIn("result:one", result["selected_record_sha256"])
        terminal = next(row for row in resolution["records"] if row["ref"] == "result:one")["document"]
        terminal.update(truth_scope="player_perception", subject_id=resolution["player_id"])
        self.reject(values, code="INVALID_QUALIFICATION")

    def test_retained_action_event_and_result_refs_resolve_even_outside_receipt_subset(self):
        values = inputs("closed_reference_v1", True)
        resolution = values[3]
        action = next(row for row in resolution["records"] if row["ref"] == resolution["action_refs"][0])["document"]
        action.update(significance="branch_forming", branch_relevance="branch_event_created", branch_event_ref="event:historic")
        self.reject(values, code="UNRESOLVED_REFERENCE")
        resolution["records"].append(reference("event:historic", "branch_event_ref", "leaf_branch_state", "branch:historic", "branch:historic"))
        _, result = self.migration(values)
        self.assertIn("event:historic", result["selected_record_sha256"])
        action["resulting_worldstate_delta_refs"] = ["result:historic"]
        # This action is retained but omitted from the selected consequence's
        # action subset, so its own reference closure must still be checked.
        consequence = next(row for row in resolution["records"] if row["ref"] == "consequence:first")["document"]
        consequence["action_refs"].remove(action["action_trace_id"])
        self.reject(values, code="UNRESOLVED_REFERENCE")
        resolution["records"].append(reference("result:historic", "worldstate_delta_refs", "leaf_branch_state", BRANCH))
        _, result = self.migration(values)
        self.assertIn("result:historic", result["selected_record_sha256"])

    def test_manifestation_consumption_uses_explicit_binding_not_catalog_alias_order(self):
        from tests.test_m4_player_state import manifestation

        values = inputs("closed_reference_v1", True)
        resolution, event = values[3], manifestation()
        resolution["records"].append(record("z:historical:event", "manifestation", event))
        resolution["consumed_manifestation_event_ids"] = [event["manifestation_event_id"]]
        resolution["manifestation_bindings"] = [{"manifestation_event_id": event["manifestation_event_id"], "record_ref": "z:historical:event"}]
        _, first = self.migration(values)
        resolution["records"].append(record("a:unused:event:alias", "manifestation", event))
        _, second = self.migration(values)
        self.assertEqual(first, second)
        resolution["manifestation_bindings"] = []
        self.reject(values, code="INVALID_QUALIFICATION")

    def test_source_and_result_are_bound_to_exact_bytes_without_aliases(self):
        values = inputs()
        raw, sources, targets, resolution, _ = values
        migration, result = self.migration(values)
        original = copy.deepcopy(result)
        sources["closed_reference_v1"]["title"] = "mutated"
        targets["spine"]["title"] = "mutated"
        resolution["spine"]["player_id"] = "other:player"
        detached = migration.resolution()
        detached["spine"]["player_id"] = "other:player"
        self.assertTrue(migration.verify(raw, original))
        self.assertFalse(migration.verify(raw + b" ", original))
        result["baseline"]["spine"]["player_id"] = "other:player"
        self.assertFalse(migration.verify(raw, result))
        self.assertEqual(original, migration.migrate(raw))

    def test_unused_catalog_extension_does_not_change_selected_bindings(self):
        values = inputs()
        _, original = self.migration(values)
        values[3]["records"].append(reference("unused:one", "quest_history_refs"))
        _, extended = self.migration(values)
        self.assertEqual(original, extended)
        selected = next(row for row in values[3]["records"] if row["ref"] == "diagnostic:initial")
        selected["document"]["source_sha256"] = "b" * 64
        _, changed = self.migration(values)
        self.assertNotEqual(original["import_anchor"], changed["import_anchor"])

    def test_changed_schemas_and_profile_are_bound_without_rewriting_legacy_files(self):
        values = inputs()
        migration, result = self.migration(values)
        values[2]["spine"]["title"] += " qualified variant"
        changed, _ = self.migration(values)
        self.assertFalse(changed.verify(values[0], result))
        self.assertTrue(migration.verify(values[0], result))

    def test_foreign_scope_wrong_reference_category_and_missing_raven_refuse(self):
        for mutation in (lambda rows: rows[0].update(player_id="player:other"),
                         lambda rows: next(row for row in rows if row["ref"] == "identity:mortal")["document"].update(truth_scope="shared_worldstate"),
                         lambda rows: rows.remove(next(row for row in rows if row["ref"] == "raven:initial"))):
            values = inputs()
            mutation(values[3]["records"])
            self.reject(values)

    def test_schema_resolution_is_offline_and_rejects_unknown_refs_and_cycles(self):
        values = inputs()
        values[2]["spine"]["properties"]["player_id"] = {"$ref": "https://untrusted.invalid/source.json"}
        self.reject(values, code="INVALID_QUALIFICATION")
        values = inputs()
        values[1]["closed_reference_v1"] = []
        self.reject(values, code="INVALID_QUALIFICATION")
        values = inputs()
        values[2]["spine"]["$defs"]["loop"] = {"$ref": "#/$defs/loop"}
        self.reject(values, code="INVALID_QUALIFICATION")

    def test_strict_parser_refuses_duplicates_nonfinite_bad_unicode_oversize_and_unknown_versions(self):
        raw, sources, targets, resolution, _ = inputs()
        cases = [(raw.replace(b'"schema_version":"0.1.0"', b'"schema_version":"0.1.0","schema_version":"0.1.0"'), "INVALID_SOURCE"),
                 (raw.replace(b'"schema_version":"0.1.0"', b'"schema_version":"7.0.0"'), "UNSUPPORTED_VERSION"),
                 (b'{"bad":NaN}', "INVALID_SOURCE"), (b'{"bad":"\\ud800"}', "INVALID_SOURCE"),
                 (b' ' * 65537, "MIGRATION_LIMIT")]
        for changed, code in cases:
            with self.subTest(code=code):
                r = copy.deepcopy(resolution)
                r["source_sha256"] = hashlib.sha256(changed).hexdigest()
                migration = PlayerStateMigration("closed_reference_v1", sources, targets, r)
                with self.assertRaises(MigrationError) as caught:
                    migration.migrate(changed)
                self.assertEqual(code, caught.exception.code)

    def test_explicit_adapter_selection_refuses_cross_format_and_ambiguous_source(self):
        raw, sources, targets, resolution, _ = inputs()
        wrong = PlayerStateMigration("historical_record_v1", sources, targets, resolution)
        with self.assertRaises(MigrationError) as caught:
            wrong.migrate(raw)
        self.assertEqual("UNSUPPORTED_FORMAT", caught.exception.code)
        source = json.loads(raw)
        source["record_type"] = "PlayerRuntimeState"
        ambiguous = encode(source)
        resolution["source_sha256"] = hashlib.sha256(ambiguous).hexdigest()
        migration = PlayerStateMigration("closed_reference_v1", sources, targets, resolution)
        with self.assertRaises(MigrationError) as caught:
            migration.migrate(ambiguous)
        self.assertEqual("UNSUPPORTED_FORMAT", caught.exception.code)


if __name__ == "__main__":
    unittest.main()
