"""Explicit standalone Core composition; stage authority never publishes Session state."""
from dataclasses import dataclass
import hashlib
import threading
from . import core_values as cv
from .module_lifecycle import CoreModuleLifecycle,CoreExecutionGate,CoreStageGrant,ModuleTicket
from .cosmology_engine.cosmology import CosmologyEngine
from .realm_engine.realm import RealmEngine
from .ash_pattern_engine.core_facade import AshCoreFacade
from .narrative_engine.narrative import NarrativeEngine
from .perception_engine.perception import PerceptionEngine,_truth_facts
from .ash_pattern_engine.state_model import StateModel
from .ash_pattern_engine import state_values as sv,normalization_values as nv,diagnostics_values as dv
from .ash_pattern_engine import planner_emitter_values as pv
from .ash_pattern_engine.diagnostics import ReferenceDevelopmentDiagnostics,ReferenceReleaseDiagnostics

_PERMIT_FACTORY=object()


@dataclass(frozen=True,slots=True)
class _PermitCookie:
    original: object
    issuer: object
    gate: object
    binding_sha256: str
    plan_result: object
    run: object
    original_origin: object
    normalization_result: object


class CorePlanPermit:
    """Original API-only capability exposing immutable actual plan provenance."""
    __slots__=('_cookie','binding','plan_result','original_origin','normalization_result')

    def __new__(cls,marker=None):
        if marker is not _PERMIT_FACTORY:
            cv._fail('generation_plan_ref','CORE_PROVENANCE_MISSING')
        return super().__new__(cls)

    def __setattr__(self,name,value):
        raise AttributeError('CorePlanPermit is immutable')

    def configuration(self):
        if type(self) is not CorePlanPermit:
            cv._fail('generation_plan_ref','CORE_PROVENANCE_MISSING')
        try:
            binding=object.__getattribute__(self,'binding')
            cookie=object.__getattribute__(self,'_cookie')
        except AttributeError:
            cv._fail('generation_plan_ref','CORE_PROVENANCE_MISSING')
        if not CoreOrchestrator.validate_plan_permit(self,binding=binding):
            cv._fail('generation_plan_ref','CORE_PROVENANCE_MISSING')
        _collector,_scope,_source,_profile,generation=CoreExecutionGate.configuration(cookie.gate)
        return cookie.run,binding,cookie.run.operation_reference,generation


def _context(reference):
    return sv.DiagnosticContext(reference,reference+':input',reference+':detection',reference+':classification')


def _local(reference,suffix):
    return 'core:'+hashlib.sha256(reference.encode('ascii')).hexdigest()+':'+suffix


def _runner_class():
    from .ash_pattern_engine.generation_runner import ReferenceGenerationRunner
    return ReferenceGenerationRunner


def _runner_configuration(runner,model,diagnostics):
    try:
        return _runner_class().configuration(runner,state_model=model,diagnostics=diagnostics)
    except (pv.PlannerEmitterContractError,AttributeError,ValueError):
        cv._fail('binding','CORE_BINDING_MISMATCH')


class CoreOrchestrator(cv._ConfiguredOwner):
    __slots__=('_model','_diagnostics','_runner','_cosmology','_realms','_patterns','_narrative','_perception',
               '_rules','_registry','_composition','_returns','_return_lock')
    CORE_OWNER='ORCHESTRATION'

    def __init__(self,binding,state_model,diagnostics,generation_runner,cosmology,realms,patterns,narrative,perception,*,projection_rules=(),archetype_registry=None):
        cv._initialize_owner(self,binding,CoreOrchestrator)
        cv._validate_model(state_model,binding)
        if not cv._one_of(type(diagnostics),(ReferenceDevelopmentDiagnostics,ReferenceReleaseDiagnostics)):
            cv._fail('binding','CORE_BINDING_MISMATCH')
        runner_type=_runner_class()
        if type(generation_runner) is not runner_type:
            cv._fail('owner')
        runner_binding=_runner_configuration(generation_runner,state_model,diagnostics)
        if cv._wire_digest(runner_binding.canonical_binding)!=cv._wire_digest(binding.canonical_binding) or cv._wire_digest(runner_binding.profile_binding)!=cv._wire_digest(binding.profile_binding):
            cv._fail('binding','CORE_BINDING_MISMATCH')
        for owner_type,owner in ((CosmologyEngine,cosmology),(RealmEngine,realms),(AshCoreFacade,patterns),(NarrativeEngine,narrative),(PerceptionEngine,perception)):
            if type(owner) is not owner_type or cv._wire_digest(owner_type.configuration(owner))!=cv._wire_digest(binding):
                cv._fail('binding','CORE_BINDING_MISMATCH')
        if type(projection_rules) is not tuple or len(projection_rules)>64:
            cv._fail('rules')
        for row in projection_rules:
            if type(row) is not cv.PatternProjectionRule:
                cv._fail('rules')
            cv.revalidate_value(row)
        if len({row.pattern_id for row in projection_rules})!=len(projection_rules):
            cv._fail('pattern_id','CORE_PROFILE_CONFLICT')
        if archetype_registry is not None:
            if type(archetype_registry) is not cv.ArchetypeRegistry:
                cv._fail('archetypes')
            cv.revalidate_value(archetype_registry)
        self._model,self._diagnostics,self._runner=state_model,diagnostics,generation_runner
        self._cosmology,self._realms,self._patterns,self._narrative,self._perception=cosmology,realms,patterns,narrative,perception
        self._rules,self._registry=projection_rules,archetype_registry
        self._composition=(self,state_model,diagnostics,generation_runner,cosmology,realms,patterns,narrative,perception,
            tuple(cv._wire_digest(row) for row in projection_rules),None if archetype_registry is None else cv._wire_digest(archetype_registry))
        self._returns={}
        self._return_lock=threading.RLock()

    def configuration(self):
        binding=cv._owner_configuration(self,CoreOrchestrator)
        current=(self,self._model,self._diagnostics,self._runner,self._cosmology,self._realms,self._patterns,self._narrative,self._perception)
        if type(self._composition) is not tuple or len(self._composition)!=11 or any(actual is not expected for actual,expected in zip(current,self._composition[:9])):
            cv._fail('owner','CORE_BINDING_MISMATCH')
        cv._validate_model(self._model,binding)
        for cls,owner in ((CosmologyEngine,self._cosmology),(RealmEngine,self._realms),(AshCoreFacade,self._patterns),(NarrativeEngine,self._narrative),(PerceptionEngine,self._perception)):
            if type(owner) is not cls or cv._wire_digest(cls.configuration(owner))!=cv._wire_digest(binding):
                cv._fail('binding','CORE_BINDING_MISMATCH')
        runner_binding=_runner_configuration(self._runner,self._model,self._diagnostics)
        if cv._wire_digest(runner_binding.canonical_binding)!=cv._wire_digest(binding.canonical_binding) or cv._wire_digest(runner_binding.profile_binding)!=cv._wire_digest(binding.profile_binding):
            cv._fail('binding','CORE_BINDING_MISMATCH')
        if (tuple(cv._wire_digest(row) for row in self._rules)!=self._composition[9] or
                (None if self._registry is None else cv._wire_digest(self._registry))!=self._composition[10]):
            cv._fail('archetypes','CORE_PROFILE_CONFLICT')
        return binding

    def validate_owned_result(self,result):
        try:
            binding=CoreOrchestrator.configuration(self)
            if type(result) is cv.CoreOrchestrationResult or type(result) is cv.CoreResult:
                return cv._validate_result(self,result,binding)
            if type(result) is pv.PlannerEmitterCaptureReceipt:
                row=self._returns.get(result.operation_reference)
                return row is not None and row[1] is result and _runner_class().validate_owned_result(self._runner,result) is True
        except (cv.CoreContractError,pv.PlannerEmitterContractError,AttributeError,ValueError):
            return False
        return False

    @staticmethod
    def validate_plan_permit(permit,*,binding):
        if type(permit) is not CorePlanPermit or type(binding) is not cv.CoreBinding:
            return False
        try:
            cookie=object.__getattribute__(permit,'_cookie')
            if (type(cookie) is not _PermitCookie or cookie.original is not permit or type(cookie.issuer) is not CoreOrchestrator or
                    type(cookie.binding_sha256) is not str or type(cookie.run) is not pv.GenerationRunReceipt or
                    type(cookie.plan_result) is not pv.PlannerResult or type(cookie.original_origin) is not sv.StateDiagnosis or
                    not (cookie.normalization_result is None or type(cookie.normalization_result) is nv.NormalizationResult) or
                    permit.plan_result is not cookie.plan_result or permit.original_origin is not cookie.original_origin or
                    permit.normalization_result is not cookie.normalization_result):
                return False
            owner=cookie.issuer
            configured=CoreOrchestrator.configuration(owner)
            if cookie.binding_sha256!=cv._wire_digest(binding) or cookie.binding_sha256!=cv._wire_digest(configured):
                return False
            if permit.binding is not configured or CoreExecutionGate.capture_disposition(cookie.gate)!='ACTIVE':
                return False
            return _runner_class().validate_owned_result(owner._runner,cookie.run) is True and cookie.run.status=='READY'
        except (cv.CoreContractError,pv.PlannerEmitterContractError,AttributeError,ValueError):
            return False

    def _permit(self,run,gate,request,normalization):
        if not _runner_class().validate_owned_result(self._runner,run) or run.status!='READY':
            cv._fail('generation_run','CORE_PROVENANCE_MISSING')
        capture=run.last_observation
        if (type(capture) is not pv.PlannerEmitterCaptureReceipt or type(capture.result) is not pv.PlannerResult or
                capture.status!='CONFIRMED' or type(capture.completion) is not dv.DiagnosticsCompletionReceipt or capture.completion.status!='COMPLETE' or
                capture.final_observation is None or capture.final_observation.status!='CONFIRMED'):
            cv._fail('generation_run','CORE_PROVENANCE_MISSING')
        permit=CorePlanPermit(_PERMIT_FACTORY)
        binding=CoreOrchestrator.configuration(self)
        for name,value in (('binding',binding),('plan_result',capture.result),('original_origin',request.origin),('normalization_result',normalization)):
            object.__setattr__(permit,name,value)
        object.__setattr__(permit,'_cookie',_PermitCookie(permit,self,gate,cv._wire_digest(binding),capture.result,run,request.origin,normalization))
        return permit

    def _fields(self):
        return dict(normalization_result=None,normalization_completion=None,normalized_origin=None,normalized_origin_completion=None,
            generation_run=None,cosmology=None,realm_access=None,realm_shift=None,pattern=None,archetypes=None,narrative=None,perception=None)

    def _result(self,request,fields,status='COMPLETED',code=None,field=None):
        diagnostic=cv.CoreDiagnostic(_local(request.operation_reference,'diagnostic'),self.CORE_OWNER,
            'STAGE_GATE' if code=='CORE_STAGE_REVOKED' else 'RESOURCE_LIMIT' if code=='CORE_RESOURCE_LIMIT' else 'PROVENANCE',
            status,code,field,(), 'Actual Core stage packets were retained; no Session publication occurred.')
        return cv._issue_result(self,cv.CoreOrchestrationResult(request,CoreOrchestrator.configuration(self),**fields,status=status,diagnostics=(diagnostic,)))

    def _grant(self,gate,stage):
        grant=CoreExecutionGate.stage_grant(gate,stage)
        if type(grant) is not CoreStageGrant or grant.status!='GRANTED':
            cv._fail('phase','CORE_STAGE_REVOKED')
        return grant

    def run(self,request):
        binding=CoreOrchestrator.configuration(self)
        if type(request) is not cv.CoreOrchestrationRequest:
            cv._fail('request')
        cv.revalidate_value(request)
        fields=self._fields()
        refusal=self._result(request,fields,'REFUSED','CORE_RESOURCE_LIMIT','request')
        if cv.raw_business_size(refusal)>cv.MAX_RAW_CORE_BYTES:
            cv._fail('request','CORE_RESOURCE_LIMIT')
        if request.operation_reference in ('NONE','SELF'):
            return self._result(request,fields,'REFUSED','CORE_VALUE_INVALID','operation_reference')
        effective=request.truth_input if request.truth_input is not None else None if request.perception_request is None else request.perception_request.truth
        if request.truth_input is not None and request.perception_request is not None and cv.canonical_bytes(request.truth_input)!=cv.canonical_bytes(request.perception_request.truth):
            return self._result(request,fields,'REFUSED','CORE_FACT_CONFLICT','truth_input')
        if request.archetype_context is not None:
            if self._registry is None:
                return self._result(request,fields,'REFUSED','CORE_CAPABILITY_UNAVAILABLE','archetype_context')
            if effective is None:
                return self._result(request,fields,'REFUSED','CORE_PROVENANCE_MISSING','truth_input')
        if effective is not None:
            try:
                _truth_facts(effective)
            except cv.CoreContractError as error:
                return self._result(request,fields,'REFUSED',error.code,error.field_name)
        lifecycle=self._core_lifecycle
        if type(lifecycle) is not CoreModuleLifecycle:
            return self._result(request,fields,'REFUSED','CORE_LIFECYCLE_REJECTED','phase')
        digest=cv._wire_digest(request)
        status=CoreModuleLifecycle.status(lifecycle)
        base=request.operation_reference
        core_stages=('NORMALIZATION_VALIDATE','NORMALIZATION_CAPTURE','COSMOLOGY','REALM_ACCESS','REALM_SHIFT_PROPOSAL','PATTERN_PROJECTION','NARRATIVE','PERCEPTION')
        pairs=[(base,core_stages),(request.origin.assessment_binding.assessment_reference,('ORIGIN_CAPTURE',))]
        for suffix,stage in (('source','SOURCE_ENCODING'),('chain','CHAIN'),('normalized','ORIGIN_CAPTURE'),('final','FINAL_DIAGNOSIS'),('destination','DESTINATION_ENCODING'),('topology','TOPOLOGY'),('axioms','AXIOMS'),('planner','PLANNER')):
            pairs.append((base+':'+suffix,(stage,)))
        if request.normalization is not None:
            pairs.append((request.normalization.context.operation_reference,('NORMALIZATION_VALUE','NORMALIZATION_POST_CAPTURE')))
        if len({reference for reference,stages in pairs})!=len(pairs):
            return self._result(request,fields,'REFUSED','CORE_VALUE_INVALID','operation_reference')
        with self._return_lock:
            prior=self._returns.get(base)
            if prior is not None:
                return prior[1] if prior[0]==digest and prior[1] is not None and status.phase=='ACTIVE' else self._result(request,fields,'REFUSED','CORE_LIFECYCLE_REJECTED','request')
            ticket=CoreModuleLifecycle.admit(lifecycle,base,expected_generation=status.generation,operation_bindings=tuple(pairs))
            if type(ticket) is not ModuleTicket:
                return self._result(request,fields,'REFUSED','CORE_LIFECYCLE_REJECTED','phase')
            self._returns[base]=(digest,None)
        gate=None
        output=None
        try:
            gate=CoreModuleLifecycle.execution_gate(lifecycle,ticket,self._diagnostics)
            def keep(name,value):
                fields[name]=value
                if cv.raw_business_size(self._result(request,fields,'REFUSED','CORE_RESOURCE_LIMIT','value'))>cv.MAX_RAW_CORE_BYTES:
                    cv._fail('value','CORE_RESOURCE_LIMIT')
                if CoreExecutionGate.capture_disposition(gate)!='ACTIVE':
                    cv._fail('phase','CORE_STAGE_REVOKED')
            origin_gate=CoreExecutionGate.for_operation(gate,request.origin.assessment_binding.assessment_reference,'ORIGIN_CAPTURE')
            self._grant(origin_gate,'ORIGIN_CAPTURE')
            validation=StateModel.validate_diagnosis(self._model,request.origin)
            if validation.status!='VERIFIED':
                cv._fail('origin','CORE_BINDING_MISMATCH')
            origin_completion=type(self._diagnostics).complete_assessment(self._diagnostics,request.origin)
            if type(origin_completion) is not dv.DiagnosticsCompletionReceipt or origin_completion.status!='COMPLETE':
                cv._fail('origin','CORE_PROVENANCE_MISSING')
            current=request.origin
            if request.normalization is not None:
                self._grant(gate,'NORMALIZATION_VALIDATE')
                norm=request.normalization
                if cv._wire_digest(norm.plan.original_diagnosis)!=cv._wire_digest(request.origin):
                    cv._fail('normalization','CORE_BINDING_MISMATCH')
                checked=StateModel.validate_normalization_plan(self._model,norm.plan)
                if checked.validation_status!='VALIDATED' or norm.plan.decision!='PLAN_READY':
                    cv._fail('normalization','CORE_CAPABILITY_UNAVAILABLE')
                self._grant(gate,'NORMALIZATION_CAPTURE')
                child=CoreExecutionGate.for_operation(gate,norm.context.operation_reference,('NORMALIZATION_VALUE','NORMALIZATION_POST_CAPTURE'))
                actual=StateModel.apply_normalization(self._model,norm.plan,normalization_context=norm.context,execution_gate=child)
                fields['normalization_result']=actual
                completion=type(self._diagnostics).complete_normalization(self._diagnostics,actual,execution_gate=child)
                fields['normalization_completion']=completion
                keep('normalization_result',actual)
                if type(actual) is not nv.NormalizationResult or actual.outcome!='NORMALIZED' or type(completion) is not dv.DiagnosticsCompletionReceipt or completion.status!='COMPLETE':
                    cv._fail('normalization','CORE_PROVENANCE_MISSING')
                child=CoreExecutionGate.for_operation(gate,base+':normalized','ORIGIN_CAPTURE')
                self._grant(child,'ORIGIN_CAPTURE')
                adapter=type(self._diagnostics).assessment_capture(self._diagnostics,execution_gate=child)
                measured=StateModel(binding.profile_binding,binding.canonical_binding,adapter)
                fresh=StateModel.diagnose(measured,actual.normalized_state.signature,diagnostic_context=_context(base+':normalized'))
                if type(fresh) is not sv.StateDiagnosis:
                    cv._fail('normalized_origin','CORE_PROVENANCE_MISSING')
                fields['normalized_origin']=fresh
                first=type(self._diagnostics).complete_assessment(self._diagnostics,fresh)
                fields['normalized_origin_completion']=first
                keep('normalized_origin',fresh)
                if type(first) is not dv.DiagnosticsCompletionReceipt or first.status!='COMPLETE':
                    cv._fail('normalized_origin','CORE_PROVENANCE_MISSING')
                current=fresh
            elif not current.state_validity_diagnostic.is_valid:
                cv._fail('normalization','CORE_CAPABILITY_UNAVAILABLE')
            self._grant(gate,'COSMOLOGY')
            actual=CosmologyEngine.initialize_cosmos(self._cosmology,current,operation_reference=_local(base,'cosmology'))
            keep('cosmology',actual)
            if actual.status!='COMPLETED':
                cv._fail('cosmology','CORE_PROVENANCE_MISSING')
            if request.realm_request is not None:
                self._grant(gate,'REALM_ACCESS')
                actual=RealmEngine.evaluate_access(self._realms,request.realm_request)
                keep('realm_access',actual)
                if actual.value.eligible is not True:
                    output=self._result(request,fields,actual.status,'CORE_PROVENANCE_MISSING','realm_request')
                else:
                    self._grant(gate,'REALM_SHIFT_PROPOSAL')
                    keep('realm_shift',RealmEngine.propose_shift(self._realms,actual.value,proposal_ref=_local(base,'shift')))
            if output is None:
                actual=_runner_class().run(self._runner,request.inputs,current,request.declared_subject,request.target_constraints,
                    operation_reference=base,execution_gate=gate)
                keep('generation_run',actual)
                permit=self._permit(actual,gate,request,fields['normalization_result'])
                self._grant(gate,'PATTERN_PROJECTION')
                actual=AshCoreFacade.project_patterns(self._patterns,permit,self._rules,snapshot_ref=_local(base,'snapshot'))
                keep('pattern',actual)
                if actual.status not in ('COMPLETED','NO_OP'):
                    cv._fail('pattern','CORE_PROVENANCE_MISSING')
                if request.archetype_context is not None:
                    self._grant(gate,'NARRATIVE')
                    evaluation=NarrativeEngine.evaluate_archetypes(self._narrative,actual.value,request.archetype_context,self._registry)
                    keep('archetypes',evaluation)
                    if evaluation.status not in ('COMPLETED','NO_OP'):
                        cv._fail('archetypes','CORE_PROVENANCE_MISSING')
                    self._grant(gate,'NARRATIVE')
                    narrative=NarrativeEngine.interpret(self._narrative,evaluation.value,effective,interpretation_ref=_local(base,'interpretation'))
                    keep('narrative',narrative)
                    if narrative.status not in ('COMPLETED','NO_OP'):
                        cv._fail('narrative','CORE_PROVENANCE_MISSING')
                if request.perception_request is not None:
                    provenance=request.perception_request.provenance
                    if cv._wire_digest(provenance)!=cv._wire_digest(fields['pattern'].value.provenance):
                        cv._fail('perception_request','CORE_PROVENANCE_MISSING')
                    self._grant(gate,'PERCEPTION')
                    perception=PerceptionEngine.compose_overlay(self._perception,request.perception_request)
                    keep('perception',perception)
                    if perception.status not in ('COMPLETED','NO_OP'):
                        cv._fail('perception','CORE_PROVENANCE_MISSING')
                output=self._result(request,fields)
        except cv.CoreContractError as error:
            output=self._result(request,fields,'PENDING' if error.code=='CORE_STAGE_REVOKED' else 'REFUSED',error.code,
                error.field_name if error.field_name in cv.DOMAINS['CORE_FIELD'] else 'value')
        except (sv.StateContractError,nv.NormalizationContractError,dv.DiagnosticsContractError,pv.PlannerEmitterContractError):
            output=self._result(request,fields,'REFUSED','CORE_PROVENANCE_MISSING','value')
        finally:
            if output is None:
                output=self._result(request,fields,'PENDING','CORE_PROVENANCE_MISSING','value')
            with self._return_lock:
                self._returns[base]=(digest,output)
            CoreModuleLifecycle.complete(lifecycle,ticket,output)
        return output

    def emit(self,actual_owned_result,target,*,operation_reference):
        CoreOrchestrator.configuration(self)
        cv._text(operation_reference,'ID','operation_reference')
        if (type(actual_owned_result) is not cv.CoreOrchestrationResult or not CoreOrchestrator.validate_owned_result(self,actual_owned_result) or
                actual_owned_result.status!='COMPLETED' or cv.raw_business_size(actual_owned_result)>cv.MAX_RAW_CORE_BYTES or
                actual_owned_result.generation_run is None):
            cv._fail('generation_run','CORE_PROVENANCE_MISSING')
        run=actual_owned_result.generation_run
        if run.status!='READY' or not _runner_class().validate_owned_result(self._runner,run):
            cv._fail('generation_run','CORE_PROVENANCE_MISSING')
        from .ash_pattern_engine.memory_document_target import MemoryDocumentTarget
        if type(target) is not MemoryDocumentTarget:
            cv._fail('target_reference','CORE_VALUE_INVALID')
        target_binding=MemoryDocumentTarget.configuration(target)
        lifecycle=self._core_lifecycle
        if type(lifecycle) is not CoreModuleLifecycle:
            cv._fail('phase','CORE_LIFECYCLE_REJECTED')
        request_digest=hashlib.sha256((cv._wire_digest(actual_owned_result)+cv._wire_digest(target_binding)+operation_reference).encode('ascii')).hexdigest()
        status=CoreModuleLifecycle.status(lifecycle)
        with self._return_lock:
            prior=self._returns.get(operation_reference)
            if prior is not None:
                if (prior[0]==request_digest and type(prior[1]) is pv.PlannerEmitterCaptureReceipt and
                        len(prior)==3 and prior[2] is target and status.phase=='ACTIVE'):
                    return prior[1]
                cv._fail('operation_reference','CORE_LIFECYCLE_REJECTED')
            ticket=CoreModuleLifecycle.admit(lifecycle,operation_reference,expected_generation=status.generation,
                operation_bindings=((operation_reference,('EMISSION_PREPARE','EMISSION_DISPATCH')),))
            if type(ticket) is not ModuleTicket:
                cv._fail('phase','CORE_LIFECYCLE_REJECTED')
            self._returns[operation_reference]=(request_digest,None,target)
        actual=None
        entered=False
        try:
            gate=CoreModuleLifecycle.execution_gate(lifecycle,ticket,self._diagnostics)
            # The runner owns preparation and the emitter owns admission/dispatch grants.
            entered=True
            actual=_runner_class().emit(self._runner,run.last_observation,target,operation_reference=operation_reference,execution_gate=gate)
            return actual
        finally:
            if actual is None:
                actual=cv._operation_result(self,CoreOrchestrator,operation_reference,None,'STAGE_GATE',status='PENDING',
                    code='CORE_PROVENANCE_MISSING' if entered else 'CORE_STAGE_REVOKED',field='generation_run',effect='UNKNOWN' if entered else 'NONE',
                    explanation='No peer return was received; attempted dispatch outcome remains unknown.' if entered else 'The operation was stopped before dispatch entry.')
            with self._return_lock:
                self._returns[operation_reference]=(request_digest,actual,target)
            CoreModuleLifecycle.complete(lifecycle,ticket,actual)
