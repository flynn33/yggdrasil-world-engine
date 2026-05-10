# Unity Adapter Interface

## Purpose

The Unity adapter translates YWE engine outputs into Unity-native implementations.

## Responsibilities

- Load and parse YWE JSON schemas into Unity data structures (ScriptableObjects or similar)
- Bridge engine interface calls to Unity MonoBehaviours and systems
- Translate realm overlay data into Unity scene modifications
- Map perception engine outputs to Unity rendering changes

## Implementation Guidelines

- Use native C# and Unity APIs
- Use ScriptableObjects for data-driven content
- Use Assembly Definitions for layer boundary enforcement
- Use the Unity Job System for performance-critical paths where appropriate
- Follow Unity naming conventions and project structure patterns

## Dependencies

- YWE core engine interfaces (from `core/*/engine_interface.json`)
- YWE data schemas (from `data/`)

## ASH Materialization Boundary Addendum

This adapter consumes `GenerationPlan`, `CosmicPatternSnapshot`, and `DiagnosticEnvelope` records emitted by the ASH-governed YWE core. It may materialize host objects, visuals, scenes, or entities from those records, but it must not author ASH truth or YWE domain truth.

Required carried references: `generation_plan_ref`, `cosmic_pattern_snapshot_ref`, `diagnostic_ref`, and `source_ash_refs`. Any adapter-side failure returns a host diagnostic linked to the originating `DiagnosticEnvelope`.
