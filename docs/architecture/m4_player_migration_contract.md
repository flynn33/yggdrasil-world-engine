# M4 complete player migration and imported continuity

Adopted reference realization: YWE-REQ-0057 / ADR-0049. This contract extends
the player aggregate with explicit imports of the two existing player formats.
It does not replace the legacy schemas, initial v2 constructor, or existing
origin/player archive identities. Source interpretation follows the player
runtime, memory/action, branch integration and exact resonance contracts.

## Source boundaries and target versions

The adapters are explicitly selected: `closed_reference_v1` accepts only
`schema_id=ywe.player_runtime_state.v1` and `schema_version=0.1.0`;
`historical_record_v1` accepts only `record_type=PlayerRuntimeState` and
`version=1.0.0` under the historical generation-packet definition. A source
containing both discriminator families is ambiguous and fails. Unknown active
fields, including nested historical extensions, fail before activation.
Structural validation never authenticates source authority or completeness.

New files define `ywe.player_runtime_state.v3` / `3.0.0`,
`ywe.player_aggregate.v2` and `ywe.origin_progression.v2`. The v3 spine retains
the current reference groups and adds a closed active `runtime_context`.
Existing v2 spine, aggregate-v1 and origin-v1 schemas remain unchanged. Imported
history starts a new journal at revision zero; the source logical sequence is
separate. An import must not invent past commits, requests, receipts or phases.

`PlayerStateMigration(adapter_id, source_schemas, target_schemas, resolution)`
is a pure trusted configuration boundary. `migrate(raw_source_bytes)` returns
a source-bound result; `verify(raw_source_bytes, result)` recomputes it exactly.
`PlayerStateStore.from_migration(result, migration, raw_source_bytes,
*configuration)` independently verifies that result before using the imported
dialect. `load_migrated` reconstructs the identical imported genesis and replays
the journal. The original constructor and `load` retain their existing boundary.

The resolution binds exact source bytes, world/player, original veiled creation,
current phase, component records, action/memory history and complete consumed
identities. Missing knowledge is not an empty ledger. Qualified inputs are
trusted composition data; serialized approval flags grant no capability.
Complete selected records and qualification wrappers, schemas and profiles are
bound by digest. Unused catalog extension must not invalidate replay.

The closed resolution contains `format=ywe.player_migration_resolution.v1`,
`source_sha256`, `world_id`, `player_id`, `player_profile`, `origin_profile`,
`spine`, `creation`, `current_phase`, `action_refs`, `memory_refs`,
`consumed_action_refs`, `records`, `consumed_updates`, `consumed_request_refs`,
`consumed_manifestation_event_ids`, `manifestation_bindings`, `realm_name_map`, `fragment_bindings` and
`provenance`. The spine is the complete explicitly qualified v3 candidate; its
projection must agree with every supported source field. Consumed-update rows
contain exactly `update_ref` and `consequence_ref`. Realm mapping contains
`profile_id` and `mappings`; fragment rows contain `fragment_ref` and
`fragment_id`. Manifestation rows contain `manifestation_event_id` and
`record_ref`, with exactly one explicit binding per consumed event identity.
An unused alias cannot choose a different historical qualification wrapper.
Original component numeric migration may be separately verified
before supplying the complete records; this boundary does not guess aliases.

The result contains `format=ywe.player_state_migration.v1`, `adapter_id`,
`migration_id`, world/player, source format/version/digest, source/target schema
digests, `qualification_sha256`, `selected_record_sha256`, `import_anchor`,
`source_presence_map`, `field_mapping_rows`, `decimal_conversion_rows`,
`origin_baseline`, `baseline` and `target_sha256`. The baseline is the complete
new aggregate with empty local accepted/compensation receipts. Its
`import_baseline` contains source digest, import anchor, `consumed_update_refs`,
`consumed_request_refs`, `consumed_effects`, `consumed_manifestation_event_ids`
and provenance. Each consumed-effect row has update/consequence refs and the
three-element consequence/effect/player tuple. The import anchor hashes the
source and qualified inputs before output construction; target digest hashes
the complete baseline, avoiding a circular receipt hash.

## Imported origin baseline

`OriginProgressionPolicy.from_baseline(baseline, *original_configuration)`
keeps the same pure policy API. The closed baseline contains exactly:

```text
format = ywe.origin_baseline.v1
world_id, player_id, profile_id, source_sha256, import_anchor
current_phase, actions, memories, consumed_action_refs, provenance
```

The eight original configuration arguments still supply the original veiled
creation, explicit phase profile, grants, future evidence and action/memory
schemas. Baseline scope/profile must match. Source digest and import anchor are
lowercase SHA-256 values. Provenance has the existing CoreProvenance shape.
Actions and memories retain their exact values and order, validate against the
same exact wire versions, and have unique identities. Every memory resolves to
a retained action with matching branch when declared. Consumed action IDs are
explicit, unique and a subset of retained action IDs. Their completeness is a
trusted input obligation; it cannot be inferred from phase or action count.

The imported component has format `ywe.origin_progression.v2`, original creation,
current phase, retained actions/memories, an initially empty `advances` list and
`import_baseline` containing source digest, import anchor, consumed action refs
and provenance. Empty advances do not claim that no historical progression
occurred. New advancement checks both imported consumption and new advances.
Old actions may support a fresh memory without becoming new progression credit.
The new `origin.v2` policy identity binds the old policy identity and complete
baseline. The original constructor's policy/genesis/archive bytes are unchanged.

## Lossless active state

Closed v1 fields, optional absence, arrays and declarations are copied exactly
except recorded version/protocol and resolved component-reference conversions.
Continuing state requires a qualified current origin baseline; it is never reset
to the initial phase. Added origin, ability and Raven bindings are explicit.
Existing pending/accepted/rejected update references and resilience history stay
available. Typed references must resolve under their actual world/player/branch.

Historical state maps current phase to the origin owner and each supplied
resonance scalar to a complete qualified component. Sparse omissions never imply
zero. Exact q6 conversion must agree with every supplied plane, bloodline and
white/dark wolf score. Wolf channels remain independent. The supported historical
bloodline shape is explicitly a score map keyed by bloodline identity; structured
or unknown signal shapes fail. The realm-name mapping is explicit configuration
bound to the chosen profile, never inferred from presentation labels.

The active runtime context preserves historical state identity, logical sequence,
phase confidence, identity reveal policy, origin/celestial-memory labels, active
realm form, wolf interpretation, branch-generation/event references, awakening
fragments, narrative memory, relationships, faction stances, unresolved tensions,
active quests, completed resolutions, perception, last action, generation context,
the full ASH provenance and authority/update constraints. Worldstate deltas and
future bias map to the existing world-link collections. Unknown fields cannot be
hidden in inert archived source bytes as a substitute for usable state.

This adapter explicitly supports `reveal_through_play`, mortal origin and the
non-moral wolf interpretation. A celestial-memory label must be a canonical
identity-state name and equal the qualified current celestial state; this is a
new conservative adapter rule, not a claim about the open legacy schema's enum.
Other labels require a future explicit adapter. Awakening fragment associations
are explicit qualified bindings, not guessed string equivalence.

Phase confidence is an exact finite decimal coefficient/exponent, not q6 and
not assigned an invented zero-to-one bound. Parse decimal source tokens directly;
ambient Decimal precision must not affect conversion. Absence, explicit null and
ordered collections remain distinguishable. Source lexical bytes are separately
retained by the caller and bound by digest; mathematical equality does not claim
lexical equality.
Player decimal tokens are bounded to 128 characters and an exponent within
minus/plus 10,000. Canonical confidence coefficients have at most 128 characters,
the same exponent bound, no trailing zero, and exponent zero for zero. This
player parser leaves the published resonance-only migration parser unchanged.

## Continuation and consumed identities

Imported update IDs, effect tuples, request IDs and manifestation IDs stay in
separate explicit ledgers. New admission checks them as well as local receipts.
A historical request without its original receipt is reserved, not relabeled an
exact transport retry. Compensation targets only verified local reversible
receipts; imported accepted IDs do not manufacture an inverse. Current presence
is independently qualified; resonance never implies manifestation.
Retained action event and world-result links resolve to their qualified objective
records, including when no imported consequence receipt names that action.
Historical branch links keep their own branch; they are not rewritten to the
current branch. Imported consequence results equal the declared result union of
their retained actions and cannot use observer records as objective evidence.

A closed typed continuity operation in the new dialect updates named supported
fields through their owning source and qualified evidence, alongside normal
origin/consequence admission. No generic JSON patch is executable. Narrative
owns identity context, memory and tension; Quest owns active quest/resolution
updates; Runtime Cosmology owns branch-generation context; Perception owns only
the observer reference; Realm owns supported active form. Append-first history
retains order. Removing active quests or tensions requires explicit reasoned
resolution. A phase change with existing confidence requires an explicitly
qualified replacement confidence. Sequence increments once per committed update
when present; a present last-action field follows the actual final action.

The operation is exactly `{kind: context, context_ref, condition_refs}`. Its
qualified catalog record has kind `context` and document fields `field`,
`previous_value`, `value` and `phase`. The phase must equal post-origin phase,
the field must already be present, and the previous value must match exactly.
Supported fields are phase confidence, celestial memory, active realm form,
perception state, and the reference collections listed above. Nonempty condition
refs must be qualified current update evidence. An update may write each field
once. Initial admission and subsequent changes resolve each historical reference
under its exact field category. An awakening reference's source digest binds the
corresponding current celestial fragment. Active realm form resolves a qualified
same-branch shared/leaf reference of category `active_realm_form`. The authority,
identity, source provenance and fixed policy declarations are not generic-editable.

Removing active quest or unresolved tension references additionally requires a
closed `resolution` member on that context record: `removed_refs`, `action_refs`,
`reason_refs`, and `disposition` (`resolved` or `cancelled`). Removed refs match
the actual ordered removal exactly. Named current-bundle actions must cover the
removed entities in `affected_entity_refs`; reasons are nonempty qualified update
evidence included in operation conditions. Quest removal specifically requires
Quest ownership and `quest_resolution` actions. The context record and action
memory retain this explicit resolution; no completed-history entry is fabricated.
The member is forbidden on other fields and when no reference was removed.

All validations and complete state bounds precede publication. Imported baselines
and future reductions use the same 65,536-byte, 4,096-node, depth-32 and bounded
record/journal limits. Strict source parsing rejects duplicate keys, nonfinite
numbers, invalid Unicode and oversized input. An external migration receipt may
be bounded separately to 1 MiB; it is not inserted wholesale into journal state.

## Verification and completion boundary

Capture actual original archive bytes before implementation. Verify old empty,
populated, compensated and branch-transfer archives unchanged. Exercise both
adapters with initial and continuing sources, nonempty active legacy fields,
exact numeric conversions and absence/null/order preservation. Continue an
import with new meaningful evidence and typed context changes, then replay it.
Refuse missing history/qualification, changed source/schema/selected records,
unknown extensions, cross-scope references, old consumed actions/effects and
late invalid changes without publishing partial state.

Reference implementation paths are `core/player_state_migration.py`, existing
player/domain/origin modules, and exact new tests
`tests/test_m4_player_migration.py`, `tests/m4_player_migration_fixture.py`,
`tests/test_m4_player_import.py`, `tests/test_m4_origin_baseline.py` and
`tests/test_m4_player_migration_schemas.py`. No new dependency or platform runtime
is introduced. This adoption is not implementation evidence and closes no M4
deliverable, exit criterion or placeholder.
