"""Independent complete ternary frontier, lineage and admission controls."""
from copy import copy, deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch

from core.ash_pattern_engine import generation_values as g
from core.ash_pattern_engine import state_values as s
from core.ash_pattern_engine.state_model import StateModel, RecordingDiagnosticCapture
from core.ash_pattern_engine.topology import ReferenceTopologyGenerator


def ash(number):
    return s.AshState(tuple(int(char) for char in format(number, "09b")))


def module_model(states=(0,), *, unavailable=False):
    source = s.ProfileSourceBinding("tests:TA:declared-profile", "1"*64, "tests:TA:profile-evidence")
    binding = (s.UnavailableProfileBinding(s.UnavailableValidityProfileEvidence(
               "TA:profile", source, "PROFILE_DATA_UNAVAILABLE", "Explicit unavailable test profile."))
               if unavailable else s.AvailableProfileBinding(s.ValidityProfile(
               "TA:profile", source, tuple(ash(n) for n in states))))
    canonical = s.CanonicalAshBinding(**dict(s.MODULE_CANONICAL_BINDING_FIELDS))
    return StateModel(binding, canonical, RecordingDiagnosticCapture())


def diagnosis(model, candidate=0, reference="test:TA:origin"):
    return model.diagnose(ash(candidate) if type(candidate) is int else candidate,
                          diagnostic_context=s.DiagnosticContext(reference, reference+":input",
                                                                  reference+":detection", reference+":classification"))


class TopologyTests(unittest.TestCase):
    def setUp(self):
        self.model = module_model()
        self.origin = diagnosis(self.model)
        self.owner = ReferenceTopologyGenerator(self.model, g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS))

    def test_every_supported_depth_final_frontier_and_all_ancestor_strings(self):
        for depth, frontier, visited in zip(range(7), (1,3,9,27,81,243,729), (1,4,13,40,121,364,1093)):
            with self.subTest(depth=depth):
                result = self.owner.generate(g.TopologyRequest("topology:test", self.origin, depth, "seed"))
                self.assertIs(type(result), g.TopologyResult)
                self.assertEqual(frontier, len(result.nodes))
                self.assertEqual(visited, result.visited_node_count)
                for ordinal, node in enumerate(result.nodes):
                    digits, number = "", ordinal
                    for _ in range(depth):
                        digits = str(number % 3) + digits
                        number //= 3
                    expected = "topology:seed:r" + digits
                    self.assertEqual(expected, node.node_id)
                    self.assertEqual("r"+digits, node.path_token)
                    self.assertEqual(ordinal, node.ordinal)
                    self.assertEqual(depth, node.depth)
                    self.assertEqual(None if depth == 0 else expected[:-1], node.parent_id)
                    ancestors = [expected[:len("topology:seed:r")+level] for level in range(depth+1)]
                    self.assertEqual(["topology:seed:r"+digits[:level] for level in range(depth+1)], ancestors)
                record = result.produced_diagnostics[0]
                self.assertEqual("ash_state_000000000", record.envelope.subject_reference)
                self.assertEqual(self.origin.emitted_diagnostics[0].diagnostic_reference, record.envelope.parent_diagnostic_reference)
                self.assertEqual(self.origin.emitted_diagnostics[0].diagnostic_reference, record.envelope.chain_root_reference)
                self.assertEqual("PROCESSING", record.envelope.stage)
                self.assertTrue(self.owner.validate_owned_result(result))
                self.assertLessEqual(len(result.canonical_bytes()), 1_048_576)

    def test_negative_and_excessive_depth_retains_actual_refusal(self):
        for depth in (-2**63, -1, 7, 2**63-1):
            failure = self.owner.generate(g.TopologyRequest("depth:test", self.origin, depth))
            self.assertIs(type(failure), g.TopologyFailure)
            self.assertEqual("DEPTH_RANGE_EXCEEDED", failure.failure_code)
            self.assertEqual(depth, failure.produced_diagnostics[0].payload.depth)
            self.assertIsNone(failure.pending_diagnostic)
            self.assertEqual("BLOCKED", failure.produced_diagnostics[0].envelope.disposition)

    def test_non_normalized_unparsed_unavailable_and_priority(self):
        for candidate, unavailable, expected in ((1,False,"STATE_NOT_NORMALIZED"),
                                                  ("invalid",False,"ORIGIN_UNPARSED"),
                                                  (0,True,"PROFILE_UNAVAILABLE")):
            model = module_model(unavailable=unavailable)
            origin = diagnosis(model, candidate)
            owner = ReferenceTopologyGenerator(model, g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS))
            result = owner.generate(g.TopologyRequest("reject:test", origin, 7))
            self.assertEqual(expected, result.failure_code)
            self.assertEqual(1, len(result.produced_diagnostics))
            self.assertFalse(hasattr(result, "nodes"))

    def test_actual_malformed_input_observations_survive_reused_n1_boundary(self):
        from core.ash_pattern_engine.axioms import ReferenceAxiomEvaluator
        from tests.test_m3_axioms import subject
        cases = ("\ud800", "\udfff", b"\xff", "invalid", "", [0]*8)
        for index, candidate in enumerate(cases):
            origin = diagnosis(self.model, candidate, f"malformed:origin:{index}")
            self.assertIsNone(origin.parsed_state)
            result = self.owner.generate(g.TopologyRequest(f"malformed:topology:{index}",origin,0))
            self.assertEqual("ORIGIN_UNPARSED",result.failure_code)
            self.assertEqual(origin.input_evidence.preview,result.to_record()["request"]["origin_diagnosis"]["input_evidence"]["preview"])
            self.assertEqual(1,len(result.produced_diagnostics))
            axiom = ReferenceAxiomEvaluator(self.model,self.owner.configuration()[2]).evaluate(
                     g.AxiomRequest(f"malformed:axiom:{index}",origin,subject(self.origin)))
            self.assertEqual("ORIGIN_UNPARSED",axiom.failure_code)
            self.assertEqual(origin.input_evidence.preview,axiom.to_record()["request"]["origin_diagnosis"]["input_evidence"]["preview"])
        with self.assertRaises(g.GenerationContractError):
            g.AxiomSubjectProvenance("DECLARED_REFERENCE_INPUT","declared:source","\ud800","1","origin:dx")

    def test_foreign_current_profile_is_rejected_with_actual_validation_and_no_fake_ten(self):
        other = module_model(states=(0,1))
        result = self.owner.generate(g.TopologyRequest("foreign:test", diagnosis(other), 0))
        self.assertEqual("ORIGIN_REJECTED", result.failure_code)
        self.assertEqual("REJECTED", result.origin_validation.status)
        self.assertEqual((), result.produced_diagnostics)
        self.assertEqual(("VERIFIED_ORIGIN",), result.pending_diagnostic.missing_requirements)

    def test_reference_collision_and_unavailable_validation_are_pending_without_fake_provenance(self):
        origin = self.model.diagnose(ash(0), diagnostic_context=s.DiagnosticContext(
                                    "collision:origin", "collision:input", "collision:diagnostic:topology", "collision:classification"))
        failure = self.owner.generate(g.TopologyRequest("collision", origin, 0))
        self.assertEqual("REFERENCE_COLLISION", failure.failure_code)
        self.assertEqual("VERIFIED", failure.origin_validation.status)
        self.assertEqual((), failure.produced_diagnostics)
        self.assertEqual(("DISTINCT_REFERENCES",), failure.pending_diagnostic.missing_requirements)
        for outcome in (None, object()):
            with patch.object(StateModel, "validate_diagnosis", return_value=outcome):
                failure = self.owner.generate(g.TopologyRequest("unavailable:test", self.origin, 0))
            self.assertEqual("VALIDATION_UNAVAILABLE", failure.failure_code)
            self.assertIsNone(failure.origin_validation)
            self.assertEqual((), failure.produced_diagnostics)
        with patch.object(StateModel, "validate_diagnosis", side_effect=RuntimeError("secret collaborator body")):
            failure = self.owner.generate(g.TopologyRequest("exception:test", self.origin, 0))
        self.assertNotIn("secret collaborator body", str(failure.to_record()))

    def test_source_recheck_refuses_known_old_and_corrupt_mixed_configuration(self):
        old = s.CanonicalAshBinding(**dict(s.CANONICAL_BINDING_FIELDS))
        with self.assertRaises(g.GenerationContractError):
            ReferenceTopologyGenerator(StateModel(self.model.profile_binding, old, RecordingDiagnosticCapture()), self.owner.configuration()[2])
        self.model._canonical_binding = old
        failure = self.owner.generate(g.TopologyRequest("source:test", self.origin, 0))
        self.assertEqual("SOURCE_UNSUPPORTED", failure.failure_code)
        self.assertIsNone(failure.origin_validation)
        self.assertEqual((), failure.produced_diagnostics)
        self.assertEqual(old, failure.source_binding.canonical_binding)
        mixed = copy(old)
        object.__setattr__(mixed, "taxonomy_source_sha256", dict(s.MODULE_CANONICAL_BINDING_FIELDS)["taxonomy_source_sha256"])
        self.model._canonical_binding = mixed
        with self.assertRaises(s.StateContractError):
            self.owner.generate(g.TopologyRequest("mixed:test", self.origin, 0))

    def test_pure_class_dispatch_ignores_instance_io_hooks(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("unexpected effect or instance dispatch")
        for name in ("validate_diagnosis", "_orbit", "_diagnose", "_codec", "diagnose", "inspect_state"):
            setattr(self.model, name, forbidden)
        with patch("builtins.open", side_effect=forbidden), patch("time.time", side_effect=forbidden), patch("subprocess.run", side_effect=forbidden):
            result = self.owner.generate(g.TopologyRequest("pure:test", self.origin, 3))
            self.assertIs(type(result), g.TopologyResult)
            self.assertTrue(ReferenceTopologyGenerator.validate_owned_result(self.owner, result))

    def test_result_execution_seal_rejects_public_copies_foreign_and_corruption(self):
        result = self.owner.generate(g.TopologyRequest("seal:test", self.origin, 1))
        self.assertTrue(self.owner.validate_owned_result(result))
        for cloned in (copy(result), deepcopy(result), replace(result)):
            self.assertEqual(result.canonical_bytes(), cloned.canonical_bytes())
            self.assertFalse(self.owner.validate_owned_result(cloned))
        other = ReferenceTopologyGenerator(self.model, self.owner.configuration()[2])
        self.assertFalse(other.validate_owned_result(result))
        copied_metadata = copy(result)
        object.__setattr__(copied_metadata, "_self_identity", copied_metadata)
        self.assertFalse(self.owner.validate_owned_result(copied_metadata))
        corrupt = copy(result)
        object.__setattr__(corrupt, "_self_identity", corrupt)
        object.__setattr__(corrupt, "visited_node_count", 999)
        self.assertFalse(self.owner.validate_owned_result(corrupt))
        with self.assertRaises(g.GenerationContractError):
            corrupt.to_record()
        self.assertFalse(self.owner.validate_owned_result(object()))

    def test_maximal_frontier_complete_512_profile_raw_and_fresh_wire(self):
        model = module_model(states=range(512))
        origin = diagnosis(model)
        owner = ReferenceTopologyGenerator(model, g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS))
        result = owner.generate(g.TopologyRequest("r"*160, origin, 6, "s"*32))
        self.assertEqual(729, len(result.nodes))
        self.assertEqual(512, len(result.origin_validation.current_profile_binding.profile.recognized_valid_states))
        self.assertLessEqual(len(result.canonical_bytes()), g.RAW_BUSINESS_LIMIT)
        wire = result.to_record()
        wire["nodes"].clear()
        self.assertEqual(729, len(result.to_record()["nodes"]))


if __name__ == "__main__":
    unittest.main()
