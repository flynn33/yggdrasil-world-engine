#!/usr/bin/env python3
"""Validate the complete M1 canon, terminology, and governance closure."""

from __future__ import annotations

import hashlib
import io
import json
import re
import runpy
import subprocess
import sys
import tarfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import FormatChecker
from jsonschema.validators import validator_for

import sync_ash_specifications as ash_sync
import check_m0_truthful_baseline as m0_validation


REQUIREMENT_PATH = "data/governance/normative_requirement_register.json"
GOVERNANCE_RECORD_PATH = "data/governance/governance_record_register.json"
TERM_INDEX_PATH = "data/governance/canonical_term_index.json"
GLOSSARY_PATH = "docs/glossary/ywe_design_glossary.md"
LATTICE_PATH = "data/governance/truth_authority_lattice.json"
ASH_IDENTITY_PATH = "data/governance/ash_dependency_identity.json"
ROADMAP_PATH = "data/governance/specification_roadmap.json"
DEBT_PATH = "data/validation/repository_quality_debt_inventory.json"
EVIDENCE_PATH = "data/governance/m1_acceptance_evidence.json"
EVIDENCE_DOCUMENT_PATH = "docs/project/M1_CANON_TERMINOLOGY_GOVERNANCE_ACCEPTANCE.md"
CHECK_CATALOG_PATH = "data/validation/repository_checks.json"
CLASSIFICATION_PATH = "data/governance/artifact_classification_manifest.json"
SCOPE_MANIFEST_PATH = "data/governance/scope_partition_manifest.json"
SYNC_SCRIPT_PATH = "scripts/sync_ash_specifications.py"
PLATFORM_CHECK_PATH = "scripts/check_platform_agnosticism.py"
ATTRIBUTION_CHECK_PATH = "scripts/check_repository_attribution_policy.py"

M0_IMMUTABLE_PATHS = (
    "data/governance/m0_acceptance_evidence.json",
    "docs/project/M0_TRUTHFUL_BASELINE_ACCEPTANCE.md",
)
M1_EVIDENCE_PATHS = (EVIDENCE_PATH, EVIDENCE_DOCUMENT_PATH)
CLASSIFICATION_METRIC_KEYS = (
    "normative",
    "informative",
    "example",
    "historical",
    "deprecated",
    "superseded",
    "placeholder",
)
SCOPE_METRIC_KEYS = (
    "ywe_core",
    "ywe_extension_profile",
    "ash_dependency_material",
    "wrw_reference_profile",
    "governance_validation",
    "historical_evidence",
    "later_release_work",
)
NORMATIVE_SURFACES = (
    "docs/governance/normative_language_and_requirement_id_policy.md",
    "docs/governance/governance_records_policy.md",
    "docs/architecture/truth_authority_lattice.md",
    "docs/architecture/ywe_core_wrw_scope_contract.md",
)
STRUCTURALLY_CITED_NORMATIVE_PATHS = {
    REQUIREMENT_PATH,
    GOVERNANCE_RECORD_PATH,
}
ACTIVE_SEMANTIC_SURFACES = (
    "yggdrasil-instructions.json",
    GLOSSARY_PATH,
    "docs/master_specification/YWE_MASTER_SPECIFICATION.md",
    "docs/architecture/truth_authority_lattice.md",
    "docs/architecture/ywe_core_wrw_scope_contract.md",
    "data/realm_registry/realms.json",
    "data/ash_state/realm_bit_mapping.yaml",
    "core/ash_pattern_engine/canonical/core/realm-identity.pseudo.md",
)

EXPECTED_REQUIREMENT_STATEMENTS = {
    "YWE-REQ-0001": (
        "Only the exact uppercase keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY carry "
        "normative force; lowercase uses are descriptive."
    ),
    "YWE-REQ-0002": (
        "Every new or materially changed normative clause MUST cite at least one stable "
        "requirement identifier."
    ),
    "YWE-REQ-0003": (
        "Allocated requirement identifiers MUST NOT be renumbered, reused for another meaning, "
        "or deleted, and terminal requirement records MUST be retained."
    ),
    "YWE-REQ-0004": (
        "Material architecture decisions, change proposals, risks, deviations, and semantic "
        "questions MUST have durable typed governance records."
    ),
    "YWE-REQ-0005": "The nine-coordinate base ontology MUST remain immutable.",
    "YWE-REQ-0006": (
        "Every mutable state change MUST be truth-scoped, typed, and provenance-bearing."
    ),
    "YWE-REQ-0007": "Perception state MUST NOT rewrite shared truth.",
    "YWE-REQ-0008": (
        "A coordinate index or bit position, an ordinal, a presentation order, a realm or plane "
        "identity, and a full vector or state identity MUST be treated as distinct concepts and "
        "MUST NOT be inferred from one another without an explicit mapping."
    ),
    "YWE-REQ-0009": (
        "The ASH Cosmological Model MUST own the upstream symbolic grammar used by YWE."
    ),
    "YWE-REQ-0010": (
        "The ASH dependency identity MUST be content-addressed and pinned by a deterministic digest."
    ),
    "YWE-REQ-0011": (
        "wolf_resonance MUST be the canonical field, wolf_alignment MAY be accepted only as a read "
        "or migration alias, and the dual-variable model MUST NOT be interpreted as a moral axis."
    ),
    "YWE-REQ-0012": "Accepted event history MUST be append-only.",
    "YWE-REQ-0013": (
        "A reversal or correction MUST be represented by a new compensating delta and MUST NOT "
        "erase or rewrite the accepted event."
    ),
    "YWE-REQ-0014": (
        "A lower truth-authority layer MUST NOT overwrite a higher layer's constraints."
    ),
    "YWE-REQ-0015": "A WRW-specific rule MUST NOT become normative YWE Core truth.",
    "YWE-REQ-0016": (
        "core/ash_pattern_engine/canonical MUST be the authoritative ASH specification source, and "
        "specs MUST remain its deterministically synchronized generated mirror."
    ),
    "YWE-REQ-0017": "Every material decision MUST retain a durable rationale.",
    "YWE-REQ-0018": "Each glossary concept MUST have exactly one canonical definition.",
}
EXPECTED_REQUIREMENT_IDS = set(EXPECTED_REQUIREMENT_STATEMENTS)
EXPECTED_REQUIREMENT_METADATA = {
    "YWE-REQ-0001": ("mixed", "forsetti_lifecycle_governance", "governance_validation"),
    "YWE-REQ-0002": ("MUST", "forsetti_lifecycle_governance", "governance_validation"),
    "YWE-REQ-0003": ("mixed", "forsetti_lifecycle_governance", "governance_validation"),
    "YWE-REQ-0004": ("MUST", "forsetti_lifecycle_governance", "governance_validation"),
    "YWE-REQ-0005": ("MUST", "ash_cosmological_model", "ash_dependency_material"),
    "YWE-REQ-0006": ("MUST", "ywe_core", "ywe_core"),
    "YWE-REQ-0007": ("MUST_NOT", "ywe_core", "ywe_core"),
    "YWE-REQ-0008": ("mixed", "ywe_core", "ywe_core"),
    "YWE-REQ-0009": ("MUST", "ash_cosmological_model", "ash_dependency_material"),
    "YWE-REQ-0010": ("MUST", "ash_cosmological_model", "ash_dependency_material"),
    "YWE-REQ-0011": ("mixed", "wrw_reference_profile", "wrw_reference_profile"),
    "YWE-REQ-0012": ("MUST", "ywe_core", "ywe_core"),
    "YWE-REQ-0013": ("mixed", "ywe_core", "ywe_core"),
    "YWE-REQ-0014": ("MUST_NOT", "ywe_core", "ywe_core"),
    "YWE-REQ-0015": ("MUST_NOT", "ywe_core", "ywe_core"),
    "YWE-REQ-0016": ("MUST", "ash_cosmological_model", "ash_dependency_material"),
    "YWE-REQ-0017": ("MUST", "forsetti_lifecycle_governance", "governance_validation"),
    "YWE-REQ-0018": ("MUST", "forsetti_lifecycle_governance", "governance_validation"),
}

EXPECTED_RECORD_TYPES = {
    **{f"ADR-{number:04d}": "decision" for number in range(1, 11)},
    "CP-0001": "change_proposal",
    **{f"RISK-{number:04d}": "risk" for number in range(1, 4)},
    **{f"DEV-{number:04d}": "deviation" for number in range(1, 6)},
    **{f"Q-{number:04d}": "question" for number in range(1, 9)},
}
EXPECTED_RECORD_STATUSES = {
    **{identifier: "accepted" for identifier in EXPECTED_RECORD_TYPES if identifier.startswith("ADR-")},
    "CP-0001": "implemented",
    **{identifier: "mitigated" for identifier in EXPECTED_RECORD_TYPES if identifier.startswith("RISK-")},
    **{identifier: "resolved" for identifier in EXPECTED_RECORD_TYPES if identifier.startswith("DEV-")},
    **{identifier: "resolved" for identifier in EXPECTED_RECORD_TYPES if identifier.startswith("Q-")},
}
EXPECTED_QUESTION_RESOLUTIONS = {
    f"Q-{number:04d}": f"ADR-{number + 2:04d}" for number in range(1, 9)
}
EXPECTED_DEVIATION_LEGACY_IDS = {
    f"DEV-{number:04d}": [f"D-{number:03d}"] for number in range(1, 6)
}
EXPECTED_GOVERNANCE_SUMMARY = {
    "total_records": 27,
    "architecture_decisions": 10,
    "accepted_decisions": 10,
    "change_proposals": 1,
    "implemented_change_proposals": 1,
    "risks": 3,
    "mitigated_risks": 3,
    "deviations": 5,
    "resolved_deviations": 5,
    "questions": 8,
    "resolved_questions": 8,
    "open_records": 0,
}

EXPECTED_M1_DEBT_IDS = {
    "QD-PH-dd00c6d30da8",
    "QD-PH-37cd25fd2cac",
    "QD-OW-001",
    "QD-063",
    "QD-064",
    "QD-065",
    "QD-066",
    "QD-067",
    "QD-068",
    "QD-069",
}
EXPECTED_REALMS = (
    "divine_core",
    "celestial",
    "causal",
    "mental",
    "astral",
    "etheric",
    "physical",
    "shadow",
    "void",
)
GLOSSARY_SUBTITLE = "Framework-agnostic terminology reference for Yggdrasil World Engine"
REQUIRED_GLOSSARY_HEADINGS = {
    "Ontology",
    "Structural Coordinate",
    "Coordinate Index",
    "Ordinal",
    "Presentation Order",
    "ASH State Vector",
    "State Identity",
    "Wolf Resonance",
    "Dual-Variable Alignment",
    "Event History",
    "Current-State Effect",
    "Compensating Delta",
    "YWE Core",
    "WRW Reference Profile",
    "Synchronized Mirror",
}
APPROVED_SHARED_ALIAS_OWNERS = {
    "wolf_alignment": {"wolf_alignment", "wolf_resonance"},
    "dual_variable_alignment": {"dual_variable_alignment", "wolf_resonance"},
}
WRW_REFERENCE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:"
    r"white[ _-]wolf|dark[ _-]wolf|wolf[ _-](?:resonance|alignment)|"
    r"floki|nathruun|ravenfall|lucifer|odin|divine[ _-]core|"
    r"where[ _-]ravens[ _-]wait|celestial[ _-]memory"
    r")(?![A-Za-z0-9])",
    re.IGNORECASE,
)

EXPECTED_NODE_RULES = {
    "ash_cosmological_model": (
        "authority",
        "ash_dependency_material",
        "governance_revision_only",
        False,
        ("base_world_ontology",),
        (),
    ),
    "ywe_core": (
        "authority",
        "ywe_core",
        "governance_revision_only",
        False,
        ("ywe_normative_contract", "diagnostic_noop"),
        ("ash_cosmological_model",),
    ),
    "ywe_extension_profile": (
        "authority",
        "ywe_extension_profile",
        "governance_revision_only",
        False,
        ("extension_profile_contract",),
        ("ash_cosmological_model", "ywe_core"),
    ),
    "wrw_reference_profile": (
        "authority",
        "wrw_reference_profile",
        "governance_revision_only",
        False,
        ("wrw_reference_canon",),
        ("ash_cosmological_model", "ywe_core", "ywe_extension_profile"),
    ),
    "shared_worldstate": (
        "state",
        "ywe_core",
        "append_only_transition",
        False,
        ("shared_worldstate",),
        ("ash_cosmological_model", "ywe_core", "ywe_extension_profile", "wrw_reference_profile"),
    ),
    "branch_local_state": (
        "state",
        "ywe_core",
        "append_only_transition",
        False,
        ("leaf_branch_state",),
        (
            "ash_cosmological_model",
            "ywe_core",
            "ywe_extension_profile",
            "wrw_reference_profile",
            "shared_worldstate",
        ),
    ),
    "player_local_state": (
        "state",
        "ywe_core",
        "append_only_transition",
        False,
        ("player_state",),
        (
            "ash_cosmological_model",
            "ywe_core",
            "ywe_extension_profile",
            "wrw_reference_profile",
            "shared_worldstate",
            "branch_local_state",
        ),
    ),
    "perception_social_interpretation": (
        "interpretive",
        "cross_scope",
        "derived_view",
        False,
        ("player_perception", "mythic_interpretation", "prophetic_pressure", "faction_claim"),
        (
            "ash_cosmological_model",
            "ywe_core",
            "ywe_extension_profile",
            "wrw_reference_profile",
            "shared_worldstate",
            "branch_local_state",
            "player_local_state",
        ),
    ),
    "host_materialization": (
        "materialization",
        "later_release_work",
        "derived_view",
        False,
        ("host_materialization",),
        (
            "ash_cosmological_model",
            "ywe_core",
            "ywe_extension_profile",
            "wrw_reference_profile",
            "shared_worldstate",
            "branch_local_state",
            "player_local_state",
            "perception_social_interpretation",
        ),
    ),
    "forsetti_lifecycle_governance": (
        "lifecycle_governance",
        "governance_validation",
        "governance_revision_only",
        True,
        (),
        (
            "ash_cosmological_model",
            "ywe_core",
            "ywe_extension_profile",
            "wrw_reference_profile",
            "shared_worldstate",
            "branch_local_state",
            "player_local_state",
            "perception_social_interpretation",
        ),
    ),
}
EXPECTED_RELATIONSHIPS = {
    ("ash_cosmological_model", "ywe_core", "constrains"),
    ("ywe_core", "ywe_extension_profile", "specializes"),
    ("ywe_core", "wrw_reference_profile", "specializes"),
    ("ywe_extension_profile", "wrw_reference_profile", "specializes"),
    ("ywe_core", "shared_worldstate", "records_within"),
    ("ywe_core", "branch_local_state", "records_within"),
    ("ywe_core", "player_local_state", "records_within"),
    ("shared_worldstate", "perception_social_interpretation", "projects_to"),
    ("branch_local_state", "perception_social_interpretation", "projects_to"),
    ("player_local_state", "perception_social_interpretation", "projects_to"),
    ("wrw_reference_profile", "perception_social_interpretation", "projects_to"),
    ("shared_worldstate", "host_materialization", "materializes"),
    ("branch_local_state", "host_materialization", "materializes"),
    ("player_local_state", "host_materialization", "materializes"),
    ("perception_social_interpretation", "host_materialization", "materializes"),
    ("forsetti_lifecycle_governance", "ywe_core", "governs_activation"),
    ("forsetti_lifecycle_governance", "ywe_extension_profile", "governs_activation"),
    ("forsetti_lifecycle_governance", "wrw_reference_profile", "governs_activation"),
}
EXPECTED_TRUTH_SCOPES = {
    "base_world_ontology": ("ash_cosmological_model", True),
    "ywe_normative_contract": ("ywe_core", True),
    "extension_profile_contract": ("ywe_extension_profile", True),
    "wrw_reference_canon": ("wrw_reference_profile", True),
    "shared_worldstate": ("shared_worldstate", True),
    "leaf_branch_state": ("branch_local_state", True),
    "player_state": ("player_local_state", True),
    "player_perception": ("perception_social_interpretation", False),
    "mythic_interpretation": ("perception_social_interpretation", False),
    "prophetic_pressure": ("perception_social_interpretation", False),
    "faction_claim": ("perception_social_interpretation", False),
    "host_materialization": ("host_materialization", False),
    "diagnostic_noop": ("ywe_core", False),
}
EXPECTED_SCOPE_ROUTING = {
    "ywe_core": {
        "normative_reach": "all_conforming_ywe_implementations",
        "must_be_setting_neutral": True,
        "may_require_wrw_identity": False,
    },
    "wrw_reference_profile": {
        "normative_reach": "declared_wrw_profile_conformance",
        "must_conform_to_ywe_core": True,
        "may_universalize_profile_content": False,
    },
}
EXPECTED_LATTICE_ASH_DEPENDENCY = {
    "dependency_identity_ref": ASH_IDENTITY_PATH,
    "canonical_source_root": ash_sync.SOURCE_ROOT.as_posix(),
    "generated_mirror_root": ash_sync.MIRROR_ROOT.as_posix(),
    "canonical_source_exclusions": ["README.md"],
    "synchronization_script_ref": SYNC_SCRIPT_PATH,
    "synchronization_mode": "normalized_utf8_lf_relative_paths",
}


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def normalized_text_data(value: bytes) -> bytes:
    if value.startswith(b"\xef\xbb\xbf"):
        value = value[3:]
    text = value.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_bytes(path: Path) -> bytes:
    return normalized_text_data(path.read_bytes())


def normalized_sha256(path: Path) -> str:
    return hashlib.sha256(normalized_text_bytes(path)).hexdigest()


def load_json(root: Path, relative_path: str, errors: list[str]) -> dict[str, Any] | None:
    path = root / relative_path
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        errors.append(f"Unable to load {relative_path}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{relative_path} must contain a JSON object")
        return None
    return value


def load_yaml(root: Path, relative_path: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = yaml.safe_load((root / relative_path).read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"Unable to load {relative_path}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{relative_path} must contain a YAML object")
        return None
    return value


def validate_bound_instance(
    root: Path,
    relative_path: str,
    document: dict[str, Any],
    errors: list[str],
) -> None:
    schema_ref = document.get("schema_ref")
    if not isinstance(schema_ref, str):
        errors.append(f"{relative_path} is missing schema_ref")
        return
    schema = load_json(root, schema_ref, errors)
    if schema is None:
        return
    try:
        validator_class = validator_for(schema)
        validator_class.check_schema(schema)
        validator = validator_class(schema, format_checker=FormatChecker())
        issues = sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
        for issue in issues:
            pointer = "/" + "/".join(str(part) for part in issue.absolute_path)
            errors.append(f"{relative_path}{pointer}: {issue.message}")
    except Exception as exc:
        errors.append(f"Unable to validate {relative_path}: {exc}")


def validate_snapshot_bound_instance(
    relative_path: str,
    document: dict[str, Any],
    snapshot_files: dict[str, bytes],
    errors: list[str],
) -> None:
    schema_ref = document.get("schema_ref")
    if not isinstance(schema_ref, str):
        errors.append(f"Historical {relative_path} is missing schema_ref")
        return
    schema = snapshot_json(snapshot_files, schema_ref, errors)
    if schema is None:
        return
    try:
        validator_class = validator_for(schema)
        validator_class.check_schema(schema)
        validator = validator_class(schema, format_checker=FormatChecker())
        issues = sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
        for issue in issues:
            pointer = "/" + "/".join(str(part) for part in issue.absolute_path)
            errors.append(f"historical {relative_path}{pointer}: {issue.message}")
    except Exception as exc:
        errors.append(f"Unable to validate historical {relative_path}: {exc}")


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def repository_ref_exists(
    root: Path,
    relative_path: str,
    snapshot_files: dict[str, bytes] | None = None,
) -> bool:
    safe = (
        bool(relative_path)
        and not Path(relative_path).is_absolute()
        and "\\" not in relative_path
        and ".." not in Path(relative_path).parts
    )
    if not safe:
        return False
    if snapshot_files is not None:
        return relative_path in snapshot_files
    return (root / relative_path).is_file()


def source_reference_paths(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    paths: list[str] = []
    for item in value:
        if isinstance(item, str):
            paths.append(item.split("#", 1)[0])
        elif isinstance(item, dict) and isinstance(item.get("path"), str):
            paths.append(item["path"].split("#", 1)[0])
    return paths


def repository_ref_bytes(
    root: Path,
    relative_path: str,
    snapshot_files: dict[str, bytes] | None = None,
) -> bytes | None:
    if snapshot_files is not None:
        return snapshot_files.get(relative_path)
    try:
        return (root / relative_path).read_bytes()
    except OSError:
        return None


def markdown_heading_slugs(text: str) -> set[str]:
    slugs: set[str] = set()
    counts: Counter[str] = Counter()
    for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", text):
        label = re.sub(r"<[^>]+>", "", match.group(1)).strip().lower()
        slug = re.sub(r"[^\w\s-]", "", label, flags=re.UNICODE)
        slug = re.sub(r"\s+", "-", slug)
        suffix = counts[slug]
        counts[slug] += 1
        slugs.add(slug if suffix == 0 else f"{slug}-{suffix}")
    return slugs


def resolve_dotted_path(document: Any, locator: str) -> bool:
    current = document
    for token in locator.split("."):
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return False
    return True


def check_evidence_locators(
    root: Path,
    value: Any,
    label: str,
    errors: list[str],
    snapshot_files: dict[str, bytes] | None = None,
) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{label} lacks precise evidence locators")
        return
    for item in value:
        if not isinstance(item, dict):
            errors.append(f"{label} contains a malformed evidence locator")
            continue
        kind = item.get("kind")
        path = item.get("path")
        locator = item.get("locator")
        if not isinstance(path, str) or not repository_ref_exists(root, path, snapshot_files):
            errors.append(f"{label} locator references missing repository path {path!r}")
            continue
        if not isinstance(locator, str) or not locator:
            errors.append(f"{label} has an empty evidence locator")
            continue
        content = repository_ref_bytes(root, path, snapshot_files)
        if content is None:
            errors.append(f"{label} locator cannot read {path!r}")
            continue
        try:
            text = normalized_text_data(content).decode("utf-8")
            if kind == "heading":
                headings = {
                    match.group(1).strip()
                    for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", text)
                }
                requested = [part.strip() for part in locator.split(";") if part.strip()]
                valid = bool(requested) and all(part in headings for part in requested)
            elif kind == "json_pointer":
                document = json.loads(text, object_pairs_hook=unique_object)
                valid, _resolved = m0_validation.resolve_json_pointer(document, locator)
            elif kind == "yaml_path":
                valid = resolve_dotted_path(yaml.safe_load(text), locator)
            elif kind == "exact_text":
                valid = locator in text
            else:
                valid = False
        except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, yaml.YAMLError):
            valid = False
        if not valid:
            errors.append(f"{label} locator {kind!r} does not resolve: {path}#{locator}")


def check_reference_paths(
    root: Path,
    value: Any,
    label: str,
    errors: list[str],
    snapshot_files: dict[str, bytes] | None = None,
) -> None:
    for path in source_reference_paths(value):
        if not repository_ref_exists(root, path, snapshot_files):
            errors.append(f"{label} references missing repository path {path!r}")
    if not isinstance(value, list):
        return
    for item in value:
        reference = item if isinstance(item, str) else item.get("path") if isinstance(item, dict) else None
        if not isinstance(reference, str) or "#" not in reference:
            continue
        path, fragment = reference.split("#", 1)
        if not fragment or not repository_ref_exists(root, path, snapshot_files):
            continue
        content = repository_ref_bytes(root, path, snapshot_files)
        if content is None:
            continue
        try:
            text = normalized_text_data(content).decode("utf-8")
            if fragment.startswith("/"):
                document = json.loads(text, object_pairs_hook=unique_object)
                valid, _resolved = m0_validation.resolve_json_pointer(document, fragment)
            elif path.lower().endswith(".md"):
                valid = fragment in markdown_heading_slugs(text)
            else:
                valid = False
        except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError):
            valid = False
        if not valid:
            errors.append(f"{label} contains an unresolved repository reference {reference!r}")


def duplicates(values: Iterable[Any]) -> list[Any]:
    return [value for value, count in Counter(values).items() if count > 1]


def strip_inline_code(line: str) -> str:
    delimiter = chr(96)
    output: list[str] = []
    position = 0
    while position < len(line):
        start = line.find(delimiter, position)
        if start < 0:
            output.append(line[position:])
            break
        output.append(line[position:start])
        run = 1
        while start + run < len(line) and line[start + run] == delimiter:
            run += 1
        closing = delimiter * run
        end = line.find(closing, start + run)
        if end < 0:
            output.append(line[start:])
            break
        position = end + run
    return "".join(output)


def markdown_normative_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    fence: str | None = None

    def flush() -> None:
        if current:
            blocks.append(" ".join(current))
            current.clear()

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith(chr(96) * 3):
            flush()
            fence = chr(96) * 3
            continue
        if stripped.startswith("~~~"):
            flush()
            fence = "~~~"
            continue
        if not stripped:
            flush()
            continue
        if "|" in stripped:
            flush()
            continue
        line = strip_inline_code(stripped)
        if re.match(r"^(?:[-+*]|\d+[.)])\s+", line):
            flush()
            current.append(line)
        elif line.startswith("#"):
            flush()
            current.append(line)
            flush()
        else:
            current.append(line)
    flush()
    return blocks


def check_normative_clauses(root: Path, errors: list[str]) -> None:
    keyword = re.compile(r"\b(?:MUST NOT|SHOULD NOT|MUST|SHOULD|MAY)\b")
    requirement_ref = re.compile(r"\[YWE-REQ-[0-9]{4}\]")
    for relative_path in NORMATIVE_SURFACES:
        try:
            text = (root / relative_path).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"Unable to scan normative surface {relative_path}: {exc}")
            continue
        for number, block in enumerate(markdown_normative_blocks(text), start=1):
            if keyword.search(block) and not requirement_ref.search(block):
                excerpt = re.sub(r"\s+", " ", block)[:120]
                errors.append(
                    f"{relative_path} normative block {number} uses an uppercase keyword "
                    f"without a requirement identifier: {excerpt!r}"
                )


def check_requirements(root: Path, document: dict[str, Any], errors: list[str]) -> None:
    records = document.get("requirements")
    if not isinstance(records, list):
        errors.append(f"{REQUIREMENT_PATH} requirements must be an array")
        return
    raw_ids = [item.get("requirement_id") for item in records if isinstance(item, dict)]
    ids = [identifier for identifier in raw_ids if isinstance(identifier, str)]
    duplicate_ids = duplicates(ids)
    if duplicate_ids:
        errors.append(f"Requirement register has duplicate or reused identifiers: {duplicate_ids}")
    if not EXPECTED_REQUIREMENT_IDS.issubset(set(ids)):
        errors.append("M1 requirement register must retain YWE-REQ-0001 through YWE-REQ-0018")
    for identifier in raw_ids:
        if not isinstance(identifier, str):
            errors.append(f"Requirement register has an invalid identifier: {identifier!r}")
    numeric_ids: list[int] = []
    for requirement_id in ids:
        if re.fullmatch(r"YWE-REQ-[0-9]{4}", requirement_id) is None:
            errors.append(f"Requirement register has an invalid identifier: {requirement_id!r}")
            continue
        numeric_ids.append(int(requirement_id.rsplit("-", 1)[1]))
    if numeric_ids and sorted(numeric_ids) != list(range(1, max(numeric_ids) + 1)):
        errors.append("Requirement identifiers must remain a contiguous monotonic allocation")
    by_id = {
        item.get("requirement_id"): item
        for item in records
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    governance_ids: set[str] = set()
    governance_document = load_json(root, GOVERNANCE_RECORD_PATH, errors)
    if governance_document is not None:
        governance_ids = {
            identifier
            for record in governance_records(governance_document)
            if (identifier := record_identifier(record)) is not None
        }
    for requirement_id, expected_statement in EXPECTED_REQUIREMENT_STATEMENTS.items():
        item = by_id.get(requirement_id)
        if item is None:
            continue
        if item.get("normative_statement") != expected_statement:
            errors.append(f"{requirement_id} meaning changed; allocate a new identifier")
        actual_metadata = (
            item.get("normative_level"),
            item.get("authority_node"),
            item.get("scope_partition"),
        )
        if actual_metadata != EXPECTED_REQUIREMENT_METADATA[requirement_id]:
            errors.append(f"{requirement_id} authority or normative force changed")
        if item.get("status") not in {"active", "superseded", "retired"}:
            errors.append(f"{requirement_id} regressed to a non-terminal pre-acceptance status")
        if item.get("introduced_milestone") != "M1":
            errors.append(f"{requirement_id} has an invalid introduced milestone")
    valid_records = [item for item in records if isinstance(item, dict)]
    status_counts = Counter(item.get("status") for item in valid_records)
    next_number = max(numeric_ids, default=0) + 1
    next_identifier = f"YWE-REQ-{next_number:04d}"
    expected_summary = {
        "total_requirements": len(valid_records),
        "active": status_counts["active"],
        "proposed": status_counts["proposed"],
        "terminal": status_counts["superseded"] + status_counts["retired"],
        "next_identifier": next_identifier,
    }
    if document.get("summary") != expected_summary:
        errors.append(
            f"Normative requirement summary is stale: expected {expected_summary}, "
            f"found {document.get('summary')}"
        )
    id_policy = document.get("id_policy", {})
    if not isinstance(id_policy, dict) or id_policy.get("next_available_id") != next_identifier:
        errors.append(f"Normative requirement ID policy must allocate {next_identifier} next")
    all_ids = set(identifier for identifier in ids if isinstance(identifier, str))
    for item in valid_records:
        identifier = item.get("requirement_id", "<missing>")
        if item.get("status") not in {"proposed", "active", "superseded", "retired"}:
            errors.append(f"{identifier} has an invalid requirement lifecycle status")
        if item.get("authority_node") not in EXPECTED_NODE_RULES:
            errors.append(f"{identifier} references an unknown truth-authority node")
        check_reference_paths(root, item.get("source_refs"), str(identifier), errors)
        check_reference_paths(root, item.get("verification_refs"), str(identifier), errors)
        decision_refs = item.get("decision_refs")
        if not isinstance(decision_refs, list) or any(
            not isinstance(ref, str) or re.fullmatch(r"ADR-[0-9]{4}", ref) is None
            for ref in decision_refs
        ):
            errors.append(f"{identifier} has an invalid decision reference")
        elif governance_ids and any(ref not in governance_ids for ref in decision_refs):
            errors.append(f"{identifier} references a nonexistent governance decision")
        for relation_field in ("aliases", "supersedes"):
            values = item.get(relation_field)
            if not isinstance(values, list) or any(value not in all_ids for value in values):
                errors.append(f"{identifier} has invalid {relation_field} requirement links")


LOGICAL_RECORD_ARRAYS = {
    "architecture_decisions": "decision",
    "change_proposals": "change_proposal",
    "risks": "risk",
    "deviations": "deviation",
    "questions": "question",
}


def governance_records(document: dict[str, Any]) -> list[dict[str, Any]]:
    records_value = document.get("records")
    if isinstance(records_value, list):
        return [item for item in records_value if isinstance(item, dict)]
    sources: list[tuple[str, Any]] = []
    if isinstance(records_value, dict):
        sources.extend((key, records_value.get(key)) for key in LOGICAL_RECORD_ARRAYS)
    else:
        sources.extend((key, document.get(key)) for key in LOGICAL_RECORD_ARRAYS)
    records: list[dict[str, Any]] = []
    for key, value in sources:
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict):
                continue
            record = dict(item)
            record.setdefault("record_type", LOGICAL_RECORD_ARRAYS[key])
            records.append(record)
    return records


def record_identifier(record: dict[str, Any]) -> str | None:
    for key in (
        "id",
        "record_id",
        "decision_id",
        "proposal_id",
        "risk_id",
        "deviation_id",
        "question_id",
    ):
        value = record.get(key)
        if isinstance(value, str):
            return value
    return None


def recompute_governance_summary(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(item.get("record_type") for item in records)
    statuses = Counter((item.get("record_type"), item.get("status")) for item in records)
    terminal = {"accepted", "superseded", "rejected", "implemented", "withdrawn", "mitigated", "closed", "expired", "resolved"}
    return {
        "total_records": len(records),
        "architecture_decisions": counts["decision"],
        "accepted_decisions": statuses[("decision", "accepted")],
        "change_proposals": counts["change_proposal"],
        "implemented_change_proposals": statuses[("change_proposal", "implemented")],
        "risks": counts["risk"],
        "mitigated_risks": statuses[("risk", "mitigated")],
        "deviations": counts["deviation"],
        "resolved_deviations": statuses[("deviation", "resolved")],
        "questions": counts["question"],
        "resolved_questions": statuses[("question", "resolved")],
        "open_records": sum(item.get("status") not in terminal for item in records),
    }


def check_governance_records(root: Path, document: dict[str, Any], errors: list[str]) -> None:
    records = governance_records(document)
    identifiers = [record_identifier(item) for item in records]
    duplicate_ids = duplicates(identifiers)
    if duplicate_ids:
        errors.append(f"Governance register has duplicate identifiers: {duplicate_ids}")
    if not set(EXPECTED_RECORD_TYPES).issubset(set(identifiers)):
        errors.append(
            "Governance register must retain ADR-0001 through ADR-0010, CP-0001, "
            "RISK-0001 through RISK-0003, DEV-0001 through DEV-0005, and Q-0001 through Q-0008"
        )
    by_id = {
        identifier: record
        for record in records
        if (identifier := record_identifier(record)) is not None
    }
    requirement_ids: set[str] = set()
    requirement_document = load_json(root, REQUIREMENT_PATH, errors)
    if requirement_document is not None:
        requirement_ids = {
            item.get("requirement_id")
            for item in requirement_document.get("requirements", [])
            if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
        }
    for identifier, expected_type in EXPECTED_RECORD_TYPES.items():
        record = by_id.get(identifier)
        if record is None:
            continue
        if record.get("record_type") != expected_type:
            errors.append(f"{identifier} has invalid lifecycle type {record.get('record_type')!r}")
        expected_status = EXPECTED_RECORD_STATUSES[identifier]
        permitted_statuses = {
            "decision": {"accepted", "superseded"},
            "change_proposal": {"implemented"},
            "risk": {"mitigated", "accepted", "closed"},
            "deviation": {"resolved"},
            "question": {"resolved"},
        }[expected_type]
        if record.get("status") not in permitted_statuses:
            errors.append(
                f"{identifier} regressed from its required M1 closure state {expected_status!r}"
            )
        if expected_type == "decision":
            if len(str(record.get("rationale", "")).strip()) < 20:
                errors.append(f"{identifier} lacks durable rationale")
            if len(str(record.get("decision", "")).strip()) < 20:
                errors.append(f"{identifier} lacks a material decision")
        if expected_type == "deviation" and record.get("legacy_ids") != EXPECTED_DEVIATION_LEGACY_IDS[identifier]:
            errors.append(f"{identifier} does not preserve its exact legacy deviation identity")
        if expected_type == "question":
            if record.get("resolution_record_ref") != EXPECTED_QUESTION_RESOLUTIONS[identifier]:
                errors.append(f"{identifier} has an invalid resolution record")
            if len(str(record.get("resolution", "")).strip()) < 15:
                errors.append(f"{identifier} lacks a durable resolution")
        requirement_refs = record.get("requirement_refs")
        if not isinstance(requirement_refs, list) or not requirement_refs:
            errors.append(f"{identifier} has no requirement references")
        elif any(
            not isinstance(ref, str)
            or re.fullmatch(r"YWE-REQ-[0-9]{4}", ref) is None
            or (requirement_ids and ref not in requirement_ids)
            for ref in requirement_refs
        ):
            errors.append(f"{identifier} has an invalid requirement reference")
        check_reference_paths(root, record.get("source_refs"), identifier, errors)
    valid_statuses = {
        "decision": {"proposed", "accepted", "superseded", "rejected"},
        "change_proposal": {"draft", "under_review", "accepted", "implemented", "rejected", "withdrawn"},
        "risk": {"open", "mitigated", "accepted", "closed"},
        "deviation": {"requested", "approved", "expired", "resolved", "rejected"},
        "question": {"open", "resolved", "deferred", "withdrawn"},
    }
    prefix_types = {
        "ADR": "decision",
        "CP": "change_proposal",
        "RISK": "risk",
        "DEV": "deviation",
        "Q": "question",
    }
    for record in records:
        identifier = record_identifier(record)
        match = re.fullmatch(r"(ADR|CP|RISK|DEV|Q)-[0-9]{4}", identifier or "")
        if match is None:
            errors.append(f"Governance register has an invalid record identifier: {identifier!r}")
            continue
        expected_type = prefix_types[match.group(1)]
        actual_type = record.get("record_type")
        if actual_type != expected_type:
            errors.append(f"{identifier} type does not match its identifier series")
        elif record.get("status") not in valid_statuses[actual_type]:
            errors.append(f"{identifier} has an invalid {actual_type} lifecycle status")
        for reference_field in (
            "supersedes",
            "superseded_by",
            "affected_record_refs",
            "related_record_refs",
        ):
            values = record.get(reference_field, [])
            if not isinstance(values, list):
                errors.append(f"{identifier} {reference_field} must be an array")
                continue
            if any(
                not isinstance(value, str)
                or value not in by_id
                or value == identifier
                for value in values
            ):
                errors.append(f"{identifier} has an invalid {reference_field} governance link")
        if actual_type == "question" and record.get("status") == "resolved":
            resolution_ref = record.get("resolution_record_ref")
            target = by_id.get(resolution_ref)
            if (
                not isinstance(target, dict)
                or target.get("record_type") != "decision"
                or target.get("status") != "accepted"
            ):
                errors.append(f"{identifier} does not resolve to an accepted architecture decision")
    for identifier, record in by_id.items():
        supersedes = record.get("supersedes", [])
        if not isinstance(supersedes, list):
            supersedes = []
        for target_id in supersedes:
            target = by_id.get(target_id)
            reciprocal = target.get("superseded_by", []) if isinstance(target, dict) else []
            if not isinstance(reciprocal, list):
                reciprocal = []
            if isinstance(target, dict) and identifier not in reciprocal:
                errors.append(
                    f"{identifier} supersedes {target_id} without a reciprocal superseded_by link"
                )
        superseded_by = record.get("superseded_by", [])
        if not isinstance(superseded_by, list):
            superseded_by = []
        for source_id in superseded_by:
            source = by_id.get(source_id)
            reciprocal = source.get("supersedes", []) if isinstance(source, dict) else []
            if not isinstance(reciprocal, list):
                reciprocal = []
            if isinstance(source, dict) and identifier not in reciprocal:
                errors.append(
                    f"{identifier} superseded_by {source_id} lacks a reciprocal supersedes link"
                )
    actual_summary = recompute_governance_summary(records)
    if document.get("summary") != actual_summary:
        errors.append(
            f"Governance record summary is stale: expected {actual_summary}, "
            f"found {document.get('summary')}"
        )


def glossary_headings(root: Path) -> list[str]:
    text = (root / GLOSSARY_PATH).read_text(encoding="utf-8-sig")
    return [
        match.group(1).strip()
        for match in re.finditer(r"(?m)^## ([^\r\n]+)$", text)
        if match.group(1).strip() != GLOSSARY_SUBTITLE
    ]


def glossary_section(root: Path, heading: str) -> str:
    text = (root / GLOSSARY_PATH).read_text(encoding="utf-8-sig")
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        text,
    )
    return match.group(1).strip() if match else ""


def normalized_alias(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def check_terms(root: Path, document: dict[str, Any], errors: list[str]) -> None:
    terms = document.get("terms")
    if not isinstance(terms, list):
        errors.append(f"{TERM_INDEX_PATH} terms must be an array")
        return
    keys = [item.get("term_key") for item in terms if isinstance(item, dict)]
    indexed_headings = [item.get("glossary_heading") for item in terms if isinstance(item, dict)]
    canonical_labels = [item.get("canonical_label") for item in terms if isinstance(item, dict)]
    for label, values in (
        ("term keys", keys),
        ("glossary headings", indexed_headings),
        ("canonical labels", [normalized_alias(value) for value in canonical_labels if isinstance(value, str)]),
    ):
        repeated = duplicates(values)
        if repeated:
            errors.append(f"Canonical term index has duplicate {label}: {repeated}")
    try:
        headings = glossary_headings(root)
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"Unable to inspect canonical glossary: {exc}")
        return
    duplicate_headings = duplicates(headings)
    if duplicate_headings:
        errors.append(f"Canonical glossary has duplicate headings: {duplicate_headings}")
    if set(indexed_headings) != set(headings) or len(indexed_headings) != len(headings):
        errors.append(
            "Canonical term index and glossary headings disagree; "
            f"missing={sorted(set(headings) - set(indexed_headings))}, "
            f"stale={sorted(set(indexed_headings) - set(headings))}"
        )
    missing_required = sorted(REQUIRED_GLOSSARY_HEADINGS - set(headings))
    if missing_required:
        errors.append(f"Canonical glossary is missing M1 concepts: {missing_required}")
    if "Plane" in headings:
        errors.append("Glossary must not create a competing canonical Plane concept")
    realm_section = glossary_section(root, "Realm")
    identity_section = glossary_section(root, "State Identity")
    if (
        "preferred" not in realm_section.casefold()
        or "ontology" not in realm_section.casefold()
        or "plane" not in realm_section.casefold()
        or "presentation alias" not in realm_section.casefold()
    ):
        errors.append("Glossary Realm entry does not define the preferred ontology-member term")
    if (
        "realmidentity" not in identity_section.casefold()
        or "realm_id" not in identity_section.casefold()
        or "deprecated" not in identity_section.casefold()
    ):
        errors.append(
            "Glossary State Identity entry does not define RealmIdentity and realm_id as deprecated aliases"
        )

    alias_owners: dict[str, list[str]] = defaultdict(list)
    deprecated_alias_count = 0
    for item in terms:
        if not isinstance(item, dict):
            continue
        owner = item.get("term_key")
        aliases = item.get("aliases", [])
        if not isinstance(owner, str) or not isinstance(aliases, list):
            continue
        local_labels: list[str] = []
        for alias in aliases:
            if not isinstance(alias, dict) or not isinstance(alias.get("label"), str):
                continue
            label = normalized_alias(alias["label"])
            local_labels.append(alias["label"].strip())
            alias_owners[label].append(owner)
            if alias.get("status") == "deprecated":
                deprecated_alias_count += 1
        repeated_local = duplicates(local_labels)
        if repeated_local:
            errors.append(f"Canonical term {owner!r} repeats alias definitions: {repeated_local}")
    for label, owners_list in alias_owners.items():
        owners = set(owners_list)
        if len(owners) <= 1:
            continue
        approved = APPROVED_SHARED_ALIAS_OWNERS.get(label)
        if approved is None or owners != approved:
            errors.append(f"Alias {label!r} has competing canonical owners: {sorted(owners)}")

    by_key = {
        item.get("term_key"): item
        for item in terms
        if isinstance(item, dict) and isinstance(item.get("term_key"), str)
    }
    if "plane" in by_key:
        errors.append("Canonical term index must not create a competing Plane concept")
    required_aliases = {
        "realm": (("Plane", "presentation_alias"), ("plane", "presentation_alias")),
        "state_identity": (("RealmIdentity", "deprecated"), ("realm_id", "deprecated")),
    }
    for term_key, requirements in required_aliases.items():
        term = by_key.get(term_key)
        aliases = term.get("aliases", []) if isinstance(term, dict) else []
        for required_label, required_status in requirements:
            matches = [
                alias
                for alias in aliases
                if isinstance(alias, dict)
                and alias.get("label") == required_label
                and alias.get("status") == required_status
            ]
            if not matches:
                errors.append(
                    f"Canonical term {term_key!r} lacks required {required_label!r} "
                    f"{required_status} mapping"
                )

    expected_summary = {
        "term_count": len(terms),
        "canonical_count": sum(
            item.get("status") == "canonical" for item in terms if isinstance(item, dict)
        ),
        "deprecated_alias_count": deprecated_alias_count,
    }
    if document.get("summary") != expected_summary:
        errors.append(
            f"Canonical term summary is stale: expected {expected_summary}, "
            f"found {document.get('summary')}"
        )


def node_identifier(node: dict[str, Any]) -> str | None:
    value = node.get("node_id", node.get("id"))
    return value if isinstance(value, str) else None


def relationship_values(edge: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    source = edge.get("source_node", edge.get("source", edge.get("from")))
    target = edge.get("target_node", edge.get("target", edge.get("to")))
    relation = edge.get("relation", edge.get("relationship_type"))
    return (
        source if isinstance(source, str) else None,
        target if isinstance(target, str) else None,
        relation if isinstance(relation, str) else None,
    )


def directed_cycle(edges: list[tuple[str, str]]) -> bool:
    graph: dict[str, set[str]] = defaultdict(set)
    for source, target in edges:
        graph[source].add(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in graph[node]):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in list(graph))


def check_lattice(document: dict[str, Any], errors: list[str]) -> None:
    nodes_value = document.get("nodes")
    relationships_value = document.get("relationships")
    scopes_value = document.get("truth_scopes")
    if not isinstance(nodes_value, list):
        errors.append(f"{LATTICE_PATH} nodes must be an array")
        return
    if not isinstance(relationships_value, list):
        errors.append(f"{LATTICE_PATH} relationships must be an array")
        return
    if not isinstance(scopes_value, list):
        errors.append(f"{LATTICE_PATH} truth_scopes must be an array")
        return

    nodes = [item for item in nodes_value if isinstance(item, dict)]
    node_ids = [node_identifier(item) for item in nodes]
    if duplicates(node_ids):
        errors.append(f"Truth-authority lattice has duplicate nodes: {duplicates(node_ids)}")
    if set(node_ids) != set(EXPECTED_NODE_RULES) or len(node_ids) != len(EXPECTED_NODE_RULES):
        errors.append("Truth-authority lattice must define the ten canonical nodes exactly once")
    by_id = {
        identifier: node
        for node in nodes
        if (identifier := node_identifier(node)) is not None
    }
    for identifier, expected in EXPECTED_NODE_RULES.items():
        node = by_id.get(identifier)
        if node is None:
            continue
        actual = (
            node.get("node_kind"),
            node.get("authority_scope"),
            node.get("mutability"),
            node.get("orthogonal"),
            tuple(node.get("writable_truth_scopes", [])),
            tuple(node.get("forbidden_override_targets", [])),
        )
        if actual != expected:
            errors.append(f"Truth-authority node {identifier} violates its authority boundary")

    relationship_tuples = [
        relationship_values(item) for item in relationships_value if isinstance(item, dict)
    ]
    if duplicates(relationship_tuples):
        errors.append(f"Truth-authority lattice has duplicate relationships: {duplicates(relationship_tuples)}")
    for relationship in relationship_tuples:
        source, target, relation = relationship
        if source not in EXPECTED_NODE_RULES or target not in EXPECTED_NODE_RULES:
            errors.append(f"Truth-authority relationship has a dangling endpoint: {relationship}")
        if relation not in {item[2] for item in EXPECTED_RELATIONSHIPS}:
            errors.append(f"Truth-authority relationship has an invalid type: {relation!r}")
    if set(relationship_tuples) != EXPECTED_RELATIONSHIPS or len(relationship_tuples) != len(EXPECTED_RELATIONSHIPS):
        errors.append("Truth-authority relationships do not match the approved typed lattice")
    ordering_edges = [
        (source, target)
        for source, target, relation in relationship_tuples
        if source is not None and target is not None and relation in {"constrains", "specializes"}
    ]
    if directed_cycle(ordering_edges):
        errors.append("Truth-authority constraint and specialization graph contains a cycle")

    scopes = [item for item in scopes_value if isinstance(item, dict)]
    scope_ids = [item.get("scope_id") for item in scopes]
    if duplicates(scope_ids):
        errors.append(f"Truth-authority lattice has duplicate truth scopes: {duplicates(scope_ids)}")
    if set(scope_ids) != set(EXPECTED_TRUTH_SCOPES) or len(scope_ids) != len(EXPECTED_TRUTH_SCOPES):
        errors.append("Truth-authority lattice does not define the thirteen canonical truth scopes")
    scope_by_id = {
        item.get("scope_id"): item
        for item in scopes
        if isinstance(item.get("scope_id"), str)
    }
    for scope_id, expected in EXPECTED_TRUTH_SCOPES.items():
        scope = scope_by_id.get(scope_id)
        if scope is not None and (scope.get("record_node"), scope.get("objective_state")) != expected:
            errors.append(f"Truth scope {scope_id} violates its record authority or objectivity")

    if document.get("scope_routing") != EXPECTED_SCOPE_ROUTING:
        errors.append("YWE Core and WRW scope routing no longer preserves setting-neutral Core authority")
    if document.get("ash_dependency") != EXPECTED_LATTICE_ASH_DEPENDENCY:
        errors.append("Truth-authority lattice ASH dependency routing is stale or incomplete")


def check_lattice_document(root: Path, errors: list[str]) -> None:
    relative_path = "docs/architecture/truth_authority_lattice.md"
    try:
        text = (root / relative_path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"Unable to inspect human truth-authority lattice: {exc}")
        return
    for scope_id in EXPECTED_TRUTH_SCOPES:
        if scope_id not in text:
            errors.append(f"Human truth-authority lattice omits truth scope {scope_id}")
    if "normalized_utf8_lf_relative_paths" not in text:
        errors.append(
            "Human truth-authority lattice does not state normalized UTF-8/LF mirror semantics"
        )


def validate_wrw_reference_exceptions(
    root: Path,
    scope: dict[str, Any],
    errors: list[str],
) -> None:
    for rule in scope.get("ordered_rules", []):
        if isinstance(rule, dict) and "wrw_reference_exception" in rule:
            errors.append("WRW reference exceptions are forbidden on scope rules")
    for override in scope.get("overrides", []):
        if not isinstance(override, dict) or "wrw_reference_exception" not in override:
            continue
        path = override.get("path", "<missing>")
        exception = override.get("wrw_reference_exception")
        if override.get("primary_partition") != "ywe_core":
            errors.append(f"WRW reference exception is only valid on ywe_core override {path}")
        if not isinstance(exception, dict):
            errors.append(f"WRW reference exception for {path} must be an object")
            continue
        markers = exception.get("markers")
        if (
            not isinstance(markers, list)
            or not markers
            or any(not isinstance(marker, str) or not marker for marker in markers)
            or len(markers) != len(set(markers))
        ):
            errors.append(f"WRW reference exception for {path} must list unique exact markers")
            continue
        for marker in markers:
            if WRW_REFERENCE_PATTERN.fullmatch(marker) is None or any(
                token in marker for token in "*?[]"
            ):
                errors.append(f"WRW reference exception for {path} has invalid marker {marker!r}")
        rationale = exception.get("rationale")
        if not isinstance(rationale, str) or len(rationale.strip()) < 20:
            errors.append(f"WRW reference exception for {path} lacks substantive rationale")
        authority_ref = exception.get("authority_ref")
        if authority_ref != "docs/architecture/ywe_core_wrw_scope_contract.md":
            errors.append(f"WRW reference exception for {path} has invalid authority_ref")
        elif not repository_ref_exists(root, authority_ref):
            errors.append(f"WRW reference exception for {path} references missing authority")


def check_scope_separation(
    root: Path,
    classification: dict[str, Any],
    scope: dict[str, Any],
    errors: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    validate_wrw_reference_exceptions(root, scope, errors)
    paths = m0_validation.repository_candidate_paths(root, errors)
    class_assignments = m0_validation.effective_assignments(
        paths,
        classification,
        "classification",
        errors,
        "M1 artifact classification",
    )
    scope_assignments = m0_validation.effective_assignments(
        paths,
        scope,
        "primary_partition",
        errors,
        "M1 scope partition",
    )
    for path in sorted(set(class_assignments) & set(scope_assignments)):
        if class_assignments[path].get("classification") != "normative":
            continue
        assignment = scope_assignments[path]
        if assignment.get("primary_partition") != "ywe_core":
            continue
        file_path = root / path
        if not file_path.is_file():
            continue
        try:
            text = file_path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            continue
        actual_markers = {match.group(0) for match in WRW_REFERENCE_PATTERN.finditer(text)}
        if not actual_markers:
            continue
        exception = assignment.get("wrw_reference_exception")
        if not isinstance(exception, dict):
            errors.append(
                f"Normative ywe_core artifact contains WRW-specific identity without "
                f"a per-path exception: {path}: {sorted(actual_markers)}"
            )
            continue
        allowed = set(exception.get("markers", []))
        if actual_markers != allowed:
            errors.append(
                f"WRW reference exception markers do not exactly match {path}: "
                f"observed={sorted(actual_markers)}, allowed={sorted(allowed)}"
            )
    return class_assignments, scope_assignments


def temporal_normative_blocks(relative_path: str, text: str) -> list[str]:
    if Path(relative_path).suffix.casefold() == ".md":
        blocks = markdown_normative_blocks(text)
    else:
        blocks = [strip_inline_code(line.strip()) for line in text.splitlines() if line.strip()]
    return [re.sub(r"\s+", " ", block).strip() for block in blocks if block.strip()]


def check_temporal_normative_clauses(
    root: Path,
    class_assignments: dict[str, dict[str, Any]],
    snapshot_files: dict[str, bytes],
    errors: list[str],
) -> None:
    keyword = re.compile(r"\b(?:MUST NOT|SHOULD NOT|MUST|SHOULD|MAY)\b")
    requirement_ref = re.compile(r"\[YWE-REQ-[0-9]{4}\]")
    for relative_path, assignment in sorted(class_assignments.items()):
        if assignment.get("classification") != "normative":
            continue
        if relative_path in STRUCTURALLY_CITED_NORMATIVE_PATHS:
            continue
        path = root / relative_path
        if not path.is_file():
            continue
        try:
            current_text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            continue
        historical_data = snapshot_files.get(relative_path)
        if historical_data is None:
            historical_blocks: set[str] = set()
        else:
            try:
                historical_text = normalized_text_data(historical_data).decode("utf-8")
            except UnicodeDecodeError:
                historical_blocks = set()
            else:
                historical_blocks = set(
                    temporal_normative_blocks(relative_path, historical_text)
                )
        for block in temporal_normative_blocks(relative_path, current_text):
            if block in historical_blocks:
                continue
            if keyword.search(block) and not requirement_ref.search(block):
                errors.append(
                    f"Added or materially changed normative block in {relative_path} "
                    f"lacks a stable requirement identifier: {block[:120]!r}"
                )


STATIC_WORLD_PATTERN = re.compile(r"\b(?:the\s+)?world\s+does\s+not\s+change\b", re.IGNORECASE)
REALM_VECTOR_PATTERNS = (
    re.compile(
        r"(?:full\s+)?(?:f2\s*\^\s*9|nine[- ]bit|9[- ]bit)\s+"
        r"(?:full[- ]state\s+)?(?:ash\s+)?(?:state\s+)?vectors?.{0,100}"
        r"(?:is|are|equals?|identif(?:y|ies|ied)|represents?|corresponds?\s+to).{0,60}"
        r"(?:one\s+of\s+)?(?:the\s+)?nine\s+(?:named\s+)?realms?",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"512\s+(?:states|vertices).{0,100}"
        r"(?:are|represent|identify|correspond\s+to).{0,60}"
        r"(?:the\s+)?nine\s+(?:named\s+)?realms?",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"512\s+states.{0,30}\bvertices\s*/\s*realms\b",
        re.IGNORECASE | re.DOTALL,
    ),
)


def check_forbidden_semantic_phrases(
    relative_path: str,
    text: str,
    errors: list[str],
) -> None:
    if STATIC_WORLD_PATTERN.search(text):
        errors.append(f"Normative static-world contradiction remains in {relative_path}")
    if any(pattern.search(text) for pattern in REALM_VECTOR_PATTERNS):
        errors.append(
            f"{relative_path} incorrectly equates full ASH state vectors with the nine named realms"
        )


def check_realm_registry(document: dict[str, Any], errors: list[str]) -> None:
    if document.get("profile_id") != "wrw_reference_profile":
        errors.append("Realm registry must identify the WRW reference profile")
    if document.get("realms") != list(EXPECTED_REALMS):
        errors.append("Realm registry compatibility array changed or is out of canonical order")
    bindings = document.get("coordinate_bindings")
    if not isinstance(bindings, list) or len(bindings) != 9:
        errors.append("Realm registry must contain exactly nine coordinate bindings")
        return
    if any(not isinstance(item, dict) for item in bindings):
        errors.append("Realm registry coordinate bindings must be objects")
        return
    ids = [item.get("realm_id") for item in bindings]
    coordinates = [item.get("coordinate_index") for item in bindings]
    ordinals = [item.get("ordinal") for item in bindings]
    if ids != list(EXPECTED_REALMS):
        errors.append("Realm coordinate bindings do not preserve canonical realm order")
    if (
        coordinates != list(range(9))
        or any(type(value) is not int for value in coordinates)
        or len(set(value for value in coordinates if type(value) is int)) != 9
    ):
        errors.append("Realm coordinate indices must be unique and exactly 0 through 8")
    if (
        ordinals != list(range(1, 10))
        or any(type(value) is not int for value in ordinals)
        or len(set(value for value in ordinals if type(value) is int)) != 9
    ):
        errors.append("Realm ordinals must be unique and exactly 1 through 9")


def check_realm_mapping(document: dict[str, Any], errors: list[str]) -> None:
    if document.get("profile_id") != "wrw_reference_profile":
        errors.append("Realm bit mapping must identify the WRW reference profile")
    anchors = document.get("realm_state_anchors")
    if not isinstance(anchors, list) or len(anchors) != 9:
        errors.append("Realm bit mapping must contain exactly nine WRW state anchors")
        return
    if any(not isinstance(anchor, dict) for anchor in anchors):
        errors.append("Realm state anchors must be objects")
        return
    ids = [anchor.get("realm_id") for anchor in anchors]
    coordinates = [anchor.get("coordinate_index") for anchor in anchors]
    ordinals = [anchor.get("ordinal") for anchor in anchors]
    state_ids = [anchor.get("state_identity") for anchor in anchors]
    if ids != list(EXPECTED_REALMS):
        errors.append("Realm state anchors do not preserve canonical realm order")
    if (
        coordinates != list(range(9))
        or any(type(value) is not int for value in coordinates)
        or len(set(value for value in coordinates if type(value) is int)) != 9
    ):
        errors.append("Realm anchor coordinate indices must be unique and exactly 0 through 8")
    if (
        ordinals != list(range(1, 10))
        or any(type(value) is not int for value in ordinals)
        or len(set(value for value in ordinals if type(value) is int)) != 9
    ):
        errors.append("Realm anchor ordinals must be unique and exactly 1 through 9")
    if any(not isinstance(value, str) for value in state_ids) or len(
        set(value for value in state_ids if isinstance(value, str))
    ) != 9:
        errors.append("Realm state anchor identities must be unique")
    for index, anchor in enumerate(anchors):
        expected_state = "".join("1" if position == index else "0" for position in range(9))
        if anchor.get("structural_coordinate") != f"b{index}":
            errors.append(f"Realm anchor {index} has an invalid structural coordinate")
        if anchor.get("coordinate_index") != index:
            errors.append(f"Realm anchor {index} lacks its canonical coordinate index")
        if anchor.get("ordinal") != index + 1:
            errors.append(f"Realm anchor {index} lacks its canonical ordinal")
        if anchor.get("presentation_order") != index + 1:
            errors.append(f"Realm anchor {index} lacks its canonical presentation order")
        if anchor.get("state_identity") != expected_state:
            errors.append(f"Realm anchor {index} is not its canonical one-hot full-state identity")
        if anchor.get("bit_index") != anchor.get("coordinate_index"):
            errors.append(f"Realm anchor {index} has a conflicting bit_index alias")
        if anchor.get("ash_state") != anchor.get("state_identity"):
            errors.append(f"Realm anchor {index} has a conflicting ash_state alias")


def wolf_values(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        key: value.get(key)
        for key in ("white_wolf", "dark_wolf")
        if key in value
    }


def check_player_documents(
    documents: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for relative_path, document in documents.items():
        resonance = document.get("wolf_resonance")
        if not isinstance(resonance, dict):
            errors.append(f"{relative_path} does not define canonical wolf_resonance state")
            continue
        values = wolf_values(resonance)
        if values is None or set(values) != {"white_wolf", "dark_wolf"}:
            errors.append(f"{relative_path} wolf_resonance lacks both canonical variables")
        alignment = document.get("wolf_alignment")
        if alignment is not None:
            if wolf_values(alignment) != values:
                errors.append(f"{relative_path} wolf_alignment and wolf_resonance disagree")
        for marker in ("morality_system", "good_evil_axis"):
            if marker in resonance and resonance.get(marker) is not False:
                errors.append(f"{relative_path} incorrectly treats wolf resonance as a moral axis")

    schema = documents.get("data/schemas/player_schema.json")
    if schema is None:
        return
    policy = schema.get("wolf_alias_policy")
    expected_policy = {
        "canonical_field": "wolf_resonance",
        "canonical_write_target": "wolf_resonance",
        "deprecated_field_alias": "wolf_alignment",
        "compatibility_model_alias": "dual_variable_alignment",
        "legacy_read_behavior": "resolve_as_wolf_resonance",
        "dual_field_requirement": "white_wolf_and_dark_wolf_values_must_match",
        "conflict_behavior": "reject_record",
        "creates_independent_state": False,
        "morality_axis": False,
    }
    if policy != expected_policy:
        errors.append("Player schema wolf alias policy no longer enforces one-way canonical migration")
    dual_model = schema.get("dual_variable_alignment")
    if not isinstance(dual_model, dict) or (
        dual_model.get("canonical_field") != "wolf_resonance"
        or dual_model.get("creates_independent_state") is not False
    ):
        errors.append("Player schema dual-variable model creates a competing state authority")


def check_history_documents(
    npc_rules: dict[str, Any],
    worldstate_rules: dict[str, Any],
    errors: list[str],
) -> None:
    synthesis = npc_rules.get("synthesis_laws")
    if not isinstance(synthesis, dict):
        errors.append("NPC synthesis rules lack synthesis_laws")
    else:
        if synthesis.get("npc_memory_history_append_only") is not True:
            errors.append("NPC accepted memory history is not append-only")
        if synthesis.get("npc_memory_effect_reversal_requires_compensating_delta") is not True:
            errors.append("NPC memory reversal does not require a compensating delta")
        if synthesis.get("host_adapter_may_author_npc_truth") is not False:
            errors.append("NPC synthesis allows a host adapter to author domain truth")
        if synthesis.get("npc_claim_may_rewrite_shared_world_truth") is not False:
            errors.append("NPC synthesis allows interpretive claims to overwrite shared truth")

    history = worldstate_rules.get("history_and_reversal_semantics")
    if not isinstance(history, dict):
        errors.append("Worldstate rules lack history and reversal semantics")
        return
    event_history = history.get("event_history")
    expected_event_history = {
        "mutability": "append_only",
        "accepted_records_are_immutable": True,
        "deletion_or_in_place_edit_allowed": False,
    }
    if event_history != expected_event_history:
        errors.append("Worldstate event history may erase or edit accepted records")
    reversal = history.get("reversal")
    expected_reversal = {
        "canonical_operation": "append_compensating_worldstate_delta",
        "requires_provenance": True,
        "preserves_original_event": True,
        "may_reorder_history": False,
    }
    if reversal != expected_reversal:
        errors.append("Worldstate reversal no longer preserves append-only event history")


def check_perception_document(document: dict[str, Any], errors: list[str]) -> None:
    rules = document.get("perception_rules")
    if not isinstance(rules, dict) or (
        rules.get("objective_state_change_requires_accepted_delta") is not True
        or rules.get("perception_is_derived_view") is not True
    ):
        errors.append("Perception schema permits a derived view to become shared objective truth")
    compatibility = document.get("terminology_compatibility")
    wolf = compatibility.get("wolf_alignment") if isinstance(compatibility, dict) else None
    if not isinstance(wolf, dict) or (
        wolf.get("canonical_field") != "wolf_resonance"
        or wolf.get("canonical_write_target") != "wolf_resonance"
        or wolf.get("conflict_behavior") != "reject_record"
        or wolf.get("creates_independent_state") is not False
    ):
        errors.append("Perception schema has an invalid wolf migration alias policy")
    boundary = document.get("ash_alignment_contract")
    boundary_text = str(boundary.get("truth_boundary", "")).lower() if isinstance(boundary, dict) else ""
    if "must not author ash truth or ywe domain truth" not in boundary_text:
        errors.append("Perception materialization boundary no longer forbids truth authorship")


def check_executable_identity_namespace(
    namespace: dict[str, Any],
    errors: list[str],
) -> None:
    encode_state = namespace.get("encode_state_identity")
    encode_realm = namespace.get("encode_realm_identity")
    build_snapshot = namespace.get("build_cosmic_pattern_snapshot")
    plan_generation_function = namespace.get("plan_generation")
    if not all(
        callable(value)
        for value in (encode_state, encode_realm, build_snapshot, plan_generation_function)
    ):
        errors.append("Canonical executable identity interface lacks required callables")
        return
    sample = "100000000"
    try:
        canonical = encode_state(sample)
        legacy = encode_realm(sample)
        snapshot = build_snapshot(sample)
        plan = plan_generation_function("m1_identity_check", sample)
    except Exception as exc:
        errors.append(f"Canonical executable identity interface raised an error: {exc}")
        return
    if not isinstance(canonical, dict):
        errors.append("encode_state_identity must return an identity object")
        return
    required_identity = {"state_signature": sample}
    for field, expected in required_identity.items():
        if canonical.get(field) != expected:
            errors.append(f"Canonical executable identity lacks exact {field}")
    for field in ("vertex_id", "realm_id", "orbit_id"):
        if not isinstance(canonical.get(field), str) or not canonical[field]:
            errors.append(f"Canonical executable identity lacks {field}")
    if canonical.get("vertex_id") != canonical.get("realm_id"):
        errors.append("Executable realm_id alias disagrees with canonical vertex_id")
    if legacy != canonical:
        errors.append("Legacy encode_realm_identity does not equal encode_state_identity")
    if not isinstance(snapshot, dict) or (
        snapshot.get("state_identity") != canonical
        or snapshot.get("realm_identity") != canonical
    ):
        errors.append("CosmicPatternSnapshot lacks equal canonical and compatibility identities")
    destination = None
    if isinstance(snapshot, dict) and isinstance(snapshot.get("normalized_state"), str):
        destination = encode_state(snapshot["normalized_state"])
    if not isinstance(plan, dict) or (
        plan.get("source_state_identity") != canonical
        or plan.get("source_realm") != canonical
        or plan.get("destination_state_identity") != destination
        or plan.get("destination_realm") != destination
    ):
        errors.append("GenerationPlan lacks equal canonical and compatibility identity outputs")


def check_executable_identity(root: Path, errors: list[str]) -> None:
    relative_path = "core/ash_pattern_engine/ash_canonical.py"
    try:
        namespace = runpy.run_path(str(root / relative_path))
    except Exception as exc:
        errors.append(f"Unable to load canonical executable identity interface: {exc}")
        return
    check_executable_identity_namespace(namespace, errors)


def check_semantic_surfaces(root: Path, errors: list[str]) -> None:
    for relative_path in ACTIVE_SEMANTIC_SURFACES:
        try:
            text = (root / relative_path).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"Unable to inspect semantic surface {relative_path}: {exc}")
            continue
        check_forbidden_semantic_phrases(relative_path, text, errors)
    canonical_root = root / ash_sync.SOURCE_ROOT
    if canonical_root.is_dir():
        for path in sorted(canonical_root.rglob("*")):
            if not path.is_file() or path.name == "README.md":
                continue
            relative_path = path.relative_to(root).as_posix()
            if relative_path in ACTIVE_SEMANTIC_SURFACES:
                continue
            try:
                text = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(f"Unable to inspect semantic surface {relative_path}: {exc}")
                continue
            check_forbidden_semantic_phrases(relative_path, text, errors)

    realm_registry = load_json(root, "data/realm_registry/realms.json", errors)
    if realm_registry is not None:
        check_realm_registry(realm_registry, errors)
    realm_mapping = load_yaml(root, "data/ash_state/realm_bit_mapping.yaml", errors)
    if realm_mapping is not None:
        check_realm_mapping(realm_mapping, errors)

    player_documents: dict[str, dict[str, Any]] = {}
    for relative_path in ("data/player_schema.json", "data/schemas/player_schema.json"):
        document = load_json(root, relative_path, errors)
        if document is not None:
            player_documents[relative_path] = document
    check_player_documents(player_documents, errors)

    npc_rules = load_yaml(root, "core/narrative_engine/npc_synthesis_rules.yaml", errors)
    worldstate_rules = load_yaml(root, "core/narrative_engine/worldstate_delta_rules.yaml", errors)
    if npc_rules is not None and worldstate_rules is not None:
        check_history_documents(npc_rules, worldstate_rules, errors)
    perception = load_json(root, "core/perception_engine/perception_schema.json", errors)
    if perception is not None:
        check_perception_document(perception, errors)
    check_executable_identity(root, errors)

    realm_identity_path = "core/ash_pattern_engine/canonical/core/realm-identity.pseudo.md"
    try:
        realm_identity = (root / realm_identity_path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return
    for marker in ("StateIdentity", "vertex_id", "compatibility alias", "RealmIdentity", "realm_id"):
        if marker.casefold() not in realm_identity.casefold():
            errors.append(f"ASH state identity specification lacks {marker!r}")


def check_ash_identity(
    root: Path,
    document: dict[str, Any],
    errors: list[str],
) -> None:
    try:
        expected = ash_sync.expected_manifest(root)
    except (OSError, UnicodeDecodeError, ash_sync.SynchronizationError) as exc:
        errors.append(f"Unable to compute canonical ASH dependency identity: {exc}")
        return
    if document != expected:
        errors.append("ASH dependency identity is stale relative to canonical source content")
    if len(expected.get("files", [])) < 32:
        errors.append(
            f"Canonical ASH dependency must retain at least the 32 M1 governed files; "
            f"found {len(expected.get('files', []))}"
        )
    if expected.get("canonical_profile") != {
        "field_dimension": 9,
        "state_count": 512,
        "codeword_count": 16,
    }:
        errors.append("ASH dependency identity no longer preserves the approved F2^9 profile")


def run_external_check(
    root: Path,
    relative_path: str,
    arguments: list[str],
    label: str,
    errors: list[str],
) -> None:
    script = root / relative_path
    if not script.is_file():
        errors.append(f"Missing {label} tool: {relative_path}")
        return
    result = subprocess.run(
        [sys.executable, str(script), *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        output = (result.stdout + "\n" + result.stderr).strip()
        errors.append(f"{label} failed: {output}")


def check_external_guardrails(root: Path, errors: list[str]) -> None:
    run_external_check(
        root,
        SYNC_SCRIPT_PATH,
        ["--check", "--root", str(root)],
        "ASH specification synchronization",
        errors,
    )
    run_external_check(
        root,
        PLATFORM_CHECK_PATH,
        [str(root)],
        "Platform boundary validation",
        errors,
    )
    run_external_check(
        root,
        ATTRIBUTION_CHECK_PATH,
        [str(root)],
        "Repository attribution policy validation",
        errors,
    )


def git_blob(root: Path, ref: str, relative_path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:{relative_path}"],
        check=False,
        capture_output=True,
    )
    return result.stdout if result.returncode == 0 else None


def introduction_commit(root: Path, relative_path: str) -> str | None:
    result = run_git(root, ["log", "--diff-filter=A", "--format=%H", "--", relative_path])
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return commits[-1] if result.returncode == 0 and commits else None


def check_m0_immutable(root: Path, errors: list[str]) -> None:
    for relative_path in M0_IMMUTABLE_PATHS:
        commit = introduction_commit(root, relative_path)
        if commit is None:
            errors.append(f"Unable to locate introduction commit for immutable {relative_path}")
            continue
        historical = git_blob(root, commit, relative_path)
        try:
            current = (root / relative_path).read_bytes()
            if historical is None or normalized_text_data(historical) != normalized_text_data(current):
                errors.append(f"Immutable M0 acceptance artifact changed: {relative_path}")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"Unable to verify immutable M0 artifact {relative_path}: {exc}")


def check_debt_and_roadmap(
    root: Path,
    roadmap: dict[str, Any],
    debt: dict[str, Any],
    errors: list[str],
) -> None:
    milestone_records = roadmap.get("milestones")
    milestones = {
        item.get("id"): item
        for item in milestone_records
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    } if isinstance(milestone_records, list) else {}
    if milestones.get("M0", {}).get("status") != "complete":
        errors.append("M1 closure requires the immutable M0 baseline to remain complete")
    current_milestone = roadmap.get("current_milestone")
    current_match = re.fullmatch(r"M([0-9]+)", str(current_milestone))
    if current_match is None or int(current_match.group(1)) < 2:
        errors.append("Accepted M1 requires the roadmap to have advanced to M2 or later")
    if milestones.get("M1", {}).get("status") != "complete":
        errors.append("M1 closure requires M1 status complete")
    expected_m2_status = "in_progress" if current_milestone == "M2" else "complete"
    if milestones.get("M2", {}).get("status") != expected_m2_status:
        errors.append(
            f"Accepted M1 requires M2 status {expected_m2_status} at {current_milestone}"
        )
    expected_evidence = [EVIDENCE_PATH, EVIDENCE_DOCUMENT_PATH]
    if milestones.get("M1", {}).get("acceptance_evidence") != expected_evidence:
        errors.append(f"Completed M1 must reference exactly {expected_evidence}")

    if current_milestone == "M2":
        publication = roadmap.get("publication")
        if not isinstance(publication, dict) or (
            publication.get("state") != "unreleased"
            or publication.get("published_releases") != 0
            or publication.get("github_release_objects") != 0
            or publication.get("agnostic_specification_releases") != 0
        ):
            errors.append("M1 transition roadmap makes an unsupported publication or release claim")
        platform_gate = roadmap.get("platform_gate")
        if not isinstance(platform_gate, dict) or (
            platform_gate.get("authorized_after") != "M10"
            or platform_gate.get("status") != "deferred"
            or platform_gate.get("platform_work_authorized") is not False
        ):
            errors.append("M1 transition roadmap authorizes platform work before the M10 gate")

    subsystem_records = roadmap.get("subsystems")
    authority = next(
        (
            item
            for item in subsystem_records
            if isinstance(item, dict) and item.get("id") == "authority_boundaries"
        ),
        {},
    ) if isinstance(subsystem_records, list) else {}
    if authority.get("open_work") != []:
        errors.append("Authority-boundaries subsystem still records open M1 work")
    maturity = authority.get("maturity")
    for dimension in (
        "normative_artifact_complete",
        "executable_schema_complete",
        "conformance_tested",
        "release_ready",
    ):
        if not isinstance(maturity, dict) or maturity.get(dimension) != "complete":
            errors.append(f"Authority-boundaries subsystem has incomplete {dimension}")

    debt_records = debt.get("debts")
    records = [item for item in debt_records if isinstance(item, dict)] if isinstance(debt_records, list) else []
    assigned_ids = {
        item.get("debt_id")
        for item in records
        if item.get("assigned_milestone") == "M1"
    }
    if assigned_ids != EXPECTED_M1_DEBT_IDS:
        errors.append(
            "M1 debt assignment set changed; "
            f"missing={sorted(EXPECTED_M1_DEBT_IDS - assigned_ids)}, "
            f"unexpected={sorted(assigned_ids - EXPECTED_M1_DEBT_IDS)}"
        )
    by_id = {
        item.get("debt_id"): item
        for item in records
        if isinstance(item.get("debt_id"), str)
    }
    for debt_id in sorted(EXPECTED_M1_DEBT_IDS):
        record = by_id.get(debt_id)
        if record is None:
            continue
        if record.get("status") != "resolved":
            errors.append(f"M1 debt is not resolved: {debt_id}")
        evidence = record.get("resolution_evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"M1 debt lacks resolution evidence: {debt_id}")
        else:
            check_reference_paths(root, evidence, debt_id, errors)
        check_evidence_locators(
            root,
            record.get("resolution_evidence_details"),
            f"{debt_id} resolution evidence",
            errors,
        )


def check_provisional_debt_and_roadmap(
    roadmap: dict[str, Any],
    debt: dict[str, Any],
    errors: list[str],
) -> None:
    milestone_records = roadmap.get("milestones")
    milestones = {
        item.get("id"): item
        for item in milestone_records
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    } if isinstance(milestone_records, list) else {}
    if milestones.get("M0", {}).get("status") != "complete":
        errors.append("Active M1 requires the immutable M0 baseline to remain complete")
    if roadmap.get("current_milestone") != "M1":
        errors.append("Provisional M1 state must keep M1 as the current milestone")
    if milestones.get("M1", {}).get("status") != "in_progress":
        errors.append("Provisional M1 state must keep M1 in progress")
    if milestones.get("M1", {}).get("acceptance_evidence") != []:
        errors.append("Provisional M1 must not claim acceptance evidence before closure")
    if milestones.get("M2", {}).get("status") != "planned":
        errors.append("Provisional M1 state must keep M2 planned")

    publication = roadmap.get("publication")
    if not isinstance(publication, dict) or (
        publication.get("state") != "unreleased"
        or publication.get("published_releases") != 0
        or publication.get("github_release_objects") != 0
        or publication.get("agnostic_specification_releases") != 0
    ):
        errors.append("Provisional M1 makes an unsupported publication or release claim")
    platform_gate = roadmap.get("platform_gate")
    if not isinstance(platform_gate, dict) or (
        platform_gate.get("authorized_after") != "M10"
        or platform_gate.get("status") != "deferred"
        or platform_gate.get("platform_work_authorized") is not False
    ):
        errors.append("Provisional M1 authorizes platform work before the M10 gate")

    debt_records = debt.get("debts")
    records = [item for item in debt_records if isinstance(item, dict)] if isinstance(debt_records, list) else []
    assigned_ids = {
        item.get("debt_id")
        for item in records
        if item.get("assigned_milestone") == "M1"
    }
    if assigned_ids != EXPECTED_M1_DEBT_IDS:
        errors.append(
            "Provisional M1 debt assignment set changed; "
            f"missing={sorted(EXPECTED_M1_DEBT_IDS - assigned_ids)}, "
            f"unexpected={sorted(assigned_ids - EXPECTED_M1_DEBT_IDS)}"
        )


def closure_requested(
    root: Path,
    roadmap: dict[str, Any],
    evidence: dict[str, Any],
) -> bool:
    milestones = roadmap.get("milestones")
    m1 = next(
        (
            item
            for item in milestones
            if isinstance(item, dict) and item.get("id") == "M1"
        ),
        {},
    ) if isinstance(milestones, list) else {}
    return bool(
        evidence
        or (root / EVIDENCE_PATH).is_file()
        or (root / EVIDENCE_DOCUMENT_PATH).is_file()
        or m1.get("status") == "complete"
        or roadmap.get("current_milestone") == "M2"
    )


def repository_candidate_paths(root: Path, errors: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        errors.append("Unable to enumerate repository paths for M1 evidence digest")
        return []
    try:
        return [
            item.decode("utf-8")
            for item in result.stdout.split(b"\0")
            if item
        ]
    except UnicodeDecodeError as exc:
        errors.append(f"Repository path list is not UTF-8: {exc}")
        return []


def repository_snapshot_files(
    root: Path,
    ref: str,
    errors: list[str],
) -> dict[str, bytes] | None:
    result = subprocess.run(
        ["git", "-C", str(root), "archive", "--format=tar", ref],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        errors.append(f"Unable to read repository snapshot at {ref}")
        return None
    files: dict[str, bytes] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                stream = archive.extractfile(member)
                if stream is None:
                    errors.append(f"Unable to read snapshot member {member.name}")
                    return None
                files[member.name] = stream.read()
    except (tarfile.TarError, OSError) as exc:
        errors.append(f"Unable to parse repository snapshot at {ref}: {exc}")
        return None
    return files


def snapshot_json(
    files: dict[str, bytes],
    relative_path: str,
    errors: list[str],
) -> dict[str, Any] | None:
    value = files.get(relative_path)
    if value is None:
        errors.append(f"Evidence-introduction snapshot lacks {relative_path}")
        return None
    try:
        document = json.loads(
            normalized_text_data(value).decode("utf-8"),
            object_pairs_hook=unique_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        errors.append(f"Unable to load historical {relative_path}: {exc}")
        return None
    if not isinstance(document, dict):
        errors.append(f"Historical {relative_path} must contain a JSON object")
        return None
    return document


def repository_state_digest_from_files(
    files: dict[str, bytes],
    exclusions: set[str],
    errors: list[str],
) -> str | None:
    payload = bytearray()
    try:
        for relative_path in sorted(set(files) - exclusions):
            content_hash = hashlib.sha256(normalized_text_data(files[relative_path])).hexdigest()
            payload.extend(relative_path.encode("utf-8"))
            payload.extend(b"\0")
            payload.extend(content_hash.encode("ascii"))
            payload.extend(b"\0")
    except UnicodeDecodeError as exc:
        errors.append(f"Unable to compute M1 repository state digest: {exc}")
        return None
    return hashlib.sha256(bytes(payload)).hexdigest()


def repository_state_digest(
    root: Path,
    paths: Iterable[str],
    exclusions: set[str],
    errors: list[str],
) -> str | None:
    files: dict[str, bytes] = {}
    try:
        for relative_path in sorted(set(paths) - exclusions):
            path = root / relative_path
            if not path.is_file():
                continue
            files[relative_path] = path.read_bytes()
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"Unable to compute M1 repository state digest: {exc}")
        return None
    return repository_state_digest_from_files(files, exclusions, errors)


def checked_git_value(root: Path, args: list[str], label: str, errors: list[str]) -> str | None:
    result = run_git(root, args)
    value = result.stdout.strip()
    if result.returncode != 0 or not value:
        errors.append(f"Unable to resolve {label}: {result.stderr.strip()}")
        return None
    return value


def historical_diff_review(
    root: Path,
    base_sha: str,
    introduction_commit_sha: str,
    errors: list[str],
) -> dict[str, Any] | None:
    pathspec = [
        ".",
        f":(exclude){EVIDENCE_PATH}",
        f":(exclude){EVIDENCE_DOCUMENT_PATH}",
    ]
    common = [
        base_sha,
        introduction_commit_sha,
        "--",
        *pathspec,
    ]
    diff_result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "--binary",
            "--no-ext-diff",
            "--find-renames=50%",
            *common,
        ],
        check=False,
        capture_output=True,
    )
    status_result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "--name-status",
            "--find-renames=50%",
            *common,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if diff_result.returncode != 0 or status_result.returncode != 0:
        errors.append("Unable to compute the historical non-circular M1 diff review")
        return None
    counts = {
        "files_created": 0,
        "files_patched": 0,
        "files_deleted": 0,
        "files_renamed": 0,
    }
    for line in status_result.stdout.splitlines():
        if not line:
            continue
        status = line.split("\t", 1)[0]
        kind = status[:1]
        if kind == "A":
            counts["files_created"] += 1
        elif kind in {"M", "T"}:
            counts["files_patched"] += 1
        elif kind == "D":
            counts["files_deleted"] += 1
        elif kind == "R":
            counts["files_renamed"] += 1
        elif kind == "C":
            counts["files_created"] += 1
        else:
            errors.append(f"Unsupported historical diff status {status!r}")
    return {
        **counts,
        "diff_hash_algorithm": "sha256_git_diff_binary_excluding_m1_evidence",
        "diff_sha256": hashlib.sha256(diff_result.stdout).hexdigest(),
    }


def applicable_catalog_check_count(catalog: dict[str, Any], context: str) -> int:
    checks = catalog.get("checks")
    if not isinstance(checks, list):
        return 0
    return sum(
        1
        for item in checks
        if isinstance(item, dict)
        and isinstance(item.get("contexts"), list)
        and ("always" in item["contexts"] or context in item["contexts"])
    )


def check_catalog_m1_groups(catalog: dict[str, Any], errors: list[str]) -> None:
    checks = catalog.get("checks")
    by_id = {
        item.get("id"): item
        for item in checks
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    } if isinstance(checks, list) else {}
    for check_id in ("ash_specification_sync", "m1_canon_governance"):
        record = by_id.get(check_id)
        if not isinstance(record, dict) or "m1" not in record.get("groups", []):
            errors.append(f"Repository check {check_id} must carry the literal m1 group")


def check_evidence_baseline(
    root: Path,
    evidence: dict[str, Any],
    errors: list[str],
    snapshot_files: dict[str, bytes] | None = None,
) -> None:
    baseline = evidence.get("baseline")
    if not isinstance(baseline, dict):
        errors.append("M1 evidence lacks repository baseline information")
        return
    try:
        if snapshot_files is None:
            version = (root / "VERSION").read_text(encoding="utf-8-sig").strip()
        else:
            version = normalized_text_data(snapshot_files["VERSION"]).decode("utf-8").strip()
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"Unable to read repository VERSION: {exc}")
        version = None
    except KeyError:
        errors.append("Evidence-introduction snapshot lacks VERSION")
        version = None
    if baseline.get("repository_version") != version:
        errors.append("M1 evidence repository version is stale")
    if baseline.get("base_ref") != "origin/main":
        errors.append("M1 evidence base_ref must be origin/main")
    if baseline.get("branch") != "governance/m1-canon-terminology":
        errors.append("M1 evidence records the wrong implementation branch")
    base_sha = baseline.get("base_sha")
    merge_base = baseline.get("merge_base")
    if (
        not isinstance(base_sha, str)
        or re.fullmatch(r"[a-f0-9]{40}", base_sha) is None
        or merge_base != base_sha
    ):
        errors.append("M1 evidence base_sha and merge_base must be the same valid baseline commit")


def check_m1_evidence_immutable_and_historical(
    root: Path,
    evidence: dict[str, Any],
    errors: list[str],
) -> None:
    introduction_commits: dict[str, str] = {}
    for relative_path in M1_EVIDENCE_PATHS:
        commit = introduction_commit(root, relative_path)
        if commit is None:
            errors.append(f"Unable to locate introduction commit for immutable {relative_path}")
            continue
        introduction_commits[relative_path] = commit
        historical = git_blob(root, commit, relative_path)
        try:
            current = (root / relative_path).read_bytes()
            if historical is None or normalized_text_data(historical) != normalized_text_data(current):
                errors.append(f"Immutable M1 acceptance artifact changed: {relative_path}")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"Unable to verify immutable M1 artifact {relative_path}: {exc}")

    evidence_commit = introduction_commits.get(EVIDENCE_PATH)
    baseline = evidence.get("baseline")
    if evidence_commit is None or not isinstance(baseline, dict):
        return
    base_sha = baseline.get("base_sha")
    merge_base = baseline.get("merge_base")
    if not isinstance(base_sha, str) or merge_base != base_sha:
        return
    commit_check = run_git(root, ["cat-file", "-e", f"{base_sha}^{{commit}}"])
    if commit_check.returncode != 0:
        errors.append("M1 evidence base_sha does not resolve to a commit")
        return
    ancestor = run_git(root, ["merge-base", "--is-ancestor", base_sha, evidence_commit])
    if ancestor.returncode != 0:
        errors.append("M1 evidence base_sha was not an origin/main ancestor at evidence introduction")
    actual_merge_base = checked_git_value(
        root,
        ["merge-base", base_sha, evidence_commit],
        "historical M1 evidence merge base",
        errors,
    )
    if actual_merge_base is not None and actual_merge_base != base_sha:
        errors.append("M1 evidence historical merge-base relationship is invalid")


def check_evidence_catalog_and_runs(
    root: Path,
    evidence: dict[str, Any],
    catalog: dict[str, Any],
    errors: list[str],
    snapshot_files: dict[str, bytes] | None = None,
) -> None:
    check_catalog = evidence.get("check_catalog")
    if snapshot_files is None:
        catalog_sha256 = normalized_sha256(root / CHECK_CATALOG_PATH)
    else:
        catalog_bytes = snapshot_files.get(CHECK_CATALOG_PATH)
        if catalog_bytes is None:
            errors.append(f"Evidence-introduction snapshot lacks {CHECK_CATALOG_PATH}")
            return
        catalog_sha256 = hashlib.sha256(normalized_text_data(catalog_bytes)).hexdigest()
    expected_catalog = {
        "path": CHECK_CATALOG_PATH,
        "hash_algorithm": "sha256_utf8_lf_normalized",
        "sha256": catalog_sha256,
    }
    if check_catalog != expected_catalog:
        errors.append(
            f"M1 evidence check catalog identity is stale: expected {expected_catalog}, "
            f"found {check_catalog}"
        )
    runs = evidence.get("validation_runs")
    if not isinstance(runs, list):
        errors.append("M1 evidence validation_runs must be an array")
        return
    contexts = [run.get("context") for run in runs if isinstance(run, dict)]
    if contexts != ["local", "pull_request"]:
        errors.append("M1 evidence must record local validation before pull-request validation")
    for run in runs:
        if not isinstance(run, dict):
            continue
        context = run.get("context")
        if context not in {"local", "pull_request"}:
            continue
        expected_count = applicable_catalog_check_count(catalog, context)
        if run.get("check_count") != expected_count or run.get("passed") != expected_count:
            errors.append(
                f"M1 {context} validation counts are stale: expected {expected_count} passing checks"
            )
        summary = run.get("result_summary")
        if isinstance(summary, str):
            actual_hash = hashlib.sha256(
                normalized_text_data(summary.encode("utf-8"))
            ).hexdigest()
            if run.get("result_summary_sha256") != actual_hash:
                errors.append(f"M1 {context} validation summary hash is stale")


def evidence_classification_metrics(classification: dict[str, Any]) -> dict[str, Any]:
    class_counts = classification.get("coverage", {}).get("counts_by_class", {})
    tracked_path_count = classification.get("tracked_path_snapshot", {}).get("path_count")
    return {
        "tracked_paths": tracked_path_count,
        "classified_paths": sum(
            class_counts.get(metric, 0) for metric in CLASSIFICATION_METRIC_KEYS
        ),
        "unclassified_paths": 0,
        "multiply_classified_paths": 0,
        **{
            metric: class_counts.get(metric, 0)
            for metric in CLASSIFICATION_METRIC_KEYS
        },
    }


def evidence_scope_metrics(scope_manifest: dict[str, Any]) -> dict[str, int]:
    scope_counts = scope_manifest.get("coverage", {}).get("counts_by_partition", {})
    return {
        metric: scope_counts.get(metric, 0) for metric in SCOPE_METRIC_KEYS
    }


def check_evidence(
    root: Path,
    evidence: dict[str, Any],
    requirements: dict[str, Any],
    record_document: dict[str, Any],
    terms: dict[str, Any],
    lattice: dict[str, Any],
    ash_identity: dict[str, Any],
    catalog: dict[str, Any],
    classification: dict[str, Any],
    scope_manifest: dict[str, Any],
    errors: list[str],
    snapshot_files: dict[str, bytes] | None = None,
    evidence_commit: str | None = None,
) -> None:
    check_evidence_baseline(root, evidence, errors, snapshot_files)
    try:
        check_evidence_catalog_and_runs(root, evidence, catalog, errors, snapshot_files)
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"Unable to verify the M1 validation catalog: {exc}")

    if evidence.get("digest_exclusions") != list(M1_EVIDENCE_PATHS):
        errors.append("M1 evidence digest exclusions are not the exact evidence pair")
    if snapshot_files is None:
        paths = repository_candidate_paths(root, errors)
        actual_digest = repository_state_digest(root, paths, set(M1_EVIDENCE_PATHS), errors)
    else:
        actual_digest = repository_state_digest_from_files(
            snapshot_files,
            set(M1_EVIDENCE_PATHS),
            errors,
        )
    if actual_digest is not None and evidence.get("repository_state_digest") != actual_digest:
        errors.append("M1 evidence repository state digest is stale")

    deliverable_ids = {
        item.get("id") for item in evidence.get("deliverables", []) if isinstance(item, dict)
    }
    exit_ids = {
        item.get("id") for item in evidence.get("exit_criteria", []) if isinstance(item, dict)
    }
    if deliverable_ids != {f"m1-d{number}" for number in range(1, 11)}:
        errors.append("M1 evidence does not contain the exact ten deliverable judgments")
    if exit_ids != {f"m1-e{number}" for number in range(1, 4)}:
        errors.append("M1 evidence does not contain the exact three exit judgments")
    for judgment in [
        *evidence.get("deliverables", []),
        *evidence.get("exit_criteria", []),
    ]:
        if not isinstance(judgment, dict):
            continue
        if judgment.get("outcome") != "pass":
            errors.append(f"M1 judgment {judgment.get('id')} is not passing")
        check_reference_paths(
            root,
            judgment.get("evidence_refs"),
            str(judgment.get("id", "M1 judgment")),
            errors,
            snapshot_files,
        )

    closures = [
        item for item in evidence.get("debt_closures", []) if isinstance(item, dict)
    ]
    closure_ids = {item.get("debt_id") for item in closures}
    if closure_ids != EXPECTED_M1_DEBT_IDS or len(closures) != len(EXPECTED_M1_DEBT_IDS):
        errors.append("M1 evidence does not contain the exact ten debt closures")
    for closure in closures:
        if closure.get("outcome") != "resolved":
            errors.append(f"M1 debt closure {closure.get('debt_id')} is not resolved")
        check_reference_paths(
            root,
            closure.get("evidence_refs"),
            str(closure.get("debt_id", "M1 debt closure")),
            errors,
            snapshot_files,
        )
        check_evidence_locators(
            root,
            closure.get("evidence_details"),
            str(closure.get("debt_id", "M1 debt closure")),
            errors,
            snapshot_files,
        )

    expected_metrics = {
        "requirement_count": len(requirements.get("requirements", [])),
        "governance_record_count": len(governance_records(record_document)),
        "term_count": len(terms.get("terms", [])),
        "authority_node_count": len(lattice.get("nodes", [])),
        "ash_source_file_count": len(ash_identity.get("files", [])),
        "ash_source_aggregate_sha256": ash_identity.get("aggregate_sha256"),
    }
    if evidence.get("authority_metrics") != expected_metrics:
        errors.append(
            f"M1 evidence authority metrics are stale: expected {expected_metrics}, "
            f"found {evidence.get('authority_metrics')}"
        )

    expected_classification_metrics = evidence_classification_metrics(classification)
    if evidence.get("classification_metrics") != expected_classification_metrics:
        errors.append(
            "M1 evidence classification metrics are stale: "
            f"expected {expected_classification_metrics}, "
            f"found {evidence.get('classification_metrics')}"
        )

    expected_scope_metrics = evidence_scope_metrics(scope_manifest)
    if evidence.get("scope_metrics") != expected_scope_metrics:
        errors.append(
            f"M1 evidence scope metrics are stale: expected {expected_scope_metrics}, "
            f"found {evidence.get('scope_metrics')}"
        )

    diff_review = evidence.get("diff_review")
    if not isinstance(diff_review, dict) or (
        diff_review.get("base_ref") != "origin/main"
        or diff_review.get("files_deleted") != 0
        or diff_review.get("files_renamed") != 0
        or diff_review.get("m0_acceptance_files_changed") is not False
    ):
        errors.append("M1 evidence diff review violates non-destructive closure constraints")
    if isinstance(diff_review, dict) and evidence_commit is not None:
        base_sha = evidence.get("baseline", {}).get("base_sha")
        if isinstance(base_sha, str):
            historical_diff = historical_diff_review(
                root,
                base_sha,
                evidence_commit,
                errors,
            )
            if historical_diff is not None:
                for field, expected in historical_diff.items():
                    if diff_review.get(field) != expected:
                        errors.append(
                            f"M1 evidence diff review {field} is stale: "
                            f"expected {expected!r}, found {diff_review.get(field)!r}"
                        )

    math_review = evidence.get("math_change_review")
    if not isinstance(math_review, dict):
        errors.append("M1 evidence lacks the required math-change review")
    else:
        note_path = math_review.get("note_path")
        if not isinstance(note_path, str) or not repository_ref_exists(
            root,
            note_path,
            snapshot_files,
        ):
            errors.append("M1 evidence math-change note is missing")
        else:
            try:
                if snapshot_files is None:
                    note = (root / note_path).read_text(encoding="utf-8-sig")
                else:
                    note = normalized_text_data(snapshot_files[note_path]).decode("utf-8")
                headings = set(re.findall(r"(?m)^## ([^\r\n]+)$", note))
                required = {"What changed", "Why", "Baseline preservation statement"}
                if not required.issubset(headings):
                    errors.append("M1 math-change note lacks required review sections")
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(f"Unable to inspect M1 math-change note: {exc}")
        label = math_review.get("label_observation")
        if not isinstance(label, dict) or label.get("label") != math_review.get("required_label"):
            errors.append("M1 math-change review label observation is inconsistent")
        if math_review.get("baseline_shape_preserved") is not True:
            errors.append("M1 math-change review does not preserve the approved baseline shape")

    check_evidence_transition(evidence, errors)
    if evidence.get("publication_state") != "unreleased":
        errors.append("M1 evidence makes an unsupported publication claim")
    if evidence.get("platform_work_authorized") is not False:
        errors.append("M1 evidence authorizes platform implementation work")
    if evidence.get("unresolved_issues") != []:
        errors.append("Passing M1 evidence contains unresolved issues")


def check_evidence_transition(evidence: dict[str, Any], errors: list[str]) -> None:
    transition = evidence.get("roadmap_transition")
    expected = {
        "completed_milestone": "M1",
        "activated_milestone": "M2",
        "current_milestone": "M2",
    }
    if transition != expected:
        errors.append(f"M1 evidence roadmap transition is invalid; expected {expected}")


def validation_errors(
    root: Path,
    *,
    run_external: bool = True,
) -> list[str]:
    errors: list[str] = []
    required_documents = (
        REQUIREMENT_PATH,
        GOVERNANCE_RECORD_PATH,
        TERM_INDEX_PATH,
        LATTICE_PATH,
        ASH_IDENTITY_PATH,
        ROADMAP_PATH,
        DEBT_PATH,
        CHECK_CATALOG_PATH,
        CLASSIFICATION_PATH,
        SCOPE_MANIFEST_PATH,
    )
    documents: dict[str, dict[str, Any]] = {}
    for relative_path in required_documents:
        document = load_json(root, relative_path, errors)
        if document is None:
            continue
        documents[relative_path] = document
        if relative_path in {
            REQUIREMENT_PATH,
            GOVERNANCE_RECORD_PATH,
            TERM_INDEX_PATH,
            LATTICE_PATH,
            ASH_IDENTITY_PATH,
            EVIDENCE_PATH,
            CLASSIFICATION_PATH,
            SCOPE_MANIFEST_PATH,
        }:
            validate_bound_instance(root, relative_path, document, errors)

    if (root / EVIDENCE_PATH).is_file():
        evidence_document = load_json(root, EVIDENCE_PATH, errors)
        if evidence_document is not None:
            documents[EVIDENCE_PATH] = evidence_document
            if introduction_commit(root, EVIDENCE_PATH) is None:
                validate_bound_instance(root, EVIDENCE_PATH, evidence_document, errors)

    requirements = documents.get(REQUIREMENT_PATH, {})
    records = documents.get(GOVERNANCE_RECORD_PATH, {})
    terms = documents.get(TERM_INDEX_PATH, {})
    lattice = documents.get(LATTICE_PATH, {})
    ash_identity = documents.get(ASH_IDENTITY_PATH, {})
    roadmap = documents.get(ROADMAP_PATH, {})
    debt = documents.get(DEBT_PATH, {})
    evidence = documents.get(EVIDENCE_PATH, {})
    catalog = documents.get(CHECK_CATALOG_PATH, {})
    classification = documents.get(CLASSIFICATION_PATH, {})
    scope_manifest = documents.get(SCOPE_MANIFEST_PATH, {})

    if requirements:
        check_requirements(root, requirements, errors)
    if catalog:
        check_catalog_m1_groups(catalog, errors)
    check_normative_clauses(root, errors)
    if records:
        check_governance_records(root, records, errors)
    if terms:
        check_terms(root, terms, errors)
    if lattice:
        check_lattice(lattice, errors)
        check_lattice_document(root, errors)
    class_assignments: dict[str, dict[str, Any]] = {}
    if classification and scope_manifest:
        class_assignments, _scope_assignments = check_scope_separation(
            root,
            classification,
            scope_manifest,
            errors,
        )
    check_semantic_surfaces(root, errors)
    if ash_identity:
        check_ash_identity(root, ash_identity, errors)
    if run_external:
        check_external_guardrails(root, errors)
    check_m0_immutable(root, errors)
    closure = closure_requested(root, roadmap, evidence)
    if roadmap and debt:
        if closure:
            check_debt_and_roadmap(root, roadmap, debt, errors)
        else:
            check_provisional_debt_and_roadmap(roadmap, debt, errors)
    if evidence:
        snapshot_files: dict[str, bytes] | None = None
        evidence_inputs = {
            REQUIREMENT_PATH: requirements,
            GOVERNANCE_RECORD_PATH: records,
            TERM_INDEX_PATH: terms,
            LATTICE_PATH: lattice,
            ASH_IDENTITY_PATH: ash_identity,
            CHECK_CATALOG_PATH: catalog,
            CLASSIFICATION_PATH: classification,
            SCOPE_MANIFEST_PATH: scope_manifest,
        }
        evidence_commit = introduction_commit(root, EVIDENCE_PATH)
        if evidence_commit is not None:
            snapshot_files = repository_snapshot_files(root, evidence_commit, errors)
            if snapshot_files is not None:
                validate_snapshot_bound_instance(
                    EVIDENCE_PATH,
                    evidence,
                    snapshot_files,
                    errors,
                )
                for relative_path in tuple(evidence_inputs):
                    historical = snapshot_json(snapshot_files, relative_path, errors)
                    if historical is not None:
                        evidence_inputs[relative_path] = historical
                check_temporal_normative_clauses(
                    root,
                    class_assignments,
                    snapshot_files,
                    errors,
                )
        check_evidence(
            root,
            evidence,
            evidence_inputs[REQUIREMENT_PATH],
            evidence_inputs[GOVERNANCE_RECORD_PATH],
            evidence_inputs[TERM_INDEX_PATH],
            evidence_inputs[LATTICE_PATH],
            evidence_inputs[ASH_IDENTITY_PATH],
            evidence_inputs[CHECK_CATALOG_PATH],
            evidence_inputs[CLASSIFICATION_PATH],
            evidence_inputs[SCOPE_MANIFEST_PATH],
            errors,
            snapshot_files,
            evidence_commit,
        )
        check_m1_evidence_immutable_and_historical(root, evidence, errors)
    elif closure:
        errors.append(f"Missing M1 acceptance evidence: {EVIDENCE_PATH}")
    if closure and not (root / EVIDENCE_DOCUMENT_PATH).is_file():
        errors.append(f"Missing M1 acceptance document: {EVIDENCE_DOCUMENT_PATH}")
    return errors


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    root = Path(arguments[0] if arguments else ".").resolve()
    errors = validation_errors(root)
    if errors:
        print("M1 canon terminology and governance check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    requirements = json.loads((root / REQUIREMENT_PATH).read_text(encoding="utf-8-sig"))
    records = json.loads((root / GOVERNANCE_RECORD_PATH).read_text(encoding="utf-8-sig"))
    terms = json.loads((root / TERM_INDEX_PATH).read_text(encoding="utf-8-sig"))
    ash_identity = json.loads((root / ASH_IDENTITY_PATH).read_text(encoding="utf-8-sig"))
    print(
        "M1 canon terminology and governance check passed "
        f"({len(requirements.get('requirements', []))} requirements; "
        f"{len(governance_records(records))} governance records; "
        f"{len(terms.get('terms', []))} canonical terms; "
        f"{len(ash_identity.get('files', []))} ASH source files)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
