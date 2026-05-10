# Semantic Contracts for Future Implementations

## Authority status

This contract layer is authoritative for module-level implementation behavior within the current 9D foundation.

**Codeword-set closure**: The codeword set `C ⊂ F2^9` is fully closed as a [9, 4, 4] doubly-even linear code with 16 members, defined in `specs/core/codeword-set.pseudo.md`. Implementations must use exactly the specified codeword set and must not invent or extend codewords.

## Umbrella contract document

This file is the **umbrella contract document** for the ASH Pattern System. It lists the required semantic modules and references the detailed contract files.

## Required semantic modules

Every downstream implementation must provide semantic equivalents of the following modules:

| # | Module | Detailed contract |
|---|--------|------------------|
| 1 | `StateModel` | `contracts/state-model-contract.md` |
| 2 | `RealmEncoder` | `contracts/realm-encoder-contract.md` |
| 3 | `TransitionRegistry` | `contracts/transition-registry-contract.md` |
| 4 | `TopologyGenerator` | `contracts/topology-generator-contract.md` |
| 5 | `AxiomEvaluator` | `contracts/axiom-evaluator-contract.md` |
| 6 | `GenerationPlanner` | `contracts/generation-planner-contract.md` |
| 7 | `ArtifactEmitter` | `contracts/artifact-emitter-contract.md` |
| 8 | `Diagnostics` | `contracts/diagnostics-module-contract.md` |
| 9 | `RecoveryEngine` | `contracts/recovery-engine-contract.md` |

## Materialization boundary (locked)

The boundary between `GenerationPlanner` and `ArtifactEmitter` is a **locked design decision**:

- `GenerationPlanner` produces an abstract, target-aware but non-materialized plan. It must not emit artifacts or perform side effects.
- `ArtifactEmitter` materializes that plan for a target runtime/platform. It must not invent semantics not present in the plan.
- The plan is the sole interface between planner and emitter.
- Planning and materialization must not be collapsed into a single opaque step.

## Canonical algebraic conformance

A downstream implementation **must**:

- treat the full F2^9 state space as canonical
- use XOR-by-codeword transformations as the canonical state transformation mechanism
- use the canonical 16-member codeword set defined in `specs/core/codeword-set.pseudo.md`
- use full 9-bit state admissibility (see `specs/core/state-admissibility.pseudo.md`)
- preserve full-state canonical processing throughout diagnosis, recovery, and transition behavior

## Mandatory registry, schema, and taxonomy conformance

- Fallback selection must use the canonical fallback-policy registry (`specs/registries/fallback-policy-registry.md`)
- All diagnostics must conform to the shared diagnostic schema (`specs/interfaces/diagnostic-schema.md`)
- All rule IDs must conform to the canonical taxonomy (`specs/interfaces/rule-id-taxonomy.md`)

## Prohibited shortcuts

A downstream implementation must not:

- treat syntax as the source of truth over semantics
- skip normalization before encoding or transition application
- collapse planning and materialization into one opaque semantic step
- replace semantic validation with superficial metadata checks
- bypass full-state admissibility classification
- silently treat a transformation-incompatible state as valid
- invent module behavior not grounded in the canonical specifications
- substitute alternate state decompositions for canonical processing

## Portability rule

Implementations may differ in syntax, packaging, runtime model, memory layout, and tooling.
They may not differ in the semantic behavior defined by this repository and its contract files.
