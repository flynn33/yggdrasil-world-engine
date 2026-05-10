# Godot Adapter Interface

## Purpose

The Godot adapter translates YWE engine outputs into Godot-native implementations.

## Responsibilities

- Load and parse YWE JSON schemas into Godot Resources
- Bridge engine interface calls to Godot Node classes
- Translate realm overlay data into Godot scene modifications
- Map perception engine outputs to Godot rendering changes

## Implementation Guidelines

- Use GDScript or C# with Godot APIs
- Use Godot Resources for data-driven content
- Use Godot's scene/node system for entity management
- Follow Godot naming conventions and project structure patterns

## Dependencies

- YWE core engine interfaces (from `core/*/engine_interface.json`)
- YWE data schemas (from `data/`)

## ASH Materialization Boundary Addendum

This adapter consumes `GenerationPlan`, `CosmicPatternSnapshot`, and `DiagnosticEnvelope` records emitted by the ASH-governed YWE core. It may materialize host objects, visuals, scenes, or entities from those records, but it must not author ASH truth or YWE domain truth.

Required carried references: `generation_plan_ref`, `cosmic_pattern_snapshot_ref`, `diagnostic_ref`, and `source_ash_refs`. Any adapter-side failure returns a host diagnostic linked to the originating `DiagnosticEnvelope`.
