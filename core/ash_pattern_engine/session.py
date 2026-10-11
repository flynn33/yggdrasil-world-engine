"""Issued reference session lifecycle under YWE-REQ-0044.

RecoveryEngine supplies the sole public mutation authority. This collaborator
owns semantic state, admission and immutable history; Diagnostics owns capture.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, replace
import hashlib
import json
import threading

from . import state_values as sv
from . import recovery_values as rv
from . import diagnostics_values as dv
from . import session_values as v
from .state_model import StateModel


_MAX_GENERATION = (1 << 64) - 1
_PACKETS = (rv.RecoveryNoAction, rv.RecoveredValue, rv.RecoveredFallbackValue,
            rv.RecoveryHandoff, rv.RecoveryFailure)
_COMMANDS = (v.SessionRecoveryRequest, v.SessionContainmentRequest,
             v.SessionResolutionRequest, v.SessionHaltRequest)
_SEVERITIES = ("INFO", "WARNING", "ERROR", "CRITICAL")
_CONTAINMENT_RULES = dict(zip(rv.CONTAINMENT_TRIGGERS, (
    "ASH-CONTAINMENT-TRIGGER-001", "ASH-CONTAINMENT-TRIGGER-002",
    "ASH-CONTAINMENT-TRIGGER-003", "ASH-CONTAINMENT-TRIGGER-004")))
_HALT_RULES = {
    "CONTAINMENT_BREACH": "ASH-HALT-TRIGGER-001",
    "ESCALATION_FROM_FAILED": "ASH-HALT-TRIGGER-002",
    "OPERATOR_HALT_REQUEST": "ASH-HALT-TRIGGER-003",
    "POLICY_HALT_REQUEST": "ASH-HALT-TRIGGER-004",
    "UNRESOLVABLE_BLOCKED_RECOVERY": "ASH-HALT-TRIGGER-005",
}
_RESTRICTED = ("READ_SESSION", "READ_DIAGNOSTICS", "EXPORT_DIAGNOSTICS",
               "REQUEST_HALT", "RESOLVE_CONTAINMENT")
_FACADE_KEY = object()
_SIZING_TEXT = "\U00010000" * 512
_SIZING_REFERENCE = "r" * 256


def _sizing_size(record, limit):
    """Count private closed sizing records; never accept a caller dictionary."""
    total = 0
    for chunk in json.JSONEncoder(ensure_ascii=True, separators=(",", ":"),
                                  allow_nan=False).iterencode(record):
        total += len(chunk)
        if total > limit:
            return limit + 1
    return total


def _sizing_upper(record):
    """Dominate bounded future scalar values without claiming an observation."""
    if type(record) is dict:
        return {key: _sizing_upper(value) for key, value in record.items()}
    if type(record) is list:
        return [_sizing_upper(value) for value in record]
    if type(record) is str:
        return _SIZING_TEXT
    if type(record) is bool:
        return False
    if type(record) is int:
        return record if len(str(record)) > 20 else _MAX_GENERATION
    return record


def _assessment_completion_sizing_record():
    """Cartesian wire upper from the owned health domains and tuple ceilings."""
    enums = dict(dv.ENUMS)
    def longest(domain):
        return max(enums[domain], key=lambda value: (len(value), value))
    health = {field.name: _MAX_GENERATION for field in fields(dv.DiagnosticsHealth)}
    health.update(coverage_status=longest("OverallCoverage"), active_reservations=8,
        used_bytes=v.MAX_RAW_BUSINESS_BYTES, storage_state=longest("StorageState"),
        last_failure_code=longest("DiagnosticsFailure"), range_detail_coalesced=False,
        meta_record_count=16, meta_storage_state=longest("StorageState"),
        fallback_cause_code=longest("MetaCauseCode"),
        missing_sources=[dict(source=longest("CoverageSource"), status=longest("CoverageStatus"),
                              reason=longest("UnavailableReason")) for _ in range(32)],
        retention_boundaries=[dict(first_sequence=_MAX_GENERATION, last_sequence=_MAX_GENERATION,
            record_count=_MAX_GENERATION, reason=longest("RetentionReason"), coalesced=False)
            for _ in range(16)],
        counter_states=[dict(field=longest("CounterField"), status=longest("CounterStatus"),
                             reason=longest("CounterReason")) for _ in range(8)])
    # The structural receipt permits 768 indices even when the actual assessment
    # owns two slots. Include that larger representation in the future guard.
    return dict(operation_reference=_SIZING_REFERENCE, status=longest("CompletionStatus"),
        operation_outcome=longest("ObservedOutcome"), confirmed_event_indices=[1023] * 768,
        diagnostic_coverage=longest("OverallCoverage"), failure_code=longest("DiagnosticsFailure"),
        attempted_event_index=1023, health=health)


class ReferenceSession:
    """Exact privately issued facade; its engine alone accepts its identity."""
    __slots__ = ("_services",)

    def __init__(self, key=None, services=None):
        if key is not _FACADE_KEY:
            raise v.SessionContractError("SESSION_INPUT_INVALID", "request")
        self._services = services

    def read(self):
        return self._services.read_session(self)

    def execute(self, command):
        return self._services.execute_session(self, command)

    def history(self):
        return self._services.read_session_history(self)


class _Refusal(Exception):
    def __init__(self, code, field, reason, evidence=None):
        self.code, self.field, self.reason, self.evidence = code, field, reason, evidence
        self.eligible = False


@dataclass
class _Operation:
    command: object
    lease: object
    gate: object
    admission: object
    context: object
    origin: object = None
    origin_completion: object = None
    recovery: object = None
    cause: object = None
    publication: object = None
    resolution: object = None
    post: object = None
    post_completion: object = None
    scope: object = None
    completion: object = None
    failure: object = None
    confirmed: tuple = ()
    attempted: tuple = ()
    pending: object = None
    effects: object = False
    after: object = None
    terminal: bool = False
    finished: bool = False
    observed: bool = False
    raw_phase: object = None
    interrupted: object = None


class ReferenceSessionLifecycle:
    """One controlled semantic owner, bound once to one issuing engine."""

    def __init__(self, state_model, diagnostics, policy_binding):
        from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
        if type(state_model) is not StateModel:
            raise v.SessionContractError("SESSION_INPUT_INVALID", "binding")
        if not any(type(diagnostics) is kind for kind in (ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics)):
            raise v.SessionContractError("SESSION_INPUT_INVALID", "capture")
        if type(policy_binding) is not v.SessionPolicyBinding:
            raise v.SessionContractError("SESSION_SOURCE_REJECTED", "binding.policy_binding")
        v.revalidate_value(policy_binding)
        self._model, self._diagnostics, self._policy = state_model, diagnostics, policy_binding
        self._lock = threading.RLock()
        self._services = self._facade = self._binding = self._snapshot = None
        self._initial = self._accepted = self._phase_origin = None
        self._accepted_generation = None
        self._handle = self._last_retention = None
        self._serial = 0
        self._prefix = None
        self._lease = self._phase_snapshot = self._active = None
        self._gates = {}
        self._ledger = {}
        self._recover_count = self._mode_count = self._denial_count = 0
        self._preterminal_denial_count = 0
        self._children, self._recoveries, self._results, self._resolutions = [], [], [], []
        self._confirmed, self._attempted, self._pending = [], [], []
        self._chronology = []
        self._main_root = self._main_previous = None
        self._severity = "INFO"
        self._terminal_reference = None
        self._terminal_members = frozenset()
        self._frozen_partial = frozenset()

    def _bind_engine(self, engine_identity, state_model, diagnostics):
        from .recovery import _SessionEngineServices
        if (type(engine_identity) is not _SessionEngineServices or
                not engine_identity.is_issued(engine_identity) or
                not engine_identity.matches_composition(state_model, diagnostics) or
                state_model is not self._model or diagnostics is not self._diagnostics):
            raise v.SessionContractError("SESSION_INPUT_INVALID", "binding")
        with self._lock:
            if self._services is not None:
                raise v.SessionContractError("SESSION_OPERATION_DUPLICATE", "binding")
            self._services = engine_identity

    def _identity(self, engine, session=None):
        if engine is not self._services or engine is None:
            raise v.SessionContractError("SESSION_INPUT_INVALID", "binding")
        if session is not None and (type(session) is not ReferenceSession or session is not self._facade):
            raise v.SessionContractError("SESSION_ORIGIN_FOREIGN", "request.session_reference")

    def _next_reference(self, kind):
        self._serial += 1
        return self._prefix + ":" + kind + ":" + str(self._serial)

    def _new_snapshot(self, **changes):
        return replace(self._snapshot, snapshot_reference=self._next_reference("snapshot"), **changes)

    def _source(self, binding):
        if type(binding) is not v.SessionBinding:
            raise v.SessionContractError("SESSION_INPUT_INVALID", "binding")
        v.revalidate_value(binding)
        try:
            baseline = sv.canonical_source_baseline(binding.canonical_binding)
        except sv.StateContractError:
            raise v.SessionContractError("SESSION_SOURCE_REJECTED", "binding.canonical_binding") from None
        if baseline != "N3_LIFECYCLE" or binding.canonical_binding != self._model.canonical_binding:
            raise v.SessionContractError("SESSION_SOURCE_REJECTED", "binding.canonical_binding")
        expected = tuple(rv.SourcePin(path, digest) for path, digest in
                         rv.recovery_contract_pin_fields(binding.canonical_binding))
        if (binding.recovery_binding.canonical_binding != binding.canonical_binding or
                binding.recovery_binding.contract_pins != expected):
            raise v.SessionContractError("SESSION_SOURCE_REJECTED", "binding.recovery_binding")
        if binding.profile_binding != self._model.profile_binding:
            raise v.SessionContractError("SESSION_PROFILE_REJECTED", "binding.profile_binding")
        if binding.policy_binding != self._policy:
            raise v.SessionContractError("SESSION_SOURCE_REJECTED", "binding.policy_binding")

    def _assessment_valid(self, actual, snapshot, *, stable=False):
        if type(actual) is not sv.StateAssessment or type(actual.parsed_state) is not sv.AshState:
            return False
        try:
            actual.__post_init__()
            validation = self._model.validate_assessment(actual)
        except (sv.StateContractError, rv.RecoveryContractError):
            return False
        context = sv.SystemContext(snapshot.mode == "SAFE_HALT", snapshot.mode == "CONTAINED")
        return (validation.status == "VERIFIED" and actual.parsed_state == snapshot.current_state and
                actual.system_context == context and actual.source_binding == snapshot.binding.canonical_binding and
                actual.profile_binding == snapshot.binding.profile_binding and
                len(actual.emitted_diagnostics) == 2 and
                (not stable or (actual.system_state_class == "STABLE" and
                                actual.recovery_category == "NO_ACTION" and
                                actual.state_validity_diagnostic.is_valid)))

    @staticmethod
    def _complete(receipt, reference):
        if type(receipt) is not dv.DiagnosticsCompletionReceipt:
            return False
        try:
            receipt.__post_init__()
        except dv.DiagnosticsContractError:
            return False
        return receipt.operation_reference == reference and receipt.status == "COMPLETE"

    def _retention(self, phase, receipt):
        if type(receipt) is v.SessionRetentionReceipt:
            try:
                v.revalidate_value(receipt)
            except v.SessionContractError:
                receipt = None
        if (type(receipt) is not v.SessionRetentionReceipt or
                receipt.session_reference != self._binding.session_reference or receipt.phase != phase):
            return v.SessionRetentionReceipt(self._binding.session_reference, "NOT_CONFIRMED", phase,
                "STORAGE_UNCERTAIN", 0, 0, 0, "SESSION_RETENTION_UNCONFIRMED")
        return receipt

    def _remember_retention(self, receipt):
        # A later successful pin cannot erase the observer's actual failed
        # receipt. This bounded API sidecar never rewrites an observed result.
        if (receipt is not None and (self._last_retention is None or
                self._last_retention.status == "CONFIRMED")):
            self._last_retention = receipt

    def _open(self, engine, origin, *, session_binding):
        self._identity(engine)
        self._source(session_binding)
        if type(origin) is not sv.StateAssessment or type(origin.parsed_state) is not sv.AshState:
            raise v.SessionContractError("SESSION_ORIGIN_REJECTED", "origin_assessment")
        try:
            validation = self._model.validate_assessment(origin)
        except (sv.StateContractError, rv.RecoveryContractError):
            raise v.SessionContractError("SESSION_ORIGIN_REJECTED", "origin_assessment") from None
        if (validation.status != "VERIFIED" or origin.system_context != sv.SystemContext(False, False) or
                len(origin.emitted_diagnostics) != 2 or
                origin.assessment_binding.assessment_reference != session_binding.initial_assessment_reference or
                origin.source_binding != session_binding.canonical_binding or
                origin.profile_binding != session_binding.profile_binding):
            raise v.SessionContractError("SESSION_ORIGIN_REJECTED", "origin_assessment")
        with self._lock:
            if self._facade is not None:
                raise v.SessionContractError("SESSION_BUDGET_EXCEEDED", "binding")
            self._binding = session_binding
            self._prefix = "session:" + hashlib.sha256(session_binding.session_reference.encode("ascii")).hexdigest()
            self._snapshot = v.SessionSnapshot(self._next_reference("snapshot"), session_binding, 0,
                origin.parsed_state, "NORMAL", False, "AUDIT_BLOCKED", None, None, False, None, None, None)
            self._initial = self._phase_origin = origin
            self._main_root = origin.assessment_binding.diagnosis_reference
            self._main_previous = origin.emitted_diagnostics[-1].diagnostic_reference
            self._severity = max((e.envelope.severity for e in origin.emitted_diagnostics), key=_SEVERITIES.index)
            self._facade = ReferenceSession(_FACADE_KEY, engine)
            facade = self._facade
        try:
            returned = self._diagnostics.register_session(session_binding)
        except Exception:
            returned = None
        handle = receipt = None
        if type(returned) is tuple and len(returned) == 2:
            handle, receipt = returned
        receipt = self._retention("REGISTER", receipt)
        with self._lock:
            self._handle, self._last_retention = handle, receipt
            terminal = self._snapshot.terminal_latched
        if receipt.status == "CONFIRMED" and handle is not None and not terminal:
            try:
                attached = self._diagnostics.attach_result(handle, origin)
            except Exception:
                attached = None
            receipt = self._retention("ATTACH", attached)
            with self._lock:
                self._last_retention = receipt
                if receipt.status == "CONFIRMED" and not self._snapshot.terminal_latched:
                    self._accepted, self._accepted_generation = origin, 0
                    self._snapshot = self._new_snapshot(admission_status="OPEN",
                        current_assessment_reference=origin.assessment_binding.assessment_reference,
                        observed_system_state_class=origin.system_state_class)
        return facade, receipt

    def _read(self, engine, session):
        self._identity(engine, session)
        with self._lock:
            return self._snapshot

    def _history_value(self, *, extra=None):
        results = tuple(self._results) + (() if extra is None else (extra,))
        return v.SessionHistory(self._prefix + ":history", self._binding, self._initial,
            tuple(self._children), tuple(self._recoveries), results, tuple(self._resolutions),
            tuple(self._confirmed), tuple(self._attempted), tuple(self._pending),
            self._snapshot if self._snapshot.terminal_latched else None, self._snapshot.terminal_latched)

    def _history(self, engine, session):
        self._identity(engine, session)
        with self._lock:
            return self._history_value()

    def _live(self, op):
        return (self._lease is op.lease and self._active is op and
                self._snapshot is self._phase_snapshot and not self._snapshot.terminal_latched)

    def _stage_grant(self, gate, stage):
        with self._lock:
            entry = self._gates.get(id(gate))
            if entry is None or entry[0] is not gate or not v._gate_is_issued_by(gate, self):
                raise v.SessionContractError("SESSION_LEASE_REJECTED", "execution_gate")
            _, lease, ordinal, terminal = entry
            active = (not terminal and ordinal < 8192 and self._lease is lease and
                      self._snapshot is self._phase_snapshot and not self._snapshot.terminal_latched)
            if active:
                self._source(self._binding)
            index = min(ordinal, 8191)
            self._gates[id(gate)] = (gate, lease, min(ordinal + 1, 8192), terminal)
            return v.SessionStageGrant(index, stage, "GRANTED" if active else "CANCELLED",
                                       lease.lease_reference, self._snapshot.generation)

    def _gate(self, lease, *, terminal=False):
        gate = v._issue_gate(self, lease, collector=self._diagnostics)
        self._gates[id(gate)] = (gate, lease, 0, terminal)
        v._set_capture_disposition(self, gate, "ACTIVE")
        return gate

    def _child_link(self, engine, gate):
        self._identity(engine)
        with self._lock:
            entry = self._gates.get(id(gate))
            if (entry is None or entry[0] is not gate or not v._gate_is_issued_by(gate, self) or
                    entry[3] or self._active is None or not self._live(self._active) or
                    self._active.gate is not gate or type(self._active.command) is not v.SessionRecoveryRequest):
                raise v.SessionContractError("SESSION_LEASE_REJECTED", "execution_gate")
            request, before = entry[1].request, entry[1].before
            return v.SessionChildLink(request.request_reference + ":child", self._binding.binding_reference,
                before.generation, before.current_assessment_reference,
                request.request_reference + ":origin:assessment", request.request_reference)

    def _post_mode_snapshot(self, engine, gate, submitted_snapshot):
        self._identity(engine)
        with self._lock:
            entry = self._gates.get(id(gate))
            return (entry is not None and entry[0] is gate and not entry[3] and
                v._gate_is_issued_by(gate, self) and self._active is not None and
                self._active.gate is gate and self._live(self._active) and
                self._active.publication is not None and self._active.publication.status == "COMMITTED" and
                type(submitted_snapshot) is v.SessionSnapshot and submitted_snapshot is self._snapshot and
                submitted_snapshot is self._phase_snapshot and submitted_snapshot.mode in ("NORMAL", "CONTAINED"))

    def _require_live(self, op):
        with self._lock:
            if not self._live(op):
                raise _Refusal("SESSION_EXECUTION_CANCELLED", "execution_gate",
                               "The owner revoked this command phase before further work.")
            self._source(self._binding)

    def _authority(self, command, origin, *, required=True):
        observation = command.authority_observation
        if observation is None:
            if required:
                raise _Refusal("SESSION_AUTHORITY_UNAVAILABLE", "authority", "Required authority is unavailable.")
            return None
        request = command.request
        if (observation.request_reference != request.request_reference or
                observation.expected_snapshot_reference != request.expected_snapshot.snapshot_reference or
                observation.request_origin != origin):
            raise _Refusal("SESSION_EVIDENCE_MISMATCH", "authority", "Authority is not bound to this request.", observation)
        if observation.status != "AUTHORIZED":
            raise _Refusal("SESSION_AUTHORITY_DENIED" if observation.status == "DENIED" else
                           "SESSION_AUTHORITY_UNAVAILABLE", "authority", "Actual authority does not grant this request.", observation)
        return observation

    def _boundary(self, command, condition, *, required=True):
        request = command.request
        matches = tuple(item for item in command.boundary_observations if item.condition == condition)
        if len(matches) != 1:
            if not required and not matches:
                return None
            raise _Refusal("SESSION_BOUNDARY_NOT_SATISFIED", "boundary", "Required bound boundary is not present.")
        observed = matches[0]
        if (observed.request_reference != request.request_reference or
                observed.expected_snapshot_reference != request.expected_snapshot.snapshot_reference):
            raise _Refusal("SESSION_EVIDENCE_MISMATCH", "boundary", "Boundary is not bound to this request.", observed)
        if observed.status != "SATISFIED":
            raise _Refusal("SESSION_BOUNDARY_NOT_SATISFIED", "boundary", "Boundary is not actually satisfied.", observed)
        return observed

    def _owned_recovery(self, reference):
        if reference is None:
            return None
        actual = next((item for item in self._recoveries if
                       item.operation_context.operation_reference == reference), None)
        if actual is None:
            raise _Refusal("SESSION_EVIDENCE_MISMATCH", "cause", "Recovery reference is not in this owner's actual registry.")
        return actual

    def _cause(self, command, kind, trigger, recovery=None):
        request = command.request
        return v.SessionCauseObservation(request.request_reference + ":cause", request.request_reference,
            request.expected_snapshot.snapshot_reference, kind, trigger,
            None if recovery is None else recovery.operation_context.operation_reference,
            getattr(command, "authority_observation", None), getattr(command, "boundary_observations", ()))

    def _guard_containment(self, command, trigger, recovery=None):
        recovery = self._owned_recovery(getattr(command, "recovery_operation_reference", None)) if recovery is None else recovery
        if trigger == "OPERATOR_REQUEST":
            policy_handoff = (type(recovery) is rv.RecoveryHandoff and
                recovery.directive.requested_action == "ENTER_CONTAINMENT" and
                recovery.directive.trigger == trigger and recovery.directive.request_origin == "POLICY" and
                recovery.directive.policy_binding is not None and
                self._complete(recovery.completion_observation, recovery.operation_context.operation_reference))
            observation = getattr(command, "authority_observation", None)
            if not policy_handoff and (observation is None or observation.request_origin not in ("OPERATOR", "POLICY")):
                raise _Refusal("SESSION_AUTHORITY_UNAVAILABLE", "authority", "Containment requires actual operator or policy authority.")
            if not policy_handoff:
                self._authority(command, observation.request_origin)
            kind = "N2_HANDOFF" if policy_handoff else "AUTHORITY_REQUEST"
        elif trigger == "FALLBACK_FAILURE":
            if (type(recovery) is not rv.RecoveryHandoff or recovery.directive.requested_action != "ENTER_CONTAINMENT" or
                    recovery.directive.trigger != trigger or not self._complete(recovery.completion_observation,
                    recovery.operation_context.operation_reference)):
                raise _Refusal("SESSION_EVIDENCE_MISMATCH", "cause", "Fallback containment needs the retained complete matching handoff.")
            kind = "N2_HANDOFF"
        elif trigger == "PROPAGATION_RISK":
            risk = (type(recovery) is rv.RecoveryHandoff and
                recovery.operation_context.propagation_evidence.status == "RISK" and
                recovery.directive.requested_action == "ENTER_CONTAINMENT" and
                recovery.directive.trigger == trigger and
                self._complete(recovery.completion_observation, recovery.operation_context.operation_reference))
            if not risk:
                self._boundary(command, "PROPAGATION_RISK")
            kind = "N2_HANDOFF" if risk else "PROPAGATION_RISK_BOUNDARY"
        elif trigger == "RECOVERY_VALIDATION_FAILURE":
            failed_post = (recovery is not None and any(type(post.assessment) is sv.StateAssessment and
                (post.assessment.system_state_class != "STABLE" or not post.assessment.state_validity_diagnostic.is_valid)
                for post in recovery.post_assessments))
            if not failed_post:
                raise _Refusal("SESSION_EVIDENCE_MISMATCH", "cause", "Recovery validation containment needs an actual retained failed postassessment.")
            if not (type(recovery) is rv.RecoveryHandoff and recovery.directive.trigger == trigger and
                    self._complete(recovery.completion_observation, recovery.operation_context.operation_reference)):
                self._boundary(command, "RECOVERY_VALIDATION_FAILURE")
            kind = "RECOVERY_VALIDATION_BOUNDARY"
        else:
            raise _Refusal("SESSION_INPUT_INVALID", "trigger", "Unknown containment trigger.")
        return self._cause(command, kind, trigger, recovery)

    def _guard_halt(self, command, trigger, recovery=None):
        recovery = self._owned_recovery(getattr(command, "recovery_operation_reference", None)) if recovery is None else recovery
        snapshot = self._snapshot
        if trigger == "CONTAINMENT_BREACH":
            if snapshot.mode != "CONTAINED":
                raise _Refusal("SESSION_MODE_FORBIDDEN", "trigger", "Breach requires actual current containment.")
            self._boundary(command, "CONTAINMENT_BREACH")
            kind = "CONTAINMENT_BREACH"
        elif trigger in ("OPERATOR_HALT_REQUEST", "POLICY_HALT_REQUEST"):
            self._authority(command, "OPERATOR" if trigger == "OPERATOR_HALT_REQUEST" else "POLICY")
            kind = "AUTHORITY_REQUEST"
        elif trigger == "ESCALATION_FROM_FAILED":
            retained = (type(recovery) is rv.RecoveryHandoff and recovery.directive.requested_action == "ENTER_SAFE_HALT" and
                        recovery.directive.trigger == trigger and
                        recovery.operation_context.external_authority_evidence.status == "UNREACHABLE" and
                        self._complete(recovery.completion_observation, recovery.operation_context.operation_reference))
            active_failed = (retained and self._active is not None and self._live(self._active) and
                self._active.recovery is recovery and self._active.origin is recovery.origin_assessment and
                recovery.origin_assessment.system_state_class == "FAILED" and
                self._assessment_valid(recovery.origin_assessment, snapshot))
            failed = snapshot.observed_system_state_class == "FAILED" or active_failed
            authority = getattr(command, "authority_observation", None)
            external = authority is not None and authority.status == "AUTHORIZED"
            if not failed or not (retained or external):
                raise _Refusal("SESSION_EVIDENCE_MISMATCH", "trigger", "Failed halt needs actual failed class and no-path or external halt authority.")
            if external:
                self._authority(command, command.authority_observation.request_origin)
            kind = "N2_HANDOFF" if retained else "AUTHORITY_REQUEST"
        elif trigger == "UNRESOLVABLE_BLOCKED_RECOVERY":
            self._boundary(command, "RECOVERY_NO_PATH")
            self._boundary(command, "CONTAINMENT_UNAVAILABLE")
            kind = "UNRESOLVABLE_BLOCKED_BOUNDARY"
        else:
            raise _Refusal("SESSION_INPUT_INVALID", "trigger", "Unknown halt trigger.")
        return self._cause(command, kind, trigger, recovery)

    def _context(self, request, snapshot):
        return v.SessionContextObservation(request.request_reference + ":context", snapshot,
            request.request_reference, snapshot.current_state, snapshot.mode != "SAFE_HALT",
            snapshot.mode == "CONTAINED", snapshot.mode == "SAFE_HALT")

    def _failure(self, refusal, *, status=None, attempted=None, pending=None):
        return v.SessionFailureDetail(refusal.code, refusal.field, refusal.evidence, status,
            attempted, pending, None, None, refusal.reason)

    def _result(self, op, *, status=None):
        if status is None:
            status = ("UNCONFIRMED" if op.failure is not None and op.effects else
                      "FAILED" if op.failure is not None else "COMPLETED")
        return v.SessionOperationResult(op.command, status, op.lease.before, op.after, op.effects,
            op.admission, op.context, getattr(op.command, "authority_observation", None), op.cause,
            op.origin, op.origin_completion, op.recovery, op.publication, op.confirmed, op.attempted,
            op.pending, op.resolution, op.completion, op.failure, op.post, op.post_completion)

    def _refused_result(self, command, refusal, before):
        request = command.request
        admission = v.SessionAdmission("REJECTED", request, before, None,
            refusal.code, refusal.field, refusal.reason)
        result = v.SessionOperationResult(command, "REFUSED", before, before, False, admission,
            self._context(request, before), getattr(command, "authority_observation", None),
            None, None, None, None, None, (), (), None, None, None,
            self._failure(refusal), None, None)
        returned = result
        if v.raw_business_size(result) > v.MAX_RAW_BUSINESS_BYTES:
            returned = v.SessionRawBusinessFailure(request.request_reference,
                self._binding.session_reference, self._prefix + ":history", "CANDIDATE_RESULT",
                before, before, False, "SESSION_RAW_BUSINESS_LIMIT", "API_ONLY")
        if not refusal.eligible:
            return returned
        with self._lock:
            self._results.append(result)
            self._chronology.append(result)
            self._ledger[request.request_reference] = (command, result)
            handle = self._handle
        receipt = None
        if handle is not None:
            try:
                receipt = (self._diagnostics.observe_session_result(handle, returned, actual_result=result)
                    if type(returned) is v.SessionRawBusinessFailure else
                    self._diagnostics.observe_session_result(handle, result))
            except Exception:
                pass
            receipt = self._retention("FINAL_RESULT", receipt)
        with self._lock:
            self._remember_retention(receipt)
            if not self._snapshot.terminal_latched and (receipt is None or receipt.status != "CONFIRMED"):
                self._snapshot = self._new_snapshot(admission_status="AUDIT_BLOCKED")
            history = self._history_value() if not self._snapshot.terminal_latched else None
        if handle is not None and history is not None:
            try:
                retained = self._retention("PIN", self._diagnostics.pin_history(handle, history))
            except Exception:
                retained = self._retention("PIN", None)
            with self._lock:
                self._remember_retention(retained)
                if not self._snapshot.terminal_latched and retained.status != "CONFIRMED":
                    self._snapshot = self._new_snapshot(admission_status="AUDIT_BLOCKED")
        return returned

    def _denial(self, *, terminal, reference=None, reason="SESSION_TERMINAL"):
        with self._lock:
            snapshot = self._snapshot
            if not terminal:
                self._preterminal_denial_count = min(_MAX_GENERATION, self._preterminal_denial_count + 1)
                return v.SessionDeniedAttempt(self._binding.session_reference, snapshot, None, reference,
                    "VALIDATED_REFERENCE_ONLY", reason, None, None, "NOT_CONFIRMED", None)
            if self._denial_count >= 16:
                self._denial_count = 17
                return v.SessionDeniedAttempt(self._binding.session_reference, snapshot, None,
                    None if terminal else reference, "NOT_INSPECTED_AT_TERMINAL" if terminal else
                    "VALIDATED_REFERENCE_ONLY", reason, None, None, "NOT_CONFIRMED", None)
            self._denial_count += 1
            ordinal = self._denial_count
            audit_reference = self._prefix + ":denial:" + str(ordinal)
            handle = self._handle
        record = sv.DiagnosticEmission(audit_reference, sv.DiagnosticEnvelope("STATE_VALIDITY", "CRITICAL",
            "DETECTION", "BLOCKED", "ash_state_" + snapshot.current_state.signature,
            None, audit_reference, ("ASH-STATE-GENERAL-001", "ASH-RECOVERY-ACTION-001"),
            "Session request denied at an actual owner boundary.",
            ("Caller body was not inspected at the terminal boundary." if terminal else
             "Only the validated request reference is retained.",)))
        scope = None
        if handle is not None:
            try:
                scope = self._diagnostics.denial_capture(handle, snapshot, denial_ordinal=ordinal)
            except Exception:
                pass
        receipt = None
        if scope is not None:
            try:
                receipt = scope.append(record)
            except Exception:
                pass
        capture = (receipt.status if type(receipt) is sv.CaptureReceipt and
                   receipt.diagnostic_reference == record.diagnostic_reference else "NOT_CONFIRMED")
        denial = v.SessionDeniedAttempt(self._binding.session_reference, snapshot, ordinal,
            None if terminal else reference, "NOT_INSPECTED_AT_TERMINAL" if terminal else
            "VALIDATED_REFERENCE_ONLY", reason, audit_reference, record, capture, None)
        completion = None
        if scope is not None:
            try:
                completion = scope.finish(denial)
            except Exception:
                pass
        if type(completion) is v.SessionLifecycleCompletion:
            try:
                v.revalidate_value(completion)
            except v.SessionContractError:
                completion = None
        else:
            completion = None
        final = replace(denial, completion_observation=completion)
        if handle is not None:
            try:
                self._diagnostics.observe_session_denial(handle, final)
            except Exception:
                pass
        return final

    def _admit(self, command):
        request = command.request
        before = self._snapshot
        if request.session_reference != self._binding.session_reference:
            raise _Refusal("SESSION_ORIGIN_FOREIGN", "request.session_reference", "Request names a foreign session.")
        self._source(self._binding)
        action = request.action
        is_halt = action == "REQUEST_HALT" or (type(command) is v.SessionResolutionRequest and
                                                command.resolution_action == "HALT")
        if (action == "RECOVER" and before.mode != "NORMAL" or
                action == "REQUEST_CONTAINMENT" and before.mode != "NORMAL" or
                action == "RESOLVE_CONTAINMENT" and before.mode != "CONTAINED"):
            raise _Refusal("SESSION_MODE_FORBIDDEN", "request.action", "Actual mode forbids this operation.")
        previous = self._ledger.get(request.request_reference)
        if previous is not None:
            old_command, result = previous
            if old_command != command:
                raise _Refusal("SESSION_OPERATION_DUPLICATE", "request.reference", "Request reference has another bounded command.")
            if result is None:
                raise _Refusal("SESSION_OPERATION_IN_PROGRESS", "request.reference", "This exact request is still finalizing.")
            return v.SessionReplayObservation(request.request_reference, result, before, False)
        if not is_halt and self._lease is not None:
            raise _Refusal("SESSION_OPERATION_IN_PROGRESS", "lease", "Another ordinary lease remains exclusive.")
        if ((action == "RECOVER" and self._recover_count >= 2) or
                (action != "RECOVER" and not is_halt and self._mode_count >= 15) or
                (not is_halt and len(self._ledger) >= 17) or (is_halt and len(self._ledger) >= 18)):
            raise _Refusal("SESSION_BUDGET_EXCEEDED", "request", "Declared command capacity is exhausted.")
        if not is_halt:
            if action == "RECOVER":
                self._recover_count += 1
            else:
                self._mode_count += 1
            self._ledger[request.request_reference] = (command, None)
        try:
            return self._admit_eligible(command, before, is_halt)
        except _Refusal as refusal:
            if is_halt:
                # Rejected halt commands spend an ordinary mode slot. A later
                # actual justified first halt still owns the terminal reserve.
                if self._mode_count >= 15 or len(self._ledger) >= 17:
                    raise _Refusal("SESSION_BUDGET_EXCEEDED", "request",
                        "Ordinary refusal capacity is exhausted; first halt remains reserved.") from None
                self._mode_count += 1
                self._ledger[request.request_reference] = (command, None)
            refusal.eligible = True
            raise

    def _admit_eligible(self, command, before, is_halt):
        request, action = command.request, command.request.action
        if request.expected_snapshot != before:
            raise _Refusal("SESSION_STATE_STALE", "request.expected_snapshot", "Full expected snapshot is not current.")
        if not is_halt and before.admission_status != "OPEN":
            raise _Refusal("SESSION_AUDIT_BLOCKED", "capture", "Current mode has no complete actual observation boundary.")
        if not is_halt and before.generation >= _MAX_GENERATION - 1:
            raise _Refusal("SESSION_GENERATION_EXHAUSTED", "generation", "The final generation is reserved for first halt.")
        if type(command) is v.SessionRecoveryRequest:
            if (command.origin_assessment is not self._accepted or self._accepted_generation != before.generation or
                    not self._assessment_valid(command.origin_assessment, before)):
                raise _Refusal("SESSION_ORIGIN_FOREIGN", "origin_assessment", "Recovery origin is not this generation's actual accepted assessment.")
            context = command.operation_context
            if (context.operation_reference != request.request_reference or
                    context.origin_assessment_reference != request.request_reference + ":origin:assessment" or
                    context.context_observation.context != sv.SystemContext(False, False)):
                raise _Refusal("SESSION_EVIDENCE_MISMATCH", "operation_context", "Fresh origin context is not already bound to this command.")
        cause = None
        if type(command) is v.SessionContainmentRequest:
            cause = self._guard_containment(command, command.trigger)
        elif type(command) is v.SessionHaltRequest:
            cause = self._guard_halt(command, command.trigger)
        elif type(command) is v.SessionResolutionRequest:
            if is_halt:
                if command.route != "ESCALATE_TO_SAFE_HALT" or command.target_state is not None:
                    raise _Refusal("SESSION_INPUT_INVALID", "resolution.route", "Halt resolution has an inconsistent target/route.")
                origin = command.authority_observation.request_origin
                if origin not in ("OPERATOR", "POLICY"):
                    raise _Refusal("SESSION_AUTHORITY_DENIED", "authority", "Resolution halt requires operator or policy authority.")
                cause = self._guard_halt(command, "OPERATOR_HALT_REQUEST" if origin == "OPERATOR" else "POLICY_HALT_REQUEST")
            else:
                origin = "OPERATOR" if command.route == "OPERATOR_INTERVENTION" else "POLICY" if command.route == "POLICY_DRIVEN" else None
                if origin is None or command.resolution_action != "REPLACE_STATE" or type(command.target_state) is not sv.AshState:
                    raise _Refusal("SESSION_INPUT_INVALID", "resolution.route", "Replacement resolution has an inconsistent route/action/target.")
                self._authority(command, origin)
                self._boundary(command, "CONTAINMENT_CLEAR")
                evidence = command.propagation_evidence
                if (evidence is None or evidence.status != "SAFE" or
                        evidence.operation_reference != request.request_reference or
                        evidence.origin_assessment_reference != before.current_assessment_reference):
                    raise _Refusal("SESSION_EVIDENCE_MISMATCH", "operation_context.propagation_evidence", "Resolution requires current bound SAFE propagation.")
        active = self._new_snapshot(active_operation_reference=request.request_reference)
        lease = v.SessionOperationLease(request.request_reference + ":lease", request, before,
            "HALT" if is_halt else {"RECOVER": "RECOVER", "REQUEST_CONTAINMENT": "CONTAIN", "RESOLVE_CONTAINMENT": "RESOLVE"}[action], active)
        gate = self._gate(lease)
        admission = v.SessionAdmission("GRANTED", request, before, lease, None, None,
                                       "Exact current owner phase granted this issued lease.")
        op = _Operation(command, lease, gate, admission, self._context(request, before),
                        origin=self._accepted, cause=cause,
                        interrupted=self._active if is_halt else None)
        self._snapshot, self._phase_snapshot = active, active
        self._lease, self._active = lease, op
        self._ledger[request.request_reference] = (command, None)
        return op

    def _execute(self, engine, session, command):
        self._identity(engine, session)
        with self._lock:
            terminal = self._snapshot.terminal_latched
        if terminal:
            return self._denial(terminal=True)
        if not any(type(command) is kind for kind in _COMMANDS):
            raise v.SessionContractError("SESSION_INPUT_INVALID", "request")
        v.revalidate_value(command)
        with self._lock:
            if self._snapshot.terminal_latched:
                terminal = True
                op = None
            else:
                terminal = False
                try:
                    op = self._admit(command)
                except _Refusal as refusal:
                    op, refusal_before = refusal, self._snapshot
        if terminal:
            return self._denial(terminal=True)
        if type(op) is _Refusal:
            if op.code in ("SESSION_MODE_FORBIDDEN", "SESSION_BUDGET_EXCEEDED"):
                return self._denial(terminal=False, reference=command.request.request_reference, reason=op.code)
            return self._refused_result(command, op, refusal_before)
        if type(op) is v.SessionReplayObservation:
            return op
        try:
            if type(command) is v.SessionRecoveryRequest:
                self._recover(op)
            elif type(command) is v.SessionContainmentRequest:
                self._contain(op, command.trigger)
            elif type(command) is v.SessionHaltRequest or command.resolution_action == "HALT":
                self._halt(op, op.cause.trigger)
            else:
                self._resolve(op)
        except _Refusal as refusal:
            op.failure = self._failure(refusal, pending=op.pending,
                attempted=op.attempted[-1] if op.attempted else None)
        except v.SessionContractError as error:
            op.failure = self._failure(_Refusal(error.failure_code, error.field_name,
                "An exact controlled session boundary refused this operation."), pending=op.pending)
        except (sv.StateContractError, rv.RecoveryContractError, dv.DiagnosticsContractError):
            op.failure = self._failure(_Refusal("SESSION_INTERNAL_INVARIANT", "collaborator",
                "A closed internal value boundary rejected this operation."), pending=op.pending)
        except Exception:
            op.failure = self._failure(_Refusal("SESSION_COLLABORATOR_FAILED", "collaborator",
                "An actual collaborator did not return the required bounded observation."), pending=op.pending)
        return self._finalize(op)

    def _begin_scope(self, op, *, terminal=False):
        if not terminal:
            self._require_live(op)
            if op.gate.stage_grant("CAPTURE_BEGIN").status != "GRANTED":
                raise _Refusal("SESSION_EXECUTION_CANCELLED", "execution_gate", "Lifecycle capture grant was revoked.")
        with self._lock:
            handle = self._handle
            refs = tuple(dict.fromkeys((self._initial.assessment_binding.assessment_reference,
                self._main_root, self._main_previous)))
        returned = None
        if handle is not None:
            try:
                returned = self._diagnostics.lifecycle_capture(handle, execution_gate=op.gate).begin(
                    op.command, before=op.lease.before, origin_refs=refs, terminal=terminal)
            except Exception:
                pass
        scope = admission = None
        if type(returned) is tuple and len(returned) == 2:
            scope, admission = returned
        valid = type(admission) is v.SessionLifecycleCaptureAdmission
        if valid:
            try:
                v.revalidate_value(admission)
            except v.SessionContractError:
                valid = False
        if valid and admission.operation_reference == op.command.request.request_reference and scope is not None:
            # The exact collector may have allocated an actual scope before its
            # reservation acknowledgment fails. Preserve that scope for its
            # single cleanup finish without granting capture or publication.
            op.scope = scope
        if (not valid or admission.operation_reference != op.command.request.request_reference or
                admission.status != "CONFIRMED" or scope is None or admission.reserved_events != 4 or
                admission.reserved_bytes != (655360 if terminal else 327680) or
                admission.reserved_aliases != 512 or
                admission.reserved_supporting_bytes != (425984 if terminal else 98304)):
            raise _Refusal("SESSION_CAPTURE_FAILED", "capture.admission", "Actual fixed lifecycle reservation was not confirmed.")
        if not terminal:
            self._require_live(op)

    def _clock(self, op):
        observed = None
        if op.scope is not None:
            try:
                observed = op.scope.observe_clock()
            except Exception:
                pass
        if type(observed) is dv.ClockObservation:
            try:
                observed.__post_init__()
            except dv.DiagnosticsContractError:
                observed = None
        if type(observed) is not dv.ClockObservation or observed.monotonic_nanoseconds is None:
            return None
        if not op.terminal:
            self._require_live(op)
        return observed

    def _pending_record(self, op, kind, trigger, fields, reason):
        return v.PendingLifecycleRecord(op.command.request.request_reference +
            (":containment" if kind == "CONTAINMENT" else ":halt"), kind, trigger,
            self._phase_origin, op.lease.before, op.after, op.cause, fields, reason)

    def _bridge(self, op, outcome, *, terminal=False):
        request = op.command.request
        with self._lock:
            origin, previous, root, severity = self._phase_origin, self._main_previous, self._main_root, self._severity
        payload = rv.RecoveryDiagnostic(origin.recovery_category, origin.system_state_class,
            origin.state_validity_diagnostic, (), outcome,
            op.publication.after.current_state if outcome in ("RECOVERED", "RECOVERED_VIA_FALLBACK") else None,
            next((decision.diagnostic.fallback_policy_id for decision in op.recovery.action_decisions
                  if decision.diagnostic.outcome == "RECOVERED_VIA_FALLBACK"), None)
                if outcome == "RECOVERED_VIA_FALLBACK" else None,
            "The actual session owner made this bounded lifecycle decision.",
            ("ASH-STATE-GENERAL-001", "ASH-RECOVERY-ACTION-001") if outcome in ("BLOCKED", "ESCALATE_TO_CONTAINMENT", "NOT_APPLICABLE") else
            ("ASH-STATE-VALIDITY-001", "ASH-RECOVERY-ACTION-001", "ASH-FALLBACK-SELECTION-001") if outcome == "RECOVERED_VIA_FALLBACK" else
            ("ASH-STATE-STRUCTURE-001", "ASH-ADMISSIBILITY-CLASSIFICATION-001", "ASH-STATE-VALIDITY-001", "ASH-CODEWORD-STRUCTURE-001", "ASH-RECOVERY-ACTION-001"))
        reference = request.request_reference + ":bridge"
        envelope = sv.DiagnosticEnvelope("RECOVERY", "CRITICAL" if terminal else severity, "RECOVERY",
            "BLOCKED" if outcome == "BLOCKED" else "ESCALATED" if outcome == "ESCALATE_TO_CONTAINMENT" else "RESOLVED",
            origin.subject_reference, previous, root, payload.rule_ids,
            "Actual session lifecycle bridge.", ("No correction steps are claimed by this bridge.",))
        return v.LifecycleRecord(reference, envelope, payload, op.cause)

    def _append(self, op, record):
        if not op.terminal:
            self._require_live(op)
        with self._lock:
            op.attempted += (record,)
        receipt = None
        try:
            receipt = op.scope.append(record)
        except Exception:
            pass
        valid = type(receipt) is sv.CaptureReceipt
        if valid:
            try:
                receipt.__post_init__()
            except sv.StateContractError:
                valid = False
        status = receipt.status if valid and receipt.diagnostic_reference == record.diagnostic_reference else "NOT_CONFIRMED"
        if status != "CONFIRMED":
            raise _Refusal("SESSION_CAPTURE_FAILED", "capture.append", "Actual lifecycle append was not confirmed.")
        with self._lock:
            allowed = (op.terminal and self._terminal_reference == op.command.request.request_reference) or self._live(op)
            if not allowed:
                raise _Refusal("SESSION_EXECUTION_CANCELLED", "execution_gate", "Append returned after the owner sealed this phase.")
            op.confirmed += (record,)
            self._main_previous = record.diagnostic_reference
            self._severity = max((self._severity, record.envelope.severity), key=_SEVERITIES.index)

    def _publication(self, op, state, mode, cause, *, proof=None, terminal=False):
        with self._lock:
            if not terminal:
                if not self._live(op):
                    raise _Refusal("SESSION_PUBLICATION_STALE", "publication.before", "Issued phase changed before publication.")
                self._source(self._binding)
                if self._snapshot.generation >= _MAX_GENERATION - 1:
                    raise _Refusal("SESSION_GENERATION_EXHAUSTED", "generation", "Last generation is reserved for halt.")
            generation = self._snapshot.generation + 1
            if generation > _MAX_GENERATION:
                raise _Refusal("SESSION_GENERATION_EXHAUSTED", "generation", "Generation cannot wrap.")
            reference = op.command.request.request_reference
            after = self._new_snapshot(generation=generation, current_state=state, mode=mode,
                terminal_latched=terminal, admission_status="TERMINAL" if terminal else "AUDIT_BLOCKED",
                containment_reference=reference + ":containment" if mode == "CONTAINED" else None,
                halt_reference=reference + ":halt" if terminal else None,
                recovery_attempted=self._snapshot.recovery_attempted or type(op.command) is v.SessionRecoveryRequest,
                active_operation_reference=None if terminal else reference,
                current_assessment_reference=None, observed_system_state_class=None)
            publication = v.SessionPublication(reference + ":publication", reference, op.lease.lease_reference,
                op.lease.before, after, "COMMITTED", True, state, mode, cause.cause_reference, proof, None,
                "The exact owner phase atomically committed this state/mode publication.")
            self._snapshot = self._phase_snapshot = after
            self._accepted = self._accepted_generation = None
            op.publication, op.effects, op.after = publication, True, after
            return publication

    def _mode_assessment_sizing_record(self, op):
        """Private pure-model specimen, never a captured session assessment."""
        from .state_model import RecordingDiagnosticCapture
        command = op.command
        contained = type(command) is v.SessionContainmentRequest or (
            type(op.recovery) is rv.RecoveryHandoff and op.recovery.directive.requested_action == "ENTER_CONTAINMENT")
        state = (command.target_state if type(command) is v.SessionResolutionRequest else
                 op.recovery.candidate_state if any(type(op.recovery) is kind for kind in (rv.RecoveredValue, rv.RecoveredFallbackValue))
                 else op.lease.before.current_state)
        reference = command.request.request_reference + ":mode:assessment"
        context = sv.DiagnosticContext(reference, command.request.request_reference + ":mode:input",
            command.request.request_reference + ":mode:detection", command.request.request_reference + ":mode:classification")
        predicates = tuple(sv.NotEvaluatedPredicate(sv.PredicateBinding(reference, context.detection_reference,
            "ash_state_" + state.signature, self._model.profile_binding.profile_id,
            self._model.profile_binding.source_binding.source_sha256, self._model.canonical_binding.dependency_id,
            self._model.canonical_binding.aggregate_sha256, reference + ":" + name), _SIZING_TEXT)
            for name in sv.PREDICATE_NAMES)
        private_model = StateModel(self._model.profile_binding, self._model.canonical_binding,
                                   RecordingDiagnosticCapture())
        specimen = private_model.assess(state, context=sv.SystemContext(False, contained),
            classification_evidence=sv.ClassificationEvidence(*predicates), diagnostic_context=context)
        record = v.raw_business_record(specimen)
        upper = _sizing_upper(record)
        # These fixed bindings/profile are already actual and immutable. Keep
        # their exact bytes rather than inflating their closed finite tree.
        upper["source_binding"], upper["profile_binding"] = record["source_binding"], record["profile_binding"]
        for emission in upper["emitted_diagnostics"]:
            emission["envelope"]["notes"] = [_SIZING_TEXT] * 8
            emission["envelope"]["rule_ids"] = [_SIZING_TEXT] * 5
        upper["state_validity_diagnostic"]["notes"] = [_SIZING_TEXT] * 8
        upper["state_validity_diagnostic"]["rule_ids"] = [_SIZING_TEXT] * 5
        # A failed capture has additional fields and one attempted emission.
        # Including those fields with the complete shape dominates both unions.
        upper.update(failure_kind=_SIZING_TEXT, failure_code=_SIZING_TEXT,
                     capture_status=_SIZING_TEXT, attempted_diagnostic=upper["emitted_diagnostics"][-1])
        return upper

    @staticmethod
    def _completion_sizing_record():
        return dict(operation_reference=_SIZING_REFERENCE, status=_SIZING_TEXT,
            confirmed_references=[_SIZING_REFERENCE] * 4, failure_code=_SIZING_TEXT)

    def _prospective_result_record(self, op, result):
        """Bound unobserved finish/post-mode fields, retaining actual large DAGs."""
        record = v.raw_business_record(result)
        before = record["before"]
        after = dict(record["after"] or before)
        after.update(snapshot_reference=_SIZING_REFERENCE, generation=_MAX_GENERATION,
            current_assessment_reference=_SIZING_REFERENCE, observed_system_state_class=_SIZING_TEXT,
            active_operation_reference=_SIZING_REFERENCE, admission_status=_SIZING_TEXT)
        record["after"] = after
        cause = record["cause"]
        if record["publication"] is None and cause is not None:
            record["publication"] = dict(publication_reference=_SIZING_REFERENCE,
                request_reference=_SIZING_REFERENCE, lease_reference=_SIZING_REFERENCE, before=before, after=after,
                status=_SIZING_TEXT, session_effects_performed=True, requested_state=before["current_state"],
                requested_mode=_SIZING_TEXT, cause_reference=_SIZING_REFERENCE,
                proof_reference=_SIZING_REFERENCE, failure_code=_SIZING_TEXT, reason=_SIZING_TEXT)
        planned = list(record["attempted_lifecycle_records"])
        if not planned and type(op.command) is not v.SessionResolutionRequest:
            bridge = _sizing_upper(v.raw_business_record(self._bridge(op, "NOT_APPLICABLE")))
            bridge["envelope"]["notes"] = [_SIZING_TEXT] * 8
            bridge["envelope"]["rule_ids"] = [_SIZING_TEXT] * 5
            bridge["payload"]["corrected_state"] = before["current_state"]
            bridge["payload"]["fallback_policy_id"] = _SIZING_REFERENCE
            planned = [bridge]
        record["attempted_lifecycle_records"] = record["confirmed_lifecycle_records"] = planned
        post = record["actual_post_assessment"] or self._mode_assessment_sizing_record(op)
        record["actual_post_assessment"] = post
        record["actual_post_completion_observation"] = _assessment_completion_sizing_record()
        if record["resolution_observation"] is not None:
            resolution = dict(record["resolution_observation"])
            resolution.update(publication=record["publication"], actual_post_assessment=post,
                status=_SIZING_TEXT, reason=_SIZING_TEXT)
            record["resolution_observation"] = resolution
        completion = self._completion_sizing_record()
        record["completion_observation"] = completion
        pending = dict(intended_reference=_SIZING_REFERENCE, kind=_SIZING_TEXT, trigger=_SIZING_TEXT,
            original_assessment=v.raw_business_record(self._phase_origin), before=before, actual_after=after,
            cause=cause, missing_fields=[_SIZING_TEXT] * 15, reason_code=_SIZING_TEXT)
        record["pending_lifecycle_record"] = pending
        evidence = record["recovery_result"] or record["publication"]
        record["failure_detail"] = dict(failure_code=_SIZING_TEXT, field_name=_SIZING_TEXT,
            primary_evidence=evidence, capture_status=_SIZING_TEXT,
            attempted_lifecycle_record=planned[-1] if planned else None, pending_lifecycle_record=pending,
            completion_failure_code=_SIZING_TEXT, unconfirmed_completion_observation=completion,
            reason=_SIZING_TEXT)
        return record

    def _anticipated_terminal_record(self, history, trace, current):
        """Full structural first-halt upper, including every repeated trace slot."""
        before = dict(current["after"])
        terminal = dict(before, mode="SAFE_HALT", terminal_latched=True, admission_status="TERMINAL",
            current_assessment_reference=None, observed_system_state_class=None,
            containment_reference=None, halt_reference=_SIZING_REFERENCE, active_operation_reference=None)
        request = dict(request_reference=_SIZING_REFERENCE, session_reference=self._binding.session_reference,
            expected_snapshot=before, action=_SIZING_TEXT, reason=_SIZING_TEXT)
        source = dict(source_reference=_SIZING_REFERENCE, source_sha256="f" * 64,
                      evidence_reference=_SIZING_REFERENCE)
        authority = dict(request_reference=_SIZING_REFERENCE, expected_snapshot_reference=_SIZING_REFERENCE,
            status=_SIZING_TEXT, request_origin=_SIZING_TEXT, source_binding=source,
            observation_reference=_SIZING_REFERENCE, reason=_SIZING_TEXT)
        boundary = dict(request_reference=_SIZING_REFERENCE, expected_snapshot_reference=_SIZING_REFERENCE,
            condition=_SIZING_TEXT, status=_SIZING_TEXT, source_binding=source,
            observation_reference=_SIZING_REFERENCE, reason=_SIZING_TEXT)
        command = dict(request=request, trigger=_SIZING_TEXT, authority_observation=authority,
                       boundary_observations=[boundary] * 6, recovery_operation_reference=_SIZING_REFERENCE)
        cause = dict(cause_reference=_SIZING_REFERENCE, kind=_SIZING_TEXT, trigger=_SIZING_TEXT,
            request_reference=_SIZING_REFERENCE, expected_snapshot_reference=_SIZING_REFERENCE,
            recovery_operation_reference=_SIZING_REFERENCE, authority_observation=authority,
            boundary_observations=[boundary] * 6)
        publication = dict(publication_reference=_SIZING_REFERENCE, request_reference=_SIZING_REFERENCE,
            lease_reference=_SIZING_REFERENCE, before=before, after=terminal, status=_SIZING_TEXT,
            session_effects_performed=True, requested_state=before["current_state"], requested_mode=_SIZING_TEXT,
            cause_reference=_SIZING_REFERENCE, proof_reference=_SIZING_REFERENCE,
            failure_code=_SIZING_TEXT, reason=_SIZING_TEXT)
        envelope = {field.name: _SIZING_TEXT for field in fields(sv.DiagnosticEnvelope)}
        envelope.update(rule_ids=[_SIZING_TEXT] * 5, notes=[_SIZING_TEXT] * 8)
        original = current["actual_post_assessment"] or v.raw_business_record(self._phase_origin)
        bridge = dict(diagnostic_reference=_SIZING_REFERENCE, envelope=envelope, cause=cause,
            payload=dict(recovery_category=_SIZING_TEXT, original_state_class=_SIZING_TEXT,
                original_diagnostic=original["state_validity_diagnostic"], steps=[], outcome=_SIZING_TEXT,
                corrected_state=before["current_state"], fallback_policy_id=_SIZING_REFERENCE,
                reason=_SIZING_TEXT, rule_ids=[_SIZING_TEXT] * 5))
        closure = dict(request_reference=_SIZING_REFERENCE, bridge_record=bridge,
            terminal_emission=dict(diagnostic_reference=_SIZING_REFERENCE, envelope=envelope),
            actual_terminal_publication=publication)
        halt = dict(diagnostic_reference=_SIZING_REFERENCE, envelope=envelope, cause=cause,
            payload=dict(trigger=_SIZING_TEXT, original_diagnostic=original["state_validity_diagnostic"],
                system_state_class=_SIZING_TEXT, halt_time=dict(observed_utc="9999-12-31T23:59:59.999999Z",
                    monotonic_nanoseconds=_MAX_GENERATION, utc_reason=_SIZING_TEXT, monotonic_reason=_SIZING_TEXT),
                full_diagnostic_chain=trace + [closure], is_terminal=True,
                rule_ids=[_SIZING_TEXT], notes=[_SIZING_TEXT] * 8))
        records = [bridge, halt]
        completion = self._completion_sizing_record()
        pending = dict(intended_reference=_SIZING_REFERENCE, kind=_SIZING_TEXT, trigger=_SIZING_TEXT,
            original_assessment=original, before=before, actual_after=terminal, cause=cause,
            missing_fields=[_SIZING_TEXT] * 15, reason_code=_SIZING_TEXT)
        result = {field.name: None for field in fields(v.SessionOperationResult)}
        result.update(request=command, status=_SIZING_TEXT, before=before, after=terminal,
            session_effects_performed=True, admission=dict(status=_SIZING_TEXT, request=request, before=before,
                lease=dict(lease_reference=_SIZING_REFERENCE, request=request, before=before,
                    action=_SIZING_TEXT, active_snapshot=before), failure_code=_SIZING_TEXT,
                field_name=_SIZING_TEXT, reason=_SIZING_TEXT),
            context_observation=dict(observation_reference=_SIZING_REFERENCE, snapshot=before,
                operation_reference=_SIZING_REFERENCE, subject_state=before["current_state"],
                is_running=False, is_contained=False, is_halted=False),
            authority_observation=authority, cause=cause, origin_assessment=original,
            publication=publication, confirmed_lifecycle_records=records, attempted_lifecycle_records=records,
            pending_lifecycle_record=pending, completion_observation=completion,
            failure_detail=dict(failure_code=_SIZING_TEXT, field_name=_SIZING_TEXT,
                primary_evidence=publication, capture_status=_SIZING_TEXT, attempted_lifecycle_record=halt,
                pending_lifecycle_record=pending, completion_failure_code=_SIZING_TEXT,
                unconfirmed_completion_observation=completion, reason=_SIZING_TEXT))
        final = dict(history)
        final["command_results"] = history["command_results"] + [result]
        final["confirmed_lifecycle_records"] = history["confirmed_lifecycle_records"] + records
        final["attempted_lifecycle_records"] = history["attempted_lifecycle_records"] + records
        final["pending_lifecycle_records"] = history["pending_lifecycle_records"] + [pending]
        final.update(terminal_snapshot=terminal, frozen=True)
        return final

    def _raw_preflight(self, op, *, candidate=None):
        result = self._result(op) if candidate is None else candidate
        limit = v.MAX_RAW_BUSINESS_BYTES
        def refuse(phase, field, reason):
            op.raw_phase = phase
            raise _Refusal("SESSION_RAW_BUSINESS_LIMIT", field, reason)
        if v.raw_business_size(result) > limit:
            refuse("CANDIDATE_RESULT", "raw_business_packet", "Candidate raw business packet exceeds its fixed limit.")
        upper = self._prospective_result_record(op, result)
        if _sizing_size(upper, limit) > limit:
            refuse("CANDIDATE_RESULT", "raw_business_packet", "Candidate plus bounded future observations exceeds its fixed limit.")
        with self._lock:
            history = self._history_value(extra=result)
            trace_values = (self._initial,) + tuple(self._chronology)
        if v.raw_business_size(history) > limit:
            refuse("PROSPECTIVE_HISTORY", "history", "Prospective complete history exceeds its fixed raw limit.")
        history_record = v.raw_business_record(history)
        history_record["command_results"][-1] = upper
        history_record["confirmed_lifecycle_records"] += upper["confirmed_lifecycle_records"]
        history_record["attempted_lifecycle_records"] += upper["attempted_lifecycle_records"]
        history_record["pending_lifecycle_records"] += [upper["pending_lifecycle_record"]]
        if upper["resolution_observation"] is not None:
            history_record["resolution_observations"] += [upper["resolution_observation"]]
        if _sizing_size(history_record, limit) > limit:
            refuse("PROSPECTIVE_HISTORY", "history", "History plus bounded final observations exceeds its fixed limit.")
        trace = [v.raw_business_record(item) for item in trace_values] + [upper]
        anticipated = self._anticipated_terminal_record(history_record, trace, upper)
        if _sizing_size(anticipated, limit) > limit:
            refuse("ANTICIPATED_TERMINAL", "history", "Full repeated terminal closure cannot fit the raw limit.")

    def _post_mode(self, op, *, stable):
        self._require_live(op)
        request = op.command.request
        diagnostic_context = sv.DiagnosticContext(request.request_reference + ":mode:assessment",
            request.request_reference + ":mode:input", request.request_reference + ":mode:detection",
            request.request_reference + ":mode:classification")
        with self._lock:
            snapshot = self._snapshot
        relation = v.SessionAssessmentLink(self._binding.session_reference, request.request_reference,
            request.request_reference + ":resolution" if stable else None, self._main_root)
        capture = op.scope.assessment_capture(relation)
        returned = self._services.assess_mode(self._phase_origin, actual_snapshot=snapshot,
            diagnostic_context=diagnostic_context, capture=capture, execution_gate=op.gate)
        if type(returned) is tuple and len(returned) == 2:
            op.post, op.post_completion = returned
        self._require_live(op)
        if (not self._assessment_valid(op.post, snapshot, stable=stable) or
                not self._complete(op.post_completion, diagnostic_context.assessment_reference)):
            raise _Refusal("SESSION_CAPTURE_FAILED", "capture", "Actual committed mode assessment or its first completion is incomplete.")

    def _contain(self, op, trigger):
        self._require_live(op)
        if op.cause is None:
            with self._lock:
                op.cause = self._guard_containment(op.command, trigger, op.recovery)
        self._begin_scope(op)
        clock = self._clock(op)
        if clock is None:
            op.pending = self._pending_record(op, "CONTAINMENT", trigger, ("containment_time",), "CLOCK_UNAVAILABLE")
            raise _Refusal("SESSION_CAPTURE_FAILED", "clock", "No measured clock supports canonical containment.")
        bridge = self._bridge(op, "ESCALATE_TO_CONTAINMENT")
        payload = v.ContainmentDiagnostic(trigger, self._phase_origin.state_validity_diagnostic, "CONTAINED",
            _RESTRICTED, clock, True, "PENDING", (_CONTAINMENT_RULES[trigger],),
            ("The session owner entered containment through an actual guarded decision.",))
        record = v.LifecycleRecord(op.command.request.request_reference + ":containment",
            sv.DiagnosticEnvelope("CONTAINMENT", self._severity, "ESCALATION", "ESCALATED",
                self._phase_origin.subject_reference, bridge.diagnostic_reference, self._main_root,
                payload.rule_ids, "Actual session containment entry.", payload.notes), payload, op.cause)
        # The candidate group includes both exact intended canonical records before CAS.
        probe = replace(self._result(op), attempted_lifecycle_records=(bridge, record))
        self._raw_preflight(op, candidate=probe)
        self._append(op, bridge)
        self._publication(op, self._snapshot.current_state, "CONTAINED", op.cause)
        self._append(op, record)
        self._post_mode(op, stable=False)

    def _resolve(self, op):
        command = op.command
        target = self._model.validate_resolution_target(command.target_state,
                                                       prospective_context=sv.SystemContext(False, False))
        if target.status != "VERIFIED":
            raise _Refusal("SESSION_TARGET_NOT_VALID", "resolution.target_validation", "Current pure target mathematics rejected replacement.", target)
        op.cause = self._cause(command, "AUTHORITY_REQUEST", "OPERATOR_REQUEST")
        self._begin_scope(op)
        clear = self._boundary(command, "CONTAINMENT_CLEAR")
        observation = v.SessionResolutionObservation(command.request.request_reference + ":resolution",
            command.request, command.route, op.lease.before.containment_reference, target,
            command.authority_observation, clear, command.propagation_evidence, None, None, "UNCONFIRMED", False,
            "Current target/authority evidence was validated before owner publication.")
        op.resolution = observation
        self._raw_preflight(op)
        self._require_live(op)
        with self._lock:
            self._authority(command, command.authority_observation.request_origin)
            self._boundary(command, "CONTAINMENT_CLEAR")
            if self._snapshot.containment_reference != op.lease.before.containment_reference:
                raise _Refusal("SESSION_PUBLICATION_STALE", "resolution", "Actual containment identity changed.")
            if self._model.validate_resolution_target(command.target_state,
                    prospective_context=sv.SystemContext(False, False)) != target:
                raise _Refusal("SESSION_TARGET_NOT_VALID", "resolution.target_validation", "Target proof changed before CAS.", target)
            self._publication(op, command.target_state, "NORMAL", op.cause,
                              proof=observation.resolution_reference)
        self._post_mode(op, stable=True)
        op.resolution = replace(observation, publication=op.publication, actual_post_assessment=op.post,
            status="RESOLVED", session_effects_performed=True,
            reason="Actual authorized target publication and actual clear-context assessment occurred.")
        self._require_live(op)
        receipt = op.scope.append_resolution(op.resolution)
        self._require_live(op)
        if type(receipt) is not sv.CaptureReceipt or receipt.status != "CONFIRMED":
            raise _Refusal("SESSION_CAPTURE_FAILED", "capture.append", "Actual resolution control was not confirmed.")

    def _recover(self, op):
        request = op.command.request
        context = sv.DiagnosticContext(request.request_reference + ":origin:assessment",
            request.request_reference + ":origin:input", request.request_reference + ":origin:detection",
            request.request_reference + ":origin:classification")
        live_origin, op.origin = op.origin, None
        returned = self._services.assess_origin(live_origin, diagnostic_context=context,
            operation_context=op.command.operation_context, execution_gate=op.gate)
        if type(returned) is tuple and len(returned) == 2:
            child, op.origin_completion = returned
            if type(child) is rv.UnavailablePostAssessmentFacts:
                op.origin = None
                raise _Refusal("SESSION_ORIGIN_REJECTED", "origin_assessment",
                    "The actual fresh-origin provider returned unavailable facts.", child)
            op.origin = child
        self._require_live(op)
        if any(type(op.origin) is kind for kind in (sv.StateAssessment, sv.ClassificationEvidenceFailure, sv.DiagnosticCaptureFailure)):
            link = self._child_link(self._services, op.gate)
            try:
                attached = self._diagnostics.attach_result(self._handle, op.origin, relation=link)
            except Exception:
                attached = None
            attached = self._retention("ATTACH", attached)
            self._require_live(op)
            with self._lock:
                self._children.append(link)
                self._remember_retention(attached)
        else:
            attached = None
        if (not self._assessment_valid(op.origin, self._snapshot) or
                op.origin.assessment_binding.assessment_reference != context.assessment_reference or
                not self._complete(op.origin_completion, context.assessment_reference)):
            raise _Refusal("SESSION_ORIGIN_REJECTED", "origin_assessment", "Actual fresh origin assessment/completion was not confirmed.")
        if attached is None or attached.status != "CONFIRMED":
            raise _Refusal("SESSION_RETENTION_FAILED", "retention", "Actual fresh child association was not confirmed.", attached)
        op.recovery = self._services.recover(op.origin, operation_context=op.command.operation_context,
                                             execution_gate=op.gate)
        if not any(type(op.recovery) is kind for kind in _PACKETS):
            op.recovery = None
            raise _Refusal("SESSION_N2_RESULT_REJECTED", "collaborator", "N2 returned no exact owned packet.")
        op.recovery.__post_init__()
        with self._lock:
            if self._live(op):
                self._recoveries.append(op.recovery)
                self._chronology.append(op.recovery)
        self._require_live(op)
        actual = op.recovery
        if (actual.origin_assessment is not op.origin or actual.source_binding != self._binding.recovery_binding or
                actual.operation_context != op.command.operation_context):
            raise _Refusal("SESSION_N2_RESULT_REJECTED", "cause", "N2 packet is not the actual bound command result.", actual)
        if not self._complete(actual.completion_observation, request.request_reference):
            raise _Refusal("SESSION_N2_COMPLETION_UNCONFIRMED", "capture.finish", "Actual first N2 completion does not confirm this packet.", actual)
        retained = self._retention("ATTACH", self._diagnostics.attach_result(self._handle, actual))
        self._require_live(op)
        if retained.status != "CONFIRMED":
            raise _Refusal("SESSION_RETENTION_FAILED", "retention", "Actual N2 packet retention was not confirmed.", retained)
        if type(actual) is rv.RecoveryHandoff:
            if actual.directive.requested_action == "ENTER_CONTAINMENT":
                with self._lock:
                    op.cause = self._guard_containment(op.command, actual.directive.trigger, actual)
                self._contain(op, actual.directive.trigger)
            elif actual.directive.requested_action == "ENTER_SAFE_HALT":
                with self._lock:
                    op.cause = self._guard_halt(op.command, actual.directive.trigger, actual)
                self._halt(op, actual.directive.trigger)
            else:
                # A complete handoff can deliberately request observation
                # without publishing a session mode. Capture that real
                # no-effect decision rather than inventing an audit failure.
                op.cause = self._cause(op.command, "N2_RESULT", None, actual)
                self._begin_scope(op)
                self._raw_preflight(op)
                self._append(op, self._bridge(op, "NOT_APPLICABLE"))
            return
        if type(actual) is rv.RecoveryFailure:
            raise _Refusal("SESSION_N2_RESULT_REJECTED", "cause", "Actual N2 failure supplies no publishable candidate.", actual)
        op.cause = self._cause(op.command, "N2_RESULT", None, actual)
        self._begin_scope(op)
        if type(actual) is rv.RecoveryNoAction:
            self._raw_preflight(op)
            self._append(op, self._bridge(op, "NOT_APPLICABLE"))
            return
        post = next((item.assessment for item in reversed(actual.post_assessments) if
            type(item.assessment) is sv.StateAssessment and item.capture_status == "COMPLETE" and
            item.candidate_state == actual.candidate_state and
            item.assessment.system_state_class == "STABLE" and item.assessment.state_validity_diagnostic.is_valid), None)
        proposed = replace(self._snapshot, current_state=actual.candidate_state)
        if post is None or not self._assessment_valid(post, proposed, stable=True):
            raise _Refusal("SESSION_N2_RESULT_REJECTED", "publication", "Actual N2 candidate has no current complete STABLE/VALID proof.", actual)
        self._raw_preflight(op)
        self._publication(op, actual.candidate_state, "NORMAL", op.cause,
                          proof=post.assessment_binding.assessment_reference)
        op.post = post
        self._append(op, self._bridge(op, "RECOVERED" if type(actual) is rv.RecoveredValue else "RECOVERED_VIA_FALLBACK"))

    def _retain_main_result(self, op, result):
        reference = op.command.request.request_reference
        if reference in self._frozen_partial:
            return
        self._results.append(result)
        self._chronology.append(result)
        self._confirmed.extend(op.confirmed)
        self._attempted.extend(op.attempted)
        if op.pending is not None:
            self._pending.append(op.pending)
        if op.resolution is not None:
            self._resolutions.append(op.resolution)
        self._ledger[reference] = (op.command, result)

    def _halt(self, op, trigger):
        # All semantic eligibility checks happened before this point. The first
        # action here is the in-memory publication and cutover, without IO.
        with self._lock:
            if self._snapshot.terminal_latched:
                raise _Refusal("SESSION_TERMINAL", "publication", "An earlier halt already sealed this owner.")
            interrupted = op.interrupted
            prior_mode = self._snapshot.mode
            incomplete_interrupted = interrupted is not None
            if interrupted is not None:
                interrupted.failure = self._failure(_Refusal("SESSION_EXECUTION_CANCELLED", "execution_gate",
                    "First halt sealed this actual interrupted command group."))
                interrupted.after = self._snapshot
                if interrupted.effects or interrupted.confirmed:
                    partial = self._result(interrupted, status="UNCONFIRMED")
                    self._retain_main_result(interrupted, partial)
                    self._frozen_partial = self._frozen_partial | frozenset((interrupted.command.request.request_reference,))
            op.terminal = True
            self._publication(op, self._snapshot.current_state, "SAFE_HALT", op.cause, terminal=True)
            self._terminal_reference = op.command.request.request_reference
            for gate, lease, ordinal, terminal in tuple(self._gates.values()):
                if not terminal:
                    v._set_capture_disposition(self, gate, "SEALED")
            op.gate = self._gate(op.lease, terminal=True)
            self._lease = self._phase_snapshot = self._active = None
            slots = (op.command.request.request_reference + ":halt",)
            if prior_mode == "NORMAL":
                slots += (op.command.request.request_reference + ":bridge",)
            self._terminal_members = frozenset(record.diagnostic_reference for record in self._confirmed) | frozenset(slots)
            op.pending = self._pending_record(op, "SAFE_HALT", trigger,
                ("halt_time", "envelope", "full_diagnostic_chain"), "CAPTURE_UNCONFIRMED")
        try:
            self._begin_scope(op, terminal=True)
        except _Refusal as refusal:
            op.failure = self._failure(refusal, pending=op.pending)
            return
        clock = self._clock(op)
        if clock is None:
            op.pending = self._pending_record(op, "SAFE_HALT", trigger, ("halt_time",), "CLOCK_UNAVAILABLE")
            op.failure = self._failure(_Refusal("SESSION_CAPTURE_FAILED", "clock",
                "Mandatory halt occurred without a measured canonical halt time."), pending=op.pending)
            return
        if incomplete_interrupted:
            op.pending = self._pending_record(op, "SAFE_HALT", trigger, ("full_diagnostic_chain",), "CHAIN_UNCONFIRMED")
            op.failure = self._failure(_Refusal("SESSION_CAPTURE_FAILED", "history",
                "Mandatory halt sealed an in-flight group whose actual complete closure is unavailable."), pending=op.pending)
            return
        with self._lock:
            origin = self._phase_origin
            previous, root = self._main_previous, self._main_root
            trace = (self._initial,) + tuple(self._chronology)
        bridge = self._bridge(op, "BLOCKED", terminal=True) if prior_mode == "NORMAL" else None
        parent = bridge.diagnostic_reference if bridge is not None else previous
        reference = op.command.request.request_reference + ":halt"
        envelope = sv.DiagnosticEnvelope("SAFE_HALT", "CRITICAL", "TERMINAL", "TERMINAL",
            origin.subject_reference, parent, root, (_HALT_RULES[trigger],),
            "Actual irreversible reference session safe halt.",
            ("No ordinary session mutation is permitted after this owner cutover.",))
        closure = v.SessionTerminalChainClosure(op.command.request.request_reference, bridge,
                                                sv.DiagnosticEmission(reference, envelope), op.publication)
        payload = v.SafeHaltDiagnostic(trigger, origin.state_validity_diagnostic, "SAFE_HALT", clock,
            trace + (closure,), True, (_HALT_RULES[trigger],), envelope.notes)
        record = v.LifecycleRecord(reference, envelope, payload, op.cause)
        intended = (bridge, record) if bridge else (record,)
        candidate = replace(self._result(op), confirmed_lifecycle_records=intended,
            attempted_lifecycle_records=intended, pending_lifecycle_record=None)
        limit = v.MAX_RAW_BUSINESS_BYTES
        exceeds = v.raw_business_size(record) > limit or v.raw_business_size(candidate) > limit
        if not exceeds:
            candidate_record = v.raw_business_record(candidate)
            completion = self._completion_sizing_record()
            candidate_record["completion_observation"] = completion
            candidate_record["failure_detail"] = dict(failure_code=_SIZING_TEXT, field_name=_SIZING_TEXT,
                primary_evidence=candidate_record["publication"], capture_status=_SIZING_TEXT,
                attempted_lifecycle_record=candidate_record["attempted_lifecycle_records"][-1],
                pending_lifecycle_record=None, completion_failure_code=_SIZING_TEXT,
                unconfirmed_completion_observation=completion, reason=_SIZING_TEXT)
            with self._lock:
                history = self._history_value(extra=candidate)
            exceeds = v.raw_business_size(history) > limit
            if not exceeds:
                prospective = v.raw_business_record(history)
                prospective["command_results"][-1] = candidate_record
                prospective["confirmed_lifecycle_records"] += candidate_record["confirmed_lifecycle_records"]
                prospective["attempted_lifecycle_records"] += candidate_record["attempted_lifecycle_records"]
                exceeds = _sizing_size(candidate_record, limit) > limit or _sizing_size(prospective, limit) > limit
        if exceeds:
            op.raw_phase = "TERMINAL_CHAIN"
            op.pending = self._pending_record(op, "SAFE_HALT", trigger, ("full_diagnostic_chain",), "RAW_BUSINESS_LIMIT")
            op.failure = self._failure(_Refusal("SESSION_RAW_BUSINESS_LIMIT", "history",
                "Mandatory terminal state is actual; the full raw terminal packet exceeds its limit."), pending=op.pending)
            return
        try:
            if bridge is not None:
                self._append(op, bridge)
            self._append(op, record)
            op.pending = None
        except _Refusal as refusal:
            op.pending = self._pending_record(op, "SAFE_HALT", trigger, ("envelope",), "CAPTURE_UNCONFIRMED")
            op.failure = self._failure(refusal, attempted=record, pending=op.pending)

    def _finish_response(self, op, receipt):
        if type(receipt) is not v.SessionLifecycleCompletion:
            return None, False
        try:
            v.revalidate_value(receipt)
        except v.SessionContractError:
            return None, False
        confirmed = (receipt.operation_reference == op.command.request.request_reference and
                     receipt.status == "COMPLETE" and
                     all(record.diagnostic_reference in receipt.confirmed_references for record in op.confirmed))
        return receipt, confirmed

    def _associate_completed(self, op):
        if not self._live(op):
            return
        actual = op.post
        if actual is not None and self._assessment_valid(actual, self._snapshot,
                                                       stable=self._snapshot.mode == "NORMAL"):
            self._accepted, self._accepted_generation = actual, self._snapshot.generation
            self._snapshot = self._new_snapshot(admission_status="OPEN",
                current_assessment_reference=actual.assessment_binding.assessment_reference,
                observed_system_state_class=actual.system_state_class)
            self._phase_snapshot = self._snapshot
            if op.resolution is not None:
                self._phase_origin = actual
                self._main_root = actual.assessment_binding.diagnosis_reference
                self._main_previous = actual.emitted_diagnostics[-1].diagnostic_reference
                self._severity = max((record.envelope.severity for record in actual.emitted_diagnostics), key=_SEVERITIES.index)
        op.after = self._snapshot

    def _finalize(self, op):
        with self._lock:
            if op.after is None:
                op.after = self._snapshot
            if not op.terminal and not self._live(op) and op.failure is None:
                op.failure = self._failure(_Refusal("SESSION_EXECUTION_CANCELLED", "execution_gate",
                    "This actual return occurred after the owner cutover."))
        tentative = self._result(op, status="UNCONFIRMED" if op.pending is not None else None)
        complete = False
        if op.scope is not None and not op.finished:
            op.finished = True
            receipt = None
            try:
                receipt = op.scope.finish(tentative)
            except Exception:
                pass
            op.completion, complete = self._finish_response(op, receipt)
            if not complete:
                if op.failure is None:
                    op.failure = self._failure(_Refusal("SESSION_CAPTURE_FAILED", "capture.finish",
                        "Actual first lifecycle finish did not confirm this operation."))
                op.failure = replace(op.failure,
                    completion_failure_code="CAPTURE_COMPLETION_REJECTED" if op.completion is not None and
                        op.completion.status == "INCOMPLETE" else "CAPTURE_COMPLETION_UNCONFIRMED",
                    unconfirmed_completion_observation=op.completion)
        with self._lock:
            if complete and op.failure is None and not op.terminal:
                self._associate_completed(op)
            elif self._live(op) and (op.effects or op.failure is not None):
                self._snapshot = self._new_snapshot(admission_status="AUDIT_BLOCKED")
                self._phase_snapshot = self._snapshot
                op.after = self._snapshot
        final = self._result(op, status="UNCONFIRMED" if op.pending is not None else None)
        if op.raw_phase is None and v.raw_business_size(final) > v.MAX_RAW_BUSINESS_BYTES:
            op.raw_phase = "TERMINAL_CHAIN" if op.terminal else "CANDIDATE_RESULT"
        returned = final
        if op.raw_phase is not None:
            returned = v.SessionRawBusinessFailure(op.command.request.request_reference,
                self._binding.session_reference, self._prefix + ":history", op.raw_phase,
                op.lease.before, op.after, op.effects, "SESSION_RAW_BUSINESS_LIMIT",
                "PARTIAL" if op.terminal else "API_ONLY")
        receipt = None
        if self._handle is not None and not op.observed:
            op.observed = True
            try:
                if type(returned) is v.SessionRawBusinessFailure:
                    receipt = self._diagnostics.observe_session_result(self._handle, returned, actual_result=final)
                else:
                    receipt = self._diagnostics.observe_session_result(self._handle, final)
            except Exception:
                pass
            receipt = self._retention("FINAL_RESULT", receipt)
        with self._lock:
            live = self._live(op)
            selected = (live or op.terminal and self._terminal_reference == op.command.request.request_reference)
            if selected:
                self._retain_main_result(op, final)
                self._remember_retention(receipt)
                if op.terminal:
                    v._set_capture_disposition(self, op.gate, "SEALED")
            if live:
                if receipt is None or receipt.status != "CONFIRMED":
                    self._snapshot = self._new_snapshot(admission_status="AUDIT_BLOCKED")
                self._snapshot = self._new_snapshot(active_operation_reference=None)
                self._lease = self._phase_snapshot = self._active = None
                v._set_capture_disposition(self, op.gate, "SEALED")
            history = self._history_value() if selected else None
        if self._handle is not None and history is not None:
            try:
                if op.terminal:
                    retained = self._diagnostics.freeze_terminal(self._handle, history, op.publication)
                    phase = "FREEZE"
                else:
                    retained = self._diagnostics.pin_history(self._handle, history)
                    phase = "PIN"
                retained = self._retention(phase, retained)
                with self._lock:
                    self._remember_retention(retained)
                    if not op.terminal and retained.status != "CONFIRMED" and not self._snapshot.terminal_latched:
                        self._snapshot = self._new_snapshot(admission_status="AUDIT_BLOCKED")
            except Exception:
                with self._lock:
                    self._remember_retention(self._retention("FREEZE" if op.terminal else "PIN", None))
                    if not op.terminal and not self._snapshot.terminal_latched:
                        self._snapshot = self._new_snapshot(admission_status="AUDIT_BLOCKED")
        return returned
