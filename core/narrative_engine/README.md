# Narrative Engine

The Narrative Engine transforms cosmic patterns into player-specific story.

## Purpose

Manages the narrative loop that converts ASH patterns into personalized player experiences, stores player narrative memory, and drives the myth formation pipeline.

## Narrative Loop

```
ASH state
  -> cosmic pattern
  -> player interpretation
  -> quest manifestation
  -> consequence memory
  -> myth formation
  -> prophecy generation
```

## Player Narrative Memory

Each player stores interpretation-specific memory that changes future dialogue, quests, and myth perception.

Example:
```json
{
  "player_memory": {
    "ravenfall_gate": "sealed_by_player",
    "shadow_keeper_trusted": true,
    "artifact_4512_status": "hidden"
  }
}
```

## Dependencies

- Cosmology Engine (cosmic state)
- Realm Engine (realm context)
- ASH Pattern Engine (detected patterns)

## Files

- `narrative_schema.json` -- Data schema for narrative state
- `engine_interface.json` -- Interface definition for implementations
