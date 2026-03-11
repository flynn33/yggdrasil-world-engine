# Godot Entity Spawn Bridge

## Purpose

Bridges YWE creature and entity generation into Godot's Node instantiation system.

## Responsibilities

- Translate creature engine outputs into Godot Node/PackedScene instantiation
- Map artifact properties to Godot node properties
- Handle NPC variant spawning based on perception engine output
- Manage entity lifecycle through Godot's scene tree

## Godot Implementation Notes

- Use PackedScene for entity templates
- Use object pooling for frequently spawned entities
- Entity properties should be driven by YWE data via Resources
- Support realm-specific entity variants through shader parameters or scene variants
