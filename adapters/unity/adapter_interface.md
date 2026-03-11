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
