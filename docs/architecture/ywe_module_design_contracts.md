# YWE Module Design Contracts

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: Forsetti-compatible module baseline

## ASH Upstream Authority Rule

This section title is retained as a superseded acceptance marker. Current
module authority language is the ASH Cosmology Authority Rule below.

## ASH Cosmology Authority Rule

ASH Cosmological Model is the upstream foundation for YWE and its systems. ASH
Pattern System is a YWE component for diagnostics, pattern integrity, recovery,
containment, resilience, conformance, and update/patch stability. All core and
feature modules interpret the ASH Cosmological Model through YWE contracts and
may consume ASH Pattern System component diagnostics through the shared packet
spine defined in `ash_upstream_authority_contract.md`. The shared packet spine
remains valid as component-level diagnostic, conformance, and stability
evidence.

The module authority chain is:

```text
ASH Cosmological Model
  -> Yggdrasil World Engine
    -> ASH Pattern System component and YWE runtime systems
      -> YWE feature engines
        -> platform-specific runtime implementations
```

YWE consumes ASH-derived state, diagnostics, codeword traces, and generation
plans. Feature engines specialize ASH Cosmological Model-derived
interpretation into manifests and may use ASH Pattern System component checks
for stability.
No module may redefine ASH math, author local symbolic grammar, bypass ASH
diagnostics, or materialize meaningful content before a `GenerationPlan`.

## Core Truth Services

- `com.ywe.core.cosmology-engine`: planned `service` module for cosmology canon and realm ontology anchors.
- `com.ywe.core.realm-engine`: planned `service` module for attunement and lawful realm access.
- `com.ywe.core.ash-pattern-engine`: planned `service` module for ASH-derived pattern detection.
- `com.ywe.core.narrative-engine`: planned `service` module for interpretation, quest pressure, and consequence routing.
- `com.ywe.core.perception-engine`: planned `service` module for multiplayer-safe divergence without rewriting shared truth.

## Feature Manifestation Services

- `com.ywe.module.quest-engine`: planned `service` module for quest chains and quest state transitions.
- `com.ywe.module.myth-engine`: planned `service` module for myth seeds, myth records, and faction versions.
- `com.ywe.module.prophecy-engine`: planned `service` module for prophecy weighting and activation pressure.
- `com.ywe.module.artifact-engine`: planned `service` module for artifact manifestations.
- `com.ywe.module.creature-engine`: planned `service` module for creature manifestations.

## Adapter Position

- Unity, Unreal, and Godot remain downstream execution connectors.
- In a Forsetti implementation, they belong in platform-specific host or app layers.
- They must never become sources of canonical YWE truth.
- They must materialize approved manifests but do not author symbolic truth.

## Shared Rules

- modules that emit meaningful manifests preserve `source_ash_refs`, `diagnostic_ref`, `generation_plan_ref`, `requested_manifest_kind`, and `worldstate_delta_policy`
- generation context enters ASH-governed generation through `YWEGenerationContextPacket`
- `YWEGenerationContextPacket.player_runtime_state_ref` points to `PlayerRuntimeState`, the Phase 10 player-specific runtime truth contract
- player branch context must flow through `current_leaf_branch_ref`, `branch_generation_context_refs`, and `branch_event_refs`; feature modules may read those refs but may not author canonical player state directly
- persistent consequence must flow through `WorldstateDeltaPacket`; scoped site changes must flow through `LocationMutationState` and `LocationMutationDelta`
- location mutation may influence future generation context through `FutureGenerationBiasUpdate`, but it may not rewrite base ontology or bypass diagnostic evidence
- feature modules receive ASH-derived interpretation through `YWEInterpretationPacket`
- modules activate through Forsetti lifecycle rules
- modules communicate through framework-mediated channels only
- direct runtime dependencies remain one-way
- peer awareness may exist through events, not direct ownership inversion
- truth-sensitive responsibilities must be declared as non-delegable even when realization support is delegable-compatible
- suppression conditions may defer activation but may not transfer YWE truth ownership to adapters or external environments
- truth modules never request framework-reserved `ui_theme_mask`
