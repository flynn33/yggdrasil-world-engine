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
    "docs/project/repository_map.md",
    "docs/project/repository_map.md",
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


def test_all_engine_interfaces_carry_ash_math_contract(root: Path, sink: FailureSink) -> None:
    interface_paths = sorted(
        {
            *root.glob("core/*/engine_interface.json"),
            *root.glob("modules/*/engine_interface.json"),
            *root.glob("modules/*/*_engine_interface.json"),
            root / "core" / "narrative_engine" / "character_creation_progression_interface.json",
        }
    )
    required_markers = [
        "ash_alignment_contract",
        "F2^9",
        "CosmicPatternSnapshot",
        "DiagnosticEnvelope",
        "GenerationPlan",
    ]
    required_core_fields = ["engine_id", "purpose", "layer", "methods"]
    required_module_fields = [*required_core_fields, "dependencies"]
    sink.require(bool(interface_paths), "No engine interface files found for ASH math contract coverage")
    for path in interface_paths:
        text = read_text(path)
        for marker in required_markers:
            sink.require(marker in text, f"Engine interface missing {marker!r}: {rel(path, root)}")
        try:
            data = load_json(path)
        except Exception as exc:
            sink.require(False, f"Engine interface JSON failed to load: {rel(path, root)}: {exc}")
            continue
        required_fields = required_module_fields if rel(path, root).startswith("modules/") else required_core_fields
        for field in required_fields:
            sink.require(field in data, f"Engine interface missing required field {field!r}: {rel(path, root)}")
        if rel(path, root).startswith("modules/"):
            sink.require(data.get("layer") == "module", f"Module engine interface must have layer 'module': {rel(path, root)}")
            deps = data.get("dependencies", [])
            dep_names = [dep.split(".")[-1] if isinstance(dep, str) and "." in dep else dep for dep in deps]
            sink.require("ash_pattern_engine" in dep_names, f"Module engine interface must depend on ash_pattern_engine: {rel(path, root)}")
        elif path.name == "engine_interface.json":
            sink.require(data.get("layer") == "core", f"Core engine interface must have layer 'core': {rel(path, root)}")


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


def test_ash_upstream_authority_contract_integrated(root: Path, sink: FailureSink) -> None:
    contract_path = "docs/architecture/ash_upstream_authority_contract.md"
    require_markers(
        root,
        sink,
        [contract_path],
        [
            "ASH is the upstream mathematical and generative authority",
            "ASH Pattern System",
            "Yggdrasil World Engine",
            "YWEGenerationContextPacket",
            "ASHUpstreamGenerationEnvelope",
            "YWEInterpretationPacket",
            "FutureGenerationBiasUpdate",
            "Host adapters may materialize approved manifests",
        ],
    )
    required_references = {
        "docs/architecture/ash_downstream_contract.md": [
            "ash_upstream_authority_contract.md",
            "subordinate",
            "upstream mathematical and generative authority",
        ],
        "docs/master_specification/YWE_MASTER_SPECIFICATION.md": [
            "ASH Upstream Authority",
            "generative authority",
            "YWE consumes ASH-derived",
        ],
        "docs/architecture/ywe_module_design_contracts.md": [
            "ASH Upstream Authority Rule",
            "shared packet spine",
        ],
        "docs/architecture/ywe_cross_module_dependency_map.md": [
            "ASH Pattern System",
            "host adapters",
        ],
        "docs/architecture/ywe_invariant_guardrails.md": [
            "No YWE system may redefine ASH math",
            "Player actions influence generation context",
        ],
        "docs/architecture/README.md": [
            "ash_upstream_authority_contract.md",
            "ASH defines upstream mathematical and generative authority",
        ],
    }
    for path_name, markers in required_references.items():
        require_markers(root, sink, [path_name], markers)


def test_runtime_generation_flow_has_upstream_spine(root: Path, sink: FailureSink) -> None:
    path_name = "core/narrative_engine/ash_runtime_generation_flow.yaml"
    require_markers(
        root,
        sink,
        [path_name],
        [
            "status: active_contract",
            "YWEGenerationContextPacket",
            "ASHUpstreamGenerationEnvelope",
            "YWEInterpretationPacket",
            "SystemManifestExchange",
            "HostAdapterMaterializationRequest",
            "MaterializationResult",
            "ResolutionPayload",
            "WorldstateDeltaPacket",
            "DiagnosticNoOp",
            "FutureGenerationBiasUpdate",
            "exploration_driven_world_generation",
            "player_action_driven_quest_generation",
            "player_action_driven_npc_generation",
            "consequence_driven_future_generation_bias",
        ],
    )
    text = read_text(root / path_name)
    sink.require(
        "placeholder_awaiting_finalized_content" not in text,
        "Runtime generation flow must not remain placeholder-only",
    )
    materialization_index = text.find("HostAdapterMaterializationRequest")
    plan_index = text.find("GenerationPlan")
    sink.require(
        plan_index != -1 and materialization_index != -1 and plan_index < materialization_index,
        "Runtime generation flow must require planning before host materialization",
    )


def test_upstream_packet_spine_records_exist(root: Path, sink: FailureSink) -> None:
    required_schema_files = [
        "data/schemas/ash_upstream_generation_envelope_schema.json",
        "data/schemas/ywe_generation_context_packet_schema.json",
        "data/schemas/ywe_interpretation_packet_schema.json",
        "data/schemas/player_action_trace_schema.json",
        "data/schemas/exploration_frontier_request_schema.json",
        "data/schemas/future_generation_bias_update_schema.json",
    ]
    require_paths(root, sink, required_schema_files)
    packet_schema = load_json(root / "data" / "schemas" / "ash_generation_packet_schema.json")
    records = packet_schema.get("records", {})
    for record_name in (
        "ASHUpstreamGenerationEnvelope",
        "YWEGenerationContextPacket",
        "YWEInterpretationPacket",
        "PlayerActionTrace",
        "ExplorationFrontierRequest",
        "FutureGenerationBiasUpdate",
        "SystemManifestExchange",
    ):
        sink.require(record_name in records, f"Missing upstream packet record: {record_name}")
    spine = packet_schema.get("shared_generation_spine", [])
    for step in (
        "RuntimeGenerationTrigger",
        "YWEGenerationContextPacket",
        "ASHUpstreamGenerationEnvelope",
        "YWEInterpretationPacket",
        "SystemManifestExchange",
        "HostAdapterMaterializationRequest",
        "MaterializationResult",
        "ResolutionPayload",
        "WorldstateDeltaPacket|DiagnosticNoOp",
        "FutureGenerationBiasUpdate",
    ):
        sink.require(step in spine, f"Shared generation spine missing step: {step}")


def test_generation_gate_requires_upstream_authority(root: Path, sink: FailureSink) -> None:
    contract = load_contract(root)
    upstream_gate_path = root / "data" / "validation" / "ash_upstream_authority_gate_contract.json"
    sink.require(upstream_gate_path.is_file(), "Missing upstream authority gate contract")
    upstream_gate = load_json(upstream_gate_path)

    for marker in (
        "ASHUpstreamGenerationEnvelope",
        "YWEGenerationContextPacket",
        "YWEInterpretationPacket",
        "PlayerActionTrace",
        "ExplorationFrontierRequest",
        "FutureGenerationBiasUpdate",
    ):
        sink.require(marker in contract.get("shared_required_markers", []), f"Generation gate missing marker: {marker}")

    for field in (
        "source_ash_refs",
        "diagnostic_ref",
        "generation_plan_ref",
        "requested_manifest_kind",
        "worldstate_delta_policy",
    ):
        sink.require(field in contract.get("required_provenance_fields", []), f"Generation gate missing provenance field: {field}")
        sink.require(field in upstream_gate.get("required_provenance_fields", []), f"Upstream gate missing provenance field: {field}")

    for rejection in (
        "local_symbolic_rng_as_source_of_meaning",
        "ywe_defined_ash_state_space",
        "ywe_defined_codeword_set",
        "materialization_before_generation_plan",
        "adapter_authored_truth",
        "feature_engine_claims_math_authority",
        "player_action_mutates_ash_math",
    ):
        sink.require(rejection in contract.get("reject_if", []), f"Generation gate missing rejection: {rejection}")
        sink.require(rejection in upstream_gate.get("reject_if", []), f"Upstream gate missing rejection: {rejection}")


def test_forbidden_upstream_authority_drift_absent(root: Path, sink: FailureSink) -> None:
    forbidden = [
        "The root engine defines cosmology and procedural truth",
        "YWE owns ASH math",
        "YWE defines ASH math",
        "YWE mutates ASH math",
        "YWE replaces ASH math",
        "YWE core math",
        "local ASH math",
        "local ASH codeword set",
        "adapter authored truth",
        "materialization before generation planning",
    ]
    allowed_context_paths = {
        "docs/architecture/ash_upstream_authority_contract.md",
        "docs/architecture/ywe_invariant_guardrails.md",
    }
    hits = []
    for path in scan_text_files(root):
        rp = rel(path, root)
        text = read_text(path)
        if rp in allowed_context_paths:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for phrase in forbidden:
                if phrase in line:
                    hits.append(f"{rp}:{line_no}: {line.strip()}")
                    break
    sink.require(not hits, "Forbidden upstream authority drift found: " + "; ".join(hits[:10]))


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
    test_all_engine_interfaces_carry_ash_math_contract,
    test_character_creation_requires_ash_provenance,
    test_creature_creation_requires_ash_provenance,
    test_quest_generation_requires_multiple_interpretations_and_delta_route,
    test_myth_is_retrospective_not_world_truth_rewrite,
    test_prophecy_is_attractor_not_script,
    test_perception_overlay_does_not_rewrite_shared_world_truth,
    test_adapters_cannot_author_ywe_truth,
    test_ash_upstream_authority_contract_integrated,
    test_runtime_generation_flow_has_upstream_spine,
    test_upstream_packet_spine_records_exist,
    test_generation_gate_requires_upstream_authority,
    test_forbidden_upstream_authority_drift_absent,
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
