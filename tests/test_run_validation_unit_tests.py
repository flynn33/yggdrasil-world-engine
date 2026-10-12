from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_validation_unit_tests as recorder
import validate_repository as validator
from jsonschema import Draft202012Validator


class UnitEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "checkout"
        self.root.mkdir()
        (self.root / "tests").mkdir()
        self.source = self.root / "tests/test_cases.py"
        self.receipt = Path(self.temporary.name) / "cases.json"

    def prepare(self, source):
        self.source.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
        commands = [["git", "init", "--quiet"], ["git", "config", "user.name", "Test Fixture"],
                    ["git", "config", "user.email", "fixture@example.invalid"], ["git", "add", "."],
                    ["git", "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "fixture"]]
        for command in commands:
            subprocess.run(command, cwd=self.root, capture_output=True, check=True)

    def run_cases(self, *extra):
        environment = os.environ.copy()
        environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", GIT_ALLOW_PROTOCOL="file")
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/run_validation_unit_tests.py"),
                                 "--receipt", str(self.receipt), "discover", "-s", "tests", "-p", "test_*.py", *extra],
                                cwd=self.root, env=environment, capture_output=True)
        return result, json.loads(self.receipt.read_text())

    def test_script_entry_preserves_selected_checkout_package_imports_with_and_without_receipt(self):
        package = self.root / "checkout_package"
        package.mkdir()
        (package / "__init__.py").write_text('VALUE = "selected checkout"\n', encoding="utf-8")
        (self.root / "tests/test_other.py").write_text(
            'import unittest\nfrom checkout_package import VALUE\nclass OtherCases(unittest.TestCase):\n'
            '    def test_second_module_import(self):\n        self.assertEqual("selected checkout", VALUE)\n',
            encoding="utf-8")
        self.prepare('''
            import unittest
            import checkout_package
            from pathlib import Path
            class Cases(unittest.TestCase):
                def test_selected_package(self):
                    self.assertEqual("selected checkout", checkout_package.VALUE)
                    self.assertEqual(Path(__file__).resolve().parents[1] / "checkout_package/__init__.py",
                                     Path(checkout_package.__file__).resolve())
        ''')
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", GIT_ALLOW_PROTOCOL="file")
        ordinary = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
                                  cwd=self.root, env=environment, capture_output=True)
        self.assertEqual(0, ordinary.returncode, ordinary.stderr.decode())
        foreign = Path(self.temporary.name) / "foreign-working-directory"
        foreign.mkdir()
        decoy = foreign / "checkout_package"
        decoy.mkdir()
        (decoy / "__init__.py").write_text('VALUE = "foreign checkout"\n', encoding="utf-8")
        for explicit_root in (False, True):
            for recorded in (False, True):
                with self.subTest(explicit_root=explicit_root, recorded=recorded):
                    command = [sys.executable, "-B", str(ROOT / "scripts/run_validation_unit_tests.py")]
                    current_environment = dict(environment)
                    if explicit_root:
                        command += ["--root", str(self.root)]
                        current_environment["PYTHONPATH"] = str(foreign)
                    receipt = Path(self.temporary.name) / f"packages-{explicit_root}-{recorded}.json"
                    if recorded:
                        command += ["--receipt", str(receipt)]
                    command += ["discover", "-s", "tests", "-p", "test_*.py"]
                    result = subprocess.run(command, cwd=foreign if explicit_root else self.root,
                                            env=current_environment, capture_output=True)
                    self.assertEqual(0, result.returncode, result.stderr.decode())
                    self.assertIn(b"Ran 2 tests", result.stderr)
                    if recorded:
                        evidence = json.loads(receipt.read_text())
                        self.assertEqual(2, evidence["summary"]["tests_run"])
                        self.assertEqual(["test_cases.Cases.test_selected_package", "test_other.OtherCases.test_second_module_import"],
                                         [row["runtime_id"] for row in evidence["cases"]])
                        self.assertEqual(["PASS", "PASS"], [row["status"] for row in evidence["cases"]])
                        self.assertTrue(all(row["runtime_body_verified"] for row in evidence["cases"]))
                        self.assertEqual([], evidence["fixture_errors"])
                        self.assertEqual([], evidence["source_integrity_errors"])
                        self.assertEqual([], evidence["dirty_before"])
                        self.assertEqual([], evidence["dirty_after"])
                    else:
                        self.assertFalse(receipt.exists())

    def test_actual_outcomes_and_source_bodies_preserve_standard_discovery(self):
        self.prepare('''
            import unittest
            print("actual import output")
            class Cases(unittest.TestCase):
                def test_a_pass(self):
                    print("actual test output")
                    self.assertEqual(3, 1 + 2)
                def test_b_failure(self):
                    self.fail("actual failure")
                def test_c_error(self):
                    raise RuntimeError("actual error")
                @unittest.skip("declared skip")
                def test_d_skip(self):
                    self.fail("never entered")
                @unittest.expectedFailure
                def test_e_expected(self):
                    self.fail("declared expected failure")
                @unittest.expectedFailure
                def test_f_unexpected(self):
                    self.assertTrue(True)
        ''')
        result, evidence = self.run_cases()
        ordinary = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
                                  cwd=self.root, capture_output=True)
        self.assertEqual(ordinary.returncode, result.returncode)
        self.assertEqual(1, result.returncode)
        self.assertTrue(evidence["execution_complete"])
        self.assertEqual([], evidence["dirty_before"])
        self.assertEqual([], evidence["dirty_after"])
        self.assertEqual(["PASS", "FAIL", "ERROR", "SKIP", "EXPECTED_FAILURE", "UNEXPECTED_SUCCESS"],
                         [row["status"] for row in evidence["cases"]])
        self.assertEqual([True, True, True, False, True, True],
                         [row["runtime_body_verified"] for row in evidence["cases"]])
        self.assertEqual({"tests_run": 6, "failures": 1, "errors": 1, "skips": 1,
                          "expected_failures": 1, "unexpected_successes": 1, "successful": False}, evidence["summary"])
        for row in evidence["cases"]:
            self.assertEqual((1, 1), (row["starts"], row["stops"]))
            self.assertEqual(row["source_before"], row["source_after"])
        body = 'def test_e_expected(self):\n        self.fail("declared expected failure")'
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), evidence["cases"][4]["source_before"]["body_sha256"])
        self.assertIn(b"actual import output", result.stdout)
        self.assertIn(b"actual test output", result.stdout)
        self.assertIn(b"Ran 6 tests", result.stderr)

    def test_failed_or_skipped_subtests_cannot_become_parent_pass(self):
        self.prepare('''
            import unittest
            class Cases(unittest.TestCase):
                def test_failed(self):
                    for value in (0, 1):
                        with self.subTest(value=value):
                            self.assertEqual(0, value)
                def test_skipped(self):
                    with self.subTest(part="skip"):
                        self.skipTest("partial skip")
        ''')
        result, evidence = self.run_cases()
        self.assertEqual(1, result.returncode)
        self.assertEqual(["FAIL", "SKIP"], [row["status"] for row in evidence["cases"]])
        self.assertEqual(1, evidence["summary"]["failures"])

    def test_rebound_runtime_method_cannot_claim_execution_of_original_ast_body(self):
        for replacement in ('Cases.test_required = lambda self: None',
                            'def load_tests(loader, tests, pattern):\n    case = Cases("test_required")\n    case.test_required = lambda: None\n    return unittest.TestSuite([case])'):
            with self.subTest(replacement=replacement):
                self.prepare('import unittest\nclass Cases(unittest.TestCase):\n    def test_required(self):\n        self.fail("the reviewed body must fail if it actually runs")\n' + replacement + '\n')
                result, evidence = self.run_cases()
                self.assertEqual(0, result.returncode)
                row = evidence["cases"][0]
                self.assertEqual("PASS", row["status"], "Retain actual unittest callback truth")
                self.assertFalse(row["runtime_body_verified"])
                self.assertEqual(row["source_before"], row["source_after"])

    def test_captured_original_method_entry_remains_verified_after_setup_rebind(self):
        self.prepare('''
            import unittest
            class Cases(unittest.TestCase):
                def setUp(self):
                    Cases.test_required = lambda self: None
                def test_required(self):
                    self.assertEqual(8, 2 * 4)
        ''')
        result, evidence = self.run_cases()
        self.assertEqual(0, result.returncode)
        self.assertTrue(evidence["cases"][0]["runtime_body_verified"])

    def test_decorator_requires_actual_direct_body_entry_and_preserves_previous_profile(self):
        self.prepare('''
            import functools
            import sys
            import unittest
            def prior(frame, event, argument):
                pass
            sys.setprofile(prior)
            def forwards(function):
                @functools.wraps(function)
                def wrapped(*args):
                    return function(*args)
                return wrapped
            def bypasses(function):
                @functools.wraps(function)
                def wrapped(*args):
                    return None
                return wrapped
            class Cases(unittest.TestCase):
                @bypasses
                def test_a_bypassed(self):
                    self.fail("must not be attributed to this unexecuted body")
                @forwards
                def test_b_forwarded(self):
                    self.assertIs(sys.getprofile(), prior)
                    self.assertEqual(8, 2 * 4)
        ''')
        result, evidence = self.run_cases()
        self.assertEqual(0, result.returncode)
        self.assertEqual([False, True], [row["runtime_body_verified"] for row in evidence["cases"]])

    def test_displaced_body_observer_keeps_runtime_evidence_unavailable(self):
        self.prepare('''
            import sys
            import unittest
            class Cases(unittest.TestCase):
                def setUp(self):
                    sys.setprofile(None)
                def test_required(self):
                    self.assertEqual(8, 2 * 4)
        ''')
        result, evidence = self.run_cases()
        self.assertEqual(0, result.returncode)
        self.assertFalse(evidence["cases"][0]["runtime_body_verified"])
        self.assertIn("observer was displaced", evidence["cases"][0]["source_error"])

    def test_class_setup_error_retains_not_run_cases_and_fixture_error(self):
        self.prepare('''
            import unittest
            class Cases(unittest.TestCase):
                @classmethod
                def setUpClass(cls):
                    raise RuntimeError("class setup failed")
                def test_never_entered(self):
                    self.fail("must not enter")
        ''')
        result, evidence = self.run_cases()
        ordinary = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"],
                                  cwd=self.root, capture_output=True)
        self.assertEqual(ordinary.returncode, result.returncode)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(ordinary.returncode, evidence["return_code"])
        self.assertTrue(evidence["execution_complete"])
        self.assertEqual(1, evidence["summary"]["errors"])
        self.assertEqual(0, evidence["summary"]["failures"])
        self.assertFalse(evidence["summary"]["successful"])
        self.assertEqual("NOT_RUN", evidence["cases"][0]["status"])
        self.assertEqual((0, 0), (evidence["cases"][0]["starts"], evidence["cases"][0]["stops"]))
        self.assertEqual("ERROR", evidence["fixture_errors"][0]["status"])
        self.assertEqual(0, evidence["summary"]["tests_run"])

    def test_zero_tests_preserves_installed_program_exit(self):
        self.prepare("import unittest\n")
        result, evidence = self.run_cases()
        ordinary = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"],
                                  cwd=self.root, capture_output=True)
        self.assertEqual(ordinary.returncode, result.returncode)
        self.assertEqual(5, result.returncode)
        self.assertEqual([], evidence["cases"])
        self.assertTrue(evidence["execution_complete"])

    def test_duplicate_identity_and_exact_discovery_order_are_retained(self):
        self.prepare('''
            import unittest
            class Cases(unittest.TestCase):
                def test_pass(self):
                    self.assertEqual(6, 2 * 3)
            def load_tests(loader, tests, pattern):
                actual = Cases("test_pass")
                return unittest.TestSuite([actual, actual])
        ''')
        result, evidence = self.run_cases()
        self.assertEqual(0, result.returncode)
        self.assertEqual(2, len(evidence["cases"]))
        self.assertEqual(evidence["cases"][0]["runtime_id"], evidence["cases"][1]["runtime_id"])
        self.assertEqual([(1, 1), (1, 1)], [(row["starts"], row["stops"]) for row in evidence["cases"]])

    def test_source_change_leaves_execution_incomplete_and_fails_wrapper(self):
        self.prepare('''
            import unittest
            from pathlib import Path
            class Cases(unittest.TestCase):
                def test_mutates_source(self):
                    path = Path(__file__)
                    path.write_text(path.read_text() + "\\n# actual mutation\\n")
        ''')
        result, evidence = self.run_cases()
        self.assertEqual(1, result.returncode)
        self.assertFalse(evidence["execution_complete"])
        self.assertIn("Source changed:", evidence["source_integrity_errors"][0])
        self.assertNotEqual(evidence["cases"][0]["source_before"], evidence["cases"][0]["source_after"])

    def test_interrupt_leaves_seeded_incomplete_receipt(self):
        self.prepare('''
            import unittest
            class Cases(unittest.TestCase):
                def test_interrupt(self):
                    raise KeyboardInterrupt("actual interruption")
        ''')
        result, evidence = self.run_cases()
        self.assertNotEqual(0, result.returncode)
        self.assertFalse(evidence["execution_complete"])
        self.assertTrue(evidence["discovery_complete"])
        self.assertEqual("NOT_RUN", evidence["cases"][0]["status"])

    def test_receipt_inside_checkout_is_observed_as_dirty(self):
        self.prepare('''
            import unittest
            class Cases(unittest.TestCase):
                def test_pass(self):
                    self.assertTrue(True)
        ''')
        self.receipt = self.root / "actual-evidence.json"
        _, evidence = self.run_cases()
        self.assertEqual([], evidence["dirty_before"])
        self.assertIn("?? actual-evidence.json", evidence["dirty_after"])

    def test_ast_body_hash_normalizes_lf_and_excludes_decorator(self):
        content = 'import unittest\r\nclass Cases(unittest.TestCase):\r\n    @unittest.skip("x")\r\n    def test_body(self):\r\n        self.assertEqual(2, 1 + 1)\r\n'
        self.source.write_bytes(content.encode())
        actual = recorder.source_receipt(self.root, "tests/test_cases.py", "Cases", "test_body")
        body = 'def test_body(self):\n        self.assertEqual(2, 1 + 1)'
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), actual["body_sha256"])
        self.assertEqual(hashlib.sha256(content.replace("\r\n", "\n").encode()).hexdigest(), actual["source_sha256"])
        self.assertEqual(4, actual["line"])
        with self.assertRaises(ValueError):
            recorder.source_receipt(self.root, "tests/test_cases.py", "Cases", "missing")

    def test_parent_binds_full_combined_transcript_after_process_return(self):
        self.prepare('''
            import unittest
            import sys
            print("actual discovery stdout", flush=True)
            print("actual discovery stderr", file=sys.stderr, flush=True)
            class Cases(unittest.TestCase):
                def test_pass(self):
                    print("actual body stdout", flush=True)
                    print("actual body stderr", file=sys.stderr, flush=True)
                    self.assertEqual(3, 1 + 2)
        ''')
        environment = os.environ.copy()
        environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", GIT_ALLOW_PROTOCOL="file")
        path = Path(self.temporary.name) / "repository.json"
        command = [sys.executable, str(ROOT / "scripts/run_validation_unit_tests.py"), "discover", "-s", "tests", "-p", "test_*.py"]
        return_code, evidence = validator.run_unit_evidence(command, self.root, environment, path)
        self.assertEqual(0, return_code)
        self.assertTrue(evidence["execution_complete"])
        transcript = Path(evidence["transcript_path"]).read_bytes()
        for actual in (b"actual discovery stdout", b"actual discovery stderr", b"actual body stdout",
                       b"actual body stderr", b"Ran 1 test", b"OK"):
            self.assertIn(actual, transcript)
        self.assertEqual(hashlib.sha256(transcript).hexdigest(), evidence["transcript_sha256"])
        self.assertEqual(hashlib.sha256(Path(evidence["receipt_path"]).read_bytes()).hexdigest(), evidence["receipt_sha256"])
        with self.assertRaises(ValueError):
            validator.run_unit_evidence(command, self.root, environment, path)

    def test_report_schema_retains_historical_rows_and_limits_optional_branch_to_units(self):
        schema = json.loads((ROOT / "data/schemas/repository_validation_report_schema.json").read_text())
        row_schema = {"$defs": schema["$defs"], **schema["properties"]["results"]["items"]}
        verifier = Draft202012Validator(row_schema)
        old = {"check_id": "historical_check", "blocking": True, "return_code": 0}
        self.assertEqual([], list(verifier.iter_errors(old)))
        branch = {"execution_complete": True, "receipt_path": "cases.json", "receipt_sha256": "a" * 64,
                  "transcript_path": "full.log", "transcript_sha256": "b" * 64}
        new = {**old, "check_id": "validation_unit_tests", "unit_evidence": branch}
        self.assertEqual([], list(verifier.iter_errors(new)))
        new["check_id"] = "historical_check"
        self.assertTrue(list(verifier.iter_errors(new)))
        new["check_id"] = "validation_unit_tests"
        new["unit_evidence"]["receipt_sha256"] = None
        self.assertTrue(list(verifier.iter_errors(new)))


if __name__ == "__main__":
    unittest.main()
