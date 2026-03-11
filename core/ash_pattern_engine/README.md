# ASH Pattern Engine

The ASH Pattern Engine is the central procedural generation system. All meaningful content in the Yggdrasil World Engine originates from ASH cosmological state analysis.

## Purpose

Detects cosmic patterns from the current ASH state and provides them to all other engines for content generation. No subsystem may generate meaningful content independently of the cosmic state.

## Core Rule

All procedural systems must derive from **ASH Pattern Detection**. No subsystem may become an independent random generator detached from the cosmic state.

## Pattern Detection

Patterns are detected from the current cosmic state and provide seeds for:

- Quests
- Artifacts
- Creatures
- Myths
- Prophecies
- Narrative spaces

## Pattern Schema

```json
{
  "pattern_id": "PTN_00451",
  "type": "hidden_knowledge",
  "realm_bias": "shadow",
  "strength": 0.72
}
```

## Dependencies

- Cosmology Engine (cosmic state)
- Realm Engine (realm bias calculations)

## Files

- `pattern_engine_schema.json` -- Data schema for pattern nodes
- `engine_interface.json` -- Interface definition for implementations
