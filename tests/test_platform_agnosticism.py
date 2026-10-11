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
