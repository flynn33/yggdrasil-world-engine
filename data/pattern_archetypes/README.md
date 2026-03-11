# Pattern Archetypes

Contains pattern node schemas and archetype definitions for the ASH Pattern Engine.

## Pattern Node Schema

See `pattern_schema.json` for the base schema.

Pattern nodes represent detected cosmic patterns that drive all procedural generation in the engine.

## Fields

- `pattern_id` -- Unique identifier for the pattern
- `type` -- The type of pattern (e.g., hidden_knowledge, revelation, cosmic_imbalance)
- `realm_bias` -- Which realm this pattern is most associated with
- `strength` -- Pattern strength from 0 to 1
