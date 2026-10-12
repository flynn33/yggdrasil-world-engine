"""Exact Core wire boundaries, immutable data and original owner authority."""
import copy
from dataclasses import fields,asdict,replace
import hashlib
import json
from pathlib import Path
import unittest

from core import core_values as v
from core.ash_pattern_engine import state_values as s
from core.ash_pattern_engine.state_model import wrw_profile_binding
from core.deterministic_policy import DeterministicPolicy

ROOT = Path(__file__).resolve().parents[1]


def core_binding(*, profile=None, realms=()):
    return v.CoreBinding(s.CanonicalAshBinding(**dict(v.CANONICAL_FIELDS)),
        wrw_profile_binding() if profile is None else profile, v.CORE_POLICY_ID,
        v.CORE_POLICY_SHA256, realms)


class CoreValueTests(unittest.TestCase):
    def test_all53_inventory_field_orders_and_compiled_policy_source(self):
        inventory = json.loads((ROOT / 'docs/design-planning/m3/core-domain/CORE_API_INVENTORY.json').read_text(encoding='utf-8'))
        self.assertEqual(len(v.WIRE_TYPES), 53)
        for row in inventory['types']:
            self.assertEqual(tuple(field.name for field in fields(getattr(v, row['name']))), tuple(row['fields']))
        raw = (ROOT / 'docs/design-planning/m3/core-domain/CORE_POLICY.json').read_bytes().replace(b'\r\n', b'\n')
        self.assertEqual(hashlib.sha256(raw).hexdigest(), v.CORE_POLICY_SHA256)

    def test_identity_only_hostile_metaclass_and_conversion_boundaries(self):
        calls = []
        class Meta(type):
            def __eq__(self, other):
                calls.append('eq')
                return False
            def __hash__(self):
                calls.append('hash')
                return 0
        class Hostile(metaclass=Meta):
            def __str__(self):
                calls.append('str')
                return 'bad'
            def __iter__(self):
                calls.append('iter')
                return iter(())
        for value in (Hostile(), Hostile):
            for operation in (v.revalidate_value, v.canonical_bytes, v.raw_business_size):
                with self.assertRaises(v.CoreContractError):
                    operation(value)
            with self.assertRaises(v.CoreContractError):
                v.WeightedOption('bad', value)
        self.assertEqual(calls, [])

    def test_frozen_arrays_roundtrip_and_copied_data_are_legal(self):
        value = v.TruthInputSnapshot('snapshot', 'scope', [], ['entity'], 'DECLARED_INPUT')
        self.assertEqual(value.entity_refs, ('entity',))
        for replica in (copy.copy(value), copy.deepcopy(value)):
            self.assertEqual(v.canonical_bytes(replica), v.canonical_bytes(value))
        with self.assertRaises(AttributeError):
            value.entity_refs = ()

    def test_result_copy_reset_and_reflective_mutation_never_authenticate(self):
        owner = DeterministicPolicy(core_binding())
        actual = owner.normalize((v.WeightedOption('x', 1),))
        self.assertTrue(owner.validate_owned_result(actual))
        self.assertFalse(owner.validate_owned_result(copy.copy(actual)))
        changed = copy.copy(actual)
        object.__setattr__(changed, '_core_result_cookie', actual._core_result_cookie)
        self.assertFalse(owner.validate_owned_result(changed))
        object.__setattr__(actual, 'status', 'NO_OP')
        self.assertFalse(owner.validate_owned_result(actual))

    def test_reflected_owner_and_result_seal_hashes_reject_without_conversion_hooks(self):
        calls=[]
        class Hostile:
            def __eq__(self,other):calls.append('equality');return False
            def __hash__(self):calls.append('hash');return 0
            def __str__(self):calls.append('str');return 'hostile'
        owner=DeterministicPolicy(core_binding())
        actual=owner.normalize((v.WeightedOption('x',1),))
        object.__setattr__(actual._core_result_cookie,'wire_sha256',Hostile())
        self.assertFalse(owner.validate_owned_result(actual))
        object.__setattr__(owner._core_owner_cookie,'binding_sha256',Hostile())
        with self.assertRaises(v.CoreContractError):owner.configuration()
        self.assertEqual(calls,[])

    def test_bool_float_unicode_corruption_cycles_and_complete_binding_refuse(self):
        for value in (True, 0.5, float('nan'), float('inf'), -1, 1000001):
            with self.assertRaises(v.CoreContractError):
                v.WeightedOption('x', value)
        with self.assertRaises(v.CoreContractError):
            v.WeightedOption('\ud800', 1)
        packet = v.TruthInputSnapshot('snapshot', 'scope', (), (), 'DECLARED_INPUT')
        object.__setattr__(packet, 'facts', (packet,))
        with self.assertRaises(v.CoreContractError):
            v.canonical_bytes(packet)
        with self.assertRaises(v.CoreContractError):
            v.CoreBinding(s.CanonicalAshBinding(**dict(s.MODULE_CANONICAL_BINDING_FIELDS)),
                wrw_profile_binding(), v.CORE_POLICY_ID, v.CORE_POLICY_SHA256, ())

    def test_exact_whole1mib_and_plus_one_preserve_full_immutable_graph(self):
        evidence=tuple('r'+f'{index:02d}'+'x'*117 for index in range(65))
        facts=tuple(v.DeclaredTruthFact('fact'+f'{index:03d}','OBJECTIVE_SHARED','scope','subject','v',evidence) for index in range(128))
        packet=v.TruthInputSnapshot('snapshot','scope',facts,(),'DECLARED_INPUT')
        def independent_size(value):
            return len(json.dumps(asdict(value),sort_keys=True,ensure_ascii=True,separators=(',',':')).encode('ascii'))
        remaining=v.MAX_RAW_CORE_BYTES-independent_size(packet)
        self.assertGreater(remaining,0)
        self.assertLessEqual(remaining,128*511)
        grown=[]
        for fact in facts:
            addition=min(511,remaining)
            remaining-=addition
            grown.append(replace(fact,value_token='v'+'x'*addition))
        self.assertEqual(remaining,0)
        exact=replace(packet,facts=tuple(grown))
        self.assertEqual(independent_size(exact),1048576)
        self.assertEqual(len(v.canonical_bytes(exact)),1048576)
        index=next(i for i,fact in enumerate(grown) if len(fact.value_token)<512)
        larger=list(grown)
        larger[index]=replace(larger[index],value_token=larger[index].value_token+'x')
        overflow=replace(packet,facts=tuple(larger))
        self.assertEqual(independent_size(overflow),1048577)
        self.assertEqual(v.raw_business_size(overflow),1048577)
        with self.assertRaises(v.CoreContractError) as failure:
            v.canonical_bytes(overflow)
        self.assertEqual(failure.exception.code,'CORE_RESOURCE_LIMIT')
        self.assertEqual(len(overflow.facts),128)
        self.assertIs(overflow.facts[index],larger[index])


if __name__ == '__main__':
    unittest.main()
