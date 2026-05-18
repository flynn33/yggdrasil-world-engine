#!/usr/bin/env python3
"""Validate Phase 10 Player Runtime State v1 package artifacts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

TEXT_ENCODING = "utf-8-sig"
REQUIRED_ARTIFACTS = "data/validation/required_phase_10_artifacts.json"

SPEC_PATHS = {
    "runtime_schema": "data/validation/check_player_runtime_state_schema.spec.json",
    "branch_refs": "data/validation/check_player_state_branch_refs.spec.json",
    "celestial_identity": "data/validation/check_celestial_identity_no_upfront_reveal.spec.json",
    "wolf_resonance": "data/validation/check_wolf_non_morality_state.spec.json",
    "authority_role": "data/validation/check_ash_pattern_component_role_phase_10.spec.json",
    "platform_code": "data/validation/check_no_platform_runtime_code_phase_10.spec.json",
    "non_destructive": "data/validation/check_non_destructive_diff_phase_10.spec.json",
}

AUTHORITY_SCAN_PATHS = [
    "docs/architecture/player_runtime_state_contract.md",
    "docs/architecture/player_state_asp_resilience_contract.md",
    "docs/master_specification/YWE_MASTER_SPECIFICATION.md",
    "data/schemas/README.md",
]


def relative_name(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding=TEXT_ENCODING)


def load_json_checked(root: Path, rel_path: str, errors: list[str]) -> Any | None:
    path = root / rel_path
    if not path.is_file():
        errors.append(f"Missing required JSON file: {rel_path}")
        return None
    try:
        return json.loads(path.read_text(encoding=TEXT_ENCODING))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {rel_path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        errors.append(f"Unable to read {rel_path}: {exc}")
    return None


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def iter_schema_terms(value: Any, under_forbidden: bool = False):
    if isinstance(value, dict):
        for key, child in value.items():
            child_under_forbidden = under_forbidden or key == "forbidden"
            if not child_under_forbidden:
                yield key
                if key == "const" and isinstance(child, str):
                    yield child
                elif key in {"enum", "required", "default"} and isinstance(child, list):
                    for item in child:
                        if isinstance(item, str):
                            yield item
            yield from iter_schema_terms(child, child_under_forbidden)
    elif isinstance(value, list):
        for child in value:
            yield from iter_schema_terms(child, under_forbidden)


def load_specs(root: Path, errors: list[str]) -> dict[str, Any]:
    specs: dict[str, Any] = {}
    for name, rel_path in SPEC_PATHS.items():
        spec = load_json_checked(root, rel_path, errors)
        if spec is not None:
            specs[name] = spec
    return specs


def check_required_artifacts(root: Path, errors: list[str]) -> None:
    contract = load_json_checked(root, REQUIRED_ARTIFACTS, errors)
    if contract is None:
        return

    for section in ("required_markdown", "required_json"):
        for rel_path in contract.get(section, []):
            require((root / rel_path).is_file(), f"Missing Phase 10 artifact: {rel_path}", errors)


def check_runtime_schema(root: Path, spec: dict[str, Any], errors: list[str]) -> None:
    target = spec.get("target", "data/schemas/player_runtime_state_schema.json")
    schema = load_json_checked(root, target, errors)
    if schema is None:
        return

    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    for field in spec.get("required_properties", []):
        require(field in properties, f"{target} missing property: {field}", errors)
        require(field in required, f"{target} must require property: {field}", errors)

    authority_role = (
        properties.get("authority", {})
        .get("properties", {})
        .get("ash_pattern_system_role", {})
        .get("const", "")
    )
    require("YWE component" in authority_role, f"{target} must keep ASH Pattern System in YWE component role.", errors)

    update_control = properties.get("update_control", {}).get("properties", {})
    require(
        update_control.get("requires_update_packet", {}).get("const") is True,
        f"{target} must require update packets for state mutation.",
        errors,
    )
    require(
        update_control.get("allowed_update_packet_schema", {}).get("const") == "ywe.player_state_update_packet.v1",
        f"{target} must reference ywe.player_state_update_packet.v1.",
        errors,
    )


def parse_json_target(rel_path: str, text: str, errors: list[str]) -> Any | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {rel_path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    return None


def load_check_targets(root: Path, targets: list[str], errors: list[str]) -> list[tuple[str, str, Any | None]]:
    loaded_targets: list[tuple[str, str, Any | None]] = []
    for rel_path in targets:
        if not rel_path:
            continue
        path = root / rel_path
        if not path.is_file():
            errors.append(f"Missing check target: {rel_path}")
            continue
        text = read_text(path)
        parsed = parse_json_target(rel_path, text, errors) if rel_path.endswith(".json") else None
        loaded_targets.append((rel_path, text, parsed))
    return loaded_targets


def check_required_terms(root: Path, spec: dict[str, Any], errors: list[str]) -> None:
    loaded_targets = load_check_targets(root, spec.get("targets") or [spec.get("target")], errors)
    target_texts = [(rel_path, text) for rel_path, text, _ in loaded_targets]
    target_json_values = [(rel_path, parsed) for rel_path, _, parsed in loaded_targets if parsed is not None]
    combined = "\n".join(text for _, text in target_texts)
    schema_terms = {term for _, data in target_json_values for term in iter_schema_terms(data)}
    all_targets_are_json = bool(target_texts) and len(target_json_values) == len(target_texts)
    for term in spec.get("required_terms", []) + spec.get("must_include", []):
        if all_targets_are_json:
            require(
                term in schema_terms,
                f"Missing required Phase 10 schema construct `{term}` in {', '.join(t for t, _ in target_texts)}",
                errors,
            )
        else:
            require(term in combined, f"Missing required Phase 10 term `{term}` in {', '.join(t for t, _ in target_texts)}", errors)

    for term in spec.get("forbidden_terms", []):
        require(term not in schema_terms, f"Forbidden term used as active schema construct: {term}", errors)


def check_celestial_initial_state(root: Path, errors: list[str]) -> None:
    example_path = "examples/player_runtime_state/player_runtime_state_initial_mortal_veiled.example.json"
    example = load_json_checked(root, example_path, errors)
    if example is None:
        return
    require(example.get("state_lifecycle") == "initial", f"{example_path} must declare state_lifecycle as initial.", errors)
    initial_state = example.get("identity", {}).get("celestial_identity_initial_state")
    require(initial_state == "veiled", f"{example_path} must start celestial identity as veiled.", errors)


def check_authority_role(root: Path, spec: dict[str, Any], errors: list[str]) -> None:
    text = "\n".join(read_text(root / rel_path) for rel_path in AUTHORITY_SCAN_PATHS if (root / rel_path).is_file())
    required_phrase = spec.get("required_phrase")
    if required_phrase:
        require(required_phrase in text, f"Missing required authority phrase: {required_phrase}", errors)
    for phrase in spec.get("forbidden_phrases", []):
        require(phrase not in text, f"Forbidden authority phrase found: {phrase}", errors)


def git_ref_exists(root: Path, ref: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", ref],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0


def git_fetch_origin_branch(root: Path, branch: str) -> bool:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "fetch",
                "--no-tags",
                "--depth=1",
                "origin",
                f"{branch}:refs/remotes/origin/{branch}",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0


def default_base_ref(root: Path) -> str | None:
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        github_base_candidate = f"origin/{github_base_ref}"
        if git_ref_exists(root, github_base_candidate):
            return github_base_candidate
        if git_fetch_origin_branch(root, github_base_ref) and git_ref_exists(root, github_base_candidate):
            return github_base_candidate

    base_ref = os.environ.get("BASE_REF")
    if base_ref:
        if git_ref_exists(root, base_ref):
            return base_ref
        if base_ref.startswith("origin/"):
            branch = base_ref.removeprefix("origin/")
            if git_fetch_origin_branch(root, branch) and git_ref_exists(root, base_ref):
                return base_ref

    if git_ref_exists(root, "origin/main"):
        return "origin/main"
    if git_fetch_origin_branch(root, "main") and git_ref_exists(root, "origin/main"):
        return "origin/main"
    if git_ref_exists(root, "main"):
        return "main"
    return None


def parse_name_status(line: str) -> tuple[str, str] | None:
    parts = line.split("\t")
    if len(parts) < 2:
        return None
    status = parts[0]
    path = parts[-1]
    return status, path


def git_diff_paths(root: Path, base_ref: str, head_ref: str = "HEAD") -> list[tuple[str, str]]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-status", "--find-renames", f"{base_ref}...{head_ref}"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    paths: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        parsed = parse_name_status(line)
        if parsed is not None:
            paths.append(parsed)
    return paths


def git_change_paths(root: Path, errors: list[str]) -> list[tuple[str, str]]:
    paths: dict[str, str] = {}
    base_ref = default_base_ref(root)
    if not base_ref:
        message = "Unable to resolve git base ref for Phase 10 diff checks."
        if message not in errors:
            errors.append(message)
        return []
    for status, path in git_diff_paths(root, base_ref):
        paths[path] = status
    return [(status, path) for path, status in paths.items()]


def check_no_platform_code(root: Path, spec: dict[str, Any], errors: list[str]) -> None:
    forbidden_extensions = set(spec.get("forbidden_extensions", []))
    for status, rel_path in git_change_paths(root, errors):
        is_added = status.startswith("A")
        if not is_added:
            continue
        suffix = Path(rel_path).suffix
        if suffix in forbidden_extensions:
            errors.append(f"Phase 10 added forbidden platform/code file: {rel_path}")


def check_non_destructive_diff(root: Path, spec: dict[str, Any], errors: list[str]) -> None:
    statuses = git_change_paths(root, errors)
    deleted = [path for status, path in statuses if status.startswith("D")]
    renamed_or_copied = [path for status, path in statuses if status.startswith(("R", "C"))]
    existing_touched = [
        path
        for status, path in statuses
        if not status.startswith(("A", "D", "R", "C"))
    ]

    max_deleted = int(spec.get("max_existing_file_deletions", 0))
    max_renamed = int(spec.get("max_directory_renames", 0))
    max_touched = int(spec.get("max_existing_files_touched_without_review", 25))
    require(len(deleted) <= max_deleted, f"Existing file deletions exceed budget: {deleted}", errors)
    require(
        len(renamed_or_copied) <= max_renamed,
        f"Renamed or copied paths exceed budget {max_renamed}: {renamed_or_copied}",
        errors,
    )
    require(
        len(existing_touched) <= max_touched,
        f"Existing files touched exceed budget {max_touched}: {len(existing_touched)}",
        errors,
    )


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []

    specs = load_specs(root, errors)
    check_required_artifacts(root, errors)

    if "runtime_schema" in specs:
        check_runtime_schema(root, specs["runtime_schema"], errors)
    if "branch_refs" in specs:
        check_required_terms(root, specs["branch_refs"], errors)
    if "celestial_identity" in specs:
        check_required_terms(root, specs["celestial_identity"], errors)
    if "wolf_resonance" in specs:
        check_required_terms(root, specs["wolf_resonance"], errors)
    if "authority_role" in specs:
        check_authority_role(root, specs["authority_role"], errors)
    if "platform_code" in specs:
        check_no_platform_code(root, specs["platform_code"], errors)
    if "non_destructive" in specs:
        check_non_destructive_diff(root, specs["non_destructive"], errors)
    check_celestial_initial_state(root, errors)

    if errors:
        print("Player Runtime State check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Player Runtime State check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
