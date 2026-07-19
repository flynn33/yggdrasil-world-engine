# YWE Design Glossary
## Framework-agnostic terminology reference for Yggdrasil World Engine

Date: 2026-03-13  
Project: Yggdrasil World Engine  
Status: agnostic terminology baseline

---

# 1. Purpose

This glossary defines the canonical design language for YWE.

Its job is to reduce terminology drift across:
- canon design
- symbolic system design
- runtime orchestration
- consequence persistence
- myth and prophecy systems
- repo exchange and implementation planning
- future cross-thread continuation

This is a **design glossary**, not a lore encyclopedia and not a code dictionary.

It defines how terms should be understood inside the YWE design stack.

---

# 2. Usage rule

When a term in this glossary conflicts with a looser everyday meaning, the **glossary meaning wins** for YWE design work.

When a future document introduces a new important term, it should either:
- reuse a term already defined here, or
- add a new glossary entry explicitly

---

# 3. Glossary

## ASH Cosmological Model
The upstream foundation for YWE and its systems.

The ASH Cosmological Model owns the cosmological meaning layer: nine planes of
existence, axioms A1-A6, existence potential Φ, pattern vectors, branching
choice realization, leaf branch realities, wolf attractor logic, bloodline
resonance meaning, symbolic-grammar meaning, and Shadow / Void / Divine Core
roles. YWE consumes this authority; it does not acquire ownership of it.

## Structural Coordinate
One named algebraic position `b0` through `b8` in an ASH State Vector in
`F2^9`.

`ASH Coordinate` is a presentation alias. A Structural Coordinate is not a
named realm, an ordinal, a presentation rank, or a complete state identity.
The WRW realm-anchor projection may associate a named realm with a one-hot
vector for interchange, but that association does not privilege the coordinate
in ASH mathematics.

## ASH Dependency Identity
The machine-verifiable pin for the repository's upstream ASH specification
snapshot.

The current identity is recorded in
`data/governance/ash_dependency_identity.json`. It names the authoritative
source tree, its generated mirror, the digest algorithm, and the aggregate
digest. Repository prose must reference that identity rather than inventing a
second version label.

## ASH State Vector
One complete nine-coordinate value `x = (b0, ..., b8)` in `F2^9`.

All nine Structural Coordinates participate in the vector. A vector determines
one state/vertex identity; a coordinate, Coordinate Index, ordinal, or
presentation order does not. The nine one-hot WRW realm anchors are projection
records, not an exhaustive definition of the 512 possible ASH states or of a
named realm's full meaning.

## ASH Pattern System
A YWE component for diagnostics, pattern integrity, recovery, containment,
resilience, conformance, and update/patch stability.

Earlier planning sometimes used ASH Pattern System as shorthand for the
upstream mathematical layer. That shorthand is superseded by the current
authority stack: ASH Cosmological Model is the upstream foundation for YWE,
while ASH Pattern System is a YWE component that protects and stabilizes engine
systems. It does not own ASH mathematics, base ontology, or symbolic-grammar
meaning.

## Activation
The framework-level act of making a module or subsystem operational in a runtime context.

In YWE design, activation is a **governance concern**, not a core agnostic design concern.
Forsetti governs activation; YWE design defines what the activated system means.

## Adapter
A repository-level bridge that translates YWE outputs into engine-specific realization behavior.

In deeper governance terms, adapters are better understood as **external execution negotiation bridges**, not owners of YWE truth.

## Agnostic Design
Design work expressed independently of implementation language, rendering engine, storage engine, or framework lifecycle.

Agnostic design defines:
- truth
- structure
- meaning
- system boundaries
- allowable relationships

It does not define code-level activation or framework ownership mechanics.

## ASH Model
The cosmological and pattern-interpretation model that underlies meaningful procedural generation in YWE.

In YWE, ASH is not flavor background. It is the lawful origin of meaningful generation pressure.

## ASH Pattern Detection
The process by which current cosmic and symbolic state is interpreted into active patterns.

This is the root of all meaningful procedural generation.
No major content system should bypass it.

## Where Ravens Wait: Eternal Reckoning
The game and narrative layer built on the Yggdrasil World Engine.

Where Ravens Wait: Eternal Reckoning owns player-facing story identity,
specific quests, specific locations, scenes, characters, prose, dialogue, and
content direction. It is the WRW Reference Profile, not the agnostic engine,
and cannot make its game-specific content universal YWE Core truth.

## Yggdrasil World Engine
The agnostic game engine.

Yggdrasil World Engine owns engine-agnostic contracts, runtime systems,
worldstate deltas, feature engine interfaces, host adapter boundaries, and
repository governance. Its mandatory setting-neutral layer is YWE Core. It is
not merely the game title and does not own upstream ASH meaning.


## Archetype
A reusable symbolic pattern category used by the engine to interpret meaning.

Archetypes are not merely storytelling labels. They are part of the machine-usable grammar used for:
- characters
- quests
- regions
- factions
- transformations
- events

## Architect
One of the consciousnesses transformed out of the Dark Star when it collapsed
into the Divine Core and the nine realms stabilized.

Architects are not interchangeable with ordinary celestials, gods, or later
pantheon figures.

## Artifact Engine
A specialized manifestation module responsible for symbolic objects, relics, and item-like mythic outputs.

It is downstream of pattern and narrative logic, not an independent source of meaning.

## Attunement
A measurable form of resonance between a player and a realm, symbolic pressure, site, or related pattern field.

In practice, realm attunement governs lawful access and relevance, not ownership of a realm.

## Authoritative Source
The sole repository path or external dependency identity whose content controls
a declared concern.

An authoritative source may have generated mirrors, indexes, or summaries.
Those derivatives improve access but do not acquire override authority.

## Ontology
The immutable-at-runtime definition of what kinds of entities, states, and
relations may exist under the governing authority. `Base World Ontology` is the
compatibility label for the cosmological substrate governed by upstream ASH.

Ontology constrains runtime state. It is not the current condition of every
entity, site, branch, or player, and it cannot be changed by a worldstate delta,
perception overlay, game profile, or host adapter.

## Bloodline
An inherited pattern of mythic resonance tied to lineage.

Bloodline affects:
- eligibility
- symbolic salience
- prophecy relevance
- myth interpretation
- faction and entity response

Bloodline does **not** hard-lock destiny.

## Coordinate Index
The zero-based integer index `0` through `8` of a Structural Coordinate in an
ASH State Vector.

`Bit Position` and `bit_index` are deprecated compatibility aliases. A
Coordinate Index describes storage or interchange position; it does not
establish an ordinal, presentation order, cosmological priority, or State
Identity.

## Canon
The highest-order design truth that lower systems must not contradict.

Canon includes cosmology, realm ontology, player origin law, wolf law, and other non-negotiable foundations.

## Canonical Term
The single preferred label and definition for one material YWE concept within a
declared scope.

Aliases may route legacy or presentation vocabulary to a canonical term, but
they do not create another definition or state field. Every level-two concept
heading in this glossary has one entry in the canonical term index.

## Canonical Data Domain
A major category of truth the engine must preserve distinctly, such as cosmology, realm ontology, player identity, myth, prophecy, or perception.

The purpose of domain separation is to prevent design drift through truth-mixing.

## Celestial Heritage
The deeper mythic origin or higher-order identity a player may gradually uncover through play.

It is revealed progressively through quests, memory, attunement, mythic consequence, and prophecy pressure.
It is not fully chosen at character creation.

## Coherence
The degree to which generated or designed content remains consistent with canon, symbolic grammar, system boundaries, and current state.

High coherence does not mean simplicity; it means lawful fit.

## Compatibility Matrix
The symbolic compatibility reference that scores resonance, friction, contradiction, or instability between archetypes and related system elements.

It helps prevent random-looking generation and supports lawful composition.

## Consequence
A meaningful outcome that changes future state.

In YWE, consequence should not vanish after local completion. It should feed persistence, memory, myth, prophecy, faction response, perception, or future weighting.

## Compensating Delta
A new append-only state-transition record whose accepted effect changes or
counterbalances a prior reversible Current-State Effect.

It references the prior record and carries ordinary provenance. It does not
edit, delete, reorder, or make the prior event cease to have happened.

## Contradiction
A tension, clash, or mismatch between system elements.

Contradiction is not always an error.
Some contradiction is productive and dramatically useful.
Too much contradiction breaks coherence.

## Creature Engine
A specialized manifestation module responsible for creature generation and creature-linked symbolic/ecological presence.

Like artifact generation, it must remain downstream of pattern and narrative law.

## Cross-Module Dependency
A conceptual relationship in which one engine or subsystem depends on another for truth, interpretation, manifestation, consequence, or feedback weighting.

Dependency does not automatically imply ownership.

## Delta
A discrete persistent state change emitted from meaningful resolution.

A delta may affect a player, NPC, site, faction, myth seed, prophecy weight, or perception state.

## Current State
The result of deterministically folding accepted historical records for a
declared truth scope at a specified point in the event sequence.

Current state may change. The event history from which it is derived remains
append-only, and a later state does not erase the records that produced an
earlier state.

## Current-State Effect
The presently effective result of one or more accepted history records after
they are folded for a declared truth scope.

The effect may be reversible when its domain contract permits. Reversing it
requires a Compensating Delta; the source event and original delta remain in
Event History.

## Dark Wolf
One of the two paired symbiotic wolf forces that emerge with Divine Core
creation.

Dark Wolf is associated with hiddenness, concealment, depth, and the guarding of
what must pass through darkness without being lost to Void.
It is not an evil marker.

## Design Guardrail
A non-negotiable boundary that protects YWE from architectural or canonical drift.

Guardrails exist because later modules may otherwise produce content that is mechanically interesting but no longer truly YWE.

## Divine Core
The cosmological origin point of reality and the deepest origin-level layer in the YWE canon.

It is not just another travel zone or optional high-tier dungeon space.
It is origin-level reality and one of the nine realms or planes.

## Dormant
A state in which a system, prophecy, module, or possibility exists but is not actively manifesting or exerting full current pressure.

The term is contextual and should not be confused with deletion or absence.

## Dual-Variable Alignment
A compatibility model name for the two non-moral, independently accumulating
White Wolf and Dark Wolf resonance values.

It describes the shape of `wolf_resonance`; it is not a third state ledger.
New state and prose use **Wolf Resonance**. Historical
`dual_variable_alignment` metadata may remain to explain the migration model.

## Durable Rationale
An auditable explanation of why a material requirement, authority boundary,
terminology choice, or exception was adopted, including the decision context
and consequences needed for later review.

A durable rationale is stored in a governed decision record or controlling
contract. A transient discussion or unexplained edit is not a substitute.

## Emergence
The process by which higher-order meaning or social structure arises from prior state and consequence.

Examples:
- myth emerges from consequence
- prophecy emerges from convergence
- identity emerges through play

## Engine
A major conceptual subsystem that owns a distinct domain of truth, interpretation, manifestation, or experience.

In YWE design, “engine” does not necessarily mean a separate executable. It means a defined responsibility center.

## Engine Interface Contract
A design-level statement of what a given engine:
- owns
- consumes
- emits
- must never decide

These contracts protect boundaries before coding begins.

## Event History
The ordered, append-only sequence of accepted events, deltas, commits, and
diagnostic no-ops that records how state was reached.

Accepted history records are immutable. Correction, containment, compensation,
or reversal is expressed by appending a new record with provenance, never by
editing or deleting a prior record.

## External Execution Environment
A non-YWE runtime environment such as Unreal, Unity, or Godot that may realize YWE outputs.

These environments may render or embody YWE results, but they do not own YWE truth.

## Faction
An organized collective actor with doctrine, pressure, legitimacy dynamics, and interpretive bias.

Factions are not just reputation buckets. They are carriers of social consequence, myth interpretation, and prophecy response.

## Forsetti Framework
The governing framework inside which YWE exists.

In the corrected model:
- YWE lives inside Forsetti
- Forsetti governs module lifecycle
- Forsetti negotiates with external execution environments
- YWE remains the owner of its internal truth rules

## Synchronized Mirror
A mechanically produced repository copy of an Authoritative Source, maintained
for compatibility, tooling, or path-local consumption and verified by a
deterministic synchronization check.

A Synchronized Mirror must identify its source and synchronization mechanism.
`Generated Mirror` is a presentation alias. The mirror must be
content-equivalent within its declared mapping and cannot override the source.
The ASH mirror under `specs/` is generated from
`core/ash_pattern_engine/canonical/` by
`scripts/sync_ash_specifications.py`.

## Foundational Canon
The highest authority layer of YWE design truth.

Foundational canon is rarely or never altered by runtime play. Lower layers may express it, react to it, or interpret it, but not rewrite it.

## Floki Hrafen Vilgerson
Nathruun's persistent Raven Companion in the first Where Ravens Wait: Eternal
Reckoning campaign.

Floki is a raven companion, ancestor, historical identity, and bloodline memory
vector. He is not a generic pet, cosmetic familiar, or replaceable companion
slot.

## Generation Intent
The narrative-direction choice describing what kind of meaningful content should emerge at a given moment.

Examples include:
- identity progression
- oath pressure
- world repair
- descent revelation
- prophecy escalation

## Governance Alignment
The act of making sure YWE system design and responsibilities remain compatible with Forsetti’s framework-level ownership and lifecycle model.

This is related to implementation planning, not a replacement for agnostic system truth.

## Host Engine
A rendering or execution engine such as Unreal, Unity, or Godot.

In older shorthand, these may be called hosts. In the corrected model, they are better understood as external execution environments rather than owners of YWE modules.

## Identity Pressure
The active symbolic and narrative forces pulling the player toward self-discovery, self-conflict, oath, refusal, role adoption, or transformation.

Identity pressure is central to YWE because player identity is revealed through play, not fully preselected.

## Implementation Mapping
A exchange-oriented mapping from conceptual design artifacts to repository locations, schemas, contracts, or engine ownership zones.

Implementation mapping helps coding agents avoid misplacing system logic.

## Invariant
A design truth that must remain true across all modules, expansions, and implementations.

An invariant may be cosmological, architectural, generative, or experiential.

## Legitimacy
A socially recognized form of authority, credibility, or claim-validity.

Legitimacy matters especially in faction, myth, succession, oath, and prophecy contexts.
It is not the same as objective truth.

## Manifestation
The process by which interpreted pressure becomes something concrete enough to encounter.

Examples include:
- quest manifestation
- omen manifestation
- temporary space manifestation
- NPC manifestation

## Mental Model
A shorthand conceptual framing used to keep later design aligned.

YWE depends heavily on having the right mental models, such as:
- perception is not world rewrite
- prophecy is not fixed fate
- myth is not raw fact

## Module
A specialized subsystem, usually narrower than a core engine, responsible for a specific manifestation or consequence domain.

Examples include:
- quest_engine
- myth_engine
- prophecy_engine
- artifact_engine
- creature_engine

## Module Design Contract
A framework-agnostic definition of a module’s purpose, owned responsibilities, required inputs, outputs, invariants, forbidden scope, and dependency position.

## Mortal Origin
The canonical starting condition of the player.

Players begin as mortals with veiled celestial memory.
This is one of the central YWE guardrails.

## Multiplayer-Safe Divergence
A design condition in which different players may perceive different overlays, meanings, or visibility states without breaking shared-world continuity.

In YWE, perception is the main vehicle for multiplayer-safe divergence.

## Myth
A socially circulating interpretive memory of meaningful consequence.

Myth is not simply history.
It is consequence under retelling pressure.

## Myth Emergence
The process by which consequence-bearing events become rumors, songs, doctrines, inscriptions, shrine narratives, political claims, or other socially carried interpretive forms.

## Myth Line
The family of related myth versions that all trace back to a common seed or consequence cluster.

A myth line may contain competing accounts rather than a single official truth.

## Myth Seed
A consequence-bearing event fragment with enough emotional, symbolic, or social charge to support future myth emergence.

A myth seed is not yet a fully circulated myth.

## Narrative Engine
The core orchestration engine that selects direction, routes consequence, manages runtime generation flow, and coordinates meaningful emergence across systems.

It is broader than quest logic.

## Narrative Space
A meaningful experiential or symbolic space used by the engine to host content.

Some narrative spaces are persistent authored locations.
Others are temporary generated environments.

## NPC Synthesis
The process of generating NPCs as meaningful actors rather than generic service nodes.

NPC synthesis includes motive, role, truth-function, shadow risk, relational pressure, and persistence significance.

## Oath
A binding commitment, vow, obligation, or relationship to duty that carries identity and consequence weight.

Oaths matter because YWE identity and world response often crystallize through commitment, refusal, or betrayal.

## Omen
A perceivable sign associated with rising prophecy, symbolic convergence, or mythically charged future pressure.

Omens do not necessarily explain themselves. They increase interpretive tension.

## Pattern
A detected configuration of symbolic, cosmological, relational, or narrative pressure derived from ASH state.

Patterns are not random tags. They are meaningful signals.

## Pattern Cluster
A reusable grouping of related symbolic patterns that helps organize higher-order generation logic.

Clusters help connect archetype selection, quest families, transformation logic, and future consequence.

## Perception Layer
The system layer that derives a player-specific view of locations, NPCs,
symbols, access, or meaning from authoritative ontology and scoped state.

Perception may change visibility, interpretation, description, or eligible
interaction. A perception record is not objective worldstate and cannot mutate
base ontology or shared truth. An action prompted by perception may later cause
an independently validated worldstate delta.

## Perception Overlay
The derived, player- or observer-scoped output of the Perception Layer.

An overlay references its truth substrate and may alter presentation or
visibility only. It is recomputable, must not be used as the source of an
objective location mutation, and cannot escape its declared observer scope.

## Perception Variant
A player-specific or state-specific version of how a location, event, or actor is perceived.

Perception variants support hidden truths, realm overlays, cult visibility, omen density, and multiplayer-safe divergence.

## Persistent Geography
The stable world topology authored by developers.

YWE does not generate persistent geography as its primary mode.
It generates temporary narrative environments and stateful interpretive overlays around authored space.

## Player Narrative Snapshot
A runtime summary of the player’s current narrative condition, including phase, unresolved tensions, identity pressure, active risks, and related progression relevance.

This snapshot helps downstream generation stay phase-aware.

## Player Origin Arc
The multi-phase progression from mortal unknowing through awakening, memory recovery, identity conflict, chosen becoming, and world-level significance.

## Pressure
A weighted force making certain meanings, manifestations, conflicts, or futures more likely.

Pressure may be symbolic, narrative, factional, mythic, prophetic, or relational.

## Prophecy
A future-oriented attractor built from symbolic convergence, myth pressure, bloodline salience, realm pressure, wolf pressure, repeated patterns, and consequence buildup.

Prophecy is not fixed script.

## Prophecy Activation
The process by which dormant prophetic potential crosses thresholds into active pressure, omen emission, generation bias, or future-structuring influence.

## Prophecy Line
A family of related prophetic interpretations centered on the same future attractor.

As with myths, multiple interpretations may coexist.

## Presentation Order
The one-based order in which a document, user interface, or registry displays
the nine named realms.

Presentation order is contextual and may differ between surfaces. It is not an
Ordinal, Structural Coordinate, Coordinate Index, State Identity, authority
rank, or cosmological priority. A surface that records it must name the ordering
scheme.

## Quest Chain
A structured multi-stage manifestation of meaningful narrative pressure.

A quest chain should carry:
- change
- cost
- interpretation
- relationship consequence
- world or identity effect

## Quest Reward Resolver
The downstream resolver that converts quest resolution into auditable
consequence packets.

The Quest Reward Resolver emits `QuestRewardResolutionPacket` records that
reference `ConsequenceResolutionPacket` records. Those packets route changes to
player state, companion state, ability pressure, worldstate, location mutation,
myth, prophecy, faction/social signals, and future generation bias by refs.

## Quest Template
A reusable scaffold that organizes quest chains into coherent stage structures without flattening them into filler loops.

Templates are symbolic structures, not generic task lists.

## Realm
A profile-level semantic identity assigned to one ontology member by a named
extension or reference profile. Within that profile, each Realm is bound
one-to-one to one Structural Coordinate for deterministic interchange.

Realm is not a universal nine-member YWE Core ontology, a Coordinate Index, an
Ordinal, a Presentation Order, or the State Identity of an ASH vector. A
profile may define its own realm vocabulary and mapping without changing ASH
mathematics. Realm is the preferred ontology-member term. **Plane** and
`plane` are accepted presentation aliases for Realm; they do not define a
competing ontology type.

## Raven Companion
A persistent player-bound companion state represented in player runtime state.

For the canonical Nathruun campaign, the Raven Companion is Floki Hrafen
Vilgerson. The Raven Companion may be offscreen or temporarily noninteractive
for presentation, but is not absent from runtime state unless an explicit
story-state records the exception.

## Realm Engine
The core engine responsible for realm relevance, attunement interpretation, access checks, and lawful realm-shift gating.

It does not invent new realms.

## Realm Ontology
The profile-scoped, immutable-at-runtime truth of which named realms exist
within a declared profile and what category of cosmological state they
represent.

Realm ontology is a profile-specialized view of Ontology, not a universal list
of named YWE Core realms. Within its declared profile it constrains mutable
branch, location, player, and shared worldstate but is not itself one of those
state records.

## Ordinal
The one-based integer equal to `Coordinate Index + 1` in the canonical WRW
realm-anchor mapping.

`Realm Ordinal` is a presentation alias. The ordinal is a human-facing count of
the mapped anchor position. It is not a Structural Coordinate, Coordinate
Index, presentation order, State Identity, power level, or runtime location.

## Realm Shift
A lawful change in world-layer access or experiential state allowing deeper interaction with a non-Physical realm.

Realm shift requires attunement and appropriate site conditions.
It is not generic teleportation.

## Repo Implementation Mapping
The design-to-repository placement reference that says where rules, schemas, docs, and module artifacts belong in the codebase.

## Resonance
A meaningful alignment or responsiveness between an entity and a realm, symbol, bloodline, site, oath, myth, or other higher-order pressure source.

Resonance is broader than mechanical affinity. It is lawful meaningful fit.

## Reversal
A lawful later transition that changes a reversible current-state effect by
appending a Compensating Delta.

Reversal never deletes, edits, negates the occurrence of, or reorders the
original history. A domain contract may declare an effect irreversible; the
existence of the reversal mechanism does not guarantee that every effect can be
reversed.

## Runtime Generation Flow
The canonical orchestration sequence that transforms current state into live manifestations and then routes outcomes back into persistence.

## Sacred Site
A place with heightened symbolic, realm, oath, mythic, or veil significance.

Sacred sites often function as thresholds, catalysts, anchors, or memory-bearing places.

## Shadow Risk
A latent distortion tendency associated with an archetype, NPC, identity path, or pattern pressure.

Shadow risk is not just villainy. It is the dangerous overextension, corruption, or misapplication of a meaningful tendency.

## Site Activation
A state change in a location that alters its relevance, threshold strength, visibility, symbolic activity, or future generation significance.

## Social Memory
The collectively held and circulated memory-form of events, often carried through myth, rumor, ritual, doctrine, or faction narrative.

Social memory is one of the main bridges between consequence and future behavior.

## State Identity
The deterministic identity of one complete state value.

For ASH, state identity is derived from all nine coordinates of the full `F2^9`
vector. A one-hot named-realm anchor is one complete state used by the WRW
projection; neither its active Coordinate Index, Ordinal, nor presentation
order is the State Identity by itself.

`RealmIdentity` is the deprecated type alias for `StateIdentity` in legacy ASH
records. Within that legacy object, `realm_id` is the deprecated field alias
for canonical `vertex_id`; it is not an alias for the entire identity record.
New records use `StateIdentity` or `state_identity` and expose `vertex_id`.
Neither deprecated alias defines a profile-level Realm.

## Symbolic Grammar
The canonical archetypal language by which ASH-derived patterns carry meaning
into deterministic YWE interpretation.

The ASH Cosmological Model owns symbolic-grammar meaning. YWE owns the contracts
that consume and route that meaning; the ASH Pattern System component validates
and stabilizes the operations; WRW specializes outputs into game content. A
feature engine, game profile, or host must not create an independent symbolic
grammar authority.

## Temporary Narrative Environment
A generated experiential space used for visions, trials, prophecy chambers, memory descent spaces, or other bounded narrative manifestations.

These environments may leave residue, but they are not automatically persistent geography.

## Thin Veil
A condition or site where boundaries between realms are unusually permeable.

Thin veil conditions matter because realm shift and related manifestations require more than raw attunement alone.

## Truth Function
The way an NPC or system relates to truth in runtime design.

Examples include:
- fragment-holder
- concealer
- false interpreter
- witness
- tester of truthworthiness

Truth function matters because YWE does not want flat exposition delivery.

## Truth and Authority Lattice
The partial order that identifies who may author each kind of truth and how a
lower scope may specialize, interpret, or materialize a higher authority.

The lattice combines authority layer, truth scope, mutability, and lawful
derivation. Repository path prominence is not authority. The normative machine
form is `data/governance/truth_authority_lattice.json`.

## Visibility Class
A category describing who can perceive, access, or circulate a given myth, prophecy, perception variant, or related state.

Examples include private, factional, local public, cult internal, or broader public scopes.

## White Wolf
One of the two paired symbiotic wolf forces that emerge with Divine Core
creation.

White Wolf is associated with illumination, revelation, knowledge, and truth exposure.
It is not a morality marker.

## Wolf Manifestation
An event, vision, appearance, combat aid, omen, or presence in which one or both wolves become experientially active.

The wolves cannot die permanently, may lose coherence temporarily, and should
never be reduced to ordinary boss encounters.

## Wolf Resonance
The canonical two-value, non-moral relationship between a subject and the
informational pressures represented by White Wolf and Dark Wolf.

Both values accumulate independently, both may increase from one event, and
neither is subtracted. Balance is a consequence target, not a requirement that
the values be equal after every event. `wolf_alignment` is the deprecated
compatibility field; `dual_variable_alignment` is a compatibility model name.
All three names resolve to one canonical resonance state. Readers may accept
the deprecated alias in legacy records; writers use `wolf_resonance`. If both
fields occur, their White Wolf and Dark Wolf values must be identical, and a
conflict is invalid.

## World Actor
A player who has progressed far enough that their identity and actions have meaningful influence on larger collective or systemic conditions.

## WRW Reference Profile
The Where Ravens Wait: Eternal Reckoning game- and narrative-specific
specialization of YWE contracts.

It owns named story canon, characters, quests, locations, dialogue, campaign
rules, and profile-specific manifestations. It may demonstrate and specialize
YWE Core but cannot override ASH or Core or make WRW-specific identities
universal requirements.

## Worldstate
The current mutable, persistent state for an explicitly declared scope, derived
by folding accepted append-only history under YWE state contracts.

Worldstate may include faction, site, NPC, myth, prophecy, location, branch, or
shared-world conditions. It changes within Ontology; it does not
change what the ontology permits to exist. Player perception is a derived view
of state, not an objective worldstate mutation.

## Worldstate Delta
A structured record of what changed after meaningful resolution.

This is the persistence spine of consequence. An accepted delta is appended to
event history. A later compensating delta may reverse a reversible current-state
effect without erasing the original record.

## Yggdrasil
The symbolic and real connective architecture through which the realms are
understood and crossed.

Yggdrasil is not decorative metaphor alone.
It is part of the lawful connective structure of existence, and the wolves tend
its roots to preserve balance.

## YWE
The canonical initialism and presentation alias for **Yggdrasil World Engine**.

It does not name Where Ravens Wait: Eternal Reckoning, a host renderer, or an
independent ASH authority.

## YWE Core
The mandatory setting-neutral and platform-neutral contract layer of the
Yggdrasil World Engine.

YWE Core defines truth boundaries, deterministic state and delta behavior,
provenance, diagnostics, engine interfaces, and extension points required of
every conforming implementation. It may be tested with WRW fixtures, but it
must not require WRW-specific identities, stories, locations, or endings.

---

# 4. Glossary maintenance rules

Future additions should follow these rules:

1. Prefer one stable term over multiple near-synonyms.
2. Do not define implementation details as if they were canon.
3. Do not define social interpretation as objective cosmology.
4. Distinguish clearly between:
   - truth
   - interpretation
   - manifestation
   - consequence
   - perception
5. When a term has both a repository meaning and a deeper conceptual meaning, note both.

---

# 5. Recommended immediate follow-on use

This glossary should now be treated as a reference layer for:
- future YWE design files
- repo documentation normalization
- naming cleanup
- schema naming consistency
- coding-agent exchange clarification
- future thread continuation
