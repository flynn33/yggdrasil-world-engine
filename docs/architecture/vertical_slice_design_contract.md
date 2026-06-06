# Vertical Slice Design Contract

Status: `phase_16_recovery`
Phase: `16`
Applies to: game-layer vertical-slice design artifacts.


## Source-of-Truth Stack

Use this hierarchy for every Phase 16 artifact:

```text
ASH Model of the Universe
  -> mathematical / ontological foundation of the Yggdrasil World Engine simulation layer

Yggdrasil World Engine
  -> agnostic engine framework and modular simulation architecture

ASH Pattern System
  -> YWE component for pattern integrity, diagnostics, recovery, containment,
     conformance, code resilience, update safety, and patch stability

Where Ravens Wait: Eternal Reckoning
  -> game / narrative layer and first flagship implementation
```

The engine cosmology is a framework foundation, not a fixed setting bible. The Phase 16 Ravenfall Gate vertical slice is game-layer content for **Where Ravens Wait: Eternal Reckoning** that validates YWE engine systems without converting YWE itself into a single fixed setting.

The White Wolf and Dark Wolf are complementary opposites, not good and evil. They are physical companion presences that walk with the player, appear in visions, assist in quests and combat, cannot truly die, and may temporarily decohere before returning.


## Purpose

A vertical slice is a controlled game-layer validation package that proves multiple engine systems can work together in a concrete player-facing scenario.

For Phase 16, the vertical slice is:

```text
Where Ravens Wait: Eternal Reckoning
  -> Ravenfall Gate
    -> The Buried Oath at Ravenfall Gate
```

## Required properties

A YWE vertical slice must define:

```text
location anchor
quest anchor
player decision set
branch outcomes
worldstate deltas
location mutations
wolf companion involvement
ability usage
quest reward resolution
NPC and lore eligibility
artifact and creature eligibility
myth seed and prophecy pressure
future generation bias
playtest trace scenarios
acceptance matrix
```

## Boundary

A vertical slice may include game-specific names and narrative context, but it may not convert the engine into a fixed setting. It is an implementation example, not the whole engine.

## Forbidden

```text
platform-specific runtime implementation
scripted-only future
static-only location model
static branch-map shortcut
generic random quest package
wolf-as-score interface
```
