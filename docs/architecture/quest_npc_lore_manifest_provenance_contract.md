# Quest / NPC / Lore Manifest Provenance Contract

## Purpose

Define a shared provenance spine for all Phase 12 generated content.

## Required Provenance

```json
{
  "cosmology_source_ref": "ASH_Cosmological_Model",
  "branch_context_ref": "required",
  "player_runtime_state_ref": "required",
  "worldstate_or_location_ref": "required",
  "axiom_diagnostic_refs": "required_if_axiom_driven",
  "existence_potential_ref": "required",
  "pattern_vector_refs": "required",
  "truth_scope": "required",
  "asp_diagnostic_refs": "optional_but_recommended_for_resilience"
}
```

## Manifest Transition

Phase 12 generates candidates and exchanges. Final consequence resolution is not owned by Phase 12.

```text
QuestManifestCandidate -> Quest Reward Resolver later
NPCManifestCandidate -> NPC system later
GeneratedLoreFragment -> Lore Archive/Perception/Myth/Prophecy systems later
```
