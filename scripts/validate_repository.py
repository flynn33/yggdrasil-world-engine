#!/usr/bin/env python3
"""Run the canonical YWE repository check catalog."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--group", action="append", default=[])
    parser.add_argument("--check", action="append", default=[])
    parser.add_argument("--context", choices=sorted(VALID_CONTEXTS))
    parser.add_argument("--base")
    parser.add_argument("--list", action="store_true")
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
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
