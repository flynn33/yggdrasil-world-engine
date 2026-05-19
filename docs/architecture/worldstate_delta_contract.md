# Worldstate Delta Contract

## Purpose

The Worldstate Delta Contract defines how YWE records meaningful consequences produced by player action, system resolution, location mutation, branch events, perception shifts, myth pressure, prophecy pressure, faction claims, artifact bindings, creature ecology changes, and future generation bias.

## Canonical rule

Every meaningful consequence must produce either:

```text
WorldstateDeltaPacket
```

or:

```text
DiagnosticNoOp
```

No meaningful event should silently disappear from the engine.

## Authority boundary

The ASH Cosmological Model is the upstream foundation for YWE systems. The ASH Pattern System is a YWE component that provides diagnostics, recovery, containment, conformance, pattern integrity, code resilience, and patch/update stability. Worldstate deltas record YWE game-world consequences; they do not redefine cosmology and do not mutate ASH Pattern System canonical behavior.

## Delta scopes

A worldstate delta must identify one or more truth scopes:

```text
base_world_truth
shared_world_truth
leaf_branch_truth
player_perception
mythic_interpretation
prophetic_pressure
faction_claim
host_materialization
diagnostic_noop
```

## Consequence classes

A worldstate delta must classify what changed:

```text
shared_world_truth_change
leaf_branch_truth_change
location_state_change
location_access_change
perception_overlay_change
myth_pressure_change
prophecy_pressure_change
faction_claim_change
npc_relationship_change
artifact_binding_change
creature_ecology_change
ability_pressure_change
player_state_reference
future_generation_bias_update
diagnostic_noop
```

## Required provenance

A meaningful delta should include references to applicable inputs:

```text
player_action_trace_ref
branch_event_ref
leaf_branch_reality_ref
player_state_snapshot_ref
location_state_ref
location_resolution_context_ref
ash_pattern_diagnostic_ref
source_cosmology_refs
```

## Forbidden behaviors

```text
changing shared truth without a delta
recording branch-specific truth as base ontology
letting perception rewrite shared truth
letting myth rewrite history without delta evidence
letting prophecy guarantee a scripted future
letting faction claim become truth automatically
feature engines mutating consequence state without a packet
```

## Output relationship

Worldstate deltas may feed:

```text
LocationStateRecord
LocationBranchOverlay
FutureGenerationBiasUpdate
PlayerStateUpdatePacket
Quest eligibility
NPC eligibility
Lore visibility
Myth seed candidacy
Prophecy pressure
```

Phase 11 records eligibility and bias only. Phase 12 consumes these outputs to generate quest, NPC, and lore content.
