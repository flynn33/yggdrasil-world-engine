"""Owned ordered composition and actual capture of complete generation [YWE-REQ-0049]."""
from . import planner_emitter_values as p
from . import state_values as s
from . import generation_values as g
from . import realm_transition_values as rt
from . import diagnostic_module_values as mv
from . import diagnostics_values as dv
from .state_model import StateModel
from .realm_transition import RealmEncoder, TransitionRegistry
from .topology import ReferenceTopologyGenerator
from .axioms import ReferenceAxiomEvaluator
from .generation_planner import ReferenceGenerationPlanner
from .artifact_emitter import ReferenceArtifactEmitter, _gate_active, _stage
from .memory_document_target import MemoryDocumentTarget

_OWNER=object()


class ReferenceGenerationRunner:
    __slots__=("_model","_diagnostics","_encoder","_registry","_topology","_axioms","_planner","_emitter","_cookie")

    def __init_subclass__(cls,**kwargs):
        raise TypeError("ReferenceGenerationRunner is final")

    def __init__(self,model,diagnostics,encoder,registry,topology,axioms,planner,emitter):
        from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
        for value,cls,field in ((model,StateModel,"model"),(encoder,RealmEncoder,"encoder"),
                (registry,TransitionRegistry,"registry"),(topology,ReferenceTopologyGenerator,"topology"),
                (axioms,ReferenceAxiomEvaluator,"axioms"),(planner,ReferenceGenerationPlanner,"planner"),
                (emitter,ReferenceArtifactEmitter,"emitter")):
            p._exact(value,cls,field)
        p._exact(diagnostics,(ReferenceDevelopmentDiagnostics,ReferenceReleaseDiagnostics),"diagnostics")
        self._model,self._diagnostics,self._encoder,self._registry=model,diagnostics,encoder,registry
        self._topology,self._axioms,self._planner,self._emitter=topology,axioms,planner,emitter
        self._cookie=(_OWNER,self,model,diagnostics,encoder,registry,topology,axioms,planner,emitter)
        ReferenceGenerationRunner.configuration(self)

    def configuration(self,*,state_model=None,diagnostics=None):
        p._exact(self,ReferenceGenerationRunner,"runner")
        cookie=self._cookie
        actual=(self._model,self._diagnostics,self._encoder,self._registry,self._topology,self._axioms,self._planner,self._emitter)
        if (type(cookie) is not tuple or len(cookie)!=10 or cookie[0] is not _OWNER or cookie[1] is not self or
                any(a is not b for a,b in zip(cookie[2:],actual))):
            p._fail("runner","VALUE_CORRUPT")
        if state_model is not None:
            p._exact(state_model,StateModel,"state_model")
            if state_model is not self._model:
                p._fail("state_model","VALUE_CORRUPT")
        if diagnostics is not None:
            from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
            p._exact(diagnostics,(ReferenceDevelopmentDiagnostics,ReferenceReleaseDiagnostics),"diagnostics")
            if diagnostics is not self._diagnostics:
                p._fail("diagnostics","VALUE_CORRUPT")
        binding=ReferenceGenerationPlanner.configuration(self._planner)
        if binding!=ReferenceArtifactEmitter.configuration(self._emitter):
            p._fail("binding","SOURCE_UNRECOGNIZED")
        canonical,profile=p._model_bindings(self._model)
        if binding.canonical_binding!=canonical or binding.profile_binding!=profile:
            p._fail("binding","SOURCE_UNRECOGNIZED")
        for cls,owner in ((RealmEncoder,self._encoder),(TransitionRegistry,self._registry)):
            peer=cls.configuration(owner)
            if peer.canonical_binding!=binding.canonical_binding or peer.profile_binding!=binding.profile_binding:
                p._fail("binding","SOURCE_UNRECOGNIZED")
        for cls,owner in ((ReferenceTopologyGenerator,self._topology),(ReferenceAxiomEvaluator,self._axioms)):
            source,profile,_policy=cls.configuration(owner)
            if source.canonical_binding!=binding.canonical_binding or profile!=binding.profile_binding:
                p._fail("binding","SOURCE_UNRECOGNIZED")
        return binding

    def validate_owned_result(self,result):
        if type(self) is not ReferenceGenerationRunner:
            return False
        try:
            binding=ReferenceGenerationRunner.configuration(self)
            if not p._result_is_owned(result,self,(p.GenerationRunReceipt,p.PlannerEmitterCaptureReceipt)):
                return False
            if type(result) is p.GenerationRunReceipt:
                if result.status!="READY": return True
                capture=result.last_observation
                if (capture.status!="CONFIRMED" or not _completed(capture) or
                        not ReferenceGenerationPlanner.validate_owned_result(self._planner,capture.result) or
                        type(capture.result) is not p.PlannerResult or capture.result.binding!=binding):
                    return False
                return (result.completed_operation_references[-1]==capture.operation_reference and
                        capture.operation_reference==result.operation_reference+":planner")
            return (type(result.result) is p.EmitterResult and
                    ReferenceArtifactEmitter.validate_owned_result(self._emitter,result.result) and
                    result.result.binding==binding)
        except (p.PlannerEmitterContractError,s.StateContractError,rt.RealmTransitionContractError,
                g.GenerationContractError,mv.ModuleContractError,AttributeError,ValueError):
            return False

    def run(self,inputs,origin,declared_subject,target_constraints,*,operation_reference,execution_gate=None):
        return _run(self,inputs,origin,declared_subject,target_constraints,operation_reference,execution_gate)

    def emit(self,actual_plan_capture,target,*,operation_reference,execution_gate=None):
        binding=ReferenceGenerationRunner.configuration(self)
        p._exact(actual_plan_capture,p.PlannerEmitterCaptureReceipt,"capture")
        p._exact(target,MemoryDocumentTarget,"target")
        p._ref(operation_reference,maximum=160)
        p.revalidate_value(actual_plan_capture)
        if (type(actual_plan_capture.result) is not p.PlannerResult or actual_plan_capture.status!="CONFIRMED" or
                not _completed(actual_plan_capture) or
                not ReferenceGenerationPlanner.validate_owned_result(self._planner,actual_plan_capture.result) or
                actual_plan_capture.result.binding!=binding):
            p._fail("capture","VALUE_CORRUPT")
        if not ReferenceArtifactEmitter.validate_preparation_composition(self._emitter,self._diagnostics,target):
            p._fail("target","VALUE_CORRUPT")
        _gate(self,execution_gate,operation_reference)
        if not _gate_active(execution_gate) or not _stage(execution_gate,"EMISSION_PREPARE"):
            return _preparation_failure(self,actual_plan_capture,target,operation_reference,"COMMAND_CANCELLED")
        cls=_collector(self)
        admission=cls.prepare_emission(self._diagnostics,self._planner,actual_plan_capture.result,
                actual_plan_capture,self._emitter,target,operation_reference=operation_reference,execution_gate=execution_gate)
        if type(admission) is not mv.EmissionPreparationAdmission:
            p._fail("preparation","VALUE_CORRUPT")
        if admission.prepared is None:
            return _preparation_failure(self,actual_plan_capture,target,operation_reference,admission.receipt.failure_code or "PREPARATION_FOREIGN")
        capture=ReferenceArtifactEmitter.emit(self._emitter,admission.prepared,execution_gate=execution_gate)
        p._exact(capture,p.PlannerEmitterCaptureReceipt,"capture")
        if (not ReferenceArtifactEmitter.validate_owned_result(self._emitter,capture.result) or
                capture.operation_reference!=operation_reference):
            p._fail("capture","VALUE_CORRUPT")
        # The wrapper remains the actual same object; only API-only runner-return seal changes.
        return p._seal_result(capture,self)


def _collector(owner):
    from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
    return ReferenceDevelopmentDiagnostics if type(owner._diagnostics) is ReferenceDevelopmentDiagnostics else ReferenceReleaseDiagnostics


def _gate(owner,gate,reference):
    if gate is None:return
    from core.module_lifecycle import CoreExecutionGate
    if (type(gate) is not CoreExecutionGate or
            CoreExecutionGate.validate_issued_for_collector(gate,owner._diagnostics,reference) is not True):
        p._fail("execution_gate")
    _collector,_op,canonical,profile,_generation=CoreExecutionGate.configuration(gate)
    binding=ReferenceGenerationRunner.configuration(owner)
    if canonical!=binding.canonical_binding or profile!=binding.profile_binding:
        p._fail("execution_gate","SOURCE_UNRECOGNIZED")


def _child(gate,reference,stage):
    if gate is None:return True,None
    from core.module_lifecycle import CoreExecutionGate
    from core.core_values import CoreContractError
    try:
        return True,CoreExecutionGate.for_operation(gate,reference,stage)
    except CoreContractError as error:
        if error.code in ("CORE_STAGE_REVOKED","CORE_RESOURCE_LIMIT"):
            return False,None
        raise


def _completed(capture):
    return (capture.completion is not None and capture.completion.status=="COMPLETE" and
            capture.completion.operation_reference==capture.operation_reference and
            capture.final_observation is not None and capture.final_observation.status=="CONFIRMED" and
            capture.final_observation.operation_reference==capture.operation_reference and capture.attempted_record is None)


def _facts(result):
    if p._is(result,(p.TransitionChainResult,p.TransitionChainFailure)):
        return result.operation_reference,result.origin,result.constructed_records
    if p._is(result,rt.RESULT_TYPES):
        return result.operation_reference,result.origin,result.constructed_records
    if p._is(result,g.PACKET_TYPES):
        return result.request.request_reference,result.request.origin_diagnosis,result.produced_diagnostics
    return result.request.operation_reference,result.request.final_origin_diagnosis,result.produced_diagnostics


def _record_ref(record):
    return record.record_reference if p._is(record,(rt.RealmTransitionRecord,p.ChainRecord)) else record.diagnostic_reference


def _capture(owner,producer,result,kind,gate,dependencies):
    from .diagnostic_module_capture import ModuleCaptureScope
    reference,origin,records=_facts(result)
    wrapper=p.PlannerEmitterCaptureReceipt if p._is(result,(p.PlannerResult,p.PlannerFailure)) else p.GenerationDependencyCaptureReceipt
    scope=None;confirmed=[];attempted=None;completion=observer=None;failure=None
    if not _gate_active(gate) or not _stage(gate,kind):
        failure="MODULE_CAPTURE_UNCONFIRMED"
    else:
        context=mv.ModuleCaptureContext(reference,{
            "SOURCE_ENCODING":"REALM_ENCODER","CHAIN":"TRANSITION_REGISTRY","DESTINATION_ENCODING":"REALM_ENCODER",
            "TOPOLOGY":"TOPOLOGY_GENERATOR","AXIOMS":"AXIOM_EVALUATOR","PLANNER":"GENERATION_PLANNER"}[kind],
            type(producer).configuration(producer),origin,result,dependencies)
        try:
            admission=_collector(owner).module_capture(owner._diagnostics,producer,context,execution_gate=gate)
            if type(admission) is mv.ModuleCaptureAdmission:
                if ModuleCaptureScope.validate_issued_for_context(admission.scope,owner._diagnostics,producer,context,
                        execution_gate=gate) is True:
                    scope=admission.scope
                mv.ModuleCaptureAdmission.__post_init__(admission)
                if admission.status!="ADMITTED" or admission.operation_reference!=reference or scope is None:
                    failure=admission.failure_code or "MODULE_CAPTURE_UNCONFIRMED"
            else:failure="MODULE_CAPTURE_UNCONFIRMED"
        except Exception:failure="MODULE_CAPTURE_UNCONFIRMED"
    if scope is not None:
        if failure is None:
            for record in records:
                if not _gate_active(gate):
                    attempted=record;failure="MODULE_CAPTURE_UNCONFIRMED";break
                try:
                    response=ModuleCaptureScope.append(scope,record)
                    reference_record=_record_ref(record)
                    if (type(response) is not s.CaptureReceipt or response.status!="CONFIRMED" or
                            response.diagnostic_reference!=reference_record):
                        attempted=record;failure="MODULE_CAPTURE_UNCONFIRMED";break
                    confirmed.append(reference_record)
                except Exception:
                    attempted=record;failure="MODULE_CAPTURE_UNCONFIRMED";break
        try:
            response=ModuleCaptureScope.finish(scope,result)
            if type(response) is dv.DiagnosticsCompletionReceipt:completion=response
        except Exception:pass
        try:
            response=ModuleCaptureScope.observe_final(scope,result,completion)
            if type(response) is mv.ModuleFinalObservationReceipt:observer=response
        except Exception:pass
        try:_collector(owner).audit_module_return(owner._diagnostics,scope,boundary="RETURN")
        except Exception:pass
        if (completion is None or completion.status!="COMPLETE" or completion.operation_reference!=reference or
                observer is None or observer.status!="CONFIRMED" or observer.operation_reference!=reference):
            failure=failure or "MODULE_COMPLETION_REJECTED"
    captured=wrapper(reference,"CONFIRMED" if failure is None else "NOT_CONFIRMED",result,tuple(confirmed),attempted,
                     completion,observer,failure)
    return p._seal_result(captured,owner) if wrapper is p.PlannerEmitterCaptureReceipt else captured


def _run(owner,inputs,origin,subject,constraints,reference,gate):
    binding=ReferenceGenerationRunner.configuration(owner)
    p._exact(inputs,p.GenerationInputs,"inputs");p.revalidate_value(inputs)
    p._exact(origin,s.StateDiagnosis,"origin")
    p._exact(subject,g.AxiomSubject,"subject");g.revalidate_value(subject)
    p._exact(constraints,p.TargetConstraints,"constraints");p.revalidate_value(constraints)
    p._ref(reference,maximum=128);_gate(owner,gate,reference)
    completed=[]
    def finish(status,stage,observation,origin_completion=None):
        return p._seal_result(p.GenerationRunReceipt(reference,status,stage,observation,origin_completion,tuple(completed)),owner)
    validation=StateModel.validate_diagnosis(owner._model,origin)
    if (validation.status!="VERIFIED" or origin.parsed_state is None or not origin.state_validity_diagnostic.is_valid or
            inputs.profile_id!=binding.profile_binding.profile_id):
        return finish("REFUSED","ORIGIN",origin)
    if not _gate_active(gate):return finish("NOT_CONFIRMED","ORIGIN",origin)
    results=[]
    # Each of these six stages owns one computation grant and one capture grant.
    for stage,suffix,producer in (("SOURCE_ENCODING",":source",owner._encoder),("CHAIN",":chain",owner._registry)):
        available,child=_child(gate,reference+suffix,stage)
        if not available or not _stage(child,stage):return finish("NOT_CONFIRMED","ORIGIN" if not results else "SOURCE_ENCODING",origin if not results else capture)
        result=(RealmEncoder.encode(producer,origin,operation_reference=reference+suffix) if stage=="SOURCE_ENCODING" else
                TransitionRegistry.apply_chain(producer,origin,inputs.transition_sequence,operation_reference=reference+suffix))
        capture=_capture(owner,producer,result,stage,child,tuple(results))
        if capture.status!="CONFIRMED":return finish("NOT_CONFIRMED",stage,capture)
        completed.append(reference+suffix)
        if type(result) is rt.RealmTransitionFailure or type(result) is p.TransitionChainFailure:
            return finish("REFUSED",stage,capture)
        results.append(result)
    available,child=_child(gate,reference+":final","FINAL_DIAGNOSIS")
    if not available or not _stage(child,"FINAL_DIAGNOSIS"):return finish("NOT_CONFIRMED","CHAIN",capture)
    cls=_collector(owner)
    try:
        capture_port=cls.assessment_capture(owner._diagnostics,execution_gate=child)
        # Fresh owned model prevents caller-assigned instance math/codec hooks in a new actual diagnosis.
        fresh_model=StateModel(binding.profile_binding,binding.canonical_binding,capture_port)
        final=StateModel.diagnose(fresh_model,results[1].last_candidate,diagnostic_context=s.DiagnosticContext(
              reference+":final",reference+":final:input",reference+":final:detection",reference+":final:classification"))
    except dv.DiagnosticsContractError:
        return finish("NOT_CONFIRMED","CHAIN",capture)
    first=None
    try:
        response=cls.complete_assessment(owner._diagnostics,final)
        if type(response) is dv.DiagnosticsCompletionReceipt:first=response
    except Exception:pass
    if (type(final) is not s.StateDiagnosis or first is None or first.status!="COMPLETE" or
            first.operation_reference!=reference+":final" or not final.state_validity_diagnostic.is_valid):
        return finish("NOT_CONFIRMED","FINAL_DIAGNOSIS",final,first)
    completed.append(reference+":final")
    if not _gate_active(gate):return finish("NOT_CONFIRMED","FINAL_DIAGNOSIS",final,first)
    # Only provenance/state/ref association is rebound; all explicitly declared measures stay exact.
    from dataclasses import replace
    actual_subject=replace(subject,state=final.parsed_state,provenance=replace(subject.provenance,
            origin_diagnosis_reference=final.assessment_binding.diagnosis_reference))
    for stage,suffix,producer in (("DESTINATION_ENCODING",":destination",owner._encoder),
                                  ("TOPOLOGY",":topology",owner._topology),("AXIOMS",":axioms",owner._axioms),
                                  ("PLANNER",":planner",owner._planner)):
        available,child=_child(gate,reference+suffix,stage)
        if not available or not _stage(child,stage):return finish("NOT_CONFIRMED","FINAL_DIAGNOSIS" if len(results)==2 else previous_stage,
                                                final if len(results)==2 else capture,first if len(results)==2 else None)
        if stage=="DESTINATION_ENCODING":result=RealmEncoder.encode(producer,final,operation_reference=reference+suffix)
        elif stage=="TOPOLOGY":result=ReferenceTopologyGenerator.generate(producer,g.TopologyRequest(reference+suffix,final,inputs.topology_depth,inputs.seed_token))
        elif stage=="AXIOMS":result=ReferenceAxiomEvaluator.evaluate(producer,g.AxiomRequest(reference+suffix,final,actual_subject))
        else:result=ReferenceGenerationPlanner.plan(producer,p.PlannerRequest(reference+suffix,inputs,origin,final,
                results[0],results[1],results[2],results[3],results[4],constraints))
        capture=_capture(owner,producer,result,stage,child,tuple(results))
        if capture.status!="CONFIRMED":return finish("NOT_CONFIRMED",stage,capture)
        completed.append(reference+suffix)
        if p._is(result,(rt.RealmTransitionFailure,g.TopologyFailure,g.AxiomEvaluationFailure,p.PlannerFailure)):
            return finish("REFUSED",stage,capture)
        results.append(result);previous_stage=stage
    return finish("READY","PLANNER",capture)


def _preparation_failure(owner,capture,target,reference,code):
    plan=capture.result.plan
    request=p.EmitterRequest(reference,plan,MemoryDocumentTarget.configuration(target),reference+":refused")
    pending=p.PendingPlannerEmitterDiagnostic(reference+":summary","ARTIFACT_EMISSION","OPERATION_SUMMARY",code,"CAPABILITY_REFUSED")
    result=p._seal_result(p.EmitterResult(request,ReferenceGenerationRunner.configuration(owner),"FAILED",False,(),(),pending,code),owner._emitter)
    return p._seal_result(p.PlannerEmitterCaptureReceipt(reference,"NOT_CONFIRMED",result,(),None,None,None,code),owner)
