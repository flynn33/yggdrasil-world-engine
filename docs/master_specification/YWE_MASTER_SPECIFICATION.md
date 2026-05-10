# YGGDRASIL WORLD ENGINE (YWE)
## Master Specification Document

Version: **1.0**  
Status: **Foundational Canon**  
Framework Alignment: **Forsetti Framework**  
Cosmology Model: **ASH Model**

---

# 1. PROJECT OVERVIEW

The **Yggdrasil World Engine (YWE)** is a **code-agnostic cosmic narrative simulation engine** designed to generate:

- infinite quests
- mythologies
- artifacts
- creatures
- civilizations
- player mythic identities

All procedural systems derive from **ASH cosmological mathematics**.

YWE functions as a **reality simulation layer**, not a rendering engine.

Rendering engines (Unity, Unreal, Godot) function as **host environments**.

## ASH Upstream Authority

ASH is the upstream mathematical and generative authority for YWE.

```text
ASH Pattern System
  -> Yggdrasil World Engine
    -> YWE game systems / feature engines
      -> platform-specific runtime implementations
```

YWE is the downstream world, narrative, and manifestation engine built on ASH
authority. YWE consumes ASH-derived state, diagnostics, codeword traces, and
generation plans, then interprets them into realm, quest, NPC, creature,
artifact, myth, prophecy, perception, faction, progression, wolf, and ability
manifestations.

YWE is not the origin of ASH math. YWE must not redefine ASH state space,
codeword sets, transition rules, diagnostics, or generation-planning semantics.
Player actions influence future generation context; they do not mutate ASH
math. Host adapters materialize approved manifests but do not author symbolic
truth.

The canonical architecture contract for this boundary is
`docs/architecture/ash_upstream_authority_contract.md`.

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

White Wolf and Dark Wolf are **paired symbiotic companions of consciousness**, not morality markers.
The healthiest path is balance, not domination of one over the other.

## White Wolf

Represents:

- illumination
- revelation
- knowledge
- truth exposure
- consuming ignorance

## Dark Wolf

Represents:

- hiddenness
- fear
- unseen forces
- concealment
- depth

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

Bloodlines represent **ancestral resonance with mythic structures**.

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

Bloodlines do not lock destiny. They influence **cosmic eligibility**.

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

---

# 16. DIVINE CORE ENDGAME

The Divine Core is the **ultimate destination**, one of the nine realms or planes, and the endgame objective.

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

ASH defines upstream mathematical and generative authority. YWE interprets and
manifests ASH-derived truth through engine-first contracts.

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
ASH Pattern Detection
```

No subsystem may become an independent random generator detached from the cosmic state.

---

# END OF SPECIFICATION
