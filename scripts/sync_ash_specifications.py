#!/usr/bin/env python3
"""Synchronize the generated ASH specification mirror and pin its source identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


SOURCE_ROOT = Path("core/ash_pattern_engine/canonical")
MIRROR_ROOT = Path("specs")
MANIFEST_PATH = Path("data/governance/ash_dependency_identity.json")
SCHEMA_PATH = "data/schemas/ash_dependency_identity_schema.json"
EXCLUDED_SOURCE_PATHS = ("README.md",)

ARTIFACT_TYPE = "ash_dependency_identity"
ARTIFACT_VERSION = "1.0.0"
DEPENDENCY_ID = "ash_cosmological_model.f2_9.canonical"
SYMBOLIC_GRAMMAR_OWNER = "ash_cosmological_model"
CONSUMERS = ("yggdrasil_world_engine", "ash_pattern_system")
TEXT_NORMALIZATION = "utf8_optional_bom_crlf_cr_to_lf_preserve_final_newline"
AGGREGATE_ALGORITHM = "sha256_sorted_relative_path_nul_file_sha256_lf"
CANONICAL_PROFILE = {
    "field_dimension": 9,
    "state_count": 512,
    "codeword_count": 16,
}
SEMVER = re.compile(
    r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$"
)


class DuplicateKeyError(ValueError):
    """Raised when a JSON document contains a duplicate member name."""


class SynchronizationError(RuntimeError):
    """Raised when synchronization cannot complete without violating policy."""

    def __init__(self, errors: Iterable[str]):
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON member {key!r}")
        result[key] = value
    return result


def normalized_utf8_data(value: bytes, label: str) -> bytes:
    """Return strict UTF-8 with an optional BOM removed and line endings as LF."""
    try:
        text = value.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} is not strict UTF-8: {exc}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(value: bytes, label: str) -> str:
    return hashlib.sha256(normalized_utf8_data(value, label)).hexdigest()


def aggregate_sha256(files: Iterable[dict[str, str]]) -> str:
    """Hash sorted relative-path/NUL/file-hash/LF records deterministically."""
    records = sorted(files, key=lambda item: item["relative_path"])
    payload = b"".join(
        item["relative_path"].encode("utf-8")
        + b"\0"
        + item["sha256"].encode("ascii", errors="strict")
        + b"\n"
        for item in records
    )
    return hashlib.sha256(payload).hexdigest()


def _relative_files(directory: Path) -> dict[str, Path]:
    if not directory.is_dir():
        raise ValueError(f"required directory is missing: {directory.as_posix()}")
    result: dict[str, Path] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symbolic links are not permitted: {path.as_posix()}")
        if not path.is_file():
            continue
        relative_path = path.relative_to(directory).as_posix()
        result[relative_path] = path
    return result


def _source_material(root: Path) -> tuple[dict[str, bytes], list[dict[str, str]]]:
    source_directory = root / SOURCE_ROOT
    source_paths = _relative_files(source_directory)
    for excluded_path in EXCLUDED_SOURCE_PATHS:
        source_paths.pop(excluded_path, None)
    if not source_paths:
        raise ValueError(f"no canonical source files found under {SOURCE_ROOT.as_posix()}")

    normalized_files: dict[str, bytes] = {}
    identities: list[dict[str, str]] = []
    for relative_path, source_path in sorted(source_paths.items()):
        normalized = normalized_utf8_data(
            source_path.read_bytes(),
            f"{SOURCE_ROOT.as_posix()}/{relative_path}",
        )
        normalized_files[relative_path] = normalized
        identities.append(
            {
                "relative_path": relative_path,
                "sha256": hashlib.sha256(normalized).hexdigest(),
            }
        )
    return normalized_files, identities


def _repository_baseline(root: Path) -> str:
    version_path = root / "VERSION"
    try:
        version = normalized_utf8_data(
            version_path.read_bytes(),
            "VERSION",
        ).decode("utf-8").strip()
    except OSError as exc:
        raise ValueError(f"unable to read VERSION: {exc}") from exc
    if SEMVER.fullmatch(version) is None:
        raise ValueError(
            f"VERSION must contain strict MAJOR.MINOR.PATCH SemVer; found {version!r}"
        )
    return version


def expected_manifest(
    root: Path,
    identities: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    if identities is None:
        _normalized_files, identities = _source_material(root)
    sorted_identities = sorted(identities, key=lambda item: item["relative_path"])
    return {
        "schema_ref": SCHEMA_PATH,
        "artifact_type": ARTIFACT_TYPE,
        "artifact_version": ARTIFACT_VERSION,
        "repository_baseline": _repository_baseline(root),
        "dependency_id": DEPENDENCY_ID,
        "symbolic_grammar_owner": SYMBOLIC_GRAMMAR_OWNER,
        "consumers": list(CONSUMERS),
        "canonical_source_root": SOURCE_ROOT.as_posix(),
        "mirror_root": MIRROR_ROOT.as_posix(),
        "excluded_source_paths": list(EXCLUDED_SOURCE_PATHS),
        "text_normalization": TEXT_NORMALIZATION,
        "aggregate_algorithm": AGGREGATE_ALGORITHM,
        "canonical_profile": dict(CANONICAL_PROFILE),
        "files": sorted_identities,
        "aggregate_sha256": aggregate_sha256(sorted_identities),
    }


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_bytes().decode("utf-8-sig", errors="strict"),
            object_pairs_hook=_unique_object,
        )
    except OSError as exc:
        raise ValueError(f"unable to read {path.as_posix()}: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        raise ValueError(f"unable to parse {path.as_posix()}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def _first_difference(actual: Any, expected: Any, location: str = "$") -> str | None:
    if type(actual) is not type(expected):
        return (
            f"{location} has type {type(actual).__name__}; "
            f"expected {type(expected).__name__}"
        )
    if isinstance(expected, dict):
        actual_keys = set(actual)
        expected_keys = set(expected)
        if actual_keys != expected_keys:
            missing = sorted(expected_keys - actual_keys)
            extra = sorted(actual_keys - expected_keys)
            return f"{location} keys differ; missing={missing}, extra={extra}"
        for key in expected:
            difference = _first_difference(actual[key], expected[key], f"{location}.{key}")
            if difference:
                return difference
        return None
    if isinstance(expected, list):
        if len(actual) != len(expected):
            return f"{location} has {len(actual)} items; expected {len(expected)}"
        for index, expected_item in enumerate(expected):
            difference = _first_difference(
                actual[index],
                expected_item,
                f"{location}[{index}]",
            )
            if difference:
                return difference
        return None
    if actual != expected:
        return f"{location} is {actual!r}; expected {expected!r}"
    return None


def synchronization_errors(root: Path) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    try:
        source_material, identities = _source_material(root)
        expected = expected_manifest(root, identities)
    except (OSError, ValueError) as exc:
        return [str(exc)], None

    mirror_directory = root / MIRROR_ROOT
    try:
        mirror_paths = _relative_files(mirror_directory)
    except ValueError as exc:
        errors.append(str(exc))
        mirror_paths = {}

    source_names = set(source_material)
    mirror_names = set(mirror_paths)
    for relative_path in sorted(source_names - mirror_names):
        errors.append(f"missing mirror path: {MIRROR_ROOT.as_posix()}/{relative_path}")
    for relative_path in sorted(mirror_names - source_names):
        errors.append(f"extra mirror path: {MIRROR_ROOT.as_posix()}/{relative_path}")
    for relative_path in sorted(source_names & mirror_names):
        mirror_path = mirror_paths[relative_path]
        try:
            mirror_data = normalized_utf8_data(
                mirror_path.read_bytes(),
                f"{MIRROR_ROOT.as_posix()}/{relative_path}",
            )
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
            continue
        if mirror_data != source_material[relative_path]:
            errors.append(f"stale mirror path: {MIRROR_ROOT.as_posix()}/{relative_path}")

    manifest_path = root / MANIFEST_PATH
    if not manifest_path.is_file():
        errors.append(f"missing dependency identity manifest: {MANIFEST_PATH.as_posix()}")
    else:
        try:
            actual_manifest = _load_json_object(manifest_path)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            difference = _first_difference(actual_manifest, expected)
            if difference:
                errors.append(f"dependency identity manifest is stale: {difference}")
    return errors, expected


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass


def write_synchronized_state(root: Path) -> dict[str, Any]:
    """Refresh generated outputs while leaving the canonical source tree untouched."""
    try:
        source_material, identities = _source_material(root)
        manifest = expected_manifest(root, identities)
    except (OSError, ValueError) as exc:
        raise SynchronizationError([str(exc)]) from exc

    mirror_directory = root / MIRROR_ROOT
    if mirror_directory.exists():
        try:
            mirror_paths = _relative_files(mirror_directory)
        except ValueError as exc:
            raise SynchronizationError([str(exc)]) from exc
    else:
        mirror_paths = {}
    extra_paths = sorted(set(mirror_paths) - set(source_material))
    if extra_paths:
        raise SynchronizationError(
            [
                f"extra mirror path: {MIRROR_ROOT.as_posix()}/{relative_path}"
                for relative_path in extra_paths
            ]
        )

    try:
        for relative_path, normalized_data in sorted(source_material.items()):
            target = mirror_directory / Path(relative_path)
            if target.is_file():
                try:
                    current_bytes = target.read_bytes()
                    current = normalized_utf8_data(
                        current_bytes,
                        f"{MIRROR_ROOT.as_posix()}/{relative_path}",
                    )
                except (OSError, ValueError):
                    current = None
                    current_bytes = None
                if current == normalized_data and current_bytes == normalized_data:
                    continue
            _atomic_write(target, normalized_data)

        manifest_bytes = (
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        _atomic_write(root / MANIFEST_PATH, manifest_bytes)
    except OSError as exc:
        raise SynchronizationError(
            [f"unable to write synchronized ASH outputs: {exc}"]
        ) from exc

    errors, verified_manifest = synchronization_errors(root)
    if errors:
        raise SynchronizationError(errors)
    if verified_manifest is None:
        raise SynchronizationError(["unable to verify synchronized ASH state"])
    return verified_manifest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check or refresh the generated ASH specification mirror and "
            "dependency identity manifest."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail on any mirror or manifest drift")
    mode.add_argument("--write", action="store_true", help="refresh mirrors and the manifest")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the repository containing this script)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.write:
        try:
            manifest = write_synchronized_state(root)
        except SynchronizationError as exc:
            for error in exc.errors:
                print(f"FAIL: {error}", file=sys.stderr)
            return 1
        print(
            "WROTE: synchronized "
            f"{len(manifest['files'])} ASH specification files; "
            f"aggregate {manifest['aggregate_sha256']}"
        )
        return 0

    errors, manifest = synchronization_errors(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    assert manifest is not None
    print(
        "PASS: synchronized "
        f"{len(manifest['files'])} ASH specification files; "
        f"aggregate {manifest['aggregate_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
