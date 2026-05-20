#!/usr/bin/env python3
"""Validate source-truth and Twin Wolf alignment guardrails."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

TEXT_ENCODING = "utf-8-sig"

REQUIRED_ARTIFACTS = "data/validation/required_artifacts.json"
SOURCE_TRUTH_CONTRACT = "data/validation/source_truth_alignment_contract.json"
TWIN_WOLF_RULES = "data/validation/twin_wolf_canon_validation_rules.json"
FORBIDDEN_LANGUAGE = "data/validation/forbidden_language_patterns.json"
NON_DESTRUCTIVE_BUDGET = "data/validation/non_destructive_change_budget.json"
GITHUB_CHECKS_MATRIX = "data/validation/github_checks_matrix.json"

SCAN_PATHS = [
    "README.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "core",
    "docs/architecture",
    "docs/master_specification",
    "lore/wolf_canon",
]

FORBIDDEN_CONTEXT_MARKERS = {
    "forbidden",
    "non-canonical",
    "reject",
    "rejected",
    "rejection",
    "superseded",
    "historical",
    "must not",
    "does not",
    "do not",
    "not the",
    "not a",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding=TEXT_ENCODING)


def load_json(path: Path):
    with path.open(encoding=TEXT_ENCODING) as handle:
        return json.load(handle)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def load_json_checked(root: Path, path_name: str, errors: list[str]):
    path = root / path_name
    if not path.is_file():
        errors.append(f"Missing required JSON file: {path_name}")
        return None
    try:
        return load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {path_name}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        errors.append(f"Unable to read {path_name}: {exc}")
    return None


def text_corpus(root: Path) -> str:
    parts: list[str] = []
    for path_name in dict.fromkeys(SCAN_PATHS):
        path = root / path_name
        if path.is_file():
            parts.append(read_text(path))
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix in {".md", ".json", ".yaml", ".yml"}:
                    parts.append(read_text(child))
    return "\n".join(parts)


def check_required_artifacts(root: Path, errors: list[str]) -> None:
    data = load_json_checked(root, REQUIRED_ARTIFACTS, errors)
    if not isinstance(data, dict):
        return
    for key in ("required_docs", "required_schemas", "required_validation_contracts"):
        values = data.get(key, [])
        if not isinstance(values, list):
            errors.append(f"{REQUIRED_ARTIFACTS} {key} must be a list.")
            continue
        for path_name in values:
            require(isinstance(path_name, str), f"{REQUIRED_ARTIFACTS} {key} entries must be strings.", errors)
            if isinstance(path_name, str):
                require((root / path_name).is_file(), f"Missing source-truth required artifact: {path_name}", errors)


def check_required_language(root: Path, errors: list[str]) -> None:
    corpus = text_corpus(root)
    source_truth = load_json_checked(root, SOURCE_TRUTH_CONTRACT, errors)
    if isinstance(source_truth, dict):
        for phrase in source_truth.get("required_statements", []):
            require(isinstance(phrase, str) and phrase in corpus, f"Missing required source-truth statement: {phrase}", errors)
        forbidden_claims = [
            phrase
            for phrase in source_truth.get("forbidden_claims", [])
            if isinstance(phrase, str)
        ]
        check_forbidden_patterns(root, forbidden_claims, "source-truth forbidden claim", errors)

    wolf_rules = load_json_checked(root, TWIN_WOLF_RULES, errors)
    if isinstance(wolf_rules, dict):
        for phrase in wolf_rules.get("required_canon_phrases", []):
            require(isinstance(phrase, str) and phrase.lower() in corpus.lower(), f"Missing required wolf canon phrase: {phrase}", errors)
        required_truth_phrases = {
            "complementary_non_moral_opposites": "complementary opposites",
            "not_good_and_evil": "not good and evil",
            "not_morality_system": "not a morality system",
            "each_has_what_the_other_needs": "each wolf has what the other needs",
            "physical_companion_presence": "physically walk",
            "quest_assistance": "assist in quests",
            "combat_assistance": "assist in combat",
            "cannot_be_killed": "cannot be killed",
            "temporary_decoherence": "temporarily decohere",
            "return_after_decoherence": "return",
        }
        for truth in wolf_rules.get("required_truths", []):
            phrase = required_truth_phrases.get(truth)
            if phrase:
                require(phrase in corpus.lower(), f"Missing required wolf canon truth: {truth}", errors)


def active_scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for path_name in SCAN_PATHS:
        path = root / path_name
        if path.is_file():
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(path)
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix in {".md", ".json", ".yaml", ".yml"}:
                    resolved = child.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        files.append(child)
    return files


def allowed_forbidden_context(context: str) -> bool:
    lowered = context.lower()
    return any(marker in lowered for marker in FORBIDDEN_CONTEXT_MARKERS)


def check_forbidden_patterns(root: Path, patterns: list[str], label: str, errors: list[str]) -> None:
    for path in active_scan_files(root):
        rel = path.relative_to(root).as_posix()
        if rel.startswith("docs/handoff/"):
            continue
        lines = read_text(path).splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            for pattern in patterns:
                context = "\n".join(lines[max(0, index - 3) : index + 1])
                if pattern.lower() in lowered and not allowed_forbidden_context(context):
                    errors.append(f"Forbidden {label} in {rel}:{index + 1}: {line.strip()}")


def check_forbidden_language(root: Path, errors: list[str]) -> None:
    data = load_json_checked(root, FORBIDDEN_LANGUAGE, errors)
    if not isinstance(data, dict):
        return
    pattern_items = data.get("forbidden_patterns", data.get("patterns", []))
    patterns = [
        item.get("pattern", "")
        for item in pattern_items
        if isinstance(item, dict) and isinstance(item.get("pattern"), str)
    ]
    check_forbidden_patterns(root, patterns, "source-truth phrase", errors)


def git_ref_exists(root: Path, ref: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", ref],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def default_base_ref(root: Path) -> str | None:
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref and git_ref_exists(root, f"origin/{github_base_ref}"):
        return f"origin/{github_base_ref}"
    base_ref = os.environ.get("BASE_REF")
    if base_ref and git_ref_exists(root, base_ref):
        return base_ref
    if git_ref_exists(root, "origin/main"):
        return "origin/main"
    if git_ref_exists(root, "main"):
        return "main"
    return None


def parse_name_status(line: str) -> tuple[str, str] | None:
    parts = line.split("\t")
    if len(parts) < 2:
        return None
    return parts[0], parts[-1]


def git_name_status(root: Path, *args: str) -> list[tuple[str, str]]:
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-status", "--find-renames", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [parsed for line in result.stdout.splitlines() if (parsed := parse_name_status(line)) is not None]


def git_untracked_paths(root: Path) -> list[tuple[str, str]]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [("A", path) for path in result.stdout.splitlines() if path]


def git_change_paths(root: Path, errors: list[str]) -> list[tuple[str, str]]:
    base_ref = default_base_ref(root)
    if base_ref is None:
        errors.append("Unable to resolve base ref for source-truth non-destructive diff.")
        return []
    paths: dict[str, str] = {}
    for status, path_name in git_name_status(root, f"{base_ref}...HEAD"):
        paths[path_name] = status
    for status, path_name in git_name_status(root):
        paths[path_name] = status
    for status, path_name in git_name_status(root, "--cached"):
        paths[path_name] = status
    for status, path_name in git_untracked_paths(root):
        paths.setdefault(path_name, status)
    return [(status, path_name) for path_name, status in paths.items()]


def int_budget_value(data: dict, names: tuple[str, ...], default: int) -> int:
    for name in names:
        if name in data:
            return int(data[name])
    return default


def check_non_destructive_changes(root: Path, data: dict, label: str, errors: list[str]) -> None:
    max_deleted = int_budget_value(data, ("max_deleted_files", "max_files_deleted_without_human_review"), 0)
    max_modified = int_budget_value(
        data,
        ("max_modified_files_without_review", "max_files_modified_without_human_review"),
        25,
    )
    max_renames = int_budget_value(data, ("max_directory_renames", "max_renamed_files"), 0)
    deleted = []
    modified = []
    renamed = []
    for status, path_name in git_change_paths(root, errors):
        if status.startswith("D"):
            deleted.append(path_name)
        elif status.startswith("R"):
            renamed.append(path_name)
        elif not status.startswith(("A", "C")):
            modified.append(path_name)
    require(len(deleted) <= max_deleted, f"{label} file deletions exceed budget {max_deleted}: {deleted}", errors)
    require(len(renamed) <= max_renames, f"{label} file renames exceed budget {max_renames}: {renamed}", errors)
    require(
        len(modified) <= max_modified,
        f"{label} modified files exceed budget {max_modified}: {len(modified)}",
        errors,
    )


def check_non_destructive_diff(root: Path, errors: list[str]) -> None:
    budget = load_json_checked(root, NON_DESTRUCTIVE_BUDGET, errors)
    if isinstance(budget, dict):
        check_non_destructive_changes(root, budget, "Source-truth", errors)


def check_json_integrity(root: Path, errors: list[str]) -> None:
    for path in sorted(root.rglob("*.json")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/"):
            continue
        try:
            load_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON in {rel}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
        except OSError as exc:
            errors.append(f"Unable to read JSON file {rel}: {exc}")


def as_string_list(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def spec_file_scope(spec: dict) -> list[str]:
    paths: list[str] = []
    for key in ("required_files", "target", "targets"):
        paths.extend(as_string_list(spec.get(key)))
    return paths


def spec_haystack(root: Path, spec: dict) -> str:
    paths = spec_file_scope(spec)
    if not paths:
        return text_corpus(root)
    parts = []
    for path_name in paths:
        path = root / path_name
        if path.is_file():
            parts.append(read_text(path))
    return "\n".join(parts)


def check_required_spec_phrases(root: Path, spec_name: str, spec: dict, errors: list[str]) -> None:
    haystack = spec_haystack(root, spec).lower()
    for key in ("required_phrases", "required_terms", "must_include"):
        for phrase in as_string_list(spec.get(key)):
            require(
                phrase.lower() in haystack,
                f"{spec_name} missing required phrase from {key}: {phrase}",
                errors,
            )


def check_forbidden_spec_phrases(root: Path, spec_name: str, spec: dict, errors: list[str]) -> None:
    patterns: list[str] = []
    for key in ("forbidden_phrases", "forbidden_semantics", "forbidden_terms", "forbidden_patterns"):
        patterns.extend(as_string_list(spec.get(key)))
    check_forbidden_patterns(root, patterns, f"{spec_name} forbidden phrase", errors)


def check_spec(root: Path, spec_name: str, spec: dict, errors: list[str]) -> None:
    for path_name in spec_file_scope(spec):
        require((root / path_name).is_file(), f"{spec_name} missing required file: {path_name}", errors)
    check_required_spec_phrases(root, spec_name, spec, errors)
    check_forbidden_spec_phrases(root, spec_name, spec, errors)
    if "max_deleted_files" in spec or "max_modified_files_without_review" in spec:
        check_non_destructive_changes(root, spec, spec_name, errors)


def check_github_checks_matrix(root: Path, errors: list[str]) -> None:
    matrix = load_json_checked(root, GITHUB_CHECKS_MATRIX, errors)
    if not isinstance(matrix, dict):
        return
    checks = matrix.get("checks", [])
    if not isinstance(checks, list):
        errors.append(f"{GITHUB_CHECKS_MATRIX} checks must be a list.")
        return
    for check in checks:
        if not isinstance(check, dict) or not check.get("required"):
            continue
        name = str(check.get("name", "unnamed check"))
        if name == "JSON Integrity":
            check_json_integrity(root, errors)
            continue
        spec_name = check.get("spec")
        if not isinstance(spec_name, str):
            errors.append(f"Required GitHub check lacks executable spec: {name}")
            continue
        spec_path = f"data/validation/{spec_name}"
        spec = load_json_checked(root, spec_path, errors)
        if isinstance(spec, dict):
            check_spec(root, spec_name, spec, errors)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []
    check_required_artifacts(root, errors)
    check_required_language(root, errors)
    check_forbidden_language(root, errors)
    check_non_destructive_diff(root, errors)
    check_github_checks_matrix(root, errors)

    if errors:
        print("Source Truth Alignment check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Source Truth Alignment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
