# 2026-07-19 ASH Source Authority and Realm Identity

## What changed

- Established `core/ash_pattern_engine/canonical/` as the authoritative ASH
  specification source and `specs/` as its generated mirror.
- Added the canonical fallback-policy registry that was previously present only
  in the mirror.
- Defined state / vertex identity as the canonical identity semantics while
  preserving `RealmIdentity` and `realm_id` as lossless compatibility aliases.
- Corrected the canonical state-space and codeword-transformation wording so
  the 512 ASH states are called states or vertices, not realms. Profile-level
  Realm mappings remain outside the mathematical state-space cardinality.
- Pinned the normalized per-file and aggregate identity of the canonical ASH
  dependency in machine-readable governance.

Changed-file inventory for this terminology correction:

- `core/ash_pattern_engine/canonical/core/ash-state-space.pseudo.md`;
- `core/ash_pattern_engine/canonical/algorithms/codeword-transformation-semantics.pseudo.md`;
- synchronized mirrors at `specs/core/ash-state-space.pseudo.md` and
  `specs/algorithms/codeword-transformation-semantics.pseudo.md`; and
- `data/governance/ash_dependency_identity.json`, refreshed by the canonical
  synchronization workflow.

## Why

- M1 requires one authoritative source or generated mirror for ASH
  specifications and a pinned ASH dependency identity.
- State-space identity must distinguish the mathematical vertex from realm
  presentation vocabulary without breaking established integration names.
- Calling every state a realm conflated the fixed `F2^9` vertex set with
  profile-level semantic identities. Removing that synonym clarifies scope
  without changing the set, coordinates, codewords, or transition operation.
- Deterministic synchronization and identity hashes make source drift,
  unexpected mirror files, and stale dependency records detectable.

## Baseline preservation statement

- The canonical state space remains `F2^9` with exactly 512 states / vertices.
- No state or vertex was added, removed, merged, or remapped; only the
  inaccurate `realms` synonym was removed from the 512-state descriptions.
- The canonical codeword set remains the fixed 16-member `[9, 4, 4]` code.
- XOR-by-codeword transitions, orbit structure, averaging, branching, recovery,
  containment, diagnostics, and generation semantics are unchanged.
- The `RealmIdentity` and `realm_id` aliases preserve existing compatibility;
  this change introduces no new mathematical equivalence or state collapse.
