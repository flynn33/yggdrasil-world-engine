#!/usr/bin/env python3
"""Run the canonical YWE repository check catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

MANIFEST_PATH = "data/validation/repository_checks.json"
ROADMAP_PATH = "data/governance/specification_roadmap.json"
VALID_CONTEXTS = {"local", "pull_request", "push", "manual"}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def infer_context(requested: str | None) -> str:
    if requested:
        return requested
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    if event_name == "pull_request":
        return "pull_request"
    if event_name == "push":
        return "push"
    if event_name == "workflow_dispatch":
        return "manual"
    return "local"


def resolve_base(requested: str | None) -> str:
    if requested:
        return requested
    if os.environ.get("BASE_REF"):
        return os.environ["BASE_REF"]
    if os.environ.get("GITHUB_BASE_REF"):
        return f"origin/{os.environ['GITHUB_BASE_REF']}"
    return "origin/main"


def check_applies(check: dict, context: str) -> bool:
    contexts = set(check.get("contexts", []))
    return "always" in contexts or context in contexts


def select_checks(manifest: dict, groups: set[str], check_ids: set[str], context: str) -> list[dict]:
    selected = []
    for check in manifest.get("checks", []):
        if not check_applies(check, context):
            continue
        if check_ids and check.get("id") not in check_ids:
            continue
        if groups and not groups.intersection(check.get("groups", [])):
            continue
        selected.append(check)
    return selected


def expand_command(command: list[str], root: Path, base: str) -> list[str]:
    replacements = {
        "{python}": sys.executable,
        "{root}": str(root),
        "{base}": base,
    }
    return [replacements.get(token, token) for token in command]


def git_state(root: Path) -> tuple[str, list[str]]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    return revision, status


def validation_report(root: Path, manifest: dict, context: str, groups: list[str],
                      check_ids: list[str], offline: bool) -> dict:
    revision, dirty = git_state(root)
    tools = {"python": platform.python_version()}
    for package in ("jsonschema", "PyYAML", "referencing"):
        try:
            tools[package] = version(package)
        except PackageNotFoundError:
            tools[package] = None
    catalog = (root / MANIFEST_PATH).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    return {
        "artifact_type": "ywe_repository_validation_report",
        "artifact_version": "1.0.0",
        "execution_complete": False,
        "revision": revision,
        "context": context,
        "check_catalog_sha256": hashlib.sha256(catalog.encode("utf-8")).hexdigest(),
        "selection": {"groups": groups, "check_ids": check_ids},
        "offline": {"requested": offline, "git_allow_protocol": "file" if offline else None},
        "dirty_before": dirty,
        "dirty_after": [],
        "tool_versions": tools,
        "results": [],
        "summary": {"passed": 0, "blocking_failures": 0, "advisories": 0},
    }


def save_report(path: Path, report: dict, root: Path) -> None:
    report["execution_complete"] = False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    revision, report["dirty_after"] = git_state(root)
    if revision != report["revision"]:
        raise ValueError("Repository revision changed during validation")
    report["execution_complete"] = True
    # Writing a report inside the checkout must not manufacture clean evidence.
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--group", action="append", default=[])
    parser.add_argument("--check", action="append", default=[])
    parser.add_argument("--context", choices=sorted(VALID_CONTEXTS))
    parser.add_argument("--base")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--report", type=Path, help="Save executed results and checkout evidence as JSON")
    parser.add_argument("--offline", action="store_true", help="Deny remote Git protocols during repository checks")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    context = infer_context(args.context)
    base = resolve_base(args.base)

    try:
        manifest = load_json(root / MANIFEST_PATH)
        roadmap = load_json(root / ROADMAP_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Validation bootstrap failed: {exc}")
        return 1

    checks = select_checks(manifest, set(args.group), set(args.check), context)
    if args.list:
        for check in checks:
            print(f"{check['id']}: {check['name']} [{', '.join(check['groups'])}]")
        return 0

    if not checks:
        print("No repository checks matched the requested selection.")
        return 1

    try:
        report = validation_report(root, manifest, context, args.group, args.check, args.offline) if args.report else None
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Unable to collect validation evidence: {exc}")
        return 1

    print("=" * 64)
    print("Yggdrasil World Engine — Canonical Repository Validation")
    print("=" * 64)
    print(f"Roadmap milestone: {roadmap.get('current_milestone', 'unknown')}")
    print(f"Execution context: {context}")
    print(f"Checks selected: {len(checks)}")
    print()
    sys.stdout.flush()

    environment = os.environ.copy()
    environment.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    if args.offline:
        environment["GIT_ALLOW_PROTOCOL"] = "file"
    passed = 0
    failed = 0
    nonblocking_failed = 0

    for check in checks:
        print(f"--- {check['id']}: {check['name']} ---")
        sys.stdout.flush()
        command = expand_command(check["command"], root, base)
        try:
            result = subprocess.run(command, cwd=root, env=environment, check=False)
            return_code = result.returncode
        except OSError as exc:
            print(f"Unable to run check: {exc}")
            return_code = 1

        if report is not None:
            report["results"].append({
                "check_id": check["id"], "blocking": check.get("blocking", True),
                "return_code": return_code,
            })

        if return_code == 0:
            print(f"PASS: {check['id']}")
            passed += 1
        elif check.get("blocking", True):
            print(f"FAIL: {check['id']}")
            failed += 1
        else:
            print(f"ADVISORY: {check['id']}")
            nonblocking_failed += 1
        print()

    print("=" * 64)
    print(f"Results: {passed} passed, {failed} blocking failures, {nonblocking_failed} advisories")
    print("=" * 64)
    if report is not None:
        report["summary"] = {"passed": passed, "blocking_failures": failed, "advisories": nonblocking_failed}
        try:
            save_report(args.report.resolve(), report, root)
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            print(f"Unable to save validation evidence: {exc}")
            return 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
