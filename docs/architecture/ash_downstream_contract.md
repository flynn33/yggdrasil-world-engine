# ASH Downstream Contract
## Consumption rules for systems that read ASH archetypes

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: canonical contract

---

# 1. Purpose

This document defines how downstream YWE systems may consume ASH archetypes
without locally redefining them.

It exists to stop the same symbolic logic from being rewritten in:
- quest logic
- NPC logic
- myth logic
- prophecy logic
- artifact logic
- creature logic
- perception logic

---

# 2. Global rule

Downstream systems may **consume** archetype outputs.
They may **not** become independent authorities on archetype meaning.

ASH owns symbolic grammar.
Other systems own specialized manifestation of that grammar.

---

# 3. Allowed downstream use

## NPC synthesis
May use archetypes to determine:
- motive bias
- truth function
- shadow risk
- relationship stance
- transformation potential

Must not invent new canonical meanings for archetypes.

## Quest engine
May use archetypes to determine:
- quest chain pressure curve
- threshold form
- reversal form
- cost profile
- residue shape

Must not bypass narrative_engine intent selection.

## Myth engine
May use archetypes to determine:
- what becomes memorable
- what becomes sainted, feared, taboo, or legitimized
- faction-specific retelling emphasis

Must not treat myth as the source of archetype truth.

## Prophecy engine
May use archetypes to determine:
- omen style
- attractor profile
- activation tendency
- interpretation volatility

Must not convert archetype bias into deterministic fate.

## Artifact engine
May use archetypes to determine:
- symbolic object role
- resonance hooks
- costs and risks
- quest integration hooks

Must not generate loot logic detached from archetype meaning.

## Creature engine
May use archetypes to determine:
- encounter symbolism
- creature role
- omen presence
- relational or territorial meaning

Must not create standalone ecology divorced from ASH state.

## Perception engine
May use archetypes to determine:
- what becomes legible
- what is concealed or emphasized
- which interpretation variants become visible to a player

Must not rewrite shared-world truth.

---

# 4. Consumption packet expectation

Codex should prefer a normalized packet shape whenever a downstream system reads
ASH outputs.

Suggested shared packet:

```yaml
ArchetypeEvaluationPacket:
  dominant_archetypes: [string]
  secondary_archetypes: [string]
  friction_pairs: [string]
  contradiction_pairs: [string]
  realm_pressure_map: {}
  wolf_pressure_map: {}
  player_phase_map: {}
  downstream_affinity_hints: {}
```

This packet is a transport shape.
It is not a replacement for the underlying registry.

---

# 5. Hard boundaries

Downstream systems must never:

- rename canonical archetypes locally
- quietly alter canonical summaries
- define incompatible local field shapes without an adapter layer
- claim exclusive ownership over a shared archetype
- reduce archetypes to flavor-only labels
- convert archetype bias into hard class locks or morality rails

---

# 6. Codex implementation note

When Codex encounters a downstream rule file that relies on archetype language,
it should prefer references to canonical IDs like `char_guardian` rather than
rewriting prose meanings inside each subsystem.

If a subsystem needs local specialization, Codex should use:
- affinity mappings
- role mappings
- manifestation hints
- local weighting tables

It should not clone the canonical definitions into every file.

---

# 7. Final rule

ASH defines symbolic truth.
Downstream systems define what that truth becomes in play.
The repo stays coherent only if that boundary is kept clean.
