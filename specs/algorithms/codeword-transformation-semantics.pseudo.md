# Codeword Transformation Semantics — canonical specification

## Purpose

This specification defines the **canonical state transformation** for the ASH Pattern System.

In the ASH Pattern System, ordinary motion between states is defined as **XOR by a codeword**. This is the foundational transformation operation from which all state evolution derives.

## Canonical transformation

Given:
- a state `x ∈ F2^9` (a 9-bit binary vector)
- a codeword `c ∈ C` where `C ⊂ F2^9` is the codeword set

The canonical transformation is:

```text
x' = x ⊕ c
```

where `⊕` denotes coordinate-wise XOR (addition in F2).

## State space

- The state space is **F2^9** — the set of all 9-bit binary vectors.
- There are **512 states** (vertices / realms) in the state space.
- Each state is a full 9-bit vector `(b0, b1, b2, b3, b4, b5, b6, b7, b8)` where each `bi ∈ F2`.
- No coordinate is structurally privileged over any other at the foundational transformation level.

## Codeword structure

- Codewords are **9-bit vectors** in F2^9.
- The codeword set `C` is a subset of F2^9 defining the allowed transformations.
- Codewords are treated as full 9-bit objects in canonical processing.
- The specific codeword set `C` for the ASH Pattern System is a [9, 4, 4] doubly-even linear code with 16 members, fully specified in `codeword-set.pseudo.md`.

## Pseudocode

```text
FUNCTION apply_codeword_transformation(state[9], codeword[9]) -> Vector[9] over F2
    PRECONDITION: length(state) == 9
    PRECONDITION: length(codeword) == 9
    PRECONDITION: all elements are in F2
    PRECONDITION: codeword ∈ C (the canonical codeword set)

    result = state XOR codeword    -- coordinate-wise XOR

    POSTCONDITION: length(result) == 9
    POSTCONDITION: result ∈ F2^9

    RETURN result
END FUNCTION
```

## Determinism requirements

1. The same state and codeword always produce the same result.
2. Transformation does not depend on platform, language, runtime, or execution context.
3. Transformation has no side effects — it is a pure function over F2^9.

## Prohibition on inferring extra semantics

The codeword transformation is defined entirely by the XOR operation on F2^9. Implementations must not:

- Infer extra per-coordinate derivation rules beyond the canonical generators and enumerated codewords
- Partition canonical transformation into alternate semantic stages that change the `x ⊕ c` rule
- Add transformation rules that are not grounded in the canonical specifications
- Treat any single coordinate as structurally special at the transformation level unless a canonical specification explicitly requires it

## Invariants

1. **Closure**: `x ⊕ c` is in F2^9 for all `x ∈ F2^9` and `c ∈ C`
2. **Determinism**: identical inputs produce identical outputs
3. **Purity**: transformation has no side effects
4. **Identity**: if the zero vector `0` is in `C`, then `x ⊕ 0 = x`
5. **Involution**: `(x ⊕ c) ⊕ c = x` — applying the same codeword twice returns to the original state

## Relation to other specifications

- **codeword-set.pseudo.md** — defines the canonical codeword set `C ⊂ F2^9`
- **state-admissibility.pseudo.md** — defines admissibility relative to codeword orbit structure
- **ash-state-space.pseudo.md** — defines the canonical F2^9 state space
- **averaging-operator-semantics.pseudo.md** — defines the averaging operator built on codeword transformations
- **transition-system.pseudo.md** — general transition framework; codeword transformation is the canonical transition mechanism
