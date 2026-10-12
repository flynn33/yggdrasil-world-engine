"""Actual owned generation stages and first capture truth under standalone Core gates."""
from dataclasses import replace
import copy
import unittest
from unittest.mock import patch

from core.ash_pattern_engine import planner_emitter_values as p,generation_values as g,realm_transition_values as rt,state_values as s
from core.ash_pattern_engine.state_model import StateModel
from core.ash_pattern_engine.realm_transition import RealmEncoder,TransitionRegistry
from core.ash_pattern_engine.topology import ReferenceTopologyGenerator
from core.ash_pattern_engine.axioms import ReferenceAxiomEvaluator
from core.ash_pattern_engine.generation_planner import ReferenceGenerationPlanner
from core.ash_pattern_engine.artifact_emitter import ReferenceArtifactEmitter
from core.ash_pattern_engine.memory_document_target import MemoryDocumentTarget
from core.ash_pattern_engine.generation_runner import ReferenceGenerationRunner
from core.ash_pattern_engine.diagnostic_module_capture import ModuleCaptureScope
from core.ash_pattern_engine import diagnostic_module_values as mv
from core.module_lifecycle import CoreModuleLifecycle,CoreExecutionGate
from core.deterministic_policy import DeterministicPolicy
from tests.test_m3_core_orchestration import current_assembly
from tests.test_m3_core_values import core_binding
from tests.test_m3_transition_chain import assembly,select
from tests.test_m3_realm_transition_values import diagnosis
from tests.test_m3_axioms import subject


def runtime_assembly(*,depth=5,store=None,choice='REFERENCE_MANIFEST_PAGES'):
    core,model,collector,store,clock=current_assembly(store=store)
    _seed,reference_encoder,_reference_registry=assembly(profile=model.profile_binding)
    rt_binding=reference_encoder.configuration()
    definitions=tuple(rt.TransitionDefinition(f'ash_codeword_{i:02d}',f'ASH codeword {i:02d}',
          'Apply the complete canonical nine-coordinate XOR codeword.',s.AshState(bits),'1'*512)
          for i,bits in enumerate(s.CANONICAL_CODEWORDS))
    encoder=RealmEncoder(model,rt_binding)
    registry=TransitionRegistry(model,rt.TransitionCatalog(rt_binding,definitions))
    topology=ReferenceTopologyGenerator(model,g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS))
    axioms=ReferenceAxiomEvaluator(model,g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS))
    pins=p.FIELD_SCHEMAS['PlannerEmitterBinding']['contract_pins']['const']
    binding=p.PlannerEmitterBinding(model.canonical_binding,model.profile_binding,tuple((x['path'],x['sha256']) for x in pins),
                                   p.PlannerEmitterPolicyBinding(*p.POLICY_FIELDS))
    planner=ReferenceGenerationPlanner(model,binding,encoder,registry,topology,axioms)
    target=MemoryDocumentTarget(p.MemoryTargetConfiguration('target:memory','REFERENCE_MEMORY_DOCUMENTS',binding.policy_binding,32,1048576))
    emitter=ReferenceArtifactEmitter(model,binding,collector,target)
    runner=ReferenceGenerationRunner(model,collector,encoder,registry,topology,axioms,planner,emitter)
    for owner in (encoder,registry,topology,axioms,planner,emitter):
        registration=type(collector).register_module_producer(collector,owner)
        if registration.status!='REGISTERED':raise AssertionError(registration)
    origin=diagnosis(model,'000000000','runtime:origin')
    first=type(collector).complete_assessment(collector,origin)
    if first.status!='COMPLETE':raise AssertionError(first)
    inputs=p.GenerationInputs('runtime','seed',depth,(select(1),select(1),select(2),select(2)),model.profile_binding.profile_id,
        'ALREADY_VALID','TERNARY_BRANCH_ROLES_001','YWE_ASCII_DOCUMENT_NAMES_001','DECLARED_AXIOM_FACTS_001',
        'REFERENCE_MANIFEST_PAGES_001','REFERENCE_MEMORY_DOCUMENTS',choice)
    constraints=p.TargetConstraints(32,32768,1048576,False,'EXACT_BYTES_IDEMPOTENT_OR_REFUSE')
    return runner,inputs,origin,subject(origin,(True,)*5),constraints,target,(core,model,collector,store,clock,planner,emitter)


def run_gate(core,collector,reference):
    lifecycle=CoreModuleLifecycle(DeterministicPolicy(core))
    lifecycle.start('runtime:start',expected_generation=0)
    stages=(('source','SOURCE_ENCODING'),('chain','CHAIN'),('final','FINAL_DIAGNOSIS'),('destination','DESTINATION_ENCODING'),
            ('topology','TOPOLOGY'),('axioms','AXIOMS'),('planner','PLANNER'))
    ticket=lifecycle.admit(reference,expected_generation=1,operation_bindings=tuple((reference+':'+suffix,(stage,)) for suffix,stage in stages))
    return lifecycle,lifecycle.execution_gate(ticket,collector)


class GenerationRunnerTests(unittest.TestCase):
    def test_foreign_genuine_scope_is_untouched_and_original_wrong_receipt_scope_finishes_once(self):
        runner,inputs,origin,declared,constraints,_,ports=runtime_assembly(depth=0)
        collector,encoder=ports[2],runner._encoder
        foreign=encoder.encode(origin,operation_reference='runner:foreign')
        context=mv.ModuleCaptureContext(foreign.operation_reference,'REALM_ENCODER',encoder.configuration(),origin,foreign,())
        scope=collector.module_capture(encoder,context).scope
        injected=mv.ModuleCaptureAdmission('runner:injected:source','ADMITTED',scope,None)
        with patch.object(type(collector),'module_capture',return_value=injected),\
                patch.object(ModuleCaptureScope,'append',wraps=ModuleCaptureScope.append) as append,\
                patch.object(ModuleCaptureScope,'finish',wraps=ModuleCaptureScope.finish) as finish,\
                patch.object(ModuleCaptureScope,'observe_final',wraps=ModuleCaptureScope.observe_final) as observe:
            actual=runner.run(inputs,origin,declared,constraints,operation_reference='runner:injected')
        self.assertEqual(actual.status,'NOT_CONFIRMED')
        self.assertEqual((append.call_count,finish.call_count,observe.call_count),(0,0,0))
        self.assertEqual((scope._native.finished,scope._native.failed),(False,None))
        self.assertIsNone(actual.last_observation.completion)

        original=type(collector).module_capture
        issued=[]
        def wrong(admitted_collector,producer,actual_context,**kwargs):
            admission=original(admitted_collector,producer,actual_context,**kwargs)
            issued.append((admission.scope,actual_context))
            return mv.ModuleCaptureAdmission('runner:wrong:receipt','ADMITTED',admission.scope,None)
        with patch.object(type(collector),'module_capture',wrong),\
                patch.object(ModuleCaptureScope,'append',wraps=ModuleCaptureScope.append) as append,\
                patch.object(ModuleCaptureScope,'finish',wraps=ModuleCaptureScope.finish) as finish,\
                patch.object(ModuleCaptureScope,'observe_final',wraps=ModuleCaptureScope.observe_final) as observe:
            actual=runner.run(inputs,origin,declared,constraints,operation_reference='runner:own')
        self.assertEqual((append.call_count,finish.call_count,observe.call_count),(0,1,1))
        self.assertEqual((actual.status,actual.last_observation.completion.status),('NOT_CONFIRMED','INCOMPLETE'))
        self.assertEqual(actual.last_observation.completion.operation_reference,'runner:own:source')
        self.assertTrue(issued[0][0]._native.finished)
        self.assertTrue(ModuleCaptureScope.validate_issued_for_context(issued[0][0],collector,encoder,issued[0][1]))

    def test_historical_rt_capture_foreign_scope_is_untouched_and_wrong_original_receipt_cleanup_once(self):
        from tests.test_m3_module_diagnostics import assembly as old_runtime
        from core.ash_pattern_engine.realm_transition import RealmTransitionReferenceRunner
        collector,_,owners,origin,_,_=old_runtime()
        encoder,registry=owners[:2]
        runner=RealmTransitionReferenceRunner(encoder,registry,collector)
        result=encoder.encode(origin,operation_reference='rt:foreign')
        context=mv.ModuleCaptureContext(result.operation_reference,'REALM_ENCODER',encoder.configuration(),origin,result,())
        scope=collector.module_capture(encoder,context).scope
        with patch.object(type(collector),'module_capture',return_value=mv.ModuleCaptureAdmission('rt:injected','ADMITTED',scope,None)),\
                patch.object(ModuleCaptureScope,'finish',wraps=ModuleCaptureScope.finish) as finish:
            actual=runner.run_encode(origin,operation_reference='rt:injected')
        self.assertEqual((actual.status,finish.call_count,scope._native.finished,scope._native.failed),('NOT_CONFIRMED',0,False,None))
        original=type(collector).module_capture
        def wrong(admitted_collector,producer,actual_context,**kwargs):
            admission=original(admitted_collector,producer,actual_context,**kwargs)
            return mv.ModuleCaptureAdmission('rt:wrong:receipt','ADMITTED',admission.scope,None)
        with patch.object(type(collector),'module_capture',wrong),\
                patch.object(ModuleCaptureScope,'append',wraps=ModuleCaptureScope.append) as append,\
                patch.object(ModuleCaptureScope,'finish',wraps=ModuleCaptureScope.finish) as finish:
            actual=runner.run_encode(origin,operation_reference='rt:own')
        self.assertEqual((actual.status,append.call_count,finish.call_count,actual.completion.status),('NOT_CONFIRMED',0,1,'INCOMPLETE'))
        self.assertEqual(actual.completion.operation_reference,'rt:own')

    def test_configuration_exact_expectations_refuse_foreign_and_hostile_before_hooks_or_io(self):
        runner,_,_,_,_,target,ports=runtime_assembly(depth=0)
        _,model,collector,store,clock,_,_=ports
        before=(len(store.calls),clock.value)
        expected=ReferenceGenerationRunner.configuration(runner)
        self.assertEqual(ReferenceGenerationRunner.configuration(runner,state_model=model,diagnostics=collector),expected)
        foreign_model=copy.copy(model)
        for arguments in ({'state_model':foreign_model},{'diagnostics':copy.copy(collector)}):
            with self.assertRaises(p.PlannerEmitterContractError):
                ReferenceGenerationRunner.configuration(runner,**arguments)
        calls=[]
        class HostileType(type):
            def __eq__(cls,other):calls.append('eq');raise AssertionError('caller equality')
            def __hash__(cls):calls.append('hash');raise AssertionError('caller hash')
        class Hostile(metaclass=HostileType):
            def __eq__(self,other):calls.append('value_eq');raise AssertionError('caller value equality')
            def __str__(self):calls.append('str');raise AssertionError('caller string')
        for name in ('state_model','diagnostics'):
            with self.assertRaises(p.PlannerEmitterContractError):
                ReferenceGenerationRunner.configuration(runner,**{name:Hostile()})
        clone=copy.copy(runner)
        clone._cookie=runner._cookie
        with self.assertRaises(p.PlannerEmitterContractError):
            ReferenceGenerationRunner.configuration(clone,state_model=model,diagnostics=collector)
        reflected=copy.copy(runner)
        reflected._model=foreign_model
        with self.assertRaises(p.PlannerEmitterContractError):
            ReferenceGenerationRunner.configuration(reflected,state_model=foreign_model,diagnostics=collector)
        self.assertEqual(calls,[])
        self.assertEqual((len(store.calls),clock.value),before)

    def test_actual_depth5_ready_nonzero_fourstep_complete_prefix_and13_delegated_grants(self):
        runner,inputs,origin,declared,constraints,target,ports=runtime_assembly()
        core,model,collector,store,clock,planner,emitter=ports
        lifecycle,gate=run_gate(core,collector,'runtime:run')
        with patch.object(CoreExecutionGate,'stage_grant',wraps=CoreExecutionGate.stage_grant) as grants:
            actual=runner.run(inputs,origin,declared,constraints,operation_reference='runtime:run',execution_gate=gate)
        self.assertEqual(actual.status,'READY',(actual.last_stage,getattr(actual.last_observation,'failure_code',None)))
        self.assertTrue(runner.validate_owned_result(actual))
        capture=actual.last_observation
        self.assertEqual((capture.status,capture.completion.status,capture.final_observation.status),('CONFIRMED','COMPLETE','CONFIRMED'))
        self.assertEqual((len(capture.result.plan.topology_nodes),len(capture.result.plan.artifacts)),(243,8))
        self.assertEqual([step.transformation_observation.candidate.signature for step in capture.result.request.chain.steps],
                         ['000011110','000000000','001100110','000000000'])
        self.assertEqual(actual.completed_operation_references,tuple('runtime:run:'+suffix for suffix in
                         ('source','chain','final','destination','topology','axioms','planner')))
        self.assertEqual(grants.call_count,13)
        self.assertEqual(target.snapshot().documents,())

    def test_initial_nonvalid_or_foreign_origin_preserves_actual_refusal_without_new_plan(self):
        runner,inputs,origin,declared,constraints,target,ports=runtime_assembly(depth=0)
        _,model,collector,store,clock,_,_=ports
        invalid=diagnosis(model,'010101010','runtime:tc')
        type(collector).complete_assessment(collector,invalid)
        before=len(store.calls)
        actual=runner.run(inputs,invalid,declared,constraints,operation_reference='runtime:refused')
        self.assertEqual((actual.status,actual.last_stage),('REFUSED','ORIGIN'))
        self.assertIs(actual.last_observation,invalid)
        self.assertEqual(actual.completed_operation_references,())
        self.assertEqual(len(store.calls),before)

    def test_original_runner_copies_reflected_reset_and_foreign_gate_refuse_before_hooks(self):
        runner,inputs,origin,declared,constraints,target,ports=runtime_assembly(depth=0)
        core,model,collector,store,clock,_,_=ports
        for clone in (copy.copy(runner),copy.deepcopy(runner,{id(x):x for x in ports+(target,)})):
            with self.assertRaises(p.PlannerEmitterContractError):ReferenceGenerationRunner.configuration(clone)
        before=len(store.calls)
        with self.assertRaises(p.PlannerEmitterContractError):
            runner.run(inputs,origin,declared,constraints,operation_reference='runtime:bad',execution_gate=object())
        self.assertEqual(before,len(store.calls))


if __name__=='__main__':unittest.main()
