# TransitionRegistry Contract — implementation contract (Canonical Baseline)

## Purpose

The `TransitionRegistry` module resolves and applies state transitions deterministically. It operates on full 9-bit states and uses XOR-by-codeword as the canonical transformation mechanism.

## Canonical responsibility

The `TransitionRegistry` module is the single authority for:

- resolving which transitions are available for a given state
- applying a selected transition to produce a new state
- ensuring transitions respect the codeword structure

## Required inputs

- A valid `AshState` (full 9-bit vector in F2^9)
- A transition identifier or codeword

## Required outputs

- A new `AshState` (full 9-bit vector, the result of applying the transition)
- Transition diagnostics when resolution or application fails

## Required behaviors

### Deterministic resolution
- Transition resolution must be deterministic — the same state and transition identifier always resolve to the same outcome

### XOR-by-codeword transformation
- The canonical transformation mechanism is `x' = x ⊕ c` where `c ∈ C ⊂ F2^9`
- Transitions operate on the full 9-bit state simultaneously
- There is no separate "apply to subset, then re-derive remainder" step

### Valid-state requirement
- Transitions should operate on valid states
- If an invalid state is provided, the registry must fail with a diagnostic

## Required diagnostics

- If transition resolution fails, produce a diagnostic conforming to `diagnostic-schema.md`
- Rule IDs must conform to `rule-id-taxonomy.md`

## Invariants

1. Transition resolution is deterministic
2. XOR-by-codeword produces a well-formed 9-bit state
3. `(x ⊕ c) ⊕ c = x` — applying the same codeword twice returns to the original state
4. Failed applicability checks return explainable diagnostics

## Prohibited shortcuts

- Must not decompose the state into sub-components for transformation
- Must not silently drop a failed transition
- Must not assume a specific exhaustive codeword set if research-baseline closure is pending

## Relation to other contracts and specifications

- `state-model-contract.md` — provides valid states consumed by TransitionRegistry
- `transition-system.pseudo.md` — transition semantics
- `codeword-transformation-semantics.pseudo.md` — canonical XOR-by-codeword operation
- `codeword-set.pseudo.md` — canonical codeword structure
- `ash-state-space.pseudo.md` — canonical F2^9 state definition
- `diagnostics-module-contract.md` — schema and taxonomy conformance

## Additive bounded ordered-chain application

A reference registry MAY expose a separately declared bounded ordered-chain
operation in addition to unchanged single selected application and resolution.
The reference chain bound is four selections; it MUST retain the complete requested
order, actual evaluated prefix, full intermediate candidates and source/profile
bindings. It MUST begin from a current valid diagnosis and construct its actual
valid-source gate. Every evaluated selection, applicability and simultaneous
full-vector XOR condition MUST immediately construct its own owned record. The
applicability mask is indexed by the complete current candidate, not the original
source. Unknown or inapplicable selection MUST stop with an explained actual prefix. [YWE-REQ-0049]

Each computed target retains an actual pure StateModel validity diagnostic. Strict
chain continuation MUST require that exact target to be VALID under identical full
source/profile bindings. The next step MAY reuse that already evaluated proof
without inventing a fresh StateDiagnosis, root or validity evaluation. A nonVALID
target stops at its actual computed candidate and records the failed continuation
condition on that transformation; its rule vector additionally cites state validity.
The original single selected application still returns its well-formed target and
actual target diagnosis without a new postVALID promise or hidden normalization. [YWE-REQ-0049]

An empty chain is a valid identity after its actual source gate. A four-selection
reference chain constructs at most thirteen records: one source gate and three
per evaluated step. All records retain the actual initial DETECTION subject/root
and previously constructed parent, with nondecreasing severity. No intermediate
StateModel emission, collector ACK or session publication is manufactured.
