# M4 scoped commit journal

Status: active first-slice contract. Owner: State and synchronization maintainers.
Partition: `ywe_core`. Requirement: [YWE-REQ-0052]. Decision: `ADR-0044`.

This contract is adopted under the owner's October 14, 2026 authorization to
resume M4. It defines a bounded reference protocol, not completed M4 acceptance.
The existing truth authority lattice and accepted M3 source identities remain
controlling. No new ASH axiom or production storage implementation is introduced.

## Responsibility and boundaries

A journal MUST retain accepted transitions in one immutable truth scope, apply
each committed request identity at most once, and reproduce its state by ordered
replay under the same declared owner policy. Failure before publication leaves
the journal unchanged. Perception journals cannot write objective journals.
[YWE-REQ-0052]

`core/state_journal.py` is a Python reference oracle. Its constructor receives
an explicit scope, policy identity, initial state and trusted pure owner reducer.
The reducer validates domain packets and returns the next state; the journal
does not treat a packet's self-declared acceptance status as authorization.
The constructor is a trusted composition boundary, not an endpoint exposed to
players. The reducer has no journal reference, host effect or ambient dependency.
Replacing policy behavior without changing its immutable identity is invalid.
No existing M3 producer automatically obtains this constructor's authority.

The scope is `(world_id, truth_scope, subject_id)`. Allowed truth scopes are
`shared_worldstate`, `leaf_branch_state`, `player_state`, `player_perception`.
For shared state the subject is the world ID; other subjects explicitly identify
their branch, player, or observer. Scope equality is exact. Realm and location
partitions and cross-scope transactions are deferred to their synchronization
contract; they do not acquire new truth-authority levels here. The journal does
not yet supply the final player packet adapter, branch merge or authority grants.

## Owned representation

Identifiers use 1–128 ASCII characters: first alphanumeric, then alphanumeric,
dot, underscore, colon, slash or hyphen. Policy identity identifies a fixed
version of the owner's deterministic validation and reduction rules.

`data/schemas/m4_commit_journal_schema.json` defines the closed archive shape
and reuses the common identifier grammar with this journal's narrower length
limit. An entry is an internal ledger envelope, not a replacement for the M2
common Event or Compensation packet. Domain owners retain those packets and
their required event kind, logical time and provenance inside `packet` when
applicable. The schema verifies structure; the codec and replay validate the
additional byte, depth, identity, hash, policy and truth-scope constraints.

State and packet values are JSON objects, owned by canonical byte copies.
The v1 reference domain admits null, bool, exact integers in
`[-9007199254740991, 9007199254740991]`, scalar Unicode strings, arrays and objects
with string keys. Floats, duplicate keys in raw input, lone surrogates, custom
Python objects, nonfinite numbers and implicit coercions are rejected. Each
value has at most 4,096 nodes and 32 nesting levels and at most 65,536 canonical
UTF-8 bytes. These are new journal transport limits, not changes to existing
M2/M3 schema acceptance. A future domain adapter must make any representation
conversion explicit and lossless.

Canonical encoding uses lexicographically sorted Unicode scalar keys, compact
JSON separators, literal Unicode encoded as UTF-8, and no Unicode normalization.
Integer zero is `0`. SHA-256 digests are lowercase hex. The initial chain digest
binds the format, exact scope, policy identity and complete initial state.
Each entry digest binds the entire entry body including the previous digest.
Hashes detect inconsistency against a trusted digest; they do not authenticate
an attacker who can replace an entire archive. A host must retain a trusted
head digest separately to establish archive identity.

## Interfaces and transitions

`CommitJournal(scope, policy_id, initial_state, reducer)` validates construction
and owns a private state and ordered entries. `state()` returns a detached JSON
copy. `save()` returns an owned canonical archive byte string. Both observe one
complete committed revision under the same lock used by `commit`.

`commit(request_id, expected_revision, packet, compensates=None)` validates and
copies arguments, then serializes admission and reduction. The request identity
is local to this journal and never reusable after commit. Its fingerprint binds
the expected revision, packet and optional compensation target. An exact retry
returns the original immutable receipt before checking the now-stale revision
and without invoking the reducer again. Changed content under a committed ID
fails with `IDENTITY_CONFLICT`. A new ID with a stale revision fails with
`REVISION_CONFLICT`. Rejected attempts reserve neither identity nor revision.

The reducer receives detached state and packet objects plus the immutable scope.
It either returns a construction-valid next state or rejects by raising an
exception. Invalid output and reducer exceptions produce `POLICY_REJECTED` with
no partial write. A reducer attempting reentrant journal access is rejected;
cross-thread external effects are outside the pure reducer contract. Publication
replaces state and appends its entry atomically under the lock only after all
validation, serialization and hashing succeed. A receipt reports the committed
revision, entry digest and resulting state digest. It does not claim disk or
network acknowledgement.

An entry stores request identity, original expected revision, packet, compensation
target, monotonic revision, previous digest, before/after state digests and entry
digest. Entries are never edited or removed. The v1 reference journal permits
128 committed entries, then fails `CAPACITY_EXCEEDED`; exact retries still work.
Production retention, compaction and archive segmentation need a later protocol.

`compensates` optionally identifies an earlier committed request. Missing targets
are rejected. The owner reducer decides the compensating packet's lawful effect;
the journal never guesses an inverse or deletes history. Repeated compensation
under a new request ID is a domain-policy decision. Uncommitted failure is atomic
rollback; reversal of committed effects is a new, visible compensation.

## Save, load and replay

The closed v1 archive contains format, scope, policy identity, initial state,
entries and final state. Maximum raw input is 16 MiB; parsing rejects duplicate
keys and noninteger numbers before any owner callback. Entry count is bounded
before replay. Version changes are rejected, never guessed as migrations.

`load(raw, scope, policy_id, reducer, trusted_head)` verifies exact expected scope
and policy and requires the independently retained trusted head. It replays
every entry from the initial state with the supplied owner reducer, checking
each complete regenerated entry and the cached final state. Reordered, omitted,
duplicated, mutated, cross-scope or incompatible-policy records fail closed.
No partially replayed journal escapes. Load failure cannot overwrite a live
journal. Reducers must therefore remain pure even during failed replay.

The reference implementation MUST reject inconsistent archives and return the
same canonical save bytes after successful load; exact retries after load MUST
retain their original receipts without repeating the reducer. The trusted head
MUST match the reconstructed complete chain. [YWE-REQ-0052]

## Verification and remaining work

`tests/test_m4_state_journal.py` exercises isolated reference owners, including
atomic rejection, duplicate delivery, conflicting retries, concurrent admission,
compensation, corruption, scope isolation and replay. Counter-like test owners
prove journal mechanics only; they do not prove player progression semantics.

Full player and branch schemas, domain-owned admission, perception adapters,
migration, distributed ordering, multi-scope atomicity, reconciliation and branch
merge remain M4 work. Neither this contract nor a passing reference suite closes
any M4 deliverable or authorizes platform-specific product code before M10.
