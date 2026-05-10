# Unreal Entity Spawn Bridge

## Purpose

Bridges YWE creature and entity generation into Unreal's Actor spawning systems.

## Responsibilities

- Translate creature engine outputs into Unreal Actor/Pawn spawning
- Map artifact properties to Unreal components
- Handle NPC variant spawning based on perception engine output
- Manage entity lifecycle through Unreal's Actor lifecycle

## Unreal Implementation Notes

- Use Unreal Actor/Pawn classes for entity templates
- Use object pooling for frequently spawned entities
- Entity properties should be driven by YWE data via DataAssets
- Support realm-specific entity variants through material instances or mesh swaps

## ASH Materialization Boundary Addendum

This adapter consumes `GenerationPlan`, `CosmicPatternSnapshot`, and `DiagnosticEnvelope` records emitted by the ASH-governed YWE core. It may materialize host objects, visuals, scenes, or entities from those records, but it must not author ASH truth or YWE domain truth.

Required carried references: `generation_plan_ref`, `cosmic_pattern_snapshot_ref`, `diagnostic_ref`, and `source_ash_refs`. Any adapter-side failure returns a host diagnostic linked to the originating `DiagnosticEnvelope`.
