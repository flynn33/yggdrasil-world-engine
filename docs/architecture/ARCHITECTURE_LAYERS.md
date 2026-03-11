# Architecture Layers

The Yggdrasil World Engine follows the Forsetti Framework's layered architecture pattern.

## Layer Hierarchy

```
Core <- Data <- Runtime <- Presentation <- Editor
```

| Layer | Responsibility | Depends On |
|-------|---------------|------------|
| **Core** | Engine interfaces, cosmology rules, pattern detection logic, invariants | Nothing |
| **Data** | JSON schemas, data loading, registry parsing, data models | Core |
| **Runtime** | Quest generation, myth formation, prophecy tracking, creature spawning | Core, Data |
| **Presentation** | Realm overlays, perception rendering, UI integration, temporary environments | Core, Data, Runtime |
| **Editor** | Build tools, inspectors, world builders, testing utilities | All above |

## Rules

1. **One-way dependencies only.** A lower layer must never import from a higher layer.
2. **No circular dependencies.** Direct or indirect cycles are forbidden.
3. **Core is pure.** No engine-specific code, no rendering, no UI.
4. **Data is passive.** Data layer loads and validates; it does not generate content.
5. **Runtime drives generation.** All procedural generation happens at the Runtime layer, reading from Core logic and Data schemas.
6. **Presentation is host-specific.** This is where engine adapters (Unity, Unreal, Godot) live.
7. **Editor is optional.** Tools and inspectors for development; not required for runtime.

## Enforcement

- Architecture validation scripts check dependency direction
- CI workflows block merges on layer violations
- Engine interface definitions enforce contract boundaries
