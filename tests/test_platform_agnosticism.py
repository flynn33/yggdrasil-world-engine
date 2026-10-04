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
    def test_reviewed_state_reference_files_do_not_admit_neighboring_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "core/ash_pattern_engine"
            reference.mkdir(parents=True)
            for name in ("__init__.py", "ash_canonical.py", "state_model.py", "state_values.py"):
                (reference / name).write_text("# Reference fixture\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual([], violations)
            self.assertEqual(4, inspected)

            for name in ("state_model_runtime.py", "state_values_extra.py", "product.cpp"):
                (reference / name).write_text("# Unauthorized neighbor fixture\n", encoding="utf-8")
            violations, inspected = platform_violations(root)
            self.assertEqual(7, inspected)
            self.assertEqual(3, len(violations))
            for name in ("state_model_runtime.py", "state_values_extra.py", "product.cpp"):
                self.assertTrue(any(f"core/ash_pattern_engine/{name}:" in item for item in violations))


if __name__ == "__main__":
    unittest.main()
