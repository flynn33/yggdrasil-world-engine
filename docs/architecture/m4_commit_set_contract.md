# M4 commit-set journal reference contract

**Adopted reference realization:** YWE-REQ-0058 / ADR-0050, October 14, 2026. Source checkpoint: `93bc35208e187a5c8578e4c7e04346dadd057ce2`. The journal MUST preserve the exact component, identity, atomic publication and replay invariants specified below. [YWE-REQ-0058] This contract specifies journal mechanics only; concrete world, branch, location, multiplayer admission, and observer coordination policies remain separate contracts.

## Purpose and compatibility

`CommitSetJournal` publishes one bounded set of owner transitions and round decisions in one local snapshot. Its `CommitSetBinding` is an atomicity/audit identity, not a `TruthScope` and not a new authority tier. Every component retains its existing exact `TruthScope` and immutable owner policy pin. Realm/location partitions retain their governing shared or branch scope.

The existing `CommitJournal`, `CommitReceipt`, formats, codecs, limits, public signatures, refusal behavior, and standalone owner archives remain unchanged. There is no multi-journal prepare/reserve/commit protocol. This is an in-memory reference mechanism with trusted pure collaborators, not a storage service, transport, distributed transaction protocol, callback sandbox, or player-visible unrestricted history API.

## Public API

The new module exposes:

```python
@dataclass(frozen=True)
class CommitSetBinding:
    world_id: str
    container_id: str
    def to_record(self) -> dict: ...

@dataclass(frozen=True)
class RoundReceipt:
    revision: int
    entry_digest: str
    state_digest: str
    decisions_digest: str

def initial_component(binding, component_id, scope, owner_policy_id, state) -> dict: ...
def advance_component(binding, round_id, raw_step, previous_component) -> tuple[dict, dict]: ...
def canonical_round_packet(packet) -> dict: ...

class CommitSetReadView:
    def decision(self, principal, proposal_id) -> dict | None: ...
    def component_request(self, component_id, owner_request_ref) -> dict | None: ...
    def component_at(self, exact_head) -> dict: ...

class CommitSetJournal:
    def __init__(self, binding, policy_id, initial_state, reducer): ...
    def commit(self, round_id, expected_revision, packet) -> RoundReceipt: ...
    def state(self) -> dict: ...
    def vector(self) -> list[dict]: ...
    def decisions(self, round_id) -> list[dict]: ...
    def save(self) -> bytes: ...
    def head(self) -> str: ...
    def checkpoint(self) -> tuple[bytes, str]: ...
    @classmethod
    def load(cls, raw, binding, policy_id, initial_state, reducer, trusted_head): ...
```

The reducer signature is **`reducer(binding, current_state, canonical_packet, history)`**. It returns exactly `{"decisions": [...], "component_steps": [...]}` or those keys plus optional `"state"`. Optional state is a redundant assertion of the complete final container, including journal-derived heads. The journal always reconstructs the final state from the raw steps; it never installs a reducer-supplied final state directly. All JSON inputs and returns are detached, bounded exact JSON values. The immutable binding may be shared. No live journal object is passed to the reducer.

`CommitSetBinding` is exact-type checked and frozen. Its exact record is `{format:"ywe.commit_set_binding.v1",world_id,container_id}`. IDs use the current journal's 1..128 ASCII identifier grammar. `policy_id` binds the immutable coordinator policy and its admission/ordering/qualification semantics. Trusted construction must supply the actual policy. The journal does not discover or authenticate arbitrary policy IDs.

`initial_component` takes an exact `TruthScope` object, checks its world against binding, validates and detaches state under the existing owner bounds, and returns a complete revision-zero component with the genesis head below. `initial_state` is the complete container shape below; constructor checks every component's revision is zero and its head is exactly regenerated from its pin/state. The same exact trusted initial state must be supplied to `load` and match the archive. No caller-supplied historic head establishes trust.

## Closed data shapes

Every shape below is closed: no undeclared keys. Exact integer means `type(value) is int`, excluding bool. Digests are lowercase 64-character SHA256 hex. Each scope record is exactly the existing `{world_id,truth_scope,subject_id}` and must instantiate a valid `TruthScope` in the binding world.

- Component pin: `{component_id,scope,owner_policy_id}`.
- Component head: pin plus `{revision,head_digest,state_sha256}`.
- Complete component: head plus `{state}`. The state is one existing bounded owner object.
- Container: `{format:"ywe.commit_set_state.v1",world_id,components}`. Components are sorted by `component_id`, with unique IDs. Multiple components may share a scope; an actual policy must authorize disjoint owner partitions. The journal only enforces distinct IDs and immutable pins.
- Round packet: `{format:"ywe.closed_round.v1",round_id,sequence,proposals}`. `sequence` equals original `expected_revision`, and its round ID equals the commit envelope. This is a logical counter, not an RFC timestamp.
- Proposal: `{principal,proposal_id,sequence,predecessor_refs,reads,writes,components,compensations}`. Principal/proposal ID are identifiers; sequence is a nonnegative bounded exact integer. Predecessors are unique `{principal,proposal_id}` records in the same closed proposal set. Reads are exact component heads sorted by component ID. Writes are unique component IDs sorted lexically. Components are sorted unique `{component_id,scope,owner_policy_id,owner_request_ref,packet}` records. Each packet is an existing bounded owner object. Compensation mappings are defined below. Empty read/write/component arrays are structurally permitted so a policy may record a denial or deliberate no-write decision; substantive admission belongs to that policy.

`canonical_round_packet` copies and validates the complete input, sorts the set-like arrays above and compensation mappings by `(component_id,component_request_ref)`, rejects duplicate component/predecessor/proposal identities, missing predecessors and cycles, and emits stable topological proposal order. Among eligible proposals the tie-break is `(sequence,principal,proposal_id)`. It preserves every other supplied value; it does not fill defaults, manufacture IDs, renumber sequences, remove duplicates, or infer domain accesses. Commit requires packet bytes to equal this normalization. Policy must derive/check actual accesses and source qualification; a caller cannot hide a write by omitting it from metadata.

## Reducer trace and head generation

A raw step is exactly:

```text
{component_id, scope, owner_policy_id, principal, proposal_id,
 owner_request_ref, packet, state_after, create}
```

`create` is an exact bool. Steps are in proposal order and within each proposal in component-ID order; at most one step per component per proposal. Each accepted step must correspond exactly to the same selected component record in that proposal, including canonical packet bytes, scope, policy and owner request. Its component ID must appear in that proposal's declared writes. The policy additionally checks those declarations against real actions and qualifications. Rejected/duplicate decisions have no steps. The journal rejects orphan, missing-index, reordered, duplicated, or differently attributed steps.

`advance_component(binding,round_id,raw_step,previous_component)` is a pure detached helper. For an existing component, `create` is false, `previous_component` is its complete current staged record, and the exact pin must match. For explicit creation, `create` is true and previous is `None`; the raw step supplies the pin. The helper checks all closed fields, identifier/scope/owner bounds and previous component state's digest; it does not authenticate a caller-supplied previous head by itself. Only lookup in the journal's staged state establishes that head's provenance. It returns **`(new_complete_component, finalized_step)`**.

Genesis component head is SHA256 of canonical:

```text
{format:"ywe.component_genesis.v1", binding, component_id, scope,
 owner_policy_id, state_sha256}
```

Initial components have revision 0. A transition or creation head is SHA256 of canonical:

```text
{format:"ywe.component_step.v1", binding, component_id, scope, owner_policy_id,
 previous_head, revision, round_id, principal, proposal_id, owner_request_ref,
 packet_sha256, before_state_sha256, after_state_sha256}
```

Here `previous_head` is the previous digest (or null for creation), revision increments by one (creation starts at 1), and `before_state_sha256` is previous state digest (or null for creation). Accepted steps advance even if the resulting state bytes are identical. `after_state_sha256` hashes canonical `state_after`; packet hash uses canonical owner packet bytes. Heads never include the enclosing entry digest, avoiding a hash cycle. They are distinct from standalone journal heads.

The finalized serialized step is exactly `{round_id,component_id,scope,owner_policy_id,principal,proposal_id,owner_request_ref,packet_sha256,before,after,create}`, where before is the complete component head or null and after is the complete new head. Full intermediate states/packets are not duplicated in the archive's finalized trace. They are regenerated by replay from the entry packet and trusted reducer.

A coordinator may call `advance_component` while staging earlier accepted proposals so later predecessor proposals see the correct heads. After reduction the journal independently repeats the helper on its own pre-round state in raw-step order, validates every intermediate owner state, and derives the only publishable final state and finalized trace. A supplied optional `state` must equal those regenerated bytes. Creating an existing ID or updating a missing one is invalid. Existing pins never change and components never disappear. Domain ownership, actual owner execution, and permission to create are policy obligations, not facts proved by a hash.

## Decisions and immutable history

A raw decision is exactly `{principal,proposal_id,status,code,prior_decision,step_indices}` in canonical proposal order, one per proposal. Status is `ACCEPTED`, `REJECTED`, or `DUPLICATE`; code is an identifier with no exception text. Accepted uses `code="ACCEPTED"`, null prior and precisely the indices of its raw steps. Rejected has null prior and empty step indices; its code must be declared by the coordinator policy. Duplicate uses `code="DUPLICATE"`, empty steps and an exact prior reference. Journal adds `proposal_sha256` from the full canonical proposal to form each serialized decision. The journal checks association, ranges, complete coverage and the required status for an already-recorded identity. An accepted no-write decision is permitted by mechanics, subject to policy.

A prior reference is `{round_id,decision_index,decision_sha256}`. Decision digest hashes the complete serialized decision. The first recorded original decision is the canonical target: duplicates do not form chains of duplicate references. A duplicate of a rejected decision remains dependent on that rejected original outcome; coordinator dependency logic must not treat all duplicates as prior successes.

`history` is an immutable snapshot taken before the current round. It has no mutation, commit, host-I/O, live journal or arbitrary callback API. Its methods operate on private immutable canonical bytes and return fresh detached objects:

- `decision(principal,proposal_id)` returns null if unknown, otherwise `{round_id,decision_index,decision_sha256,decision}` for the first recorded original decision. Malformed identifiers fail.
- `component_request(component_id,owner_request_ref)` returns null if unknown, otherwise `{round_id,principal,proposal_id,component_id,owner_request_ref,step_index,packet_sha256,head}` for the actual accepted step. Head is its complete after-head. Imported reserved identities do not create synthetic container admissions.
- `component_at(exact_head)` validates the complete exact head and returns the matching complete component, including detached state, from trusted initial state or verified prior accepted steps. A mismatched or unknown head fails `UNKNOWN_COMPONENT_HEAD`; matching only its digest or state is insufficient. No caller body is trusted.

Current-round staged state and request decisions remain coordinator-local and use the pure head helper; history contains only previously committed rounds. Compensation targets in this first slice must be previously committed. Historic bodies are reconstructed during private replay, indexed by complete exact head, and retained as canonical byte snapshots. With 16 genesis components and 64*32 accepted steps there are at most 2,064 state bodies, each at most 65,536 bytes (129 MiB payload before bounded metadata). Copies need not be made for each read-view construction. Escaped read views remain fixed snapshots and cannot observe later publication.

## Identity, compensation and failure behavior

The round fingerprint binds `{round_id,expected_revision,packet}`. Exact committed-round retry returns its original frozen receipt before stale/capacity/reducer checks. Changed content under the same round ID fails `IDENTITY_CONFLICT`. Fresh rounds require `expected_revision` equal committed count.

Proposal identity is the tuple `(principal,proposal_id)` and binds the complete canonical proposal. Previously recorded identical proposals must return a `DUPLICATE` decision referring to the original; changed proposals abort with `IDENTITY_CONFLICT`. A finalized rejected proposal consumes decision identity, but no owner request or effect. An entirely failed round reserves nothing.

An accepted owner request is keyed by `(component_id,owner_request_ref)` and maps to the exact original round/proposal/step. Reuse in a new nonduplicate proposal fails `IDENTITY_CONFLICT`; a duplicate whole proposal is checked first. No concatenated string key may confuse component or principal boundaries.

Each compensation mapping is exactly `{component_id,component_request_ref,target_round_id,target_principal,target_proposal_id,target_component_request_ref,target_component_head}`. Target head is the complete exact after-head. The current component request must name a selected component packet in this proposal. The journal verifies that the target is a previously accepted step in this container, same component and immutable policy, and every target identity/head agrees. A mapping cannot target an imported reserved ID without a real container step. The coordinator validates packet-specific linkage (for a player, `packet.compensates` and typed operation name that exact target), reason evidence, current postcondition, repeated compensation, and actual owner inverse eligibility. Multiple mapped owner compensations and fresh views may share one proposal; there is no generic whole-round inverse. The journal does not infer a packet's domain meaning.

A policy may preflight known authorization/dependency/conflict denials as `REJECTED` without running the losing owner reducer. A successful round can record those decisions alongside accepted proposals. An unexpected/late owner exception, invalid reduction, structural/identity error, serialization/bound/capacity failure, or reentrant journal access aborts the entire round. Do not catch a late owner failure and publish earlier owners. Rejected decisions in a successfully finalized round and a failed whole-round admission are different cases.

Public boundary codes: malformed exact shapes/scalars `INVALID_VALUE`; invalid binding type `INVALID_BINDING`; invalid owner scope/world `INVALID_SCOPE`; noncallable policy `INVALID_POLICY`; bounded object/round/trace/decision/entry size failure `VALUE_LIMIT`; exhausted persistent component/round capacity `CAPACITY_EXCEEDED`; stale round `REVISION_CONFLICT`; altered/reused identity `IDENTITY_CONFLICT`; missing compensation admission `UNKNOWN_COMPENSATION`; unknown decisions(round_id) lookup `UNKNOWN_ROUND`; unknown historic exact head `UNKNOWN_COMPONENT_HEAD`. A reducer exception or reentrant attempt maps to `POLICY_REJECTED`, without exception text, even if the reducer catches the access exception. A returned malformed/inconsistent trace maps to `INVALID_REDUCTION`; explicit output bounds still report `VALUE_LIMIT`, and component-capacity exhaustion reports `CAPACITY_EXCEEDED`. Standalone refusal codes remain unchanged.

## Canonical codec and bounds

Use current exact JSON scalar semantics: null/bool/exact integers in +/-9007199254740991/valid UTF-8 strings/lists/string-keyed objects; no floats, custom containers, cycles, coercion or Unicode normalization. Encoding is UTF-8, sorted keys, compact separators, `ensure_ascii=False`, `allow_nan=False`. Dictionary keys count as nodes; root depth is zero. Every state and owner packet separately passes existing `_object_bytes` limits. Existing M3 source qualification bytes remain governed by their own ASCII codec.

| Value | Bytes | Nodes including keys | Depth |
| --- | ---: | ---: | ---: |
| Each owner state or packet | 65,536 | 4,096 | 32 |
| Complete container state | 2,097,152 | 131,072 | 40 |
| Canonical round packet | 262,144 | 32,768 | 40 |
| Raw reducer result including optional state | 8,388,608 | 524,288 | 44 |
| Serialized decision array | 65,536 | 8,192 | 16 |
| Complete serialized entry | 524,288 | 65,536 | 44 |
| Complete raw archive | 67,108,864 | per bounded header/entry/state | 48 |

Counts: 1..16 retained components, 1..8 proposals per round, at most 32 accepted component steps per round, 0..64 committed rounds; at most 16 reads/writes/component selections/compensation mappings per proposal and at most 8 predecessors. Limits are conjunctive; not every count-maximal collection of individually maximal objects fits the round byte limit.

Keep `core/state_journal.py` unchanged in this first implementation. Reuse its stateless scalar/encoding/hash/strict-parser helpers; implement a bounded aggregate helper with explicit byte/node/depth parameters in the new module. It must retain the existing scalar semantics and per-string 65,536-byte cap. Closed metadata plus independently bounded owner objects prevent the aggregate allowance from loosening domain values. Use iterative bound/depth walking before recursive encoding where possible. If later factoring is necessary, retain `_object_bytes` as an exact fixed-limit wrapper and require differential refusal tests plus all frozen archives; this contract does not authorize journal lifecycle refactoring.

**Capacity and deferred expansion:** capacity counts every retained parent, child, merge result and partition. Preflight the complete projected membership before reducing a creation; any candidate round that would exceed 16 components fails `CAPACITY_EXCEEDED` atomically, including a fork bundled with transfer. No partial fork, hidden deletion, parent eviction, skipped creation, or automatically failed individual proposal is used to conceal exhaustion. At 64 rounds fresh commits likewise fail. Exact committed-round retries, reads and checkpoint remain available. The reference exposes no rollover, history compaction or automatic container expansion. A future explicitly adopted version must define authenticated checkpoint handoff, component/history ancestry, identity preservation and capacity transition before a larger container can continue the same world. Fork/merge callers must surface this typed refusal; the roadmap must not describe this bounded reference as unbounded progression.

## Publication, archive and replay

One RLock and reentrancy guard cover all live public reads/commits. Validate request/canonical packet, lookup exact retry, validate fresh revision/capacity/identity, create detached current state and fixed read view, invoke the reducer, validate/recompute decisions and raw-step transitions, check all bounds including the complete candidate archive, then publish state, entry sequence, round receipts, original proposal decisions, request mappings and historical component bodies in one snapshot assignment. No successful state/history/index publication occurs earlier. The same-thread callback guard must taint the reduction on any attempted live access even if caught. Pure helpers/read-view access do not reenter the live journal.

Header is exactly `{format:"ywe.commit_set_journal.v1",binding,policy_id,initial_state}`. Genesis outer head is SHA256 of its canonical bytes. Archive is header plus `{entries,final_state}`. Each entry is exactly `{round_id,expected_revision,packet,revision,previous_digest,before_state_digest,after_state_digest,decisions,component_steps,entry_digest}`. Entry digest hashes the canonical entry excluding `entry_digest`; revision is committed ordinal, previous digest is prior outer head, and state digests hash complete container bytes. Receipt uses that revision/entry digest/after-state digest and SHA256(canonical decision array). Component heads precede outer entry hashing.

`state`, `vector`, `decisions` return detached copies; vector omits component state and is sorted by component ID. `save` returns canonical archive bytes; `head` returns genesis or latest entry digest. `checkpoint` captures a matching `(save_bytes,head_digest)` under one lock.

Load accepts exact bytes only within raw limit and a correctly shaped trusted digest. Strict UTF-8 JSON parsing rejects duplicate keys, floats/constants, oversized integers, malformed encoding and excessive depth; errors are `INVALID_ARCHIVE`, except a syntactically invalid trusted head is `INVALID_TRUSTED_HEAD`. Exact trusted binding/policy/initial-state checks precede reductions. Construct privately from trusted initial state; for each entry require the next ordinal before commit, run the same reducer with history derived only from verified earlier entries, regenerate component bodies/heads/decisions/entry bytes, and compare exact canonical bytes. Repeated entries cannot replay as retries. Compare final state and externally supplied trusted outer head. Rebuild all indexes from replay, never serialized caches. Any mismatch fails `INVALID_ARCHIVE`; no partially reconstructed journal escapes. Raw whitespace/key order need not be canonical on input, but every reconstructed serialized value and returned `save` is canonical. JSON escape spelling does not change canonical value identity.

## Required verification for this mechanics slice

Preserve all 20 frozen original/imported standalone archives, hashes and exact retries. Exercise actual extracted owner policies for multiple components; inject late second-owner/observer failure and prove state/checkpoint/vector/all identities unchanged. Test canonical closed-set permutation equivalence, dependency cycles/missing predecessors, same-scope distinct component IDs, swapped pins, exact/altered round and proposal retries, duplicate prior rejection, component request collision, optional final-state mismatch, helper/staged-head equivalence, explicit creation and cap refusal, typed compensation lookup, history detachment/exact-head rejection, replay rebuilt histories, hostile decoder boundaries, all count/byte/node/depth limits, caught reentrant access and concurrent checkpoint consistency. No test may treat journal hash mechanics as proof of domain grants or multiplayer truth qualification.

Observed sizing at source checkpoint: two actual imported player policies plus two actual perception policies produce a 53,350-byte/3,411-node/depth-10 wrapper after ordinary updates. At 16 actual visibility rules per observer the wrapper is 68,385 bytes/4,491 nodes and existing `_object_bytes` rejects it with `VALUE_LIMIT`, while each owner individually succeeds. At 64 rules it is 116,721 bytes/7,947 nodes. These justify separate aggregate bounds; they do not verify a coordinator or authenticate the synthetic cross-owner fixture. Exact measurements, complete input bodies and source hashes are in `ywe-m4-commit-set-measurements-20261014.json`.

## Approved realization paths

This increment approves only `core/commit_set_journal.py`,
`tests/test_m4_commit_set_journal.py`,
`data/schemas/m4_commit_set_journal_schema.json` and
`examples/state_journal/commit_set.example.json`, with exact catalog, guardrail
and governance integration. No new dependency, host storage, transport or platform
runtime is selected. No M4 deliverable, exit, placeholder or debt closes here.
