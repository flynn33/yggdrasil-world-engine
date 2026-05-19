# Future Generation Bias Contract

## Purpose

FutureGenerationBiasUpdate records how consequences affect future eligibility and weighting for generated content without generating that content directly.

## Bias is not content

A bias update may influence future systems. It must not directly emit quests, NPCs, lore, artifacts, creatures, myths, prophecies, or abilities.

## Bias targets

```text
quest_eligibility
npc_eligibility
lore_visibility
artifact_eligibility
creature_ecology_pressure
myth_seed_likelihood
prophecy_pressure
location_access
ability_pressure
wolf_manifestation_hooks
bloodline_echo_likelihood
plane_pressure
faction_attention
```

## Required references

```text
source_worldstate_delta_refs
source_location_state_ref
source_location_branch_overlay_ref
source_player_state_snapshot_ref
source_branch_event_ref
source_cosmology_refs
ash_pattern_diagnostic_ref
```

## Guardrail

If a bias update materializes content directly, reject it. Phase 12+ systems may consume the bias, but Phase 11 only records it.
