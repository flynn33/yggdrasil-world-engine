# Yggdrasil World Engine (YWE) v2.0.23

A cosmology-driven procedural narrative simulation engine built on the ASH Model of the Universe and governed by code-agnostic engine contracts.

---

## Current Authority Stack

The ASH Model of the Universe is the mathematical and ontological foundation of
Yggdrasil World Engine. Yggdrasil World Engine is an agnostic simulation
framework built on that model. The ASH Pattern System is a YWE component that
provides pattern integrity, diagnostics, recovery, containment, conformance,
code resilience, update safety, and patch stability. Where Ravens Wait: Eternal
Reckoning is the game and narrative layer built on the engine.

Mandatory source-truth statements:

- Yggdrasil World Engine is built on the ASH Model of the Universe.
- The ASH Model of the Universe is the mathematical and ontological foundation of the engine simulation layer.
- The ASH Pattern System is a YWE component for pattern integrity, diagnostics, recovery, containment, conformance, code resilience, update safety, and patch stability.
- Where Ravens Wait: Eternal Reckoning is the game and narrative layer.

The engine is a framework foundation, not a fixed setting bible. Designers may
define their own lore, gods, mythologies, factions, histories, and worlds on top
of the structural ontology.

Current authority contracts:

- `docs/architecture/ash_model_engine_cosmology_contract.md`
- `docs/architecture/ywe_cosmology_authority_contract.md`
- `docs/architecture/ash_pattern_system_component_contract.md`
- `docs/architecture/engine_vs_game_layer_contract.md`
- `docs/architecture/cosmology_framework_extensibility_contract.md`

Earlier repository language may use ASH Pattern System as shorthand for the
upstream mathematical layer. That shorthand is superseded by the current
authority stack above: the ASH Model of the Universe is the foundation, and the
ASH Pattern System is a YWE component.

---

## Overview

The Yggdrasil World Engine is a **code-agnostic cosmic narrative simulation engine** designed to generate:

- Open-ended quest generation
- Mythologies
- Artifacts
- Creatures
- Civilizations
- Player mythic identities

All procedural systems derive from the **ASH Model of the Universe** through
ASH cosmic pattern state, diagnostics, generation plans, and YWE interpretation
contracts.

YWE functions as a **reality simulation layer**, not a rendering engine.
Rendering engines (Unity, Unreal, Godot) function as **host environments**.

The authenticated reference wiki for this repository is available at:

[Yggdrasil World Engine Wiki](https://github.com/flynn33/yggdrasil-world-engine/wiki)

<!-- roadmap-status:start -->
## Specification Roadmap

YWE is under active development as a platform-neutral specification. Platform
products remain deferred until the M10 specification gate is accepted.

[View the detailed specification roadmap](docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md) · [View machine-readable roadmap status](data/governance/specification_roadmap.json)

### Current status

| Indicator | Current state |
|---|---|
| Repository baseline | `v2.0.23` |
| Current milestone | 🟡 `M1` — Normalize canon terminology and governance (`in_progress`) |
| Accepted milestone gates | `1 of 11` |
| Milestone queue | `1` in progress; `9` planned; `0` blocked; `0` deferred |
| Release-ready subsystems | `0 of 15` |
| Specification publication | `unreleased`; `0` GitHub Release objects; `0` agnostic specification releases (verified `2026-07-19`) |
| Platform product work | ⏸️ `deferred`; authorization requires `M10` acceptance |

Milestone indicators: 🟢 `complete` · 🟡 `in_progress` · ⚪ `planned` · 🔴 `blocked` · ⏸️ `deferred`.

| Milestone | Indicator | Status | Dependencies | Objective |
|---|:---:|---|---|---|
| M0 | 🟢 | `complete` | None | Establish one truthful baseline |
| M1 | 🟡 | `in_progress` | M0 | Normalize canon terminology and governance |
| M2 | ⚪ | `planned` | M1 | Build the canonical contract and schema foundation |
| M3 | ⚪ | `planned` | M2 | Complete core deterministic semantics and the reference oracle |
| M4 | ⚪ | `planned` | M3 | Complete state persistence branching and multiplayer |
| M5 | ⚪ | `planned` | M3, M4 | Finish narrative and content generation engines |
| M6 | ⚪ | `planned` | M4, M5 | Close ability companion reward and vertical slice phases |
| M7 | ⚪ | `planned` | M6 | Build the combat and encounter system foundation |
| M8 | ⚪ | `planned` | M5, M7 | Complete environment world and society profiles |
| M9 | ⚪ | `planned` | M3, M4, M5, M6, M7, M8 | Prove agnosticism and whole-system conformance |
| M10 | ⚪ | `planned` | M9 | Freeze and release the agnostic specification |

### Subsystem maturity snapshot

| Dimension | Complete | Partial | Not started | Not applicable | Deferred | Not ready |
|---|---:|---:|---:|---:|---:|---:|
| Historical phase gate | 6 | 3 | 1 | 5 | 0 | 0 |
| Normative artifact | 1 | 10 | 4 | 0 | 0 | 0 |
| Executable schema | 0 | 9 | 6 | 0 | 0 | 0 |
| Conformance tested | 1 | 11 | 3 | 0 | 0 | 0 |
| Release readiness | 0 | 0 | 0 | 0 | 0 | 15 |

These five maturity dimensions are independent. Accepted gates and maturity
counts are not an estimated completion percentage: milestones differ in scope
and effort, and historical foundations do not pass a new gate without its
required acceptance evidence.

See the roadmap inventories of [completed or verified foundations](docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md#completed-or-verified-foundations), [material work remaining](docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md#material-work-remaining), and the [15-subsystem maturity matrix](docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md#subsystem-maturity-matrix).
<!-- roadmap-status:end -->

Current repository baseline. Existing `v2.0.x` Git tags, including historical
annotations that use release wording, identify baselines only; no GitHub Release
objects or YWE Agnostic Specification releases have been published.

| Baseline | Status | Primary Surface |
|---|---|---|
| `v2.0.23` | Current accepted repository baseline | Repository policy hygiene and accepted Phase 16/17 foundation |
| `v2.0.15` | Authority-drift guardrail baseline | Source-truth and Twin Wolf resonance |
| `v2.0.14` | Phase 12 accepted baseline | Quest, NPC, lore, myth, and social-distribution generation |
| `v2.0.13` | Phase 11 accepted baseline | Worldstate and location mutation |
| `v2.0.12` | Phase 10 accepted baseline | Player Runtime State v1 |

---

## Design Goals

- Open-ended narrative generation within deterministic resource and conformance bounds
- Cosmology-consistent simulation
- Player-driven myth formation
- Modular engine architecture
- Engine-agnostic implementation
- Compatibility with RPG, MMO, and TTRPG

---

## Features

### WRW Reference 9-Realm Cosmology

The WRW reference profile binds nine named realms one-to-one to the immutable
nine-coordinate structural ontology. YWE Core requires explicit structural
mappings, not these names as universal fictional locations. Other profiles may
use different presentation labels while preserving their declared coordinate
relationships.

1. Divine Core
2. Celestial
3. Causal
4. Mental
5. Astral
6. Etheric
7. Physical
8. Shadow
9. Void

### Open-Ended Quest Generation

Quests are not random templates. They are generated from ASH cosmic pattern state through pattern detection and player interpretation.

### Dynamic Myth Formation

Significant player events become mythology, influencing books, songs, cult beliefs, shrine inscriptions, future quests, and world rumors.

### Prophecy Generation

Prophecies generate future narrative attractors as probability weights, making related patterns more likely to emerge.

### Perception Layer

The structural ontology is immutable, while governed shared, branch-local, and player-local worldstate may change through recorded deltas. The perception layer derives player-specific interpretations without rewriting authoritative worldstate, so the same location can be interpreted differently depending on realm attunement, wolf resonance, bloodline resonance, and narrative memory.

### Cosmic Pattern Engine

The ASH Model of the Universe is the mathematical and ontological foundation of
the engine simulation layer. The ASH Pattern System is a YWE component that
protects pattern integrity, diagnostics, recovery, containment, conformance,
code resilience, update safety, and patch stability. No subsystem may generate
meaningful content independently of ASH-derived state, diagnostics, codeword
traces, and generation plans.

### ASH/ASP Core Math Baseline

The active ASH/ASP math authority is the accepted
`YWE_ASP_CORE_MATH_REBUILD_PACKAGE` baseline. The ASH state space is `F2^9`:
512 complete 9-coordinate states, transformed only by the fixed 16 canonical
full-state codewords. State transitions use `x' = x XOR c`.

Meaningful YWE generation now carries `CosmicPatternSnapshot`,
`DiagnosticEnvelope`, and `GenerationPlan` provenance through the character,
creature, quest, NPC, artifact, myth, prophecy, perception, faction,
worldstate, lore archive, and realm contracts. Host adapters may materialize from
those plans, but they must not author ASH truth or YWE domain truth.

### ASH Upstream Generation Authority

The historical upstream-generation contract remains as ASH Pattern System
component and packet-spine evidence, but the current repository authority stack
is defined by `docs/architecture/ywe_cosmology_authority_contract.md`.

```text
ASH Model of the Universe
  -> Yggdrasil World Engine
    -> ASH Pattern System component and YWE runtime systems
      -> YWE feature engines
        -> post-M10 downstream platform implementations
```

Player actions and exploration create YWE context packets and worldstate
deltas. YWE submits that context into ASH-governed generation, receives lawful
pattern structure, diagnostics, and generation plans, then interprets the output
into world, quest, NPC, creature, artifact, myth, prophecy, perception, faction,
progression, wolf, and ability manifests. Host adapters materialize approved
manifests but do not author symbolic truth.

### Ability / Power Engine

Phase 14 defines the code-agnostic Ability / Power Engine surface. Abilities
emerge from source provenance rather than a generic unlock ladder: branch
history, worldstate deltas, player runtime state, plane attunement, lineage and
bloodline resonance, wolf companion state, artifact binding, myth participation,
prophecy exposure, and location threshold events may all contribute pressure.

The core Phase 14 contracts live in `docs/architecture/ability_*.md`, with
schemas in `data/schemas/ability_*_schema.json`, validation rules in
`data/validation/ability_*_validation_rules.json`, and Ravenfall Gate examples
in `examples/ability_power_engine/`. Meaningful use records
`AbilityConsequencePacket`; state mutation hands off through
`AbilityStateUpdatePacket`; eligibility and pressure are represented by
`AbilityUnlockPressure`.

### Phase 15A Companion and Reward Foundation

Phase 15A records the Where Ravens Wait: Eternal Reckoning game identity,
Nathruun-first campaign identity, persistent Raven Companion law, conditional
Wolf Manifestation Resolver foundation, and Quest Reward Resolver packet
foundation.

The Raven Companion is persistent player runtime state. In the canonical
Nathruun campaign, Floki Hrafen Vilgerson occupies that role. White Wolf and
Dark Wolf presence is conditional and must be represented by source-referenced
manifestation events rather than default party membership.

Quest Reward Resolver output uses `QuestRewardResolutionPacket` and
`ConsequenceResolutionPacket` records to route player, world, location,
companion, ability, myth, prophecy, and future-generation consequences by refs.

---

## System Map

```mermaid
flowchart TB
  Cosmology["Cosmology Engine<br/>Dark Star, Divine Core, nine fixed realms"]
  Realm["Realm Engine<br/>realm law, attunement, boundaries"]
  ASH["ASH Pattern Engine<br/>F2^9 state, 16 codewords, XOR transitions"]
  Upstream["ASH Upstream Authority<br/>diagnostics, codeword traces, generation plans"]
  Narrative["Narrative Engine<br/>NPCs, worldstate, memory, lore archive"]
  Perception["Perception Engine<br/>player-specific overlays"]
  Quest["Quest Engine"]
  Myth["Myth Engine"]
  Prophecy["Prophecy Engine"]
  Artifact["Artifact Engine"]
  Creature["Creature Engine"]
  Adapters["Unity / Unreal / Godot adapters<br/>materialization only"]

  Cosmology --> Realm
  Cosmology --> ASH
  Realm --> ASH
  ASH --> Upstream
  Upstream --> Narrative
  Upstream --> Perception
  Narrative --> Quest
  Narrative --> Myth
  Narrative --> Prophecy
  Narrative --> Artifact
  Narrative --> Creature
  Perception --> Adapters
  Quest --> Adapters
  Myth --> Adapters
  Prophecy --> Adapters
  Artifact --> Adapters
  Creature --> Adapters
```

## Generation Flow

```mermaid
sequenceDiagram
  participant C as Cosmology / Realm State
  participant A as ASH Pattern Engine
  participant U as ASH Upstream Authority
  participant D as Diagnostics
  participant P as Generation Planner
  participant Y as YWE Domain Engine
  participant H as Host Adapter

  C->>A: complete F2^9 state
  A->>A: x' = x XOR c
  A->>D: validate state, orbit, fallback route
  D-->>A: DiagnosticEnvelope
  A->>U: CosmicPatternSnapshot + codeword trace
  U->>P: SourceASHRefs + DiagnosticEnvelope
  P-->>Y: ASHUpstreamGenerationEnvelope + GenerationPlan
  Y-->>H: domain manifest with source ASH refs
  H-->>H: materialize without authoring YWE truth
```

## Authority Boundary

| Surface | Owns | Must Not Own |
|---|---|---|
| ASH canonical specs | State space, codewords, transitions, diagnostics | Host rendering, game-engine implementation |
| ASH upstream authority | Lawful pattern generation, diagnostics, codeword traces, generation plans | YWE domain manifestation, host materialization |
| YWE core repo | Code-agnostic engines, schemas, lore, conformance, adapter contracts | ASH math, engine-specific runtime code |
| Forsetti governance | Module lifecycle, contracts, validation, policy enforcement | ASH math, YWE cosmology truth, codeword authority |
| Unity / Unreal / Godot adapters | Host materialization from `GenerationPlan` | ASH truth or YWE domain truth |

---

## Future Host Targets

| Engine | Eligibility gate |
|--------|------------------|
| Unity | M10 specification acceptance |
| Unreal | M10 specification acceptance |
| Godot | M10 specification acceptance |

---

## Repository Structure

```
yggdrasil-world-engine/
  core/               -- Core engine specifications
    cosmology_engine/  -- Origin of gravity and reality
    realm_engine/      -- Profile realm projection and scoped state management
    ash_pattern_engine/-- ASH pattern detection and generation
    narrative_engine/  -- Player-specific story transformation
    perception_engine/ -- Player perception and realm overlay

  modules/            -- Expansion engine specifications
    quest_engine/      -- Quest generation from cosmic patterns
    myth_engine/       -- Myth formation from significant events
    prophecy_engine/   -- Prophecy generation and tracking
    artifact_engine/   -- Artifact generation and management
    creature_engine/   -- Creature generation and behavior

  data/               -- Canonical schemas and registries
    realm_registry/    -- Nine canonical realms
    realm/             -- Realm-law and transition canonical rules
    module_capability/ -- Module capability schemas and applied manifests
    faction_topology/  -- Faction topology canonical schema surfaces
    pattern_archetypes/-- Pattern node schemas
    quest_archetypes/  -- Quest seed schemas
    myth_archetypes/   -- Myth record schemas
    bloodline_registry/-- Bloodline schemas
    perception/        -- Perception overlay canonical rules

  lore/               -- Cosmological lore and canon
    wrw_cosmology/     -- Creation and realm formation
    wolf_canon/        -- White Wolf and Dark Wolf canon
    bloodline_history/ -- Bloodline system lore

  adapters/           -- Host engine adapter specifications
    unity/
    unreal/
    godot/

  docs/               -- Documentation
    master_specification/
    architecture/
    ash_compliance/
```

---

## Getting Started

1. Clone this repository.
2. Review the master specification: `docs/master_specification/YWE_MASTER_SPECIFICATION.md`
3. Review the GitHub wiki: `https://github.com/flynn33/yggdrasil-world-engine/wiki`
4. Review the repository bootstrap baseline: `docs/project/repository_map.md`
5. Review the architecture documentation: `docs/architecture/`
6. Review data schemas and canonical rule artifacts as platform-neutral specification inputs.
7. Review core engine interfaces in `core/*/engine_interface.json`.
8. Review expansion-module contracts under `modules/*/`.
9. Run `bash scripts/run_checks.sh` before proposing any repository change.

Recommended reading paths:

| Reader | Start Here | Then Read |
|---|---|---|
| Repository reviewer | `docs/architecture/README.md` | `conformance/`, `scripts/run_checks.sh`, `.github/workflows/ywe_repository_guardrails.yml` |
| Engine implementor | `developer-guide.md` | `adapters/`, `core/`, `data/schemas/README.md` |
| Systems designer | `wiki.md` | `docs/architecture/`, `lore/`, `modules/` |
| Ability / power designer | `docs/architecture/ability_power_engine_contract.md` | `docs/architecture/ability_*_contract.md`, `examples/ability_power_engine/` |
| Companion / reward designer | `docs/architecture/companion_presence_model_contract.md` | `docs/architecture/raven_companion_engine_contract.md`, `docs/architecture/wolf_manifestation_resolver_contract.md`, `docs/architecture/quest_reward_resolver_contract.md` |
| Wiki reader | GitHub wiki `Home` | `System Workflow Atlas`, `Runtime Generation Flow`, `Validation And Conformance` |

---

## Built on the Forsetti Framework (v0.1.0)

The Yggdrasil World Engine is built on the [Forsetti Framework](https://github.com/flynn33/Forsetti-Framework) -- an architecture governance framework that enforces module contracts, runtime policy, and structural integrity. The framework ensures that every module, contract, and integration follows a consistent set of rules.

Forsetti governs module lifecycle and activation policy. It does not override
the ASH/ASP core math baseline, YWE cosmology truth, canonical codeword set,
diagnostics, generation semantics, or package acceptance gates.

Forsetti governs the engine through **five design principles**:

1. **Native-first** -- Separately authorized downstream implementations use native host idioms after M10 acceptance
2. **Contract-first** -- Interfaces are defined in `core/*/engine_interface.json` before any implementation begins
3. **Boundary-first** -- Engine architecture enforces strict one-way dependencies
4. **Policy-first** -- Modules declare capabilities; the host evaluates policy before activation
5. **Host-agnostic modules** -- The core specification is engine-agnostic; platform code belongs only in separate downstream repositories after M10 acceptance

### Governance Files

| File | Description |
|------|-------------|
| [guide.md](guide.md) | Concise integration rules |
| [developer-guide.md](developer-guide.md) | Extended guide for engine implementors |
| [wiki.md](wiki.md) | Comprehensive reference and playbook |
| [docs/master_specification/YWE_MASTER_SPECIFICATION.md](docs/master_specification/YWE_MASTER_SPECIFICATION.md) | Informative WRW-backed mixed-scope composite; route binding claims to focused authorities |
| [docs/project/repository_map.md](docs/project/repository_map.md) | Repository-structure baseline paired with the master spec |
| [missing_source_documents.md](missing_source_documents.md) | Synchronized placeholder and missing-source summary |
| [docs/architecture/authored_override_and_tooling_notes.md](docs/architecture/authored_override_and_tooling_notes.md) | Canonical authored override and tooling guardrail rules |
| [docs/architecture/realm_truth_boundary_contract.md](docs/architecture/realm_truth_boundary_contract.md) | Canonical boundary contract for realm truth vs interpretive layers |
| [repository-contribution-policy.json](repository-contribution-policy.json) | Machine-readable contributor automation constraints |
| [yggdrasil-instructions.json](yggdrasil-instructions.json) | Machine-readable architecture rules |

### Canonical Rule Artifacts

| File | Description |
|------|-------------|
| [data/perception/perception_overlay_rules.yaml](data/perception/perception_overlay_rules.yaml) | Canonical perception overlay rules and truth-boundary constraints |
| [data/realm/realm_mechanics_rules.yaml](data/realm/realm_mechanics_rules.yaml) | Canonical realm-law rules for attunement, bleed, manifestation, and shifts |
| [data/realm/realm_boundary_profiles.yaml](data/realm/realm_boundary_profiles.yaml) | Canonical boundary profile catalog for lawful threshold behavior |
| [data/realm/realm_transition_examples.yaml](data/realm/realm_transition_examples.yaml) | Canonical lawful and unlawful transition examples |
| [data/module_capability/module_capability_manifest_schema.yaml](data/module_capability/module_capability_manifest_schema.yaml) | Canonical module capability and delegation-governance schema |
| `data/module_capability/manifests/*.yaml` | Applied canonical capability declarations for the current YWE core engines and feature modules |
| [data/faction_topology/faction_topology_state_schema.yaml](data/faction_topology/faction_topology_state_schema.yaml) | Canonical faction-topology state schema |

---

## ASH Rebuild Evidence

| File | Description |
|------|-------------|
| [specs/core/ash-state-space.pseudo.md](specs/core/ash-state-space.pseudo.md) | Canonical `F2^9` state-space specification |
| [specs/core/codeword-set.pseudo.md](specs/core/codeword-set.pseudo.md) | Fixed 16-codeword ASH transition set |
| [data/schemas/ash_generation_packet_schema.json](data/schemas/ash_generation_packet_schema.json) | Shared `CosmicPatternSnapshot`, `DiagnosticEnvelope`, and `GenerationPlan` packet schema |
| [docs/architecture/ash_upstream_authority_contract.md](docs/architecture/ash_upstream_authority_contract.md) | Canonical upstream mathematical and generative authority contract |
| [data/schemas/ash_upstream_generation_envelope_schema.json](data/schemas/ash_upstream_generation_envelope_schema.json) | Shared `ASHUpstreamGenerationEnvelope` provenance schema |
| [data/schemas/ywe_generation_context_packet_schema.json](data/schemas/ywe_generation_context_packet_schema.json) | Shared `YWEGenerationContextPacket` schema for player/world context |
| [data/schemas/ywe_interpretation_packet_schema.json](data/schemas/ywe_interpretation_packet_schema.json) | Shared `YWEInterpretationPacket` schema for feature-engine exchange |
| [data/validation/ash_generation_gate_contract.json](data/validation/ash_generation_gate_contract.json) | Required package gate contract for rebuilt generation systems |
| [data/validation/ash_upstream_authority_gate_contract.json](data/validation/ash_upstream_authority_gate_contract.json) | Dedicated upstream authority gate contract |
| [conformance/acceptance-judgment.md](conformance/acceptance-judgment.md) | Current conformance judgment for the code-agnostic repository scope |
| [.github/scripts/ywe_package_acceptance_check.py](.github/scripts/ywe_package_acceptance_check.py) | Blocking package acceptance test runner |

---

## ASH Compliance

All meaningful procedural systems must derive from ASH Model-grounded state,
diagnostics, codeword traces, generation plans, and YWE interpretation
contracts. No subsystem may become an independent random generator detached
from cosmic state and diagnostic provenance.

See `docs/ash_compliance/` for the full compliance rules and checklist.

## Local Validation

Install the pinned validation dependencies and run the authoritative suite from
the repository root:

```bash
python3 -m pip install -r scripts/requirements.txt
bash scripts/run_checks.sh
```

The check catalog at `data/validation/repository_checks.json` is the single
source for local and GitHub validation. To reproduce pull-request-only diff
checks locally:

```bash
bash scripts/run_checks.sh --context pull_request --base origin/main
```

Repository validation keeps this README dashboard synchronized with the
[development roadmap](docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md) and
its machine-readable status authority. To render the canonical dashboard after
a roadmap status change, run:

```bash
python3 scripts/check_specification_roadmap.py --print-readme-status
```

---

## License

Proprietary. All rights reserved. Copyright Jim Daley.

See [LICENSE](LICENSE) for full terms.
