# Player Runtime State Contract

## Status

```text
phase: 10
status: accepted_for_phase_10
scope: engine_agnostic_contract
```

## Purpose

The Player Runtime State defines the persistent, engine-agnostic state of the player inside the Yggdrasil World Engine.

It is the shared state spine read by later systems and updated through controlled packets. It records the player's current leaf branch reality, identity state, branch history, resonance pressures, action memory, progression signals, and ASH Pattern System resilience references.

## Authority hierarchy

```text
Where Ravens Wait: Eternal Reckoning
  = game / narrative layer

Yggdrasil World Engine
  = agnostic game engine

ASH Cosmological Model
  = upstream foundation for YWE and its systems

ASH Pattern System component
  = YWE component for diagnostics, pattern integrity, recovery,
    containment, conformance, code resilience, and patch/update stability
```

## Contract statement

The Player Runtime State is not a generic RPG character sheet. It is a cosmology-aware runtime context packet that allows YWE systems to determine what branch reality the player currently occupies, what the player has done, what cosmological pressures are active, what identity fragments have surfaced, and what future generation may lawfully respond to.

## Required responsibilities

Player Runtime State must track:

```text
current_leaf_branch_ref
branch_history_refs
player_agent_state_ref
mortal_identity
celestial_identity_state_ref
plane_attunement_state_ref
bloodline_resonance_state_ref
wolf_resonance_summary_ref
perception_state_refs
ability_pressure_refs
quest_history_refs
player_action_trace_refs
worldstate_delta_refs
location_state_refs
artifact_binding_refs
creature_encounter_refs
npc_relationship_refs
faction_standing_refs
myth_participation_refs
prophecy_pressure_refs
ash_pattern_system_diagnostic_refs
```

## Required boundaries

Player Runtime State may:

- provide generation context;
- record the player's branch history;
- expose resonance and progression signals;
- reference consequence, memory, location, and relationship artifacts;
- be updated by validated PlayerStateUpdatePacket instances.

Player Runtime State may not:

- mutate the base nine-plane ontology;
- replace leaf branch reality state;
- directly materialize quests, NPCs, or locations;
- reveal full celestial identity at character creation;
- treat wolf resonance as morality;
- treat bloodline or plane attunement as static class locks;
- bypass ASH Pattern System diagnostics where resilience/provenance is required.

## Mutation rule

Player Runtime State is mutated only through `PlayerStateUpdatePacket`.

```text
feature system result
  -> proposed PlayerStateUpdatePacket
  -> provenance and diagnostic check
  -> controlled merge into PlayerRuntimeState
```

Direct mutation by feature engines is forbidden.

## Initial state expectation

A new player state should begin as:

```text
mortal_identity: established or generated through character setup
celestial_identity: veiled
current_leaf_branch_ref: initial/base branch or first generated branch
plane_attunement: low or seed-level
bloodline_resonance: seed-level / dormant / unknown
wolf_resonance: latent or balanced seed state
branch_history: empty or initial branch event only
```

## Integration with later phases

Phase 10 prepares for:

```text
Phase 11 — Worldstate and Location Mutation
Phase 12 — Quest / NPC / Lore Generation
Phase 13 — Twin Wolf Companion Engine
Phase 14 — Ability / Power Engine
Phase 15 — Quest Reward Resolver
Phase 16 — Ravenfall Gate Vertical Slice
```

It does not implement those systems.
