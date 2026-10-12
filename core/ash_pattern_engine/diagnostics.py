"""Bounded reference Diagnostics composition [YWE-REQ-0042].

All observations and persistence cross explicit injected ports. Core performs no
source discovery, filesystem access, ambient clock lookup or native OS calls.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
import re
import threading
from typing import Protocol

from . import diagnostics_values as dv
from . import state_values as sv
from . import normalization_values as nv


def _configured_source_snapshots(identity, snapshots):
    """Validate declared assembly input before any storage or clock effects."""
    revision = identity.source_revision
    if revision is not None and (type(revision) is not str or re.fullmatch(r"[0-9a-f]{40}", revision) is None):
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    if snapshots is None:
        snapshots = () if revision is None else (dv.SourcePin("ASH_AGGREGATE", dv.LEGACY_SOURCE_REVISION,
            dict(sv.CANONICAL_BINDING_FIELDS)["aggregate_sha256"]),)
    if type(snapshots) is not tuple or len(snapshots) > 4:
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    expected = tuple(dict(fields)["aggregate_sha256"] for _, fields in sv.CANONICAL_BINDING_BASELINES)
    indexes, result = [], []
    for pin in snapshots:
        if type(pin) is not dv.SourcePin:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
        try:
            dv.SourcePin.__post_init__(pin)
        except (AttributeError, dv.DiagnosticsContractError):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE") from None
    module_present = any(pin.sha256 == dict(sv.MODULE_CANONICAL_BINDING_FIELDS)["aggregate_sha256"] for pin in snapshots)
    generation_present = any(pin.sha256 == dict(sv.GENERATION_CANONICAL_BINDING_FIELDS)["aggregate_sha256"] for pin in snapshots)
    for pin in snapshots:
        if pin.source_kind != "ASH_AGGREGATE" or pin.sha256 not in expected:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
        index = expected.index(pin.sha256)
        expected_revision = (dv.LEGACY_SOURCE_REVISION if index == 0 else
            dv.HISTORICAL_N3_SOURCE_REVISION if index == 1 and (module_present or generation_present) else
            dv.HISTORICAL_MODULE_SOURCE_REVISION if index == 2 and generation_present else revision)
        if pin.revision != expected_revision or index > 0 and revision is None:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
        indexes.append(index)
        result.append(dv.SourcePin(pin.source_kind, pin.revision, pin.sha256))
    if indexes != sorted(set(indexes)):
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    return tuple(result)


def _encode(value):
    return json.dumps(value.to_record(), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _fingerprint(value):
    return hashlib.sha256(_encode(value)).hexdigest()


class DiagnosticsClockPort(Protocol):
    def read(self) -> dv.ClockObservation: ...


class ProtectedStore(Protocol):
    def verify(self) -> dv.StorageVerification: ...
    def commit_event(self, sequence: int, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def commit_supporting(self, sequence: int, kind: str, evidence_alias: str, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def commit_meta(self, sequence: int, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def commit_incident(self, sequence: int, incident_alias: str, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def commit_health(self, sequence: int | None, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def commit_fallback_health(self, sequence: int | None, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def write_pair(self, bundle_alias: str, json_bytes: bytes, markdown_bytes: bytes, manifest_bytes: bytes, *, last_included_sequence: int | None): ...
    def purge_bundle(self, bundle_alias: str) -> dv.StorePurgeReceipt: ...
    def purge_capture(self, request: dv.CapturePurgeRequest) -> dv.StoreCapturePurgeReceipt: ...


def _context(**values):
    row = {name: None for name in dv.CONTEXT_FIELDS}
    row.update(values)
    row["unavailable_fields"] = tuple(name.upper() for name, value in row.items() if value is None)
    row["input_failure_code"] = values.get("input_failure_code")
    return dv.SafeStateContext(**row)


def _orbit(value):
    return None if value is None else dv.SafeOrbit(value.orbit_id, value.contains_known_valid_state)


@dataclass(frozen=True, slots=True)
class _Origin:
    assessment_reference: str
    subject_reference: str
    chain_root_reference: str
    last_diagnostic_reference: str
    system_state_class: str | None
    recovery_category: str | None

    @classmethod
    def observed(cls, packet):
        last = packet.emitted_diagnostics[-1]
        return cls(packet.assessment_binding.assessment_reference,
                   last.envelope.subject_reference, last.envelope.chain_root_reference,
                   last.diagnostic_reference, getattr(packet, "system_state_class", None),
                   getattr(packet, "recovery_category", None))


class _CaptureScope:
    def __init__(self, owner, reference, producer, *, relation=None, original=None,
                 reserved_events=2, reserved_bytes=131072, reserved_aliases=64, denial=False,
                 execution_gate=None, budget_parent=None, reserved_supporting_bytes=0):
        self.owner, self.reference, self.producer = owner, reference, producer
        self.storage_reference = reference
        self.relation = relation
        self.original = None if original is None else _Origin.observed(original)
        self.reserved_events, self.reserved_bytes, self.reserved_aliases = reserved_events, reserved_bytes, reserved_aliases
        self.remaining_events, self.remaining_bytes, self.remaining_aliases = reserved_events, reserved_bytes, reserved_aliases
        self.denial, self.finished = denial, False
        self.execution_gate, self.budget_parent = execution_gate, budget_parent
        self.reserved_supporting_bytes = reserved_supporting_bytes
        self.remaining_supporting_bytes = reserved_supporting_bytes
        self.final_observation_pending = False
        self.late_indices = []
        self.completed_result = self.completion_response = None
        self.completed_hash = None
        self.audit_cleanup_allowed = False
        self.references, self.indices, self.hashes = [], [], []
        self.attempted_reference, self.attempted_hash, self.attempted_index = None, None, None
        self.failed, self.first_clock, self.last_envelope = None, owner._last_clock, None
        self.child_operations = []
        self.support_keys = set()
        self.purged = False
        self.step_indices = {}
        self.step_policies = {}
        self.remaining_incidents = 32 if producer == "RECOVERY_ENGINE" and not denial else 1
        if budget_parent is not None:
            self.remaining_incidents = 0

    def append(self, record):
        return self.owner._append(self, record)

    def finish(self, result):
        return self.owner._complete(self, result, "RECOVERY_ENGINE")


class _AssessmentCapture:
    def __init__(self, owner, relation, execution_gate=None):
        self.owner, self.relation, self.execution_gate = owner, relation, execution_gate

    def begin(self, assessment_reference):
        if self.execution_gate is not None:
            with self.owner._session_io():
                return self.owner._begin(assessment_reference, 'STATE_MODEL', relation=self.relation,
                    execution_gate=self.execution_gate)
        return self.owner._begin(assessment_reference, "STATE_MODEL", relation=self.relation,
            execution_gate=self.execution_gate)


def _is_issued_recovery_scope(scope, collector, execution_gate, operation_reference):
    """Authenticate an issued native scope for once-only cleanup, without IO."""
    from . import session_values as v
    if type(scope) is not _CaptureScope or type(collector) not in (ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics):
        return False
    if type(operation_reference) is not str or type(scope.reference) is not str or type(scope.storage_reference) is not str or type(scope.producer) is not str:
        return False
    return (scope.owner is collector and scope.execution_gate is execution_gate and
        scope.reference == operation_reference and scope.producer == "RECOVERY_ENGINE" and
        v._gate_matches_collector(execution_gate, collector) and
        collector._scopes.get(scope.storage_reference) is scope)


class _NormalizationCapture:
    def __init__(self, owner, execution_gate=None):
        self.owner, self.execution_gate = owner, execution_gate

    def begin(self, operation_reference, *, original_diagnosis):
        if type(original_diagnosis) is not sv.StateDiagnosis:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "ORIGINAL_DIAGNOSIS")
        if self.execution_gate is None:
            self.owner._attached(original_diagnosis.emitted_diagnostics)
            return self.owner._begin(operation_reference, "NORMALIZATION", original=original_diagnosis)
        self.owner._check_capture_binding(self.execution_gate, operation_reference=operation_reference)
        _, _, source, profile, _ = type(self.execution_gate).configuration(self.execution_gate)
        from .session_values import revalidate_value
        revalidate_value(original_diagnosis)
        if original_diagnosis.source_binding != source or original_diagnosis.profile_binding != profile:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        with self.owner._session_io():
            self.owner._check_gate(self.execution_gate)
            self.owner._attached(original_diagnosis.emitted_diagnostics)
            return self.owner._begin(operation_reference, "NORMALIZATION", original=original_diagnosis,
                execution_gate=self.execution_gate)


class _RecoveryCapture:
    def __init__(self, owner, execution_gate=None):
        self.owner, self.execution_gate = owner, execution_gate

    def begin(self, origin, *, operation_reference):
        return self.owner._recovery_begin(origin, operation_reference, False, self.execution_gate)

    def begin_denial(self, origin, *, operation_reference):
        return self.owner._recovery_begin(origin, operation_reference, True, self.execution_gate)


class _SessionRetention:
    def __init__(self, handle, binding):
        self.handle, self.binding = handle, binding
        self.pinned_scopes, self.pinned_support = set(), set()
        self.recovery_results, self.results, self.denials = {}, {}, {}
        self.main_origin = self.episode_origin = None
        self.main_root = self.main_previous = None
        self.frozen = False
        self.freeze_receipt = None
        self.observed, self.denial_observed = set(), set()
        self.resolution_previous = {}
        self.module_controls, self.module_results = {}, {}
        self.module_history_reference = None


_MODULE_CONTROL_FACTORY = object()


class SessionModuleControlScope:
    __slots__ = ('_collector', '_state', '_native', '_lease', '_original', '_receipt', '_result')
    def __new__(cls, marker=None):
        if cls is not SessionModuleControlScope or marker is not _MODULE_CONTROL_FACTORY:
            raise dv.DiagnosticsContractError('DIAGNOSTICS_RECORD_NONCONFORMANT')
        return super().__new__(cls)

    def observe_final(self, actual_result):
        from . import session_values as v
        from . import diagnostic_session_values as safe
        if type(self) is not SessionModuleControlScope:
            raise dv.DiagnosticsContractError('DIAGNOSTICS_ORIGIN_MISMATCH')
        try:
            collector, state, native = self._collector, self._state, self._native
            if ((type(collector) is not ReferenceDevelopmentDiagnostics and type(collector) is not ReferenceReleaseDiagnostics) or
                    type(state) is not _SessionRetention or type(native) is not _CaptureScope or
                    type(self._lease) is not v.SessionModuleLease or self._original is not self or
                    state.module_controls.get(self._lease.command.request_reference) is not self or
                    collector._scopes.get(native.storage_reference) is not native or native.owner is not collector):
                raise dv.DiagnosticsContractError('DIAGNOSTICS_ORIGIN_MISMATCH')
            v.revalidate_value(actual_result)
            if type(actual_result) is not v.SessionModuleResult or actual_result.command != self._lease.command or actual_result.admission.lease != self._lease:
                raise dv.DiagnosticsContractError('DIAGNOSTICS_COMPLETION_MISMATCH')
            if self._receipt is not None:
                if actual_result != self._result:
                    raise dv.DiagnosticsContractError('DIAGNOSTICS_COMPLETION_MISMATCH')
                return self._receipt
            with collector._session_io():
                if self._receipt is not None:
                    if actual_result != self._result:
                        raise dv.DiagnosticsContractError('DIAGNOSTICS_COMPLETION_MISMATCH')
                    return self._receipt
                self._result = actual_result
                native.audit_cleanup_allowed = True
                previous = collector._charging_scope
                collector._charging_scope = native
                failure = None
                alias = None
                try:
                    projection = collector._projection(state)
                    from . import diagnostic_module_values as module_values
                    origin = actual_result.origin_diagnosis
                    origin_evidence = None if origin is None or not origin.emitted_diagnostics else collector._assessment_support(origin)
                    module_scope = _ReferenceDiagnostics._modules(collector).scopes.get(self._lease.command.request_reference)
                    module_operation = None if module_scope is None else module_scope._projection.operation_alias
                    module_final = None if module_scope is None or module_scope._final is None else module_scope._final.supporting_reference
                    def snapshot(value):
                        return dict(snapshot_reference=projection.alias(value.snapshot_reference), generation=value.generation,
                            state_signature=value.current_state.signature, mode=value.mode, terminal_latched=value.terminal_latched,
                            admission_status=value.admission_status, current_assessment_reference=projection.alias(value.current_assessment_reference),
                            active_operation_reference=projection.alias(value.active_operation_reference))
                    alias = projection.put('SESSION_MODULE_LINK', safe.SafeSessionModuleLinkEvidence, actual_result,
                        session_binding_reference=projection.binding(state.binding), session_reference=projection.alias(state.binding.session_reference),
                        request_reference=projection.alias(actual_result.command.request_reference), lease_reference=projection.alias(self._lease.lease_reference),
                        producer=actual_result.command.producer, operation=actual_result.command.operation,
                        before=snapshot(actual_result.before), active=snapshot(self._lease.active_snapshot), after=snapshot(actual_result.after),
                        actual_origin_evidence_reference=origin_evidence,
                        actual_origin_completion_reference=None if actual_result.origin_completion is None else origin_evidence,
                        actual_module_operation_reference=module_operation, actual_module_final_reference=module_final,
                        status=actual_result.status, failure_code=actual_result.failure_code if actual_result.failure_code in v.SESSION_FAILURE_CODES else None,
                        module_failure_code=actual_result.failure_code if actual_result.failure_code in module_values.FAILURES else None,
                        session_effects_performed=False, late_after_cutover=state.frozen, coverage=actual_result.coverage)
                    state.module_results[actual_result.command.request_reference] = (actual_result, alias)
                    if origin is not None:
                        source_scope = collector._scopes.get(origin.assessment_binding.assessment_reference)
                        if source_scope is not None:
                            state.pinned_scopes.add(source_scope.storage_reference)
                            state.pinned_support.update(source_scope.support_keys)
                    if module_scope is not None:
                        state.pinned_scopes.add(module_scope._native.storage_reference)
                        state.pinned_support.update(module_scope._native.support_keys)
                    state.pinned_support.update(native.support_keys)
                    collector._select_support(state, state.pinned_support)
                except (dv.DiagnosticsContractError, v.SessionContractError):
                    failure = 'SESSION_RETENTION_INCOMPLETE'
                    collector._mark_failure('DIAGNOSTICS_COMPLETION_MISMATCH')
                finally:
                    native.finished, native.audit_cleanup_allowed = True, False
                    collector._charging_scope = previous
                self._receipt = v.SessionModuleRetentionReceipt(state.binding.session_reference,
                    actual_result.command.request_reference, 'FINAL_RESULT', 'CONFIRMED' if failure is None else 'NOT_CONFIRMED',
                    'COMPLETE_SPECIFIED_SAFE_GRAPH' if failure is None else 'PARTIAL', len(state.pinned_support), alias, failure)
                return self._receipt
        except (AttributeError, v.SessionContractError):
            raise dv.DiagnosticsContractError('DIAGNOSTICS_ORIGIN_MISMATCH') from None


class _SessionLifecycleCapture:
    def __init__(self, owner, state, execution_gate):
        self.owner, self.state, self.execution_gate = owner, state, execution_gate

    def begin(self, command, *, before, origin_refs, terminal=False):
        return self.owner._session_begin(self.state, self.execution_gate, command, before, origin_refs, terminal)


class _SessionLifecycleScope:
    def __init__(self, owner, state, scope, command, *, terminal=False):
        self.owner, self.state, self.scope, self.command = owner, state, scope, command
        self.terminal = terminal

    def append(self, record):
        return self.owner._session_append(self, record)

    def observe_clock(self):
        with self.owner._session_io():
            if self.scope.finished:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
            return self.owner._observe_clock(execution_gate=self.scope.execution_gate)

    def assessment_capture(self, relation):
        from . import session_values as v
        v.revalidate_value(relation)
        if type(relation) is not v.SessionAssessmentLink or relation.session_reference != self.state.binding.session_reference or relation.parent_operation_reference != self.scope.reference:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        return self.owner.assessment_capture(relation=relation, execution_gate=self.scope.execution_gate)

    def append_resolution(self, observation):
        return self.owner._session_resolution(self, observation)

    def finish(self, tentative_result):
        return self.owner._session_finish(self, tentative_result)


class _SessionDenialScope:
    def __init__(self, owner, state, scope, snapshot, ordinal):
        self.owner, self.state, self.scope = owner, state, scope
        self.snapshot, self.ordinal = snapshot, ordinal

    def append(self, record):
        with self.owner._session_io():
            return self.owner._append(self.scope, record)

    def finish(self, tentative_denial):
        return self.owner._session_finish(self, tentative_denial)


class _SessionIO:
    def __init__(self, owner):
        self.owner = owner

    def __enter__(self):
        if not self.owner._lock.acquire(blocking=False):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
        if self.owner._io_depth:
            self.owner._lock.release()
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")

    def __exit__(self, *unused):
        self.owner._lock.release()


class _ReferenceDiagnostics:
    _profile_id = None

    def __init__(self, identity, profile, store, clock, *, canonical_source_snapshots=None):
        if type(identity) is not dv.DiagnosticsIdentity or type(profile) is not dv.DiagnosticsProfile:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID")
        snapshots = _configured_source_snapshots(identity, canonical_source_snapshots)
        if identity.profile_id != self._profile_id or profile.profile_id != self._profile_id or identity.implementation_id != profile.implementation_id:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID")
        methods = ("verify", "commit_event", "commit_supporting", "commit_meta", "commit_health",
                   "commit_fallback_health", "write_pair", "purge_bundle", "purge_capture", "commit_incident")
        if any(not callable(getattr(store, method, None)) for method in methods) or not callable(getattr(clock, "read", None)):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID")
        self.identity, self.profile, self.store, self.clock = identity, profile, store, clock
        self._canonical_source_snapshots = snapshots
        self._lock, self._limits = threading.RLock(), dv.DiagnosticLimits()
        self._io_depth = 0
        verification = store.verify()
        if type(verification) is not dv.StorageVerification or verification.status != "VERIFIED":
            raise dv.DiagnosticsContractError("STORAGE_PROTECTION_UNAVAILABLE", "STORE")
        self._aliases, self._next_alias = {}, 1
        # Assembly aliases are already safe identity values, never raw-key records.
        seeded = (identity.build_id, identity.session_reference, profile.selection_authority,
                  *identity.source_provenance.dirty_path_aliases)
        self._next_alias = max(int(item[4:]) for item in seeded) + 1
        self._events, self._meta, self._incidents, self._scopes, self._acks = [], [], [], {}, {}
        self._support = {kind: {} for kind in dv.enum_values("SupportingKind")}
        self._support_bytes, self._used, self._next_sequence = 0, 0, 0
        self._counts = dict.fromkeys(dv.enum_values("CounterField"), 0)
        self._saturated = set()
        self._redactions, self._retention = {}, []
        self._failure = self._fallback_cause = None
        self._incident_bytes = 0
        self._unconfirmed_incidents = []
        self._unconfirmed_events = {}
        self._unconfirmed_support = {}
        self._session_handles = {}
        self._lifecycle_scopes = {}
        from .diagnostic_module_capture import ModuleCaptureService
        self._module_capture_service = ModuleCaptureService(self)
        self._first_unavailable = self._last_unavailable = None
        self._storage = self._meta_storage = "PROTECTED_VERIFIED"
        self._producer_completed = set()
        self._issued_snapshots, self._export_slot = {}, None
        self._export_completed = False
        self._export_boundary = None
        self._last_clock = self._start_clock = self._observe_clock(initial=True)
        self._charging_scope = None
        self._persist_health()

    def _increment(self, field, amount=1):
        previous = self._counts[field]
        if previous is None:
            return
        if previous > (1 << 64) - 1 - amount:
            self._counts[field] = (1 << 64) - 1
            self._saturated.add(field)
            self._failure = "DIAGNOSTICS_COUNTER_LIMIT"
        else:
            self._counts[field] = previous + amount

    def _alias(self, reference):
        if type(reference) is not str or not 1 <= len(reference) <= 256 or not reference.isascii():
            raise dv.DiagnosticsContractError("DIAGNOSTICS_VALUE_INVALID")
        if reference in self._aliases:
            return self._aliases[reference]
        charged = self._charging_scope
        if charged is not None:
            charged = self._budget_scope(charged)
            self._check_scope_tokens(charged)
        if charged is not None and charged.remaining_aliases <= 0:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ALIAS_LIMIT")
        reserved = sum(scope.remaining_aliases for scope in self._scopes.values()
            if not scope.finished or scope.final_observation_pending)
        if charged is None and len(self._aliases) + reserved >= 6144:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ALIAS_LIMIT")
        if len(self._aliases) >= 6144 or self._next_alias > 999999:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ALIAS_LIMIT")
        alias = f"ref:{self._next_alias:06d}"
        self._next_alias += 1
        self._aliases[reference] = alias
        if charged is not None:
            charged.remaining_aliases -= 1
        self._increment("REDACTED_REFERENCES")
        return alias

    @staticmethod
    def _check_gate(execution_gate):
        if execution_gate is None:
            return
        from . import session_values as session
        from core.module_lifecycle import CoreExecutionGate
        if type(execution_gate) is CoreExecutionGate:
            disposition = CoreExecutionGate.capture_disposition(execution_gate)
        elif session._is_issued_gate(execution_gate):
            disposition = session.SessionExecutionGate.capture_disposition(execution_gate)
        else:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        if disposition != "ACTIVE":
            raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")

    def _check_scope_tokens(self, scope):
        if scope is None or scope.audit_cleanup_allowed:
            return
        self._check_gate(scope.execution_gate)
        control = getattr(scope, 'emitter_control', None)
        if control is not None:
            from .planner_emitter_values import IssuedEmitterCaptureControl
            if IssuedEmitterCaptureControl.capture_disposition(control) != 'ACTIVE':
                raise dv.DiagnosticsContractError('DIAGNOSTICS_REPLAY_REFUSED')

    def _session_io(self):
        return _SessionIO(self)

    def _check_capture_binding(self, gate, handle=None, *, operation_reference=None):
        if gate is None:
            return
        from . import session_values as v
        from core.module_lifecycle import CoreExecutionGate
        if type(gate) is CoreExecutionGate:
            if handle is not None:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
            try:
                collector, reference, source, profile, generation = CoreExecutionGate.configuration(gate)
                if (collector is not self or not CoreExecutionGate.validate_issued_for_collector(gate, self,
                        operation_reference if operation_reference is not None else reference)):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
                sv.CanonicalAshBinding.__post_init__(source)
                type(profile).__post_init__(profile)
                if not any(pin.sha256 == source.aggregate_sha256 for pin in self._canonical_source_snapshots):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE")
            except (AttributeError, ValueError, TypeError):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH") from None
            return
        if not v._gate_matches_collector(gate, self, handle):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")

    def _session_state(self, handle):
        from . import session_values as v
        if not v._handle_is_issued_by(handle, self):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        state = self._session_handles.get(handle)
        if state is None or state.handle is not handle:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        return state

    def _budget_scope(self, scope):
        return self._scopes[scope.budget_parent] if scope.budget_parent is not None else scope

    @staticmethod
    def _raw_bytes(value, scope):
        if scope is None or scope.execution_gate is None:
            return _encode(value)
        from . import session_values as session
        try:
            return session.raw_business_bytes(value)
        except session.SessionContractError as error:
            code = "DIAGNOSTICS_RAW_PACKET_LIMIT" if error.failure_code == "SESSION_RAW_BUSINESS_LIMIT" else "DIAGNOSTICS_RECORD_NONCONFORMANT"
            raise dv.DiagnosticsContractError(code) from None

    def _observe_clock(self, *, initial=False, execution_gate=None):
        self._check_gate(execution_gate)
        try:
            self._io_depth += 1
            try:
                observed = self.clock.read()
            finally:
                self._io_depth -= 1
            if type(observed) is not dv.ClockObservation:
                raise ValueError()
        except Exception:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CLOCK_UNAVAILABLE") from None
        self._check_gate(execution_gate)
        value = observed.monotonic_nanoseconds
        if value is None:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CLOCK_UNAVAILABLE")
        if not initial:
            previous = self._last_clock.monotonic_nanoseconds
            if value < previous:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_CLOCK_REGRESSION")
            if value - self._start_clock.monotonic_nanoseconds > 600000000000:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_DURATION_LIMIT")
            self._last_clock = observed
        return observed

    def _begin(self, reference, producer, *, relation=None, original=None,
               reserved_events=2, reserved_bytes=131072, reserved_aliases=64, denial=False,
               execution_gate=None, reserved_supporting_bytes=0, storage_reference=None):
        sv.InputEvidence.validate_reference(reference)
        with self._lock:
            storage_reference = storage_reference or reference
            self._check_capture_binding(execution_gate, operation_reference=reference)
            session_state = None
            if execution_gate is not None:
                from . import session_values as session
                session_state = next((state for state in self._session_handles.values()
                    if session._gate_matches_collector(execution_gate, self, state.handle)), None)
            if self.identity.source_revision is None or not self._canonical_source_snapshots:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE", "ORIGINAL_SOURCE")
            self._check_gate(execution_gate)
            if execution_gate is not None and self._io_depth:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
            self._observe_clock(execution_gate=execution_gate)
            if storage_reference in self._scopes:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
            active = tuple(scope for scope in self._scopes.values()
                if not scope.finished or scope.final_observation_pending)
            incidents = 32 if producer == "RECOVERY_ENGINE" and not denial else 1
            budget_parent = None
            if relation is not None:
                from .recovery_values import PostAssessmentLink
                if type(relation) is PostAssessmentLink:
                    budget_parent = relation.parent_operation_reference
                else:
                    from . import session_values as session
                    if type(relation) is session.SessionAssessmentLink:
                        lifecycle_parent = self._lifecycle_scopes.get(relation.parent_operation_reference)
                        if lifecycle_parent is None:
                            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE")
                        budget_parent = lifecycle_parent.storage_reference
                    elif type(relation) is session.SessionChildLink:
                        session.revalidate_value(relation)
                        state = session_state
                        if execution_gate is None or state is None or state.frozen or reference != relation.child_origin_assessment_reference or relation.live_origin_assessment_reference not in self._scopes:
                            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
                        if state.binding.binding_reference != relation.session_binding_reference:
                            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
                    else:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
            if budget_parent is not None:
                reserved_events, reserved_bytes, reserved_aliases = 0, 0, 0
                reserved_supporting_bytes = 0
                incidents = 0
            if len(self._incidents) + len(self._unconfirmed_incidents) + sum(scope.remaining_incidents for scope in active) + incidents > 32:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
            if len(active) >= 8 or len(self._events) + len(self._unconfirmed_events) + sum(scope.remaining_events for scope in active) + reserved_events > 1024:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
            if self._used + sum(scope.remaining_bytes for scope in active) + reserved_bytes > 33554432:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
            if len(self._aliases) + sum(scope.remaining_aliases for scope in active) + reserved_aliases > 6144:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ALIAS_LIMIT")
            if self._support_bytes + sum(scope.remaining_supporting_bytes for scope in active) + reserved_supporting_bytes > 2097152:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
            if budget_parent is not None:
                parent = self._scopes.get(budget_parent)
                expected = "RECOVERY_ENGINE" if type(relation) is PostAssessmentLink else "SESSION_LIFECYCLE"
                if parent is None or parent.finished or parent.producer != expected or parent.execution_gate is not execution_gate:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE")
                parent.child_operations.append(reference)
                # Children consume their operation's existing whole reservation.
                reserved_events, reserved_bytes, reserved_aliases = 0, 0, 0
            scope = _CaptureScope(self, reference, producer, relation=relation, original=original,
                reserved_events=reserved_events, reserved_bytes=reserved_bytes,
                reserved_aliases=reserved_aliases, denial=denial, execution_gate=execution_gate,
                budget_parent=budget_parent, reserved_supporting_bytes=reserved_supporting_bytes)
            scope.storage_reference = storage_reference
            self._scopes[storage_reference] = scope
            if session_state is not None:
                scope.session_state = session_state
                session_state.pinned_scopes.add(storage_reference)
            previous_charge = self._charging_scope
            self._charging_scope = scope
            try:
                self._alias(reference)
            finally:
                self._charging_scope = previous_charge
            return scope

    def assessment_capture(self, *, relation=None, execution_gate=None):
        self._check_capture_binding(execution_gate)
        self._check_gate(execution_gate)
        return _AssessmentCapture(self, relation, execution_gate)

    def _modules(self):
        from .diagnostic_module_capture import ModuleCaptureService
        if (type(self) is not ReferenceDevelopmentDiagnostics and type(self) is not ReferenceReleaseDiagnostics) or type(self._module_capture_service) is not ModuleCaptureService or self._module_capture_service.collector is not self:
            raise dv.DiagnosticsContractError('DIAGNOSTICS_CONFIG_INVALID')
        return self._module_capture_service

    def register_module_producer(self, producer):
        from .diagnostic_module_capture import ModuleCaptureService
        return ModuleCaptureService.register(_ReferenceDiagnostics._modules(self), producer)

    def module_capture(self, producer, context, *, execution_gate=None, emitter_control=None):
        from .diagnostic_module_capture import ModuleCaptureService
        return ModuleCaptureService.begin(_ReferenceDiagnostics._modules(self), producer, context, execution_gate, emitter_control)

    def audit_module_return(self, scope, *, boundary):
        from .diagnostic_module_capture import ModuleCaptureService
        return ModuleCaptureService.audit(_ReferenceDiagnostics._modules(self), scope, boundary)

    def release_preparations_for_emitter(self, emitter):
        from .diagnostic_module_capture import ModuleCaptureService
        return ModuleCaptureService.release_preparations(_ReferenceDiagnostics._modules(self), emitter)

    def prepare_emission(self, planner, result, capture, emitter, target, *, operation_reference, execution_gate=None):
        from .diagnostic_module_capture import ModuleCaptureService
        return ModuleCaptureService.prepare(_ReferenceDiagnostics._modules(self), planner, result, capture,
            emitter, target, operation_reference, execution_gate)

    def normalization_capture(self, *, execution_gate=None):
        if execution_gate is not None:
            from core.module_lifecycle import CoreExecutionGate
            if type(execution_gate) is not CoreExecutionGate:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
            self._check_capture_binding(execution_gate)
            self._check_gate(execution_gate)
        return _NormalizationCapture(self, execution_gate)

    def recovery_capture(self, *, execution_gate=None):
        if execution_gate is not None:
            from .session_values import SessionExecutionGate
            if type(execution_gate) is not SessionExecutionGate:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        self._check_capture_binding(execution_gate)
        self._check_gate(execution_gate)
        return _RecoveryCapture(self, execution_gate)

    def _session_receipt(self, state, phase, failure=None):
        from . import session_values as v
        selected = () if state is None else tuple(self._scopes[ref] for ref in state.pinned_scopes if ref in self._scopes)
        known = {index for scope in selected for index in (*scope.indices, *scope.late_indices)}
        unknown = {scope.attempted_index for scope in selected
                   if scope.attempted_index in self._unconfirmed_events}
        uncertain = bool(unknown) or state is not None and bool(state.pinned_support & self._unconfirmed_support.keys())
        code = failure or ("SESSION_RETENTION_UNCONFIRMED" if uncertain or self._storage != "PROTECTED_VERIFIED" else None)
        return v.SessionRetentionReceipt(state.binding.session_reference, "CONFIRMED" if code is None else "NOT_CONFIRMED" if code == "SESSION_RETENTION_UNCONFIRMED" else "REJECTED",
            phase, "STORAGE_UNCERTAIN" if uncertain or self._storage != "PROTECTED_VERIFIED" else "PARTIAL" if code else "COMPLETE_SPECIFIED_SAFE_GRAPH",
            len(known), len(unknown), len(state.pinned_support), code,
            policy_binding=state.binding.policy_binding if state.binding.policy_binding.policy_version == "1.1.0" else None)

    def _projection(self, state):
        from .diagnostic_session_values import SessionProjection
        return SessionProjection(self, state)

    def _select_support(self, state, seeds):
        pending = list(seeds)
        selected = set()
        by_alias = {}
        for kind, nodes in self._support.items():
            for alias in nodes:
                by_alias.setdefault(alias, []).append((kind, alias))
        for key in self._unconfirmed_support:
            by_alias.setdefault(key[1], []).append(key)
        def references(value):
            if type(value) is str:
                yield from by_alias.get(value, ())
            elif type(value) is dict:
                for child in value.values():
                    yield from references(child)
            elif type(value) in (list, tuple):
                for child in value:
                    yield from references(child)
        while pending:
            key = pending.pop()
            if key in selected:
                continue
            node = self._support[key[0]].get(key[1], self._unconfirmed_support.get(key))
            if node is None:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
            selected.add(key)
            pending.extend(references(node.to_record()))
        if len(selected) > (2663 if state.binding.policy_binding.policy_version == '1.1.0' else 2544):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
        state.pinned_support.update(selected)
        return selected

    def register_session(self, binding):
        from . import session_values as v
        if type(binding) is not v.SessionBinding:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        v.revalidate_value(binding)
        state = _SessionRetention(None, binding)
        try:
            with self._session_io():
                if any(item.binding.session_reference == binding.session_reference for item in self._session_handles.values()):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
                self._observe_clock()
                handle = v._issue_retention_handle(self, binding.session_reference)
                state.handle = handle
                self._projection(state).binding(binding)
                self._select_support(state, state.pinned_support)
                self._persist_health()
                if self._storage != "PROTECTED_VERIFIED":
                    raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
                self._session_handles[handle] = state
                return handle, self._session_receipt(state, "REGISTER")
        except (dv.DiagnosticsContractError, v.SessionContractError) as error:
            code = "SESSION_RETENTION_UNCONFIRMED" if getattr(error, "code", "").startswith("STORAGE") else "SESSION_RETENTION_REJECTED"
            return None, self._session_receipt(state, "REGISTER", code)

    def attach_result(self, handle, result, *, relation=None):
        from . import session_values as v
        from . import recovery_values as rv
        state = self._session_state(handle)
        try:
            with self._session_io():
                if state.frozen:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
                v.revalidate_value(result)
                assessment = type(result) in (sv.StateAssessment, sv.ClassificationEvidenceFailure, sv.DiagnosticCaptureFailure)
                if not assessment and type(result) not in (rv.RecoveryNoAction, rv.RecoveredValue, rv.RecoveredFallbackValue, rv.RecoveryHandoff, rv.RecoveryFailure):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                reference = result.assessment_binding.assessment_reference if assessment else result.operation_context.operation_reference
                scope = self._scopes.get(reference)
                if scope is None or not scope.finished or scope.purged:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE")
                self._attached(result.emitted_diagnostics if assessment else tuple(
                    sv.DiagnosticEmission(item.diagnostic_reference, item.envelope) for item in result.emitted_diagnostics))
                if tuple(hashlib.sha256(self._raw_bytes(record, scope)).hexdigest() for record in result.emitted_diagnostics) != tuple(scope.hashes):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                if assessment and result.source_binding != state.binding.canonical_binding or assessment and result.profile_binding != state.binding.profile_binding:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
                if assessment and scope.completed_hash != hashlib.sha256(self._raw_bytes(result, scope)).hexdigest():
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                if relation is not None:
                    if type(relation) is not v.SessionChildLink or scope.relation != relation or relation.session_binding_reference != state.binding.binding_reference or relation.child_origin_assessment_reference != reference:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
                    v.revalidate_value(relation)
                    self._session_child_link(state, relation)
                elif assessment and reference != state.binding.initial_assessment_reference:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
                state.pinned_scopes.add(reference)
                state.pinned_scopes.update(scope.child_operations)
                for ref in (reference, *scope.child_operations):
                    state.pinned_support.update(self._scopes[ref].support_keys)
                projection = self._projection(state)
                if assessment:
                    projection.assessment(result)
                    if state.main_origin is None and reference == state.binding.initial_assessment_reference:
                        if type(result) is not sv.StateAssessment or scope.failed:
                            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE")
                        state.main_origin = state.episode_origin = result
                        state.main_root = result.emitted_diagnostics[0].diagnostic_reference
                        state.main_previous = result.emitted_diagnostics[-1].diagnostic_reference
                else:
                    if len(state.recovery_results) >= 2 and reference not in state.recovery_results:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
                    if result.completion_observation != scope.completion_response:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                    state.recovery_results[reference] = result
                self._select_support(state, state.pinned_support)
                return self._session_receipt(state, "ATTACH", "SESSION_RETENTION_INCOMPLETE" if scope.failed else None)
        except (dv.DiagnosticsContractError, v.SessionContractError):
            return self._session_receipt(state, "ATTACH", "SESSION_RETENTION_INCOMPLETE")

    def _session_child_link(self, state, relation):
        from .diagnostic_session_values import SafeSessionChildLink, SafeSessionChildLinkEvidence
        projection = self._projection(state)
        projection.put("SESSION_LINK", SafeSessionChildLinkEvidence, relation,
            link=SafeSessionChildLink(*(projection.alias(getattr(relation, name)) if name != "admitted_generation" else relation.admitted_generation
                for name in ("link_reference", "session_binding_reference", "admitted_generation", "live_origin_assessment_reference", "child_origin_assessment_reference", "child_operation_reference"))))

    def lifecycle_capture(self, handle, *, execution_gate):
        state = self._session_state(handle)
        self._check_capture_binding(execution_gate, handle)
        self._check_gate(execution_gate)
        return _SessionLifecycleCapture(self, state, execution_gate)

    def reserve_session_module(self, handle, lease, *, execution_gate):
        from . import session_values as v
        state = self._session_state(handle)
        try:
            v.revalidate_value(lease)
            if type(lease) is not v.SessionModuleLease or state.binding.policy_binding.policy_version != '1.1.0' or lease.before.binding != state.binding:
                raise dv.DiagnosticsContractError('DIAGNOSTICS_ORIGIN_MISMATCH')
            if v.SessionExecutionGate.validate_module_capture(execution_gate, self,
                    lease.command.request_reference, lease.command.producer) is not True:
                raise dv.DiagnosticsContractError('DIAGNOSTICS_ORIGIN_MISMATCH')
            with self._session_io():
                self._check_gate(execution_gate)
                reference = lease.command.request_reference
                active = tuple(scope for scope in self._scopes.values() if not scope.finished or scope.final_observation_pending)
                if (state.frozen or reference in state.module_controls or len(state.module_controls) >= 4 or len(active) >= 8 or
                        self._used + sum(scope.remaining_bytes for scope in active) + 65536 > 33554432 or
                        self._support_bytes + sum(scope.remaining_supporting_bytes for scope in active) + 32768 > 2097152 or
                        len(self._aliases) + sum(scope.remaining_aliases for scope in active) + 64 > 6144):
                    raise dv.DiagnosticsContractError('DIAGNOSTICS_RESERVATION_REFUSED')
                native = _CaptureScope(self, reference, 'SESSION_LIFECYCLE', reserved_events=0,
                    reserved_bytes=65536, reserved_aliases=64, reserved_supporting_bytes=32768, execution_gate=execution_gate)
                native.storage_reference = 'session:module:control:' + hashlib.sha256((state.binding.session_reference + ':' + reference).encode('ascii')).hexdigest()
                native.remaining_incidents = 0
                scope = SessionModuleControlScope(_MODULE_CONTROL_FACTORY)
                scope._collector, scope._state, scope._native, scope._lease = self, state, native, lease
                scope._original, scope._receipt, scope._result = scope, None, None
                state.module_controls[reference] = scope
                self._scopes[native.storage_reference] = native
                state.pinned_scopes.add(native.storage_reference)
                return v.SessionModuleCaptureAdmission('ADMITTED', scope, None)
        except (dv.DiagnosticsContractError, v.SessionContractError):
            return v.SessionModuleCaptureAdmission('REJECTED', None, 'SESSION_RETENTION_REJECTED')

    def _session_begin(self, state, gate, command, before, origin_refs, terminal):
        from . import session_values as v
        reference = command.request.request_reference if type(command) in v._COMMANDS else "session:invalid"
        scope = None
        previous_charge = self._charging_scope
        try:
            with self._session_io():
                v.revalidate_value(command)
                v.revalidate_value(before)
                if type(terminal) is not bool or type(origin_refs) is not tuple or not 1 <= len(origin_refs) <= 4 or len(set(origin_refs)) != len(origin_refs):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                if state.frozen or state.main_origin is None or before != command.request.expected_snapshot or before.binding != state.binding or command.request.session_reference != state.binding.session_reference:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
                if terminal and (type(command) not in (v.SessionHaltRequest, v.SessionResolutionRequest, v.SessionRecoveryRequest) or state.main_previous is None):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                for ref in origin_refs:
                    sv.InputEvidence.validate_reference(ref)
                    if ref != state.binding.initial_assessment_reference and ref not in self._acks:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE")
                current = state.binding.policy_binding.policy_version == '1.1.0'
                budget = ((4, 688128, 512, 458752) if current else (4, 655360, 512, 425984)) if terminal else (4, 327680, 512, 98304)
                scope = self._begin(reference, "SESSION_LIFECYCLE", reserved_events=budget[0], reserved_bytes=budget[1],
                    reserved_aliases=budget[2], reserved_supporting_bytes=budget[3], execution_gate=gate,
                    storage_reference="session:lifecycle:" + hashlib.sha256((state.binding.session_reference + ":" + reference).encode("ascii")).hexdigest())
                scope.session_state, scope.session_command, scope.terminal = state, command, terminal
                self._lifecycle_scopes[reference] = scope
                state.pinned_scopes.add(scope.storage_reference)
                projection = self._projection(state)
                self._charging_scope = scope
                projection.request(command)
                projection.snapshot(before)
                self._persist_health()
                self._check_gate(gate)
                if self._storage != "PROTECTED_VERIFIED":
                    raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
                return _SessionLifecycleScope(self, state, scope, command, terminal=terminal), v.SessionLifecycleCaptureAdmission(reference, "CONFIRMED", *budget, None)
        except (dv.DiagnosticsContractError, v.SessionContractError) as error:
            if scope is not None:
                scope.failed = getattr(error, "code", "DIAGNOSTICS_RECORD_NONCONFORMANT")
                return _SessionLifecycleScope(self, state, scope, command, terminal=terminal), v.SessionLifecycleCaptureAdmission(reference, "NOT_CONFIRMED", *budget, "CAPTURE_ADMISSION_UNCONFIRMED")
            return None, v.SessionLifecycleCaptureAdmission(reference, "REJECTED", 0, 0, 0, 0, "CAPTURE_ADMISSION_REJECTED")
        finally:
            self._charging_scope = previous_charge

    def _session_append(self, wrapper, record):
        from . import session_values as v
        reference = record.diagnostic_reference if type(record) is v.LifecycleRecord else wrapper.scope.reference
        try:
            with self._session_io():
                v.revalidate_value(record)
                if type(record) is not v.LifecycleRecord or record.cause.request_reference != wrapper.scope.reference or record.cause.expected_snapshot_reference != wrapper.command.request.expected_snapshot.snapshot_reference:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
                return self._append(wrapper.scope, record)
        except (dv.DiagnosticsContractError, v.SessionContractError):
            wrapper.scope.failed = wrapper.scope.failed or "DIAGNOSTICS_RECORD_NONCONFORMANT"
            return sv.CaptureReceipt(reference, "NOT_CONFIRMED")

    def _session_resolution(self, wrapper, observation):
        from . import session_values as v
        previous_charge = self._charging_scope
        try:
            with self._session_io():
                v.revalidate_value(observation)
                if type(observation) is not v.SessionResolutionObservation or observation.request != wrapper.command.request or wrapper.scope.finished:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                self._check_gate(wrapper.scope.execution_gate)
                self._charging_scope = wrapper.scope
                ref = self._projection(wrapper.state).resolution(observation, wrapper.command)
                context = _context(resolution_evidence_reference=ref)
                outcome = {"RESOLVED": "COMPLETED", "REFUSED": "REJECTED", "UNCONFIRMED": "NOT_CONFIRMED"}[observation.status]
                receipt = self._session_control_event(wrapper.scope, observation.resolution_reference, "CONTAINMENT_RESOLUTION_RECORDED", context, outcome)
                if receipt.status == "CONFIRMED" and observation.status == "RESOLVED":
                    post = observation.actual_post_assessment
                    child = None if post is None else self._scopes.get(post.assessment_binding.assessment_reference)
                    if child is None or child.budget_parent != wrapper.scope.storage_reference or child.failed or not child.finished or type(post) is not sv.StateAssessment:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                    self._attached(post.emitted_diagnostics)
                    wrapper.state.resolution_previous[observation.resolution_reference] = wrapper.state.main_root
                    wrapper.state.episode_origin = post
                    wrapper.state.main_root = post.emitted_diagnostics[0].diagnostic_reference
                    wrapper.state.main_previous = post.emitted_diagnostics[-1].diagnostic_reference
                return receipt
        except (dv.DiagnosticsContractError, v.SessionContractError):
            wrapper.scope.failed = wrapper.scope.failed or "DIAGNOSTICS_COMPLETION_MISMATCH"
            return sv.CaptureReceipt(getattr(observation, "resolution_reference", wrapper.scope.reference), "NOT_CONFIRMED")
        finally:
            self._charging_scope = previous_charge

    def _session_control_event(self, scope, reference, template, context, outcome):
        observed = self._observe_clock(execution_gate=scope.execution_gate)
        sequence = self._next_sequence
        event = dv.DiagnosticEvent(self._alias(reference), sequence, observed, "SESSION_LIFECYCLE", "ACTION_OBSERVED", template,
            self.identity.session_reference, self._alias(scope.reference), None, None, None, None, outcome,
            observed.monotonic_nanoseconds - scope.first_clock.monotonic_nanoseconds, None, context, None, ())
        payload = _encode(event)
        if len(self._events) + len(self._unconfirmed_events) >= 1024 or sequence > 1023:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
        self._consume_reservation(scope, len(payload), event=True)
        self._next_sequence += 1
        try:
            self._commit("commit_event", sequence, payload)
        except dv.DiagnosticsContractError:
            self._unconfirmed_events[sequence] = event
            self._used += len(payload)
            raise
        self._events.append(event)
        self._used += len(payload)
        try:
            self._check_gate(scope.execution_gate)
        except dv.DiagnosticsContractError:
            scope.late_indices.append(sequence)
            self._increment("RETAINED")
            raise
        scope.references.append(reference)
        scope.indices.append(sequence)
        self._increment("ACCEPTED")
        self._increment("RETAINED")
        self._persist_health()
        try:
            self._check_gate(scope.execution_gate)
        except dv.DiagnosticsContractError:
            scope.references.pop(); scope.indices.pop()
            scope.late_indices.append(sequence)
            raise
        if self._storage != "PROTECTED_VERIFIED":
            scope.references.pop(); scope.indices.pop()
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
        return sv.CaptureReceipt(reference, "CONFIRMED")

    def _session_finish(self, wrapper, result):
        from . import session_values as v
        scope = wrapper.scope
        try:
            with self._session_io():
                if scope.completion_response is not None:
                    return v.SessionLifecycleCompletion(scope.reference, "INCOMPLETE", tuple(scope.references), "CAPTURE_COMPLETION_REJECTED")
                scope.finished, scope.final_observation_pending = True, True
                v.revalidate_value(result)
                if type(wrapper) is _SessionDenialScope:
                    if type(result) is not v.SessionDeniedAttempt or result.frozen_snapshot != wrapper.snapshot or result.denial_ordinal != wrapper.ordinal or result.completion_observation is not None:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                    if result.attempted_record is not None and tuple(scope.hashes) != (_fingerprint(result.attempted_record),):
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                else:
                    if type(result) is not v.SessionOperationResult or result.request != wrapper.command or result.completion_observation is not None:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                    if v.raw_business_size(result) > v.MAX_RAW_BUSINESS_BYTES:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RAW_PACKET_LIMIT")
                    for item in result.confirmed_lifecycle_records:
                        self._attached((sv.DiagnosticEmission(item.diagnostic_reference, item.envelope),))
                    for ref in scope.child_operations:
                        child = self._scopes[ref]
                        if not child.finished or child.failed:
                            raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                        wrapper.state.pinned_scopes.add(ref)
                        wrapper.state.pinned_support.update(child.support_keys)
                    if result.pending_lifecycle_record is not None:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                if scope.failed:
                    raise dv.DiagnosticsContractError(scope.failed)
                self._persist_health()
                if self._storage != "PROTECTED_VERIFIED":
                    raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
                response = v.SessionLifecycleCompletion(scope.reference, "COMPLETE", tuple(scope.references), None)
                scope.completed_result, scope.completion_response = result, response
                return response
        except (dv.DiagnosticsContractError, v.SessionContractError) as error:
            response = v.SessionLifecycleCompletion(scope.reference, "INCOMPLETE", tuple(scope.references),
                "CAPTURE_COMPLETION_UNCONFIRMED" if getattr(error, "code", "").startswith("STORAGE") else "CAPTURE_COMPLETION_REJECTED")
            if scope.completion_response is None:
                scope.finished, scope.final_observation_pending = True, True
                scope.completed_result, scope.completion_response = result, response
            return response

    def observe_session_result(self, handle, final_result, *, actual_result=None):
        from . import session_values as v
        state = self._session_state(handle)
        reference = None
        scope = None
        previous_charge = self._charging_scope
        try:
            with self._session_io():
                descriptor = final_result if type(final_result) is v.SessionRawBusinessFailure else None
                if descriptor is not None:
                    v.revalidate_value(descriptor)
                    if type(actual_result) is not v.SessionOperationResult:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                    result = actual_result
                else:
                    if actual_result is not None or type(final_result) is not v.SessionOperationResult:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                    result = final_result
                v.revalidate_value(result)
                reference = result.request.request.request_reference
                if result.before.binding != state.binding or reference in state.observed or len(state.observed) >= 18:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
                scope = self._lifecycle_scopes.get(reference)
                if scope is not None:
                    if scope.producer != "SESSION_LIFECYCLE" or not scope.finished or result.completion_observation != scope.completion_response:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                else:
                    # A genuine rejected admission has no event/canonical scope.
                    # Reserve its safe sidecar explicitly, without issuing ACK.
                    if result.completion_observation is not None or result.confirmed_lifecycle_records or result.attempted_lifecycle_records:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISSING")
                    if result.admission.status != "REJECTED":
                        if result.failure_detail is None or result.session_effects_performed or result.publication is not None:
                            raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISSING")
                        if result.origin_assessment is not None:
                            origin = result.origin_assessment
                            child = self._scopes.get(origin.assessment_binding.assessment_reference)
                            if child is None or child.storage_reference not in state.pinned_scopes or not child.finished or child.completed_hash != hashlib.sha256(self._raw_bytes(origin, child)).hexdigest() or result.origin_completion_observation != child.completion_response:
                                raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                        if result.recovery_result is not None:
                            self._session_recovery_failure(state, result)
                    scope = self._begin(reference, "SESSION_LIFECYCLE", reserved_events=0, reserved_bytes=327680,
                        reserved_aliases=512, reserved_supporting_bytes=98304,
                        storage_reference="session:lifecycle:" + hashlib.sha256((state.binding.session_reference + ":" + reference).encode("ascii")).hexdigest())
                    self._lifecycle_scopes[reference] = scope
                    scope.session_state = state
                    scope.finished, scope.final_observation_pending = True, True
                state.observed.add(reference)
                state.results[reference] = result
                state.pinned_scopes.add(scope.storage_reference)
                scope.audit_cleanup_allowed = True
                self._charging_scope = scope
                self._projection(state).components(result, final=True, descriptor=descriptor)
                state.pinned_support.update(scope.support_keys)
                self._select_support(state, state.pinned_support)
                self._persist_health()
                return self._session_receipt(state, "FINAL_RESULT")
        except (dv.DiagnosticsContractError, v.SessionContractError):
            return self._session_receipt(state, "FINAL_RESULT", "SESSION_RETENTION_INCOMPLETE")
        finally:
            if scope is not None:
                scope.audit_cleanup_allowed = False
                if not getattr(scope, "terminal", False):
                    scope.final_observation_pending = False
            self._charging_scope = previous_charge

    def _session_recovery_failure(self, state, result):
        """Correlate interrupted or unadmitted N2 truth without a main member."""
        from . import recovery_values as rv
        packet = result.recovery_result
        reference = result.request.request.request_reference
        if type(packet) is not rv.RecoveryFailure or packet.operation_context.operation_reference != reference or packet.origin_assessment != result.origin_assessment or packet.source_binding != state.binding.recovery_binding:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        native = self._scopes.get(reference)
        if native is None:
            if packet.completion_observation is not None or packet.emitted_diagnostics or packet.steps or packet.post_assessments or packet.action_decisions:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
            return
        if not _is_issued_recovery_scope(native, self, native.execution_gate, reference) or native.storage_reference not in state.pinned_scopes or not native.finished or native.completed_result is None or packet.completion_observation != native.completion_response:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
        fields = ("operation_context", "origin_assessment", "origin_validation", "source_binding", "registry_binding",
            "route_authorization", "steps", "post_assessments", "policy_attempts", "action_decisions", "emitted_diagnostics",
            "candidate_state", "directive", "normalization_preparation", "correction_observation", "registry_snapshot", "registry_validation")
        if any(getattr(packet, name) != getattr(native.completed_result, name) for name in fields):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
        if tuple(hashlib.sha256(self._raw_bytes(record, native)).hexdigest() for record in packet.emitted_diagnostics) != tuple(native.hashes):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
        self._attached(tuple(sv.DiagnosticEmission(record.diagnostic_reference, record.envelope) for record in packet.emitted_diagnostics))
        state.recovery_results[reference] = packet

    def pin_history(self, handle, history):
        from . import session_values as v
        state = self._session_state(handle)
        try:
            with self._session_io():
                v.revalidate_value(history)
                if type(history) is not v.SessionHistory or history.binding != state.binding or state.frozen:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
                for result in history.command_results:
                    if state.results.get(result.request.request.request_reference) != result:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                for ref in state.pinned_scopes:
                    state.pinned_support.update(self._scopes[ref].support_keys)
                self._select_support(state, state.pinned_support)
                return self._session_receipt(state, "PIN")
        except (dv.DiagnosticsContractError, v.SessionContractError):
            return self._session_receipt(state, "PIN", "SESSION_RETENTION_INCOMPLETE")

    def pin_session_module_history(self, handle, history):
        from . import session_values as v
        state = self._session_state(handle)
        failure = None
        try:
            v.revalidate_value(history)
            if type(history) is not v.SessionModuleHistory or history.session_binding_reference != state.binding.binding_reference:
                raise dv.DiagnosticsContractError('DIAGNOSTICS_ORIGIN_MISMATCH')
            with self._session_io():
                for result, observation in zip(history.results, history.control_observations):
                    ref = result.command.request_reference
                    actual = state.module_results.get(ref)
                    if observation is None:
                        if result.admission.status != 'REJECTED':
                            raise dv.DiagnosticsContractError('DIAGNOSTICS_COMPLETION_MISMATCH')
                        continue
                    if actual is None or actual[0] != result or observation.supporting_reference != actual[1]:
                        raise dv.DiagnosticsContractError('DIAGNOSTICS_COMPLETION_MISMATCH')
                for reference in state.pinned_scopes:
                    state.pinned_support.update(self._scopes[reference].support_keys)
                self._select_support(state, state.pinned_support)
        except (dv.DiagnosticsContractError, v.SessionContractError):
            failure = 'SESSION_RETENTION_INCOMPLETE'
            self._mark_failure('DIAGNOSTICS_COMPLETION_MISMATCH')
        return v.SessionModuleRetentionReceipt(state.binding.session_reference, None, 'PIN',
            'CONFIRMED' if failure is None else 'NOT_CONFIRMED', 'COMPLETE_SPECIFIED_SAFE_GRAPH' if failure is None else 'PARTIAL',
            len(state.pinned_support), state.module_history_reference, failure)

    def _module_history_support(self, state, history):
        from . import diagnostic_session_values as safe
        projection = self._projection(state)
        cutover = history.pending_cutover
        cutover_alias = None
        if cutover is not None:
            source = self._scopes.get(cutover.actual_origin_reference)
            operation = _ReferenceDiagnostics._modules(self).scopes.get(cutover.actual_module_operation_reference)
            cutover_alias = projection.key('SESSION_MODULE_CUTOVER', cutover)
            node = safe.SafeSessionModuleCutoverEvidence(evidence_reference=cutover_alias,
                session_binding_reference=projection.binding(state.binding), session_reference=projection.alias(state.binding.session_reference),
                request_reference=projection.alias(cutover.request_reference), lease_reference=projection.alias(cutover.lease_reference),
                generation=cutover.admitted_generation, before_snapshot_reference=projection.alias(cutover.before_snapshot_reference),
                active_snapshot_reference=projection.alias(cutover.active_snapshot_reference), cutover_snapshot_reference=projection.alias(cutover.cutover_snapshot_reference),
                actual_origin_evidence_reference=None if source is None or source.completed_result is None else self._assessment_support(source.completed_result),
                actual_module_operation_reference=None if operation is None else operation._projection.operation_alias, phase=cutover.phase)
            try:
                self._supporting('SESSION_MODULE_CUTOVER', cutover_alias, node)
            finally:
                if cutover_alias in self._support['SESSION_MODULE_CUTOVER'] or ('SESSION_MODULE_CUTOVER', cutover_alias) in self._unconfirmed_support:
                    state.pinned_support.add(('SESSION_MODULE_CUTOVER', cutover_alias))
        links, controls = [], []
        for result, receipt in zip(history.results, history.control_observations):
            actual = state.module_results.get(result.command.request_reference)
            if actual is not None:
                links.append(actual[1])
            controls.append(None if receipt is None else dict(request_reference=projection.alias(receipt.request_reference),
                status=receipt.status, coverage=receipt.coverage, supporting_reference=receipt.supporting_reference, failure_code=receipt.failure_code))
        state.module_history_reference = projection.put('SESSION_MODULE_HISTORY', safe.SafeSessionModuleHistoryEvidence, history,
            session_binding_reference=projection.binding(state.binding), session_reference=projection.alias(state.binding.session_reference),
            member_link_references=tuple(links), control_observations=tuple(controls), frozen=history.frozen,
            cutover_generation=history.cutover_generation, pending_cutover_evidence_reference=cutover_alias)
        return state.module_history_reference

    def freeze_terminal(self, handle, history, actual_terminal_publication):
        from . import session_values as v
        from . import diagnostic_session_values as safe
        state = self._session_state(handle)
        scope = None
        previous_charge = self._charging_scope
        try:
            with self._session_io():
                v.revalidate_value(history)
                v.revalidate_value(actual_terminal_publication)
                if type(history) is not v.SessionHistory or type(actual_terminal_publication) is not v.SessionPublication or history.binding != state.binding or not history.frozen or history.terminal_snapshot is None:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
                if state.frozen:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
                reference = actual_terminal_publication.request_reference
                result = state.results.get(reference)
                scope = self._lifecycle_scopes.get(reference)
                if actual_terminal_publication.status != "COMMITTED" or actual_terminal_publication.requested_mode != "SAFE_HALT" or result is None or result not in history.command_results or result.publication != actual_terminal_publication or scope is None or not scope.finished or reference not in state.observed:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                if v.raw_business_size(history) > v.MAX_RAW_BUSINESS_BYTES:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RAW_PACKET_LIMIT")
                # Seal before the first index IO. Failed/unknown writes retain
                # their selected roots and cannot be retried as a new index.
                state.frozen = True
                scope.audit_cleanup_allowed = True
                self._charging_scope = scope
                projection = self._projection(state)
                module_history = None
                if history.module_history is not None:
                    module_history = self._module_history_support(state, history.module_history)
                terminal_closure = None
                halt_records = tuple(item for item in result.confirmed_lifecycle_records if item.envelope.diagnostic_kind == "SAFE_HALT")
                if halt_records:
                    halt = halt_records[-1]
                    closure = halt.payload.full_diagnostic_chain[-1]
                    if type(closure) is not v.SessionTerminalChainClosure:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                    terminal_closure = projection.put("SESSION_TERMINAL_CLOSURE", safe.SafeSessionTerminalClosureEvidence, closure,
                        request_evidence_reference=projection.request(result.request),
                        bridge_record_reference=None if closure.bridge_record is None else projection.alias(closure.bridge_record.diagnostic_reference),
                        terminal_diagnostic_reference=projection.alias(closure.terminal_emission.diagnostic_reference),
                        terminal_envelope=self._safe_envelope(closure.terminal_emission.envelope, "RECOVERY_ACTION_RECORDED"),
                        actual_terminal_publication_evidence_reference=projection.publication(closure.actual_terminal_publication, result.request, result.authority_observation, result.cause),
                        assurance="ACTUAL_FINAL_HALT_LINK_NONRECURSIVE_COMPLETE_TYPED_CLOSURE")
                selected_scopes = {history.main_assessment.assessment_binding.assessment_reference}
                selected_scopes.update(self._lifecycle_scopes[item.request.request.request_reference].storage_reference
                    for item in history.command_results if item.request.request.request_reference in self._lifecycle_scopes)
                selected_scopes.update(item.operation_context.operation_reference for item in history.recovery_results)
                selected_scopes.update(item.child_origin_assessment_reference for item in history.child_links)
                if history.module_history is not None:
                    cutover = history.module_history.pending_cutover
                    if cutover is not None:
                        if cutover.actual_origin_reference is not None:
                            selected_scopes.add(cutover.actual_origin_reference)
                        if cutover.actual_module_operation_reference is not None:
                            selected_scopes.add(cutover.actual_module_operation_reference)
                    for module_result in history.module_history.results:
                        control = state.module_controls.get(module_result.command.request_reference)
                        if control is not None:
                            selected_scopes.add(control._native.storage_reference)
                        if module_result.origin_diagnosis is not None:
                            selected_scopes.add(module_result.origin_diagnosis.assessment_binding.assessment_reference)
                        if module_result.module_capture is not None:
                            selected_scopes.add(module_result.command.request_reference)
                for ref in tuple(selected_scopes):
                    member = self._scopes.get(ref)
                    if member is not None:
                        selected_scopes.update(member.child_operations)
                # The sealed index selects actual history, not later denial or
                # interrupted-operation audit. All audit remains purge-pinned.
                seeds = {key for ref in selected_scopes if ref in self._scopes for key in self._scopes[ref].support_keys}
                seeds.add(("SESSION_BINDING", projection.binding(history.binding)))
                if terminal_closure is not None:
                    seeds.add(("SESSION_TERMINAL_CLOSURE", terminal_closure))
                if module_history is not None:
                    seeds.add(('SESSION_MODULE_HISTORY', module_history))
                selected = self._select_support(state, seeds)
                selected = {key for key in selected if key[0] not in ("SESSION_HISTORY", "SESSION_HISTORY_PAGE", "SESSION_DENIED")}
                history_alias = projection.key("SESSION_HISTORY", history)
                selected.add(("SESSION_HISTORY", history_alias))
                current = state.binding.policy_binding.policy_version == '1.1.0'
                if len(selected) > (2622 if current else 2504):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
                indices = {index for ref in selected_scopes if ref in self._scopes for index in (*self._scopes[ref].indices, *self._scopes[ref].late_indices)}
                unknown_indices = {self._scopes[ref].attempted_index for ref in selected_scopes if ref in self._scopes and self._scopes[ref].attempted_index in self._unconfirmed_events}
                records = []
                for index in sorted(indices | unknown_indices):
                    event = next((item for item in self._events if item.local_sequence == index), self._unconfirmed_events.get(index))
                    if event is None:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                    records.append(safe.SafeHistoryRecordReference(event.diagnostic_reference or event.event_id, event.event_id,
                        index, "UNKNOWN" if index in unknown_indices else "CONFIRMED"))
                reference_cls = safe.SafeCurrentSessionSupportingReference if current else safe.SafeSupportingReference
                supporting = tuple(reference_cls(kind, alias) for kind, alias in sorted(selected))
                page_count = max((len(records) + 63) // 64, (len(supporting) + 63) // 64)
                if page_count > (41 if current else 40):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
                pages = []
                for index in range(page_count):
                    alias = self._alias("session:index:" + hashlib.sha256(history.history_reference.encode("ascii")).hexdigest() + ":" + str(index))
                    page_cls = safe.SafeCurrentSessionHistoryPage if current else safe.SafeSessionHistoryPage
                    page_context = {'session_policy_version': '1.1.0'} if current else {}
                    node = page_cls(alias, history_alias, index, tuple(records[index*64:(index+1)*64]), supporting[index*64:(index+1)*64], **page_context)
                    state.pinned_support.add(("SESSION_HISTORY_PAGE", alias))
                    pages.append(self._supporting("SESSION_HISTORY_PAGE", alias, node))
                by_kind = {kind: tuple(alias for selected_kind, alias in sorted(selected) if selected_kind == kind) for kind in self._support}
                assessments = tuple(self._projection(state).assessment(item.actual_post_assessment) for item in history.command_results if item.actual_post_assessment is not None)
                main_assessment = projection.assessment(history.main_assessment)
                history_cls = safe.SafeCurrentSessionHistoryEvidence if current else safe.SafeSessionHistoryEvidence
                history_context = {'module_history_evidence_reference': module_history, 'session_policy_version': '1.1.0'} if current else {}
                node = history_cls(history_alias, projection.binding(history.binding), main_assessment,
                    None, None, by_kind["SESSION_CONTEXT"], by_kind["SESSION_PUBLICATION"], by_kind["LIFECYCLE"],
                    None if not history.pending_lifecycle_records else projection.lifecycle(history.pending_lifecycle_records[-1], result.request, "NOT_CONFIRMED"),
                    tuple(pages), len(indices), len(unknown_indices), len(history.attempted_lifecycle_records), len(selected), True,
                    "STORAGE_UNCERTAIN" if unknown_indices or selected & self._unconfirmed_support.keys() else "PARTIAL" if result.completion_observation is None or result.completion_observation.status != "COMPLETE" else "COMPLETE_SPECIFIED_SAFE_GRAPH",
                    "RAW_BUSINESS_PACKETS_REQUEST_REASON_CANONICAL_FREE_NOTES", by_kind["SESSION_REQUEST"], by_kind["SESSION_AUTHORITY"], by_kind["SESSION_CAUSE"],
                    by_kind["SESSION_BOUNDARY"], by_kind["SESSION_COMMAND"], by_kind["SESSION_FAILURE"], by_kind["SESSION_RESOLUTION"],
                    tuple(projection.alias(item.operation_context.operation_reference) for item in history.recovery_results), by_kind["SESSION_LINK"],
                    None, tuple(dict.fromkeys(item for item in (main_assessment, *assessments) if item is not None)), terminal_closure, **history_context)
                state.pinned_support.add(("SESSION_HISTORY", history_alias))
                self._supporting("SESSION_HISTORY", history_alias, node)
                state.pinned_support.update(scope.support_keys)
                self._select_support(state, state.pinned_support)
                state.freeze_receipt = self._session_receipt(state, "FREEZE", "SESSION_RETENTION_INCOMPLETE" if node.coverage == "PARTIAL" else None)
                return state.freeze_receipt
        except (dv.DiagnosticsContractError, v.SessionContractError):
            state.freeze_receipt = self._session_receipt(state, "FREEZE", "SESSION_RETENTION_INCOMPLETE")
            return state.freeze_receipt
        finally:
            if scope is not None:
                scope.audit_cleanup_allowed = False
                scope.final_observation_pending = False
            self._charging_scope = previous_charge

    def denial_capture(self, handle, frozen_snapshot, *, denial_ordinal):
        from . import session_values as v
        state = self._session_state(handle)
        with self._session_io():
            v.revalidate_value(frozen_snapshot)
            if type(frozen_snapshot) is not v.SessionSnapshot or frozen_snapshot.binding != state.binding or not frozen_snapshot.terminal_latched or type(denial_ordinal) is not int or not 1 <= denial_ordinal <= 16 or denial_ordinal in state.denials:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
            reference = state.binding.session_reference[:160] + ":denial:" + str(denial_ordinal)
            scope = self._begin(reference, "SESSION_LIFECYCLE", denial=True, reserved_events=1, reserved_bytes=270336, reserved_aliases=64)
            scope.session_state = state
            state.denials[denial_ordinal] = scope
            state.pinned_scopes.add(reference)
            return _SessionDenialScope(self, state, scope, frozen_snapshot, denial_ordinal)

    def observe_session_denial(self, handle, final_denial):
        from . import session_values as v
        from .diagnostic_session_values import SafeSessionDeniedEvidence
        state = self._session_state(handle)
        scope = None
        previous_charge = self._charging_scope
        try:
            with self._session_io():
                v.revalidate_value(final_denial)
                if type(final_denial) is not v.SessionDeniedAttempt or final_denial.denial_ordinal is None or final_denial.denial_ordinal in state.denial_observed:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
                scope = state.denials.get(final_denial.denial_ordinal)
                if scope is None or not scope.finished or final_denial.completion_observation != scope.completion_response:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                state.denial_observed.add(final_denial.denial_ordinal)
                self._charging_scope = scope
                projection = self._projection(state)
                projection.put("SESSION_DENIED", SafeSessionDeniedEvidence, final_denial,
                    session_binding_reference=projection.binding(state.binding), snapshot_evidence_reference=projection.snapshot(final_denial.frozen_snapshot),
                    audit_reference=projection.alias(final_denial.audit_reference), request_reference=projection.alias(final_denial.request_reference),
                    request_observation=final_denial.request_observation, reason_code=final_denial.reason_code,
                    record_reference=None if final_denial.attempted_record is None else projection.alias(final_denial.attempted_record.diagnostic_reference),
                    capture_status=final_denial.capture_status, omitted_fields="REQUEST_REASON", denial_ordinal=final_denial.denial_ordinal,
                    completion_observation=projection.completion(final_denial.completion_observation))
                state.pinned_support.update(scope.support_keys)
                self._select_support(state, state.pinned_support)
                return self._session_receipt(state, "FINAL_RESULT")
        except (dv.DiagnosticsContractError, v.SessionContractError):
            return self._session_receipt(state, "FINAL_RESULT", "SESSION_RETENTION_INCOMPLETE")
        finally:
            if scope is not None:
                scope.final_observation_pending = False
            self._charging_scope = previous_charge

    def _attached(self, emissions):
        for emission in emissions:
            witness = self._acks.get(emission.diagnostic_reference)
            if witness is None:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE")
            if witness.emission_sha256 != _fingerprint(emission):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        return True

    def _recovery_begin(self, origin, reference, denial, execution_gate=None):
        if type(origin) is not sv.StateAssessment:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "ORIGINAL_ASSESSMENT")
        sv.InputEvidence.validate_reference(reference)
        if len(reference) > 192:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_VALUE_INVALID")
        references = tuple(item.diagnostic_reference for item in origin.emitted_diagnostics)
        with self._lock:
            scope = None
            try:
                self._attached(origin.emitted_diagnostics)
                original_scope = self._scopes.get(origin.assessment_binding.assessment_reference)
                if original_scope is None or not original_scope.finished or original_scope.failed:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE")
                if denial != (origin.system_state_class == "SAFE_HALT" and origin.recovery_category == "TERMINAL_NO_RECOVERY"):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                scope = self._begin(reference, "RECOVERY_ENGINE", original=origin,
                    reserved_events=1 if denial else 768, reserved_bytes=270336 if denial else 31588352,
                    reserved_aliases=64 if denial else 5931, denial=denial, execution_gate=execution_gate)
                self._assessment_support(origin)
                self._persist_health()
                self._check_gate(execution_gate)
                if self._storage != "PROTECTED_VERIFIED":
                    raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
                return scope, dv.RecoveryAdmissionReceipt("CONFIRMED", reference,
                    origin.assessment_binding.assessment_reference, references,
                    scope.reserved_events, scope.reserved_bytes, None)
            except dv.DiagnosticsContractError as error:
                if scope is not None and execution_gate is not None:
                    scope.failed = error.code
                    self._mark_failure(error.code)
                    return scope, dv.RecoveryAdmissionReceipt("NOT_CONFIRMED", reference,
                        origin.assessment_binding.assessment_reference, references, 0, 0, error.code)
                if scope is not None:
                    scope.finished, scope.failed = True, error.code
                self._mark_failure(error.code)
                return None, dv.RecoveryAdmissionReceipt("REJECTED", reference,
                    origin.assessment_binding.assessment_reference, references, 0, 0, error.code)

    def _safe_envelope(self, envelope, template):
        return dv.SafeDiagnosticEnvelope(envelope.diagnostic_kind, envelope.severity,
            envelope.stage, envelope.disposition, self._alias(envelope.subject_reference),
            None if envelope.parent_diagnostic_reference is None else self._alias(envelope.parent_diagnostic_reference),
            self._alias(envelope.chain_root_reference), envelope.rule_ids,
            dv.message_text(template), (dv.message_text("UNTRUSTED_PROSE_OMITTED"),))

    def _validate_chain(self, scope, emission, phase):
        envelope = emission.envelope
        previous = scope.last_envelope
        if emission.diagnostic_reference in self._acks:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED", "CHAIN")
        if envelope.subject_reference != (scope.original.subject_reference if scope.original else envelope.subject_reference):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
        if scope.producer == "STATE_MODEL":
            if len(scope.indices) >= 2 or envelope.stage != ("DETECTION" if not scope.indices else "CLASSIFICATION") or any(rule not in sv.ASSESSMENT_RULE_IDS for rule in envelope.rule_ids):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CANONICAL_ENVELOPE")
        elif scope.producer == "NORMALIZATION":
            if len(scope.indices) >= 2 or phase != ("COMPUTATION" if not scope.indices else "POST_VALIDATION"):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "EXPECTED_STEP")
            if not scope.indices:
                if envelope.parent_diagnostic_reference != scope.original.last_diagnostic_reference or envelope.chain_root_reference != scope.original.chain_root_reference:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
            elif previous.disposition != "PENDING":
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "EXPECTED_STEP")
        elif scope.denial:
            from . import recovery_values as rv
            if scope.indices or envelope.stage != "DETECTION" or envelope.disposition != "BLOCKED" or envelope.severity != "CRITICAL" or envelope.diagnostic_kind != "STATE_VALIDITY" or envelope.parent_diagnostic_reference is not None or envelope.chain_root_reference != emission.diagnostic_reference or envelope.rule_ids != ("ASH-STATE-GENERAL-001", "ASH-RECOVERY-ACTION-001"):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
        elif scope.producer == "SESSION_LIFECYCLE":
            state = scope.session_state
            predecessor = self._acks.get(state.main_previous)
            prior = next((event.envelope for event in self._events if predecessor is not None and event.local_sequence == predecessor.confirmed_sequence), None)
            if prior is None or envelope.parent_diagnostic_reference != state.main_previous or envelope.chain_root_reference != state.main_root or self._alias(envelope.subject_reference) != prior.subject_reference:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH", "CHAIN")
            allowed = {"RECOVERY": ("RECOVERY", ("CLASSIFICATION", "RECOVERY")),
                "CONTAINMENT": ("ESCALATION", ("RECOVERY",)), "SAFE_HALT": ("TERMINAL", ("RECOVERY", "ESCALATION"))}
            expected = allowed.get(envelope.diagnostic_kind)
            if expected is None or envelope.stage != expected[0] or prior.stage not in expected[1] or prior.disposition == "TERMINAL":
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
            if envelope.diagnostic_kind == "SAFE_HALT" and not scope.terminal or scope.terminal and envelope.diagnostic_kind == "CONTAINMENT":
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
            severity = ("INFO", "WARNING", "ERROR", "CRITICAL")
            if severity.index(envelope.severity) < severity.index(prior.severity):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
            return
        else:
            if envelope.diagnostic_kind not in ("RECOVERY", "FALLBACK") or envelope.stage not in ("RECOVERY", "ESCALATION"):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CANONICAL_ENVELOPE")
            if not scope.indices:
                if envelope.parent_diagnostic_reference != scope.original.last_diagnostic_reference or envelope.chain_root_reference != scope.original.chain_root_reference:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
        if previous is not None:
            if previous.disposition == "TERMINAL" or previous.stage == "TERMINAL":
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
            if envelope.parent_diagnostic_reference != scope.references[-1] or self._alias(envelope.chain_root_reference) != previous.chain_root_reference or self._alias(envelope.subject_reference) != previous.subject_reference:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
            severity = ("INFO", "WARNING", "ERROR", "CRITICAL")
            if severity.index(envelope.severity) < severity.index(previous.severity):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
        elif scope.producer == "STATE_MODEL" and (envelope.parent_diagnostic_reference is not None or envelope.chain_root_reference != emission.diagnostic_reference):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")

    def _append(self, scope, record):
        with self._lock:
            self._charging_scope = scope
            emission = None
            try:
                self._check_gate(scope.execution_gate)
                if scope.execution_gate is not None and self._io_depth:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
                if scope.finished or scope.failed:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
                raw = self._raw_bytes(record, scope)
                if len(raw) > 33554432:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RAW_PACKET_LIMIT")
                if scope.producer == "STATE_MODEL":
                    if type(record) is not sv.DiagnosticEmission:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                    emission, phase, template, context = record, record.envelope.stage, "DIAGNOSIS_RECORDED" if not scope.indices else "CLASSIFICATION_RECORDED", _context()
                elif scope.producer == "NORMALIZATION":
                    if type(record) is not nv.NormalizationDiagnosticRecord:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                    emission, phase = record.emission, record.phase
                    template = "NORMALIZATION_COMPUTED" if phase == "COMPUTATION" else "POST_VALIDATION_RECORDED"
                    context = self._diagnosis_context(record.state_validity_diagnostic)
                    if record.step is not None:
                        context = self._context_update(context, before_state=record.step.input_state.signature,
                            codeword=record.step.codeword.signature, after_state=record.step.actual_state.signature,
                            actual_state=record.step.actual_state.signature, step_index=record.step.step_index)
                elif scope.producer == "SESSION_LIFECYCLE":
                    from . import session_values as session
                    from . import recovery_values as rv
                    if scope.denial:
                        if type(record) is not sv.DiagnosticEmission:
                            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                        emission, phase, template, context = record, "DETECTION", "RECOVERY_ACTION_RECORDED", _context()
                    else:
                        if type(record) is not session.LifecycleRecord:
                            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                        payload = record.payload
                        if payload.original_diagnostic != scope.session_state.episode_origin.state_validity_diagnostic or type(payload) is rv.RecoveryDiagnostic and (payload.steps or payload.original_state_class != scope.session_state.episode_origin.system_state_class or payload.recovery_category != scope.session_state.episode_origin.recovery_category):
                            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
                        emission = sv.DiagnosticEmission(record.diagnostic_reference, record.envelope)
                        phase, template = record.envelope.stage, "RECOVERY_ACTION_RECORDED"
                        lifecycle = self._projection(scope.session_state).lifecycle(record, scope.session_command, "NOT_CONFIRMED")
                        context = _context(proof_evidence_reference=lifecycle)
                else:
                    from . import recovery_values as rv
                    if type(record) is not rv.RecoveryRecord:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                    emission = sv.DiagnosticEmission(record.diagnostic_reference, record.envelope)
                    phase, template = "RECOVERY", "RECOVERY_ACTION_RECORDED"
                    context = self._recovery_context(scope, record.payload)
                    if scope.denial and (record.record_kind != "OPERATION_DECISION" or record.payload.action != "HANDOFF" or record.payload.directive is None or record.payload.directive.requested_action != "REMAIN_SAFE_HALT"):
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                scope.attempted_reference, scope.attempted_hash = emission.diagnostic_reference, hashlib.sha256(raw).hexdigest()
                self._validate_chain(scope, emission, phase)
                observed = self._observe_clock(execution_gate=scope.execution_gate)
                if self._next_sequence >= 1 << 64:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_SEQUENCE_LIMIT")
                sequence = self._next_sequence
                scope.attempted_index = sequence if sequence <= 1023 else None
                if len(self._events) + len(self._unconfirmed_events) >= 1024 or len(scope.indices) >= (1 if scope.denial else 768 if scope.producer == "RECOVERY_ENGINE" else 4 if scope.producer == "SESSION_LIFECYCLE" else 2):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
                safe = self._safe_envelope(emission.envelope, template)
                redactions = (dv.RedactionEntry("SUMMARY", "UNTRUSTED_FREEFORM", 1),
                              dv.RedactionEntry("NOTES", "UNTRUSTED_FREEFORM", len(emission.envelope.notes)))
                from .recovery_values import PostAssessmentLink
                relation = None
                if type(scope.relation) is PostAssessmentLink:
                    relation = dv.CaptureRelation(self._alias(scope.relation.parent_operation_reference),
                        self._alias(scope.relation.parent_action_reference), self._alias(scope.relation.originating_chain_root_reference))
                event = dv.DiagnosticEvent(self._alias(emission.diagnostic_reference), sequence, observed,
                    scope.producer, "DIAGNOSTIC", template, self.identity.session_reference,
                    self._alias(scope.reference), self._action_alias(record), relation,
                    self._alias(emission.diagnostic_reference), safe, "OBSERVED",
                    observed.monotonic_nanoseconds - scope.first_clock.monotonic_nanoseconds, None,
                    context, None, redactions)
                payload = _encode(event)
                if len(payload) > 32768:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_EVENT_TOO_LARGE")
                if self._used + len(payload) > 33554432:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_BYTE_LIMIT")
                if scope.execution_gate is not None:
                    self._check_gate(scope.execution_gate)
                    self._consume_reservation(scope, len(payload), event=True)
                    self._next_sequence += 1
                    try:
                        self._commit("commit_event", sequence, payload)
                    except dv.DiagnosticsContractError:
                        self._unconfirmed_events[sequence] = event
                        self._used += len(payload)
                        raise
                else:
                    self._commit("commit_event", sequence, payload)
                self._events.append(event)
                self._used += len(payload)
                if scope.execution_gate is None:
                    self._consume_reservation(scope, len(payload), event=True)
                    self._next_sequence += 1
                try:
                    self._check_gate(scope.execution_gate)
                except dv.DiagnosticsContractError:
                    scope.late_indices.append(sequence)
                    self._increment("RETAINED")
                    raise
                scope.references.append(emission.diagnostic_reference)
                scope.indices.append(sequence)
                scope.hashes.append(hashlib.sha256(raw).hexdigest())
                # Safe envelope retains chain state; raw business record is not retained.
                scope.last_envelope = safe
                self._acks[emission.diagnostic_reference] = dv.PrivateAcknowledgmentWitness(
                    emission.diagnostic_reference, self.identity.build_id, self.identity.session_reference,
                    sequence, _fingerprint(emission))
                for row in redactions:
                    key = (row.field_category, row.reason)
                    self._redactions[key] = self._redactions.get(key, 0) + row.count
                    self._increment("REDACTED_FIELDS", row.count)
                self._increment("ACCEPTED")
                self._increment("RETAINED")
                self._persist_health()
                sealed = scope.execution_gate is not None and scope.execution_gate.capture_disposition() != "ACTIVE"
                if self._storage != "PROTECTED_VERIFIED" or sealed:
                    # Event bytes are retained, but health completion did not ACK.
                    scope.references.pop()
                    scope.indices.pop()
                    scope.hashes.pop()
                    self._acks.pop(emission.diagnostic_reference, None)
                    if sealed:
                        scope.late_indices.append(sequence)
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED" if sealed else "STORAGE_COMMIT_UNCONFIRMED", "STORE")
                if scope.producer == "RECOVERY_ENGINE" and hasattr(record.payload, "step_index"):
                    scope.step_indices[record.payload.step_index] = sequence
                    scope.step_policies[record.payload.step_index] = record.payload.policy_id
                if scope.producer == "SESSION_LIFECYCLE" and not scope.denial:
                    scope.session_state.main_previous = emission.diagnostic_reference
                return sv.CaptureReceipt(emission.diagnostic_reference, "CONFIRMED")
            except dv.DiagnosticsContractError as error:
                scope.failed = error.code
                self._mark_failure(error.code)
                self._meta_failure(scope, error.code)
                self._persist_health()
                reference = emission.diagnostic_reference if emission else scope.reference
                return sv.CaptureReceipt(reference, "NOT_CONFIRMED" if error.code.startswith("STORAGE") else "REJECTED")
            except Exception:
                scope.failed = "DIAGNOSTICS_COLLECTOR_FAILURE"
                self._mark_failure(scope.failed)
                self._meta_failure(scope, scope.failed)
                return sv.CaptureReceipt(emission.diagnostic_reference if emission else scope.reference, "NOT_CONFIRMED")
            finally:
                self._charging_scope = None

    def _context_update(self, old, **values):
        row = {name: getattr(old, name) for name in dv.CONTEXT_FIELDS}
        if old.resolution_evidence_reference is not None:
            row["resolution_evidence_reference"] = old.resolution_evidence_reference
        row.update(values)
        return _context(**row)

    def _diagnosis_context(self, diagnostic):
        state = diagnostic.input_state
        return _context(input_state=state.signature if type(state) is sv.AshState else None,
            admissibility_status=diagnostic.admissibility_status,
            transformation_compatibility=diagnostic.transformation_compatibility,
            normalization_status=diagnostic.normalization_status,
            recoverability_relevance=diagnostic.recoverability_relevance,
            is_valid=diagnostic.is_valid, orbit_info=_orbit(diagnostic.orbit_info))

    def _action_alias(self, record):
        payload = getattr(record, "payload", None)
        reference = getattr(payload, "action_reference", None)
        return None if reference is None else self._alias(reference)

    def _commit(self, method, sequence, payload, *args):
        try:
            self._io_depth += 1
            try:
                receipt = getattr(self.store, method)(sequence, *args, payload)
            finally:
                self._io_depth -= 1
        except Exception:
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED", "STORE") from None
        if type(receipt) is not dv.StorageReceipt or receipt.sequence != sequence or receipt.status != "COMMITTED":
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED", "STORE")
        return receipt

    def _supporting(self, kind, alias, node):
        encoded = _encode(node)
        writing_scope = self._charging_scope
        def retain_key():
            if writing_scope is not None:
                writing_scope.support_keys.add((kind, alias))
                state = getattr(writing_scope, "session_state", None)
                if state is not None:
                    state.pinned_support.add((kind, alias))
        if (kind, alias) in self._unconfirmed_support:
            if _encode(self._unconfirmed_support[(kind, alias)]) != encoded:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
            retain_key()
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
        existing = self._support[kind].get(alias)
        if existing is not None:
            if _encode(existing) != encoded:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
            retain_key()
            return alias
        maxima = {"PROFILE": 16, "ASSESSMENT": 512, "RECOVERY_DIAGNOSTIC": 64,
            "CANONICAL_SOURCE": 16, "NORMALIZATION_PROOF": 8, "CORRECTION_PROOF": 8,
            "REGISTRY_PROOF": 8, "CONDITION": 512, "PREDICATE_OBSERVATION": 512, "RECOVERY_SAFETY": 8,
            "TARGET_VALIDITY": 264}
        maxima.update({kind: maximum for _field, kind, _cls, maximum in dv.SESSION_SUPPORT_FIELDS})
        maxima.update({kind: maximum for _field, kind, _cls, maximum in dv.CURRENT_SESSION_SUPPORT_FIELDS})
        maxima.update(dv.MODULE_KIND_QUOTAS)
        if kind in dv.MODULE_KIND_QUOTAS and any(alias in self._support[other] or (other, alias) in self._unconfirmed_support for other in dv.MODULE_KIND_QUOTAS if other != kind):
            raise dv.DiagnosticsContractError('DIAGNOSTICS_COMPLETION_MISMATCH')
        if len(self._support[kind]) + sum(key[0] == kind for key in self._unconfirmed_support) >= maxima[kind]:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
        if len(encoded) > 32768 or self._support_bytes + len(encoded) > 2097152:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
        charged = None if writing_scope is None else self._budget_scope(writing_scope)
        if charged is not None and (charged.execution_gate is not None or getattr(charged, 'emitter_control', None) is not None):
            if not charged.audit_cleanup_allowed:
                self._check_scope_tokens(charged)
            if self._io_depth or len(encoded) > charged.remaining_bytes:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
            if charged.reserved_supporting_bytes and len(encoded) > charged.remaining_supporting_bytes:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
        outstanding = sum(scope.remaining_supporting_bytes for scope in self._scopes.values()
            if (not scope.finished or scope.final_observation_pending) and scope is not charged)
        if self._support_bytes + outstanding + len(encoded) > 2097152:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
        if self._used + len(encoded) + sum(scope.remaining_bytes for scope in self._scopes.values()
                if (not scope.finished or scope.final_observation_pending) and scope is not charged) > 33554432:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_BYTE_LIMIT")
        sequence = self._next_sequence
        try:
            self._commit("commit_supporting", sequence, encoded, kind, alias)
        except dv.DiagnosticsContractError:
            if charged is not None and (charged.execution_gate is not None or charged.producer in dv.MODULE_PRODUCERS or charged.producer == "SESSION_LIFECYCLE") or kind in {row[1] for row in dv.SESSION_SUPPORT_FIELDS} or kind in dv.MODULE_KIND_QUOTAS:
                self._unconfirmed_support[(kind, alias)] = node
                retain_key()
                self._support_bytes += len(encoded)
                self._used += len(encoded)
                if charged is not None:
                    self._consume_reservation(charged, len(encoded))
                    if hasattr(charged, 'module_kind_remaining') and kind in charged.module_kind_remaining:
                        charged.module_kind_remaining[kind] -= 1
                    if charged.reserved_supporting_bytes:
                        charged.remaining_supporting_bytes -= len(encoded)
                self._mark_failure("STORAGE_COMMIT_UNCONFIRMED")
            raise
        self._support[kind][alias] = node
        retain_key()
        self._support_bytes += len(encoded)
        self._used += len(encoded)
        if charged is not None:
            self._consume_reservation(charged, len(encoded))
            if hasattr(charged, 'module_kind_remaining') and kind in charged.module_kind_remaining:
                charged.module_kind_remaining[kind] -= 1
            if charged is not None and charged.reserved_supporting_bytes:
                charged.remaining_supporting_bytes -= len(encoded)
            if not charged.audit_cleanup_allowed:
                self._check_scope_tokens(charged)
        return alias

    def _consume_reservation(self, scope, byte_count, *, event=False):
        scope = self._budget_scope(scope)
        if byte_count > scope.remaining_bytes or event and scope.remaining_events <= 0:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
        scope.remaining_bytes -= byte_count
        if event:
            scope.remaining_events -= 1

    def _source_support(self, binding):
        if self.identity.source_revision is None:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE", "ORIGINAL_SOURCE")
        try:
            fields = sv.canonical_diagnostic_pin_fields(binding)
        except sv.StateContractError:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE", "ORIGINAL_SOURCE") from None
        snapshot = next((pin for pin in self._canonical_source_snapshots if pin.sha256 == fields[0][1]), None)
        if snapshot is None:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE", "ORIGINAL_SOURCE")
        alias = self._alias("canonical-source:" + fields[0][1])
        pins = tuple(dv.SourcePin(name, snapshot.revision, digest) for name, digest in fields)
        return self._supporting("CANONICAL_SOURCE", alias, dv.SafeSourceEvidence(alias, pins, None))

    def _profile_support(self, binding):
        profile = binding.profile if binding.availability == "AVAILABLE" else binding.evidence
        alias = self._alias("profile-evidence:" + _fingerprint(binding))
        node = dv.SafeProfileEvidence(alias, self._alias(binding.profile_id), binding.availability,
            self._alias(binding.source_binding.source_reference), self._alias(binding.source_binding.source_sha256), self._alias(binding.source_binding.evidence_reference),
            None if binding.availability == "UNAVAILABLE" else tuple(sorted(state.signature for state in profile.recognized_valid_states)),
            "NOT_PROVIDED" if binding.availability == "UNAVAILABLE" else None)
        return self._supporting("PROFILE", alias, node)

    def _safe_validity(self, diagnostic, input_reference):
        state = diagnostic.input_state
        safe_input = dv.SafeInputState("ASH_STATE" if type(state) is sv.AshState else "REJECTED",
            state.signature if type(state) is sv.AshState else None, self._alias(input_reference),
            None if type(state) is sv.AshState else state.input_evidence.failure_code)
        return dv.SafeStateValidity(safe_input, diagnostic.admissibility_status,
            diagnostic.transformation_compatibility, diagnostic.normalization_status,
            diagnostic.recoverability_relevance, diagnostic.is_valid, _orbit(diagnostic.orbit_info),
            diagnostic.rule_ids, (dv.message_text("UNTRUSTED_PROSE_OMITTED"),))

    def _safe_predicate(self, fact):
        binding = fact.binding
        return dv.SafePredicate(fact.evaluation, getattr(fact, "value", None),
            self._alias(binding.assessment_reference), self._alias(binding.diagnosis_reference),
            self._alias(binding.subject_reference), self._alias(binding.profile_id),
            self._alias(binding.profile_source_sha256), self._alias(binding.evidence_reference))

    def _assessment_support(self, packet):
        source = self._source_support(packet.source_binding)
        profile = self._profile_support(packet.profile_binding)
        binding = packet.assessment_binding
        alias = self._alias("assessment-evidence:" + _fingerprint(packet))
        context = getattr(packet, "system_context", None)
        evidence = getattr(packet, "classification_evidence", None)
        node = dv.SafeAssessmentEvidence(alias, self._alias(binding.assessment_reference),
            self._alias(packet.input_evidence.original_input_reference),
            None if packet.parsed_state is None else packet.parsed_state.signature, source, profile,
            self._safe_validity(packet.state_validity_diagnostic, packet.input_evidence.original_input_reference),
            False if context is None else context.is_in_safe_halt,
            False if context is None else context.is_in_containment,
            None if evidence is None else self._safe_predicate(evidence.correction_path_is_known),
            None if evidence is None else self._safe_predicate(evidence.fallback_is_available),
            getattr(packet, "system_state_class", None), getattr(packet, "recovery_category", None),
            tuple(name.upper() for name in getattr(packet, "consulted_predicates", ())),
            tuple(self._safe_envelope(emission.envelope, "DIAGNOSIS_RECORDED" if index == 0 else "CLASSIFICATION_RECORDED")
                  for index, emission in enumerate(packet.emitted_diagnostics)))
        new = alias not in self._support["ASSESSMENT"]
        result = self._supporting("ASSESSMENT", alias, node)
        if new:
            if packet.input_evidence.preview is not None:
                self._redact("INPUT_PREVIEW", 1)
            scalars = sum(observation.scalar_kind != "INTEGER_BIT" for observation in packet.input_evidence.coordinate_observations)
            if scalars:
                self._redact("NON_BIT_SCALAR", scalars)
            self._redact("NOTES", len(packet.state_validity_diagnostic.notes))
        return result

    def _redact(self, category, count):
        key = (category, "UNTRUSTED_FREEFORM")
        self._redactions[key] = self._redactions.get(key, 0) + count
        self._increment("REDACTED_FIELDS", count)

    def _normalization_support(self, packet):
        self._assessment_support(packet.original_diagnosis)
        plan, validation = packet.plan, packet.plan_validation
        source = self._source_support(validation.canonical_binding)
        profile = self._profile_support(validation.profile_binding)
        submitted_profile = self._profile_support(packet.original_diagnosis.profile_binding)
        alias = self._alias("normalization-proof:" + plan.evidence_reference)
        node = dv.SafeNormalizationProof(alias, "READY" if validation.validation_status == "VALIDATED" else "REJECTED",
            self._alias(packet.original_diagnosis.assessment_binding.assessment_reference),
            self._alias(packet.original_diagnosis.emitted_diagnostics[0].diagnostic_reference),
            self._alias(plan.plan_reference), self._alias(plan.policy_binding.policy_id),
            self._alias(packet.original_diagnosis.source_binding.aggregate_sha256), source,
            submitted_profile, profile,
            self._proof_status(validation.origin_validation_status), self._proof_status(validation.validation_status),
            plan.decision, tuple(item.signature for item in plan.eligible_targets),
            None if validation.recomputed_eligible_targets is None else tuple(item.signature for item in validation.recomputed_eligible_targets),
            None if plan.selected_target is None else plan.selected_target.signature,
            None if validation.recomputed_target is None else validation.recomputed_target.signature,
            tuple(item.signature for item in plan.codeword_chain),
            None if validation.recomputed_codeword_chain is None else tuple(item.signature for item in validation.recomputed_codeword_chain),
            self._validation_field(validation.field_name), None if validation.failure_code is None else "SOURCE_REPORTED_FAILURE")
        return self._supporting("NORMALIZATION_PROOF", alias, node)

    @staticmethod
    def _proof_status(status):
        return "VERIFIED" if status in ("VALIDATED", "VERIFIED") else status

    @staticmethod
    def _validation_field(field):
        if field is None:
            return None
        mapping = {"original_diagnosis.source_binding": "ORIGINAL_SOURCE",
            "original_diagnosis.profile_binding": "ORIGINAL_PROFILE", "original_diagnosis": "ORIGINAL_DIAGNOSIS",
            "eligible_targets": "TARGET_SET", "selected_target": "SELECTED_TARGET", "codeword_chain": "CODEWORD_CHAIN"}
        return mapping.get(field, "UNKNOWN_REGISTERED_FIELD")

    def complete_assessment(self, result):
        if not any(type(result) is kind for kind in (sv.StateDiagnosis, sv.StateAssessment, sv.ClassificationEvidenceFailure, sv.DiagnosticCaptureFailure)):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        reference = result.assessment_binding.assessment_reference
        scope = self._scopes.get(reference)
        if (scope is not None and scope.completion_response is not None and
                sv.canonical_source_baseline(result.source_binding) == 'M3_GENERATION'):
            with self._session_io():
                return self._first_response(scope, result, 'STATE_MODEL', reference)
        return self._complete(scope, result, "STATE_MODEL", reference=reference)

    def _first_response(self, scope, result, producer, reference):
        from .session_values import revalidate_value
        revalidate_value(result)
        if (type(scope) is not _CaptureScope or scope.owner is not self or
                self._scopes.get(scope.storage_reference) is not scope or scope.purged or not scope.finished or
                scope.producer != producer or scope.reference != reference or scope.completion_response is None or
                scope.completion_response.operation_reference != reference or
                scope.completion_response.confirmed_event_indices != tuple(scope.indices)):
            raise dv.DiagnosticsContractError('DIAGNOSTICS_COMPLETION_MISMATCH')
        self._check_capture_binding(scope.execution_gate, operation_reference=reference)
        raw = self._raw_bytes(result, scope)
        references = tuple(record.emission.diagnostic_reference if producer == 'NORMALIZATION' else
            record.diagnostic_reference for record in result.emitted_diagnostics)
        if (hashlib.sha256(raw).hexdigest() != scope.completed_hash or
                references != tuple(scope.references) or
                tuple(hashlib.sha256(self._raw_bytes(record, scope)).hexdigest() for record in result.emitted_diagnostics) != tuple(scope.hashes)):
            raise dv.DiagnosticsContractError('DIAGNOSTICS_COMPLETION_MISMATCH')
        return scope.completion_response

    def complete_normalization(self, result, *, execution_gate=None):
        if not any(type(result) is kind for kind in (nv.NormalizationResult, nv.NormalizationFailure, nv.NormalizationCaptureFailure)):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        reference = result.operation_binding.operation_reference
        scope = self._scopes.get(reference)
        if execution_gate is not None:
            from core.module_lifecycle import CoreExecutionGate
            if type(execution_gate) is not CoreExecutionGate:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
            self._check_capture_binding(execution_gate, operation_reference=reference)
            if scope is not None and scope.execution_gate is not execution_gate:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        return self._complete(scope, result, "NORMALIZATION", reference=reference)

    def _complete(self, scope, result, producer, *, reference=None):
        with self._session_io() if scope is not None and scope.execution_gate is not None else self._lock:
            from core.module_lifecycle import CoreExecutionGate
            if scope is not None and type(scope.execution_gate) is CoreExecutionGate and scope.completion_response is not None:
                return self._first_response(scope, result, producer, reference or scope.reference)
            self._charging_scope = scope
            if scope is not None and scope.execution_gate is not None:
                scope.audit_cleanup_allowed = True
            reference = reference or scope.reference
            indices, attempted, failure = (), None, None
            raw_result = None
            outcome = "COMPLETED"
            try:
                self._observe_clock()
                if scope is None or scope.producer != producer:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISSING")
                indices = tuple(scope.indices)
                attempted = scope.attempted_index if scope.failed else None
                if scope.finished:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
                raw_result = self._raw_bytes(result, scope)
                if len(raw_result) > 33554432:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RAW_PACKET_LIMIT")
                records = result.emitted_diagnostics
                if tuple(hashlib.sha256(self._raw_bytes(record, scope)).hexdigest() for record in records) != tuple(scope.hashes):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                if producer == "STATE_MODEL":
                    if type(result) is sv.StateDiagnosis and len(records) != 1 or type(result) is sv.StateAssessment and len(records) != 2:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                    if not records:
                        if type(result) is not sv.DiagnosticCaptureFailure:
                            raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                    else:
                        self._assessment_support(result)
                    partial = any(type(result) is kind for kind in (sv.ClassificationEvidenceFailure, sv.DiagnosticCaptureFailure))
                elif producer == "NORMALIZATION":
                    if type(result) is nv.NormalizationResult and tuple(record.phase for record in records) != ("COMPUTATION", "POST_VALIDATION"):
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                    self._normalization_support(result)
                    partial = type(result) is nv.NormalizationCaptureFailure
                    outcome = "NORMALIZED" if type(result) is nv.NormalizationResult else "FAILED"
                else:
                    partial, outcome = self._recovery_completion(scope, result)
                if getattr(result, "attempted_diagnostic", None) is not None:
                    if scope.attempted_hash != _fingerprint(result.attempted_diagnostic):
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                if partial or scope.failed:
                    raise dv.DiagnosticsContractError(scope.failed or "DIAGNOSTICS_REQUIRED_STEP_MISSING")
                if producer == "RECOVERY_ENGINE" and getattr(result, "failure_detail", None) is not None:
                    self._incident_failure(scope, "SOURCE_REPORTED_FAILURE")
                scope.finished = True
                self._producer_completed.add(producer)
                self._persist_health()
                if self._storage != "PROTECTED_VERIFIED":
                    raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
                self._charging_scope = None
                response = dv.DiagnosticsCompletionReceipt(reference, "COMPLETE", outcome, indices,
                    "COMPLETE_DECLARED_REFERENCE_SCOPE", None, None, self.health())
                if scope.completion_response is None:
                    scope.completed_hash, scope.completion_response = hashlib.sha256(raw_result).hexdigest(), response
                    if scope.execution_gate is not None:
                        scope.completed_result = result
                if scope.execution_gate is not None:
                    scope.audit_cleanup_allowed = False
                return response
            except dv.DiagnosticsContractError as error:
                failure = error.code
            except Exception:
                failure = "DIAGNOSTICS_COLLECTOR_FAILURE"
            if scope is not None:
                scope.finished, scope.failed = True, scope.failed or failure
                self._meta_failure(scope, failure)
                try:
                    self._incident_failure(scope, "STORAGE_FAILURE" if failure.startswith("STORAGE") else "MISSING_REQUIRED_STEP")
                except dv.DiagnosticsContractError as error:
                    failure = error.code
            self._mark_failure(failure)
            self._persist_health()
            self._charging_scope = None
            response = dv.DiagnosticsCompletionReceipt(reference, "INCOMPLETE", "INCOMPLETE", indices,
                "PARTIAL", failure, attempted, self.health())
            if scope is not None:
                if scope.completion_response is None:
                    scope.completion_response = response
                    try:
                        if raw_result is None:
                            raw_result = self._raw_bytes(result, scope)
                        if len(raw_result) <= 33554432:
                            scope.completed_hash = hashlib.sha256(raw_result).hexdigest()
                    except dv.DiagnosticsContractError:
                        pass
                    if scope.execution_gate is not None:
                        scope.completed_result = result
                scope.audit_cleanup_allowed = False
            return response

    def _mark_failure(self, code):
        self._failure = code
        self._increment("REJECTED")
        self._first_unavailable = self._next_sequence if self._first_unavailable is None else self._first_unavailable
        self._last_unavailable = self._next_sequence
        if code.startswith("STORAGE"):
            self._storage = "UNCERTAIN"
            self._counts["LOST"] = None

    def _meta_failure(self, scope, code):
        cause = "COMPLETION_MISSING" if code in ("DIAGNOSTICS_COMPLETION_MISSING", "DIAGNOSTICS_REQUIRED_STEP_MISSING") else "SCHEMA_NONCONFORMANCE"
        self._fallback_cause = cause
        if len(self._meta) >= 16:
            self._increment("META_OVERFLOW")
            self._fallback_health()
            return
        try:
            reference = self._alias("meta:" + str(len(self._meta)))
            envelope = dv.SafeDiagnosticEnvelope("STATE_VALIDITY", "ERROR", "DETECTION", "BLOCKED",
                self._alias(scope.reference), None, reference, ("ASH-STATE-GENERAL-001",),
                dv.message_text("DIAGNOSTIC_NONCONFORMANCE"), (dv.message_text("UNTRUSTED_PROSE_OMITTED"),))
            meta = dv.MetaDiagnosticRecord(reference, len(self._meta), self._last_clock, envelope,
                dv.MetaCause(cause, self._alias(scope.reference), None if scope.attempted_reference is None else self._alias(scope.attempted_reference), None, None))
            self._commit("commit_meta", meta.local_sequence, _encode(meta))
            self._meta.append(meta)
        except Exception:
            self._meta_storage = "UNCERTAIN"
            self._increment("META_OVERFLOW")
            self._fallback_health()

    def _fallback_health(self):
        record = dv.FallbackHealthRecord(self._fallback_cause or "SCHEMA_NONCONFORMANCE", self._storage,
            self._events[-1].local_sequence if self._events else None,
            self._first_unavailable, self._last_unavailable, self._counts["META_OVERFLOW"], self._last_clock)
        try:
            self._commit("commit_fallback_health", None, _encode(record))
        except dv.DiagnosticsContractError:
            self._meta_storage = "UNCERTAIN"

    def _incident_failure(self, scope, safe_failure):
        operation_alias = self._alias(scope.reference)
        if any(operation_alias in incident.affected_operation_references for incident in self._incidents):
            return
        if any(operation_alias in incident.affected_operation_references for incident in self._unconfirmed_incidents):
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
        timeline = tuple(event.event_id for event in self._events
            if event.operation_reference == operation_alias or event.relation is not None and event.relation.parent_operation_reference == operation_alias)
        if not timeline and scope.original is not None:
            origin = self._scopes.get(scope.original.assessment_reference)
            if origin is not None:
                timeline = tuple(event.event_id for event in self._events if event.local_sequence in origin.indices)
        if not timeline:
            timeline = tuple(meta.meta_reference for meta in self._meta
                if meta.cause.related_operation_reference == operation_alias)
        if not timeline:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
        if len(self._incidents) + len(self._unconfirmed_incidents) >= 32:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_INCIDENT_LIMIT")
        alias = self._alias("incident:" + scope.reference)
        trigger = timeline[-1]
        semantic = safe_failure == "SOURCE_REPORTED_FAILURE"
        error = dv.SafeError("RECOVERY" if semantic else "STORAGE" if safe_failure == "STORAGE_FAILURE" else "DIAGNOSTICS",
            safe_failure, (), "STORE" if safe_failure == "STORAGE_FAILURE" else "EXPECTED_STEP", None,
            "CAPTURE_UNCONFIRMED", ("EXCEPTION_TEXT", "STACK", "ABSOLUTE_PATH"))
        incident = dv.DiagnosticIncident(alias, trigger,
            dv.ExpectedBehavior("VALID_RETURN" if semantic else "ACKNOWLEDGED_STEPS", self._alias("docs/architecture/m3_reference_diagnostics_contract.md"), "COMPLETED" if semantic else "CONFIRMED"),
            "FAILED" if semantic else "NOT_CONFIRMED", (operation_alias,), timeline, (), error, (), None,
            (dv.EvidenceFact("CAPTURE_CONFIRMED" if semantic else "CAPTURE_NOT_CONFIRMED", (trigger,)),), (), ("NO_SUPPORTED_CAUSE",), True)
        payload = _encode(incident)
        if len(payload) > 32768 or self._incident_bytes + len(payload) > 1048576:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_INCIDENT_LIMIT")
        charged = self._budget_scope(scope)
        if charged.remaining_incidents <= 0:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_INCIDENT_LIMIT")
        charged.remaining_incidents -= 1
        try:
            sequence = self._events[-1].local_sequence if self._events else self._next_sequence
            self._commit("commit_incident", sequence, payload, alias)
            self._incidents.append(incident)
            self._incident_bytes += len(payload)
            self._used += len(payload)
            if self._charging_scope is not None:
                self._consume_reservation(self._charging_scope, len(payload))
        except dv.DiagnosticsContractError:
            self._unconfirmed_incidents.append(incident)
            self._incident_bytes += len(payload)
            self._used += len(payload)
            if self._charging_scope is not None:
                self._consume_reservation(self._charging_scope, len(payload))
            self._storage = "UNCERTAIN"
            self._failure = "STORAGE_COMMIT_UNCONFIRMED"
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED") from None

    def _coverage(self):
        available = {"DIAGNOSTICS", "PROTECTED_STORAGE", "ENVIRONMENT_OS", "RUNTIME_VERSION", "ARCHITECTURE", "HOST_CLASS", "UTC_CLOCK", "MONOTONIC_CLOCK"} | self._producer_completed
        if self._export_completed:
            available.add("PAIRED_EXPORT")
        environmental_missing = {row.source: row.reason for row in self.identity.environment.unavailable_fields}
        if self._storage != "PROTECTED_VERIFIED":
            environmental_missing["PROTECTED_STORAGE"] = "STORAGE_UNAVAILABLE"
        if self._unconfirmed_incidents or self._failure == "DIAGNOSTICS_INCIDENT_LIMIT":
            environmental_missing["DIAGNOSTICS"] = "LOSS_UNCONFIRMED"
        if self._last_clock.observed_utc is None:
            environmental_missing["UTC_CLOCK"] = self._last_clock.utc_reason
        if self._failure in ("DIAGNOSTICS_CLOCK_UNAVAILABLE", "DIAGNOSTICS_CLOCK_REGRESSION", "DIAGNOSTICS_DURATION_LIMIT"):
            environmental_missing["MONOTONIC_CLOCK"] = {"DIAGNOSTICS_CLOCK_REGRESSION": "CLOCK_REGRESSION",
                "DIAGNOSTICS_DURATION_LIMIT": "DURATION_LIMIT"}.get(self._failure, "CLOCK_UNAVAILABLE")
        available.difference_update(environmental_missing)
        excluded = {"REALM_ENCODER", "TRANSITION_REGISTRY", "TOPOLOGY_GENERATOR", "AXIOM_EVALUATOR", "GENERATION_PLANNER", "ARTIFACT_EMITTER", "NATIVE_RUNTIME", "NATIVE_RELEASE", "PHYSICAL_CRASH"}
        if self._module_capture_service is not None:
            excluded.difference_update(self._module_capture_service.registered)
        return tuple(dv.MissingCoverage(source, "EXCLUDED" if source in excluded else "AVAILABLE" if source in available else "UNAVAILABLE",
            "EXCLUDED_REFERENCE_SCOPE" if source in excluded else None if source in available else environmental_missing.get(source, "NOT_MEASURED")) for source in dv.enum_values("CoverageSource"))

    def health(self):
        with self._lock:
            coverage = self._coverage()
            active = sum(not scope.finished or scope.final_observation_pending for scope in self._scopes.values())
            status = "PARTIAL" if active or self._failure else "COMPLETE_DECLARED_REFERENCE_SCOPE"
            counters = tuple(dv.DiagnosticCounterState(field,
                "UNAVAILABLE" if self._counts[field] is None else "SATURATED" if field in self._saturated else "EXACT",
                "STORAGE_UNCONFIRMED" if self._counts[field] is None else "COUNTER_LIMIT" if field in self._saturated else None) for field in dv.enum_values("CounterField"))
            return dv.DiagnosticsHealth(status, self._counts["ACCEPTED"], self._counts["REJECTED"], self._counts["RETAINED"],
                self._counts["EXPIRED"], self._counts["LOST"], self._counts["REDACTED_FIELDS"], self._counts["REDACTED_REFERENCES"],
                self._events[-1].local_sequence if self._events else None, self._first_unavailable, self._last_unavailable,
                active, self._used, self._storage, self._failure, tuple(row for row in coverage if row.status != "AVAILABLE"),
                tuple(self._retention), any(row.coalesced for row in self._retention), self._counts["META_OVERFLOW"], counters, len(self._meta), self._meta_storage, self._fallback_cause)

    def _persist_health(self):
        try:
            self._commit("commit_health", self._events[-1].local_sequence if self._events else None, _encode(self.health()))
        except dv.DiagnosticsContractError:
            self._storage = "UNCERTAIN"
            self._failure = "STORAGE_COMMIT_UNCONFIRMED"
            self._fallback_health()

    def _evidence(self):
        support = self._support
        if self._module_capture_service is not None:
            support = {kind: dict(nodes) for kind, nodes in support.items()}
            for scope in self._module_capture_service.scopes.values():
                for key in scope._native.support_keys:
                    uncertain = self._unconfirmed_support.get(key)
                    if uncertain is not None:
                        support[key[0]][key[1]] = uncertain
        return dv.SupportingEvidence((), (), (), tuple(support["PROFILE"].values()),
            tuple(support["ASSESSMENT"].values()), tuple(support["RECOVERY_DIAGNOSTIC"].values()),
            tuple(support["CANONICAL_SOURCE"].values()), tuple(support["NORMALIZATION_PROOF"].values()),
            tuple(support["CORRECTION_PROOF"].values()), tuple(support["REGISTRY_PROOF"].values()),
            tuple(support["CONDITION"].values()), tuple(support["PREDICATE_OBSERVATION"].values()),
            tuple(support["RECOVERY_SAFETY"].values()), tuple(support["TARGET_VALIDITY"].values()),
            **{field: tuple(node for node in support[kind].values() if type(node) is cls)
                for field, kind, cls, _max in (*dv.SESSION_SUPPORT_FIELDS, *dv.CURRENT_SESSION_SUPPORT_FIELDS)},
            module_evidence=tuple(node for kind in dv.MODULE_KIND_QUOTAS for node in support[kind].values()))

    def snapshot(self, *, bundle_reference):
        sv.InputEvidence.validate_reference(bundle_reference)
        with self._lock:
            try:
                observed = self._observe_clock()
            except dv.DiagnosticsContractError as error:
                self._mark_failure(error.code)
                observed = dv.ClockObservation(None, None, "CLOCK_UNAVAILABLE", "CLOCK_UNAVAILABLE")
            for scope in self._scopes.values():
                if not scope.finished and scope.producer not in dv.MODULE_PRODUCERS:
                    self._failure = "DIAGNOSTICS_COMPLETION_MISSING"
            self._persist_health()
            bundle_alias = self._alias(bundle_reference)
            aliases = self._counts["REDACTED_REFERENCES"]
            entries = tuple(dv.RedactionEntry(category, reason, count) for (category, reason), count in self._redactions.items())
            if aliases:
                entries += (dv.RedactionEntry("CALLER_REFERENCE", "OPAQUE_REFERENCE_ALIAS", aliases),)
            limitations = tuple(dv.Limitation(code, source) for code, source in (
                ("REFERENCE_IMPLEMENTATION_ONLY", "DIAGNOSTICS"), ("TRUSTED_CAPTURE_CONTRACT", "DIAGNOSTICS"),
                ("NO_REMOTE_ACK_AUTHENTICATION", "DIAGNOSTICS"), ("NATIVE_COMPOSITION_DEFERRED", "NATIVE_RUNTIME"),
                ("NATIVE_RELEASE_DEFERRED", "NATIVE_RELEASE"), ("NO_PHYSICAL_CRASH_PROOF", "PHYSICAL_CRASH"),
                ("NO_POWER_LOSS_DURABILITY_PROOF", "PROTECTED_STORAGE"), ("NO_ENCRYPTION_CLAIM", "PROTECTED_STORAGE"),
                ("NO_SECOND_USER_ACCESS_TEST", "PROTECTED_STORAGE"), ("UNTRUSTED_PROSE_OMITTED", "DIAGNOSTICS")))
            events = tuple(self._events)
            if self._module_capture_service is not None:
                events = tuple(sorted((*events, *(event for event in self._unconfirmed_events.values()
                    if event.source in dv.MODULE_PRODUCERS)), key=lambda event: event.local_sequence))
            snapshot = dv.DiagnosticSnapshot(bundle_alias, observed.observed_utc, observed.utc_reason,
                self.identity, self.profile, dv.CaptureWindow(events[0].local_sequence if events else None,
                    events[-1].local_sequence if events else None, self._start_clock, observed),
                self._coverage(), events, tuple(self._meta), tuple(self._incidents), self._evidence(), self.health(),
                dv.RetentionAccount(self._limits, tuple(self._retention),
                    tuple(dict.fromkeys(self._alias(scope.reference) for scope in self._scopes.values() if not scope.finished or scope.final_observation_pending)),
                    tuple(dict.fromkeys(reference for incident in self._incidents if incident.unresolved
                                        for reference in incident.affected_operation_references)), any(row.coalesced for row in self._retention)),
                dv.RedactionAccount(self._counts["REDACTED_FIELDS"], self._counts["REDACTED_REFERENCES"], entries), limitations)
            self._issued_snapshots[snapshot.bundle_id] = _fingerprint(snapshot)
            return snapshot

    def export_pair(self, snapshot):
        if type(snapshot) is not dv.DiagnosticSnapshot:
            raise dv.DiagnosticsContractError("EXPORT_SNAPSHOT_INVALID")
        with self._lock:
            try:
                if type(snapshot.bundle_id) is not str or self._issued_snapshots.get(snapshot.bundle_id) != _fingerprint(snapshot):
                    raise dv.DiagnosticsContractError("EXPORT_SNAPSHOT_INVALID")
            except Exception:
                raise dv.DiagnosticsContractError("EXPORT_SNAPSHOT_INVALID") from None
            if self._export_slot is not None:
                parts = tuple(dv.PartReceipt(kind, name, "NOT_WRITTEN", None, None, None)
                    for kind, name in (("JSON", "diagnostics.json"), ("MARKDOWN", "diagnostics.md"), ("MANIFEST", "manifest.json")))
                return dv.ExportFailure(snapshot.bundle_id, "EXPORT_SLOT_OCCUPIED", "PUBLICATION", parts, snapshot)
            raw = _encode(snapshot)
            markdown = self._markdown(snapshot, raw)
            if len(raw) > 33554432 or len(markdown) > 50331648:
                raise dv.DiagnosticsContractError("EXPORT_BYTE_LIMIT")
            if json.loads(markdown.split(b"```json\n", 1)[1].rsplit(b"\n```", 1)[0]) != json.loads(raw):
                raise dv.DiagnosticsContractError("EXPORT_PARITY_FAILED")
            manifest = json.dumps({"bundle_id": snapshot.bundle_id, "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
                "json_sha256": hashlib.sha256(raw).hexdigest(), "markdown_sha256": hashlib.sha256(markdown).hexdigest(),
                "last_included_sequence": snapshot.capture_window.last_sequence,
                "parity": "EXACT_EMBEDDED_SNAPSHOT"}, sort_keys=True, separators=(",", ":")).encode("ascii")
            try:
                receipt = self.store.write_pair(snapshot.bundle_id, raw, markdown, manifest,
                    last_included_sequence=snapshot.capture_window.last_sequence)
            except Exception:
                receipt = None
            if type(receipt) is dv.StorePairReceipt and receipt.bundle_id == snapshot.bundle_id and receipt.last_included_sequence == snapshot.capture_window.last_sequence:
                expected = (raw, markdown, manifest)
                if all(part.bytes == len(data) and part.sha256 == hashlib.sha256(data).hexdigest() for part, data in zip(receipt.parts, expected)):
                    self._export_slot = snapshot.bundle_id
                    self._export_completed = True
                    self._export_boundary = snapshot.capture_window.last_sequence
                    return dv.ExportReceipt(snapshot.bundle_id, receipt.parts, receipt.last_included_sequence, snapshot)
            if type(receipt) is dv.StorePairFailure and receipt.bundle_id == snapshot.bundle_id:
                self._export_slot = snapshot.bundle_id
                self._export_boundary = snapshot.capture_window.last_sequence
                return dv.ExportFailure(snapshot.bundle_id, receipt.failure_code, receipt.failed_part, receipt.parts, snapshot)
            parts = tuple(dv.PartReceipt(kind, name, "WRITTEN_UNCONFIRMED", None, None, "EXPORT_PUBLICATION_FAILED")
                for kind, name in (("JSON", "diagnostics.json"), ("MARKDOWN", "diagnostics.md"), ("MANIFEST", "manifest.json")))
            self._export_slot = snapshot.bundle_id
            self._export_boundary = snapshot.capture_window.last_sequence
            return dv.ExportFailure(snapshot.bundle_id, "EXPORT_PUBLICATION_FAILED", "PUBLICATION", parts, snapshot)

    @staticmethod
    def _markdown(snapshot, raw):
        identity = snapshot.identity
        lines = ["# Reference Diagnostics", "", f"Bundle `{snapshot.bundle_id}`; product `{identity.product_version}`; implementation `{identity.implementation_id}`.",
            f"Source `{identity.source_revision}`; provenance `{identity.source_provenance.status}`; coverage `{snapshot.health.coverage_status}`.",
            "", "## Coverage", ""]
        for row in snapshot.coverage:
            lines.append(f"- {row.source}: {row.status}" + (f" ({row.reason})" if row.reason else ""))
        lines.extend(("", "## Observed timeline", ""))
        for event in snapshot.events:
            envelope = event.envelope
            classification = "local observation" if envelope is None else f"{envelope.diagnostic_kind}/{envelope.stage}/{envelope.severity}/{envelope.disposition}"
            lines.extend((f"### {event.local_sequence}: {event.event_id}", "",
                f"Producer `{event.source}`; {classification}; outcome `{event.outcome}`.",
                dv.message_text(event.message_template), "",
                "Context: `" + json.dumps(event.context.to_record(), sort_keys=True, separators=(",", ":")) + "`", ""))
            if event.error is not None:
                lines.extend(("Observed error: `" + json.dumps(event.error.to_record(), sort_keys=True, separators=(",", ":")) + "`", ""))
        lines.extend(("## Incidents", ""))
        for incident in snapshot.incidents:
            lines.extend((f"### {incident.incident_id}", "",
                f"Expected `{incident.expected.invariant}/{incident.expected.expected_outcome}`; observed `{incident.observed_outcome}`; unresolved `{incident.unresolved}`.",
                "Timeline: " + ", ".join(incident.timeline_event_references),
                "Unknown causes: " + ", ".join(incident.unknowns),
                "Retained evidence: `" + json.dumps(incident.to_record(), sort_keys=True, separators=(",", ":")) + "`", ""))
        lines.extend(("## Supporting evidence", ""))
        supporting = snapshot.supporting_evidence.to_record()
        for name, rows in supporting.items():
            if type(rows) is list and rows:
                lines.extend((f"### {name} ({len(rows)})", ""))
                lines.extend("- `" + json.dumps(row, sort_keys=True, separators=(",", ":")) + "`" for row in rows)
                lines.append("")
        lines.extend(("## Retention, redaction and health", ""))
        for name in ("retention", "redaction", "health"):
            lines.extend((name + ": `" + json.dumps(getattr(snapshot, name).to_record(), sort_keys=True, separators=(",", ":")) + "`", ""))
        lines.extend(("## Limitations", ""))
        lines.extend(f"- {row.code}: {row.source}" for row in snapshot.limitations)
        lines.extend(("", "## Exact paired snapshot", "", "The following artifact is identical to the paired JSON file.", ""))
        detailed = ("\n".join(lines) + "\n").encode("ascii")
        if len(detailed) > 16777216:
            raise dv.DiagnosticsContractError("EXPORT_BYTE_LIMIT")
        return detailed + b"```json\n" + raw + b"\n```\n"

    def purge_completed(self, *, through_sequence):
        if type(through_sequence) is not int or not 0 <= through_sequence < 1 << 64:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_VALUE_INVALID")
        with self._lock:
            groups = []
            for scope in self._scopes.values():
                if scope.relation is not None or scope.purged or not scope.finished or scope.failed:
                    continue
                if self._module_capture_service is not None and self._module_capture_service.pins_origin(scope.reference):
                    continue
                group = (scope,) + tuple(self._scopes[reference] for reference in scope.child_operations)
                if any(member.storage_reference in state.pinned_scopes for state in self._session_handles.values() for member in group):
                    continue
                if any(not member.finished or member.failed for member in group):
                    continue
                indices = tuple(index for member in group for index in member.indices)
                if indices and max(indices) <= through_sequence:
                    aliases = {self._alias(member.reference) for member in group}
                    event_aliases = {event.event_id for event in self._events if event.local_sequence in indices}
                    if any(incident.unresolved and (aliases.intersection(incident.affected_operation_references) or
                            event_aliases.intersection(incident.timeline_event_references))
                            for incident in (*self._incidents, *self._unconfirmed_incidents)):
                        continue
                    groups.append(group)
            retained_before = {event.local_sequence for event in self._events}
            indices = tuple(sorted(index for group in groups for member in group for index in member.indices if index in retained_before))
            if not indices or not callable(getattr(self.store, "purge_capture", None)):
                return dv.RetentionReceipt("REJECTED", (), self.health())
            request = dv.CapturePurgeRequest(indices, ())
            def invalidate_origins(affected):
                self._acks = {reference: witness for reference, witness in self._acks.items()
                    if witness.confirmed_sequence not in affected}
                for scope in self._scopes.values():
                    if affected.intersection(scope.indices):
                        scope.failed = scope.failed or "STORAGE_COMMIT_UNCONFIRMED"
                self._issued_snapshots.clear()
            try:
                observed = self.store.purge_capture(request)
                expected = tuple(dv.CaptureObjectKey("EVENT", index, None, None) for index in indices)
                if type(observed) is not dv.StoreCapturePurgeReceipt or tuple(row.key for row in observed.observations) != expected:
                    raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
            except Exception:
                # A thrown or malformed result cannot establish whether the
                # requested files still exist. Retain their graph roots, but
                # never use the old acknowledgements for a new attachment.
                invalidate_origins(set(indices))
                self._mark_failure("STORAGE_COMMIT_UNCONFIRMED")
                self._persist_health()
                return dv.RetentionReceipt("REJECTED", (), self.health())
            removed = {row.key.sequence for row in observed.observations if row.status == "REMOVED"}
            uncertain = {row.key.sequence for row in observed.observations if row.status == "UNCONFIRMED"}
            if uncertain:
                invalidate_origins(uncertain)
            for event in tuple(self._events):
                if event.local_sequence in removed:
                    self._events.remove(event)
                    self._used -= len(_encode(event))
                    self._increment("EXPIRED")
                    self._counts["RETAINED"] -= 1
            self._acks = {reference: witness for reference, witness in self._acks.items() if witness.confirmed_sequence not in removed}
            for group in groups:
                if all(index in removed or index not in retained_before for member in group for index in member.indices):
                    for member in group:
                        member.purged = True
            # Unknown event deletions remain roots. The second request is computed
            # from actual retained evidence, never from intended first-phase removal.
            reachable = set()
            for state in self._session_handles.values():
                reachable.update(state.pinned_support)
            for scope in self._scopes.values():
                if not scope.purged:
                    reachable.update(scope.support_keys)
            def references(value):
                if type(value) is str:
                    yield value
                elif type(value) in (tuple, list):
                    for child in value:
                        yield from references(child)
                elif type(value) is dict:
                    for child in value.values():
                        yield from references(child)
            indexed = {alias: (kind, alias) for kind, nodes in self._support.items() for alias in nodes}
            for event in self._events:
                reachable.update(indexed[alias] for alias in references(event.to_record()) if alias in indexed)
            changed = True
            while changed:
                changed = False
                for kind, alias in tuple(reachable):
                    node = self._support[kind].get(alias, self._unconfirmed_support.get((kind, alias)))
                    if node is None:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                    for reference in references(node.to_record()):
                        key = indexed.get(reference)
                        if key is not None and key not in reachable:
                            reachable.add(key)
                            changed = True
            unreachable = tuple(dv.CaptureObjectKey("SUPPORTING", None, kind, alias)
                for kind, alias in sorted(set(indexed.values()) - reachable))
            partial = observed.status != "COMPLETED"
            if unreachable:
                try:
                    support_receipt = self.store.purge_capture(dv.CapturePurgeRequest((), unreachable))
                    if type(support_receipt) is not dv.StoreCapturePurgeReceipt or tuple(row.key for row in support_receipt.observations) != unreachable:
                        raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
                    for row in support_receipt.observations:
                        if row.status == "REMOVED":
                            node = self._support[row.key.supporting_kind].pop(row.key.evidence_reference)
                            size = len(_encode(node))
                            self._support_bytes -= size
                            self._used -= size
                    partial = partial or support_receipt.status != "COMPLETED"
                except Exception:
                    partial = True
            boundaries = []
            for index in sorted(removed):
                if boundaries and index == boundaries[-1][1] + 1:
                    boundaries[-1][1] = index
                else:
                    boundaries.append([index, index])
            account = tuple(dv.RetentionBoundary(first, last, last - first + 1, "EXPLICIT_PURGE", False) for first, last in boundaries)
            self._retention.extend(account)
            if len(self._retention) > 16:
                first, last = self._retention[0].first_sequence, self._retention[-1].last_sequence
                self._retention[:] = [dv.RetentionBoundary(first, last, sum(row.record_count for row in self._retention), "EXPLICIT_PURGE", True)]
            if partial:
                self._mark_failure("STORAGE_COMMIT_UNCONFIRMED")
            elif self._export_slot is not None and self._export_boundary is not None and self._export_boundary <= through_sequence:
                try:
                    exported = self.store.purge_bundle(self._export_slot)
                    if type(exported) is not dv.StorePurgeReceipt or exported.bundle_id != self._export_slot or exported.status != "COMPLETED":
                        raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
                    self._export_slot, self._export_boundary, self._export_completed = None, None, False
                except Exception:
                    partial = True
                    self._mark_failure("STORAGE_COMMIT_UNCONFIRMED")
            self._issued_snapshots.clear()
            self._persist_health()
            return dv.RetentionReceipt("REJECTED" if partial else "COMPLETED", account[:16], self.health())

    def _evidence_source(self, value):
        return dv.SafeEvidenceSourceBinding(self._alias(value.source_reference),
            self._alias(value.source_sha256), self._alias(value.evidence_reference))

    def _condition_support(self, condition):
        alias = self._alias(condition.condition_id)
        return self._supporting("CONDITION", alias,
            dv.SafeConditionEvidence(alias, self._evidence_source(condition.source_binding)))

    def _predicate_support(self, observed):
        condition_alias = self._condition_support(observed.condition)
        alias = self._alias("predicate-observation:" + _fingerprint(observed))
        node = dv.SafePredicateObservationEvidence(alias, observed.status, condition_alias,
            self._evidence_source(observed.condition.source_binding), self._evidence_source(observed.source_binding),
            self._alias(observed.operation_reference), self._alias(observed.origin_assessment_reference),
            self._alias(observed.registry_id), self._alias(observed.registry_source_sha256),
            self._alias(observed.policy_id), observed.phase, observed.candidate_state_reference.signature)
        return self._supporting("PREDICATE_OBSERVATION", alias, node)

    def _directive(self, directive):
        from . import recovery_values as rv
        trigger = directive.trigger
        if type(trigger) is rv.ExternalEscalationRequired:
            trigger = dv.SafeExternalEscalationRequired(trigger.authority_status)
        elif type(trigger) is rv.ExistingModeBoundary:
            trigger = dv.SafeExistingModeBoundary(trigger.observed_system_state_class,
                self._alias(trigger.observed_assessment_reference))
        return dv.SafeRecoveryDirective(directive.requested_action, trigger,
            self._alias(directive.origin_assessment_reference), self._alias(directive.causing_decision_reference),
            tuple(self._alias(reference) for reference in directive.evidence_references), directive.request_origin,
            None if directive.policy_binding is None else dv.SafeRecoverySafetyPolicy())

    @staticmethod
    def _step_kind(action):
        mapping = {"NORMALIZE_PLAN": "NORMALIZE", "NORMALIZE_XOR": "NORMALIZE", "CORRECTION_RESOLVE": "CORRECT",
            "CORRECTION_XOR": "CORRECT", "CANDIDATE_APPLICABILITY": "APPLICABILITY", "FALLBACK_SELECT": "SELECT_FALLBACK",
            "CANDIDATE_VALIDATION": "ADDITIONAL_VALIDATION", "POST_ASSESSMENT": "VALIDATE_RECOVERY", "HANDOFF": "HANDOFF",
            "NORMALIZE": "NORMALIZE", "CORRECT": "CORRECT", "FALLBACK": "SELECT_FALLBACK", "NO_ACTION": "SUMMARY",
            "CANDIDATE_DECISION": "CANDIDATE_DECISION", "SUMMARY": "SUMMARY"}
        return mapping.get(action, "SUMMARY")

    def _recovery_diagnostic_support(self, scope, decision):
        diagnostic = decision.diagnostic
        alias = self._alias(decision.action_reference)
        steps = []
        indices = tuple(scope.step_indices[index] for index in decision.step_indices if index in scope.step_indices)
        if len(indices) > 32:
            groups = {}
            for index in decision.step_indices:
                if index in scope.step_indices:
                    groups.setdefault(scope.step_policies.get(index), []).append(scope.step_indices[index])
            grouped = tuple(tuple(rows) for rows in groups.values())
        else:
            grouped = tuple((index,) for index in indices)
        for index, step in enumerate(diagnostic.steps):
            step_indices = grouped[index] if index < len(grouped) else ()
            if len(step_indices) > 32:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
            steps.append(dv.SafeRecoveryStep(alias, self._step_kind(step.action),
                "COMPLETED" if step.status == "COMPLETED" else "BLOCKED" if step.status == "BLOCKED" else "FAILED",
                None, step_indices, "RECOVERY_ACTION_RECORDED"))
        node = dv.SafeRecoveryDiagnostic(diagnostic.recovery_category, diagnostic.original_state_class,
            self._alias(scope.original.last_diagnostic_reference), tuple(steps), diagnostic.outcome,
            None if diagnostic.corrected_state is None else diagnostic.corrected_state.signature,
            None if diagnostic.fallback_policy_id is None else self._alias(diagnostic.fallback_policy_id),
            dv.message_text("RECOVERY_ACTION_RECORDED"), diagnostic.rule_ids)
        return self._supporting("RECOVERY_DIAGNOSTIC", alias, node)

    def _recovery_context(self, scope, payload):
        from . import recovery_values as rv
        if type(payload) is rv.RecoveryStepEvidence:
            values = dict(step_index=payload.step_index,
                before_state=None if payload.before_state is None else payload.before_state.signature,
                codeword=None if payload.codeword is None else payload.codeword.signature,
                after_state=None if payload.after_state is None else payload.after_state.signature,
                actual_state=None if payload.after_state is None else payload.after_state.signature,
                policy_reference=None if payload.policy_id is None else self._alias(payload.policy_id),
                post_assessment_reference=None if payload.post_assessment_reference is None else self._alias(payload.post_assessment_reference))
            if payload.predicate_observation is not None:
                observed = payload.predicate_observation
                values.update(predicate_name=observed.phase,
                    predicate_value=True if observed.status == "TRUE" else False if observed.status == "FALSE" else None,
                    source_evidence_reference=self._predicate_support(observed))
            return _context(**values)
        if type(payload) is not rv.RecoveryActionDecision:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        return _context(recovery_diagnostic_reference=self._recovery_diagnostic_support(scope, payload),
            system_state_class=payload.diagnostic.original_state_class,
            recovery_category=payload.diagnostic.recovery_category,
            actual_state=None if payload.diagnostic.corrected_state is None else payload.diagnostic.corrected_state.signature,
            policy_reference=None if payload.diagnostic.fallback_policy_id is None else self._alias(payload.diagnostic.fallback_policy_id))

    def _registry_support(self, result):
        snapshot, validation = result.registry_snapshot, result.registry_validation
        if snapshot is None:
            return None
        binding = snapshot.source_binding
        alias = self._alias("registry-proof:" + result.operation_context.operation_reference)
        current_source = self._source_support(validation.current_source_binding)
        current_profile = self._profile_support(validation.current_profile_binding)
        submitted_profile = self._profile_support(result.origin_assessment.profile_binding)
        entries = []
        certifications = {item.policy_id: item for item in getattr(snapshot, "candidate_certifications", ())}
        validations = {item.policy_id: item for item in validation.candidate_validations}
        for index, entry in enumerate(getattr(snapshot, "entries", ())):
            certification = certifications[entry.policy_id]
            self._assessment_support(certification.source_assessment)
            for condition in (*entry.applicability_conditions, *entry.validation_requirements):
                self._condition_support(condition)
            item = validations.get(entry.policy_id)
            entries.append(dv.SafeRegistryEntry(self._alias(entry.policy_id), index, entry.ordering_rank,
                tuple(self._alias(condition.condition_id) for condition in entry.applicability_conditions),
                tuple(self._alias(condition.condition_id) for condition in entry.validation_requirements),
                entry.candidate_state_reference.signature, entry.escalation_on_failure,
                self._alias(certification.source_assessment.assessment_binding.assessment_reference),
                "NOT_EVALUATED" if item is None else item.assessment_validation.status,
                None if item is None or item.target_diagnostic is None else self._target_support(item.target_diagnostic,
                    validation.current_source_binding, validation.current_profile_binding)))
        node = dv.SafeRegistryProof(alias, self._alias(binding.registry_id), snapshot.availability,
            self._alias(binding.source_binding.source_reference), current_source, submitted_profile, current_profile,
            validation.status, tuple(entries), tuple(self._alias(attempt.policy_id) for attempt in result.policy_attempts),
            None if validation.failed_policy_id is None else self._alias(validation.failed_policy_id),
            self._validation_field(validation.field_name), None if validation.failure_code is None else "SOURCE_REPORTED_FAILURE")
        return self._supporting("REGISTRY_PROOF", alias, node)

    def _preparation_support(self, result):
        preparation = result.normalization_preparation
        if preparation is not None:
            diagnosis = preparation.original_diagnosis
            self._assessment_support(diagnosis)
            validation, plan = preparation.plan_validation, preparation.plan
            current = result.origin_validation
            alias = self._alias("normalization-proof:" + result.operation_context.operation_reference)
            node = dv.SafeNormalizationProof(alias, preparation.status,
                self._alias(result.origin_assessment.assessment_binding.assessment_reference),
                self._alias(diagnosis.emitted_diagnostics[0].diagnostic_reference),
                None if plan is None else self._alias(plan.plan_reference), self._alias(preparation.policy_binding.policy_id),
                self._alias(diagnosis.source_binding.aggregate_sha256), self._source_support(current.current_source_binding),
                self._profile_support(diagnosis.profile_binding), self._profile_support(current.current_profile_binding),
                "NOT_EVALUATED" if validation is None else self._proof_status(validation.origin_validation_status),
                "NOT_EVALUATED" if validation is None else self._proof_status(validation.validation_status),
                None if plan is None else plan.decision, None if plan is None else tuple(state.signature for state in plan.eligible_targets),
                None if validation is None or validation.recomputed_eligible_targets is None else tuple(state.signature for state in validation.recomputed_eligible_targets),
                None if plan is None or plan.selected_target is None else plan.selected_target.signature,
                None if validation is None or validation.recomputed_target is None else validation.recomputed_target.signature,
                None if plan is None else tuple(state.signature for state in plan.codeword_chain),
                None if validation is None or validation.recomputed_codeword_chain is None else tuple(state.signature for state in validation.recomputed_codeword_chain),
                None if validation is None else self._validation_field(validation.field_name),
                None if validation is None or validation.failure_code is None else "SOURCE_REPORTED_FAILURE")
            self._supporting("NORMALIZATION_PROOF", alias, node)
        observation = result.correction_observation
        if observation is not None and observation.validation is not None:
            correction, validation = observation.submitted, observation.validation
            alias = self._alias("correction-proof:" + correction.correction_reference)
            node = dv.SafeCorrectionProof(alias, self._alias(correction.correction_reference),
                self._alias(correction.original_assessment_reference), self._alias(correction.source_binding.source_reference),
                self._source_support(validation.current_source_binding), self._profile_support(result.origin_assessment.profile_binding),
                self._profile_support(validation.current_profile_binding), validation.origin_validation.status, validation.status,
                tuple(state.signature for state in correction.chain), correction.expected_target.signature,
                None if validation.computed_target is None else validation.computed_target.signature,
                None if validation.target_diagnostic is None else self._target_support(validation.target_diagnostic,
                    validation.current_source_binding, validation.current_profile_binding),
                self._validation_field(validation.field_name), None if validation.failure_code is None else "SOURCE_REPORTED_FAILURE")
            self._supporting("CORRECTION_PROOF", alias, node)

    def _target_support(self, diagnostic, source_binding, profile_binding):
        if type(diagnostic) is not sv.StateValidityDiagnostic:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        alias = self._alias("target-validity:" + _fingerprint(diagnostic) + ":" + _fingerprint(profile_binding))
        state = diagnostic.input_state
        reference = "ash_state_" + state.signature if type(state) is sv.AshState else state.input_evidence.original_input_reference
        node = dv.SafeTargetValidityEvidence(alias, self._source_support(source_binding),
            self._profile_support(profile_binding), self._safe_validity(diagnostic, reference))
        new = alias not in self._support["TARGET_VALIDITY"]
        result = self._supporting("TARGET_VALIDITY", alias, node)
        if new:
            self._redact("NOTES", len(diagnostic.notes))
        return result

    def _safety_support(self, result):
        context = result.operation_context
        alias = self._alias("safety-evidence:" + context.operation_reference)
        directive = result.directive
        consulted_propagation = result.origin_assessment.system_state_class in ("UNSTABLE", "CORRECTABLE", "DEGRADED")
        consulted_authority = result.origin_assessment.system_state_class == "FAILED"
        node = dv.SafeRecoverySafetyEvidence(alias, self._alias(context.operation_reference),
            self._alias(context.origin_assessment_reference), context.propagation_evidence.status,
            self._evidence_source(context.propagation_evidence.source_binding), consulted_propagation,
            context.external_authority_evidence.status, self._evidence_source(context.external_authority_evidence.source_binding),
            consulted_authority, None if directive is None else self._directive(directive))
        new = alias not in self._support["RECOVERY_SAFETY"]
        result = self._supporting("RECOVERY_SAFETY", alias, node)
        if new:
            self._redact("CAUSAL_TEXT", 2 + (directive is not None))
        return result

    def _recovery_completion(self, scope, result):
        from . import recovery_values as rv
        kinds = (rv.RecoveryNoAction, rv.RecoveredValue, rv.RecoveredFallbackValue, rv.RecoveryHandoff, rv.RecoveryFailure)
        if not any(type(result) is kind for kind in kinds) or result.operation_context.operation_reference != scope.reference:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
        original_scope = self._scopes.get(result.origin_assessment.assessment_binding.assessment_reference)
        if _Origin.observed(result.origin_assessment) != scope.original or original_scope is None or original_scope.completed_hash != hashlib.sha256(self._raw_bytes(result.origin_assessment, original_scope)).hexdigest():
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        self._attached(result.origin_assessment.emitted_diagnostics)
        if scope.denial and (not any(type(result) is kind for kind in (rv.RecoveryHandoff, rv.RecoveryFailure)) or result.steps or result.post_assessments or result.registry_snapshot is not None):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        if tuple(post.assessment.assessment_binding.assessment_reference for post in result.post_assessments) != tuple(scope.child_operations):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
        for post in result.post_assessments:
            child = self._scopes.get(post.assessment.assessment_binding.assessment_reference)
            if child is None or not child.finished or child.failed:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
            if child.relation != post.link or child.completed_hash != hashlib.sha256(self._raw_bytes(post.assessment, child)).hexdigest():
                raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
            self._assessment_support(post.assessment)
        if result.directive is not None and type(result.directive.trigger) is rv.ExistingModeBoundary:
            boundary = result.directive.trigger
            assessments = (result.origin_assessment, *(post.assessment for post in result.post_assessments))
            if not any(type(assessment) is sv.StateAssessment and
                    assessment.assessment_binding.assessment_reference == boundary.observed_assessment_reference and
                    assessment.system_state_class == boundary.observed_system_state_class
                    for assessment in assessments):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        recorded_steps = tuple(record.payload for record in result.emitted_diagnostics if record.record_kind == "ACTION_VALUE_COMPUTED")
        if any(step not in result.steps for step in recorded_steps):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
        if type(result) is not rv.RecoveryFailure and recorded_steps != result.steps:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
        self._preparation_support(result)
        self._registry_support(result)
        self._safety_support(result)
        attempted = None if result.failure_detail is None else result.failure_detail.attempted_diagnostic
        if attempted is not None and scope.attempted_hash != _fingerprint(attempted):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
        mapping = {"NO_ACTION": "NOT_APPLICABLE", "RECOVERED_VALUE": "RECOVERED",
                   "RECOVERED_FALLBACK_VALUE": "RECOVERED_VIA_FALLBACK", "HANDOFF_REQUIRED": "COMPLETED", "FAILURE": "FAILED"}
        return bool(scope.failed), mapping[result.outcome]


class ReferenceDevelopmentDiagnostics(_ReferenceDiagnostics):
    _profile_id = "REFERENCE_DEVELOPMENT"


class ReferenceReleaseDiagnostics(_ReferenceDiagnostics):
    _profile_id = "REFERENCE_RELEASE"
