"""Closed owned values and bounded serializers; constructor facts confer no capture authority."""
import copy
from dataclasses import fields,is_dataclass,replace
import json
from pathlib import Path
import unittest

from core.ash_pattern_engine import planner_emitter_values as p, realm_transition_values as rt
from tests.test_m3_generation_planner import planner_assembly
from tests.test_m3_memory_document_target import target_assembly,test_lease
from tests.test_m3_transition_chain import select
from tests.test_m3_realm_transition_values import assembly as old_assembly,diagnosis
from core.ash_pattern_engine.generation_planner import record_reference


def shape_values():
    target,emitter,plan,planner,request=target_assembly()
    actual=planner.plan(request)
    artifact=plan.artifacts[0]
    outcome=target.materialize(test_lease(target,emitter,artifact,'value:emit'),artifact)
    origin=request.final_origin_diagnosis.emitted_diagnostics[0]
    emission_request=p.EmitterRequest('value:emit',plan,target.configuration(),'value:preparation')
    dispatch=p.EmissionDispatchDiagnostic('value:emit',plan.plan_reference,artifact.artifact_reference,
              artifact.plan_element_reference,0,artifact.content_sha256,artifact.content_byte_count,'target:memory')
    outcome_payload=p.EmissionOutcomeDiagnostic(record_reference('value:emit',0),outcome)
    summary=p.EmissionSummaryDiagnostic('value:emit',plan.plan_reference,'SUCCEEDED',1,1,1,True,None)
    rules=('ASH-GENERATION-TRACEABILITY-001','ASH-GENERATION-PLANFIDELITY-001','ASH-GENERATION-EMISSION-001')
    records=[]
    previous=origin.diagnostic_reference
    for index,payload in enumerate((dispatch,outcome_payload,summary)):
        reference=record_reference('value:emit',index)
        env=p.PlannerEmitterEnvelope('ARTIFACT_EMISSION','INFO','PROCESSING','RESOLVED',origin.envelope.subject_reference,
                                    previous,origin.envelope.chain_root_reference,rules,'Declared shape observation.',())
        records.append(p.PlannerEmitterRecord(reference,env,payload))
        previous=reference
    # Records above are explicitly authored value shapes over a real isolated target receipt.
    # No producer seal, scope, finish, ACK, final observer or host authentication is asserted.
    emitted=p.EmitterResult(emission_request,plan.binding,'SUCCEEDED',True,(outcome,),tuple(records),None,None)
    capture=p.PlannerEmitterCaptureReceipt('value:emit','NOT_CONFIRMED',emitted,(),None,None,None,'COMPLETION_UNCONFIRMED')
    dependency=p.GenerationDependencyCaptureReceipt(request.chain.operation_reference,'NOT_CONFIRMED',request.chain,
               (),None,None,None,'MODULE_CAPTURE_UNCONFIRMED')
    run=p.GenerationRunReceipt('value:run','NOT_CONFIRMED','PLANNER',capture,None,())
    failure=planner.plan(replace(request,target_constraints=replace(request.target_constraints,max_artifacts=0)))
    old_model,_,_=old_assembly()
    pending_failure=planner.plan(replace(request,final_origin_diagnosis=diagnosis(old_model,'100000000','value:foreign')))
    # The typed unknown-selection failure is produced by the genuine pure chain owner.
    registry=planner._registry
    chain_failure=registry.apply_chain(request.origin_diagnosis,(rt.TransitionSelection('IDENTIFIER','unknown',None),),
                                      operation_reference='value:failedchain')
    rejected=p.EmissionPreparationReceipt('value:preparation',plan.plan_reference,'target:memory','REJECTED',None,'PLAN_INCOMPLETE')
    found={}
    seen=set()
    def walk(value):
        if id(value) in seen:return
        seen.add(id(value))
        if any(type(value) is cls for cls in p.WIRE_TYPES):found.setdefault(type(value),value)
        if type(value) is tuple:
            for child in value:walk(child)
        elif is_dataclass(value):
            for field in fields(type(value)):walk(object.__getattribute__(value,field.name))
    for value in (actual,emitted,capture,dependency,run,failure,pending_failure,chain_failure,rejected,target.snapshot()):walk(value)
    return found


class PlannerEmitterValueTests(unittest.TestCase):
    def test_actual_exact36_field_orders_and_independently_bounded_shape_values(self):
        root=Path(__file__).resolve().parents[1]
        inventory=json.loads((root/'docs/design-planning/m3/planner-emitter/BUSINESS_API_INVENTORY.json').read_text())
        self.assertEqual(36,len(p.WIRE_TYPES))
        for row in inventory['types']:
            cls=getattr(p,row['name'])
            self.assertEqual(tuple(field.name for field in fields(cls)),tuple(field['name'] for field in row['constructor_fields']))
        values=shape_values()
        self.assertEqual(set(p.WIRE_TYPES),set(values))
        for value in values.values():
            p.revalidate_value(value)
            self.assertEqual(value.to_record(),json.loads(p.canonical_bytes(value)))

    def test_compact_raw_boundary_sentinel_and_fresh_record_containers(self):
        target,_,plan,_,_=target_assembly()
        raw=p.canonical_bytes(plan)
        self.assertEqual(raw,p.canonical_bytes(plan,limit=len(raw)))
        self.assertEqual(len(raw),p.raw_business_size(plan,len(raw)))
        self.assertEqual(len(raw),p.raw_business_size(plan,len(raw)-1))
        with self.assertRaises(p.PlannerEmitterContractError) as failure:p.canonical_bytes(plan,limit=len(raw)-1)
        self.assertEqual('RAW_BUSINESS_LIMIT',failure.exception.code)
        record=plan.to_record()
        record['role_assignments'].clear()
        self.assertEqual(1,len(plan.role_assignments))
        for bad in (True,0,p.RAW_BUSINESS_LIMIT+1):
            with self.assertRaises(p.PlannerEmitterContractError):p.raw_business_size(plan,bad)

    def test_hostile_type_deep_graph_scalar_union_and_cycle_reject_before_hooks(self):
        hooks=[]
        class Meta(type):
            def __eq__(cls,other):hooks.append('eq');return False
            def __hash__(cls):hooks.append('hash');return 7
        class Hostile(metaclass=Meta):
            def __str__(self):hooks.append('str');return 'foreign'
        value=Hostile()
        target,_,plan,_,_=target_assembly()
        for call in (lambda:p.canonical_bytes(value),lambda:p.raw_business_size(value),
                     lambda:replace(plan.inputs,transition_sequence=(value,)),lambda:replace(plan,target_constraints=value),
                     lambda:p.MemoryTargetConfiguration(value,'REFERENCE_MEMORY_DOCUMENTS',plan.binding.policy_binding,32,1048576)):
            with self.assertRaises(p.PlannerEmitterContractError):call()
        self.assertEqual([],hooks)
        cyclic=copy.copy(plan)
        object.__setattr__(cyclic,'binding',cyclic)
        with self.assertRaises(p.PlannerEmitterContractError):p.canonical_bytes(cyclic)

    def test_reflected_document_role_alias_and_actual_receipt_semantics_revalidated(self):
        target,emitter,plan,_,_=target_assembly()
        for kwargs in ({'source_realm':plan.destination_state_identity},):
            # Identity chain makes these equal; force a wrong full signature instead.
            bad=copy.copy(plan.source_state_identity)
            object.__setattr__(bad,'state_signature','111111111')
            with self.assertRaises((p.PlannerEmitterContractError,rt.RealmTransitionContractError)):
                replace(plan,source_realm=bad)
        artifact=plan.artifacts[0]
        with self.assertRaises(p.PlannerEmitterContractError):replace(artifact,content_sha256='0'*64)
        with self.assertRaises(p.PlannerEmitterContractError):replace(plan.role_assignments[0],role_kind='NEGATIVE')
        receipt=target.materialize(test_lease(target,emitter,artifact),artifact)
        with self.assertRaises(p.PlannerEmitterContractError):replace(receipt,actual_effects=False)
        with self.assertRaises(p.PlannerEmitterContractError):replace(receipt,target_revision_after=0)


if __name__=='__main__':unittest.main()
