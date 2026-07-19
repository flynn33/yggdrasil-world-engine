# Repository Status

This index records the current Yggdrasil World Engine project state in durable
repository terms. Canonical contracts, schemas, validation rules, examples, and
conformance files remain the active authority for implementation details.

The active specification roadmap is
`docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md`. Historical phase acceptance
below records package provenance; it does not by itself assert normative,
schema, conformance, or release completion.

## Specification Maturity

| Dimension | Current status |
|---|---|
| Historical phase gates | Accepted through the Phase 16/17 foundation |
| Normative artifact completion | Partial |
| Executable schema completion | Partial; tracked under M2 |
| Whole-system conformance | Not complete |
| Agnostic specification release readiness | Not ready |
| Published releases | None; no GitHub Release objects or agnostic specification releases have been published |
| M0 truthful baseline | Complete; evidence recorded in `data/governance/m0_acceptance_evidence.json` and `docs/project/M0_TRUTHFUL_BASELINE_ACCEPTANCE.md` |
| Current roadmap milestone | M1 - Normalize canon terminology and governance |
| Platform product work | Deferred through M10 |

## Authority Stack

| Layer | Current authority |
|---|---|
| Game and narrative | Where Ravens Wait: Eternal Reckoning |
| Engine | Yggdrasil World Engine |
| Foundation | ASH Cosmological Model |
| Resilience component | ASH Pattern System |

## Accepted Phase Sequence

| Phase | Status | Canonical anchors |
|---|---|---|
| Phase 7 - Post-Alignment Acceptance Audit | `PHASE_7_ACCEPTED` | `docs/architecture/ywe_cosmology_authority_contract.md`, `data/validation/phase_7_acceptance_audit_contract.json` |
| Phase 8 - Baseline Freeze and Restore Point | accepted | `docs/project/repository_status.md`, `data/validation/phase_8_9_acceptance_contract.json` |
| Phase 9 - Runtime Cosmology and Leaf Branch Reality Foundation | accepted | `docs/architecture/runtime_cosmology_foundation_contract.md`, `docs/architecture/leaf_branch_reality_contract.md` |
| Phase 10 - Player Runtime State v1 | accepted | `docs/architecture/player_runtime_state_contract.md`, `data/schemas/player_runtime_state_schema.json` |
| Phase 11 - Worldstate and Location Mutation | accepted | `docs/architecture/worldstate_location_mutation_v1.md`, `data/schemas/worldstate_location_mutation_schema.json` |
| Phase 12 - Quest, NPC, and Lore Generation | accepted | `docs/architecture/quest_npc_lore_generation_v1.md`, `data/schemas/quest_npc_lore_generation_schema.json` |
| Phase 14 - Ability and Power Engine | accepted | `docs/architecture/ability_power_engine_contract.md`, `data/validation/phase_14_acceptance_contract.json` |
| Phase 15A - Companion and Reward Foundation | accepted | `docs/architecture/companion_reward_integration_map.md`, `data/validation/phase_15a_acceptance_contract.json` |
| Phase 16 - Ravenfall Gate Vertical Slice | accepted | `docs/architecture/ravenfall_gate_vertical_slice_integration_map.md` |
| Phase 17 - Playtest Trace and Acceptance Expansion | accepted | `docs/architecture/phase_17_repository_guardrails.md`, `data/validation/phase_17_acceptance_contract.json` |
| Phase 18 readiness | unblocked | `docs/architecture/phase_16_17_recovery_and_phase_18_unblock_contract.md`, `data/validation/phase_18_unblock_prerequisite_contract.json` |

## Boundary Facts

- The nine planes of existence define the base world ontology.
- Leaf branch realities are runtime-generated player realities.
- Leaf branches are not pre-generated.
- Player runtime state references branch reality; it does not replace branch reality.
- Worldstate and location mutation use scoped consequence packets and preserve base ontology.
- Quest, NPC, lore archive, myth, and prophecy outputs require provenance and truth scope.
- Ability, companion, reward, vertical-slice, and playtest artifacts are code-agnostic repository contracts; only a future post-M10 downstream adapter contract may own host realization.

## Validation Entry Points

- `bash scripts/run_checks.sh`
- `pwsh -File scripts/run_checks.ps1`
- `python3 scripts/validate_repository.py --list`
- `data/validation/repository_checks.json`
