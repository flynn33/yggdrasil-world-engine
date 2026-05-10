# Unreal Environment Bridge

## Purpose

Handles generation and lifecycle of temporary narrative environments in Unreal Engine.

## Scope

YWE only generates temporary narrative environments, not persistent world geography.

## Lifecycle

```
generate -> instantiate -> play -> resolve -> dissolve
```

## Unreal Implementation Notes

- Use Unreal level streaming for environment lifecycle
- Use Procedural Content Generation (PCG) framework where appropriate
- Environment parameters come from YWE pattern data
- Dissolve phase should properly unload and garbage collect level assets

## ASH Materialization Boundary Addendum

This adapter consumes `GenerationPlan`, `CosmicPatternSnapshot`, and `DiagnosticEnvelope` records emitted by the ASH-governed YWE core. It may materialize host objects, visuals, scenes, or entities from those records, but it must not author ASH truth or YWE domain truth.

Required carried references: `generation_plan_ref`, `cosmic_pattern_snapshot_ref`, `diagnostic_ref`, and `source_ash_refs`. Any adapter-side failure returns a host diagnostic linked to the originating `DiagnosticEnvelope`.
