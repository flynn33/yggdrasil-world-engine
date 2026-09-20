#!/usr/bin/env python3
"""Unit and mutation tests for the M2 acceptance gate."""

from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_m2_acceptance",
    ROOT / "scripts/check_m2_acceptance.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to import scripts/check_m2_acceptance.py")
m2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m2)


class M2AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.negative_schema = json.loads(
            (ROOT / "data/schemas/m2_negative_fixture_policy_schema.json").read_text(
                encoding="utf-8-sig"
            )
        )
        cls.catalog = json.loads(
            (ROOT / "data/validation/m2_fixture_catalog.json").read_text(
                encoding="utf-8-sig"
            )
        )

    def diagnostic_ids(self, instance: dict) -> set[str]:
        errors = list(m2.M2Validator(self.negative_schema).iter_errors(instance))
        identifiers: set[str] = set()
        for error in errors:
            match = m2.DIAGNOSTIC_PATTERN.match(error.message)
            self.assertIsNotNone(match, error.message)
            identifiers.add(match.group(1))
        return identifiers

    def load_example(self, relative_path: str) -> dict:
        return json.loads((ROOT / relative_path).read_text(encoding="utf-8-sig"))

    def test_repository_preflight_passes(self) -> None:
        errors, metrics = m2.run(ROOT, preflight=True)
        self.assertEqual([], errors)
        self.assertEqual(39, metrics["closed_debt_count"])
        self.assertFalse(metrics["network_access_required"])

    def test_preflight_is_repeatable(self) -> None:
        first = m2.run(ROOT, preflight=True)
        second = m2.run(ROOT, preflight=True)
        self.assertEqual(first, second)

    def test_catalog_has_unique_ids_and_all_fixture_classes(self) -> None:
        entries = self.catalog["entries"]
        identifiers = [entry["fixture_id"] for entry in entries]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(
            m2.REQUIRED_FIXTURE_CLASSES,
            {entry["fixture_class"] for entry in entries},
        )

    def test_catalog_closes_exactly_the_recorded_39_paths(self) -> None:
        closed = {
            entry["instance_path"]
            for entry in self.catalog["entries"]
            if entry["closes_schema_debt"]
        }
        self.assertEqual(39, len(closed))
        self.assertEqual(39, self.catalog["closed_debt_count"])

    def test_missing_ability_provenance_rejects_for_intended_rule(self) -> None:
        value = self.load_example(
            "examples/ability_power_engine/invalid_ability_without_source_refs.example.json"
        )
        self.assertEqual(
            {"check_ability_source_provenance"},
            self.diagnostic_ids(value),
        )

    def test_generic_xp_unlock_rejects_for_intended_rule(self) -> None:
        value = self.load_example(
            "examples/ability_power_engine/invalid_generic_xp_unlock.example.json"
        )
        self.assertEqual({"check_no_generic_skill_tree"}, self.diagnostic_ids(value))

    def test_permanent_wolf_cost_rejects_for_intended_rule(self) -> None:
        value = self.load_example(
            "examples/ability_power_engine/invalid_permanent_wolf_death_cost.example.json"
        )
        self.assertEqual(
            {"check_ability_decoherence_not_death"},
            self.diagnostic_ids(value),
        )

    def test_wolf_morality_ability_rejects_for_intended_rule(self) -> None:
        value = self.load_example(
            "examples/ability_power_engine/invalid_white_good_dark_evil_ability.example.json"
        )
        self.assertEqual(
            {"check_no_wolf_morality_ability_drift"},
            self.diagnostic_ids(value),
        )

    def test_phase12_negative_envelope_reports_declared_rules_only(self) -> None:
        value = self.load_example(
            "examples/phase_12_quest_npc_lore_generation/quest_generation/"
            "invalid_generic_random_quest_candidate.example.json"
        )
        self.assertEqual(set(value["should_fail_rules"]), self.diagnostic_ids(value))

    def test_phase17_no_reward_packet_rejects_for_intended_rule(self) -> None:
        value = self.load_example(
            "examples/ravenfall_gate/phase_17/invalid_no_reward_packet_trace.reject.json"
        )
        self.assertEqual(
            {"check_no_feature_consequence_without_packet"},
            self.diagnostic_ids(value),
        )

    def test_phase17_platform_runtime_rejects_for_intended_rule(self) -> None:
        value = self.load_example(
            "examples/ravenfall_gate/phase_17/invalid_platform_runtime_trace.reject.json"
        )
        self.assertEqual(
            {"check_no_platform_specific_runtime_phase_17"},
            self.diagnostic_ids(value),
        )

    def test_phase17_static_location_rejects_for_intended_rule(self) -> None:
        value = self.load_example(
            "examples/ravenfall_gate/phase_17/invalid_static_location_trace.reject.json"
        )
        self.assertEqual(
            {"check_no_static_only_location_model_phase_17"},
            self.diagnostic_ids(value),
        )

    def test_phase17_wolf_rejections_remain_distinct(self) -> None:
        permanent = self.load_example(
            "examples/ravenfall_gate/phase_17/invalid_permanent_wolf_death.reject.json"
        )
        morality = self.load_example(
            "examples/ravenfall_gate/phase_17/invalid_wolf_morality_trace.reject.json"
        )
        self.assertEqual(
            {"check_no_permanent_wolf_death_phase_17"},
            self.diagnostic_ids(permanent),
        )
        self.assertEqual(
            {"check_no_wolf_morality_language_phase_17"},
            self.diagnostic_ids(morality),
        )

    def test_mutation_that_repairs_provenance_no_longer_matches_expected_rejection(self) -> None:
        value = self.load_example(
            "examples/ability_power_engine/invalid_ability_without_source_refs.example.json"
        )
        changed = copy.deepcopy(value)
        changed["candidate"]["source_refs"] = ["source.ash.reference"]
        self.assertEqual(
            {"YWE-M2-NEGATIVE-NOT-REPRODUCED"},
            self.diagnostic_ids(changed),
        )


if __name__ == "__main__":
    unittest.main()
