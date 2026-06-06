#!/usr/bin/env python3
"""Validate Phase 16 and Phase 17 recovery prerequisites."""

from __future__ import annotations

import fnmatch
import json
import subprocess
import sys
from pathlib import Path

TEXT_ENCODING = "utf-8-sig"

REQUIRED_PATHS = ("reveal", "conceal", "bind", "study", "weaponize")

PHASE_16_DOCS = [
    "docs/architecture/vertical_slice_design_contract.md",
    "docs/architecture/ravenfall_gate_vertical_slice_integration_map.md",
    "docs/architecture/vertical_slice_playtest_trace_contract.md",
    "docs/game/vertical_slices/ravenfall_gate/00_ravenfall_gate_vertical_slice_overview.md",
    "docs/game/vertical_slices/ravenfall_gate/01_ravenfall_gate_location_brief.md",
    "docs/game/vertical_slices/ravenfall_gate/02_the_buried_oath_quest_design.md",
    "docs/game/vertical_slices/ravenfall_gate/03_branch_outcome_matrix.md",
    "docs/game/vertical_slices/ravenfall_gate/04_location_mutation_plan.md",
    "docs/game/vertical_slices/ravenfall_gate/05_wolf_companion_scene_plan.md",
    "docs/game/vertical_slices/ravenfall_gate/06_ability_use_plan.md",
    "docs/game/vertical_slices/ravenfall_gate/07_combat_encounter_plan.md",
    "docs/game/vertical_slices/ravenfall_gate/08_npc_and_faction_hooks.md",
    "docs/game/vertical_slices/ravenfall_gate/09_lore_and_myth_hooks.md",
    "docs/game/vertical_slices/ravenfall_gate/10_prophecy_and_future_bias_hooks.md",
    "docs/game/vertical_slices/ravenfall_gate/11_artifact_and_creature_eligibility.md",
    "docs/game/vertical_slices/ravenfall_gate/12_reward_resolution_plan.md",
    "docs/game/vertical_slices/ravenfall_gate/13_playtest_scenarios.md",
    "docs/game/vertical_slices/ravenfall_gate/14_vertical_slice_acceptance_matrix.md",
    "docs/game/vertical_slices/ravenfall_gate/15_phase_16_transition_notes.md",
]

PHASE_17_DOCS = [
    "docs/game/vertical_slices/ravenfall_gate/16_phase_17_acceptance_plan.md",
    "docs/game/vertical_slices/ravenfall_gate/17_playtest_trace_matrix.md",
    "docs/game/vertical_slices/ravenfall_gate/18_choice_path_validation.md",
    "docs/game/vertical_slices/ravenfall_gate/19_wolf_companion_validation.md",
    "docs/game/vertical_slices/ravenfall_gate/20_ability_and_combat_validation.md",
    "docs/game/vertical_slices/ravenfall_gate/21_worldstate_location_validation.md",
    "docs/game/vertical_slices/ravenfall_gate/22_npc_lore_myth_prophecy_validation.md",
    "docs/game/vertical_slices/ravenfall_gate/23_future_generation_bias_validation.md",
    "docs/game/vertical_slices/ravenfall_gate/24_phase_17_acceptance_report_requirements.md",
]

PHASE_16_EXAMPLES = [
    *(f"examples/vertical_slices/ravenfall_gate/branch_outcome_{path}.example.json" for path in REQUIRED_PATHS),
    *(f"examples/vertical_slices/ravenfall_gate/quest_reward_resolution_{path}.example.json" for path in REQUIRED_PATHS),
    *(f"examples/vertical_slices/ravenfall_gate/playtest_trace_{path}.example.json" for path in REQUIRED_PATHS),
    "examples/vertical_slices/ravenfall_gate/ravenfall_gate_vertical_slice_manifest.example.json",
    "examples/vertical_slices/ravenfall_gate/ravenfall_gate_location_brief.example.json",
    "examples/vertical_slices/ravenfall_gate/buried_oath_quest_design.example.json",
    "examples/vertical_slices/ravenfall_gate/wolf_scene_approach_gate.example.json",
    "examples/vertical_slices/ravenfall_gate/wolf_combat_assist_threshold_break.example.json",
    "examples/vertical_slices/ravenfall_gate/wolf_decoherence_not_death.example.json",
]

REQUIRED_CHECK_SPECS = [
    "data/validation/check_phase_sequence_no_skip.spec.json",
    "data/validation/check_required_phase_16_artifacts.spec.json",
    "data/validation/check_required_phase_16_vertical_slice_artifacts.spec.json",
    "data/validation/check_required_phase_17_artifacts.spec.json",
    "data/validation/check_phase18_unblock_prerequisites.spec.json",
    "data/validation/check_ravenfall_choice_path_coverage.spec.json",
    "data/validation/check_wolf_companion_trace_presence.spec.json",
    "data/validation/check_no_wolf_morality_language_phase_17.spec.json",
    "data/validation/check_no_permanent_wolf_death_phase_17.spec.json",
    "data/validation/check_no_platform_specific_runtime_phase_16_17.spec.json",
    "data/validation/check_non_destructive_diff_phase_16_17.spec.json",
    "data/validation/check_phase_16_17_non_destructive_diff.spec.json",
]

PHASE_17_EXAMPLE_DIR = "examples/ravenfall_gate/phase_17"
RECOVERY_EXAMPLE_DIR = "examples/phase_16_17_recovery"
WOLF_COMPANION_TRACE_SCHEMA = "data/schemas/wolf_companion_trace_schema.json"

ALLOWED_PLATFORM_CONTEXT = (
    "forbidden",
    "invalid",
    "reject",
    "rejected",
    "must not",
    "do not add",
    "no platform",
    "not implement",
    "does not implement",
    "deferred",
    "agnostic",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding=TEXT_ENCODING)


def load_json(path: Path):
    with path.open(encoding=TEXT_ENCODING) as handle:
        return json.load(handle)


def load_json_checked(root: Path, rel_path: str, errors: list[str]):
    path = root / rel_path
    if not path.is_file():
        errors.append(f"Missing required JSON file: {rel_path}")
        return None
    try:
        return load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {rel_path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        errors.append(f"Unable to read {rel_path}: {exc}")
    return None


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_file(root: Path, rel_path: str, errors: list[str]) -> None:
    require((root / rel_path).is_file(), f"Missing Phase 16/17 artifact: {rel_path}", errors)


def require_dir_with_json(root: Path, rel_path: str, errors: list[str]) -> None:
    directory = root / rel_path
    require(directory.is_dir(), f"Missing Phase 16/17 example directory: {rel_path}", errors)
    if directory.is_dir():
        require(any(directory.glob("*.json")), f"Phase 16/17 example directory has no JSON files: {rel_path}", errors)


def non_empty(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict, tuple, set)):
        return bool(value)
    return True


def schema_enum_values(root: Path, rel_path: str, property_name: str, errors: list[str]) -> set[str]:
    schema = load_json_checked(root, rel_path, errors)
    if not isinstance(schema, dict):
        return set()
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        errors.append(f"Schema has invalid properties object: {rel_path}")
        return set()
    property_schema = properties.get(property_name, {})
    if not isinstance(property_schema, dict):
        errors.append(f"Schema property is missing or invalid: {rel_path}#{property_name}")
        return set()
    values = property_schema.get("enum", [])
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        errors.append(f"Schema property enum is missing or invalid: {rel_path}#{property_name}")
        return set()
    return set(values)


def check_phase_16_artifacts(root: Path, errors: list[str]) -> None:
    required = load_json_checked(root, "data/validation/phase_16_required_artifacts.json", errors)
    if isinstance(required, dict):
        for rel_path in required.get("required_docs", []):
            require_file(root, rel_path, errors)
        for pattern in required.get("required_schema_patterns", []):
            require(
                any(root.glob(pattern)),
                f"Missing Phase 16 schema match for pattern: {pattern}",
                errors,
            )
        example_dir = required.get("required_example_directory")
        if isinstance(example_dir, str):
            require_dir_with_json(root, example_dir, errors)

    for rel_path in PHASE_16_DOCS + PHASE_16_EXAMPLES:
        require_file(root, rel_path, errors)


def phase_17_required_files(root: Path, errors: list[str]) -> list[str]:
    required = load_json_checked(root, "data/validation/phase_17_required_artifacts.json", errors)
    files: list[str] = []
    if isinstance(required, dict):
        for key in ("architecture_docs", "game_docs", "schemas", "validation_rules"):
            values = required.get(key, [])
            if isinstance(values, list):
                files.extend(value for value in values if isinstance(value, str))
    return files


def check_phase_17_artifacts(root: Path, errors: list[str]) -> None:
    for rel_path in PHASE_17_DOCS + phase_17_required_files(root, errors) + REQUIRED_CHECK_SPECS:
        require_file(root, rel_path, errors)
    require_dir_with_json(root, PHASE_17_EXAMPLE_DIR, errors)
    require_dir_with_json(root, RECOVERY_EXAMPLE_DIR, errors)


def check_phase_18_unblock_prerequisites(root: Path, errors: list[str]) -> None:
    spec = load_json_checked(root, "data/validation/check_phase18_unblock_prerequisites.spec.json", errors)
    if not isinstance(spec, dict):
        return
    for rel_path in spec.get("required_artifacts", []):
        if isinstance(rel_path, str):
            require_file(root, rel_path, errors)
    required_paths = spec.get("required_choice_paths", [])
    if isinstance(required_paths, list):
        require(set(required_paths) == set(REQUIRED_PATHS), "Phase 18 unblock path list does not match required Ravenfall paths.", errors)


def check_choice_path_coverage(root: Path, errors: list[str]) -> None:
    trace_dir = root / PHASE_17_EXAMPLE_DIR
    covered: set[str] = set()
    for path in sorted(trace_dir.glob("ravenfall_gate_playtest_trace_*_oath.example.json")):
        trace = load_json_checked(root, path.relative_to(root).as_posix(), errors)
        if isinstance(trace, dict):
            mode = trace.get("completion_mode")
            if isinstance(mode, str):
                covered.add(mode)
            require(trace.get("choice_to_consequence_trace_ref"), f"Missing choice trace ref in {path.name}", errors)
            require(trace.get("wolf_companion_trace_ref"), f"Missing wolf trace ref in {path.name}", errors)
            require(trace.get("acceptance_result_ref"), f"Missing acceptance result ref in {path.name}", errors)

    for mode in REQUIRED_PATHS:
        require(mode in covered, f"Missing Ravenfall Gate playtest trace for path: {mode}", errors)
        require_file(root, f"{PHASE_17_EXAMPLE_DIR}/choice_to_consequence_{mode}_oath.example.json", errors)
        require_file(root, f"{PHASE_17_EXAMPLE_DIR}/wolf_companion_trace_{mode}_oath.example.json", errors)
        require_file(root, f"{RECOVERY_EXAMPLE_DIR}/ravenfall_{mode}_playtest_trace_minimum.example.json", errors)

    batch = load_json_checked(root, f"{PHASE_17_EXAMPLE_DIR}/playtest_trace_batch_all_paths.example.json", errors)
    if isinstance(batch, dict):
        modes = set(batch.get("completion_modes_covered", []))
        missing = set(REQUIRED_PATHS) - modes
        require(not missing, f"Playtest trace batch is missing completion modes: {sorted(missing)}", errors)


def check_consequence_traceability(root: Path, errors: list[str]) -> None:
    for mode in REQUIRED_PATHS:
        rel_path = f"{PHASE_17_EXAMPLE_DIR}/choice_to_consequence_{mode}_oath.example.json"
        trace = load_json_checked(root, rel_path, errors)
        if not isinstance(trace, dict):
            continue

        choice = trace.get("choice", {})
        require(isinstance(choice, dict), f"Choice trace has invalid choice object: {rel_path}", errors)
        if isinstance(choice, dict):
            require(choice.get("completion_mode") == mode, f"Choice trace mode mismatch for {mode}: {rel_path}", errors)
            require(non_empty(choice.get("branch_event_ref")), f"Choice trace missing branch event ref for {mode}", errors)

        require(non_empty(trace.get("quest_reward_resolution_ref")), f"Choice trace missing reward resolution ref for {mode}", errors)
        require(non_empty(trace.get("consequence_resolution_refs")), f"Choice trace missing consequence refs for {mode}", errors)
        require(non_empty(trace.get("player_state_update_refs")), f"Choice trace missing player state update refs for {mode}", errors)
        require(
            non_empty(trace.get("worldstate_delta_refs")) or non_empty(trace.get("diagnostic_noop_refs")),
            f"Choice trace missing worldstate delta or diagnostic no-op for {mode}",
            errors,
        )
        require(
            non_empty(trace.get("location_mutation_refs")) or non_empty(trace.get("location_noop_reason")),
            f"Choice trace missing location mutation or no-op reason for {mode}",
            errors,
        )
        require(
            non_empty(trace.get("future_generation_bias_refs")) or non_empty(trace.get("future_generation_bias_noop_reason")),
            f"Choice trace missing future generation bias or no-op reason for {mode}",
            errors,
        )


def check_wolf_canon(root: Path, errors: list[str]) -> None:
    saw_quest_assist = False
    saw_combat_assist = False
    saw_vision_signal = False
    wolf_presence_values = schema_enum_values(root, WOLF_COMPANION_TRACE_SCHEMA, "white_wolf_presence", errors)
    dark_wolf_presence_values = schema_enum_values(root, WOLF_COMPANION_TRACE_SCHEMA, "dark_wolf_presence", errors)
    for mode in REQUIRED_PATHS:
        rel_path = f"{PHASE_17_EXAMPLE_DIR}/wolf_companion_trace_{mode}_oath.example.json"
        trace = load_json_checked(root, rel_path, errors)
        if not isinstance(trace, dict):
            continue

        white_presence = trace.get("white_wolf_presence")
        dark_presence = trace.get("dark_wolf_presence")
        require(white_presence in wolf_presence_values, f"Invalid White Wolf presence for {mode}: {white_presence}", errors)
        require(dark_presence in dark_wolf_presence_values, f"Invalid Dark Wolf presence for {mode}: {dark_presence}", errors)
        require(trace.get("permanent_death") is False, f"Wolf trace allows permanent death for {mode}", errors)
        require(trace.get("morality_model") is False, f"Wolf trace models wolves as morality for {mode}", errors)
        require(isinstance(trace.get("decoherence_events"), list), f"Wolf trace must record decoherence events as a list for {mode}", errors)

        modes = set(trace.get("assistance_modes", []))
        saw_quest_assist = saw_quest_assist or "quest_assist" in modes
        saw_combat_assist = saw_combat_assist or "combat_assist" in modes
        saw_vision_signal = saw_vision_signal or "vision_signal" in modes

    require(saw_quest_assist, "Phase 17 wolf traces never show quest assistance.", errors)
    require(saw_combat_assist, "Phase 17 wolf traces never show combat assistance.", errors)
    require(saw_vision_signal, "Phase 17 wolf traces never show vision/signal assistance.", errors)


def platform_line_allowed(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in ALLOWED_PLATFORM_CONTEXT)


def check_platform_boundary(root: Path, errors: list[str]) -> None:
    spec = load_json_checked(root, "data/validation/check_no_platform_specific_runtime_phase_16_17.spec.json", errors)
    if not isinstance(spec, dict):
        return
    forbidden = [(item, item.lower()) for item in spec.get("forbidden_patterns", []) if isinstance(item, str)]
    scan_files = {root / rel_path for rel_path in PHASE_16_DOCS + PHASE_17_DOCS}
    scan_files.update((root / "docs" / "architecture").glob("*vertical_slice*.md"))
    scan_files.update((root / "docs" / "architecture").glob("*ravenfall_gate*.md"))
    scan_files.update((root / "docs" / "architecture").glob("choice_to_consequence_traceability_contract.md"))
    scan_files.update((root / "docs" / "architecture").glob("phase_17_*.md"))
    scan_files.update((root / "docs" / "architecture").glob("playtest_trace_contract.md"))
    scan_files.update((root / "docs" / "architecture").glob("wolf_companion_playtest_validation_contract.md"))
    scan_files.update((root / "data" / "schemas").glob("*trace_schema.json"))
    scan_files.update((root / "data" / "schemas").glob("*ravenfall*_schema.json"))
    scan_files.update((root / "examples" / "vertical_slices" / "ravenfall_gate").glob("*.json"))
    scan_files.update((root / "examples" / "ravenfall_gate" / "phase_17").glob("*.json"))
    scan_files.update((root / "examples" / "phase_16_17_recovery").glob("*.json"))

    for path in sorted(scan_files):
        if not path.is_file() or path.suffix not in {".md", ".json"}:
            continue
        if path.suffix == ".json" and (path.name.startswith("invalid_") or ".reject." in path.name):
            continue
        rel_path = path.relative_to(root).as_posix()
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            lowered_line = line.lower()
            for term, lowered_term in forbidden:
                if lowered_term in lowered_line and not platform_line_allowed(line):
                    errors.append(f"Platform runtime term outside allowed context: {rel_path}:{line_number}: {term}")


def check_package_root_files_not_copied(root: Path, errors: list[str]) -> None:
    spec = load_json_checked(root, "data/validation/check_no_package_root_files_copied.spec.json", errors)
    if not isinstance(spec, dict):
        return
    globs = spec.get("reject_filename_globs", [])
    if not isinstance(globs, list):
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_path = path.relative_to(root).as_posix()
        for pattern in globs:
            if isinstance(pattern, str) and fnmatch.fnmatch(path.name, pattern):
                errors.append(f"Package-root instruction file must not be copied: {rel_path}")


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


def default_base_ref(root: Path) -> str:
    for ref in ("origin/main", "origin/master", "main", "master"):
        if git_ref_exists(root, ref):
            return ref
    return ""


def parse_name_status(line: str) -> tuple[str, str] | None:
    parts = line.split("\t")
    if len(parts) < 2:
        return None
    return parts[0], parts[-1]


def git_diff_name_status(root: Path, base_ref: str, errors: list[str]) -> list[tuple[str, str]]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-status", "--find-renames", f"{base_ref}..HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        errors.append(f"Unable to inspect Phase 16/17 recovery git diff: {exc}")
        return []
    if result.returncode != 0:
        errors.append(f"Unable to inspect Phase 16/17 recovery git diff against {base_ref}: {result.stderr.strip()}")
        return []
    paths: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        parsed = parse_name_status(line)
        if parsed is not None:
            paths.append(parsed)
    return paths


def check_non_destructive_diff(root: Path, errors: list[str]) -> None:
    base_ref = default_base_ref(root)
    if not base_ref:
        errors.append("Unable to resolve git base ref for Phase 16/17 recovery diff checks.")
        return
    for status, rel_path in git_diff_name_status(root, base_ref, errors):
        if status.startswith("D"):
            errors.append(f"Phase 16/17 recovery must not delete files: {rel_path}")
        if status.startswith("R"):
            errors.append(f"Phase 16/17 recovery must not rename files: {rel_path}")


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd().resolve()
    errors: list[str] = []

    check_phase_16_artifacts(root, errors)
    check_phase_17_artifacts(root, errors)
    check_phase_18_unblock_prerequisites(root, errors)
    check_choice_path_coverage(root, errors)
    check_consequence_traceability(root, errors)
    check_wolf_canon(root, errors)
    check_platform_boundary(root, errors)
    check_package_root_files_not_copied(root, errors)
    check_non_destructive_diff(root, errors)

    if errors:
        print("Phase 16/17 recovery check failed.")
        for error in errors:
            print(f"  FAIL: {error}")
        return 1

    print("Phase 16/17 recovery and Phase 18 unblock prerequisites check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
