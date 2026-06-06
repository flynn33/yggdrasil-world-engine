# Vertical Slice Playtest Trace Contract

Status: `phase_16_recovery`

## Purpose

Defines how a vertical slice proves itself through structured playtest traces without requiring platform-specific runtime implementation.

## Required trace sequence

A playtest trace should record:

```text
initial branch state
initial player runtime state
initial location state
triggering exploration event
quest discovery event
wolf companion presence
NPC/lore/ability cues
player choice
quest reward resolution
worldstate delta or diagnostic no-op
location mutation
branch overlay
future generation bias
post-choice revisitation behavior
```

## Acceptance

A Phase 16 playtest trace is valid if it demonstrates at least one complete path from player discovery to future-generation bias.

The Ravenfall Gate package should include traces for:

```text
Reveal
Conceal
Bind
Study
Weaponize
```
