# Yggdrasil World Engine (YWE) v2.0

A cosmology-driven procedural narrative simulation engine based on the ASH Model and the Forsetti Framework.

---

## Overview

The Yggdrasil World Engine is a **code-agnostic cosmic narrative simulation engine** designed to generate:

- Infinite quests
- Mythologies
- Artifacts
- Creatures
- Civilizations
- Player mythic identities

All procedural systems derive from **ASH cosmological mathematics**.

YWE functions as a **reality simulation layer**, not a rendering engine.
Rendering engines (Unity, Unreal, Godot) function as **host environments**.

---

## Design Goals

- Infinite narrative generation
- Cosmology-consistent simulation
- Player-driven myth formation
- Modular engine architecture
- Engine-agnostic implementation
- Compatibility with RPG, MMO, and TTRPG

---

## Features

### Canonical 9-Realm Cosmology

The core cosmology is based on nine fixed cosmological states:

1. Divine Core
2. Celestial
3. Causal
4. Mental
5. Astral
6. Etheric
7. Physical
8. Shadow
9. Void

### Infinite Quest Generation

Quests are not random templates. They are generated from ASH cosmic pattern state through pattern detection and player interpretation.

### Dynamic Myth Formation

Significant player events become mythology, influencing books, songs, cult beliefs, shrine inscriptions, future quests, and world rumors.

### Prophecy Generation

Prophecies generate future narrative attractors as probability weights, making related patterns more likely to emerge.

### Perception Layer

The world does not change -- player perception changes. The same location can be interpreted differently depending on realm attunement, wolf alignment, bloodline resonance, and narrative memory.

### Cosmic Pattern Engine

All procedural generation originates from ASH cosmological state analysis. No subsystem may generate meaningful content independently of the cosmic state.

---

## Supported Host Engines

| Engine | Status |
|--------|--------|
| Unity | Planned |
| Unreal | Planned |
| Godot | Planned |

---

## Repository Structure

```
yggdrasil-world-engine/
  core/               -- Core engine specifications
    cosmology_engine/  -- Origin of gravity and reality
    realm_engine/      -- Fixed cosmological state management
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
3. Review the architecture documentation: `docs/architecture/`
4. Load data schemas and canonical rule artifacts into your host engine.
5. Implement core engines following interface definitions in `core/*/engine_interface.json`.
6. Extend with expansion modules following `modules/*/`.

---

## Built on the Forsetti Framework (v0.1.0)

The Yggdrasil World Engine is built on the [Forsetti Framework](https://github.com/flynn33/Forsetti-Framework) -- an architecture governance framework that enforces module contracts, runtime policy, and structural integrity. The framework ensures that every module, contract, and integration follows a consistent set of rules.

Forsetti governs the engine through **five design principles**:

1. **Native-first** -- Engine implementations use native idioms (C# for Unity, C++ for Unreal, GDScript for Godot)
2. **Contract-first** -- Interfaces are defined in `core/*/engine_interface.json` before any implementation begins
3. **Boundary-first** -- Engine architecture enforces strict one-way dependencies
4. **Policy-first** -- Modules declare capabilities; the host evaluates policy before activation
5. **Host-agnostic modules** -- The core specification is engine-agnostic; engine-specific code lives only in implementation branches

### Governance Files

| File | Description |
|------|-------------|
| [guide.md](guide.md) | Concise integration rules |
| [developer-guide.md](developer-guide.md) | Extended guide for engine implementors |
| [wiki.md](wiki.md) | Comprehensive reference and playbook |
| [missing_source_documents.md](missing_source_documents.md) | Canonical artifact inventory and pending placeholder tracking |
| [agentic-coding-policy.json](agentic-coding-policy.json) | Machine-readable AI agent constraints |
| [yggdrasil-instructions.json](yggdrasil-instructions.json) | Machine-readable architecture rules |

---

## ASH Compliance

All procedural systems must derive from ASH Pattern Detection. No subsystem may become an independent random generator detached from the cosmic state.

See `docs/ash_compliance/` for the full compliance rules and checklist.

---

## License

Proprietary. All rights reserved. Copyright Jim Daley.

See [LICENSE](LICENSE) for full terms.
