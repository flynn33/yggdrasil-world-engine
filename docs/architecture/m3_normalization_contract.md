# M3 semantic normalization reference contract

Status: active N1 contract, adopted on October 4, 2026 after the verified first
StateModel slice `229cb78c1cbc1fea361f5592505e78d649187c30`. Owner and partition:
`ywe_core`. Requirement: `[YWE-REQ-0040]`. Decision: `ADR-0030`.

[YWE-REQ-0040] A conforming reference StateModel MUST satisfy the exact ownership,
planning, use-time validation, actual computation, immediate capture and retained
failure contracts below. It MUST preserve immutable explicit profile/source
bindings and the fixed canonical mathematics. It MUST NOT claim active-session
publication, operational recovery, complete Diagnostics or M3 acceptance from N1.
Python remains the platform-neutral reference oracle and testing implementation.

The independent external review of the adopted interface inventory has normalized
SHA256 `70209bbcf1da10748586a3a4c88eef24064667e0b0c1cfb3d6382d66ad4497e9`;
its matching machine inventory is `7a19434055eebc3a8121c65807083a662ad06c5b320d66caec72213a2517a301`.
Those review fingerprints identify the proposal that was read before adoption;
they do not assert that the following current contract or implementation has those bytes.

## Sources and scope

Canonical source root: `core/ash_pattern_engine/canonical`, dependency
`ash_cosmological_model.f2_9.canonical`, aggregate
`0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb`.
All 32 actual source pins were read and verified by `N1_CURRENT_SOURCE_AUDIT.py`.
N1 semantic owners are:

| Exact source | Sections / obligation |
| --- | --- |
| interfaces/contracts/state-model-contract.md | Canonical responsibility; Normalization; Required diagnostics: already-valid identity, compatible codeword correction, incompatible diagnostic failure, complete validity diagnosis for every attempt |
| core/state-admissibility.pseudo.md | Codeword orbits; Classifier: recognized states and full C orbit reachability |
| core/codeword-set.pseudo.md | Generators; Exhaustive enumeration; Subgroup; Downstream implementation constraints: exactly C16, fixed full vectors |
| algorithms/codeword-transformation-semantics.pseudo.md | Canonical transformation; Purity; Involution: actual full-vector XOR |
| core/state-validity-diagnostics.pseudo.md | Diagnostic record; Pseudocode; Completeness: retain complete original and actual-result diagnoses |
| interfaces/diagnostic-schema.md | Ten fields; Stage conventions; Chaining; No silent omission |
| interfaces/contracts/diagnostics-module-contract.md | Immediate capture, complete chains and conformance; full Diagnostics realization remains later work |
| interfaces/rule-id-taxonomy.md | Usage rules; Example rule IDs: source-defined ASH-CODEWORD-STRUCTURE-001 exists |
| verification/invariant-spec.md | INV-STATE-002/003; INV-CODEWORD-001..004; INV-DIAG-001..004; no severity decrease in recovery chains |

No `core/state-normalization.pseudo.md` exists in this pinned source tree. The
normalization owner is the StateModel contract, not an invented missing algorithm.
The source does not choose among multiple eligible recognized targets. The
identity-first / full-signature ordering below is an explicit local policy.

N1 supplies pure planning and actual immutable value computation. It does not own
operation admission, active state, a session commit, recovery routing, containment,
halt, fallback, operational SystemContext, STABLE classification or RECOVERED.
Legacy `normalize_bits` remains the adopted representation adapter.

## Existing-interface constraints observed at the first-slice baseline

- AshState, profile/source bindings, StateDiagnosis and all its records are owned
  immutable values. Exact built-in types and existing codec bounds remain in force.
- StateDiagnosis carries a complete original assessment/input/source/profile
  packet and one acknowledged detection record. StateAssessment and failure
  packets are distinct types and are not silently converted into StateDiagnosis.
- Available and unavailable profiles are distinct. An available empty profile
  yields NOT_NORMALIZABLE for every well-formed vertex; it is not unavailable.
- DiagnosticEnvelope already accepts all canonical kinds and stages. Its shape
  remains exactly ten fields. `_StatePacket._validate_emission` and
  `_RecordingAssessmentCapture.append` enforce first-slice DETECTION /
  CLASSIFICATION order and maximum two records; those owners are not N1 scopes.
- Existing `RULE_IDS` accepts six first-slice IDs and excludes the source-defined
  ASH-CODEWORD-STRUCTURE-001. N1 must adopt that canonical rule for its computation
  witnesses. This contract adopts extending common RULE_IDS by this exact ID, with a
  fixed ASSESSMENT_RULE_IDS containing the prior six IDs. `_StatePacket` must
  enforce the six-ID subset on original semantic diagnosis and every owned
  envelope, including a capture failure's attempted record through
  `_validate_emission`. N1 schema owns seven-ID operation envelopes; it may reuse
  old StateDiagnosis/semantic definitions, but not their six-ID operation envelope.
  First-slice producer/schema output remains unchanged. This explicit selection
  avoids a duplicate ten-field envelope owner and is adopted by this contract.
  Do not invent an ASH normalization policy rule ID or use a catch-all to conceal
  the available specific codeword rule. This is an explicit implementation delta.
- StateContractError has a closed first-slice code list and an empty emitted
  snapshot. New N1 structural codes should use a separately adopted
  NormalizationContractError, or an explicitly reviewed code-list extension;
  undocumented new strings cannot be passed into the current constructor.

## Fixed normalization policy

`YWE-NORMALIZE-LEXICOGRAPHIC-001`, revision `1.0.0`:

1. Compute the complete set T = recognized states intersect Orbit(original).
2. If original is recognized, select original unchanged, even when T contains a
   lower signature; record every eligible target and an empty codeword sequence.
3. Otherwise, if T is nonempty, select its smallest nine-character ASCII signature.
4. Otherwise no semantic normalization target exists.
5. A compatible correction uses the single full codeword original XOR target.

The single-codeword inference follows from fixed C being a subgroup: the sum of
any C chain is in C, and each reachable target has that unique difference. It does
not establish an upstream target ordering. The exact policy definition is
`docs/architecture/m3_normalization_policy.md`, with UTF8/LF SHA256
`804eec92cf52b465b7aaf0cb5f139f581ac2899d13203a8c4cfe9f4d7579c383`.
It is adopted before dependent reference implementation.

## Adopted API and ownership

Preserve the current three positional StateModel constructor parameters. Add an
explicit optional keyword collaborator `normalization_capture=None`; absence
means the N1 application capability is unavailable, not a hidden default/global
capture. The reference assembly must explicitly supply RecordingNormalizationCapture
when it intends to exercise semantic application. Existing assessment callers
remain compatible and continue using their separate diagnostic_capture.

```python
StateModel(profile_binding, canonical_binding, diagnostic_capture,
           *, normalization_capture=None)

StateModel.plan_normalization(diagnosis, *, plan_reference, evidence_reference,
                              policy_binding)
# exact StateDiagnosis -> immutable NormalizationPlan; pure, no application/capture
# foreign/forged origin -> NormalizationContractError with retained pre-plan comparison

StateModel.validate_normalization_plan(plan)
# -> owned NormalizationPlanValidation; rederives semantics from this model's
# current immutable bindings; pure; no validated flag permits skipping apply checks

StateModel.apply_normalization(plan, *, normalization_context)
# -> NormalizationResult | NormalizationFailure | NormalizationCaptureFailure;
# always revalidates at use
```

Pure planning and explicit plan validation do not require normalization_capture.
Only apply_normalization requires that collaborator and a NormalizationContext.
A missing application capability cannot prevent producing or independently
validating a portable plan under the model's current immutable bindings.

There is no candidate decoder in N1. Call the existing `diagnose` first, retain
its real StateDiagnosis, then plan. A diagnose capture failure cannot become an
acknowledged source diagnosis or a ready plan. This sequencing avoids the cycle
of requiring contextual correction knowledge before a correction path can exist.
Later correction-known evidence must be bound to whichever diagnosis is being
classified and to an actually revalidated plan; compatibility alone is not that
fact. N1 does not add a convenience facade that guesses evidence/context.

## Exact owned values

All arrays use exact list/tuple inputs copied to tuples, exact AshState members,
fresh record containers and exact enum strings. Existing identifier bounds
1..256 ASCII and explanation bounds 1..512 / 1..8 remain. No caller object hooks,
private class names, exception details, wall-clock timestamps or arbitrary metadata.

| Value | Exact owned constructor fields | Invariants |
| --- | --- | --- |
| NormalizationPolicyBinding | policy_id, policy_version, source_reference, source_sha256 | exact adopted policy revision/definition; no caller-selectable alternative policy |
| NormalizationPlan | plan_reference, evidence_reference, policy_binding, original_diagnosis, decision, eligible_targets_complete, eligible_targets, selected_target, codeword_chain, reason_code | exact original StateDiagnosis; structural branch rules below; no issuance token, validated bool or self-digest |
| NormalizationPlanValidation | plan, original_diagnosis, canonical_binding, profile_binding, origin_validation_status, validation_status, failure_code, field_name, expected_decision, recomputed_eligible_targets, recomputed_target, recomputed_codeword_chain | required exact original StateDiagnosis; optional plan only on early NOT_EVALUATED/REJECTED origin branches with null expected/recomputed facts; plan present requires original_diagnosis==plan.original_diagnosis; retains current model's complete immutable bindings and actual comparison evidence; this observation is not future-use authority |
| NormalizationContext | operation_reference, computation_reference, post_validation_reference | stable explicit refs; new diagnostic refs distinct from one another and inherited detection ref |
| NormalizationStep | step_index, input_state, codeword, actual_state | index exactly0; exact canonical codeword; constructor checks full-vector XOR; actual immutable states, not requested targets |
| NormalizationDiagnosticRecord | emission, phase, state_validity_diagnostic, step | exact existing DiagnosticEmission/envelope and complete nine-field semantic payload; phase COMPUTATION or POST_VALIDATION; reviewed consistency rules below |
| NormalizationContractError | code, field_name, submitted_plan=None, validation=None | dedicated ValueError; exactly four closed precondition/value codes; empty emitted snapshot; optional owned comparison retained; no successful wire packet |

Plan decision branches:

| Decision / reason | Complete eligible set | Selected target / chain |
| --- | --- | --- |
| ALREADY_VALID / NORMALIZATION_ALREADY_VALID | true; sorted unique T, maximum16, includes original | original; empty chain |
| PLAN_READY / NORMALIZATION_PLAN_READY | true; sorted unique nonempty T, maximum16 | smallest target; exactly one C member original XOR target |
| NOT_NORMALIZABLE / NORMALIZATION_NO_TARGET | true; empty T | null; empty chain |
| BLOCKED / NORMALIZATION_INPUT_REJECTED or NORMALIZATION_PROFILE_UNAVAILABLE | false; empty observations, not a claim that no target exists | null; empty chain |

Unavailable evaluation preserves a well-formed original AshState when one exists.
Only rejected representation has parsed_state=null. Do not discard the unavailable profile's original parsed state or mistake
absence of a new normalized output/target/proof for absence of an original state.
All selected-target and codeword fields are plans until actual application.

## Validation and provenance before use

The constructor owns structural types/width/bounds/order/uniqueness and decision
nullability. StateModel owns provenance and mathematical validation. At planning,
explicit validation and every application, check in this order:

1. Exact values/types and policy before semantic comparison. Application also
   checks its context and declared normalization capability before calling
   untrusted ports. Pure planning/validation never require that capability.
   Malformed configuration is an N1 typed precondition failure, no success.
2. Original diagnosis source binding equals every one of this model's fixed
   canonical fields. Its full ProfileBinding equals this model's full binding,
   including availability, source evidence and all recognized states; ID/hash
   equality alone cannot certify a substituted known-valid set.
3. Assessment/input references, parsed state and original diagnostic input agree.
   Preserve the original owned packet, evidence and detection envelope verbatim.
4. Independently rederive the original validity row and full orbit under current
   bindings. Check original row/orbit/rule/producer-envelope coherence. Metadata
   or a caller assertion of VALID/COMPATIBLE is not arithmetic evidence.
5. Recompute complete T (including all targets for an already-valid input), exact
   decision and identity-first/lex selection. Compare every candidate in order.
6. Recompute exact zero/one codeword chain, C membership and requested target.

The original semantic comparison is exactly the seven non-prose fields:
input_state, admissibility_status, transformation_compatibility,
normalization_status, recoverability_relevance, is_valid and orbit_info.
Compare the full owned input vector/rejected evidence and every OrbitInfo field,
including the minimum orbit signature, member_count=16 and actual known-valid
intersection; do not compare only the status label. The currently adopted
StateModel._diagnose/_DIAGNOSIS_RULES producer supplies the exact ordered rule
sequence ASH-STATE-STRUCTURE-001, ASH-ADMISSIBILITY-CLASSIFICATION-001,
ASH-STATE-VALIDITY-001. N1's verified-origin precondition requires that coverage,
without contextual classification/recovery or the new computation rule being
inserted into the original diagnosis.

Check the single original detection envelope's producer coherence independently:
STATE_VALIDITY / DETECTION; reference=root=assessment diagnosis_reference;
null parent; original vertex/input subject; severity/disposition INFO/RESOLVED
for VALID, WARNING/PENDING for TRANSFORMATION_COMPATIBLE, and ERROR/BLOCKED for
TRANSFORMATION_INCOMPATIBLE or UNCLASSIFIED. Envelope rule_ids equal the original
diagnosis's ordered rule_ids and envelope notes equal its notes. Notes remain
nonempty bounded owned explanatory text and summary remains bounded and one line.
Retain both verbatim; do not demand the current producer's exact English templates
or compare notes/summary to rederived prose as arithmetic evidence. This check
observes structural/semantic producer coherence, not external receipt truth.

Examples rejected before an application step: altered source/profile/assessment,
same profile ID/hash but changed recognized set, forged original validity row or
orbit, omitted/reordered/duplicated candidates, alternative higher target,
identity case selected lower target, invented C word, extra zero step and foreign
input. When a plan exists, rejected validation retains that full plan and the
observed comparison witness; it never repairs the submitted plan invisibly.
Apply cannot rely on a prior validation result or caller-produced validated flag.

Planning has a separate pre-plan origin refusal. For example, a real diagnosis
from an origin-only profile cannot be planned by a WRW model merely because both
have the same canonical source binding. A foreign source/full profile or forged
original diagnosis raises NormalizationContractError with code
NORMALIZATION_PLAN_INVALID, submitted_plan=null and an owned validation carrying
plan=null, the required submitted original_diagnosis, this model's current
canonical_binding/full profile_binding, origin_validation_status=REJECTED and
validation_status=REJECTED. Its underlying failure_code is
NORMALIZATION_BINDING_MISMATCH or NORMALIZATION_ORIGINAL_DIAGNOSIS_MISMATCH;
validation.field_name equals the exception's precise failed origin field.
All expected/recomputed fields are null. This is an observed rejected comparison,
not NOT_EVALUATED. No plan, operation context, capture scope, inherited prefix or
application result is invented. The public validate_normalization_plan method
accepts a submitted plan and always retains it; only pre-planning/precondition
witnesses may have plan=null.

There are two distinct refusal boundaries. If canonical/profile bindings or the
original diagnostic mathematics cannot be validated, the supplied diagnosis is
retained as submitted evidence, not accepted as an acknowledged chain root.
Return a pre-application plan_validation refusal with origin_validation_status=REJECTED,
inherited_diagnostics=(), emitted_diagnostics=(), no capture.begin call and no
application step. Recomputed facts stay null until they can be evaluated honestly.
This is a caller-contract/provenance rejection before the normalization attempt
starts; it cannot produce a RECOVERY child attached to an unverified root.

Only after original provenance/mathematics pass may origin_validation_status be
VERIFIED and its producer-contract detection prefix be inherited. Later
target-set/selection/codeword validation failures may emit the immediate refusal
under that verified origin. Keeping this boundary explicit prevents accepting a
forged complete-looking StateDiagnosis as historical acknowledgement evidence.

A portable immutable diagnosis/plan does not cryptographically prove that a
remote collector acknowledged a historical record. Inherited confirmation comes
from the explicit trusted StateDiagnosis producer/capture contract. There is no
generic JSON-to-confirmed-diagnosis importer in N1. Source-file freshness and
actual collector truth remain composition/publishing checks, as in the adopted
first slice; do not claim newly verified IO from constructor metadata.

Validation witnesses require the submitted original_diagnosis even when no plan
exists, and retain current model bindings separately from submitted plan/origin
bindings, so a source/profile mismatch is observable without falsely
relabeling the submitted diagnostic as a current-model diagnosis. Before canonical
binding/original diagnosis checks pass, expected_decision and recomputed collections
are null (not evaluated); after complete mathematical evaluation, collections use
actual tuples, including an honestly computed empty tuple. These fields cannot
turn an unevaluated comparison into a claimed empty target set.

Origin status is a runtime comparison observation, never authentication of a
historical receipt. Exact cross-field rules:

- NOT_EVALUATED: a precondition declined before origin comparison (for example
  missing normalization capability or invalid policy). Overall status REJECTED;
  failure code is the corresponding four-code structural precondition code;
  expected decision and all recomputed fields are null. No inherited prefix,
  scope, append or application. A typed precondition exception may carry this
  partial owned validation when an exact submitted original_diagnosis is
  available. plan may be null before planning; when a structurally valid plan is
  retained, original_diagnosis must equal plan.original_diagnosis. Missing
  normalization capability applies only to application, never pure planning.
- REJECTED: an actual source/full-profile/original-diagnosis comparison failed.
  Overall status REJECTED, failure code NORMALIZATION_BINDING_MISMATCH or
  NORMALIZATION_ORIGINAL_DIAGNOSIS_MISMATCH, expected/recomputed fields null;
  no inherited prefix or capture/application calls. plan may be null only before
  planning. A submitted plan is always retained for explicit validation or apply,
  and its original_diagnosis must equal the witness's original_diagnosis.
- VERIFIED: source/full-profile/original diagnosis checks passed. Overall status
  VALIDATED has null failure_code/field_name and the exact expected decision;
  overall REJECTED names the later target/selection/codeword mismatch and its
  observed expected values. Ready/already-valid/incompatible branches carry a
  completely recomputed tuple of targets (possibly empty). BLOCKED carries
  expected_decision=BLOCKED, recomputed_eligible_targets=null and no target/chain
  computation, preserving the distinction between unknown and empty. Only this
  status permits the origin prefix to be inherited. A nonnull plan is required,
  with equal original_diagnosis. Apply rederives it every time.

The two origin mismatch codes have exact local field mappings.
NORMALIZATION_BINDING_MISMATCH names original_diagnosis.source_binding or
original_diagnosis.profile_binding. NORMALIZATION_ORIGINAL_DIAGNOSIS_MISMATCH
names the evaluated inconsistent assessment_binding, input_evidence,
parsed_state, state_validity_diagnostic or emitted_diagnostics path under
original_diagnosis. These are fields of the retained submitted packet; current
model bindings remain separate. No unevaluated target/selection/codeword failure
can stand in for an origin mismatch.

## Capture protocol and immediate sequence

Use a new owner. Do not call or widen RecordingDiagnosticCapture's assessment
scope for normalization. Adopted protocol:

```python
NormalizationCapture.begin(operation_reference, *, original_diagnosis)
# -> normalization-scoped capture with explicit inherited detection prefix
NormalizationScope.append(record: NormalizationDiagnosticRecord)
# -> the existing three-status CaptureReceipt for record.emission reference
```

Seeding retains the exact original immutable detection prefix. It does not append
that record again, manufacture a receipt, count it as a new acknowledgement or
query the adapter's storage. A scope starts with zero newly acknowledged records.
Expose `inherited_diagnostics` separately from `emitted_diagnostics`; a complete
view is their concatenation. The original diagnosis remains separately nested.
Only a returned and reference-checked CONFIRMED receipt extends the new prefix.
Seeding is permitted only after current origin binding/mathematical validation
passes; early origin refusals never open this scope or claim an inherited prefix.

For an admissible ready/already-valid plan:

1. Validate before the application step. Open the new scope before computation,
   then check that the returned value satisfies the declared NormalizationScope
   interface with a callable append port. None, a non-scope value or a missing /
   noncallable append port is a malformed begin result. Refuse it before XOR or
   any application step, with the same retained intended blocked COMPUTATION
   record and NOT_CONFIRMED boundary as a begin exception. Checking this interface
   does not call append or assert that future receipts will be truthful.
2. Compute actual full-vector XOR for PLAN_READY, yielding an immutable AshState
   and one observed step. ALREADY_VALID uses the original unchanged and zero
   steps; it must not claim application of the zero codeword.
3. Immediately append the COMPUTATION record: STATE_VALIDITY / RECOVERY, parent
   inherited detection, root inherited detection, subject original vertex/input
   reference, original complete validity diagnostic, and actual step when present.
   This record reports value computation, not successful operational recovery.
   Its disposition is PENDING while actual-result validation is outstanding.
4. Only after acknowledgement, re-diagnose the actual state under the same full
   profile/source. Immediately append POST_VALIDATION: STATE_VALIDITY / RECOVERY,
   parent computation ref, same root/subject, complete actual-result diagnosis
   and the observed step. It does not reset stage to DETECTION or rewrite original.
5. Publish normalized_state only when actual == selected target, actual diagnoses
   VALID and both new records are acknowledged. The successful POST_VALIDATION
   disposition is RESOLVED; a failing actual-result check uses BLOCKED, even when
   its diagnosis is VALID but the actual value differs from the requested target.
   No session is modified.

Both records reuse the exact ten-field envelope. Kind STATE_VALIDITY is deliberate:
N1 does not possess the canonical RecoveryDiagnostic's original system class or
executed recovery category. Kind RECOVERY must not pretend that incomplete N2
content is a complete RecoveryDiagnostic. STATE_VALIDITY at RECOVERY with an
attached original/post validity payload is an adopted local phase mapping; canonical stages permit correction at RECOVERY.

Severity is nondecreasing from inherited detection through the new chain. A valid
post diagnosis does not reset an inherited WARNING/ERROR envelope to INFO.
Successful post validation uses RESOLVED while preserving that prior severity.
Reason/rule/summary content describes the value operation only. Relevant rules:
ASH-STATE-STRUCTURE-001, ASH-ADMISSIBILITY-CLASSIFICATION-001,
ASH-STATE-VALIDITY-001 and ASH-CODEWORD-STRUCTURE-001 in actual evaluation order.

[YWE-REQ-0040] Confirmed computation preceding POST_VALIDATION MUST be PENDING, never a BLOCKED
refusal. Result and post-validation failure constructors MUST preserve that phase
distinction. A capture failure with an acknowledged computation prefix MUST retain
validated ready/already-valid planning, actual one/zero steps respectively, and a
PENDING computation; refusal branches cannot advance to POST_VALIDATION.

NOT_NORMALIZABLE/BLOCKED plans produce one immediate RECOVERY/BLOCKED refusal
record with the complete original diagnosis, null step/normalized output, original
parsed state if present and explicit reason. A semantic validation mismatch found
at apply produces a retaining failure/refusal before the application step.
There is no post-validation record when no result was computed.

## Outcomes and exact wire boundaries

Use new standalone local schema IDs; do not broaden the assessment/M2 schemas:

- plan schema_ref `data/schemas/m3_normalization_plan_schema.json`, artifact_type
  `ywe_state_normalization_plan`, artifact_version `1.0.0`.
- result schema_ref `data/schemas/m3_state_normalization_schema.json`, artifact_type
  `ywe_state_normalization`, artifact_version `1.0.0`.

Plan wire has those three headers plus exactly the ten NormalizationPlan fields
above. Owned states use the existing {state_space:F2^9,bits:[9]} record, not IDs as
substitutes. original_diagnosis embeds the unchanged existing StateDiagnosis packet.

Serialized application plan_validation always contains a nonnull submitted plan,
and its original_diagnosis equals both plan.original_diagnosis and the result's
original_diagnosis. Its plan equals the result's plan. The plan=null witness is
retained only by a planning/precondition exception and is not an application wire
alternative; no new outcome packet is needed for that boundary.

Every result/failure has the three result headers and these exact common fields:
`outcome, operation_binding, plan, plan_validation, original_diagnosis,
actual_state, steps, post_validity_diagnostic, normalized_state,
inherited_diagnostics, emitted_diagnostics`.
operation_binding contains the exact NormalizationContext record. `steps` is zero
or one real observed step; emitted_diagnostics is zero, one or two newly confirmed
NormalizationDiagnosticRecords. inherited_diagnostics is the one verified origin
record once an attempt starts, or empty for the early invalid-origin refusal.

| Result alternative | Additional fields / evidence |
| --- | --- |
| NormalizationResult, outcome ALREADY_VALID | no additional keys; actual_state==original==normalized_state, zero steps, complete VALID post diagnosis, exactly2 new confirmations |
| NormalizationResult, outcome NORMALIZED | no additional keys; one actual XOR step, actual_state==selected target==normalized_state, complete VALID post diagnosis, exactly2 new confirmations |
| NormalizationFailure, outcome NOT_NORMALIZABLE or BLOCKED | failure_kind=semantic, failure_code, failed_field; null normalized/post result, zero steps, actual_state=original parsed state or null, exactly1 newly confirmed refusal |
| NormalizationFailure, outcome FAILURE, failure_kind=plan_validation | failure_code, failed_field; original-binding/math failure: retained submitted diagnosis and empty inherited/new prefixes with no capture scope or application; later target/selection/codeword failure after verified origin: one inherited record and exactly1 newly confirmed refusal, no application step |
| NormalizationFailure, outcome FAILURE, failure_kind=post_validation | failure_code, failed_field; retains actual step/result and complete failing post diagnosis, both records confirmed, null normalized_state |
| NormalizationCaptureFailure, outcome FAILURE, failure_kind=diagnostic_capture | failure_code, failed_field, capture_status, attempted_diagnostic; new confirmed prefix0/1 plus full attempted record, actual computations/post diagnosis retained if completed, null normalized_state |

Exact constructor inventories: NormalizationResult owns the eleven common fields
above, with outcome restricted ALREADY_VALID/NORMALIZED. NormalizationFailure owns
those eleven plus failure_kind/failure_code/failed_field, with the semantic,
plan_validation and post_validation alternatives described in the table.
NormalizationCaptureFailure owns the ten common fields excluding outcome plus
failure_code/failed_field/capture_status/attempted_diagnostic; outcome=FAILURE and
failure_kind=diagnostic_capture are fixed class discriminators. Headers are fixed
class values on every result. Branches prohibit keys belonging to another failure.

Exact first-slice packet headers/shape remain unchanged. No N1 packet has
system_context, system_state_class, recovery_category, committed_state, RECOVERED
or a bool claiming a collector acknowledgement without a real receipt.

Capture failures preserve both inherited and newly acknowledged prefixes.
Matching REJECTED guarantees no append of that exact record. Throw before/after
append, wrong ref, malformed receipt and NOT_CONFIRMED all yield NOT_CONFIRMED;
the possible external append is not queried/replayed into a confirmation.
Computation may have succeeded as a value before capture failed; retain actual_state
and step as observations, but normalized_state stays null. A scope-begin failure
occurs before application and retains an intended complete blocked record with
phase COMPUTATION/null step; it must not claim the codeword executed. A malformed
begin result (including None/non-scope) uses that same before-computation branch,
not an append failure after avoidable computation.

## Stable N1 codes and finite limits

NormalizationContractError is a dedicated ValueError subclass. Its constructor is
`NormalizationContractError(code, field_name, *, submitted_plan=None, validation=None)`.
Its code set is exactly these four precondition/value codes:
NORMALIZATION_CONFIG_INVALID, NORMALIZATION_CONTEXT_INVALID,
NORMALIZATION_POLICY_INVALID, NORMALIZATION_PLAN_INVALID. It owns an empty
emitted_diagnostics tuple; optional submitted_plan/validation are exact immutable
N1 values or null, with no input hooks or partial malformed values retained.
Optional validation has exactly two permitted exception branches:

- Precondition refusal: origin NOT_EVALUATED, overall REJECTED, failure_code and
  field_name equal the exception's code/path, and every expected/recomputed field
  null. submitted_plan equals validation.plan, which may be null before planning.
  The required original_diagnosis is retained; if plan is nonnull, it equals
  plan.original_diagnosis. With no exact owned original diagnosis available,
  validation is null rather than a partial malformed object.
- Evaluated pre-planning origin refusal: exception code
  NORMALIZATION_PLAN_INVALID, submitted_plan=null, validation.plan=null,
  origin REJECTED and overall REJECTED. Retain the exact submitted
  original_diagnosis and current model canonical/full-profile bindings. Inner
  failure_code is NORMALIZATION_BINDING_MISMATCH or
  NORMALIZATION_ORIGINAL_DIAGNOSIS_MISMATCH using the exact origin-field mapping
  above; inner field_name equals the exception's field_name. All expected /
  recomputed fields are null. The differing inner code is intentional: the
  exception names the failed planning contract, the observation names the actual
  rejected comparison. No capture or application occurred.

Other evaluated-origin exception combinations are forbidden. When validation is
null, submitted_plan may still retain an exact structurally valid plan, or be null
when none exists. An exception is not a successful packet and has no successful
to_record operation. Error construction cannot claim VERIFIED origin or retain a
validation for a different submitted plan / original diagnosis.

`field_name` is a closed local interface-path enum, not caller-supplied arbitrary
text and not an upstream taxonomy. Its authority is this adopted constructor /
packet inventory. Exact permitted paths are: normalization_capture,
normalization_context, policy_binding, plan, plan_validation, plan_reference,
evidence_reference, decision,
original_diagnosis, original_diagnosis.source_binding,
original_diagnosis.profile_binding, original_diagnosis.assessment_binding,
original_diagnosis.input_evidence, original_diagnosis.parsed_state,
original_diagnosis.state_validity_diagnostic,
original_diagnosis.emitted_diagnostics, eligible_targets_complete,
eligible_targets, selected_target, codeword_chain, reason_code, step_index,
input_state, codeword, actual_state, phase, emission, emission.envelope,
emission.envelope.rule_ids, emission.diagnostic_reference,
operation_reference, computation_reference, post_validation_reference,
inherited_diagnostics, emitted_diagnostics, steps, post_validity_diagnostic,
normalized_state, origin_validation_status, validation_status, failure_code,
field_name, expected_decision, recomputed_eligible_targets, recomputed_target,
recomputed_codeword_chain. Exceptions and failure values use this same closed
path list; no external key, exception string or class name becomes a field path.
Also permitted, directly from the declared constructor/packet fields:
policy_binding.policy_id, policy_binding.policy_version,
policy_binding.source_reference, policy_binding.source_sha256,
canonical_binding, profile_binding, state_validity_diagnostic, step,
outcome, operation_binding, failure_kind, failed_field, capture_status,
attempted_diagnostic, submitted_plan and validation. This list is closed rather
than a grammar accepting arbitrary new descendants. Unknown code/path, wrong
optional types or a validation referencing a different submitted plan rejects
the error object's construction with a fixed ValueError; do not recursively build
another invalid NormalizationContractError or echo the supplied bad string.

Retaining runtime validation codes, distinct from the four exception codes:
NORMALIZATION_BINDING_MISMATCH, NORMALIZATION_ORIGINAL_DIAGNOSIS_MISMATCH,
NORMALIZATION_TARGET_SET_MISMATCH, NORMALIZATION_SELECTION_MISMATCH,
NORMALIZATION_CODEWORD_MISMATCH. Semantic codes: NORMALIZATION_INPUT_REJECTED,
NORMALIZATION_PROFILE_UNAVAILABLE, NORMALIZATION_NO_TARGET,
NORMALIZATION_POST_VALIDATION_FAILED. Reuse the explicit receipt pairing
DIAGNOSTIC_CAPTURE_REJECTED / DIAGNOSTIC_CAPTURE_UNCONFIRMED in capture outcomes.
All codes are downstream transport identifiers, not canonical ASH rule IDs.

Bounded values: targets0..16, codeword chain0..1, actual steps0..1, inherited
records0..1 (zero only for pre-application invalid-origin refusal), new records0..2,
semantic/envelope fields exactly9/10, notes1..8
of1..512, summary1..512 one line, existing identifier1..256. Frozen original
packet keeps existing profile0..512, input observation0..9 and codec limits.
Runtime checks own cross-field references, complete eligibility, full-profile
equality, actual XOR, policy choice, original/post mathematics and capture truth.
Wire schema owns closure, exact alternatives, bounds, types and outcome consistency;
schema validity alone does not establish mathematical or acknowledgement facts.

## Independent execution and remaining M3 scope

The reviewed expectations cover all 512 vertices under each explicit WRW, origin,
empty and multiple-target profile. Expected ALREADY_VALID/NORMALIZED/NOT_NORMALIZABLE
counts are respectively 9/135/368, 1/15/496, 0/0/512 and 3/13/496. These are case
expectations, not a claim that implementation execution passed. Synthetic profiles
are validation-only. Actual planning maps expected NORMALIZED to PLAN_READY.

[YWE-REQ-0040] Implementation verification MUST execute all 2,048 cases with an independent
codeword/generator and arithmetic oracle. It MUST exercise rejected input,
unavailable profiles while retaining parsed originals, all sixteen eligible
targets, invalid origin/profile/source/proof, changed complete profile data under
unchanged identifiers, repeated planning/application, mutation and hostile hooks.
Capture tests MUST exercise begin throws and malformed scope results, plus each
append refusal, throw before/after, missing/malformed/wrong-reference receipt.
They MUST verify actual zero/one steps, complete original and post diagnoses,
confirmed-prefix counts, exact attempted records, RECOVERY parent/root/subject
links and nondecreasing severity. No normalized output is permitted before all
required confirmations. Invalid origin must prove zero capture and application
calls while retaining the submitted packet and current-model comparison.

[YWE-REQ-0040] Independent positive wire packets and intended-keyword/location rejections MUST
validate both new schemas. Existing assessment/M2 format, facade identity and
mathematical safeguards remain applicable. Expected-artifact integrity does not
replace execution. Full Diagnostics, recovery/fallback/containment/halt/session
behavior, generation, canonical byte serialization, lifecycle, core placeholders
and the unchanged five M3 exit criteria remain subsequent obligations.
