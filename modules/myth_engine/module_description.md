# Myth Engine -- Module Description

## Responsibility

Transform significant narrative events into persistent mythology. Myths shape the world's cultural landscape and influence future content generation.

## Inputs

- `NarrativeEvent` (myth-eligible events from the Narrative Engine)
- `FactionContext` (faction perspectives for variant myth generation)
- `PatternNode` (cosmic context for myth theming)

## Outputs

- `MythRecord` -- generated myth with title, source event, and faction versions
- World content updates (books, songs, inscriptions, rumors)
- Future quest influence weights

## Rules

1. Myths derive from significant narrative events, not random generation.
2. Different factions may produce different versions of the same myth.
3. Myths persist permanently in the world once generated.
4. Myths influence future quest generation through the ASH Pattern Engine.

## Myth Record Schema

```json
{
  "myth_id": "",
  "source_event": "",
  "title": "",
  "faction_versions": {}
}
```
