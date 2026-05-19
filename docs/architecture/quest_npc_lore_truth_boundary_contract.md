# Quest / NPC / Lore Truth Boundary Contract

## Purpose

Prevent generated quests, NPCs, and lore from incorrectly rewriting truth.

## Truth Scopes

```text
base_world_truth
shared_world_truth
leaf_branch_truth
player_perception
mythic_interpretation
prophetic_pressure
faction_claim
host_materialization
```

## Rules

- A quest can ask the player to reveal, conceal, bind, study, or weaponize truth, but the actual truth mutation must happen through worldstate/location systems.
- An NPC may believe, lie, misunderstand, testify, prophesy, or remember, but that does not automatically make the claim shared truth.
- A lore fragment may record myth, prophecy, perception, or faction belief, but must label its truth scope.
- Prophecy is pressure, not a guaranteed script.
- Myth is cultural/pattern memory, not automatic historical overwrite.

## Required Validation

Generated content must include:

```text
truth_scope
source_context_refs
provenance
worldstate_delta_refs when shared truth changes
DiagnosticNoOp when no persistent change occurs
```
