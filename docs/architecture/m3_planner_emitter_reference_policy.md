# Bounded M3 generation planner and artifact emitter reference policy

Status: active adopted M3 contract design. Source4 extension is ACCEPTED_PENDING_APPLICATION;
implementation remains NOT_ISSUED and runtime acceptance/containing revision is not asserted.
Requirement: YWE-REQ-0049. Governance decision: ADR-0041.
Identity: YWE-M3-PLANNER-EMITTER-REFERENCE-001, version 1.0.0.
Partition: ywe_core. Method pin: Raven v0.7.0 at
87409bc36fb9d4782eab02189adb184f2b3962a7. This proposal preserves the actual legacy
plan_generation helpers and existing ash_generation_packet_schema.json, the
adopted TA policy ab645a078e9aaee04e3eb01ac1ced01de986340d8f0242057eb3e4567196c7ae,
all sixteen canonical full-vector codewords and all512 states. Future generation
bias records remain eligibility/weighting input to separately contracted later
systems, never direct quests, NPCs, lore, world artifacts, creatures or abilities.

## 1. Reference scope and explicit choices

The planner MUST produce a complete deterministic inspectable abstract plan with
no collector, clock, storage, process, host callback or target effect. The emitter
MUST materialize solely from that complete plan into an explicitly configured
REFERENCE_MEMORY_DOCUMENTS runtime target. The selected target publishes canonical
ASCII JSON documents to an owned bounded in-memory document store. Those are actual
runtime artifacts and observable store effects; they are not physical files,
durability attestations, platform packages or gameplay content. No file target is
implicitly substituted or claimed. [YWE-REQ-0049]

Every GenerationInputs constructor field is explicit. The reference convenience
factory may populate the documented literal choices, but the resulting immutable
request MUST retain them: normalization_mode ALREADY_VALID; role_profile_id
TERNARY_BRANCH_ROLES_001; naming_policy_id YWE_ASCII_DOCUMENT_NAMES_001;
subject_policy_id DECLARED_AXIOM_FACTS_001; artifact_policy_id
REFERENCE_MANIFEST_PAGES_001; target_runtime REFERENCE_MEMORY_DOCUMENTS;
emission_choice REFERENCE_MANIFEST_PAGES or INSPECT_ONLY. INSPECT_ONLY is an explicit
requested no-artifact plan, never a fallback for a materializing request.
project_name matches [a-z][a-z0-9_-]{0,31}; seed_token matches [A-Za-z0-9_-]{1,32};
depth is0..6; ordered transition selections are0..4. Unknown policy IDs, target
runtime, choice or constraint kinds are structural contract errors before hooks. [YWE-REQ-0049]

## 2. Full binding and original owner identity

PlannerEmitterBinding contains the complete current CanonicalAshBinding,
AvailableProfileBinding or tagged UnavailableProfileBinding, exact ordered eleven
canonical contract pins and the exact policy identity/version/bytehash. Operations
are eligible only for the proposed M3_GENERATION complete vector; old complete source baselines
remain recognized historical evidence and refuse new execution. No aggregate-only,
mixed vector, partial profile or caller authenticity boolean is sufficient.

The eleven pins, in order, are generation-planner-contract, artifact-emitter-contract,
generation-planning.pseudo, realm-encoder-contract, transition-registry-contract,
topology-generator-contract, axiom-evaluator-contract, realm-identity.pseudo,
diagnostic-schema, rule-id-taxonomy, diagnostics-module-contract. Exact peer RT and
TA bindings independently retain their complete eleven/seven pins. This proposal
does not drop peer semantic pins to fit a local producer table. Each dependency
must have equal complete canonical and profile values, its own adopted policy and
its exact configured producer seal. SOURCE_PINS.json derives exact bytes from the
full external proposed-canonical tree, with actual current originals recorded.

SOURCE_EXTENSION_INVENTORY.proposed.json defines candidate M3_GENERATION aggregate
2371f71e570b4e193f5fc3e3e210816b06640204582dbb17046f78ae1d5efcc8.
Exactly transition-registry-contract.md and diagnostics-module-contract.md gain
normative chain/effectful capture clauses; thirty of32 normalized source blobs
remain exact. All three earlier complete vector objects, including f431 M3_MODULES,
remain exact historical recognized inputs. The new complete9 fields, paired7
Recovery/8 Diagnostics fields and11RT/7TA/11planner-emitter pins are all derived
from the same candidate32 bytes. No old baseline row is overwritten or aliased to
new meaning. Matching actual owner adoption and containing Git proof are required
before new-vector constructors or hosts are admitted. Null defaults stay legacy;
explicit ordered subsets and historical revision treatment remain compatible.

Proposed host/source mapping has four exact named branches. New generation revision
must match actual nonnull ImplementationIdentity.source_revision; supplied earlier
N3/MODULES revisions must match their independently verified historical containing
manifests. Exact fourth branches propagate through StateModel/PredicateBinding,
Recovery7pins, Diagnostics8pins/profile/source schemas and host verification, RT11
and TA7 bindings, source guards, public registration and fixture controls before
implementation. Old RT single-apply and standalone TA f431 operation eligibility
stay exact; chain/planner/emitter require the new vector. Complete generation and
emission operate under the standalone Core lifecycle, with no new Session generation
or emission command. The separately proposed Session v1.1 lane is limited to the
four pure producers and explicit complete f431/M3_GENERATION source/policy pairs;
its source4 transition action selects original single-apply, never compound chain.
Session publication stays exclusive RecoveryEngine. Core execution gates confer
no Session/Recovery authority and those owners refuse them before caller hooks.

configuration() returns the exact immutable PlannerEmitterBinding through exact
class-owned dispatch. validate_owned_result(result) returns an exact bool through
class-owned dispatch. Original producer identity and original constructor model,
binding/dependency-owner/target configuration identities are sealed privately;
shallow/deep copies and reflected self-identity reset cannot mint/validate/register.
Result cookies bind the original issuer and exact result object, not text IDs or
copied private slots. No unbounded per-result registry is introduced. These seals
prove configured local execution, not collector persistence or host authenticity.

## 3. Additive substantive ordered transition chain

TransitionRegistry.apply_chain(origin, selections, *, operation_reference) is a
proposed additive pure API. Existing resolve/apply shapes and single-apply behavior,
including actual TC targets, stay exact. The chain consumes the actual current
StateDiagnosis and shared class-owned DiagnosisValidation. It emits an initial
VALID_SOURCE record even for empty selection. An unparsed, unavailable, rejected or
nonVALID source retains the actual failure gate/prefix or typed pending evidence;
no default state or replacement StateDiagnosis is made.

For each requested selection in order: exact canonical membership is evaluated and
recorded; the selected definition's512ASCII mask is indexed by the full current
candidate's nine-bit integer and recorded; then every coordinate is XORed with the
full selected codeword, the actual class-owned StateModel.inspect_state(candidate)
is retained and the transformation is recorded immediately. There are no instance
hooks or target emissions. Unknown selection stops after its membership record;
false mask stops after applicability; no later condition is evaluated or recorded.

Each completed step retains ordinal, actual input state, actual selected definition,
actual selection/applicability/transformation observations, the complete pure
target diagnostic, source proof reference and its three real records. The next
step reuses that exact already evaluated target diagnostic as its VALID admission
proof under the same complete binding; it performs no new validity evaluation and
emits no fabricated gate. The final transformation record cites both
ASH-CODEWORD-TRANSFORMATION-001 and ASH-STATE-VALIDITY-001 and is BLOCKED if its
computed target is notVALID. A TC/TI/UNCLASSIFIED target stops the strict aggregate
at that computed candidate, retaining the actual computed prefix and
CHAIN_TARGET_NOT_VALID. It is not normalized, encoded or published. Original
single apply still reports the computed TC target without this strict chain policy.

An empty chain completes as identity after its one source gate. A chain of four
steps has at most13 records, inside the existing17 reservation. A failed chain
retains requested selections, actual evaluated prefix, failed index/phase and
last actual candidate. Failure at step0 selection has no computed step; failure
after a transformation includes that actual step. There is no per-step assessment,
collector ACK or new root. All chain TENs use the actual initial DETECTION subject,
root and successive actual parent. Severity never drops.

The standard WRW profile retains9VALID/135TC one-step pairs. Strict chains must
therefore exercise nonzero multi-step transitions under an explicitly valid
full512 or independently enumerated C-coset test profile. Zero-codeword repetitions
in WRW are not the sole substantive chain control. Restricted-mask refusal and
second-step inapplicability are tested against the actual intermediate candidate.

## 4. Explicit composition before pure planning

ReferenceGenerationRunner performs assembly and ordered persistence outside the
pure planner. It obtains actual completed initial StateDiagnosis, captures source
RealmEncodingResult, captures one owned successful aggregate TransitionChainResult,
then calls StateModel.diagnose on the actual final candidate with fresh explicit
diagnostic references and completes that actual N1 diagnosis in the same collector.
It captures destination RealmEncodingResult, TopologyResult and complete
AxiomEvaluationResult rooted in that actual final diagnosis. Even an identity
chain receives a fresh actual final diagnosis. It does not relabel an old root.

PlannerRequest contains five immutable issued dependencies in fixed order:
source encoding, aggregate chain, destination encoding, topology and axiom result,
plus inputs, actual source/final diagnoses and the explicit target constraints.
The planner checks complete value/math/source/profile/current-policy coherence and
exact class-owned execution seals; these are pure checks, not persistence claims.
Collector module admission independently requires those five dependencies'
first matching COMPLETE finish and CONFIRMED final observation, and the actual
final diagnosis first-completed DETECTION. Five roots fit the existing maximum6;
four arbitrary transition roots are not used as an aggregate substitute.

Chain source equals normalized source; destination encoder state, final actual
diagnosis, topology input and axiom subject state equal the actual final candidate.
All profile IDs and inputs are bound to their actual full profile values.
Topology request depth and seed token equal the explicit GenerationInputs.
The new final diagnosis root is the planner's root; initial/chain/source encoding
roots remain typed dependency facts and are never spliced into its parent chain.

ReferenceGenerationRunner.run returns exact GenerationRunReceipt with six fields:
operation_reference (maximum128 so every child operation fits160), status
READY/REFUSED/NOT_CONFIRMED, last_stage, last_observation,
last_origin_completion and completed_operation_references (maximum7). The closed
last_observation is one actual N1 diagnosis/failure or actual dependency/plan
capture receipt; it does not recursively repeat all prior packets. An N1 last
observation retains its actual first DiagnosticsCompletionReceipt separately;
otherwise last_origin_completion is null because the nested capture already has
its real completion. completed_operation_references identify actual prior immutable
same-collector members; missing/unconfirmed stages are never listed as completed.
Early source/chain/final diagnosis/topology/axiom/capture failure stops the sequence
and retains its actual typed last observation. It does not construct a missing plan.

Runner configuration() and validate_owned_result(run_receipt_or_actual_emit_capture)
are pure exact
class-owned ports with original constructor/return self seals and full current
binding. READY is issued only after actual plan first COMPLETE finish and CONFIRMED
final observation from its genuine execution; a caller-constructed or copied
receipt cannot confer that local capture fact. Core composition may consume this
public seal and actual plan field to issue its own pure view permit, without
reading peer private state or inventing a new collector authentication port.
Runner.emit returns the actual PlannerEmitterCaptureReceipt object while retaining
its original emitter result and collector first response. The same public
validate_owned_result port additionally accepts only the exact genuine capture
instance returned by that original runner, with an API-private original runner/
return/self/operation/composition cookie. A direct foreign emitter receipt, copy
or reflected self reset cannot confer runner completion. No wire field or prior
receipt is rewritten; target complete/partial/unknown effects and capture status
remain independently factual.

normalize_state is the explicit ALREADY_VALID identity boundary in this reference
policy. The initial actual source must already beVALID/ALREADY_VALID. A caller
requiring normalization must perform the existing separately captured StateModel
normalization before constructing the generation input. No policy silently picks
a nearest valid state or invokes recovery from the pure planner.

## 5. Roles and declared axiom subject

assign_roles maps each actual final-frontier node, in its existing ordinal order,
to one of exactly four abstract roles ROOT, CONTINUATION, POSITIVE, NEGATIVE by
the actual topology branch_kind. role IDs are role:root, role:continuation,
role:positive, role:negative. Assignment identity is
<plan_reference>:assignment:<path_token>; path/depth/ordinal/full destination state
are retained. This mapping does not derive world/Cosmology/personality/gameplay
roles or measures. Every topology node has exactly one assignment, no extras.

build_axiom_subject binds an explicitly declared AxiomSubject to the actual final
state and actual final diagnosis reference. It does not derive relation_count,
compressed/raw measure, scale_count, erasure cost or self-reference booleans from
bits, topology size or branch roles. All units, tick scales, provenance source,
method and revision remain actual declared input and are preserved. The current
five-AxiomEvaluator supplies all32 component combinations, both self-reference
booleans independently, full explanations, cumulative chain severity and the
fifth component/conjunction distinction. Declared measurements are not certified
real-world measurements or claims of consciousness.

False complete axioms do not make the abstract plan malformed. warnings contains
one exact A1_FAILED..A5_FAILED code per false component in A1..A5 order. The explicit
constraint ALLOW_DECLARED_AXIOM_FAILURES decides emission eligibility: true permits
those documented warnings, false yields a complete inspectable plan whose emission
authorization is blocked before target effects. Nothing hides failed components.

## 6. Deterministic complete plan and artifact semantics

plan_reference is request.operation_reference + :plan (operation max160 here keeps
every derived reference <=256). Plan retains normalized state, source/destination
RealmIdentity, lossless source_realm/destination_realm aliases, complete topology
nodes, role assignments, full declared axiom subject, AxiomDiagnostic, ordered
warning codes, target constraints, explicit input metadata, source/profile/policy
bindings and dependency operation references. The plan alone contains everything
needed for artifact materialization; the emitter never calls any planner/RT/TA
owner. A receipt authorizes provenance separately from content specification.

For REFERENCE_MANIFEST_PAGES, split the ordered final-frontier into contiguous
pages of32 rows; each row contains its actual TopologyNode and RoleAssignment.
Depth0 yields1 page, depth6 yields23 pages, last page25 rows. Manifest name is
ywe-<project_name>-manifest-<three-digit-zero-based-page>.json. Flat ASCII names are
unique, maximum62 characters, independent of OS conventions. No implicit path,
directory, filename extension, overwrite policy or generated prose is invented.
Artifact reference is <plan_reference>:artifact:<three-digit-page>; plan element
reference is <plan_reference>:manifest:<three-digit-page>. Artifact kind is
REFERENCE_MANIFEST. Perartifact role references are the unique fixed role IDs
present in its rows, in ROOT/CONTINUATION/POSITIVE/NEGATIVE order, at most4.

ReferenceManifestDocument has exact schema_version1.0.0, document_kind
YWE_REFERENCE_MANIFEST, plan_reference, project_name, page_index/page_count,
source/destination nine-bit states and identity records, full declared axiom subject,
AxiomDiagnostic, warnings, explicit target/role/naming/subject/artifact policy IDs,
complete policy/source digests, ordered dependency references and the exact rows.
These payload facts are already in the plan. Every document uses the same explicit
UTF8_ASCII_JSON_SORTED_COMPACT_NO_NEWLINE serializer (ensure_ascii=True,
sort_keys=True, separators comma/colon, allow_nan=False); bytes are ASCII/UTF-8
equivalent. Description retains exact document, SHA256 and byte count, measured
<=32768 before returning an ordinary plan. INSPECT_ONLY retains the same complete
plan facts but artifacts=() and no document derivation. It does not authorize a
materializing target to guess a document.

Metadata is a closed typed record, not a map: explicit request/profile/policy IDs,
source/destination diagnosis references, chain/topology/axiom operation references,
the three declared semantic policies, normalization_mode and materialization_boundary
ABSTRACT_NO_EXTERNAL_EFFECTS. Targets are abstract runtime choices/capabilities.
Constraints are fixed typed fields: max_artifacts0..32, max_document_bytes1..32768,
max_total_document_bytes1..1048576, allow_declared_axiom_failures bool,
existing_document_policy EXACT_BYTES_IDEMPOTENT_OR_REFUSE. Actual document totals
are checked against requested constraints; unsatisfied ordinary planning constraints
produce a typed refusal, not an implicitly shortened plan or fewer nodes.

## 7. Pure diagnostics, guards and failure shape

Planning constructs its one owned GENERATION_PLAN/PROCESSING record at the actual
condition. Success cites PLAN001 and BOUNDARY001; summary and notes are compiled
closed templates describing counts, choices and actual warnings. Failure retains
the exact failed field and finite reason code with an actual record if a current
verified actual final diagnosis supplies a legitimate root, otherwise typed pending
evidence. No timestamp, severity downgrade, reparented subject or fake capture
completion is produced. Persistence takes place after pure computation by composition.

Every constructor and serializer uses exact owned classes, identity-only type
membership, primitive-before-comparison checks, no caller eq/hash/str/to_record,
bounded tuples and recursion, no cycles/unknown classes/subclasses and no instance
method/property callbacks. Reused bounded N1 malformed-input observations remain
truthful; new authored text is scalar-valid. Results and reflection-corrupted copies
are fully revalidated at every public boundary, with actual byte measurements.

Every complete planner/emitter business-plus-first-finish-plus-final-observer packet
is compact ensure_ascii <=2097152 bytes. Raw size measurement returns limit+1 on
size overflow only; canonical_bytes/to_record raise the closed raw-limit error.
An input too large to return in a closed refusal is an API contract error before
capture/effect; its exact immutable API DAG may be retained locally, never silently
truncated or described as a valid wire packet. Before each target action, validate
the candidate full final-result upper shape with the actual prior prefix and
remaining worst closed outputs/records/completion/final observer. No ad hoc byte
allowance substitutes for this proof. Each actual new TEN measured<=8192 bytes.

The seven source-owned wire families have distinct additive source4 schema IDs and
filenames: m3_generation_state_schema.json,
m3_generation_normalization_plan_schema.json,
m3_generation_state_normalization_schema.json,
m3_generation_realm_transition_schema.json and
m3_generation_topology_axiom_schema.json, m3_generation_recovery_value_schema.json
and m3_generation_module_capture_schema.json, all under https://ywe.local/schemas/.
They are generated deterministically from pinned original schema bytes and the
complete source4 matrix. Historical schema IDs, definitions and serializer headers
remain exact. Each family's class-owned wire_schema(exact_owned_value) returns its
compiled schema ID from the exact retained full canonical vector and the owned
root type/format; it takes no caller selector or arbitrary schema path. A recognized
historical root returns its existing schema ID; a full M3_GENERATION root returns
its generation-family ID. Unknown/mixed/foreign roots fail before hooks. Existing
TEN fields are unchanged. to_record emits the corresponding compiled schema_ref
where that root already has such a header; no new header is added to RT/TA roots
that lack it. All source4 normalization nested references use the new plan/state
IDs, so a source4 NormalizationResult cannot route its actual original diagnosis
through an old source3 schema. Source4 Core/Session/collector/PE schemas consume
these explicit IDs; original selected fixtures remain bound to historical IDs.

## 8. Authenticated plan transfer without emitter callback

Diagnostics.prepare_emission(planner, actual_plan_result, actual_capture_receipt,
emitter, target) is a proposed composition port, not an existing function. Outside
collector IO it validates the exact registered planner/emitter and class-owned
full bindings; inside its bounded ledger it authenticates the original planner
result, first matching COMPLETE completion and CONFIRMED final observation.
It issues a private PreparedEmission capability tied to exact collector, emitter,
target, complete plan object/self identity/hash/current bindings and one operation
reference. It returns a separate closed preparation receipt, never rewrites pure
plan/capture. It confers local transfer eligibility, not durable host certification.

Emitter consumes only PreparedEmission plus its complete plan/target configuration;
it does not call configuration()/validate_owned_result on the planner or request
more semantics. Collector handles provenance at preparation/admission. Prepared
capabilities are API-only, copied/foreign/used/logically-invalid/mismatched values refuse by
identity before arbitrary comparisons or IO. Fixed capacity64 preparations,8active
emissions, lifetime64 retained final operations; no unlimited token ledger or silent
eviction. Every ordinary return frees active membership and completes once; final
evidence stays retained until explicit collector teardown. This new preparation
ledger does not enlarge the collector's existing store/support/alias/event limits.

There is no wall-clock expiry or new clock port. Logical invalidation occurs only
when its exact preparation is consumed by one emit attempt, cancel latches that
operation, shutdown seals the emitter, collector teardown invalidates its issuer,
or complete source/profile/policy/target composition changes at a current recheck.
Each issued preparation consumes one lifetime slot even if canceled or refused
before effects. Nonissued refusal allocates no slot. Active membership is released
after the actual once-finish/observer attempt, while the immutable operation and
first response remain in the fixed64 lifetime records; slots are not silently
recycled. shutdown returns exact API-only OwnerShutdownObservation and revokes
all following grants without collector/target callbacks under the owner lock.

## 9. ACK-before-effect and exact lock boundaries

Emitter preflight validates closed plan/document bytes, constraints, target binding,
explicit warning authorization, capability/current composition and full worst-case
combined raw size. Whole collector reservation/projection and genuine issued scope
are obtained before ordinary target action. Allocated scope is retained for cleanup
even if admission receipt or its references are unconfirmed. Matching confirmed
admission is required to dispatch, not merely cleanup eligibility.

For artifact i: under emitter lock choose its fixed index/reference/hash/name and
construct ARTIFACT_DISPATCH with exact trace/fidelity/ emission rules. Release the
emitter lock, append that record through the exact scope; require actual CONFIRMED
CaptureReceipt with matching diagnostic reference and current issuance/bindings.
Reacquire emitter lock to grant exactly one action lease and atomically verify the
operation remains active/not canceled, target/current capability unchanged, previous
outcome known and actual expected target revision. Release all emitter/collector
locks before exact class-owned MemoryDocumentTarget.materialize(lease, description).
Injected clock/store may reenter cancellation while append is in flight. A canceled
operation has no following grant. A callback already granted may finish; this is
not physical preemption. A late return is retained as actual outcome, cannot gain a
later dispatch or append to a separately frozen N3 chain. These modules remain
standalone M3_GENERATION under Core lifecycle, with no Session publication authority.

The target holds only its own private nonblocking lock during immutable document
map commit/readback. It calls no collector, emitter or caller hook while locked.
Lease validation, hashing, readback construction and receipt sealing under that
lock use only exact owned slots and local compiled functions; no producer method,
instance property, equality/hash/string/conversion hook or private foreign-member
call is permitted. Target lease metadata consumes one of2048 lifetime slots;
active lease membership is released on the actual return, consumed identity stays
in that finite ledger and never becomes reusable by resetting a copied field.
Emitter invokes neither target nor Diagnostics while holding its lock. Collector
trusted code invokes neither producer nor target under IO. An unexpected target
exception/wrong or foreign receipt yields UNKNOWN/null effects unless an exact
trusted receipt proves actual outcome; no untrusted exception text is retained.
After return, construct and attempt the actual ARTIFACT_RECEIPT even when failed,
unknown or cancellation occurred. Unconfirmed outcome capture stops later dispatch;
confirmed capture never changes actual target truth. Ordinary posteffect failure
cannot claim rollback.

The effectful scope checks two original API-only tokens: its exact CoreExecutionGate
child when provided and an exact IssuedEmitterCaptureControl. The private control
is issued by the original emitter for that exact collector/operation/prepared
capability; its cookie retains original control/self/emitter/collector identities
and fixed record slots. A copy, reflected self reset, foreign emitter/collector or
wrong operation refuses before IO. It has no public authority constructor. The
class-owned IssuedEmitterCaptureControl.validate_issued_for_collector(control,
collector,operation_reference) returns exact bool and capture_disposition(control)
returns ACTIVE/SEALED/UNAVAILABLE by nonblocking token read, without owner entry.
Emitter cancel/shutdown latches its private cancellation before callbacks and seals
that control. Core stop independently seals the Core child. The scope's ordinary
append requires both provided tokens ACTIVE before and after IO. A held token is
UNAVAILABLE, never an inferred grant. No stage_grant is called under collector IO.
Direct standalone emit with Core gate None still requires the original emitter
control; pure old module_capture with no tokens remains unchanged. Core orchestration
always supplies its issued child gate. Diagnostics.module_capture gains only the
explicit keyword emitter_control for this effectful branch, alongside execution_gate;
unknown or duck-typed controls are rejected. Its six-field ModuleCaptureContext
retains the complete immutable EmitterRequest, not a capability wire field.

A target return after either token seals is retained as the actual immutable outcome
in the owner result and bounded separate late-audit/pending lane. It cannot append
an ordinary TEN successor after cutover or claim a dispatch/outcome ACK. The genuine
original scope still finishes once and observes that actual first response once;
cleanup does not revive either token, mint a stage grant or replace a prior response.
Actual INCOMPLETE/NOT_CONFIRMED cleanup truth and final retention failure remain
separate from actual target effect truth. Already granted finite actions may return;
no physical preemption or rollback is claimed. Original scope/control/gate tokens
remain retained for this cleanup until explicit collector teardown.

Then construct one OPERATION_SUMMARY from actual prefix/outcome/failure facts,
attempt it once if current main capture remains appendable, otherwise retain it as
pending actual evidence. Finish the genuine scope exactly once with the actual
owned final result, retain the actual first response, observe_final once and audit
return. No cleanup retry fabricates complete coverage. Max records2N+1<=65;
selected23 artifacts<=47. Zero artifacts returns NO_OP with sole actual summary,
no action lease and no target entry. A refused capability creates bounded API
failure/pending evidence without pretending an admitted scope existed.

The effectful capture context has its prepared immutable EmitterRequest and exact
PreparedEmission capability, plus one already captured PlannerResult dependency.
Its actual final diagnosis is retained by that issued preparation; it is a real
collector member, not reconstructed from plan metadata. Before effects, the scope
fixes artifact dispatch/outcome/summary reference slots and phase order from the
complete plan. It validates issued immediate records as each condition occurs;
unknown target outcomes are not precomputed, hashed or fabricated at admission.
The module-capture source4 copy routes nested RT/TA/N1 values through the generation
family IDs; its completion representation and five API-value field shapes remain
unchanged. The N2 source4 copy preserves all three historical paired RecoverySourceBinding
branches and adds only the exact fourth full canonical plus seven-pin branch;
RegistrySourceBinding retains exactly the four recognized aggregate values and
runtime pairing still requires the full current source/profile association. Its
normalization plan/result references use the generation-family IDs.
This is an explicit additive effectful capture branch; the current pure-result
tuple/hash validation remains unchanged. The emitter final owner validates its
record/outcome trace without calling target materialize again.

## 10. Target effect, readback, conflict and concurrency truth

MemoryDocumentTarget constructor takes exact target_reference, policy binding and
explicit limits (max_documents32, max_bytes1048576); starts version0 and empty map.
Original target/cookie/self/constructor config identities are privately issued.
Snapshot returns exact immutable TargetSnapshot(revision, complete0..32 documents,
actual_byte_count) under the target lock; it performs no IO or outside callback.
Documents are sorted by exact ASCII name in ascending lexical order. Each MaterializedDocument contains actual artifact/plan/element refs, flat name,
canonical content_ascii, actual bytecount/SHA and creation revision.

An exact issued single-use action lease binds target, emitter, operation, artifact,
full plan hash, expected target revision and expected bytes/hash. Under target lock
the target validates the lease using its own issued association, not emitter callbacks.
Wrong/copy/stale/used lease or busy target refuses before target change. Fresh name
and remaining capacity publishes the complete immutable document atomically and
increments version by1, then independently reads retained bytes/hash/length to
produce SUCCEEDED/actual_effects=true. Same existing bytes and same plan element
returns NO_EFFECT/false with unchanged revision and exact readback. Same name with
different bytes or plan element returns FAILED/false/DOCUMENT_CONFLICT and actual
existing hash/count/revision. Resource refusal or known busy has false effects.
No overwrite, delete, silent eviction or operator cleanup is performed.

Before fresh-name map publication, revision==UINT64_MAX refuses with
TARGET_VERSION_EXHAUSTED/false and unchanged map/revision. Equal existing bytes
still permit known NO_EFFECT at UINT64_MAX because no version increment occurs.
Every count/byte/revision/lease-capacity comparison precedes ordinary map mutation.

The target's private single-use lease membership is bounded to2048 lifetime
dispatches, with at most8 active leased actions, alongside64 retained operation
preparations. A typed limit refusal precedes additional target change. Factory
issuance retains exact original target/emitter/lease/description identities and
constructor configuration, so target validation does not call emitter/collector
while holding its lock. No public constructor or copied self-identity grants a
lease. Already granted actions remain eligible to return after cancellation.

A target receipt is owned, exact immutable and tied to actual single action plus
before/after version; forged/copy/mismatched receipt cannot authorize success.
Status SUCCEEDED requires matching expected readback/hash/count and version+1;
NO_EFFECT requires matching readback and unchanged version; FAILED retains its
actual finite reason and known effect fact; UNKNOWN carries null fact/version or
readback only where unavailable. A real internal failure after map commit may
return FAILED with effects=true and actual published/readback facts. It never
returns a false preaction failure after an observed commit. The general unknown
fallback is intentionally conservative and does not claim an effect occurred.

Only one active command per emitter/target pairing is admitted, with nonblocking
refusal on reentry; across different emitters sharing one exact target, stale
revision/lease refuses under target lock before additional changes. Previous
success artifacts survive all later failures. Result distinguishes semantic
SUCCEEDED/NO_OP/FAILED/PARTIAL/UNKNOWN from capture CONFIRMED/NOT_CONFIRMED.
UNKNOWN target effects stop later actions. Idempotent complete retry of the same
plan is a new explicit operation/preparation; it reports NO_EFFECT for existing
equal documents, never a second effect or substituted semantics.

## 11. Required closed safe graph corrections and executed proof

The six revised source4 safe definitions are additive GenerationSafe_PRODUCER_SOURCE,
GenerationSafe_ROLE_PAGE, GenerationSafe_GENERATION_PLAN, GenerationSafe_TARGET_CONSTRAINTS,
GenerationSafe_EMISSION_OUTPUT and GenerationSafe_TRANSITION_REGISTRY. Each has required
projection_version M3_GENERATION_1_0; source is exactly M3_GENERATION. Their separate
SafeGenerationModuleEvidence wrapper is disjoint from the unchanged historical
SafeModuleEvidence wrapper by additionalProperties and the required version tag,
including an empty role page. SupportingEvidence.module_evidence selects oneOf those
two wrappers. All seventeen historical payload definitions and selected historical
validators remain exact, including their rejection keyword/path signatures. A new
source4 producer MUST select the revised six-kind branch; it cannot omit new facts
by choosing a historical validator. The other eleven payload kinds reuse their
unchanged exact definitions. The existing node-kind quotas stay unchanged. [YWE-REQ-0049]

ROLE_PAGE must add exact role_kind ROOT/CONTINUATION/POSITIVE/NEGATIVE so abstract
meaning is not hidden behind an opaque alias. GENERATION_PLAN must retain aggregate
chain operation, actual source/final diagnoses, normalization mode, requested choice
and exact target runtime. TARGET_CONSTRAINTS must retain actual numeric limits,
warning authorization, idempotent/conflict policy and runtime. EMISSION_OUTPUT must
retain actual target version facts, finite detailed outcome reason and readback
assurance, separate from actual effect bool/null. TRANSITION_REGISTRY must retain
actual chain selections, perstep source-proof/record links and failed prefix using
the existing registry/definition/record nodes rather than four root dependencies.
These are proposed additive safe schema/domain amendments before dependent code,
not unreviewed reinterpretations of current fields.

Opaque project/seed/name/method/revision/provenance/target/operation references are
aliased, never exported raw caller text; raw complete source/profile/measure facts,
ordered topology paths, role meaning, selected codeword/mask, target actual effect,
hash/count/revision and closed compiled notes remain visible. Content is represented
by complete plan semantic facts plus name/content aliases/hash/count; safe export
does not promise arbitrary original raw document bytes or measurement authenticity.
Every new retained node retains SafeModuleEvidence wrapper identity; all references
resolve or explicitly describe omitted observations. No arbitrary map or caller note
enters safe support. The original seventeen node kind quotas/global limits and six
whole reservations remain controlling; amendments must be measured and independently
replayed. Structural maxima are representation witnesses, not actual runtime effects.

The full isolated closure includes two actual N1 origins, five completed planner
dependencies, the planner parent and the emitter, not invented per-step origins.
Novel reservation arithmetic is separate from this complete retained graph:
required prior dependency contexts/operations/final nodes and aliases already exist
in the same collector and are pinned by exact immutable key, without copying them.
Every prospective scope still checks actual existing usage plus all active remaining
reservations plus its own grant against unchanged global limits. The pipeline may
refuse even when a single isolated representation fits. Two old origin closures
are conservatively charged131072 bytes in the complete graph and must actually
measure within that guard; novel own-origin closure remains guarded65536 bytes.
There is no assumption that arbitrary caller references deduplicate.

The executed authored default-pipeline key model gives an explicit materialization
limit under the unchanged fixed grants: depth6/729 nodes/23documents leaves1102
aliases after planner completion; its following5120-alias emitter reservation
requires6222 and MUST refuse against6144 before target entry. This does not make
the complete inspectable depth6 plan invalid or authorize a smaller substituted
plan. Depth5/243nodes/8documents leaves495 aliases, plus5120=5615, so a substantive
nontrivial materializing representation fits. The modeled final depth5 graph has544
aliases. Actual current f431 foundation scopes were executed and completed; future
chain/planner/emitter alias keys were reconstructed from explicit references.
PIPELINE_ALIAS_PROOF.proposed.json records those exact keys and separately marks
unknown future runtime source4 admission/capture/target behavior. Runtime later
must reproduce the gate result, not assume this representation is an effect test. [YWE-REQ-0049]

Optional Core preplanning normalization is a separately captured actual operation,
retaining original TC diagnosis, actual NormalizationResult/first completion and
one fresh normalized diagnosis before this ALREADY_VALID runner. It adds real
origins/scopes/support/aliases to the two-origin witness. It requires its own
end-to-end charged closure and stage gate controls; it is not covered by or hidden
inside this unnormalized two-origin default pipeline certificate. The separate
executed H4 witness declares {0,C1,C2,C1 XOR C2}, original C4 is TC, real
normalization completes to0, and real fresh normalized diagnosis is the initial
runner origin, counted once. Ordered [C1,C1,C2,C2] has four actual pure VALID targets.
Its depth5 foundation has123 aliases, modeled completed planner506, following
emitter5120 grant requires5626<=6144, modeled final555. Depth6 completed planner1113
plus5120=6233 refuses by89. Every original diagnosis/normalization/first completion,
fresh initial/final diagnosis and safe member key is retained in the separate
pipeline proof. Measured individual H4 initial/final origin closure is3372 bytes;
full origin-plus-normalization union7331 bytes; complete raw normalization prefix
40507 bytes. Full512 default individual origin closure is9468 bytes and two-origin
union11025. These are executed finite witness sizes, not universal maxima. The
additional normalized prefix guard is one65536-byte originalTC origin allowance
plus131072-byte normalization scope allowance, total196608, separate from the two
initial/final65536 allowances. Actual global store/support usage and sequential
remaining reservations are checked; unused scopes are not assumed absent. The
frozen bound report separately charges this prefix and does not grant new quotas.

Full safe readback closure resolves every emitted plan/context/dependency, actual
record/dispatch/outcome, source/profile/policy, target/name/content and first/final
completion alias to its original immutable retained member or to explicitly
bounded unavailable evidence. The emitter isolated closure has seven producer
contexts (five dependencies, planner and emitter) and two actual N1 origins.
Class-owned lineage and actual ledger keys determine reuse; never array position,
matching caller text or a synthetic maximum specimen. Alias/readback/retention
failure is partial coverage and blocks following ordinary effects without rewriting
already observed target truth. Protected wrapper JSON and paired Markdown preserve
identical alias graph identities. The measured worst guarded origin closures,
current retained usage and prospective final observer must fit before ACK/effect.

CoreModuleLifecycle.execution_gate(exact_issued_ticket,collector) issues the exact
API-only CoreExecutionGate. The class-owned configuration(gate) returns the immutable
tuple(collector,operation_reference,source_binding,profile_binding,generation).
stage_grant(gate,stage) returns exact CoreStageGrant(operation_reference,stage,
generation,grant_sequence,status GRANTED/CANCELLED/UNAVAILABLE); capture_disposition
returns ACTIVE/SEALED/UNAVAILABLE. validate_issued_for_collector(gate,collector,
operation_reference) is pure exact cookie/original-self/metadata validation without
owner entry or IO. CoreExecutionGate.for_operation(gate,operation_reference,stage)
returns an exact privately issued child bound to the same original ticket, collector,
full source/profile and generation, with the exact registered child operation and
allowed stage group. The owner registers actual bounded child references before
issuance; there is no prefix or caller-text authentication. Maximum64 child gates
per ticket; copied/foreign children refuse. Runner child operation suffixes are
:source, :chain, :final, :destination, :topology, :axioms and :planner from its
maximum128-character operation; optional fresh normalized origin uses :normalized.
Original origin diagnosis references are registered explicit request facts. Emission
operation is separately explicit and all its fixed record slots share one child.
Current private ticket/generation/phase is checked by its owner
before each grant; maximum64 grants per ticket. Halt/stop seals before callbacks;
held token is UNAVAILABLE until SEALED, never revived ACTIVE. Original gates remain
for truthful late cleanup; copied/foreign/Session gates refuse before hooks.

The Core orchestrator performs grants outside pure module owners, before each public
normalization/provider/computation/capture stage. Pure finite kernels never call the
gate and mutate its counters. Collector tests token disposition before and after
each append/IO without owner entry under IO; one genuine cleanup finish remains
available after sealing. Runner calls the exact class-owned Core gate at SOURCE_ENCODING,
CHAIN, FINAL_DIAGNOSIS, DESTINATION_ENCODING, TOPOLOGY, AXIOMS and PLANNER before
each next computation and before initial capture admission. EMISSION_PREPARE gates
transfer/preflight; after each actual matching dispatch ACK, EMISSION_DISPATCH gates
its one target action grant. Token checks before/after dispatch capture prevent a
halt reentry from reaching the grant. Already granted finite pure computation or
target action may return late; no following capture/effect is authorized by its value.
Capture token reads/appends/first finish/final observer do not mint grants. The
fixed maximal Core run has26 grants: origin1; optional normalization validation/
capture/value/post4 and fresh normalized root1; cosmology1; optional realm access/
proposal2; source/chain/destination/topology/axiom/planner computation+capture12;
fresh final diagnosis1; pattern1; narrative evaluation/interpretation2; perception1.
Exact grant call-site ownership is Core direct run11, class-owned
StateModel.apply_normalization2 (NORMALIZATION_VALUE and NORMALIZATION_POST_CAPTURE),
and ReferenceGenerationRunner.run13 (six producer computation/capture pairs plus
fresh FINAL_DIAGNOSIS). Core does not pre-grant delegated calls. Runner.emit makes
one EMISSION_PREPARE grant before Diagnostics.prepare_emission; Emitter.emit makes
one grant before initial scope admission and one EMISSION_DISPATCH per actual
matching dispatch ACK. A depth5 eight-document emission therefore delegates1 to
Runner and9 to Emitter, total10. Core emit entry issues the ticket/child gate and
checks disposition; it does not duplicate those grants. Pure validation, token
reads, append/firstfinish/final observer/late cleanup create no additional grant.
The per-ticket owner cursor identifies each actual call phase, not only a repeated
stage name; duplicate/replayed/out-of-order phases refuse before following work.

A separate depth5 eight-document emission uses prepare1, initial emitter capture1
and eight EMISSION_DISPATCH grants after matching ACKs, total10. All target/collector
callbacks remain outside Core/emitter locks. A64 grant exhaustion
is a bounded refusal before following work; it is not silently reset or borrowed.

## 12. Proposed implementation ownership and acceptance

After exact owner adoption and issuance, the planner/emitter owner implements the
additive chain in realm_transition.py/realm_transition_values.py, the planner/emitter/
memory-target/runner files and values, seven copied source4 schemas, precise owner
wire_schema/source-selection controls and isolated pure/effect/boundary tests.
The Core owner implements Core domain/lifecycle and exact StateModel normalization
and gate seams; shared StateModel/state_values changes route through that owner.
The Diagnostics/Session owner implements current Session/Recovery integration,
scalar and native host source4 admission, exact collector capture/preparation and
safe projection/retention changes. Existing shared file edits route through their
assigned owner; no peer directly mutates another slice. Root owns canonical source
application, exports, governance/registers, examples/catalogs, composed acceptance
and publication. This list is proposed allocation, not issued implementation.

Before any dependent code, owner adoption records YWE-REQ-0049 / ADR-0041 and the
complete source/chain/PE/schema/safe package. A documentation-only adoption checkpoint
may accept the exact source4 extension pending application: the product canonical
runtime tree stays f431 until source4 changes and dependent admission/runtime are
issued together and independently checked. No source4 constructor/host/Git proof
is claimed merely from contract adoption. Original external proposal bytes remain
preserved. Ready-for-adoption copies carry their own actual status/requirement bytes
and recomputed policy hash in every binding, schema and authored specimen. Stable
path/API/version references connect Core and Session contracts without mutual
policy-bytehash cycles.

## 13. Acceptance and legacy preservation

Before implementation: owner adopts this exact policy/wire/safe/API/chain amendment,
requirement/ADR/Trace owners, exact byte hashes and proof; issues scoped paths.
Status-routing changes reconcile actual adopted policy bytes/hash without overwriting
this external proposal. The existing32 canonical blobs are preserved as historical
source inputs; only the two explicitly proposed normative source pages change.
Canonical mathematics,
legacy plan_generation signatures/output, old512/8192 tests and M2 schemas remain.
No M4/M5 implementation or subjective metaphysical measurement is included.

Controls include all0..4 chain lengths; nonzero reversal and actual candidate masks;
unknown/inapplicable/TC failed prefixes; current binding and original owner/result
copy/reflection/hostile-type purity; everydepth/729roles/23documents/reconstructible
path; all32axiom warnings and independent self flags; exact document bytes/hash/
readback/idempotence/conflict/resource refusal; zeroartifact no target call; every
dispatch ACK/reference/refusal/cancellation point; effects outside both locks;
late/partial/unknown target truth; first finish/final observer/cleanup once even
wrong admission reference; offline allcloseddefinitions/maxleaves/full combined raw
guards; existing helper/schema/catalog fixtures unchanged. Passing synthetic schema
proof does not replace actual future runtime controls or final normal M3 checks.
