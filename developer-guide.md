# Yggdrasil World Engine -- Developer Guide

This guide is for contributors extending the YWE specification and for teams preparing separate downstream implementations after M10 acceptance.

## 1. Understanding the Repository

Every branch in this repository is platform-neutral specification work. The `main` branch is the current accepted repository baseline and contains:

- Engine interface definitions (`core/*/engine_interface.json`)
- Data schemas (`data/`)
- Cosmological lore (`lore/`)
- Adapter specifications (`adapters/`)
- Documentation (`docs/`)
- Governance files (`guide.md`, `wiki.md`, `repository-contribution-policy.json`, `yggdrasil-instructions.json`)

No platform-specific runtime code belongs on any branch in this repository.

## 2. Preparing a Downstream Engine Implementation

1. After M10 acceptance and explicit authorization, create a separate downstream product repository for the target host.
2. Read all engine interfaces in `core/*/engine_interface.json`.
3. Read the data schemas in `data/`.
4. Read the ASH compliance rules in `docs/ash_compliance/`.
5. Implement each engine interface in that downstream repository using native host idioms.

## 3. Implementation Rules

### Use Native Idioms

| Engine | Language | Patterns |
|--------|----------|----------|
| Unity | C# | MonoBehaviours, ScriptableObjects, Assembly Definitions |
| Unreal | C++ | UObjects, Blueprints, Modules |
| Godot | GDScript/C# | Nodes, Resources, Scenes |

### Respect Layer Boundaries

```
Core <- Data <- Runtime <- Presentation <- Editor
```

Lower layers must never depend on higher layers.

### ASH-Derived Generation Compliance

All meaningful procedural generation must derive from ASH Model-grounded state,
diagnostics, codeword traces, generation plans, and YWE interpretation
contracts. Do not create independent random generators for meaningful content.

## 4. Data Loading

The `data/` directory contains JSON schemas plus canonical YAML rule artifacts. Your engine implementation should:

1. Parse these JSON schemas into engine-native data structures.
2. Load canonical YAML rule artifacts from `data/perception/`, `data/realm/`, `data/faction_topology/`, and `data/module_capability/`, including `data/module_capability/manifests/*.yaml`, as authoritative design inputs.
3. Validate data against schemas and rule contracts at load time.
4. Use the data to drive engine behavior -- do not hardcode values.

## 5. Adapter Implementation

The `adapters/` directory contains specifications for each engine adapter. Your implementation should follow these specifications for:

- Environment generation hooks (temporary narrative environments)
- Entity spawning bridges (creatures, NPCs, artifacts)
- UI integration (realm overlays, perception changes)

## 6. Testing

Every engine implementation should include tests for:

- Cosmological invariant preservation (nine-coordinate structure, explicit realm mappings, and wolf rules)
- Engine interface compliance
- Data schema validation
- ASH pattern generation compliance
- Layer dependency enforcement

## 7. Validation

Before submitting any pull request:

1. Install dependencies with `python3 -m pip install -r scripts/requirements.txt`.
2. Run `bash scripts/run_checks.sh` from the repository root.
3. Verify all JSON schemas are valid.
4. Verify canonical YAML/doc artifact checks pass.
5. Verify no ASH compliance violations.
6. Verify no layer boundary violations.

PowerShell environments may use `pwsh -File scripts/run_checks.ps1` where
available. Both wrappers invoke the same canonical check catalog.
