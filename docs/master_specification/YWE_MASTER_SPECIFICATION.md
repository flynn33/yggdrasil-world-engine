# YGGDRASIL WORLD ENGINE (YWE)
## Master Specification Document

Version: **1.0**  
Status: **Foundational Canon**  
Framework Alignment: **Forsetti Framework**  
Cosmology Model: **ASH Model of the Universe**

---

## Current Authority Stack

The ASH Model of the Universe is the mathematical and ontological foundation of
Yggdrasil World Engine. Yggdrasil World Engine is an agnostic simulation
framework built on that model. The ASH Pattern System is a YWE component for
pattern integrity, diagnostics, recovery, containment, conformance, code
resilience, update safety, and patch stability. Where Ravens Wait: Eternal
Reckoning is the game and narrative layer built on the engine.

YWE systems interpret and manifest the ASH Model of the Universe through
engine-agnostic contracts. ASH Pattern System checks and contracts preserve
pattern integrity, diagnostic coverage, recovery behavior, safe failure,
conformance, and patch/update stability.

The controlling authority contracts for this clarification are
`docs/architecture/ash_model_engine_cosmology_contract.md`,
`docs/architecture/ywe_cosmology_authority_contract.md`, and
`docs/architecture/ash_pattern_system_component_contract.md`.

---

# 1. PROJECT OVERVIEW

The **Yggdrasil World Engine (YWE)** is a **code-agnostic cosmic narrative simulation engine** designed to generate:

- infinite quests
- mythologies
- artifacts
- creatures
- civilizations
- player mythic identities

All procedural systems derive from the **ASH Model of the Universe** through
ASH cosmic pattern state, diagnostics, generation plans, and YWE interpretation
contracts.

Phase 8-9 supersession note: The ASH Model of the Universe is the upstream
foundation for YWE and its systems. The ASH Pattern System is a YWE component
for pattern integrity, diagnostics, recovery, containment, conformance, code
resilience, update safety, and patch stability. Generated content must be
grounded in cosmological provenance, branch context, axiom diagnostics,
pattern-vector semantics, existence potential, and worldstate evidence.

YWE functions as a **reality simulation layer**, not a rendering engine.

Rendering engines (Unity, Unreal, Godot) function as **host environments**.

## ASH Upstream Authority

Historical note: earlier repository language described ASH Pattern System as
the upstream mathematical and generative authority for YWE. That framing is now
superseded by the current authority stack: ASH Model of the Universe is the
foundation for YWE and its systems, and ASH Pattern System is a YWE component
for diagnostics, integrity, recovery, containment, resilience, conformance,
code resilience, update safety, and patch stability.

```text
ASH Model of the Universe
  -> Yggdrasil World Engine
    -> ASH Pattern System component and YWE runtime systems
      -> YWE feature engines
        -> platform-specific runtime implementations
```

YWE is the downstream world, narrative, and manifestation engine built on the
ASH Model of the Universe. YWE consumes ASH-derived state, diagnostics,
codeword traces, and generation plans, then interprets them into realm, quest,
NPC, creature, artifact, myth, prophecy, perception, faction, progression,
wolf, and ability manifestations.

YWE is not the origin of ASH math. YWE must not redefine ASH state space,
codeword sets, transition rules, diagnostics, or generation-planning semantics.
Player actions influence future generation context; they do not mutate ASH
math. Host adapters materialize approved manifests but do not author symbolic
truth.

The canonical architecture contract for this boundary is
`docs/architecture/ash_upstream_authority_contract.md`.

## Phase 9 Runtime Cosmology Foundation

Where Ravens Wait: Eternal Reckoning remains the game and narrative layer.
Yggdrasil World Engine remains the agnostic simulation framework. The ASH Model
of the Universe remains the upstream foundation for YWE and its systems. The
ASH Pattern System remains a YWE component for pattern integrity, diagnostics,
recovery, containment, conformance, code resilience, update safety, and patch
stability.

The default nine planes define engine-level structural state layers and
simulation constants. They are the substrate from which runtime manifestation
is interpreted, not a generated branch tree, not mandatory fictional locations,
and not ordinary gameplay zones.

Leaf branch realities are runtime-generated player realities. Each
runtime-generated leaf branch is created from meaningful player choice and
cosmology-grounded context. Meaningful player choices can create branch events,
and those events condition branch state through attunement, bloodline
resonance, wolf resonance, perception, location state, worldstate deltas, and
cosmological law. Leaf branches are not pre-generated.

## Phase 10 Player Runtime State v1

Player Runtime State v1 is the Phase 10 state spine for player branch,
identity, resonance, memory, and ASH Pattern System resilience references.
It keeps the current leaf branch reality as a reference, starts the player as
a mortal instance with veiled celestial identity, and requires meaningful
state mutation to flow through `PlayerStateUpdatePacket`.

## Design Goals

```yaml
design_goals:
  - infinite narrative generation
  - cosmology-consistent simulation
  - player-driven myth formation
  - modular engine architecture
  - engine agnostic implementation
  - compatibility with RPG, MMO, and TTRPG
```

---

# 2. COSMOLOGY CANON

## Primordial State

Before existence:

```text
Primordial Darkness
```

Within that darkness, consciousness began to gather.

Dark matter compacted into the first conscious singularity:

```text
Dark Star
```

## Creation Event

Creation continues through the collapse of the Dark Star into the **Divine Core**.

```text
Dark Star Formation
→ gravity emerges
→ time emerges
→ Void forms as containment
→ Dark Star collapses into the Divine Core
→ nine realms / planes stabilize
→ Architects emerge from contained consciousness
→ first wolves emerge to preserve balance
```

## Realm Formation

In YWE canon, **realm** and **plane** are equivalent terms.
`Realm` remains the preferred repository term.

The universe stabilizes into **nine fixed realms or planes**.
They are layered states of existence separated by liminal space.
They do not change structure.

At the engine layer, the default nine realms are structural simulation layers
and implementation categories, not mandatory fictional map locations. Where
Ravens Wait: Eternal Reckoning expresses them as realms of being; other games
may rename or reskin them while preserving their structural relationships.

---

# 3. REALM SYSTEM

Realms are **fixed cosmological states**.

Players do not move the realms.

Players **change resonance with realms**.
Players change access, perception, and consequence, not realm structure.

## Canonical Realms

```yaml
realms:
  - divine_core
  - celestial
  - causal
  - mental
  - astral
  - etheric
  - physical
  - shadow
  - void
```

## Realm Interpretation

| Realm | Meaning |
|------|------|
| Divine Core | origin of gravity and reality |
| Celestial | order, creation |
| Causal | law, fate |
| Mental | cognition |
| Astral | energetic patterns |
| Etheric | life force |
| Physical | material world |
| Shadow | hidden truths |
| Void | dissolution |

## Realm Travel Rules

Players start in:

```text
Physical Realm
```

Travel to other realms requires:

```text
Realm Attunement ≥ Threshold
+
Thin Veil Location
```

---

# 4. PLAYER MODEL

Players begin as **mortals who have forgotten their celestial heritage**.

Identity emerges through gameplay.

## Player Origin State

```json
{
  "origin": "mortal",
  "celestial_memory": "veiled",
  "realm_attunement": {},
  "wolf_alignment": {
    "white_wolf": 0,
    "dark_wolf": 0
  },
  "bloodline_resonance": {},
  "awakening_fragments": []
}
```

## Character Arc

All players originate as mortals. They unlock fragments of their celestial heritage through quests. The engine generates their personal backstory over time based on:

- quests completed
- realm attunement
- White Wolf accumulation
- Dark Wolf accumulation
- bloodline resonance
- mythic encounters
- prophecy activation

Identity is **revealed through play**, not chosen at character creation.

---

# 5. ALIGNMENT SYSTEM

White Wolf and Dark Wolf are **complementary opposites**, but not moral
opposites. They are not good and evil, and they are not a morality system. The
player may act morally or immorally, but the wolves are not moral poles.

The wolves are embodied companions that physically walk with the player, assist
in quest completion and combat, appear in visions, and signal major changes.
They cannot be killed. They can only temporarily decohere and later return.
Each wolf carries what the other needs.

The healthiest path is balance, not domination of one over the other.

## White Wolf

Represents:

- illumination
- protection
- revelation
- knowledge
- truth exposure
- clarification
- making patterns visible

## Dark Wolf

Represents:

- hiddenness
- fear
- unseen forces
- concealment
- depth
- endurance
- transformation
- gravity and memory

## Alignment Rules

```yaml
alignment_rules:
  accumulation_only: true
  subtraction: false
  morality_system: false
```

Both alignments may increase simultaneously.

A single quest may award both White Wolf and Dark Wolf attunement depending on how the player completes it.
Every conscious being carries both wolves.

The legacy `wolf_alignment` field is a non-moral dual-variable alignment
surface. Preferred prose should use `wolf_resonance` or
`dual_variable_alignment` when describing the model.

---

# 6. REALM ATTUNEMENT SYSTEM

Realm attunement represents player resonance with specific realms.

Players gain realm attunement through quests aligned with those realms.

Example:

- Shadow-aligned quest completion → Shadow Attunement
- Astral-aligned quest completion → Astral Attunement
- Celestial-aligned quest completion → Celestial Attunement

## Realm Unlock Rule

A realm becomes travel-accessible when:

```text
Realm Attunement ≥ Realm Threshold
AND
Player is at a thin veil / place of power
```

## Physical Realm Rule

Players always have access to the Physical Realm.

Even outside realm-shift locations, players may activate realm-aligned abilities while remaining in the Physical Realm.

---

# 7. BLOODLINE SYSTEM

Bloodlines represent **lineage resonance with mythic structures**.
Lineage resonance is a simulation-level propagation mechanic. Designers may
theme it as ancestry, inheritance, faction legacy, house memory, oath-chain
pressure, or other lineage systems.

Example:

```text
Ravenson lineage
```

Bloodlines affect:

- quest interpretation
- prophecy activation
- myth formation
- access to certain visions
- mythic entity response

## Bloodline Schema

```json
{
  "bloodline_id": "ravenson",
  "mythic_origin": "odin_lineage",
  "resonance_effects": [
    "raven_symbols",
    "gate_patterns",
    "shadow_knowledge"
  ]
}
```

Lineage resonance does not lock destiny. It influences **cosmic eligibility**,
interpretive pressure, and inherited cosmological attunements.

---

# 8. PERCEPTION LAYER

The world itself does **not change**.

Player perception changes.

Example:

Player A sees:

```text
normal marketplace
```

Player B sees:

```text
shadow cult marketplace
```

The same world location can be interpreted differently depending on:

- realm attunement
- active realm form
- White Wolf / Dark Wolf accumulation
- bloodline resonance
- player narrative memory

This rule is critical for multiplayer compatibility.

---

# 9. REALM SHIFT SYSTEM

Players begin in the Physical Realm and may fully shift into other realms only at:

- places of power
- thin veil sites
- sacred ruins
- dimensionally unstable locations

## Realm Shift Conditions

```yaml
realm_shift_requirements:
  realm_attunement_threshold_met: true
  veil_location_required: true
  player_form_changes: true
```

When shifted, the player experiences a realm-specific overlay:

- NPCs change
- vendors change
- trainers change
- quest givers change
- realm-only players become visible

If a player remains in the Physical Realm but channels alignment, they may use realm-based abilities without changing world layer.

---

# 10. COSMIC PATTERN ENGINE

All procedural generation originates from **ASH cosmological state analysis**.
Meaningful generation is routed through ASH-governed generation planning before
YWE interpretation and host materialization.

## Pattern Detection

Example pattern:

```json
{
  "pattern_id": "PTN_00451",
  "type": "hidden_knowledge",
  "realm_bias": "shadow",
  "strength": 0.72
}
```

Patterns generate:

- quests
- artifacts
- creatures
- myths
- prophecies
- narrative spaces

## Core Rule

All procedural systems must derive from **ASH Pattern Detection**.

No subsystem may generate meaningful content independently of the cosmic state.

Every meaningful generated manifest must preserve `source_ash_refs`,
`diagnostic_ref`, `generation_plan_ref`, `requested_manifest_kind`, and
`worldstate_delta_policy`.

---

# 11. QUEST GENERATION ENGINE

Quests derive from ASH-governed cosmic patterns interpreted through player
history, local worldstate, faction topology, myth pressure, prophecy pressure,
realm context, and consequence memory.

## Quest Seed

```json
{
  "quest_seed_id": "QS_212",
  "pattern_id": "PTN_00451",
  "interpretations": [
    "reveal",
    "conceal",
    "study"
  ]
}
```

## Quest Completion Modes

Every quest must support multiple completion paths.

Example:

- Reveal truth
- Hide truth
- Weaponize truth

Each path grants different:

- White Wolf gains
- Dark Wolf gains
- realm attunement
- myth consequences
- prophecy weights

## Infinite Quest Principle

Quests are not random templates. They are generated from:

```text
PlayerActionTrace
→ WorldstateDeltaPacket
→ FutureGenerationBiasUpdate
→ YWEGenerationContextPacket
→ ASHUpstreamGenerationEnvelope
→ YWEInterpretationPacket
→ QuestChainManifest
```

Quest templates are interpretive containers. They do not generate symbolic
truth independently.

---

# 12. NARRATIVE ENGINE

The Narrative Engine transforms cosmic patterns into player-specific story.

## Narrative Loop

```text
Player explores or acts
→ YWE records action/context and worldstate deltas
→ YWE submits generation context to ASH-governed generation
→ ASH provides lawful pattern structure, diagnostics, and generation plan
→ YWE interprets output into world/game-domain meaning
→ feature engines emit manifests
→ host adapter materializes approved content
→ result creates worldstate delta or DiagnosticNoOp
→ future generation bias updates context for later ASH-governed generation
```

## Player Narrative Memory

Each player stores interpretation-specific memory.

Example:

```json
{
  "player_memory": {
    "ravenfall_gate": "sealed_by_player",
    "shadow_keeper_trusted": true,
    "artifact_4512_status": "hidden"
  }
}
```

This changes future dialogue, quests, and myth perception for that player.

---

# 13. MYTH GENERATION ENGINE

Significant events become mythology.

Example event:

```text
artifact destroyed
```

Generated myth:

```text
The Shattering of Ravenfall
```

Myths influence:

- books
- songs
- cult beliefs
- shrine inscriptions
- future quests
- world rumors

Different factions can produce different versions of the same myth.

---

# 14. PROPHECY ENGINE

Prophecies generate **future narrative attractors**.

Example:

```json
{
  "prophecy_id": "PR_0082",
  "condition": "shadow_gate_pattern",
  "status": "dormant"
}
```

Prophecies are not fixed scripts. They are probability weights that make related patterns more likely to emerge later.

Prophecies should be influenced by:

- bloodline resonance
- high realm attunement
- repeated myth participation
- major cosmic imbalances

---

# 15. WOLF MANIFESTATION SYSTEM

White Wolf and Dark Wolf:

- cannot be killed
- exist outside the realm system
- appear during cosmic events
- can guide the player
- can assist in combat

## Wolf Interaction Types

```yaml
wolf_interactions:
 - vision
 - quest_guidance
 - combat_assistance
 - prophecy_trigger
 - dream_sequence
```

If a wolf loses coherence in manifestation:

```text
temporary coherence loss
withdrawal from active manifestation
later return
```

The wolves are never enemies.

They are paired balance-keepers and visible companions where canonically appropriate.

## Ability / Power Engine Integration

Abilities are YWE feature-engine manifests grounded in source provenance. They
do not unlock only from level, class, currency, or skill-point purchase. Valid
ability pressure may come from player branch history, worldstate deltas, player
runtime state, plane attunement, bloodline and lineage resonance, wolf
companion state, artifact binding, myth participation, prophecy exposure, or
location threshold events.

Meaningful ability use must resolve through an `AbilityConsequencePacket`,
`WorldstateDeltaPacket`, player state update, future generation bias, wolf
coherence event, or explicit `DiagnosticNoOp`. Ability state mutation is
represented by `AbilityStateUpdatePacket`; eligibility and pressure are
represented by `AbilityUnlockPressure`.

Wolf-linked abilities preserve Twin Wolf companion canon. White Wolf and Dark
Wolf can participate in combat, quest guidance, perception, threshold traversal,
and containment without becoming moral poles. Ability strain can cause temporary
decoherence with recovery conditions; it cannot make the wolves enemies or
remove recovery.

---

# 16. DIVINE CORE ENDGAME

In the Where Ravens Wait narrative layer, the Divine Core is the **ultimate
destination**, expressed through the nine-realm structural ontology and the
endgame objective.

Requirements to approach may include:

- major realm mastery
- high wolf alignment totals
- prophecy completion
- bloodline resonance thresholds
- mythic identity completion

The Divine Core should behave unlike most other realms:

- altered space
- altered time
- altered causality
- mythic-only entities
- origin-level cosmological events

---

# 17. TERRAIN GENERATION MODEL

Persistent terrain is created by developers in the host engine.

YWE only generates **temporary narrative environments**.

Examples:

- vision realms
- celestial trials
- shadow labyrinths
- ancestral memories
- prophecy chambers
- awakening quests

## Terrain Lifecycle

```text
generate
instantiate
play
resolve
dissolve
```

## Terrain Scope Rule

Persistent world geography is not generated by YWE.

YWE only generates procedural terrain for:

- character-specific quest phases
- mythic instanced events
- symbolic narrative spaces

---

# 18. ENGINE-FIRST ARCHITECTURE

YWE is organized as an **engine-first** architecture.

The ASH Model of the Universe defines the mathematical and ontological
foundation. YWE interprets and manifests ASH-derived truth through engine-first
contracts. The ASH Pattern System component stabilizes pattern operations,
diagnostics, recovery, containment, conformance, code resilience, update
safety, and patch stability.

Additional systems can be implemented as separate engines/modules later.

## Core Engines

```yaml
core_engines:
  - cosmology_engine
  - realm_engine
  - ash_pattern_engine
  - narrative_engine
  - perception_engine
```

## Expansion Engines

```yaml
expansion_engines:
  - quest_engine
  - myth_engine
  - prophecy_engine
  - artifact_engine
  - creature_engine
  - civilization_engine
  - religion_engine
  - economy_engine
  - faction_engine
```

All expansion engines must read from the same cosmic state.

---

# 19. REPOSITORY STRUCTURE

```yaml
repository_structure:
  root: yggdrasil-world-engine

  folders:
    core:
      - cosmology_engine
      - realm_engine
      - ash_pattern_engine
      - narrative_engine
      - perception_engine

    modules:
      - quest_engine
      - myth_engine
      - prophecy_engine
      - artifact_engine
      - creature_engine

    data:
      - realm_registry
      - pattern_archetypes
      - myth_archetypes
      - quest_archetypes
      - bloodline_registry

    lore:
      - wrw_cosmology
      - wolf_canon
      - bloodline_history

    adapters:
      - unity
      - unreal
      - godot

    docs:
      - master_specification
      - architecture
      - ash_compliance
```

---

# 20. DATA SCHEMAS

## Player State Schema

```json
{
  "origin": "mortal",
  "celestial_memory": "veiled",
  "realm_attunement": {},
  "wolf_alignment": {
    "white_wolf": 0,
    "dark_wolf": 0
  },
  "bloodline_resonance": {},
  "awakening_fragments": []
}
```

## Pattern Node Schema

```json
{
  "pattern_id": "",
  "type": "",
  "realm_bias": "",
  "strength": 0
}
```

## Quest Seed Schema

```json
{
  "quest_seed_id": "",
  "pattern_id": "",
  "interpretations": []
}
```

## Myth Record Schema

```json
{
  "myth_id": "",
  "source_event": "",
  "title": "",
  "faction_versions": {}
}
```

## Prophecy Schema

```json
{
  "prophecy_id": "",
  "condition": "",
  "status": "dormant"
}
```

## Bloodline Schema

```json
{
  "bloodline_id": "",
  "mythic_origin": "",
  "resonance_effects": []
}
```

---

# 21. ENGINE ADAPTERS

Adapters translate YWE systems to host engines.

Supported engines:

```yaml
adapters:
 - unity
 - unreal
 - godot
```

Adapters handle:

- environment generation hooks
- entity spawning bridges
- UI integration
- temporary narrative space loading
- realm overlay presentation

---

# 22. ASH COMPLIANCE RULES

YWE must never violate the ASH cosmological model.

## Compliance Rules

```yaml
ash_rules:
  realms_are_fixed: true
  player_resonance_changes: true
  patterns_drive_generation: true
  information_states_govern_events: true
  divine_core_is_origin_center: true
  wolves_predate_realms: true
```

## Final Compliance Principle

At every major milestone, the engine should undergo a sanity check to ensure gameplay systems do not violate:

- fixed realm cosmology
- informational-force interpretation of White/Dark
- pattern-driven generation rules
- Divine Core creation model
- bloodline cosmological resonance

---

# 23. FORSETTI FRAMEWORK ALIGNMENT

The engine follows Forsetti Framework principles:

- modular structure
- clear boundaries
- data-driven design
- host-engine separation
- code-agnostic architecture

All modules should communicate through stable interfaces and explicit data definitions.

---

# 24. IMPLEMENTATION PRINCIPLES

```yaml
implementation:
  language_independent: true
  engine_agnostic: true
  data_driven: true
  modular_expansion: true
  cosmology_locked: true
```

---

# 25. FINAL RULE

All procedural systems must derive from:

```text
ASH cosmic pattern state under the ASH Model of the Universe
```

ASH Pattern Detection is the component-level validation and stabilization
surface. No subsystem may become an independent random generator detached from
the cosmic state.

---

# END OF SPECIFICATION
