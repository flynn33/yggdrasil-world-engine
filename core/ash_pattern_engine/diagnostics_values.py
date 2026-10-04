"""Closed immutable reference Diagnostics values [YWE-REQ-0042].

The adopted owner is docs/architecture/m3_reference_diagnostics_contract.md.
These values validate representation and cross-field observations. Native IO,
source assembly and actual producer execution belong to their explicit owners.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import ClassVar

from . import state_values as sv


_E_SOURCE_STATUS = frozenset(('VERIFIED_CLEAN', 'VERIFIED_DIRTY', 'UNKNOWN'))
_E_UNAVAILABLE_REASON = frozenset(('NOT_MEASURED', 'NOT_PROVIDED', 'EXCLUDED_REFERENCE_SCOPE', 'NOT_IMPLEMENTED', 'SOURCE_NOT_VERIFIED', 'CLOCK_UNAVAILABLE', 'LOSS_UNCONFIRMED', 'RETENTION_EXPIRED', 'STORAGE_UNAVAILABLE', 'CLOCK_REGRESSION', 'DURATION_LIMIT', 'COUNTER_LIMIT'))
_E_OPERATING_SYSTEM = frozenset(('WINDOWS', 'LINUX', 'MACOS', 'UNKNOWN'))
_E_ARCHITECTURE = frozenset(('X86_64', 'ARM64', 'UNKNOWN'))
_E_HOST_CLASS = frozenset(('HOST', 'VM', 'SIMULATOR', 'UNKNOWN'))
_E_IMPLEMENTATION = frozenset(('REFERENCE_DEVELOPMENT_DIAGNOSTICS', 'REFERENCE_RELEASE_DIAGNOSTICS'))
_E_PROFILE_ID = frozenset(('REFERENCE_DEVELOPMENT', 'REFERENCE_RELEASE'))
_E_COVERAGE_SOURCE = frozenset(('STATE_MODEL', 'NORMALIZATION', 'RECOVERY_ENGINE', 'DIAGNOSTICS', 'PROTECTED_STORAGE', 'PAIRED_EXPORT', 'REALM_ENCODER', 'TRANSITION_REGISTRY', 'TOPOLOGY_GENERATOR', 'AXIOM_EVALUATOR', 'GENERATION_PLANNER', 'ARTIFACT_EMITTER', 'NATIVE_RUNTIME', 'NATIVE_RELEASE', 'PHYSICAL_CRASH', 'ENVIRONMENT_OS', 'RUNTIME_VERSION', 'ARCHITECTURE', 'HOST_CLASS', 'UTC_CLOCK', 'MONOTONIC_CLOCK'))
_E_COVERAGE_STATUS = frozenset(('AVAILABLE', 'UNAVAILABLE', 'EXCLUDED'))
_E_OVERALL_COVERAGE = frozenset(('COMPLETE_DECLARED_REFERENCE_SCOPE', 'PARTIAL', 'UNAVAILABLE'))
_E_RETENTION_REASON = frozenset(('EXPLICIT_PURGE', 'DURATION_EXPIRED', 'WHOLE_OPERATION_ROTATION', 'UNCERTAIN_STORAGE_RANGE'))
_E_STORAGE_STATE = frozenset(('PROTECTED_VERIFIED', 'UNAVAILABLE', 'UNCERTAIN'))
_E_CANONICAL_KIND = frozenset(('STATE_VALIDITY', 'RECOVERY', 'FALLBACK', 'CONTAINMENT', 'SAFE_HALT'))
_E_CANONICAL_SEVERITY = frozenset(('INFO', 'WARNING', 'ERROR', 'CRITICAL'))
_E_CANONICAL_STAGE = frozenset(('DETECTION', 'CLASSIFICATION', 'RECOVERY', 'ESCALATION', 'TERMINAL'))
_E_CANONICAL_DISPOSITION = frozenset(('RESOLVED', 'PENDING', 'BLOCKED', 'ESCALATED', 'TERMINAL'))
_E_CANONICAL_RULE = frozenset(('ASH-STATE-STRUCTURE-001', 'ASH-STATE-VALIDITY-001', 'ASH-STATE-GENERAL-001', 'ASH-CODEWORD-STRUCTURE-001', 'ASH-ADMISSIBILITY-CLASSIFICATION-001', 'ASH-CLASSIFICATION-MAPPING-001', 'ASH-RECOVERY-ACTION-001', 'ASH-FALLBACK-SELECTION-001', 'ASH-CONTAINMENT-TRIGGER-001', 'ASH-HALT-TRIGGER-001'))
_E_ADMISSIBILITY = frozenset(('VALID', 'TRANSFORMATION_COMPATIBLE', 'TRANSFORMATION_INCOMPATIBLE', 'UNCLASSIFIED'))
_E_COMPATIBILITY = frozenset(('COMPATIBLE', 'INCOMPATIBLE', 'UNKNOWN'))
_E_NORMALIZATION_STATUS = frozenset(('ALREADY_VALID', 'NORMALIZABLE', 'NOT_NORMALIZABLE', 'BLOCKED'))
_E_RECOVERABILITY_RELEVANCE = frozenset(('NO_RECOVERY_NEEDED', 'RECOVERY_APPLICABLE', 'NOT_RECOVERABLE', 'CONTAINMENT_NEEDED'))
_E_SYSTEM_CLASS = frozenset(('STABLE', 'UNSTABLE', 'CORRECTABLE', 'DEGRADED', 'CONTAINED', 'FAILED', 'SAFE_HALT'))
_E_RECOVERY_CATEGORY = frozenset(('NO_ACTION', 'NORMALIZE_STATE', 'APPLY_CORRECTION', 'FALLBACK_REQUIRED', 'CONTAINMENT_REQUIRED', 'ESCALATION_REQUIRED', 'TERMINAL_NO_RECOVERY'))
_E_PREDICATE_NAME = frozenset(('CORRECTION_PATH_IS_KNOWN', 'FALLBACK_IS_AVAILABLE', 'APPLICABILITY', 'ADDITIONAL_VALIDATION'))
_E_PRODUCER = frozenset(('STATE_MODEL', 'NORMALIZATION', 'RECOVERY_ENGINE', 'DIAGNOSTICS', 'REFERENCE_HOST'))
_E_EVENT_TYPE = frozenset(('SESSION_START', 'SESSION_END', 'DIAGNOSTIC', 'OPERATION_ADMITTED', 'OPERATION_COMPLETED', 'ACTION_OBSERVED', 'INCIDENT', 'META_DIAGNOSTIC', 'HEALTH', 'RETENTION', 'EXPORT'))
_E_MESSAGE_TEMPLATE = frozenset(('SESSION_OPENED', 'SESSION_CLOSED', 'ORIGIN_ATTACHED', 'DIAGNOSIS_RECORDED', 'CLASSIFICATION_RECORDED', 'NORMALIZATION_COMPUTED', 'POST_VALIDATION_RECORDED', 'RECOVERY_ACTION_RECORDED', 'RECOVERY_REFUSED', 'RECOVERY_HANDOFF_RECORDED', 'DIAGNOSTIC_NONCONFORMANCE', 'CAPTURE_UNCONFIRMED', 'RETENTION_REPORTED', 'EXPORT_COMPLETE', 'EXPORT_INCOMPLETE', 'UNTRUSTED_PROSE_OMITTED'))
_E_OBSERVED_OUTCOME = frozenset(('OBSERVED', 'NOT_EVALUATED', 'COMPLETED', 'FAILED', 'BLOCKED', 'NOT_APPLICABLE', 'ALREADY_VALID', 'NORMALIZED', 'NOT_NORMALIZABLE', 'RECOVERED', 'RECOVERED_VIA_FALLBACK', 'RECOVERY_FAILED', 'ESCALATE_TO_CONTAINMENT', 'CONTAINMENT_HANDOFF', 'HALT_HANDOFF', 'TERMINAL_REFUSAL', 'CONFIRMED', 'REJECTED', 'NOT_CONFIRMED', 'INCOMPLETE'))
_E_FAILURE_DOMAIN = frozenset(('INPUT', 'STATE', 'NORMALIZATION', 'RECOVERY', 'DIAGNOSTICS', 'STORAGE', 'EXPORT'))
_E_SAFE_FAILURE = frozenset(('SOURCE_REPORTED_FAILURE', 'ORIGINAL_PROFILE_MISMATCH', 'ORIGINAL_SOURCE_MISMATCH', 'ORIGINAL_DIAGNOSIS_MISMATCH', 'PLAN_TARGET_SET_MISMATCH', 'PLAN_SELECTION_MISMATCH', 'PLAN_CODEWORD_MISMATCH', 'INPUT_REJECTED', 'PROFILE_UNAVAILABLE', 'NO_TARGET', 'POST_VALIDATION_FAILED', 'CAPTURE_REJECTED', 'CAPTURE_UNCONFIRMED', 'REGISTRY_UNAVAILABLE', 'NO_APPLICABLE_POLICY', 'CORRECTION_PROVIDER_UNAVAILABLE', 'CORRECTION_PROOF_INVALID', 'NONCONFORMANT_DIAGNOSTIC', 'MISSING_REQUIRED_STEP', 'STORAGE_FAILURE', 'EXPORT_FAILURE'))
_E_SAFE_FIELD = frozenset(('ORIGINAL_SOURCE', 'ORIGINAL_PROFILE', 'ORIGINAL_DIAGNOSIS', 'ORIGINAL_ASSESSMENT', 'TARGET_SET', 'SELECTED_TARGET', 'CODEWORD_CHAIN', 'INPUT', 'POST_VALIDATION', 'CAPTURE', 'REGISTRY', 'APPLICABILITY', 'ADDITIONAL_VALIDATION', 'CANONICAL_ENVELOPE', 'CHAIN', 'EXPECTED_STEP', 'STORE', 'EXPORT_PART'))
_E_FACT_TYPE = frozenset(('ACTUAL_STATE_RETAINED', 'STEP_COMPLETED', 'POST_STATE_VALID', 'POST_STATE_NOT_VALID', 'CAPTURE_CONFIRMED', 'CAPTURE_NOT_CONFIRMED', 'ORIGIN_BINDING_DIFFERED', 'PLAN_PROOF_DIFFERED', 'REGISTRY_UNAVAILABLE', 'NO_CANDIDATE_APPLICABLE', 'REQUIRED_STEP_MISSING', 'WHOLE_PAIR_COMPLETED', 'PAIR_INCOMPLETE'))
_E_EXPECTED_INVARIANT = frozenset(('VALID_RETURN', 'STABLE_RETURN', 'ACKNOWLEDGED_STEPS', 'NO_EFFECTS_ON_REFUSAL', 'COMPLETE_CHAIN', 'PAIRED_EXPORT', 'SAFE_PROJECTION'))
_E_UNKNOWN_CAUSE = frozenset(('NO_SUPPORTED_CAUSE', 'STORAGE_COMMIT_UNCONFIRMED', 'CLOCK_NOT_MEASURED', 'EXTERNAL_COLLECTOR_TRUTH_NOT_VERIFIED', 'NATIVE_RUNTIME_NOT_REALIZED', 'PHYSICAL_CRASH_NOT_EXERCISED'))
_E_PINNED_SOURCE = frozenset(('YWE_IMPLEMENTATION', 'ASH_AGGREGATE', 'ASH_STATE_SPACE', 'ASH_CODEWORDS', 'ASH_VALIDITY', 'ASH_CLASSIFICATION', 'ASH_RECOVERY', 'ASH_DIAGNOSTIC_SCHEMA', 'ASH_TAXONOMY', 'RAVEN_POLICY', 'YWE_NORMALIZATION_POLICY'))
_E_OMISSION_CATEGORY = frozenset(('SUMMARY', 'NOTES', 'CALLER_REFERENCE', 'PROFILE_ID', 'UNVERIFIED_SOURCE_DIGEST', 'EVIDENCE_REFERENCE', 'INPUT_PREVIEW', 'NON_BIT_SCALAR', 'URL', 'QUERY', 'HEADER', 'BODY', 'EXCEPTION_TEXT', 'CAUSAL_TEXT', 'STACK', 'ABSOLUTE_PATH', 'ATTACHMENT', 'UNREGISTERED_PAYLOAD', 'HYPOTHESIS'))
_E_REDACTION_REASON = frozenset(('UNTRUSTED_FREEFORM', 'OPAQUE_REFERENCE_ALIAS', 'UNSUPPORTED_SOURCE', 'SENSITIVE_CONTENT', 'EXCLUDED_REFERENCE_SCOPE'))
_E_LIMITATION_CODE = frozenset(('REFERENCE_IMPLEMENTATION_ONLY', 'DECLARED_PRODUCERS_ONLY', 'TRUSTED_CAPTURE_CONTRACT', 'NO_REMOTE_ACK_AUTHENTICATION', 'NATIVE_COMPOSITION_DEFERRED', 'NATIVE_RELEASE_DEFERRED', 'NO_PHYSICAL_CRASH_PROOF', 'NO_POWER_LOSS_DURABILITY_PROOF', 'NO_ENCRYPTION_CLAIM', 'NO_SECOND_USER_ACCESS_TEST', 'NO_AMBIENT_ACTIVITY_CAPTURE', 'UNTRUSTED_PROSE_OMITTED', 'LOSS_RANGE_COALESCED', 'PARENT_STORAGE_NOT_VERIFIED'))
_E_META_CAUSE_CODE = frozenset(('REQUIRED_FIELD_MISSING', 'SCHEMA_NONCONFORMANCE', 'RULE_NOT_APPROVED', 'DUPLICATE_REFERENCE', 'PARENT_MISMATCH', 'ROOT_MISMATCH', 'SUBJECT_MISMATCH', 'STAGE_REGRESSION', 'TERMINAL_SUCCESSOR', 'REQUIRED_STEP_MISSING', 'PRODUCER_PAYLOAD_MISMATCH', 'CLOCK_UNAVAILABLE', 'CLOCK_REGRESSION', 'DURATION_EXPIRED', 'COUNTER_LIMIT', 'MAIN_CAPACITY_EXHAUSTED', 'COMPLETION_MISSING'))
_E_EXPECTED_PHASE = frozenset(('DETECTION', 'CLASSIFICATION', 'COMPUTATION', 'POST_VALIDATION', 'RECOVERY_PREDICATE', 'RECOVERY_STEP', 'RECOVERY_POST_ASSESSMENT', 'BOUNDARY_HANDOFF'))
_E_STORAGE_COMMIT_STATUS = frozenset(('COMMITTED', 'REJECTED', 'UNKNOWN'))
_E_EXPORT_PART = frozenset(('JSON', 'MARKDOWN', 'MANIFEST', 'PUBLICATION'))
_E_PART_NAME = frozenset(('diagnostics.json', 'diagnostics.md', 'manifest.json'))
_E_PART_STATUS = frozenset(('NOT_WRITTEN', 'WRITTEN_UNCONFIRMED', 'CONFIRMED'))
_E_RETENTION_RECEIPT_STATUS = frozenset(('COMPLETED', 'REJECTED'))
_E_STORAGE_VERIFICATION_STATUS = frozenset(('VERIFIED', 'REJECTED'))
_E_STORAGE_PRINCIPAL = frozenset(('EFFECTIVE_USER', 'SYSTEM'))
_E_CONTEXT_FIELD = frozenset(('INPUT_STATE', 'ACTUAL_STATE', 'SELECTED_TARGET', 'ELIGIBLE_TARGETS', 'CODEWORD_CHAIN', 'ADMISSIBILITY_STATUS', 'TRANSFORMATION_COMPATIBILITY', 'NORMALIZATION_STATUS', 'RECOVERABILITY_RELEVANCE', 'IS_VALID', 'ORBIT_INFO', 'SYSTEM_STATE_CLASS', 'RECOVERY_CATEGORY', 'PREDICATE_NAME', 'PREDICATE_VALUE', 'CANDIDATE_ORDER_INDEX', 'STEP_INDEX', 'PROFILE_REFERENCE', 'SOURCE_EVIDENCE_REFERENCE', 'FIXTURE_REFERENCE', 'PROFILE_EVIDENCE_REFERENCE', 'ORIGINAL_ASSESSMENT_REFERENCE', 'POST_ASSESSMENT_REFERENCE', 'RECOVERY_DIAGNOSTIC_REFERENCE', 'BEFORE_STATE', 'CODEWORD', 'AFTER_STATE', 'POLICY_REFERENCE', 'VALIDATION_STATUS', 'FAILED_FIELD', 'PROOF_EVIDENCE_REFERENCE', 'RECOVERY_SAFETY_EVIDENCE_REFERENCE'))
_E_INPUT_FAILURE = frozenset(('INPUT_DEPTH_LIMIT', 'INPUT_JSON_DUPLICATE_KEY', 'INPUT_JSON_INVALID', 'INPUT_JSON_NONFINITE', 'INPUT_KIND_UNSUPPORTED', 'INPUT_NUMERIC_TOKEN_INVALID', 'INPUT_RECORD_INVALID', 'INPUT_RECORD_KEY_INVALID', 'INPUT_RECORD_SIZE_LIMIT', 'INPUT_SIGNATURE_INVALID', 'INPUT_SIZE_LIMIT', 'INPUT_STATE_SPACE_INVALID', 'INPUT_TOKEN_LIMIT', 'INPUT_UTF8_INVALID', 'STATE_COORDINATE_TYPE', 'STATE_COORDINATE_VALUE', 'STATE_WIDTH'))
_E_DIAGNOSTICS_FAILURE = frozenset(('DIAGNOSTICS_VALUE_INVALID', 'DIAGNOSTICS_CONFIG_INVALID', 'DIAGNOSTICS_ORIGIN_UNAVAILABLE', 'DIAGNOSTICS_ORIGIN_MISMATCH', 'DIAGNOSTICS_RESERVATION_REFUSED', 'DIAGNOSTICS_EVENT_TOO_LARGE', 'DIAGNOSTICS_ALIAS_LIMIT', 'DIAGNOSTICS_BYTE_LIMIT', 'DIAGNOSTICS_DURATION_LIMIT', 'DIAGNOSTICS_SEQUENCE_LIMIT', 'DIAGNOSTICS_RECORD_NONCONFORMANT', 'DIAGNOSTICS_REQUIRED_STEP_MISSING', 'DIAGNOSTICS_META_UNAVAILABLE', 'DIAGNOSTICS_COLLECTOR_FAILURE', 'STORAGE_PROTECTION_UNAVAILABLE', 'STORAGE_PARENT_UNTRUSTED', 'STORAGE_IDENTITY_CHANGED', 'STORAGE_REPARSE_REFUSED', 'STORAGE_PATH_ALREADY_EXISTS', 'STORAGE_COMMIT_REJECTED', 'STORAGE_COMMIT_UNCONFIRMED', 'EXPORT_SNAPSHOT_INVALID', 'EXPORT_REDACTION_FAILED', 'EXPORT_JSON_FAILED', 'EXPORT_MARKDOWN_FAILED', 'EXPORT_MANIFEST_FAILED', 'EXPORT_PUBLICATION_FAILED', 'EXPORT_BYTE_LIMIT', 'EXPORT_PARITY_FAILED', 'DIAGNOSTICS_COMPLETION_MISSING', 'DIAGNOSTICS_COMPLETION_MISMATCH', 'DIAGNOSTICS_REPLAY_REFUSED', 'DIAGNOSTICS_SUPPORTING_LIMIT', 'DIAGNOSTICS_INCIDENT_LIMIT', 'DIAGNOSTICS_RAW_PACKET_LIMIT', 'EXPORT_SLOT_OCCUPIED', 'DIAGNOSTICS_CLOCK_UNAVAILABLE', 'DIAGNOSTICS_CLOCK_REGRESSION', 'DIAGNOSTICS_COUNTER_LIMIT'))
_E_PROFILE_AVAILABILITY = frozenset(('AVAILABLE', 'UNAVAILABLE'))
_E_SAFE_INPUT_KIND = frozenset(('ASH_STATE', 'REJECTED'))
_E_PREDICATE_EVALUATION = frozenset(('EVALUATED', 'NOT_EVALUATED'))
_E_RECOVERY_STEP_KIND = frozenset(('NORMALIZE', 'CORRECT', 'APPLICABILITY', 'ADDITIONAL_VALIDATION', 'SELECT_FALLBACK', 'VALIDATE_RECOVERY', 'VALIDATE_FALLBACK', 'CANDIDATE_DECISION', 'HANDOFF', 'SUMMARY'))
_E_COUNTER_FIELD = frozenset(('ACCEPTED', 'REJECTED', 'RETAINED', 'EXPIRED', 'LOST', 'REDACTED_FIELDS', 'REDACTED_REFERENCES', 'META_OVERFLOW'))
_E_COUNTER_STATUS = frozenset(('EXACT', 'SATURATED', 'UNAVAILABLE'))
_E_COUNTER_REASON = frozenset(('COUNTER_LIMIT', 'STORAGE_UNCONFIRMED'))
_E_ADMISSION_STATUS = frozenset(('CONFIRMED', 'REJECTED', 'NOT_CONFIRMED'))
_E_PROOF_STATUS = frozenset(('NOT_EVALUATED', 'VERIFIED', 'REJECTED'))
_E_NORMALIZATION_DECISION = frozenset(('ALREADY_VALID', 'PLAN_READY', 'NOT_NORMALIZABLE', 'BLOCKED'))
_E_PREPARATION_STATUS = frozenset(('READY', 'UNAVAILABLE', 'REJECTED'))
_E_STEP_STATUS = frozenset(('COMPLETED', 'BLOCKED', 'FAILED'))
_E_VALIDATION_FIELD = frozenset(('ORIGINAL_SOURCE', 'ORIGINAL_PROFILE', 'ORIGINAL_DIAGNOSIS', 'ORIGINAL_ASSESSMENT', 'ORIGIN_PROFILE', 'ORIGIN_SOURCE', 'SUBMITTED_SOURCE', 'SUBMITTED_PROFILE', 'TARGET_SET', 'SELECTED_TARGET', 'CODEWORD_CHAIN', 'REGISTRY_SOURCE', 'REGISTRY_PROFILE', 'CERTIFICATION_INVENTORY', 'CERTIFICATION_STATE', 'POST_VALIDATION', 'INPUT', 'UNKNOWN_REGISTERED_FIELD'))
_E_ESCALATION_POLICY = frozenset(('TRY_NEXT', 'ESCALATE_TO_CONTAINMENT'))
_E_PREDICATE_PHASE = frozenset(('APPLICABILITY', 'ADDITIONAL_VALIDATION'))
_E_PREDICATE_OBSERVATION_STATUS = frozenset(('TRUE', 'FALSE', 'UNAVAILABLE'))
_E_SUPPORTING_KIND = frozenset(('CANONICAL_SOURCE', 'PROFILE', 'ASSESSMENT', 'RECOVERY_DIAGNOSTIC', 'NORMALIZATION_PROOF', 'CORRECTION_PROOF', 'REGISTRY_PROOF', 'CONDITION', 'PREDICATE_OBSERVATION', 'RECOVERY_SAFETY', 'TARGET_VALIDITY'))
_E_COMPLETION_STATUS = frozenset(('COMPLETE', 'INCOMPLETE'))
_E_PROPAGATION_STATUS = frozenset(('SAFE', 'RISK', 'UNAVAILABLE'))
_E_AUTHORITY_STATUS = frozenset(('REACHABLE', 'UNREACHABLE', 'UNAVAILABLE'))
_E_DIRECTIVE_ACTION = frozenset(('ENTER_CONTAINMENT', 'REQUEST_EXTERNAL_AUTHORITY', 'ENTER_SAFE_HALT', 'REMAIN_CONTAINED', 'REMAIN_SAFE_HALT'))
_E_REQUEST_ORIGIN = frozenset(('POLICY', 'SOURCE_RECOVERABILITY', 'OBSERVED_EXISTING_MODE'))
_E_CANONICAL_CONTAINMENT_TRIGGER = frozenset(('FALLBACK_FAILURE', 'PROPAGATION_RISK', 'OPERATOR_REQUEST', 'RECOVERY_VALIDATION_FAILURE'))
_E_CANONICAL_SAFE_HALT_TRIGGER = frozenset(('ESCALATION_FROM_FAILED', 'CONTAINMENT_BREACH', 'OPERATOR_HALT_REQUEST', 'POLICY_HALT_REQUEST', 'UNRESOLVABLE_BLOCKED_RECOVERY'))
_E_EXISTING_MODE_CLASS = frozenset(('CONTAINED', 'SAFE_HALT'))
_E_CAPTURE_OBJECT_KIND = frozenset(('EVENT', 'SUPPORTING'))
_E_CAPTURE_REMOVAL_STATUS = frozenset(('REMOVED', 'NOT_REMOVED', 'UNCONFIRMED'))
_E_CAPTURE_PURGE_STATUS = frozenset(('COMPLETED', 'PARTIAL', 'REJECTED'))

ENUMS = (('SourceStatus', ('VERIFIED_CLEAN', 'VERIFIED_DIRTY', 'UNKNOWN')), ('UnavailableReason', ('NOT_MEASURED', 'NOT_PROVIDED', 'EXCLUDED_REFERENCE_SCOPE', 'NOT_IMPLEMENTED', 'SOURCE_NOT_VERIFIED', 'CLOCK_UNAVAILABLE', 'LOSS_UNCONFIRMED', 'RETENTION_EXPIRED', 'STORAGE_UNAVAILABLE', 'CLOCK_REGRESSION', 'DURATION_LIMIT', 'COUNTER_LIMIT')), ('OperatingSystem', ('WINDOWS', 'LINUX', 'MACOS', 'UNKNOWN')), ('Architecture', ('X86_64', 'ARM64', 'UNKNOWN')), ('HostClass', ('HOST', 'VM', 'SIMULATOR', 'UNKNOWN')), ('Implementation', ('REFERENCE_DEVELOPMENT_DIAGNOSTICS', 'REFERENCE_RELEASE_DIAGNOSTICS')), ('ProfileId', ('REFERENCE_DEVELOPMENT', 'REFERENCE_RELEASE')), ('CoverageSource', ('STATE_MODEL', 'NORMALIZATION', 'RECOVERY_ENGINE', 'DIAGNOSTICS', 'PROTECTED_STORAGE', 'PAIRED_EXPORT', 'REALM_ENCODER', 'TRANSITION_REGISTRY', 'TOPOLOGY_GENERATOR', 'AXIOM_EVALUATOR', 'GENERATION_PLANNER', 'ARTIFACT_EMITTER', 'NATIVE_RUNTIME', 'NATIVE_RELEASE', 'PHYSICAL_CRASH', 'ENVIRONMENT_OS', 'RUNTIME_VERSION', 'ARCHITECTURE', 'HOST_CLASS', 'UTC_CLOCK', 'MONOTONIC_CLOCK')), ('CoverageStatus', ('AVAILABLE', 'UNAVAILABLE', 'EXCLUDED')), ('OverallCoverage', ('COMPLETE_DECLARED_REFERENCE_SCOPE', 'PARTIAL', 'UNAVAILABLE')), ('RetentionReason', ('EXPLICIT_PURGE', 'DURATION_EXPIRED', 'WHOLE_OPERATION_ROTATION', 'UNCERTAIN_STORAGE_RANGE')), ('StorageState', ('PROTECTED_VERIFIED', 'UNAVAILABLE', 'UNCERTAIN')), ('CanonicalKind', ('STATE_VALIDITY', 'RECOVERY', 'FALLBACK', 'CONTAINMENT', 'SAFE_HALT')), ('CanonicalSeverity', ('INFO', 'WARNING', 'ERROR', 'CRITICAL')), ('CanonicalStage', ('DETECTION', 'CLASSIFICATION', 'RECOVERY', 'ESCALATION', 'TERMINAL')), ('CanonicalDisposition', ('RESOLVED', 'PENDING', 'BLOCKED', 'ESCALATED', 'TERMINAL')), ('CanonicalRule', ('ASH-STATE-STRUCTURE-001', 'ASH-STATE-VALIDITY-001', 'ASH-STATE-GENERAL-001', 'ASH-CODEWORD-STRUCTURE-001', 'ASH-ADMISSIBILITY-CLASSIFICATION-001', 'ASH-CLASSIFICATION-MAPPING-001', 'ASH-RECOVERY-ACTION-001', 'ASH-FALLBACK-SELECTION-001', 'ASH-CONTAINMENT-TRIGGER-001', 'ASH-HALT-TRIGGER-001')), ('Admissibility', ('VALID', 'TRANSFORMATION_COMPATIBLE', 'TRANSFORMATION_INCOMPATIBLE', 'UNCLASSIFIED')), ('Compatibility', ('COMPATIBLE', 'INCOMPATIBLE', 'UNKNOWN')), ('NormalizationStatus', ('ALREADY_VALID', 'NORMALIZABLE', 'NOT_NORMALIZABLE', 'BLOCKED')), ('RecoverabilityRelevance', ('NO_RECOVERY_NEEDED', 'RECOVERY_APPLICABLE', 'NOT_RECOVERABLE', 'CONTAINMENT_NEEDED')), ('SystemClass', ('STABLE', 'UNSTABLE', 'CORRECTABLE', 'DEGRADED', 'CONTAINED', 'FAILED', 'SAFE_HALT')), ('RecoveryCategory', ('NO_ACTION', 'NORMALIZE_STATE', 'APPLY_CORRECTION', 'FALLBACK_REQUIRED', 'CONTAINMENT_REQUIRED', 'ESCALATION_REQUIRED', 'TERMINAL_NO_RECOVERY')), ('PredicateName', ('CORRECTION_PATH_IS_KNOWN', 'FALLBACK_IS_AVAILABLE', 'APPLICABILITY', 'ADDITIONAL_VALIDATION')), ('Producer', ('STATE_MODEL', 'NORMALIZATION', 'RECOVERY_ENGINE', 'DIAGNOSTICS', 'REFERENCE_HOST')), ('EventType', ('SESSION_START', 'SESSION_END', 'DIAGNOSTIC', 'OPERATION_ADMITTED', 'OPERATION_COMPLETED', 'ACTION_OBSERVED', 'INCIDENT', 'META_DIAGNOSTIC', 'HEALTH', 'RETENTION', 'EXPORT')), ('MessageTemplate', ('SESSION_OPENED', 'SESSION_CLOSED', 'ORIGIN_ATTACHED', 'DIAGNOSIS_RECORDED', 'CLASSIFICATION_RECORDED', 'NORMALIZATION_COMPUTED', 'POST_VALIDATION_RECORDED', 'RECOVERY_ACTION_RECORDED', 'RECOVERY_REFUSED', 'RECOVERY_HANDOFF_RECORDED', 'DIAGNOSTIC_NONCONFORMANCE', 'CAPTURE_UNCONFIRMED', 'RETENTION_REPORTED', 'EXPORT_COMPLETE', 'EXPORT_INCOMPLETE', 'UNTRUSTED_PROSE_OMITTED')), ('ObservedOutcome', ('OBSERVED', 'NOT_EVALUATED', 'COMPLETED', 'FAILED', 'BLOCKED', 'NOT_APPLICABLE', 'ALREADY_VALID', 'NORMALIZED', 'NOT_NORMALIZABLE', 'RECOVERED', 'RECOVERED_VIA_FALLBACK', 'RECOVERY_FAILED', 'ESCALATE_TO_CONTAINMENT', 'CONTAINMENT_HANDOFF', 'HALT_HANDOFF', 'TERMINAL_REFUSAL', 'CONFIRMED', 'REJECTED', 'NOT_CONFIRMED', 'INCOMPLETE')), ('FailureDomain', ('INPUT', 'STATE', 'NORMALIZATION', 'RECOVERY', 'DIAGNOSTICS', 'STORAGE', 'EXPORT')), ('SafeFailure', ('SOURCE_REPORTED_FAILURE', 'ORIGINAL_PROFILE_MISMATCH', 'ORIGINAL_SOURCE_MISMATCH', 'ORIGINAL_DIAGNOSIS_MISMATCH', 'PLAN_TARGET_SET_MISMATCH', 'PLAN_SELECTION_MISMATCH', 'PLAN_CODEWORD_MISMATCH', 'INPUT_REJECTED', 'PROFILE_UNAVAILABLE', 'NO_TARGET', 'POST_VALIDATION_FAILED', 'CAPTURE_REJECTED', 'CAPTURE_UNCONFIRMED', 'REGISTRY_UNAVAILABLE', 'NO_APPLICABLE_POLICY', 'CORRECTION_PROVIDER_UNAVAILABLE', 'CORRECTION_PROOF_INVALID', 'NONCONFORMANT_DIAGNOSTIC', 'MISSING_REQUIRED_STEP', 'STORAGE_FAILURE', 'EXPORT_FAILURE')), ('SafeField', ('ORIGINAL_SOURCE', 'ORIGINAL_PROFILE', 'ORIGINAL_DIAGNOSIS', 'ORIGINAL_ASSESSMENT', 'TARGET_SET', 'SELECTED_TARGET', 'CODEWORD_CHAIN', 'INPUT', 'POST_VALIDATION', 'CAPTURE', 'REGISTRY', 'APPLICABILITY', 'ADDITIONAL_VALIDATION', 'CANONICAL_ENVELOPE', 'CHAIN', 'EXPECTED_STEP', 'STORE', 'EXPORT_PART')), ('FactType', ('ACTUAL_STATE_RETAINED', 'STEP_COMPLETED', 'POST_STATE_VALID', 'POST_STATE_NOT_VALID', 'CAPTURE_CONFIRMED', 'CAPTURE_NOT_CONFIRMED', 'ORIGIN_BINDING_DIFFERED', 'PLAN_PROOF_DIFFERED', 'REGISTRY_UNAVAILABLE', 'NO_CANDIDATE_APPLICABLE', 'REQUIRED_STEP_MISSING', 'WHOLE_PAIR_COMPLETED', 'PAIR_INCOMPLETE')), ('ExpectedInvariant', ('VALID_RETURN', 'STABLE_RETURN', 'ACKNOWLEDGED_STEPS', 'NO_EFFECTS_ON_REFUSAL', 'COMPLETE_CHAIN', 'PAIRED_EXPORT', 'SAFE_PROJECTION')), ('UnknownCause', ('NO_SUPPORTED_CAUSE', 'STORAGE_COMMIT_UNCONFIRMED', 'CLOCK_NOT_MEASURED', 'EXTERNAL_COLLECTOR_TRUTH_NOT_VERIFIED', 'NATIVE_RUNTIME_NOT_REALIZED', 'PHYSICAL_CRASH_NOT_EXERCISED')), ('PinnedSource', ('YWE_IMPLEMENTATION', 'ASH_AGGREGATE', 'ASH_STATE_SPACE', 'ASH_CODEWORDS', 'ASH_VALIDITY', 'ASH_CLASSIFICATION', 'ASH_RECOVERY', 'ASH_DIAGNOSTIC_SCHEMA', 'ASH_TAXONOMY', 'RAVEN_POLICY', 'YWE_NORMALIZATION_POLICY')), ('OmissionCategory', ('SUMMARY', 'NOTES', 'CALLER_REFERENCE', 'PROFILE_ID', 'UNVERIFIED_SOURCE_DIGEST', 'EVIDENCE_REFERENCE', 'INPUT_PREVIEW', 'NON_BIT_SCALAR', 'URL', 'QUERY', 'HEADER', 'BODY', 'EXCEPTION_TEXT', 'CAUSAL_TEXT', 'STACK', 'ABSOLUTE_PATH', 'ATTACHMENT', 'UNREGISTERED_PAYLOAD', 'HYPOTHESIS')), ('RedactionReason', ('UNTRUSTED_FREEFORM', 'OPAQUE_REFERENCE_ALIAS', 'UNSUPPORTED_SOURCE', 'SENSITIVE_CONTENT', 'EXCLUDED_REFERENCE_SCOPE')), ('LimitationCode', ('REFERENCE_IMPLEMENTATION_ONLY', 'DECLARED_PRODUCERS_ONLY', 'TRUSTED_CAPTURE_CONTRACT', 'NO_REMOTE_ACK_AUTHENTICATION', 'NATIVE_COMPOSITION_DEFERRED', 'NATIVE_RELEASE_DEFERRED', 'NO_PHYSICAL_CRASH_PROOF', 'NO_POWER_LOSS_DURABILITY_PROOF', 'NO_ENCRYPTION_CLAIM', 'NO_SECOND_USER_ACCESS_TEST', 'NO_AMBIENT_ACTIVITY_CAPTURE', 'UNTRUSTED_PROSE_OMITTED', 'LOSS_RANGE_COALESCED', 'PARENT_STORAGE_NOT_VERIFIED')), ('MetaCauseCode', ('REQUIRED_FIELD_MISSING', 'SCHEMA_NONCONFORMANCE', 'RULE_NOT_APPROVED', 'DUPLICATE_REFERENCE', 'PARENT_MISMATCH', 'ROOT_MISMATCH', 'SUBJECT_MISMATCH', 'STAGE_REGRESSION', 'TERMINAL_SUCCESSOR', 'REQUIRED_STEP_MISSING', 'PRODUCER_PAYLOAD_MISMATCH', 'CLOCK_UNAVAILABLE', 'CLOCK_REGRESSION', 'DURATION_EXPIRED', 'COUNTER_LIMIT', 'MAIN_CAPACITY_EXHAUSTED', 'COMPLETION_MISSING')), ('ExpectedPhase', ('DETECTION', 'CLASSIFICATION', 'COMPUTATION', 'POST_VALIDATION', 'RECOVERY_PREDICATE', 'RECOVERY_STEP', 'RECOVERY_POST_ASSESSMENT', 'BOUNDARY_HANDOFF')), ('StorageCommitStatus', ('COMMITTED', 'REJECTED', 'UNKNOWN')), ('ExportPart', ('JSON', 'MARKDOWN', 'MANIFEST', 'PUBLICATION')), ('PartName', ('diagnostics.json', 'diagnostics.md', 'manifest.json')), ('PartStatus', ('NOT_WRITTEN', 'WRITTEN_UNCONFIRMED', 'CONFIRMED')), ('RetentionReceiptStatus', ('COMPLETED', 'REJECTED')), ('StorageVerificationStatus', ('VERIFIED', 'REJECTED')), ('StoragePrincipal', ('EFFECTIVE_USER', 'SYSTEM')), ('ContextField', ('INPUT_STATE', 'ACTUAL_STATE', 'SELECTED_TARGET', 'ELIGIBLE_TARGETS', 'CODEWORD_CHAIN', 'ADMISSIBILITY_STATUS', 'TRANSFORMATION_COMPATIBILITY', 'NORMALIZATION_STATUS', 'RECOVERABILITY_RELEVANCE', 'IS_VALID', 'ORBIT_INFO', 'SYSTEM_STATE_CLASS', 'RECOVERY_CATEGORY', 'PREDICATE_NAME', 'PREDICATE_VALUE', 'CANDIDATE_ORDER_INDEX', 'STEP_INDEX', 'PROFILE_REFERENCE', 'SOURCE_EVIDENCE_REFERENCE', 'FIXTURE_REFERENCE', 'PROFILE_EVIDENCE_REFERENCE', 'ORIGINAL_ASSESSMENT_REFERENCE', 'POST_ASSESSMENT_REFERENCE', 'RECOVERY_DIAGNOSTIC_REFERENCE', 'BEFORE_STATE', 'CODEWORD', 'AFTER_STATE', 'POLICY_REFERENCE', 'VALIDATION_STATUS', 'FAILED_FIELD', 'PROOF_EVIDENCE_REFERENCE', 'RECOVERY_SAFETY_EVIDENCE_REFERENCE')), ('InputFailure', ('INPUT_DEPTH_LIMIT', 'INPUT_JSON_DUPLICATE_KEY', 'INPUT_JSON_INVALID', 'INPUT_JSON_NONFINITE', 'INPUT_KIND_UNSUPPORTED', 'INPUT_NUMERIC_TOKEN_INVALID', 'INPUT_RECORD_INVALID', 'INPUT_RECORD_KEY_INVALID', 'INPUT_RECORD_SIZE_LIMIT', 'INPUT_SIGNATURE_INVALID', 'INPUT_SIZE_LIMIT', 'INPUT_STATE_SPACE_INVALID', 'INPUT_TOKEN_LIMIT', 'INPUT_UTF8_INVALID', 'STATE_COORDINATE_TYPE', 'STATE_COORDINATE_VALUE', 'STATE_WIDTH')), ('DiagnosticsFailure', ('DIAGNOSTICS_VALUE_INVALID', 'DIAGNOSTICS_CONFIG_INVALID', 'DIAGNOSTICS_ORIGIN_UNAVAILABLE', 'DIAGNOSTICS_ORIGIN_MISMATCH', 'DIAGNOSTICS_RESERVATION_REFUSED', 'DIAGNOSTICS_EVENT_TOO_LARGE', 'DIAGNOSTICS_ALIAS_LIMIT', 'DIAGNOSTICS_BYTE_LIMIT', 'DIAGNOSTICS_DURATION_LIMIT', 'DIAGNOSTICS_SEQUENCE_LIMIT', 'DIAGNOSTICS_RECORD_NONCONFORMANT', 'DIAGNOSTICS_REQUIRED_STEP_MISSING', 'DIAGNOSTICS_META_UNAVAILABLE', 'DIAGNOSTICS_COLLECTOR_FAILURE', 'STORAGE_PROTECTION_UNAVAILABLE', 'STORAGE_PARENT_UNTRUSTED', 'STORAGE_IDENTITY_CHANGED', 'STORAGE_REPARSE_REFUSED', 'STORAGE_PATH_ALREADY_EXISTS', 'STORAGE_COMMIT_REJECTED', 'STORAGE_COMMIT_UNCONFIRMED', 'EXPORT_SNAPSHOT_INVALID', 'EXPORT_REDACTION_FAILED', 'EXPORT_JSON_FAILED', 'EXPORT_MARKDOWN_FAILED', 'EXPORT_MANIFEST_FAILED', 'EXPORT_PUBLICATION_FAILED', 'EXPORT_BYTE_LIMIT', 'EXPORT_PARITY_FAILED', 'DIAGNOSTICS_COMPLETION_MISSING', 'DIAGNOSTICS_COMPLETION_MISMATCH', 'DIAGNOSTICS_REPLAY_REFUSED', 'DIAGNOSTICS_SUPPORTING_LIMIT', 'DIAGNOSTICS_INCIDENT_LIMIT', 'DIAGNOSTICS_RAW_PACKET_LIMIT', 'EXPORT_SLOT_OCCUPIED', 'DIAGNOSTICS_CLOCK_UNAVAILABLE', 'DIAGNOSTICS_CLOCK_REGRESSION', 'DIAGNOSTICS_COUNTER_LIMIT')), ('ProfileAvailability', ('AVAILABLE', 'UNAVAILABLE')), ('SafeInputKind', ('ASH_STATE', 'REJECTED')), ('PredicateEvaluation', ('EVALUATED', 'NOT_EVALUATED')), ('RecoveryStepKind', ('NORMALIZE', 'CORRECT', 'APPLICABILITY', 'ADDITIONAL_VALIDATION', 'SELECT_FALLBACK', 'VALIDATE_RECOVERY', 'VALIDATE_FALLBACK', 'CANDIDATE_DECISION', 'HANDOFF', 'SUMMARY')), ('CounterField', ('ACCEPTED', 'REJECTED', 'RETAINED', 'EXPIRED', 'LOST', 'REDACTED_FIELDS', 'REDACTED_REFERENCES', 'META_OVERFLOW')), ('CounterStatus', ('EXACT', 'SATURATED', 'UNAVAILABLE')), ('CounterReason', ('COUNTER_LIMIT', 'STORAGE_UNCONFIRMED')), ('AdmissionStatus', ('CONFIRMED', 'REJECTED', 'NOT_CONFIRMED')), ('ProofStatus', ('NOT_EVALUATED', 'VERIFIED', 'REJECTED')), ('NormalizationDecision', ('ALREADY_VALID', 'PLAN_READY', 'NOT_NORMALIZABLE', 'BLOCKED')), ('PreparationStatus', ('READY', 'UNAVAILABLE', 'REJECTED')), ('StepStatus', ('COMPLETED', 'BLOCKED', 'FAILED')), ('ValidationField', ('ORIGINAL_SOURCE', 'ORIGINAL_PROFILE', 'ORIGINAL_DIAGNOSIS', 'ORIGINAL_ASSESSMENT', 'ORIGIN_PROFILE', 'ORIGIN_SOURCE', 'SUBMITTED_SOURCE', 'SUBMITTED_PROFILE', 'TARGET_SET', 'SELECTED_TARGET', 'CODEWORD_CHAIN', 'REGISTRY_SOURCE', 'REGISTRY_PROFILE', 'CERTIFICATION_INVENTORY', 'CERTIFICATION_STATE', 'POST_VALIDATION', 'INPUT', 'UNKNOWN_REGISTERED_FIELD')), ('EscalationPolicy', ('TRY_NEXT', 'ESCALATE_TO_CONTAINMENT')), ('PredicatePhase', ('APPLICABILITY', 'ADDITIONAL_VALIDATION')), ('PredicateObservationStatus', ('TRUE', 'FALSE', 'UNAVAILABLE')), ('SupportingKind', ('CANONICAL_SOURCE', 'PROFILE', 'ASSESSMENT', 'RECOVERY_DIAGNOSTIC', 'NORMALIZATION_PROOF', 'CORRECTION_PROOF', 'REGISTRY_PROOF', 'CONDITION', 'PREDICATE_OBSERVATION', 'RECOVERY_SAFETY', 'TARGET_VALIDITY')), ('CompletionStatus', ('COMPLETE', 'INCOMPLETE')), ('PropagationStatus', ('SAFE', 'RISK', 'UNAVAILABLE')), ('AuthorityStatus', ('REACHABLE', 'UNREACHABLE', 'UNAVAILABLE')), ('DirectiveAction', ('ENTER_CONTAINMENT', 'REQUEST_EXTERNAL_AUTHORITY', 'ENTER_SAFE_HALT', 'REMAIN_CONTAINED', 'REMAIN_SAFE_HALT')), ('RequestOrigin', ('POLICY', 'SOURCE_RECOVERABILITY', 'OBSERVED_EXISTING_MODE')), ('CanonicalContainmentTrigger', ('FALLBACK_FAILURE', 'PROPAGATION_RISK', 'OPERATOR_REQUEST', 'RECOVERY_VALIDATION_FAILURE')), ('CanonicalSafeHaltTrigger', ('ESCALATION_FROM_FAILED', 'CONTAINMENT_BREACH', 'OPERATOR_HALT_REQUEST', 'POLICY_HALT_REQUEST', 'UNRESOLVABLE_BLOCKED_RECOVERY')), ('ExistingModeClass', ('CONTAINED', 'SAFE_HALT')), ('CaptureObjectKind', ('EVENT', 'SUPPORTING')), ('CaptureRemovalStatus', ('REMOVED', 'NOT_REMOVED', 'UNCONFIRMED')), ('CapturePurgeStatus', ('COMPLETED', 'PARTIAL', 'REJECTED')))
MESSAGE_TEMPLATES = (('SESSION_OPENED', 'Reference diagnostic session opened; capture is limited to the declared producers.'), ('SESSION_CLOSED', 'Reference diagnostic session closed; retained evidence and coverage limitations remain explicit.'), ('ORIGIN_ATTACHED', 'The exact previously confirmed origin was attached by this collector; no origin record was emitted again.'), ('DIAGNOSIS_RECORDED', 'State validity was diagnosed under the explicit complete source and profile bindings.'), ('CLASSIFICATION_RECORDED', 'Contextual classification evaluated only the recorded context and consulted predicates.'), ('NORMALIZATION_COMPUTED', 'Actual full-vector normalization completed; post-validation acknowledgment is pending.'), ('POST_VALIDATION_RECORDED', 'Actual post-operation state was diagnosed and classified in its separately linked assessment chain.'), ('RECOVERY_ACTION_RECORDED', 'The consulted predicate or value step completed with the structured outcome shown in this record.'), ('RECOVERY_REFUSED', 'Recovery was refused before unapproved effects; the original submitted evidence remains retained.'), ('RECOVERY_HANDOFF_RECORDED', 'Only a typed containment or halt request was produced; no runtime mode entry is claimed.'), ('DIAGNOSTIC_NONCONFORMANCE', 'A required diagnostic invariant failed; the related operation or record was not silently accepted.'), ('CAPTURE_UNCONFIRMED', 'Capture did not acknowledge this attempted record; its external persistence remains unconfirmed.'), ('RETENTION_REPORTED', 'A whole declared retention range became unavailable; counts and boundary evidence are retained.'), ('EXPORT_COMPLETE', 'The JSON and Markdown parts and manifest completed for one verified sanitized snapshot.'), ('EXPORT_INCOMPLETE', 'The paired diagnostic export did not complete; retained part status and failure evidence are explicit.'), ('UNTRUSTED_PROSE_OMITTED', 'Untrusted producer prose, previews, paths and exception material were omitted before persistence.'))

class DiagnosticsContractError(ValueError):
    def __init__(self, code, failed_field=None):
        if type(code) is not str or code not in _E_DIAGNOSTICS_FAILURE:
            raise ValueError("unknown Diagnostics failure code")
        if failed_field is not None and (type(failed_field) is not str or failed_field not in _E_SAFE_FIELD):
            raise ValueError("unknown Diagnostics failure field")
        self.code = code
        self.failed_field = failed_field
        super().__init__(code if failed_field is None else code + ": " + failed_field)


def _invalid():
    raise DiagnosticsContractError("DIAGNOSTICS_VALUE_INVALID")


def _string(value, pattern, maximum):
    if type(value) is not str or len(value) > maximum or re.fullmatch(pattern, value, flags=re.ASCII) is None:
        _invalid()


def _reference(value, maximum=256):
    _string(value, r"[A-Za-z0-9][A-Za-z0-9._:/-]{0," + str(maximum - 1) + r"}", maximum)
    if value in ("NONE", "SELF"):
        _invalid()


def _enum(value, choices):
    if type(value) is not str or value not in choices:
        _invalid()


def _integer(value, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        _invalid()


def _boolean(value):
    if type(value) is not bool:
        _invalid()


def _owned(value, kind):
    if type(value) is not kind:
        _invalid()


def _union(value, strings, kinds):
    if type(value) is str and value in strings:
        return
    if any(type(value) is kind for kind in kinds):
        return
    _invalid()


def _tuple(value, minimum, maximum, check):
    if type(value) is not tuple and type(value) is not list:
        _invalid()
    if not minimum <= len(value) <= maximum:
        _invalid()
    for item in value:
        check(item)
    return tuple(value)


def _utc(value):
    _string(value, r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z", 27)
    try:
        datetime(int(value[:4]), int(value[5:7]), int(value[8:10]), int(value[11:13]), int(value[14:16]), int(value[17:19]), int(value[20:26]))
    except ValueError:
        _invalid()


def _template(value):
    if type(value) is not str or value not in tuple(text for _, text in MESSAGE_TEMPLATES):
        _invalid()


def _record_value(value):
    if value is None or type(value) is str or type(value) is int or type(value) is bool:
        return value
    if type(value) is tuple:
        return [_record_value(item) for item in value]
    if any(type(value) is kind for kind in VALUE_TYPES):
        return value.to_record()
    _invalid()


def enum_values(name):
    if type(name) is not str:
        _invalid()
    for key, values in ENUMS:
        if name == key:
            return values
    _invalid()


def message_text(name):
    if type(name) is not str:
        _invalid()
    for key, value in MESSAGE_TEMPLATES:
        if name == key:
            return value
    _invalid()


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    status: str
    verified_revision: str | None
    dirty_path_aliases: tuple
    unavailable_reason: str | None

    def __post_init__(self):
        _enum(self.status, _E_SOURCE_STATUS)
        if self.verified_revision is not None:
            _string(self.verified_revision, r"[0-9a-f]{40}", 40)
        object.__setattr__(self, "dirty_path_aliases", _tuple(self.dirty_path_aliases, 0, 128, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        if self.unavailable_reason is not None:
            _enum(self.unavailable_reason, _E_UNAVAILABLE_REASON)
        _coherent(self)

    def to_record(self):
        return {
            "status": _record_value(self.status),
            "verified_revision": _record_value(self.verified_revision),
            "dirty_path_aliases": _record_value(self.dirty_path_aliases),
            "unavailable_reason": _record_value(self.unavailable_reason),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticsEnvironment:
    os_kind: str
    runtime_kind: ClassVar[object] = 'PYTHON_REFERENCE'
    runtime_version: tuple | None
    architecture: str
    host_class: str
    unavailable_fields: tuple

    def __post_init__(self):
        _enum(self.os_kind, _E_OPERATING_SYSTEM)
        if self.runtime_version is not None:
            object.__setattr__(self, "runtime_version", _tuple(self.runtime_version, 3, 3, lambda item: _integer(item, 0, 4294967295)))
        _enum(self.architecture, _E_ARCHITECTURE)
        _enum(self.host_class, _E_HOST_CLASS)
        object.__setattr__(self, "unavailable_fields", _tuple(self.unavailable_fields, 0, 8, lambda item: _owned(item, MissingCoverage)))
        _coherent(self)

    def to_record(self):
        return {
            "os_kind": _record_value(self.os_kind),
            "runtime_kind": _record_value(self.runtime_kind),
            "runtime_version": _record_value(self.runtime_version),
            "architecture": _record_value(self.architecture),
            "host_class": _record_value(self.host_class),
            "unavailable_fields": _record_value(self.unavailable_fields),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticsIdentity:
    product_id: ClassVar[object] = 'yggdrasil-world-engine-reference'
    product_version: str
    implementation_id: str
    profile_id: str
    schema_version: ClassVar[object] = '1.0.0'
    build_id: str
    source_revision: str | None
    source_provenance: SourceProvenance
    session_reference: str
    environment: DiagnosticsEnvironment

    def __post_init__(self):
        _enum(self.product_version, ("2.0.23",))
        _enum(self.implementation_id, _E_IMPLEMENTATION)
        _enum(self.profile_id, _E_PROFILE_ID)
        _string(self.build_id, r"ref:[0-9]{6}", 10)
        if self.source_revision is not None:
            _string(self.source_revision, r"[0-9a-f]{40}", 40)
        _owned(self.source_provenance, SourceProvenance)
        _string(self.session_reference, r"ref:[0-9]{6}", 10)
        _owned(self.environment, DiagnosticsEnvironment)
        _coherent(self)

    def to_record(self):
        return {
            "product_id": _record_value(self.product_id),
            "product_version": _record_value(self.product_version),
            "implementation_id": _record_value(self.implementation_id),
            "profile_id": _record_value(self.profile_id),
            "schema_version": _record_value(self.schema_version),
            "build_id": _record_value(self.build_id),
            "source_revision": _record_value(self.source_revision),
            "source_provenance": _record_value(self.source_provenance),
            "session_reference": _record_value(self.session_reference),
            "environment": _record_value(self.environment),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticsProfile:
    profile_id: str
    implementation_id: str
    selection_authority: str
    development_payloads_enabled: bool
    native_release_replacement_status: ClassVar[object] = 'DEFERRED_M10'
    native_release_qualification: ClassVar[object] = 'NOT_VERIFIED'

    def __post_init__(self):
        _enum(self.profile_id, _E_PROFILE_ID)
        _enum(self.implementation_id, _E_IMPLEMENTATION)
        _string(self.selection_authority, r"ref:[0-9]{6}", 10)
        _boolean(self.development_payloads_enabled)
        _coherent(self)

    def to_record(self):
        return {
            "profile_id": _record_value(self.profile_id),
            "implementation_id": _record_value(self.implementation_id),
            "selection_authority": _record_value(self.selection_authority),
            "development_payloads_enabled": _record_value(self.development_payloads_enabled),
            "native_release_replacement_status": _record_value(self.native_release_replacement_status),
            "native_release_qualification": _record_value(self.native_release_qualification),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticLimits:
    event_capacity: ClassVar[object] = 1024
    incident_capacity: ClassVar[object] = 32
    alias_capacity: ClassVar[object] = 6144
    max_event_bytes: ClassVar[object] = 32768
    store_byte_capacity: ClassVar[object] = 33554432
    health_capacity: ClassVar[object] = 16
    max_active_operations: ClassVar[object] = 8
    max_operation_events: ClassVar[object] = 768
    capture_duration_milliseconds: ClassVar[object] = 600000
    supporting_byte_capacity: ClassVar[object] = 2097152
    incident_byte_capacity: ClassVar[object] = 1048576
    alias_byte_capacity: ClassVar[object] = 2097152
    health_byte_capacity: ClassVar[object] = 65536
    inherited_origin_byte_capacity: ClassVar[object] = 65536
    envelope_byte_capacity: ClassVar[object] = 1048576
    max_json_bytes: ClassVar[object] = 33554432
    max_markdown_bytes: ClassVar[object] = 50331648
    max_manifest_bytes: ClassVar[object] = 65536
    max_export_bundles: ClassVar[object] = 1
    protected_disk_byte_capacity: ClassVar[object] = 134217728
    logical_serialized_buffer_capacity: ClassVar[object] = 201326592
    raw_business_packet_byte_capacity: ClassVar[object] = 33554432
    max_meta_records: ClassVar[object] = 16
    max_meta_record_bytes: ClassVar[object] = 3072
    health_status_byte_capacity: ClassVar[object] = 8192
    fallback_health_byte_capacity: ClassVar[object] = 8192

    def __post_init__(self):
        _coherent(self)

    def to_record(self):
        return {
            "event_capacity": _record_value(self.event_capacity),
            "incident_capacity": _record_value(self.incident_capacity),
            "alias_capacity": _record_value(self.alias_capacity),
            "max_event_bytes": _record_value(self.max_event_bytes),
            "store_byte_capacity": _record_value(self.store_byte_capacity),
            "health_capacity": _record_value(self.health_capacity),
            "max_active_operations": _record_value(self.max_active_operations),
            "max_operation_events": _record_value(self.max_operation_events),
            "capture_duration_milliseconds": _record_value(self.capture_duration_milliseconds),
            "supporting_byte_capacity": _record_value(self.supporting_byte_capacity),
            "incident_byte_capacity": _record_value(self.incident_byte_capacity),
            "alias_byte_capacity": _record_value(self.alias_byte_capacity),
            "health_byte_capacity": _record_value(self.health_byte_capacity),
            "inherited_origin_byte_capacity": _record_value(self.inherited_origin_byte_capacity),
            "envelope_byte_capacity": _record_value(self.envelope_byte_capacity),
            "max_json_bytes": _record_value(self.max_json_bytes),
            "max_markdown_bytes": _record_value(self.max_markdown_bytes),
            "max_manifest_bytes": _record_value(self.max_manifest_bytes),
            "max_export_bundles": _record_value(self.max_export_bundles),
            "protected_disk_byte_capacity": _record_value(self.protected_disk_byte_capacity),
            "logical_serialized_buffer_capacity": _record_value(self.logical_serialized_buffer_capacity),
            "raw_business_packet_byte_capacity": _record_value(self.raw_business_packet_byte_capacity),
            "max_meta_records": _record_value(self.max_meta_records),
            "max_meta_record_bytes": _record_value(self.max_meta_record_bytes),
            "health_status_byte_capacity": _record_value(self.health_status_byte_capacity),
            "fallback_health_byte_capacity": _record_value(self.fallback_health_byte_capacity),
        }


@dataclass(frozen=True, slots=True)
class CaptureRelation:
    parent_operation_reference: str
    parent_action_reference: str
    originating_chain_root_reference: str

    def __post_init__(self):
        _string(self.parent_operation_reference, r"ref:[0-9]{6}", 10)
        _string(self.parent_action_reference, r"ref:[0-9]{6}", 10)
        _string(self.originating_chain_root_reference, r"ref:[0-9]{6}", 10)
        _coherent(self)

    def to_record(self):
        return {
            "parent_operation_reference": _record_value(self.parent_operation_reference),
            "parent_action_reference": _record_value(self.parent_action_reference),
            "originating_chain_root_reference": _record_value(self.originating_chain_root_reference),
        }


@dataclass(frozen=True, slots=True)
class MissingCoverage:
    source: str
    status: str
    reason: str | None

    def __post_init__(self):
        _enum(self.source, _E_COVERAGE_SOURCE)
        _enum(self.status, _E_COVERAGE_STATUS)
        if self.reason is not None:
            _enum(self.reason, _E_UNAVAILABLE_REASON)
        _coherent(self)

    def to_record(self):
        return {
            "source": _record_value(self.source),
            "status": _record_value(self.status),
            "reason": _record_value(self.reason),
        }


@dataclass(frozen=True, slots=True)
class RetentionBoundary:
    first_sequence: int
    last_sequence: int
    record_count: int
    reason: str
    coalesced: bool

    def __post_init__(self):
        _integer(self.first_sequence, 0, 18446744073709551615)
        _integer(self.last_sequence, 0, 18446744073709551615)
        _integer(self.record_count, 0, 18446744073709551615)
        _enum(self.reason, _E_RETENTION_REASON)
        _boolean(self.coalesced)
        _coherent(self)

    def to_record(self):
        return {
            "first_sequence": _record_value(self.first_sequence),
            "last_sequence": _record_value(self.last_sequence),
            "record_count": _record_value(self.record_count),
            "reason": _record_value(self.reason),
            "coalesced": _record_value(self.coalesced),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticsHealth:
    coverage_status: str
    accepted_count: int | None
    rejected_count: int | None
    retained_count: int | None
    expired_count: int | None
    lost_count: int | None
    redacted_field_count: int | None
    redacted_reference_count: int | None
    last_confirmed_sequence: int | None
    first_unavailable_sequence: int | None
    last_unavailable_sequence: int | None
    active_reservations: int
    used_bytes: int
    storage_state: str
    last_failure_code: str | None
    missing_sources: tuple
    retention_boundaries: tuple
    range_detail_coalesced: bool
    meta_overflow_count: int | None
    counter_states: tuple
    meta_record_count: int
    meta_storage_state: str
    fallback_cause_code: str | None

    def __post_init__(self):
        _enum(self.coverage_status, _E_OVERALL_COVERAGE)
        if self.accepted_count is not None:
            _integer(self.accepted_count, 0, 18446744073709551615)
        if self.rejected_count is not None:
            _integer(self.rejected_count, 0, 18446744073709551615)
        if self.retained_count is not None:
            _integer(self.retained_count, 0, 18446744073709551615)
        if self.expired_count is not None:
            _integer(self.expired_count, 0, 18446744073709551615)
        if self.lost_count is not None:
            _integer(self.lost_count, 0, 18446744073709551615)
        if self.redacted_field_count is not None:
            _integer(self.redacted_field_count, 0, 18446744073709551615)
        if self.redacted_reference_count is not None:
            _integer(self.redacted_reference_count, 0, 18446744073709551615)
        if self.last_confirmed_sequence is not None:
            _integer(self.last_confirmed_sequence, 0, 18446744073709551615)
        if self.first_unavailable_sequence is not None:
            _integer(self.first_unavailable_sequence, 0, 18446744073709551615)
        if self.last_unavailable_sequence is not None:
            _integer(self.last_unavailable_sequence, 0, 18446744073709551615)
        _integer(self.active_reservations, 0, 8)
        _integer(self.used_bytes, 0, 33554432)
        _enum(self.storage_state, _E_STORAGE_STATE)
        if self.last_failure_code is not None:
            _enum(self.last_failure_code, _E_DIAGNOSTICS_FAILURE)
        object.__setattr__(self, "missing_sources", _tuple(self.missing_sources, 0, 32, lambda item: _owned(item, MissingCoverage)))
        object.__setattr__(self, "retention_boundaries", _tuple(self.retention_boundaries, 0, 16, lambda item: _owned(item, RetentionBoundary)))
        _boolean(self.range_detail_coalesced)
        if self.meta_overflow_count is not None:
            _integer(self.meta_overflow_count, 0, 18446744073709551615)
        object.__setattr__(self, "counter_states", _tuple(self.counter_states, 8, 8, lambda item: _owned(item, DiagnosticCounterState)))
        _integer(self.meta_record_count, 0, 16)
        _enum(self.meta_storage_state, _E_STORAGE_STATE)
        if self.fallback_cause_code is not None:
            _enum(self.fallback_cause_code, _E_META_CAUSE_CODE)
        _coherent(self)

    def to_record(self):
        return {
            "coverage_status": _record_value(self.coverage_status),
            "accepted_count": _record_value(self.accepted_count),
            "rejected_count": _record_value(self.rejected_count),
            "retained_count": _record_value(self.retained_count),
            "expired_count": _record_value(self.expired_count),
            "lost_count": _record_value(self.lost_count),
            "redacted_field_count": _record_value(self.redacted_field_count),
            "redacted_reference_count": _record_value(self.redacted_reference_count),
            "last_confirmed_sequence": _record_value(self.last_confirmed_sequence),
            "first_unavailable_sequence": _record_value(self.first_unavailable_sequence),
            "last_unavailable_sequence": _record_value(self.last_unavailable_sequence),
            "active_reservations": _record_value(self.active_reservations),
            "used_bytes": _record_value(self.used_bytes),
            "storage_state": _record_value(self.storage_state),
            "last_failure_code": _record_value(self.last_failure_code),
            "missing_sources": _record_value(self.missing_sources),
            "retention_boundaries": _record_value(self.retention_boundaries),
            "range_detail_coalesced": _record_value(self.range_detail_coalesced),
            "meta_overflow_count": _record_value(self.meta_overflow_count),
            "counter_states": _record_value(self.counter_states),
            "meta_record_count": _record_value(self.meta_record_count),
            "meta_storage_state": _record_value(self.meta_storage_state),
            "fallback_cause_code": _record_value(self.fallback_cause_code),
        }


@dataclass(frozen=True, slots=True)
class ClockObservation:
    observed_utc: str | None
    monotonic_nanoseconds: int | None
    utc_reason: str | None
    monotonic_reason: str | None

    def __post_init__(self):
        if self.observed_utc is not None:
            _utc(self.observed_utc)
        if self.monotonic_nanoseconds is not None:
            _integer(self.monotonic_nanoseconds, 0, 18446744073709551615)
        if self.utc_reason is not None:
            _enum(self.utc_reason, _E_UNAVAILABLE_REASON)
        if self.monotonic_reason is not None:
            _enum(self.monotonic_reason, _E_UNAVAILABLE_REASON)
        _coherent(self)

    def to_record(self):
        return {
            "observed_utc": _record_value(self.observed_utc),
            "monotonic_nanoseconds": _record_value(self.monotonic_nanoseconds),
            "utc_reason": _record_value(self.utc_reason),
            "monotonic_reason": _record_value(self.monotonic_reason),
        }


@dataclass(frozen=True, slots=True)
class CaptureWindow:
    first_sequence: int | None
    last_sequence: int | None
    start: ClockObservation
    end: ClockObservation

    def __post_init__(self):
        if self.first_sequence is not None:
            _integer(self.first_sequence, 0, 18446744073709551615)
        if self.last_sequence is not None:
            _integer(self.last_sequence, 0, 18446744073709551615)
        _owned(self.start, ClockObservation)
        _owned(self.end, ClockObservation)
        _coherent(self)

    def to_record(self):
        return {
            "first_sequence": _record_value(self.first_sequence),
            "last_sequence": _record_value(self.last_sequence),
            "start": _record_value(self.start),
            "end": _record_value(self.end),
        }


@dataclass(frozen=True, slots=True)
class SafeDiagnosticEnvelope:
    diagnostic_kind: str
    severity: str
    stage: str
    disposition: str
    subject_reference: str
    parent_diagnostic_reference: str | None
    chain_root_reference: str
    rule_ids: tuple
    summary: str
    notes: tuple

    def __post_init__(self):
        _enum(self.diagnostic_kind, _E_CANONICAL_KIND)
        _enum(self.severity, _E_CANONICAL_SEVERITY)
        _enum(self.stage, _E_CANONICAL_STAGE)
        _enum(self.disposition, _E_CANONICAL_DISPOSITION)
        _string(self.subject_reference, r"ref:[0-9]{6}", 10)
        if self.parent_diagnostic_reference is not None:
            _string(self.parent_diagnostic_reference, r"ref:[0-9]{6}", 10)
        _string(self.chain_root_reference, r"ref:[0-9]{6}", 10)
        object.__setattr__(self, "rule_ids", _tuple(self.rule_ids, 1, 10, lambda item: _enum(item, _E_CANONICAL_RULE)))
        _template(self.summary)
        object.__setattr__(self, "notes", _tuple(self.notes, 1, 8, lambda item: _template(item)))
        _coherent(self)

    def to_record(self):
        return {
            "diagnostic_kind": _record_value(self.diagnostic_kind),
            "severity": _record_value(self.severity),
            "stage": _record_value(self.stage),
            "disposition": _record_value(self.disposition),
            "subject_reference": _record_value(self.subject_reference),
            "parent_diagnostic_reference": _record_value(self.parent_diagnostic_reference),
            "chain_root_reference": _record_value(self.chain_root_reference),
            "rule_ids": _record_value(self.rule_ids),
            "summary": _record_value(self.summary),
            "notes": _record_value(self.notes),
        }


@dataclass(frozen=True, slots=True)
class SafeOrbit:
    orbit_id: str
    member_count: ClassVar[object] = 16
    contains_known_valid_state: bool

    def __post_init__(self):
        _string(self.orbit_id, r"[01]{9}", 9)
        _boolean(self.contains_known_valid_state)
        _coherent(self)

    def to_record(self):
        return {
            "orbit_id": _record_value(self.orbit_id),
            "member_count": _record_value(self.member_count),
            "contains_known_valid_state": _record_value(self.contains_known_valid_state),
        }


@dataclass(frozen=True, slots=True)
class SafeStateContext:
    input_state: str | None
    actual_state: str | None
    selected_target: str | None
    eligible_targets: tuple | None
    codeword_chain: tuple | None
    admissibility_status: str | None
    transformation_compatibility: str | None
    normalization_status: str | None
    recoverability_relevance: str | None
    is_valid: bool | None
    orbit_info: SafeOrbit | None
    system_state_class: str | None
    recovery_category: str | None
    predicate_name: str | None
    predicate_value: bool | None
    candidate_order_index: int | None
    step_index: int | None
    profile_reference: str | None
    source_evidence_reference: str | None
    fixture_reference: str | None
    unavailable_fields: tuple
    input_failure_code: str | None
    profile_evidence_reference: str | None
    original_assessment_reference: str | None
    post_assessment_reference: str | None
    recovery_diagnostic_reference: str | None
    before_state: str | None
    codeword: str | None
    after_state: str | None
    policy_reference: str | None
    validation_status: str | None
    failed_field: str | None
    proof_evidence_reference: str | None
    recovery_safety_evidence_reference: str | None

    def __post_init__(self):
        if self.input_state is not None:
            _string(self.input_state, r"[01]{9}", 9)
        if self.actual_state is not None:
            _string(self.actual_state, r"[01]{9}", 9)
        if self.selected_target is not None:
            _string(self.selected_target, r"[01]{9}", 9)
        if self.eligible_targets is not None:
            object.__setattr__(self, "eligible_targets", _tuple(self.eligible_targets, 0, 16, lambda item: _string(item, r"[01]{9}", 9)))
        if self.codeword_chain is not None:
            object.__setattr__(self, "codeword_chain", _tuple(self.codeword_chain, 0, 16, lambda item: _string(item, r"[01]{9}", 9)))
        if self.admissibility_status is not None:
            _enum(self.admissibility_status, _E_ADMISSIBILITY)
        if self.transformation_compatibility is not None:
            _enum(self.transformation_compatibility, _E_COMPATIBILITY)
        if self.normalization_status is not None:
            _enum(self.normalization_status, _E_NORMALIZATION_STATUS)
        if self.recoverability_relevance is not None:
            _enum(self.recoverability_relevance, _E_RECOVERABILITY_RELEVANCE)
        if self.is_valid is not None:
            _boolean(self.is_valid)
        if self.orbit_info is not None:
            _owned(self.orbit_info, SafeOrbit)
        if self.system_state_class is not None:
            _enum(self.system_state_class, _E_SYSTEM_CLASS)
        if self.recovery_category is not None:
            _enum(self.recovery_category, _E_RECOVERY_CATEGORY)
        if self.predicate_name is not None:
            _enum(self.predicate_name, _E_PREDICATE_NAME)
        if self.predicate_value is not None:
            _boolean(self.predicate_value)
        if self.candidate_order_index is not None:
            _integer(self.candidate_order_index, 0, 31)
        if self.step_index is not None:
            _integer(self.step_index, 0, 767)
        if self.profile_reference is not None:
            _string(self.profile_reference, r"ref:[0-9]{6}", 10)
        if self.source_evidence_reference is not None:
            _string(self.source_evidence_reference, r"ref:[0-9]{6}", 10)
        if self.fixture_reference is not None:
            _string(self.fixture_reference, r"ref:[0-9]{6}", 10)
        object.__setattr__(self, "unavailable_fields", _tuple(self.unavailable_fields, 0, 32, lambda item: _enum(item, _E_CONTEXT_FIELD)))
        if self.input_failure_code is not None:
            _enum(self.input_failure_code, _E_INPUT_FAILURE)
        if self.profile_evidence_reference is not None:
            _string(self.profile_evidence_reference, r"ref:[0-9]{6}", 10)
        if self.original_assessment_reference is not None:
            _string(self.original_assessment_reference, r"ref:[0-9]{6}", 10)
        if self.post_assessment_reference is not None:
            _string(self.post_assessment_reference, r"ref:[0-9]{6}", 10)
        if self.recovery_diagnostic_reference is not None:
            _string(self.recovery_diagnostic_reference, r"ref:[0-9]{6}", 10)
        if self.before_state is not None:
            _string(self.before_state, r"[01]{9}", 9)
        if self.codeword is not None:
            _string(self.codeword, r"[01]{9}", 9)
        if self.after_state is not None:
            _string(self.after_state, r"[01]{9}", 9)
        if self.policy_reference is not None:
            _string(self.policy_reference, r"ref:[0-9]{6}", 10)
        if self.validation_status is not None:
            _enum(self.validation_status, _E_PROOF_STATUS)
        if self.failed_field is not None:
            _enum(self.failed_field, _E_VALIDATION_FIELD)
        if self.proof_evidence_reference is not None:
            _string(self.proof_evidence_reference, r"ref:[0-9]{6}", 10)
        if self.recovery_safety_evidence_reference is not None:
            _string(self.recovery_safety_evidence_reference, r"ref:[0-9]{6}", 10)
        _coherent(self)

    def to_record(self):
        return {
            "input_state": _record_value(self.input_state),
            "actual_state": _record_value(self.actual_state),
            "selected_target": _record_value(self.selected_target),
            "eligible_targets": _record_value(self.eligible_targets),
            "codeword_chain": _record_value(self.codeword_chain),
            "admissibility_status": _record_value(self.admissibility_status),
            "transformation_compatibility": _record_value(self.transformation_compatibility),
            "normalization_status": _record_value(self.normalization_status),
            "recoverability_relevance": _record_value(self.recoverability_relevance),
            "is_valid": _record_value(self.is_valid),
            "orbit_info": _record_value(self.orbit_info),
            "system_state_class": _record_value(self.system_state_class),
            "recovery_category": _record_value(self.recovery_category),
            "predicate_name": _record_value(self.predicate_name),
            "predicate_value": _record_value(self.predicate_value),
            "candidate_order_index": _record_value(self.candidate_order_index),
            "step_index": _record_value(self.step_index),
            "profile_reference": _record_value(self.profile_reference),
            "source_evidence_reference": _record_value(self.source_evidence_reference),
            "fixture_reference": _record_value(self.fixture_reference),
            "unavailable_fields": _record_value(self.unavailable_fields),
            "input_failure_code": _record_value(self.input_failure_code),
            "profile_evidence_reference": _record_value(self.profile_evidence_reference),
            "original_assessment_reference": _record_value(self.original_assessment_reference),
            "post_assessment_reference": _record_value(self.post_assessment_reference),
            "recovery_diagnostic_reference": _record_value(self.recovery_diagnostic_reference),
            "before_state": _record_value(self.before_state),
            "codeword": _record_value(self.codeword),
            "after_state": _record_value(self.after_state),
            "policy_reference": _record_value(self.policy_reference),
            "validation_status": _record_value(self.validation_status),
            "failed_field": _record_value(self.failed_field),
            "proof_evidence_reference": _record_value(self.proof_evidence_reference),
            "recovery_safety_evidence_reference": _record_value(self.recovery_safety_evidence_reference),
        }


@dataclass(frozen=True, slots=True)
class SafeError:
    domain: str
    code: str
    cause_codes: tuple
    failed_field: str | None
    source_reference: str | None
    message_template: str
    omitted_error_material: tuple

    def __post_init__(self):
        _enum(self.domain, _E_FAILURE_DOMAIN)
        _enum(self.code, _E_SAFE_FAILURE)
        object.__setattr__(self, "cause_codes", _tuple(self.cause_codes, 0, 8, lambda item: _enum(item, _E_SAFE_FAILURE)))
        if self.failed_field is not None:
            _enum(self.failed_field, _E_SAFE_FIELD)
        if self.source_reference is not None:
            _string(self.source_reference, r"ref:[0-9]{6}", 10)
        _enum(self.message_template, _E_MESSAGE_TEMPLATE)
        object.__setattr__(self, "omitted_error_material", _tuple(self.omitted_error_material, 0, 8, lambda item: _enum(item, _E_OMISSION_CATEGORY)))
        _coherent(self)

    def to_record(self):
        return {
            "domain": _record_value(self.domain),
            "code": _record_value(self.code),
            "cause_codes": _record_value(self.cause_codes),
            "failed_field": _record_value(self.failed_field),
            "source_reference": _record_value(self.source_reference),
            "message_template": _record_value(self.message_template),
            "omitted_error_material": _record_value(self.omitted_error_material),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    event_id: str
    local_sequence: int
    clock: ClockObservation
    source: str
    event_type: str
    message_template: str
    session_reference: str
    operation_reference: str | None
    action_reference: str | None
    relation: CaptureRelation | None
    diagnostic_reference: str | None
    envelope: SafeDiagnosticEnvelope | None
    outcome: str
    duration_nanoseconds: int | None
    duration_reason: str | None
    context: SafeStateContext
    error: SafeError | None
    redaction_entries: tuple

    def __post_init__(self):
        _string(self.event_id, r"ref:[0-9]{6}", 10)
        _integer(self.local_sequence, 0, 18446744073709551615)
        _owned(self.clock, ClockObservation)
        _enum(self.source, _E_PRODUCER)
        _enum(self.event_type, _E_EVENT_TYPE)
        _enum(self.message_template, _E_MESSAGE_TEMPLATE)
        _string(self.session_reference, r"ref:[0-9]{6}", 10)
        if self.operation_reference is not None:
            _string(self.operation_reference, r"ref:[0-9]{6}", 10)
        if self.action_reference is not None:
            _string(self.action_reference, r"ref:[0-9]{6}", 10)
        if self.relation is not None:
            _owned(self.relation, CaptureRelation)
        if self.diagnostic_reference is not None:
            _string(self.diagnostic_reference, r"ref:[0-9]{6}", 10)
        if self.envelope is not None:
            _owned(self.envelope, SafeDiagnosticEnvelope)
        _enum(self.outcome, _E_OBSERVED_OUTCOME)
        if self.duration_nanoseconds is not None:
            _integer(self.duration_nanoseconds, 0, 18446744073709551615)
        if self.duration_reason is not None:
            _enum(self.duration_reason, _E_UNAVAILABLE_REASON)
        _owned(self.context, SafeStateContext)
        if self.error is not None:
            _owned(self.error, SafeError)
        object.__setattr__(self, "redaction_entries", _tuple(self.redaction_entries, 0, 32, lambda item: _owned(item, RedactionEntry)))
        _coherent(self)

    def to_record(self):
        return {
            "event_id": _record_value(self.event_id),
            "local_sequence": _record_value(self.local_sequence),
            "clock": _record_value(self.clock),
            "source": _record_value(self.source),
            "event_type": _record_value(self.event_type),
            "message_template": _record_value(self.message_template),
            "session_reference": _record_value(self.session_reference),
            "operation_reference": _record_value(self.operation_reference),
            "action_reference": _record_value(self.action_reference),
            "relation": _record_value(self.relation),
            "diagnostic_reference": _record_value(self.diagnostic_reference),
            "envelope": _record_value(self.envelope),
            "outcome": _record_value(self.outcome),
            "duration_nanoseconds": _record_value(self.duration_nanoseconds),
            "duration_reason": _record_value(self.duration_reason),
            "context": _record_value(self.context),
            "error": _record_value(self.error),
            "redaction_entries": _record_value(self.redaction_entries),
        }


@dataclass(frozen=True, slots=True)
class EvidenceFact:
    fact_type: str
    event_references: tuple

    def __post_init__(self):
        _enum(self.fact_type, _E_FACT_TYPE)
        object.__setattr__(self, "event_references", _tuple(self.event_references, 1, 8, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        _coherent(self)

    def to_record(self):
        return {
            "fact_type": _record_value(self.fact_type),
            "event_references": _record_value(self.event_references),
        }


@dataclass(frozen=True, slots=True)
class ExpectedBehavior:
    invariant: str
    source_reference: str
    expected_outcome: str

    def __post_init__(self):
        _enum(self.invariant, _E_EXPECTED_INVARIANT)
        _string(self.source_reference, r"ref:[0-9]{6}", 10)
        _enum(self.expected_outcome, _E_OBSERVED_OUTCOME)
        _coherent(self)

    def to_record(self):
        return {
            "invariant": _record_value(self.invariant),
            "source_reference": _record_value(self.source_reference),
            "expected_outcome": _record_value(self.expected_outcome),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticIncident:
    incident_id: str
    trigger_event_reference: str
    expected: ExpectedBehavior
    observed_outcome: str
    affected_operation_references: tuple
    timeline_event_references: tuple
    attempt_event_references: tuple
    error: SafeError
    state_event_references: tuple
    reproduction_fixture_reference: str | None
    observed_facts: tuple
    supported_findings: tuple
    hypotheses: ClassVar[object] = ()
    unknowns: tuple
    unresolved: bool

    def __post_init__(self):
        _string(self.incident_id, r"ref:[0-9]{6}", 10)
        _string(self.trigger_event_reference, r"ref:[0-9]{6}", 10)
        _owned(self.expected, ExpectedBehavior)
        _enum(self.observed_outcome, _E_OBSERVED_OUTCOME)
        object.__setattr__(self, "affected_operation_references", _tuple(self.affected_operation_references, 1, 8, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        object.__setattr__(self, "timeline_event_references", _tuple(self.timeline_event_references, 1, 768, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        object.__setattr__(self, "attempt_event_references", _tuple(self.attempt_event_references, 0, 35, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        _owned(self.error, SafeError)
        object.__setattr__(self, "state_event_references", _tuple(self.state_event_references, 0, 34, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        if self.reproduction_fixture_reference is not None:
            _string(self.reproduction_fixture_reference, r"ref:[0-9]{6}", 10)
        object.__setattr__(self, "observed_facts", _tuple(self.observed_facts, 1, 16, lambda item: _owned(item, EvidenceFact)))
        object.__setattr__(self, "supported_findings", _tuple(self.supported_findings, 0, 16, lambda item: _owned(item, EvidenceFact)))
        object.__setattr__(self, "unknowns", _tuple(self.unknowns, 0, 16, lambda item: _enum(item, _E_UNKNOWN_CAUSE)))
        _boolean(self.unresolved)
        _coherent(self)

    def to_record(self):
        return {
            "incident_id": _record_value(self.incident_id),
            "trigger_event_reference": _record_value(self.trigger_event_reference),
            "expected": _record_value(self.expected),
            "observed_outcome": _record_value(self.observed_outcome),
            "affected_operation_references": _record_value(self.affected_operation_references),
            "timeline_event_references": _record_value(self.timeline_event_references),
            "attempt_event_references": _record_value(self.attempt_event_references),
            "error": _record_value(self.error),
            "state_event_references": _record_value(self.state_event_references),
            "reproduction_fixture_reference": _record_value(self.reproduction_fixture_reference),
            "observed_facts": _record_value(self.observed_facts),
            "supported_findings": _record_value(self.supported_findings),
            "hypotheses": _record_value(self.hypotheses),
            "unknowns": _record_value(self.unknowns),
            "unresolved": _record_value(self.unresolved),
        }


@dataclass(frozen=True, slots=True)
class SourcePin:
    source_kind: str
    revision: str
    sha256: str

    def __post_init__(self):
        _enum(self.source_kind, _E_PINNED_SOURCE)
        _string(self.revision, r"[0-9a-f]{40}", 40)
        _string(self.sha256, r"[0-9a-f]{64}", 64)
        _coherent(self)

    def to_record(self):
        return {
            "source_kind": _record_value(self.source_kind),
            "revision": _record_value(self.revision),
            "sha256": _record_value(self.sha256),
        }


@dataclass(frozen=True, slots=True)
class SupportingEvidence:
    verified_source_pins: tuple
    synthetic_fixture_references: tuple
    metric_event_references: tuple
    attachments: ClassVar[object] = ()
    attachment_reason: ClassVar[object] = 'EXCLUDED_REFERENCE_SCOPE'
    profiles: tuple
    assessments: tuple
    recovery_diagnostics: tuple
    source_evidence: tuple
    normalization_proofs: tuple
    correction_proofs: tuple
    registry_proofs: tuple
    conditions: tuple
    predicate_observations: tuple
    recovery_safety_evidence: tuple
    target_validity: tuple

    def __post_init__(self):
        object.__setattr__(self, "verified_source_pins", _tuple(self.verified_source_pins, 0, 40, lambda item: _owned(item, SourcePin)))
        object.__setattr__(self, "synthetic_fixture_references", _tuple(self.synthetic_fixture_references, 0, 128, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        object.__setattr__(self, "metric_event_references", _tuple(self.metric_event_references, 0, 1024, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        object.__setattr__(self, "profiles", _tuple(self.profiles, 0, 16, lambda item: _owned(item, SafeProfileEvidence)))
        object.__setattr__(self, "assessments", _tuple(self.assessments, 0, 512, lambda item: _owned(item, SafeAssessmentEvidence)))
        object.__setattr__(self, "recovery_diagnostics", _tuple(self.recovery_diagnostics, 0, 64, lambda item: _owned(item, SafeRecoveryDiagnostic)))
        object.__setattr__(self, "source_evidence", _tuple(self.source_evidence, 0, 16, lambda item: _owned(item, SafeSourceEvidence)))
        object.__setattr__(self, "normalization_proofs", _tuple(self.normalization_proofs, 0, 8, lambda item: _owned(item, SafeNormalizationProof)))
        object.__setattr__(self, "correction_proofs", _tuple(self.correction_proofs, 0, 8, lambda item: _owned(item, SafeCorrectionProof)))
        object.__setattr__(self, "registry_proofs", _tuple(self.registry_proofs, 0, 8, lambda item: _owned(item, SafeRegistryProof)))
        object.__setattr__(self, "conditions", _tuple(self.conditions, 0, 512, lambda item: _owned(item, SafeConditionEvidence)))
        object.__setattr__(self, "predicate_observations", _tuple(self.predicate_observations, 0, 512, lambda item: _owned(item, SafePredicateObservationEvidence)))
        object.__setattr__(self, "recovery_safety_evidence", _tuple(self.recovery_safety_evidence, 0, 8, lambda item: _owned(item, SafeRecoverySafetyEvidence)))
        object.__setattr__(self, "target_validity", _tuple(self.target_validity, 0, 264, lambda item: _owned(item, SafeTargetValidityEvidence)))
        _coherent(self)

    def to_record(self):
        return {
            "verified_source_pins": _record_value(self.verified_source_pins),
            "synthetic_fixture_references": _record_value(self.synthetic_fixture_references),
            "metric_event_references": _record_value(self.metric_event_references),
            "attachments": _record_value(self.attachments),
            "attachment_reason": _record_value(self.attachment_reason),
            "profiles": _record_value(self.profiles),
            "assessments": _record_value(self.assessments),
            "recovery_diagnostics": _record_value(self.recovery_diagnostics),
            "source_evidence": _record_value(self.source_evidence),
            "normalization_proofs": _record_value(self.normalization_proofs),
            "correction_proofs": _record_value(self.correction_proofs),
            "registry_proofs": _record_value(self.registry_proofs),
            "conditions": _record_value(self.conditions),
            "predicate_observations": _record_value(self.predicate_observations),
            "recovery_safety_evidence": _record_value(self.recovery_safety_evidence),
            "target_validity": _record_value(self.target_validity),
        }


@dataclass(frozen=True, slots=True)
class RedactionEntry:
    field_category: str
    reason: str
    count: int

    def __post_init__(self):
        _enum(self.field_category, _E_OMISSION_CATEGORY)
        _enum(self.reason, _E_REDACTION_REASON)
        _integer(self.count, 0, 18446744073709551615)
        _coherent(self)

    def to_record(self):
        return {
            "field_category": _record_value(self.field_category),
            "reason": _record_value(self.reason),
            "count": _record_value(self.count),
        }


@dataclass(frozen=True, slots=True)
class RedactionAccount:
    profile: ClassVar[object] = 'OWNED_SAFE_PROJECTION_V1'
    field_count: int
    reference_count: int
    entries: tuple
    secondary_check: ClassVar[object] = 'PASSED'

    def __post_init__(self):
        _integer(self.field_count, 0, 18446744073709551615)
        _integer(self.reference_count, 0, 18446744073709551615)
        object.__setattr__(self, "entries", _tuple(self.entries, 0, 32, lambda item: _owned(item, RedactionEntry)))
        _coherent(self)

    def to_record(self):
        return {
            "profile": _record_value(self.profile),
            "field_count": _record_value(self.field_count),
            "reference_count": _record_value(self.reference_count),
            "entries": _record_value(self.entries),
            "secondary_check": _record_value(self.secondary_check),
        }


@dataclass(frozen=True, slots=True)
class RetentionAccount:
    configured_limits: DiagnosticLimits
    boundaries: tuple
    active_operation_references: tuple
    incident_pinned_operation_references: tuple
    range_detail_coalesced: bool

    def __post_init__(self):
        _owned(self.configured_limits, DiagnosticLimits)
        object.__setattr__(self, "boundaries", _tuple(self.boundaries, 0, 16, lambda item: _owned(item, RetentionBoundary)))
        object.__setattr__(self, "active_operation_references", _tuple(self.active_operation_references, 0, 8, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        object.__setattr__(self, "incident_pinned_operation_references", _tuple(self.incident_pinned_operation_references, 0, 32, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        _boolean(self.range_detail_coalesced)
        _coherent(self)

    def to_record(self):
        return {
            "configured_limits": _record_value(self.configured_limits),
            "boundaries": _record_value(self.boundaries),
            "active_operation_references": _record_value(self.active_operation_references),
            "incident_pinned_operation_references": _record_value(self.incident_pinned_operation_references),
            "range_detail_coalesced": _record_value(self.range_detail_coalesced),
        }


@dataclass(frozen=True, slots=True)
class Limitation:
    code: str
    source: str

    def __post_init__(self):
        _enum(self.code, _E_LIMITATION_CODE)
        _enum(self.source, _E_COVERAGE_SOURCE)
        _coherent(self)

    def to_record(self):
        return {
            "code": _record_value(self.code),
            "source": _record_value(self.source),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticSnapshot:
    bundle_id: str
    generated_at_utc: str | None
    generation_time_reason: str | None
    identity: DiagnosticsIdentity
    profile: DiagnosticsProfile
    capture_window: CaptureWindow
    coverage: tuple
    events: tuple
    meta_diagnostics: tuple
    incidents: tuple
    supporting_evidence: SupportingEvidence
    health: DiagnosticsHealth
    retention: RetentionAccount
    redaction: RedactionAccount
    limitations: tuple

    def __post_init__(self):
        _string(self.bundle_id, r"ref:[0-9]{6}", 10)
        if self.generated_at_utc is not None:
            _utc(self.generated_at_utc)
        if self.generation_time_reason is not None:
            _enum(self.generation_time_reason, _E_UNAVAILABLE_REASON)
        _owned(self.identity, DiagnosticsIdentity)
        _owned(self.profile, DiagnosticsProfile)
        _owned(self.capture_window, CaptureWindow)
        object.__setattr__(self, "coverage", _tuple(self.coverage, 1, 32, lambda item: _owned(item, MissingCoverage)))
        object.__setattr__(self, "events", _tuple(self.events, 0, 1024, lambda item: _owned(item, DiagnosticEvent)))
        object.__setattr__(self, "meta_diagnostics", _tuple(self.meta_diagnostics, 0, 16, lambda item: _owned(item, MetaDiagnosticRecord)))
        object.__setattr__(self, "incidents", _tuple(self.incidents, 0, 32, lambda item: _owned(item, DiagnosticIncident)))
        _owned(self.supporting_evidence, SupportingEvidence)
        _owned(self.health, DiagnosticsHealth)
        _owned(self.retention, RetentionAccount)
        _owned(self.redaction, RedactionAccount)
        object.__setattr__(self, "limitations", _tuple(self.limitations, 1, 16, lambda item: _owned(item, Limitation)))
        _coherent(self)

    def to_record(self):
        return {
            "bundle_id": _record_value(self.bundle_id),
            "generated_at_utc": _record_value(self.generated_at_utc),
            "generation_time_reason": _record_value(self.generation_time_reason),
            "identity": _record_value(self.identity),
            "profile": _record_value(self.profile),
            "capture_window": _record_value(self.capture_window),
            "coverage": _record_value(self.coverage),
            "events": _record_value(self.events),
            "meta_diagnostics": _record_value(self.meta_diagnostics),
            "incidents": _record_value(self.incidents),
            "supporting_evidence": _record_value(self.supporting_evidence),
            "health": _record_value(self.health),
            "retention": _record_value(self.retention),
            "redaction": _record_value(self.redaction),
            "limitations": _record_value(self.limitations),
            "schema_ref": "data/schemas/m3_reference_diagnostic_bundle_schema.json",
            "artifact_type": "ywe_reference_diagnostic_bundle",
            "artifact_version": "1.0.0",
        }


@dataclass(frozen=True, slots=True)
class MetaCause:
    cause_code: str
    related_operation_reference: str | None
    related_diagnostic_reference: str | None
    expected_phase: str | None
    observed_phase: str | None

    def __post_init__(self):
        _enum(self.cause_code, _E_META_CAUSE_CODE)
        if self.related_operation_reference is not None:
            _string(self.related_operation_reference, r"ref:[0-9]{6}", 10)
        if self.related_diagnostic_reference is not None:
            _string(self.related_diagnostic_reference, r"ref:[0-9]{6}", 10)
        if self.expected_phase is not None:
            _enum(self.expected_phase, _E_EXPECTED_PHASE)
        if self.observed_phase is not None:
            _enum(self.observed_phase, _E_EXPECTED_PHASE)
        _coherent(self)

    def to_record(self):
        return {
            "cause_code": _record_value(self.cause_code),
            "related_operation_reference": _record_value(self.related_operation_reference),
            "related_diagnostic_reference": _record_value(self.related_diagnostic_reference),
            "expected_phase": _record_value(self.expected_phase),
            "observed_phase": _record_value(self.observed_phase),
        }


@dataclass(frozen=True, slots=True)
class StorageReceipt:
    sequence: int | None
    status: str
    failure_code: str | None

    def __post_init__(self):
        if self.sequence is not None:
            _integer(self.sequence, 0, 18446744073709551615)
        _enum(self.status, _E_STORAGE_COMMIT_STATUS)
        if self.failure_code is not None:
            _enum(self.failure_code, _E_DIAGNOSTICS_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "sequence": _record_value(self.sequence),
            "status": _record_value(self.status),
            "failure_code": _record_value(self.failure_code),
        }


@dataclass(frozen=True, slots=True)
class PartReceipt:
    part: str
    relative_name: str
    status: str
    bytes: int | None
    sha256: str | None
    failure_code: str | None

    def __post_init__(self):
        _enum(self.part, _E_EXPORT_PART)
        _enum(self.relative_name, _E_PART_NAME)
        _enum(self.status, _E_PART_STATUS)
        if self.bytes is not None:
            _integer(self.bytes, 0, 18446744073709551615)
        if self.sha256 is not None:
            _string(self.sha256, r"[0-9a-f]{64}", 64)
        if self.failure_code is not None:
            _enum(self.failure_code, _E_DIAGNOSTICS_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "part": _record_value(self.part),
            "relative_name": _record_value(self.relative_name),
            "status": _record_value(self.status),
            "bytes": _record_value(self.bytes),
            "sha256": _record_value(self.sha256),
            "failure_code": _record_value(self.failure_code),
        }


@dataclass(frozen=True, slots=True)
class ExportReceipt:
    bundle_id: str
    status: ClassVar[object] = 'COMPLETE'
    parts: tuple
    last_included_sequence: int | None
    snapshot: DiagnosticSnapshot

    def __post_init__(self):
        _string(self.bundle_id, r"ref:[0-9]{6}", 10)
        object.__setattr__(self, "parts", _tuple(self.parts, 3, 3, lambda item: _owned(item, PartReceipt)))
        if self.last_included_sequence is not None:
            _integer(self.last_included_sequence, 0, 18446744073709551615)
        _owned(self.snapshot, DiagnosticSnapshot)
        _coherent(self)

    def to_record(self):
        return {
            "bundle_id": _record_value(self.bundle_id),
            "status": _record_value(self.status),
            "parts": _record_value(self.parts),
            "last_included_sequence": _record_value(self.last_included_sequence),
            "snapshot": _record_value(self.snapshot),
        }


@dataclass(frozen=True, slots=True)
class ExportFailure:
    bundle_id: str
    status: ClassVar[object] = 'INCOMPLETE'
    failure_code: str
    failed_part: str
    parts: tuple
    snapshot: DiagnosticSnapshot

    def __post_init__(self):
        _string(self.bundle_id, r"ref:[0-9]{6}", 10)
        _enum(self.failure_code, _E_DIAGNOSTICS_FAILURE)
        _enum(self.failed_part, _E_EXPORT_PART)
        object.__setattr__(self, "parts", _tuple(self.parts, 3, 3, lambda item: _owned(item, PartReceipt)))
        _owned(self.snapshot, DiagnosticSnapshot)
        _coherent(self)

    def to_record(self):
        return {
            "bundle_id": _record_value(self.bundle_id),
            "status": _record_value(self.status),
            "failure_code": _record_value(self.failure_code),
            "failed_part": _record_value(self.failed_part),
            "parts": _record_value(self.parts),
            "snapshot": _record_value(self.snapshot),
        }


@dataclass(frozen=True, slots=True)
class RetentionReceipt:
    status: str
    boundaries: tuple
    health: DiagnosticsHealth

    def __post_init__(self):
        _enum(self.status, _E_RETENTION_RECEIPT_STATUS)
        object.__setattr__(self, "boundaries", _tuple(self.boundaries, 0, 16, lambda item: _owned(item, RetentionBoundary)))
        _owned(self.health, DiagnosticsHealth)
        _coherent(self)

    def to_record(self):
        return {
            "status": _record_value(self.status),
            "boundaries": _record_value(self.boundaries),
            "health": _record_value(self.health),
        }


@dataclass(frozen=True, slots=True)
class StorageVerification:
    mechanism: ClassVar[object] = 'WINDOWS_PROTECTED_DACL'
    status: str
    persistent_acls: bool
    owner_matches_effective_sid: bool
    dacl_protected: bool
    grant_principals: tuple
    no_reparse_path: bool
    trusted_parent: bool
    stable_identity: bool
    failure_code: str | None

    def __post_init__(self):
        _enum(self.status, _E_STORAGE_VERIFICATION_STATUS)
        _boolean(self.persistent_acls)
        _boolean(self.owner_matches_effective_sid)
        _boolean(self.dacl_protected)
        object.__setattr__(self, "grant_principals", _tuple(self.grant_principals, 2, 2, lambda item: _enum(item, _E_STORAGE_PRINCIPAL)))
        _boolean(self.no_reparse_path)
        _boolean(self.trusted_parent)
        _boolean(self.stable_identity)
        if self.failure_code is not None:
            _enum(self.failure_code, _E_DIAGNOSTICS_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "mechanism": _record_value(self.mechanism),
            "status": _record_value(self.status),
            "persistent_acls": _record_value(self.persistent_acls),
            "owner_matches_effective_sid": _record_value(self.owner_matches_effective_sid),
            "dacl_protected": _record_value(self.dacl_protected),
            "grant_principals": _record_value(self.grant_principals),
            "no_reparse_path": _record_value(self.no_reparse_path),
            "trusted_parent": _record_value(self.trusted_parent),
            "stable_identity": _record_value(self.stable_identity),
            "failure_code": _record_value(self.failure_code),
        }


@dataclass(frozen=True, slots=True)
class SafeProfileEvidence:
    evidence_reference: str
    profile_reference: str
    availability: str
    source_reference: str
    source_digest_reference: str
    source_evidence_reference: str
    recognized_valid_states: tuple | None
    unavailable_reason: str | None

    def __post_init__(self):
        _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.profile_reference, r"ref:[0-9]{6}", 10)
        _enum(self.availability, _E_PROFILE_AVAILABILITY)
        _string(self.source_reference, r"ref:[0-9]{6}", 10)
        _string(self.source_digest_reference, r"ref:[0-9]{6}", 10)
        _string(self.source_evidence_reference, r"ref:[0-9]{6}", 10)
        if self.recognized_valid_states is not None:
            object.__setattr__(self, "recognized_valid_states", _tuple(self.recognized_valid_states, 0, 512, lambda item: _string(item, r"[01]{9}", 9)))
        if self.unavailable_reason is not None:
            _enum(self.unavailable_reason, _E_UNAVAILABLE_REASON)
        _coherent(self)

    def to_record(self):
        return {
            "evidence_reference": _record_value(self.evidence_reference),
            "profile_reference": _record_value(self.profile_reference),
            "availability": _record_value(self.availability),
            "source_reference": _record_value(self.source_reference),
            "source_digest_reference": _record_value(self.source_digest_reference),
            "source_evidence_reference": _record_value(self.source_evidence_reference),
            "recognized_valid_states": _record_value(self.recognized_valid_states),
            "unavailable_reason": _record_value(self.unavailable_reason),
        }


@dataclass(frozen=True, slots=True)
class SafeInputState:
    kind: str
    state: str | None
    input_reference: str
    failure_code: str | None

    def __post_init__(self):
        _enum(self.kind, _E_SAFE_INPUT_KIND)
        if self.state is not None:
            _string(self.state, r"[01]{9}", 9)
        _string(self.input_reference, r"ref:[0-9]{6}", 10)
        if self.failure_code is not None:
            _enum(self.failure_code, _E_INPUT_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "kind": _record_value(self.kind),
            "state": _record_value(self.state),
            "input_reference": _record_value(self.input_reference),
            "failure_code": _record_value(self.failure_code),
        }


@dataclass(frozen=True, slots=True)
class SafeStateValidity:
    input_state: SafeInputState
    admissibility_status: str
    transformation_compatibility: str
    normalization_status: str
    recoverability_relevance: str
    is_valid: bool
    orbit_info: SafeOrbit | None
    rule_ids: tuple
    notes: tuple

    def __post_init__(self):
        _owned(self.input_state, SafeInputState)
        _enum(self.admissibility_status, _E_ADMISSIBILITY)
        _enum(self.transformation_compatibility, _E_COMPATIBILITY)
        _enum(self.normalization_status, _E_NORMALIZATION_STATUS)
        _enum(self.recoverability_relevance, _E_RECOVERABILITY_RELEVANCE)
        _boolean(self.is_valid)
        if self.orbit_info is not None:
            _owned(self.orbit_info, SafeOrbit)
        object.__setattr__(self, "rule_ids", _tuple(self.rule_ids, 1, 5, lambda item: _enum(item, _E_CANONICAL_RULE)))
        object.__setattr__(self, "notes", _tuple(self.notes, 1, 8, lambda item: _template(item)))
        _coherent(self)

    def to_record(self):
        return {
            "input_state": _record_value(self.input_state),
            "admissibility_status": _record_value(self.admissibility_status),
            "transformation_compatibility": _record_value(self.transformation_compatibility),
            "normalization_status": _record_value(self.normalization_status),
            "recoverability_relevance": _record_value(self.recoverability_relevance),
            "is_valid": _record_value(self.is_valid),
            "orbit_info": _record_value(self.orbit_info),
            "rule_ids": _record_value(self.rule_ids),
            "notes": _record_value(self.notes),
        }


@dataclass(frozen=True, slots=True)
class SafePredicate:
    evaluation_status: str
    value: bool | None
    assessment_reference: str
    diagnosis_reference: str
    subject_reference: str
    profile_reference: str
    source_reference: str
    evidence_reference: str

    def __post_init__(self):
        _enum(self.evaluation_status, _E_PREDICATE_EVALUATION)
        if self.value is not None:
            _boolean(self.value)
        _string(self.assessment_reference, r"ref:[0-9]{6}", 10)
        _string(self.diagnosis_reference, r"ref:[0-9]{6}", 10)
        _string(self.subject_reference, r"ref:[0-9]{6}", 10)
        _string(self.profile_reference, r"ref:[0-9]{6}", 10)
        _string(self.source_reference, r"ref:[0-9]{6}", 10)
        _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        _coherent(self)

    def to_record(self):
        return {
            "evaluation_status": _record_value(self.evaluation_status),
            "value": _record_value(self.value),
            "assessment_reference": _record_value(self.assessment_reference),
            "diagnosis_reference": _record_value(self.diagnosis_reference),
            "subject_reference": _record_value(self.subject_reference),
            "profile_reference": _record_value(self.profile_reference),
            "source_reference": _record_value(self.source_reference),
            "evidence_reference": _record_value(self.evidence_reference),
        }


@dataclass(frozen=True, slots=True)
class SafeAssessmentEvidence:
    evidence_reference: str
    assessment_reference: str
    original_input_reference: str
    parsed_state: str | None
    canonical_source_reference: str
    profile_evidence_reference: str
    state_validity_diagnostic: SafeStateValidity
    is_in_safe_halt: bool
    is_in_containment: bool
    correction_path_is_known: SafePredicate | None
    fallback_is_available: SafePredicate | None
    system_state_class: str | None
    recovery_category: str | None
    consulted_predicates: tuple
    emissions: tuple

    def __post_init__(self):
        _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.assessment_reference, r"ref:[0-9]{6}", 10)
        _string(self.original_input_reference, r"ref:[0-9]{6}", 10)
        if self.parsed_state is not None:
            _string(self.parsed_state, r"[01]{9}", 9)
        _string(self.canonical_source_reference, r"ref:[0-9]{6}", 10)
        _string(self.profile_evidence_reference, r"ref:[0-9]{6}", 10)
        _owned(self.state_validity_diagnostic, SafeStateValidity)
        _boolean(self.is_in_safe_halt)
        _boolean(self.is_in_containment)
        if self.correction_path_is_known is not None:
            _owned(self.correction_path_is_known, SafePredicate)
        if self.fallback_is_available is not None:
            _owned(self.fallback_is_available, SafePredicate)
        if self.system_state_class is not None:
            _enum(self.system_state_class, _E_SYSTEM_CLASS)
        if self.recovery_category is not None:
            _enum(self.recovery_category, _E_RECOVERY_CATEGORY)
        object.__setattr__(self, "consulted_predicates", _tuple(self.consulted_predicates, 0, 2, lambda item: _enum(item, _E_PREDICATE_NAME)))
        object.__setattr__(self, "emissions", _tuple(self.emissions, 1, 2, lambda item: _owned(item, SafeDiagnosticEnvelope)))
        _coherent(self)

    def to_record(self):
        return {
            "evidence_reference": _record_value(self.evidence_reference),
            "assessment_reference": _record_value(self.assessment_reference),
            "original_input_reference": _record_value(self.original_input_reference),
            "parsed_state": _record_value(self.parsed_state),
            "canonical_source_reference": _record_value(self.canonical_source_reference),
            "profile_evidence_reference": _record_value(self.profile_evidence_reference),
            "state_validity_diagnostic": _record_value(self.state_validity_diagnostic),
            "is_in_safe_halt": _record_value(self.is_in_safe_halt),
            "is_in_containment": _record_value(self.is_in_containment),
            "correction_path_is_known": _record_value(self.correction_path_is_known),
            "fallback_is_available": _record_value(self.fallback_is_available),
            "system_state_class": _record_value(self.system_state_class),
            "recovery_category": _record_value(self.recovery_category),
            "consulted_predicates": _record_value(self.consulted_predicates),
            "emissions": _record_value(self.emissions),
        }


@dataclass(frozen=True, slots=True)
class SafeRecoveryStep:
    action_reference: str
    step_kind: str
    outcome: str
    actual_state: str | None
    event_indices: tuple
    reason_template: str

    def __post_init__(self):
        _string(self.action_reference, r"ref:[0-9]{6}", 10)
        _enum(self.step_kind, _E_RECOVERY_STEP_KIND)
        _enum(self.outcome, _E_OBSERVED_OUTCOME)
        if self.actual_state is not None:
            _string(self.actual_state, r"[01]{9}", 9)
        object.__setattr__(self, "event_indices", _tuple(self.event_indices, 0, 32, lambda item: _integer(item, 0, 1023)))
        _enum(self.reason_template, _E_MESSAGE_TEMPLATE)
        _coherent(self)

    def to_record(self):
        return {
            "action_reference": _record_value(self.action_reference),
            "step_kind": _record_value(self.step_kind),
            "outcome": _record_value(self.outcome),
            "actual_state": _record_value(self.actual_state),
            "event_indices": _record_value(self.event_indices),
            "reason_template": _record_value(self.reason_template),
        }


@dataclass(frozen=True, slots=True)
class SafeRecoveryDiagnostic:
    recovery_category: str
    original_state_class: str
    original_diagnostic: str
    steps: tuple
    outcome: str
    corrected_state: str | None
    fallback_policy_id: str | None
    reason: str
    rule_ids: tuple

    def __post_init__(self):
        _enum(self.recovery_category, _E_RECOVERY_CATEGORY)
        _enum(self.original_state_class, _E_SYSTEM_CLASS)
        _string(self.original_diagnostic, r"ref:[0-9]{6}", 10)
        object.__setattr__(self, "steps", _tuple(self.steps, 0, 32, lambda item: _owned(item, SafeRecoveryStep)))
        _enum(self.outcome, _E_OBSERVED_OUTCOME)
        if self.corrected_state is not None:
            _string(self.corrected_state, r"[01]{9}", 9)
        if self.fallback_policy_id is not None:
            _string(self.fallback_policy_id, r"ref:[0-9]{6}", 10)
        _template(self.reason)
        object.__setattr__(self, "rule_ids", _tuple(self.rule_ids, 1, 10, lambda item: _enum(item, _E_CANONICAL_RULE)))
        _coherent(self)

    def to_record(self):
        return {
            "recovery_category": _record_value(self.recovery_category),
            "original_state_class": _record_value(self.original_state_class),
            "original_diagnostic": _record_value(self.original_diagnostic),
            "steps": _record_value(self.steps),
            "outcome": _record_value(self.outcome),
            "corrected_state": _record_value(self.corrected_state),
            "fallback_policy_id": _record_value(self.fallback_policy_id),
            "reason": _record_value(self.reason),
            "rule_ids": _record_value(self.rule_ids),
        }


@dataclass(frozen=True, slots=True)
class PrivateAcknowledgmentWitness:
    original_reference: str
    collector_reference: str
    session_reference: str
    confirmed_sequence: int
    emission_sha256: str

    def __post_init__(self):
        _reference(self.original_reference)
        _string(self.collector_reference, r"ref:[0-9]{6}", 10)
        _string(self.session_reference, r"ref:[0-9]{6}", 10)
        _integer(self.confirmed_sequence, 0, 18446744073709551615)
        _string(self.emission_sha256, r"[0-9a-f]{64}", 64)
        _coherent(self)

    def to_record(self):
        return {
            "original_reference": _record_value(self.original_reference),
            "collector_reference": _record_value(self.collector_reference),
            "session_reference": _record_value(self.session_reference),
            "confirmed_sequence": _record_value(self.confirmed_sequence),
            "emission_sha256": _record_value(self.emission_sha256),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticCounterState:
    field: str
    status: str
    reason: str | None

    def __post_init__(self):
        _enum(self.field, _E_COUNTER_FIELD)
        _enum(self.status, _E_COUNTER_STATUS)
        if self.reason is not None:
            _enum(self.reason, _E_COUNTER_REASON)
        _coherent(self)

    def to_record(self):
        return {
            "field": _record_value(self.field),
            "status": _record_value(self.status),
            "reason": _record_value(self.reason),
        }


@dataclass(frozen=True, slots=True)
class MetaDiagnosticRecord:
    meta_reference: str
    local_sequence: int
    clock: ClockObservation
    envelope: SafeDiagnosticEnvelope
    cause: MetaCause
    message_template: ClassVar[object] = 'DIAGNOSTIC_NONCONFORMANCE'

    def __post_init__(self):
        _string(self.meta_reference, r"ref:[0-9]{6}", 10)
        _integer(self.local_sequence, 0, 18446744073709551615)
        _owned(self.clock, ClockObservation)
        _owned(self.envelope, SafeDiagnosticEnvelope)
        _owned(self.cause, MetaCause)
        _coherent(self)

    def to_record(self):
        return {
            "meta_reference": _record_value(self.meta_reference),
            "local_sequence": _record_value(self.local_sequence),
            "clock": _record_value(self.clock),
            "envelope": _record_value(self.envelope),
            "cause": _record_value(self.cause),
            "message_template": _record_value(self.message_template),
        }


@dataclass(frozen=True, slots=True)
class RecoveryAdmissionReceipt:
    status: str
    operation_reference: str
    origin_assessment_reference: str
    origin_diagnostic_references: tuple
    reserved_events: int
    reserved_bytes: int
    failure_code: str | None

    def __post_init__(self):
        _enum(self.status, _E_ADMISSION_STATUS)
        _reference(self.operation_reference, 192)
        _reference(self.origin_assessment_reference)
        object.__setattr__(self, "origin_diagnostic_references", _tuple(self.origin_diagnostic_references, 2, 2, lambda item: _reference(item)))
        _integer(self.reserved_events, 0, 768)
        _integer(self.reserved_bytes, 0, 31588352)
        if self.failure_code is not None:
            _enum(self.failure_code, _E_DIAGNOSTICS_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "status": _record_value(self.status),
            "operation_reference": _record_value(self.operation_reference),
            "origin_assessment_reference": _record_value(self.origin_assessment_reference),
            "origin_diagnostic_references": _record_value(self.origin_diagnostic_references),
            "reserved_events": _record_value(self.reserved_events),
            "reserved_bytes": _record_value(self.reserved_bytes),
            "failure_code": _record_value(self.failure_code),
        }


@dataclass(frozen=True, slots=True)
class SafeSourceEvidence:
    evidence_reference: str
    dependency_id: ClassVar[object] = 'ash_cosmological_model.f2_9.canonical'
    verified_pins: tuple
    external_source_reference: str | None
    external_verification: ClassVar[object] = 'DECLARED_NOT_AUTHENTICATED'

    def __post_init__(self):
        _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        object.__setattr__(self, "verified_pins", _tuple(self.verified_pins, 8, 8, lambda item: _owned(item, SourcePin)))
        if self.external_source_reference is not None:
            _string(self.external_source_reference, r"ref:[0-9]{6}", 10)
        _coherent(self)

    def to_record(self):
        return {
            "evidence_reference": _record_value(self.evidence_reference),
            "dependency_id": _record_value(self.dependency_id),
            "verified_pins": _record_value(self.verified_pins),
            "external_source_reference": _record_value(self.external_source_reference),
            "external_verification": _record_value(self.external_verification),
        }


@dataclass(frozen=True, slots=True)
class SafeNormalizationProof:
    evidence_reference: str
    preparation_status: str
    original_assessment_reference: str
    original_diagnosis_reference: str
    submitted_plan_reference: str | None
    policy_reference: str
    submitted_source_reference: str
    current_source_evidence_reference: str
    submitted_profile_evidence_reference: str
    current_profile_evidence_reference: str
    origin_validation_status: str
    plan_validation_status: str
    decision: str | None
    submitted_targets: tuple | None
    expected_targets: tuple | None
    submitted_target: str | None
    expected_target: str | None
    submitted_chain: tuple | None
    recomputed_chain: tuple | None
    failed_field: str | None
    safe_failure: str | None

    def __post_init__(self):
        _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        _enum(self.preparation_status, _E_PREPARATION_STATUS)
        _string(self.original_assessment_reference, r"ref:[0-9]{6}", 10)
        _string(self.original_diagnosis_reference, r"ref:[0-9]{6}", 10)
        if self.submitted_plan_reference is not None:
            _string(self.submitted_plan_reference, r"ref:[0-9]{6}", 10)
        _string(self.policy_reference, r"ref:[0-9]{6}", 10)
        _string(self.submitted_source_reference, r"ref:[0-9]{6}", 10)
        _string(self.current_source_evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.submitted_profile_evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.current_profile_evidence_reference, r"ref:[0-9]{6}", 10)
        _enum(self.origin_validation_status, _E_PROOF_STATUS)
        _enum(self.plan_validation_status, _E_PROOF_STATUS)
        if self.decision is not None:
            _enum(self.decision, _E_NORMALIZATION_DECISION)
        if self.submitted_targets is not None:
            object.__setattr__(self, "submitted_targets", _tuple(self.submitted_targets, 0, 16, lambda item: _string(item, r"[01]{9}", 9)))
        if self.expected_targets is not None:
            object.__setattr__(self, "expected_targets", _tuple(self.expected_targets, 0, 16, lambda item: _string(item, r"[01]{9}", 9)))
        if self.submitted_target is not None:
            _string(self.submitted_target, r"[01]{9}", 9)
        if self.expected_target is not None:
            _string(self.expected_target, r"[01]{9}", 9)
        if self.submitted_chain is not None:
            object.__setattr__(self, "submitted_chain", _tuple(self.submitted_chain, 0, 1, lambda item: _string(item, r"[01]{9}", 9)))
        if self.recomputed_chain is not None:
            object.__setattr__(self, "recomputed_chain", _tuple(self.recomputed_chain, 0, 1, lambda item: _string(item, r"[01]{9}", 9)))
        if self.failed_field is not None:
            _enum(self.failed_field, _E_VALIDATION_FIELD)
        if self.safe_failure is not None:
            _enum(self.safe_failure, _E_SAFE_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "evidence_reference": _record_value(self.evidence_reference),
            "preparation_status": _record_value(self.preparation_status),
            "original_assessment_reference": _record_value(self.original_assessment_reference),
            "original_diagnosis_reference": _record_value(self.original_diagnosis_reference),
            "submitted_plan_reference": _record_value(self.submitted_plan_reference),
            "policy_reference": _record_value(self.policy_reference),
            "submitted_source_reference": _record_value(self.submitted_source_reference),
            "current_source_evidence_reference": _record_value(self.current_source_evidence_reference),
            "submitted_profile_evidence_reference": _record_value(self.submitted_profile_evidence_reference),
            "current_profile_evidence_reference": _record_value(self.current_profile_evidence_reference),
            "origin_validation_status": _record_value(self.origin_validation_status),
            "plan_validation_status": _record_value(self.plan_validation_status),
            "decision": _record_value(self.decision),
            "submitted_targets": _record_value(self.submitted_targets),
            "expected_targets": _record_value(self.expected_targets),
            "submitted_target": _record_value(self.submitted_target),
            "expected_target": _record_value(self.expected_target),
            "submitted_chain": _record_value(self.submitted_chain),
            "recomputed_chain": _record_value(self.recomputed_chain),
            "failed_field": _record_value(self.failed_field),
            "safe_failure": _record_value(self.safe_failure),
        }


@dataclass(frozen=True, slots=True)
class SafeCorrectionProof:
    evidence_reference: str
    correction_reference: str
    original_assessment_reference: str
    submitted_source_reference: str
    current_source_evidence_reference: str
    submitted_profile_evidence_reference: str
    current_profile_evidence_reference: str
    declared_source_authentication: ClassVar[object] = 'DECLARED_NOT_AUTHENTICATED'
    origin_validation_status: str
    correction_validation_status: str
    submitted_chain: tuple
    claimed_target: str
    computed_target: str | None
    target_diagnostic_reference: str | None
    failed_field: str | None
    safe_failure: str | None

    def __post_init__(self):
        _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.correction_reference, r"ref:[0-9]{6}", 10)
        _string(self.original_assessment_reference, r"ref:[0-9]{6}", 10)
        _string(self.submitted_source_reference, r"ref:[0-9]{6}", 10)
        _string(self.current_source_evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.submitted_profile_evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.current_profile_evidence_reference, r"ref:[0-9]{6}", 10)
        _enum(self.origin_validation_status, _E_PROOF_STATUS)
        _enum(self.correction_validation_status, _E_PROOF_STATUS)
        object.__setattr__(self, "submitted_chain", _tuple(self.submitted_chain, 0, 16, lambda item: _string(item, r"[01]{9}", 9)))
        _string(self.claimed_target, r"[01]{9}", 9)
        if self.computed_target is not None:
            _string(self.computed_target, r"[01]{9}", 9)
        if self.target_diagnostic_reference is not None:
            _string(self.target_diagnostic_reference, r"ref:[0-9]{6}", 10)
        if self.failed_field is not None:
            _enum(self.failed_field, _E_VALIDATION_FIELD)
        if self.safe_failure is not None:
            _enum(self.safe_failure, _E_SAFE_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "evidence_reference": _record_value(self.evidence_reference),
            "correction_reference": _record_value(self.correction_reference),
            "original_assessment_reference": _record_value(self.original_assessment_reference),
            "submitted_source_reference": _record_value(self.submitted_source_reference),
            "current_source_evidence_reference": _record_value(self.current_source_evidence_reference),
            "submitted_profile_evidence_reference": _record_value(self.submitted_profile_evidence_reference),
            "current_profile_evidence_reference": _record_value(self.current_profile_evidence_reference),
            "declared_source_authentication": _record_value(self.declared_source_authentication),
            "origin_validation_status": _record_value(self.origin_validation_status),
            "correction_validation_status": _record_value(self.correction_validation_status),
            "submitted_chain": _record_value(self.submitted_chain),
            "claimed_target": _record_value(self.claimed_target),
            "computed_target": _record_value(self.computed_target),
            "target_diagnostic_reference": _record_value(self.target_diagnostic_reference),
            "failed_field": _record_value(self.failed_field),
            "safe_failure": _record_value(self.safe_failure),
        }


@dataclass(frozen=True, slots=True)
class SafeRegistryEntry:
    policy_reference: str
    input_order_index: int
    ordering_rank: int
    applicability_condition_references: tuple
    validation_condition_references: tuple
    candidate_state: str
    escalation_on_failure: str
    certification_assessment_reference: str
    certification_validation_status: str
    target_diagnostic_reference: str | None

    def __post_init__(self):
        _string(self.policy_reference, r"ref:[0-9]{6}", 10)
        _integer(self.input_order_index, 0, 31)
        _integer(self.ordering_rank, -9223372036854775808, 9223372036854775807)
        object.__setattr__(self, "applicability_condition_references", _tuple(self.applicability_condition_references, 0, 8, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        object.__setattr__(self, "validation_condition_references", _tuple(self.validation_condition_references, 0, 8, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        _string(self.candidate_state, r"[01]{9}", 9)
        _enum(self.escalation_on_failure, _E_ESCALATION_POLICY)
        _string(self.certification_assessment_reference, r"ref:[0-9]{6}", 10)
        _enum(self.certification_validation_status, _E_PROOF_STATUS)
        if self.target_diagnostic_reference is not None:
            _string(self.target_diagnostic_reference, r"ref:[0-9]{6}", 10)
        _coherent(self)

    def to_record(self):
        return {
            "policy_reference": _record_value(self.policy_reference),
            "input_order_index": _record_value(self.input_order_index),
            "ordering_rank": _record_value(self.ordering_rank),
            "applicability_condition_references": _record_value(self.applicability_condition_references),
            "validation_condition_references": _record_value(self.validation_condition_references),
            "candidate_state": _record_value(self.candidate_state),
            "escalation_on_failure": _record_value(self.escalation_on_failure),
            "certification_assessment_reference": _record_value(self.certification_assessment_reference),
            "certification_validation_status": _record_value(self.certification_validation_status),
            "target_diagnostic_reference": _record_value(self.target_diagnostic_reference),
        }


@dataclass(frozen=True, slots=True)
class SafeRegistryProof:
    evidence_reference: str
    registry_reference: str
    availability: str
    declared_source_authentication: ClassVar[object] = 'DECLARED_NOT_AUTHENTICATED'
    submitted_source_reference: str
    current_source_evidence_reference: str
    submitted_profile_evidence_reference: str
    current_profile_evidence_reference: str
    validation_status: str
    entries: tuple
    evaluated_policy_references: tuple
    failed_policy_reference: str | None
    failed_field: str | None
    safe_failure: str | None

    def __post_init__(self):
        _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.registry_reference, r"ref:[0-9]{6}", 10)
        _enum(self.availability, _E_PROFILE_AVAILABILITY)
        _string(self.submitted_source_reference, r"ref:[0-9]{6}", 10)
        _string(self.current_source_evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.submitted_profile_evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.current_profile_evidence_reference, r"ref:[0-9]{6}", 10)
        _enum(self.validation_status, _E_PROOF_STATUS)
        object.__setattr__(self, "entries", _tuple(self.entries, 0, 32, lambda item: _owned(item, SafeRegistryEntry)))
        object.__setattr__(self, "evaluated_policy_references", _tuple(self.evaluated_policy_references, 0, 32, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        if self.failed_policy_reference is not None:
            _string(self.failed_policy_reference, r"ref:[0-9]{6}", 10)
        if self.failed_field is not None:
            _enum(self.failed_field, _E_VALIDATION_FIELD)
        if self.safe_failure is not None:
            _enum(self.safe_failure, _E_SAFE_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "evidence_reference": _record_value(self.evidence_reference),
            "registry_reference": _record_value(self.registry_reference),
            "availability": _record_value(self.availability),
            "declared_source_authentication": _record_value(self.declared_source_authentication),
            "submitted_source_reference": _record_value(self.submitted_source_reference),
            "current_source_evidence_reference": _record_value(self.current_source_evidence_reference),
            "submitted_profile_evidence_reference": _record_value(self.submitted_profile_evidence_reference),
            "current_profile_evidence_reference": _record_value(self.current_profile_evidence_reference),
            "validation_status": _record_value(self.validation_status),
            "entries": _record_value(self.entries),
            "evaluated_policy_references": _record_value(self.evaluated_policy_references),
            "failed_policy_reference": _record_value(self.failed_policy_reference),
            "failed_field": _record_value(self.failed_field),
            "safe_failure": _record_value(self.safe_failure),
        }


@dataclass(frozen=True, slots=True)
class StorePairReceipt:
    bundle_id: str
    status: ClassVar[object] = 'COMPLETE'
    parts: tuple
    last_included_sequence: int | None
    published: ClassVar[object] = True

    def __post_init__(self):
        _string(self.bundle_id, r"ref:[0-9]{6}", 10)
        object.__setattr__(self, "parts", _tuple(self.parts, 3, 3, lambda item: _owned(item, PartReceipt)))
        if self.last_included_sequence is not None:
            _integer(self.last_included_sequence, 0, 18446744073709551615)
        _coherent(self)

    def to_record(self):
        return {
            "bundle_id": _record_value(self.bundle_id),
            "status": _record_value(self.status),
            "parts": _record_value(self.parts),
            "last_included_sequence": _record_value(self.last_included_sequence),
            "published": _record_value(self.published),
        }


@dataclass(frozen=True, slots=True)
class StorePairFailure:
    bundle_id: str
    status: ClassVar[object] = 'INCOMPLETE'
    parts: tuple
    last_included_sequence: int | None
    failed_part: str
    failure_code: str
    published: ClassVar[object] = False

    def __post_init__(self):
        _string(self.bundle_id, r"ref:[0-9]{6}", 10)
        object.__setattr__(self, "parts", _tuple(self.parts, 3, 3, lambda item: _owned(item, PartReceipt)))
        if self.last_included_sequence is not None:
            _integer(self.last_included_sequence, 0, 18446744073709551615)
        _enum(self.failed_part, _E_EXPORT_PART)
        _enum(self.failure_code, _E_DIAGNOSTICS_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "bundle_id": _record_value(self.bundle_id),
            "status": _record_value(self.status),
            "parts": _record_value(self.parts),
            "last_included_sequence": _record_value(self.last_included_sequence),
            "failed_part": _record_value(self.failed_part),
            "failure_code": _record_value(self.failure_code),
            "published": _record_value(self.published),
        }


@dataclass(frozen=True, slots=True)
class SafeEvidenceSourceBinding:
    source_reference: str
    source_digest_reference: str
    evidence_reference: str
    source_verification: ClassVar[object] = 'DECLARED_NOT_AUTHENTICATED'

    def __post_init__(self):
        _string(self.source_reference, r"ref:[0-9]{6}", 10)
        _string(self.source_digest_reference, r"ref:[0-9]{6}", 10)
        _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        _coherent(self)

    def to_record(self):
        return {
            "source_reference": _record_value(self.source_reference),
            "source_digest_reference": _record_value(self.source_digest_reference),
            "evidence_reference": _record_value(self.evidence_reference),
            "source_verification": _record_value(self.source_verification),
        }


@dataclass(frozen=True, slots=True)
class SafeConditionEvidence:
    condition_reference: str
    source_binding: SafeEvidenceSourceBinding

    def __post_init__(self):
        _string(self.condition_reference, r"ref:[0-9]{6}", 10)
        _owned(self.source_binding, SafeEvidenceSourceBinding)
        _coherent(self)

    def to_record(self):
        return {
            "condition_reference": _record_value(self.condition_reference),
            "source_binding": _record_value(self.source_binding),
        }


@dataclass(frozen=True, slots=True)
class SafePredicateObservationEvidence:
    evidence_reference: str
    status: str
    condition_reference: str
    expected_condition_source: SafeEvidenceSourceBinding
    observed_provider_source: SafeEvidenceSourceBinding
    operation_reference: str
    origin_assessment_reference: str
    registry_reference: str
    registry_source_digest_reference: str
    policy_reference: str
    phase: str
    candidate_state: str
    reason_template: ClassVar[object] = 'RECOVERY_ACTION_RECORDED'

    def __post_init__(self):
        _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        _enum(self.status, _E_PREDICATE_OBSERVATION_STATUS)
        _string(self.condition_reference, r"ref:[0-9]{6}", 10)
        _owned(self.expected_condition_source, SafeEvidenceSourceBinding)
        _owned(self.observed_provider_source, SafeEvidenceSourceBinding)
        _string(self.operation_reference, r"ref:[0-9]{6}", 10)
        _string(self.origin_assessment_reference, r"ref:[0-9]{6}", 10)
        _string(self.registry_reference, r"ref:[0-9]{6}", 10)
        _string(self.registry_source_digest_reference, r"ref:[0-9]{6}", 10)
        _string(self.policy_reference, r"ref:[0-9]{6}", 10)
        _enum(self.phase, _E_PREDICATE_PHASE)
        _string(self.candidate_state, r"[01]{9}", 9)
        _coherent(self)

    def to_record(self):
        return {
            "evidence_reference": _record_value(self.evidence_reference),
            "status": _record_value(self.status),
            "condition_reference": _record_value(self.condition_reference),
            "expected_condition_source": _record_value(self.expected_condition_source),
            "observed_provider_source": _record_value(self.observed_provider_source),
            "operation_reference": _record_value(self.operation_reference),
            "origin_assessment_reference": _record_value(self.origin_assessment_reference),
            "registry_reference": _record_value(self.registry_reference),
            "registry_source_digest_reference": _record_value(self.registry_source_digest_reference),
            "policy_reference": _record_value(self.policy_reference),
            "phase": _record_value(self.phase),
            "candidate_state": _record_value(self.candidate_state),
            "reason_template": _record_value(self.reason_template),
        }


@dataclass(frozen=True, slots=True)
class FallbackHealthRecord:
    cause_code: str
    storage_state: str
    last_confirmed_sequence: int | None
    first_unavailable_sequence: int | None
    last_unavailable_sequence: int | None
    meta_overflow_count: int | None
    clock: ClockObservation
    coverage_status: ClassVar[object] = 'PARTIAL'

    def __post_init__(self):
        _enum(self.cause_code, _E_META_CAUSE_CODE)
        _enum(self.storage_state, _E_STORAGE_STATE)
        if self.last_confirmed_sequence is not None:
            _integer(self.last_confirmed_sequence, 0, 18446744073709551615)
        if self.first_unavailable_sequence is not None:
            _integer(self.first_unavailable_sequence, 0, 18446744073709551615)
        if self.last_unavailable_sequence is not None:
            _integer(self.last_unavailable_sequence, 0, 18446744073709551615)
        if self.meta_overflow_count is not None:
            _integer(self.meta_overflow_count, 0, 18446744073709551615)
        _owned(self.clock, ClockObservation)
        _coherent(self)

    def to_record(self):
        return {
            "cause_code": _record_value(self.cause_code),
            "storage_state": _record_value(self.storage_state),
            "last_confirmed_sequence": _record_value(self.last_confirmed_sequence),
            "first_unavailable_sequence": _record_value(self.first_unavailable_sequence),
            "last_unavailable_sequence": _record_value(self.last_unavailable_sequence),
            "meta_overflow_count": _record_value(self.meta_overflow_count),
            "clock": _record_value(self.clock),
            "coverage_status": _record_value(self.coverage_status),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticsCompletionReceipt:
    operation_reference: str
    status: str
    operation_outcome: str
    confirmed_event_indices: tuple
    diagnostic_coverage: str
    failure_code: str | None
    attempted_event_index: int | None
    health: DiagnosticsHealth

    def __post_init__(self):
        _reference(self.operation_reference)
        _enum(self.status, _E_COMPLETION_STATUS)
        _enum(self.operation_outcome, _E_OBSERVED_OUTCOME)
        object.__setattr__(self, "confirmed_event_indices", _tuple(self.confirmed_event_indices, 0, 768, lambda item: _integer(item, 0, 1023)))
        _enum(self.diagnostic_coverage, _E_OVERALL_COVERAGE)
        if self.failure_code is not None:
            _enum(self.failure_code, _E_DIAGNOSTICS_FAILURE)
        if self.attempted_event_index is not None:
            _integer(self.attempted_event_index, 0, 1023)
        _owned(self.health, DiagnosticsHealth)
        _coherent(self)

    def to_record(self):
        return {
            "operation_reference": _record_value(self.operation_reference),
            "status": _record_value(self.status),
            "operation_outcome": _record_value(self.operation_outcome),
            "confirmed_event_indices": _record_value(self.confirmed_event_indices),
            "diagnostic_coverage": _record_value(self.diagnostic_coverage),
            "failure_code": _record_value(self.failure_code),
            "attempted_event_index": _record_value(self.attempted_event_index),
            "health": _record_value(self.health),
        }


@dataclass(frozen=True, slots=True)
class StorePurgeReceipt:
    bundle_id: str
    status: str
    removed_parts: int
    removed_bytes: int
    failure_code: str | None

    def __post_init__(self):
        _string(self.bundle_id, r"ref:[0-9]{6}", 10)
        _enum(self.status, _E_RETENTION_RECEIPT_STATUS)
        _integer(self.removed_parts, 0, 3)
        _integer(self.removed_bytes, 0, 18446744073709551615)
        if self.failure_code is not None:
            _enum(self.failure_code, _E_DIAGNOSTICS_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "bundle_id": _record_value(self.bundle_id),
            "status": _record_value(self.status),
            "removed_parts": _record_value(self.removed_parts),
            "removed_bytes": _record_value(self.removed_bytes),
            "failure_code": _record_value(self.failure_code),
        }


@dataclass(frozen=True, slots=True)
class SafeExternalEscalationRequired:
    trigger_domain: ClassVar[object] = 'YWE_RECOVERABILITY_CATEGORY'
    recovery_category: ClassVar[object] = 'ESCALATION_REQUIRED'
    authority_status: str

    def __post_init__(self):
        _enum(self.authority_status, _E_AUTHORITY_STATUS)
        _coherent(self)

    def to_record(self):
        return {
            "trigger_domain": _record_value(self.trigger_domain),
            "recovery_category": _record_value(self.recovery_category),
            "authority_status": _record_value(self.authority_status),
        }


@dataclass(frozen=True, slots=True)
class SafeExistingModeBoundary:
    trigger_domain: ClassVar[object] = 'YWE_OBSERVED_MODE_BOUNDARY'
    observed_class: str
    assessment_reference: str

    def __post_init__(self):
        _enum(self.observed_class, _E_EXISTING_MODE_CLASS)
        _string(self.assessment_reference, r"ref:[0-9]{6}", 10)
        _coherent(self)

    def to_record(self):
        return {
            "trigger_domain": _record_value(self.trigger_domain),
            "observed_class": _record_value(self.observed_class),
            "assessment_reference": _record_value(self.assessment_reference),
        }


@dataclass(frozen=True, slots=True)
class SafeRecoverySafetyPolicy:
    policy_id: ClassVar[object] = 'YWE-RECOVERY-SAFETY-001'
    policy_version: ClassVar[object] = '1.0.0'
    policy_document: ClassVar[object] = 'docs/architecture/m3_recovery_safety_policy.md'
    policy_sha256: ClassVar[object] = '00fcee810c5cd445dd0baaaf98c754000347489001e21588eb03afdd1e1ebb95'

    def __post_init__(self):
        _coherent(self)

    def to_record(self):
        return {
            "policy_id": _record_value(self.policy_id),
            "policy_version": _record_value(self.policy_version),
            "policy_document": _record_value(self.policy_document),
            "policy_sha256": _record_value(self.policy_sha256),
        }


@dataclass(frozen=True, slots=True)
class SafeRecoveryDirective:
    requested_action: str
    trigger: str | SafeExternalEscalationRequired | SafeExistingModeBoundary
    origin_assessment_reference: str
    causing_decision_reference: str
    evidence_references: tuple
    actual_mode_status: ClassVar[object] = 'NOT_ENTERED_BY_N2'
    request_origin: str
    policy_binding: SafeRecoverySafetyPolicy | None

    def __post_init__(self):
        _enum(self.requested_action, _E_DIRECTIVE_ACTION)
        _union(self.trigger, ('FALLBACK_FAILURE', 'PROPAGATION_RISK', 'OPERATOR_REQUEST', 'RECOVERY_VALIDATION_FAILURE', 'ESCALATION_FROM_FAILED', 'CONTAINMENT_BREACH', 'OPERATOR_HALT_REQUEST', 'POLICY_HALT_REQUEST', 'UNRESOLVABLE_BLOCKED_RECOVERY'), (SafeExternalEscalationRequired, SafeExistingModeBoundary))
        _string(self.origin_assessment_reference, r"ref:[0-9]{6}", 10)
        _string(self.causing_decision_reference, r"ref:[0-9]{6}", 10)
        object.__setattr__(self, "evidence_references", _tuple(self.evidence_references, 1, 8, lambda item: _string(item, r"ref:[0-9]{6}", 10)))
        _enum(self.request_origin, _E_REQUEST_ORIGIN)
        if self.policy_binding is not None:
            _owned(self.policy_binding, SafeRecoverySafetyPolicy)
        _coherent(self)

    def to_record(self):
        return {
            "requested_action": _record_value(self.requested_action),
            "trigger": _record_value(self.trigger),
            "origin_assessment_reference": _record_value(self.origin_assessment_reference),
            "causing_decision_reference": _record_value(self.causing_decision_reference),
            "evidence_references": _record_value(self.evidence_references),
            "actual_mode_status": _record_value(self.actual_mode_status),
            "request_origin": _record_value(self.request_origin),
            "policy_binding": _record_value(self.policy_binding),
        }


@dataclass(frozen=True, slots=True)
class SafeRecoverySafetyEvidence:
    evidence_reference: str
    operation_reference: str
    origin_assessment_reference: str
    propagation_status: str
    propagation_source_binding: SafeEvidenceSourceBinding
    propagation_was_consulted: bool
    authority_status: str
    authority_source_binding: SafeEvidenceSourceBinding
    authority_was_consulted: bool
    directive: SafeRecoveryDirective | None

    def __post_init__(self):
        _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.operation_reference, r"ref:[0-9]{6}", 10)
        _string(self.origin_assessment_reference, r"ref:[0-9]{6}", 10)
        _enum(self.propagation_status, _E_PROPAGATION_STATUS)
        _owned(self.propagation_source_binding, SafeEvidenceSourceBinding)
        _boolean(self.propagation_was_consulted)
        _enum(self.authority_status, _E_AUTHORITY_STATUS)
        _owned(self.authority_source_binding, SafeEvidenceSourceBinding)
        _boolean(self.authority_was_consulted)
        if self.directive is not None:
            _owned(self.directive, SafeRecoveryDirective)
        _coherent(self)

    def to_record(self):
        return {
            "evidence_reference": _record_value(self.evidence_reference),
            "operation_reference": _record_value(self.operation_reference),
            "origin_assessment_reference": _record_value(self.origin_assessment_reference),
            "propagation_status": _record_value(self.propagation_status),
            "propagation_source_binding": _record_value(self.propagation_source_binding),
            "propagation_was_consulted": _record_value(self.propagation_was_consulted),
            "authority_status": _record_value(self.authority_status),
            "authority_source_binding": _record_value(self.authority_source_binding),
            "authority_was_consulted": _record_value(self.authority_was_consulted),
            "directive": _record_value(self.directive),
        }


@dataclass(frozen=True, slots=True)
class CaptureObjectKey:
    kind: str
    sequence: int | None
    supporting_kind: str | None
    evidence_reference: str | None

    def __post_init__(self):
        _enum(self.kind, _E_CAPTURE_OBJECT_KIND)
        if self.sequence is not None:
            _integer(self.sequence, 0, 18446744073709551615)
        if self.supporting_kind is not None:
            _enum(self.supporting_kind, _E_SUPPORTING_KIND)
        if self.evidence_reference is not None:
            _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        _coherent(self)

    def to_record(self):
        return {
            "kind": _record_value(self.kind),
            "sequence": _record_value(self.sequence),
            "supporting_kind": _record_value(self.supporting_kind),
            "evidence_reference": _record_value(self.evidence_reference),
        }


@dataclass(frozen=True, slots=True)
class CapturePurgeRequest:
    event_sequences: tuple
    supporting_keys: tuple

    def __post_init__(self):
        object.__setattr__(self, "event_sequences", _tuple(self.event_sequences, 0, 1024, lambda item: _integer(item, 0, 18446744073709551615)))
        object.__setattr__(self, "supporting_keys", _tuple(self.supporting_keys, 0, 1928, lambda item: _owned(item, CaptureObjectKey)))
        _coherent(self)

    def to_record(self):
        return {
            "event_sequences": _record_value(self.event_sequences),
            "supporting_keys": _record_value(self.supporting_keys),
        }


@dataclass(frozen=True, slots=True)
class CaptureRemovalObservation:
    key: CaptureObjectKey
    status: str
    removed_bytes: int | None
    failure_code: str | None

    def __post_init__(self):
        _owned(self.key, CaptureObjectKey)
        _enum(self.status, _E_CAPTURE_REMOVAL_STATUS)
        if self.removed_bytes is not None:
            _integer(self.removed_bytes, 0, 18446744073709551615)
        if self.failure_code is not None:
            _enum(self.failure_code, _E_DIAGNOSTICS_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "key": _record_value(self.key),
            "status": _record_value(self.status),
            "removed_bytes": _record_value(self.removed_bytes),
            "failure_code": _record_value(self.failure_code),
        }


@dataclass(frozen=True, slots=True)
class StoreCapturePurgeReceipt:
    status: str
    observations: tuple
    failure_code: str | None

    def __post_init__(self):
        _enum(self.status, _E_CAPTURE_PURGE_STATUS)
        object.__setattr__(self, "observations", _tuple(self.observations, 1, 1928, lambda item: _owned(item, CaptureRemovalObservation)))
        if self.failure_code is not None:
            _enum(self.failure_code, _E_DIAGNOSTICS_FAILURE)
        _coherent(self)

    def to_record(self):
        return {
            "status": _record_value(self.status),
            "observations": _record_value(self.observations),
            "failure_code": _record_value(self.failure_code),
        }


@dataclass(frozen=True, slots=True)
class SafeTargetValidityEvidence:
    evidence_reference: str
    source_evidence_reference: str
    profile_evidence_reference: str
    state_validity_diagnostic: SafeStateValidity

    def __post_init__(self):
        _string(self.evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.source_evidence_reference, r"ref:[0-9]{6}", 10)
        _string(self.profile_evidence_reference, r"ref:[0-9]{6}", 10)
        _owned(self.state_validity_diagnostic, SafeStateValidity)
        _coherent(self)

    def to_record(self):
        return {
            "evidence_reference": _record_value(self.evidence_reference),
            "source_evidence_reference": _record_value(self.source_evidence_reference),
            "profile_evidence_reference": _record_value(self.profile_evidence_reference),
            "state_validity_diagnostic": _record_value(self.state_validity_diagnostic),
        }


VALUE_TYPES = (SourceProvenance, DiagnosticsEnvironment, DiagnosticsIdentity, DiagnosticsProfile, DiagnosticLimits, CaptureRelation, MissingCoverage, RetentionBoundary, DiagnosticsHealth, ClockObservation, CaptureWindow, SafeDiagnosticEnvelope, SafeOrbit, SafeStateContext, SafeError, DiagnosticEvent, EvidenceFact, ExpectedBehavior, DiagnosticIncident, SourcePin, SupportingEvidence, RedactionEntry, RedactionAccount, RetentionAccount, Limitation, DiagnosticSnapshot, MetaCause, StorageReceipt, PartReceipt, ExportReceipt, ExportFailure, RetentionReceipt, StorageVerification, SafeProfileEvidence, SafeInputState, SafeStateValidity, SafePredicate, SafeAssessmentEvidence, SafeRecoveryStep, SafeRecoveryDiagnostic, PrivateAcknowledgmentWitness, DiagnosticCounterState, MetaDiagnosticRecord, RecoveryAdmissionReceipt, SafeSourceEvidence, SafeNormalizationProof, SafeCorrectionProof, SafeRegistryEntry, SafeRegistryProof, StorePairReceipt, StorePairFailure, SafeEvidenceSourceBinding, SafeConditionEvidence, SafePredicateObservationEvidence, FallbackHealthRecord, DiagnosticsCompletionReceipt, StorePurgeReceipt, SafeExternalEscalationRequired, SafeExistingModeBoundary, SafeRecoverySafetyPolicy, SafeRecoveryDirective, SafeRecoverySafetyEvidence, CaptureObjectKey, CapturePurgeRequest, CaptureRemovalObservation, StoreCapturePurgeReceipt, SafeTargetValidityEvidence,)

CONTEXT_FIELDS = ('input_state', 'actual_state', 'selected_target', 'eligible_targets', 'codeword_chain', 'admissibility_status', 'transformation_compatibility', 'normalization_status', 'recoverability_relevance', 'is_valid', 'orbit_info', 'system_state_class', 'recovery_category', 'predicate_name', 'predicate_value', 'candidate_order_index', 'step_index', 'profile_reference', 'source_evidence_reference', 'fixture_reference', 'profile_evidence_reference', 'original_assessment_reference', 'post_assessment_reference', 'recovery_diagnostic_reference', 'before_state', 'codeword', 'after_state', 'policy_reference', 'validation_status', 'failed_field', 'proof_evidence_reference', 'recovery_safety_evidence_reference')
COUNTER_FIELDS = ('accepted_count', 'rejected_count', 'retained_count', 'expired_count', 'lost_count', 'redacted_field_count', 'redacted_reference_count', 'meta_overflow_count')

def _same_optional_reason(value, reason):
    if (value is None) != (reason is not None):
        _invalid()


def _unique(values):
    if len(set(values)) != len(values):
        _invalid()


def _coherent(value):
    kind = type(value)
    if kind is SourceProvenance:
        if value.status == "UNKNOWN":
            if value.verified_revision is not None or value.unavailable_reason is None or value.dirty_path_aliases:
                _invalid()
        elif value.verified_revision is None or value.unavailable_reason is not None or bool(value.dirty_path_aliases) != (value.status == "VERIFIED_DIRTY"):
            _invalid()
        _unique(value.dirty_path_aliases)
    elif kind is DiagnosticsEnvironment:
        unavailable = tuple(row.source for row in value.unavailable_fields)
        _unique(unavailable)
        for name, unknown, source in (("os_kind", "UNKNOWN", "ENVIRONMENT_OS"), ("architecture", "UNKNOWN", "ARCHITECTURE"), ("host_class", "UNKNOWN", "HOST_CLASS")):
            if (getattr(value, name) == unknown) != (source in unavailable):
                _invalid()
        if (value.runtime_version is None) != ("RUNTIME_VERSION" in unavailable):
            _invalid()
    elif kind is DiagnosticsIdentity:
        if value.source_revision != value.source_provenance.verified_revision:
            _invalid()
        if (value.implementation_id, value.profile_id) not in (("REFERENCE_DEVELOPMENT_DIAGNOSTICS", "REFERENCE_DEVELOPMENT"), ("REFERENCE_RELEASE_DIAGNOSTICS", "REFERENCE_RELEASE")):
            _invalid()
    elif kind is DiagnosticsProfile:
        development = value.profile_id == "REFERENCE_DEVELOPMENT"
        if value.development_payloads_enabled != development or value.implementation_id != ("REFERENCE_DEVELOPMENT_DIAGNOSTICS" if development else "REFERENCE_RELEASE_DIAGNOSTICS"):
            _invalid()
    elif kind is MissingCoverage:
        if (value.status == "AVAILABLE") != (value.reason is None):
            _invalid()
    elif kind is RetentionBoundary:
        if value.first_sequence > value.last_sequence or value.record_count == 0 or value.record_count > value.last_sequence - value.first_sequence + 1:
            _invalid()
    elif kind is ClockObservation:
        _same_optional_reason(value.observed_utc, value.utc_reason)
        _same_optional_reason(value.monotonic_nanoseconds, value.monotonic_reason)
    elif kind is CaptureWindow:
        if (value.first_sequence is None) != (value.last_sequence is None):
            _invalid()
        if value.first_sequence is not None and value.first_sequence > value.last_sequence:
            _invalid()
        if value.start.monotonic_nanoseconds is not None and value.end.monotonic_nanoseconds is not None and value.end.monotonic_nanoseconds < value.start.monotonic_nanoseconds:
            if value.end.monotonic_reason != "CLOCK_REGRESSION":
                _invalid()
    elif kind is SafeDiagnosticEnvelope:
        _unique(value.rule_ids)
    elif kind is SafeStateContext:
        absent = tuple(field.upper() for field in CONTEXT_FIELDS if getattr(value, field) is None)
        if set(value.unavailable_fields) != set(absent) or len(value.unavailable_fields) != len(absent):
            _invalid()
    elif kind is SafeError:
        _unique(value.omitted_error_material)
    elif kind is DiagnosticEvent:
        _same_optional_reason(value.duration_nanoseconds, value.duration_reason)
        if (value.envelope is None) != (value.diagnostic_reference is None):
            _invalid()
        if value.envelope is not None and value.event_type not in ("DIAGNOSTIC", "META_DIAGNOSTIC"):
            _invalid()
        if value.envelope is not None and value.event_id != value.diagnostic_reference:
            _invalid()
    elif kind is EvidenceFact:
        _unique(value.event_references)
    elif kind is DiagnosticIncident:
        _unique(value.timeline_event_references)
        if value.trigger_event_reference not in value.timeline_event_references:
            _invalid()
        allowed = set(value.timeline_event_references)
        if any(reference not in allowed for reference in value.attempt_event_references + value.state_event_references):
            _invalid()
        if any(reference not in allowed for fact in value.observed_facts + value.supported_findings for reference in fact.event_references):
            _invalid()
    elif kind is DiagnosticCounterState:
        if value.status == "EXACT" and value.reason is not None:
            _invalid()
        if value.status == "SATURATED" and value.reason != "COUNTER_LIMIT":
            _invalid()
        if value.status == "UNAVAILABLE" and value.reason != "STORAGE_UNCONFIRMED":
            _invalid()
    elif kind is DiagnosticsHealth:
        if tuple(row.field for row in value.counter_states) != enum_values("CounterField"):
            _invalid()
        for field, state in zip(COUNTER_FIELDS, value.counter_states):
            count = getattr(value, field)
            if state.status == "EXACT" and count is None:
                _invalid()
            if state.status == "SATURATED" and count != 18446744073709551615:
                _invalid()
            if state.status == "UNAVAILABLE" and count is not None:
                _invalid()
        if (value.first_unavailable_sequence is None) != (value.last_unavailable_sequence is None):
            _invalid()
        if value.first_unavailable_sequence is not None and value.first_unavailable_sequence > value.last_unavailable_sequence:
            _invalid()
        if any(row.status == "AVAILABLE" for row in value.missing_sources):
            _invalid()
        _unique(tuple(row.source for row in value.missing_sources))
    elif kind is RedactionEntry:
        if value.count == 0:
            _invalid()
    elif kind is RedactionAccount:
        if value.field_count != sum(row.count for row in value.entries if row.reason != "OPAQUE_REFERENCE_ALIAS") or value.reference_count != sum(row.count for row in value.entries if row.reason == "OPAQUE_REFERENCE_ALIAS"):
            _invalid()
    elif kind is SafeProfileEvidence:
        _same_optional_reason(value.recognized_valid_states, value.unavailable_reason)
        if (value.availability == "AVAILABLE") != (value.recognized_valid_states is not None):
            _invalid()
        if value.recognized_valid_states is not None and tuple(sorted(set(value.recognized_valid_states))) != value.recognized_valid_states:
            _invalid()
    elif kind is SafeInputState:
        if value.kind == "ASH_STATE":
            if value.state is None or value.failure_code is not None:
                _invalid()
        elif value.state is not None or value.failure_code is None:
            _invalid()
    elif kind is SafeStateValidity:
        row = (value.admissibility_status, value.transformation_compatibility, value.normalization_status, value.recoverability_relevance, value.is_valid)
        if row not in sv.DIAGNOSTIC_ROWS:
            _invalid()
        if value.admissibility_status == "UNCLASSIFIED":
            if value.orbit_info is not None:
                _invalid()
        elif value.orbit_info is None or value.orbit_info.contains_known_valid_state != (value.admissibility_status != "TRANSFORMATION_INCOMPATIBLE"):
            _invalid()
        if value.input_state.kind == "REJECTED" and value.admissibility_status != "UNCLASSIFIED":
            _invalid()
        if any(rule not in sv.ASSESSMENT_RULE_IDS for rule in value.rule_ids):
            _invalid()
        _unique(value.rule_ids)
    elif kind is SafePredicate:
        if (value.evaluation_status == "EVALUATED") != (value.value is not None):
            _invalid()
    elif kind is SafeAssessmentEvidence:
        if (value.system_state_class is None) != (value.recovery_category is None):
            _invalid()
        if value.system_state_class is not None and (value.system_state_class, value.recovery_category) not in sv.RECOVERY_CATEGORY_PAIRS:
            _invalid()
        if (value.parsed_state is None) != (value.state_validity_diagnostic.input_state.kind == "REJECTED"):
            _invalid()
        if value.parsed_state is not None and value.parsed_state != value.state_validity_diagnostic.input_state.state:
            _invalid()
        if any(name not in ("CORRECTION_PATH_IS_KNOWN", "FALLBACK_IS_AVAILABLE") for name in value.consulted_predicates):
            _invalid()
        _unique(value.consulted_predicates)
        for predicate in (value.correction_path_is_known, value.fallback_is_available):
            if value.system_state_class is not None and predicate is not None and predicate.assessment_reference != value.assessment_reference:
                _invalid()
    elif kind is SafeRecoveryStep:
        if tuple(sorted(set(value.event_indices))) != value.event_indices:
            _invalid()
    elif kind is SafeRecoveryDiagnostic:
        if (value.original_state_class, value.recovery_category) not in sv.RECOVERY_CATEGORY_PAIRS:
            _invalid()
        _unique(value.rule_ids)
    elif kind is SafeSourceEvidence:
        expected = ("ASH_AGGREGATE", "ASH_STATE_SPACE", "ASH_CODEWORDS", "ASH_VALIDITY", "ASH_CLASSIFICATION", "ASH_RECOVERY", "ASH_DIAGNOSTIC_SCHEMA", "ASH_TAXONOMY")
        if tuple(pin.source_kind for pin in value.verified_pins) != expected:
            _invalid()
        if tuple(pin.sha256 for pin in value.verified_pins) != tuple(digest for _, digest in sv.CANONICAL_BINDING_FIELDS[1:]):
            _invalid()
    elif kind is SafeNormalizationProof:
        if value.origin_validation_status == "REJECTED" and value.plan_validation_status == "VERIFIED":
            _invalid()
        if value.plan_validation_status == "VERIFIED" and (value.failed_field is not None or value.safe_failure is not None):
            _invalid()
        if value.plan_validation_status == "REJECTED" and (value.failed_field is None or value.safe_failure is None):
            _invalid()
        for targets in (value.submitted_targets, value.expected_targets):
            if targets is not None and tuple(sorted(set(targets))) != targets:
                _invalid()
    elif kind is SafeCorrectionProof:
        if value.correction_validation_status == "VERIFIED" and (value.computed_target is None or value.target_diagnostic_reference is None or value.failed_field is not None or value.safe_failure is not None):
            _invalid()
        if value.correction_validation_status == "REJECTED" and (value.failed_field is None or value.safe_failure is None):
            _invalid()
    elif kind is SafeRegistryProof:
        if tuple(row.input_order_index for row in value.entries) != tuple(range(len(value.entries))):
            _invalid()
        _unique(tuple(row.policy_reference for row in value.entries))
        if value.validation_status == "VERIFIED" and (value.failed_field is not None or value.safe_failure is not None or value.failed_policy_reference is not None):
            _invalid()
        if value.validation_status == "REJECTED" and (value.failed_field is None or value.safe_failure is None):
            _invalid()
        _unique(value.evaluated_policy_references)
        if any(reference not in tuple(row.policy_reference for row in value.entries) for reference in value.evaluated_policy_references):
            _invalid()
    elif kind is SafeRecoveryDirective:
        if value.request_origin == "POLICY":
            if value.policy_binding is None or value.trigger != "OPERATOR_REQUEST":
                _invalid()
        elif value.policy_binding is not None:
            _invalid()
        if type(value.trigger) is SafeExistingModeBoundary:
            if value.request_origin != "OBSERVED_EXISTING_MODE" or value.trigger.assessment_reference != value.origin_assessment_reference or value.requested_action != ("REMAIN_SAFE_HALT" if value.trigger.observed_class == "SAFE_HALT" else "REMAIN_CONTAINED"):
                _invalid()
        elif value.request_origin == "OBSERVED_EXISTING_MODE":
            _invalid()
        if type(value.trigger) is SafeExternalEscalationRequired and value.requested_action != "REQUEST_EXTERNAL_AUTHORITY":
            _invalid()
        _unique(value.evidence_references)
    elif kind is SafeRecoverySafetyEvidence:
        if value.directive is not None and value.directive.origin_assessment_reference != value.origin_assessment_reference:
            _invalid()
    elif kind is StorageVerification:
        if value.status == "VERIFIED" and (not all((value.persistent_acls, value.owner_matches_effective_sid, value.dacl_protected, value.no_reparse_path, value.trusted_parent, value.stable_identity)) or value.failure_code is not None):
            _invalid()
        if value.status == "REJECTED" and value.failure_code is None:
            _invalid()
        if value.grant_principals != ("EFFECTIVE_USER", "SYSTEM"):
            _invalid()
    elif kind is StorageReceipt:
        if (value.status == "COMMITTED") != (value.failure_code is None):
            _invalid()
    elif kind is PartReceipt:
        if (value.part, value.relative_name) not in (("JSON", "diagnostics.json"), ("MARKDOWN", "diagnostics.md"), ("MANIFEST", "manifest.json")):
            _invalid()
        if value.status == "CONFIRMED" and (value.bytes is None or value.sha256 is None or value.failure_code is not None):
            _invalid()
        if value.status == "NOT_WRITTEN" and (value.bytes is not None or value.sha256 is not None):
            _invalid()
    elif kind in (StorePairReceipt, StorePairFailure, ExportReceipt, ExportFailure):
        if tuple(part.part for part in value.parts) != ("JSON", "MARKDOWN", "MANIFEST"):
            _invalid()
        if kind in (StorePairReceipt, ExportReceipt) and any(part.status != "CONFIRMED" for part in value.parts):
            _invalid()
        if kind in (ExportReceipt, ExportFailure) and value.snapshot.bundle_id != value.bundle_id:
            _invalid()
        if kind is ExportReceipt and value.last_included_sequence != value.snapshot.capture_window.last_sequence:
            _invalid()
    elif kind is StorePurgeReceipt:
        if (value.status == "COMPLETED") != (value.failure_code is None):
            _invalid()
    elif kind is RecoveryAdmissionReceipt:
        if value.status == "CONFIRMED":
            if (value.reserved_events, value.reserved_bytes) not in ((768, 31588352), (1, 270336)) or value.failure_code is not None:
                _invalid()
        elif value.reserved_events or value.reserved_bytes or value.failure_code is None:
            _invalid()
        _unique(value.origin_diagnostic_references)
    elif kind is DiagnosticsCompletionReceipt:
        if tuple(sorted(set(value.confirmed_event_indices))) != value.confirmed_event_indices:
            _invalid()
        if value.status == "COMPLETE":
            if value.failure_code is not None or value.attempted_event_index is not None:
                _invalid()
        elif value.failure_code is None or value.diagnostic_coverage == "COMPLETE_DECLARED_REFERENCE_SCOPE":
            _invalid()
    elif kind is MetaDiagnosticRecord:
        envelope = value.envelope
        if (envelope.diagnostic_kind, envelope.stage, envelope.severity, envelope.disposition, envelope.parent_diagnostic_reference, envelope.chain_root_reference, envelope.rule_ids) != ("STATE_VALIDITY", "DETECTION", "ERROR", "BLOCKED", None, value.meta_reference, ("ASH-STATE-GENERAL-001",)):
            _invalid()
    elif kind is DiagnosticSnapshot:
        _same_optional_reason(value.generated_at_utc, value.generation_time_reason)
        if value.identity.profile_id != value.profile.profile_id or value.identity.implementation_id != value.profile.implementation_id:
            _invalid()
        if tuple(row.source for row in value.coverage) != enum_values("CoverageSource"):
            _invalid()
        sequences = tuple(event.local_sequence for event in value.events)
        if tuple(sorted(set(sequences))) != sequences:
            _invalid()
        aliases = tuple(event.event_id for event in value.events) + tuple(record.meta_reference for record in value.meta_diagnostics)
        _unique(aliases)
        allowed = set(aliases)
        for incident in value.incidents:
            if any(reference not in allowed for reference in incident.timeline_event_references):
                _invalid()
        if value.capture_window.first_sequence != (min(sequences) if sequences else None) or value.capture_window.last_sequence != (max(sequences) if sequences else None):
            _invalid()
        if value.redaction.field_count != value.health.redacted_field_count or value.redaction.reference_count != value.health.redacted_reference_count:
            _invalid()

    elif kind is CaptureObjectKey:
        if value.kind == "EVENT":
            if value.sequence is None or value.supporting_kind is not None or value.evidence_reference is not None:
                _invalid()
        elif value.sequence is not None or value.supporting_kind is None or value.evidence_reference is None:
            _invalid()
    elif kind is CapturePurgeRequest:
        if (bool(value.event_sequences) == bool(value.supporting_keys)):
            _invalid()
        if value.event_sequences != tuple(sorted(set(value.event_sequences))):
            _invalid()
        keys = tuple((key.supporting_kind, key.evidence_reference) for key in value.supporting_keys)
        if any(key.kind != "SUPPORTING" for key in value.supporting_keys) or keys != tuple(sorted(set(keys))):
            _invalid()
    elif kind is CaptureRemovalObservation:
        if value.status == "REMOVED":
            if value.removed_bytes is None or value.failure_code is not None:
                _invalid()
        elif value.status == "NOT_REMOVED":
            if value.removed_bytes != 0 or value.failure_code is None:
                _invalid()
        elif value.removed_bytes is not None or value.failure_code is None:
            _invalid()
    elif kind is StoreCapturePurgeReceipt:
        removed = sum(row.status == "REMOVED" for row in value.observations)
        if value.status == "COMPLETED":
            if removed != len(value.observations) or value.failure_code is not None:
                _invalid()
        elif value.status == "PARTIAL":
            if not 0 < removed < len(value.observations) or value.failure_code is None:
                _invalid()
        elif removed or value.failure_code is None:
            _invalid()
        keys = tuple((row.key.kind, row.key.sequence, row.key.supporting_kind, row.key.evidence_reference) for row in value.observations)
        if len(set(keys)) != len(keys) or len({row.key.kind for row in value.observations}) != 1:
            _invalid()
