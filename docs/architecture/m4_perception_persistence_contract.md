# M4 observer-scoped perception persistence

Status: active bounded reference contract. Owner: State and synchronization
maintainers. Partition: `ywe_core`. Requirement: [YWE-REQ-0053]. Decision: ADR-0045.
Adopted before implementation under the owner's October 14, 2026 M4 resumption.

## Responsibility and composition

`core/perception_engine/persistence.py` owns one observer's persisted view of
declared truth. It MUST compose each view through the existing M3
`PerceptionEngine`, validate the original issued result, and preserve the complete
truth input and provenance without publishing any objective-state mutation.
It MUST replay accepted views under the same immutable observer, world, Core
binding and visibility rules. [YWE-REQ-0053]

`PerceptionStore(world_id, observer_id, binding, rules, sources)` is a trusted
composition boundary. `binding` is an exact M3 CoreBinding; `rules` is a tuple
of exact PerceptionRule values; `sources` is a tuple of `(TruthInputSnapshot,
CoreProvenance)` pairs supplied by the truth owner. No client-supplied overlay,
acceptance label or serialized result cookie confers admission authority.
This reference composition does not authenticate remote players or establish
multiplayer authority grants. The store receives no objective journal, reducer
or world write capability. Existing M3 producers and schemas remain unchanged.

Each source has a unique snapshot reference and `scope_ref == world_id`.
The complete snapshot may retain explicitly scoped shared, branch, player and
derived facts; the store does not elevate any fact's authority. References and
world/observer identifiers obey the journal's 1–128 character identifier grammar.
Input values are validated and privately copied at construction. No mutable
caller-owned catalog or rule collection is retained. The Core binding is copied
before constructing the private engine.

The source catalog has at most 128 snapshots, each at most 65,536 M3 canonical
bytes including its provenance, with at most 1 MiB in aggregate. There are at
most 256 rules and at most 65,536 canonical rule bytes. Invalid construction
fails before a usable store escapes. Final state and packet limits remain those
of the journal; a larger otherwise-valid M3 overlay fails atomically and is never
clipped. These are explicit reference transport bounds, not new M3 limits.

## Admission, identity and state

`publish(request_id, expected_revision, truth_ref)` resolves only a retained
truth source, constructs the exact PerceptionRequest with the fixed observer and
rules, and delegates to PerceptionEngine. Only an original validated COMPLETED
or NO_OP result with an exact PerceptionOverlay and objective effect NONE can
be persisted. A refused result, unknown source or resource overflow publishes
nothing and reserves no request identity. Successful empty-entity views are
recorded, including their complete provenance.

The journal scope is `(world_id, player_perception, observer_id)`. Its policy ID
is `perception.v1:` plus the SHA-256 digest of canonical JSON containing the
record format, scope, complete Core binding and ordered rules. Source catalogs
are not part of that policy identity: a later construction may add sources, but
every retained historical reference used by the journal must still resolve to
the exact snapshot and provenance digests recorded in its packet. Catalog loss
or changed historical content fails replay; it is not silently migrated.

Each packet contains only `request_ref`, `truth_ref`, `truth_sha256` and
`provenance_sha256`. Digests of M3 values use M3 canonical ASCII JSON; journal
encoding continues to use its own specified UTF-8 encoding. No conversion of
numeric values, normalization or truncation is permitted. The private reducer
reconstructs the request from copied catalog data and regenerates the complete
overlay on every first admission and replay. An exact retry is answered by the
journal without repeating composition. Changed request identities, revision
conflicts and capacity follow the scoped journal contract.

`state()` returns a detached PerceptionStateRecord: `format` is
`ywe.perception_state.v1`; `world_id`, `observer_id`, `truth_substrate_ref`,
`overlay` and `objective_effects` are required. The last field is always NONE.
Initially both truth reference and overlay are null. After publication the truth
reference identifies the overlay's complete request truth and the overlay uses
the existing M3 PerceptionOverlay shape. The record schema is
`data/schemas/m4_perception_state_schema.json`; schema validation establishes
shape, while the owner and replay establish identity and semantics.

## Checkpoints and replay

`checkpoint()` returns `(archive_bytes, trusted_head)` from one committed
revision under the journal lock. This additive journal operation avoids pairing
an archive with a head read after a concurrent commit. The caller retains the
head through its trusted storage channel; including it beside an untrusted
archive does not authenticate that archive. Existing save/head calls remain
available on the journal, with their original independent observations.

`PerceptionStore.load(raw, trusted_head, world_id, observer_id, binding, rules,
sources)` constructs the owner privately, verifies the scoped journal and exact
empty initial record, and replays all entries through the private engine. It
MUST reject changed observer/world/policy, missing or changed historical truth,
tampered cached overlays and mismatched trusted heads. A successful reload MUST
produce identical archive bytes and retain exact retry receipts. A failed load
cannot mutate an existing store or the caller's truth inputs. [YWE-REQ-0053]

The implementation is a bounded conformance oracle without disk, network,
clock, randomness or service dependencies. Journal errors remain stable codes;
construction uses INVALID_POLICY or INVALID_VALUE, and unresolved publication
uses UNKNOWN_TRUTH. Reducer refusal remains POLICY_REJECTED and failed archive
reconstruction remains INVALID_ARCHIVE. Internal exception text is not returned.

## Compatibility and verification

This is an additive M4 adapter and record schema. The two legacy perception
persistence descriptor schemas remain explicit debt until final player/location
integration and their consumer migration are implemented; neither is relabeled
complete by this slice. Cross-scope synchronization, branch merging, migration
and distributed admission remain open. No M4 deliverable or exit closes here.

Verification covers actual M3 engine output, two observer views over identical
truth, input/output alias isolation, original-result validation, exact retries,
concurrent checkpoint consistency, replay, changed policy/source refusal,
corruption, source loss and bounded atomic refusal. Tests compare complete
objective input bytes before and after publication and replay, including failure.
Single-executor review is recorded; no independent review is claimed.
