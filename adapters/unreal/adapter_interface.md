# Unreal Adapter Interface

## Purpose

The Unreal adapter translates YWE engine outputs into Unreal-native implementations.

## Responsibilities

- Load and parse YWE JSON schemas into Unreal data structures (DataTables, DataAssets)
- Bridge engine interface calls to Unreal C++ classes and Blueprints
- Translate realm overlay data into Unreal level/sublevel modifications
- Map perception engine outputs to Unreal rendering and material changes

## Implementation Guidelines

- Use native C++ and Unreal APIs
- Use DataTables and DataAssets for data-driven content
- Use Unreal Module system for layer boundary enforcement
- Follow Unreal naming conventions and project structure patterns

## Dependencies

- YWE core engine interfaces (from `core/*/engine_interface.json`)
- YWE data schemas (from `data/`)
