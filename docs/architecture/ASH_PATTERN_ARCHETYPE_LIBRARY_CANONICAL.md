# YWE Pattern Archetype Extension Library — Canonical Extension Specification
## Downstream interpretation profile constrained by the pinned ASH dependency

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: canonical YWE extension-profile specification
Authority: YWE-owned downstream mapping constrained by pinned ASH symbolic grammar
Replaces as authority: `ASH_PATTERN_ARCHETYPE_LIBRARY_V0_2.md`
Retains as historical context only: prior design-summary text versions

---

# 1. Purpose

This document defines the canonical architecture, within the optional YWE
extension-profile scope, for the YWE Pattern Archetype Library.

It maps symbolic input from the upstream grammar owned by the ASH Cosmological
Model into YWE-owned interpretation records used before quest, NPC, myth,
prophecy, artifact, creature, or perception-layer manifestation. It does not
add to or redefine the upstream grammar. [YWE-REQ-0009]

This file exists to answer these questions cleanly:

- what a YWE extension archetype is
- what archetype families exist
- what fields every archetype record must define
- what relationships between archetypes are allowed
- how archetypes may influence downstream systems
- what archetypes must never be treated as

This document is **not** a exchange diary, progress memo, or conversational
summary.

---

# 2. Authority rule

For repository and implementation purposes:

- this file is canonical only for the optional **YWE extension-profile
  mapping**; it is not an upstream ASH specification or a separate owner of
  symbolic grammar
- family-specific YAML registries under `data/pattern_archetypes/` are the
  corresponding YWE-owned machine-readable extension mappings
- quest archetypes under `data/quest_archetypes/` are downstream YWE extension
  mappings and cannot add to or redefine upstream symbolic grammar
- the pinned ASH dependency constrains the symbolic inputs consumed by these
  mappings, but does not own the downstream YWE mapping records
- this file and every artifact under `data/pattern_archetypes/` are explicitly
  excluded from the upstream dependency identity in
  `data/governance/ash_dependency_identity.json`; only the dependency paths
  enumerated by that identity contribute to its digest [YWE-REQ-0010]
- the older `ASH_PATTERN_ARCHETYPE_LIBRARY_V0_2.md` should be preserved only as
  historical context unless its contents are explicitly migrated into canonical
  fields here

If historical prose conflicts with this document, this document controls only
within the YWE extension-profile scope. It cannot override the pinned ASH
dependency, YWE Core, or a declared game profile.

---

# 3. Core design law

Generation using this YWE extension profile must follow this order:

```text
ASH State
  -> Pattern Detection
  -> Archetype Evaluation
  -> Narrative Interpretation
  -> Manifestation
  -> Consequence
  -> Future Pattern Pressure
```

The archetype library therefore does **not** directly generate content or
define upstream symbolic meaning. It defines deterministic downstream mapping
vocabulary from which YWE content can be derived.

---

# 4. What an archetype is

A YWE extension archetype is a downstream mapping record that interprets a
symbolic pattern shape supplied under the pinned ASH grammar for use within
YWE's cosmology-driven narrative simulation.

An archetype is not merely a trope label.
It is a structured meaning unit that can:

- describe pressure
- describe relationship to truth
- bias realm relevance
- bias interpretation
- bias manifestation suitability
- bias consequence form
- bias mythic or prophetic residue

An archetype may describe:

- a character mode
- a quest pressure shape
- a region meaning profile
- a faction behavioral logic
- a transformation path
- an event pressure type
- a cluster of reinforcing patterns

---

# 5. Archetype families

This YWE extension profile defines these families as canonical within its own
scope.

## A. Character archetypes
Used for people, role-bearers, recurring NPC identities, and player-facing
symbolic mirrors.

Initial canonical character set:
- `char_seeker`
- `char_guardian`
- `char_exile`
- `char_builder`
- `char_judge`
- `char_weaver`
- `char_harbinger`
- `char_sovereign`
- `char_trickster`

## B. Quest archetypes
Used for quest shape and pressure logic.
These define why the quest exists and what kind of pressure it exerts, rather
than surface objectives alone.

## C. Region archetypes
Used for place meaning, local resonance, experiential bias, and symbolic terrain
relevance.

## D. Faction archetypes
Used for collective motive logic, legitimacy pressure, doctrine style, and group
behavior.

## E. Transformation archetypes
Used for becoming, corruption, awakening, reversal, sacrifice, transmutation,
and identity transition.

## F. Event archetypes
Used for crossings, ruptures, revelations, omens, sieges, returns, awakenings,
and other meaningful happening-shapes.

## G. Pattern clusters
Used for compound pressures made from multiple compatible archetypes.
Clusters are not freeform moodboards. They are explicit multi-archetype
configurations with defined combined significance.

---

# 6. Character archetype meanings

These baseline definitions are canonical extension-profile starting points for
the character family.

## `char_seeker`
Meaning pressure centered on pursuit, hidden truth, longing, discovery,
threshold-crossing, and incomplete understanding.

## `char_guardian`
Meaning pressure centered on protection, containment, stewardship, warding,
burden-bearing, and controlled access.

## `char_exile`
Meaning pressure centered on displacement, estrangement, severed belonging,
misfit survival, and return-or-refusal tension.

## `char_builder`
Meaning pressure centered on making, restoration, order-shaping, craft,
institution, repair, and durable structure.

## `char_judge`
Meaning pressure centered on discernment, weighing, revelation through testing,
boundary enforcement, reckoning, and consequence.

## `char_weaver`
Meaning pressure centered on interconnection, hidden relation, thread-binding,
meaning assembly, and subtle influence.

## `char_harbinger`
Meaning pressure centered on warning, approach, omen, transition, dawning fate,
and signals of emerging change.

## `char_sovereign`
Meaning pressure centered on rule, responsibility, legitimacy, command,
inheritance, and the cost of central authority.

## `char_trickster`
Meaning pressure centered on inversion, exposure through disruption, adaptive
subversion, loophole movement, and destabilizing revelation.

---

# 7. Archetype record contract

Every archetype record in machine-readable form must contain the following
minimum fields.

```yaml
id: string
family: character | quest | region | faction | transformation | event | cluster
name: string
summary: string
symbolic_function: [string]
truth_modes: [string]
shadow_modes: [string]
realm_bias: [string]
wolf_bias:
  white: float
  dark: float
player_phase_bias: [string]
compatible_with: [string]
friction_with: [string]
contradicts: [string]
downstream_affinities:
  npc: [string]
  quest: [string]
  myth: [string]
  prophecy: [string]
  artifact: [string]
  creature: [string]
manifestation_hints: [string]
invariant_notes: [string]
status: canonical | provisional | deprecated  # within the YWE extension profile
```

## Field meaning rules

### `symbolic_function`
Describes what kind of meaning pressure the archetype contributes.

### `truth_modes`
Describes lawful forms of truth revelation associated with the archetype.

### `shadow_modes`
Describes lawful distortion, corruption, or destructive expression associated
with the archetype.

### `realm_bias`
Describes which realms naturally resonate with the archetype.
This is a weighting signal, not a hard exclusivity lock.

### `wolf_bias`
Describes how the archetype tends to resonate with White Wolf / Dark Wolf
informational pressure.
This is not morality.

### `player_phase_bias`
Describes which player-origin phases are especially compatible with the
archetype.

### `compatible_with`
Archetypes that reinforce or productively combine with this one.

### `friction_with`
Archetypes that can combine, but generate tension or contradiction that must be
handled deliberately.

### `contradicts`
Archetypes that should not be combined casually because they collapse coherence
unless an explicit contradiction design is intended.

### `downstream_affinities`
Explicit hints for downstream consumption.
These are guidance weights, not permission to bypass evaluation constrained by
the pinned ASH dependency.

---

# 8. Relationship semantics

Archetype relationships use three modes canonical within this YWE extension
profile.

## Compatibility
The pair reinforces each other and tends to produce coherent pressure.

## Friction
The pair can coexist but produces tension, instability, cost, paradox, or split
interpretation.

## Contradiction
The pair should be treated as structurally unstable unless a higher-order design
intentionally frames the contradiction.

Contradiction is allowed as a design tool.
It is not allowed as accidental noise.

---

# 9. Cluster rules

Pattern clusters must satisfy all of the following:

- include at least two canonical archetypes
- define a combined symbolic summary
- define why the combination is lawful
- define what downstream systems the cluster should influence
- declare any contradiction risk explicitly
- specify whether the cluster is stable, unstable, cyclical, or threshold-based

A cluster must not exist merely because several archetypes sound cool together.

---

# 10. Downstream usage law

The archetype library influences downstream systems in these ways.

## Narrative engine
Consumes archetype pressure to decide active narrative direction.

## NPC synthesis
Uses archetypes to shape motive, truth function, shadow risk, relationship
pressure, and transformation potential.

## Quest engine
Uses archetypes to select chain type, pressure curve, threshold style,
consequence bias, and resolution residue.

## Myth engine
Uses archetypes to bias what events become memorable, retold, sanctified,
feared, or legitimized.

## Prophecy engine
Uses archetypes to bias which future pressures become legible as omens or
attractors.

## Artifact engine
Uses archetypes to derive symbolic object meaning, resonance hooks, and risk.

## Creature engine
Uses archetypes to derive meaningful living presences and encounter symbolism.

## Perception engine
May use archetypes to alter how truths are surfaced, obscured, or interpreted,
without rewriting shared-world fact.

---

# 11. Forbidden interpretations

The YWE pattern-archetype extension library must never be treated as:

- a random trope bag
- a flavor-only writing aid
- a replacement for cosmology truth
- a quest generator by itself
- a morality alignment table
- a class-selection system
- a lore dump detached from runtime use
- a generic content taxonomy with no symbolic pressure semantics

---

# 12. Invariants

## Invariant 1
All meaningful generation remains downstream of ASH Pattern Detection.

## Invariant 2
Archetypes bias meaning; they do not hard-script destiny.

## Invariant 3
Realm bias is weighted relevance, not exclusive ownership.

## Invariant 4
White Wolf / Dark Wolf bias is informational pressure, not good/evil judgment.

## Invariant 5
Contradiction must be designed, not accidental.

## Invariant 6
Downstream systems may consume archetype outputs, but may not redefine their
canonical meaning locally.

## Invariant 7
Historical notes, conversation summaries, and exchange files are not canonical
unless explicitly migrated into this specification or its registries.

---

# 13. Repository placement

Canonical YWE extension-profile placement:

```text
docs/architecture/ASH_PATTERN_ARCHETYPE_LIBRARY_CANONICAL.md
```

Machine-readable companions:

```text
data/pattern_archetypes/ash_pattern_registry_schema.yaml
data/pattern_archetypes/*_archetypes.yaml
data/pattern_archetypes/pattern_clusters.yaml
data/quest_archetypes/quest_archetypes.yaml
```

Historical prior exchange:

```text
docs/architecture/ASH_PATTERN_ARCHETYPE_LIBRARY_V0_2.md
```

---

# 14. Migration rule

Repository maintainers should treat the older `ASH_PATTERN_ARCHETYPE_LIBRARY_V0_2.md` as one of
these:

- historical context to preserve
- a source to mine for definitions that can be normalized into canonical fields
- not the final architecture authority

Repository maintainers should not block repository creation because the earlier file reads like a
summary.
Repository maintainers should instead create this normalized canonical file and route historical
content to the history folder.

---

# 15. Final statement

The YWE Pattern Archetype Library is a downstream, YWE-owned extension mapping
constrained by the symbolic grammar foundation owned by the ASH Cosmological
Model. It is excluded from upstream ASH dependency identity and cannot alter
that identity or grammar. Clear extension mappings give downstream systems a
stable interpretation spine without claiming upstream authority.
