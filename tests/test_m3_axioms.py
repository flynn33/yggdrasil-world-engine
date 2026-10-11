"""Independent all32 five-axiom vectors and declared-unit controls."""
from dataclasses import replace
from itertools import product
import unittest

from core.ash_pattern_engine import generation_values as g
from core.ash_pattern_engine.axioms import ReferenceAxiomEvaluator
from tests.test_m3_topology import module_model, diagnosis, ash


def subject(origin, truth=(True,)*5, *, self_flags=None):
    self_flags = (truth[4], truth[4]) if self_flags is None else self_flags
    return g.AxiomSubject("declared:subject", origin.parsed_state, int(truth[0]),
                           g.AxiomMeasure(1, "STRUCTURE_TICK", 100),
                           g.AxiomMeasure(0 if truth[1] else 1, "STRUCTURE_TICK", 100),
                           2 if truth[2] else 1, g.AxiomMeasure(int(truth[3]), "ERASURE_TICK", 10),
                           *self_flags, g.AxiomSubjectProvenance("DECLARED_REFERENCE_INPUT", "declared:source",
                           "test-method", "1", origin.emitted_diagnostics[0].diagnostic_reference))


class AxiomTests(unittest.TestCase):
    def setUp(self):
        self.model = module_model()
        self.origin = diagnosis(self.model)
        self.owner = ReferenceAxiomEvaluator(self.model, g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS))

    def evaluate(self, value):
        return self.owner.evaluate(g.AxiomRequest("axiom:test", self.origin, value))

    def test_all32_components_conjunction_order_explanations_and_cumulative_impact(self):
        for vector in product((False, True), repeat=5):
            with self.subTest(vector=vector):
                result = self.evaluate(subject(self.origin, vector))
                self.assertIs(type(result), g.AxiomEvaluationResult)
                records = result.produced_diagnostics
                self.assertEqual(5, len(records))
                self.assertEqual(vector, tuple(record.payload.passed for record in records))
                self.assertEqual(all(vector), result.axiom_diagnostic.overall_pass)
                parent = self.origin.emitted_diagnostics[0].diagnostic_reference
                warned = False
                for index, record in enumerate(records):
                    warned |= not vector[index]
                    self.assertEqual(f"A{index+1}", record.payload.axiom_id)
                    self.assertEqual(parent, record.envelope.parent_diagnostic_reference)
                    self.assertEqual("ash_state_000000000", record.envelope.subject_reference)
                    self.assertEqual("WARNING" if warned else "INFO", record.envelope.severity)
                    self.assertEqual("INFO" if vector[index] else "WARNING", record.payload.current_impact)
                    self.assertEqual("RESOLVED" if (all(vector) if index == 4 else vector[index]) else "BLOCKED", record.envelope.disposition)
                    self.assertIn("component_pass="+str(vector[index]).lower(), record.payload.explanation)
                    self.assertEqual(subject(self.origin, vector), record.payload.subject)
                    parent = record.diagnostic_reference
                self.assertEqual(("ASH-AXIOM-SELFREFERENCE-001", "ASH-AXIOM-CONJUNCTION-001"), records[-1].envelope.rule_ids)
                self.assertEqual(tuple(record.payload.explanation for record in records), result.axiom_diagnostic.notes)
                self.assertTrue(self.owner.validate_owned_result(result))

    def test_independent_self_flags_and_earlierfalse_fifthtrue(self):
        for first, second in product((False, True), repeat=2):
            result = self.evaluate(subject(self.origin, self_flags=(first, second)))
            self.assertEqual(first and second, result.produced_diagnostics[-1].payload.passed)
        for index in range(4):
            truth = [True]*5
            truth[index] = False
            result = self.evaluate(subject(self.origin, truth))
            self.assertTrue(result.produced_diagnostics[-1].payload.passed)
            self.assertFalse(result.produced_diagnostics[-1].payload.overall_pass)
            self.assertEqual("BLOCKED", result.produced_diagnostics[-1].envelope.disposition)

    def test_strict_numeric_thresholds_equality_extremes(self):
        base = subject(self.origin)
        for field, values, expected in (("relation_count", (0,1,g.INT63_MAX), (False,True,True)),
                                        ("scale_count", (0,1,2,g.INT63_MAX), (False,False,True,True))):
            index = 0 if field == "relation_count" else 2
            for number, passed in zip(values, expected):
                self.assertEqual(passed, self.evaluate(replace(base, **{field:number})).produced_diagnostics[index].payload.passed)
        for number in (0,1,g.INT63_MAX):
            self.assertEqual(number>0, self.evaluate(replace(base, erasure_cost=g.AxiomMeasure(number,"ERASURE_TICK",1))).produced_diagnostics[3].payload.passed)
        pairs = ((0,0),(0,1),(1,1),(1,0),(g.INT63_MAX-1,g.INT63_MAX),(g.INT63_MAX,g.INT63_MAX),(g.INT63_MAX,0))
        for compressed, raw in pairs:
            value = replace(base, raw_measure=g.AxiomMeasure(raw,"STRUCTURE_TICK",1), compressed_measure=g.AxiomMeasure(compressed,"STRUCTURE_TICK",1))
            self.assertEqual(compressed<raw, self.evaluate(value).produced_diagnostics[1].payload.passed)

    def test_units_scales_state_and_provenance_refuse_before_any_component(self):
        base = subject(self.origin)
        attempted = [(replace(base,state=ash(1)),"SUBJECT_STATE_MISMATCH","request.subject.state"),
                     (replace(base,provenance=replace(base.provenance,origin_diagnosis_reference="foreign:origin")),"SUBJECT_ORIGIN_MISMATCH","request.subject.provenance.origin_diagnosis_reference"),
                     (replace(base,raw_measure=g.AxiomMeasure(1,"ERASURE_TICK",100)),"SUBJECT_UNIT_MISMATCH","request.subject.raw_measure.unit"),
                     (replace(base,compressed_measure=g.AxiomMeasure(0,"ERASURE_TICK",100)),"SUBJECT_UNIT_MISMATCH","request.subject.compressed_measure.unit"),
                     (replace(base,compressed_measure=g.AxiomMeasure(0,"STRUCTURE_TICK",99)),"SUBJECT_UNIT_MISMATCH","request.subject.compressed_measure.ticks_per_unit"),
                     (replace(base,erasure_cost=g.AxiomMeasure(1,"STRUCTURE_TICK",1)),"SUBJECT_UNIT_MISMATCH","request.subject.erasure_cost.unit")]
        for value, code, field in attempted:
            result = self.evaluate(value)
            self.assertIs(type(result),g.AxiomEvaluationFailure)
            self.assertEqual((code,field),(result.failure_code,result.failed_field))
            self.assertEqual(1,len(result.produced_diagnostics))
            self.assertIs(type(result.produced_diagnostics[0].payload),g.AxiomInputDiagnostic)
            self.assertEqual(value,result.produced_diagnostics[0].payload.subject)
            self.assertIn(field,result.produced_diagnostics[0].payload.explanation)
            self.assertFalse(hasattr(result,"axiom_diagnostic"))

    def test_parsed_nonvalid_origin_is_allowed_with_actual_severity(self):
        origin = diagnosis(self.model, 1)
        result = self.owner.evaluate(g.AxiomRequest("nonvalid:test",origin,subject(origin)))
        self.assertIs(type(result),g.AxiomEvaluationResult)
        self.assertTrue(result.axiom_diagnostic.overall_pass)
        self.assertEqual("ERROR", result.produced_diagnostics[-1].envelope.severity)
        self.assertEqual("ash_state_000000001",result.produced_diagnostics[-1].envelope.subject_reference)


if __name__ == "__main__":
    unittest.main()
