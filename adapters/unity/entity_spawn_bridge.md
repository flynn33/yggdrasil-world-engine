# Unity Entity Spawn Bridge

## Purpose

Bridges YWE creature and entity generation into Unity's instantiation and prefab systems.

## Responsibilities

- Translate creature engine outputs into Unity prefab instantiation
- Map artifact properties to Unity GameObject components
- Handle NPC variant spawning based on perception engine output
- Manage entity lifecycle (spawn, interact, despawn)

## Unity Implementation Notes

- Use Unity prefab system for entity templates
- Use object pooling for frequently spawned entities
- Entity properties should be driven by YWE data, not hardcoded
- Support realm-specific entity variants through prefab variants or material swaps
