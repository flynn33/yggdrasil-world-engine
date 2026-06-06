# Lore Generation From Pattern Trace Contract

Status: draft_for_phase_12_implementation  
Scope: Yggdrasil World Engine, code-agnostic contract

## Purpose

Define how YWE generates lore fragments from pattern traces, branch records, worldstate deltas, location state, axiom pressure, and player discovery context.

## Principle

```text
Pattern first. Text second.
```

YWE may generate text, inscriptions, lore archive entries, testimonies, visions, dreams, and records only after a valid pattern trace and truth scope exist.

## Required Inputs

```text
LoreGenerationContext
LorePatternTrace
AxiomDiagnosticPacket[]
ExistencePotential
PatternVector[]
WorldstateDeltaPacket[]
LocationStateRecord
LocationBranchOverlay
PlayerRuntimeState
TruthScope
VisibilityRule
```

## Lore Fragment Kinds

```text
lore_archive_entry
location_memory
branch_record
npc_testimony
artifact_inscription
dream_fragment
vision_fragment
myth_seed
prophecy_hint
faction_claim_record
witness_record
hidden_oath_record
```

## Required Lore Fragment Fields

```text
lore_fragment_id
lore_kind
pattern_trace_ref
source_axiom_pressure_refs
source_worldstate_delta_refs
source_branch_refs
source_location_refs
source_player_action_refs
truth_scope
visibility_conditions
stability_classification
myth_eligibility
prophecy_eligibility
generated_text_policy
provenance
```

## Forbidden

```text
random_lore_text_as_canon
lore_without_pattern_trace
lore_without_truth_scope
lore_that_rewrites_shared_truth_without_worldstate_delta
prophecy_lore_that_guarantees_future
myth_lore_that_rewrites_history_without_evidence
```
