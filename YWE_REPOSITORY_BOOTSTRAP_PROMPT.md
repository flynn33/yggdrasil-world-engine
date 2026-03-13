# YGGDRASIL WORLD ENGINE
## Repository Bootstrap Prompt for AI Coding Agent

You are tasked with initializing the **Yggdrasil World Engine (YWE)** GitHub repository.

You will receive a document called:

```text
YWE_MASTER_SPECIFICATION.md
```

That document contains the **canonical design specification** for the engine.

Your task is to **create the repository structure and scaffolding exactly according to the specification**.

Do not invent systems outside the specification.  
Do not alter cosmology rules.

The repository should be designed to support **multi-engine implementation** (Unity, Unreal, Godot).

---

# PRIMARY OBJECTIVE

Create the foundational repository for the **Yggdrasil World Engine**, including:

- directory structure
- module placeholders
- configuration schemas
- documentation
- data templates
- engine adapters

The engine must remain **code-agnostic and data-driven**.

---

# STEP 1 — CREATE REPOSITORY

Repository name:

```text
yggdrasil-world-engine
```

Initialize with:

```text
README.md
LICENSE
.gitignore
```

Recommended license:

```text
MIT
```

---

# STEP 2 — CREATE CORE DIRECTORY STRUCTURE

Create the following structure:

```text
yggdrasil-world-engine
│
├── core
│   ├── cosmology_engine
│   ├── realm_engine
│   ├── ash_pattern_engine
│   ├── narrative_engine
│   └── perception_engine
│
├── modules
│   ├── quest_engine
│   ├── myth_engine
│   ├── prophecy_engine
│   ├── artifact_engine
│   └── creature_engine
│
├── data
│   ├── realm_registry
│   ├── pattern_archetypes
│   ├── myth_archetypes
│   ├── quest_archetypes
│   └── bloodline_registry
│
├── lore
│   ├── wrw_cosmology
│   ├── wolf_canon
│   └── bloodline_history
│
├── adapters
│   ├── unity
│   ├── unreal
│   └── godot
│
└── docs
    ├── architecture
    ├── ash_compliance
    └── master_specification
```

---

# STEP 3 — CORE ENGINE MODULES

Each core engine directory should include:

```text
README.md
interface_definition.json
module_description.md
```

Example:

```text
core/cosmology_engine/
```

Files:

```text
cosmology_engine/
    README.md
    cosmology_schema.json
    engine_interface.json
```

---

# STEP 4 — DATA SCHEMA TEMPLATES

Create base JSON schemas for the following systems.

## Player State Schema

File:

```text
data/player_schema.json
```

Contents:

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

```text
data/pattern_archetypes/pattern_schema.json
```

```json
{
  "pattern_id": "",
  "type": "",
  "realm_bias": "",
  "strength": 0
}
```

## Quest Seed Schema

```text
data/quest_archetypes/quest_seed_schema.json
```

```json
{
  "quest_seed_id": "",
  "pattern_id": "",
  "interpretations": []
}
```

## Myth Record Schema

```text
data/myth_archetypes/myth_schema.json
```

```json
{
  "myth_id": "",
  "source_event": "",
  "title": "",
  "faction_versions": {}
}
```

## Prophecy Schema

```text
modules/prophecy_engine/prophecy_schema.json
```

```json
{
  "prophecy_id": "",
  "condition": "",
  "status": "dormant"
}
```

## Bloodline Schema

```text
data/bloodline_registry/bloodline_schema.json
```

```json
{
  "bloodline_id": "",
  "mythic_origin": "",
  "resonance_effects": []
}
```

---

# STEP 5 — REALM REGISTRY

Create canonical realm registry file:

```text
data/realm_registry/realms.json
```

Contents:

```json
{
  "realms": [
    "divine_core",
    "celestial",
    "causal",
    "mental",
    "astral",
    "etheric",
    "physical",
    "shadow",
    "void"
  ]
}
```

---

# STEP 6 — DOCUMENTATION

Move the following document into:

```text
docs/master_specification/
```

File:

```text
YWE_MASTER_SPECIFICATION.md
```

This is the **canonical design reference**.

---

# STEP 7 — ADAPTER MODULES

Create placeholder adapters.

Example:

```text
adapters/unity/
```

Files:

```text
adapter_interface.md
environment_bridge.md
entity_spawn_bridge.md
```

Repeat for:

```text
unreal
godot
```

Adapters will translate YWE systems into engine-specific implementations.

---

# STEP 8 — README

Create a top-level README summarizing the engine.

Suggested content:

```markdown
# Yggdrasil World Engine (YWE)

A cosmology-driven procedural narrative engine based on the ASH Model and the Forsetti Framework.

## Features
- infinite quest generation
- dynamic myth formation
- prophecy generation
- cosmic pattern simulation
- realm-based narrative systems
- modular engine architecture

## Supported Host Engines
- Unity
- Unreal
- Godot
```

---

# STEP 9 — FUTURE MODULE EXTENSIBILITY

Ensure the repository structure allows additional engines to be added later.

Possible future modules:

```text
civilization_engine
economy_engine
religion_engine
faction_engine
politics_engine
```

Modules must read from the **Cosmic Pattern Engine** rather than generating independent systems.

---

# STEP 10 — DOCUMENT INITIAL PLACEHOLDER FILES

Each folder should contain enough placeholder documentation so future developers or agents know its role.

Examples:

- `README.md`
- `module_description.md`
- `schema_notes.md`
- `adapter_interface.md`

These placeholders should explain purpose, inputs, outputs, and dependency expectations.

---

# FINAL RULE

All systems must derive procedural generation from:

```text
ASH Pattern Detection
```

No independent random generators may be created for meaningful content.

All emergent content must originate from **cosmic pattern state**.

---

# OUTPUT EXPECTATION

At completion the repository should contain:

- structured folders
- JSON schema templates
- documentation
- module placeholders
- adapter scaffolding

No gameplay implementation code is required at this stage.

The goal is a **clean, extensible GitHub skeleton** consistent with the YWE master specification.

---

# END OF BOOTSTRAP PROMPT
