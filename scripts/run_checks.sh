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

run_check() {
    local name="$1"
    local cmd="$2"
    echo "--- $name ---"
    if eval "$cmd"; then
        echo "PASS: $name"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $name"
        FAIL=$((FAIL + 1))
    fi
    echo ""
}

run_check "Architecture Validation" "python3 '$SCRIPT_DIR/validate_architecture.py' '$ROOT_DIR'"
run_check "Schema Validation" "python3 '$SCRIPT_DIR/validate_schemas.py' '$ROOT_DIR'"
run_check "ASH Compliance Validation" "python3 '$SCRIPT_DIR/validate_ash_compliance.py' '$ROOT_DIR'"

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
