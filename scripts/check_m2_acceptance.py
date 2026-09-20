#!/usr/bin/env python3
"""Validate the YWE M2 canonical contract, schema, fixture, and acceptance gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urldefrag, urljoin

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import ValidationError
    from jsonschema.validators import extend, validator_for
    from referencing import Registry, Resource
except ImportError:
    print("Missing validation dependencies. Install scripts/requirements.txt.")
    raise SystemExit(1)

TEXT_ENCODING = "utf-8-sig"
CATALOG_PATH = "data/validation/m2_fixture_catalog.json"
CATALOG_SCHEMA_PATH = "data/schemas/m2_fixture_catalog_schema.json"
SCHEMA_DEBT_PATH = "data/validation/schema_quality_baseline.json"
ROADMAP_PATH = "data/governance/specification_roadmap.json"
EVIDENCE_PATH = "data/governance/m2_acceptance_evidence.json"
ACCEPTANCE_DOCUMENT_PATH = "docs/project/M2_CANONICAL_CONTRACT_SCHEMA_FOUNDATION_ACCEPTANCE.md"
EXPECTED_CLOSED_DEBT_COUNT = 39
REQUIRED_FIXTURE_CLASSES = {
    "positive",
    "boundary",
    "reject",
    "recovery",
    "replay",
    "migration",
}
DIAGNOSTIC_PATTERN = re.compile(r"^\[([A-Za-z0-9][A-Za-z0-9._-]+)\]\s")


class DuplicateKeyError(ValueError):
    """Raised when a JSON object contains a duplicate member name."""


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def load_json(path: Path) -> Any:
    with path.open(encoding=TEXT_ENCODING) as handle:
        return json.load(handle, object_pairs_hook=unique_object)


def repository_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError:
        result = None
    if result is not None and result.returncode == 0:
        names = result.stdout.decode("utf-8", errors="strict").split("\0")
        return sorted(root / name for name in names if name and (root / name).is_file())
    return sorted(path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts)


def normalized_sha256(path: Path) -> str:
    text = path.read_bytes().decode("utf-8-sig", errors="strict")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def resolve_json_pointer(document: Any, pointer: str) -> Any:
    if pointer in {"", "/"}:
        return document
    if not pointer.startswith("/"):
        raise KeyError(f"JSON pointer must begin with '/': {pointer!r}")
    current = document
    for encoded in pointer[1:].split("/"):
        token = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise KeyError(f"object member {token!r} is absent")
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit() or int(token) >= len(current):
                raise KeyError(f"array index {token!r} is invalid")
            current = current[int(token)]
        else:
            raise KeyError(f"cannot traverse {token!r} through {type(current).__name__}")
    return current


def walk_refs(value: Any, pointer: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, item in value.items():
            next_pointer = f"{pointer}/{str(key).replace('~', '~0').replace('/', '~1')}"
            if key == "$ref" and isinstance(item, str):
                yield next_pointer, item
            yield from walk_refs(item, next_pointer)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_refs(item, f"{pointer}/{index}")


def diagnostic_error(identifier: str, message: str) -> ValidationError:
    return ValidationError(f"[{identifier}] {message}")


def validate_ywe_policy(
    validator: Draft202012Validator,
    policy: Any,
    instance: Any,
    schema: dict[str, Any],
):
    del validator, schema
    if policy != "dispatch_negative_fixture" or not isinstance(instance, dict):
        return

    if instance.get("invalid_example") is True:
        reason = instance.get("reject_reason")
        candidate = instance.get("candidate")
        if not isinstance(candidate, dict):
            yield diagnostic_error("YWE-M2-NEGATIVE-CANDIDATE", "candidate must be an object")
            return
        if reason == "missing_source_provenance":
            source_refs = candidate.get("source_refs")
            if isinstance(source_refs, list) and not source_refs:
                yield diagnostic_error(
                    "check_ability_source_provenance",
                    "ability candidates require at least one source reference",
                )
                return
        elif reason == "generic_xp_only_unlock":
            unlock = str(candidate.get("unlock_condition", "")).lower()
            if ("level" in unlock or "xp" in unlock) and ("skill" in unlock or "point" in unlock):
                yield diagnostic_error(
                    "check_no_generic_skill_tree",
                    "generic XP and skill-point unlocks are forbidden",
                )
                return
        elif reason == "permanent_wolf_death_forbidden":
            cost = str(candidate.get("cost", "")).lower()
            if "wolf" in cost and ("permanent" in cost or "kill" in cost or "death" in cost):
                yield diagnostic_error(
                    "check_ability_decoherence_not_death",
                    "wolf costs use temporary decoherence rather than permanent death",
                )
                return
        elif reason == "wolf_morality_drift":
            description = str(candidate.get("description", "")).lower()
            if all(term in description for term in ("white wolf", "good", "dark wolf", "evil")):
                yield diagnostic_error(
                    "check_no_wolf_morality_ability_drift",
                    "Twin Wolf semantics are not a good-versus-evil morality system",
                )
                return
        yield diagnostic_error(
            "YWE-M2-NEGATIVE-NOT-REPRODUCED",
            f"declared ability rejection {reason!r} was not reproduced",
        )
        return

    declared_rules = instance.get("should_fail_rules")
    if isinstance(declared_rules, list):
        for identifier in declared_rules:
            if isinstance(identifier, str) and identifier:
                yield diagnostic_error(identifier, "declared negative fixture requirement")
        return

    invalid_pattern = str(instance.get("invalid_pattern", "")).lower()
    if invalid_pattern:
        if ("quest_complete" in invalid_pattern or "quest complete" in invalid_pattern) and "flag" in invalid_pattern:
            yield diagnostic_error(
                "check_no_feature_consequence_without_packet",
                "quest completion requires reward and consequence packets",
            )
            return
        if "static-only location" in invalid_pattern:
            yield diagnostic_error(
                "check_no_static_only_location_model_phase_17",
                "location traces require mutation or diagnostic no-op semantics",
            )
            return

    invalid_terms = instance.get("invalid_terms")
    if isinstance(invalid_terms, list):
        corpus = "\n".join(str(item).lower() for item in invalid_terms)
        if any(term in corpus for term in ("monobehaviour", "blueprint class", "gdscript")):
            yield diagnostic_error(
                "check_no_platform_specific_runtime_phase_17",
                "platform runtime implementation language is forbidden in the agnostic specification",
            )
            return
        if "wolf" in corpus and any(term in corpus for term in ("permanent", "kill", "death")):
            yield diagnostic_error(
                "check_no_permanent_wolf_death_phase_17",
                "Twin Wolf traces use decoherence and return, not permanent death",
            )
            return
        if "white wolf" in corpus and "dark wolf" in corpus and any(term in corpus for term in ("good", "evil", "morality")):
            yield diagnostic_error(
                "check_no_wolf_morality_language_phase_17",
                "Twin Wolf traces cannot use morality-meter semantics",
            )
            return

    yield diagnostic_error(
        "YWE-M2-NEGATIVE-NOT-REPRODUCED",
        "negative fixture did not reproduce a recognized requirement violation",
    )


M2Validator = extend(Draft202012Validator, {"x-ywe-policy": validate_ywe_policy})


def schema_registry(
    root: Path,
    errors: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, str], Registry]:
    schemas: dict[str, dict[str, Any]] = {}
    id_to_path: dict[str, str] = {}
    registry = Registry()
    for path in repository_files(root):
        if path.suffix.lower() != ".json":
            continue
        relative = path.relative_to(root).as_posix()
        try:
            document = load_json(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
            errors.append(f"{relative}: unable to parse JSON while building M2 registry: {exc}")
            continue
        if not isinstance(document, dict) or not isinstance(document.get("$schema"), str):
            continue
        schemas[relative] = document
        try:
            validator_for(document).check_schema(document)
        except Exception as exc:
            errors.append(f"{relative}: invalid JSON Schema: {exc}")
        schema_id = document.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            errors.append(f"{relative}: declared schema lacks a non-empty $id")
            continue
        if schema_id in id_to_path:
            errors.append(f"duplicate schema identifier {schema_id!r}: {id_to_path[schema_id]}, {relative}")
            continue
        id_to_path[schema_id] = relative
        try:
            registry = registry.with_resource(schema_id, Resource.from_contents(document))
        except Exception as exc:
            errors.append(f"{relative}: unable to register schema resource: {exc}")
    return schemas, id_to_path, registry


def check_offline_references(
    schemas: dict[str, dict[str, Any]],
    id_to_path: dict[str, str],
    errors: list[str],
) -> None:
    for path, schema in schemas.items():
        base_id = schema.get("$id")
        for pointer, reference in walk_refs(schema):
            if reference.startswith("#"):
                try:
                    resolve_json_pointer(schema, reference[1:] or "/")
                except KeyError as exc:
                    errors.append(f"{path}{pointer}: unresolved local reference {reference!r}: {exc}")
                continue
            absolute = urljoin(str(base_id), reference)
            resource_uri, fragment = urldefrag(absolute)
            target_path = id_to_path.get(resource_uri)
            if target_path is None:
                errors.append(f"{path}{pointer}: offline resource is absent for {reference!r}")
                continue
            if fragment:
                try:
                    resolve_json_pointer(schemas[target_path], f"/{fragment.lstrip('/')}")
                except KeyError as exc:
                    errors.append(f"{path}{pointer}: unresolved referenced fragment {reference!r}: {exc}")


def validate_catalog(
    root: Path,
    schemas: dict[str, dict[str, Any]],
    registry: Registry,
    errors: list[str],
) -> tuple[dict[str, Any] | None, Counter[str]]:
    catalog_path = root / CATALOG_PATH
    catalog_schema = schemas.get(CATALOG_SCHEMA_PATH)
    if not catalog_path.is_file():
        errors.append(f"missing M2 fixture catalog: {CATALOG_PATH}")
        return None, Counter()
    if catalog_schema is None:
        errors.append(f"missing declared catalog schema: {CATALOG_SCHEMA_PATH}")
        return None, Counter()
    try:
        catalog = load_json(catalog_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        errors.append(f"unable to load M2 fixture catalog: {exc}")
        return None, Counter()
    for error in sorted(
        Draft202012Validator(catalog_schema, registry=registry).iter_errors(catalog),
        key=lambda item: ([str(part) for part in item.absolute_path], item.message),
    ):
        pointer = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{CATALOG_PATH}:{pointer}: {error.message}")
    if not isinstance(catalog, dict) or not isinstance(catalog.get("entries"), list):
        return None, Counter()

    entries = catalog["entries"]
    fixture_ids = [entry.get("fixture_id") for entry in entries if isinstance(entry, dict)]
    if len(fixture_ids) != len(set(fixture_ids)):
        errors.append("M2 fixture catalog contains duplicate fixture_id values")
    binding_keys = [
        (entry.get("instance_path"), entry.get("instance_pointer"), entry.get("schema_path"))
        for entry in entries
        if isinstance(entry, dict)
    ]
    if len(binding_keys) != len(set(binding_keys)):
        errors.append("M2 fixture catalog contains duplicate instance-pointer-schema bindings")

    class_counts: Counter[str] = Counter()
    closed_paths: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        fixture_id = str(entry.get("fixture_id", f"index-{index}"))
        fixture_class = entry.get("fixture_class")
        if isinstance(fixture_class, str):
            class_counts[fixture_class] += 1
        instance_path = entry.get("instance_path")
        schema_path = entry.get("schema_path")
        pointer = entry.get("instance_pointer")
        if not all(isinstance(value, str) for value in (instance_path, schema_path, pointer)):
            continue
        instance_file = root / instance_path
        if not instance_file.is_file():
            errors.append(f"{fixture_id}: instance file does not exist: {instance_path}")
            continue
        schema = schemas.get(schema_path)
        if schema is None:
            errors.append(f"{fixture_id}: catalog schema is not a declared schema: {schema_path}")
            continue
        try:
            document = load_json(instance_file)
            instance = resolve_json_pointer(document, pointer)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, KeyError) as exc:
            errors.append(f"{fixture_id}: unable to resolve instance {instance_path}#{pointer}: {exc}")
            continue
        validation_errors = sorted(
            M2Validator(schema, registry=registry).iter_errors(instance),
            key=lambda item: ([str(part) for part in item.absolute_path], item.message),
        )
        expected_result = entry.get("expected_result")
        expected_ids = set(entry.get("expected_diagnostic_ids", []))
        if expected_result == "pass":
            if validation_errors:
                rendered = "; ".join(error.message for error in validation_errors[:5])
                errors.append(f"{fixture_id}: expected pass but validation failed: {rendered}")
        elif expected_result == "reject":
            if not validation_errors:
                errors.append(f"{fixture_id}: expected rejection but validation passed")
            actual_ids: set[str] = set()
            unidentified: list[str] = []
            for error in validation_errors:
                match = DIAGNOSTIC_PATTERN.match(error.message)
                if match is None:
                    unidentified.append(error.message)
                else:
                    actual_ids.add(match.group(1))
            if unidentified:
                errors.append(
                    f"{fixture_id}: rejection produced unidentified schema errors: {unidentified[:5]}"
                )
            if actual_ids != expected_ids:
                errors.append(
                    f"{fixture_id}: expected diagnostics {sorted(expected_ids)}; actual {sorted(actual_ids)}"
                )
        else:
            errors.append(f"{fixture_id}: unsupported expected_result {expected_result!r}")
        if entry.get("closes_schema_debt") is True:
            if instance_path in closed_paths:
                errors.append(f"{fixture_id}: duplicate schema-debt closure path {instance_path}")
            closed_paths.add(instance_path)

    missing_classes = sorted(REQUIRED_FIXTURE_CLASSES - set(class_counts))
    if missing_classes:
        errors.append(f"M2 catalog lacks required fixture classes: {missing_classes}")
    if catalog.get("closed_debt_count") != EXPECTED_CLOSED_DEBT_COUNT:
        errors.append(
            f"M2 catalog closed_debt_count must be {EXPECTED_CLOSED_DEBT_COUNT}; "
            f"found {catalog.get('closed_debt_count')!r}"
        )
    if len(closed_paths) != EXPECTED_CLOSED_DEBT_COUNT:
        errors.append(
            f"M2 catalog must close exactly {EXPECTED_CLOSED_DEBT_COUNT} distinct legacy paths; "
            f"found {len(closed_paths)}"
        )
    return catalog, class_counts


def check_example_coverage(root: Path, catalog: dict[str, Any] | None, errors: list[str]) -> None:
    catalog_paths = {
        entry.get("instance_path")
        for entry in (catalog or {}).get("entries", [])
        if isinstance(entry, dict) and entry.get("normative") is True
    }
    unbound: list[str] = []
    for path in repository_files(root):
        relative = path.relative_to(root).as_posix()
        if not relative.startswith("examples/") or path.suffix.lower() != ".json":
            continue
        try:
            document = load_json(path)
        except Exception:
            continue
        inline = isinstance(document, dict) and any(
            key in document for key in ("$schema", "schema_ref", "schema_id")
        )
        if not inline and relative not in catalog_paths:
            unbound.append(relative)
    if unbound:
        errors.append(f"JSON examples remain outside inline or catalog bindings: {sorted(unbound)}")


def check_schema_debt(root: Path, errors: list[str]) -> None:
    try:
        baseline = load_json(root / SCHEMA_DEBT_PATH)
        known_debt = baseline["known_debt"]
    except (OSError, KeyError, json.JSONDecodeError, DuplicateKeyError) as exc:
        errors.append(f"unable to load M2 schema debt baseline: {exc}")
        return
    nonempty = {key: value for key, value in known_debt.items() if value}
    if nonempty:
        errors.append(f"M2 schema debt baseline is not empty: {nonempty}")
    completion = baseline.get("completion_gate", {})
    if completion.get("milestone") != "M2":
        errors.append("schema debt completion gate is not assigned to M2")
    if completion.get("require_empty_debt") is not True:
        errors.append("schema debt completion gate does not require empty debt")
    if completion.get("require_fixture_catalog") is not True:
        errors.append("schema debt completion gate does not require a fixture catalog")


def check_acceptance_state(root: Path, preflight: bool, errors: list[str]) -> None:
    try:
        roadmap = load_json(root / ROADMAP_PATH)
    except Exception as exc:
        errors.append(f"unable to load roadmap for M2 status validation: {exc}")
        return
    milestones = {
        item.get("id"): item
        for item in roadmap.get("milestones", [])
        if isinstance(item, dict)
    }
    m2 = milestones.get("M2", {})
    m3 = milestones.get("M3", {})
    if preflight:
        if m2.get("status") not in {"in_progress", "complete"}:
            errors.append(f"M2 preflight found unsupported milestone status {m2.get('status')!r}")
        return
    expected_evidence = [EVIDENCE_PATH, ACCEPTANCE_DOCUMENT_PATH]
    if roadmap.get("current_milestone") != "M3":
        errors.append("final M2 acceptance requires current_milestone M3")
    if m2.get("status") != "complete":
        errors.append("final M2 acceptance requires M2 status complete")
    if m3.get("status") != "in_progress":
        errors.append("final M2 acceptance requires M3 status in_progress")
    if m2.get("acceptance_evidence") != expected_evidence:
        errors.append(
            f"M2 acceptance_evidence must be {expected_evidence}; found {m2.get('acceptance_evidence')!r}"
        )
    evidence_file = root / EVIDENCE_PATH
    if not evidence_file.is_file():
        errors.append(f"missing durable M2 acceptance evidence: {EVIDENCE_PATH}")
    else:
        try:
            evidence = load_json(evidence_file)
        except Exception as exc:
            errors.append(f"unable to load M2 acceptance evidence: {exc}")
        else:
            if not isinstance(evidence, dict) or evidence.get("milestone_id") != "M2":
                errors.append("M2 acceptance evidence has the wrong milestone_id")
            if evidence.get("outcome") != "pass":
                errors.append("M2 acceptance evidence does not record a passing outcome")
    if not (root / ACCEPTANCE_DOCUMENT_PATH).is_file():
        errors.append(f"missing M2 acceptance report: {ACCEPTANCE_DOCUMENT_PATH}")


def run(root: Path, *, preflight: bool = False) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    schemas, id_to_path, registry = schema_registry(root, errors)
    check_offline_references(schemas, id_to_path, errors)
    catalog, class_counts = validate_catalog(root, schemas, registry, errors)
    check_example_coverage(root, catalog, errors)
    check_schema_debt(root, errors)
    check_acceptance_state(root, preflight, errors)
    metrics = {
        "declared_schema_count": len(schemas),
        "unique_schema_identifier_count": len(id_to_path),
        "catalog_entry_count": len((catalog or {}).get("entries", [])),
        "closed_debt_count": len(
            {
                entry.get("instance_path")
                for entry in (catalog or {}).get("entries", [])
                if isinstance(entry, dict) and entry.get("closes_schema_debt") is True
            }
        ),
        "fixture_class_counts": dict(sorted(class_counts.items())),
        "catalog_sha256": normalized_sha256(root / CATALOG_PATH) if (root / CATALOG_PATH).is_file() else None,
        "offline_resolution": True,
        "network_access_required": False,
    }
    return errors, metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--final", action="store_true", dest="final_mode")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    if args.preflight and args.final_mode:
        parser.error("--preflight and --final are mutually exclusive")
    root = args.root.resolve()
    if args.preflight:
        preflight = True
    elif args.final_mode:
        preflight = False
    else:
        roadmap = load_json(root / ROADMAP_PATH)
        milestones = {item.get("id"): item for item in roadmap.get("milestones", [])}
        preflight = not (
            roadmap.get("current_milestone") == "M3"
            and milestones.get("M2", {}).get("status") == "complete"
        )
    errors, metrics = run(root, preflight=preflight)
    if args.json_output:
        print(json.dumps({"outcome": "fail" if errors else "pass", "errors": errors, "metrics": metrics}, indent=2))
    elif errors:
        print("M2 acceptance check failed:")
        for error in errors:
            print(f"  - {error}")
    else:
        mode = "preflight" if preflight else "final"
        print(
            f"M2 acceptance check passed ({mode}; {metrics['declared_schema_count']} schemas; "
            f"{metrics['catalog_entry_count']} catalog entries; {metrics['closed_debt_count']} debt closures; "
            "offline resolution only)."
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
