# factions Schema Notes

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: canonical schema baseline

## Purpose

Tracks the validation and interpretation boundaries for faction-topology data in
the canonical YWE truth layer.

## Current canonical schema

- `faction_topology_state_schema.yaml`

## Validation expectations

- the schema must remain at `data/factions/faction_topology_state_schema.yaml`
- `meta.system` must remain `faction_topology_state`
- the file must keep the `FactionTopologyState`, `FactionNode`, `FactionEdge`,
  `ClaimRecord`, `ReformCurrent`, and `SuccessionTrack` structures
- claim pressure, legitimacy, reform, schism, and succession must stay modeled
  as explicit state rather than being flattened into reputation only

## Boundary notes

- faction topology is downstream of world truth and worldstate consequence
- topology changes may feed myth, prophecy, quest, NPC, and perception systems
- topology must not rewrite cosmology, realm ontology, or core shared-world truth
