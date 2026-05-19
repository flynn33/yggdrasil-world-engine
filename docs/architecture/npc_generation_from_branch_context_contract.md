# NPC Generation From Branch Context Contract

Status: draft_for_phase_12_implementation  
Scope: Yggdrasil World Engine, code-agnostic contract

## Purpose

Define how YWE generates meaningful NPC candidates from branch reality, player state, location state, relation graph, axiom pressure, and existence potential.

## NPC Definition

A meaningful NPC is a relational manifestation with a role in the current world/branch context.

## Required Inputs

```text
NPCGenerationContext
LeafBranchRealityState
PlayerRuntimeState
PlayerMemoryRecord[]
WorldstateDeltaPacket[]
LocationStateRecord
LocationBranchOverlay
AxiomDiagnosticPacket[]
ExistencePotential
PatternVector
TruthScope
RelationGraph
SelfReferenceState
```

## NPC Role Classes

```text
witness
keeper
guide
opponent
threshold_guardian
branch_survivor
relation_restorer
memory_carrier
lore_bearer
quest_anchor
self_reference_mirror
faction_interpreter
myth_seed_carrier
prophecy_vector
shadow_containment_agent
void_noise_remnant
```

## Consciousness Requirement

If an NPC is conscious, it must include a self-reference classification.

```text
self_reference_state:
  none
  latent
  partial
  active
  fractured
  mirrored
  restored
```

## Relation Requirement

Meaningful NPCs must participate in at least one relation.

```text
relation_to_player
relation_to_location
relation_to_branch
relation_to_faction
relation_to_quest
relation_to_lore
relation_to_axiom_pressure
```

## Forbidden

```text
npc_without_relation_context
npc_without_branch_or_location_context
conscious_npc_without_self_reference_classification
npc_spawn_table_as_primary_meaning_source
npc_dialogue_as_shared_truth_without_truth_scope
```
