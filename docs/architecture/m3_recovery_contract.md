# M3 immutable recovery values and reference Diagnostics contract

Status: active N2 contract, adopted October 4, 2026 before dependent implementation. Owner and partition: `ywe_core`. Requirements: [YWE-REQ-0041] and [YWE-REQ-0042]. Decision: ADR-0031. Read against frozen N1 implementation `5328f018f341b80ad58cdb82f64708992ee2d6ae` and publication checkpoint `4c01af5b01b4690da5cd2a97d5e6025e97a48e1c`. Implementation, executable acceptance, milestone completion and native qualification remain incomplete. The exact Core field/API authority is the appendix below; the Diagnostics authority is [its separate adopted inventory](m3_reference_diagnostics_contract.md#exact-interface-inventory).

## Bounded implementation scope

N2 provides Core reference RecoveryEngine immutable-value operations, a canonical-structure FallbackRegistry, and a cohesive bounded reference Diagnostics collector with actual protected local host storage and paired JSON/Markdown export. It executes actual full-nine-bit XOR values and full contextual postassessments. It emits completed-action RecoveryDiagnostic records, retains every attempted candidate and refuses missing evidence. It returns typed requests for containment, external authority or safe halt. It performs no live-session commit, native state transition, mode entry, authority communication or product integration.

The next N3 owner is required before RecoveryEngine module acceptance or any M3 criterion acceptance. N3 must own session admission, operation/mode permissions, live state commit, containment restricted-operation subset and resolution, safe halt entry/frozen chain and denied-attempt audit. No N2 handoff is labelled a canonical ContainmentDiagnostic or SafeHaltDiagnostic: their source fields assert actual CONTAINED/SAFE_HALT entry. Neither capture acknowledgment nor a constructor certifies that entry. M3 remains in progress; native Development/Release Diagnostics replacement and product Release-artifact qualification remain M10/downstream work.

Adopted implementation allocation: core/ash_pattern_engine/recovery_values.py, recovery.py, fallback_registry.py, diagnostics_values.py and diagnostics.py; StateModel gains narrow pure owned validation ports. Windows IO/protection and user-invoked export belong scripts/reference_diagnostics_host.py, injected through a platform-neutral port. Existing first-slice/N1 API, packet headers and schema IDs remain distinct; no planner, registry transition or client framework is inferred.

## Evidence and source precedence

The canonical recovery-engine contract requires known codeword recovery, full STABLE postclassification, deterministic registry selection, diagnosable mutations, containment/halt and monotonic escalation. Recoverability has exact seven class/category pairs and a blocked-path table. The registry has exactly seven entry fields, rank then policy-ID order, conjunctive applicability, known-good nine-bit targets, full STABLE validation and entry-owned TRY_NEXT/ESCALATE_TO_CONTAINMENT. No actual populated fallback dataset is supplied by the source; authored examples are explicit downstream input data, not hidden upstream defaults.

Concrete tensions and their adopted resolutions are recorded in docs/architecture/m3_recovery_safety_policy.md, with source ownership preserved: specific entry TRY_NEXT overrides generic first-candidate failure pseudocode; full STABLE overrides is_valid-only postcheck; blocked normalization contains while blocked correction takes an explicitly separately named after-correction-failure fallback route; the original CORRECTABLE class is retained. Normalization-blocked entry uses an actual local policy request under canonical OPERATOR_REQUEST and request_origin=POLICY rather than fabricating a canonical trigger. Capture/meta metadata stays outside the unchanged TEN envelope. A postassessment keeps its own detection root rather than regressing/reparenting the main recovery chain.

No codeword order, target heuristic, validity anchor, registry entry, context flag, physical propagation decision, external-authority reachability or timestamp is guessed. Full fixed source pins and reviewed source bytes are independently verified before adoption/publication, as in the existing reference assembly boundary. Core constructors check exact reviewed bindings and copied values; they do not read the filesystem per call or claim runtime source-byte verification.

## Owned origin verification before capture or effects

RecoveryEngine accepts the exact existing StateAssessment type, not a diagnostic row plus free class/category strings. Its constructor requires one exact current StateModel, registry, Diagnostics port and explicit correction/evaluator/post-facts ports; no dependency supplies a default stable context or guessed route. The first operation is StateModel.validate_assessment(submitted), a pure method with no codec, capture, provider call, mutation or registry lookup.

StateModel itself must recompute the submitted parsed state under its complete current profile and fixed canonical codeword relation. Verification covers all seven mathematical diagnostic fields (input_state, admissibility_status, transformation_compatibility, normalization_status, recoverability_relevance, is_valid, orbit_info), exact ordered producer rule IDs, complete current source/profile binding, bounded input evidence and subject/reference coherence. It checks both predicate bindings even when unconsulted. It independently applies halt > containment > VALID > compatible/known-correction > incompatible/fallback > UNCLASSIFIED precedence, exact consulted predicate requirement, class/category pair, both complete emitted record references and detection/classification rule/impact coherence. Notes are bounded/nonempty and detection-envelope notes must equal the original diagnostic notes; generated English is not a mathematical oracle. A shape-correct forged class, reordered/missing rules, altered orbit, stale profile, wrong subject or unconsulted predicate binding cannot become an accepted origin.

AssessmentValidation retains the complete submitted assessment, current source/profile, computed expected diagnosis/class/category/consulted facts where available, and exact closed failure/path. VERIFIED is an output of the trusted owned method, never an input certification token accepted from callers. The bounded InputEvidence observation cannot authenticate unavailable original raw bytes; this validation certifies the submitted owned observation and parsed-state semantics, not an unseen original packet.

Origin rejection returns a retained failure observation before a recovery scope is opened. It does not manufacture an origin diagnostic, seed an inherited-confirmed prefix or append to an unverified chain. Structurally invalid dependency/context inputs raise closed RecoveryContractError before effects; semantically invalid exact owned origins return ORIGIN_REJECTED with the actual comparison witness.

After owned semantic verification, Diagnostics must attach the exact same collector's two already confirmed original records. A producer packet's emitted_diagnostics array is reported evidence, not proof of actual collector acknowledgment. Missing/mismatched/detached origin refuses admission; the collector never re-appends origin records or infers confirmation from equality alone. The origin's context observation must equal its actual SystemContext, and operation/context/propagation/authority evidence bindings must name the exact operation/origin.

Reserve the conservative complete transaction budget before provider/evaluator/value steps: no more than768 new records including all linked postassessment pairs, with incident/alias/byte quota. Refusal reserves a bounded health/nonconformance channel rather than a recursive logger. An existing contained/halted context stops recovery effects; denied attempts use a separately correlated audit trail and preserve the original incident.

## Actual value action flow

The source class/category map is immutable: STABLE/NO_ACTION; UNSTABLE/NORMALIZE_STATE; CORRECTABLE/APPLY_CORRECTION; DEGRADED/FALLBACK_REQUIRED; CONTAINED/CONTAINMENT_REQUIRED; FAILED/ESCALATION_REQUIRED; SAFE_HALT/TERMINAL_NO_RECOVERY. No alternate class is synthesized from a desired route.

NO_ACTION returns the verified unchanged candidate with a completed NOT_APPLICABLE decision; it does not claim recovered value or live commit. Existing CONTAINED/SAFE_HALT returns a boundary handoff without recovery replay. For existing SAFE_HALT, RecoveryCapture.begin_denial requires the exact same collector origin and returns a separate DenialScope/admission tuple. It reserves one new audit event plus fixed supporting/incident/alias bytes. Append exactly one OPERATION_DECISION RecoveryRecord with fresh operation_reference+:denied root, STATE_VALIDITY/DETECTION, CRITICAL/BLOCKED, parent null/root self, ASH-STATE-GENERAL-001 then ASH-RECOVERY-ACTION-001. Its full canonical nine-field payload is NOT_APPLICABLE under original SAFE_HALT/TERMINAL_NO_RECOVERY and the action wrapper retains REMAIN_SAFE_HALT/ExistingModeBoundary directive. It never appends or reparents into the frozen origin chain. DenialScope.finish checks the actual boundary/failure packet has no steps/posts/registry/provider effects; failed audit capture retains the full attempted record separately. Registry snapshot/validation are null on paths that do not consult it, with no fake inspection. FAILED produces an external-authority directive; explicit UNREACHABLE evidence requests safe halt under ESCALATION_FROM_FAILED. UNAVAILABLE is not silently called unreachable. N3 owns actual authority contact, halt policy/entry and mode observability.

Before normalization/correction/fallback, explicit SAFE propagation evidence is required. RISK or UNAVAILABLE requests containment without the first value step, retains the exact supplied evidence, and emits the required refusal decision. This is a local policy interpretation of the source's no-assumed-safety rule; it does not claim a real physical propagation model.

NORMALIZE_STATE reuses the adopted N1 pure plan and proof policy through public StateModel ownership. It does not call N1.apply_normalization and reparent its already acknowledged records. The normalization choice remains the adopted lexicographic complete-target proof; no new N2 target tie-break is introduced. Engine-owned actual XOR value replay retains the whole before/codeword/after state, confirms each immediate step event, then invokes actual contextual postassessment. For actual coherent UNSTABLE, complete T is nonempty and the owned N1 pure plan is always PLAN_READY. The abstract no-mathematical-path source branch is therefore unreachable under this frozen finite model and must not be exercised by a forged UNSTABLE/noT input. A narrow required NormalizationResolutionProvider returns complete READY StateModel-owned N1 proof or explicit UNAVAILABLE boundary observation with exact source/reference/reason. The adopted local safety policy maps only that typed unavailable resolution to blocked-normalization containment; None, throw or malformed proof remains collaborator failure. Reference provider uses actual StateModel and always READY for coherent UNSTABLE. The complete resolution/proof is retained, and independent controlled unavailable-port routing tests do not claim mathematical absence. No fabricated RECOVERY_VALIDATION_FAILURE is used before an action completed.

APPLY_CORRECTION obtains the caller's explicit KnownCorrection or UnavailableCorrection. It never replaces a missing known sequence with freshly computed N1 normalization. KnownCorrection contains full source evidence, the original known-path predicate evidence reference, exact original assessment/profile,0..16 submitted whole-nine-bit declared codewords and expected full target. Its constructor owns width/types/copying; StateModel owns canonical C membership. Empty/identity sequences are structurally representable; StateModel's pure validate_known_correction checks every member, exact full XOR, current target VALID and canonical source/profile/origin match. The full canonical_binding is compared to the current model; generic external provider source_reference/hash is declared retained provenance, not authenticated authority. provider_source_verification=DECLARED_NOT_AUTHENTICATED records that limit. An invalid current origin returns a precise early CorrectionValidation rejection with the complete rejected AssessmentValidation and null target facts. An actual CORRECTABLE empty/identity-only sequence cannot pass a VALID-target proof. Missing/bad known proof creates a completed BLOCKED correction decision; postfailure creates RECOVERY_FAILED. Before a fallback attempt, preserve the failed whole-action diagnostic and issue the explicit after-correction-failure route witness. A completed normalization RECOVERY_FAILED action with the full observed non-STABLE/wrong-target postassessment may similarly use the separately named AFTER_NORMALIZATION_FAILURE route, retaining UNSTABLE. This route never accepts BLOCKED normalization, which still requests direct policy containment. The same failed correction is never replayed again.

Successful and unsuccessful paths retain NormalizationPreparation with the full N1 original-diagnosis projection, fixed policy, plan, full validation and any typed planning error, and CorrectionObservation with the full supplied sequence/unavailability and validation. No proof survives only as a reason string. StateModel.diagnosis_from_assessment is an explicit pure validated projection of the already confirmed original detection record for N1 planning; it emits nothing and never asserts a new acknowledgment.

No RecoveryEngine peer copies the classifier or reaches into StateModel private helpers. Pure inspect_state and correction/assessment verification remain StateModel-owned. Known sequence proof and N1 proof are inspections, not falsely acknowledged recovery events. A trusted dependency failure is retained as COLLABORATOR_FAILED; it is not converted to a successful plan.

## Registry ownership and candidate evidence

FallbackRegistry accepts one immutable AVAILABLE or UNAVAILABLE snapshot. AVAILABLE may have zero entries, distinctly from missing registry data. The exact seven canonical FallbackPolicyEntry fields are preserved. The local condition-reference representation, immutable source binding, maximum 32 entries and 8 conditions in each phase are explicit adoption decisions. Policy IDs use bounded uppercase domain plus001..999 sequence; duplicate IDs are rejected. The constructor copies one immutable snapshot and provides no registry-reload or ID-reassignment API. It cannot prove unseen historical global ID ownership from a current source declaration; external governed registry history remains the dataset owner's obligation, with no upstream populated dataset invented here. ordering_rank is exact signed64 integer, bool excluded, including negative ranks. Input arrays are copied and all candidates inspect as current-profile VALID under the full canonical model before the snapshot is accepted. AVAILABLE wrapper includes candidate_certifications in entry inputorder, exactly one policy-ID-correlated complete StateAssessment plus ContextObservation per entry. Current StateModel pure revalidation must verify its full source/profile/subject/predicates/class, target equality and STABLE under the supplied explicit context. It is source-reported semantic certification, not a physical-mode or collector-ACK proof. Empty AVAILABLE has zero entries/certifications, distinct UNAVAILABLE. Fresh actual postassessment remains mandatory at use. Complete source snapshot and RegistryValidation comparisons are retained on the result, not only its hash. Registry retains its complete constructor profile and source; RecoveryEngine compares all current fields including the complete recognized-state collection, not just ID/hash, and re-inspects every AVAILABLE target at use. Foreign same-ID/hash profile contents are rejected before capture/effects.

The canonical direct get_candidates(origin_DEGRADED) interface remains DEGRADED-only. A separately named get_candidates_after_correction_failure(origin_CORRECTABLE, authorization) checks exact prior failed action decision, original class/category and allowed BLOCKED/RECOVERY_FAILED outcome before applying the same registry algorithm. The separately named get_candidates_after_normalization_failure admits only UNSTABLE with completed normalization RECOVERY_FAILED and complete observed postassessment, never blocked normalization. No class/category/diagnostic is relabelled and no registry condition/ordering/validation rule is bypassed. Public FallbackRegistry.validate_for_model(current_model) returns the complete RegistryValidation at use; public immutable snapshot/profile_binding/canonical_binding properties avoid private access. Constructor semantic refusal raises RecoveryContractError with that complete validation witness.

Direct DEGRADED registry binding rejection precedes initial recovery admission and every provider, predicate or value effect. A registry first consulted after an actual completed failed correction or normalization is revalidated before the first fallback predicate, selection or value effect; rejection retains that earlier admitted scope, actual steps and failed action. Successful correction and normalization do not consult an unused registry. This timing distinguishes the first direct admission boundary from the later route boundary without erasing prior work.

Sort all entries deterministically by (ordering_rank, ASCII policy_id), then evaluate applicability predicates in declared order. PredicateObservation binds exact condition source, operation/origin, registry ID/hash, policy ID, phase and full candidate. TRUE/FALSE are explicit observations; UNAVAILABLE/throw/mismatched binding prevents a guessed selection. Each actual evaluation is immediately captured and acknowledged before proceeding; a false predicate makes the entry ineligible, and remaining unconsulted references are retained as unconsulted metadata. No diagnostic claims those unexecuted predicates were evaluated.

For each eligible candidate, retain the selection, perform mandatory actual full StateModel postassessment and additional validation predicates. Empty extra validation lists never remove the mandatory STABLE postcheck. A truly STABLE target with extra-predicate FALSE follows the entry TRY_NEXT/ESCALATE action. Before TRY_NEXT, emit the full canonical nine-field RecoveryDiagnostic for that failed candidate, referencing all acknowledged steps and complete postassessment. Original candidate order, each failed attempt/reason and the final decision remain retained even when a later target succeeds.

Known target shape/initial inspection does not replace postcheck. Explicit postcontext CONTAINED/SAFE_HALT stops candidate iteration and returns the actual boundary handoff, with its complete derived classification retained. A postassessment capture failure or missing/bad evidence also stops iteration; it cannot be treated as ordinary FALSE or swallowed to reach a later success. AVAILABLE-empty, all-ineligible, all-invalid, immediate-entry-escalation and UNAVAILABLE registry have distinct typed reasons; required fallback escalation uses FALLBACK kind and no ad hoc target.

## Postassessment child chain and outcome certification

PostAssessmentFactsProvider supplies a complete explicit ContextObservation plus new ClassificationEvidence and the exact fresh DiagnosticContext chosen for that action. Both predicate facts are bound to the NEW candidate's subject/diagnosis/profile/ASH pins even when NOT_EVALUATED. No original-subject evidence, implicit false context, reused assessment reference or clearing of containment/halt flags is allowed. Caller evidence is retained as an observation; the reference layer does not assert physical platform truth.

PostAssessmentLink has exactly parent_operation_reference, parent_action_reference and originating_chain_root_reference. The child is explicitly assembled by the actual public StateModel constructor with this engine model's exact complete profile/canonical bindings and this admitted engine DiagnosticsPort.assessment_capture(relation=link). There is no undefined hidden post-model capture factory. These are collector correlation metadata outside the canonical TEN. The StateModel child starts its own DETECTION root and emits its unchanged two-record DETECTION/CLASSIFICATION sequence through the linked actual collector; both records require immediate receipts. Main recovery envelopes keep their original root, immediate main predecessor, RECOVERY/ESCALATION stage and nondecreasing severity floor. No child envelope is rewritten to pretend it was a main-chain recovery record.

Only complete StateAssessment with VALID semantics AND system_state_class=STABLE, matching candidate and current source/profile may certify RECOVERED_VALUE or RECOVERED_FALLBACK_VALUE. The complete derived packet is retained. ClassificationEvidenceFailure, DiagnosticCaptureFailure, non-STABLE class, missing receipt or wrong observed target cannot certify success. Keep complete partial child records, attempted child record and evidence failure; no replacement diagnosis or invented confirmation.

## Diagnostic granularity and exact wire ownership

Canonical TEN means exactly diagnostic_kind,severity,stage,disposition,subject_reference,parent_diagnostic_reference,chain_root_reference,rule_ids,summary,notes. Existing assessment packet stays six IDs; existing N1 packet stays its fixed seven IDs even when generic common envelope/collector taxonomy adds N2 source rules. Add an explicit immutable NORMALIZATION_RULE_IDS guard in standalone NormalizationDiagnosticRecord and every confirmed/attempted normalization packet record before widening generic envelope RULE_IDS; current N1 otherwise inherits its bound from that generic set. N2 packet uses its own fixed producer rule set and reviewed evaluation order, not an arbitrary regex-shaped source ID.

Each actual codeword/predicate step emits ACTION_VALUE_COMPUTED with full actual step evidence and canonical TEN immediately. This is an intermediate step, not a completed recovery outcome. When a normalization/correction/candidate/fallback summary/action decision exists, emit OPERATION_DECISION with exactly canonical RecoveryDiagnostic's nine fields: recovery_category,original_state_class,original_diagnostic,steps,outcome,corrected_state,fallback_policy_id,reason,rule_ids. Its steps and references retain the entire acknowledged action prefix and complete postassessment; every failed whole action/candidate has this decision before subsequent attempt. This source-granularity interpretation preserves immediate computation evidence and per-completed-action minimum source record without inventing a PENDING canonical RecoveryOutcome or falsely certifying provisional recovery.

RecoveryValuePacket has fixed schema_ref=data/schemas/m3_recovery_value_schema.json, artifact_type=ywe_recovery_value and artifact_version=1.0.0. The exact typed union is RecoveryNoAction|RecoveredValue|RecoveredFallbackValue|RecoveryHandoff|RecoveryFailure, sharing 25 serialized keys with 19 nonconstant constructor fields. All common fields are mandatory as in the machine inventory; outcome branches are NO_ACTION,RECOVERED_VALUE,RECOVERED_FALLBACK_VALUE,HANDOFF_REQUIRED,FAILURE. execution_scope is CORE_REFERENCE_IMMUTABLE_VALUE and session_effects_performed is false. Successful candidates have complete successful decision/postassessment and no directive/failure; handoffs have typed directive and actual retained decision; failures retain exact code/path, pending mandatory directive if already established, attempted record/status and complete confirmed prefix. No own RecoveryOutcome value is smuggled into the canonical nine-field payload.

RecoveryDiagnostic.recovery_category always equals the original StateAssessment's class-mapped category, and original_state_class equals its original class. The exact source recovery-fallback-semantics.pseudo.md line17 initializes result.recovery_category=classify_recoverability(state_class); line53 passes that result into select_fallback, whose signature at line88 retains it. A separately authorized after-failure route records active_recovery_category=FALLBACK_REQUIRED in route metadata without forging a new original classification pair. This applies to every candidate and summary.

A canonical RecoveryDiagnostic.corrected_state can retain an actual failed candidate when source RECOVERY_FAILED is recorded; it does not certify that candidate. Wire branch/context and full derived assessment determine certification. Complete root fields/branch fields and nested objects are closed. Constructor types are exact built-ins/owned values, booleans are excluded from integer arithmetic, sequences copied to tuples, finite text/collection limits checked at the boundary owner. JSON Schema checks structural row/branch/enum/bounds; mathematical XOR, full profile membership, source equality, actual ACK, origin authenticity, ordering/provenance and physical mode truth remain owned code/evidence obligations.

Derived reference grammar is fixed locally: operation_reference max 192 using existing safe reference alphabet; action refs append :action:NNN, step refs :step:NNN, child refs :post:NNN:{assessment,input,detection,classification}. Derived suffixes never exceed existing 256-character bound. The collector requires all references unique relative to existing origin/session and source-specific meanings. No random ID, wall clock or filesystem path affects canonical semantics.

## Failure and before-effects boundary

The local record reservation is 768 events:32*(8 applicability+8 additional+1 selection+1 main post+2 child+1 candidate decision)+16 correction+1 resolve+1 correction post+2 correction child+1 correction decision+1 route+1 summary+1 handoff=696, with72 remaining admission/meta/refusal/finish slots. Maximum postassessments is33 (one failed correction plus32 fallback), and action decisions35. Detailed RecoveryStepEvidence stays transaction-global; each canonical RecoveryDiagnostic.steps is action-local at most32, and a final fallback summary has one RecoveryStep per attempted candidate. Exact ordered step_indices retain every detailed predicate/XOR/post event without copying all512 predicate steps into the summary. The frozen closed projection proof measures largest event9512B, safety node1343B, supporting graph1459252B, private aliases1671169B and whole maximal assembly9386993B. Reserve31588352B within collector32MiB:768*32KiB events +2MiB supporting +1MiB incidents +2MiB aliases +64KiB health +64KiB inherited origins +1MiB envelope. Separate JSON32MiB, Markdown48MiB, manifest64KiB and protected disk128MiB admit only one bundle including incomplete exports. Logical serialized buffer bound192MiB is not an exact Python heap bound; raw caller business packets are separately capped32MiB. Exact proof/fields/budget are the frozen Diagnostics inventory and byte-bound artifact, not a claimed executed producer or native acceptance.

RecoveryContractError has exactly RECOVERY_INPUT_INVALID,RECOVERY_BINDING_MISMATCH,RECOVERY_PLAN_INVALID,RECOVERY_PORT_INVALID and closed RecoveryFieldPath. Paths are fixed public field names plus declared bounded indexed forms for chain[0..15],entries[0..31],conditions[0..7],steps[0..767],post_assessments[0..32]; no arbitrary freeform path/exception string. Structurally inadmissible objects are not recursively inspected or repr'ed.

Semantic result failure codes are the exact fifteen machine-inventory values. Capture matching CONFIRMED permits the next value step; REJECTED guarantees no acceptance; throws/malformed/wrong-ref/partial commit become NOT_CONFIRMED. Retain the complete attempted owned business record and confirmed prefix in memory. Storage/redaction evidence is a separate artifact and cannot replace that raw business observation. Omission of a required emitted action is a Diagnostics nonconformance at finish, with an actual bounded meta event or explicit meta-unavailable health state. Business action failure and diagnostic infrastructure failure remain distinct.

Future N3 must acquire operational admission before any live effect, verify current session generation/state/source/context, reserve capture/resource budget, prevent containment-forbidden operations and halt reentry, bind each action to that session lease and commit only actual observed state/mode truth. Pure codeword computation here does not satisfy TransitionRegistry's ordinary VALID-state transition precondition; no TransitionRegistry call or permitted live recovery mode is inferred. On terminal session truth, refuse before codec/math/provider/registry access and use only a separately bounded denial audit. RecoveryCapture.begin has exact signature begin(origin,*,operation_reference)->(RecoveryScope|None,RecoveryAdmissionReceipt), fixed768 plus whole-byte reservation; scope exists iff matching CONFIRMED. Scope.append accepts exact RecoveryRecord and returns CaptureReceipt; finish accepts exact RecoveryValuePacket and returns DiagnosticsCompletionReceipt. No free caller count or arbitrary payload dict. Finish is called once with the tentative actual typed result; completion_observation is null on that tentative packet. The receipt has COMPLETE/INCOMPLETE status and the original API_ONLY operation_reference, not an exported alias. Only an exact DiagnosticsCompletionReceipt with the current operation reference and COMPLETE permits publishing the final immutable result copy with that receipt. Matching INCOMPLETE fills the common completion_observation and adds secondary completion_failure_code=COMPLETION_REJECTED. Wrong type/reference or thrown collaborator adds secondary COMPLETION_UNCONFIRMED and leaves common completion_observation null; any exact typed wrong-reference receipt is retained in failure_detail.unconfirmed_completion_observation. If the tentative result is already RecoveryFailure, its original primary failure code, submitted evidence, attempted record, capture status, pending directive and reason remain unchanged. Only the two bounded secondary detail fields are added. For an originally successful/handoff/no-action result, return RecoveryFailure with the primary completion failure code. Both secondary fields are mandatory and null when no secondary failure occurred. No arbitrary returned object is serialized or acknowledgment inferred; no recursive second finish or capture.

A later unconfirmed terminal diagnostic cannot undo an already required actual halt or authorize further effects; N3 must retain actual-mode and capture truth separately.

## Reference Diagnostics implementation and acceptance boundary

The independently reviewed Diagnostics sub-contract is adopted as docs/architecture/m3_reference_diagnostics_contract.md. Its exact62structure/75enum inventory remains a separate Diagnostics authority, with actual source/privacy/budget audits and protected host capability evidence. It owns source-schema/taxonomy/chain validation, whole-operation admission, missing-step expectation ledgers, meta diagnostics, pre-persistence safe projection, bounded retention/overflow/health, immutable snapshots and consistent paired JSON/Markdown export. Canonical Diagnostics coverage for absent RealmEncoder/TransitionRegistry/etc is unavailable with reason, not healthy full-system completion.

Sanitized stored/exported artifacts are explicitly separately versioned views. Caller freeform notes/references/previews are not automatically safe; raw packets remain business memory. Typed allowlisted source/state/enum evidence is retained, arbitrary prose excluded with explicit omission account and stable aliases. Both formats derive from one redacted immutable snapshot and export rechecks its closed safe domain. The host adapter uses only a verified direct fresh protected D:/ child. The actual native probe confirms explicit effective-user+SYSTEM protected DACL, exact inherited child grants, NTFS persistent ACL, native volume/file identity, exclusive flush/readback and existing-root refusal. It retains the negative C:/ root DELETE_CHILD finding and same-user rename disproof. Protection excludes current user, SYSTEM and administrators; no second-user effective-access, adversarial privileged race, encryption or power-loss durability was tested. Implementation must recheck actual root/children ACL, ownership, nonreparse and native identities at boundaries, refuse unverified destinations, enforce quotas and report partial pair writes. No existing ACL was changed.

Initial scoped acceptance requires actual StateModel-origin through this collector, N1 and N2 producer adapters, a representative recovered value and controlled failure with every step/incident retained, real protected synthetic host storage and inspected JSON/Markdown pair. Authored tests must independently cover source/row/class/context/ACK/candidate/TRY_NEXT/mode boundary mutants, missing-record meta, nested secret exclusion, full retained-evidence parity, concurrent snapshot boundary, quota/rotation/duration/admission and store/export failures. Production results are not test oracles. Existing begin/append adapters do not expose producer result completion. At the real reference composition boundary call Diagnostics.complete_assessment/complete_normalization with the exact returned owned typed result, and finish each N2 result/child before certification. Branch-owned expectation tables distinguish one-record diagnosis, one-record contextual failure and missing classification; no record count alone infers completion. The original business packet is unchanged; a separate typed completion receipt/failure and meta-health account reports conformance. Any uncompleted direct producer scope is explicitly OPEN/INCOMPLETE coverage. Native framework/Release runtime, real product UI/support path and other absent canonical producers remain explicit gaps. Actual trusted same-profile normalization/correction math produces a VALID target; explicit noncontained/nonhalted postcontext therefore classifies STABLE. Completed RECOVERY_FAILED/wrong-target after-failure routes are abstract source/actual-defect defenses, not fabricated normal business branches under that verified closure. Contained/halted postcontext is an existing-mode handoff, not ordinary TRY_NEXT. Additional declared predicate FALSE on a genuinely STABLE candidate is the ordinarily reachable registry retry path. Independent tests distinguish those scopes. No fixture count or CLI success closes M3 by itself.

RecoveryStep.action is a source prose/string field, so N2 adopts this explicitly local closed representation: normalize, correct, validate-recovery, select-fallback, validate-fallback, resolve-normalization, resolve-correction, evaluate-applicability, evaluate-additional-validation, handoff, no-action, fallback-summary. The first five preserve canonical pseudocode examples; the others describe only the already scoped resolve/predicate/directive/summary evidence. The exact interface appendix maps each transaction action to its exact local literal, including candidate postcheck validate-fallback versus normalize/correct postcheck validate-recovery. These are not new canonical RecoveryOutcome or action enum tokens.

After-failure registry methods receive the full retained post evidence explicitly: normalization requires failed_post_assessment; correction requires it only for RECOVERY_FAILED and forbids it on BLOCKED. Pure Registry validation checks the exact action/link/candidate/current-model semantic correspondence and stops CONTAINED/SAFE_HALT for the Engine boundary handoff. It does not authenticate collector acknowledgment. Engine verifies actual child completion, and scope finish checks the same collector ledger. A bare post reference cannot satisfy this input.

## Exact interface inventory

This adopted inventory fixes field order, constructors, closed domains, method signatures and bounded results before code. The independent external proposal fingerprints were contract `e8038ea9000faaf82f1bbffa86a2ce562c4c2d3e9b78527907ee9178bd7e8fb7`, merged inventory `2b171ee44358ac2f9f5a258ae0ae451fd8162e5ca1c220d27997344db10c177a`, and artifact index `c4325686fac35b170465688d828af12f0ba74a1efb646c68b6c41dd06f21a077`. They identify reviewed external bytes, not the current adopted document. The active safety-policy digest is `00fcee810c5cd445dd0baaaf98c754000347489001e21588eb03afdd1e1ebb95`.

```json
{
  "status": "ACTIVE_ADOPTED_N2_CONTRACT_IMPLEMENTATION_INCOMPLETE",
  "baseline_revision": "5328f018f341b80ad58cdb82f64708992ee2d6ae",
  "requirements": "YWE-REQ-0041; YWE-REQ-0042; ADR-0031",
  "core_scope": "reference immutable recovery values, registry and complete bounded reference Diagnostics; mode/session execution belongs N3",
  "resource_limits": {
    "registry_entries": 32,
    "conditions_per_entry_per_phase": 8,
    "known_correction_codewords": 16,
    "new_operation_diagnostics": 768,
    "linked_post_assessments": 33,
    "action_decisions": 35,
    "notes": 8,
    "reason_characters": 512,
    "operation_reference_characters": 192,
    "ordinary_reference_characters": 256,
    "canonical_steps_per_action_decision": 32,
    "budget_formula": "32*(8 applicability+8 additional+1 selection+1 main post+2 child+1 decision)+16 correction+1 resolve+1 correction post+2 correction child+1 correction decision+1 route+1 summary+1 handoff=696;768 reserves72 additional admission/meta/refusal/finish slots"
  },
  "proposed_schemas": {
    "recovery": "https://ywe.local/schemas/m3_recovery_value_schema.json",
    "registry": "https://ywe.local/schemas/m3_fallback_registry_schema.json",
    "diagnostics": "https://ywe.local/schemas/m3_reference_diagnostic_bundle_schema.json"
  },
  "error_codes": [
    "RECOVERY_INPUT_INVALID",
    "RECOVERY_BINDING_MISMATCH",
    "RECOVERY_PLAN_INVALID",
    "RECOVERY_PORT_INVALID"
  ],
  "assessment_failure_codes": [
    "SOURCE_BINDING_MISMATCH",
    "PROFILE_BINDING_MISMATCH",
    "INPUT_BINDING_MISMATCH",
    "DIAGNOSIS_MISMATCH",
    "PREDICATE_BINDING_MISMATCH",
    "PREDICATE_NOT_EVALUATED",
    "CLASSIFICATION_MISMATCH",
    "CLASSIFICATION_ENVELOPE_MISMATCH"
  ],
  "correction_failure_codes": [
    "SOURCE_BINDING_MISMATCH",
    "PROFILE_BINDING_MISMATCH",
    "ORIGIN_MISMATCH",
    "CHAIN_MEMBER_INVALID",
    "CHAIN_TARGET_MISMATCH",
    "TARGET_NOT_VALID"
  ],
  "result_failure_codes": [
    "ORIGIN_REJECTED",
    "CAPTURE_ADMISSION_REJECTED",
    "CAPTURE_ADMISSION_UNCONFIRMED",
    "STEP_CAPTURE_REJECTED",
    "STEP_CAPTURE_UNCONFIRMED",
    "POST_EVIDENCE_UNAVAILABLE",
    "POST_ASSESSMENT_FAILED",
    "POST_CAPTURE_REJECTED",
    "POST_CAPTURE_UNCONFIRMED",
    "COLLABORATOR_FAILED",
    "RESOURCE_LIMIT",
    "INTERNAL_INVARIANT_FAILURE",
    "REGISTRY_BINDING_REJECTED",
    "COMPLETION_REJECTED",
    "COMPLETION_UNCONFIRMED"
  ],
  "step_actions": [
    "NORMALIZE_PLAN",
    "NORMALIZE_XOR",
    "CORRECTION_RESOLVE",
    "CORRECTION_XOR",
    "CANDIDATE_APPLICABILITY",
    "FALLBACK_SELECT",
    "CANDIDATE_VALIDATION",
    "POST_ASSESSMENT",
    "HANDOFF",
    "NO_ACTION"
  ],
  "outcomes": [
    "NO_ACTION",
    "RECOVERED_VALUE",
    "RECOVERED_FALLBACK_VALUE",
    "HANDOFF_REQUIRED",
    "FAILURE"
  ],
  "types": {
    "AssessmentValidation": {
      "status": "VERIFIED|REJECTED",
      "submitted_assessment": "StateAssessment",
      "current_source_binding": "CanonicalAshBinding",
      "current_profile_binding": "AvailableProfileBinding|UnavailableProfileBinding",
      "expected_diagnostic": "StateValidityDiagnostic|null",
      "expected_system_state_class": "SystemStateClass|null",
      "expected_recovery_category": "RecoveryCategory|null",
      "expected_consulted_predicates": "predicate-name[0..1]|null",
      "failure_code": "AssessmentFailureCode|null",
      "field_name": "RecoveryFieldPath|null"
    },
    "RecoverySourceBinding": {
      "canonical_binding": "CanonicalAshBinding exact current fixed9pins",
      "contract_pins": "exact reviewed7 SourcePins: recovery-engine-contract,diagnostics-module-contract,fallback-policy-registry,recovery-fallback-semantics,containment-safe-failure-semantics,diagnostic-schema,rule-id-taxonomy; full32inventory remains assembly/test proof"
    },
    "SourcePin": {
      "path": "canonical relative reference max256",
      "sha256": "lowercase hex64"
    },
    "EvidenceSourceBinding": {
      "source_reference": "reference max256",
      "source_sha256": "lowercase hex64",
      "evidence_reference": "reference max256"
    },
    "RecoveryOperationContext": {
      "operation_reference": "reference max192",
      "origin_assessment_reference": "reference max256",
      "context_observation": "ContextObservation",
      "propagation_evidence": "PropagationEvidence",
      "external_authority_evidence": "ExternalAuthorityEvidence"
    },
    "ContextObservation": {
      "context": "SystemContext exact2booleans",
      "owner_reference": "reference max256",
      "observation_reference": "reference max256",
      "source_binding": "EvidenceSourceBinding"
    },
    "PropagationEvidence": {
      "status": "SAFE|RISK|UNAVAILABLE",
      "operation_reference": "reference max192",
      "origin_assessment_reference": "reference max256",
      "source_binding": "EvidenceSourceBinding",
      "reason": "nonblank text max512"
    },
    "ExternalAuthorityEvidence": {
      "status": "REACHABLE|UNREACHABLE|UNAVAILABLE",
      "operation_reference": "reference max192",
      "origin_assessment_reference": "reference max256",
      "source_binding": "EvidenceSourceBinding",
      "reason": "nonblank text max512"
    },
    "KnownCorrection": {
      "correction_reference": "reference max256",
      "original_assessment_reference": "reference max256",
      "source_binding": "EvidenceSourceBinding",
      "profile_id": "reference max256",
      "profile_source_sha256": "lowercase hex64",
      "chain": "AshState[0..16] submitted declared sequence; C membership is StateModel semantic proof",
      "expected_target": "AshState",
      "reason": "nonblank text max512",
      "classification_evidence_reference": "exact origin correction_path_is_known.binding.evidence_reference",
      "canonical_binding": "CanonicalAshBinding exact fixed9 source fields",
      "provider_source_verification": "const DECLARED_NOT_AUTHENTICATED"
    },
    "UnavailableCorrection": {
      "original_assessment_reference": "reference max256",
      "source_binding": "EvidenceSourceBinding",
      "reason": "nonblank text max512",
      "classification_evidence_reference": "exact origin correction_path_is_known.binding.evidence_reference",
      "provider_source_verification": "const DECLARED_NOT_AUTHENTICATED"
    },
    "CorrectionValidation": {
      "status": "VERIFIED|REJECTED",
      "submitted_correction": "KnownCorrection",
      "origin_validation": "AssessmentValidation VERIFIED|REJECTED",
      "current_source_binding": "CanonicalAshBinding",
      "current_profile_binding": "AvailableProfileBinding|UnavailableProfileBinding",
      "computed_target": "AshState|null",
      "target_diagnostic": "StateValidityDiagnostic|null",
      "failure_code": "CorrectionFailureCode|null",
      "field_name": "RecoveryFieldPath|null"
    },
    "ConditionReference": {
      "condition_id": "reference max128",
      "source_binding": "EvidenceSourceBinding"
    },
    "FallbackPolicyEntry": {
      "policy_id": "FALLBACK-[A-Z][A-Z0-9]{0,31}-[001..999]",
      "applicability_conditions": "ConditionReference[0..8]",
      "candidate_state_reference": "AshState",
      "ordering_rank": "exact int signed64 no bool",
      "validation_requirements": "ConditionReference[0..8]",
      "escalation_on_failure": "TRY_NEXT|ESCALATE_TO_CONTAINMENT",
      "notes": "nonblank text max512[1..8]"
    },
    "RegistrySourceBinding": {
      "registry_id": "reference max128",
      "source_binding": "EvidenceSourceBinding",
      "profile_id": "reference max256",
      "profile_source_sha256": "lowercase hex64",
      "ash_dependency_id": "fixed canonical dependency",
      "ash_aggregate_sha256": "fixed canonical aggregate",
      "source_verification": "const DECLARED_NOT_AUTHENTICATED for external data provenance; canonical/model pins independently reviewed"
    },
    "AvailableFallbackRegistry": {
      "schema_ref": "const data/schemas/m3_fallback_registry_schema.json",
      "artifact_type": "const ywe_fallback_registry",
      "artifact_version": "const 1.0.0",
      "availability": "const AVAILABLE",
      "source_binding": "RegistrySourceBinding",
      "entries": "FallbackPolicyEntry[0..32]",
      "candidate_certifications": "CandidateCertification[0..32], exact one-to-one entry policyID mapping in entries inputorder"
    },
    "UnavailableFallbackRegistry": {
      "schema_ref": "const data/schemas/m3_fallback_registry_schema.json",
      "artifact_type": "const ywe_fallback_registry",
      "artifact_version": "const 1.0.0",
      "availability": "const UNAVAILABLE",
      "source_binding": "RegistrySourceBinding",
      "reason": "nonblank text max512"
    },
    "FallbackRouteAuthorization": {
      "route": "DIRECT_DEGRADED|AFTER_CORRECTION_FAILURE|AFTER_NORMALIZATION_FAILURE",
      "original_system_state_class": "DEGRADED|CORRECTABLE|UNSTABLE",
      "origin_assessment_reference": "reference max256",
      "failed_action_decision_reference": "reference max256|null",
      "failed_outcome": "BLOCKED|RECOVERY_FAILED|null; AFTER_NORMALIZATION_FAILURE only RECOVERY_FAILED",
      "rule_ids": "exact [ASH-RECOVERY-ACTION-001,ASH-FALLBACK-SELECTION-001]",
      "origin_predicate_evidence_reference": "reference max256|null; exact original correction/fallback fact for applicable route",
      "active_recovery_category": "const FALLBACK_REQUIRED; routeaction only, never original classification rewrite"
    },
    "PredicateObservation": {
      "status": "TRUE|FALSE|UNAVAILABLE",
      "condition": "ConditionReference",
      "operation_reference": "reference max192",
      "origin_assessment_reference": "reference max256",
      "registry_id": "reference max128",
      "registry_source_sha256": "lowercase hex64",
      "policy_id": "policy ID",
      "phase": "APPLICABILITY|ADDITIONAL_VALIDATION",
      "candidate_state_reference": "AshState",
      "source_binding": "EvidenceSourceBinding",
      "reason": "nonblank text max512"
    },
    "PostAssessmentFacts": {
      "diagnostic_context": "DiagnosticContext freshly derived operation+candidate ordinal",
      "context_observation": "ContextObservation",
      "classification_evidence": "ClassificationEvidence newly bound to target/diagnosis/profile/ASH"
    },
    "UnavailablePostAssessmentFacts": {
      "operation_reference": "reference max192",
      "candidate_state_reference": "AshState",
      "source_binding": "EvidenceSourceBinding",
      "reason": "nonblank text max512"
    },
    "PostAssessmentLink": {
      "parent_operation_reference": "reference max192",
      "parent_action_reference": "reference max256",
      "originating_chain_root_reference": "reference max256"
    },
    "LinkedPostAssessment": {
      "link": "PostAssessmentLink",
      "candidate_state": "AshState",
      "context_observation": "ContextObservation",
      "assessment": "StateAssessment|ClassificationEvidenceFailure|DiagnosticCaptureFailure",
      "capture_status": "COMPLETE|REJECTED|NOT_CONFIRMED"
    },
    "RecoveryStepEvidence": {
      "step_index": "exact int0..767",
      "action": "closed10action enum",
      "status": "COMPLETED|BLOCKED|FAILED",
      "before_state": "AshState|null",
      "codeword": "CanonicalCodeword|null",
      "after_state": "AshState|null",
      "policy_id": "policy ID|null",
      "predicate_observation": "PredicateObservation|null",
      "post_assessment_reference": "reference max256|null",
      "diagnostic_reference": "reference max256",
      "reason": "nonblank text max512"
    },
    "RecoveryDiagnostic": {
      "recovery_category": "exact immutable original origin_assessment.recovery_category for all actions/candidates/summary",
      "original_state_class": "exact immutable origin_assessment.system_state_class",
      "original_diagnostic": "StateValidityDiagnostic exact9fields",
      "steps": "RecoveryStep[0..32] action-local steps; summary one step per attempted policy, detail retained via exact step_indices",
      "outcome": "RECOVERED|RECOVERED_VIA_FALLBACK|BLOCKED|RECOVERY_FAILED|ESCALATE_TO_CONTAINMENT|NOT_APPLICABLE",
      "corrected_state": "AshState|null",
      "fallback_policy_id": "policy ID|null",
      "reason": "nonblank text max512",
      "rule_ids": "N2RuleID[1..5] unique evaluation order"
    },
    "RecoveryStep": {
      "action": "exact canonical_step_action_literals local12string enum",
      "status": "COMPLETED|BLOCKED|FAILED",
      "reason": "nonblank text max512"
    },
    "RecoveryRecord": {
      "diagnostic_reference": "reference max256",
      "envelope": "DiagnosticEnvelope exact10fields",
      "record_kind": "ACTION_VALUE_COMPUTED|OPERATION_DECISION",
      "payload": "RecoveryStepEvidence|RecoveryActionDecision"
    },
    "RecoveryActionDecision": {
      "action_reference": "reference max256",
      "action": "NORMALIZE|CORRECT|FALLBACK_CANDIDATE|FALLBACK_SUMMARY|NO_ACTION|HANDOFF",
      "diagnostic": "RecoveryDiagnostic",
      "step_indices": "tuple length0..768 of exact ordered unique integer values0..767, references transaction-global actual observations; no detailed evidence omitted",
      "post_assessment_reference": "reference max256|null",
      "candidate_context": "SystemContext|null",
      "directive": "RecoveryDirective|null; HANDOFF exact typedrequest, no modeentryclaim"
    },
    "PolicyAttempt": {
      "policy_id": "policy ID",
      "applicability_observations": "PredicateObservation[0..8]",
      "unconsulted_applicability": "ConditionReference[0..8]",
      "validation_observations": "PredicateObservation[0..8]",
      "unconsulted_validation": "ConditionReference[0..8]",
      "post_assessment_reference": "reference max256|null",
      "decision_reference": "reference max256",
      "result": "INELIGIBLE|RECOVERED|VALIDATION_FAILED|UNAVAILABLE|LIFECYCLE_BOUNDARY"
    },
    "RecoveryDirective": {
      "requested_action": "ENTER_CONTAINMENT|REQUEST_EXTERNAL_AUTHORITY|ENTER_SAFE_HALT|REMAIN_CONTAINED|REMAIN_SAFE_HALT",
      "trigger": "CanonicalContainmentTrigger|CanonicalSafeHaltTrigger|ExternalEscalationRequired|ExistingModeBoundary",
      "origin_assessment_reference": "reference max256",
      "causing_decision_reference": "reference max256",
      "evidence_references": "reference[1..8]",
      "actual_mode_status": "const NOT_ENTERED_BY_N2",
      "reason": "nonblank text max512",
      "request_origin": "POLICY|SOURCE_RECOVERABILITY|OBSERVED_EXISTING_MODE",
      "policy_binding": "RecoverySafetyPolicyBinding|null"
    },
    "ExternalEscalationRequired": {
      "trigger_domain": "const YWE_RECOVERABILITY_CATEGORY",
      "recovery_category": "const ESCALATION_REQUIRED",
      "authority_status": "REACHABLE|UNREACHABLE|UNAVAILABLE"
    },
    "RecoveryFailureDetail": {
      "failure_code": "exact15 result_failure_codes",
      "field_name": "RecoveryFieldPath",
      "submitted_evidence": "AssessmentValidation|RegistryValidation|CorrectionValidation|NormalizationPreparation|PostAssessmentFacts|UnavailablePostAssessmentFacts|PredicateObservation|DiagnosticsCompletionReceipt|null",
      "attempted_diagnostic": "RecoveryRecord|null",
      "capture_status": "REJECTED|NOT_CONFIRMED|null",
      "pending_directive": "RecoveryDirective|null",
      "reason": "nonblank text max512",
      "completion_failure_code": "null|COMPLETION_REJECTED|COMPLETION_UNCONFIRMED; secondary finish failure does not replace primary original failure",
      "unconfirmed_completion_observation": "DiagnosticsCompletionReceipt|null; exact typed wrong-reference receipt retained, never arbitrary malformed returned object"
    },
    "RecoverySafetyPolicyBinding": {
      "policy_id": "const YWE-RECOVERY-SAFETY-001",
      "policy_version": "const 1.0.0",
      "source_path": "const docs/architecture/m3_recovery_safety_policy.md",
      "source_sha256": "const 00fcee810c5cd445dd0baaaf98c754000347489001e21588eb03afdd1e1ebb95"
    },
    "ExistingModeBoundary": {
      "trigger_domain": "const YWE_OBSERVED_MODE_BOUNDARY",
      "observed_system_state_class": "CONTAINED|SAFE_HALT",
      "observed_assessment_reference": "reference max256"
    },
    "NormalizationPreparation": {
      "status": "READY|UNAVAILABLE|REJECTED",
      "original_diagnosis": "StateDiagnosis exact actual original detection projection, no new ACK",
      "policy_binding": "adopted N1 NormalizationPolicyBinding",
      "plan": "NormalizationPlan|null",
      "plan_validation": "NormalizationPlanValidation|null",
      "planning_error": "NormalizationErrorObservation|null",
      "resolution_observation": "NormalizationResolutionObservation"
    },
    "NormalizationErrorObservation": {
      "code": "existing exact4 NormalizationContractError codes",
      "field_name": "existing exact62 N1 field paths",
      "plan_validation": "NormalizationPlanValidation|null",
      "reason": "const NORMALIZATION_PLANNING_REFUSED; code+field_name retain precise typed refusal, never arbitrary exception repr"
    },
    "CorrectionObservation": {
      "submitted": "KnownCorrection|UnavailableCorrection",
      "validation": "CorrectionValidation|null"
    },
    "EntryApplicability": {
      "policy_id": "policy ID",
      "observations": "PredicateObservation[0..8] exact declared prefix",
      "unconsulted_conditions": "ConditionReference[0..8] exact remaining suffix"
    },
    "RecoveryPacketCommon": {
      "schema_ref": "const data/schemas/m3_recovery_value_schema.json",
      "artifact_type": "const ywe_recovery_value",
      "artifact_version": "const 1.0.0",
      "outcome": "variant enum",
      "execution_scope": "const CORE_REFERENCE_IMMUTABLE_VALUE",
      "operation_context": "RecoveryOperationContext",
      "origin_assessment": "StateAssessment",
      "origin_validation": "AssessmentValidation",
      "source_binding": "RecoverySourceBinding",
      "registry_binding": "RegistrySourceBinding|null",
      "route_authorization": "FallbackRouteAuthorization|null",
      "steps": "RecoveryStepEvidence[0..768] all actual observations; confirmed emission list is separate",
      "post_assessments": "LinkedPostAssessment[0..33]",
      "policy_attempts": "PolicyAttempt[0..32]",
      "action_decisions": "RecoveryActionDecision[0..35]",
      "emitted_diagnostics": "RecoveryRecord[0..768] CONFIRMED only",
      "candidate_state": "AshState|null",
      "directive": "RecoveryDirective|null",
      "failure_detail": "RecoveryFailureDetail|null",
      "session_effects_performed": "const false",
      "normalization_preparation": "NormalizationPreparation|null",
      "correction_observation": "CorrectionObservation|null",
      "registry_snapshot": "AvailableFallbackRegistry|UnavailableFallbackRegistry|null, fullsnapshot mandatory whenconsulted",
      "registry_validation": "RegistryValidation VERIFIED|REJECTED|null, actual fullcurrent comparison whenconsulted",
      "completion_observation": "DiagnosticsCompletionReceipt|null; null before/no admitted finish; matching actual COMPLETE/INCOMPLETE receipt after finish"
    },
    "RecoveryNoAction": {
      "common_fields": "RecoveryPacketCommon all25exactserializedkeys",
      "outcome": "const NO_ACTION",
      "branch_guard": "branch_constraints.NO_ACTION",
      "constructor_fields": "19 nonconstant common fields; header3/outcome/execution_scope/session_effects fixed class values"
    },
    "RecoveredValue": {
      "common_fields": "RecoveryPacketCommon all25exactserializedkeys",
      "outcome": "const RECOVERED_VALUE",
      "branch_guard": "branch_constraints.RECOVERED_VALUE",
      "constructor_fields": "19 nonconstant common fields; header3/outcome/execution_scope/session_effects fixed class values"
    },
    "RecoveredFallbackValue": {
      "common_fields": "RecoveryPacketCommon all25exactserializedkeys",
      "outcome": "const RECOVERED_FALLBACK_VALUE",
      "branch_guard": "branch_constraints.RECOVERED_FALLBACK_VALUE",
      "constructor_fields": "19 nonconstant common fields; header3/outcome/execution_scope/session_effects fixed class values"
    },
    "RecoveryHandoff": {
      "common_fields": "RecoveryPacketCommon all25exactserializedkeys",
      "outcome": "const HANDOFF_REQUIRED",
      "branch_guard": "branch_constraints.HANDOFF_REQUIRED",
      "constructor_fields": "19 nonconstant common fields; header3/outcome/execution_scope/session_effects fixed class values"
    },
    "RecoveryFailure": {
      "common_fields": "RecoveryPacketCommon all25exactserializedkeys",
      "outcome": "const FAILURE",
      "branch_guard": "branch_constraints.FAILURE",
      "constructor_fields": "19 nonconstant common fields; header3/outcome/execution_scope/session_effects fixed class values"
    },
    "RecoveryValuePacket": {
      "union": "RecoveryNoAction|RecoveredValue|RecoveredFallbackValue|RecoveryHandoff|RecoveryFailure",
      "construction": "typing union only, never instantiate"
    },
    "CandidateCertification": {
      "policy_id": "exact corresponding canonical entry policyID",
      "context_observation": "ContextObservation equals source_assessment.system_context",
      "source_assessment": "StateAssessment complete source-reported semanticcertification; currentmodelvalidates parsedtargetequalsentry and STABLE; no physicalmode or ACK proof"
    },
    "RegistryTargetValidation": {
      "policy_id": "policyID",
      "submitted_certification": "CandidateCertification",
      "assessment_validation": "AssessmentValidation current fullmodel",
      "target_diagnostic": "StateValidityDiagnostic|null"
    },
    "RegistryValidation": {
      "status": "VERIFIED|REJECTED",
      "submitted_snapshot": "AvailableFallbackRegistry|UnavailableFallbackRegistry",
      "current_source_binding": "CanonicalAshBinding",
      "current_profile_binding": "AvailableProfileBinding|UnavailableProfileBinding",
      "candidate_validations": "RegistryTargetValidation[0..32] exact evaluated inputprefix",
      "failure_code": "REGISTRY_SOURCE_MISMATCH|REGISTRY_PROFILE_MISMATCH|CERTIFICATION_INVENTORY_MISMATCH|TARGET_NOT_VALID|CERTIFICATION_NOT_STABLE|null",
      "failed_policy_id": "policyID|null",
      "field_name": "RecoveryFieldPath|null"
    },
    "NormalizationResolutionObservation": {
      "availability": "READY|UNAVAILABLE",
      "operation_reference": "reference max192",
      "origin_assessment_reference": "reference max256",
      "source_binding": "EvidenceSourceBinding declared provider provenance",
      "reason": "nonblank text max512"
    },
    "RecoveryContractError": {
      "code": "exact4contractcodes",
      "field_name": "RecoveryFieldPath",
      "validation": "AssessmentValidation|RegistryValidation|CorrectionValidation|null",
      "emitted_diagnostics": "const empty tuple; no effects occurred"
    }
  },
  "public_api": [
    {
      "owner": "StateModel",
      "signature": "validate_assessment(submitted: StateAssessment) -> AssessmentValidation",
      "capture": "none",
      "mathematical_owner": true
    },
    {
      "owner": "StateModel",
      "signature": "validate_known_correction(submitted: KnownCorrection, *, origin: StateAssessment) -> CorrectionValidation",
      "capture": "none",
      "mathematical_owner": true
    },
    {
      "owner": "StateModel",
      "signature": "diagnosis_from_assessment(submitted: StateAssessment) -> StateDiagnosis | AssessmentValidation(REJECTED)",
      "capture": "none; full owned origin validation before projecting exact actual original detection record; rejection returns retained comparison",
      "mathematical_owner": true
    },
    {
      "owner": "StateModel",
      "signature": "inspect_state(state: AshState) -> StateValidityDiagnostic",
      "capture": "none; explicitly an inspection value, not an emitted record",
      "mathematical_owner": true
    },
    {
      "owner": "KnownCorrectionProvider",
      "signature": "resolve(origin: StateAssessment, *, operation_context: RecoveryOperationContext) -> KnownCorrection | UnavailableCorrection",
      "capture": "caller captures observation before subsequent effect"
    },
    {
      "owner": "NormalizationResolutionProvider",
      "signature": "resolve(origin: StateAssessment, *, operation_context: RecoveryOperationContext, policy_binding: NormalizationPolicyBinding) -> NormalizationPreparation(READY|UNAVAILABLE)",
      "capture": "explicit observation capturedbefore furtheraction; READY proof actualStateModelowned; UNAVAILABLE localboundary typed, never invented noT"
    },
    {
      "owner": "ConditionEvaluator",
      "signature": "evaluate(condition: ConditionReference, *, origin: StateAssessment, entry: FallbackPolicyEntry, phase: APPLICABILITY|ADDITIONAL_VALIDATION, operation_context: RecoveryOperationContext) -> PredicateObservation",
      "capture": "caller captures observation immediately"
    },
    {
      "owner": "PostAssessmentFactsProvider",
      "signature": "provide(candidate: AshState, *, origin: StateAssessment, action_reference: str, diagnostic_context: DiagnosticContext, operation_context: RecoveryOperationContext) -> PostAssessmentFacts | UnavailablePostAssessmentFacts",
      "capture": "actual StateModel.assess invoked only after exact binding check"
    },
    {
      "owner": "FallbackRegistry",
      "signature": "__init__(snapshot: AvailableFallbackRegistry|UnavailableFallbackRegistry, *, state_model: StateModel)",
      "capture": "none; whole snapshot pinned/copied and all AVAILABLE targets inspected VALID"
    },
    {
      "owner": "FallbackRegistry",
      "signature": "ordered_entries() -> tuple[FallbackPolicyEntry,...]",
      "capture": "none; exact(rank,ASCIIpolicyID)"
    },
    {
      "owner": "RecoveryEngine",
      "signature": "__init__(state_model: StateModel, registry: FallbackRegistry, diagnostics: DiagnosticsPort, normalization_resolver: NormalizationResolutionProvider, correction_provider: KnownCorrectionProvider, condition_evaluator: ConditionEvaluator, post_facts_provider: PostAssessmentFactsProvider)",
      "capture": "all dependencies explicit no defaults"
    },
    {
      "owner": "RecoveryEngine",
      "signature": "recover(origin: StateAssessment, *, operation_context: RecoveryOperationContext) -> RecoveryValuePacket",
      "capture": "reserve/attach before effects; immediate step and completed-action acknowledgment; no session mutation"
    },
    {
      "owner": "FallbackRegistry",
      "signature": "get_candidates(origin: StateAssessment, *, applicability: tuple[EntryApplicability,...]) -> tuple[FallbackPolicyEntry,...]",
      "capture": "none; canonical direct DEGRADED-only precondition; exact complete current observed applicability inventory"
    },
    {
      "owner": "FallbackRegistry",
      "signature": "get_candidates_after_correction_failure(origin: StateAssessment, *, failed_action: RecoveryActionDecision, authorization: FallbackRouteAuthorization, applicability: tuple[EntryApplicability,...], failed_post_assessment: LinkedPostAssessment|None=None) -> tuple[FallbackPolicyEntry,...]",
      "capture": "pure; exact CORRECTABLE plus prior BLOCKED/RECOVERY_FAILED action. Full failed_post_assessment mandatory on RECOVERY_FAILED, forbidden/nonconsulted on BLOCKED; matching action/link/candidate/current fullmodel/class. No collector ACK authentication; Engine and Scope.finish own real child completion."
    },
    {
      "owner": "FallbackRegistry",
      "signature": "get_candidates_after_normalization_failure(origin: StateAssessment, *, failed_action: RecoveryActionDecision, failed_post_assessment: LinkedPostAssessment, authorization: FallbackRouteAuthorization, applicability: tuple[EntryApplicability,...]) -> tuple[FallbackPolicyEntry,...]",
      "capture": "pure; only UNSTABLE completed normalization RECOVERY_FAILED; exact full retained post action/link/candidate/currentmodel/class comparison, never BLOCKED. CONTAINED/SAFE_HALT postclass refuses fallback and returns to Engine boundary handoff. Pure validation does not authenticate collector ACK; Engine and Scope.finish own it."
    },
    {
      "owner": "FallbackRegistry",
      "signature": "validate_for_model(current_model: StateModel) -> RegistryValidation",
      "capture": "pure; exactfullsource/profile plus everyentry/cert,target revalidated; no internal access byEngine"
    },
    {
      "owner": "FallbackRegistry",
      "signature": "snapshot -> AvailableFallbackRegistry|UnavailableFallbackRegistry",
      "capture": "immutable public property; full declaredsource dataset retained"
    },
    {
      "owner": "FallbackRegistry",
      "signature": "profile_binding -> AvailableProfileBinding|UnavailableProfileBinding; canonical_binding -> CanonicalAshBinding",
      "capture": "immutable exactconstructor modelproperties"
    },
    {
      "owner": "RecoveryCapture",
      "signature": "begin(origin: StateAssessment, *, operation_reference: reference<=192) -> tuple[RecoveryScope|None,RecoveryAdmissionReceipt]",
      "capture": "fixed768event/wholebyte reservation; samecollector exact2originrefs; scope iffmatchingCONFIRMED"
    },
    {
      "owner": "RecoveryCapture",
      "signature": "begin_denial(origin: StateAssessment, *, operation_reference: reference<=192) -> tuple[DenialScope|None,RecoveryAdmissionReceipt]",
      "capture": "samecollector attachment, separatelycorrelated fresh audit; reserves1newrecord+fixedsupport/incident/aliasbytes; no originalmainappend"
    },
    {
      "owner": "RecoveryScope",
      "signature": "append(record: RecoveryRecord) -> CaptureReceipt; finish(result: RecoveryValuePacket) -> DiagnosticsCompletionReceipt",
      "capture": "exactownedrecord no arbitrarydict; immediateACK; actualtypedresult expectations; finishonce"
    },
    {
      "owner": "DenialScope",
      "signature": "append(record: RecoveryRecord) -> CaptureReceipt; finish(result: RecoveryHandoff|RecoveryFailure) -> DiagnosticsCompletionReceipt",
      "capture": "exactone fresh DENIAL OPERATION_DECISION, zero effects/steps/posts/registry; failure preservesattemptedrecord"
    }
  ],
  "diagnostics_owner": "docs/architecture/m3_reference_diagnostics_contract.md#exact-interface-inventory exact adopted62structures/75enums. Independently generated byte/protection/source evidence was reviewed in the historical external N2_REVIEW_ARTIFACT_INDEX.json; source/artifact authority scopes stay explicit.",
  "post_model_assembly": "Use actual existing StateModel(current_model.profile_binding,current_model.canonical_binding,diagnostics.assessment_capture(relation=exact PostAssessmentLink)) after same collector reservation. No hidden capture factory or private classifier access.",
  "full_profile_guard": "Registry retains full constructor profile_binding and canonical_binding. RecoveryEngine compares every field including recognized_valid_states, then inspects every AVAILABLE target again at use under current model. Same ID/hash alone is insufficient.",
  "notes_guard": "Bounded nonempty notes; detection envelope.notes equals state_validity_diagnostic.notes. Pure validation does not compare generated English as mathematical oracle. Same collector attachment independently compares exact original confirmed records.",
  "constructor_semantics": {
    "KnownCorrection": "structure/complete9-bit width/copy/source/ref only; current C membership/exact XOR/target validity StateModel owned; external source_binding provenance declared, not authenticated; canonical_binding exactcurrent9 checked",
    "CorrectionValidation rejected origin": "REJECTED origin_validation permitted only early ORIGIN_MISMATCH with computed_target/target_diagnostic null",
    "RecoverySafetyPolicyDirective": "NORMALIZATION_PATH_NOT_COMPUTABLE maps canonical OPERATOR_REQUEST with request_origin POLICY and exact local policy binding; no canonical enum extension",
    "Post child": "complete current full model and exact admitted collector; actual assess call, no reparenting",
    "RecoveryValuePacket": "all actual steps/proofs retained even if final diagnostic capture unconfirmed; emitted_diagnostics only confirmed, attempted record explicit failure detail",
    "AvailableFallbackRegistry": "entry7keys unchanged; certification wrapper maps exact policyIDs in inputorder; each complete source-reported StateAssessment purecurrentmodelvalidated parsedtargetsame and STABLE under explicitcontext; ACK/physicalmode not claimed",
    "RegistryValidation": "SOURCE/PROFILE exactfullmodel check; everycurrent candidate cert+target inspected atuse; bad constructor binding raises RecoveryContractError with complete RegistryValidation comparison, no effects",
    "FallbackRegistry": "semantic cert/config refusal raises RecoveryContractError(validation=completeRegistryValidation); use-time purevalidate_for_model returnsactualcomparison; sameID/hashdiffprofile rejected beforeeffects"
  },
  "branch_constraints": {
    "NO_ACTION": "verified STABLE origin; candidate unchanged original; one completed canonical NOT_APPLICABLE decision; no directive/failure",
    "RECOVERED_VALUE": "origin UNSTABLE|CORRECTABLE; actual candidate matches full XOR/proof; complete derived STABLE postassessment; acknowledged completed action RECOVERED; no directive/failure",
    "RECOVERED_FALLBACK_VALUE": "origin DEGRADED or authorized CORRECTABLE/UNSTABLE completed action failure; selected actual registry policy; full STABLE postassessment+allconsulted additional predicatesTRUE; complete acknowledged RECOVERED_VIA_FALLBACK decision; no directive/failure",
    "HANDOFF_REQUIRED": "verified origin; actual completed refusal/decision and typed directive retained; no actual mode entry or session commit; candidate may retain an actually computed failed observation without certifying it",
    "FAILURE": "non-null exact typed failure detail; all actual observed steps/submissions/proofs plus confirmed prefix/attempted record retained; pending mandatory directive retained if already established; no recovered certification",
    "ORIGIN_REJECTED": "origin_validation REJECTED; no capture scope/steps/post/actions/emissions/provider/registry call; no directive invented",
    "CAPTURE_ADMISSION_FAILURE": "origin verified; no provider/evaluator/value effects; no invented attempted step or original acknowledgment",
    "POST_CAPTURE_FAILURE": "complete actual failed child packet retained; no later candidate; no recovered certification",
    "REGISTRY_BINDING_REJECTED": "originverified, actualRegistryValidationREJECTED retained; DIRECT_DEGRADED rejection precedes initial capture/provider/evaluator/value effects; after a completed failed correction/normalization retain the earlier admitted scope, actual steps and failed decision, rejecting before the first fallback predicate/selection/value effect; no falsecandidate",
    "EXISTING_SAFE_HALT_DENIAL": "ownedoriginverified +samecollector exactprefix; begin_denial separatefreshroot, oneOPERATION_DECISION actionHANDOFF canonicalNOT_APPLICABLE originalSAFE_HALT/TERMINAL_NO_RECOVERY, REMAIN_SAFE_HALT directive; zero mainappend/math/provider/registry thereafter"
  },
  "field_paths": {
    "fixed": [
      "origin_assessment",
      "origin_validation",
      "source_binding",
      "profile_binding",
      "registry",
      "registry.source_binding",
      "registry.entries",
      "operation_context",
      "operation_context.context_observation",
      "operation_context.propagation_evidence",
      "operation_context.external_authority_evidence",
      "normalization_preparation",
      "normalization_preparation.plan",
      "normalization_preparation.plan_validation",
      "correction_observation",
      "correction_observation.submitted",
      "correction_observation.validation",
      "route_authorization",
      "applicability",
      "predicate_observation",
      "post_assessment",
      "post_assessment.classification_evidence",
      "post_assessment.system_context",
      "capture",
      "capture.admission",
      "capture.append",
      "capture.finish",
      "directive",
      "candidate_state",
      "action_decisions",
      "emitted_diagnostics",
      "registry.candidate_certifications",
      "registry_validation",
      "normalization_preparation.resolution_observation",
      "normalization_resolver",
      "correction_provider",
      "condition_evaluator",
      "post_facts_provider"
    ],
    "indexed_forms": [
      "chain[0..15]",
      "entries[0..31]",
      "entries[0..31].applicability_conditions[0..7]",
      "entries[0..31].validation_requirements[0..7]",
      "steps[0..767]",
      "post_assessments[0..32]",
      "action_decisions[0..34]",
      "registry.entries[0..31]",
      "registry.candidate_certifications[0..31]"
    ],
    "nested_assessment_paths": [
      "origin_assessment.source_binding",
      "origin_assessment.profile_binding",
      "origin_assessment.input_evidence",
      "origin_assessment.parsed_state",
      "origin_assessment.system_context",
      "origin_assessment.system_state_class",
      "origin_assessment.recovery_category",
      "origin_assessment.consulted_predicates",
      "origin_assessment.state_validity_diagnostic.input_state",
      "origin_assessment.state_validity_diagnostic.admissibility_status",
      "origin_assessment.state_validity_diagnostic.transformation_compatibility",
      "origin_assessment.state_validity_diagnostic.normalization_status",
      "origin_assessment.state_validity_diagnostic.recoverability_relevance",
      "origin_assessment.state_validity_diagnostic.is_valid",
      "origin_assessment.state_validity_diagnostic.orbit_info",
      "origin_assessment.state_validity_diagnostic.rule_ids",
      "origin_assessment.state_validity_diagnostic.notes",
      "origin_assessment.assessment_binding.assessment_reference",
      "origin_assessment.assessment_binding.original_input_reference",
      "origin_assessment.assessment_binding.diagnosis_reference",
      "origin_assessment.classification_evidence.correction_path_is_known.evaluation",
      "origin_assessment.classification_evidence.correction_path_is_known.value",
      "origin_assessment.classification_evidence.correction_path_is_known.reason",
      "origin_assessment.classification_evidence.correction_path_is_known.binding.assessment_reference",
      "origin_assessment.classification_evidence.correction_path_is_known.binding.diagnosis_reference",
      "origin_assessment.classification_evidence.correction_path_is_known.binding.subject_reference",
      "origin_assessment.classification_evidence.correction_path_is_known.binding.profile_id",
      "origin_assessment.classification_evidence.correction_path_is_known.binding.profile_source_sha256",
      "origin_assessment.classification_evidence.correction_path_is_known.binding.ash_dependency_id",
      "origin_assessment.classification_evidence.correction_path_is_known.binding.ash_aggregate_sha256",
      "origin_assessment.classification_evidence.correction_path_is_known.binding.evidence_reference",
      "origin_assessment.classification_evidence.fallback_is_available.evaluation",
      "origin_assessment.classification_evidence.fallback_is_available.value",
      "origin_assessment.classification_evidence.fallback_is_available.reason",
      "origin_assessment.classification_evidence.fallback_is_available.binding.assessment_reference",
      "origin_assessment.classification_evidence.fallback_is_available.binding.diagnosis_reference",
      "origin_assessment.classification_evidence.fallback_is_available.binding.subject_reference",
      "origin_assessment.classification_evidence.fallback_is_available.binding.profile_id",
      "origin_assessment.classification_evidence.fallback_is_available.binding.profile_source_sha256",
      "origin_assessment.classification_evidence.fallback_is_available.binding.ash_dependency_id",
      "origin_assessment.classification_evidence.fallback_is_available.binding.ash_aggregate_sha256",
      "origin_assessment.classification_evidence.fallback_is_available.binding.evidence_reference",
      "origin_assessment.emitted_diagnostics[0].diagnostic_reference",
      "origin_assessment.emitted_diagnostics[0].envelope.diagnostic_kind",
      "origin_assessment.emitted_diagnostics[0].envelope.severity",
      "origin_assessment.emitted_diagnostics[0].envelope.stage",
      "origin_assessment.emitted_diagnostics[0].envelope.disposition",
      "origin_assessment.emitted_diagnostics[0].envelope.subject_reference",
      "origin_assessment.emitted_diagnostics[0].envelope.parent_diagnostic_reference",
      "origin_assessment.emitted_diagnostics[0].envelope.chain_root_reference",
      "origin_assessment.emitted_diagnostics[0].envelope.rule_ids",
      "origin_assessment.emitted_diagnostics[0].envelope.summary",
      "origin_assessment.emitted_diagnostics[0].envelope.notes",
      "origin_assessment.emitted_diagnostics[1].diagnostic_reference",
      "origin_assessment.emitted_diagnostics[1].envelope.diagnostic_kind",
      "origin_assessment.emitted_diagnostics[1].envelope.severity",
      "origin_assessment.emitted_diagnostics[1].envelope.stage",
      "origin_assessment.emitted_diagnostics[1].envelope.disposition",
      "origin_assessment.emitted_diagnostics[1].envelope.subject_reference",
      "origin_assessment.emitted_diagnostics[1].envelope.parent_diagnostic_reference",
      "origin_assessment.emitted_diagnostics[1].envelope.chain_root_reference",
      "origin_assessment.emitted_diagnostics[1].envelope.rule_ids",
      "origin_assessment.emitted_diagnostics[1].envelope.summary",
      "origin_assessment.emitted_diagnostics[1].envelope.notes"
    ]
  },
  "rule_scopes": {
    "ASSESSMENT_RULE_IDS": "existing fixed6 unchanged",
    "NORMALIZATION_RULE_IDS": "existing fixed7 must be explicit standalone NormalizationDiagnosticRecord and every attempted/confirmed packet path before generic taxonomy extends",
    "N2_RULE_IDS": [
      "ASH-STATE-STRUCTURE-001",
      "ASH-STATE-VALIDITY-001",
      "ASH-STATE-GENERAL-001",
      "ASH-CODEWORD-STRUCTURE-001",
      "ASH-ADMISSIBILITY-CLASSIFICATION-001",
      "ASH-CLASSIFICATION-MAPPING-001",
      "ASH-RECOVERY-ACTION-001",
      "ASH-FALLBACK-SELECTION-001"
    ],
    "N2 mode handoff": "RECOVERY or FALLBACK kind only; no actual CONTAINMENT/HALT entry ID claimed",
    "meta": "STATE_VALIDITY DETECTION appropriate existing ASH-STATE-GENERAL-001, separate bounded artifact/cause trail no invented stateValidity row"
  },
  "main_envelope_mapping": {
    "actual XOR or predicate observation": "RECOVERY or FALLBACK; RECOVERY stage; severity max originfloor/priorfloor/current observed impact; PENDING",
    "completed recovered action": "RECOVERY or FALLBACK; RECOVERY; same nondecreased severity; RESOLVED",
    "completed ineligible candidate": "FALLBACK RECOVERY PENDING until whole selection resolves",
    "completed failed candidate": "FALLBACK RECOVERY BLOCKED before entryTRY_NEXT; no severity decrease later",
    "handoff request": "RECOVERY or FALLBACK ESCALATION ESCALATED; actual mode not entered",
    "existing SAFE_HALT denial": "separate boundary audit DETECTION root, no mainappend"
  },
  "completion_ports": {
    "Diagnostics.complete_assessment": "exact actual StateDiagnosis|StateAssessment|ClassificationEvidenceFailure|DiagnosticCaptureFailure required at referencecomposition; result-derived expectation table not freecount; receipt/failure separate originalpacket unchanged",
    "Diagnostics.complete_normalization": "exact actual N1 result/failure required; scope expectations derive typed branches including attemptedrecord/prefix, no batching or inferredfinish",
    "incomplete scope": "snapshot coverage OPEN/INCOMPLETE with reason; no healthy omission-free claim withoutcompletion",
    "compatibility": "legacy begin/append APIs retained; mandatory new referencecomposition wraps actual producer calls and completion; bypassed directcalls are explicitly uncovered untilcomplete",
    "RecoveryScope.finish": "exact tentative RecoveryValuePacket with completion_observation null; calledonce; actual typed branch expectations plus every linkedchild completion; no freecount",
    "finish failure": "Exact DiagnosticsCompletionReceipt and raw API_ONLY operation_reference must match current operation. Matching COMPLETE publishes final immutable packet with completion_observation receipt. Matching INCOMPLETE fills common completion_observation and sets secondary completion_failure_code COMPLETION_REJECTED. Wrong type/reference or thrown collaborator sets secondary COMPLETION_UNCONFIRMED; exact typed wrong-reference receipt retained in failure_detail.unconfirmed_completion_observation, common completion_observation null. If tentative result is already RecoveryFailure, preserve its original failure_detail/code/submitted_evidence/attempted_diagnostic/capture_status/pending_directive/reason unchanged; add only these secondary observations. If originally successful/handoff/no-action, create RecoveryFailure with primary completion failure code. No recursive finish, arbitrary object serialization or inferred acknowledgement."
  },
  "result_union": {
    "RecoveryNoAction": "NO_ACTION",
    "RecoveredValue": "RECOVERED_VALUE",
    "RecoveredFallbackValue": "RECOVERED_FALLBACK_VALUE",
    "RecoveryHandoff": "HANDOFF_REQUIRED",
    "RecoveryFailure": "FAILURE"
  },
  "byte_budget_status": "Frozen closed sanitized projection design bounds are measured, not production acceptance; actual implementation must enforce exact caps before effects. Full calculation/specimens in ywe-m3-n2-diagnostics-byte-bounds-20261004.json; protected host evidence separately scoped.",
  "reachability": "Current coherent UNSTABLE has AvailableProfile+TRANSFORMATION_COMPATIBLE hence nonempty T and actual pure N1 plan PLAN_READY. Abstract source no-path branch mathematically unreachable here. Only explicitly adopted typed resolution UNAVAILABLE invokes local blockedroute; None/throw/malformed provider produces collaboratorfailure. No forged UNSTABLE/noT vectors.",
  "registry_history_boundary": "N2 constructor binds/copies one immutable snapshot and exposes no reload/reassignment API. It verifies current duplicateIDs and exactentry/certification correspondence, not unseen historical globalID ownership. Source-history qualification remains external governedregistry ownership; no populated upstreamdataset supplied.",
  "type_aliases": {
    "SystemStateClass": "existing exact7classes",
    "RecoveryCategory": "existing exact7class/categorymap",
    "CanonicalContainmentTrigger": [
      "FALLBACK_FAILURE",
      "PROPAGATION_RISK",
      "OPERATOR_REQUEST",
      "RECOVERY_VALIDATION_FAILURE"
    ],
    "CanonicalSafeHaltTrigger": [
      "ESCALATION_FROM_FAILED",
      "CONTAINMENT_BREACH",
      "OPERATOR_HALT_REQUEST",
      "POLICY_HALT_REQUEST",
      "UNRESOLVABLE_BLOCKED_RECOVERY"
    ],
    "CanonicalCodeword": "exact existing fixedC16 full9bitstates; submittedKnownCorrection.chain onlyAshState untilpureproof",
    "N2RuleID": "exact8listed rule_scopes.N2_RULE_IDS",
    "RecoveryFieldPath": "exact finitefixed/nested list + declared bounded indexed grammar",
    "DiagnosticsCompletionReceipt": "exact Diagnostics owner receipt: COMPLETE|INCOMPLETE; original operation_reference UntrustedReference/API_ONLY, safely aliased on export; no freecount"
  },
  "denial_envelope": {
    "diagnostic_reference": "operation_reference+:denied",
    "diagnostic_kind": "STATE_VALIDITY",
    "stage": "DETECTION",
    "severity": "CRITICAL",
    "disposition": "BLOCKED",
    "parent_diagnostic_reference": null,
    "chain_root_reference": "exactdenialdiagnosticreference",
    "rule_ids": [
      "ASH-STATE-GENERAL-001",
      "ASH-RECOVERY-ACTION-001"
    ],
    "payload": "RecoveryActionDecision(action HANDOFF,canonical9 NOT_APPLICABLE,step_indicesempty,postrefnull,candidate_contextoriginal,directiveREMAIN_SAFE_HALT)",
    "relation": "outsideTEN parent_operation_reference/originating_chain_root_reference retained; original incident frozen/unmodified"
  },
  "canonical_step_action_literals": [
    "normalize",
    "correct",
    "validate-recovery",
    "select-fallback",
    "validate-fallback",
    "resolve-normalization",
    "resolve-correction",
    "evaluate-applicability",
    "evaluate-additional-validation",
    "handoff",
    "no-action",
    "fallback-summary"
  ],
  "canonical_step_action_ownership": "Explicit adopted local closed string representation. Canonical source RecoveryStep.action is prose/string, with examples normalize/correct/validate-recovery/select-fallback/validate-fallback; remaining literals label the already scoped resolve, predicate, handoff/no-action and summary facts.",
  "canonical_step_action_mapping": {
    "NORMALIZE_PLAN": "resolve-normalization",
    "NORMALIZE_XOR": "normalize",
    "CORRECTION_RESOLVE": "resolve-correction",
    "CORRECTION_XOR": "correct",
    "CANDIDATE_APPLICABILITY": "evaluate-applicability",
    "FALLBACK_SELECT": "select-fallback",
    "CANDIDATE_VALIDATION": "evaluate-additional-validation",
    "POST_ASSESSMENT": "validate-fallback for candidate; validate-recovery for normalize/correct",
    "HANDOFF": "handoff",
    "NO_ACTION": "no-action",
    "FALLBACK_SUMMARY": "fallback-summary"
  },
  "diagnostics_inventory_file": "docs/architecture/m3_reference_diagnostics_contract.md#exact-interface-inventory",
  "byte_bounds": {
    "largest_event_leaf_assembly": 9512,
    "source_profile512": 6429,
    "post_assessment2emissions": 5779,
    "canonical_action_summary32steps": 12170,
    "incident768timeline_attempt_state_refs": 18124,
    "health16ranges": 7174,
    "largest_meta_leaf_assembly": 2156,
    "support16profiles66assessments35diagnostics_full_proofs": 1459252,
    "incidents32": 580001,
    "private_alias6144x256": 1671169,
    "operation768_events_plus_support_incidents_health": 9386993,
    "markdown_full_appendix": 9448492
  },
  "byte_reservation": {
    "new_events": 25165824,
    "supporting": 2097152,
    "incidents": 1048576,
    "private_aliases": 2097152,
    "health": 65536,
    "inherited_origins": 65536,
    "identity_envelope": 1048576,
    "reservation_total": 31588352,
    "collector_total": 33554432,
    "remaining_margin": 1966080,
    "json": 33554432,
    "markdown": 50331648,
    "manifest": 65536,
    "protected_disk_total": 134217728,
    "single_pair_total": 83951616,
    "capture_plus_single_pair": 117506048,
    "logical_serialized_buffer_total": 201326592,
    "meta_pool": 49152,
    "health_status": 8192,
    "fallback_health": 8192
  },
  "denial_reservation": {
    "new_events": 1,
    "new_aliases": 64,
    "event_bytes": 32768,
    "supporting_bytes": 32768,
    "incident_bytes": 32768,
    "alias_bytes": 32768,
    "health_bytes": 65536,
    "inherited_origin_bytes": 65536,
    "identity_bytes": 8192,
    "total_bytes": 270336
  }
}
```

## Reviewed source inventory

These exact source digests were verified before adoption against publication `4c01af5b01b4690da5cd2a97d5e6025e97a48e1c`. Raven Forge method authority remains v0.7.0 at `87409bc36fb9d4782eab02189adb184f2b3962a7`; earlier method revisions remain historical evidence. No code reads ambient source files during a Core operation.

```json
{
  "repository_revision": "5328f018f341b80ad58cdb82f64708992ee2d6ae",
  "hash_algorithm": "sha256_utf8_lf_normalized",
  "source_pins": [
    {
      "path": "core/ash_pattern_engine/canonical/interfaces/contracts/recovery-engine-contract.md",
      "sha256_utf8_lf_normalized": "27ffacc6218812b280ed236bf9052ee825e903498365d735bf57ee9cb338955b"
    },
    {
      "path": "core/ash_pattern_engine/canonical/interfaces/contracts/diagnostics-module-contract.md",
      "sha256_utf8_lf_normalized": "88b8d682fa826f128787e6154151c68b32d677239e17ddf4344a084461554a37"
    },
    {
      "path": "core/ash_pattern_engine/canonical/registries/fallback-policy-registry.md",
      "sha256_utf8_lf_normalized": "b108d6c4127da9ea375899e97c34048ded4ea3a7cb624ef24f18bfda5f8deaaa"
    },
    {
      "path": "core/ash_pattern_engine/canonical/algorithms/recovery-fallback-semantics.pseudo.md",
      "sha256_utf8_lf_normalized": "0fb8a0750acae0fb263cd842e186ff35881f77b8e498a8f11f159a5d2db270b7"
    },
    {
      "path": "core/ash_pattern_engine/canonical/algorithms/containment-safe-failure-semantics.pseudo.md",
      "sha256_utf8_lf_normalized": "83f1a19c1a0f375e02f2044c238786514d64b122ab6ab5a8bda6e6fa307c8256"
    },
    {
      "path": "core/ash_pattern_engine/canonical/core/recoverability-semantics.pseudo.md",
      "sha256_utf8_lf_normalized": "cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd"
    },
    {
      "path": "core/ash_pattern_engine/canonical/core/system-state-classification.pseudo.md",
      "sha256_utf8_lf_normalized": "806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff"
    },
    {
      "path": "core/ash_pattern_engine/canonical/core/state-validity-diagnostics.pseudo.md",
      "sha256_utf8_lf_normalized": "20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e"
    },
    {
      "path": "core/ash_pattern_engine/canonical/interfaces/diagnostic-schema.md",
      "sha256_utf8_lf_normalized": "825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7"
    },
    {
      "path": "core/ash_pattern_engine/canonical/interfaces/rule-id-taxonomy.md",
      "sha256_utf8_lf_normalized": "f5ccaf3063dfe3df749f42dbe4659449a1874a6074e1d8d28ab4cad4a462f892"
    },
    {
      "path": "core/ash_pattern_engine/state_values.py",
      "sha256_utf8_lf_normalized": "c4259a3d3f719351ebe12067a6e306bbcdc76688208bf145aab99f5f7df637c9"
    },
    {
      "path": "core/ash_pattern_engine/state_model.py",
      "sha256_utf8_lf_normalized": "16de13e13c0c60c4b7fbf40a0e9339d022f6a367dc89ac6a3f3650e3548fb594"
    },
    {
      "path": "docs/architecture/m3_state_assessment_contract.md",
      "sha256_utf8_lf_normalized": "e60f6b1cd6a338e009e4431a814bb233dd5bbd4f5b9c6a5698a87c356ae638ac"
    },
    {
      "path": "docs/architecture/m3_normalization_contract.md",
      "sha256_utf8_lf_normalized": "02900b57c4b90475f11aa92a46caf90243b82d2bf1b273231f2f54acc9ebd1be"
    },
    {
      "path": "docs/architecture/m3_normalization_policy.md",
      "sha256_utf8_lf_normalized": "804eec92cf52b465b7aaf0cb5f139f581ac2899d13203a8c4cfe9f4d7579c383"
    }
  ],
  "canonical_dependency_inventory": {
    "source_root": "core/ash_pattern_engine/canonical",
    "excluded_source_paths": [
      "README.md"
    ],
    "text_normalization": "utf8_optional_bom_crlf_cr_to_lf_preserve_final_newline",
    "aggregate_algorithm": "sha256_sorted_relative_path_nul_file_sha256_lf",
    "files": [
      {
        "relative_path": "algorithms/averaging-operator-semantics.pseudo.md",
        "sha256": "c5e2b9a6ca20118bbe887eae5d172ead0b9d46e5adb0fc7a68f5682ae4e10c36"
      },
      {
        "relative_path": "algorithms/axiom-evaluation.pseudo.md",
        "sha256": "0f205842840399aaf08932e20cde34761874a3296b260f139dc6a04df0e707ba"
      },
      {
        "relative_path": "algorithms/branching-semantics.pseudo.md",
        "sha256": "e8344b2d25b33875986e59e43809af460af25b5e319fa861e2670589083f5c57"
      },
      {
        "relative_path": "algorithms/codeword-transformation-semantics.pseudo.md",
        "sha256": "80623862ac8dfe72bdecea670f15f4f339c0096da1f63b9058a73458eeedd88e"
      },
      {
        "relative_path": "algorithms/containment-safe-failure-semantics.pseudo.md",
        "sha256": "83f1a19c1a0f375e02f2044c238786514d64b122ab6ab5a8bda6e6fa307c8256"
      },
      {
        "relative_path": "algorithms/generation-planning.pseudo.md",
        "sha256": "88d474a4e25e297ef59f28245bc6a0f4cfa375d4173433240d993639d8e30ec1"
      },
      {
        "relative_path": "algorithms/recovery-fallback-semantics.pseudo.md",
        "sha256": "0fb8a0750acae0fb263cd842e186ff35881f77b8e498a8f11f159a5d2db270b7"
      },
      {
        "relative_path": "algorithms/topology-expansion.pseudo.md",
        "sha256": "1b6ab5d3d13b678c67f185f2f91a60d0dae7a976dcbb6df2b169efa6d15c9a3d"
      },
      {
        "relative_path": "algorithms/transition-system.pseudo.md",
        "sha256": "26c456f60fbb5c847714c4a9a49cf8d11ac48ef0a7d0c127da53bd893dd527c2"
      },
      {
        "relative_path": "core/ash-state-space.pseudo.md",
        "sha256": "68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e"
      },
      {
        "relative_path": "core/codeword-set.pseudo.md",
        "sha256": "8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c"
      },
      {
        "relative_path": "core/realm-identity.pseudo.md",
        "sha256": "43f274d9c8c1b7269938bf8661c42e91cf020d215683cb6dfa4b340ff975cad5"
      },
      {
        "relative_path": "core/recoverability-semantics.pseudo.md",
        "sha256": "cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd"
      },
      {
        "relative_path": "core/state-admissibility.pseudo.md",
        "sha256": "5d9231331849a6359a8d8e537d0434ee78787bb14efe5da03f60e68ba3c1978e"
      },
      {
        "relative_path": "core/state-validity-diagnostics.pseudo.md",
        "sha256": "20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e"
      },
      {
        "relative_path": "core/system-state-classification.pseudo.md",
        "sha256": "806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff"
      },
      {
        "relative_path": "interfaces/contracts/artifact-emitter-contract.md",
        "sha256": "cca1c794405f2d85c80f5de2e1efd6a8f1bc395985a39ebf7ebc6daf64b53243"
      },
      {
        "relative_path": "interfaces/contracts/axiom-evaluator-contract.md",
        "sha256": "dc2edf80d2ded0b89b31df15416e24c13139988ab6fd38adaa6195921a692faf"
      },
      {
        "relative_path": "interfaces/contracts/diagnostics-module-contract.md",
        "sha256": "88b8d682fa826f128787e6154151c68b32d677239e17ddf4344a084461554a37"
      },
      {
        "relative_path": "interfaces/contracts/generation-planner-contract.md",
        "sha256": "09f2a6c99fa4b39484e5c5497103b3e09d274a6ddfda2c97dc9eba5cfd685708"
      },
      {
        "relative_path": "interfaces/contracts/realm-encoder-contract.md",
        "sha256": "b3fa0deb71ae136c712f402f2b8159b7448ef8756a884369931ab7098bc83fbb"
      },
      {
        "relative_path": "interfaces/contracts/recovery-engine-contract.md",
        "sha256": "27ffacc6218812b280ed236bf9052ee825e903498365d735bf57ee9cb338955b"
      },
      {
        "relative_path": "interfaces/contracts/state-model-contract.md",
        "sha256": "02193e701bf4e565ca92dbcea05b7c7420cc0926e0d0c90e9d4bedd163972ab8"
      },
      {
        "relative_path": "interfaces/contracts/topology-generator-contract.md",
        "sha256": "a408b335ecacff01e38113bcd6cc6089142e40219d521e7081e87406fac11147"
      },
      {
        "relative_path": "interfaces/contracts/transition-registry-contract.md",
        "sha256": "f123b02c3390253cba5f50a04e9c69e9c20771c6dc7cff5bcdc7a3c85aa6471f"
      },
      {
        "relative_path": "interfaces/diagnostic-schema.md",
        "sha256": "825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7"
      },
      {
        "relative_path": "interfaces/rule-id-taxonomy.md",
        "sha256": "f5ccaf3063dfe3df749f42dbe4659449a1874a6074e1d8d28ab4cad4a462f892"
      },
      {
        "relative_path": "interfaces/semantic-contracts.md",
        "sha256": "c2b965d3155443d45421542056b1fb2934df00a0d858542aaf26c4bacf4c97d3"
      },
      {
        "relative_path": "registries/fallback-policy-registry.md",
        "sha256": "b108d6c4127da9ea375899e97c34048ded4ea3a7cb624ef24f18bfda5f8deaaa"
      },
      {
        "relative_path": "verification/conformance-categories.md",
        "sha256": "979f287e3521a750997814d1bc3a85893433ce885cde6669c919511656799bf2"
      },
      {
        "relative_path": "verification/implementation-acceptance.md",
        "sha256": "7d26c54bca61f92fc054b2b03e65c0634afb66449d5d100dc254ea47ac5f4028"
      },
      {
        "relative_path": "verification/invariant-spec.md",
        "sha256": "2b7dbd52b539810b3f957ed23bcbcd7fffd068b3f01ea43f24b51a0e8f98866b"
      }
    ],
    "aggregate_sha256": "0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb",
    "verified_against": "data/governance/ash_dependency_identity.json"
  }
}
```
