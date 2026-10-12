# StateModel Contract — implementation contract (Canonical Baseline)

## Purpose

The `StateModel` module is the foundational implementation module for the ASH Pattern System. It owns the canonical state representation, normalization, validity diagnostics, system-state classification, and recoverability classification for the full 9-dimensional canonical baseline.

## Canonical responsibility

The `StateModel` module is the single authority for:

- representing ASH states as full 9-bit vectors in F2^9
- normalizing candidate states to valid configurations using the codeword structure
- classifying state admissibility via codeword-orbit membership (see `state-admissibility.pseudo.md`)
- producing state-validity diagnostics (see `state-validity-diagnostics.pseudo.md`)
- classifying system states into the 7 canonical classes (see `system-state-classification.pseudo.md`)
- classifying recoverability for each system-state class (see `recoverability-semantics.pseudo.md`)

## Required inputs

- A candidate ASH state (full 9-bit vector in F2^9)
- Access to the canonical codeword set `C ⊂ F2^9` (see `codeword-set.pseudo.md`)

## Required outputs

- Normalized `AshState` (full 9-bit vector, when normalization succeeds)
- `StateValidityDiagnostic` record (for any candidate state)
- `SystemStateClass` classification
- `RecoveryCategory` classification

## Required behaviors

### State representation
- States are full 9-bit vectors in F2^9 — all 9 coordinates participate in the algebraic structure
- No coordinate is structurally privileged at the foundational level

### Normalization
- Normalization operates on the full 9-bit state using the codeword structure
- If the state is already valid: return as-is
- If the state is transformation-compatible: restore to a valid configuration via codeword-based correction
- If the state is transformation-incompatible: normalization fails with diagnostic

### Admissibility classification
- Admissibility is determined by codeword-orbit membership relative to the canonical codeword set
- Statuses: VALID, TRANSFORMATION_COMPATIBLE, TRANSFORMATION_INCOMPATIBLE, UNCLASSIFIED
- Must use the canonical 16-member codeword set defined in `codeword-set.pseudo.md`

### System-state classification
- Map diagnostic results to one of: STABLE, UNSTABLE, CORRECTABLE, DEGRADED, CONTAINED, FAILED, SAFE_HALT
- Classification must be deterministic and total

### Recoverability classification
- Map each system-state class to its recovery category: NO_ACTION, NORMALIZE_STATE, APPLY_CORRECTION, FALLBACK_REQUIRED, CONTAINMENT_REQUIRED, ESCALATION_REQUIRED, TERMINAL_NO_RECOVERY

## Required diagnostics

- Every normalization attempt must produce a `StateValidityDiagnostic`
- Diagnostics must conform to `diagnostic-schema.md`
- Rule IDs must conform to `rule-id-taxonomy.md`
- Diagnostics must never be silently omitted

## Invariants

1. Normalization is deterministic — same input always produces same result
2. Classification is total — every state maps to exactly one class
3. All 9 coordinates participate in the algebraic structure
4. Codeword-based classification uses the canonical 16-member set without local substitution

## Prohibited shortcuts

- Must not substitute alternate state partitions for canonical processing
- Must not substitute a local codeword set for the canonical 16-member set
- Must not silently treat a transformation-incompatible state as valid

## Relation to other contracts and specifications

- `ash-state-space.pseudo.md` — canonical F2^9 state definition
- `codeword-set.pseudo.md` — canonical codeword structure
- `state-admissibility.pseudo.md` — full 9-bit admissibility
- `state-validity-diagnostics.pseudo.md` — 9D diagnostic model
- `system-state-classification.pseudo.md` — system-state classes
- `recoverability-semantics.pseudo.md` — recovery categories
- `recovery-engine-contract.md` — consumes classification and diagnostics
- `diagnostics-module-contract.md` — schema and taxonomy conformance
