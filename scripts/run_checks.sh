#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "Yggdrasil World Engine -- Validation Suite"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PASS=0
FAIL=0
PYTHON_CMD=()

resolve_python() {
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD=(python3)
        return 0
    fi

    if command -v python >/dev/null 2>&1; then
        PYTHON_CMD=(python)
        return 0
    fi

    if command -v py >/dev/null 2>&1; then
        PYTHON_CMD=(py -3)
        return 0
    fi

    return 1
}

run_check() {
    local name="$1"
    shift
    echo "--- $name ---"
    if "$@"; then
        echo "PASS: $name"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $name"
        FAIL=$((FAIL + 1))
    fi
    echo ""
}

if ! resolve_python; then
    echo "No supported Python launcher found (tried python3, python, py -3)."
    exit 1
fi

run_check "Architecture Validation" "${PYTHON_CMD[@]}" "$SCRIPT_DIR/validate_architecture.py" "$ROOT_DIR"
run_check "Schema Validation" "${PYTHON_CMD[@]}" "$SCRIPT_DIR/validate_schemas.py" "$ROOT_DIR"
run_check "ASH Compliance Validation" "${PYTHON_CMD[@]}" "$SCRIPT_DIR/validate_ash_compliance.py" "$ROOT_DIR"
run_check "ASH Canonical Semantic Integrity" "${PYTHON_CMD[@]}" "$ROOT_DIR/.github/scripts/semantic_integrity_check.py" "$ROOT_DIR"
run_check "ASH Math Integrity" "${PYTHON_CMD[@]}" "$ROOT_DIR/.github/scripts/math_integrity_check.py" "$ROOT_DIR"
run_check "ASH Downstream Conformance Artifacts" "${PYTHON_CMD[@]}" "$ROOT_DIR/.github/scripts/downstream_conformance_check.py" "$ROOT_DIR"
run_check "YWE Package Acceptance Tests" "${PYTHON_CMD[@]}" "$ROOT_DIR/.github/scripts/ywe_package_acceptance_check.py" "$ROOT_DIR"
run_check "Phase 8-9 Package Boundary Guardrail" "${PYTHON_CMD[@]}" "$SCRIPT_DIR/check_phase_8_9_package_boundary.py" "$ROOT_DIR"
run_check "Discussion Agent Validation" "${PYTHON_CMD[@]}" "$SCRIPT_DIR/github/discussion_agent.py" --validate-config --root "$ROOT_DIR"
run_check "Discussion Topic Generator Validation" "${PYTHON_CMD[@]}" "$SCRIPT_DIR/github/discussion_topic_agent.py" --validate-config --root "$ROOT_DIR"
run_check "Discussion Moderation Validation" "${PYTHON_CMD[@]}" "$SCRIPT_DIR/github/discussion_moderation_agent.py" --validate-config --root "$ROOT_DIR"
echo "Phase 10 and Phase 11 guardrails are active; Phase 12 guardrails remain deferred artifact integrity checks."
run_check "Player Runtime State Guardrail" "${PYTHON_CMD[@]}" "$SCRIPT_DIR/check_player_runtime_state.py" "$ROOT_DIR"
run_check "Worldstate Location Mutation Guardrail" "${PYTHON_CMD[@]}" "$SCRIPT_DIR/check_worldstate_location_mutation.py" "$ROOT_DIR"
run_check "Quest NPC Lore Generation Guardrail" "${PYTHON_CMD[@]}" "$SCRIPT_DIR/check_quest_npc_lore_generation.py" "$ROOT_DIR"

echo "=========================================="
echo "Results: $PASS passed, $FAIL failed"
echo "=========================================="

if [ "$FAIL" -gt 0 ]; then
    echo "VALIDATION FAILED"
    exit 1
else
    echo "ALL CHECKS PASSED"
    exit 0
fi
