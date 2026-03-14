# Authored Override and Tooling Notes

## Purpose

This document defines how authored content, developer tooling, and debug surfaces may interact with the Yggdrasil World Engine (YWE) without violating canonical truth, ASH-first generation, Forsetti governance boundaries, or persistent world consequence rules.

This is a control document, not a content document.

Its purpose is to prevent implementation convenience from silently becoming architecture drift.

---

## Scope

This file governs:

- authored overrides applied to quests, sites, factions, NPC roles, symbolic pressure, and presentation layers
- tooling used by designers, engineers, testers, and AI coding agents
- inspection surfaces used to understand why generation resolved a certain way
- emergency controls used to stabilize content or unblock production

This file does **not** govern:

- canonical cosmology truth
- ASH archetype authority
- realm law
- faction topology schema truth
- perception truth boundaries
- engine-specific editor implementation

---

## Core Principle

Authored control may **shape selection**, **bound variation**, and **pin presentation targets**, but it may not rewrite canonical truth.

Authored intent is a constrained influence layer.
It is never the final source of metaphysical, historical, or structural authority.

---

## Authority Order

When multiple sources disagree, the following precedence order applies:

1. Canonical truth and invariant guardrails
2. Realm mechanics and cosmological law
3. ASH canonical authority and downstream contract
4. Persistent worldstate and validated consequence records
5. Canonical schema surfaces for faction, perception, myth, prophecy, artifact, and creature systems
6. Authored overrides that are compliant with all higher layers
7. Tooling defaults, previews, convenience settings, and debug assists

If a lower layer conflicts with a higher layer, the lower layer must be rejected, downgraded, or surfaced as invalid.

---

## Definition: Authored Override

An **authored override** is a bounded instruction that constrains or guides generation in a specific content context.

Examples:

- pinning a quest to a specific site class
- forcing an NPC to occupy a narrative role slot within allowed ASH constraints
- increasing faction tension pressure in a known region
- requiring a prophecy seed to be visible in a quest chain
- constraining perception variants for a specific player-state band
- locking a narrative event to a specific authored window

An authored override is valid only if it remains subordinate to the authority order above.

---

## Allowed Override Types

### 1. Site Anchoring
Authored content may:

- pin a sequence to a named site
- require a site category such as shrine, ruin, threshold, archive, or court
- constrain site traits such as remoteness, sanctity, faction pressure, or veil thinness

Authored content may not:

- invent site truth that contradicts canon
- rewrite realm classification of a site
- make a site cosmologically impossible

### 2. NPC Role Anchoring
Authored content may:

- pin an NPC to a functional narrative role
- reserve role slots such as witness, guide, oath-holder, rival, claimant, exile, or ritual actor
- constrain social position, faction alignment band, or revelation timing

Authored content may not:

- violate NPC synthesis rules
- force incompatible ASH alignment
- assign impossible memory, bloodline, or myth access states

### 3. Faction Pressure Shaping
Authored content may:

- intensify reform pressure
- foreground schism risk
- elevate succession strain
- force a negotiation, contest, accusation, or alliance attempt into visibility

Authored content may not:

- flatten faction topology into simple moral binaries
- erase legitimacy history
- bypass claim structure, reform state, or covert relation rules

### 4. Quest Path Bounding
Authored content may:

- constrain available quest branches
- pin required symbolic beats
- require ritual, omen, or archive contact points
- reserve one or more revelation thresholds

Authored content may not:

- force outcomes that contradict worldstate persistence
- skip required dependency checks
- convert YWE into a fixed-script linear narrative system

### 5. Myth and Prophecy Visibility Controls
Authored content may:

- require myth fragments to surface
- set minimum prophecy visibility bands
- prefer certain omen classes or symbolic motifs
- reveal one interpretation while keeping others latent

Authored content may not:

- declare myth as fact
- declare prophecy as already fulfilled truth
- overwrite canonical event history

### 6. Perception Presentation Constraints
Authored content may:

- pin a perception presentation family
- constrain overlays by attunement, memory, bloodline, oath, faction state, or realm proximity
- require specific symbolic cues to be perceivable by qualified actors

Authored content may not:

- rewrite shared geography
- change objective worldstate truth
- turn perception overlays into unilateral reality mutation

---

## Forbidden Override Types

The following are prohibited even for internal tools, debug modes, or emergency use:

- rewriting canonical cosmology through authored flags
- forcing realm transitions that violate realm mechanics
- making incompatible ASH patterns coexist without an explicit lawful bridge
- deleting persistent consequence records for convenience
- overriding faction legitimacy, succession, or claims without schema-valid state changes
- forcing myth to become universally accepted truth without social/world mediation
- forcing prophecy to resolve as destiny rather than weighted possibility
- converting perception-only content into global shared state without lawful promotion
- spawning artifacts or creatures as filler outside pattern-derived rules
- using authored content to bypass Forsetti boundary rules or module contracts

---

## Override Strength Bands

Every authored override must declare a strength band.

### Advisory
A soft preference. Generation should try to honor it but may reject it when higher-order truth or compatibility blocks it.

### Strong
A strong constraint. Generation should honor it unless doing so would violate canon, schema, dependency, or persistence rules.

### Hard Lock
A narrow pin used only where authored certainty is required. Hard locks must be explicit, reviewed, and traceable. They may still not violate higher authority layers.

### Emergency Stabilization
A temporary production control for preventing broken states, invalid outputs, or live instability. Must be time-bounded, logged, and reviewed for removal.

---

## Required Metadata for Every Override

Every override record must include:

- `override_id`
- `owner`
- `reason`
- `scope`
- `target_systems`
- `strength_band`
- `start_condition`
- `end_condition` or review condition
- `validation_notes`
- `conflict_policy`
- `audit_visibility`

Recommended fields:

- `linked_ticket`
- `linked_design_doc`
- `playtest_context`
- `expected_side_effects`
- `rollback_plan`

Overrides without traceable metadata should be rejected in authoritative environments.

---

## Conflict Resolution Rules

When an authored override conflicts with generation logic:

1. validate against canonical truth
2. validate against schema constraints
3. validate against worldstate persistence
4. validate against ASH compatibility and downstream contract
5. validate against realm mechanics and perception boundaries
6. either:
   - accept
   - downgrade to advisory
   - reject
   - quarantine for designer review

A tooling surface must expose which rule caused rejection.

---

## Authoring Boundaries by System

### ASH Layer
Allowed:
- pattern emphasis
- archetype weighting within lawful bands
- cluster visibility shaping

Forbidden:
- hand-authoring contradictory archetype truth
- bypassing compatibility matrix rules
- inventing private ASH semantics per quest

### Quest Layer
Allowed:
- branch gating
- role reservation
- site anchoring
- symbolic beat enforcement

Forbidden:
- outcome contradiction with persistent consequence
- authored negation of required pattern logic

### Artifact Layer
Allowed:
- hand-placement of a lawful artifact instance
- authored recovery path
- ritual conditions for access

Forbidden:
- arbitrary loot injection
- artifact meaning detached from pattern origin

### Creature Layer
Allowed:
- encounter framing
- habitat anchoring
- omen relationship shaping

Forbidden:
- filler encounter spawning detached from symbolic and realm conditions
- moral simplification of creature meaning

### Faction Layer
Allowed:
- event emphasis
- negotiation scene activation
- public visibility adjustment

Forbidden:
- rewriting topology history by fiat
- reducing factions to one-dimensional alignment labels

### Perception Layer
Allowed:
- presentation band constraints
- actor qualification rules
- symbolic filter selection

Forbidden:
- rewriting shared truth
- using perception to simulate global canon mutation

### Realm Layer
Allowed:
- threshold timing
- authored site windows
- lawful attunement gating

Forbidden:
- impossible cross-realm movement
- authored violation of realm resistance or boundary law

---

## Tooling Categories

### 1. Inspection Tools
These explain generation state without changing authority.

Examples:
- ASH pattern snapshot viewer
- compatibility trace viewer
- myth pressure inspector
- prophecy weighting inspector
- faction topology state inspector
- worldstate delta inspector
- realm attunement inspector
- perception eligibility inspector

Inspection tools are strongly encouraged.
They reduce guesswork and lower the temptation to use unsafe overrides.

### 2. Authoring Tools
These create or edit lawful constraints.

Examples:
- quest authoring interfaces
- site pinning tools
- override record editors
- event scheduling surfaces
- symbolic beat editors

Authoring tools must validate against canonical schemas before save or publish.

### 3. Validation Tools
These detect drift, contradiction, or invalid data.

Examples:
- schema validation
- glossary term enforcement
- architecture drift tests
- forbidden override scanners
- placeholder artifact completeness checks
- missing source inventory updates

### 4. Emergency Stabilization Tools
These are limited-use controls for production safety.

Examples:
- temporary content quarantine
- invalid output suppression
- event rate throttling
- override disable/rollback
- broken-state containment

Emergency tools must be auditable and must not become hidden permanent behavior.

---

## Required Debug / Explainability Surfaces

The repo and future tooling should support clear inspection of at least the following:

- why a quest template was selected
- which ASH archetypes and clusters were active
- why an NPC role was allowed or rejected
- why a faction event surfaced now
- why a creature or artifact manifestation was allowed
- why a prophecy cue appeared or remained latent
- why a perception overlay was visible to one actor but not another
- what worldstate delta was created, read, or blocked
- which override affected resolution, if any

A future engineer should be able to explain a generated result without reading hidden implementation guesses.

---

## Logging and Audit Rules

All non-advisory overrides must be logged.

At minimum, audit records should capture:

- override identity
- actor or tool that created it
- time of creation and activation
- reason for use
- affected systems
- validation result
- acceptance, downgrade, rejection, or rollback outcome

Emergency overrides require explicit review after activation.

---

## Multiplayer and Shared-State Safety

No authored override may silently create divergent shared truth across players unless divergence is explicitly designated as perception-only and bounded by perception rules.

If authored content creates role-specific visibility differences:

- the shared state must remain consistent
- divergence must be attributable to perception, memory, qualification, or revelation timing
- reconciliation behavior must be defined when actors compare experiences

---

## Live Ops / Iteration Rules

During iteration, authored controls may be used to stabilize content quality, but:

- temporary controls must be labeled temporary
- recurring temporary controls must be reviewed for promotion into canonical rules or rejection
- repeated manual interventions indicate missing system law and should trigger design review

If a team uses the same override pattern repeatedly, that is evidence the architecture is underspecified.

---

## Forbidden Tooling Behaviors

Tooling may not:

- silently auto-correct canon conflicts without surfacing them
- hide contradiction reports to produce “clean” outputs
- promote preview settings into published truth without review
- treat placeholders or missing source documents as canonical authority
- infer architecture from deprecated handoff files when canonical files exist
- bypass validation to make content “just work”

Convenience is not a valid reason to break authority order.

---

## Recommended Repository Companions

This document should be paired with:

- canonical glossary terms
- missing source inventory
- schema integrity tests
- architecture drift tests
- Forsetti compliance tests
- module contract coverage tests
- source completeness tracking

If this document is merged as canon, validation should eventually check for:

- undocumented hard locks
- expired emergency overrides
- missing metadata on override records
- forbidden override categories
- tooling references to deprecated authority files

---

## Acceptance Criteria for Canonical Adoption

This file is ready for canonical use when:

- authored overrides are clearly subordinate to canonical truth
- allowed and forbidden override categories are explicit
- tooling surfaces emphasize inspection and validation over hidden mutation
- multiplayer-safe truth boundaries are preserved
- emergency controls are bounded, auditable, and removable
- future engineers can implement authoring support without converting YWE into a hand-scripted content system

---

## Final Rule

Authored content may guide YWE.
It may never replace YWE.

Tooling may reveal, validate, and safely constrain system behavior.
It may never become an ungoverned back door around canon.
