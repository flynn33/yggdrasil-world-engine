# YWE Cosmology Authority Remediation Handoff - 2026-05-16

Date: 2026-05-16
Copied into `docs/handoff`: 2026-05-17
Status: accepted Phase 0-6 cosmology-authority remediation handoff

Provenance: this file is a path-stable copy of root `REMEDIATION_HANDOFF.md`,
created during Phase 7 to satisfy the required artifact path
`docs/handoff/YWE_COSMOLOGY_AUTHORITY_REMEDIATION_HANDOFF_2026-05-16.md`.

## Summary

Repository authority stack alignment completed.

## Corrected hierarchy

```text
Where Ravens Wait: Eternal Reckoning = game/narrative layer
Yggdrasil World Engine = agnostic engine
ASH Cosmological Model = upstream foundation for YWE and its systems
ASH Pattern System = YWE component for diagnostics/resilience/stability
```

## Files created

- `.github/workflows/ywe_repository_guardrails.yml`
- `REMEDIATION_BASELINE_CHECK_RESULTS.json`
- `REMEDIATION_BASELINE_FILE_LIST.json`
- `REMEDIATION_BASELINE_INVENTORY.md`
- `REMEDIATION_GATE_RESULTS.json`
- `data/schemas/authority_stack_schema.json`
- `data/validation/cosmology_authority_gate_contract.json`
- `data/validation/repository_drift_guardrail_rules.json`
- `docs/architecture/ash_cosmological_model_source_map.md`
- `docs/architecture/ash_pattern_system_component_contract.md`
- `docs/architecture/ywe_cosmology_authority_contract.md`
- `scripts/check_authority_stack.py`
- `scripts/check_json_integrity.py`
- `scripts/check_non_destructive_diff.py`
- `scripts/check_required_contracts.py`

## Files updated

- `.github/PULL_REQUEST_TEMPLATE.md`
- `README.md`
- `SOURCE_AVAILABILITY_MANIFEST.md`
- `conformance/acceptance-judgment.md`
- `conformance/generation-system-conformance.md`
- `core/narrative_engine/ash_runtime_generation_flow.yaml`
- `docs/architecture/README.md`
- `docs/architecture/ash_downstream_contract.md`
- `docs/architecture/ash_upstream_authority_contract.md`
- `docs/architecture/ywe_cross_module_dependency_map.md`
- `docs/architecture/ywe_invariant_guardrails.md`
- `docs/architecture/ywe_module_design_contracts.md`
- `docs/ash_compliance/ash_compliance_checklist.md`
- `docs/glossary/ywe_design_glossary.md`
- `docs/master_specification/YWE_MASTER_SPECIFICATION.md`
- `missing_source_documents.md`

## Files intentionally preserved

- `core/ash_pattern_engine/canonical/**`
- `specs/**`
- `lore/**`
- `data/realm_registry/**`
- `data/bloodline_registry/**`
- `modules/**`
- `conformance/**`
- `docs/handoff/**`

## Files deleted

none

## Checks run

| Check | Result | Notes |
|---|---|---|
| `bash scripts/run_checks.sh` | passed | 10 passed, 0 failed |
| `python3 scripts/check_json_integrity.py` | passed | 74 JSON files parsed |
| `python3 scripts/check_required_contracts.py` | passed | required contracts present |
| `python3 scripts/check_authority_stack.py --config data/validation/repository_drift_guardrail_rules.json` | passed | authority stack scan passed |
| `python3 scripts/check_non_destructive_diff.py --base origin/main --head HEAD` | passed | no protected deletions |

## Gate results

```json
{
  "gate_0": "passed",
  "gate_1": "passed",
  "gate_2": "passed",
  "gate_3": "passed",
  "gate_4": "passed",
  "gate_5": "passed",
  "gate_6": "passed"
}
```

## Remaining design work

Do not start these in this remediation unless explicitly instructed. This list
is roadmap context only, not executable authority.

```text
Player Runtime State v1
Leaf Branch Reality Engine
World and Location State Contract
Twin Wolf Companion Engine
Quest Reward Resolver
Ability / Power Engine
Ravenfall Gate vertical slice
```

## Risk notes

- Prior ASH upstream authority language is retained only as explicitly superseded historical/component evidence so existing acceptance checks and conformance records remain traceable.
- New guardrail scripts allow explicit forbidden-language lists and superseded/historical context, while rejecting unqualified current-truth drift.
- Existing local wiki-source changes in the original checkout were not touched; remediation was performed in a clean sibling worktree.

## Rollback plan

Revert the remediation branch commit(s) or discard the sibling worktree if not committed. Avoid `git reset --hard` or destructive cleanup unless explicitly approved by the repository owner.

## Final acceptance statement

Repository alignment completed without destructive deletion. The repository now recognizes the ASH Cosmological Model as the engine foundation, the ASH Pattern System as a YWE resilience/stability component, Yggdrasil World Engine as the agnostic engine, and Where Ravens Wait: Eternal Reckoning as the game/narrative layer.
