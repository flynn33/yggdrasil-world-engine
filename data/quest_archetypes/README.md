# Quest Archetypes

Contains quest seed schemas and archetype definitions for the Quest Engine.

## Quest Seed Schema

See `quest_seed_schema.json` for the base schema.

Quest seeds are generated from cosmic patterns and define the structure of a quest, including available interpretation paths.

## Fields

- `quest_seed_id` -- Unique identifier for the quest seed
- `pattern_id` -- The cosmic pattern that generated this quest
- `interpretations` -- Available completion paths (e.g., reveal, conceal, study)
