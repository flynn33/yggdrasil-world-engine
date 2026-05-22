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

## Required consequence classes

```text
player_state_delta
branch_reality_delta
worldstate_delta
location_state_delta
wolf_companion_delta
plane_attunement_delta
lineage_resonance_delta
ability_pressure_delta
perception_overlay_delta
myth_seed_delta
prophecy_pressure_delta
npc_relationship_delta
faction_state_delta
artifact_eligibility_delta
creature_eligibility_delta
future_generation_bias_delta
```

## Diagnostic no-op

A DiagnosticNoOp is valid only when the resolver confirms that no meaningful
state change should be emitted. It must include the reason and context.
