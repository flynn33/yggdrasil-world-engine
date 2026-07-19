# Pattern Archetypes

Contains YWE-owned downstream pattern-node mappings and archetype definitions.
These optional extension-profile artifacts consume symbolic input constrained
by the pinned ASH grammar; they are not part of the upstream ASH dependency.

Authority: `docs/architecture/ASH_PATTERN_ARCHETYPE_LIBRARY_CANONICAL.md`

Upstream constraint: `data/governance/ash_dependency_identity.json`

Dependency identity inclusion: excluded

## Pattern Node Schema

See `pattern_schema.json` for the base schema.

Pattern nodes represent YWE interpretations of detected patterns used to bias
downstream generation. They do not define upstream symbolic meaning or create
an independent grammar.

## Fields

- `pattern_id` -- Unique identifier for the pattern
- `type` -- The type of pattern (e.g., hidden_knowledge, revelation, cosmic_imbalance)
- `realm_bias` -- Which realm this pattern is most associated with
- `strength` -- Pattern strength from 0 to 1
