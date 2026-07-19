#!/usr/bin/env python3
"""Update every repository-baseline mirror from canonical VERSION state."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROADMAP_PATH = "data/governance/specification_roadmap.json"
CLASSIFICATION_PATH = "data/governance/artifact_classification_manifest.json"
SCOPE_PATH = "data/governance/scope_partition_manifest.json"
TRUTH_PATH = "data/governance/repository_truth_manifest.json"
RELEASE_POLICY_PATH = "data/governance/release_publication_policy.json"
PROMISE_PATH = "data/governance/public_promise_register.json"
DEBT_PATH = "data/validation/repository_quality_debt_inventory.json"
M0_EVIDENCE_PATH = "data/governance/m0_acceptance_evidence.json"

BASELINE_MANIFEST_PATHS = (
    CLASSIFICATION_PATH,
    SCOPE_PATH,
    TRUTH_PATH,
    RELEASE_POLICY_PATH,
    PROMISE_PATH,
    DEBT_PATH,
)
SEMVER = re.compile(
    r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$"
)


class DuplicateKeyError(ValueError):
    """Raised when a JSON document contains a duplicate member name."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"Duplicate JSON member: {key}")
        result[key] = value
    return result


def load_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            data.decode("utf-8-sig", errors="strict"),
            object_pairs_hook=_unique_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        raise ValueError(f"Unable to parse {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def load_json(path: Path) -> dict[str, Any]:
    return load_json_bytes(path.read_bytes(), str(path))


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(json_bytes(value))


def normalized_utf8_data(value: bytes) -> bytes:
    text = value.decode("utf-8-sig", errors="strict")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(normalized_utf8_data(value)).hexdigest()


def normalized_text_sha256(path: Path) -> str:
    return normalized_bytes_sha256(path.read_bytes())


def reviewed_surface_digest(entries: Iterable[dict[str, Any]]) -> str:
    payload = b"".join(
        str(entry.get("path", "")).encode("utf-8")
        + b"\t"
        + str(entry.get("sha256", "")).encode("ascii", errors="strict")
        + b"\n"
        for entry in sorted(entries, key=lambda item: item.get("path", ""))
    )
    return hashlib.sha256(payload).hexdigest()


def _list_index(container: list[Any], segment: str, dotted_path: str) -> int:
    if not segment.isdigit():
        raise KeyError(f"Expected a numeric list segment in {dotted_path!r}; found {segment!r}")
    index = int(segment)
    if index >= len(container):
        raise KeyError(f"List index {index} is out of range in {dotted_path!r}")
    return index


def dotted_value(value: Any, dotted_path: str) -> Any:
    if not dotted_path:
        raise KeyError("A dotted field path is required")
    current = value
    for segment in dotted_path.split("."):
        if isinstance(current, dict):
            if segment not in current:
                raise KeyError(f"Missing field segment {segment!r} in {dotted_path!r}")
            current = current[segment]
        elif isinstance(current, list):
            current = current[_list_index(current, segment, dotted_path)]
        else:
            raise KeyError(f"Cannot traverse field segment {segment!r} in {dotted_path!r}")
    return current


def set_dotted_value(value: Any, dotted_path: str, replacement: str) -> None:
    if not dotted_path:
        raise KeyError("A dotted field path is required")
    segments = dotted_path.split(".")
    current = value
    for segment in segments[:-1]:
        if isinstance(current, dict):
            if segment not in current:
                raise KeyError(f"Missing field segment {segment!r} in {dotted_path!r}")
            current = current[segment]
        elif isinstance(current, list):
            current = current[_list_index(current, segment, dotted_path)]
        else:
            raise KeyError(f"Cannot traverse field segment {segment!r} in {dotted_path!r}")
    final_segment = segments[-1]
    if isinstance(current, dict):
        if final_segment not in current:
            raise KeyError(f"Missing field segment {final_segment!r} in {dotted_path!r}")
        current[final_segment] = replacement
    elif isinstance(current, list):
        current[_list_index(current, final_segment, dotted_path)] = replacement
    else:
        raise KeyError(f"Cannot set field segment {final_segment!r} in {dotted_path!r}")


def repository_file(root: Path, relative_path: Any, label: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError(f"{label} must be a non-empty repository-relative path")
    if "\\" in relative_path:
        raise ValueError(f"{label} must use forward slashes: {relative_path!r}")
    candidate = Path(relative_path)
    if candidate.is_absolute() or candidate.drive or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ValueError(f"{label} is not a safe repository-relative path: {relative_path!r}")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the repository root: {relative_path!r}") from exc
    if not resolved.is_file():
        raise ValueError(f"{label} does not exist as a file: {relative_path!r}")
    return resolved


def _require_semver(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SEMVER.fullmatch(value):
        raise ValueError(f"{label} must use MAJOR.MINOR.PATCH; found {value!r}")
    return value


def _require_top_level_baseline(document: dict[str, Any], old_version: str, label: str) -> None:
    if document.get("repository_baseline") != old_version:
        raise ValueError(
            f"{label} repository_baseline is stale: "
            f"{document.get('repository_baseline')!r}; expected {old_version!r}"
        )


def _validate_truth_baseline(document: dict[str, Any], old_version: str) -> None:
    baseline = document.get("repository_baseline")
    if not isinstance(baseline, dict) or baseline.get("canonical_source") != "VERSION":
        raise ValueError("Repository truth manifest must identify VERSION as its canonical source")
    if baseline.get("value") != old_version:
        raise ValueError("Repository truth manifest baseline value is stale")
    mirrors = baseline.get("mirrors")
    if not isinstance(mirrors, list) or not mirrors:
        raise ValueError("Repository truth manifest must contain at least one baseline mirror")
    for index, mirror in enumerate(mirrors):
        if not isinstance(mirror, dict) or mirror.get("value") != old_version:
            raise ValueError(f"Repository truth baseline mirror {index} is stale or malformed")


def _validate_release_baseline(document: dict[str, Any], old_version: str) -> None:
    baseline = document.get("repository_baseline")
    if not isinstance(baseline, dict) or baseline.get("canonical_source") != "VERSION":
        raise ValueError("Release policy must identify VERSION as its canonical source")
    if baseline.get("value") != old_version:
        raise ValueError("Release policy repository baseline is stale")


def _validate_sensitive_hashes(root: Path, classification: dict[str, Any]) -> None:
    if classification.get("sensitive_source_hash_algorithm") != "sha256_utf8_lf_normalized":
        raise ValueError("Classification sensitive sources use an unsupported hash algorithm")
    sources = classification.get("sensitive_sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("Classification manifest must contain sensitive sources")
    seen: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"Classification sensitive source {index} is malformed")
        relative_path = source.get("path")
        if relative_path in seen:
            raise ValueError(f"Classification sensitive source is duplicated: {relative_path}")
        seen.add(relative_path)
        if relative_path == CLASSIFICATION_PATH:
            raise ValueError("Classification manifest cannot hash itself as a sensitive source")
        path = repository_file(root, relative_path, "Classification sensitive source")
        try:
            actual = normalized_text_sha256(path)
        except UnicodeDecodeError as exc:
            raise ValueError(f"Classification sensitive source is not strict UTF-8: {relative_path}") from exc
        if source.get("sha256") != actual:
            raise ValueError(f"Classification sensitive source hash is stale: {relative_path}")


def _validate_reviewed_surface_hashes(root: Path, promises: dict[str, Any]) -> None:
    surfaces = promises.get("reviewed_surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise ValueError("Public promise register must contain reviewed surfaces")
    seen: set[str] = set()
    for index, surface in enumerate(surfaces):
        if not isinstance(surface, dict):
            raise ValueError(f"Reviewed surface {index} is malformed")
        relative_path = surface.get("path")
        if relative_path in seen:
            raise ValueError(f"Reviewed public surface is duplicated: {relative_path}")
        seen.add(relative_path)
        if relative_path in {PROMISE_PATH, CLASSIFICATION_PATH}:
            raise ValueError(f"Reviewed public surface creates a derived-hash cycle: {relative_path}")
        path = repository_file(root, relative_path, "Reviewed public surface")
        try:
            actual = normalized_text_sha256(path)
        except UnicodeDecodeError as exc:
            raise ValueError(f"Reviewed public surface is not strict UTF-8: {relative_path}") from exc
        if surface.get("sha256") != actual:
            raise ValueError(f"Reviewed public surface hash is stale: {relative_path}")
    if promises.get("reviewed_surface_aggregate_sha256") != reviewed_surface_digest(surfaces):
        raise ValueError("Public promise reviewed-surface aggregate hash is stale")


def _staged_bytes(path: Path, updates: dict[Path, bytes]) -> bytes:
    return updates[path] if path in updates else path.read_bytes()


def _prepare_roadmap_source_updates(
    root: Path,
    roadmap: dict[str, Any],
    old_version: str,
    new_version: str,
    updates: dict[Path, bytes],
) -> None:
    sources = roadmap.get("version_sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("Roadmap version_sources must be a non-empty array")
    canonical_entries = [
        source
        for source in sources
        if isinstance(source, dict) and source.get("path") == "VERSION" and source.get("kind") == "plain"
    ]
    if len(canonical_entries) != 1:
        raise ValueError("Roadmap must declare canonical VERSION exactly once as a plain source")

    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"Roadmap version source {index} is malformed")
        relative_path = source.get("path")
        path = repository_file(root, relative_path, f"Roadmap version source {index}")
        kind = source.get("kind")
        current_bytes = _staged_bytes(path, updates)
        if kind == "plain":
            try:
                actual = current_bytes.decode("utf-8-sig", errors="strict").strip()
            except UnicodeDecodeError as exc:
                raise ValueError(f"Plain version source is not strict UTF-8: {relative_path}") from exc
            if actual != old_version:
                raise ValueError(
                    f"Plain version source {relative_path} contains {actual!r}; expected {old_version!r}"
                )
            updates[path] = (new_version + "\n").encode("utf-8")
        elif kind == "json_field":
            field = source.get("field")
            if not isinstance(field, str) or not field:
                raise ValueError(f"JSON version source lacks a field: {relative_path}")
            document = load_json_bytes(current_bytes, str(relative_path))
            try:
                actual = dotted_value(document, field)
            except KeyError as exc:
                raise ValueError(f"JSON version source has an invalid field {relative_path}#{field}: {exc}") from exc
            if actual != old_version:
                raise ValueError(
                    f"JSON version source {relative_path}#{field} contains {actual!r}; "
                    f"expected {old_version!r}"
                )
            set_dotted_value(document, field, new_version)
            updates[path] = json_bytes(document)
        elif kind == "text_template":
            template = source.get("template")
            if not isinstance(template, str) or "{version}" not in template:
                raise ValueError(f"Text version source has an invalid template: {relative_path}")
            try:
                text = current_bytes.decode("utf-8-sig", errors="strict")
            except UnicodeDecodeError as exc:
                raise ValueError(f"Text version source is not strict UTF-8: {relative_path}") from exc
            old_marker = template.format(version=old_version)
            new_marker = template.format(version=new_version)
            marker_count = text.count(old_marker)
            if marker_count != 1:
                raise ValueError(
                    f"Version marker must occur exactly once in {relative_path}: "
                    f"{old_marker!r}; found {marker_count}"
                )
            updates[path] = text.replace(old_marker, new_marker, 1).encode("utf-8")
        else:
            raise ValueError(f"Unknown version source kind for {relative_path}: {kind!r}")


def _stage_file(path: Path, data: bytes) -> Path:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.version-update-",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, path.stat().st_mode)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return temporary_path


def _apply_updates(updates: dict[Path, bytes]) -> None:
    ordered = sorted(updates.items(), key=lambda item: item[0].as_posix())
    originals = {path: path.read_bytes() for path, _ in ordered}
    staged: dict[Path, Path] = {}
    replaced: list[Path] = []
    try:
        for path, data in ordered:
            staged[path] = _stage_file(path, data)
        for path, _ in ordered:
            os.replace(staged[path], path)
            replaced.append(path)
    except Exception as exc:
        rollback_errors: list[str] = []
        for path in reversed(replaced):
            try:
                replacement = _stage_file(path, originals[path])
                os.replace(replacement, path)
            except Exception as rollback_exc:
                rollback_errors.append(f"{path}: {rollback_exc}")
        if rollback_errors:
            raise RuntimeError(
                f"Version update failed and rollback was incomplete: {rollback_errors}"
            ) from exc
        raise
    finally:
        for temporary_path in staged.values():
            temporary_path.unlink(missing_ok=True)


def update_version_references(root: Path, new_version: str) -> tuple[str, str]:
    _require_semver(new_version, "New version")
    root = root.resolve()
    version_path = repository_file(root, "VERSION", "Canonical VERSION")
    try:
        old_version = version_path.read_bytes().decode("utf-8-sig", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise ValueError("Canonical VERSION is not strict UTF-8") from exc
    _require_semver(old_version, "Canonical VERSION")

    roadmap_path = repository_file(root, ROADMAP_PATH, "Roadmap")
    roadmap = load_json(roadmap_path)
    if roadmap.get("repository_baseline") != old_version:
        raise ValueError("Roadmap repository_baseline does not match canonical VERSION")

    manifest_paths = {
        relative_path: repository_file(root, relative_path, "Required baseline manifest")
        for relative_path in BASELINE_MANIFEST_PATHS
    }
    originals = {relative_path: load_json(path) for relative_path, path in manifest_paths.items()}
    _require_top_level_baseline(originals[CLASSIFICATION_PATH], old_version, "Classification manifest")
    _require_top_level_baseline(originals[SCOPE_PATH], old_version, "Scope manifest")
    _validate_truth_baseline(originals[TRUTH_PATH], old_version)
    _validate_release_baseline(originals[RELEASE_POLICY_PATH], old_version)
    _require_top_level_baseline(originals[PROMISE_PATH], old_version, "Public promise register")
    _require_top_level_baseline(originals[DEBT_PATH], old_version, "Quality-debt inventory")
    _validate_sensitive_hashes(root, originals[CLASSIFICATION_PATH])
    _validate_reviewed_surface_hashes(root, originals[PROMISE_PATH])

    updates: dict[Path, bytes] = {}
    _prepare_roadmap_source_updates(root, roadmap, old_version, new_version, updates)

    updated_roadmap = load_json_bytes(_staged_bytes(roadmap_path, updates), ROADMAP_PATH)
    updated_roadmap["repository_baseline"] = new_version
    updates[roadmap_path] = json_bytes(updated_roadmap)

    documents = {
        relative_path: load_json_bytes(_staged_bytes(path, updates), relative_path)
        for relative_path, path in manifest_paths.items()
    }
    documents[CLASSIFICATION_PATH]["repository_baseline"] = new_version
    documents[SCOPE_PATH]["repository_baseline"] = new_version
    truth_baseline = documents[TRUTH_PATH]["repository_baseline"]
    truth_baseline["value"] = new_version
    for mirror in truth_baseline["mirrors"]:
        mirror["value"] = new_version
    documents[RELEASE_POLICY_PATH]["repository_baseline"]["value"] = new_version
    documents[PROMISE_PATH]["repository_baseline"] = new_version
    documents[DEBT_PATH]["repository_baseline"] = new_version

    for relative_path in (SCOPE_PATH, TRUTH_PATH, RELEASE_POLICY_PATH, DEBT_PATH):
        updates[manifest_paths[relative_path]] = json_bytes(documents[relative_path])

    reviewed_surfaces = documents[PROMISE_PATH]["reviewed_surfaces"]
    for surface in reviewed_surfaces:
        relative_path = surface["path"]
        path = repository_file(root, relative_path, "Reviewed public surface")
        try:
            surface["sha256"] = normalized_bytes_sha256(_staged_bytes(path, updates))
        except UnicodeDecodeError as exc:
            raise ValueError(f"Reviewed public surface is not strict UTF-8: {relative_path}") from exc
    documents[PROMISE_PATH]["reviewed_surface_aggregate_sha256"] = reviewed_surface_digest(
        reviewed_surfaces
    )
    updates[manifest_paths[PROMISE_PATH]] = json_bytes(documents[PROMISE_PATH])

    for source in documents[CLASSIFICATION_PATH]["sensitive_sources"]:
        relative_path = source["path"]
        path = repository_file(root, relative_path, "Classification sensitive source")
        try:
            source["sha256"] = normalized_bytes_sha256(_staged_bytes(path, updates))
        except UnicodeDecodeError as exc:
            raise ValueError(f"Classification sensitive source is not strict UTF-8: {relative_path}") from exc
    updates[manifest_paths[CLASSIFICATION_PATH]] = json_bytes(documents[CLASSIFICATION_PATH])

    _apply_updates(updates)
    return old_version, new_version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if not SEMVER.fullmatch(args.version):
        parser.error("version must use MAJOR.MINOR.PATCH")
    old_version, new_version = update_version_references(args.root.resolve(), args.version)
    print(f"Updated repository version references from {old_version} to {new_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
