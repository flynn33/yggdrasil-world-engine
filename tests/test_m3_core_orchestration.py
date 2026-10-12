"""Actual standalone Core capture orchestration and cancellation prefixes."""
from dataclasses import replace
import copy
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
from core import core_values as v
from core.deterministic_policy import DeterministicPolicy
from core.module_lifecycle import CoreModuleLifecycle,CoreExecutionGate
from core.ash_pattern_engine import diagnostics as d,diagnostics_values as dv,normalization_values as nv
from core.ash_pattern_engine import state_values as s,normalization
from core.ash_pattern_engine.state_model import StateModel
from core.ash_pattern_engine.realm_transition import TransitionRegistry
from core.ash_pattern_engine.memory_document_target import MemoryDocumentTarget
from core.ash_pattern_engine.generation_planner import ReferenceGenerationPlanner
from tests.test_m3_core_values import core_binding
from tests.test_m3_realm_transition_values import profile_from,diagnosis
from tests.test_m3_module_diagnostics import ModuleStore
from tests.test_m3_reference_diagnostics import ControlledClock
from tests import test_m3_reference_diagnostics as reference_tests
from core.orchestration import CoreOrchestrator,CorePlanPermit,_local
from core.cosmology_engine.cosmology import CosmologyEngine
from core.realm_engine.realm import RealmEngine
from core.ash_pattern_engine.core_facade import AshCoreFacade
from core.narrative_engine.narrative import NarrativeEngine
from core.perception_engine.perception import PerceptionEngine


H4=('000000000','000011110','001100110','001111000')


def current_assembly(*,store=None,clock=None,profile=None):
    profile=profile_from(H4,'core:h4') if profile is None else profile
    binding=core_binding(profile=profile)
    identity=reference_tests.CanonicalSourceCompatibilityTests().identity()
    diag_profile=dv.DiagnosticsProfile(identity.profile_id,identity.implementation_id,'ref:000003',True)
    store=ModuleStore() if store is None else store
    clock=ControlledClock() if clock is None else clock
    collector=d.ReferenceDevelopmentDiagnostics(identity,diag_profile,store,clock,
        canonical_source_snapshots=(dv.SourcePin('ASH_AGGREGATE',identity.source_revision,binding.canonical_binding.aggregate_sha256),))
    model=StateModel(profile,binding.canonical_binding,collector.assessment_capture(),normalization_capture=collector.normalization_capture())
    return binding,model,collector,store,clock


def gated_normalization(*,store=None,clock=None):
    binding,model,collector,store,clock=current_assembly(store=store,clock=clock)
    origin=diagnosis(model,'010101010','core:original')
    first=collector.complete_assessment(origin)
    if first.status!='COMPLETE':
        raise AssertionError(first)
    policy=nv.NormalizationPolicyBinding(*[expected for name,expected in nv.NORMALIZATION_POLICY_BINDING_FIELDS])
    plan=StateModel.plan_normalization(model,origin,plan_reference='core:plan',evidence_reference='core:normalization:evidence',policy_binding=policy)
    context=nv.NormalizationContext('core:normalization','core:normalization:computation','core:normalization:post')
    owner=DeterministicPolicy(binding)
    lifecycle=CoreModuleLifecycle(owner)
    lifecycle.start('start',expected_generation=0)
    ticket=lifecycle.admit('core:work',expected_generation=1,
        operation_bindings=((context.operation_reference,('NORMALIZATION_VALUE','NORMALIZATION_POST_CAPTURE')),))
    original=lifecycle.execution_gate(ticket,collector)
    gate=CoreExecutionGate.for_operation(original,context.operation_reference,('NORMALIZATION_VALUE','NORMALIZATION_POST_CAPTURE'))
    return model,collector,store,clock,plan,context,lifecycle,gate


class CoreNormalizationIntegrationTests(unittest.TestCase):
    def test_actual_source4_normalization_two_grants_complete_first_response_and_class_owned_purity(self):
        model,collector,store,clock,plan,context,lifecycle,gate=gated_normalization()
        with patch.object(model,'_normalization_operations',side_effect=AssertionError('instance helper')),patch.object(model,'_diagnose',side_effect=AssertionError('instance math')):
            actual=StateModel.apply_normalization(model,plan,normalization_context=context,execution_gate=gate)
        self.assertIs(type(actual),nv.NormalizationResult)
        self.assertEqual((actual.outcome,actual.original_diagnosis.parsed_state.signature,actual.normalized_state.signature),('NORMALIZED','010101010','000000000'))
        self.assertEqual(len(actual.emitted_diagnostics),2)
        first=collector.complete_normalization(actual,execution_gate=gate)
        self.assertEqual(first.status,'COMPLETE')
        self.assertIs(collector.complete_normalization(actual,execution_gate=gate),first)
        self.assertEqual(actual.to_record()['schema_ref'],'data/schemas/m3_generation_state_normalization_schema.json')
        self.assertEqual(actual.plan.to_record()['schema_ref'],'data/schemas/m3_generation_normalization_plan_schema.json')
        self.assertEqual(gate.stage_grant('NORMALIZATION_VALUE').grant_sequence,3)

    def test_concurrent_stop_after_actual_computation_ack_retains_step_and_no_post_diagnosis(self):
        model,collector,store,clock,plan,context,lifecycle,gate=gated_normalization()
        entered,release=threading.Event(),threading.Event()
        original_append=normalization._NormalizationOperations._append
        actuals,errors=[],[]
        post_calls=[]
        original_pure=StateModel._diagnose
        def observe(self,decoded):
            # Origin validation remains mathematical; actual state zero is the post kernel.
            if decoded.state is not None and decoded.state.signature=='000000000':
                post_calls.append('post')
            return original_pure(self,decoded)
        def append(scope,record,execution_gate=None):
            response=original_append(scope,record,execution_gate)
            if record.phase=='COMPUTATION' and response=='CONFIRMED':
                entered.set()
                if not release.wait(5):
                    raise AssertionError('release missing')
            return response
        def work():
            try:
                actuals.append(StateModel.apply_normalization(model,plan,normalization_context=context,execution_gate=gate))
            except BaseException as error:
                errors.append(error)
        with patch.object(normalization._NormalizationOperations,'_append',staticmethod(append)),patch.object(StateModel,'_diagnose',observe):
            thread=threading.Thread(target=work)
            thread.start()
            try:
                self.assertTrue(entered.wait(5))
                stopped=lifecycle.stop('stop',expected_generation=1)
                self.assertEqual(stopped.status,'PENDING')
                self.assertTrue(thread.is_alive())
            finally:
                release.set()
                thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors,[])
        self.assertEqual(post_calls,[])
        actual=actuals[0]
        self.assertIs(type(actual),nv.NormalizationCaptureFailure)
        self.assertEqual((len(actual.emitted_diagnostics),len(actual.steps),actual.actual_state.signature),(1,1,'000000000'))
        self.assertIsNone(actual.post_validity_diagnostic)
        self.assertIsNone(actual.attempted_diagnostic)
        self.assertEqual(actual.capture_status,'NOT_CONFIRMED')
        first=collector.complete_normalization(actual,execution_gate=gate)
        self.assertEqual(first.status,'INCOMPLETE')
        self.assertIs(collector.complete_normalization(actual,execution_gate=gate),first)
        self.assertEqual(len([call for call in store.calls if call[0]=='commit_event']),2)
        self.assertEqual(gate.stage_grant('NORMALIZATION_POST_CAPTURE').status,'CANCELLED')
        actual.to_record()
        for changes in ({'capture_status':'REJECTED','failure_code':'DIAGNOSTIC_CAPTURE_REJECTED'},
                        {'emitted_diagnostics':()}, {'failed_field':'post_validity_diagnostic'}):
            with self.assertRaises(nv.NormalizationContractError):
                replace(actual,**changes)

    def test_foreign_session_or_blank_gate_refuses_before_normalizer_and_collector_hooks(self):
        model,collector,store,clock,plan,context,lifecycle,gate=gated_normalization()
        before=len(store.calls)
        for invalid in (object(),object.__new__(CoreExecutionGate)):
            with self.assertRaises(v.CoreContractError),patch.object(model,'_normalization_operations',side_effect=AssertionError('hook')):
                StateModel.apply_normalization(model,plan,normalization_context=context,execution_gate=invalid)
        self.assertEqual(len(store.calls),before)

    def test_concurrent_stop_during_actual_clock_callback_prevents_value_and_post_entry(self):
        class BlockingClock(ControlledClock):
            def __init__(self):
                super().__init__()
                self.block=False
                self.entered,self.release=threading.Event(),threading.Event()
            def read(self):
                if self.block:
                    self.block=False
                    self.entered.set()
                    if not self.release.wait(5):
                        raise AssertionError('clock release missing')
                return super().read()
        clock=BlockingClock()
        model,collector,store,clock,plan,context,lifecycle,gate=gated_normalization(clock=clock)
        clock.block=True
        results,errors=[],[]
        def work():
            try:results.append(StateModel.apply_normalization(model,plan,normalization_context=context,execution_gate=gate))
            except BaseException as error:errors.append(error)
        with patch.object(normalization._NormalizationOperations,'_apply_codeword',wraps=normalization._NormalizationOperations._apply_codeword) as value:
            thread=threading.Thread(target=work)
            thread.start()
            try:
                self.assertTrue(clock.entered.wait(5))
                stopped=lifecycle.stop('stop',expected_generation=1)
                self.assertEqual(stopped.status,'PENDING')
                self.assertTrue(thread.is_alive())
                self.assertEqual(gate.capture_disposition(),'SEALED')
            finally:
                clock.release.set()
                thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors,[])
        self.assertEqual(value.call_count,0)
        self.assertIs(type(results[0]),nv.NormalizationCaptureFailure)
        self.assertEqual(results[0].steps,())
        self.assertIsNone(results[0].post_validity_diagnostic)
        self.assertEqual(gate.stage_grant('NORMALIZATION_POST_CAPTURE').status,'CANCELLED')


def core_runtime(*,depth=5,normalize=True,optional=False,store=None,profile=None):
    from tests.test_m3_generation_runner import runtime_assembly
    from tests.test_m3_axioms import subject
    from tests.test_m3_core_narrative_perception import archetype,context,registry
    if profile is None:
        runner,inputs,valid_origin,declared,constraints,target,ports=runtime_assembly(depth=depth,store=store)
    else:
        # Actual declared profile data flows through every original constructor.
        with patch('tests.test_m3_generation_runner.current_assembly',lambda **kwargs:current_assembly(profile=profile,**kwargs)):
            runner,inputs,valid_origin,declared,constraints,target,ports=runtime_assembly(depth=depth,store=store)
    binding,model,collector,store,clock,planner,emitter=ports
    request_ref='core:run'
    realm_request=archetype_context=truth=perception=None
    rules=()
    catalog=None
    if optional:
        realms=(v.ProfileRealmDefinition('source',6,None,'Source',0,False,('source',)),
                v.ProfileRealmDefinition('target',2,None,'Target',500000,True,('source',)))
        binding=replace(binding,profile_realms=realms)
        realm_request=v.RealmAccessRequest('realm:request','source','target','location',
            (v.AttunementFact('target',500000,'TRUE',('attunement:source',)),))
        rules=(v.PatternProjectionRule('profile:pattern','1'*512,('ash_codeword_01',),750000,('pursuit',),('pattern:source',)),)
        catalog=registry((archetype('seeker',symbolic=('pursuit',)),))
        archetype_context=context(symbolic=('pursuit',))
        truth=v.TruthInputSnapshot('truth','scope',
            (v.DeclaredTruthFact('fact','OBJECTIVE_SHARED','scope','subject','declared',('fact:source',)),),('entity',),'DECLARED_INPUT')
    origin=valid_origin
    normalization_request=None
    if normalize:
        origin=diagnosis(model,'010101010','core:original')
        collector.complete_assessment(origin)
        policy=nv.NormalizationPolicyBinding(*[expected for name,expected in nv.NORMALIZATION_POLICY_BINDING_FIELDS])
        plan=StateModel.plan_normalization(model,origin,plan_reference='core:plan',evidence_reference='core:normalization:evidence',policy_binding=policy)
        normalization_request=v.CoreNormalizationRequest(plan,nv.NormalizationContext('core:normalization','core:normalization:computation','core:normalization:post'))
    if optional:
        refs=(origin.assessment_binding.diagnosis_reference,request_ref+':normalized:detection',request_ref+':final:detection','core:normalization')
        provenance=v.CoreProvenance(_local(request_ref,'snapshot'),request_ref+':final:detection',request_ref+':planner:plan',refs)
        perception=v.PerceptionRequest('perception:request','subject',truth,
            (v.PerceptionRule('rule',1,'subject','entity',('fact',),False,('private:view',)),),provenance)
    owner=CoreOrchestrator(binding,model,collector,runner,CosmologyEngine(binding,model),RealmEngine(binding),
        AshCoreFacade(binding,model),NarrativeEngine(binding),PerceptionEngine(binding),projection_rules=rules,archetype_registry=catalog)
    lifecycle=CoreModuleLifecycle(owner)
    lifecycle.start('start',expected_generation=0)
    request=v.CoreOrchestrationRequest(request_ref,inputs,origin,normalization_request,subject(origin),constraints,
        realm_request,archetype_context,truth,perception)
    return owner,lifecycle,request,target,(model,collector,store,clock,planner,emitter)


class CoreOrchestrationIntegrationTests(unittest.TestCase):
    def test_actual_h4_normalization_fourstep_depth5_all_optional26_grants_and_eight_document10(self):
        owner,lifecycle,request,target,ports=core_runtime(optional=True)
        model,collector,store,clock,planner,emitter=ports
        with patch.object(CoreExecutionGate,'stage_grant',wraps=CoreExecutionGate.stage_grant) as grants:
            actual=owner.run(request)
        self.assertEqual(actual.status,'COMPLETED',actual.to_record())
        self.assertTrue(owner.validate_owned_result(actual))
        self.assertEqual(grants.call_count,26)
        self.assertEqual((actual.normalization_result.outcome,actual.normalization_completion.status,
            actual.normalized_origin.parsed_state.signature,actual.normalized_origin_completion.status),('NORMALIZED','COMPLETE','000000000','COMPLETE'))
        plan_capture=actual.generation_run.last_observation
        self.assertEqual((actual.generation_run.status,plan_capture.status,plan_capture.completion.status,plan_capture.final_observation.status),('READY','CONFIRMED','COMPLETE','CONFIRMED'))
        self.assertEqual((len(plan_capture.result.plan.topology_nodes),len(plan_capture.result.plan.artifacts)),(243,8))
        self.assertEqual([row.transformation_observation.candidate.signature for row in plan_capture.result.request.chain.steps],
            ['000011110','000000000','001100110','000000000'])
        self.assertEqual(actual.pattern.value.actual_codeword_trace,('ash_codeword_04','ash_codeword_01','ash_codeword_01','ash_codeword_02','ash_codeword_02'))
        self.assertEqual(actual.pattern.value.original_signature,'010101010')
        self.assertTrue(actual.pattern.value.observations[0].matched)
        self.assertEqual(actual.realm_shift.effect_status,'PROPOSED_ONLY')
        self.assertEqual(actual.perception.value.hidden_entities,('entity',))
        self.assertLessEqual(len(v.canonical_bytes(actual)),1048576)
        calls=len(store.calls)
        self.assertIs(owner.run(request),actual)
        self.assertEqual(len(store.calls),calls)
        with patch.object(CoreExecutionGate,'stage_grant',wraps=CoreExecutionGate.stage_grant) as grants,patch.object(ReferenceGenerationPlanner,'plan',side_effect=AssertionError('emitter replanned semantics')):
            emitted=owner.emit(actual,target,operation_reference='core:emit')
        self.assertEqual((emitted.status,emitted.result.status),('CONFIRMED','SUCCEEDED'),emitted.to_record())
        self.assertEqual(grants.call_count,10)
        self.assertTrue(owner.validate_owned_result(emitted))
        self.assertEqual((len(target.snapshot().documents),target.snapshot().revision),(8,8))
        self.assertIs(owner.emit(actual,target,operation_reference='core:emit'),emitted)
        self.assertEqual(lifecycle.status().inflight,0)
        from jsonschema import Draft202012Validator
        protected=collector.snapshot(bundle_reference='core:full:protected')
        schema=json.loads((Path(__file__).resolve().parents[1]/'data/schemas/m3_reference_diagnostic_bundle_schema.json').read_text(encoding='utf-8'))
        Draft202012Validator(schema).validate(protected.to_record())
        self.assertTrue({'REALM_ENCODER','TRANSITION_REGISTRY','TOPOLOGY_GENERATOR','AXIOM_EVALUATOR','GENERATION_PLANNER','ARTIFACT_EMITTER'}<= {event.source for event in protected.events})
        for event in protected.events:
            for rule in (() if event.envelope is None else event.envelope.rule_ids):
                if rule.startswith('ASH-'):
                    self.assertRegex(rule,r'^ASH-[A-Z]+-[A-Z]+-[0-9]{3}$')

    def test_absent_optional_fields_and_truth_preflight_no_invented_empty_graph(self):
        owner,lifecycle,request,target,ports=core_runtime(depth=0,normalize=False)
        actual=owner.run(request)
        self.assertEqual(actual.status,'COMPLETED',actual.to_record())
        self.assertEqual(actual.pattern.status,'NO_OP')
        for field in ('normalization_result','normalized_origin','realm_access','realm_shift','archetypes','narrative','perception'):
            self.assertIsNone(getattr(actual,field))
        other,other_lifecycle,full,other_target,other_ports=core_runtime(depth=0,optional=True)
        missing=replace(full,truth_input=None,perception_request=None)
        before=len(other_ports[2].calls)
        refused=other.run(missing)
        self.assertEqual((refused.status,refused.diagnostics[0].failure_code,refused.diagnostics[0].field),('REFUSED','CORE_PROVENANCE_MISSING','truth_input'))
        self.assertEqual(len(other_ports[2].calls),before)
        self.assertEqual(other_lifecycle.status().ledger_used,1)

    def test_exact_runner_dependency_expectations_refuse_foreign_legitimate_instances_before_io(self):
        owner,lifecycle,request,target,ports=core_runtime(depth=0,normalize=False)
        model,collector,store,clock,planner,emitter=ports
        _binding,foreign_model,foreign_collector,foreign_store,_clock=current_assembly()
        before=(len(store.calls),len(foreign_store.calls))
        for submitted_model,submitted_collector in ((foreign_model,collector),(model,foreign_collector)):
            with self.assertRaises(v.CoreContractError),patch.object(StateModel,'diagnose',side_effect=AssertionError('diagnosis hook')):
                CoreOrchestrator(owner.configuration(),submitted_model,submitted_collector,owner._runner,
                    owner._cosmology,owner._realms,owner._patterns,owner._narrative,owner._perception)
        self.assertEqual((len(store.calls),len(foreign_store.calls)),before)
        self.assertEqual(lifecycle.status().ledger_used,1)
        for reserved in ('NONE','SELF'):
            refused=owner.run(replace(request,operation_reference=reserved))
            self.assertEqual((refused.status,refused.diagnostics[0].field),('REFUSED','operation_reference'))
        self.assertEqual(len(store.calls),before[0])

    def test_independent_complete_runs_repeat_entire_canonical_bytes_and_original_permit_only(self):
        actuals=[]
        for index in range(2):
            owner,lifecycle,request,target,ports=core_runtime(depth=0,normalize=False)
            permits=[]
            original=CoreOrchestrator._permit
            def record(self,*args):
                value=original(self,*args)
                self_test.assertTrue(CoreOrchestrator.validate_plan_permit(value,binding=self.configuration()))
                configured=CorePlanPermit.configuration(value)
                self_test.assertIs(configured[0],args[0])
                self_test.assertEqual((configured[2],configured[3]),('core:run',1))
                permits.append(value);return value
            self_test=self
            with patch.object(CoreOrchestrator,'_permit',record):actual=owner.run(request)
            self.assertEqual(actual.status,'COMPLETED')
            self.assertTrue(owner.validate_owned_result(actual))
            actuals.append(v.canonical_bytes(actual))
            permit=permits[0]
            self.assertFalse(CoreOrchestrator.validate_plan_permit(permit,binding=replace(owner.configuration(),profile_realms=(v.ProfileRealmDefinition('foreign',0,None,'Foreign',0,False,()),))))
            forged=object.__new__(CorePlanPermit)
            for name in CorePlanPermit.__slots__:object.__setattr__(forged,name,object.__getattribute__(permit,name))
            self.assertFalse(CoreOrchestrator.validate_plan_permit(forged,binding=owner.configuration()))
            with self.assertRaises(v.CoreContractError):copy.copy(permit)
            self.assertFalse(CoreOrchestrator.validate_plan_permit(permit,binding=owner.configuration()))
            with self.assertRaises(v.CoreContractError):CorePlanPermit.configuration(permit)
            self.assertEqual(lifecycle.status().inflight,0)
            self.assertEqual(target.snapshot().documents,())
        self.assertEqual(actuals[0],actuals[1])

    def test_genuine_depth6_plan_over_core_cap_keeps_complete_api_dag_and_refuses_following_stage(self):
        full_profile=profile_from(tuple(f'{number:09b}' for number in range(512)),'core:full512')
        owner,lifecycle,request,target,ports=core_runtime(depth=6,normalize=False,profile=full_profile)
        with patch.object(AshCoreFacade,'project_patterns',side_effect=AssertionError('later projection')):
            actual=owner.run(request)
        self.assertEqual((actual.status,actual.diagnostics[0].failure_code),('REFUSED','CORE_RESOURCE_LIMIT'))
        self.assertTrue(owner.validate_owned_result(actual))
        run=actual.generation_run
        self.assertEqual((run.status,run.last_observation.status,run.last_observation.completion.status),('READY','CONFIRMED','COMPLETE'))
        self.assertEqual((len(run.last_observation.result.plan.topology_nodes),len(run.last_observation.result.plan.artifacts)),(729,23))
        self.assertGreater(v.raw_business_size(actual),v.MAX_RAW_CORE_BYTES)
        with self.assertRaises(v.CoreContractError):v.canonical_bytes(actual)
        self.assertIsNone(actual.pattern)
        self.assertEqual(target.snapshot().documents,())
        self.assertEqual(lifecycle.status().inflight,0)
        with self.assertRaises(v.CoreContractError):owner.emit(actual,target,operation_reference='oversize:emit')

    def test_stop_during_actual_source_support_callback_preserves_refusal_and_no_following_chain(self):
        owner,lifecycle,request,target,ports=core_runtime(depth=0,normalize=False)
        model,collector,store,clock,planner,emitter=ports
        store.block_kind='PRODUCER_OPERATION'
        results,errors=[],[]
        def work():
            try:results.append(owner.run(request))
            except BaseException as error:errors.append(error)
        with patch.object(TransitionRegistry,'apply_chain',side_effect=AssertionError('following chain')):
            thread=threading.Thread(target=work);thread.start()
            try:
                self.assertTrue(store.entered.wait(5))
                stopped=lifecycle.stop('stop',expected_generation=1)
                self.assertEqual(stopped.status,'PENDING')
                self.assertTrue(thread.is_alive())
            finally:
                store.release.set();thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors,[])
        actual=results[0]
        self.assertEqual((actual.status,actual.diagnostics[0].failure_code),('PENDING','CORE_STAGE_REVOKED'))
        self.assertIsNotNone(actual.generation_run)
        self.assertEqual(actual.generation_run.last_stage,'SOURCE_ENCODING')
        self.assertTrue(owner.validate_owned_result(actual))
        self.assertIsNone(actual.pattern)
        self.assertEqual(target.snapshot().documents,())
        self.assertEqual((lifecycle.status().phase,lifecycle.status().inflight),('STOPPED',0))

    def test_core_stop_during_granted_target_callback_keeps_late_effect_and_denies_remaining_documents(self):
        owner,lifecycle,request,target,ports=core_runtime(depth=4,normalize=False)
        planned=owner.run(request)
        self.assertEqual(planned.status,'COMPLETED')
        self.assertEqual(len(planned.generation_run.last_observation.result.plan.artifacts),3)
        entered,release,ready=threading.Event(),threading.Event(),threading.Event()
        actuals,errors,calls=[],[],[]
        original=MemoryDocumentTarget.materialize
        def materialize(self,*args,**kwargs):
            calls.append(args)
            if len(calls)==1:
                entered.set()
                ready.set()
                if not release.wait(60):raise AssertionError('target release missing')
            return original(self,*args,**kwargs)
        def work():
            try:actuals.append(owner.emit(planned,target,operation_reference='core:late:emit'))
            except BaseException as error:errors.append(error)
            finally:ready.set()
        with patch.object(MemoryDocumentTarget,'materialize',materialize):
            thread=threading.Thread(target=work);thread.start()
            try:
                self.assertTrue(ready.wait(60),'Emission neither entered its target callback nor completed')
                self.assertEqual(errors,[])
                self.assertTrue(entered.is_set(),'Emission completed before its first target callback')
                stopped=lifecycle.stop('stop',expected_generation=1)
                self.assertEqual(stopped.status,'PENDING')
                self.assertTrue(thread.is_alive())
                self.assertEqual(target.snapshot().revision,0)
            finally:
                release.set();thread.join(60)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors,[])
        actual=actuals[0]
        self.assertEqual(len(calls),1)
        self.assertEqual((target.snapshot().revision,len(target.snapshot().documents)),(1,1))
        self.assertEqual((actual.status,actual.completion.status),('NOT_CONFIRMED','INCOMPLETE'))
        self.assertEqual((actual.result.outcomes[0].actual_status,actual.result.outcomes[0].actual_effects),('SUCCEEDED',True))
        self.assertTrue(owner.validate_owned_result(actual))
        self.assertEqual((lifecycle.status().phase,lifecycle.status().inflight),('STOPPED',0))
        with self.assertRaises(v.CoreContractError):owner.emit(planned,target,operation_reference='core:after:stop')
        self.assertEqual(target.snapshot().revision,1)


if __name__=='__main__':
    unittest.main()
