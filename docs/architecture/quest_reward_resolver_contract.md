# Quest Reward Resolver Contract

## Purpose

The Quest Reward Resolver converts quest resolution into auditable consequence packets.

It is the bridge between player choice and the world remembering what happened.

## Core Law

```text
Quest completion does not mutate systems ad hoc.
Quest completion emits a QuestRewardResolutionPacket.
QuestRewardResolutionPacket references a ConsequenceResolutionPacket.
ConsequenceResolutionPacket routes changes to downstream systems by refs.
```

## Inputs

```text
quest_ref
quest_resolution_payload
player_runtime_state_ref
leaf_branch_reality_state_ref
worldstate_context_ref
location_state_ref
companion_presence_state_ref
ability_state_refs
quest_source_refs
```

## Outputs

```text
quest_reward_resolution_packet
consequence_resolution_packet
player_state_update_refs
companion_state_delta_refs
ability_pressure_update_refs
worldstate_delta_refs
location_mutation_refs
myth_signal_refs
prophecy_pressure_refs
faction_or_social_signal_refs
future_generation_bias_refs
validation_status
```

## Resolution Classes

```text
reveal
conceal
bind
break
heal
weaponize
witness
study_noop
refuse
sacrifice
restore
```

## Reward Is Not Loot Only

Quest reward may include:

```text
knowledge
memory
branch access
location mutation
companion resonance
ability pressure
artifact binding opportunity
myth emergence
prophecy pressure
faction/social reaction
future generation bias
```

## Required Provenance

Every consequence-bearing reward must include source refs to:

```text
quest resolution
branch event
player action trace
ASH/YWE interpretation packet or diagnostic refs where applicable
```

## Invalid Case

A quest reward packet with no consequence packet is invalid.
