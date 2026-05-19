# Shared Truth vs Branch Truth Contract

## Purpose

This contract separates base ontology, shared world truth, player-specific branch truth, perception, myth, prophecy, faction belief, and host materialization.

## Truth scopes

| Scope | Meaning |
|---|---|
| `base_world_truth` | The nine-plane ontology and cosmological substrate. Not changed by player action. |
| `shared_world_truth` | Persistent world facts shared by a relevant world or campaign context. |
| `leaf_branch_truth` | Truth inside a specific player-generated leaf branch. |
| `player_perception` | What the player senses, sees, dreams, or interprets. |
| `mythic_interpretation` | Cultural or narrative memory formed around evidence. |
| `prophetic_pressure` | Future-facing attractor or pressure, not a guaranteed script. |
| `faction_claim` | What a faction believes, asserts, hides, or disputes. |
| `host_materialization` | Runtime presentation by a platform adapter. |
| `diagnostic_noop` | Explicitly evaluated event with no persistent consequence. |

## Core rule

```text
Perception, myth, prophecy, and faction claim may alter interpretation, eligibility, and presentation. They do not automatically rewrite shared world truth.
```

## Base world boundary

The base world ontology is not mutated by player action. Players can create leaf branch realities and alter location state inside those branches, but they do not redefine the nine planes or the ASH Cosmological Model.

## Host boundary

Host adapters materialize approved manifests and resolved states. They do not author truth.
