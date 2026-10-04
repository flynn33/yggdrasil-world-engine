"""Selected-source isolation for the ASH package acceptance consumer."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import py_compile
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ywe_package_acceptance_under_test",
    ROOT / ".github/scripts/ywe_package_acceptance_check.py",
)
acceptance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acceptance)


class PackageAcceptanceLoadingTests(unittest.TestCase):
    def write(self, path: Path, source: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    def write_package(self, root: Path, mode: str = "valid") -> Path:
        package = root / "core/ash_pattern_engine"
        self.write(package / "__init__.py", "from .ash_canonical import *\n")
        self.write(
            package / "values.py",
            "from __future__ import annotations\n"
            "from dataclasses import dataclass\n"
            "@dataclass(frozen=True)\n"
            "class State:\n"
            "    bits: tuple[int, ...]\n",
        )
        self.write(
            package / "transition_impl.py",
            f'MODE = "{mode}"\n'
            "def transform(state, codeword, allowed):\n"
            "    if len(state) != 9 or tuple(codeword) not in allowed:\n"
            "        raise ValueError('invalid state or codeword')\n"
            "    if MODE == 'wrong':\n"
            "        return tuple(state)\n"
            "    return tuple(a ^ b for a, b in zip(state, codeword))\n",
        )
        self.write(
            package / "ash_canonical.py",
            "from .values import State\n"
            "ASH_STATE_BITS = 9\n"
            f"CANONICAL_CODEWORDS = {acceptance.EXPECTED_CODEWORDS!r}\n"
            "def orbit_id(state):\n"
            "    return min(tuple(a ^ b for a, b in zip(state, codeword))\n"
            "               for codeword in CANONICAL_CODEWORDS)\n"
            "def transform_state(state, codeword):\n"
            "    from .transition_impl import transform\n"
            "    return State(transform(state, codeword, CANONICAL_CODEWORDS))\n",
        )
        return package

    @contextlib.contextmanager
    def assert_isolated(self):
        private_before = {name for name in sys.modules
                          if name.startswith(acceptance._ASH_PACKAGE_PREFIX)}
        live_before = {name: module for name, module in sys.modules.items()
                       if name == "core" or name.startswith("core.")
                       or name == "ash_canonical"}
        path_before = list(sys.path)
        finders_before = tuple(sys.meta_path)
        try:
            yield
        finally:
            self.assertEqual(private_before, {name for name in sys.modules
                                             if name.startswith(acceptance._ASH_PACKAGE_PREFIX)})
            self.assertEqual(live_before, {name: module for name, module in sys.modules.items()
                                          if name == "core" or name.startswith("core.")
                                          or name == "ash_canonical"})
            self.assertEqual(path_before, sys.path)
            self.assertEqual(len(finders_before), len(sys.meta_path))
            self.assertTrue(all(before is after
                                for before, after in zip(finders_before, sys.meta_path)))

    def run_check(self, root: Path, check) -> list[str]:
        sink = acceptance.FailureSink()
        with self.assert_isolated():
            check(root, sink)
        return sink.failures

    def preserve_bytecode_then_replace(self, path: Path, before: str, after: str) -> None:
        original = path.read_text(encoding="utf-8")
        changed = original.replace(before, after)
        self.assertNotEqual(original, changed)
        self.assertEqual(len(original.encode("utf-8")), len(changed.encode("utf-8")))
        stamp = path.stat().st_mtime
        py_compile.compile(str(path), doraise=True)
        path.write_text(changed, encoding="utf-8")
        os.utime(path, (stamp, stamp))

    def test_actual_three_consumers_preserve_cached_live_facade_and_globals(self):
        from core.ash_pattern_engine import ash_canonical

        sentinel = object()
        with patch.dict(sys.modules, {"ash_canonical": sentinel}):
            for check in (acceptance.test_codeword_set_exactly_16,
                          acceptance.test_transition_is_full_state_xor,
                          acceptance.test_all_generation_requires_cosmic_pattern_snapshot):
                with self.subTest(check=check.__name__):
                    self.assertEqual([], self.run_check(ROOT, check))
            self.assertIs(sentinel, sys.modules["ash_canonical"])
        self.assertIs(ash_canonical, sys.modules["core.ash_pattern_engine.ash_canonical"])

    def test_selected_package_supports_eager_dataclass_and_lazy_relative_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_package(root)
            self.assertEqual([], self.run_check(root, acceptance.test_codeword_set_exactly_16))
            self.assertEqual([], self.run_check(root, acceptance.test_transition_is_full_state_xor))

    def test_two_selected_roots_cannot_be_masked_by_cached_live_package(self):
        from core.ash_pattern_engine import ash_canonical

        with tempfile.TemporaryDirectory() as directory:
            root_a, root_b = Path(directory) / "a", Path(directory) / "b"
            self.write_package(root_a)
            self.write_package(root_b, mode="wrong")
            self.assertEqual([], self.run_check(root_a, acceptance.test_transition_is_full_state_xor))
            failures = self.run_check(root_b, acceptance.test_transition_is_full_state_xor)
            self.assertTrue(any("full 9-coordinate XOR" in error for error in failures))
            self.assertEqual([], self.run_check(root_a, acceptance.test_transition_is_full_state_xor))
        self.assertIs(ash_canonical, sys.modules["core.ash_pattern_engine.ash_canonical"])

    def test_lazy_helper_source_change_is_not_masked_by_same_size_same_timestamp_pyc(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.write_package(root)
            self.preserve_bytecode_then_replace(package / "transition_impl.py",
                                                'MODE = "valid"', 'MODE = "wrong"')
            failures = self.run_check(root, acceptance.test_transition_is_full_state_xor)
            self.assertTrue(any("full 9-coordinate XOR" in error for error in failures))

    def test_facade_source_change_is_not_masked_by_same_size_same_timestamp_pyc(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.write_package(root)
            self.preserve_bytecode_then_replace(package / "ash_canonical.py",
                                                "ASH_STATE_BITS = 9", "ASH_STATE_BITS = 8")
            failures = self.run_check(root, acceptance.test_codeword_set_exactly_16)
            self.assertIn("ASH_STATE_BITS must be 9", failures)

    def test_initializer_source_change_is_not_masked_by_same_size_same_timestamp_pyc(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.write_package(root)
            self.write(package / "__init__.py",
                       'PACKAGE_MARKER = "prior"\nfrom .ash_canonical import *\n')
            self.preserve_bytecode_then_replace(package / "__init__.py", '"prior"', '"newer"')
            with self.assert_isolated(), acceptance.import_ash(root) as ash:
                self.assertEqual("newer", sys.modules[ash.__package__].PACKAGE_MARKER)

    def test_failed_initializer_cleans_eager_children_and_private_finder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.write_package(root)
            self.write(package / "__init__.py",
                       "from .values import State\nraise RuntimeError('load failed')\n")
            with self.assert_isolated(), self.assertRaisesRegex(RuntimeError, "load failed"):
                with acceptance.import_ash(root):
                    self.fail("failed initializer must not yield a facade")

    def test_failed_facade_cleans_imported_children_and_private_finder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.write_package(root)
            self.write(package / "ash_canonical.py",
                       "from .values import State\nraise RuntimeError('facade failed')\n")
            with self.assert_isolated(), self.assertRaisesRegex(RuntimeError, "facade failed"):
                with acceptance.import_ash(root):
                    self.fail("failed facade must not yield")

    def test_failed_lazy_import_cleans_modules_and_private_finder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.write_package(root)
            self.write(package / "transition_impl.py", "raise RuntimeError('lazy failed')\n")
            with self.assert_isolated(), self.assertRaisesRegex(RuntimeError, "lazy failed"):
                acceptance.test_transition_is_full_state_xor(root, acceptance.FailureSink())

    def test_missing_selected_helper_cannot_fall_back_to_source_less_bytecode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.write_package(root)
            source = package / "transition_impl.py"
            py_compile.compile(str(source), cfile=str(package / "transition_impl.pyc"), doraise=True)
            source.unlink()
            with self.assert_isolated(), self.assertRaisesRegex(ModuleNotFoundError, "no source"):
                acceptance.test_transition_is_full_state_xor(root, acceptance.FailureSink())

    def test_failed_consumer_after_lazy_import_cleans_modules_and_private_finder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_package(root)
            with self.assert_isolated(), self.assertRaisesRegex(RuntimeError, "consumer failed"):
                with acceptance.import_ash(root) as ash:
                    ash.transform_state((0,) * 9, acceptance.EXPECTED_CODEWORDS[1])
                    raise RuntimeError("consumer failed")

    def test_historical_standalone_source_remains_supported_and_isolated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root / "core/ash_pattern_engine/ash_canonical.py",
                       "from __future__ import annotations\n"
                       "from dataclasses import dataclass\n"
                       "@dataclass(frozen=True)\n"
                       "class State:\n"
                       "    bits: tuple[int, ...]\n"
                       "def transform_state(state, codeword):\n"
                       "    return State(tuple(a ^ b for a, b in zip(state, codeword)))\n")
            with self.assert_isolated(), acceptance.import_ash(root) as ash:
                self.assertEqual((1,) * 9, ash.transform_state((0,) * 9, (1,) * 9).bits)

    def test_selected_source_loading_does_not_write_bytecode_when_global_writes_enabled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_package(root)
            with patch.object(sys, "dont_write_bytecode", False):
                self.assertEqual([], self.run_check(root, acceptance.test_transition_is_full_state_xor))
            self.assertEqual([], list(root.rglob("*.pyc")))

    def test_cli_retains_check_name_and_failure_when_selected_package_cannot_load(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.write_package(root)
            self.write(package / "__init__.py", "raise ImportError('selected package broken')\n")
            output = io.StringIO()
            with self.assert_isolated(), contextlib.redirect_stdout(output), \
                    patch.object(sys, "argv", ["acceptance", str(root)]), \
                    patch.object(acceptance, "check_governance_records"), \
                    patch.object(acceptance, "TESTS", [acceptance.test_transition_is_full_state_xor]):
                self.assertEqual(1, acceptance.main())
            self.assertIn("test_transition_is_full_state_xor raised ImportError", output.getvalue())
            self.assertIn("selected package broken", output.getvalue())


if __name__ == "__main__":
    unittest.main()
