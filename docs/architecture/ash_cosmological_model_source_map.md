# ASH Cosmological Model Source Map

Status: `recommended_repository_alignment_artifact`  
Version: `0.1.0`

## Purpose

This document maps ASH Cosmological Model source concepts into the Yggdrasil World Engine repository so systems can align without redefining the cosmology.

Scope note: named WRW concepts below are informative cross-scope routing
examples only. They do not establish YWE Core requirements; authority remains
with `docs/architecture/ywe_core_wrw_scope_contract.md`.

## Source concept map

| Source concept | Repository interpretation |
|---|---|
| Where Ravens Wait Universal Lore Archive | Source-family authority for game/narrative cosmology concepts that must be separated from engine contracts. |
| Nine planes of existence | Base world ontology and plane-pressure interpretation. |
| Axioms A1-A6 | Existence validity, quest pressure, branch event, and narrative coherence rules. |
| Existence potential Φ | Stability/coherence/collapse pressure scoring model. |
| Pattern vectors | Compact identity/state representation for beings, locations, artifacts, wolves, myths. |
| Branching choice realization | Player-driven leaf branch reality generation. |
| Wolf attractor logic | Twin wolf companion/resonance system, not morality. |
| Bloodline resonance | Eligibility and echo system, not destiny lock. |
| Shadow / Void / Divine Core | Containment, entropy/unstructured information, and rule-source architecture. |
| Leaf branch realities | Runtime branch possibility space generated from choices and cosmological conditions. |

## Repository target areas

```text
docs/architecture/ywe_cosmology_authority_contract.md
docs/architecture/leaf_branch_reality_contract.md
docs/architecture/worldstate_location_mutation_v1.md
data/schemas/pattern_vector_schema.json
data/schemas/existence_potential_schema.json
data/schemas/branch_event_schema.json
data/schemas/player_runtime_state_schema.json
```

## Non-destructive rule

This source map should not force immediate implementation of all target schemas. It should provide alignment so future design packages can proceed safely.
