# Location Branch Overlay Contract

## Purpose

A LocationBranchOverlay represents how a location resolves inside a specific player leaf branch without rewriting the base world ontology.

## Example

```text
Base Ravenfall Gate:
  physical ruin / marketplace threshold

Player Branch A:
  oath publicly revealed
  witness NPC eligibility opens
  public myth seed begins

Player Branch B:
  oath concealed
  hidden Shadow path opens
  keeper NPC eligibility opens

Player Branch C:
  oath bound
  Yggdrasil threshold stabilizes
  twin-wolf coherence pressure increases
```

## Overlay fields

A branch overlay should define:

```text
overlay_id
location_id
branch_id
truth_scope
source_delta_refs
source_branch_event_ref
player_state_snapshot_ref
visible_changes
access_changes
eligibility_changes
perception_changes
myth_pressure_refs
prophecy_pressure_refs
future_generation_bias_refs
```

## Rules

```text
branch overlays are player-specific
branch overlays may alter access, visibility, eligibility, interpretation, and resolved state
branch overlays must not claim to rewrite base ontology
branch overlays must not become pregenerated branch trees
branch overlays must be generated from player action and consequence history
```

## Forbidden

```text
prebuilt exhaustive branch tree
static-only location model
branch overlay without branch reference
branch overlay without delta or diagnostic provenance
branch overlay rewriting base world truth
branch overlay treating perception as shared truth
```
