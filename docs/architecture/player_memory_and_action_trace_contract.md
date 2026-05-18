# Player Memory and Action Trace Contract

## Purpose

Player memory and action traces preserve the player's meaningful history so future generation can respond to what the player has actually done.

## Action trace rule

Not every input is a PlayerActionTrace.

A PlayerActionTrace should be created only when an action has meaningful systemic consequence, such as:

```text
branch creation
quest resolution
oath made or broken
truth revealed or concealed
artifact bound
bloodline awakened
wolf resonance shifted
plane threshold crossed
NPC relationship changed
faction standing changed
myth seeded
prophecy pressure changed
location state changed
```

## Memory record rule

Player memory records are references to meaningful events, not prose dumps.

They may include:

```text
memory_id
memory_kind
source_action_trace_ref
branch_ref
location_ref
affected_entities
cosmological_tags
visibility_state
source_refs
```

## Use by later systems

Later systems may use action traces and memories to generate:

```text
quests
NPC reactions
lore fragments
location mutations
myths
prophecies
ability pressure
wolf manifestations
bloodline echoes
```

## Forbidden

```text
future_generation_without_history
memory_as_unverified_world_truth
minor_input_spam_as_action_trace
prose_only_memory_without_system_refs
```
