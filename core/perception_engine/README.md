# Perception Engine

The Perception Engine manages how players perceive the world based on their cosmic state.

## Purpose

The world itself does not change. Player perception changes. The same world location can be interpreted differently depending on:

- Realm attunement
- Active realm form
- White Wolf / Dark Wolf accumulation
- Bloodline resonance
- Player narrative memory

This rule is critical for multiplayer compatibility.

## Example

Player A sees: `normal marketplace`
Player B sees: `shadow cult marketplace`

Both players are in the same location, but their perception differs based on their individual cosmic state.

## Dependencies

- Cosmology Engine (cosmic state)
- Realm Engine (realm attunement)
- Narrative Engine (player memory)
- ASH Pattern Engine (active patterns)

## Files

- `perception_schema.json` -- Data schema for perception state
- `engine_interface.json` -- Interface definition for implementations
