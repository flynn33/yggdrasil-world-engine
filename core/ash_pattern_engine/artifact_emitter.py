"""Acknowledged reference memory-document emission [YWE-REQ-0049]."""
from dataclasses import dataclass
import json
from threading import Lock

from . import planner_emitter_values as p
from . import state_values as s
from .state_model import StateModel
from .memory_document_target import MemoryDocumentTarget
from .generation_planner import record_reference

_OWNER = object()
_LOCK_TYPE = type(Lock())


@dataclass(slots=True)
class _Operation:
    request: p.EmitterRequest
    prepared: object
    control: p.IssuedEmitterCaptureControl
    cancelled: bool = False
    final: bool = False


class ReferenceArtifactEmitter:
    __slots__ = ("_model", "_binding", "_diagnostics", "_target", "_cookie", "_lock", "_sealed", "_operations")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("ReferenceArtifactEmitter is final")

    def __init__(self, model, binding, diagnostics, target):
        from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
        p._exact(model,StateModel,"model")
        p._exact(binding,p.PlannerEmitterBinding,"binding")
        p._exact(diagnostics,(ReferenceDevelopmentDiagnostics,ReferenceReleaseDiagnostics),"diagnostics")
        p._exact(target,MemoryDocumentTarget,"target")
        self._model,self._binding,self._diagnostics,self._target=model,binding,diagnostics,target
        self._lock=Lock()
        self._sealed=False
        self._operations={}
        self._cookie=(_OWNER,self,model,binding,diagnostics,target,self._lock,self._operations)
        ReferenceArtifactEmitter.configuration(self)

    def configuration(self):
        p._exact(self,ReferenceArtifactEmitter,"emitter")
        cookie=self._cookie
        if (type(cookie) is not tuple or len(cookie)!=8 or cookie[0] is not _OWNER or cookie[1] is not self or
                any(actual is not expected for actual,expected in zip(cookie[2:],
                    (self._model,self._binding,self._diagnostics,self._target,self._lock,self._operations))) or
                type(self._lock) is not _LOCK_TYPE or type(self._sealed) is not bool or
                type(self._operations) is not dict or len(self._operations)>64):
            p._fail("emitter","VALUE_CORRUPT")
        for reference,operation in self._operations.items():
            p._ref(reference,maximum=160)
            if not _operation_fields(operation,reference):
                p._fail("emitter","VALUE_CORRUPT")
        p.revalidate_value(self._binding)
        canonical,profile=p._model_bindings(self._model)
        if (self._binding.canonical_binding!=canonical or
                self._binding.profile_binding!=profile or
                self._binding.policy_binding!=MemoryDocumentTarget.configuration(self._target).policy_binding):
            p._fail("binding","SOURCE_UNRECOGNIZED")
        return self._binding

    def validate_owned_result(self, result):
        if type(self) is not ReferenceArtifactEmitter:
            return False
        try:
            binding=ReferenceArtifactEmitter.configuration(self)
            return p._result_is_owned(result,self,(p.EmitterResult,)) and result.binding==binding
        except (p.PlannerEmitterContractError,s.StateContractError,AttributeError,ValueError):
            return False

    def validate_preparation_composition(self, collector, target):
        from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
        if (type(self) is not ReferenceArtifactEmitter or
                type(collector) is not ReferenceDevelopmentDiagnostics and type(collector) is not ReferenceReleaseDiagnostics or
                type(target) is not MemoryDocumentTarget):
            return False
        try:
            ReferenceArtifactEmitter.configuration(self)
            return self._diagnostics is collector and self._target is target
        except (p.PlannerEmitterContractError,s.StateContractError,AttributeError,ValueError):
            return False

    def cancel(self, operation_reference):
        ReferenceArtifactEmitter.configuration(self)
        p._ref(operation_reference,maximum=160)
        with self._lock:
            operation=self._operations.get(operation_reference)
            if operation is None:
                return p.CancellationObservation(operation_reference,"UNKNOWN_OPERATION")
            if operation.final:
                return p.CancellationObservation(operation_reference,"ALREADY_FINAL")
            operation.cancelled=True
            p._seal_emitter_control(operation.control)
            return p.CancellationObservation(operation_reference,"LATCHED")

    def shutdown(self):
        ReferenceArtifactEmitter.configuration(self)
        with self._lock:
            already=self._sealed
            self._sealed=True
            active=tuple(operation for operation in self._operations.values() if not operation.final)
            for operation in active:
                operation.cancelled=True
                p._seal_emitter_control(operation.control)
        from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
        cls=ReferenceDevelopmentDiagnostics if type(self._diagnostics) is ReferenceDevelopmentDiagnostics else ReferenceReleaseDiagnostics
        try:
            unused=cls.release_preparations_for_emitter(self._diagnostics,self)
        except Exception:
            unused=None
        return p.OwnerShutdownObservation("ALREADY_SEALED" if already else "SEALED",len(active),unused)

    def emit(self, prepared, *, execution_gate=None):
        return _emit(self,prepared,execution_gate)


def _gate_active(gate):
    if gate is None:
        return True
    from core.module_lifecycle import CoreExecutionGate
    if type(gate) is not CoreExecutionGate:
        p._fail("execution_gate")
    return CoreExecutionGate.capture_disposition(gate)=="ACTIVE"


def _stage(gate, stage):
    if gate is None:
        return True
    from core.module_lifecycle import CoreExecutionGate
    if type(gate) is not CoreExecutionGate:
        p._fail("execution_gate")
    return CoreExecutionGate.stage_grant(gate,stage).status=="GRANTED"


def _emit(owner,prepared,gate):
    # The complete effectful composition follows the issued preparation and scope ports.
    from .diagnostic_module_values import PreparedEmission
    binding=ReferenceArtifactEmitter.configuration(owner)
    request,target=PreparedEmission.configuration(prepared)
    p._exact(request,p.EmitterRequest,"request")
    if target is not owner._target or request.plan.binding!=binding:
        p._fail("preparation","VALUE_CORRUPT")
    origin,dependency=PreparedEmission.origin_and_dependency(prepared)
    p._exact(origin,s.StateDiagnosis,"origin")
    p._exact(dependency,p.PlannerResult,"dependency")
    if dependency.plan is not request.plan or dependency.request.final_origin_diagnosis is not origin:
        p._fail("preparation","VALUE_CORRUPT")
    _validate_gate(owner,gate,request.operation_reference)
    return _emit_request(owner,binding,prepared,request,origin,dependency,gate)


def _validate_gate(owner,gate,reference):
    if gate is None:
        return
    from core.module_lifecycle import CoreExecutionGate
    if (type(gate) is not CoreExecutionGate or
            CoreExecutionGate.validate_issued_for_collector(gate,owner._diagnostics,reference) is not True):
        p._fail("execution_gate")
    _collector,_op,canonical,profile,_generation=CoreExecutionGate.configuration(gate)
    if canonical!=owner._binding.canonical_binding or profile!=owner._binding.profile_binding:
        p._fail("execution_gate","SOURCE_UNRECOGNIZED")


def _collector_class(owner):
    from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
    return ReferenceDevelopmentDiagnostics if type(owner._diagnostics) is ReferenceDevelopmentDiagnostics else ReferenceReleaseDiagnostics


def _active(owner,operation,gate):
    # These token reads never enter the Core owner or collector.
    cookie=owner._cookie
    if (type(cookie) is not tuple or len(cookie)!=8 or cookie[0] is not _OWNER or cookie[1] is not owner or
            type(owner._lock) is not _LOCK_TYPE or cookie[6] is not owner._lock or
            type(owner._sealed) is not bool or not _operation_fields(operation)):
        return False
    with owner._lock:
        active=not owner._sealed and not operation.cancelled and not operation.final
    return active and _gate_active(gate) and p.IssuedEmitterCaptureControl.capture_disposition(operation.control)=="ACTIVE"


def _operation_fields(operation,reference=None):
    if (type(operation) is not _Operation or type(operation.cancelled) is not bool or
            type(operation.final) is not bool or type(operation.request) is not p.EmitterRequest or
            type(operation.request.operation_reference) is not str or
            type(operation.control) is not p.IssuedEmitterCaptureControl):
        return False
    return reference is None or operation.request.operation_reference==reference


def _effect(outcomes):
    return True if any(row.actual_effects is True for row in outcomes) else None if any(row.actual_effects is None for row in outcomes) else False


def _status(request,outcomes,code):
    if any(row.actual_effects is None for row in outcomes):
        return "UNKNOWN"
    if code is not None or len(outcomes)!=len(request.plan.artifacts) or any(row.actual_status=="FAILED" for row in outcomes):
        return "PARTIAL" if any(row.actual_effects is True for row in outcomes) else "FAILED"
    return "SUCCEEDED" if any(row.actual_effects is True for row in outcomes) else "NO_OP"


def _record(request,origin,payload,ordinal,parent,severity,failed=False):
    root=origin.emitted_diagnostics[0]
    current=max((severity,"ERROR" if failed else "INFO"),key=p.SEVERITIES.index)
    phase=("dispatch" if type(payload) is p.EmissionDispatchDiagnostic else
           "outcome" if type(payload) is p.EmissionOutcomeDiagnostic else "summary")
    envelope=p.PlannerEmitterEnvelope("ARTIFACT_EMISSION",current,"PROCESSING","BLOCKED" if failed else "RESOLVED",
             root.envelope.subject_reference,parent,root.envelope.chain_root_reference,
             ("ASH-GENERATION-TRACEABILITY-001","ASH-GENERATION-PLANFIDELITY-001","ASH-GENERATION-EMISSION-001"),
             {"dispatch":"Specified artifact dispatch constructed.","outcome":"Actual target outcome observed.",
              "summary":"Actual artifact emission prefix summarized."}[phase],
             ("Target effect truth is independent of diagnostic capture.",))
    return p.PlannerEmitterRecord(record_reference(request.operation_reference,ordinal),envelope,payload)


def _append(scope,record):
    from .diagnostic_module_capture import ModuleCaptureScope
    try:
        receipt=ModuleCaptureScope.append(scope,record)
        if type(receipt) is s.CaptureReceipt:
            s.CaptureReceipt.__post_init__(receipt)
            return receipt.status=="CONFIRMED" and receipt.diagnostic_reference==record.diagnostic_reference
    except Exception:
        pass
    return False


def _unknown(request,artifact,code):
    return p.MemoryTargetReceipt(request.operation_reference,artifact.artifact_reference,artifact.plan_element_reference,
           request.target_configuration.target_reference,"UNKNOWN",None,artifact.content_sha256,None,
           artifact.content_byte_count,None,None,None,"UNAVAILABLE",code)


def _anticipated_raw_bytes(request,binding,origin,records,outcomes,next_index):
    """Closed sizing only: actual prefix plus the largest remaining emitted branches."""
    failure=max(p.FIELD_SCHEMAS['EmitterResult']['failure_code']['anyOf'][0]['enum'],key=len)
    capture_failure=max(p.FIELD_SCHEMAS['PlannerEmitterCaptureReceipt']['failure_code']['anyOf'][0]['enum'],key=len)
    future_outcomes=list(outcomes)
    future_records=list(records)
    parent=records[-1].diagnostic_reference if records else origin.emitted_diagnostics[0].diagnostic_reference
    for index,artifact in enumerate(request.plan.artifacts[next_index:],next_index):
        dispatch=p.EmissionDispatchDiagnostic(request.operation_reference,request.plan.plan_reference,
                 artifact.artifact_reference,artifact.plan_element_reference,index,artifact.content_sha256,
                 artifact.content_byte_count,request.target_configuration.target_reference)
        if not (future_records and type(future_records[-1].payload) is p.EmissionDispatchDiagnostic and
                future_records[-1].payload.artifact_index==index):
            row=_record(request,origin,dispatch,2*index,parent,"CRITICAL")
            future_records.append(row);parent=row.diagnostic_reference
        actual=p.MemoryTargetReceipt(request.operation_reference,artifact.artifact_reference,artifact.plan_element_reference,
               request.target_configuration.target_reference,"FAILED",False,artifact.content_sha256,"f"*64,
               artifact.content_byte_count,32768,(1<<64)-2,(1<<64)-1,"OWNED_EXACT_READBACK",failure)
        future_outcomes.append(actual)
        row=_record(request,origin,p.EmissionOutcomeDiagnostic(parent,actual),2*index+1,parent,"CRITICAL",True)
        future_records.append(row);parent=row.diagnostic_reference
    summary=p.EmissionSummaryDiagnostic(request.operation_reference,request.plan.plan_reference,"SUCCEEDED",
            len(request.plan.artifacts),len(request.plan.artifacts),len(request.plan.artifacts),False,failure)
    future_records.append(_record(request,origin,summary,2*len(request.plan.artifacts),parent,"CRITICAL",True))
    pending=p.PendingPlannerEmitterDiagnostic(future_records[-1].diagnostic_reference,"ARTIFACT_EMISSION",
            "OPERATION_SUMMARY",failure,"CAPTURE_NOT_CONFIRMED")
    result={"request":request.to_record(),"binding":binding.to_record(),"status":"SUCCEEDED","actual_effects":False,
            "outcomes":[row.to_record() for row in future_outcomes],
            "produced_diagnostics":[row.to_record() for row in future_records],"pending_summary":pending.to_record(),
            "failure_code":failure,"schema_version":"1.0.0","packet_kind":"emitter_result"}
    observer={"operation_reference":request.operation_reference,"status":"NOT_CONFIRMED","supporting_reference":"ref:999999",
              "coverage":"COMPLETE_SPECIFIED_SAFE_GRAPH","failure_code":"MODULE_FINAL_OBSERVATION_REJECTED"}
    wrapper={"operation_reference":request.operation_reference,"status":"NOT_CONFIRMED","result":result,
             "confirmed_records":[row.diagnostic_reference for row in future_records],
             "attempted_record":max((row.to_record() for row in future_records),key=lambda row:len(json.dumps(row,ensure_ascii=True,separators=(",",":")))),
             "completion":None,"final_observation":observer,"failure_code":capture_failure,
             "schema_version":"1.0.0","packet_kind":"planner_emitter_capture_receipt"}
    # Complete source-owned completion-wire maximum, independently schema-tested.
    return len(json.dumps(wrapper,sort_keys=True,ensure_ascii=True,separators=(",",":"),allow_nan=False).encode("ascii"))-4+14356


def _emit_request(owner,binding,prepared,request,origin,dependency,gate):
    from . import diagnostic_module_values as mv
    from . import diagnostics_values as dv
    from .diagnostic_module_capture import ModuleCaptureScope
    cls=_collector_class(owner)
    count=len(request.plan.artifacts)
    slots=tuple(record_reference(request.operation_reference,index) for index in range(2*count+1))
    control=p._issue_emitter_control(owner,owner._diagnostics,request.operation_reference,prepared,slots)
    operation=_Operation(request,prepared,control)
    code=None
    with owner._lock:
        if owner._sealed: code="COMMAND_CANCELLED"
        elif request.operation_reference in owner._operations: code="PREPARATION_USED"
        elif len(owner._operations)>=64: code="PREPARATION_LIMIT"
        elif any(not item.final for item in owner._operations.values()): code="EMITTER_BUSY"
        else: owner._operations[request.operation_reference]=operation
    records,outcomes,confirmed=[],[],[]
    scope=None;attempted=None;appendable=True
    root=origin.emitted_diagnostics[0]
    parent,severity=root.diagnostic_reference,root.envelope.severity
    if code is None and request.plan.warnings and not request.plan.target_constraints.allow_declared_axiom_failures:
        code="AXIOM_FAILURE_NOT_AUTHORIZED"
    if code is None and _anticipated_raw_bytes(request,binding,origin,(),(),0)>p.RAW_BUSINESS_LIMIT:
        code="RAW_BUSINESS_LIMIT"
    if code is None and (not _active(owner,operation,gate) or not _stage(gate,"EMISSION_PREPARE")):
        code="COMMAND_CANCELLED"
    if code is None:
        context=mv.ModuleCaptureContext(request.operation_reference,"ARTIFACT_EMITTER",binding,origin,request,(dependency,))
        try:
            admission=cls.module_capture(owner._diagnostics,owner,context,execution_gate=gate,emitter_control=control)
            if type(admission) is mv.ModuleCaptureAdmission:
                # A genuine allocated scope gets cleanup even with a wrong admission response.
                if ModuleCaptureScope.validate_issued_for_context(admission.scope,owner._diagnostics,owner,context,
                        execution_gate=gate,emitter_control=control) is True:
                    scope=admission.scope
                mv.ModuleCaptureAdmission.__post_init__(admission)
                if admission.status!="ADMITTED" or admission.operation_reference!=request.operation_reference or scope is None:
                    code="CAPTURE_ADMISSION_UNCONFIRMED";appendable=False
            else: code="CAPTURE_ADMISSION_UNCONFIRMED";appendable=False
        except Exception:
            code="CAPTURE_ADMISSION_UNCONFIRMED";appendable=False
    for index,artifact in enumerate(request.plan.artifacts):
        if code is not None: break
        if not _active(owner,operation,gate): code="COMMAND_CANCELLED";break
        dispatch=p.EmissionDispatchDiagnostic(request.operation_reference,request.plan.plan_reference,artifact.artifact_reference,
                 artifact.plan_element_reference,index,artifact.content_sha256,artifact.content_byte_count,
                 request.target_configuration.target_reference)
        row=_record(request,origin,dispatch,2*index,parent,severity)
        records.append(row);parent,severity=row.diagnostic_reference,row.envelope.severity
        if not _append(scope,row):
            attempted=row;appendable=False;code="DISPATCH_UNCONFIRMED";break
        confirmed.append(row.diagnostic_reference)
        if not _active(owner,operation,gate): code="COMMAND_CANCELLED";break
        if _anticipated_raw_bytes(request,binding,origin,records,outcomes,index)>p.RAW_BUSINESS_LIMIT:
            code="RAW_BUSINESS_LIMIT";break
        try:
            revision=MemoryDocumentTarget.snapshot(owner._target).revision
        except Exception:
            code="TARGET_BUSY";break
        if not _active(owner,operation,gate) or not _stage(gate,"EMISSION_DISPATCH"):
            code="COMMAND_CANCELLED";break
        with owner._lock:
            if (type(owner._sealed) is not bool or not _operation_fields(operation) or
                    owner._sealed or operation.cancelled or operation.final or not _gate_active(gate)):
                lease=None
            else:
                lease=p._issue_action_lease(owner,owner._target,request.operation_reference,artifact,revision)
        if lease is None: code="COMMAND_CANCELLED";break
        try:
            receipt=MemoryDocumentTarget.materialize(owner._target,lease,artifact)
            if not p._result_is_owned(receipt,owner._target,(p.MemoryTargetReceipt,)):
                receipt=_unknown(request,artifact,"TARGET_RECEIPT_FOREIGN")
            elif (receipt.operation_reference!=request.operation_reference or receipt.artifact_reference!=artifact.artifact_reference or
                  receipt.plan_element_reference!=artifact.plan_element_reference or
                  receipt.target_reference!=request.target_configuration.target_reference or receipt.expected_sha256!=artifact.content_sha256 or
                  receipt.expected_byte_count!=artifact.content_byte_count):
                receipt=_unknown(request,artifact,"TARGET_READBACK_MISMATCH")
        except Exception:
            receipt=_unknown(request,artifact,"TARGET_EFFECT_UNKNOWN")
        outcomes.append(receipt)
        row=_record(request,origin,p.EmissionOutcomeDiagnostic(record_reference(request.operation_reference,2*index),receipt),
                    2*index+1,parent,severity,receipt.actual_status in ("FAILED","UNKNOWN"))
        records.append(row);parent,severity=row.diagnostic_reference,row.envelope.severity
        if not _active(owner,operation,gate):
            attempted=row;appendable=False;code="COMMAND_CANCELLED";break
        if not _append(scope,row):
            attempted=row;appendable=False;code="OUTCOME_CAPTURE_UNCONFIRMED";break
        confirmed.append(row.diagnostic_reference)
        if receipt.actual_status in ("FAILED","UNKNOWN"):
            code=receipt.failure_code or "TARGET_EFFECT_UNKNOWN";break
    status=_status(request,outcomes,code)
    successful=sum(row.actual_status in ("SUCCEEDED","NO_EFFECT") for row in outcomes)
    summary=p.EmissionSummaryDiagnostic(request.operation_reference,request.plan.plan_reference,status,count,len(outcomes),
            successful,_effect(outcomes),code)
    row=_record(request,origin,summary,2*count,parent,severity,code is not None)
    records.append(row)
    pending=None
    if scope is not None and appendable and _active(owner,operation,gate):
        if _append(scope,row): confirmed.append(row.diagnostic_reference)
        else: attempted=row;code=code or "SUMMARY_CAPTURE_UNCONFIRMED"
    else:
        pending=p.PendingPlannerEmitterDiagnostic(row.diagnostic_reference,"ARTIFACT_EMISSION","OPERATION_SUMMARY",
                code or "COMMAND_CANCELLED","CAPTURE_NOT_APPENDABLE" if scope is not None else "CAPABILITY_REFUSED")
    result=p._seal_result(p.EmitterResult(request,binding,_status(request,outcomes,code),_effect(outcomes),tuple(outcomes),
                            tuple(records),pending,code),owner)
    completion=observer=None
    capture_code=code if scope is None or attempted is not None or pending is not None else None
    if scope is not None:
        try:
            response=ModuleCaptureScope.finish(scope,result)
            if type(response) is dv.DiagnosticsCompletionReceipt: completion=response
        except Exception: pass
        try:
            response=ModuleCaptureScope.observe_final(scope,result,completion)
            if type(response) is mv.ModuleFinalObservationReceipt: observer=response
        except Exception: pass
        try: cls.audit_module_return(owner._diagnostics,scope,boundary="RETURN")
        except Exception: pass
        if (completion is None or completion.status!="COMPLETE" or completion.operation_reference!=request.operation_reference or
                observer is None or observer.status!="CONFIRMED" or observer.operation_reference!=request.operation_reference):
            capture_code="COMPLETION_UNCONFIRMED"
    capture=p.PlannerEmitterCaptureReceipt(request.operation_reference,"CONFIRMED" if capture_code is None else "NOT_CONFIRMED",
            result,tuple(confirmed),attempted,completion,observer,capture_code)
    capture=p._seal_result(capture,owner)
    with owner._lock:
        operation.final=True
    return capture
