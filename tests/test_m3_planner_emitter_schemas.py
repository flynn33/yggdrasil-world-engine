"""Offline source4 format closure; authored shapes do not prove persistence or effects."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from referencing import Registry,Resource

from core.ash_pattern_engine import normalization_values as nv,normalization,state_values as s
from core.ash_pattern_engine.state_model import StateModel
from tests.test_m3_planner_emitter_values import shape_values
from tests.test_m3_core_orchestration import gated_normalization

ROOT=Path(__file__).resolve().parents[1]


def validators():
    resources=[]
    for path in (ROOT/'data/schemas').glob('*.json'):
        source=json.loads(path.read_text(encoding='utf-8'))
        if isinstance(source,dict) and '$id' in source:
            resources.append((source['$id'],Resource.from_contents(source)))
    registry=Registry().with_resources(resources)
    return registry


def selected(name,family='m3_planner_emitter_schema.json'):
    source=json.loads((ROOT/'data/schemas'/family).read_text(encoding='utf-8'))
    return Draft202012Validator({'$ref':source['$id']+'#/$defs/'+name},registry=validators())


class PlannerEmitterSchemaTests(unittest.TestCase):
    def test_actual_already_valid_stopped_post_has_zero_steps_and_same_closed_current_prefix(self):
        from tests.test_m3_core_orchestration import current_assembly
        from tests.test_m3_realm_transition_values import diagnosis
        from core.module_lifecycle import CoreModuleLifecycle,CoreExecutionGate
        from core.deterministic_policy import DeterministicPolicy
        binding,model,collector,_,_=current_assembly()
        origin=diagnosis(model,'000000000','schema:already:origin')
        self.assertEqual(collector.complete_assessment(origin).status,'COMPLETE')
        policy=nv.NormalizationPolicyBinding(*[expected for _,expected in nv.NORMALIZATION_POLICY_BINDING_FIELDS])
        plan=StateModel.plan_normalization(model,origin,plan_reference='schema:already:plan',
                 evidence_reference='schema:already:evidence',policy_binding=policy)
        self.assertEqual(plan.decision,'ALREADY_VALID')
        context=nv.NormalizationContext('schema:already','schema:already:computation','schema:already:post')
        lifecycle=CoreModuleLifecycle(DeterministicPolicy(binding));lifecycle.start('schema:start',expected_generation=0)
        stages=('NORMALIZATION_VALUE','NORMALIZATION_POST_CAPTURE')
        ticket=lifecycle.admit('schema:work',expected_generation=1,operation_bindings=((context.operation_reference,stages),))
        gate=CoreExecutionGate.for_operation(lifecycle.execution_gate(ticket,collector),context.operation_reference,stages)
        original=normalization._NormalizationOperations._append
        def stop_after_ack(scope,record,execution_gate=None):
            receipt=original(scope,record,execution_gate)
            if record.phase=='COMPUTATION' and receipt=='CONFIRMED':lifecycle.stop('schema:stop',expected_generation=1)
            return receipt
        with patch.object(normalization._NormalizationOperations,'_append',staticmethod(stop_after_ack)):
            actual=StateModel.apply_normalization(model,plan,normalization_context=context,execution_gate=gate)
        self.assertIs(type(actual),nv.NormalizationCaptureFailure)
        self.assertEqual((actual.steps,len(actual.emitted_diagnostics),actual.attempted_diagnostic),((),1,None))
        self.assertEqual(collector.complete_normalization(actual,execution_gate=gate).status,'INCOMPLETE')
        record=actual.to_record()
        validator=selected('DiagnosticCaptureFailure','m3_generation_state_normalization_schema.json')
        validator.validate(record)
        missing=copy.deepcopy(record);missing['emitted_diagnostics']=[]
        self.assertTrue(list(validator.iter_errors(missing)))
        self.assertTrue(list(selected('DiagnosticCaptureFailure','m3_state_normalization_schema.json').iter_errors(record)))

    def test_all36_owned_shapes_validate_and_each_requires_every_member_and_rejects_unknown(self):
        values=shape_values()
        self.assertEqual(len(values),36)
        for value in values.values():
            name=type(value).__name__
            validator=selected(name)
            record=value.to_record()
            with self.subTest(name=name):
                validator.validate(record)
                unknown={**record,'unowned_metadata':True}
                self.assertTrue(any(e.validator=='additionalProperties' for e in validator.iter_errors(unknown)))
                for field in record:
                    missing=copy.deepcopy(record);del missing[field]
                    self.assertTrue(any(e.validator=='required' for e in validator.iter_errors(missing)),field)

    def test_new_pe_family_routes_full_source4_nested_facts_and_historical_families_refuse_it(self):
        from tests.test_m3_generation_planner import planner_assembly
        from tests.test_m3_transition_chain import select
        from tests.test_m3_realm_transition_values import profile_from
        from core.ash_pattern_engine import generation_values as g,realm_transition_values as rt
        planner,request,_=planner_assembly(profile=profile_from(('000000000','000011110','001100110','001111000')))
        result=planner.plan(request)
        selected('PlannerResult').validate(result.to_record())
        for value,name,family,legacy,owner in ((request.origin_diagnosis,'StateDiagnosis','m3_generation_state_schema.json',
                'm3_state_assessment_schema.json',s),(request.source_encoding,'RealmEncodingResult','m3_generation_realm_transition_schema.json',
                'm3_realm_transition_schema.json',rt),(request.topology,'TopologyResult','m3_generation_topology_axiom_schema.json',
                'm3_topology_axiom_schema.json',g)):
            with self.subTest(name=name):
                self.assertEqual(owner.wire_schema(value),('data/schemas/' if owner is s else 'https://ywe.local/schemas/')+family)
                selected(name,family).validate(value.to_record())
                self.assertTrue(list(selected(name,legacy).iter_errors(value.to_record())))
        corrupt=copy.deepcopy(result.to_record())
        corrupt['binding']['canonical_binding']['diagnostic_schema_sha256']='0'*64
        self.assertTrue(list(selected('PlannerResult').iter_errors(corrupt)))

    def test_actual_stopped_post_prefix_current_schema_and_precise_closed_negatives(self):
        model,collector,store,clock,plan,context,lifecycle,gate=gated_normalization()
        original=normalization._NormalizationOperations._append
        def stop_after_ack(scope,record,execution_gate=None):
            receipt=original(scope,record,execution_gate)
            if record.phase=='COMPUTATION' and receipt=='CONFIRMED':
                lifecycle.stop('schema:stop',expected_generation=1)
            return receipt
        with patch.object(normalization._NormalizationOperations,'_append',staticmethod(stop_after_ack)):
            actual=StateModel.apply_normalization(model,plan,normalization_context=context,execution_gate=gate)
        self.assertIs(type(actual),nv.NormalizationCaptureFailure)
        first=collector.complete_normalization(actual,execution_gate=gate)
        self.assertEqual(first.status,'INCOMPLETE')
        self.assertEqual(len(actual.emitted_diagnostics),1)
        self.assertIsNone(actual.attempted_diagnostic)
        record=actual.to_record()
        validator=selected('DiagnosticCaptureFailure','m3_generation_state_normalization_schema.json')
        validator.validate(record)
        for field,changed in (('emitted_diagnostics',[]),('emitted_diagnostics',record['emitted_diagnostics']*2),
                              ('steps',[]),('post_validity_diagnostic',record['original_diagnosis']['state_validity_diagnostic']),
                              ('normalized_state',record['actual_state']),('failed_field','post_validity_diagnostic'),
                              ('capture_status','REJECTED'),('failure_code','DIAGNOSTIC_CAPTURE_REJECTED')):
            mutation=copy.deepcopy(record);mutation[field]=changed
            with self.subTest(field=field):self.assertTrue(list(validator.iter_errors(mutation)))
        self.assertTrue(list(selected('DiagnosticCaptureFailure','m3_state_normalization_schema.json').iter_errors(record)))


if __name__=='__main__':unittest.main()
