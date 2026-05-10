# Unity Environment Bridge

## Purpose

Handles generation and lifecycle of temporary narrative environments in Unity.

## Scope

YWE only generates **temporary narrative environments**, not persistent world geography. Examples:

- Vision realms
- Celestial trials
- Shadow labyrinths
- Ancestral memories
- Prophecy chambers
- Awakening quests

## Lifecycle

```
generate -> instantiate -> play -> resolve -> dissolve
```

## Unity Implementation Notes

- Use Unity scene loading/unloading for environment lifecycle
- Environment materialization should use Unity's built-in terrain or mesh systems
- Environment parameters come from YWE pattern data
- Dissolve phase should clean up all scene objects

## ASH Materialization Boundary Addendum

This adapter consumes `GenerationPlan`, `CosmicPatternSnapshot`, and `DiagnosticEnvelope` records emitted by the ASH-governed YWE core. It may materialize host objects, visuals, scenes, or entities from those records, but it must not author ASH truth or YWE domain truth.

Required carried references: `generation_plan_ref`, `cosmic_pattern_snapshot_ref`, `diagnostic_ref`, and `source_ash_refs`. Any adapter-side failure returns a host diagnostic linked to the originating `DiagnosticEnvelope`.
