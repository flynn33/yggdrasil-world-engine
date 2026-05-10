"""Canonical ASH Pattern System surface for YWE.

This module is intentionally small and deterministic. It mirrors the ASH
canonical baseline in `specs/` and gives validation scripts a concrete runtime
surface for the locked 9-bit state space, fixed 16-codeword set, diagnostics,
and planner/emitter materialization boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

ASH_STATE_BITS = 9

CANONICAL_CODEWORDS: tuple[tuple[int, ...], ...] = (
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

YWE_REALM_STATE_ANCHORS: dict[str, tuple[int, ...]] = {
    "divine_core": (1, 0, 0, 0, 0, 0, 0, 0, 0),
    "celestial": (0, 1, 0, 0, 0, 0, 0, 0, 0),
    "causal": (0, 0, 1, 0, 0, 0, 0, 0, 0),
    "mental": (0, 0, 0, 1, 0, 0, 0, 0, 0),
    "astral": (0, 0, 0, 0, 1, 0, 0, 0, 0),
    "etheric": (0, 0, 0, 0, 0, 1, 0, 0, 0),
    "physical": (0, 0, 0, 0, 0, 0, 1, 0, 0),
    "shadow": (0, 0, 0, 0, 0, 0, 0, 1, 0),
    "void": (0, 0, 0, 0, 0, 0, 0, 0, 1),
}

SYSTEM_STATE_BY_ADMISSIBILITY = {
    "VALID": "STABLE",
    "TRANSFORMATION_COMPATIBLE": "CORRECTABLE",
    "TRANSFORMATION_INCOMPATIBLE": "CONTAINED",
    "UNCLASSIFIED": "SAFE_HALT",
}

RECOVERY_BY_SYSTEM_STATE = {
    "STABLE": "NO_ACTION",
    "UNSTABLE": "NORMALIZE_STATE",
    "CORRECTABLE": "APPLY_CORRECTION",
    "DEGRADED": "FALLBACK_REQUIRED",
    "CONTAINED": "CONTAINMENT_REQUIRED",
    "FAILED": "ESCALATION_REQUIRED",
    "SAFE_HALT": "TERMINAL_NO_RECOVERY",
}


@dataclass(frozen=True)
class AshState:
    bits: tuple[int, ...]

    @property
    def signature(self) -> str:
        return encode_state_signature(self.bits)


def normalize_bits(bits: Sequence[int] | str) -> tuple[int, ...]:
    if isinstance(bits, str):
        candidate = tuple(int(ch) for ch in bits.strip())
    else:
        candidate = tuple(int(bit) for bit in bits)

    if len(candidate) != ASH_STATE_BITS:
        raise ValueError("ASH states must be full 9-bit vectors")
    if any(bit not in (0, 1) for bit in candidate):
        raise ValueError("ASH state coordinates must be elements of F2")
    return candidate


def encode_state_signature(bits: Sequence[int] | str) -> str:
    return "".join(str(bit) for bit in normalize_bits(bits))


def xor_bits(left: Sequence[int], right: Sequence[int]) -> tuple[int, ...]:
    left_bits = normalize_bits(left)
    right_bits = normalize_bits(right)
    return tuple(a ^ b for a, b in zip(left_bits, right_bits))


def codeword_index(codeword: Sequence[int] | str) -> int:
    candidate = normalize_bits(codeword)
    try:
        return CANONICAL_CODEWORDS.index(candidate)
    except ValueError as exc:
        raise ValueError("codeword is not in the canonical 16-member set") from exc


def transform_state(state: Sequence[int] | str, codeword: Sequence[int] | str) -> AshState:
    codeword_index(codeword)
    return AshState(xor_bits(normalize_bits(state), normalize_bits(codeword)))


def orbit(state: Sequence[int] | str) -> tuple[str, ...]:
    seed = normalize_bits(state)
    return tuple(sorted(encode_state_signature(xor_bits(seed, c)) for c in CANONICAL_CODEWORDS))


def orbit_id(state: Sequence[int] | str) -> str:
    return orbit(state)[0]


def encode_realm_identity(state: Sequence[int] | str) -> dict[str, str]:
    signature = encode_state_signature(state)
    return {
        "state_signature": signature,
        "realm_id": f"ash_state_{signature}",
        "orbit_id": orbit_id(signature),
    }


def _known_valid_orbits() -> set[str]:
    return {orbit_id(anchor) for anchor in YWE_REALM_STATE_ANCHORS.values()}


def classify_admissibility(state: Sequence[int] | str) -> str:
    try:
        bits = normalize_bits(state)
    except (TypeError, ValueError):
        return "UNCLASSIFIED"

    if bits in YWE_REALM_STATE_ANCHORS.values():
        return "VALID"
    if orbit_id(bits) in _known_valid_orbits():
        return "TRANSFORMATION_COMPATIBLE"
    return "TRANSFORMATION_INCOMPATIBLE"


def diagnose_state(state: Sequence[int] | str) -> dict[str, object]:
    status = classify_admissibility(state)
    system_state = SYSTEM_STATE_BY_ADMISSIBILITY[status]
    recovery = RECOVERY_BY_SYSTEM_STATE[system_state]
    severity = "INFO" if system_state == "STABLE" else "ERROR"
    if system_state in {"CONTAINED", "SAFE_HALT"}:
        severity = "CRITICAL"

    subject = "malformed"
    try:
        subject = encode_state_signature(state)
    except (TypeError, ValueError):
        pass

    return {
        "diagnostic_kind": "STATE_VALIDITY",
        "severity": severity,
        "stage": "DETECTION",
        "disposition": "RESOLVED" if system_state == "STABLE" else "PENDING",
        "subject_reference": subject,
        "parent_diagnostic_reference": "NONE",
        "chain_root_reference": "SELF",
        "rule_ids": ["ASH-STATE-GENERAL-001"],
        "summary": f"ASH state classified as {status}",
        "notes": [
            "Classification used the canonical F2^9 state space and fixed 16-codeword set.",
            f"System state: {system_state}; recovery category: {recovery}.",
        ],
        "admissibility_status": status,
        "system_state_class": system_state,
        "recovery_category": recovery,
    }


def build_cosmic_pattern_snapshot(
    seed_state: Sequence[int] | str,
    transition_codewords: Iterable[Sequence[int] | str] = (),
) -> dict[str, object]:
    current = AshState(normalize_bits(seed_state))
    transitions: list[dict[str, object]] = []
    active_codeword_sequence: list[str] = []
    for codeword in transition_codewords:
        idx = codeword_index(codeword)
        codeword_signature = encode_state_signature(CANONICAL_CODEWORDS[idx])
        current = transform_state(current.bits, codeword)
        active_codeword_sequence.append(codeword_signature)
        transitions.append(
            {
                "codeword_index": idx,
                "codeword": codeword_signature,
                "result_state": current.signature,
            }
        )

    diagnostic = diagnose_state(current.bits)
    return {
        "snapshot_type": "CosmicPatternSnapshot",
        "state_space": "F2^9",
        "codeword_set_size": len(CANONICAL_CODEWORDS),
        "normalized_state": current.signature,
        "source_orbit_id": orbit_id(current.bits),
        "active_codeword_sequence": active_codeword_sequence,
        "realm_identity": encode_realm_identity(current.bits),
        "diagnostic": diagnostic,
        "diagnostic_ref": diagnostic,
        "generation_plan_ref": None,
        "transitions": transitions,
        "materialization_boundary": "GenerationPlanner emits plans; ArtifactEmitter or adapters perform side effects.",
    }


def plan_generation(
    project_name: str,
    seed_state: Sequence[int] | str,
    transition_codewords: Iterable[Sequence[int] | str] = (),
    emission_target_kind: str = "design_manifest",
) -> dict[str, object]:
    snapshot = build_cosmic_pattern_snapshot(seed_state, transition_codewords)
    plan_ref = f"GenerationPlan:{project_name}:{snapshot['normalized_state']}:{emission_target_kind}"
    return {
        "plan_type": "GenerationPlan",
        "plan_ref": plan_ref,
        "project_name": project_name,
        "normalized_state": snapshot["normalized_state"],
        "cosmic_pattern_snapshot_ref": {
            "snapshot_type": snapshot["snapshot_type"],
            "normalized_state": snapshot["normalized_state"],
            "source_orbit_id": snapshot["source_orbit_id"],
            "active_codeword_sequence": snapshot["active_codeword_sequence"],
            "diagnostic_ref": snapshot["diagnostic_ref"],
        },
        "source_realm": encode_realm_identity(seed_state),
        "destination_realm": snapshot["realm_identity"],
        "axiom_diagnostic": snapshot["diagnostic"],
        "diagnostic_ref": snapshot["diagnostic_ref"],
        "artifacts": [
            {
                "artifact_kind": emission_target_kind,
                "source_state": snapshot["normalized_state"],
                "generation_plan_ref": plan_ref,
                "emitter_contract": "ArtifactEmitter",
            }
        ],
        "warnings": [],
        "metadata": {
            "planner_contract": "GenerationPlanner",
            "emitter_contract": "ArtifactEmitter",
            "side_effects_allowed": False,
        },
    }
