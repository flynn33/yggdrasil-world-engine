# Canonical ASH Baseline

This directory mirrors the ASH Pattern System canonical baseline used by YWE:

- `core/` - F2^9 state space, canonical codeword set, realm identity, admissibility, diagnostics, classification, and recoverability semantics.
- `algorithms/` - XOR-by-codeword transitions, averaging, branching, recovery, containment, topology, axioms, and generation planning.
- `interfaces/` - diagnostic schema, rule taxonomy, semantic contracts, and implementation contracts.
- `verification/` - invariant, conformance, and acceptance requirements.

YWE treats these files as the semantic authority for `core/ash_pattern_engine/`.
The root-level `specs/` directory contains the same mirrored baseline so the
ASH governance scripts can run against the repository in their native shape.
