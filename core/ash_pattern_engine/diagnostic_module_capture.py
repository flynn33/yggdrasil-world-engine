"""Explicit bounded capture of already-produced module semantics [YWE-REQ-0048]."""
from __future__ import annotations

import hashlib
import json
import threading

from . import diagnostic_module_values as mv
from . import diagnostics_values as dv
from . import state_values as sv


def _encoded(value):
    return json.dumps(value.to_record(), separators=(",", ":"), ensure_ascii=True,
                      sort_keys=True, allow_nan=False).encode('ascii')


def _classes():
    from .realm_transition import RealmEncoder, TransitionRegistry
    from .topology import ReferenceTopologyGenerator
    from .axioms import ReferenceAxiomEvaluator
    return ((RealmEncoder, 'REALM_ENCODER'), (TransitionRegistry, 'TRANSITION_REGISTRY'),
            (ReferenceTopologyGenerator, 'TOPOLOGY_GENERATOR'), (ReferenceAxiomEvaluator, 'AXIOM_EVALUATOR'))


def _configuration(producer):
    for cls, kind in _classes():
        if type(producer) is cls:
            binding = cls.configuration(producer)
            record = mv._record(binding)
            return kind, binding, hashlib.sha256(json.dumps(record, sort_keys=True,
                separators=(',', ':'), ensure_ascii=True).encode('ascii')).hexdigest()
    mv._fail('MODULE_PRODUCER_FOREIGN')


def _owned(producer, result):
    for cls, _kind in _classes():
        if type(producer) is cls:
            return cls.validate_owned_result(producer, result) is True
    return False


def _facts(result):
    from . import realm_transition_values as rt
    from . import generation_values as gen
    if mv._is(result, rt.RESULT_TYPES):
        return result.operation_reference, result.origin, result.constructed_records
    if mv._is(result, gen.PACKET_TYPES):
        return result.request.request_reference, result.request.origin_diagnosis, result.produced_diagnostics
    mv._fail('MODULE_RESULT_REJECTED')


def _emission(record):
    from . import realm_transition_values as rt
    from . import generation_values as gen
    if type(record) is rt.RealmTransitionRecord:
        return record.emission
    if type(record) is gen.GenerationDiagnosticRecord:
        return sv.DiagnosticEmission(record.diagnostic_reference, record.envelope)
    mv._fail('MODULE_RESULT_REJECTED')


def _semantic(result):
    from . import realm_transition_values as rt
    from . import generation_values as gen
    return 'REJECTED_INPUT' if mv._is(result, (rt.RealmTransitionFailure, gen.TopologyFailure, gen.AxiomEvaluationFailure)) else 'COMPLETE_SEMANTICS'


# Closed DiagnosticsCompletionReceipt representation: all768 index slots,
# 32 missing sources,16 retention rows,8 counter states and longest enum/number
# spellings. Free strings are charged12 ASCII bytes per Unicode codepoint.
# The executable schema control in test_m3_module_diagnostics rederives this.
MAX_COMPLETION_WIRE_BYTES = 14356


def _anticipated_raw_size(result, records, reference):
    observer = mv.ModuleFinalObservationReceipt(reference, 'NOT_CONFIRMED', 'ref:999999',
        'COMPLETE_SPECIFIED_SAFE_GRAPH', max(mv.FAILURES, key=len)).to_record()
    framing = {'operation_reference': reference, 'status': 'NOT_CONFIRMED', 'result': None,
        'confirmed_records': [_emission(record).diagnostic_reference for record in records],
        'attempted_record': None, 'completion': None, 'final_observation': observer,
        'failure_code': max(mv.FAILURES, key=len)}
    encode = lambda value: json.dumps(value, ensure_ascii=True, separators=(',', ':')).encode('ascii')
    # Replace the three null placeholders with actual bounded result/attempt
    # bytes and the independent complete completion-wire upper.
    attempted = max((len(mv.pure_bytes(record)) for record in records), default=4)
    return len(encode(framing)) - 12 + len(mv.pure_bytes(result)) + attempted + MAX_COMPLETION_WIRE_BYTES


class ModuleCaptureScope:
    """API-only issued capability; public values never authenticate this scope."""
    __slots__ = ('_service', '_native', '_producer', '_context', '_records', '_self_identity',
                 '_hashes', '_projection', '_final', '_audit', '_audit_attempted', '_finalize_lock')
    def __init__(self, service, native, producer, context, records):
        from .diagnostics import _CaptureScope
        if type(service) is not ModuleCaptureService or type(native) is not _CaptureScope:
            mv._fail('MODULE_SCOPE_FOREIGN')
        self._service, self._native, self._producer = service, native, producer
        self._context, self._records = context, records
        self._self_identity = self
        self._hashes = tuple(hashlib.sha256(mv.pure_bytes(record)).hexdigest() for record in records)
        self._projection = _Projection(service.collector, self)
        self._final = None
        self._audit = None
        self._audit_attempted = False
        self._finalize_lock = threading.Lock()
        native.module_scope_identity, native.module_finalize_lock = self, self._finalize_lock

    def append(self, record):
        service = _issued_service(self)
        return ModuleCaptureService.append(service, self, record)

    def finish(self, result):
        service = _issued_service(self)
        if not self._finalize_lock.acquire(blocking=False):
            raise dv.DiagnosticsContractError('DIAGNOSTICS_RESERVATION_REFUSED')
        try:
            return ModuleCaptureService.finish(service, self, result)
        finally:
            self._finalize_lock.release()

    def observe_final(self, result, actual_first_finish_response):
        service = _issued_service(self)
        if not self._finalize_lock.acquire(blocking=False):
            raise dv.DiagnosticsContractError('DIAGNOSTICS_RESERVATION_REFUSED')
        try:
            return ModuleCaptureService.observe_final(service, self, result, actual_first_finish_response)
        finally:
            self._finalize_lock.release()


def _issued_service(scope):
    from .diagnostics import _CaptureScope, ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
    if type(scope) is not ModuleCaptureScope:
        mv._fail('MODULE_SCOPE_FOREIGN')
    try:
        service, native = scope._service, scope._native
        if type(service) is not ModuleCaptureService or type(native) is not _CaptureScope or scope._self_identity is not scope:
            mv._fail('MODULE_SCOPE_FOREIGN')
        owner = service.collector
        if type(native.reference) is not str or type(service.scopes) is not dict or not mv._is(owner, (ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics)):
            mv._fail('MODULE_SCOPE_FOREIGN')
        if type(owner._scopes) is not dict or owner._module_capture_service is not service or service.scopes.get(native.reference) is not scope or owner._scopes.get(native.reference) is not native or native.module_scope_identity is not scope or native.module_finalize_lock is not scope._finalize_lock:
            mv._fail('MODULE_SCOPE_FOREIGN')
        return service
    except AttributeError:
        mv._fail('MODULE_SCOPE_FOREIGN')


class ModuleCaptureService:
    __slots__ = ('collector', 'registered', 'scopes')
    def __init__(self, collector):
        self.collector = collector
        self.registered, self.scopes = {}, {}

    def register(self, producer):
        kind = None
        try:
            kind, binding, digest = _configuration(producer)
            canonical, profile = self._bindings(binding)
            if sv.canonical_source_baseline(canonical) != 'M3_MODULES':
                mv._fail('MODULE_PRODUCER_BINDING_MISMATCH')
            with self.collector._session_io():
                if kind in self.registered:
                    mv._fail('MODULE_PRODUCER_DUPLICATE')
                self.registered[kind] = (producer, binding, digest)
            return mv.ModuleProducerRegistrationReceipt(kind, 'REGISTERED', None)
        except mv.ModuleContractError as error:
            return mv.ModuleProducerRegistrationReceipt(kind, 'REJECTED', error.code)
        except Exception:
            return mv.ModuleProducerRegistrationReceipt(kind, 'REJECTED', 'MODULE_PRODUCER_BINDING_MISMATCH' if kind else 'MODULE_PRODUCER_FOREIGN')

    @staticmethod
    def _bindings(binding):
        from . import realm_transition_values as rt
        from . import generation_values as gen
        if type(binding) is rt.RealmTransitionBinding:
            rt.revalidate_value(binding)
            return binding.canonical_binding, binding.profile_binding
        if type(binding) is tuple and len(binding) == 3 and type(binding[0]) is gen.TopologyAxiomSourceBinding:
            gen.revalidate_value(binding[0]); gen.revalidate_value(binding[1]); gen.revalidate_value(binding[2])
            return binding[0].canonical_binding, binding[1]
        mv._fail('MODULE_PRODUCER_BINDING_MISMATCH')

    def _validate(self, producer, context):
        mv.revalidate_value(context)
        kind, binding, digest = _configuration(producer)
        registered = self.registered.get(kind)
        if registered is None or registered[0] is not producer:
            mv._fail('MODULE_PRODUCER_FOREIGN')
        if registered[2] != digest or context.producer != kind or mv._record(context.source_binding) != mv._record(binding):
            mv._fail('MODULE_PRODUCER_BINDING_MISMATCH')
        if not _owned(producer, context.prepared_value):
            mv._fail('MODULE_RESULT_REJECTED')
        reference, origin, records = _facts(context.prepared_value)
        if reference != context.operation_reference or _encoded(origin) != _encoded(context.origin_diagnosis):
            mv._fail('MODULE_CONTEXT_REJECTED')
        canonical, profile = self._bindings(binding)
        if canonical != origin.source_binding or profile != origin.profile_binding:
            mv._fail('MODULE_PRODUCER_BINDING_MISMATCH')
        maximum = mv.PRODUCER_MAPPING[kind]['max_records']
        if not records or len(records) > maximum:
            mv._fail('MODULE_REQUIRED_RECORD_MISSING')
        if _anticipated_raw_size(context.prepared_value, records, reference) > mv.RAW_LIMIT:
            mv._fail('MODULE_RAW_PACKET_LIMIT')
        return kind, records

    def _origin(self, origin):
        owner = self.collector
        native = owner._scopes.get(origin.assessment_binding.assessment_reference)
        if native is None or native.producer != 'STATE_MODEL' or native.purged or native.failed or not native.finished or native.completion_response is None or native.completion_response.status != 'COMPLETE':
            mv._fail('MODULE_ORIGIN_REJECTED')
        if native.completed_hash != hashlib.sha256(_encoded(origin)).hexdigest() or len(origin.emitted_diagnostics) != 1 or origin.emitted_diagnostics[0].envelope.stage != 'DETECTION':
            mv._fail('MODULE_ORIGIN_REJECTED')
        owner._attached(origin.emitted_diagnostics)
        selected = set(native.support_keys)
        size = sum(len(_encoded(owner._support[kind].get(alias, owner._unconfirmed_support.get((kind, alias))))) for kind, alias in selected)
        if size + len(_encoded(native.completion_response)) > 65536:
            mv._fail('MODULE_RESERVATION_REFUSED')
        return native

    def _capacity(self, kind, reference):
        owner = self.collector
        reservation = mv.WHOLE_RESERVATIONS[kind]
        maximum = mv.PRODUCER_MAPPING[kind]['max_records']
        active = tuple(scope for scope in owner._scopes.values() if not scope.finished or scope.final_observation_pending)
        if reference in owner._scopes or len(self.scopes) >= 64 or len(active) >= 8:
            mv._fail('MODULE_RESERVATION_REFUSED')
        if owner._next_sequence + maximum > 1024 or len(owner._events) + len(owner._unconfirmed_events) + sum(scope.remaining_events for scope in active) + maximum > 1024:
            mv._fail('MODULE_RESERVATION_REFUSED')
        if owner._used + sum(scope.remaining_bytes for scope in active) + reservation['bytes'] > 33554432 or owner._support_bytes + sum(scope.remaining_supporting_bytes for scope in active) + reservation['supporting_bytes'] > 2097152:
            mv._fail('MODULE_RESERVATION_REFUSED')
        if len(owner._aliases) + sum(scope.remaining_aliases for scope in active) + reservation['aliases'] > 6144 or len(owner._incidents) + len(owner._unconfirmed_incidents) + sum(scope.remaining_incidents for scope in active) + 1 > 32:
            mv._fail('MODULE_RESERVATION_REFUSED')
        for supporting, count in mv.OPERATION_KIND_COUNTS[kind].items():
            actual = len(owner._support[supporting]) + sum(key[0] == supporting for key in owner._unconfirmed_support)
            outstanding = sum(getattr(scope, 'module_kind_remaining', {}).get(supporting, 0) for scope in active)
            if actual + outstanding + count > mv.KIND_QUOTAS[supporting]:
                mv._fail('MODULE_RESERVATION_REFUSED')

    def _dependencies(self, context):
        canonical, profile = self._bindings(context.source_binding)
        for dependency in context.dependency_results:
            reference, origin, _records = _facts(dependency)
            scope = self.scopes.get(reference)
            if scope is None or scope._context.prepared_value is not dependency or scope._native.purged or scope._native.completion_response is None or scope._native.completion_response.status != 'COMPLETE' or scope._final is None or scope._final.coverage != 'COMPLETE_SPECIFIED_SAFE_GRAPH':
                mv._fail('MODULE_RESULT_REJECTED')
            if origin.source_binding != canonical or origin.profile_binding != profile:
                mv._fail('MODULE_PRODUCER_BINDING_MISMATCH')

    def begin(self, producer, context, execution_gate):
        reference = context.operation_reference if type(context) is mv.ModuleCaptureContext else 'module:rejected'
        issued = None
        try:
            kind, records = self._validate(producer, context)
            for dependency in context.dependency_results:
                dependency_scope = self.scopes.get(_facts(dependency)[0])
                if dependency_scope is None or not _owned(dependency_scope._producer, dependency):
                    mv._fail('MODULE_RESULT_REJECTED')
            # Current MODULES source is explicitly ineligible for N3 execution.
            if execution_gate is not None:
                mv._fail('MODULE_PRODUCER_BINDING_MISMATCH')
            owner = self.collector
            with owner._session_io():
                self._origin(context.origin_diagnosis)
                self._dependencies(context)
                self._capacity(kind, reference)
                from .diagnostics import _CaptureScope
                reservation = mv.WHOLE_RESERVATIONS[kind]
                native = _CaptureScope(owner, reference, kind, original=context.origin_diagnosis,
                    reserved_events=mv.PRODUCER_MAPPING[kind]['max_records'], reserved_bytes=reservation['bytes'],
                    reserved_aliases=reservation['aliases'], reserved_supporting_bytes=reservation['supporting_bytes'])
                native.module_kind_remaining = dict(mv.OPERATION_KIND_COUNTS[kind])
                native.final_observation_pending = True
                owner._scopes[reference] = native
                issued = ModuleCaptureScope(self, native, producer, context, records)
                self.scopes[reference] = issued
                previous = owner._charging_scope
                owner._charging_scope = native
                try:
                    native.first_clock = owner._observe_clock()
                    issued._projection.begin()
                    owner._persist_health()
                    if owner._storage != 'PROTECTED_VERIFIED':
                        raise dv.DiagnosticsContractError('STORAGE_COMMIT_UNCONFIRMED')
                finally:
                    owner._charging_scope = previous
            return mv.ModuleCaptureAdmission(reference, 'ADMITTED', issued, None)
        except mv.ModuleContractError as error:
            failure = error.code
        except Exception:
            failure = 'MODULE_CAPTURE_UNCONFIRMED' if issued is not None else 'MODULE_CONTEXT_REJECTED'
        if issued is not None:
            issued._native.failed = 'STORAGE_COMMIT_UNCONFIRMED' if failure == 'MODULE_CAPTURE_UNCONFIRMED' else 'DIAGNOSTICS_RECORD_NONCONFORMANT'
            self.collector._mark_failure(issued._native.failed)
        return mv.ModuleCaptureAdmission(reference, 'NOT_CONFIRMED' if issued else 'REJECTED', issued, failure)

    def _scope(self, scope, *, validate=True):
        if _issued_service(scope) is not self:
            mv._fail('MODULE_SCOPE_FOREIGN')
        native = scope._native
        if self.scopes.get(native.reference) is not scope or self.collector._scopes.get(native.reference) is not native or native.owner is not self.collector:
            mv._fail('MODULE_SCOPE_FOREIGN')
        if validate:
            self._validate(scope._producer, scope._context)
        return native

    def append(self, scope, record):
        reference = 'module:rejected'
        native = None
        owner = self.collector
        try:
            native = self._scope(scope)
            emission = _emission(record)
            reference = emission.diagnostic_reference
            raw = mv.pure_bytes(record)
            index = len(native.indices)
            if index >= len(scope._records) or hashlib.sha256(raw).hexdigest() != scope._hashes[index]:
                mv._fail('MODULE_CAPTURE_REJECTED')
            if len(json.dumps(emission.envelope.to_record(), separators=(',', ':'), ensure_ascii=True).encode('ascii')) > 8192:
                mv._fail('MODULE_RAW_PACKET_LIMIT')
            with owner._session_io():
                previous = owner._charging_scope
                owner._charging_scope = native
                try:
                    if native.finished or native.failed or index != len(native.indices) or reference in owner._acks:
                        mv._fail('MODULE_REPLAY_REFUSED')
                    self._chain(scope, emission, index)
                    native.attempted_reference, native.attempted_hash = reference, hashlib.sha256(raw).hexdigest()
                    proof = scope._projection.record(record, index)
                    observed = owner._observe_clock()
                    sequence = owner._next_sequence
                    if sequence >= 1 << 64:
                        raise dv.DiagnosticsContractError('DIAGNOSTICS_SEQUENCE_LIMIT')
                    native.attempted_index = sequence if sequence < 1024 else None
                    from .diagnostics import _context
                    event = dv.DiagnosticEvent(owner._alias(reference), sequence, observed, native.producer,
                        'DIAGNOSTIC', 'MODULE_RECORD_RECORDED', owner.identity.session_reference,
                        owner._alias(native.reference), None, None, owner._alias(reference),
                        owner._safe_envelope(emission.envelope, 'MODULE_RECORD_RECORDED'),
                        'COMPLETED' if emission.envelope.disposition == 'RESOLVED' else 'BLOCKED',
                        observed.monotonic_nanoseconds-native.first_clock.monotonic_nanoseconds, None,
                        _context(proof_evidence_reference=proof), None, ())
                    encoded = _encoded(event)
                    if len(encoded) > 32768 or native.remaining_events <= 0:
                        raise dv.DiagnosticsContractError('DIAGNOSTICS_EVENT_TOO_LARGE')
                    owner._consume_reservation(native, len(encoded), event=True)
                    owner._next_sequence += 1
                    try:
                        owner._commit('commit_event', sequence, encoded)
                    except dv.DiagnosticsContractError:
                        owner._unconfirmed_events[sequence] = event
                        owner._used += len(encoded)
                        raise
                    owner._events.append(event); owner._used += len(encoded)
                    owner._increment('RETAINED')
                    owner._persist_health()
                    if owner._storage != 'PROTECTED_VERIFIED':
                        raise dv.DiagnosticsContractError('STORAGE_COMMIT_UNCONFIRMED')
                    native.references.append(reference); native.indices.append(sequence); native.hashes.append(hashlib.sha256(raw).hexdigest())
                    native.last_envelope = event.envelope
                    owner._acks[reference] = dv.PrivateAcknowledgmentWitness(reference, owner.identity.build_id,
                        owner.identity.session_reference, sequence, hashlib.sha256(_encoded(emission)).hexdigest())
                    owner._increment('ACCEPTED')
                    return sv.CaptureReceipt(reference, 'CONFIRMED')
                finally:
                    owner._charging_scope = previous
        except Exception as error:
            if native is not None:
                native.failed = error.code if type(error) is dv.DiagnosticsContractError else 'DIAGNOSTICS_RECORD_NONCONFORMANT'
                owner._mark_failure(native.failed)
            return sv.CaptureReceipt(reference, 'NOT_CONFIRMED' if type(error) is dv.DiagnosticsContractError and error.code.startswith('STORAGE') else 'REJECTED')

    @staticmethod
    def _chain(scope, emission, index):
        envelope = emission.envelope
        origin = scope._context.origin_diagnosis.emitted_diagnostics[0]
        previous = _emission(scope._records[index-1]) if index else origin
        severity = ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
        if envelope.diagnostic_kind != mv.PRODUCER_MAPPING[scope._native.producer]['kind'] or envelope.stage != 'PROCESSING' or envelope.subject_reference != origin.envelope.subject_reference or envelope.chain_root_reference != origin.envelope.chain_root_reference or envelope.parent_diagnostic_reference != previous.diagnostic_reference or severity.index(envelope.severity) < severity.index(previous.envelope.severity) or not set(envelope.rule_ids) <= set(mv.PRODUCER_MAPPING[scope._native.producer]['rules']):
            mv._fail('MODULE_CAPTURE_REJECTED')

    def finish(self, scope, result):
        native = self._scope(scope, validate=False)
        if native.completion_response is not None:
            return native.completion_response
        owner = self.collector
        failure = None
        try:
            self._scope(scope)
            if result is not scope._context.prepared_value or not _owned(scope._producer, result):
                mv._fail('MODULE_RESULT_REJECTED')
            if tuple(native.hashes) != scope._hashes or native.failed:
                failure = native.failed or 'DIAGNOSTICS_REQUIRED_STEP_MISSING'
            with owner._session_io():
                previous = owner._charging_scope
                owner._charging_scope = native
                try:
                    scope._projection.operation(failure)
                    owner._observe_clock()
                    native.finished = True
                    owner._persist_health()
                    if owner._storage != 'PROTECTED_VERIFIED':
                        failure = 'STORAGE_COMMIT_UNCONFIRMED'
                finally:
                    owner._charging_scope = previous
        except Exception as error:
            failure = error.code if type(error) is dv.DiagnosticsContractError else 'DIAGNOSTICS_REQUIRED_STEP_MISSING'
        native.finished = True
        if failure:
            native.failed = native.failed or failure
            owner._mark_failure(failure)
        response = dv.DiagnosticsCompletionReceipt(native.reference, 'INCOMPLETE' if failure else 'COMPLETE',
            'INCOMPLETE' if failure else 'COMPLETED', tuple(native.indices), 'PARTIAL' if failure else 'COMPLETE_DECLARED_REFERENCE_SCOPE',
            failure, native.attempted_index if failure else None, owner.health())
        native.completed_hash = hashlib.sha256(mv.pure_bytes(scope._context.prepared_value)).hexdigest()
        native.completed_result, native.completion_response = scope._context.prepared_value, response
        return response

    def observe_final(self, scope, result, completion):
        native = self._scope(scope, validate=False)
        if scope._final is not None:
            return scope._final
        owner = self.collector
        alias = None
        try:
            self._scope(scope)
            if result is not scope._context.prepared_value or completion is not native.completion_response or completion is None:
                mv._fail('MODULE_FINAL_OBSERVATION_REJECTED')
            # The wrapper guard measures the full combination, not separate fits.
            candidate_complete = completion.status == 'COMPLETE' and not native.failed
            mv.raw_business_bytes(mv.ModuleCaptureReceipt(native.reference, 'CONFIRMED' if candidate_complete else 'NOT_CONFIRMED', result,
                tuple(native.references), None, completion,
                mv.ModuleFinalObservationReceipt(native.reference, 'CONFIRMED', 'ref:999999',
                    'COMPLETE_SPECIFIED_SAFE_GRAPH' if candidate_complete else 'PARTIAL', None),
                None if candidate_complete else 'MODULE_CAPTURE_UNCONFIRMED'))
            with owner._session_io():
                previous = owner._charging_scope
                owner._charging_scope = native
                try:
                    alias = scope._projection.final(completion)
                    native.final_observation_pending = False
                    owner._persist_health()
                    if owner._storage != 'PROTECTED_VERIFIED':
                        raise dv.DiagnosticsContractError('STORAGE_COMMIT_UNCONFIRMED')
                    if completion.status == 'COMPLETE' and not native.failed:
                        owner._producer_completed.add(native.producer)
                finally:
                    owner._charging_scope = previous
            coverage = 'COMPLETE_SPECIFIED_SAFE_GRAPH' if completion.status == 'COMPLETE' and not native.failed else 'PARTIAL'
            scope._final = mv.ModuleFinalObservationReceipt(native.reference, 'CONFIRMED', alias, coverage, None)
        except Exception as error:
            native.final_observation_pending = False
            failure = 'STORAGE_COMMIT_UNCONFIRMED' if type(error) is dv.DiagnosticsContractError and error.code.startswith('STORAGE') else 'DIAGNOSTICS_COMPLETION_MISMATCH'
            native.failed = native.failed or failure
            owner._mark_failure(failure)
            scope._final = mv.ModuleFinalObservationReceipt(native.reference, 'NOT_CONFIRMED', alias,
                'STORAGE_UNCERTAIN' if owner._storage != 'PROTECTED_VERIFIED' else 'PARTIAL',
                'MODULE_RAW_PACKET_LIMIT' if type(error) is mv.ModuleContractError and error.code == 'MODULE_RAW_PACKET_LIMIT' else 'MODULE_FINAL_OBSERVATION_REJECTED')
        return scope._final

    def audit(self, scope, boundary):
        self._scope(scope, validate=False)
        if not scope._finalize_lock.acquire(blocking=False):
            raise dv.DiagnosticsContractError('DIAGNOSTICS_RESERVATION_REFUSED')
        try:
            return self._audit_return(scope, boundary)
        finally:
            scope._finalize_lock.release()

    def _audit_return(self, scope, boundary):
        native = self._scope(scope, validate=False)
        mv._choice(boundary, ('RETURN', 'SHUTDOWN'))
        if scope._audit_attempted:
            prior = scope._audit
            return mv.ModuleReturnAuditObservation(native.reference, 'ALREADY_OBSERVED', prior.missing_kind,
                prior.meta_sequence, prior.coverage, prior.failure_code)
        scope._audit_attempted = True
        missing = 'REQUIRED_SEMANTIC_RECORD' if not scope._records else 'REQUIRED_CAPTURE_STEP' if tuple(native.hashes) != scope._hashes else 'FIRST_COMPLETION' if native.completion_response is None else 'REQUIRED_CAPTURE_STEP' if scope._final is None else 'NONE'
        if missing == 'NONE':
            scope._audit = mv.ModuleReturnAuditObservation(native.reference, 'COMPLETE', 'NONE', None,
                'COMPLETE_SPECIFIED_SAFE_GRAPH' if scope._final is not None and scope._final.coverage == 'COMPLETE_SPECIFIED_SAFE_GRAPH' else 'PARTIAL', None)
            return scope._audit
        owner = self.collector
        sequence = None
        try:
            with owner._session_io():
                prior_count = len(owner._meta)
                owner._mark_failure('DIAGNOSTICS_COMPLETION_MISSING')
                owner._meta_failure(native, 'DIAGNOSTICS_COMPLETION_MISSING')
                if len(owner._meta) > prior_count:
                    sequence = owner._meta[-1].local_sequence
                owner._persist_health()
            scope._audit = mv.ModuleReturnAuditObservation(native.reference, 'MISSING' if sequence is not None else 'NOT_CONFIRMED',
                missing, sequence, 'PARTIAL' if owner._meta_storage == 'PROTECTED_VERIFIED' else 'STORAGE_UNCERTAIN', 'MODULE_COMPLETION_MISSING')
        except Exception:
            owner._mark_failure('DIAGNOSTICS_COMPLETION_MISSING')
            scope._audit = mv.ModuleReturnAuditObservation(native.reference, 'NOT_CONFIRMED', missing, None, 'PARTIAL', 'MODULE_COMPLETION_MISSING')
        return scope._audit

    def pins_origin(self, reference):
        return any(not scope._native.purged and scope._context.origin_diagnosis.assessment_binding.assessment_reference == reference for scope in self.scopes.values())


class _Projection:
    def __init__(self, owner, scope):
        self.owner, self.scope = owner, scope
        self.operation_reference = scope._native.reference
        self.context_reference = self.source_reference = self.operation_alias = None
        self.outputs = []
        self.definitions = {}
        self.payload_aliases = {}

    def alias(self, suffix):
        if suffix.startswith('shared:'):
            return self.owner._alias('module:' + suffix)
        return self.owner._alias('module:' + self.operation_reference + ':' + suffix)

    def store(self, kind, key, **values):
        alias = self.alias(key)
        node = mv.SafeModuleEvidence(kind, alias, mv.SAFE_CLASSES[kind](**values))
        self.owner._supporting(kind, alias, node)
        return alias

    def begin(self):
        scope, owner = self.scope, self.owner
        context, result = scope._context, scope._context.prepared_value
        binding = context.source_binding
        canonical, profile = ModuleCaptureService._bindings(binding)
        origin = context.origin_diagnosis
        canonical_alias = owner._source_support(canonical)
        profile_alias = owner._profile_support(profile)
        origin_alias = owner._assessment_support(origin)
        from . import realm_transition_values as rt
        if type(binding) is rt.RealmTransitionBinding:
            pins = tuple({'path_reference': owner._alias(pin.source_id), 'sha256': pin.source_sha256} for pin in binding.contract_pins)
            policies = (owner._alias(binding.policy_source_reference), owner._alias(binding.policy_source_sha256), owner._alias(binding.policy_evidence_reference))
        else:
            pins = tuple({'path_reference': owner._alias(path), 'sha256': digest} for path, digest in binding[0].contract_pins)
            policies = (owner._alias('docs/architecture/m3_topology_axiom_reference_policy.md'), owner._alias(binding[2].policy_sha256))
        source_key = 'shared:source:' + scope._service.registered[context.producer][2]
        self.source_reference = self.store('PRODUCER_SOURCE', source_key, canonical_evidence_reference=canonical_alias,
            profile_evidence_reference=profile_alias, contract_pins=pins,
            diagnostics_contract_sha256='6bd5dc891960cbd9fcdc878de6b46b715912df43ccd1a2affc9793176776376b',
            diagnostic_schema_sha256=canonical.diagnostic_source_sha256, taxonomy_sha256=canonical.taxonomy_source_sha256,
            source_baseline='M3_MODULES', source_assurance='RECOGNIZED_COMPLETE_VECTOR', module_policy_references=policies)
        emission = origin.emitted_diagnostics[0]
        origin_scope = owner._scopes[origin.assessment_binding.assessment_reference]
        self.context_reference = self.store('PRODUCER_CONTEXT', 'context', operation_reference=owner._alias(context.operation_reference),
            producer=context.producer, origin_assessment_reference=origin_alias,
            origin_diagnostic_reference=owner._alias(emission.diagnostic_reference),
            origin_completion_reference=owner._alias('completion:' + hashlib.sha256(_encoded(origin_scope.completion_response)).hexdigest()),
            root_reference=owner._alias(emission.envelope.chain_root_reference), predecessor_reference=owner._alias(emission.diagnostic_reference),
            source_reference=self.source_reference, profile_reference=profile_alias,
            dependency_operation_references=tuple(owner._alias(_facts(dependency)[0]) for dependency in context.dependency_results),
            binding_status='FULL_CURRENT_BINDINGS_MATCH', capture_assurance='ACTUAL_COMPLETED_ORIGIN')
        self._outputs(result, policies[0])

    def _outputs(self, result, policy):
        from . import realm_transition_values as rt
        from . import generation_values as gen
        if type(result) is rt.RealmEncodingResult:
            identity = result.identity
            self.outputs.append(self.store('REALM_IDENTITY', 'identity', state_signature=identity.state_signature,
                vertex_id=identity.vertex_id, realm_id=identity.realm_id, orbit_id=identity.orbit_id,
                identity_policy='FULL_VECTOR_VERTEX_LOSSLESS_ALIAS'))
        definitions = result.catalog.definitions if type(result) is rt.TransitionResolutionResult else (result.selected_definition,) if getattr(result, 'selected_definition', None) is not None else ()
        if definitions:
            registry_alias = self.alias('registry')
            aliases = []
            for definition in definitions:
                alias = self.store('TRANSITION_DEFINITION', 'definition:' + definition.transition_id,
                    definition_reference=self.alias('definition:' + definition.transition_id), registry_reference=registry_alias,
                    transition_reference=self.owner._alias(definition.transition_id), codeword=definition.codeword.signature,
                    catalog_index=int(definition.transition_id[-2:]), applicability_mask=definition.applicability_mask,
                    policy_reference=policy, omitted_fields='DECLARED_DEFINITION_LABELS')
                self.definitions[definition.transition_id] = alias
                aliases.append(alias)
            self.outputs.append(self.store('TRANSITION_REGISTRY', 'registry', registry_reference=registry_alias,
                source_reference=self.source_reference, policy_reference=policy, definitions=tuple(aliases),
                policy_status='DECLARED_REFERENCE_POLICY', ordering='CANONICAL_C16_ORDER'))
        if type(result) is gen.TopologyResult:
            pages = []
            for index in range(0, len(result.nodes), 16):
                nodes = tuple({'path': node.path_token, 'parent_path': node.path_token[:-1] if node.depth else None,
                    'kind': node.branch_kind.upper(), 'depth': node.depth, 'frontier_ordinal': node.ordinal} for node in result.nodes[index:index+16])
                pages.append(self.store('TOPOLOGY_PAGE', 'topology:page:' + str(index//16), topology_reference=self.alias('topology'), page_index=index//16, nodes=nodes))
            diagnostic = result.produced_diagnostics[0].payload
            self.outputs.append(self.store('TOPOLOGY', 'topology', topology_reference=self.alias('topology'),
                context_reference=self.context_reference, input_state=result.request.origin_diagnosis.parsed_state.signature,
                seed_reference=self.owner._alias(result.request.seed_token), seed_policy='ASCII_TOKEN_1_TO_32', depth=result.request.depth,
                leaf_count=len(result.nodes), visited_count=result.visited_node_count, pages=tuple(pages),
                node_id_policy='TOPOLOGY_SEED_BASE3_PATH', frontier_policy='FINAL_FRONTIER_ONLY_BASE3_ORDER', rules=result.produced_diagnostics[0].envelope.rule_ids))
        if mv._is(result, (gen.AxiomEvaluationResult, gen.AxiomEvaluationFailure)):
            subject = result.request.subject
            measure = lambda value: {'ticks': value.ticks, 'unit': value.unit, 'ticks_per_unit': value.ticks_per_unit}
            provenance = subject.provenance
            self.outputs.append(self.store('AXIOM_SUBJECT', 'axiom:subject', subject_reference=self.owner._alias(subject.subject_reference),
                state=subject.state.signature, relation_count=subject.relation_count, scale_count=subject.scale_count,
                raw_measure=measure(subject.raw_measure), compressed_measure=measure(subject.compressed_measure),
                erasure_cost=measure(subject.erasure_cost), self_reference_capable=subject.self_reference_capable,
                self_model_available=subject.self_model_available, source_kind=provenance.source_kind,
                source_reference=self.owner._alias(provenance.source_reference), method_id_reference=self.owner._alias(provenance.method_id),
                method_revision_reference=self.owner._alias(provenance.method_revision), origin_diagnosis_reference=self.owner._alias(provenance.origin_diagnosis_reference)))

    def record(self, record, index):
        from . import realm_transition_values as rt
        from . import generation_values as gen
        emission, payload = _emission(record), record.payload
        values = dict(context_reference=self.context_reference, diagnostic_reference=self.owner._alias(emission.diagnostic_reference),
            payload_reference=self.alias('record:' + str(index)), producer=self.scope._native.producer, record_index=index,
            current_impact=getattr(payload, 'current_impact', 'ERROR' if emission.envelope.disposition == 'BLOCKED' else 'INFO'), phase='INPUT_VALIDATION',
            result='SUCCEEDED' if emission.envelope.disposition == 'RESOLVED' else 'REFUSED',
            input_state=self.scope._context.origin_diagnosis.parsed_state.signature if self.scope._context.origin_diagnosis.parsed_state is not None else None,
            output_state=None, codeword=None, is_applicable=None, verification_status=None, admissibility_status=None,
            selection_kind=None, selected_definition_reference=None, value_reference=None, actual_pure_target_diagnostic=None,
            omitted_fields='CALLER_EXPLANATION_AND_IDENTIFIERS')
        if type(payload) is rt.RealmTransitionGate:
            values.update(verification_status=payload.verification_status, admissibility_status=payload.admissibility_status)
        elif type(payload) is rt.RealmIdentity:
            values.update(phase='IDENTITY_ENCODING', value_reference=self.outputs[0], payload_reference=self.outputs[0])
        elif type(payload) is rt.TransitionSelectionObservation:
            values.update(phase='SELECTED_MEMBERSHIP', selection_kind='TRANSITION_ID' if payload.selection.selection_kind == 'IDENTIFIER' else 'CODEWORD',
                codeword=None if payload.codeword is None else payload.codeword.signature,
                selected_definition_reference=self.definitions.get(payload.transition_id))
        elif type(payload) is rt.TransitionApplicabilityObservation:
            values.update(phase='DEFINITION_APPLICABILITY' if type(self.scope._context.prepared_value) is rt.TransitionResolutionResult else 'SELECTED_APPLICABILITY',
                codeword=payload.codeword.signature, is_applicable=payload.is_applicable,
                selected_definition_reference=self.definitions.get(payload.transition_id), result='SUCCEEDED' if payload.is_applicable else 'INAPPLICABLE')
        elif type(payload) is rt.TransitionTransformationObservation:
            values.update(phase='FULL_VECTOR_TRANSFORMATION', output_state=payload.candidate.signature,
                codeword=payload.codeword.signature, selected_definition_reference=self.definitions.get(payload.transition_id),
                actual_pure_target_diagnostic=self.owner._safe_validity(payload.target_diagnosis, emission.diagnostic_reference))
        elif type(payload) is gen.TopologyDiagnostic:
            values.update(phase='TOPOLOGY_EXPANSION' if self.outputs else 'INPUT_REFUSAL', value_reference=self.outputs[0] if self.outputs else None)
        elif type(payload) is gen.AxiomCheckDiagnostic:
            names = ('A1_RELATIONAL_EXISTENCE', 'A2_STRUCTURAL_COMPRESSIBILITY', 'A3_MULTI_SCALE_PERSISTENCE', 'A4_ENERGETIC_COST_OF_ERASURE', 'A5_SELF_REFERENCE_FOR_CONSCIOUSNESS')
            alias = self.store('AXIOM_CHECK', 'axiom:check:' + str(index), subject_reference=self.outputs[0], axiom_id=names[int(payload.axiom_id[1])-1],
                passed=payload.passed, current_impact=payload.current_impact,
                operator={'GT_ZERO': 'GREATER_THAN_ZERO', 'LT': 'LESS_THAN_SAME_QUANTUM', 'GT_ONE': 'GREATER_THAN_ONE', 'BOTH_TRUE': 'BOOLEAN_CONJUNCTION'}[payload.operator],
                operand_names=tuple(name.upper() for name in payload.operand_names), overall_pass=payload.overall_pass, explanation_code='CHECK_PASSED' if payload.passed else 'CHECK_FAILED')
            values.update(phase='AXIOM_CHECK', value_reference=alias, payload_reference=alias, result='SUCCEEDED' if payload.passed else 'REFUSED')
        elif type(payload) is gen.AxiomInputDiagnostic:
            values.update(phase='INPUT_REFUSAL', result='REFUSED')
        return self.store('PRODUCER_RECORD', 'record:' + str(index), **values)

    def operation(self, failure):
        native = self.scope._native
        self.operation_alias = self.store('PRODUCER_OPERATION', 'operation', context_reference=self.context_reference,
            producer=native.producer, semantic_status=_semantic(self.scope._context.prepared_value),
            constructed_record_references=tuple(self.owner._alias(_emission(record).diagnostic_reference) for record in self.scope._records),
            attempted_event_indices=() if native.attempted_index is None else (native.attempted_index,),
            confirmed_event_indices=tuple(native.indices), pending_record_references=tuple(self.owner._alias(_emission(record).diagnostic_reference) for record in self.scope._records[len(native.indices):]),
            output_references=tuple(self.outputs), completion_observation_reference=None,
            capture_status='INCOMPLETE' if failure else 'COMPLETE', failure_code='MODULE_CAPTURE_UNCONFIRMED' if failure else None)

    def final(self, completion):
        if self.operation_alias is None:
            mv._fail('MODULE_FINAL_OBSERVATION_REJECTED')
        return self.store('PRODUCER_FINAL_OBSERVATION', 'final', operation_reference=self.owner._alias(self.operation_reference),
            tentative_operation_reference=self.operation_alias, actual_result_reference=self.operation_alias,
            completion_observation_reference=self.owner._alias('completion:' + hashlib.sha256(_encoded(completion)).hexdigest()),
            first_finish_status=completion.status, semantic_status=_semantic(self.scope._context.prepared_value),
            capture_status='COMPLETE' if completion.status == 'COMPLETE' else 'INCOMPLETE',
            failure_code=None if completion.status == 'COMPLETE' else 'MODULE_CAPTURE_UNCONFIRMED')
