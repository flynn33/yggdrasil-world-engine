# Quest Engine

The Quest Engine generates quests from cosmic patterns detected by the ASH Pattern Engine.

## Purpose

Quests are not random templates. They are generated from ASH state through pattern detection and player interpretation. Every quest must support multiple completion paths, each granting different alignment gains, realm attunement, and narrative consequences.

## Quest Generation Flow

```
ASH state
  -> pattern detection
  -> player interpretation
  -> quest manifestation
```

## Quest Completion Modes

Every quest must support multiple completion paths. Example:

- **Reveal truth** -- grants White Wolf alignment
- **Hide truth** -- grants Dark Wolf alignment
- **Weaponize truth** -- grants both alignments with different realm attunement

Each path grants different:
- White Wolf gains
- Dark Wolf gains
- Realm attunement
- Myth consequences
- Prophecy weights

## Dependencies

- ASH Pattern Engine (pattern seeds)
- Narrative Engine (player interpretation)
- Realm Engine (realm-aligned quest context)

## Files

- `module_description.md` -- Detailed module specification
- `quest_engine_interface.json` -- Interface definition for implementations
