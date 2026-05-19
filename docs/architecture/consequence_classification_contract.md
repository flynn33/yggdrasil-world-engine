# Consequence Classification Contract

## Purpose

Consequence classification gives every worldstate delta a readable, auditable type.

## Classes

```text
shared_world_truth_change
leaf_branch_truth_change
location_state_change
location_access_change
perception_overlay_change
myth_pressure_change
prophecy_pressure_change
faction_claim_change
npc_relationship_change
artifact_binding_change
creature_ecology_change
ability_pressure_change
player_state_reference
future_generation_bias_update
diagnostic_noop
```

## Rules

A delta may contain multiple classifications if the consequence spans systems.

Examples:

```text
Reveal buried oath:
  shared_world_truth_change
  location_state_change
  myth_pressure_change
  future_generation_bias_update

Conceal buried oath:
  leaf_branch_truth_change
  location_access_change
  faction_claim_change
  future_generation_bias_update

Study buried oath without acting:
  player_perception
  diagnostic_noop or deferred future_generation_bias_update
```

## Rejection

Reject deltas whose classification contradicts truth scope. Example: a `player_perception` truth scope should not contain `shared_world_truth_change` unless a separate delta proves the shared truth changed.
