"""Closed N3 safe projections; no business prose or native observation hooks.

The field inventory is compiled from the adopted N3 contract. Each concrete
frozen type has required fields and validates exact owned nested values.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
import re
from . import diagnostics_values as dv
from . import state_values as sv

FIELD_SPECS = {'SafeSessionBindingEvidence': {'evidence_reference': 'Alias',
                                'session_reference': 'Alias',
                                'assembly_generation': 'LEGACY_PAIR|N3_LIFECYCLE_PAIR',
                                'canonical_source_evidence_reference': 'Alias',
                                'paired_source_evidence_reference': 'Alias:SafeSessionSourceEvidence',
                                'profile_evidence_reference': 'Alias',
                                'policy_reference': 'Alias',
                                'policy_assurance': 'RECOGNIZED_ADOPTED_POLICY',
                                'binding_reference': 'Alias',
                                'initial_assessment_reference': 'Alias',
                                'policy_id': 'const:YWE-SESSION-SAFETY-001',
                                'policy_version': 'const:1.0.0',
                                'policy_source_path': 'const:docs/architecture/m3_session_lifecycle_policy.md',
                                'policy_source_sha256': 'const:24e2584279b95b8e3659bd61e6b5149311f344b03b981e88f74ae37775591910'},
 'SafeSessionSnapshotEvidence': {'evidence_reference': 'Alias',
                                 'session_binding_reference': 'Alias',
                                 'generation': 'uint64',
                                 'current_state': 'Signature',
                                 'mode': 'NORMAL|CONTAINED|SAFE_HALT',
                                 'terminal_latched': 'bool',
                                 'admission_status': 'OPEN|AUDIT_BLOCKED|TERMINAL',
                                 'containment_reference': 'Alias|null',
                                 'halt_reference': 'Alias|null',
                                 'recovery_attempted': 'bool',
                                 'active_operation_reference': 'Alias|null',
                                 'snapshot_reference': 'Alias',
                                 'current_assessment_reference': 'Alias|null',
                                 'observed_system_state_class': 'SystemClass|null'},
 'SafeSessionContextEvidence': {'evidence_reference': 'Alias',
                                'snapshot_evidence_reference': 'Alias',
                                'operation_reference': 'Alias',
                                'subject_state': 'Signature',
                                'is_running': 'bool',
                                'is_contained': 'bool',
                                'is_halted': 'bool',
                                'assurance': 'CURRENT_IN_PROCESS_SESSION_OBSERVATION',
                                'observation_reference': 'Alias'},
 'SafeSessionPublicationEvidence': {'evidence_reference': 'Alias',
                                    'request_reference': 'Alias',
                                    'requested_action': 'RECOVER|REQUEST_CONTAINMENT|RESOLVE_CONTAINMENT|REQUEST_HALT',
                                    'lease_reference': 'Alias',
                                    'before_snapshot_reference': 'Alias',
                                    'after_snapshot_reference': 'Alias|null',
                                    'status': 'COMMITTED|NOT_COMMITTED|UNCONFIRMED',
                                    'session_effects_performed': 'bool|null',
                                    'requested_state': 'Signature',
                                    'requested_mode': 'NORMAL|CONTAINED|SAFE_HALT',
                                    'cause_reference': 'Alias',
                                    'proof_reference': 'Alias|null',
                                    'failure_code': 'SessionFailureCode|null',
                                    'omitted_fields': 'fixed:PUBLICATION_REASON',
                                    'request_evidence_reference': 'Alias',
                                    'authority_evidence_reference': 'Alias|null',
                                    'cause_evidence_reference': 'Alias|null',
                                    'publication_reference': 'Alias'},
 'SafeLifecycleEvidence': {'evidence_reference': 'Alias',
                           'record_reference': 'Alias|null',
                           'kind': 'RECOVERY|CONTAINMENT|SAFE_HALT',
                           'envelope': 'SafeDiagnosticEnvelope|null',
                           'original_assessment_evidence_reference': 'Alias|null',
                           'recovery_diagnostic_evidence_reference': 'Alias|null',
                           'trigger': 'ContainmentTrigger|SafeHaltTrigger|null',
                           'system_state_class': 'CONTAINED|SAFE_HALT|null',
                           'restricted_operations': 'tuple<RestrictedOperation,0..5>',
                           'utc': 'UtcTimestamp|null',
                           'monotonic_nanoseconds': 'uint64|null',
                           'utc_unavailable_reason': 'UnavailableReason|null',
                           'monotonic_unavailable_reason': 'UnavailableReason|null',
                           'awaiting_resolution': 'bool|null',
                           'resolution': 'PENDING|null',
                           'is_terminal': 'bool|null',
                           'prior_history_evidence_reference': 'Alias|null',
                           'rule_ids': 'tuple<CanonicalRule17,1..10>',
                           'capture_status': 'CONFIRMED|NOT_CONFIRMED|REJECTED',
                           'omitted_fields': 'fixed:CANONICAL_FREE_NOTES',
                           'conformance': 'CANONICAL_OBSERVATION|PENDING_NONCONFORMANT',
                           'missing_fields': 'tuple<LifecycleCanonicalField,0..15>',
                           'pending_reason_code': 'PendingLifecycleReason|null',
                           'cause_evidence_reference': 'Alias|null',
                           'clock_assurance': 'fixed:COLLECTOR_OWNED_MEASURED_CLOCK_OBSERVATION'},
 'SafeSessionChildLink': {'link_reference': 'Alias',
                          'session_binding_reference': 'Alias',
                          'admitted_generation': 'uint64',
                          'live_origin_assessment_reference': 'Alias',
                          'child_origin_assessment_reference': 'Alias',
                          'child_operation_reference': 'Alias'},
 'SafeSessionHistoryEvidence': {'evidence_reference': 'Alias',
                                'session_binding_reference': 'Alias',
                                'main_assessment_evidence_reference': 'Alias|null',
                                'child_link': 'SafeSessionChildLink|null',
                                'recovery_operation_reference': 'Alias|null',
                                'context_evidence_references': 'tuple<Alias,0..53>',
                                'publication_evidence_references': 'tuple<Alias,0..18>',
                                'lifecycle_evidence_references': 'tuple<Alias,0..90>',
                                'pending_lifecycle_evidence_reference': 'Alias|null',
                                'page_evidence_references': 'tuple<Alias,0..40>',
                                'confirmed_record_count': 'uint16[0..1024]',
                                'unknown_storage_record_count': 'uint16[0..1024]',
                                'attempted_lifecycle_record_count': 'uint8[0..36]',
                                'supporting_reference_count': 'uint16[0..2504]',
                                'frozen': 'bool',
                                'coverage': 'COMPLETE_SPECIFIED_SAFE_GRAPH|PARTIAL|STORAGE_UNCERTAIN',
                                'omitted_fields': 'fixed:RAW_BUSINESS_PACKETS_REQUEST_REASON_CANONICAL_FREE_NOTES',
                                'request_evidence_references': 'tuple<Alias,0..18>',
                                'authority_evidence_references': 'tuple<Alias,0..18>',
                                'cause_evidence_references': 'tuple<Alias,0..18>',
                                'boundary_evidence_references': 'tuple<Alias,0..36>',
                                'command_evidence_references': 'tuple<Alias,0..18>',
                                'failure_evidence_references': 'tuple<Alias,0..18>',
                                'resolution_evidence_references': 'tuple<Alias,0..16>',
                                'recovery_operation_references': 'tuple<Alias,0..2>',
                                'child_link_references': 'tuple<Alias,0..2>',
                                'current_assessment_evidence_reference': 'Alias|null',
                                'episode_assessment_evidence_references': 'tuple<Alias,0..17>',
                                'terminal_closure_evidence_reference': 'Alias|null'},
 'SafeHistoryRecordReference': {'diagnostic_reference': 'Alias',
                                'event_id': 'Alias|null',
                                'local_sequence': 'uint64|null',
                                'storage_status': 'CONFIRMED|UNKNOWN'},
 'SafeSupportingReference': {'kind': 'SupportingKindWithoutHistoryPage', 'evidence_reference': 'Alias'},
 'SafeSessionHistoryPage': {'evidence_reference': 'Alias',
                            'history_evidence_reference': 'Alias',
                            'page_index': 'uint8[0..39]',
                            'record_references': 'tuple<SafeHistoryRecordReference,0..64>',
                            'supporting_references': 'tuple<SafeSupportingReference,0..64>'},
 'SafeSessionSourceEvidence': {'evidence_reference': 'Alias',
                               'assembly_generation': 'LEGACY_PAIR|N3_LIFECYCLE_PAIR',
                               'canonical_binding': 'VerifiedCanonicalVector9',
                               'paired_recovery_sources': 'tuple<VerifiedSourcePathDigest,7>',
                               'source_vector_sha256': 'VerifiedSourceVectorHash',
                               'assembly_assurance': 'RECOGNIZED_COMPLETE_VECTOR'},
 'SafeSessionDeniedEvidence': {'evidence_reference': 'Alias',
                               'session_binding_reference': 'Alias',
                               'snapshot_evidence_reference': 'Alias',
                               'audit_reference': 'Alias|null',
                               'request_reference': 'Alias|null',
                               'request_observation': 'NOT_INSPECTED_AT_TERMINAL|VALIDATED_REFERENCE_ONLY',
                               'reason_code': 'SESSION_TERMINAL|SESSION_MODE_FORBIDDEN|SESSION_BUDGET_EXCEEDED',
                               'record_reference': 'Alias|null',
                               'capture_status': 'CONFIRMED|REJECTED|NOT_CONFIRMED',
                               'omitted_fields': 'fixed:REQUEST_REASON',
                               'denial_ordinal': 'uint8[1..16]|null',
                               'completion_observation': 'SafeSessionCompletionObservation|null'},
 'SafeSessionChildLinkEvidence': {'evidence_reference': 'Alias', 'link': 'SafeSessionChildLink'},
 'SafeSessionRequestEvidence': {'evidence_reference': 'Alias',
                                'command_reference': 'Alias',
                                'session_reference': 'Alias',
                                'expected_generation': 'uint64',
                                'action': 'RECOVER|REQUEST_CONTAINMENT|RESOLVE_CONTAINMENT|REQUEST_HALT',
                                'omitted_fields': 'fixed:REQUEST_REASON',
                                'expected_snapshot_evidence_reference': 'Alias',
                                'submitted_trigger': 'ContainmentTrigger|SafeHaltTrigger|null',
                                'authority_evidence_reference': 'Alias|null',
                                'boundary_evidence_references': 'tuple<Alias,0..2>',
                                'submitted_recovery_operation_reference': 'Alias|null',
                                'submitted_recovery_context_evidence_reference': 'Alias|null'},
 'SafeSessionAuthorityEvidence': {'evidence_reference': 'Alias',
                                  'request_evidence_reference': 'Alias',
                                  'status': 'AUTHORIZED|DENIED|UNAVAILABLE',
                                  'request_origin': 'OPERATOR|POLICY|SYSTEM_BOUNDARY',
                                  'source_reference': 'Alias',
                                  'source_digest_reference': 'Alias',
                                  'source_evidence_reference': 'Alias',
                                  'observation_evidence_reference': 'Alias',
                                  'assurance': 'DECLARED_REFERENCE_AUTHORIZATION',
                                  'omitted_fields': 'fixed:AUTHORITY_REASON',
                                  'observed_expected_snapshot_reference': 'Alias',
                                  'observed_request_reference': 'Alias'},
 'SafeSessionBoundaryEvidence': {'evidence_reference': 'Alias',
                                 'request_evidence_reference': 'Alias',
                                 'condition': 'SessionBoundaryCondition',
                                 'status': 'SATISFIED|NOT_SATISFIED|UNAVAILABLE',
                                 'source_reference': 'Alias',
                                 'source_digest_reference': 'Alias',
                                 'source_evidence_reference': 'Alias',
                                 'observation_evidence_reference': 'Alias',
                                 'assurance': 'DECLARED_REFERENCE_BOUNDARY_OBSERVATION',
                                 'omitted_fields': 'fixed:BOUNDARY_REASON',
                                 'observed_expected_snapshot_reference': 'Alias',
                                 'observed_request_reference': 'Alias'},
 'SafeSessionCauseEvidence': {'evidence_reference': 'Alias',
                              'cause_reference': 'Alias',
                              'request_evidence_reference': 'Alias',
                              'kind': 'SessionCauseKind',
                              'trigger': 'ContainmentTrigger|SafeHaltTrigger|null',
                              'recovery_operation_reference': 'Alias|null',
                              'recovery_outcome': 'NO_ACTION|RECOVERED_VALUE|RECOVERED_FALLBACK_VALUE|HANDOFF_REQUIRED|FAILURE|null',
                              'recovery_diagnostic_evidence_references': 'tuple<Alias,0..35>',
                              'recovery_safety_evidence_reference': 'Alias|null',
                              'authority_evidence_reference': 'Alias|null',
                              'boundary_evidence_references': 'tuple<Alias,0..2>',
                              'projection_coverage': 'COMPLETE_SPECIFIED_SAFE_GRAPH|PARTIAL|STORAGE_UNCERTAIN',
                              'observed_expected_snapshot_reference': 'Alias',
                              'observed_request_reference': 'Alias'},
 'SafeSessionCompletionObservation': {'status': 'COMPLETE|INCOMPLETE',
                                      'operation_reference': 'Alias',
                                      'confirmed_references': 'tuple<Alias,0..4>',
                                      'failure_code': 'LifecycleCaptureCode|null',
                                      'assurance': 'OBSERVED_CAPTURE_RESPONSE_NOT_STORAGE_PROOF'},
 'SafeSessionOriginCompletionObservation': {'operation_reference': 'Alias',
                                            'status': 'CompletionStatus',
                                            'operation_outcome': 'ObservedOutcome',
                                            'confirmed_event_indices': 'tuple<uint32[0..1023],0..2>',
                                            'diagnostic_coverage': 'OverallCoverage',
                                            'failure_code': 'DiagnosticsFailure|null',
                                            'attempted_event_index': 'uint32[0..1023]|null',
                                            'assurance': 'OBSERVED_CAPTURE_RESPONSE_NOT_STORAGE_PROOF',
                                            'omitted_fields': 'fixed:RETURNED_RECEIPT_HEALTH_BUSINESS_ONLY'},
 'SafeSessionFailureEvidence': {'evidence_reference': 'Alias',
                                'request_evidence_reference': 'Alias',
                                'failure_code': 'SessionFailureCode',
                                'field_name': 'SessionFieldPath',
                                'primary_evidence_reference': 'Alias|null',
                                'capture_status': 'CONFIRMED|REJECTED|NOT_CONFIRMED|null',
                                'attempted_lifecycle_evidence_reference': 'Alias|null',
                                'completion_observation': 'SafeSessionCompletionObservation|null',
                                'completion_failure_code': 'LifecycleCaptureCode|null',
                                'unconfirmed_completion_observation': 'SafeSessionCompletionObservation|null',
                                'omitted_fields': 'fixed:FAILURE_REASON',
                                'unavailable_post_assessment_facts': 'SafeUnavailablePostAssessmentFacts|null'},
 'SafeSessionCommandEvidence': {'evidence_reference': 'Alias',
                                'request_evidence_reference': 'Alias',
                                'before_snapshot_reference': 'Alias',
                                'after_snapshot_reference': 'Alias|null',
                                'session_effects_performed': 'bool|null',
                                'admission_status': 'GRANTED|REJECTED',
                                'admission_before_snapshot_reference': 'Alias',
                                'admission_failure_code': 'SessionFailureCode|null',
                                'lease_reference': 'Alias|null',
                                'lease_expected_snapshot_reference': 'Alias|null',
                                'lease_action': 'RECOVER|CONTAIN|RESOLVE|HALT|null',
                                'authority_evidence_reference': 'Alias|null',
                                'cause_evidence_reference': 'Alias|null',
                                'origin_assessment_evidence_reference': 'Alias|null',
                                'origin_completion_observation': 'SafeSessionOriginCompletionObservation|null',
                                'recovery_operation_reference': 'Alias|null',
                                'publication_evidence_reference': 'Alias|null',
                                'lifecycle_evidence_references': 'tuple<Alias,0..2>',
                                'pending_lifecycle_evidence_reference': 'Alias|null',
                                'capture_completion_observation': 'SafeSessionCompletionObservation|null',
                                'failure_evidence_reference': 'Alias|null',
                                'projection_coverage': 'COMPLETE_SPECIFIED_SAFE_GRAPH|PARTIAL|STORAGE_UNCERTAIN',
                                'omitted_fields': 'fixed:ADMISSION_REASON_RAW_BUSINESS_PACKETS',
                                'resolution_evidence_reference': 'Alias|null',
                                'submitted_recovery_operation_reference': 'Alias|null',
                                'lease_active_snapshot_reference': 'Alias|null',
                                'admission_failure_field': 'SessionFieldPath|null',
                                'actual_post_assessment_evidence_reference': 'Alias|null',
                                'actual_post_completion_observation': 'SafeSessionOriginCompletionObservation|null',
                                'operation_status': 'SessionOperationStatus',
                                'raw_business_failure_phase': 'CANDIDATE_RESULT|PROSPECTIVE_HISTORY|ANTICIPATED_TERMINAL|TERMINAL_CHAIN|null',
                                'raw_business_failure_coverage': 'API_ONLY|PARTIAL|null'},
 'SafeResolutionTargetEvidence': {'evidence_reference': 'Alias',
                                  'session_binding_reference': 'Alias',
                                  'request_evidence_reference': 'Alias',
                                  'before_snapshot_reference': 'Alias',
                                  'containment_record_reference': 'Alias',
                                  'target_state': 'Signature',
                                  'canonical_source_evidence_reference': 'Alias',
                                  'profile_evidence_reference': 'Alias',
                                  'target_validity': 'SafeStateValidity',
                                  'prospective_is_in_safe_halt': 'const_bool:false',
                                  'prospective_is_in_containment': 'const_bool:false',
                                  'prospective_system_class': 'STABLE|null',
                                  'prospective_recovery_category': 'NO_ACTION|null',
                                  'assurance': 'fixed:PURE_TARGET_VALIDATION_PROSPECTIVE_CONTEXT_NOT_ENTERED',
                                  'validation_status': 'VERIFIED|REJECTED',
                                  'validation_failure_code': 'SESSION_TARGET_NOT_VALID|null',
                                  'validation_field_name': 'const:resolution.target_validation|null'},
 'SafeSessionResolutionEvidence': {'evidence_reference': 'Alias',
                                   'request_evidence_reference': 'Alias',
                                   'session_binding_reference': 'Alias',
                                   'containment_record_reference': 'Alias',
                                   'route': 'OPERATOR_INTERVENTION|POLICY_DRIVEN|ESCALATE_TO_SAFE_HALT',
                                   'target_evidence_reference': 'Alias|null',
                                   'authority_evidence_reference': 'Alias',
                                   'boundary_clear_evidence_reference': 'Alias|null',
                                   'propagation_evidence_reference': 'Alias|null',
                                   'before_snapshot_reference': 'Alias',
                                   'after_snapshot_reference': 'Alias|null',
                                   'publication_evidence_reference': 'Alias|null',
                                   'actual_post_assessment_reference': 'Alias|null',
                                   'status': 'RESOLVED|REFUSED|UNCONFIRMED',
                                   'session_effects_performed': 'bool|null',
                                   'observed_boundary_status': 'SATISFIED|NOT_SATISFIED|UNAVAILABLE',
                                   'observed_propagation_status': 'SAFE|RISK|UNAVAILABLE',
                                   'actual_resolution_record_reference': 'Alias|null',
                                   'omitted_fields': 'fixed:UNTRUSTED_RESOLUTION_REASON',
                                   'propagation_operation_reference': 'Alias|null',
                                   'propagation_origin_assessment_reference': 'Alias|null',
                                   'propagation_source_binding': 'SafeEvidenceSourceBinding|null',
                                   'previous_episode_root_reference': 'Alias',
                                   'actual_new_episode_root_reference': 'Alias|null',
                                   'resolution_action': 'REPLACE_STATE|HALT',
                                   'requested_target_state': 'Signature|null',
                                   'submitted_recovery_operation_reference': 'Alias|null'},
 'SafeSessionSubmittedRecoveryContextEvidence': {'evidence_reference': 'Alias',
                                                 'operation_reference': 'Alias',
                                                 'origin_assessment_reference': 'Alias',
                                                 'context_owner_reference': 'Alias',
                                                 'context_observation_reference': 'Alias',
                                                 'context_source_binding': 'SafeEvidenceSourceBinding',
                                                 'observed_is_in_safe_halt': 'bool',
                                                 'observed_is_in_containment': 'bool',
                                                 'propagation_operation_reference': 'Alias',
                                                 'propagation_origin_assessment_reference': 'Alias',
                                                 'propagation_status': 'PropagationStatus',
                                                 'propagation_source_binding': 'SafeEvidenceSourceBinding',
                                                 'authority_operation_reference': 'Alias',
                                                 'authority_origin_assessment_reference': 'Alias',
                                                 'authority_status': 'AuthorityStatus',
                                                 'authority_source_binding': 'SafeEvidenceSourceBinding',
                                                 'omitted_fields': 'fixed:PROPAGATION_AND_EXTERNAL_AUTHORITY_REASON',
                                                 'assurance': 'fixed:SUBMITTED_BOUND_EVIDENCE_NOT_CURRENT_OWNER_CONTEXT'},
 'SafeSessionTerminalClosureEvidence': {'evidence_reference': 'Alias',
                                        'request_evidence_reference': 'Alias',
                                        'bridge_record_reference': 'Alias|null',
                                        'terminal_diagnostic_reference': 'Alias',
                                        'terminal_envelope': 'SafeDiagnosticEnvelope',
                                        'actual_terminal_publication_evidence_reference': 'Alias',
                                        'assurance': 'fixed:ACTUAL_FINAL_HALT_LINK_NONRECURSIVE_COMPLETE_TYPED_CLOSURE'},
 'SafeUnavailablePostAssessmentFacts': {'operation_reference': 'Alias',
                                        'candidate_state': 'Signature',
                                        'source_binding': 'SafeEvidenceSourceBinding',
                                        'omitted_fields': 'fixed:UNAVAILABLE_POST_FACTS_REASON'}}

DOMAINS = {'Reference': 'exactASCII identifier [A-Za-z0-9][A-Za-z0-9._:/-]{0,255}; NONE/SELF forbidden',
 'CommandReference': 'Reference max160 to leave derived suffix room; no implicit generated randomness',
 'Reason': 'exactstr 1..512 without NUL; stored raw only in bounded caller-owned business values',
 'Sha256': 'exactstr lowercase hex64',
 'Uint64': 'exactint 0..18446744073709551615; bool forbidden',
 'SessionMode': ['NORMAL', 'CONTAINED', 'SAFE_HALT'],
 'SessionAdmissionStatus': ['OPEN', 'AUDIT_BLOCKED', 'TERMINAL'],
 'SessionAction': ['RECOVER', 'REQUEST_CONTAINMENT', 'RESOLVE_CONTAINMENT', 'REQUEST_HALT'],
 'LeaseAction': ['RECOVER', 'CONTAIN', 'RESOLVE', 'HALT'],
 'SessionAuthorityStatus': ['AUTHORIZED', 'DENIED', 'UNAVAILABLE'],
 'SessionAuthorityOrigin': ['OPERATOR', 'POLICY', 'SYSTEM_BOUNDARY'],
 'SessionBoundaryCondition': ['CONTAINMENT_BREACH',
                              'CONTAINMENT_UNAVAILABLE',
                              'CONTAINMENT_CLEAR',
                              'RECOVERY_NO_PATH',
                              'RECOVERY_VALIDATION_FAILURE',
                              'PROPAGATION_RISK'],
 'SessionBoundaryStatus': ['SATISFIED', 'NOT_SATISFIED', 'UNAVAILABLE'],
 'SessionCauseKind': ['N2_HANDOFF',
                      'PROPAGATION_RISK_BOUNDARY',
                      'AUTHORITY_REQUEST',
                      'CONTAINMENT_BREACH',
                      'UNRESOLVABLE_BLOCKED_BOUNDARY',
                      'RECOVERY_VALIDATION_BOUNDARY',
                      'N2_RESULT'],
 'SessionAdmissionDecision': ['GRANTED', 'REJECTED'],
 'PublicationStatus': ['COMMITTED', 'NOT_COMMITTED', 'UNCONFIRMED'],
 'ResolutionRoute': ['OPERATOR_INTERVENTION', 'POLICY_DRIVEN', 'ESCALATE_TO_SAFE_HALT'],
 'ResolutionAction': ['REPLACE_STATE', 'HALT'],
 'ResolutionStatus': ['RESOLVED', 'REFUSED', 'UNCONFIRMED'],
 'SessionOperationStatus': ['COMPLETED', 'REFUSED', 'FAILED', 'TERMINAL_REFUSAL', 'UNCONFIRMED'],
 'LifecycleKind': ['RECOVERY', 'CONTAINMENT', 'SAFE_HALT'],
 'LifecycleCaptureStatus': ['CONFIRMED', 'REJECTED', 'NOT_CONFIRMED'],
 'LifecycleCaptureCode': ['CAPTURE_ADMISSION_REJECTED',
                          'CAPTURE_ADMISSION_UNCONFIRMED',
                          'CAPTURE_APPEND_REJECTED',
                          'CAPTURE_APPEND_UNCONFIRMED',
                          'CAPTURE_COMPLETION_REJECTED',
                          'CAPTURE_COMPLETION_UNCONFIRMED',
                          'CAPTURE_FINAL_OBSERVATION_FAILED',
                          'CAPTURE_RETENTION_FAILED',
                          'CAPTURE_CLOCK_UNAVAILABLE',
                          'CAPTURE_CHAIN_UNCONFIRMED'],
 'SessionFailureCode': ['SESSION_INPUT_INVALID',
                        'SESSION_SOURCE_REJECTED',
                        'SESSION_PROFILE_REJECTED',
                        'SESSION_ORIGIN_REJECTED',
                        'SESSION_ORIGIN_FOREIGN',
                        'SESSION_STATE_STALE',
                        'SESSION_OPERATION_DUPLICATE',
                        'SESSION_OPERATION_IN_PROGRESS',
                        'SESSION_MODE_FORBIDDEN',
                        'SESSION_TERMINAL',
                        'SESSION_BUDGET_EXCEEDED',
                        'SESSION_LEASE_REJECTED',
                        'SESSION_EXECUTION_CANCELLED',
                        'SESSION_AUTHORITY_DENIED',
                        'SESSION_AUTHORITY_UNAVAILABLE',
                        'SESSION_EVIDENCE_MISMATCH',
                        'SESSION_BOUNDARY_NOT_SATISFIED',
                        'SESSION_TARGET_NOT_VALID',
                        'SESSION_N2_RESULT_REJECTED',
                        'SESSION_N2_COMPLETION_REJECTED',
                        'SESSION_N2_COMPLETION_UNCONFIRMED',
                        'SESSION_PUBLICATION_STALE',
                        'SESSION_PUBLICATION_UNCONFIRMED',
                        'SESSION_COLLABORATOR_FAILED',
                        'SESSION_CAPTURE_FAILED',
                        'SESSION_RETENTION_FAILED',
                        'SESSION_GENERATION_EXHAUSTED',
                        'SESSION_AUDIT_BLOCKED',
                        'SESSION_RAW_BUSINESS_LIMIT',
                        'SESSION_INTERNAL_INVARIANT'],
 'SessionFieldPath': ['binding',
                      'binding.canonical_binding',
                      'binding.recovery_binding',
                      'binding.profile_binding',
                      'binding.policy_binding',
                      'request',
                      'request.reference',
                      'request.session_reference',
                      'request.expected_snapshot',
                      'request.action',
                      'origin_assessment',
                      'origin_assessment.source_binding',
                      'origin_assessment.profile_binding',
                      'operation_context',
                      'operation_context.context_observation',
                      'operation_context.propagation_evidence',
                      'operation_context.external_authority_evidence',
                      'authority',
                      'boundary',
                      'cause',
                      'trigger',
                      'lease',
                      'publication',
                      'publication.before',
                      'publication.after',
                      'resolution',
                      'resolution.route',
                      'resolution.target',
                      'resolution.target_validation',
                      'resolution.boundary_clear',
                      'capture',
                      'capture.admission',
                      'capture.append',
                      'capture.finish',
                      'capture.final_observation',
                      'retention',
                      'clock',
                      'history',
                      'generation',
                      'collaborator',
                      'execution_gate',
                      'raw_business_packet'],
 'StageGrantKind': ['REGISTRY_READ',
                    'CAPTURE_BEGIN',
                    'NORMALIZATION_PROVIDER',
                    'CORRECTION_PROVIDER',
                    'CONDITION_PROVIDER',
                    'POST_FACTS_PROVIDER',
                    'CANDIDATE_COMPUTATION',
                    'ASSESSMENT_BEGIN',
                    'ASSESSMENT_APPEND',
                    'ASSESSMENT_COMPLETE',
                    'CAPTURE_APPEND'],
 'RestrictedOperation': ['READ_SESSION',
                         'READ_DIAGNOSTICS',
                         'EXPORT_DIAGNOSTICS',
                         'REQUEST_HALT',
                         'RESOLVE_CONTAINMENT'],
 'LifecycleCanonicalField': ['trigger',
                             'original_diagnostic',
                             'system_state_class',
                             'restricted_operations',
                             'containment_time',
                             'awaiting_resolution',
                             'resolution',
                             'halt_time',
                             'full_diagnostic_chain',
                             'is_terminal',
                             'rule_ids',
                             'notes',
                             'envelope',
                             'parent_diagnostic_reference',
                             'chain_root_reference'],
 'PendingLifecycleReason': ['ORIGINAL_DIAGNOSIS_UNAVAILABLE',
                            'ORIGINAL_CLASSIFICATION_UNAVAILABLE',
                            'CHAIN_UNCONFIRMED',
                            'CLOCK_UNAVAILABLE',
                            'CAPTURE_UNCONFIRMED',
                            'RAW_BUSINESS_LIMIT'],
 'SessionRetentionStatus': ['CONFIRMED', 'REJECTED', 'NOT_CONFIRMED'],
 'SessionRetentionPhase': ['REGISTER', 'ATTACH', 'PIN', 'FREEZE', 'FINAL_RESULT'],
 'SessionRetentionCoverage': ['COMPLETE_SPECIFIED_SAFE_GRAPH', 'PARTIAL', 'STORAGE_UNCERTAIN'],
 'SessionRetentionFailure': ['SESSION_RETENTION_REJECTED',
                             'SESSION_RETENTION_UNCONFIRMED',
                             'SESSION_RETENTION_INCOMPLETE',
                             'SESSION_RETENTION_LIMIT',
                             'SESSION_RETENTION_IDENTITY_MISMATCH',
                             'SESSION_RETENTION_FROZEN']}

SOURCE_VECTOR_HASHES = {'LEGACY_C78': '2f7d39c0921e45f85956cd3e6c4f28e33204ae8487bc2334e25d8d589efef246', 'N3_LIFECYCLE': '998a5a8d80c112756ce0255ff8542dcb885abd4eee388cfc2b48da2113278730'}

SUPPORT_MAXIMA = {'SESSION_BINDING': 19, 'SESSION_SNAPSHOT': 214, 'SESSION_CONTEXT': 53, 'SESSION_PUBLICATION': 18, 'LIFECYCLE': 90, 'SESSION_HISTORY': 1, 'SESSION_SOURCE': 2, 'SESSION_DENIED': 16, 'SESSION_LINK': 2, 'SESSION_REQUEST': 18, 'SESSION_AUTHORITY': 18, 'SESSION_BOUNDARY': 36, 'SESSION_CAUSE': 18, 'SESSION_COMMAND': 18, 'SESSION_FAILURE': 18, 'RESOLUTION_TARGET': 16, 'SESSION_RESOLUTION': 16, 'SESSION_HISTORY_PAGE': 40, 'SESSION_RECOVERY_CONTEXT': 2, 'SESSION_TERMINAL_CLOSURE': 1}


def _invalid():
    raise dv.DiagnosticsContractError("DIAGNOSTICS_VALUE_INVALID")


def _check(value, spec):
    if spec.endswith("|null"):
        if value is None:
            return
        return _check(value, spec[:-5])
    if spec.startswith("tuple<"):
        match = re.fullmatch(r"tuple<(.+),(\d+)(?:\.\.(\d+))?>", spec)
        if match is None or type(value) is not tuple:
            _invalid()
        lo, hi = int(match[2]), int(match[3] or match[2])
        if not lo <= len(value) <= hi:
            _invalid()
        for child in value:
            _check(child, match[1])
        return
    if spec == "bool" or spec.startswith("const_bool:"):
        if type(value) is not bool or spec == "const_bool:false" and value is not False:
            _invalid()
        return
    if spec == "uint64":
        return dv._integer(value, 0, (1 << 64) - 1)
    match = re.fullmatch(r"uint(?:8|16|32)\[(\d+)\.\.(\d+)\]", spec)
    if match:
        return dv._integer(value, int(match[1]), int(match[2]))
    if spec.startswith("Alias"):
        return dv._string(value, r"ref:[0-9]{6}", 10)
    if spec == "Signature":
        return dv._string(value, r"[01]{9}", 9)
    if spec == "UtcTimestamp":
        return dv._utc(value)
    if spec.startswith(("const:", "fixed:")):
        if type(value) is not str or value != spec.split(":", 1)[1]:
            _invalid()
        return
    if spec == "VerifiedCanonicalVector9":
        if type(value) is not sv.CanonicalAshBinding:
            _invalid()
        try:
            sv.canonical_source_baseline(value)
        except sv.StateContractError:
            _invalid()
        return
    if spec == "VerifiedSourcePathDigest":
        from . import recovery_values as rv
        if type(value) is not rv.SourcePin:
            _invalid()
        rv.SourcePin.__post_init__(value)
        return
    if spec == "VerifiedSourceVectorHash":
        if type(value) is not str or value not in SOURCE_VECTOR_HASHES.values():
            _invalid()
        return
    if spec in FIELD_SPECS:
        if type(value) is not globals()[spec]:
            _invalid()
        type(value).__post_init__(value)
        return
    old = getattr(dv, spec, None)
    if type(old) is type:
        if type(value) is not old:
            _invalid()
        old.__post_init__(value)
        return
    aliases = {"ContainmentTrigger":"CanonicalContainmentTrigger", "SafeHaltTrigger":"CanonicalSafeHaltTrigger",
        "CanonicalRule17":"CanonicalRule", "SupportingKindWithoutHistoryPage":"SupportingKind"}
    resolved = aliases.get(spec, spec)
    try:
        choices = dv.enum_values(resolved)
    except dv.DiagnosticsContractError:
        choices = DOMAINS.get(resolved)
    if choices is not None:
        if type(value) is not str or value not in choices or spec == "SupportingKindWithoutHistoryPage" and value == "SESSION_HISTORY_PAGE":
            _invalid()
        return
    if "|" in spec:
        for option in spec.split("|"):
            try:
                _check(value, option)
                return
            except dv.DiagnosticsContractError:
                pass
        _invalid()
    if type(value) is not str or value != spec:
        _invalid()


def _record(value):
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is tuple:
        return [_record(item) for item in value]
    if type(value) in VALUE_TYPES or type(value) in dv.VALUE_TYPES or type(value) is sv.CanonicalAshBinding:
        return value.to_record()
    from . import recovery_values as rv
    if type(value) is rv.SourcePin:
        return value.to_record()
    _invalid()


class _SafeRecord:
    def __post_init__(self):
        for name, spec in FIELD_SPECS[type(self).__name__].items():
            _check(getattr(self, name), spec)
        _coherent(self)

    def to_record(self):
        type(self).__post_init__(self)
        return {field.name: _record(getattr(self, field.name)) for field in fields(self)}


def _coherent(value):
    name = type(value).__name__
    if name == "SafeSessionSourceEvidence":
        from . import recovery_values as rv
        baseline = sv.canonical_source_baseline(value.canonical_binding)
        if value.assembly_generation != ("LEGACY_PAIR" if baseline == "LEGACY_C78" else "N3_LIFECYCLE_PAIR"):
            _invalid()
        if tuple((pin.path, pin.sha256) for pin in value.paired_recovery_sources) != rv.recovery_contract_pin_fields(value.canonical_binding):
            _invalid()
        if value.source_vector_sha256 != SOURCE_VECTOR_HASHES[baseline]:
            _invalid()
    elif name == "SafeSessionSnapshotEvidence":
        if value.terminal_latched != (value.mode == "SAFE_HALT"):
            _invalid()
        if (value.current_assessment_reference is None) != (value.observed_system_state_class is None):
            _invalid()
        if value.mode == "SAFE_HALT" and (value.halt_reference is None or value.current_assessment_reference is not None):
            _invalid()
    elif name == "SafeSessionContextEvidence":
        if value.is_running != (not value.is_halted) or value.is_halted and value.is_contained:
            _invalid()
    elif name == "SafeSessionPublicationEvidence":
        if value.status == "COMMITTED" and (value.after_snapshot_reference is None or value.session_effects_performed is not True):
            _invalid()
        if value.status == "NOT_COMMITTED" and value.session_effects_performed is not False:
            _invalid()
    elif name == "SafeSessionCompletionObservation":
        if (value.status == "COMPLETE") != (value.failure_code is None):
            _invalid()
    elif name == "SafeSessionOriginCompletionObservation":
        if tuple(sorted(set(value.confirmed_event_indices))) != value.confirmed_event_indices:
            _invalid()
        if value.status == "COMPLETE" and (value.failure_code is not None or value.attempted_event_index is not None):
            _invalid()
    elif name == "SafeLifecycleEvidence":
        if value.conformance == "CANONICAL_OBSERVATION":
            if value.record_reference is None or value.envelope is None or value.missing_fields or value.pending_reason_code is not None:
                _invalid()
            if value.kind != value.envelope.diagnostic_kind:
                _invalid()
        elif not value.missing_fields or value.pending_reason_code is None:
            _invalid()
        if value.kind in ("CONTAINMENT", "SAFE_HALT") and value.conformance == "CANONICAL_OBSERVATION":
            if value.monotonic_nanoseconds is None or value.monotonic_unavailable_reason is not None:
                _invalid()
            if (value.utc is None) != (value.utc_unavailable_reason is not None):
                _invalid()
    elif name == "SafeHistoryRecordReference":
        if value.storage_status == "CONFIRMED" and (value.event_id is None or value.local_sequence is None):
            _invalid()
    elif name == "SafeSessionHistoryPage":
        if not value.record_references and not value.supporting_references:
            _invalid()
    elif name == "SafeSessionTerminalClosureEvidence":
        if value.terminal_envelope.diagnostic_kind != "SAFE_HALT" or value.terminal_envelope.stage != "TERMINAL":
            _invalid()


@dataclass(frozen=True, slots=True)
class SafeSessionBindingEvidence(_SafeRecord):
    evidence_reference: object
    session_reference: object
    assembly_generation: object
    canonical_source_evidence_reference: object
    paired_source_evidence_reference: object
    profile_evidence_reference: object
    policy_reference: object
    policy_assurance: object
    binding_reference: object
    initial_assessment_reference: object
    policy_id: object
    policy_version: object
    policy_source_path: object
    policy_source_sha256: object

@dataclass(frozen=True, slots=True)
class SafeSessionSnapshotEvidence(_SafeRecord):
    evidence_reference: object
    session_binding_reference: object
    generation: object
    current_state: object
    mode: object
    terminal_latched: object
    admission_status: object
    containment_reference: object
    halt_reference: object
    recovery_attempted: object
    active_operation_reference: object
    snapshot_reference: object
    current_assessment_reference: object
    observed_system_state_class: object

@dataclass(frozen=True, slots=True)
class SafeSessionContextEvidence(_SafeRecord):
    evidence_reference: object
    snapshot_evidence_reference: object
    operation_reference: object
    subject_state: object
    is_running: object
    is_contained: object
    is_halted: object
    assurance: object
    observation_reference: object

@dataclass(frozen=True, slots=True)
class SafeSessionPublicationEvidence(_SafeRecord):
    evidence_reference: object
    request_reference: object
    requested_action: object
    lease_reference: object
    before_snapshot_reference: object
    after_snapshot_reference: object
    status: object
    session_effects_performed: object
    requested_state: object
    requested_mode: object
    cause_reference: object
    proof_reference: object
    failure_code: object
    omitted_fields: object
    request_evidence_reference: object
    authority_evidence_reference: object
    cause_evidence_reference: object
    publication_reference: object

@dataclass(frozen=True, slots=True)
class SafeLifecycleEvidence(_SafeRecord):
    evidence_reference: object
    record_reference: object
    kind: object
    envelope: object
    original_assessment_evidence_reference: object
    recovery_diagnostic_evidence_reference: object
    trigger: object
    system_state_class: object
    restricted_operations: object
    utc: object
    monotonic_nanoseconds: object
    utc_unavailable_reason: object
    monotonic_unavailable_reason: object
    awaiting_resolution: object
    resolution: object
    is_terminal: object
    prior_history_evidence_reference: object
    rule_ids: object
    capture_status: object
    omitted_fields: object
    conformance: object
    missing_fields: object
    pending_reason_code: object
    cause_evidence_reference: object
    clock_assurance: object

@dataclass(frozen=True, slots=True)
class SafeSessionChildLink(_SafeRecord):
    link_reference: object
    session_binding_reference: object
    admitted_generation: object
    live_origin_assessment_reference: object
    child_origin_assessment_reference: object
    child_operation_reference: object

@dataclass(frozen=True, slots=True)
class SafeSessionHistoryEvidence(_SafeRecord):
    evidence_reference: object
    session_binding_reference: object
    main_assessment_evidence_reference: object
    child_link: object
    recovery_operation_reference: object
    context_evidence_references: object
    publication_evidence_references: object
    lifecycle_evidence_references: object
    pending_lifecycle_evidence_reference: object
    page_evidence_references: object
    confirmed_record_count: object
    unknown_storage_record_count: object
    attempted_lifecycle_record_count: object
    supporting_reference_count: object
    frozen: object
    coverage: object
    omitted_fields: object
    request_evidence_references: object
    authority_evidence_references: object
    cause_evidence_references: object
    boundary_evidence_references: object
    command_evidence_references: object
    failure_evidence_references: object
    resolution_evidence_references: object
    recovery_operation_references: object
    child_link_references: object
    current_assessment_evidence_reference: object
    episode_assessment_evidence_references: object
    terminal_closure_evidence_reference: object

@dataclass(frozen=True, slots=True)
class SafeHistoryRecordReference(_SafeRecord):
    diagnostic_reference: object
    event_id: object
    local_sequence: object
    storage_status: object

@dataclass(frozen=True, slots=True)
class SafeSupportingReference(_SafeRecord):
    kind: object
    evidence_reference: object

@dataclass(frozen=True, slots=True)
class SafeSessionHistoryPage(_SafeRecord):
    evidence_reference: object
    history_evidence_reference: object
    page_index: object
    record_references: object
    supporting_references: object

@dataclass(frozen=True, slots=True)
class SafeSessionSourceEvidence(_SafeRecord):
    evidence_reference: object
    assembly_generation: object
    canonical_binding: object
    paired_recovery_sources: object
    source_vector_sha256: object
    assembly_assurance: object

@dataclass(frozen=True, slots=True)
class SafeSessionDeniedEvidence(_SafeRecord):
    evidence_reference: object
    session_binding_reference: object
    snapshot_evidence_reference: object
    audit_reference: object
    request_reference: object
    request_observation: object
    reason_code: object
    record_reference: object
    capture_status: object
    omitted_fields: object
    denial_ordinal: object
    completion_observation: object

@dataclass(frozen=True, slots=True)
class SafeSessionChildLinkEvidence(_SafeRecord):
    evidence_reference: object
    link: object

@dataclass(frozen=True, slots=True)
class SafeSessionRequestEvidence(_SafeRecord):
    evidence_reference: object
    command_reference: object
    session_reference: object
    expected_generation: object
    action: object
    omitted_fields: object
    expected_snapshot_evidence_reference: object
    submitted_trigger: object
    authority_evidence_reference: object
    boundary_evidence_references: object
    submitted_recovery_operation_reference: object
    submitted_recovery_context_evidence_reference: object

@dataclass(frozen=True, slots=True)
class SafeSessionAuthorityEvidence(_SafeRecord):
    evidence_reference: object
    request_evidence_reference: object
    status: object
    request_origin: object
    source_reference: object
    source_digest_reference: object
    source_evidence_reference: object
    observation_evidence_reference: object
    assurance: object
    omitted_fields: object
    observed_expected_snapshot_reference: object
    observed_request_reference: object

@dataclass(frozen=True, slots=True)
class SafeSessionBoundaryEvidence(_SafeRecord):
    evidence_reference: object
    request_evidence_reference: object
    condition: object
    status: object
    source_reference: object
    source_digest_reference: object
    source_evidence_reference: object
    observation_evidence_reference: object
    assurance: object
    omitted_fields: object
    observed_expected_snapshot_reference: object
    observed_request_reference: object

@dataclass(frozen=True, slots=True)
class SafeSessionCauseEvidence(_SafeRecord):
    evidence_reference: object
    cause_reference: object
    request_evidence_reference: object
    kind: object
    trigger: object
    recovery_operation_reference: object
    recovery_outcome: object
    recovery_diagnostic_evidence_references: object
    recovery_safety_evidence_reference: object
    authority_evidence_reference: object
    boundary_evidence_references: object
    projection_coverage: object
    observed_expected_snapshot_reference: object
    observed_request_reference: object

@dataclass(frozen=True, slots=True)
class SafeSessionCompletionObservation(_SafeRecord):
    status: object
    operation_reference: object
    confirmed_references: object
    failure_code: object
    assurance: object

@dataclass(frozen=True, slots=True)
class SafeSessionOriginCompletionObservation(_SafeRecord):
    operation_reference: object
    status: object
    operation_outcome: object
    confirmed_event_indices: object
    diagnostic_coverage: object
    failure_code: object
    attempted_event_index: object
    assurance: object
    omitted_fields: object

@dataclass(frozen=True, slots=True)
class SafeSessionFailureEvidence(_SafeRecord):
    evidence_reference: object
    request_evidence_reference: object
    failure_code: object
    field_name: object
    primary_evidence_reference: object
    capture_status: object
    attempted_lifecycle_evidence_reference: object
    completion_observation: object
    completion_failure_code: object
    unconfirmed_completion_observation: object
    omitted_fields: object
    unavailable_post_assessment_facts: object

@dataclass(frozen=True, slots=True)
class SafeSessionCommandEvidence(_SafeRecord):
    evidence_reference: object
    request_evidence_reference: object
    before_snapshot_reference: object
    after_snapshot_reference: object
    session_effects_performed: object
    admission_status: object
    admission_before_snapshot_reference: object
    admission_failure_code: object
    lease_reference: object
    lease_expected_snapshot_reference: object
    lease_action: object
    authority_evidence_reference: object
    cause_evidence_reference: object
    origin_assessment_evidence_reference: object
    origin_completion_observation: object
    recovery_operation_reference: object
    publication_evidence_reference: object
    lifecycle_evidence_references: object
    pending_lifecycle_evidence_reference: object
    capture_completion_observation: object
    failure_evidence_reference: object
    projection_coverage: object
    omitted_fields: object
    resolution_evidence_reference: object
    submitted_recovery_operation_reference: object
    lease_active_snapshot_reference: object
    admission_failure_field: object
    actual_post_assessment_evidence_reference: object
    actual_post_completion_observation: object
    operation_status: object
    raw_business_failure_phase: object
    raw_business_failure_coverage: object

@dataclass(frozen=True, slots=True)
class SafeResolutionTargetEvidence(_SafeRecord):
    evidence_reference: object
    session_binding_reference: object
    request_evidence_reference: object
    before_snapshot_reference: object
    containment_record_reference: object
    target_state: object
    canonical_source_evidence_reference: object
    profile_evidence_reference: object
    target_validity: object
    prospective_is_in_safe_halt: object
    prospective_is_in_containment: object
    prospective_system_class: object
    prospective_recovery_category: object
    assurance: object
    validation_status: object
    validation_failure_code: object
    validation_field_name: object

@dataclass(frozen=True, slots=True)
class SafeSessionResolutionEvidence(_SafeRecord):
    evidence_reference: object
    request_evidence_reference: object
    session_binding_reference: object
    containment_record_reference: object
    route: object
    target_evidence_reference: object
    authority_evidence_reference: object
    boundary_clear_evidence_reference: object
    propagation_evidence_reference: object
    before_snapshot_reference: object
    after_snapshot_reference: object
    publication_evidence_reference: object
    actual_post_assessment_reference: object
    status: object
    session_effects_performed: object
    observed_boundary_status: object
    observed_propagation_status: object
    actual_resolution_record_reference: object
    omitted_fields: object
    propagation_operation_reference: object
    propagation_origin_assessment_reference: object
    propagation_source_binding: object
    previous_episode_root_reference: object
    actual_new_episode_root_reference: object
    resolution_action: object
    requested_target_state: object
    submitted_recovery_operation_reference: object

@dataclass(frozen=True, slots=True)
class SafeSessionSubmittedRecoveryContextEvidence(_SafeRecord):
    evidence_reference: object
    operation_reference: object
    origin_assessment_reference: object
    context_owner_reference: object
    context_observation_reference: object
    context_source_binding: object
    observed_is_in_safe_halt: object
    observed_is_in_containment: object
    propagation_operation_reference: object
    propagation_origin_assessment_reference: object
    propagation_status: object
    propagation_source_binding: object
    authority_operation_reference: object
    authority_origin_assessment_reference: object
    authority_status: object
    authority_source_binding: object
    omitted_fields: object
    assurance: object

@dataclass(frozen=True, slots=True)
class SafeSessionTerminalClosureEvidence(_SafeRecord):
    evidence_reference: object
    request_evidence_reference: object
    bridge_record_reference: object
    terminal_diagnostic_reference: object
    terminal_envelope: object
    actual_terminal_publication_evidence_reference: object
    assurance: object

@dataclass(frozen=True, slots=True)
class SafeUnavailablePostAssessmentFacts(_SafeRecord):
    operation_reference: object
    candidate_state: object
    source_binding: object
    omitted_fields: object

VALUE_TYPES = (SafeSessionBindingEvidence, SafeSessionSnapshotEvidence, SafeSessionContextEvidence, SafeSessionPublicationEvidence, SafeLifecycleEvidence, SafeSessionChildLink, SafeSessionHistoryEvidence, SafeHistoryRecordReference, SafeSupportingReference, SafeSessionHistoryPage, SafeSessionSourceEvidence, SafeSessionDeniedEvidence, SafeSessionChildLinkEvidence, SafeSessionRequestEvidence, SafeSessionAuthorityEvidence, SafeSessionBoundaryEvidence, SafeSessionCauseEvidence, SafeSessionCompletionObservation, SafeSessionOriginCompletionObservation, SafeSessionFailureEvidence, SafeSessionCommandEvidence, SafeResolutionTargetEvidence, SafeSessionResolutionEvidence, SafeSessionSubmittedRecoveryContextEvidence, SafeSessionTerminalClosureEvidence, SafeUnavailablePostAssessmentFacts,)

SUPPORT_FIELDS = (
    ('session_bindings', 'SESSION_BINDING', SafeSessionBindingEvidence, 19),
    ('session_snapshots', 'SESSION_SNAPSHOT', SafeSessionSnapshotEvidence, 214),
    ('session_contexts', 'SESSION_CONTEXT', SafeSessionContextEvidence, 53),
    ('session_publications', 'SESSION_PUBLICATION', SafeSessionPublicationEvidence, 18),
    ('lifecycle_evidence', 'LIFECYCLE', SafeLifecycleEvidence, 90),
    ('session_histories', 'SESSION_HISTORY', SafeSessionHistoryEvidence, 1),
    ('session_sources', 'SESSION_SOURCE', SafeSessionSourceEvidence, 2),
    ('session_denials', 'SESSION_DENIED', SafeSessionDeniedEvidence, 16),
    ('session_child_links', 'SESSION_LINK', SafeSessionChildLinkEvidence, 2),
    ('session_requests', 'SESSION_REQUEST', SafeSessionRequestEvidence, 18),
    ('session_authorities', 'SESSION_AUTHORITY', SafeSessionAuthorityEvidence, 18),
    ('session_boundaries', 'SESSION_BOUNDARY', SafeSessionBoundaryEvidence, 36),
    ('session_causes', 'SESSION_CAUSE', SafeSessionCauseEvidence, 18),
    ('session_commands', 'SESSION_COMMAND', SafeSessionCommandEvidence, 18),
    ('session_failures', 'SESSION_FAILURE', SafeSessionFailureEvidence, 18),
    ('resolution_targets', 'RESOLUTION_TARGET', SafeResolutionTargetEvidence, 16),
    ('session_resolutions', 'SESSION_RESOLUTION', SafeSessionResolutionEvidence, 16),
    ('session_history_pages', 'SESSION_HISTORY_PAGE', SafeSessionHistoryPage, 40),
    ('session_recovery_contexts', 'SESSION_RECOVERY_CONTEXT', SafeSessionSubmittedRecoveryContextEvidence, 2),
    ('session_terminal_closures', 'SESSION_TERMINAL_CLOSURE', SafeSessionTerminalClosureEvidence, 1),
)


class SessionProjection:
    """Collector-owned graph builder. Keys depend on complete owned values.

    This object has no mutation authority over session state. It translates
    observations already issued by the semantic owner into closed safe nodes.
    """
    def __init__(self, collector, state):
        self.c, self.state = collector, state

    def key(self, kind, value, *, phase=""):
        import hashlib
        from . import session_values as v
        return self.c._alias("session:" + kind + ":" + phase + ":" +
            hashlib.sha256(v.raw_business_bytes(value)).hexdigest())

    def put(self, support_kind, cls, value, *, phase="", key_alias=None, **values):
        alias = key_alias or self.key(support_kind, value, phase=phase)
        node = cls(evidence_reference=alias, **values)
        try:
            return self.c._supporting(support_kind, alias, node)
        finally:
            if alias in self.c._support[support_kind] or (support_kind, alias) in self.c._unconfirmed_support:
                self.state.pinned_support.add((support_kind, alias))

    def alias(self, value):
        return None if value is None else self.c._alias(value)

    def cause_key(self, reference):
        import hashlib
        return self.c._alias("session:cause:" + hashlib.sha256(reference.encode("ascii")).hexdigest())

    def binding(self, value):
        from . import recovery_values as rv
        generation = "LEGACY_PAIR" if value.canonical_binding.aggregate_sha256 == dict(sv.CANONICAL_BINDING_FIELDS)["aggregate_sha256"] else "N3_LIFECYCLE_PAIR"
        source = self.put("SESSION_SOURCE", SafeSessionSourceEvidence, value.recovery_binding,
            assembly_generation=generation, canonical_binding=value.canonical_binding,
            paired_recovery_sources=value.recovery_binding.contract_pins,
            source_vector_sha256=SOURCE_VECTOR_HASHES["LEGACY_C78" if generation == "LEGACY_PAIR" else "N3_LIFECYCLE"],
            assembly_assurance="RECOGNIZED_COMPLETE_VECTOR")
        policy = value.policy_binding
        return self.put("SESSION_BINDING", SafeSessionBindingEvidence, value,
            session_reference=self.alias(value.session_reference), assembly_generation=generation,
            canonical_source_evidence_reference=self.c._source_support(value.canonical_binding),
            paired_source_evidence_reference=source, profile_evidence_reference=self.c._profile_support(value.profile_binding),
            policy_reference=self.alias(policy.source_path), policy_assurance="RECOGNIZED_ADOPTED_POLICY",
            binding_reference=self.alias(value.binding_reference), initial_assessment_reference=self.alias(value.initial_assessment_reference),
            policy_id=policy.policy_id, policy_version=policy.policy_version, policy_source_path=policy.source_path,
            policy_source_sha256=policy.source_sha256)

    def snapshot(self, value):
        return self.put("SESSION_SNAPSHOT", SafeSessionSnapshotEvidence, value,
            session_binding_reference=self.binding(value.binding), generation=value.generation,
            current_state=value.current_state.signature, mode=value.mode, terminal_latched=value.terminal_latched,
            admission_status=value.admission_status, containment_reference=self.alias(value.containment_reference),
            halt_reference=self.alias(value.halt_reference), recovery_attempted=value.recovery_attempted,
            active_operation_reference=self.alias(value.active_operation_reference), snapshot_reference=self.alias(value.snapshot_reference),
            current_assessment_reference=self.alias(value.current_assessment_reference), observed_system_state_class=value.observed_system_state_class)

    def assessment(self, value):
        if value is None:
            return None
        # Zero-emission failure has no canonical assessment node. Preserve its
        # source/profile and actual failure through the command observation.
        if not value.emitted_diagnostics:
            self.c._source_support(value.source_binding)
            self.c._profile_support(value.profile_binding)
            return None
        return self.c._assessment_support(value)

    def completion(self, value):
        if value is None:
            return None
        return SafeSessionCompletionObservation(value.status, self.alias(value.operation_reference),
            tuple(self.alias(item) for item in value.confirmed_references), value.failure_code,
            "OBSERVED_CAPTURE_RESPONSE_NOT_STORAGE_PROOF")

    def origin_completion(self, value):
        if value is None:
            return None
        return SafeSessionOriginCompletionObservation(self.alias(value.operation_reference), value.status,
            value.operation_outcome, value.confirmed_event_indices, value.diagnostic_coverage, value.failure_code,
            value.attempted_event_index, "OBSERVED_CAPTURE_RESPONSE_NOT_STORAGE_PROOF", "RETURNED_RECEIPT_HEALTH_BUSINESS_ONLY")

    def authority(self, value, request_alias):
        if value is None:
            return None
        source = value.source_binding
        return self.put("SESSION_AUTHORITY", SafeSessionAuthorityEvidence, value,
            request_evidence_reference=request_alias, status=value.status, request_origin=value.request_origin,
            source_reference=self.alias(source.source_reference), source_digest_reference=self.alias(source.source_sha256),
            source_evidence_reference=self.alias(source.evidence_reference), observation_evidence_reference=self.alias(value.observation_reference),
            assurance="DECLARED_REFERENCE_AUTHORIZATION", omitted_fields="AUTHORITY_REASON",
            observed_expected_snapshot_reference=self.alias(value.expected_snapshot_reference), observed_request_reference=self.alias(value.request_reference))

    def boundary(self, value, request_alias):
        source = value.source_binding
        return self.put("SESSION_BOUNDARY", SafeSessionBoundaryEvidence, value,
            request_evidence_reference=request_alias, condition=value.condition, status=value.status,
            source_reference=self.alias(source.source_reference), source_digest_reference=self.alias(source.source_sha256),
            source_evidence_reference=self.alias(source.evidence_reference), observation_evidence_reference=self.alias(value.observation_reference),
            assurance="DECLARED_REFERENCE_BOUNDARY_OBSERVATION", omitted_fields="BOUNDARY_REASON",
            observed_expected_snapshot_reference=self.alias(value.expected_snapshot_reference), observed_request_reference=self.alias(value.request_reference))

    def recovery_context(self, value):
        context, propagation, authority = value.context_observation, value.propagation_evidence, value.external_authority_evidence
        return self.put("SESSION_RECOVERY_CONTEXT", SafeSessionSubmittedRecoveryContextEvidence, value,
            operation_reference=self.alias(value.operation_reference), origin_assessment_reference=self.alias(value.origin_assessment_reference),
            context_owner_reference=self.alias(context.owner_reference), context_observation_reference=self.alias(context.observation_reference),
            context_source_binding=self.c._evidence_source(context.source_binding),
            observed_is_in_safe_halt=context.context.is_in_safe_halt, observed_is_in_containment=context.context.is_in_containment,
            propagation_operation_reference=self.alias(propagation.operation_reference), propagation_origin_assessment_reference=self.alias(propagation.origin_assessment_reference),
            propagation_status=propagation.status, propagation_source_binding=self.c._evidence_source(propagation.source_binding),
            authority_operation_reference=self.alias(authority.operation_reference), authority_origin_assessment_reference=self.alias(authority.origin_assessment_reference),
            authority_status=authority.status, authority_source_binding=self.c._evidence_source(authority.source_binding),
            omitted_fields="PROPAGATION_AND_EXTERNAL_AUTHORITY_REASON", assurance="SUBMITTED_BOUND_EVIDENCE_NOT_CURRENT_OWNER_CONTEXT")

    def request(self, command):
        from . import session_values as v
        request = command.request
        alias = self.key("SESSION_REQUEST", command)
        return self.put("SESSION_REQUEST", SafeSessionRequestEvidence, command,
            command_reference=self.alias(request.request_reference), session_reference=self.alias(request.session_reference),
            expected_generation=request.expected_snapshot.generation, action=request.action, omitted_fields="REQUEST_REASON",
            expected_snapshot_evidence_reference=self.snapshot(request.expected_snapshot), submitted_trigger=getattr(command, "trigger", None),
            authority_evidence_reference=self.authority(getattr(command, "authority_observation", None), alias),
            boundary_evidence_references=tuple(self.boundary(item, alias) for item in getattr(command, "boundary_observations", ())),
            submitted_recovery_operation_reference=self.alias(getattr(command, "recovery_operation_reference", None)),
            submitted_recovery_context_evidence_reference=self.recovery_context(command.operation_context) if type(command) is v.SessionRecoveryRequest else None)

    def context(self, value):
        return self.put("SESSION_CONTEXT", SafeSessionContextEvidence, value,
            snapshot_evidence_reference=self.snapshot(value.snapshot), operation_reference=self.alias(value.operation_reference),
            subject_state=value.subject_state.signature, is_running=value.is_running, is_contained=value.is_contained, is_halted=value.is_halted,
            assurance="CURRENT_IN_PROCESS_SESSION_OBSERVATION", observation_reference=self.alias(value.observation_reference))

    def cause(self, value, command):
        if value is None:
            return None
        request_alias = self.request(command)
        packet = self.state.recovery_results.get(value.recovery_operation_reference)
        references = () if packet is None else tuple(self.c._alias(item.action_reference) for item in packet.action_decisions)
        return self.put("SESSION_CAUSE", SafeSessionCauseEvidence, value, key_alias=self.cause_key(value.cause_reference),
            cause_reference=self.alias(value.cause_reference), request_evidence_reference=request_alias, kind=value.kind, trigger=value.trigger,
            recovery_operation_reference=self.alias(value.recovery_operation_reference), recovery_outcome=None if packet is None else packet.outcome,
            recovery_diagnostic_evidence_references=references, recovery_safety_evidence_reference=None if packet is None else self.c._safety_support(packet),
            authority_evidence_reference=self.authority(value.authority_observation, request_alias),
            boundary_evidence_references=tuple(self.boundary(item, request_alias) for item in value.boundary_observations),
            projection_coverage="COMPLETE_SPECIFIED_SAFE_GRAPH" if value.recovery_operation_reference is None or packet is not None else "PARTIAL",
            observed_expected_snapshot_reference=self.alias(value.expected_snapshot_reference), observed_request_reference=self.alias(value.request_reference))

    def publication(self, value, command, authority=None, cause=None):
        if value is None:
            return None
        return self.put("SESSION_PUBLICATION", SafeSessionPublicationEvidence, value,
            request_reference=self.alias(value.request_reference), requested_action=command.request.action,
            lease_reference=self.alias(value.lease_reference), before_snapshot_reference=self.snapshot(value.before),
            after_snapshot_reference=None if value.after is None else self.snapshot(value.after), status=value.status,
            session_effects_performed=value.session_effects_performed, requested_state=value.requested_state.signature,
            requested_mode=value.requested_mode, cause_reference=self.alias(value.cause_reference), proof_reference=self.alias(value.proof_reference),
            failure_code=value.failure_code, omitted_fields="PUBLICATION_REASON", request_evidence_reference=self.request(command),
            authority_evidence_reference=self.authority(authority, self.request(command)), cause_evidence_reference=self.cause_key(value.cause_reference),
            publication_reference=self.alias(value.publication_reference))

    def lifecycle(self, value, command, status):
        from . import session_values as v
        from . import recovery_values as rv
        pending = type(value) is v.PendingLifecycleRecord
        kind = value.kind if pending else value.envelope.diagnostic_kind
        payload = None if pending else value.payload
        origin = value.original_assessment if pending else self.state.episode_origin
        recovery_ref = None
        if type(payload) is rv.RecoveryDiagnostic:
            recovery_ref = self.key("RECOVERY_DIAGNOSTIC", value)
            node = dv.SafeRecoveryDiagnostic(payload.recovery_category, payload.original_state_class,
                self.alias(origin.emitted_diagnostics[0].diagnostic_reference), (), payload.outcome,
                None if payload.corrected_state is None else payload.corrected_state.signature,
                self.alias(payload.fallback_policy_id), dv.message_text("RECOVERY_ACTION_RECORDED"), payload.rule_ids)
            self.c._supporting("RECOVERY_DIAGNOSTIC", recovery_ref, node)
            self.state.pinned_support.add(("RECOVERY_DIAGNOSTIC", recovery_ref))
        clock = getattr(payload, "containment_time", getattr(payload, "halt_time", None))
        return self.put("LIFECYCLE", SafeLifecycleEvidence, value, phase=status,
            record_reference=None if pending else self.alias(value.diagnostic_reference), kind=kind,
            envelope=None if pending else self.c._safe_envelope(value.envelope, "RECOVERY_ACTION_RECORDED"),
            original_assessment_evidence_reference=self.assessment(origin), recovery_diagnostic_evidence_reference=recovery_ref,
            trigger=value.trigger if pending else getattr(payload, "trigger", None),
            system_state_class=getattr(payload, "system_state_class", None), restricted_operations=getattr(payload, "restricted_operations", ()),
            utc=None if clock is None else clock.observed_utc, monotonic_nanoseconds=None if clock is None else clock.monotonic_nanoseconds,
            utc_unavailable_reason=None if clock is None else clock.utc_reason, monotonic_unavailable_reason=None if clock is None else clock.monotonic_reason,
            awaiting_resolution=getattr(payload, "awaiting_resolution", None), resolution=getattr(payload, "resolution", None),
            is_terminal=getattr(payload, "is_terminal", None), prior_history_evidence_reference=None,
            rule_ids=("ASH-STATE-GENERAL-001",) if pending else value.envelope.rule_ids, capture_status=status,
            omitted_fields="CANONICAL_FREE_NOTES", conformance="PENDING_NONCONFORMANT" if pending else "CANONICAL_OBSERVATION",
            missing_fields=value.missing_fields if pending else (), pending_reason_code=value.reason_code if pending else None,
            cause_evidence_reference=self.cause(value.cause, command), clock_assurance="COLLECTOR_OWNED_MEASURED_CLOCK_OBSERVATION")

    def target(self, value, observation, command):
        if value is None:
            return None
        return self.put("RESOLUTION_TARGET", SafeResolutionTargetEvidence, value,
            session_binding_reference=self.binding(command.request.expected_snapshot.binding), request_evidence_reference=self.request(command),
            before_snapshot_reference=self.snapshot(command.request.expected_snapshot), containment_record_reference=self.alias(observation.containment_record_reference),
            target_state=value.target_state.signature, canonical_source_evidence_reference=self.c._source_support(value.current_source_binding),
            profile_evidence_reference=self.c._profile_support(value.current_profile_binding),
            target_validity=self.c._safe_validity(value.target_diagnostic, "ash_state_" + value.target_state.signature),
            prospective_is_in_safe_halt=False, prospective_is_in_containment=False,
            prospective_system_class=value.expected_system_state_class, prospective_recovery_category=value.expected_recovery_category,
            assurance="PURE_TARGET_VALIDATION_PROSPECTIVE_CONTEXT_NOT_ENTERED", validation_status=value.status,
            validation_failure_code=value.failure_code, validation_field_name=value.field_name)

    def resolution(self, value, command):
        if value is None:
            return None
        request_alias = self.request(command)
        propagation = value.propagation_evidence
        post = value.actual_post_assessment
        previous = self.state.resolution_previous.get(value.resolution_reference, self.state.main_root)
        return self.put("SESSION_RESOLUTION", SafeSessionResolutionEvidence, value,
            request_evidence_reference=request_alias, session_binding_reference=self.binding(command.request.expected_snapshot.binding),
            containment_record_reference=self.alias(value.containment_record_reference), route=value.route,
            target_evidence_reference=self.target(value.target_validation, value, command), authority_evidence_reference=self.authority(value.authority_observation, request_alias),
            boundary_clear_evidence_reference=None if value.boundary_clear is None else self.boundary(value.boundary_clear, request_alias),
            propagation_evidence_reference=None if propagation is None else self.alias(propagation.source_binding.evidence_reference),
            before_snapshot_reference=self.snapshot(command.request.expected_snapshot),
            after_snapshot_reference=None if value.publication is None or value.publication.after is None else self.snapshot(value.publication.after),
            publication_evidence_reference=self.publication(value.publication, command, value.authority_observation),
            actual_post_assessment_reference=self.assessment(post), status=value.status, session_effects_performed=value.session_effects_performed,
            observed_boundary_status="UNAVAILABLE" if value.boundary_clear is None else value.boundary_clear.status,
            observed_propagation_status="UNAVAILABLE" if propagation is None else propagation.status,
            actual_resolution_record_reference=self.alias(value.resolution_reference), omitted_fields="UNTRUSTED_RESOLUTION_REASON",
            propagation_operation_reference=None if propagation is None else self.alias(propagation.operation_reference),
            propagation_origin_assessment_reference=None if propagation is None else self.alias(propagation.origin_assessment_reference),
            propagation_source_binding=None if propagation is None else self.c._evidence_source(propagation.source_binding),
            previous_episode_root_reference=self.alias(previous), actual_new_episode_root_reference=None if post is None or not post.emitted_diagnostics else self.alias(post.emitted_diagnostics[0].diagnostic_reference),
            resolution_action=command.resolution_action, requested_target_state=None if command.target_state is None else command.target_state.signature,
            submitted_recovery_operation_reference=self.alias(command.recovery_operation_reference))

    def failure(self, value, result, command_alias):
        from . import session_values as v
        from . import recovery_values as rv
        if value is None:
            return None
        primary = value.primary_evidence
        unavailable = None
        primary_ref = None
        if type(primary) is rv.UnavailablePostAssessmentFacts:
            unavailable = SafeUnavailablePostAssessmentFacts(self.alias(primary.operation_reference), primary.candidate_state_reference.signature,
                self.c._evidence_source(primary.source_binding), "UNAVAILABLE_POST_FACTS_REASON")
        elif type(primary) in (sv.StateAssessment, sv.ClassificationEvidenceFailure, sv.DiagnosticCaptureFailure):
            primary_ref = self.assessment(primary)
        elif type(primary) is v.SessionAuthorityObservation:
            primary_ref = self.authority(primary, command_alias)
        elif type(primary) is v.SessionBoundaryObservation:
            primary_ref = self.boundary(primary, command_alias)
        elif type(primary) is v.SessionPublication:
            primary_ref = self.publication(primary, result.request, result.authority_observation, result.cause)
        elif type(primary) is v.ResolutionTargetValidation and result.resolution_observation is not None:
            primary_ref = self.target(primary, result.resolution_observation, result.request)
        elif primary is not None:
            # N2 validation/failure and admission/retention observations are
            # represented by the enclosing command and its existing graph.
            primary_ref = self.alias(getattr(primary, "operation_reference", getattr(primary, "session_reference", result.request.request.request_reference)))
        attempted = value.attempted_lifecycle_record
        return self.put("SESSION_FAILURE", SafeSessionFailureEvidence, value,
            request_evidence_reference=command_alias, failure_code=value.failure_code, field_name=value.field_name,
            primary_evidence_reference=primary_ref, capture_status=value.capture_status,
            attempted_lifecycle_evidence_reference=None if attempted is None else self.lifecycle(attempted, result.request, value.capture_status or "NOT_CONFIRMED"),
            completion_observation=self.completion(result.completion_observation), completion_failure_code=value.completion_failure_code,
            unconfirmed_completion_observation=self.completion(value.unconfirmed_completion_observation), omitted_fields="FAILURE_REASON",
            unavailable_post_assessment_facts=unavailable)

    def components(self, result, *, final=False, descriptor=None):
        command, admission = result.request, result.admission
        request_alias = self.request(command)
        self.context(result.context_observation)
        lease = admission.lease
        refs = tuple(self.lifecycle(item, command, "CONFIRMED") for item in result.confirmed_lifecycle_records)
        for item in result.attempted_lifecycle_records:
            if item not in result.confirmed_lifecycle_records:
                self.lifecycle(item, command, "NOT_CONFIRMED")
        pending_ref = None if result.pending_lifecycle_record is None else self.lifecycle(result.pending_lifecycle_record, command, "NOT_CONFIRMED")
        authority = self.authority(result.authority_observation, request_alias)
        cause = self.cause(result.cause, command)
        publication = self.publication(result.publication, command, result.authority_observation, result.cause)
        failure = self.failure(result.failure_detail, result, request_alias)
        resolution = self.resolution(result.resolution_observation, command)
        if not final:
            return None
        return self.put("SESSION_COMMAND", SafeSessionCommandEvidence, result,
            request_evidence_reference=request_alias, before_snapshot_reference=self.snapshot(result.before),
            after_snapshot_reference=None if result.after is None else self.snapshot(result.after), session_effects_performed=result.session_effects_performed,
            admission_status=admission.status, admission_before_snapshot_reference=self.snapshot(admission.before),
            admission_failure_code=admission.failure_code, lease_reference=None if lease is None else self.alias(lease.lease_reference),
            lease_expected_snapshot_reference=None if lease is None else self.snapshot(lease.before), lease_action=None if lease is None else lease.action,
            authority_evidence_reference=authority, cause_evidence_reference=cause, origin_assessment_evidence_reference=self.assessment(result.origin_assessment),
            origin_completion_observation=self.origin_completion(result.origin_completion_observation),
            recovery_operation_reference=None if result.recovery_result is None else self.alias(result.recovery_result.operation_context.operation_reference),
            publication_evidence_reference=publication, lifecycle_evidence_references=refs, pending_lifecycle_evidence_reference=pending_ref,
            capture_completion_observation=self.completion(result.completion_observation), failure_evidence_reference=failure,
            projection_coverage="COMPLETE_SPECIFIED_SAFE_GRAPH" if result.completion_observation is not None and result.completion_observation.status == "COMPLETE" else "PARTIAL",
            omitted_fields="ADMISSION_REASON_RAW_BUSINESS_PACKETS", resolution_evidence_reference=resolution,
            submitted_recovery_operation_reference=self.alias(getattr(command, "recovery_operation_reference", None)),
            lease_active_snapshot_reference=None if lease is None else self.snapshot(lease.active_snapshot), admission_failure_field=admission.field_name,
            actual_post_assessment_evidence_reference=self.assessment(result.actual_post_assessment), actual_post_completion_observation=self.origin_completion(result.actual_post_completion_observation),
            operation_status=result.status, raw_business_failure_phase=None if descriptor is None else descriptor.phase,
            raw_business_failure_coverage=None if descriptor is None else descriptor.coverage)
