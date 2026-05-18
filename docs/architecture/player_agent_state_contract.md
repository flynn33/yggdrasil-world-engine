# Player Agent State Contract

## Purpose

The Player Agent State describes the player as a conscious mortal agent inside the YWE runtime cosmology.

It is narrower than Player Runtime State. It focuses on the player's agent identity, current branch participation, action capacity, and provenance references.

## Core concept

```text
PlayerRuntimeState
  contains / references
PlayerAgentState
```

The agent state is the part of player state used by branch events and runtime generation context.

## Required fields

```text
agent_id
agent_kind
mortal_instance_id
current_branch_ref
current_location_ref
current_plane_pressure_ref
self_reference_status
choice_capacity_status
recent_action_trace_refs
branch_event_refs
asp_diagnostic_refs
```

## Agent kinds

Allowed initial values:

```text
player_mortal_instance
player_celestial_projection
player_branch_echo
player_memory_fragment
```

Phase 10 should default to:

```text
player_mortal_instance
```

## Branch participation

Player Agent State must reference the active branch.

It must not duplicate the entire branch state. Branch state belongs to `LeafBranchRealityState`.

## Conscious choice condition

Only meaningful conscious choices create branch events.

Minor movement, UI input, ordinary inventory sorting, or inconsequential interaction should not automatically create branch events.

## Self-reference requirement

Because player agency is tied to consciousness, Player Agent State should include a self-reference status:

```text
stable_self_model
fragmented_self_model
veiled_self_model
challenged_self_model
lost_self_model
```

This supports later systems based on the self-reference axiom.
