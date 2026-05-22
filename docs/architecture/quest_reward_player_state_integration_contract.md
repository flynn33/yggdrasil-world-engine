# Quest Reward Player State Integration Contract

Quest reward resolution may update player state through approved update packets.

## Potential updates

```text
quest_history
major_choice_log
player_action_trace_refs
current_leaf_branch_ref
celestial_identity_pressure
plane_attunement_state
lineage_resonance_state
wolf_companion_state
ability_unlock_pressure
ability_state
perception_state
memory_records
artifact_bindings
NPC relationships
faction standing
myth participation
prophecy exposure
```

## Rule

The Quest Reward Resolver must not directly mutate player state without a
PlayerStateUpdatePacket or equivalent accepted schema.
