# M4 origin progression persistence

Status: adopted reference contract. Requirement: YWE-REQ-0055. Decision: ADR-0047.
Owner: State and synchronization maintainers. Adopted before implementation
under the owner's resumed M4 roadmap authorization.

## Responsibility and compatibility

`core/narrative_engine/origin_progression.py` is a bounded reference owner for
the origin-phase and memory component of player state. It composes the scoped
commit journal. It does not replace the legacy PlayerRuntimeState format or
claim to assemble the final player record. Existing origin placeholders remain
open until that integration. No M3 producer or historical evidence is changed.

The owner MUST create only the configured initial phase, retain a veiled
creation record, admit only explicit profile transitions backed by qualified
action and memory records, and append rather than overwrite memory. It MUST
bind world/player, policy, writer and evidence on commit and replay. No branch,
world, ASH, resonance, ability or companion write capability is supplied.
[YWE-REQ-0055]

## Trusted composition and public operations

`OriginProgressionStore(world_id, player_id, profile, creation, grants, evidence,
action_schema, memory_schema)` receives immutable copies of all inputs. The
host supplies already-qualified narrative evidence, the two existing standalone
v1 schemas, and writer grants. This is a trusted local composition boundary:
the host must authenticate publishers and qualify the truth of action,
diagnostic and generation references before construction. Schema validity and
hashes alone do not establish their truth. Remote authentication, narrative
generation and distributed authority epochs remain later work.

The closed profile has an ID, initial phase, up to 16 distinct phases and up to
32 directed transitions. Each transition names distinct from/to phases and a
minimum of 1–16 distinct meaningful actions. The WRW reference profile supplies
the existing six phases in order; its first transition requires two distinct
actions to represent repeated patterns, subsequent transitions require one.
These are explicit reference admission rules, not automatic advancement or a
claim that action counts establish narrative meaning. The trusted catalog's
target phase is a qualified narrative decision. No phase names are hardcoded
in the neutral owner. Creation names a mortal identity reference and complete
CoreProvenance; its initial identity status is fixed to veiled.

Each grant binds one principal to a nonempty subset of `remember` and `advance`.
`writer(principal)` is a trusted composition API returning that principal's opaque
handle, issued afresh per owner; possession of the store itself is privileged. Publication
requires exact handle identity from that owner. A copied handle, serialized
principal or a handle from another owner cannot authorize a write. The host
must expose the restricted handle operation rather than expose the owner to
untrusted callers. This is an in-process capability boundary, not a Python
reflection sandbox.

`publish(writer, request_id, expected_revision, evidence_ref)` selects immutable
catalog evidence. Each closed evidence bundle binds evidence ID, world, player,
operation, prior phase, target phase, full action records, full memory records
and CoreProvenance. Actions and memories validate against the exact supplied
schemas, require v1 wire IDs/version `0.1.0`, nonempty source references and
bounded identifiers. Actions must name this player, be meaningful (not minor
input spam), and be distinct. Every memory must point to one included action,
and its optional branch must match that action's branch. At least one memory
is retained per action. Memory identity cannot be reused under a new commit;
an exact request retry returns the original receipt. `remember` leaves phase
unchanged. `advance` requires the exact current prior phase and a configured
edge with sufficient distinct actions. Advancing also consumes each supporting
action once, preventing one action from advancing multiple phases.

## Persistence, limits and failure

Policy identity binds format, world/player, creation, complete profile, grants
and both schema digests. The catalog is separately content-addressed per entry
so later catalogs may extend it without changing old identities. A changed or
missing historical bundle prevents replay. Schemas must be standalone Draft
2020-12 documents with their exact existing document IDs; reference keywords
are rejected to prevent implicit retrieval.

All values obey the journal's exact integer JSON and detached-copy contract.
There are at most 32 principals and 128 evidence bundles, at most 16 actions and
16 memories per bundle, 128 retained memories, and 1 MiB of catalog bytes.
Every bundle and complete state remains within 65,536 bytes/4,096 nodes/depth32.
The journal bounds commits to 128. Capacity failures leave state and request
identity untouched. Construction fails atomically on invalid policy/evidence.
An exact retry retains the original expected revision as well as request ID,
principal and evidence; changing any of those fields is an identity conflict.

`state()` returns a detached complete component. `checkpoint()` pairs archive
and trusted head under the journal lock. `load` reconstructs the owner from
explicit trusted inputs and replays every packet, checking exact empty-history
genesis, request identity, writer grant, catalog digest and transitions. It
rejects compensation entries: origin correction and full player compensation
need their own explicit policy; no automatic inverse or history deletion is
invented. Retry, stale revision and concurrent ordering use journal semantics.
Errors contain stable journal codes, never source contents.

## Verification and remaining integration

Tests must exercise actual phase advancement and memory retention through
checkpoint/replay, exact retries, concurrent conflicting advances, wrong writer,
cross-player evidence, invalid action/memory links, phase skips, reused evidence,
input/output aliasing, changed policy/catalog, schema/ref substitution and limits.
They must distinguish trusted test evidence from externally authenticated facts.
The checked-in reference profile and complete example component must validate.

Final player assembly, legacy reference resolution/migration, identity revelation,
bloodline and companion progression, branch linking, compensation and multiplayer
remain M4 work. No M4 exit or placeholder closes through this slice. Review is
single-executor; independent review is not claimed.
