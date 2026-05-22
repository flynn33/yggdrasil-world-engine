# Quest Reward Worldstate and Location Integration Contract

Quest rewards must determine whether a resolution changes the shared world,
the player branch, a location state, or only interpretation/perception.

## Location updates

```text
location_phase
threshold_status
access_state
active_plane_pressure
active_npc_eligibility
active_quest_eligibility
artifact_pressure
creature_pressure
mythic_status
prophecy_charge
future_generation_bias_refs
```

## Worldstate rule

If shared world truth changes, emit a WorldstateDeltaPacket. If only the player
branch changes, emit branch/location overlay updates with the correct truth scope.
