# factions Data Domain

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: canonical faction topology baseline

## Purpose

This domain holds canonical social-topology state surfaces for YWE. It exists
so faction structure, legitimacy, claims, reforms, succession, and inter-group
relations remain stable shared truth for downstream systems.

## Current canonical asset

- `faction_topology_state_schema.yaml`

## Planned companion assets

- `faction_registry.yaml`
- `claim_registry.yaml`

## Primary consumers

- `core/narrative_engine/worldstate_delta_rules.yaml`
- `core/narrative_engine/npc_synthesis_rules.yaml`
- `modules/quest_engine/quest_chain_templates.yaml`
- `modules/myth_engine/myth_emergence_rules.yaml`
- `modules/prophecy_engine/prophecy_activation_rules.yaml`
- `core/perception_engine`

## Invariants

- faction topology is relational world structure, not flavor-only lore
- legitimacy, claims, schism, and succession must remain first-class state
- myth, prophecy, and perception may bias faction reading without rewriting core topology truth
- Forsetti governs activation; YWE governs truth
