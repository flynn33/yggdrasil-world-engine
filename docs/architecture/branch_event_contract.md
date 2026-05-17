# Branch Event Contract

## Purpose

A BranchEvent records a meaningful player choice that creates or mutates a leaf branch reality.

## BranchEvent eligibility

A player action is a BranchEvent only when it has meaningful consequence across at least one of these domains:

```text
worldstate
location state
plane attunement
bloodline resonance
wolf resonance
quest chain
NPC relationship
artifact binding
myth pressure
prophecy pressure
perception state
future generation bias
```

## Required fields

Each BranchEvent must include:

```text
branch_event_id
agent_ref
decision_context
available_actions
chosen_action
choice_significance
base_world_ref
parent_branch_ref
location_state_ref
player_context_ref
cosmology_source_refs
asp_component_refs
worldstate_delta_refs
future_generation_bias_refs
```

## Branch weights

Branch weights may be recorded to describe alternative potentials, but the player's experienced leaf branch is determined by the chosen action and runtime generation context.

Branch weights must not be used to pre-generate a fixed branch tree.

## Relation to A6

BranchEvent is the YWE runtime representation of branching choice realization.

## Forbidden interpretations

```text
every input action is a branch event
branch event as randomizer only
branch event without player consequence
branch event without cosmology provenance
branch event that mutates base ontology
branch event that bypasses ASP diagnostics where required
```
