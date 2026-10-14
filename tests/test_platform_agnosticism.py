from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from check_platform_agnosticism import platform_violations


class ReferenceBoundaryTests(unittest.TestCase):
    def test_origin_reference_does_not_admit_neighboring_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "core/narrative_engine"
            reference.mkdir(parents=True)
            (reference / "origin_progression.py").write_text("# Reviewed reference\n", encoding="utf-8")
            self.assertEqual(([], 1), platform_violations(root))
            (reference / "origin_progression_network.py").write_text("# Unreviewed\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual(2, inspected)
            self.assertEqual(1, len(violations))

    def test_state_migration_approval_excludes_host_storage_adapters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "core"
            reference.mkdir()
            (reference / "state_migration.py").write_text("# Reference oracle\n", encoding="utf-8")
            self.assertEqual(([], 1), platform_violations(root))
            for name in ("state_migration_runtime.py", "state_migration_storage.py"):
                (reference / name).write_text("# Unapproved neighbor\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual((len(violations), inspected), (2, 3))

    def test_perception_persistence_approval_excludes_storage_and_network_neighbors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "core/perception_engine"
            reference.mkdir(parents=True)
            (reference / "persistence.py").write_text("# Reference oracle\n", encoding="utf-8")
            self.assertEqual(([], 1), platform_violations(root))
            for name in ("storage.py", "persistence_runtime.py", "network.py"):
                (reference / name).write_text("# Unapproved neighbor\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual((len(violations), inspected), (3, 4))

    def test_journal_reference_approval_does_not_admit_storage_or_network_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "core"
            reference.mkdir()
            (reference / "state_journal.py").write_text("# Journal reference\n", encoding="utf-8")
            self.assertEqual(([], 1), platform_violations(root))
            for name in ("state_journal_storage.py", "state_journal_network.py"):
                (reference / name).write_text("# Unreviewed neighbor\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual(3, inspected)
            self.assertEqual(2, len(violations))
            self.assertTrue(any("core/state_journal_storage.py:" in item for item in violations))
            self.assertTrue(any("core/state_journal_network.py:" in item for item in violations))

    def test_reviewed_module_reference_paths_do_not_admit_adjacent_runtime(self):
        names = ("realm_transition_values.py", "realm_transition.py", "generation_values.py",
                 "topology.py", "axioms.py", "diagnostic_module_values.py", "diagnostic_module_capture.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "core/ash_pattern_engine"
            reference.mkdir(parents=True)
            for name in names:
                (reference / name).write_text("# Reviewed reference control\n", encoding="utf-8")
            self.assertEqual(([], 7), platform_violations(root))
            for name in names:
                (reference / (name[:-3] + "_runtime.py")).write_text("# Unreviewed neighbor\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual(14, inspected)
            self.assertEqual(7, len(violations))
            for name in names:
                self.assertTrue(any(f"/{name[:-3]}_runtime.py:" in item for item in violations))

    def test_reviewed_session_reference_files_require_exact_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "core/ash_pattern_engine"
            reference.mkdir(parents=True)
            for name in ("session.py", "session_values.py", "diagnostic_session_values.py"):
                (reference / name).write_text("# Session reference fixture\n", encoding="utf-8")
            self.assertEqual(([], 3), platform_violations(root))
            neighbors = ("session_runtime.py", "session_values_extra.py", "diagnostic_session_values_extra.py")
            for name in neighbors:
                (reference / name).write_text("# Unreviewed neighbor\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual(6, inspected)
            self.assertEqual(3, len(violations))
            for name in neighbors:
                self.assertTrue(any(f"core/ash_pattern_engine/{name}:" in item for item in violations))

    def test_reviewed_n3_controls_do_not_admit_neighboring_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            controls = root / "docs/design-planning/m3/session-lifecycle"
            controls.mkdir(parents=True)
            for name in ("derive_bounds.py", "derive_command_reservations.py",
                         "generate_graph_control.py", "raw_business_guard_controls.py",
                         "replay_independent.py"):
                (controls / name).write_text("# Representation control\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual([], violations)
            self.assertEqual(5, inspected)
            for name in ("session_runtime.py", "derive_bounds_extra.py", "product.cpp"):
                (controls / name).write_text("# Unauthorized neighbor\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual(8, inspected)
            self.assertEqual(3, len(violations))
            for name in ("session_runtime.py", "derive_bounds_extra.py", "product.cpp"):
                self.assertTrue(any(f"session-lifecycle/{name}:" in item for item in violations))

    def test_reviewed_state_reference_files_do_not_admit_neighboring_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "core/ash_pattern_engine"
            reference.mkdir(parents=True)
            for name in ("__init__.py", "ash_canonical.py", "state_model.py", "state_values.py",
                         "normalization.py", "normalization_values.py", "recovery.py", "recovery_values.py",
                         "fallback_registry.py", "diagnostics.py", "diagnostics_values.py"):
                (reference / name).write_text("# Reference fixture\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual([], violations)
            self.assertEqual(11, inspected)

            for name in ("state_model_runtime.py", "state_values_extra.py", "normalization_runtime.py",
                         "normalization_values_extra.py", "recovery_runtime.py", "recovery_values_extra.py",
                         "fallback_registry_runtime.py", "diagnostics_runtime.py", "diagnostics_values_extra.py", "product.cpp"):
                (reference / name).write_text("# Unauthorized neighbor fixture\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual(21, inspected)
            self.assertEqual(10, len(violations))
            for name in ("state_model_runtime.py", "state_values_extra.py", "normalization_runtime.py",
                         "normalization_values_extra.py", "recovery_runtime.py", "recovery_values_extra.py",
                         "fallback_registry_runtime.py", "diagnostics_runtime.py", "diagnostics_values_extra.py", "product.cpp"):
                self.assertTrue(any(f"core/ash_pattern_engine/{name}:" in item for item in violations))


if __name__ == "__main__":
    unittest.main()
