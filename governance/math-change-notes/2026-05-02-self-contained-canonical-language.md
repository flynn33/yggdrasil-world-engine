# 2026-05-02 Self-Contained Canonical Language

## What changed

- Removed references that positioned the ASH Pattern System as dependent on an external model layer.
- Rewrote specs, contracts, governance pages, wiki pages, and agent text so the canonical math is defined as self-contained within this repository.
- Removed stale decomposition and closure wording that implied unresolved codeword semantics or special derived-coordinate handling.

## Why

- Agents and auditors should treat this repository as the complete semantic authority for the ASH Pattern System.
- Deprecated provenance language and older decomposition phrasing created ambiguity about what is normative.
- The repository needs to describe only the current closed canonical baseline, not historical framing.

## Baseline preservation statement

- No canonical math was changed by this edit set.
- The state space remains `F2^9` with 512 states.
- The codeword set remains the fixed 16-member `[9, 4, 4]` code defined in `specs/core/codeword-set.pseudo.md`.
- XOR-by-codeword transitions, the averaging operator with `T² = T`, and first-class branching semantics remain unchanged.
