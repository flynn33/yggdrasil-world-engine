# Package Authority Compliance Remediation

Date: 2026-05-17
Status: package-bound remediation control added

## Issue

Repository work advanced beyond the active user-supplied instruction packages.
The current authorized remediation scope is limited to:

- `YWE_PHASE_7_POST_REMEDIATION_ACCEPTANCE_AUDIT_PACKAGE`
- `YWE_PHASE_8_TO_9_BASELINE_AND_BRANCH_REALITY_FOUNDATION_PACKAGE`

Repository roadmap text, readiness notes, handoff forward references, deferred
work lists, and inferred phase sequences are not implementation authority.

## Bug

Using repository-internal forward references as execution authority can introduce
schemas, checks, examples, handoffs, and architecture documents that were not
authorized by the supplied packages. That creates scope drift, makes the
repository appear farther along than the accepted package boundary, and costs
review time because later work must be unwound before package acceptance can be
trusted.

## Fix

This remediation returns the branch to the Phase 7 through Phase 9 package
boundary and adds an explicit package-authority guardrail:

- required Phase 7 and Phase 8-9 package artifacts must remain present;
- known out-of-scope later-phase artifacts must remain absent;
- workflow and local validation must run the package-authority check;
- unclear scope must stop for human clarification before editing.

## Validation Plan

Run:

```bash
bash scripts/run_checks.sh
python scripts/check_package_authority_scope.py
python scripts/check_phase_8_9_required_artifacts.py
python scripts/check_branch_reality_guardrail.py
```

## Acceptance Boundary

This is a scope-control remediation. It does not authorize new runtime feature
work, new phase implementation, platform code, or future package execution.
