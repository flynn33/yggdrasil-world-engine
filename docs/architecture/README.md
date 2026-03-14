# Architecture Documentation

## Engine-First Architecture

The Yggdrasil World Engine is organized as an engine-first architecture. The root engine defines cosmology and procedural truth. Additional systems are implemented as separate engines/modules.

## Core Engines

| Engine | Purpose |
|--------|---------|
| Cosmology Engine | Origin of gravity, reality, and the nine realms |
| Realm Engine | Fixed cosmological state management and player attunement |
| ASH Pattern Engine | Cosmic pattern detection driving all procedural generation |
| Narrative Engine | Player-specific story transformation and memory |
| Perception Engine | Player perception overlay based on cosmic state |

## Expansion Engines (Modules)

| Module | Purpose |
|--------|---------|
| Quest Engine | Quest generation from cosmic patterns |
| Myth Engine | Myth formation from significant events |
| Prophecy Engine | Future narrative attractors and probability weights |
| Artifact Engine | Artifact generation and management |
| Creature Engine | Creature generation and behavior |

## Future Expansion Engines

The architecture supports additional engines:
- Civilization Engine
- Economy Engine
- Religion Engine
- Faction Engine
- Politics Engine

All expansion engines must read from the Cosmic Pattern Engine. No module may generate meaningful content independently.

## Control Documents

- `authored_override_and_tooling_notes.md` -- Canonical authored override authority order, allowed/forbidden override categories, and tooling guardrails
- `realm_truth_boundary_contract.md` -- Canonical separation contract for realm truth, perception, myth, prophecy, faction claims, and authored overrides

## Dependency Direction

All modules read from the same cosmic state. The dependency flow is:

```
Cosmology Engine (root)
  -> Realm Engine
  -> ASH Pattern Engine
    -> Narrative Engine
    -> Perception Engine
      -> Quest Engine
      -> Myth Engine
      -> Prophecy Engine
      -> Artifact Engine
      -> Creature Engine
```

No reverse dependencies. No circular dependencies.
