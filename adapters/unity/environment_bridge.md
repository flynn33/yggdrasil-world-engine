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
- Procedural generation should use Unity's built-in terrain or mesh systems
- Environment parameters come from YWE pattern data
- Dissolve phase should clean up all scene objects
