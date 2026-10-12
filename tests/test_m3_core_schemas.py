"""Offline authored format coverage and actual current Core packet schema boundaries."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator
from referencing import Registry,Resource
from core import core_values as v
from core.deterministic_policy import DeterministicPolicy
from core.ash_pattern_engine import normalization
from core.ash_pattern_engine.state_model import StateModel
from tests.test_m3_core_values import core_binding
from tests.test_m3_core_orchestration import gated_normalization

ROOT=Path(__file__).resolve().parents[1]


def offline_schemas():
    def deny(uri):
        raise AssertionError('Schema attempted network retrieval: '+uri)
    names=('m3_core_domain_schema.json','m3_core_wire_format_cases_schema.json','m3_planner_emitter_schema.json',
        'm3_generation_state_schema.json','m3_generation_normalization_plan_schema.json',
        'm3_generation_state_normalization_schema.json','m3_generation_realm_transition_schema.json',
        'm3_generation_topology_axiom_schema.json','m3_state_assessment_schema.json','m3_normalization_plan_schema.json',
        'm3_state_normalization_schema.json','m3_realm_transition_schema.json','m3_topology_axiom_schema.json',
        'prophecy_schema_expansion.json','m3_reference_diagnostic_bundle_schema.json')
    schemas={name:json.loads((ROOT/'data/schemas'/name).read_text(encoding='utf-8')) for name in names}
    for value in schemas.values():
        Draft202012Validator.check_schema(value)
    registry=Registry(retrieve=deny).with_resources((value['$id'],Resource.from_contents(value)) for value in schemas.values())
    return schemas,registry


class CoreSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas,cls.registry=offline_schemas()

    def validator(self,definition):
        source=self.schemas['m3_core_domain_schema.json']
        return Draft202012Validator({'$ref':source['$id']+'#/$defs/'+definition},registry=self.registry)

    def test_all53_preserved_authored_format_bodies_and_closed_wrapper_offline(self):
        bundle=json.loads((ROOT/'examples/core_domain/core_wire_format_cases.example.json').read_text(encoding='utf-8'))
        wrapper=Draft202012Validator(self.schemas['m3_core_wire_format_cases_schema.json'],registry=self.registry)
        self.assertEqual(list(wrapper.iter_errors(bundle)),[])
        self.assertEqual([row['schema_definition'] for row in bundle['cases']],[kind.__name__ for kind in v.WIRE_TYPES])
        for row in bundle['cases']:
            raw=json.dumps(row['value'],sort_keys=True,ensure_ascii=True,separators=(',',':')).encode('ascii')
            self.assertEqual(hashlib.sha256(raw).hexdigest(),row['value_sha256'])
            self.assertEqual(list(self.validator(row['schema_definition']).iter_errors(row['value'])),[])
            changed=copy.deepcopy(row['value'])
            changed['unowned_debug_field']=True
            self.assertTrue(list(self.validator(row['schema_definition']).iter_errors(changed)))
        malformed=copy.deepcopy(bundle)
        malformed['cases'][0]['schema_definition']='Other'
        self.assertTrue(list(wrapper.iter_errors(malformed)))

    def test_actual_normalize_bias_result_and_prophecy_transport_boundaries(self):
        owner=DeterministicPolicy(core_binding())
        actual=owner.normalize((v.WeightedOption('a',1),v.WeightedOption('b',2)))
        self.assertEqual(list(self.validator('CoreResult').iter_errors(actual.to_record())),[])
        provenance=v.CoreProvenance('snapshot','diagnostic','plan',('source',))
        route=v.ProphecyRoute('route',('condition',),'interpretation')
        prophecy=v.ProphecyRecord('prophecy',provenance,v.ProphecyAttractor('domain','target',500000),False,(route,),(),'DORMANT',('condition',))
        record=prophecy.to_record()
        self.assertEqual(list(self.validator('ProphecyRecord').iter_errors(record)),[])
        for field,value in (('fixed_script',True),('condition_refs',[]),('weight_q6',1000001)):
            changed=copy.deepcopy(record)
            if field=='weight_q6':changed['attractor'][field]=value
            else:changed[field]=value
            self.assertTrue(list(self.validator('ProphecyRecord').iter_errors(changed)))
        # Additive prophecy transport retains the historical M2 metadata root.
        old=json.loads((ROOT/'data/schemas/prophecy_schema_expansion.json').read_text(encoding='utf-8'))
        validator=Draft202012Validator({'$ref':old['$id']+'#/$defs/ProphecyRecord'},registry=self.registry)
        self.assertEqual(list(validator.iter_errors(record)),[])

    def test_actual_source4_stopped_post_null_attempt_and_historical_null_refusal(self):
        model,collector,store,clock,plan,context,lifecycle,gate=gated_normalization()
        original=normalization._NormalizationOperations._append
        def stop_after_ack(scope,record,execution_gate=None):
            response=original(scope,record,execution_gate)
            if record.phase=='COMPUTATION' and response=='CONFIRMED':
                lifecycle.stop('stop',expected_generation=1)
            return response
        with patch.object(normalization._NormalizationOperations,'_append',staticmethod(stop_after_ack)):
            actual=StateModel.apply_normalization(model,plan,normalization_context=context,execution_gate=gate)
        record=actual.to_record()
        schema=self.schemas['m3_generation_state_normalization_schema.json']
        validator=Draft202012Validator(schema,registry=self.registry)
        self.assertEqual(list(validator.iter_errors(record)),[])
        self.assertEqual(record['attempted_diagnostic'],None)
        for changes in ({'emitted_diagnostics':[]},{'failed_field':'post_validity_diagnostic'},
                        {'capture_status':'REJECTED','failure_code':'DIAGNOSTIC_CAPTURE_REJECTED'}):
            invalid=copy.deepcopy(record);invalid.update(changes)
            self.assertTrue(list(validator.iter_errors(invalid)))
        historical=Draft202012Validator(self.schemas['m3_state_normalization_schema.json'],registry=self.registry)
        self.assertTrue(list(historical.iter_errors(record)))


if __name__=='__main__':
    unittest.main()
