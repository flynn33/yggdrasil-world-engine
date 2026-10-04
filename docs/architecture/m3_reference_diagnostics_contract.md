# M3 reference Diagnostics contract

Status: active N2 contract, adopted October 4, 2026 before dependent implementation. Owner and partition: `ywe_core`. Requirement: [YWE-REQ-0042]. Decision: ADR-0031. No executed Diagnostics implementation or native product conformance is claimed by adoption. Read against frozen N1 implementation `5328f018f341b80ad58cdb82f64708992ee2d6ae`. Actual product version is 2.0.23. These adopted local choices do not prescribe upstream numeric limits or invent ASH rules.

## Owning evidence and bounded scope

Raven policy VERSION0.7.0 at 87409bc36fb9d4782eab02189adb184f2b3962a7, policy/Development_Diagnostics.md and Testing_Methodology.md114-126, owns product Diagnostics, typed collection, protected persistence, pre-persistence/export redaction, paired detailed JSON/Markdown, incidents, health, bounded resources and controlled-failure verification. Existing YWE RecordingDiagnosticCapture and RecordingNormalizationCapture are in-memory reference adapters only; no persisted collector/exporter/redactor exists to reuse.

Canonical owners are core/ash_pattern_engine/canonical/interfaces/contracts/diagnostics-module-contract.md, interfaces/diagnostic-schema.md, interfaces/rule-id-taxonomy.md and algorithms/recovery-fallback-semantics.pseudo.md. The unchanged canonical envelope has ten fields, five kinds, five stages, four severities and five dispositions. Every actual business record is validated before projection. Meta mapping is an explicitly adopted local STATE_VALIDITY/DETECTION ERROR/BLOCKED root using ASH-STATE-GENERAL-001, with closed cause/link metadata outside those ten fields. It does not fabricate a canonical meta kind or a state-validity semantic row.

This increment realizes bounded reference Diagnostics for actual StateModel, N1 and N2 producers. Other canonical module sources are explicitly UNAVAILABLE, and native runtime, native development/release replacement, platform release artifact qualification and physical crash/power-loss verification remain deferred to M10. N2 creates immutable value results and typed contain/halt handoffs; it does not enter N3 modes or complete M3.

## Exact interface and ownership

The authoritative field order, scalar types, closed enums, constructor invariants, method signatures, source mappings and budgets are in the exact interface inventory below. It has 62 closed structures and 75 closed enums. No arbitrary context/error dictionary or unspecified callback conversion is admitted. Constructors use exact builtin primitive types, copy bounded tuples, and retain exact owned children. Headers and limit values are fixed, never caller-selectable. ReferenceDevelopmentDiagnostics and ReferenceReleaseDiagnostics take exact identity, profile, ProtectedStore and DiagnosticsClockPort arguments, with no ambient clock/storage defaults.

DiagnosticsClockPort.read returns exact ClockObservation. RecoveryCapture.begin(origin, operation_reference) returns (scope or None, RecoveryAdmissionReceipt); CONFIRMED iff same-collector exact two-record origin attachment and whole fixed reservation succeed. REJECTED/NOT_CONFIRMED has no scope and zero reservations, before provider/evaluator/state effects. Unexpected throw, malformed receipt or wrong operation becomes NOT_CONFIRMED. Main scope.append accepts only exact RecoveryRecord(diagnostic_reference,envelope,record_kind,payload), where payload is RecoveryStepEvidence or RecoveryActionDecision from the N2 owned inventory. It returns the existing three-status CaptureReceipt. Scope.finish accepts the actual five-class RecoveryValuePacket and derives expectations itself. No caller expected count or caller-selected SafeContext bypass exists.

RecoveryCapture.begin_denial handles original SAFE_HALT/TERMINAL_NO_RECOVERY separately. It reserves one event, 270336 bytes and 64 novel aliases, attaches the exact existing origin, and emits one fresh denied-operation STATE_VALIDITY/DETECTION CRITICAL/BLOCKED root using GENERAL plus RECOVERY-ACTION rules. Its actual HANDOFF/NOT_APPLICABLE directive remains REMAIN_SAFE_HALT. It never appends RECOVERY to the original terminal contextual chain, never uses providers/registry/post children, and never claims actual halt entry. DenialScope.finish accepts actual RecoveryHandoff or retained RecoveryFailure; failure retains actual attempted record/prefix/status.

PostAssessmentLink carries exact untrusted parent_operation_reference, parent_action_reference and originating_chain_root_reference. Diagnostics.assessment_capture(relation=link) admits the real same-collector child StateModel call with its own DETECTION root. Child records are immediately acknowledged, and actual child completion must succeed before N2 can return recovered success.

## Original attachment and mandatory completion

Same-collector attachment compares both entire submitted origin DiagnosticEmission records against actual previously CONFIRMED private witnesses. Fingerprint is SHA256 of json.dumps(emission.to_record(),sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii'), plus original reference, collector/session identity and confirmed sequence. Only exact owned records enter it. This assumes SHA256 collision resistance; it is not remote authentication or a substitute for StateModel full math/context/predicate validation. Raw summaries/notes are not a second collector plaintext log. Digests and raw reference keys are bounded private memory and never persisted/exported.

Existing begin/append adapters cannot tell whether one record is a completed diagnosis or a missing classification. Reference composition must call complete_assessment(actual StateDiagnosis/StateAssessment/ClassificationEvidenceFailure/DiagnosticCaptureFailure) or complete_normalization(actual N1 result/failure) once. N2 calls scope.finish(actual result). Completion compares confirmed prefixes and separately retained attempted failed records, without fabricating missing diagnostics. Missing/replayed completion stays INCOMPLETE/PARTIAL and emits bounded meta/health at declared shutdown. Raw business results/API remain unchanged; completion observations are one exact DiagnosticsCompletionReceipt with COMPLETE/INCOMPLETE statuses, retained raw API operation reference and actual confirmed-prefix/failure detail. Exact matching COMPLETE alone permits final return; no recursive finish or separate completion-failure type. Exact raw operation references in receipt API let the engine verify equality; the snapshot aliases them.

## Safe projection and proof graph

Raw immutable returned business packets remain caller-owned memory, separately capped at32MiB; they are not persisted/exported by Diagnostics. Diagnostics stores a distinct sanitized artifact, never calls it an unredacted ASH packet. It copies approved actual source pins, bits/signatures/arithmetic, enums, exact measured counts and fixed trusted message templates only. All producer prose, notes, previews, non-bit scalar observations, paths, exception/stack text, URLs/query/header/body material, arbitrary metadata and hypotheses are omitted with closed category/count/reason, or their correlation references become opaque aliases. Regex token removal alone is not a safety boundary. Secondary projection validation runs before both persistence and export.

Safe supporting graph retains full recognized-valid512-signature profile nodes, the separate exact eight-digest canonical ledger (dependency_id is not a SHA row), original/post assessments including full nine-field semantic rows/context/two bound predicate facts/emission references, and action-local32-step canonical recovery summaries once. Events hold references rather than duplicate raw full packets. SourcePin.revision identifies the verified YWE snapshot containing vendored sources, not an invented upstream SHA. External provider source triples remain DECLARED_NOT_AUTHENTICATED.

SafeNormalizationProof retains all submitted/expected targets (<=16), selected/recomputed targets, submitted/recomputed chain (<=1), source/full-profile references, origin/proof statuses and precise failed-field/failure mapping. SafeCorrectionProof retains full chain<=16, claimed/computed target, validation status, model bindings and target diagnostic reference. SafeRegistryProof retains complete32-entry inventory, original input order, signed64 rank, condition references, target, escalation, certification assessment reference, actual evaluated prefix and failed policy/field. SafeConditionEvidence and SafePredicateObservationEvidence preserve expected declared condition and actual provider source/digest/evidence triples as aliases, actual TRUE/FALSE/UNAVAILABLE/phase/candidate/op/registry facts. They retain equality/difference correlation without falsely authenticating caller source digests.

SafeRecoverySafetyEvidence additionally retains actual propagation SAFE/RISK/UNAVAILABLE and external-authority REACHABLE/UNREACHABLE/UNAVAILABLE with full aliased source triples and consulted flags. Its complete safe directive preserves requested action, canonical trigger or exact external-escalation/observed-mode object, origin/causing-decision/evidence refs, request origin and reviewed policy binding; actual_mode_status remains NOT_ENTERED_BY_N2. Pending mandates survive separately confirmed supporting storage even if the referring event fails, with partial coverage. Raw reason prose is omitted.

RecoveryStepEvidence transaction-global index is preserved exactly0..767, and before/codeword/after values remain actual full signatures. Details are globally retained and bounded summaries reference exact event indices; no512-predicate copies appear in each summary. Free reasons/source metadata omission is counted explicitly. RecoverabilityRelevance preserves actual RECOVERY_APPLICABLE; uppercase safe predicate labels map explicitly to the two lowercase StateModel fields.

## Clock, counter, meta and retention boundaries

All observations enter through a trusted injected clock port under serialized admission/append/completion/snapshot boundaries. UTC is exact27-byte ASCII YYYY-MM-DDTHH:MM:SS.ffffffZ, valid Gregorian UTC with six fraction digits; unknown UTC is null with reason. Available monotonic reading is exact unsigned64, nonregressing, with checked elapsed <=600000000000ns. Unavailable/malformed/overflowing/regressing observation refuses admission or stops further capture with explicit partial health. If an effect already occurred, actual business result and unconfirmed attempted capture survive. No fake zero duration, unbounded clock claim or timer-thread deadline is asserted: enforcement is at observed boundaries. Prior retained snapshot export stays available after clock failure with null generation time and explicit reason.

Eight counters use exact unsigned64 checked arithmetic. EXACT has value and no reason; SATURATED is max18446744073709551615 with COUNTER_LIMIT, a declared lower bound; UNAVAILABLE is null with STORAGE_UNCONFIRMED. Never wrap; unknown loss is never invented zero. Counter/sequence authority overflow stops admission. Health exposes all unavailable sources, ranges and storage uncertainty.

Independent65536-byte meta/health pool is16*3072 meta +8192 health status +8192 fallback. Main event/support/incident exhaustion cannot consume it. Meta records are separate slots and cannot acknowledge a missing business step. Meta storage failure records one bounded fallback cause/counter state without recursive logging; full meta capacity coalesces explicit overflow/health rather than claim omission-free capture. Active/incident-pinned operations cannot be evicted. Whole completed unpinned operations may rotate only with exact retention ranges/counts/reasons; unknown gaps and coalescing stay visible.

Snapshot determinism requires equal explicit identity, observations, retained state and observed serialized call order. Unordered concurrency does not imply byte-order independence. One immutable sequence boundary defines both exports; no capture updates are reread during rendering.

## Resource calculation

Registry32 entries, up to8 applicability plus8 additional predicates each, correction chain16, maximum33 linked child assessments and35 action decisions yield696 events by formula `sum([32 * sum([8, 8, 1, 1, 2, 1]), 16, 1, 1, 2, 1, 1, 1, 1])`. Reserve768 including72 margin. Hard limits are1024 main event slots,16 independent meta records,32 incidents,8 active operation handles,6144 aliases and33554432 retained serialized bytes. Whole operation reserves31588352 bytes before effects, including events25165824 +support2097152 +incidents1048576 +privatealiases2097152 +health65536 +inheritedorigin65536 +identity/envelope1048576. Existing/pinned/reserved data count; nominal slots do not waive bytes.

Alias occurrence bound5403 includes512 condition bindings*4,512 provider triples*3,768 diagnostic refs,35 action refs,33 post facts*12,32 certifications*13,64 origin/registry/proof refs,16 profile nodes*4,64 control/incident/meta/bundle/identity refs and12 first malformed-return margin. Diagnostic event IDs reuse their actual diagnostic alias; support references reuse typed actual source/event refs. Arbitrary prose is omitted. Admission reserves5403 novel slots and the authoritative2MiB alias bytes before effects. Failed capacity rejects, never discovers an admitted half-operation limit.

The read-only executable ywe-n2-diagnostics-finalize-inventory-20261004.py derives conservative leaf-size assemblies from the exact machine domains, choosing nullable values by encoded width. It deliberately combines semantically impossible optional maxima as an upper bound, not a conforming business capture/schema acceptance. Source profile uses all512 distinct signatures. Metrics and full assembly are ywe-m3-n2-diagnostics-byte-bounds-20261004.json and ywe-m3-n2-diagnostics-max-leaf-assembly-20261004.json. Current measured bytes are:

- largest_event_leaf_assembly: 9,512 bytes.
- source_profile512: 6,429 bytes.
- post_assessment2emissions: 5,779 bytes.
- canonical_action_summary32steps: 12,170 bytes.
- incident768timeline_attempt_state_refs: 18,124 bytes.
- health16ranges: 7,174 bytes.
- largest_meta_leaf_assembly: 2,156 bytes.
- support16profiles66assessments35diagnostics_full_proofs: 1,459,252 bytes.
- incidents32: 580,001 bytes.
- private_alias6144x256: 1,671,169 bytes.
- operation768_events_plus_support_incidents_health: 9,386,993 bytes.
- markdown_full_appendix: 9,448,492 bytes.

Every projected event/action/proof node is below32768; profile and assessment nodes below8192; meta below3072; status health below8192. Full operation support, including all512 condition/provider evidence nodes, remains below2MiB, and private6144-key ledger below2MiB. Authoritative hard cap still applies to retained/reserved combinations.

Separate export quotas: compact JSON32MiB, Markdown48MiB (same full JSON appendix32MiB plus bounded detailed rendering16MiB), manifest64KiB. One bundle slot includes incomplete exports; second export refuses until explicit whole-bundle purge. Capture plus maximum pair117506048 bytes fits134217728 protected disk. Logical serialized-buffer ceiling192MiB covers capture32+snapshot32+JSON32+Markdown48+raw business32+aliases2=178MiB plus14MiB margin; this is not an exact Python heap bound.

All new exact safe supporting nodes must actually commit to ProtectedStore before a referencing event can return CONFIRMED or scope completion can succeed. commit_supporting(sequence, closedkind, evidencealias, redactedbytes<=32768) handles source/profile/condition/assessment/proof nodes in dependency order; reuse requires same kind+alias+bytes and an actual prior confirmed commit. Partial/unknown support write prevents event acknowledgment and leaves explicit partial coverage/retained business result. Separate commit_meta<=3072, commit_health<=8192 and commit_fallback_health<=8192 use independent reserved pools. Health/fallback keep one latest bounded own status, with explicit supersession; no full health-history claim. Meta fallback never recursively logs its failure. Dangling partial nodes are unavailable rather than falsely confirmed.

ProtectedStore.write_pair receives only aliased bundle ID/bytes/last sequence, returns StorePairReceipt or StorePairFailure actual IO evidence (three part states, publication flag, failure), and never reconstructs domain objects from JSON. Diagnostics wraps its already-owned snapshot into ExportReceipt/ExportFailure. Store purge returns only closed StorePurgeReceipt(bundle/status/removedparts/bytes/failure), while Core wraps its own health; no host-generated RetentionReceipt. Manifest publishes last; success requires all three parts confirmed, exact parity/checksums and actual final publication. Partial write/throw/unknown never becomes success; failure keeps same snapshot and known part states.

## Actual Windows protection evidence and scope

The usable demonstrated route is a direct fresh protected child of D:/, not Temp or a nested C:/pathname. D:/ Authenticated Users Modify0x1301bf permits creation but lacks DELETE_CHILD/WRITE_DAC/WRITE_OWNER; root drive has no ordinary child rename path. Native volume identity/nonreparse root checked. Ordinary creation alone is allowed; generic-all/delete-child/DAC/owner or ancestor substitution rejects. Factory checks native drive mapping/root identity and actual ACLs; trusted selected capability is never caller booleans.

A fresh direct child of D:/ was created via CreateDirectoryW SECURITY_ATTRIBUTES with the effective user SID plus SYSTEM only, protected DACL before any write. Both synthetic files inherited exactly those grants; current owner and NTFS persistent ACL support were verified. Native volume and file identity matched before and after exclusive flush/readback; existing-root creation failed with error183; independent icacls verification reported1 object and0 failures. The external D-root storage proof has SHA256 `e86fa1638c7a371212e54370dc43b7ed3046f0fdcd9d0eff880ae2f921bebc98`, root ACL audit `552d3ece42d576af07ead1ab5f6d211243858e7486c0b7be7fcdf534edfd1105`, and executable probe `03311fac563a7f09da1dde56efe38209a9ddd842c461404e8c59c35f22f7c1ad`. Host-specific user, path and device identifiers are omitted from this published design statement; those reviewed proofs are capability evidence, not collector implementation acceptance.

A negative candidate is retained: C:/ root grants Authenticated Users FullControl including DELETE_CHILD, so readonly C:/Users through selected03 cannot prove secure pathname ancestry. The earlier nested03 probe proves ACL inheritance/IO mechanism only. Evidence ywe-n2-parent-acl-audit-20261004.json and ywe-n2-trusted-parent-storage-probe-20261004.json must not be promoted to secure-ancestor acceptance. No existing ACL was changed.

A real disproof also survives: an open directory handle with READ/WRITE sharing and no DELETE did not prevent same-user MoveFileExW rename. It succeeded and was restored before IO. Protection excludes current-user processes, SYSTEM and administrators; no share-lock race guarantee. Configured host IO checks root/children ownership, grants, nonreparse paths, native identities, exclusive fixed names and flush/readback before success; it refuses pre-existing/unverified destinations or protection failure, with bounded health and no raw fallback log. Every child carries/inherits exactly the private root grants and stays open through IO. No second-user effective access/logon, active privileged race, encryption, power loss, native product release or actual Diagnostics implementation was tested.

Microsoft primary references: [CreateDirectoryW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createdirectoryw), [SDDL conversion](https://learn.microsoft.com/en-us/windows/win32/api/sddl/nf-sddl-convertstringsecuritydescriptortosecuritydescriptorw), [icacls](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/icacls), and [Python3.12 os.chmod](https://docs.python.org/3.12/library/os.html#os.chmod). Windows chmod changes readonly attribute;0o700 is not an ACL security mechanism.

## Required implementation acceptance

Exercise real StateModel origin, N1 and N2 through reference collectors, controlled failures, exact original attachment and mandatory completion. Reject detached/mutated/unknown origin with zero effects. Schema/taxonomy/parent/root/stage/terminal/replay/missing-step mutations must retain actual original failure and emit independent bounded meta evidence. Secret sentinels in every arbitrary nested string/location must be absent from store/JSON/Markdown, with explicit redaction counts. Independently extract Markdown full JSON appendix and compare typed equality to JSON. Force JSON/Markdown/manifest/publication, unknown/partial store, clock regression/unavailability, limits/retention and meta-store exhaustion separately; no false success, no silent omission or recursive logger. Run actual protected D:/ synthetic collector capture/export with ACL/file identity checks; keep unsupported native/release/physical-crash evidence explicit.

## Exact interface inventory

The frozen external prose fingerprint is `ff7898fa2a01ea9166208f054f8438156dbc54ce3efc46141eed9c4a45c83609`; its exact interface inventory fingerprint is `fcfe1335d038ea727c7d7695154098934d7c532b0aceb18e05016919a8431a2c`, byte-bound inventory `2d5b1dd72b0ba261aa1c550e700249b4a0e810953bbf617ac938603887ab5acd`, and freeze manifest `a5ba810b2f4d1991e1f015d07f6d51fda79915d162f64039c605ec0a009fe904`. These identify the independently reviewed proposals. Promotion changes only adoption metadata, live document references, the adopted safety-policy digest and published host-identifier elision. The following62 structures and75 closed enums remain the authoritative adopted interface.

```json
{
  "artifact_type": "external_n2_diagnostics_interface_proposal",
  "artifact_version": "1.0.0",
  "implementation_baseline": "5328f018f341b80ad58cdb82f64708992ee2d6ae",
  "adoption_status": "ACTIVE_ADOPTED_N2_CONTRACT_IMPLEMENTATION_INCOMPLETE",
  "primitive_types": {
    "Alias": "exact str matching ^ref:[0-9]{6}$; IDs allocated consistently from bounded per-session ledger; raw keys never serialized",
    "Signature": "exact str matching ^[01]{9}$",
    "Revision": "exact str40 lowercase hex, supplied only after actual revision verification",
    "Sha256": "exact str64 lowercase hex; retained only for actually verified approved-source/file bytes",
    "TrustedVersion": "const literal2.0.23 verified against actual VERSION and repository_truth_manifest during assembly; not caller-selected",
    "TrustedTemplateText": "exact text generated only by MessageTemplate lookup; no constructor-selected arbitrary text",
    "UtcTimestamp": "exact builtin ASCII str length27 YYYY-MM-DDTHH:MM:SS.ffffffZ, year0001..9999 valid Gregorian UTC calendar/time, seconds00..59 and exactly6fractiondigits; produced by trusted clock assembly; no extended fractions/leap-second token/arbitrary offsets",
    "uint32": "exact builtin int0..4294967295 excluding bool/subclasses",
    "uint64": "exact builtin int0..18446744073709551615 excluding bool/subclasses",
    "bool": "exact builtin bool; no truthiness conversion",
    "UntrustedReference": "API-only exact builtin ASCII str conforming existing owned identifier grammar; length1..256; raw references never persisted/exported",
    "UntrustedOperationReference": "API-only exact builtin ASCII str conforming Recovery operation grammar; length1..192; raw references never persisted/exported",
    "int64": "exact builtin int -9223372036854775808..9223372036854775807 excluding bool/subclasses"
  },
  "fields": {
    "SourceProvenance": {
      "status": "enum:SourceStatus",
      "verified_revision": "Revision|null",
      "dirty_path_aliases": "tuple<Alias,0..128>",
      "unavailable_reason": "enum:UnavailableReason|null"
    },
    "DiagnosticsEnvironment": {
      "os_kind": "enum:OperatingSystem",
      "runtime_kind": "const:PYTHON_REFERENCE",
      "runtime_version": "tuple<uint32,3>|null",
      "architecture": "enum:Architecture",
      "host_class": "enum:HostClass",
      "unavailable_fields": "tuple<MissingCoverage,0..8>"
    },
    "DiagnosticsIdentity": {
      "product_id": "const:yggdrasil-world-engine-reference",
      "product_version": "TrustedVersion",
      "implementation_id": "enum:Implementation",
      "profile_id": "enum:ProfileId",
      "schema_version": "const:1.0.0",
      "build_id": "Alias",
      "source_revision": "Revision|null",
      "source_provenance": "SourceProvenance",
      "session_reference": "Alias",
      "environment": "DiagnosticsEnvironment"
    },
    "DiagnosticsProfile": {
      "profile_id": "enum:ProfileId",
      "implementation_id": "enum:Implementation",
      "selection_authority": "Alias",
      "development_payloads_enabled": "bool",
      "native_release_replacement_status": "const:DEFERRED_M10",
      "native_release_qualification": "const:NOT_VERIFIED"
    },
    "DiagnosticLimits": {
      "event_capacity": "const:1024",
      "incident_capacity": "const:32",
      "alias_capacity": "const:6144",
      "max_event_bytes": "const:32768",
      "store_byte_capacity": "const:33554432",
      "health_capacity": "const:16",
      "max_active_operations": "const:8",
      "max_operation_events": "const:768",
      "capture_duration_milliseconds": "const:600000",
      "supporting_byte_capacity": "const:2097152",
      "incident_byte_capacity": "const:1048576",
      "alias_byte_capacity": "const:2097152",
      "health_byte_capacity": "const:65536",
      "inherited_origin_byte_capacity": "const:65536",
      "envelope_byte_capacity": "const:1048576",
      "max_json_bytes": "const:33554432",
      "max_markdown_bytes": "const:50331648",
      "max_manifest_bytes": "const:65536",
      "max_export_bundles": "const:1",
      "protected_disk_byte_capacity": "const:134217728",
      "logical_serialized_buffer_capacity": "const:201326592",
      "raw_business_packet_byte_capacity": "const:33554432",
      "max_meta_records": "const:16",
      "max_meta_record_bytes": "const:3072",
      "health_status_byte_capacity": "const:8192",
      "fallback_health_byte_capacity": "const:8192"
    },
    "CaptureRelation": {
      "parent_operation_reference": "Alias",
      "parent_action_reference": "Alias",
      "originating_chain_root_reference": "Alias"
    },
    "MissingCoverage": {
      "source": "enum:CoverageSource",
      "status": "enum:CoverageStatus",
      "reason": "enum:UnavailableReason|null"
    },
    "RetentionBoundary": {
      "first_sequence": "uint64",
      "last_sequence": "uint64",
      "record_count": "uint64",
      "reason": "enum:RetentionReason",
      "coalesced": "bool"
    },
    "DiagnosticsHealth": {
      "coverage_status": "enum:OverallCoverage",
      "accepted_count": "uint64|null",
      "rejected_count": "uint64|null",
      "retained_count": "uint64|null",
      "expired_count": "uint64|null",
      "lost_count": "uint64|null",
      "redacted_field_count": "uint64|null",
      "redacted_reference_count": "uint64|null",
      "last_confirmed_sequence": "uint64|null",
      "first_unavailable_sequence": "uint64|null",
      "last_unavailable_sequence": "uint64|null",
      "active_reservations": "uint32[0..8]",
      "used_bytes": "uint32[0..33554432]",
      "storage_state": "enum:StorageState",
      "last_failure_code": "enum:DiagnosticsFailure|null",
      "missing_sources": "tuple<MissingCoverage,0..32>",
      "retention_boundaries": "tuple<RetentionBoundary,0..16>",
      "range_detail_coalesced": "bool",
      "meta_overflow_count": "uint64|null",
      "counter_states": "tuple<DiagnosticCounterState,8>",
      "meta_record_count": "uint32[0..16]",
      "meta_storage_state": "enum:StorageState",
      "fallback_cause_code": "enum:MetaCauseCode|null"
    },
    "ClockObservation": {
      "observed_utc": "UtcTimestamp|null",
      "monotonic_nanoseconds": "uint64|null",
      "utc_reason": "enum:UnavailableReason|null",
      "monotonic_reason": "enum:UnavailableReason|null"
    },
    "CaptureWindow": {
      "first_sequence": "uint64|null",
      "last_sequence": "uint64|null",
      "start": "ClockObservation",
      "end": "ClockObservation"
    },
    "SafeDiagnosticEnvelope": {
      "diagnostic_kind": "enum:CanonicalKind",
      "severity": "enum:CanonicalSeverity",
      "stage": "enum:CanonicalStage",
      "disposition": "enum:CanonicalDisposition",
      "subject_reference": "Alias",
      "parent_diagnostic_reference": "Alias|null",
      "chain_root_reference": "Alias",
      "rule_ids": "tuple<enum:CanonicalRule,1..10>",
      "summary": "TrustedTemplateText",
      "notes": "tuple<TrustedTemplateText,1..8>"
    },
    "SafeOrbit": {
      "orbit_id": "Signature",
      "member_count": "const:16",
      "contains_known_valid_state": "bool"
    },
    "SafeStateContext": {
      "input_state": "Signature|null",
      "actual_state": "Signature|null",
      "selected_target": "Signature|null",
      "eligible_targets": "tuple<Signature,0..16>|null",
      "codeword_chain": "tuple<Signature,0..16>|null",
      "admissibility_status": "enum:Admissibility|null",
      "transformation_compatibility": "enum:Compatibility|null",
      "normalization_status": "enum:NormalizationStatus|null",
      "recoverability_relevance": "enum:RecoverabilityRelevance|null",
      "is_valid": "bool|null",
      "orbit_info": "SafeOrbit|null",
      "system_state_class": "enum:SystemClass|null",
      "recovery_category": "enum:RecoveryCategory|null",
      "predicate_name": "enum:PredicateName|null",
      "predicate_value": "bool|null",
      "candidate_order_index": "uint32[0..31]|null",
      "step_index": "uint32[0..767]|null",
      "profile_reference": "Alias|null",
      "source_evidence_reference": "Alias|null",
      "fixture_reference": "Alias|null",
      "unavailable_fields": "tuple<enum:ContextField,0..32>",
      "input_failure_code": "enum:InputFailure|null",
      "profile_evidence_reference": "Alias|null",
      "original_assessment_reference": "Alias|null",
      "post_assessment_reference": "Alias|null",
      "recovery_diagnostic_reference": "Alias|null",
      "before_state": "Signature|null",
      "codeword": "Signature|null",
      "after_state": "Signature|null",
      "policy_reference": "Alias|null",
      "validation_status": "enum:ProofStatus|null",
      "failed_field": "enum:ValidationField|null",
      "proof_evidence_reference": "Alias|null",
      "recovery_safety_evidence_reference": "Alias|null"
    },
    "SafeError": {
      "domain": "enum:FailureDomain",
      "code": "enum:SafeFailure",
      "cause_codes": "tuple<enum:SafeFailure,0..8>",
      "failed_field": "enum:SafeField|null",
      "source_reference": "Alias|null",
      "message_template": "enum:MessageTemplate",
      "omitted_error_material": "tuple<enum:OmissionCategory,0..8>"
    },
    "DiagnosticEvent": {
      "event_id": "Alias",
      "local_sequence": "uint64",
      "clock": "ClockObservation",
      "source": "enum:Producer",
      "event_type": "enum:EventType",
      "message_template": "enum:MessageTemplate",
      "session_reference": "Alias",
      "operation_reference": "Alias|null",
      "action_reference": "Alias|null",
      "relation": "CaptureRelation|null",
      "diagnostic_reference": "Alias|null",
      "envelope": "SafeDiagnosticEnvelope|null",
      "outcome": "enum:ObservedOutcome",
      "duration_nanoseconds": "uint64|null",
      "duration_reason": "enum:UnavailableReason|null",
      "context": "SafeStateContext",
      "error": "SafeError|null",
      "redaction_entries": "tuple<RedactionEntry,0..32>"
    },
    "EvidenceFact": {
      "fact_type": "enum:FactType",
      "event_references": "tuple<Alias,1..8>"
    },
    "ExpectedBehavior": {
      "invariant": "enum:ExpectedInvariant",
      "source_reference": "Alias",
      "expected_outcome": "enum:ObservedOutcome"
    },
    "DiagnosticIncident": {
      "incident_id": "Alias",
      "trigger_event_reference": "Alias",
      "expected": "ExpectedBehavior",
      "observed_outcome": "enum:ObservedOutcome",
      "affected_operation_references": "tuple<Alias,1..8>",
      "timeline_event_references": "tuple<Alias,1..768>",
      "attempt_event_references": "tuple<Alias,0..35>",
      "error": "SafeError",
      "state_event_references": "tuple<Alias,0..34>",
      "reproduction_fixture_reference": "Alias|null",
      "observed_facts": "tuple<EvidenceFact,1..16>",
      "supported_findings": "tuple<EvidenceFact,0..16>",
      "hypotheses": "const:empty_tuple",
      "unknowns": "tuple<enum:UnknownCause,0..16>",
      "unresolved": "bool"
    },
    "SourcePin": {
      "source_kind": "enum:PinnedSource",
      "revision": "Revision",
      "sha256": "Sha256"
    },
    "SupportingEvidence": {
      "verified_source_pins": "tuple<SourcePin,0..40>",
      "synthetic_fixture_references": "tuple<Alias,0..128>",
      "metric_event_references": "tuple<Alias,0..1024>",
      "attachments": "const:empty_tuple",
      "attachment_reason": "const:EXCLUDED_REFERENCE_SCOPE",
      "profiles": "tuple<SafeProfileEvidence,0..16>",
      "assessments": "tuple<SafeAssessmentEvidence,0..512>",
      "recovery_diagnostics": "tuple<SafeRecoveryDiagnostic,0..64>",
      "source_evidence": "tuple<SafeSourceEvidence,0..16>",
      "normalization_proofs": "tuple<SafeNormalizationProof,0..8>",
      "correction_proofs": "tuple<SafeCorrectionProof,0..8>",
      "registry_proofs": "tuple<SafeRegistryProof,0..8>",
      "conditions": "tuple<SafeConditionEvidence,0..512>",
      "predicate_observations": "tuple<SafePredicateObservationEvidence,0..512>",
      "recovery_safety_evidence": "tuple<SafeRecoverySafetyEvidence,0..8>"
    },
    "RedactionEntry": {
      "field_category": "enum:OmissionCategory",
      "reason": "enum:RedactionReason",
      "count": "uint64"
    },
    "RedactionAccount": {
      "profile": "const:OWNED_SAFE_PROJECTION_V1",
      "field_count": "uint64",
      "reference_count": "uint64",
      "entries": "tuple<RedactionEntry,0..32>",
      "secondary_check": "const:PASSED"
    },
    "RetentionAccount": {
      "configured_limits": "DiagnosticLimits",
      "boundaries": "tuple<RetentionBoundary,0..16>",
      "active_operation_references": "tuple<Alias,0..8>",
      "incident_pinned_operation_references": "tuple<Alias,0..32>",
      "range_detail_coalesced": "bool"
    },
    "Limitation": {
      "code": "enum:LimitationCode",
      "source": "enum:CoverageSource"
    },
    "DiagnosticSnapshot": {
      "bundle_id": "Alias",
      "generated_at_utc": "UtcTimestamp|null",
      "generation_time_reason": "enum:UnavailableReason|null",
      "identity": "DiagnosticsIdentity",
      "profile": "DiagnosticsProfile",
      "capture_window": "CaptureWindow",
      "coverage": "tuple<MissingCoverage,1..32>",
      "events": "tuple<DiagnosticEvent,0..1024>",
      "meta_diagnostics": "tuple<MetaDiagnosticRecord,0..16>",
      "incidents": "tuple<DiagnosticIncident,0..32>",
      "supporting_evidence": "SupportingEvidence",
      "health": "DiagnosticsHealth",
      "retention": "RetentionAccount",
      "redaction": "RedactionAccount",
      "limitations": "tuple<Limitation,1..16>"
    },
    "MetaCause": {
      "cause_code": "enum:MetaCauseCode",
      "related_operation_reference": "Alias|null",
      "related_diagnostic_reference": "Alias|null",
      "expected_phase": "enum:ExpectedPhase|null",
      "observed_phase": "enum:ExpectedPhase|null"
    },
    "StorageReceipt": {
      "sequence": "uint64|null",
      "status": "enum:StorageCommitStatus",
      "failure_code": "enum:DiagnosticsFailure|null"
    },
    "PartReceipt": {
      "part": "enum:ExportPart",
      "relative_name": "enum:PartName",
      "status": "enum:PartStatus",
      "bytes": "uint64|null",
      "sha256": "Sha256|null",
      "failure_code": "enum:DiagnosticsFailure|null"
    },
    "ExportReceipt": {
      "bundle_id": "Alias",
      "status": "const:COMPLETE",
      "parts": "tuple<PartReceipt,3>",
      "last_included_sequence": "uint64|null",
      "snapshot": "DiagnosticSnapshot"
    },
    "ExportFailure": {
      "bundle_id": "Alias",
      "status": "const:INCOMPLETE",
      "failure_code": "enum:DiagnosticsFailure",
      "failed_part": "enum:ExportPart",
      "parts": "tuple<PartReceipt,3>",
      "snapshot": "DiagnosticSnapshot"
    },
    "RetentionReceipt": {
      "status": "enum:RetentionReceiptStatus",
      "boundaries": "tuple<RetentionBoundary,0..16>",
      "health": "DiagnosticsHealth"
    },
    "StorageVerification": {
      "mechanism": "const:WINDOWS_PROTECTED_DACL",
      "status": "enum:StorageVerificationStatus",
      "persistent_acls": "bool",
      "owner_matches_effective_sid": "bool",
      "dacl_protected": "bool",
      "grant_principals": "tuple<enum:StoragePrincipal,2>",
      "no_reparse_path": "bool",
      "trusted_parent": "bool",
      "stable_identity": "bool",
      "failure_code": "enum:DiagnosticsFailure|null"
    },
    "SafeProfileEvidence": {
      "evidence_reference": "Alias",
      "profile_reference": "Alias",
      "availability": "enum:ProfileAvailability",
      "source_reference": "Alias",
      "source_digest_reference": "Alias",
      "source_evidence_reference": "Alias",
      "recognized_valid_states": "tuple<Signature,0..512>|null",
      "unavailable_reason": "enum:UnavailableReason|null"
    },
    "SafeInputState": {
      "kind": "enum:SafeInputKind",
      "state": "Signature|null",
      "input_reference": "Alias",
      "failure_code": "enum:InputFailure|null"
    },
    "SafeStateValidity": {
      "input_state": "SafeInputState",
      "admissibility_status": "enum:Admissibility",
      "transformation_compatibility": "enum:Compatibility",
      "normalization_status": "enum:NormalizationStatus",
      "recoverability_relevance": "enum:RecoverabilityRelevance",
      "is_valid": "bool",
      "orbit_info": "SafeOrbit|null",
      "rule_ids": "tuple<enum:CanonicalRule,1..5>",
      "notes": "tuple<TrustedTemplateText,1..8>"
    },
    "SafePredicate": {
      "evaluation_status": "enum:PredicateEvaluation",
      "value": "bool|null",
      "assessment_reference": "Alias",
      "diagnosis_reference": "Alias",
      "subject_reference": "Alias",
      "profile_reference": "Alias",
      "source_reference": "Alias",
      "evidence_reference": "Alias"
    },
    "SafeAssessmentEvidence": {
      "evidence_reference": "Alias",
      "assessment_reference": "Alias",
      "original_input_reference": "Alias",
      "parsed_state": "Signature|null",
      "canonical_source_reference": "Alias",
      "profile_evidence_reference": "Alias",
      "state_validity_diagnostic": "SafeStateValidity",
      "is_in_safe_halt": "bool",
      "is_in_containment": "bool",
      "correction_path_is_known": "SafePredicate|null",
      "fallback_is_available": "SafePredicate|null",
      "system_state_class": "enum:SystemClass|null",
      "recovery_category": "enum:RecoveryCategory|null",
      "consulted_predicates": "tuple<enum:PredicateName,0..2>",
      "emissions": "tuple<SafeDiagnosticEnvelope,1..2>"
    },
    "SafeRecoveryStep": {
      "action_reference": "Alias",
      "step_kind": "enum:RecoveryStepKind",
      "outcome": "enum:ObservedOutcome",
      "actual_state": "Signature|null",
      "event_indices": "tuple<uint32[0..1023],0..32>",
      "reason_template": "enum:MessageTemplate"
    },
    "SafeRecoveryDiagnostic": {
      "recovery_category": "enum:RecoveryCategory",
      "original_state_class": "enum:SystemClass",
      "original_diagnostic": "Alias",
      "steps": "tuple<SafeRecoveryStep,0..32>",
      "outcome": "enum:ObservedOutcome",
      "corrected_state": "Signature|null",
      "fallback_policy_id": "Alias|null",
      "reason": "TrustedTemplateText",
      "rule_ids": "tuple<enum:CanonicalRule,1..10>"
    },
    "PrivateAcknowledgmentWitness": {
      "original_reference": "UntrustedReference/API_ONLY",
      "collector_reference": "Alias",
      "session_reference": "Alias",
      "confirmed_sequence": "uint64",
      "emission_sha256": "Sha256/PRIVATE_ONLY"
    },
    "DiagnosticCounterState": {
      "field": "enum:CounterField",
      "status": "enum:CounterStatus",
      "reason": "enum:CounterReason|null"
    },
    "MetaDiagnosticRecord": {
      "meta_reference": "Alias",
      "local_sequence": "uint64",
      "clock": "ClockObservation",
      "envelope": "SafeDiagnosticEnvelope",
      "cause": "MetaCause",
      "message_template": "const:DIAGNOSTIC_NONCONFORMANCE"
    },
    "RecoveryAdmissionReceipt": {
      "status": "enum:AdmissionStatus",
      "operation_reference": "UntrustedOperationReference/API_ONLY",
      "origin_assessment_reference": "UntrustedReference/API_ONLY",
      "origin_diagnostic_references": "tuple<UntrustedReference/API_ONLY,2>",
      "reserved_events": "uint32[0..768]",
      "reserved_bytes": "uint32[0..31588352]",
      "failure_code": "enum:DiagnosticsFailure|null"
    },
    "SafeSourceEvidence": {
      "evidence_reference": "Alias",
      "dependency_id": "const:ash_cosmological_model.f2_9.canonical",
      "verified_pins": "tuple<SourcePin,8>",
      "external_source_reference": "Alias|null",
      "external_verification": "const:DECLARED_NOT_AUTHENTICATED"
    },
    "SafeNormalizationProof": {
      "evidence_reference": "Alias",
      "preparation_status": "enum:PreparationStatus",
      "original_assessment_reference": "Alias",
      "original_diagnosis_reference": "Alias",
      "submitted_plan_reference": "Alias|null",
      "policy_reference": "Alias",
      "submitted_source_reference": "Alias",
      "current_source_evidence_reference": "Alias",
      "submitted_profile_evidence_reference": "Alias",
      "current_profile_evidence_reference": "Alias",
      "origin_validation_status": "enum:ProofStatus",
      "plan_validation_status": "enum:ProofStatus",
      "decision": "enum:NormalizationDecision|null",
      "submitted_targets": "tuple<Signature,0..16>|null",
      "expected_targets": "tuple<Signature,0..16>|null",
      "submitted_target": "Signature|null",
      "expected_target": "Signature|null",
      "submitted_chain": "tuple<Signature,0..1>|null",
      "recomputed_chain": "tuple<Signature,0..1>|null",
      "failed_field": "enum:ValidationField|null",
      "safe_failure": "enum:SafeFailure|null"
    },
    "SafeCorrectionProof": {
      "evidence_reference": "Alias",
      "correction_reference": "Alias",
      "original_assessment_reference": "Alias",
      "submitted_source_reference": "Alias",
      "current_source_evidence_reference": "Alias",
      "submitted_profile_evidence_reference": "Alias",
      "current_profile_evidence_reference": "Alias",
      "declared_source_authentication": "const:DECLARED_NOT_AUTHENTICATED",
      "origin_validation_status": "enum:ProofStatus",
      "correction_validation_status": "enum:ProofStatus",
      "submitted_chain": "tuple<Signature,0..16>",
      "claimed_target": "Signature",
      "computed_target": "Signature|null",
      "target_diagnostic_reference": "Alias|null",
      "failed_field": "enum:ValidationField|null",
      "safe_failure": "enum:SafeFailure|null"
    },
    "SafeRegistryEntry": {
      "policy_reference": "Alias",
      "input_order_index": "uint32[0..31]",
      "ordering_rank": "int64",
      "applicability_condition_references": "tuple<Alias,0..8>",
      "validation_condition_references": "tuple<Alias,0..8>",
      "candidate_state": "Signature",
      "escalation_on_failure": "enum:EscalationPolicy",
      "certification_assessment_reference": "Alias",
      "certification_validation_status": "enum:ProofStatus",
      "target_diagnostic_reference": "Alias|null"
    },
    "SafeRegistryProof": {
      "evidence_reference": "Alias",
      "registry_reference": "Alias",
      "availability": "enum:ProfileAvailability",
      "declared_source_authentication": "const:DECLARED_NOT_AUTHENTICATED",
      "submitted_source_reference": "Alias",
      "current_source_evidence_reference": "Alias",
      "submitted_profile_evidence_reference": "Alias",
      "current_profile_evidence_reference": "Alias",
      "validation_status": "enum:ProofStatus",
      "entries": "tuple<SafeRegistryEntry,0..32>",
      "evaluated_policy_references": "tuple<Alias,0..32>",
      "failed_policy_reference": "Alias|null",
      "failed_field": "enum:ValidationField|null",
      "safe_failure": "enum:SafeFailure|null"
    },
    "StorePairReceipt": {
      "bundle_id": "Alias",
      "status": "const:COMPLETE",
      "parts": "tuple<PartReceipt,3>",
      "last_included_sequence": "uint64|null",
      "published": "const:true"
    },
    "StorePairFailure": {
      "bundle_id": "Alias",
      "status": "const:INCOMPLETE",
      "parts": "tuple<PartReceipt,3>",
      "last_included_sequence": "uint64|null",
      "failed_part": "enum:ExportPart",
      "failure_code": "enum:DiagnosticsFailure",
      "published": "const:false"
    },
    "SafeEvidenceSourceBinding": {
      "source_reference": "Alias",
      "source_digest_reference": "Alias",
      "evidence_reference": "Alias",
      "source_verification": "const:DECLARED_NOT_AUTHENTICATED"
    },
    "SafeConditionEvidence": {
      "condition_reference": "Alias",
      "source_binding": "SafeEvidenceSourceBinding"
    },
    "SafePredicateObservationEvidence": {
      "evidence_reference": "Alias",
      "status": "enum:PredicateObservationStatus",
      "condition_reference": "Alias",
      "expected_condition_source": "SafeEvidenceSourceBinding",
      "observed_provider_source": "SafeEvidenceSourceBinding",
      "operation_reference": "Alias",
      "origin_assessment_reference": "Alias",
      "registry_reference": "Alias",
      "registry_source_digest_reference": "Alias",
      "policy_reference": "Alias",
      "phase": "enum:PredicatePhase",
      "candidate_state": "Signature",
      "reason_template": "const:RECOVERY_ACTION_RECORDED"
    },
    "FallbackHealthRecord": {
      "cause_code": "enum:MetaCauseCode",
      "storage_state": "enum:StorageState",
      "last_confirmed_sequence": "uint64|null",
      "first_unavailable_sequence": "uint64|null",
      "last_unavailable_sequence": "uint64|null",
      "meta_overflow_count": "uint64|null",
      "clock": "ClockObservation",
      "coverage_status": "const:PARTIAL"
    },
    "DiagnosticsCompletionReceipt": {
      "operation_reference": "UntrustedReference/API_ONLY",
      "status": "enum:CompletionStatus",
      "operation_outcome": "enum:ObservedOutcome",
      "confirmed_event_indices": "tuple<uint32[0..1023],0..768>",
      "diagnostic_coverage": "enum:OverallCoverage",
      "failure_code": "enum:DiagnosticsFailure|null",
      "attempted_event_index": "uint32[0..1023]|null",
      "health": "DiagnosticsHealth"
    },
    "StorePurgeReceipt": {
      "bundle_id": "Alias",
      "status": "enum:RetentionReceiptStatus",
      "removed_parts": "uint32[0..3]",
      "removed_bytes": "uint64",
      "failure_code": "enum:DiagnosticsFailure|null"
    },
    "SafeExternalEscalationRequired": {
      "trigger_domain": "const:YWE_RECOVERABILITY_CATEGORY",
      "recovery_category": "const:ESCALATION_REQUIRED",
      "authority_status": "enum:AuthorityStatus"
    },
    "SafeExistingModeBoundary": {
      "trigger_domain": "const:YWE_OBSERVED_MODE_BOUNDARY",
      "observed_class": "enum:ExistingModeClass",
      "assessment_reference": "Alias"
    },
    "SafeRecoverySafetyPolicy": {
      "policy_id": "const:YWE-RECOVERY-SAFETY-001",
      "policy_version": "const:1.0.0",
      "policy_document": "const:docs/architecture/m3_recovery_safety_policy.md",
      "policy_sha256": "const:00fcee810c5cd445dd0baaaf98c754000347489001e21588eb03afdd1e1ebb95"
    },
    "SafeRecoveryDirective": {
      "requested_action": "enum:DirectiveAction",
      "trigger": "enum:CanonicalContainmentTrigger|enum:CanonicalSafeHaltTrigger|SafeExternalEscalationRequired|SafeExistingModeBoundary",
      "origin_assessment_reference": "Alias",
      "causing_decision_reference": "Alias",
      "evidence_references": "tuple<Alias,1..8>",
      "actual_mode_status": "const:NOT_ENTERED_BY_N2",
      "request_origin": "enum:RequestOrigin",
      "policy_binding": "SafeRecoverySafetyPolicy|null"
    },
    "SafeRecoverySafetyEvidence": {
      "evidence_reference": "Alias",
      "operation_reference": "Alias",
      "origin_assessment_reference": "Alias",
      "propagation_status": "enum:PropagationStatus",
      "propagation_source_binding": "SafeEvidenceSourceBinding",
      "propagation_was_consulted": "bool",
      "authority_status": "enum:AuthorityStatus",
      "authority_source_binding": "SafeEvidenceSourceBinding",
      "authority_was_consulted": "bool",
      "directive": "SafeRecoveryDirective|null"
    }
  },
  "enums": {
    "SourceStatus": [
      "VERIFIED_CLEAN",
      "VERIFIED_DIRTY",
      "UNKNOWN"
    ],
    "UnavailableReason": [
      "NOT_MEASURED",
      "NOT_PROVIDED",
      "EXCLUDED_REFERENCE_SCOPE",
      "NOT_IMPLEMENTED",
      "SOURCE_NOT_VERIFIED",
      "CLOCK_UNAVAILABLE",
      "LOSS_UNCONFIRMED",
      "RETENTION_EXPIRED",
      "STORAGE_UNAVAILABLE",
      "CLOCK_REGRESSION",
      "DURATION_LIMIT",
      "COUNTER_LIMIT"
    ],
    "OperatingSystem": [
      "WINDOWS",
      "LINUX",
      "MACOS",
      "UNKNOWN"
    ],
    "Architecture": [
      "X86_64",
      "ARM64",
      "UNKNOWN"
    ],
    "HostClass": [
      "HOST",
      "VM",
      "SIMULATOR",
      "UNKNOWN"
    ],
    "Implementation": [
      "REFERENCE_DEVELOPMENT_DIAGNOSTICS",
      "REFERENCE_RELEASE_DIAGNOSTICS"
    ],
    "ProfileId": [
      "REFERENCE_DEVELOPMENT",
      "REFERENCE_RELEASE"
    ],
    "CoverageSource": [
      "STATE_MODEL",
      "NORMALIZATION",
      "RECOVERY_ENGINE",
      "DIAGNOSTICS",
      "PROTECTED_STORAGE",
      "PAIRED_EXPORT",
      "REALM_ENCODER",
      "TRANSITION_REGISTRY",
      "TOPOLOGY_GENERATOR",
      "AXIOM_EVALUATOR",
      "GENERATION_PLANNER",
      "ARTIFACT_EMITTER",
      "NATIVE_RUNTIME",
      "NATIVE_RELEASE",
      "PHYSICAL_CRASH",
      "ENVIRONMENT_OS",
      "RUNTIME_VERSION",
      "ARCHITECTURE",
      "HOST_CLASS",
      "UTC_CLOCK",
      "MONOTONIC_CLOCK"
    ],
    "CoverageStatus": [
      "AVAILABLE",
      "UNAVAILABLE",
      "EXCLUDED"
    ],
    "OverallCoverage": [
      "COMPLETE_DECLARED_REFERENCE_SCOPE",
      "PARTIAL",
      "UNAVAILABLE"
    ],
    "RetentionReason": [
      "EXPLICIT_PURGE",
      "DURATION_EXPIRED",
      "WHOLE_OPERATION_ROTATION",
      "UNCERTAIN_STORAGE_RANGE"
    ],
    "StorageState": [
      "PROTECTED_VERIFIED",
      "UNAVAILABLE",
      "UNCERTAIN"
    ],
    "CanonicalKind": [
      "STATE_VALIDITY",
      "RECOVERY",
      "FALLBACK",
      "CONTAINMENT",
      "SAFE_HALT"
    ],
    "CanonicalSeverity": [
      "INFO",
      "WARNING",
      "ERROR",
      "CRITICAL"
    ],
    "CanonicalStage": [
      "DETECTION",
      "CLASSIFICATION",
      "RECOVERY",
      "ESCALATION",
      "TERMINAL"
    ],
    "CanonicalDisposition": [
      "RESOLVED",
      "PENDING",
      "BLOCKED",
      "ESCALATED",
      "TERMINAL"
    ],
    "CanonicalRule": [
      "ASH-STATE-STRUCTURE-001",
      "ASH-STATE-VALIDITY-001",
      "ASH-STATE-GENERAL-001",
      "ASH-CODEWORD-STRUCTURE-001",
      "ASH-ADMISSIBILITY-CLASSIFICATION-001",
      "ASH-CLASSIFICATION-MAPPING-001",
      "ASH-RECOVERY-ACTION-001",
      "ASH-FALLBACK-SELECTION-001",
      "ASH-CONTAINMENT-TRIGGER-001",
      "ASH-HALT-TRIGGER-001"
    ],
    "Admissibility": [
      "VALID",
      "TRANSFORMATION_COMPATIBLE",
      "TRANSFORMATION_INCOMPATIBLE",
      "UNCLASSIFIED"
    ],
    "Compatibility": [
      "COMPATIBLE",
      "INCOMPATIBLE",
      "UNKNOWN"
    ],
    "NormalizationStatus": [
      "ALREADY_VALID",
      "NORMALIZABLE",
      "NOT_NORMALIZABLE",
      "BLOCKED"
    ],
    "RecoverabilityRelevance": [
      "NO_RECOVERY_NEEDED",
      "RECOVERY_APPLICABLE",
      "NOT_RECOVERABLE",
      "CONTAINMENT_NEEDED"
    ],
    "SystemClass": [
      "STABLE",
      "UNSTABLE",
      "CORRECTABLE",
      "DEGRADED",
      "CONTAINED",
      "FAILED",
      "SAFE_HALT"
    ],
    "RecoveryCategory": [
      "NO_ACTION",
      "NORMALIZE_STATE",
      "APPLY_CORRECTION",
      "FALLBACK_REQUIRED",
      "CONTAINMENT_REQUIRED",
      "ESCALATION_REQUIRED",
      "TERMINAL_NO_RECOVERY"
    ],
    "PredicateName": [
      "CORRECTION_PATH_IS_KNOWN",
      "FALLBACK_IS_AVAILABLE",
      "APPLICABILITY",
      "ADDITIONAL_VALIDATION"
    ],
    "Producer": [
      "STATE_MODEL",
      "NORMALIZATION",
      "RECOVERY_ENGINE",
      "DIAGNOSTICS",
      "REFERENCE_HOST"
    ],
    "EventType": [
      "SESSION_START",
      "SESSION_END",
      "DIAGNOSTIC",
      "OPERATION_ADMITTED",
      "OPERATION_COMPLETED",
      "ACTION_OBSERVED",
      "INCIDENT",
      "META_DIAGNOSTIC",
      "HEALTH",
      "RETENTION",
      "EXPORT"
    ],
    "MessageTemplate": [
      "SESSION_OPENED",
      "SESSION_CLOSED",
      "ORIGIN_ATTACHED",
      "DIAGNOSIS_RECORDED",
      "CLASSIFICATION_RECORDED",
      "NORMALIZATION_COMPUTED",
      "POST_VALIDATION_RECORDED",
      "RECOVERY_ACTION_RECORDED",
      "RECOVERY_REFUSED",
      "RECOVERY_HANDOFF_RECORDED",
      "DIAGNOSTIC_NONCONFORMANCE",
      "CAPTURE_UNCONFIRMED",
      "RETENTION_REPORTED",
      "EXPORT_COMPLETE",
      "EXPORT_INCOMPLETE",
      "UNTRUSTED_PROSE_OMITTED"
    ],
    "ObservedOutcome": [
      "OBSERVED",
      "NOT_EVALUATED",
      "COMPLETED",
      "FAILED",
      "BLOCKED",
      "NOT_APPLICABLE",
      "ALREADY_VALID",
      "NORMALIZED",
      "NOT_NORMALIZABLE",
      "RECOVERED",
      "RECOVERED_VIA_FALLBACK",
      "RECOVERY_FAILED",
      "ESCALATE_TO_CONTAINMENT",
      "CONTAINMENT_HANDOFF",
      "HALT_HANDOFF",
      "TERMINAL_REFUSAL",
      "CONFIRMED",
      "REJECTED",
      "NOT_CONFIRMED",
      "INCOMPLETE"
    ],
    "FailureDomain": [
      "INPUT",
      "STATE",
      "NORMALIZATION",
      "RECOVERY",
      "DIAGNOSTICS",
      "STORAGE",
      "EXPORT"
    ],
    "SafeFailure": [
      "SOURCE_REPORTED_FAILURE",
      "ORIGINAL_PROFILE_MISMATCH",
      "ORIGINAL_SOURCE_MISMATCH",
      "ORIGINAL_DIAGNOSIS_MISMATCH",
      "PLAN_TARGET_SET_MISMATCH",
      "PLAN_SELECTION_MISMATCH",
      "PLAN_CODEWORD_MISMATCH",
      "INPUT_REJECTED",
      "PROFILE_UNAVAILABLE",
      "NO_TARGET",
      "POST_VALIDATION_FAILED",
      "CAPTURE_REJECTED",
      "CAPTURE_UNCONFIRMED",
      "REGISTRY_UNAVAILABLE",
      "NO_APPLICABLE_POLICY",
      "CORRECTION_PROVIDER_UNAVAILABLE",
      "CORRECTION_PROOF_INVALID",
      "NONCONFORMANT_DIAGNOSTIC",
      "MISSING_REQUIRED_STEP",
      "STORAGE_FAILURE",
      "EXPORT_FAILURE"
    ],
    "SafeField": [
      "ORIGINAL_SOURCE",
      "ORIGINAL_PROFILE",
      "ORIGINAL_DIAGNOSIS",
      "ORIGINAL_ASSESSMENT",
      "TARGET_SET",
      "SELECTED_TARGET",
      "CODEWORD_CHAIN",
      "INPUT",
      "POST_VALIDATION",
      "CAPTURE",
      "REGISTRY",
      "APPLICABILITY",
      "ADDITIONAL_VALIDATION",
      "CANONICAL_ENVELOPE",
      "CHAIN",
      "EXPECTED_STEP",
      "STORE",
      "EXPORT_PART"
    ],
    "FactType": [
      "ACTUAL_STATE_RETAINED",
      "STEP_COMPLETED",
      "POST_STATE_VALID",
      "POST_STATE_NOT_VALID",
      "CAPTURE_CONFIRMED",
      "CAPTURE_NOT_CONFIRMED",
      "ORIGIN_BINDING_DIFFERED",
      "PLAN_PROOF_DIFFERED",
      "REGISTRY_UNAVAILABLE",
      "NO_CANDIDATE_APPLICABLE",
      "REQUIRED_STEP_MISSING",
      "WHOLE_PAIR_COMPLETED",
      "PAIR_INCOMPLETE"
    ],
    "ExpectedInvariant": [
      "VALID_RETURN",
      "STABLE_RETURN",
      "ACKNOWLEDGED_STEPS",
      "NO_EFFECTS_ON_REFUSAL",
      "COMPLETE_CHAIN",
      "PAIRED_EXPORT",
      "SAFE_PROJECTION"
    ],
    "UnknownCause": [
      "NO_SUPPORTED_CAUSE",
      "STORAGE_COMMIT_UNCONFIRMED",
      "CLOCK_NOT_MEASURED",
      "EXTERNAL_COLLECTOR_TRUTH_NOT_VERIFIED",
      "NATIVE_RUNTIME_NOT_REALIZED",
      "PHYSICAL_CRASH_NOT_EXERCISED"
    ],
    "PinnedSource": [
      "YWE_IMPLEMENTATION",
      "ASH_AGGREGATE",
      "ASH_STATE_SPACE",
      "ASH_CODEWORDS",
      "ASH_VALIDITY",
      "ASH_CLASSIFICATION",
      "ASH_RECOVERY",
      "ASH_DIAGNOSTIC_SCHEMA",
      "ASH_TAXONOMY",
      "RAVEN_POLICY",
      "YWE_NORMALIZATION_POLICY"
    ],
    "OmissionCategory": [
      "SUMMARY",
      "NOTES",
      "CALLER_REFERENCE",
      "PROFILE_ID",
      "UNVERIFIED_SOURCE_DIGEST",
      "EVIDENCE_REFERENCE",
      "INPUT_PREVIEW",
      "NON_BIT_SCALAR",
      "URL",
      "QUERY",
      "HEADER",
      "BODY",
      "EXCEPTION_TEXT",
      "CAUSAL_TEXT",
      "STACK",
      "ABSOLUTE_PATH",
      "ATTACHMENT",
      "UNREGISTERED_PAYLOAD",
      "HYPOTHESIS"
    ],
    "RedactionReason": [
      "UNTRUSTED_FREEFORM",
      "OPAQUE_REFERENCE_ALIAS",
      "UNSUPPORTED_SOURCE",
      "SENSITIVE_CONTENT",
      "EXCLUDED_REFERENCE_SCOPE"
    ],
    "LimitationCode": [
      "REFERENCE_IMPLEMENTATION_ONLY",
      "DECLARED_PRODUCERS_ONLY",
      "TRUSTED_CAPTURE_CONTRACT",
      "NO_REMOTE_ACK_AUTHENTICATION",
      "NATIVE_COMPOSITION_DEFERRED",
      "NATIVE_RELEASE_DEFERRED",
      "NO_PHYSICAL_CRASH_PROOF",
      "NO_POWER_LOSS_DURABILITY_PROOF",
      "NO_ENCRYPTION_CLAIM",
      "NO_SECOND_USER_ACCESS_TEST",
      "NO_AMBIENT_ACTIVITY_CAPTURE",
      "UNTRUSTED_PROSE_OMITTED",
      "LOSS_RANGE_COALESCED",
      "PARENT_STORAGE_NOT_VERIFIED"
    ],
    "MetaCauseCode": [
      "REQUIRED_FIELD_MISSING",
      "SCHEMA_NONCONFORMANCE",
      "RULE_NOT_APPROVED",
      "DUPLICATE_REFERENCE",
      "PARENT_MISMATCH",
      "ROOT_MISMATCH",
      "SUBJECT_MISMATCH",
      "STAGE_REGRESSION",
      "TERMINAL_SUCCESSOR",
      "REQUIRED_STEP_MISSING",
      "PRODUCER_PAYLOAD_MISMATCH",
      "CLOCK_UNAVAILABLE",
      "CLOCK_REGRESSION",
      "DURATION_EXPIRED",
      "COUNTER_LIMIT",
      "MAIN_CAPACITY_EXHAUSTED",
      "COMPLETION_MISSING"
    ],
    "ExpectedPhase": [
      "DETECTION",
      "CLASSIFICATION",
      "COMPUTATION",
      "POST_VALIDATION",
      "RECOVERY_PREDICATE",
      "RECOVERY_STEP",
      "RECOVERY_POST_ASSESSMENT",
      "BOUNDARY_HANDOFF"
    ],
    "StorageCommitStatus": [
      "COMMITTED",
      "REJECTED",
      "UNKNOWN"
    ],
    "ExportPart": [
      "JSON",
      "MARKDOWN",
      "MANIFEST",
      "PUBLICATION"
    ],
    "PartName": [
      "diagnostics.json",
      "diagnostics.md",
      "manifest.json"
    ],
    "PartStatus": [
      "NOT_WRITTEN",
      "WRITTEN_UNCONFIRMED",
      "CONFIRMED"
    ],
    "RetentionReceiptStatus": [
      "COMPLETED",
      "REJECTED"
    ],
    "StorageVerificationStatus": [
      "VERIFIED",
      "REJECTED"
    ],
    "StoragePrincipal": [
      "EFFECTIVE_USER",
      "SYSTEM"
    ],
    "ContextField": [
      "INPUT_STATE",
      "ACTUAL_STATE",
      "SELECTED_TARGET",
      "ELIGIBLE_TARGETS",
      "CODEWORD_CHAIN",
      "ADMISSIBILITY_STATUS",
      "TRANSFORMATION_COMPATIBILITY",
      "NORMALIZATION_STATUS",
      "RECOVERABILITY_RELEVANCE",
      "IS_VALID",
      "ORBIT_INFO",
      "SYSTEM_STATE_CLASS",
      "RECOVERY_CATEGORY",
      "PREDICATE_NAME",
      "PREDICATE_VALUE",
      "CANDIDATE_ORDER_INDEX",
      "STEP_INDEX",
      "PROFILE_REFERENCE",
      "SOURCE_EVIDENCE_REFERENCE",
      "FIXTURE_REFERENCE",
      "PROFILE_EVIDENCE_REFERENCE",
      "ORIGINAL_ASSESSMENT_REFERENCE",
      "POST_ASSESSMENT_REFERENCE",
      "RECOVERY_DIAGNOSTIC_REFERENCE",
      "BEFORE_STATE",
      "CODEWORD",
      "AFTER_STATE",
      "POLICY_REFERENCE",
      "VALIDATION_STATUS",
      "FAILED_FIELD",
      "PROOF_EVIDENCE_REFERENCE",
      "RECOVERY_SAFETY_EVIDENCE_REFERENCE"
    ],
    "InputFailure": [
      "INPUT_DEPTH_LIMIT",
      "INPUT_JSON_DUPLICATE_KEY",
      "INPUT_JSON_INVALID",
      "INPUT_JSON_NONFINITE",
      "INPUT_KIND_UNSUPPORTED",
      "INPUT_NUMERIC_TOKEN_INVALID",
      "INPUT_RECORD_INVALID",
      "INPUT_RECORD_KEY_INVALID",
      "INPUT_RECORD_SIZE_LIMIT",
      "INPUT_SIGNATURE_INVALID",
      "INPUT_SIZE_LIMIT",
      "INPUT_STATE_SPACE_INVALID",
      "INPUT_TOKEN_LIMIT",
      "INPUT_UTF8_INVALID",
      "STATE_COORDINATE_TYPE",
      "STATE_COORDINATE_VALUE",
      "STATE_WIDTH"
    ],
    "DiagnosticsFailure": [
      "DIAGNOSTICS_VALUE_INVALID",
      "DIAGNOSTICS_CONFIG_INVALID",
      "DIAGNOSTICS_ORIGIN_UNAVAILABLE",
      "DIAGNOSTICS_ORIGIN_MISMATCH",
      "DIAGNOSTICS_RESERVATION_REFUSED",
      "DIAGNOSTICS_EVENT_TOO_LARGE",
      "DIAGNOSTICS_ALIAS_LIMIT",
      "DIAGNOSTICS_BYTE_LIMIT",
      "DIAGNOSTICS_DURATION_LIMIT",
      "DIAGNOSTICS_SEQUENCE_LIMIT",
      "DIAGNOSTICS_RECORD_NONCONFORMANT",
      "DIAGNOSTICS_REQUIRED_STEP_MISSING",
      "DIAGNOSTICS_META_UNAVAILABLE",
      "DIAGNOSTICS_COLLECTOR_FAILURE",
      "STORAGE_PROTECTION_UNAVAILABLE",
      "STORAGE_PARENT_UNTRUSTED",
      "STORAGE_IDENTITY_CHANGED",
      "STORAGE_REPARSE_REFUSED",
      "STORAGE_PATH_ALREADY_EXISTS",
      "STORAGE_COMMIT_REJECTED",
      "STORAGE_COMMIT_UNCONFIRMED",
      "EXPORT_SNAPSHOT_INVALID",
      "EXPORT_REDACTION_FAILED",
      "EXPORT_JSON_FAILED",
      "EXPORT_MARKDOWN_FAILED",
      "EXPORT_MANIFEST_FAILED",
      "EXPORT_PUBLICATION_FAILED",
      "EXPORT_BYTE_LIMIT",
      "EXPORT_PARITY_FAILED",
      "DIAGNOSTICS_COMPLETION_MISSING",
      "DIAGNOSTICS_COMPLETION_MISMATCH",
      "DIAGNOSTICS_REPLAY_REFUSED",
      "DIAGNOSTICS_SUPPORTING_LIMIT",
      "DIAGNOSTICS_INCIDENT_LIMIT",
      "DIAGNOSTICS_RAW_PACKET_LIMIT",
      "EXPORT_SLOT_OCCUPIED",
      "DIAGNOSTICS_CLOCK_UNAVAILABLE",
      "DIAGNOSTICS_CLOCK_REGRESSION",
      "DIAGNOSTICS_COUNTER_LIMIT"
    ],
    "ProfileAvailability": [
      "AVAILABLE",
      "UNAVAILABLE"
    ],
    "SafeInputKind": [
      "ASH_STATE",
      "REJECTED"
    ],
    "PredicateEvaluation": [
      "EVALUATED",
      "NOT_EVALUATED"
    ],
    "RecoveryStepKind": [
      "NORMALIZE",
      "CORRECT",
      "APPLICABILITY",
      "ADDITIONAL_VALIDATION",
      "SELECT_FALLBACK",
      "VALIDATE_RECOVERY",
      "VALIDATE_FALLBACK",
      "CANDIDATE_DECISION",
      "HANDOFF",
      "SUMMARY"
    ],
    "CounterField": [
      "ACCEPTED",
      "REJECTED",
      "RETAINED",
      "EXPIRED",
      "LOST",
      "REDACTED_FIELDS",
      "REDACTED_REFERENCES",
      "META_OVERFLOW"
    ],
    "CounterStatus": [
      "EXACT",
      "SATURATED",
      "UNAVAILABLE"
    ],
    "CounterReason": [
      "COUNTER_LIMIT",
      "STORAGE_UNCONFIRMED"
    ],
    "AdmissionStatus": [
      "CONFIRMED",
      "REJECTED",
      "NOT_CONFIRMED"
    ],
    "ProofStatus": [
      "NOT_EVALUATED",
      "VERIFIED",
      "REJECTED"
    ],
    "NormalizationDecision": [
      "ALREADY_VALID",
      "PLAN_READY",
      "NOT_NORMALIZABLE",
      "BLOCKED"
    ],
    "PreparationStatus": [
      "READY",
      "UNAVAILABLE",
      "REJECTED"
    ],
    "StepStatus": [
      "COMPLETED",
      "BLOCKED",
      "FAILED"
    ],
    "ValidationField": [
      "ORIGINAL_SOURCE",
      "ORIGINAL_PROFILE",
      "ORIGINAL_DIAGNOSIS",
      "ORIGINAL_ASSESSMENT",
      "ORIGIN_PROFILE",
      "ORIGIN_SOURCE",
      "SUBMITTED_SOURCE",
      "SUBMITTED_PROFILE",
      "TARGET_SET",
      "SELECTED_TARGET",
      "CODEWORD_CHAIN",
      "REGISTRY_SOURCE",
      "REGISTRY_PROFILE",
      "CERTIFICATION_INVENTORY",
      "CERTIFICATION_STATE",
      "POST_VALIDATION",
      "INPUT",
      "UNKNOWN_REGISTERED_FIELD"
    ],
    "EscalationPolicy": [
      "TRY_NEXT",
      "ESCALATE_TO_CONTAINMENT"
    ],
    "PredicatePhase": [
      "APPLICABILITY",
      "ADDITIONAL_VALIDATION"
    ],
    "PredicateObservationStatus": [
      "TRUE",
      "FALSE",
      "UNAVAILABLE"
    ],
    "SupportingKind": [
      "CANONICAL_SOURCE",
      "PROFILE",
      "ASSESSMENT",
      "RECOVERY_DIAGNOSTIC",
      "NORMALIZATION_PROOF",
      "CORRECTION_PROOF",
      "REGISTRY_PROOF",
      "CONDITION",
      "PREDICATE_OBSERVATION",
      "RECOVERY_SAFETY"
    ],
    "CompletionStatus": [
      "COMPLETE",
      "INCOMPLETE"
    ],
    "PropagationStatus": [
      "SAFE",
      "RISK",
      "UNAVAILABLE"
    ],
    "AuthorityStatus": [
      "REACHABLE",
      "UNREACHABLE",
      "UNAVAILABLE"
    ],
    "DirectiveAction": [
      "ENTER_CONTAINMENT",
      "REQUEST_EXTERNAL_AUTHORITY",
      "ENTER_SAFE_HALT",
      "REMAIN_CONTAINED",
      "REMAIN_SAFE_HALT"
    ],
    "RequestOrigin": [
      "POLICY",
      "SOURCE_RECOVERABILITY",
      "OBSERVED_EXISTING_MODE"
    ],
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
    "ExistingModeClass": [
      "CONTAINED",
      "SAFE_HALT"
    ]
  },
  "conditions": [
    "Every constructor and wire object has exactly its listed fields; copied tuples and immutable exact owned children only. Snapshot header is fixed schema_ref data/schemas/m3_reference_diagnostic_bundle_schema.json, artifact_type ywe_reference_diagnostic_bundle, artifact_version1.0.0; header fields are not constructor-selectable.",
    "SourceProvenance VERIFIED_CLEAN/VERIFIED_DIRTY requires matching actual verified_revision and DiagnosticsIdentity.source_revision; UNKNOWN has null revision and nonnull reason. VERIFIED_CLEAN dirty paths empty; DIRTY nonempty. Caller paths are aliased.",
    "Profile/Identity implementation and profile agree; DEVELOPMENT enables safe development-only payloads, RELEASE does not. Native release status is always deferred/not verified in this reference proposal.",
    "Optional unknown/nonmeasured clock/duration values are null iff their reason is nonnull. Inapplicable SafeStateContext values are null and their field names are in unavailable_fields; recognized_valid_states may be empty as actually evaluated, null means not evaluated.",
    "Event envelope/diagnostic_reference both nonnull only for diagnostic/meta event types; source templates provide summaries/notes and safe payload, not raw producer prose. Error present only when a typed failure was observed. SAFE_HALT contextual assessment remains CLASSIFICATION with TERMINAL disposition and does not assert actual mode entry.",
    "Recovery origin attachment requires exact two confirmed records from this collector; separate child assessment relation retains its own DETECTION root. N2 refuses recovery from TERMINAL_NO_RECOVERY out of the original chain; never append RECOVERY to terminal contextual origin. Actual incident-freeze-on-terminal is deferred to N3 entry/final emission.",
    "Reserved worst-case budget precedes all effects and includes child pairs; collector max1024 and N2 operation768. Counts include all stored events, incidents, alias metadata and reserved bounded health accounting; byte cap is authoritative. No active or incident-pinned operation prefix eviction.",
    "Incident timeline/error/attempt references resolve to retained snapshot events; facts/findings reference concrete events. Hypotheses empty in this implementation scope; UnknownCause entries explicitly account for unsupported causal conclusions.",
    "Health unavailable sequence ranges are null iff no known unconfirmed/lost range; unknown gaps remain unavailable, not falsely counted healthy. Retention range coalescing is explicit and retains overall counts, boundaries and limitation.",
    "COMMITTED only after host write/flush contract actual completion; UNKNOWN is never CONFIRMED. ExportReceipt requires3CONFIRMEDparts(JSON/Markdown/manifest), actual parity+checksum agreement and final publication completion. ExportFailure retains same snapshot and known part states; no success after partial pair.",
    "Source pins represent actual approved verified sources only. Arbitrary caller hex/source strings are aliases/omitted, never accepted as trusted merely by shape.",
    "Proposed local meta mapping is separate STATE_VALIDITY/DETECTION/ERROR/BLOCKED root with ASH-STATE-GENERAL-001 and safe MetaCause correlation outside canonicalTEN. Invalid original record is not meta root. Meta persistence failure uses bounded fallback health/no recursion.",
    "SafeFailure is a closed sanitized mapping. Unregistered producer codes become SOURCE_REPORTED_FAILURE with source alias and omission accounting; never echo raw error code/text. N2 source-owned codes may be added explicitly before adoption, not by dynamic heuristic.",
    "Profiles and full original/postassessment assemblies are retained once as SupportingEvidence; events carry their references. Supporting has an authoritative2MiB byte cap; per-action RecoveryDiagnostic.steps<=32, not all512predicate events duplicated. Detailed action/predicate events are globally retained and referenced by bounded event_indices.",
    "A scope remains incomplete until mandatory typed completion. Existing begin/append does not infer diagnosis-versus-assessment completion by record count. Reference composition run_diagnose/run_assess/run_normalization must call exact completion once and return unchanged raw business result plus separate completion observation; N2 invokes scope.finish and every postchild complete_assessment before recovered claim.",
    "Completion compares already confirmed prefix and exact separately attempted failed record. Capture/evidence failures retain raw business result and explicitPARTIAL diagnostic coverage; no fabricated missing-classification success. Missing completion staysuncompleted in snapshots and emits bounded meta/health evidence at declared operation/capture shutdown boundaries.",
    "Export quotas are independent: capture32MiB; JSON32MiB; Markdown48MiB consisting same complete JSON appendix32MiB plus fixed bounded detailed rendering16MiB; manifest64KiB; global protected bytes128MiB; one bundle slot including incomplete. Second export refuses until explicit whole-bundle purge. JSON uses compact owned structured encoding, not unbounded pretty expansion.",
    "Logical serialized buffers are capped192MiB: capture32+one snapshot32+JSON32+Markdown48+raw business packet32+alias2=178MiB plusbounded overhead margin. This is not a claim about exact Python heap overhead; reference performance/memory observation must declare runtime/platform and measurement limitation.",
    "Completion missingand replay areexplicit audit/nonconformance conditions; underlyingbusiness result remainsunchanged but referenceexecution cannotclaimcomplete Diagnostics or N2 RECOVERED when required postchild capture/completion fails. Exact resultclass/branch expectationregistry adopted separately; no free caller expectedcount.",
    "Private acknowledgment digest and original reference are not DiagnosticSnapshot fields and never serialize in export/persistence. Raw original producer prose is not a collector ledger payload. Exact record content comparison uses the adopted fixed complete-record fingerprint, with collision resistance stated explicitly.",
    "All clock observations occur through the injected trusted clock port under the collector serialization lock at admission, append, completion and snapshot boundaries. Available monotonic readings are exact uint64, never regress, and elapsed now-start <=600000000000 nanoseconds. Unavailable, malformed, overflowing or regressing monotonic observation refuses admission or stops further capture with explicit failure/partial health; no fake zero duration. An operation already performed retains its actual business result and returns unconfirmed attempted capture. Duration is enforced at observed boundaries, not by an unclaimed background deadline or arbitrary caller timestamp.",
    "UTC is supplementary and may be unavailable with null/reason. CaptureWindow retains first/last confirmed observations and explicit failed end observation. Snapshot generated_at_utc is null iff generation_time_reason nonnull; exporting prior retained evidence remains possible after clock failure. No canonical classifier/math result depends on clock data.",
    "Every eight-counter row exists in CounterField order. EXACT requires nonnull exact uint64 and null reason; SATURATED requires18446744073709551615 and COUNTER_LIMIT, explicitly a lower bound; UNAVAILABLE requiresnull/STORAGE_UNCONFIRMED. Checked increments saturate and stop admission on sequence/counter authority overflow, never wrap. Unknown lost count is null, not invented zero. Retained/accepted values only derive actual confirmed receipts; no estimated health counts.",
    "Independent meta/health pool65536 bytes comprises16*3072 meta records +8192 health status +8192 nonrecursive fallback. Main event/support/incident exhaustion cannot consume this reservation. Meta records are separate from main event slots, never falsely acknowledged as missing business step. Meta storage failure records one bounded fallback cause/counter state and refuses/unconfirms affected capture without logging another meta record recursively; exhausted meta capacity coalesces explicit overflow counter/health and no loss-free claim.",
    "Snapshot event/incident/meta references resolve within the retained event/meta namespace, with global serialized sequence ordering. Determinism applies only to equal explicit identities, observations, retention state and observed serialized call order; unordered concurrent calls do not imply a platform-independent byte order.",
    "Safe profile512 signatures, exact source-pin ledger, original/post assessment semantic row/context/two predicate facts/emission refs and action-local32step summaries are mandatory once-referenced supporting graph. No full raw profile/packet is copied into event context; detailed consulted predicates/XOR observations remain in globally indexed retained events. Projection omissions have explicit category/count, never silent semantic list truncation.",
    "Source projection copies DIAGNOSTIC_ROWS canonical value RECOVERY_APPLICABLE; PredicateName uppercase labels map explicitly to lowercase source fields correction_path_is_known/fallback_is_available. N1 PLAN_READY maps only planning decision; actual packet outcomes ALREADY_VALID/NORMALIZED remain those observed outcomes, not RECOVERED runtime claims.",
    "SafeStateContext.step_index preserves exact RecoveryStepEvidence transaction-global0..767. Original N1 local step indices remain0..0 in their observed subset; no index clamping or truncation. Safe before_state/codeword/after_state preserve actual typed RecoveryStepEvidence vectors, with null only when actual source field absent.",
    "NormalizationPreparation/PlanValidation project to SafeNormalizationProof: original diagnosis/assessment refs, fixed local policy ref, full submitted/current profile and source evidence refs, actual origin/plan statuses, all submitted/expected targets (<=16), actual chosen targets and full submitted/recomputed chain (<=1), precise normalized failed-field/failure. KnownCorrection/CorrectionValidation project to SafeCorrectionProof preserving full submitted<=16 chain, claimed/computed target, actual origin/proof status and target diagnosis ref.",
    "RegistryValidation projects complete entries/input order/rank/applicability and validation refs/target/escalation/certification assessment ref once in SafeRegistryProof, plus exact evaluated prefix and failed policy/field/status. Every certification semantic assessment is retained once in SafeAssessmentEvidence, target diagnostic refs resolve to that actual evidence. No arbitrary raw notes/source metadata in proof graph; omissions count SUMMARY/NOTES/PROFILE_ID/UNVERIFIED_SOURCE_DIGEST/EVIDENCE_REFERENCE/CALLER_REFERENCE as appropriate, all aliases preserve same-session equality.",
    "SafeSourceEvidence is separate verified canonical source ledger. Only actual source pins from reviewed canonical identity are literal SHA256; external caller source/digest claims are aliases and DECLARED_NOT_AUTHENTICATED. SafeNormalizationProof/SafeCorrectionProof/SafeRegistryProof comparison statuses retain observed actual mismatch fields with submitted/current evidence aliases. Exact raw values remain only caller-owned immutable packets/private bounded comparisons; sanitized graph does not falsely authenticate external data.",
    "ValidationField is an explicit reviewed mapping: original_diagnosis.profile_binding->ORIGINAL_PROFILE; original_diagnosis.source_binding->ORIGINAL_SOURCE; original_diagnosis/state math->ORIGINAL_DIAGNOSIS; submitted origin assessment->ORIGINAL_ASSESSMENT; submitted target list/selected/chain->TARGET_SET/SELECTED_TARGET/CODEWORD_CHAIN; registry source/profile/cert inventory/state->REGISTRY_SOURCE/REGISTRY_PROFILE/CERTIFICATION_INVENTORY/CERTIFICATION_STATE. An unregistered bounded source path maps UNKNOWN_REGISTERED_FIELD with omitted raw path count, never guessed provenance. Fields cannot be selected independently of owned actual typed validation.",
    "The hard2MiB supporting cap is authoritative over per-type maxima. One operation bound retains at most16 full profile nodes (conservative),66 assessment nodes (origin+33post+32cert),35 action summaries, one normalization proof, one correction proof and one registry proof; source ledger16 conservative nodes. More existing/reserved supporting data refuses admission before effects rather than truncate or duplicate. Profile/assessment nodes each<=8192bytes; registry/proof/action node each<=32768bytes; individual event remains32768.",
    "Alias capacity6144; complete operation reserves5403 conservative novel aliases in addition to alreadyallocated/pinned/reserved aliases beforeeffects. Bound5403 comprises512ConditionReferences*4=2048 +512provider source triples=1536 +768diagnosticrefs +35actionrefs +33post facts*12=396 +32certifications*13=416 +64origin/registry/proof refs +16profile nodes*4=64 +64control/session/build/incident/meta/bundle refs +12single-malformed-return margin. Reused operation/origin/registry/parent/source bindings do not allocate twice. Producer prose/raw unknown tokens are omitted, not dynamically aliased. Required free capacity and2MiB authoritative private ledger byte quota checked beforeeffects; unavailable capacity refuses whole operation.",
    "Protected host factory admits direct fresh D:/child on the verified NTFS volume root only when actual root ACL has no ordinary DELETE_CHILD/WRITE_DAC/WRITE_OWNER/generic-all substitution capability. Ordinary create-file/create-directory permissions alone are allowed. Root drive mapping, native volume identity and nonreparse root checked; fresh child atomic protected effective-user/SYSTEM DACL before anywrite. C:/root AuthenticatedUsersFullControl includes DELETE_CHILD and fails this factory route; nested readonly ancestors do notrepairthat root grant. Existing arbitrary path parents remain unavailable unless equallyverifiedagainstallancestors.",
    "Configured host factory verifies actual parent/ownedrootACLs, currentowner, nonreparse components, nativevolume/fileidentity before/afterIO, exclusive fixed ownedpartnames, actualflush/readback. Caller StorageVerification booleans are not capabilities. Same-user/SYSTEM/Administrator attacks excluded. Observed noDelete-share handle didnotprevent sameuser directoryrename; no such guarantee asserted. Every stored file must inherit or carry exactly protected-root effectiveuser/SYSTEM grants and be heldopen throughwrite/readback; no adopting preexisting file or silent fallback.",
    "ProtectedStore never reconstructs DiagnosticSnapshot from raw JSON. StorePairReceipt COMPLETE iff threepartsCONFIRMED+actualpublication, publishedtrue. StorePairFailureINCOMPLETE retains actual knownpartstatuses, publishedfalse and stablefailedpart/code; Diagnostics matchesbundle/parts/sequence againstownrequest and forms ExportReceipt/Failure containing alreadyownedsnapshot. Malformed/throwing hostreceipt produces explicitunconfirmedfailure, no inferredsuccess.",
    "RecoveryAdmissionReceipt CONFIRMED requiresnonnullscope, exactoriginalassessment/two diagnosticrefs, nullfailure and one exactadmission pair: normal768events/31588352bytes; terminaldenial1event/270336bytes. REJECTED/NOT_CONFIRMED requiresnullscope/zeroreservations/nonnullfailure. RawrefsAPIonly; safeadmissionprojectionusesaliases.",
    "CoverageSource inventory is exact ordered complete declared21source table; AVAILABLE reasonnull, UNAVAILABLE/EXCLUDED reasonnonnull. Health.missing_sources contains only actual unavailable/excluded rows. Unknown environment enum fields have matching unavailable_sources reasons; runtime_version null exactly when unavailable. No fabricated machine/runtime measurements. Snapshot captured time is exact27ASCII microsecondUTCformat; no unbounded fractional precision.",
    "SourcePin identity is the exact8 digest rows in CanonicalAshBinding: ASH_AGGREGATE aggregate_sha256, ASH_STATE_SPACE state_space_sha256, ASH_CODEWORDS codeword_source_sha256, ASH_VALIDITY validity_source_sha256, ASH_CLASSIFICATION classification_source_sha256, ASH_RECOVERY recovery_source_sha256, ASH_DIAGNOSTIC_SCHEMA diagnostic_source_sha256, ASH_TAXONOMY taxonomy_source_sha256. Dependency_id is separate fixedliteral, not a SHA row. Eight sourcekinds unique and orderfixed; contentverify duringassembly; claimedcaller hashshapes do not confertrust.",
    "SafeConditionEvidence and SafePredicateObservationEvidence retain exact expected declaredcondition triple and observedprovidersource triple as3aliases(source/refdigest/evidence), explicit DECLARED_NOT_AUTHENTICATED; provider truth status/candidate/phase/registry/operation/origin retained. Eventsource_evidence_reference resolves the actual observation node, conditionrefs resolve complete declaredbinding. Source/digest inequality remains auditable from aliases/comparison status without exposingunverifiedstrings. Free reasons/notes are omitted withcount, not guessedcause.",
    "For diagnostic events event_id aliases the actual diagnostic_reference, avoiding another anonymous alias perstoredrecord. Supporting observation reference reuses corresponding actual diagnosticref in explicitlytyped supporting namespace; no rawkeyalias growthforinternalobjectcopies. Control/incident/meta/bundle/identity allocations conservativelyreserve64slots; wholeoperationnovelaliasbound5403. Completion receipts/failures contain exact raw operation_reference onlyinmemoryAPI, to let engine check equality; snapshotprojectionaliases it.",
    "SourcePin.revision denotes the verified YWE implementation snapshot containing the vendored byte set, not an invented upstream commit. RAVEN_POLICY row uses actual independently checked policy revision87409bc36fb9d4782eab02189adb184f2b3962a7; external provider source provenance remains DECLARED_NOT_AUTHENTICATED. The verified canonical manifest aggregate algorithm is sha256_sorted_relative_path_nul_file_sha256_lf with utf8_optional_bom_crlf_cr_to_lf_preserve_final_newline; eight fixed binding digests match actual ash_dependency_identity files/aggregate.",
    "Safe graph is actuallyprotectedpersisted before businessrecord CONFIRMED/completion: commit_supporting everynew exact closednode (max32KiB) in source/profile/condition/assessment/proof dependencyorder, then commit_event actualreferencingrecord; cachednode reuse requiressamekind+alias+exactbytes and priorconfirmedcommit. Partial/unknown supportingcommit prevents referring eventconfirmation and yields explicit partialscope/coverage with retainedactualbusinessresult; danglingunconfirmed nodes aremarkedunavailable, notfalselysuccess. Nodes are immutable/idempotentonlyexactidentical; conflict refuses, neveroverwrite.",
    "Actual state/meta/fallback health commits use separate definedports andreservedcaps. One latesthealth andone fallbackslot replaces onlypreviousownconfirmedstatus with explicit supersession; collector doesnotclaimfullhealthrevisionhistory. Canonicalbusinesssteps/meta records neverbatch/suppress; healthsnapshot remainsboundedwithcoalescedranges/counters. Protectedstorecannot silentlyspill supporting/rawpackets outsidequotas. StorageReceipt sequence null allowed onlyhealth/fallbackbeforeanyeffect, neverevent/support/meta; matchedrequestandsuccess actualIO required.",
    "DiagnosticsCompletionReceipt is the one exact immutable completiontype; COMPLETE has nullfailure and no unconfirmed attemptedindex, exactrawoperationreference and fulfilled actualtypedresult expectations; INCOMPLETE has nonnullfailure, actualknownconfirmedprefix/attemptindex and partial/unavailable coverage. No separate polymorphic completionfailure object. Receipt canretainactualproducer outcome evenwhen capture completionfails; it doesnotchangeactualcandidate or falselypermitRECOVERED. Exact matchingCOMPLETE onlypermitsfinalimmutablebusinessreturn; INCOMPLETE retained failureobservation, wrong-reference typedreceipt retained submittedfailureevidence, throw malformedreceipt mappedclosedfailure, neverrecursivefinish.",
    "StorePurgeReceipt COMPLETED hasnullfailure andverifiedabsenceofallknownownedbundleparts, exactremovedpartcount/bytes, freesoneslot; REJECTED hasnonnullfailure andactualknownpartialremoval facts, leaves slotoccupied. No arbitraryhost Corehealth/RetentionReceipt reconstruction. Explicitpurgeconfinedexactownedbundleidentity andauthorizedoperation; no silent deletion/overwrite.",
    "SafeRecoverySafetyEvidence retains actual submitted propagationSAFE/RISK/UNAVAILABLE and authorityREACHABLE/UNREACHABLE/UNAVAILABLE, their aliasedfullsource triples, explicitconsulted flags and complete typed directive ifactuallyformed. Unconsulted provided evidence isnotclaimedevaluated. SafeRecoveryDirective retains requestedaction, canonicaltriggeror exactexternal/observedmodeunion, originalassessment/causingdecision/evidencerefs, requestorigin, exactreviewedpolicynode andNOT_ENTERED_BY_N2; proseomittedwithreason. Pendingmandate aftercapturefailure persistsasconfirmed supportingnode ifthatcommitcompleted, withactualeventunconfirmed andpartialcoverage, neverfalsemodeentry.",
    "StorageReceipt.sequence isnullable onlymatching health/fallbackrequestNone. Event/support/meta requests requireexactnonnullmatchingreceiptsequence; null orwrongreceipt isunconfirmed, neverACK. This isalreadyownedrequestcoherence, not hostinference."
  ],
  "budget": {
    "max_new_events": 768,
    "max_linked_post_assessments": 33,
    "max_action_decisions": 35,
    "audited_worst_case": 696,
    "reserved_health_refusal_margin": 72,
    "event_formula": "sum([32 * sum([8, 8, 1, 1, 2, 1]), 16, 1, 1, 2, 1, 1, 1, 1])=696",
    "new_event_byte_reservation": 25165824,
    "bytes": {
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
    "terminal_denial": {
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
  },
  "methods": {
    "__init__": "ReferenceDevelopmentDiagnostics(identity:DiagnosticsIdentity,profile:DiagnosticsProfile,store:ProtectedStore,clock:DiagnosticsClockPort); ReferenceReleaseDiagnostics(same exact signature). Limits are fixed DiagnosticLimits and alias/sequence ledgers private; explicit dependencies only; configuration errors raise DiagnosticsContractError(code,failed_field) before capture.",
    "clock.read": "DiagnosticsClockPort.read() -> ClockObservation; trusted injected host reference uses actual UTC and time.monotonic_ns; unavailable observations are explicit typed nulls/reasons, no fake0.",
    "assessment_capture": "assessment_capture(*,relation:PostAssessmentLink|None=None) -> old begin/append-compatible assessment capture adapter. PostAssessmentLink fields parent_operation_reference,parent_action_reference,originating_chain_root_reference are exact untrusted owned references; safe projection uses aliases.",
    "normalization_capture": "normalization_capture() -> old begin/append-compatible N1 capture adapter",
    "recovery_capture": "recovery_capture() -> RecoveryCapture",
    "recovery.begin": "RecoveryCapture.begin(origin:StateAssessment,*,operation_reference:UntrustedOperationReference) -> tuple[RecoveryScope|None,RecoveryAdmissionReceipt]. Fixed whole operation768 event and31588352 byte reservation; scope nonnull iff CONFIRMED. Failed attachment/admission means no provider/evaluator/state effects. No caller budget.",
    "recovery.append": "RecoveryScope.append(record:RecoveryRecord) -> existing CaptureReceipt. RecoveryRecord exact diagnostic_reference,envelope,record_kind,payload; payload is exact RecoveryStepEvidence|RecoveryActionDecision from N2 inventory. Owned projector admits no caller SafeContext/free dictionary.",
    "recovery.finish": "RecoveryScope.finish(result:RecoveryNoAction|RecoveredValue|RecoveredFallbackValue|RecoveryHandoff|RecoveryFailure) -> DiagnosticsCompletionReceipt",
    "complete_assessment": "complete_assessment(result:StateDiagnosis|StateAssessment|ClassificationEvidenceFailure|DiagnosticCaptureFailure) -> DiagnosticsCompletionReceipt",
    "complete_normalization": "complete_normalization(result:NormalizationResult|NormalizationFailure|NormalizationCaptureFailure) -> DiagnosticsCompletionReceipt",
    "snapshot": "snapshot(*,bundle_reference:UntrustedReference) -> DiagnosticSnapshot. Reads injected clock at the serialized snapshot boundary; caller cannot choose generated time/window. Unavailable UTC may yield null+reason; monotonic failure stops admission/capture, snapshot still exports retained evidence.",
    "export_pair": "export_pair(snapshot:DiagnosticSnapshot) -> ExportReceipt|ExportFailure using constructor-owned verified ProtectedStore; snapshot must be this collector immutable closed safe artifact, one slot, independent projection guard.",
    "health": "health() -> DiagnosticsHealth",
    "purge_completed": "purge_completed(*,through_sequence:uint64) -> RetentionReceipt",
    "error": "DiagnosticsContractError(code:enum:DiagnosticsFailure,failed_field:enum:SafeField|None); retained typed admission/commit/completion/export failure where one exists; no arbitrary raw exception rendering.",
    "recovery.begin_denial": "RecoveryCapture.begin_denial(origin:StateAssessment,*,operation_reference:UntrustedOperationReference) -> tuple[DenialScope|None,RecoveryAdmissionReceipt]. Samecollector exacttwo-origin attachment; reserves1event/270336bytes/64novelaliases beforeeffects. SAFE_HALT+TERMINAL_NO_RECOVERY only; no mainchainappend/provider/registry/child effects.",
    "denial.append": "DenialScope.append(record:RecoveryRecord) -> existing CaptureReceipt. Exactlyone OPERATION_DECISION: fresh operation denied root STATE_VALIDITY/DETECTION CRITICAL/BLOCKED parentnull/rootself, rules ASH-STATE-GENERAL-001+ASH-RECOVERY-ACTION-001, actual RecoveryActionDecision HANDOFF/NOT_APPLICABLE/REMAIN_SAFE_HALT. Same main-origin class/category retained, not actual mode entry.",
    "denial.finish": "DenialScope.finish(result:RecoveryHandoff|RecoveryFailure) -> DiagnosticsCompletionReceipt. Actual zeroeffects/zerochildren/zerosteps/zero registry use, matching confirmeddenialrecord; failedcapture retains attemptedrecord/prefix/status and coveragePARTIAL."
  },
  "completion_expectations": {
    "StateDiagnosis": [
      "DETECTION"
    ],
    "StateAssessment": [
      "DETECTION",
      "CLASSIFICATION"
    ],
    "ClassificationEvidenceFailure": [
      "confirmedDETECTION exactly",
      "retained typedfailedpredicate/evidence separately; no fabricatedclassification event",
      "coveragePARTIAL for incompletecontextualassessment"
    ],
    "DiagnosticCaptureFailure": [
      "actual confirmed prefix0/1 plus exact attempted record/status separately; coveragePARTIAL"
    ],
    "NormalizationResult": [
      "COMPUTATION/PENDING",
      "POST_VALIDATION/RESOLVED"
    ],
    "NormalizationFailure.semantic": [
      "COMPUTATION/BLOCKED"
    ],
    "NormalizationFailure.plan_validation.early": [
      "no inherited or new event; boundary refusal audit separate"
    ],
    "NormalizationFailure.plan_validation.verified": [
      "COMPUTATION/BLOCKED"
    ],
    "NormalizationFailure.post_validation": [
      "COMPUTATION/PENDING",
      "POST_VALIDATION/BLOCKED"
    ],
    "NormalizationCaptureFailure": [
      "actual confirmed prefix0/1 plus exact attempted record/status separately; coveragePARTIAL"
    ],
    "RecoveryValuePacket": [
      "derive exact consulted predicates/provider/XOR/post-child/selection/handoff/summary from owned typed packet and recorded action evidence; no caller expected count; actual child completion mandatory before recovered branch"
    ],
    "terminal_denial": [
      "exactone separate OPERATION_DECISION denied root, never append RECOVERY to original terminal chain",
      "actual RecoveryHandoff noeffects/nochildren/no state steps/no registry",
      "confirmedreceipt and result-derived completion or explicit failedprefix/attemptedrecord"
    ]
  },
  "message_templates": {
    "SESSION_OPENED": "Reference diagnostic session opened; capture is limited to the declared producers.",
    "SESSION_CLOSED": "Reference diagnostic session closed; retained evidence and coverage limitations remain explicit.",
    "ORIGIN_ATTACHED": "The exact previously confirmed origin was attached by this collector; no origin record was emitted again.",
    "DIAGNOSIS_RECORDED": "State validity was diagnosed under the explicit complete source and profile bindings.",
    "CLASSIFICATION_RECORDED": "Contextual classification evaluated only the recorded context and consulted predicates.",
    "NORMALIZATION_COMPUTED": "Actual full-vector normalization completed; post-validation acknowledgment is pending.",
    "POST_VALIDATION_RECORDED": "Actual post-operation state was diagnosed and classified in its separately linked assessment chain.",
    "RECOVERY_ACTION_RECORDED": "The consulted predicate or value step completed with the structured outcome shown in this record.",
    "RECOVERY_REFUSED": "Recovery was refused before unapproved effects; the original submitted evidence remains retained.",
    "RECOVERY_HANDOFF_RECORDED": "Only a typed containment or halt request was produced; no runtime mode entry is claimed.",
    "DIAGNOSTIC_NONCONFORMANCE": "A required diagnostic invariant failed; the related operation or record was not silently accepted.",
    "CAPTURE_UNCONFIRMED": "Capture did not acknowledge this attempted record; its external persistence remains unconfirmed.",
    "RETENTION_REPORTED": "A whole declared retention range became unavailable; counts and boundary evidence are retained.",
    "EXPORT_COMPLETE": "The JSON and Markdown parts and manifest completed for one verified sanitized snapshot.",
    "EXPORT_INCOMPLETE": "The paired diagnostic export did not complete; retained part status and failure evidence are explicit.",
    "UNTRUSTED_PROSE_OMITTED": "Untrusted producer prose, previews, paths and exception material were omitted before persistence."
  },
  "store_ports": {
    "commit_event": "commit_event(sequence:exactuint64,redacted_bytes:exactbytes1..32768) -> StorageReceipt; native configuredhostowner verifies private root before/afterIO; no pathname/key from businessmodule",
    "write_pair": "write_pair(bundle_alias:Alias,json_bytes:exactbytes<=33554432,markdown_bytes:exactbytes<=50331648,manifest_bytes:exactbytes<=65536,*,last_included_sequence:uint64|None)->StorePairReceipt|StorePairFailure. Three fixed part names; maxonebundle includingincomplete, no overwrite. Host returns actual IO evidence only; Diagnostics wraps its own snapshot into ExportReceipt/ExportFailure.",
    "verify": "verify() -> StorageVerification from actual hostsecuritychecks; report is evidenceonly and never replacesconfiguredhostowner authority",
    "purge_bundle": "purge_bundle(bundle_alias:Alias)->StorePurgeReceipt; actualclosed IO facts only, explicitwholebundlepurge, nativeconfinedexactprivateownedroot; no Corehealth/domainreceipt constructedbyhost. Diagnostics.purge_completed wraps own currenthealth separately.",
    "commit_supporting": "commit_supporting(sequence:uint64,kind:enum:SupportingKind,evidence_alias:Alias,redacted_bytes:exactbytes1..32768)->StorageReceipt. Exactlyclosed typed safe node bytes, dependencyorder andkind+alias identity; no arbitrarybackend dictionary. Receipt sequence equalsrequest; supportcommit must actuallycomplete before referencing event CONFIRMED.",
    "commit_meta": "commit_meta(sequence:uint64,redacted_bytes:exactbytes1..3072)->StorageReceipt using independentlyreserved pool; exact MetaDiagnosticRecord only. Failure neverrecursiveappend; actual fallbackhealth retained.",
    "commit_health": "commit_health(sequence:uint64|None,redacted_bytes:exactbytes1..8192)->StorageReceipt; exact current DiagnosticsHealth, one bounded lateststatusslot; priorstatus explicitlysuperseded, notclaimedfullhistory.",
    "commit_fallback_health": "commit_fallback_health(sequence:uint64|None,redacted_bytes:exactbytes1..8192)->StorageReceipt; exact FallbackHealthRecord, independent nonrecursive latestslot. Failure remainsinmemory/unconfirmed; neverrawfallbacklogs."
  },
  "primitives_constraints": {
    "UntrustedReference": "API-only exactASCIIidentifier1..256 fromexistingownedvalues. Privatealias keys canretainsuchreferences butneverproducerfreeprose/rawinput/errorstacks; raw keys neverpersist/export. Protectedstoreparent path remainshostfactoryinput, not Core/log data.",
    "PrivateAcknowledgmentLedger": "One private SHA256 digest of exact owned DiagnosticEmission.to_record encoded by json.dumps(sort_keys=True,separators=(comma,colon),ensure_ascii=True,allow_nan=False).encode(ascii), original reference, collector/session identity and actual confirmed sequence; compare both whole origin records by that fixed algorithm. No raw producer prose retained. Digests/raw reference keys are bounded private memory and never exported. Explicit SHA256 collision-resistance assumption; no remote authentication. Semantic validation remains StateModel-owned.",
    "StorageVerification": "typedcheckreport producedbyactual configuredhostfactory; plaincaller-created boolrecord isnota usable protectedstorecapability. No genericJSON->verifiedstoreimporter.",
    "ObservationBoundary": "Exact trusted injected ClockObservation; availability/reason iff coherence; UTC microsecond RFC3339; monotonicuint64 and checked difference. No platform clock reads in neutral Core.",
    "CounterIntegrity": "Exact bounded integer arithmetic as declared8row table; no bool/subclass/integer coercion or estimates; saturating lowerbound explicitly marked; incomplete/unknown measurements remainnullablewithreason."
  },
  "alias_budget": {
    "capacity": 6144,
    "new_operation_reservation": 5403,
    "condition_bindings": 2048,
    "provider_source_bindings": 1536,
    "diagnostic_references": 768,
    "action_references": 35,
    "post_facts": 396,
    "source_certifications": 416,
    "origin_registry_proof": 64,
    "profiles": 64,
    "first_malformed_result_margin": 12,
    "calculation": "sum([2048, 1536, 768, 35, 396, 416, 64, 64, 64, 12])=5403",
    "proof_scope": "Conservative distinct reference-token occurrence count under exact N2 payload/context inventories. Reused bound references counted once; actual implementations must enforce capacity beforeeffects and reject unregistered payload.",
    "control_identity": 64
  }
}
```
