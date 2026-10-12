#!/usr/bin/env python3
"""Run ordinary unittest discovery once and optionally record actual case evidence."""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import os
import platform
import subprocess
import sys
import types
import unittest
from pathlib import Path

MAPPING_PATH = "docs/design-planning/m3/core-domain/CORE_CANONICAL_INVARIANT_MAP.json"


def normalized_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def source_receipt(root: Path, relative: str, class_name: str, method_name: str) -> dict:
    """Hash a direct method body using the reviewed AST source-segment algorithm."""
    path = (root / relative).resolve()
    if path.relative_to(root.resolve()).as_posix() != relative:
        raise ValueError("Test source path must be canonical and inside the checkout")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=relative)
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name]
    if len(classes) != 1:
        raise ValueError("Test source must contain exactly one direct class")
    methods = [node for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name == method_name]
    if len(methods) != 1:
        raise ValueError("Test source must contain exactly one direct method")
    segment = ast.get_source_segment(source, methods[0])
    if segment is None:
        raise ValueError("Test body source segment is unavailable")
    return {"path": relative, "class": class_name, "method": method_name, "line": methods[0].lineno,
            "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "body_sha256": hashlib.sha256(segment.encode("utf-8")).hexdigest()}


def source_method_code(root: Path, receipt: dict):
    """Compile the read source without executing it to bind actual body entry."""
    path = (root / receipt["path"]).resolve()
    module = compile(path.read_text(encoding="utf-8"), str(path), "exec", dont_inherit=True,
                     optimize=sys.flags.optimize)
    classes = [value for value in module.co_consts if type(value) is types.CodeType and value.co_name == receipt["class"]]
    if len(classes) != 1:
        raise ValueError("Compiled source must contain one direct test class")
    methods = [value for value in classes[0].co_consts if type(value) is types.CodeType and value.co_name == receipt["method"]]
    if len(methods) != 1:
        raise ValueError("Compiled source must contain one direct test method")
    return methods[0]


def git_state(root: Path) -> tuple[str, list[str]]:
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root).decode("utf-8").splitlines()
    return revision, dirty


def iter_cases(suite):
    if isinstance(suite, unittest.TestSuite):
        for item in suite:
            yield from iter_cases(item)
    else:
        yield suite


class CaseEvidence:
    def __init__(self, root: Path, path: Path, argv: list[str]):
        self.root, self.path = root, path
        revision, dirty = git_state(root)
        self.rows = []
        self.indices = {}
        self.current = {}
        self.codes = {}
        self.observers = {}
        self.report = {
            "artifact_type": "ywe_unit_case_evidence", "artifact_version": "1.0.0",
            "execution_complete": False, "revision": revision, "dirty_before": dirty, "dirty_after": [],
            "python_version": platform.python_version(), "argv": argv,
            "offline_git_allow_protocol": os.environ.get("GIT_ALLOW_PROTOCOL"),
            "discovery_complete": False, "cases": self.rows, "fixture_errors": [],
            "source_integrity_errors": [], "summary": None, "return_code": None,
            "discovery_order_sha256": None,
            "mapping_before_sha256": normalized_sha256(root / MAPPING_PATH) if (root / MAPPING_PATH).is_file() else None,
            "mapping_after_sha256": None,
        }
        self.write()

    def write(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.report, indent=2) + "\n", encoding="utf-8")

    def seed(self, suite):
        for test in iter_cases(suite):
            if len(self.rows) >= 16384:
                raise ValueError("Case evidence exceeds the bounded suite limit")
            row = {"runtime_id": test.id(), "status": "NOT_RUN", "starts": 0, "stops": 0,
                   "source_before": None, "source_after": None, "source_error": None,
                   "runtime_body_verified": False}
            try:
                path = Path(inspect.getsourcefile(type(test))).resolve()
                relative = path.relative_to(self.root).as_posix()
                row["source_before"] = source_receipt(self.root, relative, type(test).__name__, test._testMethodName)
                self.codes[len(self.rows)] = source_method_code(self.root, row["source_before"])
            except (OSError, TypeError, ValueError, SyntaxError) as exc:
                row["source_error"] = type(exc).__name__ + ": " + str(exc)
            self.indices.setdefault(id(test), []).append(len(self.rows))
            self.rows.append(row)
        self.report["discovery_complete"] = True
        self.report["discovery_order_sha256"] = hashlib.sha256(json.dumps(
            [row["runtime_id"] for row in self.rows], separators=(",", ":")).encode("utf-8")).hexdigest()
        self.write()

    def start(self, test):
        indices = self.indices.get(id(test), [])
        index = next((i for i in indices if self.rows[i]["starts"] == 0), None)
        if index is None:
            self.report["fixture_errors"].append({"runtime_id": test.id(), "status": "UNSEEDED_START"})
            return
        self.current[id(test)] = index
        self.rows[index]["starts"] += 1
        code = self.codes.get(index)
        if code is not None:
            previous = sys.getprofile()
            if previous is not None and not callable(previous):
                self.rows[index]["source_error"] = "Existing profiler cannot be composed; actual test body remains unverified"
                return

            def observe(frame, event, argument):
                if (event == "call" and frame.f_code.co_qualname == code.co_qualname
                        and frame.f_code == code):
                    self.rows[index]["runtime_body_verified"] = True
                    self.observers[index] = (None, previous)
                    sys.setprofile(previous)
                if previous is not None:
                    previous(frame, event, argument)

            self.observers[index] = (observe, previous)
            sys.setprofile(observe)

    def outcome(self, test, status):
        parent = getattr(test, "test_case", test)
        index = self.current.get(id(parent))
        if index is None:
            self.report["fixture_errors"].append({"runtime_id": test.id(), "status": status})
            return
        row = self.rows[index]
        # A successful outer method cannot erase a skipped or failed subtest.
        if row["status"] in {"NOT_RUN", "PASS"} or status in {"FAIL", "ERROR"}:
            row["status"] = status

    def stop(self, test):
        index = self.current.pop(id(test), None)
        if index is not None:
            observer = self.observers.pop(index, None)
            if observer is not None:
                observe, previous = observer
                if observe is None:
                    pass  # The exact reviewed method body already entered.
                elif sys.getprofile() is observe:
                    sys.setprofile(previous)
                else:
                    self.rows[index]["runtime_body_verified"] = False
                    self.rows[index]["source_error"] = "Actual test body observer was displaced during execution"
            self.rows[index]["stops"] += 1

    def finish(self, result, return_code):
        errors = self.report["source_integrity_errors"]
        for row in self.rows:
            before = row["source_before"]
            if before is None:
                continue
            try:
                row["source_after"] = source_receipt(self.root, before["path"], before["class"], before["method"])
                if row["source_after"] != before:
                    errors.append("Source changed: " + row["runtime_id"])
            except (OSError, ValueError, SyntaxError) as exc:
                errors.append("Source readback unavailable: " + row["runtime_id"] + ": " + str(exc))
        revision, self.report["dirty_after"] = git_state(self.root)
        if revision != self.report["revision"]:
            errors.append("Repository revision changed during unit execution")
        if self.report["mapping_before_sha256"] is not None:
            self.report["mapping_after_sha256"] = normalized_sha256(self.root / MAPPING_PATH)
            if self.report["mapping_before_sha256"] != self.report["mapping_after_sha256"]:
                errors.append("Conformance mapping changed during unit execution")
        self.report["return_code"] = 1 if errors else return_code
        self.report["summary"] = {"tests_run": result.testsRun, "failures": len(result.failures),
            "errors": len(result.errors), "skips": len(result.skipped),
            "expected_failures": len(result.expectedFailures), "unexpected_successes": len(result.unexpectedSuccesses),
            "successful": result.wasSuccessful()}
        self.report["execution_complete"] = not errors
        self.write()


class EvidenceResult(unittest.TextTestResult):
    evidence: CaseEvidence

    def startTest(self, test):
        self.evidence.start(test)
        super().startTest(test)

    def stopTest(self, test):
        self.evidence.stop(test)
        super().stopTest(test)

    def addSuccess(self, test):
        self.evidence.outcome(test, "PASS")
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.evidence.outcome(test, "FAIL")
        super().addFailure(test, err)

    def addError(self, test, err):
        self.evidence.outcome(test, "ERROR")
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.evidence.outcome(test, "SKIP")
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self.evidence.outcome(test, "EXPECTED_FAILURE")
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self.evidence.outcome(test, "UNEXPECTED_SUCCESS")
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self.evidence.outcome(test, "FAIL" if issubclass(err[0], test.failureException) else "ERROR")
        super().addSubTest(test, subtest, err)


class EvidenceProgram(unittest.TestProgram):
    def __init__(self, evidence, **kwargs):
        self.evidence = evidence
        super().__init__(**kwargs)

    def runTests(self):
        self.evidence.seed(self.test)
        evidence = self.evidence

        class BoundResult(EvidenceResult):
            pass

        BoundResult.evidence = evidence

        class BoundRunner(unittest.TextTestRunner):
            resultclass = BoundResult

        self.testRunner = BoundRunner
        try:
            super().runTests()
        except SystemExit as exc:
            evidence.finish(self.result, exc.code)
            if evidence.report["source_integrity_errors"]:
                raise SystemExit(1) from None
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--receipt", type=Path)
    args, unit_args = parser.parse_known_args(argv)
    root = (args.root or Path.cwd()).resolve()
    if args.root:
        os.chdir(root)
    # Match python -m unittest: imports resolve from the selected checkout first.
    sys.path.insert(0, str(root))
    unit_args = unit_args or ["discover", "-s", "tests", "-p", "test_*.py"]
    unit_argv = [str(Path(__file__)), *unit_args]
    if args.receipt is None:
        unittest.TestProgram(module=None, argv=unit_argv)
    else:
        evidence = CaseEvidence(root, args.receipt.resolve(), unit_args)
        EvidenceProgram(evidence, module=None, argv=unit_argv)


if __name__ == "__main__":
    main()
