# Verification Report

Date: 2026-05-10

## Summary

The repository mirrors canonical ASH specs under `specs/` and
`core/ash_pattern_engine/canonical/`. Local validation checks the `F2^9` state
space, fixed 16-codeword set, exact runtime codeword set, full-state XOR
transition, closure, orbit count, diagnostics, materialization boundary,
downstream manifest dependencies, and ASH-derived data wrappers.

The ASH/ASP core-math rebuild adds a blocking package acceptance check for all
meaningful YWE generation systems.

This verification pass is additive against the restored planning baseline.
Existing engine, rule, data, and handoff files retain their original design
content and now carry ASH provenance and materialization contract extensions.

## Package Acceptance Surface

Blocking acceptance script:

`.github/scripts/ywe_package_acceptance_check.py`

Gate contract:

`data/validation/ash_generation_gate_contract.json`

Generation conformance evidence:

`conformance/generation-system-conformance.md`

Governance evidence:

`conformance/governance-boot-record.md`

## Required Test Families

The package acceptance script implements the following required test families:

1. `test_rejects_8_plus_1_language`
2. `test_rejects_parity_control_bit_baseline`
3. `test_codeword_set_exactly_16`
4. `test_transition_is_full_state_xor`
5. `test_all_generation_requires_cosmic_pattern_snapshot`
6. `test_all_generation_requires_diagnostic_envelope`
7. `test_all_materialization_requires_generation_plan`
8. `test_all_engine_interfaces_carry_ash_math_contract`
9. `test_character_creation_requires_ash_provenance`
10. `test_creature_creation_requires_ash_provenance`
11. `test_quest_generation_requires_multiple_interpretations_and_delta_route`
12. `test_myth_is_retrospective_not_world_truth_rewrite`
13. `test_prophecy_is_attractor_not_script`
14. `test_perception_overlay_does_not_rewrite_shared_world_truth`
15. `test_adapters_cannot_author_ywe_truth`

## Acceptance Boundary

YWE remains code-agnostic. This repository defines contracts, schemas,
validators, data records, diagnostics, and conformance evidence. Engine
adapters and host implementations may materialize only from `GenerationPlan`
outputs and must not author ASH truth or YWE domain truth.
