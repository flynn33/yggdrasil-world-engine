#!/usr/bin/env python3
"""Validate source-truth and Twin Wolf alignment guardrails."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from fnmatch import fnmatch
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
    "forbidden:",
    "forbidden framing",
    "forbidden pattern",
    "forbidden source-truth",
    "non-canonical:",
    "non-canonical framing",
    "reject:",
    "reject_if",
    "rejected:",
    "rejected framing",
    "superseded:",
    "historical:",
    "historical note:",
}

FORBIDDEN_CONTEXT_HEADINGS = {
    "forbidden",
    "historical",
    "non-canonical",
    "reject",
    "rejected",
    "superseded",
}

NON_DESTRUCTIVE_SPEC_KEYS = {
    "fail_on_deleted_protected_paths",
    "max_deleted_files",
    "max_directory_renames",
    "max_files_deleted_without_human_review",
    "max_files_modified_without_human_review",
    "max_modified_files_without_review",
    "max_renamed_files",
    "protected_paths",
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
        required_truth_phrases = required_truth_phrase_map(wolf_rules, errors)
        for truth in wolf_rules.get("required_truths", []):
            if not isinstance(truth, str):
                errors.append(f"{TWIN_WOLF_RULES} required_truths entries must be strings.")
                continue
            phrase = required_truth_phrases.get(truth)
            if not phrase:
                errors.append(f"{TWIN_WOLF_RULES} missing required truth phrase mapping for: {truth}")
                continue
            require(phrase in corpus.lower(), f"Missing required wolf canon truth: {truth}", errors)


def required_truth_phrase_map(wolf_rules: dict, errors: list[str]) -> dict[str, str]:
    phrase_map = wolf_rules.get("required_truth_phrases", {})
    if not isinstance(phrase_map, dict):
        errors.append(f"{TWIN_WOLF_RULES} required_truth_phrases must be an object.")
        return {}
    normalized: dict[str, str] = {}
    for truth, phrase in phrase_map.items():
        if not isinstance(truth, str) or not isinstance(phrase, str) or not phrase.strip():
            errors.append(f"{TWIN_WOLF_RULES} required_truth_phrases entries must map strings to non-empty strings.")
            continue
        normalized[truth] = phrase.strip().lower()
    return normalized


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


def path_matches(path_name: str, pattern: str) -> bool:
    normalized = pattern.rstrip("/")
    if pattern.endswith("/") and path_name.startswith(pattern):
        return True
    return (
        path_name == normalized
        or path_name.startswith(f"{normalized}/")
        or fnmatch(path_name, pattern)
    )


def allowed_forbidden_context(lines: list[str], index: int) -> bool:
    context_lines = [lines[index]]
    for line in reversed(lines[max(0, index - 3) : index]):
        if line.strip():
            context_lines.append(line)
            break
    for line in context_lines:
        normalized = line.lower().strip().lstrip("-* ").strip()
        heading = normalized.lstrip("#").strip().rstrip(":")
        if heading in FORBIDDEN_CONTEXT_HEADINGS:
            return True
        if any(marker in normalized for marker in FORBIDDEN_CONTEXT_MARKERS):
            return True
    return False


def check_forbidden_patterns(
    root: Path,
    patterns: list[str],
    label: str,
    errors: list[str],
    allow_in_paths: list[str] | None = None,
) -> None:
    allow_patterns = allow_in_paths or []
    for path in active_scan_files(root):
        rel = path.relative_to(root).as_posix()
        if rel.startswith("docs/exchange/"):
            continue
        if any(path_matches(rel, pattern) for pattern in allow_patterns):
            continue
        lines = read_text(path).splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            for pattern in patterns:
                if pattern.lower() in lowered and not allowed_forbidden_context(lines, index):
                    errors.append(f"Forbidden {label} in {rel}:{index + 1}: {line.strip()}")


def check_forbidden_language(root: Path, errors: list[str]) -> None:
    data = load_json_checked(root, FORBIDDEN_LANGUAGE, errors)
    if not isinstance(data, dict):
        return
    patterns = forbidden_language_patterns(data, errors)
    check_forbidden_patterns(root, patterns, "source-truth phrase", errors, allowed_path_patterns(data))


def forbidden_language_patterns(data: dict, errors: list[str]) -> list[str]:
    pattern_items = data.get("forbidden_patterns", data.get("patterns", []))
    patterns: list[str] = []
    for index, item in enumerate(pattern_items):
        if not isinstance(item, dict) or not isinstance(item.get("pattern"), str):
            continue
        pattern = item["pattern"].strip()
        if not pattern:
            pattern_id = item.get("id", index)
            errors.append(f"{FORBIDDEN_LANGUAGE} contains empty forbidden pattern: {pattern_id}")
            continue
        patterns.append(pattern)
    return patterns


def allowed_path_patterns(data: dict) -> list[str]:
    return [
        path_name
        for path_name in data.get("allow_in_paths", [])
        if isinstance(path_name, str) and path_name.strip()
    ]


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
        if status.startswith("D") or path_name not in paths:
            paths[path_name] = status
    for status, path_name in git_name_status(root, "--cached"):
        if status.startswith("D") or path_name not in paths:
            paths[path_name] = status
    for status, path_name in git_untracked_paths(root):
        paths.setdefault(path_name, status)
    return [(status, path_name) for path_name, status in paths.items()]


def int_budget_value(data: dict, names: tuple[str, ...], default: int, label: str, errors: list[str]) -> int:
    for name in names:
        if name in data:
            try:
                return int(data[name])
            except (TypeError, ValueError):
                errors.append(f"{label} budget value {name} must be an integer: {data[name]!r}")
                return default
    return default


def protected_deleted_paths(deleted: list[str], protected_paths: list[str]) -> list[str]:
    return [
        path_name
        for path_name in deleted
        if any(path_matches(path_name, protected_path) for protected_path in protected_paths)
    ]


def check_non_destructive_changes(root: Path, data: dict, label: str, errors: list[str]) -> None:
    max_deleted = int_budget_value(
        data,
        ("max_deleted_files", "max_files_deleted_without_human_review"),
        0,
        label,
        errors,
    )
    max_modified = int_budget_value(
        data,
        ("max_modified_files_without_review", "max_files_modified_without_human_review"),
        25,
        label,
        errors,
    )
    max_renames = int_budget_value(data, ("max_directory_renames", "max_renamed_files"), 0, label, errors)
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
    if data.get("fail_on_deleted_protected_paths") is True:
        protected_paths = [
            path_name
            for path_name in data.get("protected_paths", [])
            if isinstance(path_name, str) and path_name.strip()
        ]
        protected_deleted = protected_deleted_paths(deleted, protected_paths)
        require(
            not protected_deleted,
            f"{label} deleted protected paths: {protected_deleted}",
            errors,
        )
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
        for phrase in as_string_list(spec.get(key)):
            normalized = phrase.strip()
            if normalized:
                patterns.append(normalized)
            else:
                errors.append(f"{spec_name} contains empty forbidden phrase in {key}")
    allow_paths = as_string_list(spec.get("allow_in_paths")) + as_string_list(spec.get("allow_historical_paths"))
    check_forbidden_patterns(root, patterns, f"{spec_name} forbidden phrase", errors, allow_paths)


def check_spec(root: Path, spec_name: str, spec: dict, errors: list[str]) -> None:
    for path_name in spec_file_scope(spec):
        require((root / path_name).is_file(), f"{spec_name} missing required file: {path_name}", errors)
    check_required_spec_phrases(root, spec_name, spec, errors)
    check_forbidden_spec_phrases(root, spec_name, spec, errors)
    if has_non_destructive_controls(spec):
        check_non_destructive_changes(root, spec, spec_name, errors)


def has_non_destructive_controls(spec: dict) -> bool:
    return any(key in spec for key in NON_DESTRUCTIVE_SPEC_KEYS)


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
