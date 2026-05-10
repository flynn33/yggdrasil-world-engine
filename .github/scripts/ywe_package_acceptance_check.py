#!/usr/bin/env python3
"""YWE package acceptance checks for the ASH/ASP core-math rebuild."""

from __future__ import annotations

import importlib.util
import itertools
import json
import re
import subprocess
import sys
from pathlib import Path

TEXT_ENCODING = "utf-8-sig"

EXPECTED_CODEWORDS = (
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 1, 1, 1, 1, 0),
    (0, 0, 1, 1, 0, 0, 1, 1, 0),
    (0, 0, 1, 1, 1, 1, 0, 0, 0),
    (0, 1, 0, 1, 0, 1, 0, 1, 0),
    (0, 1, 0, 1, 1, 0, 1, 0, 0),
    (0, 1, 1, 0, 0, 1, 1, 0, 0),
    (0, 1, 1, 0, 1, 0, 0, 1, 0),
    (1, 0, 0, 1, 0, 1, 1, 0, 0),
    (1, 0, 0, 1, 1, 0, 0, 1, 0),
    (1, 0, 1, 0, 0, 1, 0, 1, 0),
    (1, 0, 1, 0, 1, 0, 1, 0, 0),
    (1, 1, 0, 0, 0, 0, 1, 1, 0),
    (1, 1, 0, 0, 1, 1, 0, 0, 0),
    (1, 1, 1, 1, 0, 0, 0, 0, 0),
    (1, 1, 1, 1, 1, 1, 1, 1, 0),
)

TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".txt"}
SCAN_ROOTS = (
    "specs/",
    "core/",
    "modules/",
    "data/",
    "docs/",
    "conformance/",
    "governance/",
)
SCAN_ROOT_FILES = {
    "README.md",
    "wiki.md",
    "SOURCE_AVAILABILITY_MANIFEST.md",
    "missing_source_documents.md",
    "YWE_REPOSITORY_BOOTSTRAP_PROMPT.md",
    "YWE_CODEX_GITHUB_BUILD_PACKAGE.md",
}
VALIDATOR_CONTEXTS = {
    ".github/scripts/semantic_integrity_check.py",
    ".github/scripts/ywe_package_acceptance_check.py",
}


class FailureSink:
    def __init__(self) -> None:
        self.failures: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.failures.append(message)


def read_text(path: Path) -> str:
    return path.read_text(encoding=TEXT_ENCODING)


def load_json(path: Path):
    with path.open(encoding=TEXT_ENCODING) as handle:
        return json.load(handle)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def git_active_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=str(root),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        names = [name for name in result.stdout.decode("utf-8").split("\0") if name]
        return [root / name for name in names]
    except (OSError, subprocess.CalledProcessError):
        return [
            path
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.parts
        ]


def scan_text_files(root: Path) -> list[Path]:
    files = []
    for path in git_active_files(root):
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rp = rel(path, root)
        if rp in VALIDATOR_CONTEXTS:
            continue
        if any(rp.startswith(prefix) for prefix in SCAN_ROOTS) or rp in SCAN_ROOT_FILES:
            files.append(path)
    return files


def find_pattern(root: Path, patterns: list[re.Pattern[str]]) -> list[str]:
    hits = []
    for path in scan_text_files(root):
        text = read_text(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pattern in patterns:
                if pattern.search(line):
                    hits.append(f"{rel(path, root)}:{line_no}: {line.strip()}")
                    break
    return hits


def import_ash(root: Path):
    module_path = root / "core" / "ash_pattern_engine" / "ash_canonical.py"
    spec = importlib.util.spec_from_file_location("ash_canonical", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to import ash_canonical.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def xor_bits(left, right):
    return tuple(a ^ b for a, b in zip(left, right))


def text_for_paths(root: Path, paths: list[str]) -> str:
    chunks = []
    for path_name in paths:
        path = root / path_name
        if path.is_file():
            chunks.append(read_text(path))
    return "\n".join(chunks)


def load_contract(root: Path):
    return load_json(root / "data" / "validation" / "ash_generation_gate_contract.json")


def require_paths(root: Path, sink: FailureSink, paths: list[str]) -> None:
    for path_name in paths:
        sink.require((root / path_name).is_file(), f"Missing required path: {path_name}")


def require_markers(root: Path, sink: FailureSink, paths: list[str], markers: list[str]) -> None:
    require_paths(root, sink, paths)
    combined = text_for_paths(root, paths)
    for marker in markers:
        sink.require(marker in combined, f"Missing marker {marker!r} in {paths}")


def test_rejects_8_plus_1_language(root: Path, sink: FailureSink) -> None:
    patterns = [
        re.compile(r"8\s*\+\s*1", re.IGNORECASE),
        re.compile(r"8-bit\s+core", re.IGNORECASE),
        re.compile(r"derived\s+ninth", re.IGNORECASE),
        re.compile(r"\[8\s*,\s*4\s*,\s*4\]"),
        re.compile(r"fallback candidates are.*8", re.IGNORECASE),
    ]
    hits = find_pattern(root, patterns)
    sink.require(not hits, "Stale 8+1 or [8,4,4] language found: " + "; ".join(hits[:10]))


def test_rejects_parity_control_bit_baseline(root: Path, sink: FailureSink) -> None:
    patterns = [
        re.compile(r"derived\s+parity", re.IGNORECASE),
        re.compile(r"parity-derived", re.IGNORECASE),
        re.compile(r"parity\s+formula", re.IGNORECASE),
        re.compile(r"derived\s+control\s+bit", re.IGNORECASE),
        re.compile(r"control\s+bit\s+baseline", re.IGNORECASE),
    ]
    hits = find_pattern(root, patterns)
    sink.require(not hits, "Parity/control-bit baseline language found: " + "; ".join(hits[:10]))


def test_codeword_set_exactly_16(root: Path, sink: FailureSink) -> None:
    ash = import_ash(root)
    codewords = tuple(tuple(c) for c in ash.CANONICAL_CODEWORDS)
    sink.require(getattr(ash, "ASH_STATE_BITS", None) == 9, "ASH_STATE_BITS must be 9")
    sink.require(codewords == EXPECTED_CODEWORDS, "Canonical codeword set must match the locked 16-member set exactly")
    sink.require(len(codewords) == 16, "Canonical codeword set must contain exactly 16 members")
    sink.require(len(set(codewords)) == 16, "Canonical codeword set must not contain duplicates")
    sink.require(all(len(codeword) == 9 for codeword in codewords), "Every codeword must be a full 9-bit vector")
    sink.require(all(bit in (0, 1) for codeword in codewords for bit in codeword), "Every codeword coordinate must be in F2")
    codeword_set = set(codewords)
    for left in codewords:
        for right in codewords:
            sink.require(xor_bits(left, right) in codeword_set, "Canonical codeword set must be closed under XOR")
    orbits = {ash.orbit_id(state) for state in itertools.product((0, 1), repeat=9)}
    sink.require(len(orbits) == 32, "F2^9 quotient by canonical codeword set must produce 32 orbits")


def test_transition_is_full_state_xor(root: Path, sink: FailureSink) -> None:
    ash = import_ash(root)
    state = (1, 0, 1, 0, 1, 0, 1, 0, 1)
    codeword = EXPECTED_CODEWORDS[5]
    expected = xor_bits(state, codeword)
    transformed = ash.transform_state(state, codeword)
    sink.require(tuple(transformed.bits) == expected, "transform_state must apply full 9-coordinate XOR")
    restored = ash.transform_state(transformed.bits, codeword)
    sink.require(tuple(restored.bits) == state, "Applying the same codeword twice must restore the source state")
    for bad_state, bad_codeword, message in (
        ((1, 0, 1), codeword, "non-9-bit state must be rejected"),
        (state, (1, 0, 0, 0, 0, 0, 0, 0, 1), "non-codeword transition must be rejected"),
    ):
        try:
            ash.transform_state(bad_state, bad_codeword)
        except ValueError:
            continue
        sink.require(False, message)


def test_all_generation_requires_cosmic_pattern_snapshot(root: Path, sink: FailureSink) -> None:
    contract = load_contract(root)
    for system in contract["systems"]:
        require_markers(root, sink, system["paths"], ["CosmicPatternSnapshot"])
    ash = import_ash(root)
    snapshot = ash.build_cosmic_pattern_snapshot("000000100", [EXPECTED_CODEWORDS[1]])
    for key in ("source_orbit_id", "active_codeword_sequence", "diagnostic_ref", "generation_plan_ref"):
        sink.require(key in snapshot, f"CosmicPatternSnapshot runtime output missing {key}")


def test_all_generation_requires_diagnostic_envelope(root: Path, sink: FailureSink) -> None:
    contract = load_contract(root)
    for system in contract["systems"]:
        require_markers(root, sink, system["paths"], ["DiagnosticEnvelope", "diagnostic_ref"])


def test_all_materialization_requires_generation_plan(root: Path, sink: FailureSink) -> None:
    contract = load_contract(root)
    for system in contract["systems"]:
        require_markers(root, sink, system["paths"], ["GenerationPlan"])
    for adapter_path in contract["adapter_paths"]:
        require_markers(
            root,
            sink,
            [adapter_path],
            ["GenerationPlan", "CosmicPatternSnapshot", "DiagnosticEnvelope", "must not author"],
        )
        text = read_text(root / adapter_path)
        sink.require("procedural generation" not in text.lower(), f"Adapter may not claim procedural generation authority: {adapter_path}")


def test_character_creation_requires_ash_provenance(root: Path, sink: FailureSink) -> None:
    require_markers(
        root,
        sink,
        [
            "core/narrative_engine/character_creation_progression_interface.json",
            "core/narrative_engine/character_creation_progression_rules.yaml",
            "data/schemas/character_progression_schema.json",
            "data/player_schema.json",
            "data/schemas/player_schema.json",
        ],
        [
            "CharacterSeedManifest",
            "IdentityPressureVector",
            "ProgressionDelta",
            "PlayerStateDelta",
            "cosmic_pattern_snapshot_ref",
            "diagnostic_ref",
            "generation_plan_ref",
        ],
    )


def test_creature_creation_requires_ash_provenance(root: Path, sink: FailureSink) -> None:
    require_markers(
        root,
        sink,
        [
            "modules/creature_engine/creature_engine_interface.json",
            "data/schemas/creature_manifest_schema.json",
        ],
        [
            "CreatureManifest",
            "EncounterPlan",
            "BehaviorPressureVector",
            "source_ash_refs",
            "diagnostic_ref",
            "generation_plan_ref",
        ],
    )


def test_quest_generation_requires_multiple_interpretations_and_delta_route(root: Path, sink: FailureSink) -> None:
    require_markers(
        root,
        sink,
        [
            "modules/quest_engine/quest_engine_interface.json",
            "data/quest_archetypes/quest_chain_manifest_schema.json",
        ],
        [
            "QuestChainManifest",
            "StageManifest",
            "CompletionModeSet",
            "QuestResolutionPayload",
            "WorldstateDeltaPacket",
            "minimum_mode_count",
        ],
    )


def test_myth_is_retrospective_not_world_truth_rewrite(root: Path, sink: FailureSink) -> None:
    require_markers(
        root,
        sink,
        [
            "modules/myth_engine/myth_engine_interface.json",
            "data/schemas/myth_record_schema_expansion.json",
        ],
        [
            "WorldstateDeltaPacket",
            "MythSeedCandidate",
            "MythRecord",
            "MythLine",
            "SocialDistributionDelta",
            "factual_world_truth_rewrite",
            "retrospective",
        ],
    )


def test_prophecy_is_attractor_not_script(root: Path, sink: FailureSink) -> None:
    require_markers(
        root,
        sink,
        [
            "modules/prophecy_engine/prophecy_engine_interface.json",
            "data/schemas/prophecy_schema_expansion.json",
        ],
        [
            "ProphecyRecord",
            "OmenCluster",
            "RuntimeBiasEffect",
            "attractor",
            "fixed_script",
            "deflection_routes",
            "transmutation_routes",
        ],
    )


def test_perception_overlay_does_not_rewrite_shared_world_truth(root: Path, sink: FailureSink) -> None:
    require_markers(
        root,
        sink,
        [
            "core/perception_engine/engine_interface.json",
            "core/perception_engine/perception_schema.json",
            "data/schemas/perception_layer_persistence_schema.json",
            "data/perception/perception_overlay_rules.yaml",
        ],
        [
            "PerceptionStateRecord",
            "OverlayManifest",
            "VisibilityRules",
            "truth_substrate_ref",
            "perception_overlay_does_not_rewrite_shared_world_truth",
            "geography_rewrite",
        ],
    )


def test_adapters_cannot_author_ywe_truth(root: Path, sink: FailureSink) -> None:
    contract = load_contract(root)
    for adapter_path in contract["adapter_paths"]:
        require_markers(
            root,
            sink,
            [adapter_path],
            [
                "GenerationPlan",
                "CosmicPatternSnapshot",
                "DiagnosticEnvelope",
                "must not author",
                "YWE domain truth",
            ],
        )


def check_governance_records(root: Path, sink: FailureSink) -> None:
    contract = load_contract(root)
    for _, path_name in contract["governance"].items():
        sink.require((root / path_name).is_file(), f"Missing governance/conformance record: {path_name}")
    if (root / "conformance" / "governance-boot-record.md").is_file():
        governance = read_text(root / "conformance" / "governance-boot-record.md")
        for marker in (
            "20 of 20",
            "architect",
            "sentinel",
            "planner",
            "reviewer",
            "debugger",
            "test-writer",
            "refactorer",
            "documenter",
            "performance-engineer",
            "security-auditor",
            "git-manager",
            "build-resolver",
            "coordinator",
            "multi-file-specialist",
        ):
            sink.require(marker in governance, f"Governance boot record missing marker: {marker}")


TESTS = [
    test_rejects_8_plus_1_language,
    test_rejects_parity_control_bit_baseline,
    test_codeword_set_exactly_16,
    test_transition_is_full_state_xor,
    test_all_generation_requires_cosmic_pattern_snapshot,
    test_all_generation_requires_diagnostic_envelope,
    test_all_materialization_requires_generation_plan,
    test_character_creation_requires_ash_provenance,
    test_creature_creation_requires_ash_provenance,
    test_quest_generation_requires_multiple_interpretations_and_delta_route,
    test_myth_is_retrospective_not_world_truth_rewrite,
    test_prophecy_is_attractor_not_script,
    test_perception_overlay_does_not_rewrite_shared_world_truth,
    test_adapters_cannot_author_ywe_truth,
]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    sink = FailureSink()

    print(f"YWE Package Acceptance Check at: {root}")
    check_governance_records(root, sink)
    for test in TESTS:
        before = len(sink.failures)
        try:
            test(root, sink)
        except Exception as exc:  # pragma: no cover - explicit CLI diagnostic path
            sink.failures.append(f"{test.__name__} raised {exc.__class__.__name__}: {exc}")
        if len(sink.failures) == before:
            print(f"  PASS: {test.__name__}")
        else:
            print(f"  FAIL: {test.__name__}")

    if sink.failures:
        print("\nPackage acceptance failure(s):")
        for failure in sink.failures:
            print(f"  - {failure}")
        return 1

    print("\nYWE package acceptance checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
