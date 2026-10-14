# M4 exact resonance-state migration

Status: adopted reference contract. Owner: State and synchronization maintainers.
Requirement: [YWE-REQ-0054]. Decision: ADR-0046. Adopted before implementation
under the owner's resumed M4 roadmap authorization.

## Problem and compatibility

The existing plane-attunement, bloodline-resonance and wolf-summary v1 schemas
admit decimal JSON scores in [0, 1]. The scoped journal admits exact integers.
Binary floating-point conversion or rounding would change persisted values.
The v2 schemas therefore rename only the designated numeric fields to `_q6`,
with exact integer range 0–1,000,000, and require explicit v2 schema identity and
version `2.0.0`. Other required/optional fields, ordering, references and values
are preserved. Existing v1 schemas and examples remain unchanged.

The migration MUST preserve the exact mathematical value of every converted
score and every other field. A value not representable in integer millionths
MUST fail without returning a partial target. A migration MUST NOT infer missing
references, apply schema defaults, change identity, merge duplicates, normalize
signals, or confer player/world commit authority. [YWE-REQ-0054]

This is a versioned representation change, not a new progression rule. White
and dark resonance are converted independently; no sum or morality constraint
is introduced. The nine-plane mapping belongs to the WRW migration data, not
the neutral codec. Dominance, reveal and faction claims retain their original
meanings and evidence boundaries.

## Explicit composition and plans

`core/state_migration.py` is a bounded pure reference oracle using the already
pinned jsonschema validation dependency. It receives all schemas and plans as
explicit values; it reads no files, network, clock or ambient registry.

`StateMigration(plan, source_schema, target_schema)` validates and privately
copies a closed plan. Each plan names a migration ID, source and target schema
document IDs, wire schema IDs, exact schema versions, canonical schema SHA-256
digests, and ordered conversion rules. Canonical schema hashing uses compact,
sorted-key UTF-8 JSON without Unicode normalization. Schemas are standalone
Draft 2020-12 documents; reference keywords are rejected, so validation cannot
retrieve external resources. Supplying a plan is a trusted composition action;
an untrusted record cannot choose or substitute its own migration policy.

Rules name a parent path and a source/target field. Path segments are literal
object keys; `*` traverses array elements in order. There are at most 32 rules,
eight segments per path and 256 concrete conversions. Missing parents/fields,
duplicate writes and existing target fields are rejected. The checked-in
`data/validation/m4_resonance_migration_plans.json` supplies the three exact
source-to-target mappings. Plan identity also binds both complete schemas.

## Migration and verification

`migrate(raw)` accepts UTF-8 JSON bytes, at most 65,536 bytes. Parsing rejects
duplicate object keys, nonfinite numbers, invalid Unicode, more than 4,096 nodes,
depth above 32, and numeric tokens longer than 128 characters or decimal exponents
outside [-1024, 1024]. Integers remain exact and bounded by the journal integer
domain. Decimal tokens are parsed directly into exact decimal values, never
through binary floats. Boolean scores are invalid.

Source schema identity and version must exactly match the selected plan. The
entire source is validated before conversion. Each selected numeric value must
lie in [0, 1]; exact coefficient/exponent arithmetic computes millionths without
depending on the process decimal arithmetic context. Trailing zeros and exponent
notation are accepted when they denote an exactly representable value. Excess
precision is rejected rather than rounded, clamped or silently discarded.

The complete target is validated under the target schema and the journal value
limits before a result escapes. A result contains format `ywe.state_migration.v1`,
migration ID, canonical plan digest, exact raw source digest, target digest,
target record, and ordered conversion rows with source pointer, target pointer,
source decimal spelling and integer millionths. The result is a detached JSON
object. Result size remains within the journal's 65,536-byte/4,096-node limits.
Source decimal spelling is the exact parsed decimal's representation, not a
claim to preserve whitespace or the source token's original spelling.

`verify(raw, result)` repeats migration under the constructed policy and compares
the complete canonical result. It returns false for corrupt targets, receipts,
source identities or conversion rows. Hashes prove correspondence to the supplied
bytes; the host separately authenticates the source and policy. A self-supplied
digest is not authentication. Migration does not mutate a live journal or delete
its source archive. The source remains retained for audit and recovery; no
automatic downgrade or reconstruction of original lexical bytes is claimed.

Errors use stable codes INVALID_PLAN, INVALID_SOURCE, UNREPRESENTABLE_SCORE,
INVALID_TARGET or MIGRATION_LIMIT. No source contents or validator exception
text are included in errors. Failures are atomic because output is private until
all checks complete. [YWE-REQ-0054]

## Verification and scope

Tests migrate the repository's three actual legacy fixtures, compare every
unconverted field, validate both source and target, replay migrated integer
records through the scoped journal, and reject corrupt receipts. Boundary cases
include zero/one, one millionth, exponent forms, excess precision, hostile decimal
context, duplicate keys, unknown versions, missing fields, size/depth/capacity,
and incompatible schema or plan hashes.

This slice establishes these three versioned conversions only. Full player-state
admission, creation/progression, branch synchronization, compensation semantics,
archive-version migration and multiplayer reconciliation remain M4 obligations.
No milestone exit or placeholder debt closes through this contract alone.
Single-executor review is recorded; independent review is not claimed.
