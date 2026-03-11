# Quest Engine -- Module Description

## Responsibility

Generate and manage quests derived from ASH cosmic patterns. Quests are the primary gameplay loop through which players gain realm attunement, wolf alignment, and narrative consequences.

## Inputs

- `PatternNode[]` from ASH Pattern Engine
- `PlayerState` including attunement, alignment, bloodline, and memory
- `RealmContext` from Realm Engine

## Outputs

- `QuestSeed` -- generated quest definitions
- `QuestCompletionResult` -- consequences of quest completion
- Alignment gains (White Wolf / Dark Wolf)
- Realm attunement gains
- Narrative memory updates
- Myth eligibility flags
- Prophecy weight adjustments

## Rules

1. All quests must derive from ASH patterns -- no independent random generation.
2. Every quest must support at least two completion paths.
3. Each completion path must grant different alignment and attunement results.
4. Quest consequences must be recorded in player narrative memory.
5. Significant quest completions must be evaluated for myth eligibility.

## Future Extensions

- Quest chains (linked quest sequences)
- Faction-specific quest interpretations
- Multiplayer cooperative quests
- Realm-specific quest modifiers
