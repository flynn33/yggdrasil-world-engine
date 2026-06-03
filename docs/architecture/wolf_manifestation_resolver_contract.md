# Wolf Manifestation Resolver Contract

## Purpose

Define criteria, duration, and traceability for White Wolf and Dark Wolf presence.

## Core Rule

The wolves are conditional companion manifestations. They are not constantly traveling with the player by default.

## Manifestation Event

A wolf manifestation event must define:

```text
manifestation_event_id
manifesting_companions
trigger type
criteria met
duration type
start condition
end condition
allowed functions
dismissal condition
source refs
forbidden interpretations
```

## Valid Durations

```text
single_scene
temporary_time_window
combat_event
quest_step
entire_quest_chain
vision_or_dream_sequence
threshold_crossing
```

## Valid Trigger Types

```text
quest_chain_requirement
quest_step_requirement
branch_threshold_crossed
location_threshold_state
wolf_resonance_condition
myth_pressure
prophecy_pressure
ability_unlock_requirement
combat_intervention_requirement
vision_or_dream_trigger
```

## Required Forbidden Interpretations

Every wolf manifestation event must explicitly reject:

```text
morality_meter
good_vs_evil_binary
default_party_member
generic_pet_system
permanent_wolf_loss
```

## Ravenfall Gate Correction

Future Ravenfall Gate traces must use this corrected loop:

```text
Player enters Ravenfall Gate
  -> Raven Companion is present by default
  -> wolves manifest only if Ravenfall Gate / Buried Oath criteria are met
```
