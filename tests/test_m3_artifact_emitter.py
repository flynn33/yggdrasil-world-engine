"""Actual ACK-before-memory-effect and cancellation truth, with immutable first cleanup."""
import copy
import threading
import unittest
from unittest.mock import patch

from core.ash_pattern_engine import planner_emitter_values as p
from core.ash_pattern_engine.artifact_emitter import ReferenceArtifactEmitter
from core.ash_pattern_engine.memory_document_target import MemoryDocumentTarget
from core.ash_pattern_engine.diagnostic_module_capture import ModuleCaptureScope
from core.ash_pattern_engine.generation_runner import ReferenceGenerationRunner
from core.module_lifecycle import CoreModuleLifecycle,CoreExecutionGate
from core.deterministic_policy import DeterministicPolicy
from tests.test_m3_generation_runner import runtime_assembly


def ready(*,depth=0,choice='REFERENCE_MANIFEST_PAGES'):
    runtime=runtime_assembly(depth=depth,choice=choice)
    runner,inputs,origin,subject,constraints,target,ports=runtime
    run=runner.run(inputs,origin,subject,constraints,operation_reference='emit:run')
    if run.status!='READY':raise AssertionError(run.to_record())
    return runtime,run


def emission_gate(core,collector,reference):
    lifecycle=CoreModuleLifecycle(DeterministicPolicy(core))
    lifecycle.start('emit:start',expected_generation=0)
    stages=('EMISSION_PREPARE','EMISSION_DISPATCH')
    ticket=lifecycle.admit(reference,expected_generation=1,operation_bindings=((reference,stages),))
    original=lifecycle.execution_gate(ticket,collector)
    return lifecycle,CoreExecutionGate.for_operation(original,reference,stages)


class ArtifactEmitterTests(unittest.TestCase):
    def test_effect_scope_foreign_is_untouched_and_wrong_original_receipt_cleanup_once(self):
        from core.ash_pattern_engine import diagnostic_module_values as mv
        runtime,run=ready()
        runner,_,_,_,_,target,ports=runtime
        collector,encoder=ports[2],runner._encoder
        origin=run.last_observation.result.request.final_origin_diagnosis
        foreign=encoder.encode(origin,operation_reference='emit:foreign')
        context=mv.ModuleCaptureContext(foreign.operation_reference,'REALM_ENCODER',encoder.configuration(),origin,foreign,())
        scope=collector.module_capture(encoder,context).scope
        with patch.object(type(collector),'module_capture',return_value=mv.ModuleCaptureAdmission('emit:injected','ADMITTED',scope,None)),\
                patch.object(ModuleCaptureScope,'append',wraps=ModuleCaptureScope.append) as append,\
                patch.object(ModuleCaptureScope,'finish',wraps=ModuleCaptureScope.finish) as finish,\
                patch.object(MemoryDocumentTarget,'materialize',wraps=MemoryDocumentTarget.materialize) as effect:
            actual=runner.emit(run.last_observation,target,operation_reference='emit:injected')
        self.assertEqual((append.call_count,finish.call_count,effect.call_count),(0,0,0))
        self.assertEqual((scope._native.finished,scope._native.failed),(False,None))
        self.assertEqual((actual.status,actual.result.actual_effects,actual.completion),('NOT_CONFIRMED',False,None))
        original=type(collector).module_capture
        def wrong(admitted_collector,producer,actual_context,**kwargs):
            admission=original(admitted_collector,producer,actual_context,**kwargs)
            return mv.ModuleCaptureAdmission('emit:wrong:receipt','ADMITTED',admission.scope,None)
        with patch.object(type(collector),'module_capture',wrong),\
                patch.object(ModuleCaptureScope,'append',wraps=ModuleCaptureScope.append) as append,\
                patch.object(ModuleCaptureScope,'finish',wraps=ModuleCaptureScope.finish) as finish,\
                patch.object(MemoryDocumentTarget,'materialize',wraps=MemoryDocumentTarget.materialize) as effect:
            actual=runner.emit(run.last_observation,target,operation_reference='emit:own')
        self.assertEqual((append.call_count,finish.call_count,effect.call_count),(0,1,0))
        self.assertEqual((actual.status,actual.result.actual_effects,actual.completion.status),('NOT_CONFIRMED',False,'INCOMPLETE'))
        self.assertEqual(actual.completion.operation_reference,'emit:own')

    def test_reflected_original_control_and_owner_runtime_members_reject_before_caller_hooks(self):
        runtime,run=ready()
        runner,_,_,_,_,target,ports=runtime
        collector,store,clock,planner,emitter=ports[2],ports[3],ports[4],ports[5],ports[-1]
        # Retain an actual completed operation and separately genuine unused preparation.
        captured=runner.emit(run.last_observation,target,operation_reference='emit:reflection:complete')
        self.assertEqual(captured.status,'CONFIRMED')
        preparation=type(collector).prepare_emission(collector,planner,run.last_observation.result,
                run.last_observation,emitter,target,operation_reference='emit:reflection:prepared')
        self.assertIsNotNone(preparation.prepared)
        control=p._issue_emitter_control(emitter,collector,'emit:reflection:prepared',preparation.prepared,('emit:record',))
        hooks=[]
        class Hostile:
            def __bool__(self):hooks.append('bool');return False
            def __eq__(self,other):hooks.append('eq');return False
            def __iter__(self):hooks.append('iter');return iter(())
            def acquire(self,*args):hooks.append('acquire');return False
            def release(self):hooks.append('release')
        before=(len(store.calls),clock.value,target.snapshot().revision)
        for field in ('_sealed','_lock','_operation','_slots'):
            original=getattr(control,field)
            setattr(control,field,Hostile())
            try:self.assertEqual(p.IssuedEmitterCaptureControl.capture_disposition(control),'UNAVAILABLE')
            finally:setattr(control,field,original)
        for field in ('_sealed','_lock','_operations'):
            original=getattr(emitter,field)
            setattr(emitter,field,Hostile())
            try:
                for call in (lambda:emitter.configuration(),lambda:emitter.cancel('emit:reflection:complete'),emitter.shutdown):
                    with self.assertRaises(p.PlannerEmitterContractError):call()
            finally:setattr(emitter,field,original)
        operation=emitter._operations['emit:reflection:complete']
        for field in ('cancelled','final'):
            original=getattr(operation,field)
            setattr(operation,field,Hostile())
            try:
                with self.assertRaises(p.PlannerEmitterContractError):emitter.configuration()
            finally:setattr(operation,field,original)
        self.assertEqual(hooks,[])
        self.assertEqual((len(store.calls),clock.value,target.snapshot().revision),before)

    def test_actual_h4_depth5_eight_documents_ack_each_action_and10_delegated_grants(self):
        from core.ash_pattern_engine.generation_planner import ReferenceGenerationPlanner
        runtime,run=ready(depth=5)
        runner,inputs,origin,subject,constraints,target,ports=runtime
        core,model,collector,store,clock,planner,emitter=ports
        lifecycle,gate=emission_gate(core,collector,'emit:eight')
        with patch.object(CoreExecutionGate,'stage_grant',wraps=CoreExecutionGate.stage_grant) as grants,\
                patch.object(ReferenceGenerationPlanner,'plan',side_effect=AssertionError('emission requested new planning')) as planning:
            actual=runner.emit(run.last_observation,target,operation_reference='emit:eight',execution_gate=gate)
        self.assertEqual(planning.call_count,0)
        self.assertEqual((actual.status,actual.result.status,actual.result.actual_effects),('CONFIRMED','SUCCEEDED',True),
                         (actual.failure_code,None if actual.completion is None else actual.completion.failure_code,actual.final_observation))
        self.assertEqual(grants.call_count,10)
        self.assertEqual([call.args[1] for call in grants.call_args_list],['EMISSION_PREPARE']*2+['EMISSION_DISPATCH']*8)
        self.assertTrue(runner.validate_owned_result(actual))
        self.assertEqual((actual.completion.status,actual.final_observation.status),('COMPLETE','CONFIRMED'))
        self.assertEqual((len(actual.result.outcomes),len(actual.confirmed_records)),(8,17))
        snapshot=target.snapshot()
        self.assertEqual((snapshot.revision,len(snapshot.documents)),(8,8))
        for document,artifact,outcome in zip(snapshot.documents,run.last_observation.result.plan.artifacts,actual.result.outcomes):
            self.assertEqual(document.content_ascii,p.canonical_bytes(artifact.document).decode('ascii'))
            self.assertEqual((document.actual_sha256,document.actual_byte_count),(outcome.observed_sha256,outcome.observed_byte_count))
            self.assertEqual(outcome.actual_status,'SUCCEEDED')
        protected=collector.snapshot(bundle_reference='emit:eight:protected')
        wrappers=protected.supporting_evidence.module_evidence
        leaves={row.evidence_reference:row for row in wrappers}
        operations=[row.payload.to_record() for row in wrappers if row.kind=='PRODUCER_OPERATION' and
                    row.payload.to_record()['producer']=='ARTIFACT_EMITTER']
        self.assertEqual(len(operations),1)
        self.assertEqual(len(operations[0]['output_references']),1)
        self.assertEqual(leaves[operations[0]['output_references'][0]].kind,'GENERATION_PLAN')
        receipt_records=[row.payload.to_record() for row in wrappers if row.kind=='PRODUCER_RECORD' and
                         row.payload.to_record()['phase']=='ARTIFACT_RECEIPT']
        self.assertEqual(len(receipt_records),8)
        for record in receipt_records:
            self.assertEqual(record['value_reference'],record['payload_reference'])
            self.assertEqual(leaves[record['value_reference']].kind,'EMISSION_OUTPUT')

    def test_actual_depth6_ready_plan_global_alias_reservation_refuses_before_target_effect(self):
        from core.ash_pattern_engine import diagnostic_module_values as mv
        runtime,run=ready(depth=6)
        runner,_,_,_,_,target,ports=runtime
        collector=ports[2]
        self.assertEqual((len(run.last_observation.result.plan.topology_nodes),len(run.last_observation.result.plan.artifacts)),(729,23))
        # Private count is a local capacity audit; no caller-facing authenticity claim.
        retained_aliases=len(collector._aliases)
        self.assertGreater(retained_aliases+mv.WHOLE_RESERVATIONS['ARTIFACT_EMITTER']['aliases'],6144)
        with patch.object(MemoryDocumentTarget,'materialize',wraps=MemoryDocumentTarget.materialize) as effect:
            actual=runner.emit(run.last_observation,target,operation_reference='emit:depth6:capacity')
        self.assertEqual((actual.status,actual.result.status,actual.result.actual_effects),('NOT_CONFIRMED','FAILED',False))
        self.assertEqual(actual.result.failure_code,'CAPTURE_ADMISSION_UNCONFIRMED')
        self.assertEqual((actual.result.outcomes,actual.completion,target.snapshot().documents),((),None,()))
        self.assertEqual(effect.call_count,0)
        self.assertEqual(len(collector._aliases),retained_aliases)

    def test_explicit_inspect_only_noop_and_idempotent_retry_preserve_actual_revision(self):
        runtime,run=ready(choice='INSPECT_ONLY')
        runner,_,_,_,_,target,_=runtime
        actual=runner.emit(run.last_observation,target,operation_reference='emit:inspect')
        self.assertEqual((actual.status,actual.result.status,actual.result.actual_effects),('CONFIRMED','NO_OP',False))
        self.assertEqual((actual.result.outcomes,len(actual.result.produced_diagnostics),target.snapshot().revision),((),1,0))
        runtime,run=ready()
        runner,_,_,_,_,target,_=runtime
        first=runner.emit(run.last_observation,target,operation_reference='emit:first')
        second=runner.emit(run.last_observation,target,operation_reference='emit:retry')
        self.assertEqual((first.result.status,second.result.status,second.result.outcomes[0].actual_status),('SUCCEEDED','NO_OP','NO_EFFECT'))
        self.assertEqual(target.snapshot().revision,1)

    def test_cancel_after_real_dispatch_ack_denies_action_and_keeps_once_cleanup(self):
        runtime,run=ready()
        runner,_,_,_,_,target,ports=runtime
        emitter=ports[-1]
        original=ModuleCaptureScope.append
        def append(scope,record):
            response=original(scope,record)
            if type(record.payload) is p.EmissionDispatchDiagnostic:
                self.assertEqual(response.status,'CONFIRMED')
                emitter.cancel('emit:cancel')
            return response
        with patch.object(ModuleCaptureScope,'append',append),patch.object(MemoryDocumentTarget,'materialize',wraps=MemoryDocumentTarget.materialize) as action:
            actual=runner.emit(run.last_observation,target,operation_reference='emit:cancel')
        self.assertEqual(action.call_count,0)
        self.assertEqual((actual.status,actual.result.status,actual.result.actual_effects,actual.result.failure_code),
                         ('NOT_CONFIRMED','FAILED',False,'COMMAND_CANCELLED'))
        self.assertEqual(len(actual.confirmed_records),1)
        self.assertEqual(actual.completion.status,'INCOMPLETE')
        self.assertEqual(target.snapshot().documents,())

    def test_concurrent_cancel_keeps_granted_late_effect_and_denies_ordinary_receipt_ack(self):
        runtime,run=ready(depth=4)
        runner,_,_,_,_,target,ports=runtime
        emitter=ports[-1]
        entered,release=threading.Event(),threading.Event()
        original=MemoryDocumentTarget.materialize
        results,errors=[],[]
        def blocked(actual_target,lease,description):
            entered.set()
            if not release.wait(5):raise AssertionError('release missing')
            return original(actual_target,lease,description)
        def execute():
            try:results.append(runner.emit(run.last_observation,target,operation_reference='emit:late'))
            except BaseException as error:errors.append(error)
        with patch.object(MemoryDocumentTarget,'materialize',blocked):
            thread=threading.Thread(target=execute);thread.start()
            try:
                self.assertTrue(entered.wait(5))
                self.assertEqual(emitter.cancel('emit:late').status,'LATCHED')
                self.assertTrue(thread.is_alive())
            finally:release.set();thread.join(5)
        self.assertEqual(errors,[])
        self.assertFalse(thread.is_alive())
        actual=results[0]
        self.assertEqual((actual.status,actual.result.status,actual.result.actual_effects),('NOT_CONFIRMED','PARTIAL',True))
        self.assertEqual((len(actual.result.outcomes),actual.result.outcomes[0].actual_status,len(actual.confirmed_records)),(1,'SUCCEEDED',1))
        self.assertEqual(actual.completion.status,'INCOMPLETE')
        self.assertEqual((target.snapshot().revision,len(target.snapshot().documents)),(1,1))

    def test_unknown_target_return_stops_following_dispatch_without_effect_guess(self):
        runtime,run=ready(depth=4)
        runner,_,_,_,_,target,_=runtime
        with patch.object(MemoryDocumentTarget,'materialize',side_effect=RuntimeError('unretained injected prose')) as calls:
            actual=runner.emit(run.last_observation,target,operation_reference='emit:unknown')
        self.assertEqual(calls.call_count,1)
        self.assertEqual((actual.result.status,actual.result.actual_effects,actual.result.outcomes[0].actual_status),('UNKNOWN',None,'UNKNOWN'))
        self.assertEqual(target.snapshot().documents,())
        self.assertNotIn('unretained injected prose',str(actual.to_record()))

    def test_original_composition_seals_and_readable_configuration_after_shutdown(self):
        runtime,_=ready()
        runner,_,_,_,_,target,ports=runtime
        collector,emitter=ports[2],ports[-1]
        self.assertTrue(ReferenceArtifactEmitter.validate_preparation_composition(emitter,collector,target))
        self.assertFalse(ReferenceArtifactEmitter.validate_preparation_composition(emitter,object(),target))
        memo={id(x):x for x in ports+(target,) if x is not emitter}
        memo[id(emitter._lock)]=emitter._lock
        for clone in (copy.copy(emitter),copy.deepcopy(emitter,memo)):
            self.assertFalse(ReferenceArtifactEmitter.validate_preparation_composition(clone,collector,target))
        first=emitter.shutdown();second=emitter.shutdown()
        self.assertEqual((first.status,first.unused_preparation_count,second.status,second.unused_preparation_count),
                         ('SEALED',0,'ALREADY_SEALED',0))
        self.assertTrue(ReferenceArtifactEmitter.validate_preparation_composition(emitter,collector,target))


if __name__=='__main__':unittest.main()
