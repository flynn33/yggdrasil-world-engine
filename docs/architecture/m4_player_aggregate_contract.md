# M4 player aggregate admission contract

Adopted reference realization: YWE-REQ-0056 / ADR-0048. This additive contract
implements player-local atomic admission under the M4 roadmap. It preserves the
legacy player schemas and their historical examples. The implementation is a
bounded, platform-neutral reference owner, not a production persistence service.

## Sources and ownership

The player runtime, celestial identity, ability progression, branch integration,
companion presence, Raven and twin-wolf contracts govern domain meaning. The
existing player schema cross-reference policy remains in force: the player spine
contains string references. A snapshot carries a separate resolved-record table;
an arbitrary inline object or a serialized accepted flag grants no authority.
WRW-specific seed records, identity/ability edges and companion identifiers are
explicit profile/configuration inputs. Core does not derive them from a class,
morality score, source name, or presentation adapter.
The concrete player aggregate and domain-rule modules are classified as WRW
reference-profile realizations because they consume these fixed legacy field
families. Their compatibility semantics are not universal YWE Core ontology.

`PlayerStateStore(world_id, player_id, profile, initial_spine, grants, records,
updates, schemas, origin_policy)` is a trusted composition boundary. It owns one
`player_state` journal. The host must qualify record/update catalogs and their
CoreProvenance before constructing the owner. Hashes detect changed content;
they do not authenticate external facts. Each grant has an explicit
`source_system` and operation names. Host adapters receive no writing grant.
`writer(principal)` issues an opaque local capability; publication requires the
exact handle from that owner. Possession of the store itself is privileged.
Only Narrative may advance origin phase. Other sources require their own origin
remembrance grant plus restricted aggregate operations. Perception may append
only observer overlays, Realm only threshold/location references, and Quest only
quest-history/future-bias references.

## Versioned state and catalogs

The v2 player spine retains the closed v1 field groups, adds
`origin_progression_state_ref` and `ability_state_refs`, requires the persistent
Raven reference, and selects `ywe.player_state_update_packet.v2`. The remaining
legacy fields, optional absence and collection order are preserved. Initial
identity remains explicitly veiled. After a successful update the lifecycle is
continuing and only the initial-state marker is removed.

A snapshot has format `ywe.player_aggregate.v1`, world/player/profile identity,
the spine, a resolved `records` table, accepted update receipts and compensations.
Each table entry has `kind`, `document` and `sha256`. Catalog records additionally
bind `ref`, world, player, branch and CoreProvenance. Every selected historical
record remains immutable. The sole mutable owned record is the origin component
at the spine's reserved origin reference; its document and digest advance in the
same transaction. Action/memory records from origin evidence are retained under
their declared identities and linked from the spine. They cannot overwrite a
different catalog record. Snapshots and journal archives retain history; capacity
is a refusal, never silent eviction.

Known runtime record kinds are celestial, agent, branch_history, plane,
bloodline, wolf, raven, ability, manifestation, action and memory. Their exact
schemas are supplied explicitly and bound in policy identity. Schemas permit
only acyclic local fragment references; remote or unknown references are rejected
without retrieval. A `reference` record qualifies an external terminal reference
with category, truth scope, subject and source digest. It is not an executable
world/branch/perception writer. A `consequence` record binds consequence/effect
identity, the intended update, player, branch, actions and external result refs.
The player-local consequence receipt cannot claim that the player owner committed
another truth scope. An objective player update cannot be labeled DiagnosticNoOp.
Wire versions are exact: celestial, agent, branch history, action and memory use
`0.1.0`; Raven and wolf manifestation use `1.0.0`; resonance and ability use
`2.0.0`. Unknown versions fail. Observer references cannot stand in for objective
worldstate results or branch events.

## Typed updates and atomicity

`publish(writer, request_id, expected_revision, update_ref)` selects a closed
immutable update: update/world/player/branch/source-system identifiers,
operations, evidence refs, consequence ref and CoreProvenance. No generic path,
merge, increment, deletion, unvalidated replacement state or authority flag is
executable. The following typed operations are admitted:

- `origin`: select one origin evidence bundle. Ordinary updates contain exactly
  one such operation, including a remember operation when the phase is unchanged.
- `replace`: compare a named current slot to `previous_ref` and select `next_ref`.
  Slots are celestial, agent, plane, bloodline, wolf and raven.
- `ability`: compare the current record for one ability (or explicit null for a
  new ability), select its next record, and supply explicit condition refs.
- `manifest`: add one qualified wolf manifestation event.
- `dismiss`: remove a currently active manifestation reference with a qualified
  dismissal condition; retain its record and consequence history.
- `append`: append qualified references to one explicitly enumerated continuity
  collection, preserving existing order and rejecting duplicate membership.
- `branch`: select qualified next branch, agent and append-first history records,
  with prior branch, destination location and branch-event evidence. It never
  creates branch truth. Event/action/update links identify this update's origin
  bundle. Stable agent identity persists. Player-owned identity, resonance and
  Raven state travel with the player; branch-bound abilities require explicit
  destination records with retained provenance and new qualified history.
- `compensate`: the sole operation in a reasoned compensation update, naming a
  previously accepted request and nonempty reason refs.

All ordinary operation evidence is supported by meaningful actions retained in
the same origin bundle. Those actions must name the aggregate's current branch.
New actions declare this resulting player update. An unchanged retained action
may support a fresh memory while preserving its original result refs and single
action membership. Update evidence must be qualified `evidence_refs` records
covered by the selected actions' source refs. Observer evidence cannot qualify
objective player changes. Their external
world/branch result references resolve to qualified same-world records. The
consequence's action set must match. The pure origin policy runs inside the
aggregate reducer; no component journal is published. All subsequent domain,
reference, consequence and complete-state size checks precede the one commit.
Any failure leaves every component, revision and request identity unchanged.
Repeated writes to one slot, ability, collection or branch are rejected. Branch
transfer follows origin reduction and precedes destination component changes;
source actions retain the departure branch. Current and nested agent diagnostic,
action-history, location and branch-event links must resolve.

Every operation is separately authorized. Serialized source-system names are
compared with trusted grants; they do not authenticate the caller. Meaningful
updates consume both update identity and `(consequence_id, effect_id, player_id)`.
A fresh request cannot apply the same domain effect twice. Exact transport retries
return their original receipt, including the original expected revision, before
reduction. Separate players may receive separately qualified participant effects.

## Domain transition rules

Origin phases and celestial reveal states are separate axes. Identity follows
explicit profile edges; each state has its matching reveal status. Revealed
fragment identities/content and prior evidence persist. A reveal requires new
qualified play evidence; no initial name, fragment or reveal is accepted.
Identity edges move forward only. WRW chooses adjacent edges; explicit profiles
may choose forward skips. Reveal evidence must be new to the prior identity and
occur in the update's action-linked qualified evidence.

Resonance records use the adopted exact q6 schemas. Independent wolf channels
are not normalized. Seeds are explicit qualified records, never invented zeros.
Initial bloodline signals are unknown/dormant and unrevealed; initial wolf
signals are latent. Resonance changes do not create companion manifestation.
The Raven retains its profile companion ID and mortal binding. Story separation
requires explicit qualified condition evidence; it does not remove the slot.
Wolf manifestation requires nonempty trigger criteria, duration endpoints,
dismissal and source evidence. Dismissal preserves the event record/history.
Duration endpoints differ. A consumed manifestation event ID cannot be reapplied
through the same or an aliased reference after dismissal.

Abilities have all ten canonical states. The profile lists allowed directed
transitions, including recovery from decoherence. New abilities begin latent;
sealed exit requires explicit condition evidence. History is append-first and
transformation preserves source provenance. A closed v2 ability record uses
optional exact decimal coherence `{coefficient, exponent, status}` with a
canonical signed decimal coefficient string and bounded exponent. This is a
lossless representation, not an invented zero-to-one semantic bound. Full
ability effects/combat remain M6 work.
The WRW graph chooses latent/pressured/eligible/unlocked first activation, then
explicit coherence, mastery, instability, transformation and decoherence edges.
Every stage can seal; qualified unsealing selects an explicit target. New latent
abilities reference current play evidence. State changes and branch rebinding
append qualified history. No timer infers unsealing.

Compensation is append-only and records its target and reasons. Only ordinary
updates consisting of origin remembrance plus replacements of configured
reversible resonance slots are eligible. Their memories, actions, consumed IDs
and original consequence remain. Every affected current slot must still match
the target's post-state; otherwise refusal prevents undoing later work. An
already compensated target cannot be compensated again. Origin phase, identity,
abilities, branch history and companion events have no implicit inverse.
The compensation target in the packet must match the journal envelope during
publication and load. Loading a trusted earlier checkpoint supports recovery;
it does not erase the audit history of a later independently held checkpoint.
Compensation has a fresh consequence/effect identity with empty action and
external-result lists. Its reasons are qualified `evidence_refs`; the original
consequence and consumed identity remain. A target must have at least one
reversible resonance replacement.

## Persistence, compatibility and limits

Policy identity binds format, scope, profile, grants, exact initial spine,
all selected initial catalog qualification, schema digests and pure origin
policy identity. Per-packet digests bind the
selected update and every referenced catalog record. Catalog extension is
permitted; changed or absent historical records prevent replay. `state()` returns
a detached snapshot; `checkpoint()` pairs archive and trusted head under the
journal lock. `load` reconstructs from trusted inputs, compares exact genesis,
replays transitions and verifies outer/inner request and compensation identities.

Use the existing journal's exact integer JSON, 65,536-byte/4,096-node/depth-32
state bound and 128-entry limit. Catalogs are limited to 128 records/updates each,
1 MiB each; grants to 32 principals; operations to 16 per update; references and
retained accepted receipts to 128. Fail closed before publishing partial state.

The [qualified player migration contract](m4_player_migration_contract.md) adds
two explicit source-bound adapters, imported v3/aggregate-v2 baselines and typed
active context continuation. Closed v1 continuing state requires a qualified
origin baseline; historical sparse resonance requires complete resolved records
and exact agreement with each supplied scalar. Unsupported active fields and
missing qualification refuse. Imported history starts a separate genesis and
does not invent historical receipts. The original constructor remains initial-v2
only, and original archives retain their byte identity. The explicit
`from_migration` / `load_migrated` factories select the new imported dialect.
Cross-owner coordination and multiplayer retain their separate M4 gates.

## Required evidence

### Pure owner policy for coordinated admission

`PlayerStatePolicy` provides the same nine-argument trusted configuration and
the same explicit `from_migration(result, migration, raw_source, *configuration)`
factory as the store. The factory retains complete source re-verification,
profile/schema/selected-wrapper binding and imported consumption; a bare imported
snapshot is never a public constructor. This additive interface is adopted under
YWE-REQ-0056 and YWE-REQ-0057 before extraction for M4 synchronization.

The policy exposes immutable `scope` and `policy_id`, detached `initial_state()`,
`packet(principal, request_id, update_ref)` and `reduce(state, packet)`. Reduction
copies both inputs, validates the same complete domain admission and bounds, and
returns detached state. It has no journal, revision counter, retry cache or host
effects. It consumes an owner state verified by trusted composition; it does not
authenticate arbitrary client snapshots. `record(ref)` returns a detached exact
qualified catalog wrapper for a future coordinator to compare with staged truth.
Unknown records fail with the existing UNKNOWN_EVIDENCE code.

`PlayerStateStore` remains the public standalone journal/capability wrapper, with
unchanged constructors, writer handles, publication, checkpoint and loading.
Its opaque handles stay local to that store. Policy identities, initial bytes,
packet bytes, prior refusal codes and all old and imported archive bytes remain
unchanged. Exact retries continue to bypass reduction in the journal. The store
retains its documented and tested scope, policy, initial-state, packet, reducer
and domain-validator hooks explicitly; no generic attribute forwarding is added.

This extraction adds no cross-owner commit authority. A future coordinator must
independently bind qualified external records to the actual staged owner vector,
keep participant request/compensation identities distinct from transaction IDs,
and enforce whole-container bounds. Those behaviors are not implemented merely
by exposing pure owner policies.

Execute a combined origin/identity/resonance/ability update through one commit
and exact replay; late failure with no partial mutation; distinct-request effect
duplication; capability/source mismatch; initial reveal refusal; companion and
ability unhappy paths; branch mismatch and authorized transfer; reasoned
compensation with retained memory; stale/racing updates; changed/extended catalogs;
forged genesis/envelopes; detached state; complete aggregate limits; and unchanged
independently held world/branch/perception records. Unit fixtures are trusted
qualification examples, not proof of external authentication. Cross-owner
coordination, multiplayer and complete legacy migration retain their M4 gates.
