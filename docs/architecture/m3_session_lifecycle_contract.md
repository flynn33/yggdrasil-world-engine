# M3 reference session lifecycle contract

Contract identity: YWE-M3-SESSION-LIFECYCLE-001
Contract version: 1.0.0
Status: active N3 contract, adopted October 11, 2026 before dependent implementation. Implementation and runtime verification remain outstanding.
Owner and partition: ywe_core.
Requirement: [YWE-REQ-0044]. Decisions: ADR-0033 and ADR-0034.
Adoption amendment: actual fresh-origin failure unions and safe unavailable-facts projection, October 11, 2026, before dependent implementation.
Direction: YWE-DIRECTION-20261009-AUTONOMOUS-N3.
Preparation source: 0949184b7f1be0960fec9dd409cbf09647921e61.
No historical external review or approval is asserted.

## 1. Scope and evidence boundary

This contract defines reference session publication, containment entry, explicitly authorized containment exit, deliberate halt, terminal enforcement and complete bounded Diagnostics correlation. It completes the N3 allocation of actual effects described by the N2 recovery policy. It does not supply ordinary TransitionRegistry behavior, native execution, persistence/resume, multiplayer, physical propagation, authenticated operators, complete M3 exit or M4 behavior.

The source-owned obligations remain in:
- core/ash_pattern_engine/canonical/interfaces/contracts/recovery-engine-contract.md;
- canonical/interfaces/diagnostic-schema.md;
- canonical/algorithms/recovery-fallback-semantics.pseudo.md;
- canonical/algorithms/containment-safe-failure-semantics.pseudo.md;
- canonical/interfaces/rule-id-taxonomy.md.

The current local owners and adopted witnesses are StateModel and state_values; RecoveryEngine and recovery_values; FallbackRegistry; ReferenceDevelopmentDiagnostics/ReferenceReleaseDiagnostics and diagnostics_values; the N1/N2, source-compatibility and reference-Diagnostics contracts, schemas, examples and tests. The actual relevant APIs read for this contract are StateModel.validate_assessment, inspect_state and assess; RecoveryEngine.recover and _RecoveryOperation.run/_post/_finish; Diagnostics._append/_complete/recovery_capture/assessment_capture/complete_assessment; DiagnosticEvent._coherent; state_values.canonical_source_baseline; RecoverySourceBinding and its paired seven-pin vector.

The independent policy file is [m3_session_lifecycle_policy.md](m3_session_lifecycle_policy.md). Its adopted LF UTF-8 bytes have SHA256 24e2584279b95b8e3659bd61e6b5149311f344b03b981e88f74ae37775591910. The exact policy binding and compiled implementation constant must match those bytes. Pure binding recognition never means host bytes were verified. Frozen proposal provenance and adoption edits are recorded in [the companion artifact index](../design-planning/m3/session-lifecycle/ARTIFACT_INDEX.json).

The complete normative business inventory is [BUSINESS_API_INVENTORY.json](../design-planning/m3/session-lifecycle/BUSINESS_API_INVENTORY.json). All its exact named fields, finite domains, limits, tagged unions and ports are part of this contract. The complete safe projection and structural capacity inventory are the companion [SAFE_FIELDS_AND_LIMITS.json](../design-planning/m3/session-lifecycle/SAFE_FIELDS_AND_LIMITS.json), [CAPACITY_AND_RETENTION.md](../design-planning/m3/session-lifecycle/CAPACITY_AND_RETENTION.md) and [BOUND_REPORT.json](../design-planning/m3/session-lifecycle/BOUND_REPORT.json). Source-owned values are reused with their exact existing fields; references to them are not replacement schemas. This prose defines semantic cross-field guards and execution order. Companion edits must reconcile the whole inventory before code acceptance.

## 2. RecoveryEngine ownership and composition

RecoveryEngine remains the single public recovery/lifecycle authority required by its canonical module contract. Its constructor retains the existing seven positional collaborators and accepts only the additive optional keyword lifecycle_owner=None. None preserves existing standalone behavior. A supplied ReferenceSessionLifecycle must be the exact class, configured with the identical StateModel and exact Development/Release Diagnostics collector used by that engine, the current policy binding and one session capacity.

RecoveryEngine creates one private per-engine identity capability and binds the collaborator exactly once. This is composition within its semantic ownership, not two competing public authorities. ReferenceSessionLifecycle has no independent public mutation API; its controlled _execute and assessment calls require that exact engine capability and exact privately issued session identity. It owns the lifecycle lock, current immutable snapshot pointer, current accepted assessment association, current lease phase, bounded request ledger, immutable result/history DAG, terminal flag, current main phase and membership seal. It does not read peer-private model/provider/collector members.

ReferenceSession is an exact privately issued facade. read, execute and history delegate solely to its issuing engine. A copied facade, guessed identity, copied/wire lease or equality of an otherwise valid value does not establish issuance. In-process reflection by privileged Python code is outside this reference capability boundary. No global registry or second publication provider is introduced.

New owned implementation files are core/ash_pattern_engine/session_values.py and session.py. New value constructors and schemas are closed: exact primitive/class checks, finite enums, bounded tuples, required fields, no unknown properties. References derive deterministically from caller request references; randomness supplies no diagnostic meaning. Exact complete canonical/profile/policy bindings are immutable throughout a session.

## 3. Source guard, opening and initial association

Before any N3 Diagnostics registration, reservation, clock, provider, mode change or publication:
1. Revalidate exact structural SessionBinding and all nested owned values.
2. Require state_values.canonical_source_baseline(binding.canonical_binding) == N3_LIFECYCLE.
3. Require the full canonical binding equals the current StateModel binding; its paired RecoverySourceBinding has the exact seven SourcePin path/hash pairs for that same complete vector.
4. Require the full current profile binding and exact policy ID/version/path/hash.
5. Require origin.parsed_state to be exact AshState; reject coherent malformed/unparsed assessments before registration. Require StateModel.validate_assessment(origin).status == VERIFIED, exact state and full source/profile agreement, SystemContext(false,false), two actual Detection/Classification emissions and a complete same-collector acknowledgment/completion association.
6. Require binding.initial_assessment_reference equals the exact origin assessment reference.

No aggregate-only check, legacy fixed rule subset mutation or borrowed same-state packet is sufficient. Invalid typed inputs raise SessionContractError before a session exists or any N3 effect. Host construction must verify the actual adopted source files and policy bytes; the pure owner does not claim that verification itself.

A valid open_session creates a semantic session before attempting collector registration. Initial generation is zero, mode NORMAL, terminal_latched false, no containment/halt/active operation reference, recovery_attempted false. Its current assessment reference and observed class are the actual initial assessment and actual class. FAILED is an observed class in a running NORMAL session; it is not a fourth session mode or an implicit halt.

Diagnostics.register_session/attach_result must confirm the actual initial origin prefix before ordinary admission is OPEN. If registration, clock or attachment is rejected/unconfirmed, the returned facade still exists with AUDIT_BLOCKED and the actual SessionRetentionReceipt. This permits required authorized halt when observation fails. No ordinary recovery/publication/exit is authorized while audit is blocked. Finalizing leases remain exclusive through lifecycle completion and once-final observation; ordinary admission resumes only after those are confirmed and the owner releases that exact lease. The source guard is still enforced because the owner was structurally created only with a valid complete current binding.

## 4. Immutable snapshots and live assessment freshness

SessionSnapshot contains its unique snapshot_reference, full SessionBinding, checked uint64 generation, current_state, mode, terminal_latched, admission_status, containment_reference, halt_reference, recovery_attempted, active_operation_reference, current_assessment_reference and observed_system_state_class.

The owner associates a complete assessment with a particular state/mode publication generation, actual context and exact private observation provenance. A current pointer is populated only if that actual assessment has complete same-collector capture and once completion, full current bindings, correct parsed state and SystemContext reflecting the current mode. The observed class comes from that actual assessment. It is never inferred from mode. current_assessment_reference and observed_system_state_class are null while a newly published generation has not been actually assessed and in terminal state. At halt, mode=SAFE_HALT is actual owner truth even though no new StateModel class is fabricated.

The initial origin is associated with generation zero. Successful recovery can associate an actual complete N2 candidate postassessment with the newly published generation after the owner proves its candidate/context exactly match the resulting NORMAL snapshot. A stable no-action command does not substitute an unrelated child as the current live origin. Actual post-containment and post-resolution assessments establish the next association after their publication. Once state or context changes, an older same-state assessment never regains membership by value equality.

SessionContextObservation independently records the exact snapshot and owner observation: is_running is false only at SAFE_HALT, is_contained matches CONTAINED, is_halted matches SAFE_HALT, and subject_state equals snapshot.current_state. It is actual before/admission context, not evidence that a candidate state is already live.

The owner tracks a distinct lifecycle main phase root and last main TEN record. It is separate from the current assessment pointer. A contained postassessment truthfully classifies the contained state on its own child root while the main phase's last lifecycle record remains CONTAINMENT. A confirmed successful resolution starts a new normal main phase from its new actual Detection/Classification root. Typed metadata links phases without changing TEN.

## 5. Commands, bounded parsing, admission and replay

The four exact command variants are SessionRecoveryRequest, SessionContainmentRequest, SessionResolutionRequest and SessionHaltRequest. Their primary SessionRequest carries the full expected snapshot, exact session reference, bounded request reference, closed action and bounded reason. Authority and boundary observations carry raw request/expected-snapshot references only. They never carry duplicate nested full requests or arbitrary evidence dictionaries. Every such reference must match the primary validated command before complete projection.

Terminal checking is the first execute operation after validating only the privately issued facade identity. It occurs before accessing the supplied caller object's fields, repr, equality hooks, to_record, iterators, authority evidence or replay cache. A terminal denial has request_reference=null and NOT_INSPECTED_AT_TERMINAL. It reports the actual frozen snapshot. The first sixteen denials can produce individually retained separate denial roots; later calls mint no new arbitrary aliases or retained per-attempt body and report ordinal/reference absent with explicit limit/unconfirmed coverage and bounded saturated counters.

Preterminal commands are checked by exact class and owned boundary validators. Malformed caller objects raise SessionContractError with registered code/field only; no arbitrary object or exception text is attached to retained business values. Once exact bounded input is validated, rejected admission can retain that exact command within the eighteen-entry ledger. At command quota exhaustion, further refusal returns a compact denial/limit observation without adding a request-body graph or minting arbitrary reference aliases. Invalid primitive shape and bounded valid refusal are distinct paths.

Mode gates precede replay. CONTAINED refuses ordinary recovery and publication; only reads, diagnostic export, explicitly authorized resolution and halt remain. AUDIT_BLOCKED permits reads and valid mandatory halt, not ordinary publication or exit. A previously successful normal request cannot replay an effect through a new contained or terminal boundary.

For a valid current command, full expected-snapshot equality compares every scalar, full binding, state, mode, terminal flag, generation, reference, audit flag and live assessment association before grant. Exact repeated command/reference values in a still-permitted mode return SessionReplayObservation(original_result,current_snapshot,session_effects_performed=false) with no new effect/event/reservation/alias. A conflicting duplicate returns SESSION_OPERATION_DUPLICATE; a currently running identical reference returns SESSION_OPERATION_IN_PROGRESS.

At most one ordinary command lease is live. Its SessionOperationLease contains immutable before and the distinct owner-issued active_snapshot. Active admission changes snapshot identity and active_operation_reference without claiming state/mode publication. The private owner retains exact lease issuance and current phase baseline. Publication compares against that issued baseline, not against the caller before snapshot whose active_operation_reference was null. Refusal/release produces another distinct snapshot identity; generation measures state/mode publications and never wraps. A halt may revoke the current lease. Other competing ordinary commands are refused.

## 6. Execution gates, lock order and cancellation

A gate is exact, private, non-wire, per-command and bound to the issuing engine/session/lease. A StageGrant is audit-local API metadata, not a serializable authority or new event. It has a checked ordinal below8192, a closed stage, grant/cancel status, lease reference and observed generation.

Before every following registry call, capture begin, normalization resolver, correction provider, condition evaluator, post-facts provider, full-vector candidate computation, assessment begin/append/complete and ordinary capture append, the operation requests a fresh stage grant. The owner checks exact issuance, lease identity, full current phase snapshot, generation, terminal flag and permitted mode atomically under the lifecycle lock. The uncontrolled stage runs outside that lock. The operation rechecks before interpreting a return into another stage or live publication. A stage already granted can complete; physical preemption is not asserted.

The initial phase uses lease.active_snapshot. After an actual mode publication, the owner installs a new committed active snapshot and advances the gate's private phase baseline so the required actual post-mode assessment may run. The immutable lease retains the original admission snapshot. No caller can advance this phase. Halt revokes every nonterminal phase regardless of whether a callback was in flight.

RecoveryEngine.recover adds only keyword execution_gate=None. None preserves existing standalone results and scheduling. An issued session gate yields truthful additive RecoveryFailure failure_code SESSION_EXECUTION_CANCELLED, field execution_gate, when revoked/stale before a following stage. This is not COLLABORATOR_FAILED, INTERNAL_INVARIANT_FAILURE or mathematical no-path. recovery_values.FAILURE_CODES and FIELD_NAMES, the recovery value schema and Diagnostics safe failure/code mappings receive the exact additive values; old fixture witnesses and fixed rule subsets remain unchanged.

The existing Diagnostics.recovery_capture and assessment_capture ports gain the additive optional execution_gate keyword. With gate=None, RecoveryEngine continues the old call shape without new kwargs so legacy injected collaborators remain compatible. With an issued session gate, the exact reference collector stores it on the actual scope; post-IO checks use that trusted scope association. complete_assessment keeps its existing signature and uses the scope-bound gate/cleanup state. Session-origin and post-mode captures carry the exact SessionChildLink/SessionAssessmentLink relation; old PostAssessmentLink remains unchanged for standalone N2.

The existing _RecoveryOperation.run still invokes scope.finish exactly once whenever a scope was admitted. Cancellation prevents further ordinary grants but cannot skip that finalizer. Cleanup has an explicit once-only permission distinct from stage_grant: it can release the reservation and retain the actual interrupted result, attempted prefix and actual completion response in a separate correlated audit. It cannot invoke further recovery providers, create a live candidate publication or add a frozen main member. Fresh origin assessment completion likewise runs once if that assessment scope was admitted.

No lifecycle lock is held while entering Diagnostics or any uncontrolled callback. Collector-owned trusted code invokes no lifecycle execution callback. Injected clock/store callbacks may reenter the owner while the existing collector IO lock is held; mandatory terminal nonblocking acquisition and external-callback IO-depth refusal support that path explicitly. A collector reads trusted phase/seal state only through SessionExecutionGate.capture_disposition, distinct from stage_grant. It uses an independent tiny nonblocking token lock and returns ACTIVE, SEALED or UNAVAILABLE without acquiring the lifecycle lock, issuing grants, invoking callbacks or entering owner execution. The owner updates that immutable token during lifecycle-locked phase changes and halt; token readers never request the lifecycle lock. Session terminal/denial/freeze/final observation ports acquire the collector nonblockingly and refuse reentrant external-callback IO. Busy acquisition returns NOT_CONFIRMED without waiting. This prevents an outer store/clock callback that waits for halt from deadlocking a halt that waits for that callback's collector lock.

Session-owned collector code rechecks the gate/seal after every uncontrolled clock/store callback and before acknowledging an ordinary append into the main graph. A physical late write is retained as actual late or unknown-storage evidence; it is not relabeled absent or confirmed main membership. Existing standalone behavior is preserved when no session gate is present. IO sequence reservation and charging state must not be overwritten by reentrant lifecycle capture; the busy-port refusal is part of acceptance tests.

## 7. Fresh recovery child assembly and N2 delegation

SessionRecoveryRequest.origin_assessment must be the exact owner-associated live assessment identified by its expected snapshot and generation. It is not already the N2 child. Its RecoveryOperationContext has:
- operation_reference equal to the SessionRequest reference;
- origin_assessment_reference equal to request_reference + ':origin:assessment';
- actual clear SystemContext(false,false);
- propagation and external-authority evidence already bound to that same operation and fresh origin reference.

The fresh DiagnosticContext is derived deterministically as request_reference + ':origin:assessment', ':origin:input', ':origin:detection', ':origin:classification'. The action reference is request_reference + ':origin'. No declaration is silently rebound to these references.

After grant, the engine-owned _assess_session_origin port uses the existing post_facts_provider.provide signature: candidate=actual current_state, origin=accepted live origin, action_reference=derived origin action, diagnostic_context=fresh context, operation_context=submitted fresh-bound operation context. This is an explicit N3 use of the existing provider. It does not modify standalone N2 _post behavior. The provider must return exact PostAssessmentFacts with that fresh DiagnosticContext, actual clear context and each predicate's complete fresh assessment/diagnosis/subject/profile/canonical binding. It must evaluate the consulted predicates rather than copy old truth. An exact UnavailablePostAssessmentFacts retains its source and candidate/operation facts; wrong-type, mismatched context or exceptions produce SESSION_COLLABORATOR_FAILED without arbitrary object retention.

A stage-gated StateModel using the same full profile/canonical bindings performs actual assessment through Diagnostics.assessment_capture. Diagnostics.complete_assessment is called exactly once on the actual StateAssessment/ClassificationEvidenceFailure/DiagnosticCaptureFailure. Only exact StateAssessment plus matching COMPLETE and current validate_assessment VERIFIED establishes a fresh child. Actual failure and unconfirmed completion remain retained; no N2 recover starts. SessionOperationResult.origin_assessment retains the exact StateAssessment, ClassificationEvidenceFailure or DiagnosticCaptureFailure returned by the actual child, or null if no child exists. An exact UnavailablePostAssessmentFacts is retained as SessionFailureDetail.primary_evidence with origin_assessment=null, never substituted for an assessment. Its safe inline projection retains operation, candidate and source provenance with explicit reason omission. Partial child failures retain actual emitted/attempted prefixes and once-completion observations without claiming a complete assessment supporting node. That child scope has completed/released before N2 reserves its own scope.

SessionChildLink records the session binding, admitted generation, accepted live-origin assessment, fresh child origin and N2 operation. The link is support metadata outside TEN; it does not fabricate a source parent. The collector attaches the actual confirmed child and then RecoveryEngine.recover runs the existing N2 rule/value owner with the private gate. No N3 scope or incident reservation coexists with its N2 reservation.

The actual returned N2 packet and its completion are retained once, including all child postassessments and failures. Matching COMPLETE alone is insufficient for publication: the owner validates the full result variant, origin/source/profile/operation/child association, actual candidate_state, actual complete postassessment and STABLE/VALID/current NORMAL context. A nonlifecycle publication/no-action bridge uses SessionCauseObservation.kind=N2_RESULT with trigger=null and a mandatory actual owner-retained recovery operation reference. Safe projection preserves this null rather than inventing a lifecycle trigger. A RecoveryNoAction does not publish a new state; a RecoveredValue or RecoveredFallbackValue may publish only the certified candidate under the exact still-live lease. A RecoveryHandoff requests actual containment/halt/external authority according to its actual directive. A RecoveryFailure causes no live recovery publication.

Propagation RISK and UNAVAILABLE follow existing N2 semantics and produce their actual handoff evidence. FAILED plus actual UNREACHABLE may direct ESCALATION_FROM_FAILED; FAILED with REACHABLE/UNAVAILABLE requests external authority rather than inventing a halt. The session exposes that actual result and blocks unapproved state effects. Caller command references to earlier N2 work resolve only in the owner-held maximum-two actual result registry; no caller packet is accepted.

## 8. Publication and containment entry

Ordinary recovery publication and containment entry require fixed lifecycle admission before any state/mode CAS. The N2 scope has already finished. The owner requires complete origin/main prefix, exact source/profile/policy and private lease, raw serialization preflight, declared quota and captured scope capacity. Capture admission failure causes no ordinary publication. If a source-required containment handoff cannot reserve, the owner reports the actual incomplete boundary and blocks ordinary admission; it may execute a distinct actual POLICY_HALT_REQUEST decision under this policy, consuming the reserved terminal slot. It does not claim that a reservation failure proves CONTAINMENT_BREACH or mathematical no-path.

The atomic publication assigns the new immutable state/mode snapshot under the lifecycle lock, increments generation within its terminal-reserved range and records known session_effects_performed=true. Storage uncertainty afterward does not make a known in-memory commit unknown. SessionPublication.status remains COMMITTED with the actual committed snapshot; overall SessionOperationResult can be UNCONFIRMED because capture/retention failed. Failed precommit CAS is NOT_COMMITTED with effects=false. A readback that truly cannot establish an effect retains UNCONFIRMED/null; it is never guessed from receipt failure.

For each actual containment entry, the cause is one of:
| Trigger | Required actual evidence | Rule |
|---|---|---|
| FALLBACK_FAILURE | owner-retained complete N2 handoff directing ENTER_CONTAINMENT/FALLBACK_FAILURE | ASH-CONTAINMENT-TRIGGER-001 |
| PROPAGATION_RISK | owner-retained N2 RISK handoff or matching SATISFIED PROPAGATION_RISK boundary | ASH-CONTAINMENT-TRIGGER-002 |
| OPERATOR_REQUEST | matching AUTHORIZED OPERATOR/POLICY observation or actual recognized policy decision | ASH-CONTAINMENT-TRIGGER-003 |
| RECOVERY_VALIDATION_FAILURE | actual failed N2 recovery postvalidation and matching handoff/boundary | ASH-CONTAINMENT-TRIGGER-004 |

Boundary UNAVAILABLE is preserved as unknown, not SATISFIED. Route/trigger strings alone are insufficient. Full nested reference/source observations must match the primary command. A source/profile/policy mismatch fails before reservation or effect.

The main chain receives an actual zero-step RecoveryDiagnostic bridge describing this session handoff, then exact ContainmentDiagnostic. The bridge uses the main historical original assessment's actual class/category and StateValidityDiagnostic, steps=(), outcome ESCALATE_TO_CONTAINMENT and actual cause/publication support; it does not claim math/provider work. Containment payload retains its exact nine fields, restricted_operations exact five declared operations, awaiting_resolution=true, resolution=PENDING and actual measured containment clock.

A new actual StateModel assessment is then made under the committed contained snapshot. Because actual SystemContext(false,true) causes CONTAINED before any predicate branch, newly bound NotEvaluatedPredicate records explicitly state that no predicate was consulted. It is an independent actual two-event child pair captured under the same four-slot lifecycle reservation (bridge + containment + pair). It does not replace the main CONTAINMENT predecessor. Only matching once completion confirms the current assessment association. Failure leaves actual contained mode, assessment fields null, AUDIT_BLOCKED and explicit attempted/partial coverage. Halt remains available.

## 9. Direct authorized containment resolution

Resolution is implemented, not deferred. It does not rerun N2 under a fictional NORMAL system context. The exact primary expected snapshot must be actual CONTAINED, nonterminal, audit-complete and identify the current containment record. The authority and every boundary reference must match that full snapshot/request.

For OPERATOR_INTERVENTION/REPLACE_STATE, authority is AUTHORIZED with origin OPERATOR. For POLICY_DRIVEN/REPLACE_STATE, origin is POLICY. Both require target_state, matching SAFE PropagationEvidence (operation reference=command reference, origin assessment=current actual contained assessment reference), and a matching SATISFIED CONTAINMENT_CLEAR boundary. Full propagation source reference/hash/evidence identity is retained. Null, RISK or UNAVAILABLE cannot clear containment.

StateModel.validate_resolution_target is a pure new owner operation: exact AshState, current full source/profile bindings, inspect_state mathematics and prospective SystemContext(false,false); status VERIFIED only when target diagnostic is VALID/is_valid=true, target matches input_state, expected class STABLE and category NO_ACTION. A prospective context is labeled prospective and cannot be recorded as current context. The source target validity proof is newly computed even if the same bits were earlier N2-certified; old certification alone does not prove current authorization/freshness.

Before CAS, fixed lifecycle scope admission and raw result/history/anticipated-terminal preflight succeed. Under the lifecycle lock, the owner rechecks full active phase snapshot, exact issued lease, current containment identity, source/profile/policy, authorization, SAFE propagation, clear boundary and target proof. It atomically assigns target_state and mode NORMAL, clears the containment reference and increments generation. This intervention is the explicit external/policy exception permitting a new normal episode; automatic recovery does not de-escalate containment.

The committed snapshot initially has null assessment reference/class and AUDIT_BLOCKED. The engine-owned _assess_session_mode creates freshly bound NotEvaluatedPredicate values because the pure target proof established VALID and _classify consults no predicates for actual NORMAL VALID state. It observes the actual newly committed clear SystemContext and calls real StateModel.assess/once completion under the same lifecycle scope. It never passes the prospective pre-exit context as an actual pre-exit observation.

The typed SessionResolutionObservation retains request, route, actual containment identity, pure target proof, authority, clear boundary, propagation, exact publication, actual postassessment and status/effect truth. append_resolution creates ACTION_OBSERVED with envelope=None and diagnostic_reference=None; DiagnosticEvent._coherent already permits that shape. Its typed supporting node links the actual old containment, publication, target and new assessment root. It is not a canonical diagnostic and carries no fabricated TEN fields.

The actual post pair consumes two slots, control one, within four reserved slots. If postassessment, completion, resolution control or scope completion fails after commit, the target/mode remain actual committed truth and ordinary admission remains AUDIT_BLOCKED. No rollback or claimed certification is invented. On full confirmation, the owner associates that actual STABLE assessment and installs its Detection/Classification root as the new normal main phase. Old containment records stay immutable.

RESOLVE_CONTAINMENT with route ESCALATE_TO_SAFE_HALT and resolution_action HALT requires target_state=null and actual halt authority. Operator or policy authority maps to the corresponding OPERATOR_HALT_REQUEST/POLICY_HALT_REQUEST. CONTAINMENT_BREACH is used only with actual SATISFIED breach evidence, never by route name. Other inconsistent route/action/target combinations are rejected before effects.

## 10. Deliberate halt and terminal closure

The actual trigger table is:
| Trigger | Required evidence | Rule |
|---|---|---|
| CONTAINMENT_BREACH | actual CONTAINED mode plus bound SATISFIED breach observation | ASH-HALT-TRIGGER-001 |
| ESCALATION_FROM_FAILED | actual FAILED/no-path origin and actual external halt direction or owner-retained N2 UNREACHABLE handoff | ASH-HALT-TRIGGER-002 |
| OPERATOR_HALT_REQUEST | bound AUTHORIZED OPERATOR observation | ASH-HALT-TRIGGER-003 |
| POLICY_HALT_REQUEST | bound AUTHORIZED POLICY observation or actual adopted owner policy decision | ASH-HALT-TRIGGER-004 |
| UNRESOLVABLE_BLOCKED_RECOVERY | bound SATISFIED RECOVERY_NO_PATH and CONTAINMENT_UNAVAILABLE observations | ASH-HALT-TRIGGER-005 |

Before invoking any uncontrolled callback, a valid first halt atomically:
- verifies the actual command/authority/boundary/source snapshot;
- latches terminal_latched=true and mode SAFE_HALT, with admission TERMINAL;
- preserves current_state, increments generation up to UINT64_MAX using the reserved final value, and sets halt reference;
- nulls current assessment/class, clears/revokes every ordinary lease/gate;
- freezes main membership and a complete immutable prior-history view.

The seal contains the confirmed prior main membership plus the exact current halt operation's predetermined bridge/terminal reference slots, marked pending until actual capture. It never treats planned slots as acknowledgments. The owner issues a private terminal capture permit for only those slots and that terminal operation's once completion/final sidecar; its capture_disposition may be ACTIVE for that narrow permit even though ordinary gates are SEALED. It cannot grant registry/provider/candidate/publication work or add a later main successor. Separate terminal denials and interrupted N2 cleanup retain their independent audit permits. Failed filling of a predetermined slot stays explicit pending/partial evidence.

This semantic transition does not require successful registration, reservation, clock or retention. A terminal slot exists after the maximum seventeen nonterminal ordinary entries (two recoveries plus fifteen nonterminal mode attempts), within eighteen total main command entries. It cannot be consumed by an ordinary request. Failure to obtain a scope means completion=null and explicit pending/unconfirmed capture; no second finish is invented. A first halt that interrupts a command belongs to the frozen main chronology; later interrupted returns are separate audit, not historical main successors.

For direct NORMAL halt, an actual zero-step RecoveryDiagnostic bridge with outcome BLOCKED and actual halt cause produces a legal RECOVERY predecessor. The source cannot be represented as CLASSIFICATION -> TERMINAL. For contained halt, the actual confirmed CONTAINMENT/ESCALATION predecessor is used directly; no stage regression bridge is inserted after ESCALATION. If the required predecessor is unavailable, construct PendingLifecycleRecord and explicit incomplete coverage; never fake a parent.

SafeHaltDiagnostic has the exact source-owned eight fields. Its full_diagnostic_chain is a complete grouped trace: initial assessment, actual N2 packets, prior command groups in actual chronology, then SessionTerminalChainClosure. Maximum21 grouped entries follows local limits1+2+17+1, not source canonical record count. Closure contains the current bridge if needed, the exact terminal DiagnosticEmission (same reference and TEN envelope as the outer halt record) and actual terminal publication. The outer record supplies the final payload, avoiding a recursive current result. The bundle graph must validate event-to-payload references and closure equality; a dangling final reference is not full-chain coverage.

A measured nonnull monotonic ClockObservation is required for a canonical containment/halt time. Unavailable UTC has explicit reason and is not made up. No available clock or no complete original/parent/full closure means a PendingLifecycleRecord with exact missing fields and known terminal snapshot. Mandatory halt still occurs and source-required diagnostic coverage is reported incomplete. It is not called full diagnostic conformance.

After terminal sealing, no recovery, normalization, fallback, containment clear or publication can run. First-sixteen terminal denial roots are independent STATE_VALIDITY/DETECTION CRITICAL/BLOCKED DiagnosticEmission records with registered rules and actual terminal refusal context. They do not mutate the frozen main history. Later denial overflow is explicit, bounded and body-uninspected.

## 11. Diagnostics ports, once completion and safe graph

The exact additive ports are in the business inventory. Diagnostics exposes register_session, attach_result, lifecycle_capture, observe_session_result, pin_history, freeze_terminal, denial_capture and observe_session_denial. All use an exact collector-issued opaque SessionRetentionHandle; wire equality is not issuance.

lifecycle_capture(handle, *, execution_gate) stores the exact privately issued gate on its scope and required post-mode assessment child. scope.observe_clock returns an actual collector ClockObservation through nonblocking acquisition, IO-depth refusal and pre/post gate checks. Busy, missing or regressing time remains unavailable. No scope means no available canonical time and a pending lifecycle record. These are explicit implementation seams; they grant no new authority or callback under the lifecycle lock.

Lifecycle begin selects a fixed owner budget, never a caller budget: four events/one incident/512 aliases; ordinary327680 total bytes and98304 support bytes; terminal655360 total bytes and425984 support bytes. No lifecycle reservation overlaps N2. Required post-mode child scopes spend the parent four slots. Denial reserves one event/270336 bytes/64 aliases/one incident. Existing global limits and pinned storage can still refuse admission; upper offered workloads do not guarantee capacity.

Scope.append accepts only exact LifecycleRecord and validates kind, payload, TEN fields, exact cause/command binding, source rule set, original diagnosis, immediate parent/root/stage/severity and session membership. The zero-step bridge is exactly an existing RecoveryDiagnostic with steps=(), not a caller-owned arbitrary payload. Containment/halt support nodes preserve all canonical facts and typed local cause/publication/context. Safe projection rejects unregistered fields/kinds, raw business strings, exception text, paths and previews; explicit omission reasons distinguish declared source from host-verified source.

Supporting nodes referenced by an event must be persisted and acknowledged first. Unknown store outcomes remain unknown roots. No source acknowledgment is synthesized from a bare business value or assumed samecollector prefix. Actual origin completion receipts have at most two assessment event indices and full identity checks; an arbitrary N2-style768-index receipt cannot enter their small projection budget.

scope.finish receives a tentative actual result whose own completion field is null and runs exactly once. Its SessionLifecycleCompletion has actual operation reference, COMPLETE/INCOMPLETE, actual confirmed references and registered failure. Matching COMPLETE proves only that scope. Wrong-reference COMPLETE is retained unconfirmed; matching INCOMPLETE preserves failure and actual attempted prefix. The first domain failure remains primary; later completion failure is an attached observation, not replacement.

observe_session_result is exactly once after that actual finish response. It creates a distinct immutable final-command/completion supporting node; it does not mutate a tentative supporting key or recursively finish. Its own retention receipt remains an API observation without another infinite acknowledgment layer. The same rule applies to denial finish and observe_session_denial. Reservation is held through the once-final sidecar or explicit expiry. For a compact raw-overflow descriptor, the observer may receive the complete API-only actual_result separately; it does not label it an accepted raw wire packet.

The immutable once-final result describes the command and capture observations through that first finish response. Its COMPLETED status does not confirm the subsequent observer's own retention acknowledgment or pin_history. If either later operation fails, preserve the exact result already supplied to the observer, retain the actual failed receipt in the bounded API sidecar, and block ordinary admission in the authoritative session.read() snapshot. Collector read/export must report the resulting partial or uncertain coverage. No rewriting, second observation or recursive receipt field is permitted. A later read can therefore report AUDIT_BLOCKED while the earlier immutable command result remains COMPLETED with its known actual effects.

pin_history closes and pins the actual current immutable member graph through a private issued selector ledger. It emits no evolving SESSION_HISTORY supporting node or event; a complete current-member receipt does not claim that a final terminal index already exists. The owner memory and gate cutover is the mandatory before-IO seal. After the current halt scope finishes and its once-final result observation is attempted, freeze_terminal writes the single immutable SESSION_HISTORY node and at most forty pages once from the actual sealed main history, including the actual terminal command/completion. Missing or unknown members make coverage partial; no key is overwritten. Late interrupted children/completion and terminal denials remain separately correlated audit roots, never additions to the final main index. Paired JSON/Markdown export uses one immutable sanitized snapshot and manifest; both parts include matching terminal facts, control links, actual/attempted prefixes, coverage and retention accounts.

The structural proof is the final companion BOUND_REPORT. It is arithmetic/schema sizing, not executed N3 behavior. Per-node, perkind, alias, supporting-byte, event-byte and whole graph maxima must be checked against actual existing/pinned/reserved capacity. Two N2 episodes can offer more than the existing1024 retained-event cap; refusal is expected and no cap increase/automatic purge is permitted. Existing uncertain-retention and two-phase purge rules remain authoritative.

## 12. Raw packet limit, resource exhaustion and failure truth

Finite tuple ceilings do not prove an aggregate raw byte ceiling. Before ordinary CAS, the owner performs bounded exact-owned traversal and compact ASCII JSON size preflight equivalent to json.dumps(ensure_ascii=True,separators=(',',':'),allow_nan=False). It checks candidate result, prospective history and anticipated terminal closure against33554432 bytes. The anticipated closure uses actual prior DAG and finite registered maxima for future terminal fields; a sizing-only upper-bound shape is never emitted or labeled actual evidence.

Traversal stops at cap+1 as a failure signal rather than allocating unbounded serialization or emitting truncated JSON. Unknown objects, arbitrary to_record hooks and recursion/cycles are rejected at their owner boundary. Business values form an immutable finite DAG; current terminal closure intentionally avoids self-reference.

Ordinary overflow produces SessionRawBusinessFailure with exact request/session/history references, failure phase, before/after/effect truth and SESSION_RAW_BUSINESS_LIMIT. It contains no oversize N2 packet or arbitrary primary evidence. It rejects before state/mode CAS. The actual N2 value and complete owner history remain accessible as immutable API DAG; SessionHistory.to_record raises the registered raw limit error rather than shortening the record.

Mandatory halt latches first even if the anticipated or actual terminal packet overflows. The compact descriptor carries the actual terminal snapshot; PendingLifecycleRecord reason RAW_BUSINESS_LIMIT and PARTIAL/API_ONLY coverage preserve the obligation failure. Complete immutable DAG truth is retained in memory without claiming a valid protected serialized packet. No shortened full_diagnostic_chain is called complete.

Closed failures preserve actual evidence and boolean truth. Capture or retention failure after a known commit reports effects=true and actual after; rejection before commit reports false. Unexpected inability to observe a publication reports null/unconfirmed rather than false. Matching receipt identity, confirmed attempted record, unknown physical write and cleanup completion remain separate facts. No silence is interpreted as resource availability, boundary-clear, authority denial or zero effects.

Local attempts remain bounded: two recovery episodes, sixteen mode attempts inclusive of the reserved terminal slot, eighteen ordinary result entries, thirty-six confirmed and thirty-six attempted lifecycle slots, eighteen pending slots, sixteen post-mode pairs and sixteen individual terminal denials. Registered valid refusals consume their eligible slot. A mandatory first halt can use its reserved slot even when normal ledger/capture quotas are exhausted. Overflow maintains bounded uint64/saturated health counters; it does not promise individual evidence for all later attempts.

## 13. Deterministic values, schemas and adoption registrations

All business schemas use additionalProperties=false, fixed field names, exact const tags, registered enum/rule patterns and bounded tuples. Nested source/state/N2/Diagnostics records use the same source-owned schemas as their exact existing types. No value field named state_revision, corrected_state on an N2 packet, completion_receipt_reference or fabricated completion status is introduced. RecoveryValuePacket.candidate_state and DiagnosticsCompletionReceipt.COMPLETE/INCOMPLETE retain existing semantics.

New schema: data/schemas/m3_session_lifecycle_schema.json.
Positive/rejection examples: examples/core_session_lifecycle/session_cases.example.json and session_rejections.example.json.
Tests: tests/test_m3_session_values.py, test_m3_session_lifecycle.py, test_m3_session_schemas.py, test_m3_session_diagnostics.py.
Existing owners affected are recovery.py/recovery_values.py, state_model.py, diagnostics.py/diagnostics_values.py, scripts/reference_diagnostics_host.py and recovery/reference-Diagnostics schemas. Public exports and trace/inventory verification must include the adopted exact additions.

Governance records YWE-REQ-0044 and ADR-0033, the actual local policy hash, source interpretation, exact values/ports, resource ledger and verification IDs. Runtime schema, examples and test paths in the inventory are planned allocations until their implementation is committed. No historical external review is claimed. README roadmap progress changes only with completed witnessed behavior; this contract adoption is not N3 implementation or all-M3 acceptance.

## 14. Required verification and minimal implementation sequence

N3-V01: exact current full source/profile/recovery/policy guards reject every individual hash/path/profile/aggregate/rule/pin mutation before any N3 callback/effect; legacy standalone N2 witnesses remain unchanged.
N3-V02: initial NORMAL/FAILED distinctions; initial registration/clock/storage failure returns AUDIT_BLOCKED semantic facade and authorized halt still latches.
N3-V03: exact complete live-assessment association rejects foreign samecollector packets, old same-state packet after a state cycle, full snapshot mutation and copied/unissued leases.
N3-V04: fresh origin provider receives derived context before N2; each predicate full binding, actual context, unavailable provider and actual assessment/completion failure are checked; no old evidence rebinding.
N3-V05: one active lease, exact active snapshot CAS, conflicting/inprogress duplicates, replay current-boundary truth and contained/terminal gates before replay.
N3-V06: normal/correction/fallback successful N2 candidate publication requires exact complete STABLE/VALID proof; failure and unconfirmed N2 completion cause no recovery publication.
N3-V07: four containment triggers validate actual evidence/rules; zero-step bridge and legal main parent; actual contained postpair and capture-failure truth.
N3-V08: direct operator/policy replacement resolution requires authority, SAFE propagation, clear boundary and pure current target proof; prospective context remains distinct; successful actual postpair starts a new source-valid phase.
N3-V09: resolution HALT route cannot imply breach; all five halt triggers require exact actual evidence; direct FAILED halt has a legal actual Recovery bridge.
N3-V10: halt latches before registration/reservation/clock/store failures; unsigned64 terminal reserve, no wrap; raw oversize still halts with compact/Pending evidence.
N3-V11: halt from provider/clock/store callback and concurrent thread revokes following stage grants; already granted work returns only late audit; nonblocking terminal IO avoids deadlock/reentrant charging/sequence corruption.
N3-V12: admitted N2, fresh assessment, lifecycle and denial scopes each complete exactly once; cleanup after cancellation retains actual response; wrongref/exception responses preserve primary failures and unconfirmed truth.
N3-V13: final command/denial sidecars are distinct immutable nodes, actual first finish response retained, supporting-before-ack and no recursive acknowledgment.
N3-V14: terminal first operation refuses caller object without touching malicious property/equality/repr/to_record/authority hooks; first16 separate denial roots, bounded overflow, frozen main unchanged.
N3-V15: complete graph/schema/raw-size and fixed budget boundary tests at exact cap/cap+1, old-domainzero-step maxima, pin/uncertain purge, hostile raw prose omission and paired export parity.
N3-V16: all existing repo tests/static type/lint/governance/source inventory and normal project checks pass; README accurately reports completed N3 witnesses and remaining M3/M4 scope.

Implementation sequence is cohesive and finite:
1. Adopt this reconciled prose, independent policy hash, business/safe inventories, structural proof, exact schema and fixtures; register actual governance IDs.
2. Implement closed session values and pure StateModel target proof; additive N2 gate/cancel field/code preserves standalone behavior.
3. Implement narrow per-engine lifecycle owner, immutable snapshot/association/lease/CAS/replay, fresh child assessment, actual containment/exit/halt, raw guard and terminal sealing.
4. Implement explicit Diagnostics lifecycle/control/assessment/denial ports, typed safe nodes, sequential reservations, exact once sidecars, nonblocking terminal IO and late-audit distinction.
5. Add host source/policy assembly and representative samecollector fixtures, run the required concurrent/error/cap tests and normal project checks, review final diff, publish completed behavior and README roadmap checkpoints.

No item in this sequence requires another historical proposal/review ceremony. Actual adoption and executed tests are still required before the status can say implemented or verified.
