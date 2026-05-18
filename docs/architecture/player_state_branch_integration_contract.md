# Player State and Branch Integration Contract

## Purpose

This contract defines how Player Runtime State integrates with leaf branch reality without replacing it.

## Separation of responsibility

```text
LeafBranchRealityState
  owns branch identity, parentage, branch event origin, branch overlays, and branch-level generation context.

PlayerRuntimeState
  owns player identity, player memory, player resonance, player progression, and current branch reference.
```

## Required references

PlayerRuntimeState must include:

```text
current_leaf_branch_ref
current_branch_generation_context_ref
branch_history_refs
branch_event_refs
future_generation_bias_refs
```

## Branch history

Branch history must not embed pre-generated branch trees; it must be represented as references.

A valid branch history record should include:

```text
branch_event_ref
leaf_branch_ref
chosen_action
source_action_trace_ref
resulting_worldstate_delta_refs
resulting_player_state_update_refs
```

## Forbidden

```text
pre_generated_branch_tree
player_state_owning_all_branch_data
branch_without_branch_event
branch_without_player_context
branch_without_cosmological_provenance
```
