from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_fixture_catalog as fixture_check


def read(relative: str):
    return fixture_check.load_json(ROOT / relative)


def signatures(schema, instance):
    result = {}
    for error in Draft202012Validator(schema).iter_errors(instance):
        for leaf in fixture_check.leaf_errors(error):
            signature = fixture_check.error_signature(leaf)
            result[fixture_check.signature_key(signature)] = signature
    return [result[key] for key in sorted(result)]


class AbilitySemanticAssertionsTests(unittest.TestCase):
    CASES = (
        (
            "ability_wolf_synergy_schema.json",
            "examples/ability_power_engine/ability_wolf_synergy_twin_coherence.example.json",
            "not_morality_system",
            "wolf_synergy",
            "wolf_morality",
        ),
        (
            "ability_decoherence_state_schema.json",
            "examples/ability_power_engine/ability_decoherence_event_overstrain.example.json",
            "temporary",
            "temporary_decoherence",
            "permanent_decoherence",
        ),
    )

    def setUp(self):
        self.bundle = read("examples/contract_foundation/ability_semantic_cases.example.json")

    def test_existing_complete_positive_examples_remain_accepted(self):
        for name, path, field, positive, _ in self.CASES:
            with self.subTest(schema=name):
                schema = read("data/schemas/" + name)
                Draft202012Validator.check_schema(schema)
                instance = read(path)
                self.assertIs(instance[field], True)
                self.assertEqual([], signatures(schema, instance))
                self.assertEqual(instance, self.bundle["positive"][positive])

    def test_false_has_only_the_intended_const_witness_in_a_complete_record(self):
        for name, path, field, _, reject in self.CASES:
            with self.subTest(schema=name):
                original = read(path)
                changed = copy.deepcopy(original)
                changed[field] = False
                self.assertEqual(changed, self.bundle["reject"][reject])
                self.assertEqual(
                    [{
                        "error_id": "JSON_SCHEMA_CONST",
                        "instance_pointer": "/" + field,
                        "schema_pointer": "/properties/" + field + "/const",
                    }],
                    signatures(read("data/schemas/" + name), changed),
                )

    def test_nonboolean_values_cannot_satisfy_the_true_constraint(self):
        for name, path, field, _, _ in self.CASES:
            schema = read("data/schemas/" + name)
            for value in (None, 0, 1, 1.0, "true", "false", {}, []):
                with self.subTest(schema=name, value=value):
                    instance = read(path)
                    instance[field] = value
                    actual = signatures(schema, instance)
                    self.assertEqual(
                        {"JSON_SCHEMA_CONST", "JSON_SCHEMA_TYPE"},
                        {error["error_id"] for error in actual},
                    )
                    self.assertEqual({"/" + field}, {error["instance_pointer"] for error in actual})
                    self.assertEqual(
                        {"/properties/" + field + "/const", "/properties/" + field + "/type"},
                        {error["schema_pointer"] for error in actual},
                    )

    def test_missing_flag_retains_the_existing_required_witness(self):
        for name, path, field, _, _ in self.CASES:
            with self.subTest(schema=name):
                instance = read(path)
                del instance[field]
                self.assertEqual(
                    [{"error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "", "schema_pointer": "/required", "missing_properties": [field]}],
                    signatures(read("data/schemas/" + name), instance),
                )

    def test_other_missing_fields_do_not_hide_behind_the_intended_const_error(self):
        schema = read("data/schemas/ability_decoherence_state_schema.json")
        instance = copy.deepcopy(self.bundle["reject"]["permanent_decoherence"])
        del instance["affected_ref"]
        actual = signatures(schema, instance)
        self.assertEqual(2, len(actual))
        self.assertEqual({"JSON_SCHEMA_CONST", "JSON_SCHEMA_REQUIRED"}, {error["error_id"] for error in actual})
        self.assertIn(
            {"error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "", "schema_pointer": "/required", "missing_properties": ["affected_ref"]},
            actual,
        )

    def test_true_records_keep_the_existing_open_object_contract(self):
        for name, path, _, _, _ in self.CASES:
            with self.subTest(schema=name):
                instance = read(path)
                instance["external_diagnostic"] = {"details": [None, False, "fixture"]}
                self.assertEqual([], signatures(read("data/schemas/" + name), instance))

    def test_governed_assertions_are_bound_to_the_requirement(self):
        for name, _, field, _, _ in self.CASES:
            with self.subTest(schema=name):
                self.assertEqual(
                    "YWE-REQ-0028",
                    read("data/schemas/" + name)["properties"][field]["x-ywe-requirement-id"],
                )

    def test_xp_only_source_kind_is_rejected_from_an_accepted_complete_control(self):
        schema = read("data/schemas/ability_source_ref_schema.json")
        source = copy.deepcopy(self.bundle["positive"]["source_ref"])
        self.assertEqual([], signatures(schema, source))
        rules = read("data/validation/ability_source_ref_validation_rules.json")
        for kind in rules["allowed_source_kinds"]:
            with self.subTest(kind=kind):
                source["source_kind"] = kind
                self.assertEqual([], signatures(schema, source))
        for kind in read("data/validation/ability_no_generic_skill_tree_validation_rules.json")["reject_patterns"]:
            with self.subTest(kind=kind):
                source["source_kind"] = kind
                self.assertEqual(
                    [{"error_id": "JSON_SCHEMA_ENUM", "instance_pointer": "/source_kind", "schema_pointer": "/properties/source_kind/enum"}],
                    signatures(schema, source),
                )

    def test_empty_source_provenance_has_one_cardinality_witness(self):
        schema = read("data/schemas/ability_manifest_schema.json")
        instance = read("examples/ability_power_engine/oath_sight_manifest.example.json")
        self.assertEqual([], signatures(schema, instance))
        instance["source_refs"] = []
        self.assertEqual(
            [{"error_id": "JSON_SCHEMA_MINITEMS", "instance_pointer": "/source_refs", "schema_pointer": "/properties/source_refs/minItems"}],
            signatures(schema, instance),
        )

    def test_phase_12_missing_context_scenarios_keep_exact_required_witnesses(self):
        cases = (
            ("generated_lore_fragment_schema.json", "lore_generation/ravenfall_gate_public_oath_lore_fragment.example.json", ["pattern_trace_ref", "truth_scope"]),
            ("npc_manifest_candidate_schema.json", "npc_generation/ravenfall_gate_witness_npc_candidate.example.json", ["relation_graph_ref"]),
            ("quest_generation_context_schema.json", "quest_generation/ravenfall_gate_reveal_oath_quest_generation_context.example.json", ["axiom_diagnostic_refs", "branch_reality_ref", "player_runtime_state_ref", "location_state_ref", "worldstate_delta_refs", "truth_scope", "provenance"]),
        )
        for name, relative, removed in cases:
            with self.subTest(schema=name):
                schema = read("data/schemas/" + name)
                instance = read("examples/phase_12_quest_npc_lore_generation/" + relative)
                self.assertEqual([], signatures(schema, instance))
                for field in removed:
                    del instance[field]
                self.assertEqual(
                    [{"error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "", "schema_pointer": "/required", "missing_properties": sorted(removed)}],
                    signatures(schema, instance),
                )

    def test_existing_quest_candidate_missing_title_policy_is_an_exact_rejection(self):
        instance = read("examples/phase_12_quest_npc_lore_generation/quest_generation/quest_manifest_candidate_buried_oath_reveal.example.json")
        self.assertEqual(
            [{"error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "", "schema_pointer": "/required", "missing_properties": ["quest_title_policy"]}],
            signatures(read("data/schemas/quest_manifest_candidate_schema.json"), instance),
        )


if __name__ == "__main__":
    unittest.main()
