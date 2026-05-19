# Location Mutation Rule Contract

## Purpose

A LocationMutationRule defines how a location transitions from one state to another in response to player action, worldstate deltas, branch reality, and cosmological context.

## Mutation rule structure

```text
rule_id
location_id
source_phase
target_phase
trigger
required_context
truth_scope
preconditions
effects
forbidden_effects
required_provenance
output_packets
fallback_behavior
```

## Required context categories

```text
player_action_trace
branch_event
player_runtime_state
leaf_branch_reality
location_state
worldstate_delta_history
plane_pressure
wolf_resonance
bloodline_resonance
myth_pressure
prophecy_pressure
faction_claims
ASP diagnostics
```

## Effects

Effects may include:

```text
location phase change
location access change
visibility change
branch overlay update
shared truth delta
leaf branch truth delta
perception overlay change
myth pressure update
prophecy pressure update
future generation bias update
```

## Forbidden effects

```text
mutating base ontology
writing Phase 12 content directly
rewriting player state without PlayerStateUpdatePacket
turning faction belief into truth without validation
making prophecy a guaranteed scripted future
marking perception-only changes as shared truth
```

## Fallback

If conditions are partially met or diagnostics fail, emit DiagnosticNoOp or a contained/deferred mutation record. Do not silently discard the attempted mutation.
