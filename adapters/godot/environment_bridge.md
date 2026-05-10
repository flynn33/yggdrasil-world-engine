# Godot Environment Bridge

## Purpose

Handles generation and lifecycle of temporary narrative environments in Godot.

## Scope

YWE only generates temporary narrative environments, not persistent world geography.

## Lifecycle

```
generate -> instantiate -> play -> resolve -> dissolve
```

## Godot Implementation Notes

- Use Godot scene loading/unloading for environment lifecycle
- Use host-side environment materialization via GDScript or C#
- Environment parameters come from YWE pattern data
- Dissolve phase should free all scene nodes and resources

## ASH Materialization Boundary Addendum

This adapter consumes `GenerationPlan`, `CosmicPatternSnapshot`, and `DiagnosticEnvelope` records emitted by the ASH-governed YWE core. It may materialize host objects, visuals, scenes, or entities from those records, but it must not author ASH truth or YWE domain truth.

Required carried references: `generation_plan_ref`, `cosmic_pattern_snapshot_ref`, `diagnostic_ref`, and `source_ash_refs`. Any adapter-side failure returns a host diagnostic linked to the originating `DiagnosticEnvelope`.
