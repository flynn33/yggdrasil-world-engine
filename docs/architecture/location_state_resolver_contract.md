# Location State Resolver Contract

## Purpose

The Location State Resolver determines how a location appears, behaves, unlocks, remembers, and exposes content when visited or revisited.

## Core formula

```text
ResolvedLocationState =
  BaseLocationState
  + SharedWorldDeltas
  + LeafBranchDeltas
  + LocationMutationHistory
  + LocationBranchOverlays
  + PlayerRuntimeContext
  + PlanePressure
  + FutureGenerationBias
  + Diagnostics
```

## Inputs

```text
location_id
base_location_ref
leaf_branch_reality_ref
player_runtime_state_ref
player_state_snapshot_ref
player_action_trace_refs
worldstate_delta_refs
location_mutation_history_refs
location_branch_overlay_refs
plane_pressure_state_ref
future_generation_bias_refs
ash_pattern_diagnostic_refs
source_cosmology_refs
```

## Outputs

```text
ResolvedLocationState
LocationStateRecord update
LocationBranchOverlay update
LocationAccessState
LocationContentEligibility
WorldstateDeltaPacket or DiagnosticNoOp
FutureGenerationBiasUpdate
```

## Location mutability

Locations are stateful world surfaces. A location may mutate at runtime in response to:

```text
player action
branch events
worldstate deltas
plane attunement
bloodline resonance
wolf resonance
myth pressure
prophecy pressure
faction claims
artifact bindings
creature ecology
ASP diagnostics and recovery events
```

## Boundary

A location resolver may determine eligibility and state. It must not directly write full quest, NPC, lore, artifact, or creature content for Phase 12+ systems.

## Required rejection cases

Reject or return DiagnosticNoOp when:

```text
mutation lacks provenance
mutation tries to redefine base ontology
branch overlay tries to rewrite shared truth
perception-only change is marked as shared truth
future generation bias directly materializes content
```
