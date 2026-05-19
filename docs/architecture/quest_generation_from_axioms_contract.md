# Quest Generation From Axioms Contract

Status: draft_for_phase_12_implementation  
Scope: Yggdrasil World Engine, code-agnostic contract

## Purpose

Define how YWE generates quest candidates from existential and cosmological pressure.

A quest is not arbitrary content. A quest is an actionable response to:

```text
axiom pressure
existence potential instability
branch reality divergence
player consequence history
location/worldstate mutation
plane pressure
wolf/bloodline/attunement pressure
```

## Required Inputs

```text
QuestGenerationContext
AxiomDiagnosticPacket
ExistencePotential
PatternVector
LeafBranchRealityState
PlayerRuntimeState
WorldstateDeltaPacket[]
LocationStateRecord
LocationBranchOverlay
FutureGenerationBiasUpdate[]
TruthScope
```

## Axiom Mapping

| Axiom | Quest Pressure | Candidate Quest Verbs |
|---|---|---|
| A1 Relational Existence | relation severance, isolation, exile | reconnect, witness, bind, name, reconcile |
| A2 Structural Compressibility | incoherence, noise, contradiction | decode, compress, clarify, stabilize |
| A3 Multi-Scale Persistence | identity or pattern failing across scale | preserve, echo, remember, anchor |
| A4 Energetic Cost of Erasure | cheap erasure or suppressed cost | prevent, pay, contain, transform |
| A5 Self-Reference | self-model fracture | mirror, restore, confront, integrate |
| A6 Branching Choice Realization | unresolved or divergent branch pressure | choose, reconcile, split, observe, converge |

## Generation Flow

```text
read Phase 11 location/worldstate state
read Phase 10 player state
read Phase 9 branch/axiom/pattern state
classify axiom pressure
score existence potential
select quest pressure class
build QuestGenerationContext
emit QuestManifestCandidate
validate provenance and truth scope
handoff to later quest reward/resolution systems
```

## Required Quest Candidate Properties

```text
quest_candidate_id
quest_kind
source_axiom_pressure_refs
source_branch_context_refs
source_player_context_refs
source_location_context_refs
source_worldstate_delta_refs
existence_potential_ref
pattern_vector_refs
truth_scope
expected_consequence_classes
resolution_mode_options
provenance
rejection_policy
```

## Forbidden

```text
generic_random_quest_generation
quest_without_axiom_pressure_or_consequence_context
quest_without_location_or_branch_context
quest_without_expected_consequence_classes
quest_reward_without_consequence_packet
quest_as_static_template_without_runtime_context
```
