# Quest Reward Consequence Pipeline Contract

## Pipeline

```text
QuestResolutionPayload
  -> classify completion mode
  -> gather current player / branch / world / location context
  -> validate source provenance
  -> classify truth scope
  -> build consequence bundle
  -> emit reward deltas
  -> update future generation bias
  -> write resolution report
```

## Required RewardDeltaBundle.delta_types values

```text
player_state
branch
worldstate
location
wolf
ability
plane_attunement
lineage
perception
myth_seed
prophecy_pressure
npc_relationship
faction
artifact_eligibility
creature_eligibility
future_generation_bias
```

## Diagnostic no-op

A DiagnosticNoOp is valid only when the resolver confirms that no meaningful
state change should be emitted. It must include the reason and context.
