# ASH State Space — canonical specification (Canonical Baseline)

## Design decision

The ASH state space is **F2^9** — the set of all 9-bit binary vectors.

An ASH state is a **full 9-coordinate binary vector**:

```text
S = (b0, b1, b2, b3, b4, b5, b6, b7, b8)
where each bi ∈ F2
```

There are **512 states** (vertices / realms) in the state space.

## Structural interpretation

All 9 coordinates participate in the algebraic structure of the ASH state space. No single coordinate is structurally privileged at the foundational level.

The state space structure is defined by the **codeword set** `C ⊂ F2^9`, which determines:

- the allowed transformations (XOR-by-codeword motion between states)
- the orbit structure (which states are reachable from which)
- the averaging operator and its invariant subspaces
- the branching / expansion topology

### Observation about the canonical codeword set

All canonical codewords have their 9th coordinate set to `0`. This is a property of the canonical codeword set and does not change the definition of the state space as a full 9-coordinate structure.

## Canonical state record

```text
TYPE AshState
    bits: Vector[9] over F2
END TYPE
```

Equivalent expanded form:

```text
TYPE AshStateExpanded
    b0: Bit
    b1: Bit
    b2: Bit
    b3: Bit
    b4: Bit
    b5: Bit
    b6: Bit
    b7: Bit
    b8: Bit
END TYPE
```

The canonical form is the **full 9-bit vector**. Implementations may use either representation, but the 9-bit vector is the semantic normal form.

## Canonical transformation

Ordinary movement between states is defined by **XOR-by-codeword**:

```text
x' = x ⊕ c    where x ∈ F2^9, c ∈ C ⊂ F2^9
```

See `specs/algorithms/codeword-transformation-semantics.pseudo.md` for the full definition.

## Pseudocode

```text
FUNCTION make_state(bits[9]) -> AshState
    PRECONDITION: length(bits) == 9
    PRECONDITION: all elements of bits are in F2

    state.bits = bits
    RETURN state
END FUNCTION
```

```text
FUNCTION transform_state(state: AshState, codeword[9]) -> AshState
    PRECONDITION: length(codeword) == 9
    PRECONDITION: codeword ∈ C (the canonical codeword set)

    result.bits = state.bits XOR codeword
    RETURN result
END FUNCTION
```

## Validity and admissibility

Validity and admissibility for the canonical 9-bit model are defined by:

- **Codeword-orbit membership** — whether a state is reachable from known valid states via codeword transformations
- **Admissibility classification** — VALID, TRANSFORMATION_COMPATIBLE, TRANSFORMATION_INCOMPATIBLE, or UNCLASSIFIED

See `specs/core/state-admissibility.pseudo.md` for the full admissibility specification.
See `specs/core/codeword-set.pseudo.md` for the canonical codeword structure.

## Required invariants

1. The state space is F2^9 — all states are 9-bit binary vectors
2. Normalization is deterministic — the same candidate state always produces the same result
3. Codeword transformations are deterministic — the same state and codeword always produce the same result
4. State validity can be explained diagnostically
5. All 9 coordinates are part of the algebraic structure — no coordinate is excluded from the foundational model

## Related specifications

- `specs/core/codeword-set.pseudo.md` — canonical codeword set definition
- `specs/core/state-admissibility.pseudo.md` — full 9-bit admissibility and validity
- `specs/algorithms/codeword-transformation-semantics.pseudo.md` — canonical XOR-by-codeword transformation
- `specs/algorithms/averaging-operator-semantics.pseudo.md` — canonical averaging operator `T` with `T² = T`
- `specs/algorithms/branching-semantics.pseudo.md` — canonical branching / leaf expansion
- `specs/core/realm-identity.pseudo.md` — realm identity encoding from full 9-bit state
