# YWE Codex GitHub Build Package
## Combined repository build instructions and completed design inventory for Codex

Date: 2026-03-13
Project: Yggdrasil World Engine (YWE)
Status: Codex handoff package

---

# 1. Purpose

This file is the single handoff package for Codex.

It combines:
- the purpose of the YWE project
- the architectural rules Codex must not violate
- the required GitHub repository structure
- the directory and file creation instructions
- the inventory of design assets already completed
- the mapping of those assets into the repository
- the placeholder policy for files that do not yet have finalized contents

Codex should use this document to create the GitHub repository skeleton and place
all known design artifacts into the correct locations without guessing at the
architecture.

---

# 2. What YWE Is

Yggdrasil World Engine is a cosmology-driven narrative simulation engine.

It is not a generic procedural RPG generator.

Its purpose is to transform symbolic state into:
- quest pressure
- consequence
- myth
- prophecy
- perception divergence
- future narrative possibility

The core generation law is:

```text
ASH State -> Pattern Detection -> Narrative Interpretation -> Quest Manifestation
```

All meaningful procedural content must derive from ASH Pattern Detection.
No independent random generator may own meaningful content generation.

---

# 3. Locked Canon And Non-Negotiable Rules

Codex must preserve these foundations exactly.

## Cosmology
- Primordial Darkness precedes creation.
- White Wolf and Dark Wolf predate realms, gods, matter, and time.
- Creation begins with Divine Core ignition.
- The universe stabilizes into nine fixed realms:
  - divine_core
  - celestial
  - causal
  - mental
  - astral
  - etheric
  - physical
  - shadow
  - void

## Player model
- All players begin as mortals who have forgotten their celestial heritage.
- Identity is revealed through gameplay, not fully chosen up front.
- Bloodlines affect resonance and eligibility, but do not lock destiny.

## World presentation
- Players change resonance, not realm structure.
- Persistent world geography is developer-authored.
- YWE only generates temporary narrative environments.
- Perception is the multiplayer-safe divergence layer.
- Perception must not rewrite shared-world truth.

## Wolf doctrine
- White Wolf and Dark Wolf are primordial informational forces.
- They are not morality meters.
- They are not enemies to be killed.
- Both may increase from the same quest depending on interpretation.

## Myth and prophecy doctrine
- Myth and prophecy must arise from ASH-driven consequence.
- Myth and prophecy are distinct systems.
- Myth should alter legitimacy, memory, rumor, ritual, expectation, and future pressure more than geography.

## Governance doctrine
- YWE exists inside the Forsetti Framework.
- Forsetti governs activation.
- YWE governs truth.
- External engines do not own YWE truth.
- Unity, Unreal, Godot, and future hosts are negotiated execution environments.

---

# 4. Architectural Intent

YWE uses an engine-first architecture.

## Core engines
These define universal YWE truth and should always be treated as foundational:
- cosmology_engine
- realm_engine
- ash_pattern_engine
- narrative_engine
- perception_engine

## Feature modules
These are specialized manifestation systems that consume core truth:
- quest_engine
- myth_engine
- prophecy_engine
- artifact_engine
- creature_engine

## Shared data
These hold schemas, registries, archetypes, and canonical data.

## Docs
These hold explanation, rationale, notes, contracts, and compliance material.

## Adapters
These remain repository folders for host-environment bridges, but they must be documented as downstream execution connectors rather than owners of YWE logic.

---

# 5. Repository Name And Root Files

Repository name:

```text
yggdrasil-world-engine
```

Create these root files:

```text
README.md
LICENSE
.gitignore
YWE_REPOSITORY_BOOTSTRAP_PROMPT.md
YWE_CODEX_GITHUB_BUILD_PACKAGE.md
```

Recommended license:

```text
MIT
```

---

# 6. Required Repository Structure

Create this repository structure exactly:

```text
yggdrasil-world-engine/
├── core/
│   ├── cosmology_engine/
│   ├── realm_engine/
│   ├── ash_pattern_engine/
│   ├── narrative_engine/
│   └── perception_engine/
├── modules/
│   ├── quest_engine/
│   ├── myth_engine/
│   ├── prophecy_engine/
│   ├── artifact_engine/
│   └── creature_engine/
├── data/
│   ├── realm_registry/
│   ├── pattern_archetypes/
│   ├── myth_archetypes/
│   ├── quest_archetypes/
│   ├── bloodline_registry/
│   └── schemas/
├── lore/
│   ├── wrw_cosmology/
│   ├── wolf_canon/
│   └── bloodline_history/
├── adapters/
│   ├── unity/
│   ├── unreal/
│   └── godot/
└── docs/
    ├── architecture/
    ├── ash_compliance/
    ├── master_specification/
    ├── governance/
    ├── glossary/
    └── handoff/
```

Notes:
- `data/schemas/` is an implementation-ready refinement for shared schema files.
- This does not contradict the earlier bootstrap. It improves long-term clarity.
- If strict adherence to the original spec is preferred, Codex may keep schema files in existing data folders and omit `data/schemas/`, but the rest of the structure should remain unchanged.

---

# 7. Baseline Placeholder Files For Every Directory

Each engine, module, adapter, and top-level documentation directory should contain enough files that a later developer or coding agent can understand purpose, inputs, outputs, dependencies, and constraints.

## Core engine folder baseline
For each folder under `core/`, create:

```text
README.md
module_description.md
engine_interface.json
schema_notes.md
```

## Module folder baseline
For each folder under `modules/`, create:

```text
README.md
module_description.md
engine_interface.json
schema_notes.md
```

## Adapter folder baseline
For each folder under `adapters/`, create:

```text
README.md
adapter_interface.md
environment_bridge.md
entity_spawn_bridge.md
capability_profile.yaml
activation_policy_notes.md
delegation_boundary.md
```

## Data folder baseline
For each folder under `data/`, create:

```text
README.md
schema_notes.md
```

## Lore folder baseline
For each folder under `lore/`, create:

```text
README.md
source_notes.md
canon_scope.md
```

## Docs folder baseline
For each folder under `docs/`, create:

```text
README.md
```

---

# 8. Canonical Shared Schema Files

Create the following shared schema files.

## Player state
```text
data/schemas/player_schema.json
```

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

## Realm registry
```text
data/realm_registry/realms.json
```

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

## Pattern schema
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

## Quest seed schema
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

## Myth schema
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

## Prophecy schema
```text
data/schemas/prophecy_schema.json
```

```json
{
  "prophecy_id": "",
  "condition": "",
  "status": "dormant"
}
```

## Bloodline schema
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

## Additional implementation-ready shared schemas
Create these as placeholders if the final versions are not yet supplied:

```text
data/schemas/myth_record_schema_expansion.json
data/schemas/prophecy_schema_expansion.json
data/schemas/perception_layer_persistence_schema.json
```

---

# 9. Completed Design Inventory

These design assets are already completed or explicitly defined in the current YWE design stack and should be created in the repository.

## Foundational canon / bootstrap
1. `YWE_MASTER_SPECIFICATION.md`
2. `YWE_REPOSITORY_BOOTSTRAP_PROMPT.md`

## ASH Pattern Archetype design stack
3. `ASH_PATTERN_ARCHETYPE_LIBRARY_V0_2.md`
4. `character_archetypes.yaml`
5. `quest_archetypes.yaml`
6. `region_archetypes.yaml`
7. `faction_archetypes.yaml`
8. `transformation_archetypes.yaml`
9. `event_archetypes.yaml`
10. `pattern_clusters.yaml`
11. `generation_rules.yaml`
12. `compatibility_matrix.yaml`
13. `COMPATIBILITY_MATRIX_NOTES.md`

## Player progression / identity layer
14. `player_origin_arc_rules.yaml`
15. `PLAYER_ORIGIN_ARC_NOTES.md`

## NPC generation layer
16. `npc_synthesis_rules.yaml`
17. `NPC_SYNTHESIS_NOTES.md`

## Quest scaffold layer
18. `quest_chain_templates.yaml`
19. `QUEST_CHAIN_TEMPLATE_NOTES.md`

## Runtime orchestration layer
20. `ash_runtime_generation_flow.yaml`
21. `ASH_RUNTIME_GENERATION_FLOW_NOTES.md`

## Consequence persistence layer
22. `worldstate_delta_rules.yaml`
23. `WORLDSTATE_DELTA_RULES_NOTES.md`

## Myth / prophecy layer
24. `myth_emergence_rules.yaml`
25. `MYTH_EMERGENCE_RULES_NOTES.md`
26. `prophecy_activation_rules.yaml`
27. `PROPHECY_ACTIVATION_RULES_NOTES.md`

## Repository / implementation handoff layer
28. `repo_implementation_mapping.md`
29. `myth_record_schema_expansion.json`
30. `prophecy_schema_expansion.json`
31. `perception_layer_persistence_schema.json`
32. `engine_interface_contracts.md`
33. `forsetti_governance_alignment.md`

## Agnostic design consolidation layer
34. `ywe_module_design_contracts.md`
35. `ywe_canonical_data_domains.md`
36. `ywe_cross_module_dependency_map.md`
37. `ywe_invariant_guardrails.md`

## Terminology and validation layer
38. `ywe_design_glossary.md`
39. `ash_compliance_checklist.md`

## Specialized future-spec pass already started
40. `artifact_system_rules.yaml`
41. `creature_system_rules.yaml`

---

# 10. Repository Placement Map

Place the known files in the following locations.

## Root
```text
/YWE_REPOSITORY_BOOTSTRAP_PROMPT.md
/YWE_CODEX_GITHUB_BUILD_PACKAGE.md
/README.md
/LICENSE
/.gitignore
```

## docs/master_specification
```text
docs/master_specification/YWE_MASTER_SPECIFICATION.md
```

## docs/handoff
```text
docs/handoff/repo_implementation_mapping.md
```

## docs/governance
```text
docs/governance/forsetti_governance_alignment.md
```

## docs/glossary
```text
docs/glossary/ywe_design_glossary.md
```

## docs/ash_compliance
```text
docs/ash_compliance/ash_compliance_checklist.md
```

## docs/architecture
```text
docs/architecture/ASH_PATTERN_ARCHETYPE_LIBRARY_V0_2.md
docs/architecture/COMPATIBILITY_MATRIX_NOTES.md
docs/architecture/PLAYER_ORIGIN_ARC_NOTES.md
docs/architecture/NPC_SYNTHESIS_NOTES.md
docs/architecture/QUEST_CHAIN_TEMPLATE_NOTES.md
docs/architecture/ASH_RUNTIME_GENERATION_FLOW_NOTES.md
docs/architecture/WORLDSTATE_DELTA_RULES_NOTES.md
docs/architecture/MYTH_EMERGENCE_RULES_NOTES.md
docs/architecture/PROPHECY_ACTIVATION_RULES_NOTES.md
docs/architecture/engine_interface_contracts.md
docs/architecture/ywe_module_design_contracts.md
docs/architecture/ywe_canonical_data_domains.md
docs/architecture/ywe_cross_module_dependency_map.md
docs/architecture/ywe_invariant_guardrails.md
```

## data/pattern_archetypes
```text
data/pattern_archetypes/character_archetypes.yaml
data/pattern_archetypes/region_archetypes.yaml
data/pattern_archetypes/faction_archetypes.yaml
data/pattern_archetypes/transformation_archetypes.yaml
data/pattern_archetypes/event_archetypes.yaml
data/pattern_archetypes/pattern_clusters.yaml
data/pattern_archetypes/generation_rules.yaml
data/pattern_archetypes/compatibility_matrix.yaml
```

## data/quest_archetypes
```text
data/quest_archetypes/quest_archetypes.yaml
```

## data/schemas
```text
data/schemas/player_schema.json
data/schemas/myth_record_schema_expansion.json
data/schemas/prophecy_schema_expansion.json
data/schemas/perception_layer_persistence_schema.json
data/schemas/prophecy_schema.json
```

## core/narrative_engine
```text
core/narrative_engine/player_origin_arc_rules.yaml
core/narrative_engine/npc_synthesis_rules.yaml
core/narrative_engine/ash_runtime_generation_flow.yaml
core/narrative_engine/worldstate_delta_rules.yaml
```

## core/perception_engine
```text
core/perception_engine/perception_layer_persistence_schema.json
```

## modules/quest_engine
```text
modules/quest_engine/quest_chain_templates.yaml
```

## modules/myth_engine
```text
modules/myth_engine/myth_emergence_rules.yaml
```

## modules/prophecy_engine
```text
modules/prophecy_engine/prophecy_activation_rules.yaml
```

## modules/artifact_engine
```text
modules/artifact_engine/artifact_system_rules.yaml
```

## modules/creature_engine
```text
modules/creature_engine/creature_system_rules.yaml
```

## data/myth_archetypes
```text
data/myth_archetypes/myth_schema.json
```

## data/bloodline_registry
```text
data/bloodline_registry/bloodline_schema.json
```

## data/realm_registry
```text
data/realm_registry/realms.json
```

---

# 11. If A File Exists In The Design Stack But Its Final Text Is Not Supplied

Codex must still create the file.

Use this rule:
- create the correct directory and filename
- insert a structured placeholder header
- explain the file purpose
- describe expected inputs, outputs, dependencies, and invariants
- mark it clearly as `Status: placeholder awaiting finalized content`
- do not invent lore or mechanics that contradict locked canon

## Placeholder markdown template

```markdown
# <FILE TITLE>

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: placeholder awaiting finalized content

## Purpose
<what this file is for>

## Expected responsibilities
- ...

## Inputs
- ...

## Outputs
- ...

## Dependencies
- ...

## Invariants
- all meaningful generation must remain ASH-derived
- fixed cosmology must remain locked
- perception must not rewrite shared-world truth
- Forsetti governs activation; YWE governs truth
```

## Placeholder YAML template

```yaml
version: "0.1"
status: placeholder_awaiting_finalized_content
meta:
  system: <system_name>
  purpose: <purpose>
  invariants:
    - all_meaningful_generation_must_be_ash_derived
    - fixed_cosmology_must_remain_locked
    - perception_must_not_rewrite_shared_world_truth
    - forsetti_governs_activation_ywe_governs_truth
```

---

# 12. README Guidance

Create a top-level `README.md` that explains the project clearly.

It should include:
- what YWE is
- why it exists
- core design law
- the engine-first architecture
- the relationship to Forsetti
- the supported external environments
- the difference between truth engines and execution connectors

Suggested opening:

```markdown
# Yggdrasil World Engine (YWE)

Yggdrasil World Engine is a cosmology-driven narrative simulation engine built to turn ASH-derived symbolic state into quests, consequence, myth, prophecy, and perception-safe multiplayer narrative divergence.

It is designed as a code-agnostic, engine-agnostic system architecture operating inside the Forsetti Framework.
```

---

# 13. Adapter Documentation Rule

Each adapter folder must document these truths explicitly:
- it does not own cosmology or generation truth
- it is downstream of Forsetti governance
- it exposes execution capabilities
- it may realize YWE outputs in an external environment
- it may not redefine canonical realm, wolf, player-origin, myth, or prophecy rules

---

# 14. Implementation Order For Codex

Codex should build in this order.

## Phase 1 — repository skeleton
1. create root files
2. create all folders
3. create baseline placeholder files for every folder

## Phase 2 — canonical shared data
4. create realm registry
5. create player schema
6. create pattern schema
7. create quest seed schema
8. create myth schema
9. create prophecy schema
10. create bloodline schema
11. create schema expansion placeholders

## Phase 3 — architecture docs and contracts
12. place master spec
13. place repository bootstrap prompt
14. place repository mapping
15. place engine interface contracts
16. place Forsetti governance alignment
17. place module design contracts
18. place canonical data domains
19. place cross-module dependency map
20. place invariant guardrails
21. place glossary
22. place compliance checklist

## Phase 4 — symbolic grammar and narrative files
23. place ASH archetype library
24. place archetype YAML files
25. place compatibility files
26. place player origin arc rules
27. place NPC synthesis rules
28. place quest chain templates
29. place runtime generation flow
30. place worldstate delta rules
31. place myth emergence rules
32. place prophecy activation rules
33. place artifact system rules
34. place creature system rules

## Phase 5 — adapter and docs cleanup
35. finalize adapter placeholders
36. ensure every folder has a README
37. ensure all placeholders explain purpose and boundaries
38. verify no invented systems violate canon

---

# 15. Final Validation Checklist For Codex

Before considering the GitHub initialization complete, Codex must verify:

- the repository name is correct
- every required directory exists
- every required file exists
- all placeholder files are clearly marked
- no file invents contradictory cosmology
- no module is framed as the source of universal truth if that truth belongs in core
- adapters are documented as execution connectors, not truth owners
- ASH-first generation law is repeated in the critical files
- perception is treated as divergence, not world rewrite
- persistent geography is not framed as procedurally owned by YWE
- myth and prophecy remain distinct
- Forsetti governance language is preserved correctly

---

# 16. Codex Execution Instruction

Codex should treat this document as the direct repository creation brief.

Primary instruction:
- create the GitHub repository structure
- create all required directories
- create all listed files
- place supplied files where instructed
- create high-quality placeholders where final content is not yet supplied
- preserve architecture exactly
- do not invent contradictory mechanics
- do not collapse YWE into a generic game framework

The goal is not gameplay implementation.
The goal is a clean, extensible, implementation-ready GitHub skeleton and document layout for YWE.

---

# 17. End State Expectation

At completion, the repository should contain:
- a clean engine-first directory structure
- foundational schemas and registries
- architecture and governance docs
- the completed design stack placed into coherent locations
- module placeholders where future work remains
- adapter scaffolding for Unity, Unreal, and Godot
- enough documentation that a later coding pass can proceed without structural guessing

