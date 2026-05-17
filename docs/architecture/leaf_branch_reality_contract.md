# Leaf Branch Reality Contract

## Purpose

This contract defines runtime-generated player branch realities.

A leaf branch reality is a unique player-specific reality state created from meaningful player decisions, plane attunement, bloodline resonance, wolf resonance, perception state, location state, worldstate deltas, and cosmological law.

## Core rule

```text
Leaf branches are not pre-generated.
Leaf branches are created at runtime by meaningful player branch events.
```

## Authority stack

```text
ASH Cosmological Model
  -> defines branching choice realization and existence rules

Yggdrasil World Engine
  -> resolves branch reality as game-engine state

ASH Pattern System component
  -> supplies diagnostics, conformance, recovery, containment, and stability checks

Where Ravens Wait: Eternal Reckoning
  -> materializes branch consequences as narrative/game content
```

## Branch creation

A branch is created when a BranchEvent qualifies as a meaningful conscious choice.

Qualifying events may include:

```text
quest resolution
truth revealed or concealed
oath made, broken, or bound
bloodline awakening
wolf resonance shift
plane attunement threshold
artifact binding
life/death consequence
Shadow/Void/Celestial threshold event
location threshold crossing
```

Non-qualifying events include routine movement, ordinary loot pickup, repeated menu choices, or actions with no significant consequence.

## Branch inheritance

Each leaf branch must record:

```text
base_world_ref
parent_branch_ref, if any
branch_event_ref
branch_generation_context_ref
worldstate_delta_refs
future_generation_bias_refs
```

## Branch divergence

A leaf branch may diverge by changing:

```text
location state
NPC availability
quest eligibility
lore visibility
artifact eligibility
creature pressure
myth seed status
prophecy pressure
perception overlays
plane pressure
faction claims
future generation bias
```

A leaf branch may not change:

```text
ASH Cosmological Model
nine-plane ontology
ASH Pattern System canonical integrity rules
platform implementation boundaries
```

## Persistence model

The engine should persist compact branch state, not entire pregenerated worlds.

Persist:

```text
branch id
source branch event
generation context
worldstate deltas
materialized manifest refs
future generation bias
replay/regeneration provenance
```

Do not persist:

```text
massive pregenerated alternate reality trees
unbounded authored branch catalogs
platform-specific generated assets as source truth
```
