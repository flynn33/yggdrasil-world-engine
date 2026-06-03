# Companion / Reward Integration Map

## Purpose

Define how Quest Reward Resolver output can affect companion-related state without violating companion canon.

## Raven Companion Reward Effects

Allowed Raven Companion deltas:

```text
ancestral_memory_signal_added
quest_signal_memory_recorded
threshold_recognition_updated
lore_recovery_signal_added
bloodline_resonance_interpretation_updated
raven_commentary_state_updated
```

Forbidden Raven Companion deltas:

```text
raven_removed_by_default
raven_replaced_by_generic_pet
raven_death_by_standard_companion_rule
raven_absent_without_story_state
```

## Wolf Manifestation Reward Effects

Allowed Wolf deltas:

```text
manifestation_trigger_added
manifestation_duration_extended
manifestation_condition_satisfied
wolf_resonance_summary_updated
wolf_guidance_memory_recorded
wolf_decoherence_recovery_signal_added
```

Forbidden Wolf deltas:

```text
wolf_added_as_permanent_default_party_member
wolf_removed_as_morality_punishment
white_wolf_good_dark_wolf_evil_score_changed
wolf_death_as_standard_pet_loss
```

## Quest Reward Routing

```text
QuestRewardResolutionPacket
  -> reward_outputs
    -> player_state_update_refs
    -> companion_state_delta_refs
    -> ability_pressure_update_refs
    -> worldstate_delta_refs
    -> location_mutation_refs
    -> myth_signal_refs
    -> prophecy_pressure_refs
    -> faction_social_signal_refs
    -> future_generation_bias_refs

ConsequenceResolutionPacket
  -> routes[]
    -> route_type
    -> target_ref
```
