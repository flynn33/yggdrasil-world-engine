# M3 StateModel assessment contract

Status: active first-slice contract, adopted after verified M2 acceptance on October 4, 2026. Owner and partition: `ywe_core`. Requirement: `[YWE-REQ-0039]`. Decision: `ADR-0029`.

This contract and its requirement/decision are adopted before dependent reference implementation. Adoption does not establish runtime conformance or M3 acceptance. The exact reviewed source proposal has normalized SHA256 `851c16a83e1fa7495d71f374dc2347e2ac97797f19fc84791fb65e3ce35908ff`.

A conforming first-slice StateModel reference implementation MUST satisfy the owned construction, diagnosis, contextual-classification, bounded-decoding and diagnostic-retention contracts defined below. It MUST preserve the pinned canonical mathematics and explicit Core/profile boundary, and MUST NOT claim the deferred normalization, recovery, full Diagnostics or milestone completion obligations. [YWE-REQ-0039]

The selected local representation and finite-boundary decisions below are adopted YWE rules; they are not alleged new upstream ASH axioms. The independent expected tables are validation evidence designs until the actual reference implementation executes them.

## Purpose and completion boundary

The first slice establishes construction-valid immutable ASH values, neutral profile-based admissibility, complete state assessment, exact source-derived contextual classification and allowed recovery-category mapping. It repairs representation coercion and incomplete classification in the current reference façade. It does not execute recovery/fallback, enter containment/halt, generate topology, materialize artifacts or claim any M3 exit criterion complete.

Production remains native/strictly object-oriented/platform-neutral under Raven Forge v0.7.0 at 87409bc36fb9d4782eab02189adb184f2b3962a7. Python implementation, if chosen for this slice, is an explicitly labelled repository reference oracle/testing tool. Cohesive behavior belongs to StateModel; immutable values own construction invariants; explicit collaborators own profile binding and diagnostic capture. No global mutable caches, service location, direct peer implementation access, host filesystem writes, clocks, randomness or source-repository dependency.

## Source owners and preservation

All canonical references below are under core/ash_pattern_engine/canonical, remain pinned and are not edited:

- core/ash-state-space.pseudo.md: Vector[9] over F2, 512 vertices, all coordinates participate; make_state preconditions.
- core/codeword-set.pseudo.md: exact closed 16-member set, fixed canonical constant rather than caller-selected runtime parameter; full-coordinate XOR.
- core/realm-identity.pseudo.md: injective full-state vertex identity; realm identity and realm_id are lossless aliases.
- core/state-admissibility.pseudo.md: recognized-valid states, then reachability from known-valid states through the canonical code, otherwise incompatible or unclassified when evaluation cannot proceed.
- core/state-validity-diagnostics.pseudo.md: full diagnostic fields and status projection, including malformed/unavailable completeness.
- core/system-state-classification.pseudo.md: exact ordered branches below.
- core/recoverability-semantics.pseudo.md: seven-class category table, distinct subsequent recovery execution/escalation.
- interfaces/contracts/state-model-contract.md: StateModel owns representation, diagnosis, classification and semantic normalization; the latter remains an explicit subsequent slice.
- interfaces/diagnostic-schema.md and rule-id-taxonomy.md: canonical envelope/enums/chain requirements and source rule identifiers.
- interfaces/contracts/diagnostics-module-contract.md: single Diagnostics authority, mandatory meta-diagnostics for detected nonconformance; full module conformance is deferred as stated below.

Preserve dependency ash_cosmological_model.f2_9.canonical and aggregate 0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb. Exact per-file pins accompany state-space-expected-cases.json and classifier-cases.json.

WRW source: data/ash_state/realm_bit_mapping.yaml explicitly labels its nine one-hot anchors canonical_wrw_projection, profile_id wrw_reference_profile. It says they neither exhaust ASH states nor define whole realms. Core requires an explicit ValidityProfile; WRW is a supplied profile, not a hidden universal default. The legacy façade explicitly chooses an immutable binding derived from the actual pinned nine anchors for compatibility. The public mutable YWE_REALM_STATE_ANCHORS dict remains a compatibility view only: mutating it cannot alter the legacy diagnostic/profile authority, a StateModel profile or canonical mathematics. Construct the private immutable binding from reviewed source-owned values, not from that mutable view at call time; the repository reference assembly uses values independently verified against the actual source before contract adoption, with mandatory source/profile checks before publication. Its constructor verifies equality to those immutable reviewed pins; it performs no source loading or file IO and does not certify arbitrary caller-declared profile authority. An operational assembly requires an explicitly owned source-verification factory outside neutral Core; that native/runtime assembly remains subsequent work. [YWE-REQ-0039] Caller mutation of collections used to construct a profile cannot change its accepted states.

Do not replace existing accepted M2 descriptor definitions. data/schemas/ash_generation_packet_schema.json has no StateValidityDiagnostic; its DiagnosticEnvelope uses numeric severity and six required fields. common/diagnostic.schema.json is another distinct M2 format (lowercase severities and three required fields). The new StateAssessment packet needs its own identifier/schema; preserve both existing formats and their historical fixtures. Any adapter must identify source and target formats and be lossless for fields it claims to carry; no invented numeric-to-canonical severity mapping.

## Object and interface contracts

### AshState

Immutable value with exactly nine canonical Bit coordinates. Bit is the value 0 or 1, not a lossy integer conversion of another number. Constructor establishes width and coordinate membership before the object becomes observable. Caller-owned collections are copied to owned immutable storage. Equality is coordinate equality, independent of profile/realm names. Signature is the nine ASCII digits in coordinate order b0..b8.

Native/reference constructor accepts already typed Bit values. The Python reference constructor accepts exact built-in int values 0/1, not bool, float, int subclasses or objects with conversion hooks. A representation codec is separate. Invalid width/coordinate/type raises a typed construction failure; no partially valid AshState is published. It never silently truncates 0.9, overflows on infinity, derives a privileged coordinate or creates a default zero vector. A well-formed state may be operationally inadmissible; representation validity is not profile admission.

### StateInputCodec and compatibility façade

Selected representation choices:

- Canonical value record: state_space is F2^9; bits is a nine-element numeric array whose values are exactly 0 or 1. Preserve existing M2 mathematical-integer acceptance of numeric 0.0/1.0 at the JSON decoder boundary; canonical internal Bit becomes 0/1 only after exact finite equality validation. This is a codec acceptance rule, not a broadened AshState constructor. Boolean, quoted per-coordinate strings, fractions, NaN and infinities are not F2 numeric coordinates.
- Signature input: exactly nine ASCII 0/1 digits. The legacy string façade may retain its existing surrounding-whitespace strip before this exact check. Do not accept arbitrary Unicode numeric digits as portable canonical signatures.
- An exact construction-valid AshState is also accepted directly as a typed candidate; the codec observes its immutable bits as BIT_SEQUENCE without invoking conversion hooks. [YWE-REQ-0039] Existing list/tuple bit callers remain supported through the explicit codec. Do not accept unbounded iterables/generators or arbitrary user conversion hooks; nine coordinates is a bounded field, not a stream.
- Open M2 record metadata is not reinterpreted as state semantics. The codec selects its owned state_space/bits; preserve the original bounded input capture separately instead of imposing new closure on old descriptors.

Raw JSON token decoding and already parsed values are separate boundaries. The reference raw JSON decoder uses precision-preserving decimal-token parsing (parse_float=Decimal and exact integer parsing), rejects duplicate object keys and JSON NaN/Infinity, and compares each finite numeric value to exact 0/1 before conversion. Token 1.00000000000000000001 must fail as a coordinate; token 1.000 and numeric -0.0 denote mathematical bits and may canonicalize only after that comparison. A pre-parsed exact built-in float 1.0 is accepted as the observed value 1.0; its original JSON token is unknown and cannot be certified retroactively. Neither default binary-float parsing nor float-to-int conversion may precede raw-token validation. Decimal values produced by the bounded raw decoder are allowed inside that decoder; arbitrary Decimal subclasses or numeric objects supplied by callers are not new codec inputs. Keep existing M2 schemas unchanged. This precision-preserving bit decoder is a reviewed local representation decision, not adoption of every policy in an earlier Ash_Value_Contract draft.

normalize_bits retains its legacy representation-normalization role with exact validation. It must not become semantic correction behind the backs of encode_state_identity/orbit/XOR, which must still handle every well-formed vertex. Semantic normalization of a compatible state to a recognized valid state belongs to the subsequent StateModel normalization slice.

### ValidityProfile

Immutable complete ValidityProfile contains profile_id, source/revision reference, recognized_valid_states (set of construction-valid AshState values), and optional separately owned realm-label metadata. StateModel requires a tagged immutable ProfileBinding: either AVAILABLE with that complete ValidityProfile, or UNAVAILABLE with separately typed UnavailableValidityProfileEvidence. The unavailable value retains expected profile/source/revision identity, owning evidence reference and a bounded stable reason for authoritative evaluation data being unavailable; it has no recognized-state set and is not an empty profile. Both variants are well-formed construction-checked bindings, distinct from malformed profile/configuration input. No profile changes the canonical codeword set, dimensions, XOR or vertex identity.

recognized_valid_states is explicit. A supplied empty set is not automatically a missing dependency: it recognizes no state, and every well-formed state is incompatible with that empty known-valid set. An admissible UNAVAILABLE ProfileBinding is a distinct condition yielding complete UNCLASSIFIED diagnostics with the well-formed input retained and orbit_info NONE when known-valid-state membership cannot be computed completely. Malformed or missing ProfileBinding objects instead fail construction; they cannot fabricate an availability reason. No guessed default anchors, nearest-state heuristic or inferred realm-based fallback.

First reviewed test profiles: existing wrw_reference_profile; neutral test-only ywe.validation.neutral-origin.v1 recognizing only 000000000; explicit empty-known-set test profile. The latter two are validation fixtures, not production cosmology defaults or alternate ASH mathematics.

### SystemContext

Immutable exact booleans is_in_safe_halt and is_in_containment. Both may be true; halt wins. No truthiness coercion from integer/string values. This value is an observed context snapshot, not an operation that changes lifecycle state. Classifying with halt=true is not proof of operational terminal enforcement; that proof belongs to the recovery/operation owner.

### ClassificationEvidence

Separate immutable adapter evidence for the source's abstract predicates correction_path_is_known and fallback_is_available. They are not canonical SystemContext fields. Each predicate entry has subject/profile/source-assessment binding and owner evidence reference, and is tagged EVALUATED(exact boolean) or NOT_EVALUATED(bounded reason). The evidence object is mandatory for contextual assessment. A source branch that consults a predicate requires its EVALUATED value; a NOT_EVALUATED consulted entry is an explicit evidence-unavailable contract failure, never an implicit false predicate. An unconsulted predicate may remain NOT_EVALUATED, so malformed/unavailable-profile/halt assessment does not manufacture facts irrelevant to its branch. No heuristic assumes a correction merely from compatibility or a fallback merely from some registry being present.

In the reference cases these are declared fixture facts, not claims that a recovery route was executed. A later Correction/Fallback owner must supply its evaluated facts and witnesses when its predicate is consulted in production classification. Only the predicate relevant to the selected source branch is consulted; neither is consulted for halt, containment, stable or unclassified branches. Missing/malformed evidence or an unavailable consulted predicate is a typed caller-contract failure, never silently false or true. Evidence for another subject, profile or assessment/source revision is rejected. The reference testing adapter may supply explicit fixture facts, clearly scoped as such; production must obtain evaluated facts from the later owning correction/fallback collaborators. A diagnosis-only call does not construct ClassificationEvidence and does not classify. If a consulted predicate is NOT_EVALUATED after detection was acknowledged, return typed ClassificationEvidenceFailure containing the complete StateDiagnosis, immutable confirmed emitted snapshot, missing-predicate name, stable failure code and input/subject/profile/source-assessment bindings. The detection record remains observable. There is no invented classification record, contextual class or recovery category. Structural evidence construction failure occurs before candidate diagnosis and therefore has an empty emitted snapshot; an unavailable consulted predicate occurs after diagnosis and retains the acknowledged detection snapshot.

### StateValidityDiagnostic

The source has NINE required semantic fields, all populated:

1. input_state
2. admissibility_status
3. transformation_compatibility
4. normalization_status
5. recoverability_relevance
6. is_valid
7. orbit_info
8. rule_ids
9. notes

Well-formed input_state is the full nine-bit semantic vector. Original representation is retained by the assessment's input capture; a signature is not used as a replacement vector. orbit_info is an explicit optional value: orbit_id (minimum signature under the fixed C relation, preserving current convention), member_count=16 and contains_known_valid_state. If it cannot be computed completely, use NONE, never fake a default orbit. No state identity is collapsed to orbit identity.

The coherent producer table is exact:

| admissibility_status | transformation_compatibility | normalization_status | recoverability_relevance | is_valid |
| --- | --- | --- | --- | --- |
| VALID | COMPATIBLE | ALREADY_VALID | NO_RECOVERY_NEEDED | true |
| TRANSFORMATION_COMPATIBLE | COMPATIBLE | NORMALIZABLE | RECOVERY_APPLICABLE | false |
| TRANSFORMATION_INCOMPATIBLE | INCOMPATIBLE | NOT_NORMALIZABLE | NOT_RECOVERABLE | false |
| UNCLASSIFIED | UNKNOWN | BLOCKED | CONTAINMENT_NEEDED | false |

Do not relabel incompatible relevance FALLBACK_NEEDED: it is NOT_RECOVERABLE in this source producer table. That means not recoverable by codeword normalization; contextual fallback classification remains separate. Immutable diagnostic construction rejects incoherent rows. Future recovery-attempt failure records must not mutate the original assessment to invent a different producer row.

### Malformed-input representation reconciliation

Observed source tension: input_state is declared Vector[9], but the same source explicitly requires StateValidityDiagnostic completeness for malformed candidates and says the raw candidate is retained. A malformed value cannot truthfully inhabit AshState. YWE uses the following explicitly reviewed transport variant without editing the pinned source:

- WellFormedCandidate has the canonical nine-bit input_state and StateValidityDiagnostic semantics.
- RejectedCandidateEvidence identifies the original input reference, representation kind, stable failure code and bounded raw observations. It is explicitly tagged rejected, has no AshState and no vertex identity. Nonfinite observations use typed tokens rather than invalid JSON NaN/Infinity.
- The assessment diagnostic's input_state branch carries that rejected evidence rather than any fabricated vector. Other eight required fields remain populated using the exact UNCLASSIFIED row; orbit_info is NONE and notes explain the rejected representation.

This is a project-owned wire/value representation extension to reconcile the source's malformed completeness requirement; do not advertise the rejected branch as a Vector[9] or already approved canonical source type. A later schema must make the alternatives discriminated so a rejected candidate cannot enter transformation/identity APIs. Caller-supplied input references preserve traceability for unsupported or oversized raw objects; do not call arbitrary repr/conversion methods or store memory addresses in deterministic diagnostics.

### Canonical envelope and immediate diagnostic capture

Keep the canonical TEN fields: diagnostic_kind, severity, stage, disposition, subject_reference, parent_diagnostic_reference, chain_root_reference, rule_ids, summary, notes. Enums are the pinned uppercase names. First slice uses STATE_VALIDITY kind and DETECTION/CLASSIFICATION stages. Do not create a new kind for implementation convenience.

A caller-owned DiagnosticContext supplies stable distinct detection/classification references and original input reference. For a well-formed state, subject_reference is the preserved vertex ID; malformed input uses its original input reference. Root parent=NONE and root reference is its actual detection reference; classification parent/root point to detection. No literal SELF placeholder needs an unresolved global lookup.

A cohesive per-assessment diagnostic capture owner records detection immediately after diagnosis and classification immediately after classification. It has a bounded atomic append/acknowledgement contract; the assessment retains each acknowledged immutable record immediately. Result exposes that per-call emitted snapshot. DiagnosticCaptureFailure carries the complete immutable attempted canonical record, the already acknowledged emitted snapshot, failed stage, stable failure code and subject/profile/source bindings. It publishes no successful StateAssessment and never erases an acknowledged detection record when classification capture fails. If a collaborator throws without acknowledging an append, capture_status is NOT_CONFIRMED: the record may have been stored externally, and the assessment may claim only the earlier confirmed snapshot. It must neither assert emission nor assert absence for that unconfirmed attempt. Caller retry does not imply safe replay, recovery or lifecycle transition.

This capture collaborator is an assessment-scoped port, not a claim that the complete Diagnostics module is implemented. interfaces/contracts/diagnostics-module-contract.md requires the owning Diagnostics module to produce meta-diagnostics for detected missing fields, invalid taxonomy or broken chains. That full cross-module conformance, missing-step detection, meta-diagnostic production and later recovery-to-terminal chain handling remain an explicit M3 Diagnostics obligation. Register this source-backed obligation with the subsequent Diagnostics slice; the first slice proves its own complete records and retained typed failure evidence only. It must not relabel a local exception as a canonical meta-diagnostic or claim full Diagnostics acceptance. If the capture collaborator detects record/schema/chain nonconformance, it rejects the append with a stable typed nonconformance cause retained in DiagnosticCaptureFailure; no invalid record is acknowledged. Its error result is not completion evidence for the deferred meta-diagnostic obligation. Classification reads context without entering recovery/containment/halt or mutating preserved history.

Selected envelope impact mapping, a downstream choice consistent with pinned meanings: STABLE INFO/RESOLVED; UNSTABLE WARNING/PENDING; CORRECTABLE and DEGRADED ERROR/PENDING; FAILED ERROR/BLOCKED; CONTAINED CRITICAL/PENDING; already SAFE_HALT CRITICAL/TERMINAL. Malformed detection is ERROR/BLOCKED before contextual classification. Do not emit a TERMINAL-stage record under a CLASSIFICATION parent: source requires TERMINAL parent ESCALATION or RECOVERY. Already-halted assessment describes existing context, not a new halt transition. No timestamps/random/environment values enter the deterministic assessment payload.

Rule IDs come from actually evaluated source rules, in evaluation order: ASH-STATE-STRUCTURE-001, ASH-ADMISSIBILITY-CLASSIFICATION-001, ASH-STATE-VALIDITY-001, ASH-CLASSIFICATION-MAPPING-001 and ASH-RECOVERY-ACTION-001 as applicable. A permitted source catch-all ASH-STATE-GENERAL-001 is available for a condition without a more specific state rule. No new ASH family/ID format is invented. Each notes list is nonempty and summary is one line.

### StateModel behavior and public surface

Cohesive StateModel receives an explicit ProfileBinding and the verified immutable canonical binding. An AVAILABLE binding supplies ValidityProfile; an admissible UNAVAILABLE binding supplies unavailable evaluation evidence and produces complete source diagnostics. C is fixed by source identity; there is no caller-selectable alternate codeword parameter. It owns diagnose(candidate, diagnostic_context) -> StateDiagnosis and assess(candidate, context, classification_evidence, diagnostic_context) -> StateAssessment. StateDiagnosis contains decoded state or NONE, the complete validity diagnostic, source/profile/input binding, and the acknowledged detection record; it has no contextual class/category. assess reuses the same internal diagnosis producer once in its per-call trace, then evaluates class/category and appends classification. It does not emit duplicate detection records. The legacy diagnosis-only facade delegates to diagnose and adapts the typed result to its documented flat return record. Decode/diagnose never perform correction, choose fallback, alter context or produce artifacts.

StateAssessment contains parsed_state or NONE, complete diagnostic, exact system class/recovery category, source/profile identity, bounded input evidence and immutable emitted diagnostic snapshots. The name parsed_state explicitly avoids falsely saying that every decoded F2 state is operationally valid.

The exact assessment order: capture/decode; diagnose source admissibility and complete fields; emit detection; apply classifier precedence; map allowed recovery category; emit classification; publish immutable result. Representation failure still proceeds through UNCLASSIFIED assessment; malformed context/profile/evidence construction is a typed caller/configuration error. No implicit platform side effects.

## Finite boundary policy and failure precedence

The following are reviewed YWE reference-producer limits, not new ASH axioms or restrictions on the existing accepted M2 formats:

- A ValidityProfile has at most 512 distinct construction-valid states. That ceiling follows from the complete nine-bit source space; duplicate entries are rejected rather than silently changing the supplied binding. A supplied empty set is valid. Profile/codeword/source binding is immutable and checked at construction, with no mutable global used as authority.
- Profile IDs, source/evidence references and caller diagnostic/input references use the existing common identifier contract: 1..256 ASCII characters matching ^[A-Za-z0-9][A-Za-z0-9._:/-]*$. Detection and classification references are distinct and cannot be reserved NONE or SELF. Optional realm-label metadata is independently owned and does not enter admission or identity.
- Each assessment emits at most two records, in detection then classification order. There is no process-global retained history. This producer uses at most five unique evaluated rule IDs per record, summary at most 512 characters, and at most eight notes of at most 512 characters each, all from bounded templates. The canonical source envelope itself is not redefined as this producer's universal limit.
- Raw JSON/signature decoding has a 4,096-byte UTF-8 input budget, tested before parsing or surrounding-whitespace normalization; a numeric token is at most 128 ASCII bytes. Raw JSON maximum container nesting is 32, checked by a bounded lexical pre-scan that respects quoted strings/escapes before recursive decoding. Raw JSON entry accepts exact built-in bytes and decodes strict UTF-8. For a direct exact built-in str signature, reject character count over 4,096 before UTF-8 allocation, then apply the byte budget; unpaired surrogate encoding failure has a stable rejection code. Reject oversized input/tokens/depth with explicit limit failures rather than parsing them and losing the bound. UTF-8 decoding, JSON syntax, duplicate keys, recursion failures and Decimal/integer token-construction exceptions are mapped to stable rejected-input codes (never exception messages or leaked RecursionError/decimal errors). Explicit depth enforcement does not excuse catching parser failures. Preview transport uses escaped JSON string encoding so a decoded JSON surrogate cannot break evidence serialization. This defines the reference codec boundary, without changing M2 fixture parsing or schemas.
- Direct sequence input accepts exact built-in list/tuple only. Inspect its length before copying or visiting values, inspect at most nine coordinates, and never traverse arbitrary iterables, generators or conversion hooks. Direct signature input accepts exact built-in str only. Direct record input uses exact built-in dict with at most 64 keys. Check the bounded key set contains exact built-in strings before looking up state_space/bits, so custom key equality/hash hooks cannot enter owned lookups. Inspect only the owned field values, never recursively capture unrelated metadata. Raw JSON record input is bounded by the byte budget and the same 64-key record ceiling; unsupported shapes have typed rejection rather than recursive capture. A direct record's metadata remains open and untraversed, so this boundary does not impose closed-object semantics on M2 records.
- RejectedCandidateEvidence is bounded to one representation-kind tag, exact sequence/string length where available, at most nine coordinate observations and a 64-character string/token preview. Every incomplete preview carries truncated=true and original_input_reference. Allowed observed scalars are copied without arbitrary repr: exact small 0/1 integers; other integers record sign/bit_length; finite floats use their exact bounded built-in hexadecimal form; NaN/+infinity/-infinity use fixed tags; strings use a bounded prefix; unsupported objects use the fixed UNSUPPORTED_VALUE tag. No user class name, conversion method, memory address, recursive metadata or arbitrary exception message enters canonical evidence. A rejected record asserts only these observations, not a full capture or digest of the original object.

Typed structural configuration/reference/profile/context/evidence validation precedes candidate evaluation; whether an EVALUATED predicate is required is checked when the diagnosed source branch consults it. Raw byte/token limits precede decoding; exact representation validation precedes profile recognition. A representation failure becomes the complete UNCLASSIFIED rejected-candidate diagnostic and does not escape as integer OverflowError or silently change a bit. Authoritative evaluation unavailable after valid construction remains a distinct UNCLASSIFIED diagnostic with the existing valid input vector retained. Diagnosis then detection acknowledgement precede source classifier evaluation; halt precedes containment and later predicates. Detection capture failure stops before classification. Classification capture failure returns DiagnosticCaptureFailure with acknowledged detection preserved. A missing or mismatched contextual evidence object is a caller-contract error, not UNCLASSIFIED candidate evidence, and no assessment success is produced. These failures do not themselves enter safe halt or execute recovery.

For the legacy diagnosis-only facade, deterministic diagnostic/input references are locally derived from the bounded semantic state or the fixed bounded rejected-observation payload; any digest is of that declared payload only. They must not be labelled a complete raw-input digest when capture is truncated or unsupported. The new API instead requires caller-provided original_input_reference and DiagnosticContext. A legacy caller requiring durable original-object traceability must use the new API; the facade cannot truthfully recover unprovided provenance.

## Exact classifier precedence and category table

Do not sort classes by severity to implement the classifier; execute these source branches in order:

1. context.is_in_safe_halt -> SAFE_HALT.
2. Else context.is_in_containment -> CONTAINED.
3. Else VALID and ALREADY_VALID -> STABLE.
4. Else TRANSFORMATION_COMPATIBLE and NORMALIZABLE -> CORRECTABLE if correction_path_is_known, else UNSTABLE.
5. Else TRANSFORMATION_INCOMPATIBLE -> DEGRADED if fallback_is_available, else FAILED.
6. Else -> DEGRADED, including UNCLASSIFIED/BLOCKED.

| Class | Recovery category |
| --- | --- |
| STABLE | NO_ACTION |
| UNSTABLE | NORMALIZE_STATE |
| CORRECTABLE | APPLY_CORRECTION |
| DEGRADED | FALLBACK_REQUIRED |
| CONTAINED | CONTAINMENT_REQUIRED |
| FAILED | ESCALATION_REQUIRED |
| SAFE_HALT | TERMINAL_NO_RECOVERY |

UNCLASSIFIED's CONTAINMENT_NEEDED relevance does not bypass the ordered classifier to become CONTAINED/SAFE_HALT. Missing fallback escalation is later recovery behavior. Successful recovery may restore STABLE; monotonic escalation refers to diagnostic severity/chain, not prohibiting restored health. The first slice does not yet prove no transition after halt.

## Errors and compatibility

Construction errors are typed and local: state width/coordinate/type, context boolean, inconsistent diagnostic, invalid profile state, missing/wrong subject evidence or invalid diagnostic references. No exceptions caused by integer truncation/overflow cross the candidate diagnosis boundary. Codec failure returns rejected evidence; it is not swallowed as success. Configuration binding failures are explicit, never substituted with WRW or an alternate C.

Preserve current vertex format ash_state_<nine-bit-signature>, signature, orbit convention and realm_id==vertex_id for all 512 well-formed states. encode_realm_identity remains the lossless alias. xor_bits/transform_state remain pure full-F2 mathematics regardless of operational profile admissibility. Operational RealmEncoder admission and terminal-guard APIs are separate subsequent behavior; do not retrofit them into pure identities/XOR.

The legacy no-context diagnose_state(state) becomes an explicitly diagnosis-only WRW façade. Its flattened returned record retains the existing canonical-envelope field names and admissibility_status, adds the other eight required validity fields, and omits system_state_class and recovery_category. Notes and summary describe representation/admissibility only; they must not assert that correction, fallback, containment or halt is known, available or executed. The retained envelope is the existing Python canonical-envelope-shaped transport, not the different numeric-severity M2 DiagnosticEnvelope. Its severity/disposition are chosen from diagnosis status alone: valid INFO/RESOLVED; compatible WARNING/PENDING; incompatible ERROR/BLOCKED; malformed/unavailable ERROR/BLOCKED. These producer impact choices are explicitly local, rather than deductions from absent SystemContext. The root reference is a deterministic valid diagnostic reference rather than the old unresolved SELF literal. Stable malformed input trace/reference construction follows the bounded evidence policy below; it cannot serialize arbitrary caller objects.

This removal of contextual fields is an intentional compatibility change to the Python reference façade and every embedded snapshot/planner diagnostic, documented before implementation. build_cosmic_pattern_snapshot's direct call at ash_canonical.py:212 must be adapted explicitly to diagnosis-only scope; plan_generation's diagnostic_ref/axiom_diagnostic then carry that same scope. Observed searches found no executable repository reader of the two removed fields beyond the producer, while __init__.py publicly exports diagnose_state; external consumers are unknown. Meaningful caller tests must assert field removal and complete validity/envelope data in the direct record, snapshot, and planner. They must not declare generation operationally safe from a diagnosis-only packet. Preserve snapshot identity/alias/transformation fields and existing generation behavior for this slice; its lack of runtime admission is recorded in the later M3 gap, not repaired through fabricated classification facts.

New contextual assessment requires explicit profile binding, context and bound predicate evidence; evaluated values are mandatory for consulted predicates. It corrects the old four-class mapping by executing source precedence; diagnosis-only consumers obtain no contextual class. The smaller diagnosis-only migration is selected over introducing a correction-proof owner and fallback collaborator in this first slice. It does not claim that no correction/fallback exists, nor silently choose a false predicate.


## Independent expected cases and verification plan

classifier-cases.json has 64 explicit source-derived coherent diagnostic-row x 16-context/predicate combinations. Expected counts: SAFE_HALT32, CONTAINED16, STABLE4, CORRECTABLE2, UNSTABLE2, DEGRADED6, FAILED2; recovery counts follow the exact table. Generated without importing production ash_canonical. INDEPENDENT_CASE_REVIEW.md explains its matrix and limits.

state-space-expected-cases.json has 1,536 explicit profiles/states: all 512 vertices under WRW, a neutral-origin test profile and an explicit empty-known-set test profile. Canonical codewords were parsed from pinned source enumeration; expected orbits used independent integer XOR. Counts: WRW9/135/368 valid/compatible/incompatible; neutral1/15/496; empty0/0/512. Every expected identity keeps canonical and compatibility aliases equal; every orbit has16 members and partition count32. The neutral/empty profiles are test-only proposals, not production defaults.

Implementation tests must execute constructors/codecs and actual StateModel against those independent cases; all64 cases need exact class/category and consulted-predicate traces. Invalid bit count, boolean/string coordinate, fractional value, NaN, both infinities, Unicode numeric signature, unsupported input kind/generator and legacy whitespace each need exact failure/result witnesses. Constructor tests must prove caller-owned list mutation does not alter an existing AshState and reject already parsed float even when the separate codec accepts it. Mutating caller arrays after construction must not mutate state/diagnostics. Inconsistent semantic diagnostic rows and integer-as-context-bool must fail construction. Exact root/parent references, field/enumeration presence, order, one-line/nonempty explanations, schema-format separation, source pin and input/profile/evidence mismatch need adversarial checks. Failure injection must prove no successful result after lost diagnostic capture, preservation of the entire attempted record and every previously acknowledged record, and NOT_CONFIRMED status for an unacknowledged possible append. Raw JSON regression 1.00000000000000000001 must reject before conversion; parsed exact float 1.0 is tested separately without claiming its lexeme. Test each finite limit at its exact boundary, unsupported custom conversion objects/generators, empty profile, conflicting source/profile/assessment evidence and the diagnosis-only direct/snapshot/planner compatibility change.

Keep existing four identity/alias tests and package algebra safeguards green. Do not claim all28 invariants, five categories, canonical byte serialization, operational normalization/recovery or M3 acceptance from this slice. Expected-case integrity checks validate the expected artifacts only. The actual StateModel must separately execute the implementation verification suite.

## Adopted binding and capture refinements

### Exact canonical binding

[YWE-REQ-0039] CanonicalAshBinding MUST validate every constructor field by exact
typed equality against the independently verified fixed source values recorded in
data/governance/ash_dependency_identity.json and interface_inventory.json:
dependency_id, aggregate_sha256, state_space_sha256, codeword_source_sha256,
validity_source_sha256, classification_source_sha256, recovery_source_sha256,
diagnostic_source_sha256 and taxonomy_source_sha256. Correctly shaped caller
strings MUST NOT count as verified source authority. A change to any one value
MUST reject CANONICAL_BINDING_INVALID before assessment. The closed sixteen-word
code remains an immutable source-owned constant; it is not caller-selectable.
The independent source-pin check and all-nine-field substitution tests are the
acceptance evidence for this constructor boundary, separate from runtime recovery.

## Acknowledged diagnostic capture

[YWE-REQ-0039] CaptureReceipt MUST declare CONFIRMED, REJECTED or NOT_CONFIRMED
and name the exact attempted diagnostic reference. StateModel MUST append to its
call-owned acknowledged prefix only after receiving a structurally valid matching
CONFIRMED receipt. A valid matching REJECTED receipt MUST explicitly guarantee the
attempted record was not appended; only that branch may return REJECTED/
DIAGNOSTIC_CAPTURE_REJECTED. Missing/malformed receipts, wrong references and
generic throws MUST return NOT_CONFIRMED/DIAGNOSTIC_CAPTURE_UNCONFIRMED, preserving
the full attempted emission and all previously acknowledged records. A possible
external append MUST NOT be inferred absent or acknowledged from the throw.
Per-call capture remains bounded to detection and classification; these records
and failures do not complete Diagnostics meta-diagnostic or lifecycle conformance.

## Distinct local packet transport

[YWE-REQ-0039] The reviewed YWE packet uses schema_ref
`data/schemas/m3_state_assessment_schema.json`, artifact_type
`ywe_state_assessment`, artifact_version `1.0.0`, and the diagnosis/assessment/failure
outcome discriminators in interface_inventory.json. Complete nine-field
StateValidityDiagnostic and ten-field DiagnosticEnvelope records MUST remain
separate nested objects with explicit source/profile/assessment bindings outside
their source fields. Source NONE is JSON null in this new transport; existing M2
formats and the documented flattened legacy adapter remain separately identified.
No failure packet asserts completed classification or a recovery category.

## Adopted Python reference interface and wire inventory

The following local constructor, code and packet choices are adopted for this reference slice.

### Ownership and import direction

- `state_values.py` owns construction-valid immutable values, enums, bound facts,
  full semantic diagnostics, envelopes, emissions and result/failure values.
  Frozen dataclasses with owned tuples/frozensets are suitable reference forms;
  exact built-in scalar validation occurs before equality or conversion. No
  filesystem/source loader, classification, mutable authority or capture callback.
- `state_model.py` owns StateInputCodec, StateModel diagnosis/assessment, fixed
  source-bound algebra helpers, and assessment-scoped diagnostic capture.
- `ash_canonical.py` imports/re-exports AshState from state_values. Its legacy
  normalization/diagnosis helpers use function-local state_model imports. Neither
  state_values nor state_model imports ash_canonical. StateModel obtains its fixed
  immutable codeword/source binding and WRW profile through explicit reviewed
  bindings; it must not read the mutable public YWE_REALM_STATE_ANCHORS view.
- Preserve existing public helper names, all 512 vertex IDs and lossless aliases;
  retain existing M2 descriptors. This new schema is `m3_state_assessment_schema.json`,
  proposed ID `https://ywe.local/schemas/m3_state_assessment_schema.json`.

## Exact value constructor inventory

All constructor collections are copied/validated into owned immutable storage;
no bool/int-subclass/str-subclass conversion, arbitrary iterator or repr hook.
`to_record()` returns fresh JSON-compatible containers, never a mutable internal
view. Caller mutation of emitted records cannot alter an outcome or later call.

| Value | Exact constructor fields | Owned invariants / record |
|---|---|---|
| AshState | `bits: tuple[int, ...]` (may copy an exact built-in list at construction) | exactly 9 exact built-in ints 0/1; signature b0..b8. Record `{state_space:"F2^9",bits:[...]}`. Float acceptance belongs only to codec. |
| CanonicalAshBinding | `dependency_id, aggregate_sha256, state_space_sha256, codeword_source_sha256, validity_source_sha256, classification_source_sha256, recovery_source_sha256, diagnostic_source_sha256, taxonomy_source_sha256` | validates all nine fields by exact typed equality against the fixed independently verified expected pins, not just string/hash shape. Any one-field substitution rejects CANONICAL_BINDING_INVALID. Fixed 16 codewords are private immutable source constants, not a constructor-selectable C. Source verifier/factory establishes the real binding; schema-shaped caller strings are not proof of verification. |
| ProfileSourceBinding | `source_reference, source_sha256, evidence_reference` | nonempty bounded identifiers; normalized SHA256 exact 64 lowercasehex. |
| ValidityProfile | `profile_id, source_binding:ProfileSourceBinding, recognized_valid_states` | at most 512 distinct AshState values; copied frozenset, duplicates reject. Serialize sorted recognized signatures. Empty set is AVAILABLE, not missing data. |
| UnavailableValidityProfileEvidence | `profile_id, source_binding:ProfileSourceBinding, reason_code, reason` | declared expected authority plus actual unavailable-data evidence, no recognized set. Fixed reason_code `PROFILE_DATA_UNAVAILABLE`, bounded reason of at most 512 characters; not a malformed profile object. |
| AvailableProfileBinding | `profile:ValidityProfile` | wire `{availability:"AVAILABLE",profile_id,source_binding,recognized_valid_signatures:[...]}`. |
| UnavailableProfileBinding | `evidence:UnavailableValidityProfileEvidence` | wire `{availability:"UNAVAILABLE",profile_id,source_binding,reason_code,reason}`. |
| SystemContext | `is_in_safe_halt:bool, is_in_containment:bool` | exact built-in booleans. No lifecycle operation. |
| AssessmentBinding | `assessment_reference, original_input_reference, diagnosis_reference` | stable valid identifiers supplied by caller; diagnosis_reference equals DiagnosticContext.detection_reference. |
| DiagnosticContext | `assessment_reference, original_input_reference, detection_reference, classification_reference` | valid1..256 identifier strings; detection/classification distinct; neither reserved NONE/SELF. |
| PredicateBinding | `assessment_reference, diagnosis_reference, subject_reference, profile_id, profile_source_sha256, ash_dependency_id, ash_aggregate_sha256, evidence_reference` | exact match to the current diagnosis/source/profile. A valid state subject is ash_state_signature; rejected input subject is original_input_reference. |
| EvaluatedPredicate | `binding:PredicateBinding, value:bool` | wire `{evaluation:"EVALUATED",binding:{...},value:true/false}`. value is exact bool. |
| NotEvaluatedPredicate | `binding:PredicateBinding, reason` | wire `{evaluation:"NOT_EVALUATED",binding:{...},reason:...}` with at most 512 characters; value key absent; never coerced to false. |
| ClassificationEvidence | `correction_path_is_known, fallback_is_available` | both entries are explicit EvaluatedPredicate or NotEvaluatedPredicate. Only source-consulted entry must be EVALUATED; irrelevant entries may stay NOT_EVALUATED. |
| InputEvidence | `original_input_reference, representation_kind, observed_length, length_unit, preview, preview_encoding, truncated, coordinate_observations, failure_code` | finite bounded observations below. failure_code null when representation accepted. |
| CoordinateObservation | `index, scalar_kind, value, sign, bit_length, total_length, truncated` | tagged field alternatives below; source values observed without custom conversion. Unused fields omitted on wire. |
| DecodedInput | `state:AshState or None, input_evidence:InputEvidence` | internal codec result; state=None requires a rejection failure_code; not an assessment packet. |
| RejectedCandidateEvidence | `input_evidence:InputEvidence` | wire `{candidate_kind:"REJECTED",input_evidence:{...}}`; no state/identity or fabricated bits. |
| OrbitInfo | `orbit_id, member_count, contains_known_valid_state` | minimum nine-bit signature; count16; exact bool. Unavailable membership means whole orbit_info is null. |
| StateValidityDiagnostic | `input_state, admissibility_status, transformation_compatibility, normalization_status, recoverability_relevance, is_valid, orbit_info, rule_ids, notes` | exactly nine wire fields; input_state is9-bit list or reviewed RejectedCandidateEvidence branch; enforce four coherent producer rows. |
| DiagnosticEnvelope | `diagnostic_kind, severity, stage, disposition, subject_reference, parent_diagnostic_reference, chain_root_reference, rule_ids, summary, notes` | exactly ten wire fields; pinned uppercase enums/taxonomy and complete chains. Root parent uses JSON null for source NONE; rootref equals actual emission reference. |
| DiagnosticEmission | `diagnostic_reference, envelope:DiagnosticEnvelope` | wire `{diagnostic_reference,envelope:{ten fields}}`; its reference stays outside canonical envelope. |
| CaptureReceipt | `diagnostic_reference, status` | status CONFIRMED, REJECTED or NOT_CONFIRMED; exact attempted reference. Only CONFIRMED acknowledgement extends emitted snapshot. REJECTED is an explicit guarantee that this attempted emission was not appended. |

Canonical binding records contain only the nine listed identity/hash fields,
not runtime source files or a claimed upstream Git revision (none is present in
ash_dependency_identity.json). Expected dependency is
ash_cosmological_model.f2_9.canonical, aggregate
0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb.
Use the actual manifest value when constructing: the literal is checked against
manifest/pins, rather than trusted because it appears in this prose. Source-path/hash mapping is
recorded in the companion interface_inventory.json to prevent transcription drift.

Profile and predicate references follow the existing common identifier grammar:
`^[A-Za-z0-9][A-Za-z0-9._:/-]*$`, length 1..256. The source hash is not an arbitrary
profile version string. WRW's immutable profile is derived from the actual nine
pinned anchors; neutral/empty profiles are explicitly source-bound test fixtures.
Actual source verification belongs outside neutral Core. For this repository reference assembly, independently reviewed pins/anchors and mandatory publication tests establish the supplied reference binding; individual constructor calls check those immutable declared values without performing IO or claiming fresh source verification. [YWE-REQ-0039]

## Bounded original payload

representation_kind is RAW_JSON, SIGNATURE, BIT_SEQUENCE, STATE_RECORD or UNSUPPORTED.
observed_length is an exact builtin-length observation or null; length_unit is
BYTES, CHARACTERS, ELEMENTS, KEYS or UNKNOWN. preview is null or at most 64 characters;
preview_encoding is TEXT or HEX (raw byte preview uses at most 32 bytes/64 hexchars).
coordinate_observations has at most 9 entries. Rejected evidence is an observation
of the supplied payload, never a full raw-input digest or proof of full capture.
The original reference remains the durable trace input supplied by the caller.

Coordinate scalar alternatives (no recursive metadata):

- INTEGER_BIT: value 0/1 only.
- INTEGER_OTHER: sign -1/0/1 plus exact integer bit_length; no unbounded decimal text.
- FINITE_FLOAT: value is the bounded built-in float.hex string, not a wire JSON number.
- NONFINITE_FLOAT: value NAN/POSITIVE_INFINITY/NEGATIVE_INFINITY fixed token.
- STRING: value at most 64-character prefix, total_length and explicit truncated flag.
- UNSUPPORTED: no raw value, name, repr or conversion-derived field.

Codec limits stay the reviewed 4,096 UTF8bytes, raw nesting 32, numeric token 128 bytes,
direct record 64 keys, max 9 observations and max 64-character previews. Accepted direct
containers/scalars are exact builtin types. Validate bounded dict keys as exact str
before owned lookups; leave unrelated metadata open/untraversed. Raw decode preserves
Decimal numeric tokens, catches numeric/parser failures, and forbids duplicate keys/
nonfinite JSON. Raw JSON precision and pre-parsed float values remain distinct.
`to_record()` itself is value-to-container conversion; complete canonical byte
serialization and platform numeric policy remain later M3 work.

## Result values and exact packet shapes

Every produced packet has these common required keys:

`schema_ref, artifact_type, artifact_version, outcome, assessment_binding,
source_binding, profile_binding, input_evidence, parsed_state,
state_validity_diagnostic, emitted_diagnostics`

Fixed header is schema_ref=data/schemas/m3_state_assessment_schema.json,
artifact_type=ywe_state_assessment, artifact_version=1.0.0.
source_binding is CanonicalAshBinding record; parsed_state is AshState record or
JSON null. Profile/source/assessment bindings and original-input evidence are
explicit; they are not extra canonical diagnostic fields. emitted_diagnostics is
the ordered acknowledged snapshot, with0..2 DiagnosticEmission records.

| Result constructor | outcome and additional required wire keys | Successful emission count |
|---|---|---|
| StateDiagnosis | `outcome:"diagnosis"`; common fields only | exactly 1 detection |
| StateAssessment | `outcome:"assessment"`; `system_context, classification_evidence, system_state_class, recovery_category, consulted_predicates` | exactly 2 detection then classification |
| ClassificationEvidenceFailure | `outcome:"failure",failure_kind:"classification_evidence"`; `failure_code, failed_predicate, system_context, classification_evidence` | exactly 1 confirmed detection; no invented classification record/class/category |
| DiagnosticCaptureFailure | `outcome:"failure",failure_kind:"diagnostic_capture"`; `failure_code,capture_status,attempted_diagnostic,system_context,classification_evidence` | zero at detection failure or 1 at classification failure; attempted record preserved separately |

The result constructors take the common values by exactly their listed field
names, plus the additional fields in their row. emitted_diagnostics is an owned
tuple; attempted_diagnostic is the complete immutable DiagnosticEmission. On capture
failure, system_context/classification_evidence are null for a diagnosis-only call,
otherwise the passed bound values; neither supplies class/category success.
capture_status is REJECTED (explicit no-append rejection) or NOT_CONFIRMED (no valid
acknowledgement, including throw after a possible append). Do not equate unconfirmed
with absent. Never publish success or discard the earlier acknowledged snapshot.
ClassificationEvidenceFailure retains full diagnosis/input/source/profile fields.
failed_predicate is correction_path_is_known or fallback_is_available, except
PREDICATE_BINDING_MISMATCH identifies whichever entry mismatched. Classification
has not completed; no failure packet carries system_state_class/recovery_category.

The source records remain separate nested objects: exactly 9 semantic fields and
exactly 10 envelope fields. Parent/optional NONE values use JSON null as a reviewed
local wire choice; diagnostic references otherwise use the declared identifier.
Do not map these packets to M2's numeric-severity DiagnosticEnvelope or the lower-
case closed common diagnostic format. Legacy diagnose_state output remains its
explicit flattened compatibility adapter, not this new packet serialization. Its
retained parent NONE sentinel stays the documented legacy form; the new packet
uses JSON null and the source root is always the actual stable emission reference.

## Concrete method signatures (not implementations)

```python
StateInputCodec()
StateInputCodec.decode(self, candidate, *, original_input_reference, legacy_whitespace=False)
# -> DecodedInput(state: AshState | None, input_evidence: InputEvidence)
# Representation failure is state=None + typed rejected observations, not escaped error.

StateModel(profile_binding, canonical_binding, diagnostic_capture)
StateModel.diagnose(candidate, *, diagnostic_context)
# -> StateDiagnosis | DiagnosticCaptureFailure
StateModel.assess(candidate, *, context, classification_evidence, diagnostic_context)
# -> StateAssessment | ClassificationEvidenceFailure | DiagnosticCaptureFailure

DiagnosticCapture.begin(assessment_reference)
# -> assessment-scoped capture; no retained global mutable trace.
AssessmentCapture.append(emission)
# -> CaptureReceipt; real owned append precedes CONFIRMED acknowledgement.
StateModel call-owned capture trace.confirmed_snapshot()
# -> immutable tuple of receipts actually received/validated, per-call maximum 2.
```

The default reference collaborator is an explicit in-memory RecordingDiagnosticCapture
instance supplied by the facade/factory. Injected test collaborators may reject/throw
at exact append boundaries; they do not provide arbitrary candidate conversion
callbacks. A receipt is structurally/reference-checked; NOT_CONFIRMED or malformed
receipt cannot count as emitted. REJECTED yields DIAGNOSTIC_CAPTURE_REJECTED only
when a valid receipt for the exact attempted reference explicitly guarantees no
append. Generic exceptions, malformed receipts, wrong references and absent
acknowledgement instead yield DIAGNOSTIC_CAPTURE_UNCONFIRMED/NOT_CONFIRMED; do not
infer REJECTED from them. An adapter that appends then reports REJECTED violates
its explicit collaborator contract; the in-memory producer/tests must demonstrate
real no-append on this branch. StateModel maintains its own acknowledged prefix
and extends it only after a CONFIRMED receipt is actually received and validated.
It must not query an adapter's possible stored records after an exception and infer
that an acknowledgement happened. A throw after possible external append preserves
only the earlier prefix and the complete attempted record as NOT_CONFIRMED. Preserve only the actually acknowledged snapshot;
external persistence or reliable retry is not claimed by this memory capture contract.

StateContractError(code, field_name) (proposed ValueError subclass) is a typed constructor/precondition exception
with bounded fixed field name and empty emitted snapshot. It has no successful
packet/to_record operation because malformed bindings cannot construct an honest
bound packet. Candidate malformed representations do not use this caller-error path:
they produce complete UNCLASSIFIED diagnosis. Mismatched predicate subject/source or
consulted NOT_EVALUATED found after diagnosis instead yields the retaining
ClassificationEvidenceFailure. A capture failure yields its retaining value above.
No error path executes normalization, correction, fallback, containment or safe halt.

## Stable local failure codes

These codes are YWE reference-boundary identifiers, not invented canonical ASH rule IDs.

| Owner | Codes and exact meanings |
|---|---|
| AshState constructor / decoded bits | STATE_WIDTH; STATE_COORDINATE_TYPE; STATE_COORDINATE_VALUE |
| Representation codec | INPUT_KIND_UNSUPPORTED; INPUT_SIZE_LIMIT; INPUT_DEPTH_LIMIT; INPUT_TOKEN_LIMIT; INPUT_UTF8_INVALID; INPUT_JSON_INVALID; INPUT_JSON_DUPLICATE_KEY; INPUT_JSON_NONFINITE; INPUT_NUMERIC_TOKEN_INVALID; INPUT_SIGNATURE_INVALID; INPUT_RECORD_INVALID; INPUT_RECORD_SIZE_LIMIT; INPUT_RECORD_KEY_INVALID; INPUT_STATE_SPACE_INVALID |
| Binding/configuration constructors | CANONICAL_BINDING_INVALID; PROFILE_BINDING_INVALID; PROFILE_STATE_DUPLICATE; PROFILE_SIZE_LIMIT; PROFILE_SOURCE_MISMATCH; CONTEXT_INVALID; DIAGNOSTIC_CONTEXT_INVALID; PREDICATE_EVIDENCE_INVALID |
| Contextual evidence after detection | PREDICATE_BINDING_MISMATCH; PREDICATE_NOT_EVALUATED |
| Value construction conformance | DIAGNOSTIC_ROW_INVALID; DIAGNOSTIC_ENVELOPE_INVALID |
| Capture return values | DIAGNOSTIC_CAPTURE_REJECTED; DIAGNOSTIC_CAPTURE_UNCONFIRMED |

PROFILE_DATA_UNAVAILABLE is an explicit profile availability reason, not a failed
constructor or inferred empty profile. INPUT_JSON_INVALID covers syntax/decoder
recursion failure; numeric-token errors have their dedicated code. Candidate width/
coordinate errors become InputEvidence.failure_code and UNCLASSIFIED, retaining the
bounded observation. Capture-rejected cause must remain a stable typed reason, not
an arbitrary exception message. Where more than one representation fault exists,
apply the reviewed order: outer kind/size/key/encoding/depth/token parsing, owned
state_space/width, then coordinate index order. Constructor validation order is
field declaration order. Schema diagnostics do not invent a broader runtime policy.

## Local choices and root review

The packet header/discriminators, constructor/code names and source NONE→JSONnull
mapping are precise downstream implementation choices; root accepted the header,
discriminators and null mapping. The three-status receipt correction and exact
nine-field binding validation are incorporated here for final composition. No canonical source text,
legacy M2 packet schema, classifier precedence, profile authority or completion
scope changes. If root prefers another name/field, update this inventory before
schema/tests/code depend on it. Full Diagnostics meta-diagnostic conformance stays
explicitly deferred; these failures are not a substitute for that obligation.
