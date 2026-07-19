# State / Vertex Identity — canonical specification (Canonical Baseline)

## Purpose

State identity is the stable semantic encoding of an ASH state. Every state
`x ∈ F2^9` denotes exactly one of the state space's 512 vertices, and every
vertex denotes exactly one full 9-bit state. The canonical identity therefore
identifies the state-space vertex directly.

YWE may present a vertex as a realm. `RealmIdentity` and `realm_id` remain
compatibility aliases for that same state / vertex identity; they do not define
a second identity system or collapse distinct vertices.

## Inputs

State identity is computed from a **full 9-bit ASH state** in `F2^9`.

## Canonical identity record

```text
TYPE StateIdentity
    state_signature: String
    vertex_id: String
END TYPE
```

The canonical record encodes the full 9-bit state as a single signature and
derives the stable vertex identifier from that signature.

## Compatibility aliases

```text
TYPE RealmIdentity = StateIdentity
FIELD RealmIdentity.realm_id = StateIdentity.vertex_id
```

The aliases are lossless names for the canonical identity. Reading or writing
`realm_id` is semantically identical to reading or writing `vertex_id` for the
same record. Compatibility handling must not recalculate, remap, or otherwise
change the identifier.

## Semantic rule

The same ASH state must always yield the same state / vertex identity. Different
states must yield different vertex identities. Domain-level groupings or
equivalence relations, when separately specified, relate vertices but do not
replace their canonical identities.

## Pseudocode

```text
FUNCTION encode_state_identity(state: AshState) -> StateIdentity
    PRECONDITION: state.bits has length 9
    PRECONDITION: all elements are in F2

    identity.state_signature = encode_state_signature(state.bits)
    identity.vertex_id = derive_vertex_id(identity.state_signature)

    RETURN identity
END FUNCTION
```

```text
FUNCTION encode_realm_identity(state: AshState) -> RealmIdentity
    identity = encode_state_identity(state)
    RETURN identity AS RealmIdentity
END FUNCTION
```

## Notes

This specification intentionally leaves the external string format open. A
downstream implementation may use a different formatting convention so long as
the mapping is deterministic, injective over `F2^9`, and semantically faithful.
Existing integrations may continue to expose `RealmIdentity` and `realm_id` as
compatibility aliases.

## Required invariants

1. Equal states yield equal state / vertex identities.
2. Different states yield different state / vertex identities.
3. Identity is computed from the full 9-bit state.
4. The encoding is deterministic — the same input always produces the same output.
5. All 9 coordinates of the state participate in the identity encoding.
6. `RealmIdentity` is an alias of `StateIdentity`, and `realm_id` is an alias of `vertex_id`.

## Relation to other specifications

- **ash-state-space.pseudo.md** — defines the canonical `F2^9` state space and its 512 vertices.
- **codeword-transformation-semantics.pseudo.md** — codeword transformations map between vertices.
