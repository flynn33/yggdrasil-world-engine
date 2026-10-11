"""Independently authored closed generation value boundary controls."""
from copy import copy, deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from core.ash_pattern_engine import generation_values as g
from core.ash_pattern_engine import state_values as s


class GenerationValueTests(unittest.TestCase):
    def test_exact_policy_source_fields_and_no_dependency_file_at_runtime(self):
        policy = g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS)
        self.assertEqual(policy.canonical_bytes(), json.dumps(policy.to_record(), sort_keys=True,
                         separators=(",", ":"), ensure_ascii=True).encode("ascii"))
        for _, source, pins in g.SOURCE_BASELINES:
            binding = g.TopologyAxiomSourceBinding(s.CanonicalAshBinding(**source), pins)
            self.assertEqual([list(pair) for pair in pins], binding.to_record()["contract_pins"])
            mixed = list(pins)
            mixed[0] = (mixed[0][0], "0"*64)
            with self.assertRaises(g.GenerationContractError):
                g.TopologyAxiomSourceBinding(binding.canonical_binding, tuple(mixed))

    def test_all_frontier_nodes_rederive_parent_depth_ordinal_and_branch(self):
        for depth in range(7):
            for ordinal in range(3**depth):
                digits = ""
                number = ordinal
                for _ in range(depth):
                    digits = str(number % 3) + digits
                    number //= 3
                path = "r" + digits
                parent = None if depth == 0 else "topology:seed:" + path[:-1]
                branch = "root" if depth == 0 else ("continuation", "positive", "negative")[int(digits[-1])]
                node = g.TopologyNode("topology:seed:" + path, parent, depth, ordinal, branch, path)
                self.assertEqual(parent, node.to_record()["parent_id"])
                changed = copy(node)
                object.__setattr__(changed, "ordinal", ordinal + 1)
                with self.assertRaises(g.GenerationContractError):
                    changed.to_record()

    def test_numeric_domains_are_exact_without_coercion_or_hooks(self):
        calls = []
        class Hostile:
            def __eq__(self, other):
                calls.append("eq")
                raise AssertionError("caller equality")
            def __str__(self):
                calls.append("str")
                raise AssertionError("caller conversion")
        for invalid in (True, -1, g.INT63_MAX+1, 1.0, float("nan"), float("inf"), "1", Hostile()):
            with self.subTest(value_type=type(invalid).__name__):
                with self.assertRaises(g.GenerationContractError):
                    g.AxiomMeasure(invalid, "STRUCTURE_TICK", 1)
        with self.assertRaises(g.GenerationContractError):
            g.TopologyAxiomPolicyBinding(Hostile(), "1.0.0", g.POLICY_FIELDS[2])
        self.assertEqual([], calls)

    def test_corrupt_cycles_subclasses_and_fresh_records(self):
        measure = g.AxiomMeasure(1, "STRUCTURE_TICK", 1)
        first = measure.to_record()
        first["ticks"] = 99
        self.assertEqual(1, measure.to_record()["ticks"])
        class Child(g.AxiomMeasure):
            pass
        with self.assertRaises(g.GenerationContractError):
            g.revalidate_value(Child(1, "STRUCTURE_TICK", 1))
        corrupt = copy(measure)
        object.__setattr__(corrupt, "ticks", corrupt)
        with self.assertRaises(g.GenerationContractError):
            corrupt.to_record()
        with self.assertRaises(g.GenerationContractError):
            g.revalidate_value({"ticks": 1})

    def test_bounded_measurement_and_serializer_refuse_without_truncation(self):
        value = g.AxiomMeasure(123, "STRUCTURE_TICK", 100)
        size = len(value.canonical_bytes())
        self.assertEqual(size, g.raw_business_size(value))
        self.assertEqual(size, g.raw_business_size(value, size))
        self.assertEqual(size, g.raw_business_size(value, size-1))
        self.assertEqual(2, g.raw_business_size(value, 1))
        with patch.object(g, "RAW_BUSINESS_LIMIT", 1):
            for method in (value.to_record, value.canonical_bytes):
                with self.assertRaises(g.GenerationContractError) as caught:
                    method()
                self.assertEqual("GENERATION_RAW_BYTE_LIMIT", caught.exception.code)

    def test_actual_fields_match_the_adopted_inventory(self):
        from dataclasses import fields
        inventory = json.loads((Path(__file__).parents[1]/"docs/design-planning/m3/topology-axiom/BUSINESS_API_INVENTORY.json").read_text())
        wire = [row for row in inventory["types"] if row["representation"] == "WIRE_VALUE"]
        self.assertEqual(18, len(wire))
        for row in wire:
            self.assertEqual([field["name"] for field in row["constructor_fields"]],
                             [field.name for field in fields(getattr(g, row["name"]))])

    def test_hostile_metaclass_has_no_hooks_at_request_child_and_wire_boundaries(self):
        from core.ash_pattern_engine.topology import ReferenceTopologyGenerator
        from core.ash_pattern_engine.axioms import ReferenceAxiomEvaluator
        from tests.test_m3_topology import module_model, diagnosis
        from tests.test_m3_axioms import subject

        calls = []
        class HostileMeta(type):
            def __eq__(cls, other):
                calls.append("class_eq")
                raise AssertionError("caller metaclass equality")
            def __hash__(cls):
                calls.append("class_hash")
                raise AssertionError("caller metaclass hash")
            def __str__(cls):
                calls.append("class_str")
                raise AssertionError("caller metaclass conversion")
        class Hostile(metaclass=HostileMeta):
            def __eq__(self, other):
                calls.append("value_eq")
                raise AssertionError("caller equality")
            def __hash__(self):
                calls.append("value_hash")
                raise AssertionError("caller hash")
            def __str__(self):
                calls.append("value_str")
                raise AssertionError("caller conversion")

        model = module_model()
        origin = diagnosis(model)
        policy = g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS)
        topology = ReferenceTopologyGenerator(model, policy)
        axioms = ReferenceAxiomEvaluator(model, policy)
        hostile = Hostile()
        for action in (lambda: topology.generate(hostile), lambda: axioms.evaluate(hostile),
                       lambda: g.canonical_bytes(hostile), lambda: g.revalidate_value(hostile),
                       lambda: g._record(hostile)):
            with self.assertRaises(g.GenerationContractError):
                action()
        for request, owner, method, field in (
                (g.TopologyRequest("hostile:topology", origin, 0), topology, "generate", "origin_diagnosis"),
                (g.AxiomRequest("hostile:axiom", origin, subject(origin)), axioms, "evaluate", "subject")):
            corrupt = copy(request)
            object.__setattr__(corrupt, field, hostile)
            for action in (lambda: getattr(owner, method)(corrupt), lambda: g.canonical_bytes(corrupt)):
                with self.assertRaises(g.GenerationContractError):
                    action()
        self.assertFalse(topology.validate_owned_result(hostile))
        self.assertFalse(axioms.validate_owned_result(hostile))
        self.assertEqual([], calls)

    def test_producer_original_identity_and_inputs_reject_copies_before_real_registration_io(self):
        from tests.test_m3_module_diagnostics import assembly, result_for

        diagnostics, model, owners, origin, store, clock = assembly()
        for index, owner in enumerate(owners[2:]):
            result = result_for(owner, origin, f"owner:original:{index}", depth=0)
            self.assertTrue(type(owner).validate_owned_result(owner, result))
            copies = (copy(owner), deepcopy(owner, {id(model): model}))
            for cloned in copies:
                for reset in (False, True):
                    if reset:
                        object.__setattr__(cloned, "_self_identity", cloned)
                    calls_before = len(store.calls), clock.value, dict(diagnostics._aliases)
                    with self.assertRaises(g.GenerationContractError) as caught:
                        result_for(cloned, origin, f"owner:copy:{index}", depth=0)
                    self.assertEqual("GENERATION_COMPOSITION_INVALID", caught.exception.code)
                    self.assertFalse(type(cloned).validate_owned_result(cloned, result))
                    registration = diagnostics.register_module_producer(cloned)
                    self.assertEqual("REJECTED", registration.status)
                    self.assertEqual(calls_before, (len(store.calls), clock.value, dict(diagnostics._aliases)))
            saved_model, saved_policy = owner._model, owner._policy
            for field, replacement in (("_model", copy(model)),
                                       ("_policy", g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS))):
                object.__setattr__(owner, field, replacement)
                calls_before = len(store.calls), clock.value, dict(diagnostics._aliases)
                with self.assertRaises(g.GenerationContractError):
                    result_for(owner, origin, f"owner:mutated:{index}", depth=0)
                self.assertFalse(type(owner).validate_owned_result(owner, result))
                self.assertEqual("REJECTED", diagnostics.register_module_producer(owner).status)
                self.assertEqual(calls_before, (len(store.calls), clock.value, dict(diagnostics._aliases)))
                object.__setattr__(owner, "_model", saved_model)
                object.__setattr__(owner, "_policy", saved_policy)
            self.assertTrue(type(owner).validate_owned_result(owner, result))
            self.assertEqual("REGISTERED", diagnostics.register_module_producer(owner).status)


if __name__ == "__main__":
    unittest.main()
