# YWE Phase 12 Handoff — Existential Quest, NPC, and Lore Generation

Date: 2026-05-18  
Status: active_implementation_handoff  
Scope: code-agnostic repository contracts, schemas, validation, examples

## Purpose

This handoff records the Phase 12 implementation result for existential quest,
NPC, and lore generation.

## Authority Stack

```text
Where Ravens Wait: Eternal Reckoning = game / narrative layer
Yggdrasil World Engine = agnostic game engine
ASH Cosmological Model = upstream foundation for YWE and its systems
ASH Pattern System = YWE component for diagnostics, recovery, containment, conformance, pattern integrity, code resilience, and patch/update stability
```

## Phase 12 Target

```text
Phase 12 — Existential Quest, NPC, and Lore Generation
```

## Required Core Files

```text
docs/architecture/quest_generation_from_axioms_contract.md
docs/architecture/npc_generation_from_branch_context_contract.md
docs/architecture/lore_generation_from_pattern_trace_contract.md

data/schemas/quest_generation_context_schema.json
data/schemas/npc_generation_context_schema.json
data/schemas/lore_generation_context_schema.json
data/schemas/generated_lore_fragment_schema.json
```

## Acceptance Summary

Phase 12 is accepted when generated quests, NPCs, and lore are proven to derive from:

```text
axiom pressure
existence potential Φ
pattern vector state
branch reality
player consequence history
location state
worldstate deltas
plane pressure
wolf / bloodline / attunement context
```

and are not arbitrary content tables.

## Files Added

Architecture contracts:

- `docs/architecture/quest_generation_from_axioms_contract.md`
- `docs/architecture/npc_generation_from_branch_context_contract.md`
- `docs/architecture/lore_generation_from_pattern_trace_contract.md`
- `docs/architecture/existential_content_generation_integration_map.md`
- `docs/architecture/quest_npc_lore_truth_boundary_contract.md`
- `docs/architecture/quest_npc_lore_manifest_provenance_contract.md`
- `docs/architecture/content_generation_acceptance_contract.md`
- `docs/architecture/axiom_to_content_pressure_map.md`

Schemas:

- `data/schemas/quest_generation_context_schema.json`
- `data/schemas/quest_axiom_pressure_schema.json`
- `data/schemas/quest_chain_seed_schema.json`
- `data/schemas/quest_manifest_candidate_schema.json`
- `data/schemas/quest_stage_candidate_schema.json`
- `data/schemas/quest_resolution_policy_schema.json`
- `data/schemas/npc_generation_context_schema.json`
- `data/schemas/npc_manifest_candidate_schema.json`
- `data/schemas/npc_relation_graph_schema.json`
- `data/schemas/npc_self_reference_state_schema.json`
- `data/schemas/npc_branch_role_schema.json`
- `data/schemas/lore_generation_context_schema.json`
- `data/schemas/lore_pattern_trace_schema.json`
- `data/schemas/generated_lore_fragment_schema.json`
- `data/schemas/lore_visibility_rule_schema.json`
- `data/schemas/content_generation_provenance_schema.json`
- `data/schemas/content_generation_candidate_schema.json`
- `data/schemas/content_generation_resolution_schema.json`
- `data/schemas/content_eligibility_gate_schema.json`
- `data/schemas/content_rejection_reason_schema.json`
- `data/schemas/content_generation_batch_schema.json`
- `data/schemas/content_manifest_handoff_schema.json`
- `data/schemas/quest_npc_lore_linkage_schema.json`

Validation, examples, and conformance:

- `data/validation/phase_12_acceptance_contract.json`
- `data/validation/phase_12_required_artifacts.json`
- `data/validation/phase_12_guardrail_rules.json`
- `data/validation/phase_12_forbidden_language_patterns.json`
- `data/validation/phase_12_non_destructive_change_budget.json`
- `data/validation/phase_12_github_checks_matrix.json`
- `data/validation/phase_12_prerequisite_gate.json`
- `data/validation/axiom_content_mapping_rules.json`
- `data/validation/content_provenance_validation_rules.json`
- `data/validation/quest_generation_validation_rules.json`
- `data/validation/npc_generation_validation_rules.json`
- `data/validation/lore_generation_validation_rules.json`
- `data/validation/truth_scope_content_validation_rules.json`
- `data/validation/ravenfall_gate_phase_12_example_validation.json`
- `data/validation/check_phase_11_acceptance_prereq.spec.json`
- `data/validation/check_required_phase_12_contracts.spec.json`
- `data/validation/check_phase_12_json_integrity.spec.json`
- `data/validation/check_no_generic_random_quest_generation.spec.json`
- `data/validation/check_axiom_generation_contracts.spec.json`
- `data/validation/check_feature_manifest_provenance_phase_12.spec.json`
- `data/validation/check_npc_relation_and_self_reference.spec.json`
- `data/validation/check_lore_pattern_trace_provenance.spec.json`
- `data/validation/check_quest_npc_lore_truth_scope.spec.json`
- `data/validation/check_no_content_generation_without_context.spec.json`
- `data/validation/check_non_destructive_diff_phase_12.spec.json`
- `examples/phase_12_quest_npc_lore_generation/`
- `conformance/phase-12-existential-quest-npc-lore-generation.md`

## Files Changed

- `scripts/check_quest_npc_lore_generation.py`: promoted Phase 12 from deferred scaffold validation to active artifact, schema, example, forbidden-language, and non-destructive-diff guardrails.
- `scripts/run_checks.sh`: marks Phase 10, Phase 11, and Phase 12 guardrails active.
- `scripts/check_branch_reality_guardrail.py`: excludes the Phase 12 forbidden-pattern registry from active prose scans.
- `data/validation/phase_8_9_package_boundary_guardrail.json`: adds Phase 12 to the accepted package boundary and removes active Phase 12 artifacts from the deferred-marker list.
- `data/validation/quest_npc_lore_generation_gate_contract.json`: points Phase 12 scope to this handoff.
- `data/schemas/quest_npc_lore_generation_schema.json`: removes the prior deferred boundary marker.
- `docs/architecture/README.md`, `data/schemas/README.md`, and `docs/handoff/README.md`: add active Phase 12 indexes.
- `docs/architecture/quest_npc_lore_generation_v1.md` and `docs/handoff/YWE_PHASE_12_QUEST_NPC_LORE_GENERATION_HANDOFF_2026-05-17.md`: retain earlier scaffold as historical evidence while pointing active authority to this package.
- `REMEDIATION_PHASE_STATUS.md`: updates phase-boundary text for accepted Phase 7 through Phase 12 records.

## Intentionally Not Touched

- Phase 13 Twin Wolf Companion Engine artifacts.
- Phase 14 Ability / Power Engine artifacts.
- Phase 15 Quest Reward Resolver artifacts.
- Phase 16 Ravenfall Gate vertical-slice artifacts.
- Platform-specific runtime code and host adapters.
- Package root prompts and manifests from the workstation handoff package.

## Checks Run

- `python3 scripts/check_quest_npc_lore_generation.py .`: pass.
- `python3 scripts/check_phase_8_9_package_boundary.py .`: pass.
- `python3 scripts/check_branch_reality_guardrail.py`: pass.
- `git diff --check`: pass.
- Repository JSON parse check: pass.
- `bash scripts/run_checks.sh`: pass, `14 passed, 0 failed`.

## Acceptance Gates

- Gate 12.0 Phase 11 prerequisite: pass.
- Gate 12.1 required artifacts: pass.
- Gate 12.2 JSON integrity: pass.
- Gate 12.3 quest guardrails: pass.
- Gate 12.4 NPC guardrails: pass.
- Gate 12.5 lore guardrails: pass.
- Gate 12.6 truth scope: pass.
- Gate 12.7 provenance: pass.
- Gate 12.8 non-destructive diff: pass.
- Gate 12.9 handoff report: pass.

## Blockers

None.

## Phase 13 Readiness

Phase 12 establishes the quest, NPC, lore, truth-scope, provenance, and content
handoff foundation required before Phase 13. Phase 13 work remains deferred
until the next owner-approved package is supplied.
