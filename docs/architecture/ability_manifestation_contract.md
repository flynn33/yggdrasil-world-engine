# Ability Manifestation Contract

Ability manifestation describes how an eligible or unlocked ability appears in play.

## Manifestation modes

```text
internal_sense
vision
wolf_companion_action
combat_move
quest_interaction
location_threshold_effect
perception_overlay
artifact_channel
mythic_echo
prophetic_mark
```

## Materialization boundary

The host runtime may animate, render, play audio, or simulate a manifestation. It may not author the underlying ability truth.

## Required manifestation proof

A manifestation must reference:

```text
AbilityManifest
AbilityUseContext
source_refs
player_state_ref
branch_ref
consequence_policy
```
