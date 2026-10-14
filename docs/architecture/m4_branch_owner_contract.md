# M4 branch ownership, lineage and merge

Status: adopted reference contract, October 14, 2026.
Requirement: YWE-REQ-0059. Decision: ADR-0051.
Partition: neutral YWE Core; the explicitly named WRW adapter is a separate
reference-profile compatibility surface. Source inspection at
`93bc35208e187a5c8578e4c7e04346dadd057ce2` is recorded with 30 raw/commit hashes
and 20 adverse vectors in `ywe-m4-branch-owner-design-20261014.json` in the external source-review receipt.

## Authority and compatibility

Branch ownership covers identity, parentage, event origin, compact generation
context and verified branch-domain projections. World/location owners retain
authority over their actual domain values. Player owns identity, memory,
progression and current branch bindings. Perception remains derived. The
coordinator publishes these owners together; a successful branch reduction alone
does not commit or authorize another owner.

Existing branch/event schemas are open descriptive contracts. They require
nonempty parent strings and do not prove exact head, owning player, choice
membership or actual consequence. The new schemas are additive; old schemas and
all existing player/perception archives remain unchanged. No legacy branch is
activated by guessing its parentage or treating a continuing history as a new
root. Historical import requires a separately qualified source-bound adapter.

`component_id` is registry identity, distinct from `TruthScope`. Lineage and
location may share a branch scope only under explicitly disjoint registered
partitions. Branch may not rewrite ontology, profile law, geography, shared facts
or another player's private branch. No private-to-shared merge path exists.

## Pure owner interface

`BranchStatePolicy(world_id, branch_id, owner_player_id, profile, grants,
records, proposals, schemas)` receives eight trusted, detached, bounded inputs.
It exposes immutable `scope`, `component_id`, `policy_id`, and these methods:

- `initial_state()` returns an unpublished empty owner reservation.
- `packet(principal, request_id, proposal_ref)` validates identifiers/grants and
  binds selected proposal, qualification records and exact expected heads.
- `requirements(packet)` derives the complete read set, write keys and explicit
  component creations from the proposal and registered definitions.
- `reduce(state, packet, view)` copies state/packet, uses coordinator-verified
  detached views, and returns a complete detached owner state.
- `record(ref)` returns the exact detached qualified catalog wrapper;
  unknown references fail `UNKNOWN_EVIDENCE`.

The owner has no journal, publication, revision allocator, retry cache, ambient
clock or host effect. Its verified-state boundary matches the existing pure
player policy: it is not an authenticator for arbitrary client snapshots.

The exact initial envelope is:

```text
{format: "ywe.branch_owner.v1", world_id, branch_id, owner_player_id,
 branch: null, events: {}}
```

This reservation MUST NOT appear as a committed leaf. It is installed only
during explicit creation admission, and publication requires a complete branch.
There is no pregenerated branch catalog. Final envelopes retain the same keys;
`branch` holds the final state and `events` maps retained event IDs to exact
documents. The branch alone owns its occurrence and consumed ledgers. [YWE-REQ-0059]

The policy ID binds rule version, component/scope/player, complete profile/law,
grants, schemas and selected bootstrap qualification. Packets bind selected
catalog bytes; unrelated catalog extension must not change old replay.

## Exact common types

All listed objects are closed. Use journal identifiers, lowercase SHA-256,
exact safe integers and canonical JSON. An exact component head is:

```text
{component_id, scope, owner_policy_id, revision, head_digest, state_sha256}
scope = {world_id, truth_scope, subject_id}
```

Every head must match the registry and a verified component snapshot. Historical
bodies come from the commit-set journal's fixed before-round
`history.component_at(exact_head)` lookup, which returns a detached state or
refuses. Current-round staged heads use the journal's `advance_component` rule.
A caller-supplied hash/state pair is not ancestry evidence. The ancestry closure
contains actual branch-parent edges and replay-derived component predecessor
edges; the current proposal cannot insert its own invented history.

Branch uses the world/location owner's canonical `TypedValue` definition at
`data/schemas/m4_world_location_state_schema.json#/$defs/TypedValue`:

```text
{kind: "token", token: Identifier}
{kind: "boolean", value: boolean}
{kind: "integer", value: safe_integer}
{kind: "reference", ref: Identifier}
{kind: "references", refs: Identifier[0..32]}
```

Reference arrays are unique and lexical-order canonical. The registered owner
definition fixes kind, tokens/references and integer bounds. Branch adds no
alternative value variants. Exact current slot:
`{slot_id, definition_ref, value: TypedValue, source_event_ref}`. A qualified
genesis source may occupy `source_event_ref` without inventing a branch event.

Before/after comparisons use exact `{present:false}` or
`{present:true,value:TypedValue}`. Absence differs from false, zero and an empty
reference array. Domain deletion needs its explicit owner rule; it is not an
implicit set-union operation.

## Profile and qualified choice

The exact profile keys are `profile_id`, `component_id`, `partition_id`,
`law_bindings`, `action_adapter_id`, `choice_rules`, `projections`,
`bootstrap_ref`. `partition_id` is `branch_lineage`. Law bindings are immutable
`{dependency_id, ash_sha256, core_contract_sha256, realm_law_sha256}`.

Each closed choice rule has:

```text
{rule_id, action_kind, action_tokens, significance_values,
 effect_projection_refs, minimum_effects,
 required_cosmology_refs, required_asp_refs}
```

Actions/tokens are bounded neutral IDs. Significance is a configured nonempty
subset of `meaningful`, `major`, `threshold`, `cosmological`. Minimum effects is
1..16. Required cosmology/ASP reference arrays are nonempty. A rule associates
an action with actual semantic changes; its labels cannot supply those changes.

Each closed projection binding has:

```text
{projection_ref, component_id, partition_id, target_kind, target_id,
 definition_ref, mergeable}
```

`target_kind` is `fact`, `location_field`, `player_component` or `derived_view`.
The binding selects a fixed domain-owner projection and definition, never an
arbitrary JSON path or callable supplied by a proposal. Fact/location projections
may populate branch current slots. Player/view projections may prove a meaningful
choice but do not become objective branch/shared facts. Unknown mappings refuse.

A qualified decision has exact fields `decision_ref`, `location_ref`,
`player_context_ref`, `available_actions`, `chosen_action`,
`choice_significance`, `qualifier`, `source_action_ref`. Alternatives are a
unique array of at least two actions; chosen action must be a member.

The coordinator's registered deterministic adapter derives this exact action
witness from real read-before and staged-after owner states:

```text
{adapter_id, action_ref, action_sha256, player_component_id,
 player_before_head, source_branch_head, player_id, source_branch_id, target_branch_id,
 location_ref, action_kind, chosen_action, decision_ref, player_update_ref,
 consequence_ref, resulting_delta_refs, source_refs}
```

The action must be newly retained in staged player state, absent from the
read-before state. Its canonical source document hash, player, source branch,
location, decision and staged update must agree. The actual consequence contains
the action, and resulting update/delta references match. No `accepted` boolean
or self-declared source system grants this qualification. Replay recomputes it.

A meaningful effect is exact:

```text
{effect_ref, projection_ref, component_id, before_head, source_event_ref,
 before: Presence, after: Presence, source_occurrence_sha256}
```

The trusted coordinator adapter derives its before/after from actual owner
states and a newly accepted occurrence. Branch checks component, definition,
target, head, occurrence/action linkage and rule coverage. At least the configured
minimum number of distinct allowed projections must change. Branch pointers,
record aliases, provenance-only changes, revisions, counters and appended event
rows do not count as substantive effects. A changed observer view may qualify
only under an explicit rule and remains derived.

Qualified views are internal trusted composition outputs, not a public endpoint
accepting serialized assertions. The coordinator derives them from the actual
pure owners and verifies them again on replay. Branch never authenticates them
by accepting a source flag.

## Additive branch and event schemas

New `m4_leaf_branch_reality_state_schema.json` defines
`ywe.leaf_branch_reality_state.v2`, version `2.0.0`, with exact required keys:

```text
schema_id, schema_version, world_id, leaf_branch_id, owner_player_id,
truth_scope, profile_id, profile_sha256, law_bindings, base_world_ref,
lineage, branch_status, generation_context_ref, active_plane_pressure_ref,
current_slots, derived_view_refs, history, consumed, provenance
```

Truth scope is `leaf_branch_state`. Creation status is `active`; no other status
transition is admitted until its actual diagnostic rules are adopted.
`active_plane_pressure_ref` is a qualified reference or an explicitly qualified
null baseline, never a guessed pressure. Current slots use the shared type above.
Derived views retain explicit observer binding and cannot enter objective slots.

History is closed arrays `branch_event_refs`, `worldstate_delta_refs`,
`location_overlay_refs`, `manifest_refs`, `future_generation_bias_refs`,
`occurrences`. All previous records remain. Lineage has exactly:

```text
{kind, parents, common_base, bootstrap_ref, event_ref, shared_heads}
```

- Root: zero parents, common base/event null, qualified bootstrap ref, exact
  current shared constraint heads.
- Fork: one exact parent head, common base/bootstrap null, actual choice event.
- Merge: two distinct exact parent heads in canonical order, verified common
  base, bootstrap null, actual fresh merge event.

New `m4_branch_event_schema.json` defines `ywe.branch_event.v2`, version
`2.0.0`, with exact required keys:

```text
schema_id, schema_version, branch_event_id, event_kind, world_id,
owner_player_id, target_branch_id, agent_ref, base_world_ref, parent_heads,
common_base, decision_context, generation_context_ref, read_heads, changes,
resolution_refs, worldstate_delta_refs, future_generation_bias_refs,
cosmology_source_refs, asp_component_refs, provenance
```

Choice events have one parent, null common base and qualified decision context.
Merge events have two parents and verified base; automatic compatible merges
have null decision context. A conflict resolved by a player choice retains the
qualified decision. `merge` is new explicit reconciliation semantics, not an
inference that the legacy conscious-choice contract already defined it.

Generation context is a qualified closed record binding exact input heads and
neutral player/world/location/cosmology/ASP refs. Bootstrap context has no
invented branch event. Old opaque context strings alone cannot establish it.

Its exact keys are `context_id`, `kind`, `world_id`, `owner_player_id`,
`target_branch_id`, `event_ref`, `read_heads`, `player_context_refs`,
`location_context_refs`, `cosmology_source_refs`, `asp_component_refs`,
`diagnostic_refs`, `future_generation_bias_refs`, `provenance`. Kind is
`root`, `choice` or `merge`; root event_ref is null, other kinds name the actual
event. All heads are read-before inputs, never a future owner output hash.

Bootstrap qualification is exact `{bootstrap_ref,world_id,owner_player_id,
branch_id,world_heads,player_creation_ref,initial_location_ref,
initial_projection_refs,generation_context_ref,provenance}`. Player creation
must be actual initial state with no historical branch/action/consumed ledger;
initial projections must agree with the qualified domain-owner genesis.

## Operations and derived dependencies

Closed proposal: `{proposal_ref, world_id, owner_player_id, target_branch_id,
source_system, operation, generation_context_ref, expected_heads, provenance}`.

```text
bootstrap = {kind, bootstrap_ref}
fork      = {kind, parent_head, event_ref, changes}
advance   = {kind, previous_head, event_ref, changes}
merge     = {kind, base_head, parent_heads, event_ref, resolution_refs}
change    = {slot_id, definition_ref, before, after, source_occurrence_ref}
```

Root is explicit, event-free and unique per world/player. It requires a bootstrap
grant and actual qualified initial player/world/location values. It cannot
silently absorb continuing history. Fork requires a fresh target ID, exact
current same-player parent and actual meaningful choice/effect. Advance changes
an existing branch under an exact head while preserving original lineage.
Parentage/profile/law/owner are immutable. Target IDs cannot be reused after
committed creation.

`requirements` returns exactly `{reads,historical_reads,write_keys,creates}`. Reads are exact
component heads and required trusted historical closure selectors. A write key
is `{component_id,partition_id,target_kind,target_id}`; creation is
`{component_id,scope,partition_id,owner_policy_id}`. The policy derives closure
from selected records, typed changes and projection definitions. A caller cannot
omit a dependency to win a conflict. Ontology/law/profile are never write keys.

Events bind input heads, named effects and packet bytes, not their own future
head or a cyclic whole-owner post-state digest. Resulting heads are calculated
after pure outputs serialize. The coordinator stages required domain child
states, player/agent/history/ability/location/realm bindings and affected views
with the branch before publication.

In particular an effect compares actual staged record bytes/semantic values;
it cannot require the future whole player-state hash when that player state
contains a terminal whose hash binds the branch output. Named action/update/
effect identities establish linkage without this cycle.

Changing governing branch identity requires the world/location owner's explicit
child-inheritance factory. It must verify exact parent heads and selected merge
values, create newly qualified child-scoped current records, retain original
parent wrappers/provenance and revalidate current shared/realm constraints.
Relabeling a parent record's scope or reusing its accepted status is forbidden.
The exact factory belongs to the world/location contract, not branch policy.

## Same-player three-way merge

Parents must be distinct current variants of the same player/world/profile/law.
The exact base must be a replay-verified unique maximal common ancestor in the
branch/component predecessor DAG. Missing bodies, arbitrary older bases,
ambiguous criss-cross bases, cycles, stale parent/shared heads and
ancestor-descendant pseudo-merges refuse. Neither a hash nor a source label
proves lineage.

For every registered key in base/left/right, compare validated typed Presence:

1. If left equals right, select it.
2. Otherwise, if left equals base, select right.
3. Otherwise, if right equals base, select left.
4. Otherwise require exactly one qualified conflict resolution.

Resolution is closed `{slot_id,base,left,right,result,reason_refs,
source_occurrence_ref}`. All three previous values must match; result must pass
actual domain-owner rules. Missing, duplicate or extra resolutions refuse.
There is no averaging, last-write-wins, arbitrary dictionary merge or automatic
reference union. Whole merged domain state is revalidated against current
shared/realm constraints; disjoint edits may still be jointly invalid.

Occurrence is closed `{namespace,identity_parts,payload_sha256,record_ref,
origin_component_id,origin_request_ref,origin_event_ref}`. Namespaces are
branch_event/action/memory/update/effect/manifestation/delta/resolution.
Effect identity retains its full consequence/effect/player tuple. Same identity
deduplicates only with equal payload and original occurrence provenance; altered
payload/origin rejects. Distinct events remain distinct even for equal outcomes.

Merge preserves both parent ordering constraints as dependency edges and uses
stable topological ordering with canonical occurrence identity tie-break.
Contradictory ordering cycles refuse. Consumed identity retains the same fields
except `record_ref`; inherited imported reservations do not fabricate historical
receipts. Actions, requests, updates, effects and manifestations remain consumed
on the child. Append exactly one new merge occurrence. Parents remain immutable
and are not automatically relabeled `merged`. Capacity never evicts history.

## WRW adapter boundary

`core/branch_state.py` remains neutral.
`core/branch_state_wrw.py` owns the WRW projection of the actual
`ywe.player_action_trace.v1` / `0.1.0` action and player aggregates. It validates
full action schema and digest; exact player/source branch/location; new retained
action and update/consequence linkage; selected action in the new history entry;
and profile mapping from action_kind to choice token. A `branch_forming` label
alone does not prove a qualifying fork.

Fixed player semantic projections may inspect origin phase, identity state,
specified plane/bloodline/wolf values, ability state or Raven runtime status.
Subjects are explicit; complete source component schemas validate; metadata-only
changes are excluded. These projections can qualify choices without becoming
new neutral Core player fields or branch-owned player state.

Current WRW history permits one parent. Integrated merge MUST add an explicit
merge-aware history/admission version retaining both parent heads and all old
entries/consumed IDs. It cannot hide the second parent in `source_refs` or mutate
old schema versions. This adapter change and complete participant transfer are
required before claiming working merge, even if neutral branch reduction passes. [YWE-REQ-0059]

## Bounds and required execution evidence

Reference limits: 16 retained container components; 128 records/proposals per
policy; 16 changes/proposal; 128 current slots/history/consumed entries;
32 principals; 64 ancestry snapshots. Per-state/packet canonical limits remain
65,536 bytes, 4,096 nodes and depth 32. The first exceeded bound rejects before
publication. Parent/child/merge components all count; no hidden eviction.

Required tests include actual meaningful fork, event-free root, exact head and
foreign-scope refusal, identical/disjoint/conflicting typed merge, deletion and
absence distinctions, unique trusted base and ancestry cycle refusal, conflicting
occurrence identity and retained history order, inherited consumed identity
refusal, private-to-shared refusal, full late participant failure atomicity,
merge-aware player continuation, detached pure inputs, exact retry and preserved
old archive bytes. The companion JSON lists 20 concrete adverse vectors.

Contract adoption does not implement those tests or close any M4 roadmap criterion. [YWE-REQ-0059]

## Concrete implementation boundary clarification

The following closes transport details before their dependent implementation.
The exact schema map is `{branch,event,owner,context,world}`. The first four
are the four approved branch schema resources below; `world` is the complete
`m4_world_location_state_schema.json` resource supplying `TypedValue`.
Validation uses only this fixed offline registry, rejects retrieval, dynamic
references and missing active reference targets, and binds every supplied schema
digest. The external world resource is used through its selected TypedValue
definition, not as a license to resolve unrelated source dependencies.

Grants are a bounded principal map. Each exact grant is
`{source_system,operations}`. Source `world_bootstrap` permits only `bootstrap`,
`narrative_engine` permits `fork` and `advance`, and `runtime_cosmology` permits
`merge`. All principal and operation lists are unique and bounded. Proposal
source must equal the selected grant; serialized source alone grants nothing.

The catalog uses exact wrappers `{ref,kind,scope,document,sha256,provenance}`.
The digest binds literal canonical document bytes, preserving original source
scope. Kinds are `bootstrap`, `context`, `event`, `decision`, `reference`,
`definition`, `projection` and `resolution`. Their closed document shapes are
the corresponding branch definitions. Reference documents are exactly
`{category,subject_ref,source_sha256}`; they qualify immutable source identity,
not a mutable owner value. Definition documents use the world owner's exact
FactDefinition fields and its value kind/range/token restrictions. Projection
documents are exactly `{projection_ref,head,slot}` and must match the actual
selected owner fact slot. Active reference closure is iterative and bounded;
opaque CoreProvenance source strings do not recursively become executable data.

`BranchReadView(world_id,before,after,history,actions,effects,creations=None,retentions=None,staged_history=None)` is a trusted
composition helper, not a network input. Before and after are lists of exact
commit-set Component records (complete heads plus `state`), at most 16 each.
They are copied and each component scope, policy and canonical state digest is
validated. Before is the current pre-operation vector; after contains the
actual staged owner outputs. History is the exact `CommitSetReadView` supplied
by the journal. Its `component_at` supplies prior committed snapshots. The view
cannot authenticate arbitrary caller-created snapshots, as with other pure
owner inputs.

Actions and effects are the exact neutral witnesses above, computed by the
fixed integration bridge from actual before/after records. The WRW bridge
validates the actual player schema, action, consequence and semantic projection
before constructing them; coordinator replay must repeat that derivation.
The branch reducer rechecks exact selected heads, source document/occurrence
digests, context, projection definitions and linked typed changes. Missing
mutable owner evidence cannot be replaced by a `reference` record. No flag
such as accepted/eligible/trusted is an admission shortcut.

The complete policy identity binds component-specific profile configuration.
The persisted `profile_sha256` instead binds its semantic profile: exclude
`component_id`, `bootstrap_ref`, and projection `component_id` bindings. The
remaining rule, subject, definition, partition and law fields remain included.
This lets one semantic profile govern different branch components without
mistaking a new component ID for new law. Merge requires exact semantic digest
and law agreement; each physical component still retains its own policy pin.

An ancestry traversal follows verified branch lineage parent heads plus the
most recent retained branch event's previous/current parent head for advances.
It calls the journal lookup for every historical body, uses a 64-head bound,
detects cycles and rejects an absent or ambiguous maximal common base. It does
not accept a separately caller-authored graph. Initial branch records may be
verified current components; all earlier revisions must resolve through history.

The bootstrap context explicitly selects exactly one `reference` of category
`base_world_ref` and one of category `active_plane_pressure_ref` in its
`cosmology_source_refs`. Their scope is shared world state. A pressure reference
with `subject_ref: none` and source digest of canonical JSON null explicitly
qualifies a null baseline; other pressure references remain literal identifiers.
Derived view entries are exactly `{ref,observer_id,component_id}` and never
populate current slots. Player-component projection definitions are qualified
references of category `player_component` whose subject is the fixed target ID;
objective fact projections use complete world FactDefinition documents.

Packets are exactly `{format,policy_id,principal,request_id,proposal_ref,
proposal_sha256,record_sha256}` with format `ywe.branch_packet.v1` and a map of
selected wrapper digests. Selection includes the proposal context/event,
decision, resolutions, all profile projection definitions, bootstrap projections
when selected, and their typed reference closure. Requests are consumed under
`update` identity `[component_id,principal,request_id]`; branch-event identity is
`[world_id,owner_player_id,branch_event_id]`. Ordinary reductions may not reuse
any consumed occurrence identity. History merge deduplicates only complete
identical occurrences and retains parent ordering.

`BranchReadView` additionally exposes detached `before(component_id)`,
`after(component_id)`, `component_at(head)`, `actions()` and `effects()` accessors.
Each accessor refuses a missing identity. The WRW bridge exposes
`qualify_action(profile,decision,source_branch_head,player_before,player_after,
action_ref,action_schema)` and
`qualify_player_effect(binding,player_before,player_after,update_ref)`; both take
actual complete component records. The bridge recognizes fixed target IDs
`origin_phase`, `identity_state`, `raven_status`, `ability:<id>`,
`plane:<id>:score_q6`, `bloodline:<id>:score_q6`, and the three wolf q6 fields.
Absent ability is represented as absent Presence. Unsupported targets refuse.
These functions are deterministic qualifiers for trusted owner outputs, not
validators of untrusted serialized owner states.

Bootstrap has a separate optional creation witness list, never an overloaded
action. Each creation witness is exactly `{player_id,component_id,head,
creation_ref,source_sha256}`. The fixed WRW `qualify_creation(component,
creation_ref)` requires an actual initial player state with no accepted updates,
imported baseline, action/memory/history, or revealed identity; its source digest
binds the complete initial player state. Neutral admission matches that witness
to the exact current player head and the qualified creation reference. Trusted
coordinator composition must derive it again on replay; continuing players
cannot reset branch ancestry through bootstrap.

The WRW qualifier functions take keyword-only `owner_policy`, the exact
`PlayerStatePolicy` that produced the snapshots. They require the matching scope
and policy pin and revalidate detached snapshots with its public
`validated_state(state)` accessor, rejecting any validation mutation. This stays
a local WRW compatibility boundary, not a neutral Core dependency or a new
generic validation framework. Complete source schemas and origin rules stay
owned by that player policy. Creation qualification uses the same boundary.

QualifiedAction additionally binds exact `target_branch_id`, which must match
the event and actual player destination. The existing WRW bridge supports forks;
its single-parent transfer history cannot qualify in-place advance or merge.
Those participant paths remain explicitly deferred rather than fabricating rows.
Neutral advance remains available to a separately registered adapter with actual
same-branch action evidence.

`BranchReadView` has optional `retentions`, an array of exact
`{component_id,before_head,occurrences,consumed}` bundles, with detached
`retentions()` accessor. WRW `qualify_retention(before,after,*,owner_policy)`
derives every retained action, memory, accepted update/request, consequence
effect and manifestation identity from validated actual player output. Local
receipts retain their original request; imported reservations retain their import
anchor with no invented occurrence receipt. The reducer verifies exact component,
head, scope, source payload and full identity/origin consistency. A choice must
supply its player retention bundle and include the newly qualified action. Its
identity must be fresh before merging the retained ledger. Identical inherited
rows deduplicate; a changed payload or origin refuses. Request and update IDs use
separate full identity tuples, not an unqualified string.

The finalized requirements separate `{reads,historical_reads,write_keys,creates}`.
Current `reads` are the context vector plus bootstrap world/projection heads,
fork parent, advance previous, or merge parents. Identical duplicates collapse;
different heads for one current component refuse. `historical_reads` is the
explicit merge base only, or empty. `proposal.expected_heads` remains the exact
union, preserving its wire shape. Reduction matches current reads against
`view.before` and historical reads against `view.component_at`. The view permits
historical lookup only for component IDs present in its `before` vector; all
retained components remain registered. The coordinator must filter this vector
by the caller's read grants, so traversal cannot use global journal history to
bypass source authority. A historical revision is never chosen by numeric max.

`BranchStatePolicy.genesis(principal,proposal_ref,view)` is a root-only factory.
It performs the same source/grant/catalog/current-head/bootstrap/creation checks
and returns the complete event-free root with empty occurrence and consumed
ledgers. There is no request identity because genesis is not a committed journal
proposal. It shares the validation/bootstrap path rather than reducing and
stripping a receipt. Normal `reduce` of bootstrap still consumes its real request.
The coordinator reconstructs genesis during load and compares literal candidate
branch bytes; it never publishes an unpublished null reservation. This prevents
root branch bytes from binding a synthetic request whose packet transitively
hashes the same player genesis that binds the branch document.

The final optional `staged_history` input is a detached list of at most 32 exact
Component snapshots from already accepted transitive predecessors in the same
round. Each snapshot must come from the actual commit-set `advance_component`
helper; trusted coordinator composition supplies only those authorized by the
writer's read grants and accepted predecessor closure. The view checks scope,
complete state digest, unique exact head, per-owner size, and component membership
in the filtered `before` vector. It stores immutable canonical bytes and looks up
an exact staged head before consulting fixed before-round journal history.
Different revisions of one allowed component remain distinct. Neither arbitrary
unaccepted proposal output nor a globally visible component is admitted through
this parameter. As with current inputs, the pure view validates shape/binding;
coordinator construction and replay establish provenance of helper-produced data.

## Approved implementation paths

The approved concrete implementation set is:

- `core/branch_state.py`: neutral pure policy and fixed branch admission.
- `core/branch_state_wrw.py`: explicitly scoped WRW action/effect/history bridge.
- `tests/test_m4_branch_state.py`: behavioral branch and merge tests.
- `tests/m4_branch_fixture.py`: detached reusable neutral/WRW root, fork and merge
  configurations for later coordinator integration; no test-module imports.
- `data/schemas/m4_leaf_branch_reality_state_schema.json`: closed final branch.
- `data/schemas/m4_branch_event_schema.json`: closed choice/merge events and local
  qualified action/effect definitions.
- `data/schemas/m4_branch_owner_schema.json`: exact reservation/final envelope.
- `data/schemas/m4_branch_generation_context_schema.json`: closed root/choice/
  merge contexts and bootstrap qualification definitions.

The shared TypedValue remains owned by the world/location schema. New WRW
merge-aware player history/admission paths require their own explicit approved
file assignment before modifying player behavior; those changes are not hidden
inside the neutral branch module.
