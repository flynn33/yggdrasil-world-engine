"""Independent integer expected outcomes for issued Core policies."""
import hashlib
import json
import unittest
from unittest.mock import patch
from core import core_values as v
from core.deterministic_policy import DeterministicPolicy
from tests.test_m3_core_values import core_binding


def event(identifier, domain='x', target='t', contribution=0):
    return v.BiasEvent(identifier, (v.BiasTerm(identifier, domain, target, contribution, ('source',)),), ('source',))


class CorePolicyTests(unittest.TestCase):
    def setUp(self):
        self.owner = DeterministicPolicy(core_binding())

    def test_hamilton_exact_remainders_ascii_ties_and_zero_distribution(self):
        actual = self.owner.normalize(tuple(v.WeightedOption(key, 1) for key in ('C', 'A', 'B')))
        self.assertEqual([(row.option_id, row.weight) for row in actual.value.options], [('A',333334), ('B',333333), ('C',333333)])
        self.assertEqual(actual.value.total_q6, 1000000)
        zero = self.owner.normalize((v.WeightedOption('x', 0),))
        self.assertEqual((zero.status, zero.value.total_q6, zero.value.options[0].weight), ('NO_OP',0,0))
        self.assertEqual(v.canonical_bytes(actual), v.canonical_bytes(self.owner.normalize(tuple(v.WeightedOption(key,1) for key in ('B','C','A')))))

    def test_sha_domain_full_binding_rejection_draw_and_exact16_exhaustion(self):
        request = v.SelectionRequest('domain', v._wire_digest(core_binding()), '0'*64, 'seed', (v.WeightedOption('b',2),v.WeightedOption('a',1)))
        body = {'algorithm':'YWE.CORE.SELECT.V1','domain':'domain','binding_hash':request.binding_sha256,'context_hash':'0'*64,'seed_token':'seed','counter':0}
        expected_draw = int.from_bytes(hashlib.sha256(json.dumps(body,ensure_ascii=True,sort_keys=True,separators=(',',':')).encode('ascii')).digest()[:8], 'big')
        actual = self.owner.select(request)
        self.assertEqual(actual.value.accepted_draw, expected_draw)
        self.assertEqual(actual.value.selected_id, 'a' if expected_draw%3 == 0 else 'b')
        with patch('core.deterministic_policy._selection_draw', return_value=(1<<64)-1) as draw:
            exhausted = self.owner.select(request)
        self.assertEqual((exhausted.status, exhausted.value.counters_used), ('PENDING',16))
        self.assertEqual(draw.call_count, 16)
        wrong = v.SelectionRequest('domain','1'*64,'0'*64,'seed',request.options)
        self.assertEqual(self.owner.select(wrong).diagnostics[0].failure_code, 'CORE_BINDING_MISMATCH')

    def test_existence_single_signed_ties_even(self):
        def measure(c, h):
            return self.owner.measure_existence(v.ExistentialMetricInputs('context', c,0,0,h,500000,0,0,500000,('fact',))).value.potential_q6
        self.assertEqual((measure(1,0),measure(3,0),measure(0,1),measure(0,3)), (0,2,0,-2))

    def test_bias_rank_insertion_delimiter_distinction_and_single_final_clamp(self):
        empty = v.BiasState('empty',0,(),())
        first = self.owner.merge_bias(empty,(event('one','a','z',400000),event('two','b','a',300000)),logical_epoch=0,retention_q6=1000000).value.proposed
        inserted = self.owner.merge_bias(first,(event('three','a','a',200000),),logical_epoch=0,retention_q6=1000000).value.proposed
        self.assertEqual([(row.option_id,row.weight) for row in inserted.weights], [('bias:00',200000),('bias:01',400000),('bias:02',300000)])
        colon = self.owner.merge_bias(empty,(event('colon1','a:b','c',70000),event('colon2','a','b:c',30000)),logical_epoch=0,retention_q6=1000000).value.proposed
        self.assertEqual([row.weight for row in colon.weights], [30000,70000])
        before = v.BiasState('before',0,(event('old',contribution=100000),),(v.WeightedOption('bias:00',100000),))
        after = self.owner.merge_bias(before,(event('add',contribution=1000000),event('subtract',contribution=-800000)),logical_epoch=0,retention_q6=1000000)
        self.assertEqual(after.value.proposed.weights[0].weight,300000)
        self.assertEqual(after.effect_status,'PROPOSED_ONLY')

    def test_bias_replay_never_readds_ledger_decay_floor_and_zero_key_retention(self):
        old = event('old', contribution=400000)
        before = v.BiasState('before',0,(old,),(v.WeightedOption('bias:00',400000),))
        decayed = self.owner.merge_bias(before,(old,old),logical_epoch=1,retention_q6=500000).value.proposed
        self.assertEqual(decayed.weights[0].weight,200000)
        replay = self.owner.merge_bias(decayed,(old,),logical_epoch=1,retention_q6=500000).value.proposed
        self.assertEqual(replay.weights[0].weight,200000)
        small = v.BiasState('small',0,(old,),(v.WeightedOption('bias:00',3),))
        self.assertEqual(self.owner.merge_bias(small,(),logical_epoch=2,retention_q6=500000).value.proposed.weights[0].weight,0)
        zero = self.owner.merge_bias(before,(),logical_epoch=1024,retention_q6=0).value.proposed
        self.assertEqual((len(zero.events),len(zero.weights),zero.weights[0].weight),(1,1,0))

    def test_bias_conflict_provenance_key_event_epoch_bounds_retain_before(self):
        before = v.BiasState('before',1,(event('old',contribution=4),),(v.WeightedOption('bias:00',4),))
        cases = ((before,(event('old',contribution=5),),1,'CORE_FACT_CONFLICT'),
            (v.BiasState('bad',1,before.events,(v.WeightedOption('arbitrary',4),)),(),1,'CORE_PROVENANCE_MISSING'),
            (before,(),0,'CORE_EPOCH_REVERSED'),(before,(),1026,'CORE_RESOURCE_LIMIT'),
            (before,tuple(event('new'+str(i),'domain'+str(i),'target',1) for i in range(64)),1,'CORE_RESOURCE_LIMIT'))
        for original, terms, epoch, code in cases:
            result = self.owner.merge_bias(original,terms,logical_epoch=epoch,retention_q6=1000000)
            self.assertEqual((result.status,result.diagnostics[0].failure_code),('REFUSED',code))
            self.assertIs(result.value,original)
        full = v.BiasState('full',0,tuple(event('e'+str(i), contribution=1) for i in range(512)),(v.WeightedOption('bias:00',512),))
        result = self.owner.merge_bias(full,(event('new'),),logical_epoch=0,retention_q6=1000000)
        self.assertEqual(result.diagnostics[0].failure_code,'CORE_RESOURCE_LIMIT')


if __name__ == '__main__':
    unittest.main()
