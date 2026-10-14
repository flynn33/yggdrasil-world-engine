#!/usr/bin/env python3
"""Prevent platform product artifacts from entering the agnostic specification branch."""

from __future__ import annotations

import sys
from pathlib import Path

BLOCKED_ARTIFACT_SUFFIXES = {
    ".aar",
    ".apk",
    ".app",
    ".asmdef",
    ".asset",
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".csproj",
    ".css",
    ".cxx",
    ".dart",
    ".dll",
    ".dylib",
    ".exe",
    ".gd",
    ".godot",
    ".go",
    ".gradle",
    ".h",
    ".html",
    ".hpp",
    ".ipa",
    ".jar",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".lua",
    ".m",
    ".metal",
    ".mm",
    ".pbxproj",
    ".r",
    ".rs",
    ".sln",
    ".so",
    ".swift",
    ".tres",
    ".ts",
    ".tscn",
    ".tsx",
    ".uasset",
    ".umap",
    ".unity",
    ".uplugin",
    ".uproject",
    ".vue",
    ".wasm",
    ".xcworkspace",
    ".xcodeproj",
}

BLOCKED_ARTIFACT_NAMES = {
    "AndroidManifest.xml",
    "Cargo.toml",
    "DefaultEngine.ini",
    "DefaultGame.ini",
    "Info.plist",
    "Package.swift",
    "Podfile",
    "package.json",
    "project.godot",
}

TOOL_SOURCE_SUFFIXES = {".ps1", ".py", ".sh"}
APPROVED_REFERENCE_SOURCES = {
    "core/state_journal.py",
    "core/state_migration.py",
    "core/narrative_engine/origin_progression.py",
    "core/perception_engine/persistence.py",
    "core/ash_pattern_engine/__init__.py",
    "core/ash_pattern_engine/ash_canonical.py",
    "core/ash_pattern_engine/state_model.py",
    "core/ash_pattern_engine/state_values.py",
    "core/ash_pattern_engine/normalization.py",
    "core/ash_pattern_engine/normalization_values.py",
    "core/ash_pattern_engine/recovery.py",
    "core/ash_pattern_engine/recovery_values.py",
    "core/ash_pattern_engine/fallback_registry.py",
    "core/ash_pattern_engine/diagnostics.py",
    "core/ash_pattern_engine/diagnostics_values.py",
    "core/ash_pattern_engine/session.py",
    "core/ash_pattern_engine/session_values.py",
    "core/ash_pattern_engine/diagnostic_session_values.py",
    "core/ash_pattern_engine/realm_transition_values.py",
    "core/ash_pattern_engine/realm_transition.py",
    "core/ash_pattern_engine/generation_values.py",
    "core/ash_pattern_engine/topology.py",
    "core/ash_pattern_engine/axioms.py",
    "core/ash_pattern_engine/diagnostic_module_values.py",
    "core/ash_pattern_engine/diagnostic_module_capture.py",
    "core/core_values.py",
    "core/deterministic_policy.py",
    "core/module_lifecycle.py",
    "core/orchestration.py",
    "core/cosmology_engine/cosmology.py",
    "core/realm_engine/realm.py",
    "core/ash_pattern_engine/core_facade.py",
    "core/narrative_engine/narrative.py",
    "core/perception_engine/perception.py",
    "core/ash_pattern_engine/planner_emitter_values.py",
    "core/ash_pattern_engine/generation_planner.py",
    "core/ash_pattern_engine/artifact_emitter.py",
    "core/ash_pattern_engine/memory_document_target.py",
    "core/ash_pattern_engine/generation_runner.py",
    "docs/design-planning/m2/ash-values/verification/value_model.py",
    "docs/design-planning/m2/ash-values/verification/verify_contract.py",
    "docs/design-planning/m2/consumer-compatibility/verify_compatibility.py",
    "docs/design-planning/m2/readiness/probes/schema_readiness_probe.py",
    "docs/design-planning/m2/readiness/probes/verify_probe.py",
    "docs/design-planning/m3/session-lifecycle/derive_bounds.py",
    "docs/design-planning/m3/session-lifecycle/derive_command_reservations.py",
    "docs/design-planning/m3/session-lifecycle/generate_graph_control.py",
    "docs/design-planning/m3/session-lifecycle/raw_business_guard_controls.py",
    "docs/design-planning/m3/session-lifecycle/replay_independent.py",
}

CODE_PATTERNS = {
    ".cs": ("using UnityEngine",),
    ".cpp": ("#include \"Engine/", "UCLASS(", "GENERATED_BODY("),
    ".cc": ("#include \"Engine/", "UCLASS(", "GENERATED_BODY("),
    ".cxx": ("#include \"Engine/", "UCLASS(", "GENERATED_BODY("),
    ".h": ("#include \"Engine/", "UCLASS(", "GENERATED_BODY("),
    ".hpp": ("#include \"Engine/", "UCLASS(", "GENERATED_BODY("),
    ".gd": ("extends Node", "extends Node2D", "extends Node3D"),
    ".swift": ("import SwiftUI", "import Metal", "import SceneKit"),
    ".metal": ("#include <metal_stdlib>",),
}


def approved_tool_source(relative_path: Path) -> bool:
    value = relative_path.as_posix()
    return (
        value in APPROVED_REFERENCE_SOURCES
        or value.startswith("scripts/")
        or value.startswith("tests/")
        or value.startswith(".github/scripts/")
    )


def platform_violations(root: Path) -> tuple[list[str], int]:
    violations = []
    files_checked = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative_path = path.relative_to(root)
        suffix = path.suffix.lower()
        artifact_blocked = suffix in BLOCKED_ARTIFACT_SUFFIXES or path.name in BLOCKED_ARTIFACT_NAMES
        tool_source_outside_boundary = suffix in TOOL_SOURCE_SUFFIXES and not approved_tool_source(relative_path)
        if artifact_blocked:
            files_checked += 1
            violations.append(f"{relative_path.as_posix()}: platform product artifact is prohibited")
            continue
        if tool_source_outside_boundary:
            files_checked += 1
            violations.append(f"{relative_path.as_posix()}: executable source is outside approved validation or reference paths")
            continue
        patterns = CODE_PATTERNS.get(suffix)
        if not patterns:
            if suffix in TOOL_SOURCE_SUFFIXES:
                files_checked += 1
            continue
        files_checked += 1
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(pattern in line for pattern in patterns):
                violations.append(
                    f"{relative_path.as_posix()}:{line_number}: platform-specific code marker"
                )
    return violations, files_checked


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    violations, files_checked = platform_violations(root)

    if violations:
        print("Platform product boundary check failed:")
        for violation in violations:
            print(f"  - {violation}")
        return 1
    print(f"Platform product boundary check passed ({files_checked} executable or product files inspected).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
