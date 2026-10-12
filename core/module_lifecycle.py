"""Bounded logical Core lifecycle and original execution capabilities."""
from __future__ import annotations
from dataclasses import dataclass
import importlib
import sys
import threading
import types
from . import core_values as cv

CORE_STAGES = ('ORIGIN_CAPTURE', 'NORMALIZATION_VALIDATE', 'NORMALIZATION_CAPTURE',
               'NORMALIZATION_VALUE', 'NORMALIZATION_POST_CAPTURE', 'SOURCE_ENCODING',
               'CHAIN', 'FINAL_DIAGNOSIS', 'DESTINATION_ENCODING', 'TOPOLOGY', 'AXIOMS',
               'PLANNER', 'PATTERN_PROJECTION', 'NARRATIVE', 'PERCEPTION', 'EMISSION_PREPARE',
               'EMISSION_DISPATCH', 'COSMOLOGY', 'REALM_ACCESS', 'REALM_SHIFT_PROPOSAL')
_FACTORY = object()
_TOKEN_LOCK_TYPE = type(threading.Lock())
_LIFECYCLE_LOCK_TYPE = type(threading.RLock())
_OWNER_ROUTES = (('deterministic_policy', 'DeterministicPolicy'),
              ('cosmology_engine.cosmology', 'CosmologyEngine'), ('realm_engine.realm', 'RealmEngine'),
              ('ash_pattern_engine.core_facade', 'AshCoreFacade'), ('narrative_engine.narrative', 'NarrativeEngine'),
              ('perception_engine.perception', 'PerceptionEngine'), ('orchestration', 'CoreOrchestrator'))


def _owner_class(owner):
    for module_name, class_name in _OWNER_ROUTES:
        try:
            module = importlib.import_module('.' + module_name, __package__)
        except ModuleNotFoundError as error:
            if error.name == __package__ + '.' + module_name:
                continue
            raise
        cls = getattr(module, class_name)
        if type(owner) is cls:
            return cls
    cv._fail('owner', 'CORE_LIFECYCLE_REJECTED')


def _configured_owner_is_original(lifecycle):
    """A configured owner is already imported; this lookup cannot import or dispatch."""
    owner,owner_type=lifecycle._owner,lifecycle._owner_type
    for module_name,class_name in _OWNER_ROUTES:
        module=sys.modules.get(__package__+'.'+module_name)
        if type(module) is not types.ModuleType:
            continue
        cls=vars(module).get(class_name)
        if type(owner) is cls and owner_type is cls:
            cookie=owner._core_owner_cookie
            return (type(cookie) is cv._OwnerCookie and cookie.original is owner and
                    cookie.owner_class is cls and owner._core_lifecycle is lifecycle)
    return False


@dataclass(frozen=True, slots=True)
class CoreStageGrant:
    operation_reference: str
    stage: str
    generation: int
    grant_sequence: int
    status: str

    def __post_init__(self):
        cv._text(self.operation_reference, 'REF', 'operation_reference')
        if type(self.stage) is not str or self.stage not in CORE_STAGES:
            cv._fail('phase')
        for value in (self.generation, self.grant_sequence):
            if type(value) is not int or not 0 <= value < 1 << 64:
                cv._fail('generation')
        if type(self.status) is not str or self.status not in ('GRANTED', 'CANCELLED', 'UNAVAILABLE'):
            cv._fail('status')


class ModuleTicket:
    __slots__ = ('_factory', '_original', '_lifecycle', '_reference', '_generation',
                 '_bindings', '_sealed', '_completed', '_sequence', '_children', '_gates','_actual_result')

    def __new__(cls, marker=None):
        if marker is not _FACTORY:
            cv._fail('request_ref', 'CORE_LIFECYCLE_REJECTED')
        return super().__new__(cls)


@dataclass(frozen=True, slots=True)
class _GateCookie:
    original: object
    lifecycle: object
    ticket: object
    collector: object
    reference: str
    generation: int
    stages: tuple
    binding: object
    binding_sha256: str
    parent: object


def _ticket_is_issued(lifecycle,ticket):
    """Read this owner's finite original ledger without grants, locks or hooks."""
    if type(lifecycle) is not CoreModuleLifecycle or type(ticket) is not ModuleTicket:
        return False
    try:
        ledger=lifecycle._ledger
        if (lifecycle._self is not lifecycle or not _configured_owner_is_original(lifecycle) or
                type(ledger) is not dict or len(ledger)>64 or
                any(type(key) is not str for key in ledger) or ticket._factory is not _FACTORY or
                ticket._original is not ticket or ticket._lifecycle is not lifecycle or
                type(ticket._reference) is not str or type(ticket._generation) is not int or
                not 0<=ticket._generation<(1<<64) or type(ticket._sealed) is not bool or
                type(ticket._sequence) is not int or not 0<=ticket._sequence<=64 or
                type(ticket._children) is not int or not 0<=ticket._children<=64 or
                type(ticket._bindings) is not tuple or len(ticket._bindings)>64 or
                type(ticket._gates) is not list or len(ticket._gates)>65 or
                any(type(row) is not tuple or len(row)!=3 or type(row[0]) is not CoreExecutionGate or
                    type(row[1]) is not _GateCookie or type(row[2]) is not tuple or len(row[2])!=10
                    for row in ticket._gates) or
                not (ticket._completed is None or type(ticket._completed) is cv.ModuleCompletion)):
            return False
        entry=ledger.get(ticket._reference)
        if type(entry) is not tuple or len(entry)!=2 or entry[1] is not ticket:
            return False
        body=entry[0]
        if (type(body) is not tuple or len(body)!=3 or type(body[0]) is not str or body[0]!='ADMIT' or
                type(body[1]) is not int or body[1]!=ticket._generation or body[2] is not ticket._bindings):
            return False
        for pair in ticket._bindings:
            if (type(pair) is not tuple or len(pair)!=2 or type(pair[0]) is not str or
                    type(pair[1]) is not tuple or not pair[1] or len(pair[1])>20 or
                    any(type(stage) is not str or stage not in CORE_STAGES for stage in pair[1])):
                return False
        return True
    except AttributeError:
        return False


class CoreExecutionGate:
    __slots__ = ('_factory', '_cookie', '_issued_cookie', '_issued_metadata', '_token_lock', '_sealed')

    def __new__(cls, marker=None):
        if marker is not _FACTORY:
            cv._fail('request_ref', 'CORE_LIFECYCLE_REJECTED')
        return super().__new__(cls)

    @staticmethod
    def _cookie_for(gate):
        if type(gate) is not CoreExecutionGate:
            return None
        try:
            cookie = object.__getattribute__(gate, '_cookie')
            marker = object.__getattribute__(gate, '_factory')
            issued = object.__getattribute__(gate, '_issued_cookie')
            metadata = object.__getattribute__(gate, '_issued_metadata')
        except AttributeError:
            return None
        if marker is not _FACTORY or type(cookie) is not _GateCookie or issued is not cookie or cookie.original is not gate:
            return None
        if (type(cookie.lifecycle) is not CoreModuleLifecycle or type(cookie.ticket) is not ModuleTicket or
                type(cookie.reference) is not str or type(cookie.generation) is not int or
                type(cookie.stages) is not tuple or type(cookie.binding) is not cv.CoreBinding or
                type(cookie.binding_sha256) is not str or
                not (cookie.parent is None or type(cookie.parent) is CoreExecutionGate)):
            return None
        if not cookie.stages or any(type(stage) is not str or stage not in CORE_STAGES for stage in cookie.stages):
            return None
        if (type(metadata) is not tuple or len(metadata) != 10 or type(metadata[4]) is not str or
                type(metadata[5]) is not int or type(metadata[8]) is not str):
            return None
        actual=(cookie.original,cookie.lifecycle,cookie.ticket,cookie.collector,cookie.reference,
                cookie.generation,cookie.stages,cookie.binding,cookie.binding_sha256,cookie.parent)
        if any(actual[index] is not metadata[index] for index in (0,1,2,3,6,7,9)):
            return None
        if any(actual[index] != metadata[index] for index in (4,5,8)):
            return None
        try:
            ticket = cookie.ticket
            if (ticket._factory is not _FACTORY or ticket._original is not ticket or
                    ticket._lifecycle is not cookie.lifecycle or type(ticket._reference) is not str or
                    type(ticket._generation) is not int or type(ticket._sealed) is not bool or
                    type(gate._sealed) is not bool or cookie.lifecycle._self is not cookie.lifecycle or
                    type(cookie.lifecycle._closed) is not bool):
                return None
            issued_gates=ticket._gates
            if (not _ticket_is_issued(cookie.lifecycle,ticket) or
                    type(issued_gates) is not list or len(issued_gates)>65 or
                    not any(row[0] is gate and row[1] is cookie and row[2] is metadata for row in issued_gates)):
                return None
        except AttributeError:
            return None
        return cookie

    def configuration(self):
        cookie = CoreExecutionGate._cookie_for(self)
        if cookie is None or not CoreExecutionGate.validate_issued_for_collector(self, cookie.collector, cookie.reference):
            cv._fail('binding', 'CORE_LIFECYCLE_REJECTED')
        return cookie.collector, cookie.reference, cookie.binding.canonical_binding, cookie.binding.profile_binding, cookie.generation

    @staticmethod
    def validate_issued_for_collector(gate, collector, operation_reference):
        cookie = CoreExecutionGate._cookie_for(gate)
        if cookie is None or cookie.collector is not collector or type(operation_reference) is not str:
            return False
        from .ash_pattern_engine.diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
        if not cv._one_of(type(collector), (ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics)):
            return False
        if operation_reference != cookie.reference or type(cookie.ticket) is not ModuleTicket:
            return False
        try:
            if cookie.ticket._factory is not _FACTORY or cookie.ticket._original is not cookie.ticket:
                return False
            cv.revalidate_value(cookie.binding)
            return cookie.binding_sha256 == cv._wire_digest(cookie.binding)
        except (cv.CoreContractError, AttributeError, ValueError):
            return False

    def capture_disposition(self):
        cookie = CoreExecutionGate._cookie_for(self)
        if cookie is None or type(self._token_lock) is not _TOKEN_LOCK_TYPE:
            return 'UNAVAILABLE'
        if self._sealed or cookie.ticket._sealed or cookie.lifecycle._closed:
            return 'SEALED'
        if not self._token_lock.acquire(blocking=False):
            return 'UNAVAILABLE'
        try:
            return 'SEALED' if self._sealed or cookie.ticket._sealed or cookie.lifecycle._closed else 'ACTIVE'
        finally:
            self._token_lock.release()

    def stage_grant(self, stage):
        cookie = CoreExecutionGate._cookie_for(self)
        if cookie is None:
            cv._fail('request_ref', 'CORE_LIFECYCLE_REJECTED')
        return CoreModuleLifecycle._stage_grant(cookie.lifecycle, self, stage)

    @staticmethod
    def for_operation(original_gate, operation_reference, allowed_stage):
        cookie = CoreExecutionGate._cookie_for(original_gate)
        if cookie is None or cookie.parent is not None:
            cv._fail('request_ref', 'CORE_LIFECYCLE_REJECTED')
        return CoreModuleLifecycle._child_gate(cookie.lifecycle, original_gate, operation_reference, allowed_stage)


class CoreModuleLifecycle:
    __slots__ = ('_owner', '_owner_type', '_binding', '_lock', '_generation', '_phase',
                 '_closed', '_started', '_ledger', '_inflight', '_self')

    def __init__(self, owner):
        owner_type = _owner_class(owner)
        binding = owner_type.configuration(owner)
        if owner._core_lifecycle is not None:
            cv._fail('owner', 'CORE_LIFECYCLE_REJECTED')
        self._owner, self._owner_type, self._binding = owner, owner_type, binding
        self._lock = threading.RLock()
        self._generation, self._phase, self._closed, self._started = 0, 'STOPPED', False, False
        self._ledger, self._inflight, self._self = {}, {}, self
        object.__setattr__(owner, '_core_lifecycle', self)

    def _valid(self):
        if type(self) is not CoreModuleLifecycle:
            cv._fail('owner', 'CORE_LIFECYCLE_REJECTED')
        try:
            if (self._self is not self or _owner_class(self._owner) is not self._owner_type or
                    self._owner._core_lifecycle is not self or type(self._lock) is not _LIFECYCLE_LOCK_TYPE or
                    type(self._ledger) is not dict or type(self._inflight) is not dict or
                    type(self._generation) is not int or type(self._phase) is not str or
                    type(self._closed) is not bool or type(self._started) is not bool):
                cv._fail('owner', 'CORE_LIFECYCLE_REJECTED')
            cookie = self._owner._core_owner_cookie
            if type(cookie) is not cv._OwnerCookie or cookie.original is not self._owner or cookie.owner_class is not self._owner_type:
                cv._fail('owner', 'CORE_LIFECYCLE_REJECTED')
        except AttributeError:
            cv._fail('owner', 'CORE_LIFECYCLE_REJECTED')

    def _status(self):
        return cv.ModuleStatus(self._owner_type.CORE_OWNER, self._generation, self._phase,
                               self._closed, len(self._inflight), len(self._ledger))

    def status(self):
        CoreModuleLifecycle._valid(self)
        with self._lock:
            return self._status()

    def _request(self, request_id, expected_generation):
        cv._text(request_id, 'ID', 'request_ref')
        if type(expected_generation) is not int or not 0 <= expected_generation < 1 << 64:
            cv._fail('generation')

    def _receipt(self, reference, action, before, status, failure=None):
        return cv.ModuleLifecycleReceipt(reference, action, before, self._status(), status, failure)

    def start(self, request_id, *, expected_generation):
        CoreModuleLifecycle._valid(self)
        self._request(request_id, expected_generation)
        failure = None
        try:
            self._owner_type.configuration(self._owner)
        except cv.CoreContractError as error:
            failure = error.code
        body = ('START', expected_generation)
        with self._lock:
            before = self._status()
            prior = self._ledger.get(request_id)
            if prior is not None and prior[0] == body:
                return prior[1]
            if self._closed or self._started or self._generation != expected_generation or prior is not None or len(self._ledger) >= 64:
                return self._receipt(request_id, 'START', before, 'REFUSED', 'CORE_LIFECYCLE_REJECTED')
            if self._generation > (1 << 64) - 3:
                return self._receipt(request_id, 'START', before, 'REFUSED', 'CORE_NUMERIC_OVERFLOW')
            self._started, self._phase, self._generation = True, 'FAILED' if failure else 'ACTIVE', self._generation + 1
            if failure:
                self._closed = True
            self._ledger[request_id] = body, None
            receipt = self._receipt(request_id, 'START', before, 'REFUSED' if failure else 'COMPLETED', failure)
            self._ledger[request_id] = body, receipt
            return receipt

    def admit(self, request_id, *, expected_generation, operation_bindings):
        CoreModuleLifecycle._valid(self)
        self._request(request_id, expected_generation)
        if type(operation_bindings) is not tuple or len(operation_bindings) > 64:
            cv._fail('request_ref')
        for pair in operation_bindings:
            if type(pair) is not tuple or len(pair) != 2:
                cv._fail('request_ref')
            cv._text(pair[0], 'REF', 'request_ref')
            if type(pair[1]) is not tuple or not pair[1] or len(pair[1]) > 20:
                cv._fail('phase')
            if any(type(stage) is not str or stage not in CORE_STAGES for stage in pair[1]) or len(set(pair[1])) != len(pair[1]):
                cv._fail('phase')
        if len({pair[0] for pair in operation_bindings}) != len(operation_bindings):
            cv._fail('request_ref')
        body = ('ADMIT', expected_generation, operation_bindings)
        with self._lock:
            refusal = cv.ModuleCompletion(request_id, expected_generation, 'REFUSED', None, 'NONE')
            if self._closed or self._phase != 'ACTIVE':
                return refusal
            prior = self._ledger.get(request_id)
            if prior is not None:
                return prior[1] if prior[0] == body else refusal
            # The final ledger slot preserves the once-only shutdown receipt.
            if self._generation != expected_generation or len(self._ledger) >= 63 or len(self._inflight) >= 8:
                return refusal
            ticket = ModuleTicket(_FACTORY)
            ticket._factory, ticket._original, ticket._lifecycle = _FACTORY, ticket, self
            ticket._reference, ticket._generation, ticket._bindings = request_id, self._generation, operation_bindings
            ticket._sealed, ticket._completed, ticket._sequence, ticket._children, ticket._gates = False, None, 0, 0, []
            ticket._actual_result=None
            self._ledger[request_id] = body, ticket
            self._inflight[request_id] = ticket
            return ticket

    def _ticket(self, ticket):
        if not _ticket_is_issued(self,ticket):
            cv._fail('request_ref', 'CORE_LIFECYCLE_REJECTED')

    def _new_gate(self, ticket, collector, reference, stages, parent=None):
        gate = CoreExecutionGate(_FACTORY)
        gate._factory, gate._token_lock, gate._sealed = _FACTORY, threading.Lock(), ticket._sealed
        gate._cookie = _GateCookie(gate, self, ticket, collector, reference, ticket._generation,
                                   stages, self._binding, cv._wire_digest(self._binding), parent)
        gate._issued_cookie = gate._cookie
        cookie=gate._cookie
        gate._issued_metadata=(cookie.original,cookie.lifecycle,cookie.ticket,cookie.collector,cookie.reference,
                cookie.generation,cookie.stages,cookie.binding,cookie.binding_sha256,cookie.parent)
        ticket._gates.append((gate,cookie,gate._issued_metadata))
        return gate

    def execution_gate(self, ticket, collector):
        CoreModuleLifecycle._valid(self)
        from .ash_pattern_engine.diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
        if not cv._one_of(type(collector), (ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics)):
            cv._fail('binding')
        with self._lock:
            self._ticket(ticket)
            if ticket._sealed or ticket._generation != self._generation or self._closed:
                cv._fail('generation', 'CORE_STAGE_REVOKED')
            for gate,cookie,_metadata in ticket._gates:
                if cookie.parent is None:
                    if cookie.collector is not collector:
                        cv._fail('binding')
                    return gate
            stages = tuple(dict.fromkeys(stage for pair in ticket._bindings for stage in pair[1]))
            return self._new_gate(ticket, collector, ticket._reference, stages)

    def _child_gate(self, original, reference, allowed_stage):
        CoreModuleLifecycle._valid(self)
        cv._text(reference, 'REF', 'operation_reference')
        stages = (allowed_stage,) if type(allowed_stage) is str else allowed_stage
        if type(stages) is not tuple or not stages or any(type(stage) is not str or stage not in CORE_STAGES for stage in stages):
            cv._fail('phase')
        with self._lock:
            cookie = CoreExecutionGate._cookie_for(original)
            if cookie is None or cookie.lifecycle is not self:
                cv._fail('request_ref', 'CORE_LIFECYCLE_REJECTED')
            self._ticket(cookie.ticket)
            if self._closed or cookie.ticket._sealed or cookie.ticket._generation != self._generation:
                cv._fail('generation', 'CORE_STAGE_REVOKED')
            registered = dict(cookie.ticket._bindings)
            if reference not in registered or any(stage not in registered[reference] for stage in stages):
                cv._fail('request_ref', 'CORE_LIFECYCLE_REJECTED')
            if cookie.ticket._children >= 64:
                cv._fail('request_ref', 'CORE_RESOURCE_LIMIT')
            cookie.ticket._children += 1
            return self._new_gate(cookie.ticket, cookie.collector, reference, stages, original)

    def _stage_grant(self, gate, stage):
        CoreModuleLifecycle._valid(self)
        if type(stage) is not str or stage not in CORE_STAGES:
            cv._fail('phase')
        with self._lock:
            cookie = CoreExecutionGate._cookie_for(gate)
            if cookie is None or cookie.lifecycle is not self:
                cv._fail('request_ref', 'CORE_LIFECYCLE_REJECTED')
            self._ticket(cookie.ticket)
            if stage not in cookie.stages:
                cv._fail('phase', 'CORE_LIFECYCLE_REJECTED')
            status = 'CANCELLED' if self._closed or cookie.ticket._sealed or cookie.generation != self._generation else 'GRANTED'
            if status == 'GRANTED' and cookie.ticket._sequence >= 64:
                status = 'UNAVAILABLE'
            if status == 'GRANTED':
                cookie.ticket._sequence += 1
            return CoreStageGrant(cookie.reference, stage, cookie.generation, cookie.ticket._sequence, status)

    def stop(self, request_id, *, expected_generation):
        CoreModuleLifecycle._valid(self)
        self._request(request_id, expected_generation)
        body = ('STOP', expected_generation)
        with self._lock:
            before = self._status()
            prior = self._ledger.get(request_id)
            if prior is not None and prior[0] == body:
                return prior[1]
            if self._closed or self._generation != expected_generation or prior is not None or self._generation == (1 << 64) - 1:
                return self._receipt(request_id, 'STOP', before, 'REFUSED', 'CORE_LIFECYCLE_REJECTED')
            self._closed, self._phase, self._generation = True, 'STOPPING', self._generation + 1
            for ticket in self._inflight.values():
                ticket._sealed = True
                for gate,_cookie,_metadata in ticket._gates:
                    gate._sealed = True
            if not self._inflight:
                self._phase = 'STOPPED'
            self._ledger[request_id] = body, None
            receipt = self._receipt(request_id, 'STOP', before, 'PENDING' if self._inflight else 'COMPLETED')
            self._ledger[request_id] = body, receipt
            return receipt

    def complete(self, ticket, actual_result):
        CoreModuleLifecycle._valid(self)
        # Public original-result authentication runs outside the lifecycle lock.
        authenticated = self._owner_type.validate_owned_result(self._owner, actual_result)
        with self._lock:
            self._ticket(ticket)
            if ticket._completed is not None:
                return ticket._completed if authenticated is True and actual_result is ticket._actual_result else cv.ModuleCompletion(ticket._reference,ticket._generation,'REFUSED',None,'UNKNOWN')
            if authenticated is not True:
                return cv.ModuleCompletion(ticket._reference, ticket._generation, 'REFUSED', None, 'UNKNOWN')
            if type(actual_result) is cv.CoreResult:
                reference, effect, status = actual_result.operation_reference, actual_result.effect_status, actual_result.status
            elif type(actual_result) is cv.CoreOrchestrationResult:
                reference, effect, status = actual_result.request.operation_reference, 'NONE', actual_result.status
                if actual_result.realm_shift is not None and actual_result.realm_shift.effect_status == 'PROPOSED_ONLY':
                    effect = 'PROPOSED_ONLY'
            else:
                reference = actual_result.operation_reference
                from .ash_pattern_engine import planner_emitter_values as pv
                packet = actual_result.result
                effect = 'NONE'
                if type(packet) is pv.EmitterResult:
                    if any(outcome.actual_effects is None for outcome in packet.outcomes):
                        effect = 'UNKNOWN'
                    elif packet.outcomes and all(outcome.actual_status == 'SUCCEEDED' for outcome in packet.outcomes) and packet.status == 'SUCCEEDED':
                        effect = 'KNOWN_COMPLETE'
                    elif any(outcome.actual_effects is True for outcome in packet.outcomes):
                        effect = 'KNOWN_PARTIAL'
                status = 'COMPLETED' if actual_result.status == 'CONFIRMED' else 'REFUSED' if actual_result.status == 'REFUSED' else 'PENDING'
            if reference != ticket._reference:
                return cv.ModuleCompletion(ticket._reference, ticket._generation, 'REFUSED', None, 'UNKNOWN')
            completion_status = 'INTERRUPTED' if ticket._sealed or self._closed else ('REFUSED' if status == 'REFUSED' else 'PENDING' if status == 'PENDING' else 'COMPLETED')
            completion = cv.ModuleCompletion(reference, ticket._generation, completion_status, reference, effect)
            ticket._completed, ticket._sealed = completion, True
            ticket._actual_result=actual_result
            for gate,_cookie,_metadata in ticket._gates:
                gate._sealed = True
            self._inflight.pop(reference)
            if self._phase == 'STOPPING' and not self._inflight:
                self._phase = 'STOPPED'
            return completion
