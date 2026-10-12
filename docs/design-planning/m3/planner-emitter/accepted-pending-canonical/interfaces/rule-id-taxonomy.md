# Rule-ID Taxonomy — canonical specification (Canonical Baseline)

## Purpose

This specification defines the **canonical structure and governance for rule identifiers** across the ASH Pattern System repository.

Every diagnostic record must reference one or more rule IDs. Rule IDs provide traceability from a diagnostic back to the specific specification rule that was evaluated. This taxonomy ensures that rule IDs are consistent, unique, stable, and machine-parseable across all specifications and implementations.

This taxonomy is **canonical** (Design Package D). Downstream implementation repositories must not invent local rule-ID formats.

## Canonical rule-ID pattern

```text
{FAMILY}-{CATEGORY}-{NUMBER}
```

Where:
- `{FAMILY}` is an uppercase token from the rule families list below
- `{CATEGORY}` is an uppercase token describing the rule category within the family
- `{NUMBER}` is a 3-digit zero-padded integer, monotonically increasing within the family-category pair

Example: `ASH-STATE-VALIDITY-001`

## Rule families

| Family | Scope | Source specification |
|---|---|---|
| `ASH-STATE` | State-space structure, validity, normalization | `ash-state-space.pseudo.md`, `state-validity-diagnostics.pseudo.md` |
| `ASH-CODEWORD` | Codeword structure, transformation, orbit membership | `codeword-set.pseudo.md`, `codeword-transformation-semantics.pseudo.md` |
| `ASH-ADMISSIBILITY` | State admissibility, codeword classification, correction | `state-admissibility.pseudo.md` |
| `ASH-CLASSIFICATION` | System-state classification, class-to-action mapping | `system-state-classification.pseudo.md` |
| `ASH-RECOVERY` | Recoverability semantics, recovery actions | `recoverability-semantics.pseudo.md`, `recovery-fallback-semantics.pseudo.md` |
| `ASH-FALLBACK` | Fallback policy, candidate selection, registry | `fallback-policy-registry.md`, `recovery-fallback-semantics.pseudo.md` |
| `ASH-CONTAINMENT` | Containment triggers, containment behavior | `containment-safe-failure-semantics.pseudo.md` |
| `ASH-HALT` | Safe halt triggers, terminal state semantics | `containment-safe-failure-semantics.pseudo.md` |

## Numbering rules

1. Numbers are 3-digit zero-padded: `001`, `002`, ..., `999`.
2. Numbers are monotonically increasing within each family-category pair.
3. Gaps in numbering are permitted (e.g., if a rule is deprecated, its number is not reused).
4. Numbers must not restart or wrap within a family-category pair.

## Uniqueness rules

1. Every `{FAMILY}-{CATEGORY}-{NUMBER}` triple is globally unique across the entire repository.
2. No two rules may share the same identifier, even across different specifications.
3. If a rule is moved between specifications, its identifier must remain unchanged.

## Stability rules

1. Once a rule ID is assigned to a specific rule, it must not be reassigned to a different rule.
2. A rule may be deprecated (marked as deprecated in the source specification), but its ID must not be reused.
3. Rule IDs must remain stable across design packages and repository versions.
4. Renaming a rule's description or updating its semantics does not change its ID.

## Usage rules in diagnostics

1. Every diagnostic record must include at least one rule ID in its `rule_ids` field.
2. All rule IDs in diagnostics must conform to the canonical pattern.
3. Rule IDs must reference rules that are defined in the source specification listed in the rule families table.
4. A diagnostic may include multiple rule IDs when multiple rules were evaluated.
5. The ordering of rule IDs in the `rule_ids` list should reflect the order in which rules were evaluated.

## Extension rules for future phases

1. New rule families may be added in future design phases (e.g., `ASH-TOPOLOGY`, `ASH-AXIOM`, `ASH-GENERATION`).
2. Existing rule families must not be renamed or removed.
3. New categories may be added to existing families.
4. Existing categories must not be renamed within a family.
5. Extensions must be recorded in this file with the design package that introduced them.

## Example rule IDs

| Rule ID | Meaning | Source |
|---|---|---|
| `ASH-STATE-STRUCTURE-001` | An ASH state is a full 9-bit vector in `F2^9` | `ash-state-space.pseudo.md` |
| `ASH-STATE-VALIDITY-001` | A valid state is admissible and already normalized | `state-validity-diagnostics.pseudo.md` |
| `ASH-CODEWORD-STRUCTURE-001` | Codeword set must match the canonical 16-member set | `codeword-set.pseudo.md` |
| `ASH-ADMISSIBILITY-CLASSIFICATION-001` | Every candidate state maps to exactly one admissibility class | `state-admissibility.pseudo.md` |
| `ASH-CLASSIFICATION-MAPPING-001` | Every state maps to exactly one system-state class | `system-state-classification.pseudo.md` |
| `ASH-RECOVERY-ACTION-001` | Recovery category is deterministic from state class | `recoverability-semantics.pseudo.md` |
| `ASH-FALLBACK-SELECTION-001` | Fallback must be selected from canonical registry | `fallback-policy-registry.md` |
| `ASH-CONTAINMENT-TRIGGER-001` | Containment entered due to fallback failure | `containment-safe-failure-semantics.pseudo.md` |
| `ASH-HALT-TRIGGER-001` | Safe halt entered due to containment breach | `containment-safe-failure-semantics.pseudo.md` |

## Design Package YWE-N3-LIFECYCLE — lifecycle trigger coverage

This extension assigns the remaining containment and safe-halt trigger rules
already defined by `containment-safe-failure-semantics.pseudo.md`. The two
previously assigned `TRIGGER-001` meanings remain unchanged. Each diagnostic
cites the exact trigger evaluated; no trigger is silently mapped to another.

| Rule ID | Meaning | Source |
|---|---|---|
| `ASH-CONTAINMENT-TRIGGER-002` | Containment entered due to propagation risk | `containment-safe-failure-semantics.pseudo.md`, PROPAGATION_RISK |
| `ASH-CONTAINMENT-TRIGGER-003` | Containment entered due to an explicit operator or policy request | `containment-safe-failure-semantics.pseudo.md`, OPERATOR_REQUEST |
| `ASH-CONTAINMENT-TRIGGER-004` | Containment entered after completed recovery validation failed and no permitted recovery continuation remained | `containment-safe-failure-semantics.pseudo.md`, RECOVERY_VALIDATION_FAILURE |
| `ASH-HALT-TRIGGER-002` | Safe halt entered from FAILED under the required external-authority or source-defined unreachability escalation | `containment-safe-failure-semantics.pseudo.md`, ESCALATION_FROM_FAILED; `recoverability-semantics.pseudo.md`, ESCALATION_REQUIRED blocked recovery |
| `ASH-HALT-TRIGGER-003` | Safe halt entered due to an explicit operator request | `containment-safe-failure-semantics.pseudo.md`, OPERATOR_HALT_REQUEST |
| `ASH-HALT-TRIGGER-004` | Safe halt entered due to an explicit policy request | `containment-safe-failure-semantics.pseudo.md`, POLICY_HALT_REQUEST |
| `ASH-HALT-TRIGGER-005` | Safe halt entered for blocked recovery with no path forward and no containment option | `containment-safe-failure-semantics.pseudo.md`, UNRESOLVABLE_BLOCKED_RECOVERY |

## Relation to other specifications

- **diagnostic-schema.md** — requires that every diagnostic envelope include taxonomy-compliant rule IDs
- **state-validity-diagnostics.pseudo.md** — uses `ASH-STATE` family rule IDs
- **recovery-fallback-semantics.pseudo.md** — uses `ASH-RECOVERY` and `ASH-FALLBACK` family rule IDs
- **containment-safe-failure-semantics.pseudo.md** — uses `ASH-CONTAINMENT` and `ASH-HALT` family rule IDs
- **semantic-contracts.md** — requires downstream implementations to emit taxonomy-compliant rule IDs

## Design Package YWE-M3-MODULES — six producer rule assignments

This additive extension activates ASH-TOPOLOGY, ASH-AXIOM and ASH-GENERATION. Existing identifiers, meanings and owner subsets are unchanged. The definitions below name the exact condition, not a downstream claim of implemented conformance.

| Rule ID | Evaluated meaning | Canonical semantic source |
|---|---|---|
| `ASH-STATE-IDENTITY-001` | Full-vector state identity encoding; valid-only module input. | `core/realm-identity.pseudo.md; interfaces/contracts/realm-encoder-contract.md` |
| `ASH-CODEWORD-REGISTRY-001` | Exactly ordered canonical C16 transition definitions; no implicit definition. | `core/codeword-set.pseudo.md; algorithms/transition-system.pseudo.md` |
| `ASH-CODEWORD-SELECTION-001` | Selected transition resolves to a canonical C16 member. | `algorithms/transition-system.pseudo.md` |
| `ASH-CODEWORD-APPLICABILITY-001` | Actual selected or enumerated definition applicability under the declared exact policy. | `algorithms/transition-system.pseudo.md; interfaces/contracts/transition-registry-contract.md` |
| `ASH-CODEWORD-TRANSFORMATION-001` | Simultaneous full-vector XOR and actual derived target validity. | `algorithms/codeword-transformation-semantics.pseudo.md` |
| `ASH-TOPOLOGY-ADMISSION-001` | Current valid input and declared depth/seed bound before expansion. | `interfaces/contracts/topology-generator-contract.md` |
| `ASH-TOPOLOGY-STRUCTURE-001` | Typed nodes and declared frontier-only output. | `algorithms/topology-expansion.pseudo.md` |
| `ASH-TOPOLOGY-EXPANSION-001` | Each leaf expands by continuation, positive and negative branches. | `algorithms/topology-expansion.pseudo.md` |
| `ASH-TOPOLOGY-ORDER-001` | Deterministic frontier and sibling order. | `algorithms/topology-expansion.pseudo.md` |
| `ASH-TOPOLOGY-LINEAGE-001` | Every child retains actual parent lineage. | `algorithms/topology-expansion.pseudo.md` |
| `ASH-AXIOM-SUBJECT-001` | Complete typed subject and comparable declared units before evaluation. | `algorithms/axiom-evaluation.pseudo.md; interfaces/contracts/axiom-evaluator-contract.md` |
| `ASH-AXIOM-RELATION-001` | relation_count > 0. | `algorithms/axiom-evaluation.pseudo.md` |
| `ASH-AXIOM-COMPRESSION-001` | compressed_measure < raw_measure in the same declared quantum. | `algorithms/axiom-evaluation.pseudo.md` |
| `ASH-AXIOM-SCALE-001` | scale_count > 1. | `algorithms/axiom-evaluation.pseudo.md` |
| `ASH-AXIOM-ERASURE-001` | erasure_cost > 0. | `algorithms/axiom-evaluation.pseudo.md` |
| `ASH-AXIOM-SELFREFERENCE-001` | self_reference_capable AND self_model_available. | `algorithms/axiom-evaluation.pseudo.md` |
| `ASH-AXIOM-CONJUNCTION-001` | overall_pass is the conjunction of all five checks; no short circuit. | `algorithms/axiom-evaluation.pseudo.md` |
| `ASH-GENERATION-PLAN-001` | Complete deterministic abstract plan from exact inputs. | `algorithms/generation-planning.pseudo.md; interfaces/contracts/generation-planner-contract.md` |
| `ASH-GENERATION-BOUNDARY-001` | Planning performs no observable external effect or artifact emission. | `interfaces/contracts/generation-planner-contract.md` |
| `ASH-GENERATION-TRACEABILITY-001` | Every materialized artifact traces to its exact plan element. | `interfaces/contracts/artifact-emitter-contract.md` |
| `ASH-GENERATION-EMISSION-001` | Materialize exactly the selected complete plan with actual effect receipts. | `interfaces/contracts/artifact-emitter-contract.md` |
| `ASH-GENERATION-PLANFIDELITY-001` | No invention, omitted element, local default, or callback to fill plan semantics. | `interfaces/contracts/artifact-emitter-contract.md` |
