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

The ASH upstream authority extension adds an engine-agnostic architecture
contract that makes ASH the upstream mathematical and generative authority for
YWE. It defines the generation spine from `YWEGenerationContextPacket` through
`ASHUpstreamGenerationEnvelope`, `YWEInterpretationPacket`, feature manifests,
host materialization, `WorldstateDeltaPacket` or `DiagnosticNoOp`, and
`FutureGenerationBiasUpdate`.

This verification pass is additive against the restored planning baseline.
Existing engine, rule, data, and exchange files retain their original design
content and now carry ASH provenance and materialization contract extensions.

## Package Acceptance Surface

Blocking acceptance script:

`.github/scripts/ywe_package_acceptance_check.py`

Gate contract:

`data/validation/ash_generation_gate_contract.json`

Upstream authority contract:

`docs/architecture/ash_upstream_authority_contract.md`

Upstream authority gate:

`data/validation/ash_upstream_authority_gate_contract.json`

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

The upstream authority extension also requires manual and scripted inspection
for:

1. `ash_upstream_authority_contract.md` existence and references.
2. Runtime generation flow coverage for `YWEGenerationContextPacket`,
   `ASHUpstreamGenerationEnvelope`, `YWEInterpretationPacket`,
   `WorldstateDeltaPacket`, and `FutureGenerationBiasUpdate`.
3. Packet schema coverage for `PlayerActionTrace`,
   `ExplorationFrontierRequest`, and `SystemManifestExchange`.
4. Gate-contract provenance fields: `source_ash_refs`, `diagnostic_ref`,
   `generation_plan_ref`, `requested_manifest_kind`, and
   `worldstate_delta_policy`.

## Acceptance Boundary

YWE remains code-agnostic. This repository defines contracts, schemas,
validators, data records, diagnostics, and conformance evidence. Engine
adapters and host implementations may materialize only from `GenerationPlan`
outputs and must not author ASH truth or YWE domain truth.

Player actions influence future generation context; they do not mutate ASH
math. Host adapters materialize approved manifests but do not author symbolic
truth.
