"""Closed immutable N3 lifecycle values [YWE-REQ-0044].

Constructors own representation and cross-field truth. RecoveryEngine's
lifecycle collaborator owns issuance, current assessment membership and effects.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, field
import json
import re
import threading

from . import state_values as state
from . import normalization_values as normalization
from . import recovery_values as recovery
from . import diagnostics_values as diagnostics

MAX_GENERATION = (1 << 64) - 1
MAX_RAW_BUSINESS_BYTES = 33554432
SESSION_POLICY_BINDING_FIELDS = (
    ("policy_id", "YWE-SESSION-SAFETY-001"),
    ("policy_version", "1.0.0"),
    ("source_path", "docs/architecture/m3_session_lifecycle_policy.md"),
    ("source_sha256", "24e2584279b95b8e3659bd61e6b5149311f344b03b981e88f74ae37775591910"),
)
MODULE_SESSION_POLICY_BINDING_FIELDS = (
    ("policy_id", "YWE-SESSION-SAFETY-001"),
    ("policy_version", "1.1.0"),
    ("source_path", "docs/architecture/m3_module_session_lifecycle_policy.md"),
    ("source_sha256", "173e36fd92d6aaf222d61d950a235a6938e0fcdd374f6044b9f0c2c38c342dc7"),
)
CONTAINMENT_RULES = dict(zip(recovery.CONTAINMENT_TRIGGERS, (
    "ASH-CONTAINMENT-TRIGGER-001", "ASH-CONTAINMENT-TRIGGER-002",
    "ASH-CONTAINMENT-TRIGGER-003", "ASH-CONTAINMENT-TRIGGER-004",
)))
HALT_RULES = {
    "CONTAINMENT_BREACH": "ASH-HALT-TRIGGER-001",
    "ESCALATION_FROM_FAILED": "ASH-HALT-TRIGGER-002",
    "OPERATOR_HALT_REQUEST": "ASH-HALT-TRIGGER-003",
    "POLICY_HALT_REQUEST": "ASH-HALT-TRIGGER-004",
    "UNRESOLVABLE_BLOCKED_RECOVERY": "ASH-HALT-TRIGGER-005",
}
_PACKETS = (recovery.RecoveryNoAction, recovery.RecoveredValue,
            recovery.RecoveredFallbackValue, recovery.RecoveryHandoff,
            recovery.RecoveryFailure)
_PROFILES = (state.AvailableProfileBinding, state.UnavailableProfileBinding)
_SYSTEM_CLASSES = tuple(pair[0] for pair in state.RECOVERY_CATEGORY_PAIRS)
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}", re.ASCII)

SESSION_MODES = ('NORMAL', 'CONTAINED', 'SAFE_HALT')
SESSION_ADMISSION_STATUSES = ('OPEN', 'AUDIT_BLOCKED', 'TERMINAL')
SESSION_ACTIONS = ('RECOVER', 'REQUEST_CONTAINMENT', 'RESOLVE_CONTAINMENT', 'REQUEST_HALT')
LEASE_ACTIONS = ('RECOVER', 'CONTAIN', 'RESOLVE', 'HALT')
SESSION_AUTHORITY_STATUSES = ('AUTHORIZED', 'DENIED', 'UNAVAILABLE')
SESSION_AUTHORITY_ORIGINS = ('OPERATOR', 'POLICY', 'SYSTEM_BOUNDARY')
SESSION_BOUNDARY_CONDITIONS = ('CONTAINMENT_BREACH', 'CONTAINMENT_UNAVAILABLE', 'CONTAINMENT_CLEAR', 'RECOVERY_NO_PATH', 'RECOVERY_VALIDATION_FAILURE', 'PROPAGATION_RISK')
SESSION_BOUNDARY_STATUSES = ('SATISFIED', 'NOT_SATISFIED', 'UNAVAILABLE')
SESSION_CAUSE_KINDS = ('N2_HANDOFF', 'AUTHORITY_REQUEST', 'CONTAINMENT_BREACH', 'UNRESOLVABLE_BLOCKED_BOUNDARY', 'RECOVERY_VALIDATION_BOUNDARY', 'N2_RESULT', 'PROPAGATION_RISK_BOUNDARY')
SESSION_ADMISSION_DECISIONS = ('GRANTED', 'REJECTED')
PUBLICATION_STATUSES = ('COMMITTED', 'NOT_COMMITTED', 'UNCONFIRMED')
RESOLUTION_ROUTES = ('OPERATOR_INTERVENTION', 'POLICY_DRIVEN', 'ESCALATE_TO_SAFE_HALT')
RESOLUTION_ACTIONS = ('REPLACE_STATE', 'HALT')
RESOLUTION_STATUSES = ('RESOLVED', 'REFUSED', 'UNCONFIRMED')
SESSION_OPERATION_STATUSES = ('COMPLETED', 'REFUSED', 'FAILED', 'TERMINAL_REFUSAL', 'UNCONFIRMED')
LIFECYCLE_KINDS = ('RECOVERY', 'CONTAINMENT', 'SAFE_HALT')
LIFECYCLE_CAPTURE_STATUSES = ('CONFIRMED', 'REJECTED', 'NOT_CONFIRMED')
LIFECYCLE_CAPTURE_CODES = ('CAPTURE_ADMISSION_REJECTED', 'CAPTURE_ADMISSION_UNCONFIRMED', 'CAPTURE_APPEND_REJECTED', 'CAPTURE_APPEND_UNCONFIRMED', 'CAPTURE_COMPLETION_REJECTED', 'CAPTURE_COMPLETION_UNCONFIRMED', 'CAPTURE_FINAL_OBSERVATION_FAILED', 'CAPTURE_RETENTION_FAILED', 'CAPTURE_CLOCK_UNAVAILABLE', 'CAPTURE_CHAIN_UNCONFIRMED')
SESSION_FAILURE_CODES = ('SESSION_INPUT_INVALID', 'SESSION_SOURCE_REJECTED', 'SESSION_PROFILE_REJECTED', 'SESSION_ORIGIN_REJECTED', 'SESSION_ORIGIN_FOREIGN', 'SESSION_STATE_STALE', 'SESSION_OPERATION_DUPLICATE', 'SESSION_OPERATION_IN_PROGRESS', 'SESSION_MODE_FORBIDDEN', 'SESSION_TERMINAL', 'SESSION_BUDGET_EXCEEDED', 'SESSION_LEASE_REJECTED', 'SESSION_EXECUTION_CANCELLED', 'SESSION_AUTHORITY_DENIED', 'SESSION_AUTHORITY_UNAVAILABLE', 'SESSION_EVIDENCE_MISMATCH', 'SESSION_BOUNDARY_NOT_SATISFIED', 'SESSION_TARGET_NOT_VALID', 'SESSION_N2_RESULT_REJECTED', 'SESSION_N2_COMPLETION_REJECTED', 'SESSION_N2_COMPLETION_UNCONFIRMED', 'SESSION_PUBLICATION_STALE', 'SESSION_PUBLICATION_UNCONFIRMED', 'SESSION_COLLABORATOR_FAILED', 'SESSION_CAPTURE_FAILED', 'SESSION_RETENTION_FAILED', 'SESSION_GENERATION_EXHAUSTED', 'SESSION_AUDIT_BLOCKED', 'SESSION_RAW_BUSINESS_LIMIT', 'SESSION_INTERNAL_INVARIANT')
SESSION_FIELD_PATHS = ('binding', 'binding.canonical_binding', 'binding.recovery_binding', 'binding.profile_binding', 'binding.policy_binding', 'request', 'request.reference', 'request.session_reference', 'request.expected_snapshot', 'request.action', 'origin_assessment', 'origin_assessment.source_binding', 'origin_assessment.profile_binding', 'operation_context', 'operation_context.context_observation', 'operation_context.propagation_evidence', 'operation_context.external_authority_evidence', 'authority', 'boundary', 'cause', 'trigger', 'lease', 'publication', 'publication.before', 'publication.after', 'resolution', 'resolution.route', 'resolution.target', 'resolution.target_validation', 'resolution.boundary_clear', 'capture', 'capture.admission', 'capture.append', 'capture.finish', 'capture.final_observation', 'retention', 'clock', 'history', 'generation', 'collaborator', 'execution_gate', 'raw_business_packet')
STAGE_GRANT_KINDS = ('REGISTRY_READ', 'CAPTURE_BEGIN', 'NORMALIZATION_PROVIDER', 'CORRECTION_PROVIDER', 'CONDITION_PROVIDER', 'POST_FACTS_PROVIDER', 'CANDIDATE_COMPUTATION', 'ASSESSMENT_BEGIN', 'ASSESSMENT_APPEND', 'ASSESSMENT_COMPLETE', 'CAPTURE_APPEND')
STAGE_GRANT_KINDS = STAGE_GRANT_KINDS + ('MODULE_ORIGIN_DIAGNOSE', 'PURE_MODULE_COMPUTE', 'MODULE_CAPTURE_BEGIN', 'MODULE_FINAL_OBSERVATION')
RESTRICTED_OPERATIONS = ('READ_SESSION', 'READ_DIAGNOSTICS', 'EXPORT_DIAGNOSTICS', 'REQUEST_HALT', 'RESOLVE_CONTAINMENT')
LIFECYCLE_CANONICAL_FIELDS = ('trigger', 'original_diagnostic', 'system_state_class', 'restricted_operations', 'containment_time', 'awaiting_resolution', 'resolution', 'halt_time', 'full_diagnostic_chain', 'is_terminal', 'rule_ids', 'notes', 'envelope', 'parent_diagnostic_reference', 'chain_root_reference')
PENDING_LIFECYCLE_REASONS = ('ORIGINAL_DIAGNOSIS_UNAVAILABLE', 'ORIGINAL_CLASSIFICATION_UNAVAILABLE', 'CHAIN_UNCONFIRMED', 'CLOCK_UNAVAILABLE', 'CAPTURE_UNCONFIRMED', 'RAW_BUSINESS_LIMIT')
SESSION_RETENTION_STATUSES = ('CONFIRMED', 'REJECTED', 'NOT_CONFIRMED')
SESSION_RETENTION_PHASES = ('REGISTER', 'ATTACH', 'PIN', 'FREEZE', 'FINAL_RESULT')
SESSION_RETENTION_COVERAGES = ('COMPLETE_SPECIFIED_SAFE_GRAPH', 'PARTIAL', 'STORAGE_UNCERTAIN')
SESSION_RETENTION_FAILURES = ('SESSION_RETENTION_REJECTED', 'SESSION_RETENTION_UNCONFIRMED', 'SESSION_RETENTION_INCOMPLETE', 'SESSION_RETENTION_LIMIT', 'SESSION_RETENTION_IDENTITY_MISMATCH', 'SESSION_RETENTION_FROZEN')

class SessionContractError(ValueError):
    """A bounded exact structural refusal; no arbitrary caller evidence."""
    def __init__(self, failure_code, field_name):
        if type(failure_code) is not str or failure_code not in SESSION_FAILURE_CODES:
            raise ValueError("invalid session failure code")
        if type(field_name) is not str or field_name not in SESSION_FIELD_PATHS:
            raise ValueError("invalid session failure field")
        self.failure_code = failure_code
        self.field_name = field_name
        super().__init__(f"{failure_code}: {field_name}")


def _fail(field, code="SESSION_INPUT_INVALID"):
    raise SessionContractError(code, field)


def _exact(value, kinds, field):
    allowed = kinds if type(kinds) is tuple else (kinds,)
    if not any(type(value) is kind for kind in allowed):
        _fail(field)


def _choice(value, choices, field):
    if type(value) is not str or value not in choices:
        _fail(field)


def _reference(value, field, maximum=256):
    if (type(value) is not str or len(value) > maximum or
            _IDENTIFIER.fullmatch(value) is None or value in ("NONE", "SELF")):
        _fail(field)


def _reason(value, field):
    if type(value) is not str or not 1 <= len(value) <= 512 or "\0" in value:
        _fail(field)


def _integer(value, minimum, maximum, field):
    if type(value) is not int or not minimum <= value <= maximum:
        _fail(field)


def _constant(value, expected, field):
    if type(value) is not type(expected) or value != expected:
        _fail(field)


def _sequence(value, check, minimum, maximum, field):
    _exact(value, (tuple, list), field)
    if not minimum <= len(value) <= maximum:
        _fail(field)
    for item in value:
        check(item, field)
    return tuple(value)


def _same(value, expected, field):
    if value != expected:
        _fail(field, "SESSION_EVIDENCE_MISMATCH")


class _Record:
    def to_record(self):
        try:
            return raw_business_record(self)
        except SessionContractError as error:
            if type(self) is SessionHistory and error.failure_code == "SESSION_RAW_BUSINESS_LIMIT":
                raise SessionContractError("SESSION_RAW_BUSINESS_LIMIT", "history") from None
            raise

def _integer_choice(value, choices, field):
    if value not in choices:
        _fail(field)


@dataclass(frozen=True, slots=True)
class SessionPolicyBinding(_Record):
    policy_id: str
    policy_version: str
    source_path: str
    source_sha256: str

    def __post_init__(self):
        for name, _ in SESSION_POLICY_BINDING_FIELDS:
            _exact(getattr(self, name), str, 'request')
        actual = tuple((name, getattr(self, name)) for name, _ in SESSION_POLICY_BINDING_FIELDS)
        if actual not in (SESSION_POLICY_BINDING_FIELDS, MODULE_SESSION_POLICY_BINDING_FIELDS):
            _fail('binding.policy_binding', 'SESSION_SOURCE_REJECTED')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionBinding(_Record):
    binding_reference: str
    session_reference: str
    canonical_binding: state.CanonicalAshBinding
    recovery_binding: recovery.RecoverySourceBinding
    profile_binding: object
    policy_binding: SessionPolicyBinding
    initial_assessment_reference: str

    def __post_init__(self):
        _reference(self.binding_reference, 'request')
        _reference(self.session_reference, 'request.session_reference')
        _exact(self.canonical_binding, state.CanonicalAshBinding, 'binding.canonical_binding')
        _exact(self.recovery_binding, recovery.RecoverySourceBinding, 'binding.recovery_binding')
        _exact(self.profile_binding, (state.AvailableProfileBinding, state.UnavailableProfileBinding,), 'binding.profile_binding')
        _exact(self.policy_binding, SessionPolicyBinding, 'binding.policy_binding')
        _reference(self.initial_assessment_reference, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionSnapshot(_Record):
    snapshot_reference: str
    binding: SessionBinding
    generation: int
    current_state: state.AshState
    mode: str
    terminal_latched: bool
    admission_status: str
    containment_reference: str | None
    halt_reference: str | None
    recovery_attempted: bool
    active_operation_reference: str | None
    current_assessment_reference: str | None
    observed_system_state_class: str | None

    def __post_init__(self):
        _reference(self.snapshot_reference, 'request.expected_snapshot')
        _exact(self.binding, SessionBinding, 'request')
        _integer(self.generation, 0, MAX_GENERATION, 'generation')
        _exact(self.current_state, state.AshState, 'request')
        _choice(self.mode, SESSION_MODES, 'request')
        _exact(self.terminal_latched, bool, 'request')
        _choice(self.admission_status, SESSION_ADMISSION_STATUSES, 'request')
        if self.containment_reference is not None:
            _reference(self.containment_reference, 'request')
        if self.halt_reference is not None:
            _reference(self.halt_reference, 'request')
        _exact(self.recovery_attempted, bool, 'request')
        if self.active_operation_reference is not None:
            _reference(self.active_operation_reference, 'request', 160)
        if self.current_assessment_reference is not None:
            _reference(self.current_assessment_reference, 'request')
        if self.observed_system_state_class is not None:
            _choice(self.observed_system_state_class, _SYSTEM_CLASSES, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionContextObservation(_Record):
    observation_reference: str
    snapshot: SessionSnapshot
    operation_reference: str
    subject_state: state.AshState
    is_running: bool
    is_contained: bool
    is_halted: bool

    def __post_init__(self):
        _reference(self.observation_reference, 'request')
        _exact(self.snapshot, SessionSnapshot, 'request.expected_snapshot')
        _reference(self.operation_reference, 'request.reference', 160)
        _exact(self.subject_state, state.AshState, 'request')
        _exact(self.is_running, bool, 'request')
        _exact(self.is_contained, bool, 'request')
        _exact(self.is_halted, bool, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionRequest(_Record):
    request_reference: str
    session_reference: str
    expected_snapshot: SessionSnapshot
    action: str
    reason: str

    def __post_init__(self):
        _reference(self.request_reference, 'request.reference', 160)
        _reference(self.session_reference, 'request.session_reference')
        _exact(self.expected_snapshot, SessionSnapshot, 'request.expected_snapshot')
        _choice(self.action, SESSION_ACTIONS, 'request.action')
        _reason(self.reason, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionAuthorityObservation(_Record):
    request_reference: str
    expected_snapshot_reference: str
    status: str
    request_origin: str
    source_binding: recovery.EvidenceSourceBinding
    observation_reference: str
    reason: str

    def __post_init__(self):
        _reference(self.request_reference, 'request.reference', 160)
        _reference(self.expected_snapshot_reference, 'request')
        _choice(self.status, SESSION_AUTHORITY_STATUSES, 'request')
        _choice(self.request_origin, SESSION_AUTHORITY_ORIGINS, 'request')
        _exact(self.source_binding, recovery.EvidenceSourceBinding, 'cause')
        _reference(self.observation_reference, 'request')
        _reason(self.reason, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionBoundaryObservation(_Record):
    request_reference: str
    expected_snapshot_reference: str
    condition: str
    status: str
    source_binding: recovery.EvidenceSourceBinding
    observation_reference: str
    reason: str

    def __post_init__(self):
        _reference(self.request_reference, 'request.reference', 160)
        _reference(self.expected_snapshot_reference, 'request')
        _choice(self.condition, SESSION_BOUNDARY_CONDITIONS, 'request')
        _choice(self.status, SESSION_BOUNDARY_STATUSES, 'request')
        _exact(self.source_binding, recovery.EvidenceSourceBinding, 'cause')
        _reference(self.observation_reference, 'request')
        _reason(self.reason, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionRecoveryRequest(_Record):
    request: SessionRequest
    origin_assessment: state.StateAssessment
    operation_context: recovery.RecoveryOperationContext

    def __post_init__(self):
        _exact(self.request, SessionRequest, 'request')
        _exact(self.origin_assessment, state.StateAssessment, 'origin_assessment')
        _exact(self.operation_context, recovery.RecoveryOperationContext, 'operation_context')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionContainmentRequest(_Record):
    request: SessionRequest
    trigger: str
    authority_observation: SessionAuthorityObservation | None
    boundary_observations: tuple[SessionBoundaryObservation, ...]
    recovery_operation_reference: str | None

    def __post_init__(self):
        _exact(self.request, SessionRequest, 'request')
        _choice(self.trigger, recovery.CONTAINMENT_TRIGGERS, 'trigger')
        if self.authority_observation is not None:
            _exact(self.authority_observation, SessionAuthorityObservation, 'authority')
        object.__setattr__(self, 'boundary_observations', _sequence(self.boundary_observations, lambda item, f: _exact(item, SessionBoundaryObservation, f), 0, 2, 'boundary'))
        if self.recovery_operation_reference is not None:
            _reference(self.recovery_operation_reference, 'request', 160)
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionResolutionRequest(_Record):
    request: SessionRequest
    route: str
    resolution_action: str
    target_state: state.AshState | None
    authority_observation: SessionAuthorityObservation
    propagation_evidence: recovery.PropagationEvidence | None
    boundary_observations: tuple[SessionBoundaryObservation, ...]
    recovery_operation_reference: str | None

    def __post_init__(self):
        _exact(self.request, SessionRequest, 'request')
        _choice(self.route, RESOLUTION_ROUTES, 'resolution.route')
        _choice(self.resolution_action, RESOLUTION_ACTIONS, 'resolution')
        if self.target_state is not None:
            _exact(self.target_state, state.AshState, 'resolution.target')
        _exact(self.authority_observation, SessionAuthorityObservation, 'authority')
        if self.propagation_evidence is not None:
            _exact(self.propagation_evidence, recovery.PropagationEvidence, 'operation_context.propagation_evidence')
        object.__setattr__(self, 'boundary_observations', _sequence(self.boundary_observations, lambda item, f: _exact(item, SessionBoundaryObservation, f), 0, 2, 'boundary'))
        if self.recovery_operation_reference is not None:
            _reference(self.recovery_operation_reference, 'request', 160)
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionHaltRequest(_Record):
    request: SessionRequest
    trigger: str
    authority_observation: SessionAuthorityObservation | None
    boundary_observations: tuple[SessionBoundaryObservation, ...]
    recovery_operation_reference: str | None

    def __post_init__(self):
        _exact(self.request, SessionRequest, 'request')
        _choice(self.trigger, recovery.HALT_TRIGGERS, 'trigger')
        if self.authority_observation is not None:
            _exact(self.authority_observation, SessionAuthorityObservation, 'authority')
        object.__setattr__(self, 'boundary_observations', _sequence(self.boundary_observations, lambda item, f: _exact(item, SessionBoundaryObservation, f), 0, 2, 'boundary'))
        if self.recovery_operation_reference is not None:
            _reference(self.recovery_operation_reference, 'request', 160)
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionCauseObservation(_Record):
    cause_reference: str
    request_reference: str
    expected_snapshot_reference: str
    kind: str
    trigger: str | None
    recovery_operation_reference: str | None
    authority_observation: SessionAuthorityObservation | None
    boundary_observations: tuple[SessionBoundaryObservation, ...]

    def __post_init__(self):
        _reference(self.cause_reference, 'request')
        _reference(self.request_reference, 'request.reference', 160)
        _reference(self.expected_snapshot_reference, 'request')
        _choice(self.kind, SESSION_CAUSE_KINDS, 'request')
        if self.trigger is not None:
            _choice(self.trigger, (*recovery.CONTAINMENT_TRIGGERS, *recovery.HALT_TRIGGERS), 'trigger')
        if self.recovery_operation_reference is not None:
            _reference(self.recovery_operation_reference, 'request', 160)
        if self.authority_observation is not None:
            _exact(self.authority_observation, SessionAuthorityObservation, 'authority')
        object.__setattr__(self, 'boundary_observations', _sequence(self.boundary_observations, lambda item, f: _exact(item, SessionBoundaryObservation, f), 0, 2, 'boundary'))
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionOperationLease(_Record):
    lease_reference: str
    request: SessionRequest
    before: SessionSnapshot
    action: str
    active_snapshot: SessionSnapshot

    def __post_init__(self):
        _reference(self.lease_reference, 'lease')
        _exact(self.request, SessionRequest, 'request')
        _exact(self.before, SessionSnapshot, 'publication.before')
        _choice(self.action, LEASE_ACTIONS, 'request.action')
        _exact(self.active_snapshot, SessionSnapshot, 'lease')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionAdmission(_Record):
    status: str
    request: SessionRequest
    before: SessionSnapshot
    lease: SessionOperationLease | None
    failure_code: str | None
    field_name: str | None
    reason: str

    def __post_init__(self):
        _choice(self.status, SESSION_ADMISSION_DECISIONS, 'request')
        _exact(self.request, SessionRequest, 'request')
        _exact(self.before, SessionSnapshot, 'publication.before')
        if self.lease is not None:
            _exact(self.lease, SessionOperationLease, 'lease')
        if self.failure_code is not None:
            _choice(self.failure_code, SESSION_FAILURE_CODES, 'request')
        if self.field_name is not None:
            _choice(self.field_name, SESSION_FIELD_PATHS, 'request')
        _reason(self.reason, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionAdmissionFailure(_Record):
    failure_code: str
    field_name: str
    submitted_request: object | None
    before: SessionSnapshot
    reason: str

    def __post_init__(self):
        _choice(self.failure_code, SESSION_FAILURE_CODES, 'request')
        _choice(self.field_name, SESSION_FIELD_PATHS, 'request')
        if self.submitted_request is not None:
            _exact(self.submitted_request, _COMMANDS, 'request')
        _exact(self.before, SessionSnapshot, 'publication.before')
        _reason(self.reason, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class ResolutionTargetValidation(_Record):
    status: str
    target_state: state.AshState
    current_source_binding: state.CanonicalAshBinding
    current_profile_binding: object
    target_diagnostic: state.StateValidityDiagnostic
    prospective_context: state.SystemContext
    expected_system_state_class: str | None
    expected_recovery_category: str | None
    failure_code: str | None
    field_name: str | None

    def __post_init__(self):
        _choice(self.status, ('VERIFIED', 'REJECTED'), 'request')
        _exact(self.target_state, state.AshState, 'resolution.target')
        _exact(self.current_source_binding, state.CanonicalAshBinding, 'binding.canonical_binding')
        _exact(self.current_profile_binding, _PROFILES, 'binding.profile_binding')
        _exact(self.target_diagnostic, state.StateValidityDiagnostic, 'request')
        _exact(self.prospective_context, state.SystemContext, 'request')
        if self.expected_system_state_class is not None:
            _constant(self.expected_system_state_class, 'STABLE', 'request')
        if self.expected_recovery_category is not None:
            _constant(self.expected_recovery_category, 'NO_ACTION', 'request')
        if self.failure_code is not None:
            _constant(self.failure_code, 'SESSION_TARGET_NOT_VALID', 'request')
        if self.field_name is not None:
            _constant(self.field_name, 'resolution.target_validation', 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionPublication(_Record):
    publication_reference: str
    request_reference: str
    lease_reference: str
    before: SessionSnapshot
    after: SessionSnapshot | None
    status: str
    session_effects_performed: bool | None
    requested_state: state.AshState
    requested_mode: str
    cause_reference: str
    proof_reference: str | None
    failure_code: str | None
    reason: str

    def __post_init__(self):
        _reference(self.publication_reference, 'request')
        _reference(self.request_reference, 'request.reference', 160)
        _reference(self.lease_reference, 'lease')
        _exact(self.before, SessionSnapshot, 'publication.before')
        if self.after is not None:
            _exact(self.after, SessionSnapshot, 'publication.after')
        _choice(self.status, PUBLICATION_STATUSES, 'request')
        if self.session_effects_performed is not None:
            _exact(self.session_effects_performed, bool, 'request')
        _exact(self.requested_state, state.AshState, 'request')
        _choice(self.requested_mode, SESSION_MODES, 'request')
        _reference(self.cause_reference, 'request')
        if self.proof_reference is not None:
            _reference(self.proof_reference, 'request')
        if self.failure_code is not None:
            _choice(self.failure_code, SESSION_FAILURE_CODES, 'request')
        _reason(self.reason, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class ContainmentDiagnostic(_Record):
    trigger: str
    original_diagnostic: state.StateValidityDiagnostic
    system_state_class: str
    restricted_operations: tuple[str, ...]
    containment_time: diagnostics.ClockObservation
    awaiting_resolution: bool
    resolution: str
    rule_ids: tuple[str, ...]
    notes: tuple[str, ...]

    def __post_init__(self):
        _choice(self.trigger, recovery.CONTAINMENT_TRIGGERS, 'trigger')
        _exact(self.original_diagnostic, state.StateValidityDiagnostic, 'origin_assessment')
        _constant(self.system_state_class, 'CONTAINED', 'request')
        object.__setattr__(self, 'restricted_operations', _sequence(self.restricted_operations, lambda item, f: _choice(item, RESTRICTED_OPERATIONS, f), 5, 5, 'request'))
        _exact(self.containment_time, diagnostics.ClockObservation, 'clock')
        _constant(self.awaiting_resolution, True, 'request')
        _constant(self.resolution, 'PENDING', 'request')
        object.__setattr__(self, 'rule_ids', _sequence(self.rule_ids, lambda item, f: _choice(item, tuple(CONTAINMENT_RULES.values()), f), 1, 1, 'request'))
        object.__setattr__(self, 'notes', _sequence(self.notes, lambda item, f: _reason(item, f), 1, 8, 'request'))
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SafeHaltDiagnostic(_Record):
    trigger: str
    original_diagnostic: state.StateValidityDiagnostic
    system_state_class: str
    halt_time: diagnostics.ClockObservation
    full_diagnostic_chain: tuple[object, ...]
    is_terminal: bool
    rule_ids: tuple[str, ...]
    notes: tuple[str, ...]

    def __post_init__(self):
        _choice(self.trigger, recovery.HALT_TRIGGERS, 'trigger')
        _exact(self.original_diagnostic, state.StateValidityDiagnostic, 'origin_assessment')
        _constant(self.system_state_class, 'SAFE_HALT', 'request')
        _exact(self.halt_time, diagnostics.ClockObservation, 'clock')
        first = self.full_diagnostic_chain[0] if type(self.full_diagnostic_chain) is tuple and self.full_diagnostic_chain else None
        current = (type(first) is state.StateAssessment and
            state.canonical_source_baseline(first.source_binding) in ('M3_MODULES', 'M3_GENERATION'))
        allowed = (state.StateAssessment, *_PACKETS, SessionOperationResult, SessionTerminalChainClosure)
        if current:
            allowed += (SessionModuleHistory,)
        object.__setattr__(self, 'full_diagnostic_chain', _sequence(self.full_diagnostic_chain,
            lambda item, f: _exact(item, allowed, f), 2, 22 if current else 21, 'history'))
        if sum(type(item) is SessionModuleHistory for item in self.full_diagnostic_chain) > 1:
            _fail('history')
        _constant(self.is_terminal, True, 'request')
        object.__setattr__(self, 'rule_ids', _sequence(self.rule_ids, lambda item, f: _choice(item, tuple(HALT_RULES.values()), f), 1, 1, 'request'))
        object.__setattr__(self, 'notes', _sequence(self.notes, lambda item, f: _reason(item, f), 1, 8, 'request'))
        _cohere(self)


@dataclass(frozen=True, slots=True)
class LifecycleRecord(_Record):
    diagnostic_reference: str
    envelope: state.DiagnosticEnvelope
    payload: object
    cause: SessionCauseObservation

    def __post_init__(self):
        _reference(self.diagnostic_reference, 'request')
        _exact(self.envelope, state.DiagnosticEnvelope, 'request')
        _exact(self.payload, (recovery.RecoveryDiagnostic, ContainmentDiagnostic, SafeHaltDiagnostic,), 'request')
        _exact(self.cause, SessionCauseObservation, 'cause')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class PendingLifecycleRecord(_Record):
    intended_reference: str
    kind: str
    trigger: str
    original_assessment: state.StateAssessment | None
    before: SessionSnapshot
    actual_after: SessionSnapshot | None
    cause: SessionCauseObservation
    missing_fields: tuple[str, ...]
    reason_code: str

    def __post_init__(self):
        _reference(self.intended_reference, 'request')
        _choice(self.kind, LIFECYCLE_KINDS, 'request')
        _choice(self.trigger, (*recovery.CONTAINMENT_TRIGGERS, *recovery.HALT_TRIGGERS), 'trigger')
        if self.original_assessment is not None:
            _exact(self.original_assessment, state.StateAssessment, 'origin_assessment')
        _exact(self.before, SessionSnapshot, 'publication.before')
        if self.actual_after is not None:
            _exact(self.actual_after, SessionSnapshot, 'publication.after')
        _exact(self.cause, SessionCauseObservation, 'cause')
        object.__setattr__(self, 'missing_fields', _sequence(self.missing_fields, lambda item, f: _choice(item, LIFECYCLE_CANONICAL_FIELDS, f), 1, 15, 'request'))
        _choice(self.reason_code, PENDING_LIFECYCLE_REASONS, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionResolutionObservation(_Record):
    resolution_reference: str
    request: SessionRequest
    route: str
    containment_record_reference: str
    target_validation: ResolutionTargetValidation | None
    authority_observation: SessionAuthorityObservation
    boundary_clear: SessionBoundaryObservation | None
    propagation_evidence: recovery.PropagationEvidence | None
    publication: SessionPublication | None
    actual_post_assessment: object | None
    status: str
    session_effects_performed: bool | None
    reason: str

    def __post_init__(self):
        _reference(self.resolution_reference, 'request')
        _exact(self.request, SessionRequest, 'request')
        _choice(self.route, RESOLUTION_ROUTES, 'resolution.route')
        _reference(self.containment_record_reference, 'request')
        if self.target_validation is not None:
            _exact(self.target_validation, ResolutionTargetValidation, 'resolution.target_validation')
        _exact(self.authority_observation, SessionAuthorityObservation, 'authority')
        if self.boundary_clear is not None:
            _exact(self.boundary_clear, SessionBoundaryObservation, 'resolution.boundary_clear')
        if self.propagation_evidence is not None:
            _exact(self.propagation_evidence, recovery.PropagationEvidence, 'operation_context.propagation_evidence')
        if self.publication is not None:
            _exact(self.publication, SessionPublication, 'publication')
        if self.actual_post_assessment is not None:
            _exact(self.actual_post_assessment, (state.StateAssessment, state.ClassificationEvidenceFailure, state.DiagnosticCaptureFailure,), 'origin_assessment')
        _choice(self.status, RESOLUTION_STATUSES, 'request')
        if self.session_effects_performed is not None:
            _exact(self.session_effects_performed, bool, 'request')
        _reason(self.reason, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionLifecycleCaptureAdmission(_Record):
    operation_reference: str
    status: str
    reserved_events: int
    reserved_bytes: int
    reserved_aliases: int
    reserved_supporting_bytes: int
    failure_code: str | None

    def __post_init__(self):
        _reference(self.operation_reference, 'request.reference', 160)
        _choice(self.status, ('CONFIRMED', 'REJECTED', 'NOT_CONFIRMED'), 'request')
        _exact(self.reserved_events, int, 'request'); _integer_choice(self.reserved_events, (0, 4), 'request')
        _exact(self.reserved_bytes, int, 'request'); _integer_choice(self.reserved_bytes, (0, 327680, 655360, 688128), 'request')
        _exact(self.reserved_aliases, int, 'request'); _integer_choice(self.reserved_aliases, (0, 512), 'request')
        _exact(self.reserved_supporting_bytes, int, 'request'); _integer_choice(self.reserved_supporting_bytes, (0, 98304, 425984, 458752), 'request')
        if self.failure_code is not None:
            _choice(self.failure_code, LIFECYCLE_CAPTURE_CODES, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionLifecycleCompletion(_Record):
    operation_reference: str
    status: str
    confirmed_references: tuple[str, ...]
    failure_code: str | None

    def __post_init__(self):
        _reference(self.operation_reference, 'request.reference', 160)
        _choice(self.status, ('COMPLETE', 'INCOMPLETE'), 'request')
        object.__setattr__(self, 'confirmed_references', _sequence(self.confirmed_references, lambda item, f: _reference(item, f), 0, 4, 'request'))
        if self.failure_code is not None:
            _choice(self.failure_code, LIFECYCLE_CAPTURE_CODES, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionFailureDetail(_Record):
    failure_code: str
    field_name: str
    primary_evidence: object | None
    capture_status: str | None
    attempted_lifecycle_record: LifecycleRecord | None
    pending_lifecycle_record: PendingLifecycleRecord | None
    completion_failure_code: str | None
    unconfirmed_completion_observation: SessionLifecycleCompletion | None
    reason: str

    def __post_init__(self):
        _choice(self.failure_code, SESSION_FAILURE_CODES, 'request')
        _choice(self.field_name, SESSION_FIELD_PATHS, 'request')
        if self.primary_evidence is not None:
            _exact(self.primary_evidence, (recovery.AssessmentValidation, *_PACKETS, ResolutionTargetValidation, SessionAuthorityObservation, SessionBoundaryObservation, SessionAdmission, SessionPublication, SessionRetentionReceipt, recovery.UnavailablePostAssessmentFacts), 'request')
        if self.capture_status is not None:
            _choice(self.capture_status, LIFECYCLE_CAPTURE_STATUSES, 'request')
        if self.attempted_lifecycle_record is not None:
            _exact(self.attempted_lifecycle_record, LifecycleRecord, 'request')
        if self.pending_lifecycle_record is not None:
            _exact(self.pending_lifecycle_record, PendingLifecycleRecord, 'capture')
        if self.completion_failure_code is not None:
            _choice(self.completion_failure_code, LIFECYCLE_CAPTURE_CODES, 'request')
        if self.unconfirmed_completion_observation is not None:
            _exact(self.unconfirmed_completion_observation, SessionLifecycleCompletion, 'capture.finish')
        _reason(self.reason, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionOperationResult(_Record):
    request: object
    status: str
    before: SessionSnapshot
    after: SessionSnapshot | None
    session_effects_performed: bool | None
    admission: SessionAdmission
    context_observation: SessionContextObservation
    authority_observation: SessionAuthorityObservation | None
    cause: SessionCauseObservation | None
    origin_assessment: state.StateAssessment | state.ClassificationEvidenceFailure | state.DiagnosticCaptureFailure | None
    origin_completion_observation: diagnostics.DiagnosticsCompletionReceipt | None
    recovery_result: object | None
    publication: SessionPublication | None
    confirmed_lifecycle_records: tuple[LifecycleRecord, ...]
    attempted_lifecycle_records: tuple[LifecycleRecord, ...]
    pending_lifecycle_record: PendingLifecycleRecord | None
    resolution_observation: SessionResolutionObservation | None
    completion_observation: SessionLifecycleCompletion | None
    failure_detail: SessionFailureDetail | None
    actual_post_assessment: object | None
    actual_post_completion_observation: diagnostics.DiagnosticsCompletionReceipt | None

    def __post_init__(self):
        _exact(self.request, _COMMANDS, 'request')
        _choice(self.status, SESSION_OPERATION_STATUSES, 'request')
        _exact(self.before, SessionSnapshot, 'publication.before')
        if self.after is not None:
            _exact(self.after, SessionSnapshot, 'publication.after')
        if self.session_effects_performed is not None:
            _exact(self.session_effects_performed, bool, 'request')
        _exact(self.admission, SessionAdmission, 'request')
        _exact(self.context_observation, SessionContextObservation, 'request')
        if self.authority_observation is not None:
            _exact(self.authority_observation, SessionAuthorityObservation, 'authority')
        if self.cause is not None:
            _exact(self.cause, SessionCauseObservation, 'cause')
        if self.origin_assessment is not None:
            _exact(self.origin_assessment, (state.StateAssessment, state.ClassificationEvidenceFailure, state.DiagnosticCaptureFailure), 'origin_assessment')
        if self.origin_completion_observation is not None:
            _exact(self.origin_completion_observation, diagnostics.DiagnosticsCompletionReceipt, 'capture.finish')
        if self.recovery_result is not None:
            _exact(self.recovery_result, _PACKETS, 'request')
        if self.publication is not None:
            _exact(self.publication, SessionPublication, 'publication')
        object.__setattr__(self, 'confirmed_lifecycle_records', _sequence(self.confirmed_lifecycle_records, lambda item, f: _exact(item, LifecycleRecord, f), 0, 2, 'capture'))
        object.__setattr__(self, 'attempted_lifecycle_records', _sequence(self.attempted_lifecycle_records, lambda item, f: _exact(item, LifecycleRecord, f), 0, 2, 'capture'))
        if self.pending_lifecycle_record is not None:
            _exact(self.pending_lifecycle_record, PendingLifecycleRecord, 'capture')
        if self.resolution_observation is not None:
            _exact(self.resolution_observation, SessionResolutionObservation, 'request')
        if self.completion_observation is not None:
            _exact(self.completion_observation, SessionLifecycleCompletion, 'capture.finish')
        if self.failure_detail is not None:
            _exact(self.failure_detail, SessionFailureDetail, 'request')
        if self.actual_post_assessment is not None:
            _exact(self.actual_post_assessment, (state.StateAssessment, state.ClassificationEvidenceFailure, state.DiagnosticCaptureFailure,), 'origin_assessment')
        if self.actual_post_completion_observation is not None:
            _exact(self.actual_post_completion_observation, diagnostics.DiagnosticsCompletionReceipt, 'capture.finish')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionDeniedAttempt(_Record):
    session_reference: str
    frozen_snapshot: SessionSnapshot
    denial_ordinal: int | None
    request_reference: str | None
    request_observation: str
    reason_code: str
    audit_reference: str | None
    attempted_record: state.DiagnosticEmission | None
    capture_status: str
    completion_observation: SessionLifecycleCompletion | None

    def __post_init__(self):
        _reference(self.session_reference, 'request.session_reference')
        _exact(self.frozen_snapshot, SessionSnapshot, 'request')
        if self.denial_ordinal is not None:
            _integer(self.denial_ordinal, 1, 16, 'request')
        if self.request_reference is not None:
            _reference(self.request_reference, 'request.reference', 160)
        _choice(self.request_observation, ('NOT_INSPECTED_AT_TERMINAL', 'VALIDATED_REFERENCE_ONLY'), 'request')
        _choice(self.reason_code, ('SESSION_TERMINAL', 'SESSION_MODE_FORBIDDEN', 'SESSION_BUDGET_EXCEEDED'), 'request')
        if self.audit_reference is not None:
            _reference(self.audit_reference, 'request')
        if self.attempted_record is not None:
            _exact(self.attempted_record, state.DiagnosticEmission, 'request')
        _choice(self.capture_status, LIFECYCLE_CAPTURE_STATUSES, 'request')
        if self.completion_observation is not None:
            _exact(self.completion_observation, SessionLifecycleCompletion, 'capture.finish')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionChildLink(_Record):
    link_reference: str
    session_binding_reference: str
    admitted_generation: int
    live_origin_assessment_reference: str
    child_origin_assessment_reference: str
    child_operation_reference: str

    def __post_init__(self):
        _reference(self.link_reference, 'request')
        _reference(self.session_binding_reference, 'request')
        _integer(self.admitted_generation, 0, MAX_GENERATION, 'generation')
        _reference(self.live_origin_assessment_reference, 'request')
        _reference(self.child_origin_assessment_reference, 'request')
        _reference(self.child_operation_reference, 'request', 160)
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionHistory(_Record):
    history_reference: str
    binding: SessionBinding
    main_assessment: state.StateAssessment
    child_links: tuple[SessionChildLink, ...]
    recovery_results: tuple[object, ...]
    command_results: tuple[SessionOperationResult, ...]
    resolution_observations: tuple[SessionResolutionObservation, ...]
    confirmed_lifecycle_records: tuple[LifecycleRecord, ...]
    attempted_lifecycle_records: tuple[LifecycleRecord, ...]
    pending_lifecycle_records: tuple[PendingLifecycleRecord, ...]
    terminal_snapshot: SessionSnapshot | None
    frozen: bool
    module_history: object = field(default=None, kw_only=True)

    def __post_init__(self):
        _reference(self.history_reference, 'history')
        _exact(self.binding, SessionBinding, 'request')
        if self.module_history is not None:
            _exact(self.module_history, SessionModuleHistory, 'history')
            if self.binding.policy_binding.policy_version != '1.1.0':
                _fail('binding.policy_binding', 'SESSION_SOURCE_REJECTED')
            _same(self.module_history.session_binding_reference, self.binding.binding_reference, 'history')
        _exact(self.main_assessment, state.StateAssessment, 'history')
        object.__setattr__(self, 'child_links', _sequence(self.child_links, lambda item, f: _exact(item, SessionChildLink, f), 0, 2, 'history'))
        object.__setattr__(self, 'recovery_results', _sequence(self.recovery_results, lambda item, f: _exact(item, _PACKETS, f), 0, 2, 'history'))
        object.__setattr__(self, 'command_results', _sequence(self.command_results, lambda item, f: _exact(item, SessionOperationResult, f), 0, 18, 'history'))
        object.__setattr__(self, 'resolution_observations', _sequence(self.resolution_observations, lambda item, f: _exact(item, SessionResolutionObservation, f), 0, 16, 'request'))
        object.__setattr__(self, 'confirmed_lifecycle_records', _sequence(self.confirmed_lifecycle_records, lambda item, f: _exact(item, LifecycleRecord, f), 0, 36, 'capture'))
        object.__setattr__(self, 'attempted_lifecycle_records', _sequence(self.attempted_lifecycle_records, lambda item, f: _exact(item, LifecycleRecord, f), 0, 36, 'capture'))
        object.__setattr__(self, 'pending_lifecycle_records', _sequence(self.pending_lifecycle_records, lambda item, f: _exact(item, PendingLifecycleRecord, f), 0, 18, 'capture'))
        if self.terminal_snapshot is not None:
            _exact(self.terminal_snapshot, SessionSnapshot, 'request')
        _exact(self.frozen, bool, 'request')
        _cohere(self)


class _RetentionRecord(_Record):
    __slots__ = ('_construction_policy',)


@dataclass(frozen=True, slots=True, init=False)
class SessionRetentionReceipt(_RetentionRecord):
    session_reference: str
    status: str
    phase: str
    coverage: str
    confirmed_record_count: int
    unknown_storage_record_count: int
    pinned_supporting_count: int
    failure_code: str | None

    def __init__(self, session_reference, status, phase, coverage,
                 confirmed_record_count, unknown_storage_record_count,
                 pinned_supporting_count, failure_code, *, policy_binding=None):
        object.__setattr__(self, '_construction_policy', policy_binding)
        for name, value in zip(('session_reference', 'status', 'phase', 'coverage',
                'confirmed_record_count', 'unknown_storage_record_count',
                'pinned_supporting_count', 'failure_code'), (session_reference,
                status, phase, coverage, confirmed_record_count,
                unknown_storage_record_count, pinned_supporting_count, failure_code)):
            object.__setattr__(self, name, value)
        SessionRetentionReceipt.__post_init__(self)

    def __getstate__(self):
        SessionRetentionReceipt.__post_init__(self)
        return (self._construction_policy, *(getattr(self, field.name) for field in fields(self)))

    def __setstate__(self, value):
        if type(value) is not tuple or len(value) != 9:
            _fail('binding.policy_binding', 'SESSION_SOURCE_REJECTED')
        object.__setattr__(self, '_construction_policy', value[0])
        for field, child in zip(fields(self), value[1:]):
            object.__setattr__(self, field.name, child)
        SessionRetentionReceipt.__post_init__(self)

    def __post_init__(self):
        _reference(self.session_reference, 'request.session_reference')
        _choice(self.status, SESSION_RETENTION_STATUSES, 'request')
        _choice(self.phase, SESSION_RETENTION_PHASES, 'request')
        _choice(self.coverage, SESSION_RETENTION_COVERAGES, 'request')
        _integer(self.confirmed_record_count, 0, 1024, 'request')
        _integer(self.unknown_storage_record_count, 0, 1024, 'request')
        try:
            policy = object.__getattribute__(self, '_construction_policy')
        except AttributeError:
            _fail('binding.policy_binding', 'SESSION_SOURCE_REJECTED')
        if policy is not None:
            _exact(policy, SessionPolicyBinding, 'binding.policy_binding')
            SessionPolicyBinding.__post_init__(policy)
            if policy.policy_version != '1.1.0':
                _fail('binding.policy_binding', 'SESSION_SOURCE_REJECTED')
        _integer(self.pinned_supporting_count, 0, 2663 if policy is not None else 2544, 'request')
        if self.failure_code is not None:
            _choice(self.failure_code, SESSION_RETENTION_FAILURES, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionAssessmentLink(_Record):
    session_reference: str
    parent_operation_reference: str
    parent_resolution_reference: str | None
    originating_chain_root_reference: str

    def __post_init__(self):
        _reference(self.session_reference, 'request.session_reference')
        _reference(self.parent_operation_reference, 'request', 160)
        if self.parent_resolution_reference is not None:
            _reference(self.parent_resolution_reference, 'request')
        _reference(self.originating_chain_root_reference, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionStageGrant:
    grant_index: int
    stage: str
    status: str
    lease_reference: str
    generation: int

    def __post_init__(self):
        _integer(self.grant_index, 0, 8191, 'request')
        _choice(self.stage, STAGE_GRANT_KINDS, 'request')
        _choice(self.status, ('GRANTED', 'CANCELLED'), 'request')
        _reference(self.lease_reference, 'lease')
        _integer(self.generation, 0, MAX_GENERATION, 'generation')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionReplayObservation(_Record):
    request_reference: str
    original_result: SessionOperationResult
    current_snapshot: SessionSnapshot
    session_effects_performed: bool

    def __post_init__(self):
        _reference(self.request_reference, 'request.reference', 160)
        _exact(self.original_result, SessionOperationResult, 'request')
        _exact(self.current_snapshot, SessionSnapshot, 'request')
        _constant(self.session_effects_performed, False, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionTerminalChainClosure(_Record):
    request_reference: str
    bridge_record: LifecycleRecord | None
    terminal_emission: state.DiagnosticEmission
    actual_terminal_publication: SessionPublication

    def __post_init__(self):
        _reference(self.request_reference, 'request.reference', 160)
        if self.bridge_record is not None:
            _exact(self.bridge_record, LifecycleRecord, 'request')
        _exact(self.terminal_emission, state.DiagnosticEmission, 'request')
        _exact(self.actual_terminal_publication, SessionPublication, 'request')
        _cohere(self)


@dataclass(frozen=True, slots=True)
class SessionRawBusinessFailure(_Record):
    request_reference: str
    session_reference: str
    history_reference: str
    phase: str
    before: SessionSnapshot
    after: SessionSnapshot | None
    session_effects_performed: bool | None
    failure_code: str
    coverage: str

    def __post_init__(self):
        _reference(self.request_reference, 'request.reference', 160)
        _reference(self.session_reference, 'request.session_reference')
        _reference(self.history_reference, 'history')
        _choice(self.phase, ('CANDIDATE_RESULT', 'PROSPECTIVE_HISTORY', 'ANTICIPATED_TERMINAL', 'TERMINAL_CHAIN'), 'request')
        _exact(self.before, SessionSnapshot, 'publication.before')
        if self.after is not None:
            _exact(self.after, SessionSnapshot, 'publication.after')
        if self.session_effects_performed is not None:
            _exact(self.session_effects_performed, bool, 'request')
        _constant(self.failure_code, 'SESSION_RAW_BUSINESS_LIMIT', 'request')
        _choice(self.coverage, ('API_ONLY', 'PARTIAL'), 'request')
        _cohere(self)


_COMMANDS = (SessionRecoveryRequest, SessionContainmentRequest,
             SessionResolutionRequest, SessionHaltRequest)
SessionCommand = SessionRecoveryRequest | SessionContainmentRequest | SessionResolutionRequest | SessionHaltRequest
SessionExecuteReturn = SessionOperationResult | SessionDeniedAttempt | SessionReplayObservation | SessionRawBusinessFailure
LifecycleBusinessPayload = recovery.RecoveryDiagnostic | ContainmentDiagnostic | SafeHaltDiagnostic



def _primary_request(observation, request, field):
    _same(observation.request_reference, request.request_reference, field)
    _same(observation.expected_snapshot_reference, request.expected_snapshot.snapshot_reference, field)


def _command_evidence(command):
    request = command.request
    authority = getattr(command, "authority_observation", None)
    if authority is not None:
        _primary_request(authority, request, "authority")
    for boundary in getattr(command, "boundary_observations", ()):
        _primary_request(boundary, request, "boundary")
    conditions = [item.condition for item in getattr(command, "boundary_observations", ())]
    if len(set(conditions)) != len(conditions):
        _fail("boundary")


def _cohere(value):
    kind = type(value)
    if kind is SessionBinding:
        try:
            baseline = state.canonical_source_baseline(value.canonical_binding)
            required_version = ('1.0.0' if baseline == 'N3_LIFECYCLE' else
                '1.1.0' if baseline in ('M3_MODULES', 'M3_GENERATION') else None)
            if required_version is None or value.policy_binding.policy_version != required_version:
                _fail("binding.canonical_binding", "SESSION_SOURCE_REJECTED")
            recovery.RecoverySourceBinding.__post_init__(value.recovery_binding)
        except (state.StateContractError, recovery.RecoveryContractError):
            _fail("binding.recovery_binding", "SESSION_SOURCE_REJECTED")
        _same(value.recovery_binding.canonical_binding, value.canonical_binding, "binding.recovery_binding")
    elif kind is SessionSnapshot:
        if (value.current_assessment_reference is None) != (value.observed_system_state_class is None):
            _fail("origin_assessment")
        if value.mode == "SAFE_HALT":
            if (not value.terminal_latched or value.admission_status != "TERMINAL" or
                    value.halt_reference is None or value.containment_reference is not None or
                    value.current_assessment_reference is not None):
                _fail("request.expected_snapshot")
        else:
            if value.terminal_latched or value.admission_status == "TERMINAL" or value.halt_reference is not None:
                _fail("request.expected_snapshot")
            if (value.mode == "CONTAINED") != (value.containment_reference is not None):
                _fail("request.expected_snapshot")
            if value.mode == "CONTAINED" and value.observed_system_state_class not in (None, "CONTAINED"):
                _fail("origin_assessment")
            if value.mode == "NORMAL" and value.observed_system_state_class in ("CONTAINED", "SAFE_HALT"):
                _fail("origin_assessment")
    elif kind is SessionContextObservation:
        _same(value.subject_state, value.snapshot.current_state, "operation_context.context_observation")
        if (value.is_running != (value.snapshot.mode != "SAFE_HALT") or
                value.is_contained != (value.snapshot.mode == "CONTAINED") or
                value.is_halted != (value.snapshot.mode == "SAFE_HALT")):
            _fail("operation_context.context_observation")
    elif kind is SessionRequest:
        _same(value.session_reference, value.expected_snapshot.binding.session_reference, "request.session_reference")
    elif kind in _COMMANDS:
        expected = {SessionRecoveryRequest: "RECOVER", SessionContainmentRequest: "REQUEST_CONTAINMENT",
                    SessionResolutionRequest: "RESOLVE_CONTAINMENT", SessionHaltRequest: "REQUEST_HALT"}[kind]
        _same(value.request.action, expected, "request.action")
        _command_evidence(value)
        if kind is SessionRecoveryRequest:
            _same(value.operation_context.operation_reference, value.request.request_reference, "operation_context")
            _same(value.operation_context.origin_assessment_reference,
                  value.request.request_reference + ":origin:assessment", "operation_context")
            if value.operation_context.context_observation.context != state.SystemContext(False, False):
                _fail("operation_context.context_observation")
        elif kind is SessionResolutionRequest:
            if value.resolution_action == "REPLACE_STATE":
                if value.target_state is None or value.route == "ESCALATE_TO_SAFE_HALT":
                    _fail("resolution.target")
            elif value.target_state is not None or value.route != "ESCALATE_TO_SAFE_HALT":
                _fail("resolution.route")
    elif kind is SessionCauseObservation:
        if value.kind == "N2_RESULT":
            if value.trigger is not None or value.recovery_operation_reference is None:
                _fail("cause")
        elif value.trigger is None:
            _fail("trigger")
        if value.kind == "N2_HANDOFF" and value.recovery_operation_reference is None:
            _fail("cause")
        if value.kind == "AUTHORITY_REQUEST" and value.authority_observation is None:
            _fail("authority")
        if value.kind == "PROPAGATION_RISK_BOUNDARY":
            if (value.trigger != "PROPAGATION_RISK" or value.authority_observation is not None or
                    value.recovery_operation_reference is not None or not any(
                        boundary.condition == "PROPAGATION_RISK" and boundary.status == "SATISFIED"
                        for boundary in value.boundary_observations)):
                _fail("cause")
        if value.authority_observation is not None:
            _same(value.authority_observation.request_reference, value.request_reference, "authority")
            _same(value.authority_observation.expected_snapshot_reference, value.expected_snapshot_reference, "authority")
        for boundary in value.boundary_observations:
            _same(boundary.request_reference, value.request_reference, "boundary")
            _same(boundary.expected_snapshot_reference, value.expected_snapshot_reference, "boundary")
    elif kind is SessionOperationLease:
        _same(value.before, value.request.expected_snapshot, "lease")
        for name in ("binding", "generation", "current_state", "mode", "terminal_latched", "admission_status",
                     "containment_reference", "halt_reference", "recovery_attempted",
                     "current_assessment_reference", "observed_system_state_class"):
            _same(getattr(value.active_snapshot, name), getattr(value.before, name), "lease")
        _same(value.active_snapshot.active_operation_reference, value.request.request_reference, "lease")
        actions = {"RECOVER": ("RECOVER",), "REQUEST_CONTAINMENT": ("CONTAIN",),
                   "RESOLVE_CONTAINMENT": ("RESOLVE", "HALT"), "REQUEST_HALT": ("HALT",)}
        if value.action not in actions[value.request.action]:
            _fail("lease")
    elif kind is SessionAdmission:
        if value.status == "GRANTED":
            if value.lease is None or value.failure_code is not None or value.field_name is not None:
                _fail("capture.admission")
            _same(value.request, value.lease.request, "lease")
            _same(value.before, value.lease.before, "lease")
        elif value.lease is not None or value.failure_code is None or value.field_name is None:
            _fail("capture.admission")
    elif kind is ResolutionTargetValidation:
        _same(value.prospective_context, state.SystemContext(False, False), "resolution.target_validation")
        _exact(value.target_diagnostic.input_state, state.AshState, "resolution.target_validation")
        _same(value.target_diagnostic.input_state, value.target_state, "resolution.target_validation")
        if value.status == "VERIFIED":
            if (not value.target_diagnostic.is_valid or value.target_diagnostic.admissibility_status != "VALID" or
                    value.expected_system_state_class != "STABLE" or value.expected_recovery_category != "NO_ACTION" or
                    value.failure_code is not None or value.field_name is not None):
                _fail("resolution.target_validation")
        elif (value.expected_system_state_class is not None or value.expected_recovery_category is not None or
              value.failure_code != "SESSION_TARGET_NOT_VALID" or value.field_name != "resolution.target_validation"):
            _fail("resolution.target_validation")
    elif kind is SessionPublication:
        if value.after is not None:
            _same(value.after.binding, value.before.binding, "publication.after")
        if value.status == "COMMITTED":
            if value.after is None or value.session_effects_performed is not True or value.failure_code is not None:
                _fail("publication")
            _same(value.after.generation, value.before.generation + 1, "publication.after")
            _same(value.after.current_state, value.requested_state, "publication.after")
            _same(value.after.mode, value.requested_mode, "publication.after")
        elif value.status == "NOT_COMMITTED":
            if value.session_effects_performed is not False or value.failure_code is None:
                _fail("publication")
        elif value.session_effects_performed is not None or value.failure_code is None:
            _fail("publication")
    elif kind is ContainmentDiagnostic:
        _same(value.restricted_operations, RESTRICTED_OPERATIONS, "request")
        if value.containment_time.monotonic_nanoseconds is None:
            _fail("clock")
        _same(value.rule_ids, (CONTAINMENT_RULES[value.trigger],), "trigger")
    elif kind is SafeHaltDiagnostic:
        if value.halt_time.monotonic_nanoseconds is None:
            _fail("clock")
        _same(value.rule_ids, (HALT_RULES[value.trigger],), "trigger")
        _exact(value.full_diagnostic_chain[0], state.StateAssessment, "history")
        _exact(value.full_diagnostic_chain[-1], SessionTerminalChainClosure, "history")
    elif kind is LifecycleRecord:
        payload = value.payload
        if type(payload) is recovery.RecoveryDiagnostic:
            expected_kind, stage = "RECOVERY", "RECOVERY"
            if payload.steps:
                _fail("capture")
        elif type(payload) is ContainmentDiagnostic:
            expected_kind, stage = "CONTAINMENT", "ESCALATION"
            _same(value.cause.trigger, payload.trigger, "cause")
        else:
            expected_kind, stage = "SAFE_HALT", "TERMINAL"
            _same(value.cause.trigger, payload.trigger, "cause")
        if (value.envelope.diagnostic_kind != expected_kind or value.envelope.stage != stage or
                value.envelope.parent_diagnostic_reference is None):
            _fail("capture")
        _same(value.envelope.rule_ids, payload.rule_ids, "capture")
        if type(payload) is SafeHaltDiagnostic:
            closure = payload.full_diagnostic_chain[-1]
            _same(closure.terminal_emission, state.DiagnosticEmission(value.diagnostic_reference, value.envelope), "history")
    elif kind is PendingLifecycleRecord:
        if len(set(value.missing_fields)) != len(value.missing_fields):
            _fail("capture")
        if value.kind == "CONTAINMENT" and value.trigger not in recovery.CONTAINMENT_TRIGGERS:
            _fail("trigger")
        if value.kind == "SAFE_HALT" and value.trigger not in recovery.HALT_TRIGGERS:
            _fail("trigger")
    elif kind is SessionResolutionObservation:
        _same(value.request.action, "RESOLVE_CONTAINMENT", "request.action")
        _primary_request(value.authority_observation, value.request, "authority")
        if value.boundary_clear is not None:
            _primary_request(value.boundary_clear, value.request, "resolution.boundary_clear")
            _same(value.boundary_clear.condition, "CONTAINMENT_CLEAR", "resolution.boundary_clear")
        if value.publication is not None:
            _same(value.publication.request_reference, value.request.request_reference, "publication")
        if value.status == "RESOLVED":
            if (value.target_validation is None or value.target_validation.status != "VERIFIED" or
                    value.publication is None or value.publication.status != "COMMITTED" or
                    value.publication.requested_mode != "NORMAL" or value.session_effects_performed is not True):
                _fail("resolution")
        elif value.status == "REFUSED" and value.session_effects_performed is not False:
            _fail("resolution")
    elif kind is SessionLifecycleCaptureAdmission:
        budget = (value.reserved_events, value.reserved_bytes, value.reserved_aliases, value.reserved_supporting_bytes)
        if value.status == "CONFIRMED":
            if budget not in ((4, 327680, 512, 98304), (4, 655360, 512, 425984), (4, 688128, 512, 458752)) or value.failure_code is not None:
                _fail("capture.admission")
        elif value.failure_code is None or budget not in ((0, 0, 0, 0), (4, 327680, 512, 98304), (4, 655360, 512, 425984), (4, 688128, 512, 458752)):
            _fail("capture.admission")
    elif kind is SessionLifecycleCompletion:
        if len(set(value.confirmed_references)) != len(value.confirmed_references):
            _fail("capture.finish")
        if (value.status == "COMPLETE") != (value.failure_code is None):
            _fail("capture.finish")
    elif kind is SessionFailureDetail:
        # Wrong-reference COMPLETE responses are retained as actual unconfirmed
        # observations. Matching and success authority belong to the owner.
        if value.completion_failure_code is None and value.unconfirmed_completion_observation is not None:
            _fail("capture.finish")
    elif kind is SessionOperationResult:
        _same(value.admission.request, value.request.request, "capture.admission")
        _same(value.admission.before, value.before, "capture.admission")
        _same(value.context_observation.snapshot, value.before, "operation_context.context_observation")
        _same(value.context_observation.operation_reference, value.request.request.request_reference, "operation_context")
        if value.after is not None:
            _same(value.after.binding, value.before.binding, "publication.after")
        if value.cause is not None:
            _primary_request(value.cause, value.request.request, "cause")
        if value.publication is not None:
            _same(value.publication.request_reference, value.request.request.request_reference, "publication")
            _same(value.publication.before, value.before, "publication.before")
            _same(value.session_effects_performed, value.publication.session_effects_performed, "publication")
        if value.status == "COMPLETED" and value.failure_detail is not None:
            _fail("request")
        if value.status == "REFUSED" and (value.admission.status != "REJECTED" or value.session_effects_performed is not False):
            _fail("capture.admission")
        confirmed = tuple(record.diagnostic_reference for record in value.confirmed_lifecycle_records)
        attempted = tuple(record.diagnostic_reference for record in value.attempted_lifecycle_records)
        if len(set(confirmed)) != len(confirmed) or len(set(attempted)) != len(attempted) or not set(confirmed).issubset(attempted):
            _fail("capture")
    elif kind is SessionDeniedAttempt:
        _same(value.session_reference, value.frozen_snapshot.binding.session_reference, "request.session_reference")
        if value.reason_code == "SESSION_TERMINAL" and not value.frozen_snapshot.terminal_latched:
            _fail("request.expected_snapshot")
        if value.request_observation == "NOT_INSPECTED_AT_TERMINAL" and value.request_reference is not None:
            _fail("request.reference")
        if value.capture_status == "CONFIRMED" and value.attempted_record is None:
            _fail("capture")
        if value.attempted_record is not None:
            record = value.attempted_record
            if (record.envelope.stage != "DETECTION" or record.envelope.diagnostic_kind != "STATE_VALIDITY" or
                    record.envelope.parent_diagnostic_reference is not None or
                    record.envelope.chain_root_reference != record.diagnostic_reference or
                    record.envelope.severity != "CRITICAL" or record.envelope.disposition != "BLOCKED"):
                _fail("capture")
    elif kind is SessionHistory:
        if value.main_assessment.assessment_binding.assessment_reference != value.binding.initial_assessment_reference:
            _fail("history")
        if value.frozen != (value.terminal_snapshot is not None):
            _fail("history")
        if value.terminal_snapshot is not None:
            _same(value.terminal_snapshot.binding, value.binding, "history")
            if not value.terminal_snapshot.terminal_latched:
                _fail("history")
        for result in value.command_results:
            _same(result.before.binding, value.binding, "history")
        refs = tuple(result.request.request.request_reference for result in value.command_results)
        if len(set(refs)) != len(refs):
            _fail("history")
    elif kind is SessionRetentionReceipt:
        if value.status == "CONFIRMED":
            if value.failure_code is not None or value.coverage != "COMPLETE_SPECIFIED_SAFE_GRAPH":
                _fail("retention")
        elif value.failure_code is None:
            _fail("retention")
    elif kind is SessionReplayObservation:
        _same(value.request_reference, value.original_result.request.request.request_reference, "request.reference")
        _same(value.current_snapshot.binding, value.original_result.before.binding, "request.expected_snapshot")
    elif kind is SessionTerminalChainClosure:
        if value.bridge_record is not None and (type(value.bridge_record.payload) is not recovery.RecoveryDiagnostic or value.bridge_record.payload.steps):
            _fail("history")
        publication = value.actual_terminal_publication
        _same(publication.request_reference, value.request_reference, "publication")
        if publication.status != "COMMITTED" or publication.requested_mode != "SAFE_HALT":
            _fail("publication")
        emission = value.terminal_emission
        if emission.envelope.diagnostic_kind != "SAFE_HALT" or emission.envelope.stage != "TERMINAL":
            _fail("history")
    elif kind is SessionRawBusinessFailure:
        _same(value.session_reference, value.before.binding.session_reference, "request.session_reference")
        if value.after is not None:
            _same(value.after.binding, value.before.binding, "publication.after")


_GATE_COOKIE = object()
_HANDLE_COOKIE = object()
_TOKEN_LOCK_TYPE = type(threading.Lock())


@dataclass(frozen=True, slots=True)
class _GateIssuance:
    marker: object
    original: object
    owner: object
    lease: object
    collector: object
    session_reference: str
    token_lock: object

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self


class SessionExecutionGate:
    """Private issued capability; copied values do not copy issuance."""
    __slots__ = ("_owner", "_lease", "_collector", "_session_reference",
                 "_cookie", "_self_identity", "_capture_lock", "_disposition", "_original_association")

    def __new__(cls, *args, **kwargs):
        _fail("execution_gate", "SESSION_LEASE_REJECTED")

    def stage_grant(self, stage):
        if not _is_issued_gate(self):
            _fail("execution_gate", "SESSION_LEASE_REJECTED")
        _choice(stage, STAGE_GRANT_KINDS, "execution_gate")
        from .session import ReferenceSessionLifecycle
        grant = ReferenceSessionLifecycle._stage_grant(self._owner, self, stage)
        _exact(grant, SessionStageGrant, "execution_gate")
        SessionStageGrant.__post_init__(grant)
        return grant

    def capture_disposition(self):
        if not _is_issued_gate(self):
            return "UNAVAILABLE"
        if not self._capture_lock.acquire(blocking=False):
            return "UNAVAILABLE"
        try:
            return self._disposition if type(self._disposition) is str and self._disposition in ('ACTIVE', 'SEALED') else 'UNAVAILABLE'
        finally:
            self._capture_lock.release()

    @staticmethod
    def validate_module_capture(gate, collector, operation_reference, producer):
        if (not _gate_matches_collector(gate, collector) or type(operation_reference) is not str or
                type(producer) is not str or type(gate._lease) is not SessionModuleLease):
            return False
        try:
            revalidate_value(gate._lease)
            command = gate._lease.command
            policy = command.expected_snapshot.binding.policy_binding
            return (policy.policy_version == '1.1.0' and command.request_reference == operation_reference and
                command.producer == producer and producer in MODULE_PRODUCERS)
        except (SessionContractError, AttributeError, ValueError):
            return False


def _is_issued_gate(gate):
    if type(gate) is not SessionExecutionGate:
        return False
    cookie = getattr(gate, '_cookie', None)
    association = getattr(gate, '_original_association', None)
    if (type(association) is not tuple or len(association) != 6 or association[0] is not gate or
            type(cookie) is not _GateIssuance or cookie.owner is not association[1] or cookie.lease is not association[2] or
            cookie.collector is not association[3] or type(cookie.session_reference) is not str or
            type(association[4]) is not str or cookie.session_reference != association[4] or cookie.token_lock is not association[5]):
        return False
    return (type(cookie) is _GateIssuance and cookie.marker is _GATE_COOKIE and cookie.original is gate and
        getattr(gate, '_self_identity', None) is gate and getattr(gate, '_owner', None) is cookie.owner and
        getattr(gate, '_lease', None) is cookie.lease and getattr(gate, '_collector', None) is cookie.collector and
        type(getattr(gate, '_capture_lock', None)) is _TOKEN_LOCK_TYPE and gate._capture_lock is cookie.token_lock and
        type(getattr(gate, '_session_reference', None)) is str and gate._session_reference == cookie.session_reference)


def _gate_is_issued_by(gate, owner):
    return _is_issued_gate(gate) and gate._owner is owner


def _issue_gate(owner, lease, *, collector):
    from .session import ReferenceSessionLifecycle
    from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
    _exact(owner, ReferenceSessionLifecycle, "execution_gate")
    _exact(lease, (SessionOperationLease, SessionModuleLease), "lease")
    _exact(collector, (ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics), "execution_gate")
    revalidate_value(lease)
    gate = object.__new__(SessionExecutionGate)
    gate._owner, gate._lease = owner, lease
    gate._collector = collector
    gate._session_reference = lease.before.binding.session_reference
    gate._capture_lock = threading.Lock()
    gate._cookie = _GateIssuance(_GATE_COOKIE, gate, owner, lease, collector, gate._session_reference, gate._capture_lock)
    gate._original_association = (gate, owner, lease, collector, gate._session_reference, gate._capture_lock)
    gate._self_identity = gate
    gate._disposition = "SEALED"
    return gate


def _set_capture_disposition(owner, gate, disposition):
    if not _gate_is_issued_by(gate, owner):
        _fail("execution_gate", "SESSION_LEASE_REJECTED")
    _choice(disposition, ("ACTIVE", "SEALED"), "execution_gate")
    # Revocation is the native latch, independent of a reader's held token lock.
    # Readers still return UNAVAILABLE while that tiny lock is busy.
    gate._disposition = disposition


class SessionRetentionHandle:
    """Exact collector-issued local identity without a wire form."""
    __slots__ = ("_collector", "_session_reference", "_cookie", "_self_identity")

    def __new__(cls, *args, **kwargs):
        _fail("retention", "SESSION_RETENTION_FAILED")


def _issue_retention_handle(collector, session_reference):
    from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
    _exact(collector, (ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics), "retention")
    _reference(session_reference, "request.session_reference")
    handle = object.__new__(SessionRetentionHandle)
    handle._collector, handle._session_reference = collector, session_reference
    handle._cookie, handle._self_identity = _HANDLE_COOKIE, handle
    return handle


def _handle_is_issued_by(handle, collector):
    return (type(handle) is SessionRetentionHandle and
            getattr(handle, "_cookie", None) is _HANDLE_COOKIE and
            getattr(handle, "_self_identity", None) is handle and
            getattr(handle, "_collector", None) is collector)


def _gate_matches_collector(gate, collector, handle=None):
    """Read local issued identities without entering an owner or taking locks."""
    from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
    if ((type(collector) is not ReferenceDevelopmentDiagnostics and type(collector) is not ReferenceReleaseDiagnostics) or
            not _is_issued_gate(gate) or getattr(gate, "_collector", None) is not collector):
        return False
    if handle is None:
        return True
    return (_handle_is_issued_by(handle, collector) and
            type(gate._session_reference) is str and type(handle._session_reference) is str and
            gate._session_reference == handle._session_reference)



MODULE_PRODUCERS = ('REALM_ENCODER', 'TRANSITION_REGISTRY', 'TOPOLOGY_GENERATOR', 'AXIOM_EVALUATOR')
MODULE_OPERATION_ARGUMENTS = {
    'ENCODE_REALM': ('REALM_ENCODER', 'RealmEncodingArguments'),
    'RESOLVE_TRANSITIONS': ('TRANSITION_REGISTRY', 'TransitionResolutionArguments'),
    'APPLY_TRANSITION': ('TRANSITION_REGISTRY', 'TransitionApplicationArguments'),
    'GENERATE_TOPOLOGY': ('TOPOLOGY_GENERATOR', 'TopologyArguments'),
    'EVALUATE_AXIOMS': ('AXIOM_EVALUATOR', 'AxiomArguments'),
}
MODULE_VALUE_FIELDS = {
    'SessionModuleCommand': ('request_reference', 'session_reference', 'expected_snapshot', 'producer', 'operation', 'origin_action', 'diagnostic_context', 'arguments', 'dependency_operation_references'),
    'RealmEncodingArguments': (),
    'TransitionResolutionArguments': (),
    'TransitionApplicationArguments': ('selection',),
    'TopologyArguments': ('seed', 'depth'),
    'AxiomArguments': ('subject',),
    'SessionModuleLease': ('lease_reference', 'command', 'before', 'active_snapshot', 'action', 'generation'),
    'SessionModuleAdmission': ('status', 'command', 'before', 'lease', 'failure_code'),
    'SessionModuleResult': ('command', 'status', 'before', 'after', 'session_effects_performed', 'admission', 'origin_diagnosis', 'origin_completion', 'module_capture', 'actual_pure_result', 'failure_code', 'coverage'),
    'SessionModuleCutover': ('request_reference', 'lease_reference', 'admitted_generation', 'before_snapshot_reference', 'active_snapshot_reference', 'phase', 'actual_origin_reference', 'actual_module_operation_reference', 'cutover_snapshot_reference'),
    'SessionModuleExecutionObservation': ('result', 'control_observation', 'current_snapshot'),
    'SessionModuleHistory': ('history_reference', 'session_binding_reference', 'results', 'control_observations', 'frozen', 'cutover_generation', 'pending_cutover'),
    'SessionModuleReplayObservation': ('request_reference', 'original_result', 'current_snapshot'),
    'SessionModuleRawFailure': ('request_reference', 'session_reference', 'failure_code', 'phase', 'session_effects_performed', 'actual_snapshot', 'coverage'),
    'SessionModuleRetentionReceipt': ('session_reference', 'request_reference', 'phase', 'status', 'coverage', 'pinned_supporting_count', 'supporting_reference', 'failure_code'),
}


class _ModuleRecord(_Record):
    __slots__ = ()
    def __post_init__(self):
        _validate_module_value(self)


from dataclasses import make_dataclass as _make_module_dataclass
MODULE_VALUE_TYPES = ()
for _name, _names in MODULE_VALUE_FIELDS.items():
    _cls = _make_module_dataclass(_name, [(name, object) for name in _names],
        bases=(_ModuleRecord,), frozen=True, slots=True, namespace={'__module__': __name__})
    globals()[_name] = _cls
    MODULE_VALUE_TYPES += (_cls,)


class SessionModuleCaptureAdmission:
    __slots__ = ('status', 'scope', 'failure_code')
    def __init__(self, status, scope, failure_code):
        _choice(status, ('ADMITTED', 'REJECTED', 'NOT_CONFIRMED'), 'capture.admission')
        if failure_code is not None:
            _choice(failure_code, SESSION_RETENTION_FAILURES, 'retention')
        if (status == 'ADMITTED') != (scope is not None and failure_code is None):
            _fail('capture.admission')
        self.status, self.scope, self.failure_code = status, scope, failure_code


def _validate_module_value(value):
    from . import realm_transition_values as rt
    from . import generation_values as gen
    from . import diagnostic_module_values as module
    kind = type(value)
    if not any(kind is cls for cls in MODULE_VALUE_TYPES):
        _fail('request')
    for name in ('request_reference', 'actual_module_operation_reference'):
        if name in MODULE_VALUE_FIELDS[kind.__name__] and getattr(value, name) is not None:
            _reference(getattr(value, name), 'request.reference', 160)
    for name in ('session_reference', 'lease_reference', 'history_reference', 'session_binding_reference',
                 'before_snapshot_reference', 'active_snapshot_reference', 'cutover_snapshot_reference', 'actual_origin_reference'):
        if name in MODULE_VALUE_FIELDS[kind.__name__] and getattr(value, name) is not None:
            _reference(getattr(value, name), 'request')
    if kind is SessionModuleCommand:
        _exact(value.expected_snapshot, SessionSnapshot, 'request.expected_snapshot')
        _choice(value.producer, MODULE_PRODUCERS, 'request')
        _choice(value.operation, tuple(MODULE_OPERATION_ARGUMENTS), 'request')
        expected_producer, arguments = MODULE_OPERATION_ARGUMENTS[value.operation]
        _same(value.producer, expected_producer, 'request')
        _exact(value.arguments, globals()[arguments], 'request')
        _constant(value.origin_action, 'CAPTURE_CURRENT_DIAGNOSIS', 'request')
        _exact(value.diagnostic_context, state.DiagnosticContext, 'request')
        state.DiagnosticContext.__post_init__(value.diagnostic_context)
        prefix = value.request_reference + ':module:origin'
        _same(value.diagnostic_context.assessment_reference, prefix + ':assessment', 'request')
        _same(value.diagnostic_context.original_input_reference, prefix + ':input', 'request')
        _same(value.diagnostic_context.detection_reference, prefix + ':detection', 'request')
        _same(value.diagnostic_context.classification_reference, prefix + ':classification', 'request')
        _same(value.session_reference, value.expected_snapshot.binding.session_reference, 'request.session_reference')
        object.__setattr__(value, 'dependency_operation_references', _sequence(value.dependency_operation_references,
            lambda ref, field: _reference(ref, field, 160), 0, 3, 'request'))
        if len(set(value.dependency_operation_references)) != len(value.dependency_operation_references):
            _fail('request')
    elif kind is TransitionApplicationArguments:
        _exact(value.selection, rt.TransitionSelection, 'request')
        rt.revalidate_value(value.selection)
    elif kind is TopologyArguments:
        if type(value.seed) is not str or re.fullmatch(r'[A-Za-z0-9_-]{1,32}', value.seed, re.ASCII) is None:
            _fail('request')
        _integer(value.depth, 0, 6, 'request')
    elif kind is AxiomArguments:
        _exact(value.subject, gen.AxiomSubject, 'request')
        gen.revalidate_value(value.subject)
    elif kind is SessionModuleLease:
        _exact(value.command, SessionModuleCommand, 'request')
        _exact(value.before, SessionSnapshot, 'request.expected_snapshot')
        _exact(value.active_snapshot, SessionSnapshot, 'request.expected_snapshot')
        _constant(value.action, 'MODULE', 'lease')
        _integer(value.generation, 0, MAX_GENERATION, 'generation')
        _same(value.before, value.command.expected_snapshot, 'request.expected_snapshot')
        _same(value.active_snapshot.binding, value.before.binding, 'binding')
        _same(value.active_snapshot.generation, value.generation, 'generation')
        _same(value.active_snapshot.current_state, value.before.current_state, 'request.expected_snapshot')
        _same(value.active_snapshot.active_operation_reference, value.command.request_reference, 'lease')
    elif kind is SessionModuleAdmission:
        _choice(value.status, SESSION_ADMISSION_DECISIONS, 'request')
        _exact(value.command, SessionModuleCommand, 'request')
        _exact(value.before, SessionSnapshot, 'request.expected_snapshot')
        if value.lease is not None:
            _exact(value.lease, SessionModuleLease, 'lease')
            _same(value.lease.command, value.command, 'lease')
        if value.failure_code is not None:
            _choice(value.failure_code, SESSION_FAILURE_CODES, 'request')
        if (value.status == 'GRANTED') != (value.lease is not None and value.failure_code is None):
            _fail('lease')
    elif kind is SessionModuleResult:
        _exact(value.command, SessionModuleCommand, 'request')
        _choice(value.status, ('COMPLETED', 'REFUSED', 'FAILED', 'UNCONFIRMED'), 'request')
        _exact(value.before, SessionSnapshot, 'request.expected_snapshot')
        _exact(value.after, SessionSnapshot, 'request.expected_snapshot')
        _same(value.before.binding, value.after.binding, 'binding')
        _constant(value.session_effects_performed, False, 'publication')
        _exact(value.admission, SessionModuleAdmission, 'request')
        _same(value.admission.command, value.command, 'request')
        _same(value.admission.before, value.before, 'request.expected_snapshot')
        if value.admission.status == 'GRANTED':
            _same(value.before, value.command.expected_snapshot, 'request.expected_snapshot')
        if value.origin_diagnosis is not None:
            _exact(value.origin_diagnosis, (state.StateDiagnosis, state.DiagnosticCaptureFailure), 'origin_assessment')
            _same(value.origin_diagnosis.assessment_binding.assessment_reference,
                value.command.diagnostic_context.assessment_reference, 'origin_assessment')
            _same(value.origin_diagnosis.source_binding, value.before.binding.canonical_binding, 'binding')
            _same(value.origin_diagnosis.profile_binding, value.before.binding.profile_binding, 'binding')
        if value.origin_completion is not None:
            _exact(value.origin_completion, diagnostics.DiagnosticsCompletionReceipt, 'capture.finish')
            _same(value.origin_completion.operation_reference, value.command.diagnostic_context.assessment_reference, 'capture.finish')
        if value.module_capture is not None:
            _exact(value.module_capture, module.ModuleCaptureReceipt, 'capture')
            module.revalidate_value(value.module_capture)
            _same(value.module_capture.operation_reference, value.command.request_reference, 'request')
        if value.actual_pure_result is not None:
            _exact(value.actual_pure_result, (*rt.RESULT_TYPES, *gen.PACKET_TYPES), 'request')
        pure = value.actual_pure_result if value.module_capture is None else value.module_capture.result
        if pure is not None:
            _exact(pure, (*rt.RESULT_TYPES, *gen.PACKET_TYPES), 'request')
            actual_origin = pure.origin if any(type(pure) is cls for cls in rt.RESULT_TYPES) else pure.request.origin_diagnosis
            operation_reference = pure.operation_reference if any(type(pure) is cls for cls in rt.RESULT_TYPES) else pure.request.request_reference
            _same(actual_origin, value.origin_diagnosis, 'origin_assessment')
            _same(operation_reference, value.command.request_reference, 'request')
        if value.module_capture is not None and value.actual_pure_result is not None:
            _fail('raw_business_packet')
        if value.failure_code is not None:
            _choice(value.failure_code, (*SESSION_FAILURE_CODES, *module.FAILURES), 'request')
        _choice(value.coverage, ('COMPLETE_SPECIFIED_SAFE_GRAPH', 'PARTIAL', 'API_ONLY', 'STORAGE_UNCERTAIN'), 'capture')
    elif kind is SessionModuleCutover:
        _integer(value.admitted_generation, 0, MAX_GENERATION, 'generation')
        _choice(value.phase, ('ADMITTED', 'DIAGNOSING', 'DIAGNOSED', 'COMPUTING', 'CAPTURING', 'FINISHING'), 'request')
    elif kind is SessionModuleExecutionObservation:
        _exact(value.result, SessionModuleResult, 'request')
        _exact(value.current_snapshot, SessionSnapshot, 'request.expected_snapshot')
        if value.control_observation is not None:
            _exact(value.control_observation, SessionModuleRetentionReceipt, 'retention')
            _same(value.control_observation.request_reference, value.result.command.request_reference, 'retention')
            _same(value.control_observation.session_reference, value.result.command.session_reference, 'retention')
        _same(value.current_snapshot.binding, value.result.after.binding, 'binding')
    elif kind is SessionModuleHistory:
        object.__setattr__(value, 'results', _sequence(value.results, lambda child, field: _exact(child, SessionModuleResult, field), 0, 4, 'history'))
        object.__setattr__(value, 'control_observations', _sequence(value.control_observations,
            lambda child, field: None if child is None else _exact(child, SessionModuleRetentionReceipt, field), 0, 4, 'history'))
        _exact(value.frozen, bool, 'history')
        if len(value.results) != len(value.control_observations):
            _fail('history')
        if value.cutover_generation is not None:
            _integer(value.cutover_generation, 0, MAX_GENERATION, 'generation')
        if value.pending_cutover is not None:
            _exact(value.pending_cutover, SessionModuleCutover, 'history')
        refs = tuple(result.command.request_reference for result in value.results)
        if len(set(refs)) != len(refs):
            _fail('history')
        if len({result.command.producer for result in value.results}) != len(value.results):
            _fail('history')
        for result, receipt in zip(value.results, value.control_observations):
            _same(result.before.binding.binding_reference, value.session_binding_reference, 'binding')
            if receipt is not None:
                _same(receipt.request_reference, result.command.request_reference, 'retention')
    elif kind is SessionModuleReplayObservation:
        _exact(value.original_result, SessionModuleExecutionObservation, 'request')
        _exact(value.current_snapshot, SessionSnapshot, 'request.expected_snapshot')
        _same(value.request_reference, value.original_result.result.command.request_reference, 'request.reference')
    elif kind is SessionModuleRawFailure:
        _constant(value.failure_code, 'SESSION_RAW_BUSINESS_LIMIT', 'raw_business_packet')
        _choice(value.phase, ('ORIGIN', 'CANDIDATE_RESULT', 'HISTORY', 'ANTICIPATED_TERMINAL'), 'raw_business_packet')
        _constant(value.session_effects_performed, False, 'publication')
        _exact(value.actual_snapshot, SessionSnapshot, 'request.expected_snapshot')
        _choice(value.coverage, ('API_ONLY', 'PARTIAL'), 'capture')
    elif kind is SessionModuleRetentionReceipt:
        _choice(value.phase, ('ADMISSION', 'FINAL_RESULT', 'PIN'), 'retention')
        _choice(value.status, SESSION_RETENTION_STATUSES, 'retention')
        _choice(value.coverage, SESSION_RETENTION_COVERAGES, 'retention')
        _integer(value.pinned_supporting_count, 0, 2663, 'retention')
        if value.supporting_reference is not None and (type(value.supporting_reference) is not str or re.fullmatch(r'ref:[0-9]{6}', value.supporting_reference, re.ASCII) is None):
            _fail('retention')
        if value.failure_code is not None:
            _choice(value.failure_code, SESSION_RETENTION_FAILURES, 'retention')


def _public_value_types(module):
    return tuple(value for name, value in vars(module).items()
                 if not name.startswith("_") and type(value) is type and
                 value.__module__ == module.__name__ and is_dataclass(value))


# These are finite source-owned classes, not a runtime registration mechanism.
_LEGACY_TYPES = tuple(dict.fromkeys(
    kind for module in (state, normalization, recovery, diagnostics)
    for kind in _public_value_types(module)))
from . import realm_transition_values as _realm_values
from . import generation_values as _generation_values
from . import diagnostic_module_values as _module_values
_MODULE_EXTERNAL_TYPES = (*_realm_values.OWNED_TYPES, *_generation_values.WIRE_TYPES, *_module_values.WIRE_TYPES)
_SESSION_TYPES = tuple(value for name, value in tuple(globals().items())
                       if not name.startswith("_") and type(value) is type and
                       value.__module__ == __name__ and is_dataclass(value) and
                       value is not SessionStageGrant and not any(value is cls for cls in MODULE_VALUE_TYPES))
_ALL_SESSION_TYPES = _SESSION_TYPES + MODULE_VALUE_TYPES
_WIRE_TYPES = _LEGACY_TYPES + _ALL_SESSION_TYPES + _MODULE_EXTERNAL_TYPES


def _type_is_one_of(kind, choices):
    return any(kind is choice for choice in choices)


def _revalidate_structure(value, *, allow_json_containers):
    complete, active = set(), set()
    policies, retention_policies = [], []

    def visit(item):
        kind = type(item)
        if item is None or _type_is_one_of(kind, (str, int, bool)):
            return
        if _type_is_one_of(kind, (tuple, frozenset)) or allow_json_containers and _type_is_one_of(kind, (list, dict)):
            identity = id(item)
            if identity in active:
                _fail("raw_business_packet")
            active.add(identity)
            if kind is dict:
                for key, child in item.items():
                    if type(key) is not str:
                        _fail("raw_business_packet")
                    visit(child)
            else:
                for child in item:
                    visit(child)
            active.remove(identity)
            return
        if not _type_is_one_of(kind, _WIRE_TYPES):
            _fail("raw_business_packet")
        identity = id(item)
        if identity in active:
            _fail("raw_business_packet")
        if identity in complete:
            return
        active.add(identity)
        try:
            for field in fields(item):
                visit(object.__getattribute__(item, field.name))
            validator = getattr(kind, "__post_init__", None)
            if validator is not None:
                validator(item)
            else:
                _fail("raw_business_packet")
        except SessionContractError:
            raise
        except (AttributeError, ValueError, TypeError, OverflowError):
            _fail("raw_business_packet")
        finally:
            active.remove(identity)
        complete.add(identity)
        if kind is SessionBinding:
            policies.append(item.policy_binding)
        elif kind is SessionRetentionReceipt:
            retention_policies.append(item._construction_policy)

    try:
        visit(value)
        if any(policy.policy_version == '1.0.0' for policy in policies) and any(policy is not None for policy in retention_policies):
            _fail('binding.policy_binding', 'SESSION_SOURCE_REJECTED')
    except RecursionError:
        _fail("raw_business_packet")


def revalidate_value(value):
    """Recheck exact owned structure before comparisons or serialization."""
    if not _type_is_one_of(type(value), _WIRE_TYPES):
        _fail("raw_business_packet")
    _revalidate_structure(value, allow_json_containers=False)


def wire_schema(value):
    """Select the exact owned Session family from its full policy context."""
    if not _type_is_one_of(type(value), _ALL_SESSION_TYPES):
        _fail('raw_business_packet')
    revalidate_value(value)
    active, policies = set(), []
    def visit(item):
        kind = type(item)
        if kind is SessionBinding:
            policies.append(item.policy_binding)
        elif kind is SessionPolicyBinding:
            policies.append(item)
        elif kind is SessionRetentionReceipt and item._construction_policy is not None:
            policies.append(item._construction_policy)
        if not _type_is_one_of(kind, _WIRE_TYPES) or id(item) in active:
            return
        active.add(id(item))
        for field in fields(item):
            child = object.__getattribute__(item, field.name)
            if type(child) is tuple:
                for member in child:
                    visit(member)
            else:
                visit(child)
    visit(value)
    current = _type_is_one_of(type(value), MODULE_VALUE_TYPES) or any(policy.policy_version == '1.1.0' for policy in policies)
    return ('data/schemas/m3_current_source_session_schema.json' if current else
            'data/schemas/m3_session_lifecycle_schema.json')


def _wire_items(value):
    """Return source-owned wire fields without expanding child DAGs."""
    kind = type(value)
    if _type_is_one_of(kind, _MODULE_EXTERNAL_TYPES):
        record = (_module_values.ModuleCaptureReceipt.to_record(value) if kind is _module_values.ModuleCaptureReceipt else
                  _module_values.pure_record(value) if not _type_is_one_of(kind, _module_values.WIRE_TYPES) else
                  kind.to_record(value))
        return tuple(record.items())
    if kind is state.AshState:
        return (("state_space", "F2^9"), ("bits", value.bits))
    if kind is state.ValidityProfile:
        return (("profile_id", value.profile_id), ("source_binding", value.source_binding),
                ("recognized_valid_signatures", tuple(sorted(item.signature for item in value.recognized_valid_states))))
    if kind is state.AvailableProfileBinding:
        return (("availability", "AVAILABLE"), *_wire_items(value.profile))
    if kind is state.UnavailableProfileBinding:
        return (("availability", "UNAVAILABLE"), *_wire_items(value.evidence))
    if _type_is_one_of(kind, (state.EvaluatedPredicate, state.NotEvaluatedPredicate)):
        return (("evaluation", value.evaluation),
                *((field.name, getattr(value, field.name)) for field in fields(value)))
    if kind is state.RejectedCandidateEvidence:
        return (("candidate_kind", value.candidate_kind), ("input_evidence", value.input_evidence))
    if kind is state.CoordinateObservation:
        return tuple((field.name, getattr(value, field.name)) for field in fields(value)
                     if field.name in ("index", "scalar_kind") or getattr(value, field.name) is not None)
    if kind is state.StateValidityDiagnostic:
        return tuple((field.name, value.input_state.bits if field.name == "input_state" and
                      type(value.input_state) is state.AshState else getattr(value, field.name))
                     for field in fields(value))
    if _type_is_one_of(kind, (state.StateDiagnosis, state.StateAssessment,
                state.ClassificationEvidenceFailure, state.DiagnosticCaptureFailure)):
        prefix = tuple((name, state.wire_schema(value) if name == 'schema_ref' else getattr(value, name))
                       for name in ("schema_ref", "artifact_type", "artifact_version", "outcome"))
        extra = (("failure_kind", value.failure_kind),) if kind in (state.ClassificationEvidenceFailure, state.DiagnosticCaptureFailure) else ()
        return (*prefix, *extra, *((field.name, getattr(value, field.name)) for field in fields(value)))
    if _type_is_one_of(kind, _PACKETS):
        prefix = tuple((name, recovery.wire_schema(value) if name == 'schema_ref' else getattr(value, name))
                       for name in ("schema_ref", "artifact_type", "artifact_version", "outcome", "execution_scope"))
        return (*prefix, *((field.name, getattr(value, field.name)) for field in fields(value)),
                ("session_effects_performed", value.session_effects_performed))
    if kind.__module__ == recovery.__name__:
        return (*getattr(kind, "_headers", ()),
                *((field.name, getattr(value, field.name)) for field in fields(value)))
    if kind in (normalization.NormalizationPlan, normalization.NormalizationResult,
                normalization.NormalizationFailure, normalization.NormalizationCaptureFailure):
        prefix = tuple((name, normalization.wire_schema(value) if name == 'schema_ref' else getattr(value, name))
                       for name in ("schema_ref", "artifact_type", "artifact_version"))
        if kind is normalization.NormalizationCaptureFailure:
            prefix = (*prefix, ("outcome", value.outcome))
        extra = (("failure_kind", value.failure_kind),) if kind in (normalization.NormalizationFailure, normalization.NormalizationCaptureFailure) else ()
        return (*prefix, *extra, *((field.name, getattr(value, field.name)) for field in fields(value)))
    return tuple((field.name, getattr(value, field.name)) for field in fields(value)
        if not (kind is SessionHistory and field.name == 'module_history' and value.module_history is None))


def _json_tokens(value, active):
    kind = type(value)
    if value is None:
        yield b"null"
    elif kind is bool:
        yield b"true" if value else b"false"
    elif kind is int:
        try:
            yield str(value).encode("ascii")
        except ValueError:
            _fail("raw_business_packet")
    elif kind is str:
        yield b'"'
        # Splitting source strings preserves the exact JSON escape sequence and
        # bounds temporary scalar encoding even for a plain host record.
        for offset in range(0, len(value), 4096):
            yield json.dumps(value[offset:offset + 4096], ensure_ascii=True)[1:-1].encode("ascii")
        yield b'"'
    elif _type_is_one_of(kind, (tuple, list)):
        identity = id(value)
        if identity in active:
            _fail("raw_business_packet")
        active.add(identity)
        try:
            yield b"["
            for index, child in enumerate(value):
                if index:
                    yield b","
                yield from _json_tokens(child, active)
            yield b"]"
        finally:
            active.remove(identity)
    elif kind is dict or _type_is_one_of(kind, _WIRE_TYPES):
        identity = id(value)
        if identity in active:
            _fail("raw_business_packet")
        active.add(identity)
        try:
            items = value.items() if kind is dict else _wire_items(value)
            yield b"{"
            first = True
            for name, child in items:
                if type(name) is not str:
                    _fail("raw_business_packet")
                if not first:
                    yield b","
                first = False
                yield from _json_tokens(name, active)
                yield b":"
                yield from _json_tokens(child, active)
            yield b"}"
        finally:
            active.remove(identity)
    else:
        _fail("raw_business_packet")


def _bounded_tokens(value, limit):
    _integer(limit, 0, MAX_RAW_BUSINESS_BYTES, "raw_business_packet")
    # Plain exact JSON containers are allowed for protected host projections
    # and internal sizing. They do not become authenticated business values.
    if not _type_is_one_of(type(value), _WIRE_TYPES) and not _type_is_one_of(type(value), (dict, list, tuple)):
        _fail("raw_business_packet")
    _revalidate_structure(value, allow_json_containers=_type_is_one_of(type(value), (dict, list, tuple)))
    count = 0
    for token in _json_tokens(value, set()):
        count += len(token)
        if count > limit:
            _fail("raw_business_packet", "SESSION_RAW_BUSINESS_LIMIT")
        yield token


def raw_business_size(value, *, limit=MAX_RAW_BUSINESS_BYTES):
    """Count compact JSON bytes; return limit+1 as the bounded overflow signal."""
    try:
        return sum(len(token) for token in _bounded_tokens(value, limit))
    except SessionContractError as error:
        if error.failure_code != "SESSION_RAW_BUSINESS_LIMIT":
            raise
        return limit + 1


def raw_business_bytes(value, *, limit=MAX_RAW_BUSINESS_BYTES):
    """Return a complete bounded compact JSON packet or an explicit refusal."""
    return b"".join(_bounded_tokens(value, limit))


def raw_business_record(value, *, limit=MAX_RAW_BUSINESS_BYTES):
    """Return the complete bounded plain wire record; never truncate."""
    return json.loads(raw_business_bytes(value, limit=limit))
