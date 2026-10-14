# M4 bounded world and location owner contract

Requirement: **YWE-REQ-0060**. Decision: **ADR-0052**. Adopted reference contract, October 14, 2026. Admission MUST preserve the typed effect, authority, actual source-value and replay invariants specified below. [YWE-REQ-0060] The executable choices below are new bounded M4 decisions. Existing ownership and M3 behavior are cited separately at the end.

## Ownership and compatibility

The concrete `core/world_location_state.py` player-source adapter is WRW reference-profile compatibility under YWE-REQ-0015: it reads the existing WRW player spine and `m4_plane_attunement_state_schema.json`. Those source wire schemas include the WRW plane labels. They do not become mandatory Core ontology; the objective world/realm authority invariants remain neutral, and actual RealmEngine realm IDs remain distinct from player plane IDs. A later explicitly adopted neutral source adapter may replace this compatibility binding without changing the M3 producer. This first implementation does not claim universal player-schema support.

`WorldLocationPolicy` owns one exact shared-world or leaf-branch partition of objective current facts, location state and objective player occupancy. Narrative owns consequence meaning and qualified deltas; Realm owns location rules and realm admission. Both grants are necessary for a location, overlay or realm-shift mutation. Fact-only mutation requires the Narrative grant. Scope is `{world_id,truth_scope,subject_id}` using the existing `TruthScope`; shared subject equals world, leaf subject is the actual branch. Realm and location are explicit partitions inside this authority, never additional truth tiers.

One component keeps its governing scope unchanged. It cannot relabel a parent delta, action, event or qualified record into a child branch. Fork/merge child construction needs a separately adopted qualified inheritance factory that binds original parent heads and wrappers to explicit child seed/current values. Branch integration may compare and propose owner projections; only this owner may admit resulting domain values against current shared law and geography. There is no private-to-shared promotion path.

All existing schemas, standalone owner formats, M3 implementations and accepted archives remain unchanged. No callback reducer injection, host-authored world commits, executable prose, generic dictionary patch, floating-point calculation, inferred default state or hidden expiry is introduced. M3 access remains `NONE`; an M3 shift remains `PROPOSED_ONLY`. This owner admits a separate domain effect after validating those results.

## Pure API

```
WorldLocationPolicy(scope, profile, initial_state, grants,
                    records, updates, schemas, realm_binding)
.scope                 # detached exact TruthScope
.component_id          # immutable configured Identifier
.policy_id             # deterministic identity of complete semantic configuration
.initial_state()       # detached qualified complete initial state
.record(ref)           # detached exact selected immutable catalog wrapper
.definition(ref)       # detached exact configured FactDefinition
.update(update_ref)    # detached exact qualified update
.requirements(packet) # exact {reads:[ComponentHead,...]} from selected closure
.packet(principals, request_id, update_ref)
.reduce(state, packet, read_view)
.project_facts(state)
```

Construction validates all bounded input shapes, schemas, definitions, source qualification and seed invariants. It privately constructs the actual `RealmEngine` from `realm_binding`; callers cannot inject a producer. `reduce` copies and validates every input, computes a complete detached result and has no journal, host or storage side effect. A late failure leaves all inputs and domain consumption unchanged. State/head publication, authenticated capability selection, transport retries and final cross-owner consistency belong to the separately adopted coordinator/journal.

`grants` is an Identifier-keyed map of exact `{roles}` records; `roles` is a nonempty unique subset of `narrative`, `realm`. Packet principals are exact `{narrative_principal,realm_principal}`; the latter is explicitly null only for fact-only work. Names are checked against trusted construction grants. The coordinator must derive names from its actual capability boundary; serialized names, source-system strings, hashes and accepted flags are not authentication.

`requirements(packet)` validates the exact packet and derives sorted unique external heads from selected resolution and condition records. Conflicting heads for one component refuse. Read-dependent Realm operations must match the selected resolution player head. The supplied read view must equal this complete dependency set, and its vector hash must equal the update binding; omitted and excess reads both refuse. The coordinator adds this owner's expected current component head separately.

Policy identity binds the algorithm version, scope, complete profile, exact initial state, grants, exact schema-content hashes, actual M3 binding and selected immutable law/geography anchor wrappers. Appendable record/update catalogs are excluded to avoid cross-owner future-head hash cycles. Construction still qualifies the complete supplied catalogs; every packet binds the complete selected update and source closure. Changed selected bytes fail replay. Adding unused qualified records or updates preserves policy identity. Initial state must not contain future branch heads; the coordinator qualifies actual joint genesis.

## Canonical values and owner reads

Every object described here is closed; listed fields are required unless explicitly optional. Identifier uses the current journal ASCII pattern `[A-Za-z0-9][A-Za-z0-9._:/-]*`, length 1..128. SHA256 is 64 lowercase hexadecimal characters. Integers are exact, non-boolean and within +/-9007199254740991; revisions and rounds are nonnegative. Lists whose semantics are sets have unique members in lexical order; occurrence histories keep admitted order. All source documents retain their own exact schema version.

There is one reusable `TypedValue` definition at `m4_world_location_state_schema.json#/$defs/TypedValue`, shared by the branch schema:

```
{kind:'token', token:Identifier}
{kind:'boolean', value:boolean}
{kind:'integer', value:safe_integer}
{kind:'reference', ref:Identifier}
{kind:'references', refs:Identifier[0..32]}
```

A current slot is exactly `{slot_id,definition_ref,value,source_event_ref}`. A profile fixes the value kind and admissible range/references. The reference list is a canonical set. No value contains a raw object or arbitrary path.

`ComponentHead` is exactly the adopted journal shape `{component_id,scope,owner_policy_id,revision,head_digest,state_sha256}`. `ReadComponent` is those exact six fields plus `state`. `ReadView` is `{format:'ywe.owner_read_view.v1',world_id,components}`, at most 16 unique components sorted by component_id. Its vector digest hashes the corresponding ordered complete heads, excluding state. State bytes must match every head's digest and exact component/policy/scope. A hash match proves consistency only: read bodies must be supplied by the coordinator's current staged state or replay-verified history, never by a caller-supplied head/state pair. The owner cannot independently authenticate a serialized historical head.

Every declared dependency is read at the pre-operation view: committed state or outputs of explicitly accepted predecessor proposals. A mutation cannot use its own prospective output, a later proposal, or merely a retained historical value as current qualification. Conditions select an exact read head, and the coordinator verifies that it is the current eligible staged head for this proposal.

## Schema-qualified sources

`QualifiedRecord` is exactly `{ref,kind,scope,document,sha256,provenance}`. `sha256` hashes the bounded document bytes; `provenance` is the existing closed M3 `CoreProvenance`. Wrapper scope is original source authority and is never rewritten to make a selection fit. Each active identifier and collection also receives these reference bounds even where a legacy schema is looser.

`schemas` is a fixed exact map with keys `source,state,profile,update,phase11,m3,overlay,action,plane` and eight explicit existing M3 dependency keys: `generation_state,realm_transition,normalization,normalization_plan,module_capture,topology,planner,diagnostic_bundle`. Their files are respectively `m3_generation_state_schema.json`, `m3_generation_realm_transition_schema.json`, `m3_generation_state_normalization_schema.json`, `m3_generation_normalization_plan_schema.json`, `m3_generation_module_capture_schema.json`, `m3_generation_topology_axiom_schema.json`, `m3_planner_emitter_schema.json`, and `m3_reference_diagnostic_bundle_schema.json`. Each value is the supplied complete JSON Schema object with its exact expected `$id`; all content hashes enter policy identity. The offline registry contains only these seventeen resources. Fetch/retrieve fails closed. Resolve known `$ref` targets with bounded traversal; reject missing references, unsupported dynamic references, invalid schemas and unbounded reference expansion. This is schema qualification, not proof of source authorship.

The following kind-to-definition binding is exact:

| Kind | Executable document contract |
| --- | --- |
| `delta` | `worldstate_location_mutation_schema.json#/$defs/WorldstateDeltaPacket` (Phase 11 version 1.0.0) |
| `location_mutation` | the same file's `LocationMutationDelta` |
| `overlay` | `location_branch_overlay_schema.json`; all active fields additionally use the closed known schema-property allowlist |
| `action` | `player_action_trace_schema.json`, wire version 0.1.0 |
| `diagnostic` | `m3_core_domain_schema.json#/$defs/CoreDiagnostic` |
| `law`, `geography`, `source_evidence`, `resolution`, `condition` | respective closed definitions in new `m4_world_location_source_schema.json` below |
| `resolved_location` | closed `ResolvedLocation` in new state schema |

The earlier `worldstate_delta_packet_schema.json` has a different wire shape and is not silently substituted for Phase 11. Unsupported variants require a separate adapter. Unknown active members fail; documentary strings are retained, never interpreted as commands.

New source forms are exact:

```
LawAnchor {
  format:'ywe.world_law_anchor.v1', profile_id, core_binding_sha256,
  location_rule_refs, source_evidence_refs
}
GeographyAnchor {
  format:'ywe.world_geography_anchor.v1', world_id,
  locations:[{location_id,base_location_ref,realm_ids}],
  fixed_facts:[{fact_id,subject_ref,value:TypedValue}], source_evidence_refs
}
SourceEvidence {
  format:'ywe.world_source_evidence.v1', source_id,
  source_kind:'genesis'|'declared_condition'|'ash_evidence'|'generation_bias'|'residue',
  subject_ref, value:TypedValue, source_refs, provenance:CoreProvenance
}
ResolutionPayload {
  format:'ywe.world_resolution.v1', resolution_id, world_id,
  player_head:ComponentHead, branch_head:ComponentHead,
  action_refs, delta_ref, location_mutation_refs, condition_refs,
  provenance:CoreProvenance
}
```

Locations are 1..8, realm IDs per location 1..16, fixed facts 0..32; all source/ref lists above are unique and bounded 0..32 except source_evidence_refs, action_refs and resolution condition_refs, which are 1..16. Law `location_rule_refs` may be empty if the profile has no mutable locations and otherwise names exactly its complete rule table. Law binds the canonical actual M3 CoreBinding hash. Geography binds exact profile location/base/realm identities and immutable values. No update can replace either anchor or a fixed fact.

Trusted construction qualifies immutable `SourceEvidence` declarations and their provenance. A schema-valid assertion does not qualify itself. A declared condition may supply an expressly registered immutable source predicate; it cannot stand in for an available mutable player/world/location owner value or override higher law. Generation bias remains a qualified bias value, not proof of myth/prophecy truth. Every active diagnostic ref resolves the exact closed diagnostic document, with matching diagnostic_ref and compatible owner/rule/status. For successful consequence provenance, status must be COMPLETED and failure_code null; diagnostics with PENDING/REFUSED remain noncommitting evidence. Serialized diagnostic status is not live issuer authority.

Resolution source heads must match the selected current read view. Action records must have matching player, branch, target location/affected entities, nonempty source refs and the selected delta in resulting_worldstate_delta_refs. At least one meaningful or stronger action is required; minor_record alone cannot create an objective consequence. Any source_branch_event_ref is validated against the branch owner's selected event, preserving original source scope. New actions can be qualified immutable catalog selections before publication, but the final coordinator must bind their exact bytes to the matching accepted PlayerStatePolicy action/consequence result; a world effect cannot publish without that owner result. This cross-owner check is not replaced by the source catalog.

Catalog closure follows typed reference fields only. It is iterative and bounded by 128 distinct records; benign mutual identifier references such as delta/resolution are visited once and do not create recursive hashing. Document digests hash literal references, not recursive expanded payloads. Missing active references fail. Opaque original ASH source identifiers are preserved and bound through explicit qualified source_evidence records; they do not become executable objects merely by appearing in provenance.

## Conditions compare actual values

Condition refs select closed records with exactly one of these forms:

```
{kind:'current_fact', head:ComponentHead, slot_id, expected_value:TypedValue}
{kind:'location', head:ComponentHead, location_id, realm_id,
 field:'status'|'phase'|'stability'|'access_state', access_id:null|Identifier,
 expected_value:Identifier}
{kind:'player_plane', head:ComponentHead, player_id, plane_id, minimum_q6}
{kind:'accepted_effect', head:ComponentHead, effect_id, delta_ref, delta_sha256}
{kind:'declared_source', source_ref, source_sha256, subject_ref, expected_value:TypedValue}
```

`current_fact` resolves the actual current slot and requires exact typed equality. `location` resolves the actual current location record; access_id is non-null exactly for access_state, otherwise null, and exact current value must equal expected_value. `player_plane` resolves the actual selected plane document from the player spine and compares the exact integer score to minimum_q6 in [0,1000000]. `accepted_effect` requires the exact matching admitted effect/delta tuple in the selected owner state, not a catalog delta. `declared_source` resolves a source_evidence document with source_kind declared_condition, exact digest, subject and value. It cannot satisfy a profile condition declared as a current-value condition. No generic boolean accepted/satisfied property, arbitrary JSON pointer, expression evaluator, label presence or untyped source is admitted.

All operation and rule condition refs are evaluated, not merely found. A rule's set is a required subset of the operation's condition refs. Location required plane pressures, resonance prerequisites and prerequisite deltas from legacy descriptive rules must be compiled into these explicit current-value/source conditions. Unsupported predicates fail construction. Missing or false conditions reject the complete mutation; absence never implies a permissive default.

## Immutable profile and current state

Profile is exactly `{profile_id,component_id,law_ref,geography_ref,realm_plane_bindings,fact_definitions,location_definitions,mutable_rules}`. `realm_plane_bindings` consists of `{realm_id,plane_id}`: realm_id must exist in the supplied M3 binding; plane_id is a neutral qualified Identifier, and any used binding must be a real member of the selected player plane document. Core does not encode WRW P1..P9 labels or infer a plane from a realm's display name, coordinate or ASH signature.

Each FactDefinition is exactly `{definition_ref,slot_id,domain,subject_ref,realm_id,location_id,value_kind,allowed_values,minimum,maximum,mutable,mergeable,projection_fact_id}`. Realm/location are explicit null when independent. Domains are `npc_availability`, `faction_standing`, `local_world_condition`, `myth_seed_state`, `prophecy_weight_state`, `temporary_space_residue`, `recurring_symbol_recurrence`, `future_generation_bias`. Integer values have explicit inclusive integer min/max and empty allowed_values; boolean has null bounds and empty allowed_values; token/reference/references have null bounds and nonempty allowed_values (1..32). Empty reference-set values remain valid. There are at most 32 definitions, with unique definition/slot/projection IDs; mutable and mergeable are exact booleans. Player memory/identity/resonance/attunement and perception are excluded from this owner.

LocationDefinition is exactly `{location_id,base_location_ref,realm_ids,geography_sha256,allowed_current_states,access_definitions,thin_veil_slots}`. `allowed_current_states` is 1..32 exact `{status,phase,stability}` combinations. `access_definitions` is 0..16 exact `{access_id,access_kind}`, with explicit identifiers. `thin_veil_slots` is 0..16 exact `{target_realm_id,slot_id}`; selected slots must be objective token definitions with allowed TRUE/FALSE/UNAVAILABLE and match that location. Realm IDs are exact M3 profile IDs. No missing access/veil/phase fact is filled automatically.

LocationCurrent is exactly `{status,phase,stability,active_plane_pressures,access,eligible_systems,residue_refs,future_generation_bias_refs}`. Status uses the ten Phase 11 statuses; stability uses dormant/stable/unstable/contained/collapsing/mythicized/prophecy_charged. Phase is an explicit allowed profile Identifier. Plane pressures are 0..64 unique qualified plane identifiers; no numeric pressure is inferred. Access is 0..16 `{access_id,state,condition_refs}`, where state is open/closed/sealed/hidden/conditional/unstable/contained. Eligibility uses the existing nine location-content systems, each at most once. Residue and bias lists are 0..32 unique qualified source refs with the corresponding source_kind. Each complete current triple must occur in allowed_current_states.

LocationRule is exactly `{rule_id,location_id,source_current,target_current,condition_refs}`. Both current values are **complete exact LocationCurrent tables**. They contain no wildcards, optional predicates or partial changes. Construction validates both, immutable identity, conditions and a nonempty actual difference. There are at most 64 rules with unique IDs. Runtime requires exact equality with both selected before/after records plus actual evaluated conditions. Additional rules can enumerate additional legal transitions; no generic rule evaluator exists.

ResolvedLocation is `{location_id,base_location_ref,realm_id,current,source_delta_ref,source_mutation_ref}`. Genesis uses explicit qualified genesis source refs in both source fields; mutation outputs use the actual selected delta and mutation refs. LocationEntry is `{location_id,realm_id,current_record_ref,current_record_sha256,history_event_refs}`. Occupancy is `{player_id,branch_ref,location_id,realm_id,source_event_ref}`. Occupancy must be supplied and qualified in the initial state, including actual branch/player/location evidence; existing imported realm-form name/plane alone is insufficient to infer a realm.

PartitionState is exactly `{format:'ywe.world_location_partition.v1',scope,component_id,profile_id,law_sha256,geography_sha256,facts,locations,occupancies,records,events,consumed_effects}`. Facts are CurrentSlot values, with exactly the configured slots; locations are unique (location_id,realm_id), occupancies unique player IDs. `records` retains exact selected original wrappers. Consumed effects are `{effect_id,delta_ref,delta_sha256}`. Histories/events/consumption append; no deletion, relabeling or silent eviction. An initial state requires explicit source-qualified current values and genesis refs; no accepted update history is synthesized.

Each initial fact genesis source has the exact definition subject_ref and current TypedValue. A location genesis source has subject_ref=location_id and value={kind:token,token:SHA256({location_id,base_location_ref,realm_id,current})}; source references are excluded from this seed digest to avoid a cycle. Occupancy genesis has subject_ref=player_id and the token digest of {player_id,branch_ref,location_id,realm_id}. Genesis authority is the exact governing scope or shared-world authority; foreign leaf/player declarations fail. The initial state retains the complete typed closure of its selected seed and anchor records. These are trusted construction qualifications, not synthesized historical commit receipts.

`project_facts` produces deterministic owner-derived facts only from registered slots. Scope fixes OBJECTIVE_SHARED or OBJECTIVE_BRANCH; a caller cannot change authority/subject or request promotion. Typed values are preserved through the branch projection `{slot_id,definition_ref,value,source_event_ref}`. M3 perception's token-only TruthFact view must use an explicit profile-qualified token projection; integer/reference-set state must not be stringified into a new unqualified assertion. Full observer mapping is adopted with the coordinator.

## Update, admission and actual effects

Update is `{update_ref,scope,component_id,delta_ref,effect_id,resolutions,source_read_vector_sha256,retention,compensates_effect_id,provenance}`. Compensated effect is null or a retained exact effect ID. Packet is `{request_ref,principals,update_ref,update_sha256,selected_record_sha256,read_vector_sha256}`. Selected records are the full typed active closure; each supplied digest is recomputed. Resolutions number 1..8 and correspond exactly, in order, to every Phase 11 MutationOperation with the same operation_id, target, domain and source evidence. No operation is omitted or doubled. One update changes each fact/location/occupant target at most once.

Closed resolution variants are:

```
{kind:'fact',operation_id,slot_id,before:TypedValue,after:TypedValue,condition_refs}
{kind:'location',operation_id,location_id,realm_id,before_record_ref,
 after_record_ref,mutation_ref,rule_id,condition_refs}
{kind:'overlay',operation_id,location_id,realm_id,before_record_ref,
 after_record_ref,overlay_ref,rule_id,condition_refs}
{kind:'realm_shift',operation_id,player_id,
 before:{location_id,realm_id},after:{location_id,realm_id},
 player_component_id,player_state_sha256,plane_state_ref,veil_slot_id,
 request_ref,proposal_ref,condition_refs}
```

Condition refs are nonempty, unique, 1..16. An operation must produce an actual nonempty change. Fact before values must equal the actual current slot and after values fit its immutable definition. Location before ref/digest/current must match actual owner state. Both before and after keep immutable location/base/realm relation; changing occupancy to another realm uses realm_shift. The computed location difference must equal the selected complete LocationRule and the Phase 11 changed_fields classifications. ChangedField prose/reason is retained evidence; field_path is checked against a finite mapping of the eight LocationCurrent fields and registered access IDs, never executed as a path. Unknown paths, extra listed changes, omitted real changes and mutation target/source mismatches reject.

New executable legacy normalization is explicit: commit_public_fact selects a registered objective fact; it may select realm_shift only for a registered player occupancy target with local_world_condition domain. set_status permits only declared status/phase/stability/access axes. activate_site requires target status activated; suppress_site requires suppressed. adjust_pressure changes explicit plane-pressure membership or a registered bounded integer pressure fact with exact before/after values. record_residue appends qualified residue refs. append_ref appends a registered reference collection or admits a typed leaf overlay. commit_player_local_fact is refused and belongs to PlayerStatePolicy. Every specialization still requires its exact rule/conditions and source target/domain matching.

A leaf overlay must name the actual governing branch and source location. Its descriptive visibility/perception text never executes an objective write. Typed access/eligibility after-values are retained only under that leaf scope; neither locked=true nor validation metadata gives it authority over shared state. Shared-world and realm-local legacy persistence labels must map to a concrete governing scope: realm-local requires explicit realm_id plus shared or leaf owner; player-local is refused here.

The selected legacy overlay is version1.0.0. Its source_refs object must bind worldstate_delta_refs exactly to the selected delta, player_state_snapshot_ref to the selected source player component, and location_state_record_ref to the exact before record. branch_event_ref is present exactly when the delta has a non-null source branch event, with equal value. Its pressure/bias reference arrays resolve qualified sources, while descriptive change strings remain non-executable. A location mutation's mutation_kind must match its selected operation classification; realm_bleed_contained additionally requires an actual contained target status.

Retention is exactly one of `{kind:'persistent'}`, `{kind:'until_resolved',resolution_condition_refs}`, `{kind:'timeboxed',expires_at_round}`. The source retention/scope labels must agree. Until-resolved refs are 1..16 actual typed conditions; timeboxed round is explicit. Values remain until a new qualified update admits the removal/compensation and retains its cause. Wall clock or crossing a stored round alone performs no mutation. DiagnosticNoOp is not an objective Update and creates no consumed effect here; pending/refused M3 results remain noncommitting outcomes for coordinator decisions.

AcceptedEvent is exactly `{event_ref,request_ref,effect_id,update_ref,delta_ref,source_read_vector_sha256,changes,realm_checks,retention,compensates_effect_id,provenance}`. event_ref is deterministic from the canonical scope/component/update/effect identity tuple. Changes are `{target_kind,target_id,before,after}` with values typed by fact/location/occupancy kind; complete actual values are retained. Realm checks are `{operation_id,access_result,shift_result}` using canonical records of actual M3 calls. Effects and delta identities are single-use; a fresh request cannot apply a consumed domain effect. Compensation is a fresh qualified delta, exact current postcondition, original source scope, nonempty current reasons and owner-permitted inverse; it preserves original events and cannot undo immutable laws/history. Reversal is never implied merely by a reversible flag.

## Actual M3 realm admission and replay

1. Verify current occupant, player component/branch, spine/agent location, resolved source location and all pre-operation read heads. Source and destination locations must be registered manifestations of their explicit realm IDs. Their geography/law anchors and higher shared prohibitions must agree.
2. Resolve the actual player plane document selected by `spine.state_refs.plane_attunement_state_ref`; verify retained wrapper digest and player/branch/profile. Use immutable realm_plane_bindings to select the target plane member and exact score_q6. No supplied prospective score is trusted.
3. Resolve the actual objective thin-veil slot registered for the source location and target realm. Its source scope is shared or the actual admitted leaf; it cannot override a higher shared/immutable prohibition. Missing or UNAVAILABLE remains unavailable. A perception claim cannot supply objective eligibility.
   A leaf shift additionally requires a selected current_fact condition on the exact current shared-world WorldLocation component, for the same veil slot/definition and location/target binding, with actual TRUE. The selected shared state must have matching profile, law and geography anchors. FALSE, UNAVAILABLE or a missing shared basis refuses. The coordinator must obtain this body from its registered actual WorldLocationPolicy and compare its definition/location binding; a caller-supplied shared-looking dictionary or accepted flag is not registration evidence. The pure owner checks the exact qualified head, complete source state shape and bindings; the coordinator authenticates the source owner/read provenance.
4. Construct exactly one target `AttunementFact` from those actual values and source refs; construct `RealmAccessRequest` with exact request_ref, actual source/target realm IDs and current location_id. Use the actual configured `RealmEngine.evaluate_access` and immediately call its class-owned `validate_owned_result` on the original object. Require exact CoreResult/RealmAccessResult, matching binding, COMPLETED, eligible True, effect NONE.
5. Call actual `RealmEngine.propose_shift` on the actual access.value and exact proposal_ref. Validate original issuance before serialization; require exact RealmShiftProposal, COMPLETED, PROPOSED_ONLY and exact source/target/request/proposal identities. A copied/foreign/rebuilt result is not a substitute.
6. Only after all other domain checks may this owner admit its separate occupancy effect. The coordinator must require final player spine/agent/realm-form binding, branch and world occupancy to agree, and admit all participants atomically. No single owner method claims multiplayer synchronization by itself.
7. Replay reconstructs both actual producer calls from frozen config and verified historical/staged source bodies, checks live issuance again and compares canonical result records. Stored accepted/eligible/trusted flags are insufficient. A future source vector cannot qualify the earlier shift.

Profile realm ID, player plane ID and full ASH mathematical state identity remain distinct. No XOR transition, TC normalization, implicit fast travel or StateModel change is introduced. Mathematical transitions require their own explicit admitted producer adapter.

## Bounds, errors and acceptance

Each owner state/packet/source document uses the existing 65536-byte, 4096-node, depth-32 scalar contract. Catalogs are at most 128 records and 128 updates, each catalog at most 1 MiB. Owner state has at most 32 slots, eight location manifestations, eight occupants, 64 events/effects and 128 retained records. Rules max64, realm-plane bindings max64. Ref arrays not otherwise limited are max32. The complete byte/node limit can refuse before count ceilings. Read views contain at most 16 independently bounded owners and use the separately adopted journal aggregate limits; never reinterpret one-owner limits to fit a container. Capacity refuses without truncation/reservation/eviction.

Use existing stable JournalError codes: INVALID_POLICY for malformed configuration/schema/rule, INVALID_VALUE for malformed wire values, UNKNOWN_EVIDENCE for missing active source, UNAUTHORIZED_WRITER for missing owner grant, POLICY_REJECTED for semantic mismatch/stale source/forbidden mutation/realm denial, VALUE_LIMIT for canonical limits. No raw KeyError/TypeError/validator exception escapes a hostile public input boundary. Domain count-capacity failures use POLICY_REJECTED unless the adopted journal exposes a narrower stable capacity code; domain effects remain unchanged.

Required tests include actual successful fact/location changes; malformed closed source/schema/condition/grant; exact before/after mismatch; immutable geography/law/site identity; leaf/shared isolation; nonempty meaningful source action and one-to-one delta operation coverage; false/absent/stale typed condition; accepted-effect refs absent from actual ledger; scope/digest/source version mismatch; actual threshold equality/below threshold/false/missing veil; wrong source location despite otherwise eligible M3 facts; actual M3 issuer proof and replay; shift self-qualification refused and explicit accepted predecessor permitted; distinct realm/plane/ASH fixture identities; count/byte/late-failure input isolation; consumed effect replay and qualified compensation; retention requiring explicit later admission; immutable branch projections and refusal of silent child-scope relabeling. Schema tests use a fixed offline registry with a retrieve function that fails. Existing M3 and all twenty original/imported owner golden archives must remain byte-identical.

## Approved implementation surface

- `core/world_location_state.py`
- `data/schemas/m4_world_location_source_schema.json`
- `data/schemas/m4_world_location_profile_schema.json`
- `data/schemas/m4_world_location_state_schema.json`
- `data/schemas/m4_world_location_update_schema.json`
- `data/examples/m4_world_location_example.json`
- `tests/m4_world_location_fixture.py` (reusable actual-player/M3 fixture for later coordinator integration)
- `tests/test_m4_world_location_state.py`
- `tests/test_m4_world_location_schemas.py`
- `docs/architecture/m4_world_location_owner_contract.md`

Governance/catalog/example/schema registrations and roadmap entries are root-owned. New schemas carry YWE-REQ-0060 markers. No existing schema or producer edits are required. Any additional module or changed source format needs explicit contract reconciliation before implementation.

## Observed basis and evidence

`worldstate_location_mutation_v1.md` and its rules assign Narrative consequence meaning, Realm location validation, diagnostics and new-delta reversal. `worldstate_location_mutation_schema.json` carries operation labels and changed-field descriptions without executable before/after values. `realm_truth_boundary_contract.md`, `truth_authority_lattice.md` and location overlay/resolver contracts preserve immutable geography/law and shared-vs-leaf truth. `core/realm_engine/realm.py::evaluate_access/propose_shift` implements exact M3 threshold/veil checks and NONE/PROPOSED_ONLY effects but does not resolve location_ref against a world owner. `core/core_values.py` and `m3_core_domain_schema.json` provide actual closed producer values/provenance/diagnostics. `core/state_journal.py::TruthScope` uses truth_scope; the separately adopted commit-set journal supplies the exact complete head shape. `m4_plane_attunement_state_schema.json` supplies actual selected integer scores. These source observations motivate, but do not already implement, the new contract.

Source pin and per-file SHA256 evidence are in the companion external `ywe-m4-world-location-owner-design-20261014.json`. This Markdown supersedes the first draft's alternative predicate rules, incomplete heads, P1..P9 Core assumption and presence-only condition ambiguity. No implementation or new world-owner test result is claimed by this design document.

### Concrete wire clarification

The public `realm(realm_id)` accessor returns a detached closed
`{definition,plane_id}` pair. `definition` is the exact configured actual M3
ProfileRealmDefinition wire record and `plane_id` is the corresponding explicit
profile mapping. It validates the identifier and refuses an absent definition or
mapping with `UNKNOWN_EVIDENCE`. Trusted coordinator composition uses this
accessor to qualify realm forms against actual owner configuration without
reading private catalogs or inferring identity from display names. This additive
inspection method changes no owner identity, packet, state or archive bytes.
[YWE-REQ-0060]

Schema metadata is separately bounded: the fixed bundle is at most 1 MiB canonical JSON, each resource at most 32,768 nodes, depth64 and exact integer metadata at most256bits. This admits existing M3 UINT64 schema bounds; runtime safe53/65536-byte/4096-node/depth32 limits are unchanged. Floats, nonfinite numbers, unsupported containers, cyclic Python objects and unresolvable/dynamic references fail. No raw schema parser is exposed.

The selected source read vector contains external predecessors. Own current state is bound by exact before values and the journal expected component head, avoiding a self-reference through a future policy ID. The reference compensation variant admits exact inverse fact transitions only; location/occupancy has no generic inverse. ChangedField paths are the eight literal LocationCurrent field names; access is replaced as one typed collection. project_facts returns exactly {scope,component_id,facts}, where facts are sorted CurrentSlot records; observer-specific M3 token mapping remains coordinator-owned.
