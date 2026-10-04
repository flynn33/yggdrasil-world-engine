from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_fixture_catalog as fixture_check

SCHEMA_PATH = "data/schemas/ravenfall_preview_descriptor_schema.json"
SCHEMA_ID = "https://ywe.local/schemas/ravenfall_preview_descriptor_schema.json"
BUNDLE_PATH = "examples/contract_foundation/ravenfall_preview_format_cases.example.json"
SLICE_PATH = "examples/vertical_slices/ravenfall_gate/"
RECOVERY_PATH = "examples/phase_16_17_recovery/"
MODES = ("reveal", "conceal", "bind", "study", "weaponize")

RECOVERY = "RecoveryMinimumTraceDescription"
BRANCH = "RavenfallBranchOutcomeDescription"
QUEST = "RavenfallQuestDesignDescription"
NPC = "RavenfallNPCDescription"
LORE = "RavenfallLoreDescription"
ARTIFACT = "RavenfallArtifactEligibilityDescription"
CREATURE = "RavenfallCreatureEligibilityDescription"

ORIGINALS = (
    *[(RECOVERY_PATH + f"ravenfall_{mode}_playtest_trace_minimum.example.json", RECOVERY) for mode in MODES],
    *[(SLICE_PATH + f"branch_outcome_{mode}.example.json", BRANCH) for mode in MODES],
    (SLICE_PATH + "buried_oath_quest_design.example.json", QUEST),
    (SLICE_PATH + "npc_hidden_keeper.example.json", NPC),
    (SLICE_PATH + "npc_public_witness.example.json", NPC),
    (SLICE_PATH + "lore_hidden_oath_memory.example.json", LORE),
    (SLICE_PATH + "lore_public_oath_inscription.example.json", LORE),
    (SLICE_PATH + "artifact_eligibility_oath_shard.example.json", ARTIFACT),
    (SLICE_PATH + "creature_eligibility_echo_hound.example.json", CREATURE),
)

# Exact witnesses distinguish the intended constraint from incidental rejection.
# The last column names the missing members for a required-field witness.
REJECT_CASES = (
    ("recovery_complete_true", RECOVERY, "CONST", "/acceptance/complete",
     "/properties/acceptance/properties/complete/const", ()),
    ("recovery_note_number", RECOVERY, "TYPE", "/acceptance/note",
     "/properties/acceptance/properties/note/type", ()),
    ("recovery_note_missing", RECOVERY, "REQUIRED", "/acceptance",
     "/properties/acceptance/required", ("note",)),
    ("recovery_acceptance_array", RECOVERY, "TYPE", "/acceptance", "/properties/acceptance/type", ()),
    ("recovery_ref_missing", RECOVERY, "REQUIRED", "", "/required", ("branch_event_ref",)),
    ("recovery_unknown_completion", RECOVERY, "ENUM", "/completion_mode",
     "/properties/completion_mode/enum", ()),
    ("branch_noop_boolean", BRANCH, "TYPE", "/diagnostic_noop_ref",
     "/properties/diagnostic_noop_ref/type", ()),
    ("branch_delta_item_number", BRANCH, "TYPE", "/worldstate_delta_refs/0",
     "/properties/worldstate_delta_refs/items/type", ()),
    ("branch_future_refs_string", BRANCH, "TYPE", "/future_generation_bias_refs",
     "/properties/future_generation_bias_refs/type", ()),
    ("branch_noop_missing", BRANCH, "REQUIRED", "", "/required", ("diagnostic_noop_ref",)),
    ("branch_unknown_completion", BRANCH, "ENUM", "/completion_mode", "/properties/completion_mode/enum", ()),
    ("quest_stages_number", QUEST, "TYPE", "/quest_stages", "/properties/quest_stages/type", ()),
    ("quest_stage_purpose_missing", QUEST, "REQUIRED", "/quest_stages/0",
     "/properties/quest_stages/items/required", ("purpose",)),
    ("quest_stage_purpose_array", QUEST, "TYPE", "/quest_stages/0/purpose",
     "/properties/quest_stages/items/properties/purpose/type", ()),
    ("quest_unknown_mode", QUEST, "ENUM", "/completion_modes/0", "/properties/completion_modes/items/enum", ()),
    ("npc_relation_null", NPC, "TYPE", "/relation_context", "/properties/relation_context/type", ()),
    ("npc_self_reference_integer", NPC, "TYPE", "/self_reference_required",
     "/properties/self_reference_required/type", ()),
    ("npc_relation_missing", NPC, "REQUIRED", "", "/required", ("relation_context",)),
    ("npc_role_array", NPC, "TYPE", "/npc_role", "/properties/npc_role/type", ()),
    ("lore_pattern_refs_missing", LORE, "REQUIRED", "", "/required", ("pattern_trace_refs",)),
    ("lore_pattern_item_object", LORE, "TYPE", "/pattern_trace_refs/0", "/properties/pattern_trace_refs/items/type", ()),
    ("lore_visibility_boolean", LORE, "TYPE", "/visibility", "/properties/visibility/type", ()),
    ("lore_random_text_allowed", LORE, "CONST", "/not_random_text", "/properties/not_random_text/const", ()),
    ("artifact_condition_item_boolean", ARTIFACT, "TYPE", "/eligibility_conditions/0",
     "/properties/eligibility_conditions/items/type", ()),
    ("artifact_id_missing", ARTIFACT, "REQUIRED", "", "/required", ("artifact_id",)),
    ("artifact_generic_loot_allowed", ARTIFACT, "CONST", "/not_generic_loot", "/properties/not_generic_loot/const", ()),
    ("creature_conditions_object", CREATURE, "TYPE", "/eligibility_conditions", "/properties/eligibility_conditions/type", ()),
    ("creature_condition_item_boolean", CREATURE, "TYPE", "/eligibility_conditions/0",
     "/properties/eligibility_conditions/items/type", ()),
    ("creature_random_enemy_allowed", CREATURE, "CONST", "/not_random_enemy", "/properties/not_random_enemy/const", ()),
    ("common_source_refs_boolean", BRANCH, "TYPE", "/source_truth_refs", "/allOf/0/properties/source_truth_refs/type", ()),
    ("common_phase_item_boolean", BRANCH, "TYPE", "/requires_phase_refs/0",
     "/allOf/0/properties/requires_phase_refs/items/type", ()),
    ("common_phase_id_wrong", BRANCH, "CONST", "/phase_id", "/allOf/0/properties/phase_id/const", ()),
    ("common_source_refs_missing", BRANCH, "REQUIRED", "", "/allOf/0/required", ("source_truth_refs",)),
)

BOUNDARY_CASES = {
    "recovery_empty_note": RECOVERY,
    "recovery_empty_trace_ref": RECOVERY,
    "branch_empty_worldstate_refs": BRANCH,
    "branch_noop_string": BRANCH,
    "branch_noop_null": BRANCH,
    "branch_empty_future_refs": BRANCH,
    "common_empty_source_refs": BRANCH,
    "common_empty_phase_refs": BRANCH,
    "quest_empty_stages": QUEST,
    "quest_empty_modes": QUEST,
    "npc_empty_relation_text": NPC,
    "npc_self_reference_false": NPC,
    "lore_empty_pattern_refs": LORE,
    "artifact_empty_conditions": ARTIFACT,
    "creature_empty_conditions": CREATURE,
    "recovery_open_acceptance": RECOVERY,
    "quest_open_stage": QUEST,
    **{"open_root_" + definition.lower(): definition
       for definition in (RECOVERY, BRANCH, QUEST, NPC, LORE, ARTIFACT, CREATURE)},
}


def witness(kind, instance_pointer, schema_pointer, missing=()):
    result = {
        "error_id": "JSON_SCHEMA_" + kind,
        "instance_pointer": instance_pointer,
        "schema_pointer": schema_pointer,
    }
    if missing:
        result["missing_properties"] = list(missing)
    return result


def binding(name, definition, expected_errors, category="reject"):
    result = {
        "fixture_id": "test.ravenfall_preview." + name,
        "path": BUNDLE_PATH,
        "instance_pointer": f"/{category}/{name}",
        "schema_id": SCHEMA_ID + "#/$defs/" + definition,
        "category": category,
        "expected_result": "reject" if expected_errors else "accept",
        "expected_errors": expected_errors,
    }
    if not expected_errors:
        result["expected_requirement_ids"] = ["YWE-REQ-0020", "YWE-REQ-0031"]
    return result


class RavenfallPreviewFormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = fixture_check.load_json(ROOT / SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.schema)
        cls.registry = Registry(retrieve=fixture_check.deny_retrieval).with_resource(
            SCHEMA_ID, Resource.from_contents(cls.schema)
        ).crawl()
        cls.bundle = fixture_check.load_json(ROOT / BUNDLE_PATH)

    def observed(self, definition, instance):
        validator = Draft202012Validator(
            {"$ref": SCHEMA_ID + "#/$defs/" + definition}, registry=self.registry
        )
        return [fixture_check.error_signature(leaf)
                for error in validator.iter_errors(instance)
                for leaf in fixture_check.leaf_errors(error)]

    def test_all_seventeen_original_previews_accept_at_their_explicit_format(self):
        self.assertEqual(17, len(ORIGINALS))
        for relative, definition in ORIGINALS:
            with self.subTest(path=relative):
                self.assertEqual([], self.observed(definition, fixture_check.load_json(ROOT / relative)))

    def test_thirty_five_reject_cases_match_the_entire_intended_witness_set(self):
        cases = [binding(name, definition, [witness(kind, instance, schema, missing)])
                 for name, definition, kind, instance, schema, missing in REJECT_CASES]
        cases.extend((
            binding("recovery_complete_string", RECOVERY, [
                witness("TYPE", "/acceptance/complete", "/properties/acceptance/properties/complete/type"),
                witness("CONST", "/acceptance/complete", "/properties/acceptance/properties/complete/const"),
            ]),
            binding("lore_boolean_string", LORE, [
                witness("TYPE", "/not_random_text", "/properties/not_random_text/type"),
                witness("CONST", "/not_random_text", "/properties/not_random_text/const"),
            ]),
        ))
        self.assertEqual(35, len(cases))
        self.assertEqual(set(self.bundle["reject"]), {item["instance_pointer"].split("/")[-1] for item in cases})
        errors, results = fixture_check.evaluate_fixtures(ROOT, self.registry, cases)
        self.assertEqual([], errors)
        self.assertEqual(35, len(results))

    def test_twenty_four_open_and_empty_boundaries_accept_as_formats(self):
        self.assertEqual(24, len(BOUNDARY_CASES))
        self.assertEqual(set(BOUNDARY_CASES), set(self.bundle["boundary"]))
        cases = [binding(name, definition, [], "boundary") for name, definition in BOUNDARY_CASES.items()]
        errors, results = fixture_check.evaluate_fixtures(ROOT, self.registry, cases)
        self.assertEqual([], errors)
        self.assertEqual(24, len(results))

    def test_all_source_minimum_traces_remain_incomplete_and_true_is_rejected(self):
        for relative, definition in ORIGINALS:
            if definition != RECOVERY:
                continue
            with self.subTest(path=relative):
                instance = fixture_check.load_json(ROOT / relative)
                self.assertIs(False, instance["acceptance"]["complete"])
                instance["acceptance"]["complete"] = True
                self.assertEqual([witness("CONST", "/acceptance/complete",
                                         "/properties/acceptance/properties/complete/const")],
                                 self.observed(RECOVERY, instance))

    def test_missing_note_and_missing_complete_are_distinct_rejection_reasons(self):
        original = fixture_check.load_json(ROOT / ORIGINALS[0][0])
        for missing in ("note", "complete"):
            with self.subTest(missing=missing):
                instance = copy.deepcopy(original)
                del instance["acceptance"][missing]
                self.assertEqual([witness("REQUIRED", "/acceptance", "/properties/acceptance/required", (missing,))],
                                 self.observed(RECOVERY, instance))
        case = binding("recovery_note_missing", RECOVERY, [
            witness("REQUIRED", "/acceptance", "/properties/acceptance/required", ("complete",))
        ])
        errors, results = fixture_check.evaluate_fixtures(ROOT, self.registry, [case])
        self.assertEqual([], results)
        self.assertEqual(1, len(errors))
        self.assertIn("observed reject", errors[0])

    def test_nested_stage_members_are_required_and_typed(self):
        original = fixture_check.load_json(ROOT / (SLICE_PATH + "buried_oath_quest_design.example.json"))
        for member in ("stage_id", "purpose"):
            with self.subTest(member=member):
                instance = copy.deepcopy(original)
                del instance["quest_stages"][0][member]
                self.assertEqual([witness("REQUIRED", "/quest_stages/0",
                                         "/properties/quest_stages/items/required", (member,))],
                                 self.observed(QUEST, instance))
                instance = copy.deepcopy(original)
                instance["quest_stages"][0][member] = 1
                self.assertEqual([witness("TYPE", "/quest_stages/0/" + member,
                                         "/properties/quest_stages/items/properties/" + member + "/type")],
                                 self.observed(QUEST, instance))

    def test_source_owned_exclusion_flags_reject_false_and_integer_substitutions(self):
        sources = (
            ("lore_public_oath_inscription.example.json", LORE, "not_random_text"),
            ("artifact_eligibility_oath_shard.example.json", ARTIFACT, "not_generic_loot"),
            ("creature_eligibility_echo_hound.example.json", CREATURE, "not_random_enemy"),
        )
        for name, definition, field in sources:
            original = fixture_check.load_json(ROOT / (SLICE_PATH + name))
            self.assertIs(True, original[field])
            for value in (False, 1, "true"):
                with self.subTest(definition=definition, value=value):
                    instance = copy.deepcopy(original)
                    instance[field] = value
                    expected = [witness("CONST", "/" + field, "/properties/" + field + "/const")]
                    if type(value) is not bool:
                        expected.append(witness("TYPE", "/" + field, "/properties/" + field + "/type"))
                    self.assertEqual({fixture_check.signature_key(item) for item in expected},
                                     {fixture_check.signature_key(item) for item in self.observed(definition, instance)})

    def test_npc_self_reference_is_a_design_boolean_without_invented_classification(self):
        instance = fixture_check.load_json(ROOT / (SLICE_PATH + "npc_hidden_keeper.example.json"))
        instance["self_reference_required"] = False
        self.assertEqual([], self.observed(NPC, instance))
        for value in (0, 1, "false", None):
            with self.subTest(value=value):
                instance["self_reference_required"] = value
                self.assertEqual([witness("TYPE", "/self_reference_required", "/properties/self_reference_required/type")],
                                 self.observed(NPC, instance))

    def test_study_preview_keeps_descriptive_truth_label_and_empty_delta(self):
        instance = fixture_check.load_json(ROOT / (SLICE_PATH + "branch_outcome_study.example.json"))
        self.assertEqual("diagnostic_noop", instance["truth_scope"])
        self.assertEqual([], instance["worldstate_delta_refs"])
        self.assertEqual([], self.observed(BRANCH, instance))
        for reference in (None, "", "diagnostic_noop.ravenfall_gate.study_unresolved"):
            with self.subTest(reference=reference):
                instance["diagnostic_noop_ref"] = reference
                self.assertEqual([], self.observed(BRANCH, instance))

    def test_unknown_schema_retrieval_is_denied_offline(self):
        with self.assertRaises(Unresolvable):
            fixture_check.resolve_schema_target(self.registry, "https://unowned.invalid/preview.json")


if __name__ == "__main__":
    unittest.main()
