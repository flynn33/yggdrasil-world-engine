"""Canonical ASH Pattern System surface for YWE.

This module is intentionally small and deterministic. It mirrors the ASH
canonical baseline in `specs/` and gives validation scripts a concrete runtime
surface for the locked 9-bit state space, fixed 16-codeword set, diagnostics,
and planner/emitter materialization boundary.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from .state_values import AshState, CANONICAL_CODEWORDS, StateContractError

ASH_STATE_BITS = 9

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

RECOVERY_BY_SYSTEM_STATE = {
    "STABLE": "NO_ACTION",
    "UNSTABLE": "NORMALIZE_STATE",
    "CORRECTABLE": "APPLY_CORRECTION",
    "DEGRADED": "FALLBACK_REQUIRED",
    "CONTAINED": "CONTAINMENT_REQUIRED",
    "FAILED": "ESCALATION_REQUIRED",
    "SAFE_HALT": "TERMINAL_NO_RECOVERY",
}

def normalize_bits(bits: Sequence[int] | str) -> tuple[int, ...]:
    from .state_model import StateInputCodec

    decoded = StateInputCodec().decode(
        bits, original_input_reference="legacy:normalization", legacy_whitespace=True
    )
    if decoded.state is None:
        raise StateContractError(decoded.input_evidence.failure_code, "bits")
    return decoded.state.bits


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


def encode_state_identity(state: Sequence[int] | str) -> dict[str, str]:
    """Return the canonical identity of one full ASH state-space vertex.

    ``realm_id`` is retained as a lossless compatibility alias of
    ``vertex_id``. ``orbit_id`` remains supplemental relation metadata; it is
    not a substitute for the identity of the individual vertex.
    """
    signature = encode_state_signature(state)
    vertex_id = f"ash_state_{signature}"
    return {
        "state_signature": signature,
        "vertex_id": vertex_id,
        "realm_id": vertex_id,
        "orbit_id": orbit_id(signature),
    }


def encode_realm_identity(state: Sequence[int] | str) -> dict[str, str]:
    """Compatibility alias for :func:`encode_state_identity`."""
    return encode_state_identity(state)


def classify_admissibility(state: Sequence[int] | str) -> str:
    return diagnose_state(state)["admissibility_status"]


def diagnose_state(state: Sequence[int] | str) -> dict[str, object]:
    """Return complete WRW diagnosis without inferring contextual recovery facts."""
    from .state_model import legacy_diagnosis

    return legacy_diagnosis(state)


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
    state_identity = encode_state_identity(current.bits)
    return {
        "snapshot_type": "CosmicPatternSnapshot",
        "state_space": "F2^9",
        "codeword_set_size": len(CANONICAL_CODEWORDS),
        "normalized_state": current.signature,
        "source_orbit_id": orbit_id(current.bits),
        "active_codeword_sequence": active_codeword_sequence,
        "state_identity": state_identity,
        "realm_identity": state_identity,
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
    source_state_identity = encode_state_identity(seed_state)
    destination_state_identity = snapshot["state_identity"]
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
        "source_state_identity": source_state_identity,
        "destination_state_identity": destination_state_identity,
        "source_realm": source_state_identity,
        "destination_realm": destination_state_identity,
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
