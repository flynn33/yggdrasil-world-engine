#!/usr/bin/env python3
"""Validate the roadmap, check catalog, version truth, and platform gate."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("Missing validation dependencies. Install scripts/requirements.txt.")
    raise SystemExit(1)

ROADMAP_PATH = "data/governance/specification_roadmap.json"
ROADMAP_SCHEMA_PATH = "data/schemas/specification_roadmap_schema.json"
CHECKS_PATH = "data/validation/repository_checks.json"
CHECKS_SCHEMA_PATH = "data/schemas/repository_check_manifest_schema.json"
ROADMAP_DOCUMENT_PATH = "docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md"
DEBT_PATH = "data/validation/schema_quality_baseline.json"
README_STATUS_START = "<!-- roadmap-status:start -->"
README_STATUS_END = "<!-- roadmap-status:end -->"
STATUS_INDICATORS = {
    "complete": "🟢",
    "in_progress": "🟡",
    "planned": "⚪",
    "blocked": "🔴",
    "deferred": "⏸️",
}
REQUIRED_CHECK_CONTRACTS = [
    ("roadmap_governance", "scripts/check_specification_roadmap.py", ["bootstrap", "status", "governance"]),
    ("machine_readable_artifacts", "scripts/check_machine_readable_artifacts.py", ["syntax", "schema", "machine-readable"]),
    ("validation_unit_tests", "<unit-tests>", ["bootstrap", "tests"]),
    ("architecture_structure", "scripts/validate_architecture.py", ["architecture", "governance", "legacy-structural"]),
    ("governance_contracts", "scripts/check_governance_contracts.py", ["governance", "architecture"]),
    ("legacy_schema_contracts", "scripts/validate_schemas.py", ["schema", "legacy-structural", "phase"]),
    ("ash_compliance", "scripts/validate_ash_compliance.py", ["ash", "governance"]),
    ("ash_semantic_integrity", ".github/scripts/semantic_integrity_check.py", ["ash"]),
    ("ash_math_integrity", ".github/scripts/math_integrity_check.py", ["ash"]),
    ("ash_downstream_conformance", ".github/scripts/downstream_conformance_check.py", ["ash", "conformance"]),
    ("package_acceptance", ".github/scripts/ywe_package_acceptance_check.py", ["ash", "conformance", "legacy-structural"]),
    ("required_authority_contracts", "scripts/check_required_contracts.py", ["governance", "phase"]),
    ("phase_8_9_required_artifacts", "scripts/check_phase_8_9_required_artifacts.py", ["phase", "legacy-structural"]),
    ("authority_stack", "<authority-stack>", ["governance", "phase"]),
    ("branch_reality", "scripts/check_branch_reality_guardrail.py", ["phase", "legacy-structural"]),
    ("phase_9_schema_semantics", "scripts/check_phase_9_schema_semantics.py", ["phase", "legacy-structural"]),
    ("phase_8_9_package_boundary", "scripts/check_phase_8_9_package_boundary.py", ["phase", "legacy-structural"]),
    ("player_runtime_state", "scripts/check_player_runtime_state.py", ["phase", "legacy-structural"]),
    ("worldstate_location_mutation", "scripts/check_worldstate_location_mutation.py", ["phase", "legacy-structural"]),
    ("quest_npc_lore", "scripts/check_quest_npc_lore_generation.py", ["phase", "legacy-structural"]),
    ("source_truth_alignment", "scripts/check_source_truth_alignment.py", ["phase", "governance", "legacy-structural"]),
    ("ability_power_engine", "scripts/check_ability_power_engine.py", ["phase", "legacy-structural"]),
    ("phase_15a_companion_reward", "scripts/check_phase_15a_companion_reward_foundation.py", ["phase", "legacy-structural"]),
    ("phase_16_17_recovery", "scripts/check_phase_16_17_recovery.py", ["phase", "legacy-structural"]),
    ("platform_agnosticism", "scripts/check_platform_agnosticism.py", ["platform", "governance"]),
    ("repository_attribution_policy", "scripts/check_repository_attribution_policy.py", ["attribution", "governance"]),
    ("non_destructive_diff", "<non-destructive-diff>", ["diff", "change-safety"]),
]


def load_json(path: Path):
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def dotted_value(value: dict, dotted_path: str):
    current = value
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_path)
        current = current[part]
    return current


def schema_errors(instance, schema: dict, label: str) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        pointer = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{label}:{pointer}: {error.message}")
    return errors


def expected_check_command(check_id: str, script: str) -> list[str]:
    if check_id == "validation_unit_tests":
        return ["{python}", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
    if check_id == "authority_stack":
        return [
            "{python}",
            "scripts/check_authority_stack.py",
            "--config",
            "data/validation/repository_drift_guardrail_rules.json",
            "{root}",
        ]
    if check_id == "non_destructive_diff":
        return [
            "{python}",
            "scripts/check_non_destructive_diff.py",
            "--base",
            "{base}",
            "--head",
            "HEAD",
            "{root}",
        ]
    return ["{python}", script, "{root}"]


def catalog_contract_errors(check_manifest: dict) -> list[str]:
    errors = []
    checks = check_manifest.get("checks", [])
    expected_ids = [item[0] for item in REQUIRED_CHECK_CONTRACTS]
    actual_ids = [item.get("id") for item in checks]
    if actual_ids != expected_ids:
        errors.append("Check catalog IDs or execution order differ from the required contract")
    by_id = {item.get("id"): item for item in checks}
    for check_id, script, groups in REQUIRED_CHECK_CONTRACTS:
        check = by_id.get(check_id)
        if not check:
            errors.append(f"Required check contract is missing: {check_id}")
            continue
        expected_contexts = ["pull_request"] if check_id == "non_destructive_diff" else ["always"]
        expected_command = expected_check_command(check_id, script)
        if check.get("command") != expected_command:
            errors.append(f"Required check {check_id} command changed")
        if check.get("groups") != groups:
            errors.append(f"Required check {check_id} groups changed")
        if check.get("contexts") != expected_contexts:
            errors.append(f"Required check {check_id} contexts changed")
        if check.get("blocking") is not True:
            errors.append(f"Required check {check_id} must remain blocking")
    return errors


def dependency_errors(milestones: list[dict]) -> list[str]:
    errors = []
    by_id = {item["id"]: item for item in milestones}
    expected = [f"M{number}" for number in range(11)]
    actual = [item["id"] for item in milestones]
    if actual != expected:
        errors.append(f"Milestones must be ordered exactly as {expected}; found {actual}")
    if len(by_id) != len(milestones):
        errors.append("Milestone identifiers must be unique")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(milestone_id: str) -> None:
        if milestone_id in visiting:
            errors.append(f"Milestone dependency cycle includes {milestone_id}")
            return
        if milestone_id in visited or milestone_id not in by_id:
            return
        visiting.add(milestone_id)
        for dependency in by_id[milestone_id].get("dependencies", []):
            if dependency not in by_id:
                errors.append(f"{milestone_id} references unknown dependency {dependency}")
            else:
                visit(dependency)
        visiting.remove(milestone_id)
        visited.add(milestone_id)

    for milestone_id in by_id:
        visit(milestone_id)
    for milestone in milestones:
        effort = milestone["effort_weeks"]
        if effort["minimum"] > effort["maximum"]:
            errors.append(f"{milestone['id']} effort minimum exceeds its maximum")
    return errors


def milestone_completion_errors(root: Path, milestones: list[dict]) -> list[str]:
    errors = []
    by_id = {item["id"]: item for item in milestones}
    for milestone in milestones:
        evidence = milestone["acceptance_evidence"]
        for evidence_ref in evidence:
            if not (root / evidence_ref).is_file():
                errors.append(f"Milestone {milestone['id']} evidence does not exist: {evidence_ref}")
        if milestone["status"] != "complete":
            continue
        incomplete_dependencies = [
            dependency
            for dependency in milestone["dependencies"]
            if by_id[dependency]["status"] != "complete"
        ]
        if incomplete_dependencies:
            errors.append(
                f"Completed milestone {milestone['id']} has incomplete dependencies {incomplete_dependencies}"
            )
        if not evidence:
            errors.append(f"Completed milestone {milestone['id']} requires acceptance evidence")
    return errors


def dependency_text(dependencies: list[str]) -> str:
    if not dependencies:
        return "none"
    if len(dependencies) == 1:
        return dependencies[0]
    if len(dependencies) == 2:
        return f"{dependencies[0]} and {dependencies[1]}"
    return f"{', '.join(dependencies[:-1])}, and {dependencies[-1]}"


def markdown_bullets(value: str) -> list[str]:
    bullets = []
    current = ""
    for line in value.splitlines():
        if line.startswith("- "):
            if current:
                bullets.append(current)
            current = line[2:]
        elif line.startswith("  ") and current:
            current += " " + line.strip()
    if current:
        bullets.append(current)
    return bullets


def render_readme_status(roadmap: dict) -> str:
    """Render the README projection of canonical roadmap status."""
    milestones = roadmap["milestones"]
    milestone_counts = Counter(item["status"] for item in milestones)
    current = next(item for item in milestones if item["id"] == roadmap["current_milestone"])
    subsystems = roadmap["subsystems"]
    release_ready = sum(
        item["maturity"]["release_ready"] == "complete" for item in subsystems
    )
    publication = roadmap["publication"]
    platform_gate = roadmap["platform_gate"]
    if platform_gate["platform_work_authorized"]:
        program_intro = (
            "The platform-neutral YWE specification has passed its M10 acceptance gate. Platform",
            "product work is authorized under the recorded post-specification program.",
        )
    else:
        program_intro = (
            "YWE is under active development as a platform-neutral specification. Platform",
            "products remain deferred until the M10 specification gate is accepted.",
        )
    platform_summary = (
        f"🟢 `authorized`; `{platform_gate['authorized_after']}` acceptance recorded"
        if platform_gate["platform_work_authorized"]
        else f"⏸️ `{platform_gate['status']}`; authorization requires "
        f"`{platform_gate['authorized_after']}` acceptance"
    )

    lines = [
        "## Specification Roadmap",
        "",
        *program_intro,
        "",
        "[View the detailed specification roadmap]"
        "(docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md) · "
        "[View machine-readable roadmap status]"
        "(data/governance/specification_roadmap.json)",
        "",
        "### Current status",
        "",
        "| Indicator | Current state |",
        "|---|---|",
        f"| Repository baseline | `v{roadmap['repository_baseline']}` |",
        f"| Current milestone | {STATUS_INDICATORS[current['status']]} `{current['id']}` — "
        f"{current['title']} (`{current['status']}`) |",
        f"| Accepted milestone gates | `{milestone_counts['complete']} of {len(milestones)}` |",
        f"| Milestone queue | `{milestone_counts['in_progress']}` in progress; "
        f"`{milestone_counts['planned']}` planned; `{milestone_counts['blocked']}` blocked; "
        f"`{milestone_counts['deferred']}` deferred |",
        f"| Release-ready subsystems | `{release_ready} of {len(subsystems)}` |",
        f"| Specification publication | `{publication['state']}`; "
        f"`{publication['github_release_objects']}` GitHub Release objects; "
        f"`{publication['agnostic_specification_releases']}` agnostic specification releases "
        f"(verified `{publication['verified_on']}`) |",
        f"| Platform product work | {platform_summary} |",
        "",
        "Milestone indicators: 🟢 `complete` · 🟡 `in_progress` · ⚪ `planned` · "
        "🔴 `blocked` · ⏸️ `deferred`.",
        "",
        "| Milestone | Indicator | Status | Dependencies | Objective |",
        "|---|:---:|---|---|---|",
    ]
    for milestone in milestones:
        dependencies = ", ".join(milestone["dependencies"]) or "None"
        lines.append(
            f"| {milestone['id']} | {STATUS_INDICATORS[milestone['status']]} | "
            f"`{milestone['status']}` | {dependencies} | {milestone['title']} |"
        )

    maturity_labels = {
        "phase_gate_accepted": "Historical phase gate",
        "normative_artifact_complete": "Normative artifact",
        "executable_schema_complete": "Executable schema",
        "conformance_tested": "Conformance tested",
        "release_ready": "Release readiness",
    }
    maturity_statuses = [
        "complete",
        "partial",
        "not_started",
        "not_applicable",
        "deferred",
        "not_ready",
    ]
    lines.extend(
        [
            "",
            "### Subsystem maturity snapshot",
            "",
            "| Dimension | Complete | Partial | Not started | Not applicable | Deferred | Not ready |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for dimension in roadmap["maturity_dimensions"]:
        counts = Counter(item["maturity"][dimension] for item in subsystems)
        values = " | ".join(str(counts[status]) for status in maturity_statuses)
        lines.append(f"| {maturity_labels[dimension]} | {values} |")

    lines.extend(
        [
            "",
            "These five maturity dimensions are independent. Accepted gates and maturity",
            "counts are not an estimated completion percentage: milestones differ in scope",
            "and effort, and historical foundations do not pass a new gate without its",
            "required acceptance evidence.",
            "",
            "See the roadmap inventories of "
            "[completed or verified foundations]"
            "(docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md#completed-or-verified-foundations), "
            "[material work remaining]"
            "(docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md#material-work-remaining), "
            "and the "
            "[15-subsystem maturity matrix]"
            "(docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md#subsystem-maturity-matrix).",
        ]
    )
    return "\n".join(lines)


def readme_status_errors(text: str, roadmap: dict) -> list[str]:
    """Reject a missing, duplicated, or stale README roadmap projection."""
    if text.count(README_STATUS_START) != 1 or text.count(README_STATUS_END) != 1:
        return ["README roadmap status markers must each appear exactly once"]
    start_index = text.index(README_STATUS_START)
    end_index = text.index(README_STATUS_END)
    if end_index < start_index:
        return ["README roadmap status markers are out of order"]
    actual = text[start_index + len(README_STATUS_START) : end_index].strip()
    expected = render_readme_status(roadmap)
    if actual != expected:
        return [
            "README roadmap status block is not synchronized with "
            "data/governance/specification_roadmap.json"
        ]
    return []


def document_errors(text: str, milestones: list[dict]) -> list[str]:
    errors = []
    for milestone in milestones:
        milestone_id = milestone["id"]
        heading = f"## {milestone_id} — {milestone['title']}"
        if heading not in text:
            errors.append(f"Roadmap document is missing exact heading {heading!r}")
            continue
        section_match = re.search(
            rf"(?ms)^## {re.escape(milestone_id)} — .*?(?=^## M(?:[0-9]|10) —|^## Dependency order)",
            text,
        )
        if not section_match:
            errors.append(f"Roadmap document section cannot be read for {milestone_id}")
            continue
        section = section_match.group(0)
        if f"Status: `{milestone['status']}`" not in section:
            errors.append(f"Roadmap document status is not synchronized for {milestone_id}")
        expected_dependencies = dependency_text(milestone["dependencies"])
        if f"Dependencies: {expected_dependencies}" not in section:
            errors.append(f"Roadmap document dependencies are not synchronized for {milestone_id}")
        effort = milestone["effort_weeks"]
        expected_effort = f"Indicative effort: {effort['minimum']}–{effort['maximum']} weeks"
        if expected_effort not in section:
            errors.append(f"Roadmap document effort is not synchronized for {milestone_id}")
        if f"Owner role: {milestone['owner_role']}" not in section:
            errors.append(f"Roadmap document owner role is not synchronized for {milestone_id}")
        deliverables_match = re.search(
            r"(?ms)^Deliverables:\n\n(.*?)(?=\nExit criteria:)", section
        )
        exit_match = re.search(r"(?ms)^Exit criteria:\n\n(.*)$", section)
        if not deliverables_match or markdown_bullets(deliverables_match.group(1)) != milestone["deliverables"]:
            errors.append(f"Roadmap document deliverables are not synchronized for {milestone_id}")
        if not exit_match or markdown_bullets(exit_match.group(1)) != milestone["exit_criteria"]:
            errors.append(f"Roadmap document exit criteria are not synchronized for {milestone_id}")
        indicator = STATUS_INDICATORS[milestone["status"]]
        dashboard_pattern = (
            rf"(?m)^\| {re.escape(milestone_id)} \| {re.escape(indicator)} \| "
            rf"`{re.escape(milestone['status'])}` \|"
        )
        if not re.search(dashboard_pattern, text):
            errors.append(f"Roadmap dashboard status is not synchronized for {milestone_id}")
    minimum_effort = sum(item["effort_weeks"]["minimum"] for item in milestones)
    maximum_effort = sum(item["effort_weeks"]["maximum"] for item in milestones)
    if f"serial sum of milestone estimates is {minimum_effort}–{maximum_effort} work weeks" not in text:
        errors.append("Roadmap document total effort is not synchronized")
    return errors


def status_source_errors(root: Path, roadmap: dict) -> list[str]:
    errors = []
    for source in roadmap.get("status_sources", []):
        path = root / source["path"]
        if not path.is_file():
            errors.append(f"Missing declared status source: {source['path']}")
            continue
        text = path.read_text(encoding="utf-8-sig")
        for marker in source["required_markers"]:
            if marker not in text:
                errors.append(f"{source['path']} is missing synchronized status marker {marker!r}")
    return errors


def subsystem_errors(root: Path, roadmap: dict, document_text: str | None = None) -> list[str]:
    errors = []
    subsystems = roadmap.get("subsystems", [])
    subsystem_ids = [item["id"] for item in subsystems]
    if len(subsystem_ids) != len(set(subsystem_ids)):
        errors.append("Subsystem maturity identifiers must be unique")
    milestone_ids = {item["id"] for item in roadmap["milestones"]}
    dimension_names = roadmap["maturity_dimensions"]
    for subsystem in subsystems:
        subsystem_id = subsystem["id"]
        if subsystem["next_milestone"] not in milestone_ids:
            errors.append(f"Subsystem {subsystem_id} references an unknown next milestone")
        if list(subsystem["maturity"]) != dimension_names:
            errors.append(f"Subsystem {subsystem_id} maturity dimensions are incomplete or out of order")
        maturity = subsystem["maturity"]
        if maturity["release_ready"] == "complete":
            prerequisites = (
                maturity["normative_artifact_complete"],
                maturity["executable_schema_complete"],
                maturity["conformance_tested"],
            )
            if any(value != "complete" for value in prerequisites):
                errors.append(f"Subsystem {subsystem_id} is release-ready without complete prerequisites")
            if subsystem["open_work"]:
                errors.append(f"Release-ready subsystem {subsystem_id} still records open work")
        elif not subsystem["open_work"]:
            errors.append(f"Incomplete subsystem {subsystem_id} must record open work")
        for evidence_ref in subsystem["evidence_refs"]:
            if not (root / evidence_ref).is_file():
                errors.append(f"Subsystem {subsystem_id} evidence does not exist: {evidence_ref}")
        if document_text is not None:
            values = [f"`{maturity[name]}`" for name in dimension_names]
            row = (
                f"| {subsystem['name']} | {' | '.join(values)} | "
                f"{subsystem['next_milestone']} |"
            )
            if row not in document_text:
                errors.append(f"Roadmap subsystem matrix is not synchronized for {subsystem_id}")
    return errors


def version_errors(root: Path, roadmap: dict) -> list[str]:
    errors = []
    canonical_path = root / "version.txt"
    try:
        version = canonical_path.read_text(encoding="utf-8-sig").strip()
    except OSError as exc:
        return [f"Unable to read canonical version source: {exc}"]
    if roadmap.get("repository_baseline") != version:
        errors.append(
            f"Roadmap repository_baseline {roadmap.get('repository_baseline')!r} does not match version.txt {version!r}"
        )

    for source in roadmap.get("version_sources", []):
        path = root / source["path"]
        if not path.is_file():
            errors.append(f"Missing declared version source: {source['path']}")
            continue
        try:
            if source["kind"] == "plain":
                actual = path.read_text(encoding="utf-8-sig").strip()
                if actual != version:
                    errors.append(f"{source['path']} contains {actual!r}; expected {version!r}")
            elif source["kind"] == "json_field":
                actual = dotted_value(load_json(path), source["field"])
                if actual != version:
                    errors.append(
                        f"{source['path']} field {source['field']} contains {actual!r}; expected {version!r}"
                    )
            elif source["kind"] == "text_template":
                expected = source["template"].format(version=version)
                if expected not in path.read_text(encoding="utf-8-sig"):
                    errors.append(f"{source['path']} is missing version marker {expected!r}")
        except (OSError, KeyError, json.JSONDecodeError) as exc:
            errors.append(f"Unable to validate version source {source['path']}: {exc}")
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.is_file():
        errors.append("CHANGELOG.md is missing")
    else:
        heading = rf"(?m)^## \[{re.escape(version)}\]\s+(?:-|—)\s+\d{{4}}-\d{{2}}-\d{{2}}\s*$"
        if not re.search(heading, changelog_path.read_text(encoding="utf-8-sig")):
            errors.append(f"CHANGELOG.md has no baseline heading for {version}")
    return errors


def publication_workflow_errors(root: Path, before_specification_release: bool) -> list[str]:
    if not before_specification_release:
        return []
    patterns = {
        "command-line publication": r"\bgh\s+release\s+create\b",
        "legacy publication action": r"\bactions/create-release@",
        "publication action": r"\bsoftprops/action-gh-release@|\bncipollo/release-action@",
        "release API write": r"\b(?:curl|wget)\b[^\n]*?/releases\b",
    }
    errors = []
    workflow_root = root / ".github/workflows"
    for path in sorted([*workflow_root.glob("*.yml"), *workflow_root.glob("*.yaml")]):
        text = path.read_text(encoding="utf-8-sig")
        for label, pattern in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                errors.append(f"{path.relative_to(root)} contains prohibited pre-M10 {label}")
    return errors


def main() -> int:
    arguments = sys.argv[1:]
    print_readme_status = bool(arguments and arguments[0] == "--print-readme-status")
    if print_readme_status:
        arguments = arguments[1:]
    if len(arguments) > 1:
        print(
            "Usage: check_specification_roadmap.py "
            "[--print-readme-status] [repository-root]"
        )
        return 2
    root = Path(arguments[0] if arguments else ".").resolve()
    if print_readme_status:
        try:
            roadmap = load_json(root / ROADMAP_PATH)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Unable to render README roadmap status: {exc}")
            return 1
        print(README_STATUS_START)
        print(render_readme_status(roadmap))
        print(README_STATUS_END)
        return 0

    errors: list[str] = []
    try:
        roadmap = load_json(root / ROADMAP_PATH)
        roadmap_schema = load_json(root / ROADMAP_SCHEMA_PATH)
        checks = load_json(root / CHECKS_PATH)
        checks_schema = load_json(root / CHECKS_SCHEMA_PATH)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Roadmap governance check failed: {exc}")
        return 1

    errors.extend(schema_errors(roadmap, roadmap_schema, ROADMAP_PATH))
    errors.extend(schema_errors(checks, checks_schema, CHECKS_PATH))
    if errors:
        print("Roadmap governance check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    milestones = roadmap["milestones"]
    errors.extend(dependency_errors(milestones))
    by_id = {item["id"]: item for item in milestones}
    current = roadmap["current_milestone"]
    in_progress = [item["id"] for item in milestones if item["status"] == "in_progress"]
    program_complete = all(item["status"] == "complete" for item in milestones)
    if program_complete:
        if current != "M10" or in_progress:
            errors.append("A completed roadmap must end at M10 with no milestone in progress")
    else:
        if by_id[current]["status"] != "in_progress":
            errors.append(f"Current milestone {current} must have status in_progress")
        if in_progress != [current]:
            errors.append(f"Exactly the current milestone must be in_progress; found {in_progress}")
    errors.extend(milestone_completion_errors(root, milestones))

    gate = roadmap["platform_gate"]
    if by_id["M10"]["status"] == "complete":
        if not gate["platform_work_authorized"] or gate["status"] != "authorized":
            errors.append("Completing M10 requires explicit platform authorization")
    elif gate["platform_work_authorized"] or gate["status"] != "deferred":
        errors.append("Platform work must remain deferred until M10 is complete")

    publication = roadmap["publication"]
    if by_id["M10"]["status"] == "complete":
        if (
            publication["state"] != "published"
            or publication["published_releases"] < 1
            or publication["agnostic_specification_releases"] < 1
        ):
            errors.append("Completing M10 requires a recorded specification publication")
    elif (
        publication["state"] != "unreleased"
        or publication["published_releases"] != 0
        or publication["github_release_objects"] != 0
        or publication["agnostic_specification_releases"] != 0
    ):
        errors.append("Before M10 completion the repository must record zero published releases")
    errors.extend(publication_workflow_errors(root, by_id["M10"]["status"] != "complete"))
    version_workflow = root / ".github/workflows/versioning.yml"
    if not version_workflow.is_file():
        errors.append("Version baseline workflow is missing")
    else:
        version_workflow_text = version_workflow.read_text(encoding="utf-8-sig")
        if re.search(r"(?m)^\s*pull_request\s*:", version_workflow_text):
            errors.append("Version baseline changes must not run automatically after pull-request merges")
        if re.search(r"\bgit\s+tag\b", version_workflow_text):
            errors.append("Version baseline workflow must not create publication-like tags")

    errors.extend(version_errors(root, roadmap))
    errors.extend(status_source_errors(root, roadmap))

    readme_path = root / "README.md"
    if not readme_path.is_file():
        errors.append("README.md is missing")
    else:
        errors.extend(
            readme_status_errors(readme_path.read_text(encoding="utf-8-sig"), roadmap)
        )

    check_ids = [item["id"] for item in checks["checks"]]
    errors.extend(catalog_contract_errors(checks))
    milestone_ids = set(by_id)
    for check in checks["checks"]:
        unknown = sorted(set(check["roadmap_milestones"]) - milestone_ids)
        if unknown:
            errors.append(f"Check {check['id']} references unknown milestones {unknown}")

    attribution_script = "scripts/check_repository_attribution_policy.py"
    attribution_checks = [
        item for item in checks["checks"] if item["id"] == "repository_attribution_policy"
    ]
    if not (root / attribution_script).is_file():
        errors.append("Repository attribution guard is missing")
    elif not attribution_checks or attribution_script not in attribution_checks[0]["command"]:
        errors.append("Repository attribution guard is not registered with its canonical command")

    contributor_workflow = root / ".github/workflows/contributor-identity-policy.yml"
    contributor_script = "scripts/github/Test-ContributorIdentityPolicy.ps1"
    if not contributor_workflow.is_file():
        errors.append("Contributor identity workflow is missing")
    elif contributor_script not in contributor_workflow.read_text(encoding="utf-8-sig"):
        errors.append("Contributor identity workflow no longer invokes its guard")
    if not (root / contributor_script).is_file():
        errors.append("Contributor identity guard is missing")

    roadmap_document = root / ROADMAP_DOCUMENT_PATH
    roadmap_text = None
    if not roadmap_document.is_file():
        errors.append(f"Roadmap document is missing: {ROADMAP_DOCUMENT_PATH}")
    else:
        roadmap_text = roadmap_document.read_text(encoding="utf-8-sig")
        errors.extend(document_errors(roadmap_text, milestones))
    errors.extend(subsystem_errors(root, roadmap, roadmap_text))

    if by_id["M10"]["status"] == "complete":
        incomplete_subsystems = [
            item["id"]
            for item in roadmap["subsystems"]
            if item["maturity"]["release_ready"] != "complete"
        ]
        if incomplete_subsystems:
            errors.append(f"M10 cannot complete before every subsystem is release-ready: {incomplete_subsystems}")

    if by_id["M2"]["status"] == "complete":
        debt = load_json(root / DEBT_PATH).get("known_debt", {})
        remaining = {key: value for key, value in debt.items() if value}
        if remaining:
            errors.append(f"M2 cannot be complete while schema quality debt remains: {sorted(remaining)}")
        if not (root / "data/validation/fixture_catalog.json").is_file():
            errors.append("M2 completion requires data/validation/fixture_catalog.json")

    if errors:
        print("Roadmap governance check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    publication_summary = (
        "no published releases"
        if publication["published_releases"] == 0
        else f"{publication['published_releases']} published release(s)"
    )
    print(
        f"Roadmap governance check passed (current {current}; {len(milestones)} milestones; "
        f"{len(check_ids)} registered checks; baseline {roadmap['repository_baseline']}; "
        f"{publication_summary})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
