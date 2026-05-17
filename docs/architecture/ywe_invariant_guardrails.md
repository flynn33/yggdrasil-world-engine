# YWE Invariant Guardrails

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: YWE and Forsetti guardrail baseline

## Canon Guardrails

- `cosmology_authority_invariant`: ASH Cosmological Model is the upstream foundation for YWE and its systems
- `asp_component_invariant`: ASH Pattern System is a YWE component for diagnostics, pattern integrity, recovery, containment, resilience, conformance, and update/patch stability
- `base_world_ontology_invariant`: the nine planes define the base world ontology and are not generated branch realities
- `leaf_branch_reality_invariant`: leaf branch realities are runtime-generated player realities created from meaningful branch events and cosmology-grounded context
- `no_pregenerated_branch_tree_invariant`: YWE must not model branch reality as a pre-authored alternate-reality catalog
- `wolf_non_morality_invariant`: White Wolf and Dark Wolf are symbiotic attractors, not moral opposites or morality meters
- No YWE system may redefine ASH math
- YWE consumes ASH-derived state, diagnostics, codeword traces, and generation plans
- Player actions influence generation context; they do not mutate ASH math
- feature engines specialize ASH-derived interpretation into manifests
- host adapters materialize approved manifests but do not author truth
- meaningful generation is invalid unless it preserves ASH provenance
- all meaningful generation remains ASH-derived
- fixed cosmology and the nine realms remain locked
- White Wolf and Dark Wolf remain primordial informational forces
- players begin as mortals with veiled celestial memory
- perception may diverge experience but may not rewrite shared-world truth
- myth and prophecy remain distinct systems

## Shared Packet Spine Guardrails

Every meaningful generation flow must preserve this order:

```text
YWEGenerationContextPacket
  -> ASHUpstreamGenerationEnvelope
  -> YWEInterpretationPacket
  -> SystemManifestHandoff
  -> WorldstateDeltaPacket or DiagnosticNoOp
  -> FutureGenerationBiasUpdate
```

Every meaningful manifest must retain:

- `source_ash_refs`
- `diagnostic_ref`
- `generation_plan_ref`
- `requested_manifest_kind`
- `worldstate_delta_policy`

## Red-Team Forbidden Language Checks

The following claims are invalid outside rejection tests, red-team checklists,
or explicit explanations of invalid design patterns:

- ASH Pattern System is the topmost authority
- ASH Pattern System owns the cosmology
- ASH Pattern System is upstream from YWE
- all systems are based on ASH Pattern System math
- Where Ravens Wait is the engine
- Yggdrasil World Engine is only the game title
- YWE owns ASH math
- YWE defines ASH math
- YWE mutates ASH math
- YWE replaces ASH math
- YWE core math
- local ASH math
- local ASH codeword set
- feature engine authored pattern truth
- adapter authored truth
- materialization before generation planning

## Forsetti Guardrails

- runtime features must be manifest-driven modules
- activation requires compatibility validation and host-defined entitlement approval when applicable
- service modules may run concurrently
- only one UI module may be active at a time
- modules communicate through framework-mediated channels only
- `forsetti.internal.*` remains reserved
- `ui_theme_mask` remains reserved for the framework

## Branch Guardrails

- main remains code-agnostic
- Forsetti implementation files are not vendored here
- platform APIs do not belong in this branch
- Forsetti governs activation while YWE governs truth
