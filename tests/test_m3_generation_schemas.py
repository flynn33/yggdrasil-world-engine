"""Offline schema controls from actual typed producers and independent mutations."""
from copy import deepcopy
from dataclasses import fields, replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from core.ash_pattern_engine import generation_values as g
from core.ash_pattern_engine import state_values as s
from core.ash_pattern_engine.topology import ReferenceTopologyGenerator
from core.ash_pattern_engine.axioms import ReferenceAxiomEvaluator
from core.ash_pattern_engine.state_model import StateModel
from tests.test_m3_topology import module_model, diagnosis, ash
from tests.test_m3_axioms import subject

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ID = "https://ywe.local/schemas/m3_topology_axiom_schema.json"


def authored_objects():
    """Fixed requests exercise actual owners; these are raw value fixtures only."""
    model = module_model()
    origin = diagnosis(model)
    policy = g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS)
    topo = ReferenceTopologyGenerator(model, policy)
    axioms = ReferenceAxiomEvaluator(model, policy)
    base = subject(origin)
    objects = [topo.generate(g.TopologyRequest("fixture:topology",origin,2,"authored")),
               topo.generate(g.TopologyRequest("fixture:depth",origin,-1)),
               axioms.evaluate(g.AxiomRequest("fixture:axioms",origin,base)),
               axioms.evaluate(g.AxiomRequest("fixture:fifth",origin,replace(base,relation_count=0))),
               axioms.evaluate(g.AxiomRequest("fixture:unit",origin,replace(base,raw_measure=g.AxiomMeasure(1,"ERASURE_TICK",100))))]
    for candidate in (1,"invalid"):
        child = diagnosis(model,candidate,"fixture:origin:"+str(candidate))
        objects.append(topo.generate(g.TopologyRequest("fixture:refusal:"+str(candidate),child,0)))
        objects.append(axioms.evaluate(g.AxiomRequest("fixture:axiom-refusal:"+str(candidate),child,base)))
    absent = module_model(unavailable=True)
    child = diagnosis(absent)
    objects.append(ReferenceTopologyGenerator(absent,policy).generate(g.TopologyRequest("fixture:profile",child,0)))
    objects.append(ReferenceAxiomEvaluator(absent,policy).evaluate(g.AxiomRequest("fixture:axiom-profile",child,base)))
    foreign = diagnosis(module_model(states=(0,1)))
    objects.append(topo.generate(g.TopologyRequest("fixture:foreign",foreign,0)))
    objects.append(axioms.evaluate(g.AxiomRequest("fixture:axiom-foreign",foreign,base)))
    collision = model.diagnose(ash(0),diagnostic_context=s.DiagnosticContext("fixture:collision-origin","fixture:collision-input",
                              "fixture:collision:diagnostic:topology","fixture:collision-class"))
    objects.append(topo.generate(g.TopologyRequest("fixture:collision",collision,0)))
    collision = model.diagnose(ash(0),diagnostic_context=s.DiagnosticContext("fixture:ax-collision-origin","fixture:ax-collision-input",
                              "fixture:ax-collision:diagnostic:A1","fixture:ax-collision-class"))
    objects.append(axioms.evaluate(g.AxiomRequest("fixture:ax-collision",collision,subject(collision))))
    with patch.object(StateModel,"validate_diagnosis",return_value=None):
        objects.append(topo.generate(g.TopologyRequest("fixture:validation",origin,0)))
        objects.append(axioms.evaluate(g.AxiomRequest("fixture:ax-validation",origin,base)))
    for changed in (replace(base,state=ash(1)),replace(base,provenance=replace(base.provenance,origin_diagnosis_reference="foreign:origin")),
                    replace(base,compressed_measure=g.AxiomMeasure(0,"ERASURE_TICK",100)),
                    replace(base,compressed_measure=g.AxiomMeasure(0,"STRUCTURE_TICK",99)),
                    replace(base,erasure_cost=g.AxiomMeasure(1,"STRUCTURE_TICK",1))):
        objects.append(axioms.evaluate(g.AxiomRequest("fixture:declared-refusal",origin,changed)))
    model._canonical_binding=s.CanonicalAshBinding(**dict(s.CANONICAL_BINDING_FIELDS))
    objects.append(topo.generate(g.TopologyRequest("fixture:old-source",origin,0)))
    objects.append(axioms.evaluate(g.AxiomRequest("fixture:old-ax-source",origin,base)))
    for _, source, pins in g.SOURCE_BASELINES:
        objects.append(g.TopologyAxiomSourceBinding(s.CanonicalAshBinding(**source),pins))
    return objects


def wire_values(objects):
    result = {}
    def visit(value):
        if type(value) in g.WIRE_TYPES:
            result.setdefault(type(value).__name__,value)
            for field in fields(type(value)):
                visit(getattr(value,field.name))
        elif type(value) is tuple:
            for child in value:
                visit(child)
    for value in objects:
        visit(value)
    return result


class GenerationSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def deny(uri):
            raise NoSuchResource(ref=uri)
        cls.registry=Registry(retrieve=deny)
        cls.documents={}
        for path in (ROOT/"data/schemas").glob("m3_*.json"):
            document=json.loads(path.read_text())
            cls.documents[document["$id"]]=document
            cls.registry=cls.registry.with_resource(document["$id"],Resource.from_contents(document))
        cls.document=cls.documents[SCHEMA_ID]
        cls.objects=authored_objects()
        cls.values=wire_values(cls.objects)

    def validator(self,name):
        return Draft202012Validator({"$ref":SCHEMA_ID+"#/$defs/"+name},registry=self.registry)

    def assertRejected(self,name,value,path=None,keyword=None):
        errors=list(self.validator(name).iter_errors(value))
        self.assertTrue(errors,name)
        def descend(error):
            yield error
            for child in error.context:
                yield from descend(child)
        all_errors=[nested for error in errors for nested in descend(error)]
        if path is not None or keyword is not None:
            self.assertTrue(any((path is None or list(e.absolute_path)==path) and
                                (keyword is None or e.validator==keyword) for e in all_errors),
                            [(list(e.absolute_path),e.validator) for e in all_errors])

    def test_metaschema_and_every_reference_is_resolved_offline(self):
        Draft202012Validator.check_schema(self.document)
        def walk(value):
            if type(value) is dict:
                if "$ref" in value:
                    self.registry.resolver(SCHEMA_ID).lookup(value["$ref"])
                for child in value.values():walk(child)
            elif type(value) is list:
                for child in value:walk(child)
        walk(self.document)

    def test_actual_all18_definitions_and_packet_refusal_branches(self):
        self.assertEqual(18,len(self.values))
        for name,value in self.values.items():
            with self.subTest(definition=name):
                self.validator(name).validate(value.to_record())
        for value in self.objects:
            self.validator(type(value).__name__).validate(value.to_record())

    def test_all_owned_definitions_are_closed_and_have_required_fields(self):
        for name,value in self.values.items():
            extra=value.to_record();extra["unregistered"]=True
            self.assertRejected(name,extra,[],"additionalProperties")
            missing=value.to_record();del missing[next(iter(missing))]
            self.assertRejected(name,missing,[],"required")

    def test_policy_source_and_module_metadata_pairing_is_closed(self):
        policy=self.values["TopologyAxiomPolicyBinding"].to_record();policy["policy_sha256"]="0"*64
        self.assertRejected("TopologyAxiomPolicyBinding",policy,["policy_sha256"],"const")
        source=self.values["TopologyAxiomSourceBinding"].to_record();source["contract_pins"][0][1]="0"*64
        self.assertRejected("TopologyAxiomSourceBinding",source,["contract_pins"],"const")
        record=self.values["GenerationDiagnosticRecord"].to_record();record["envelope"]["stage"]="RECOVERY"
        self.assertRejected("GenerationDiagnosticRecord",record,["envelope","stage"],"const")
        record=self.values["GenerationDiagnosticRecord"].to_record();record["envelope"]["rule_ids"]=["ASH-STATE-VALIDITY-001"]
        self.assertRejected("GenerationDiagnosticRecord",record,["envelope","rule_ids"],"const")
        record=self.values["GenerationDiagnosticRecord"].to_record();record["payload"]={"unregistered":True}
        self.assertRejected("GenerationDiagnosticRecord",record,["payload"],"additionalProperties")

    def test_numeric_and_exact_branch_metadata_boundaries(self):
        measure=self.values["AxiomMeasure"].to_record()
        for invalid,keyword in ((True,"type"),(-1,"minimum"),(2**63,"maximum"),("1","type")):
            changed=deepcopy(measure);changed["ticks"]=invalid
            self.assertRejected("AxiomMeasure",changed,["ticks"],keyword)
        node=self.values["TopologyNode"].to_record();node["depth"]=7
        self.assertRejected("TopologyNode",node,["depth"],"maximum")
        check=self.values["AxiomCheckDiagnostic"].to_record();check["overall_pass"]=True
        self.assertRejected("AxiomCheckDiagnostic",check,["overall_pass"],"type")
        packet=self.values["TopologyResult"].to_record();packet["packet_kind"]="topology_failure"
        self.assertRejected("TopologyResult",packet,["packet_kind"],"const")
        pending=self.values["PendingGenerationDiagnostic"].to_record();pending["missing_requirements"]=["CURRENT_SOURCE"]
        self.assertRejected("PendingGenerationDiagnostic",pending,["missing_requirements"],"const")

    def test_catalog_wrappers_are_closed_and_keep_body_validation_separate(self):
        catalog={"schema_ref":"data/schemas/m3_topology_axiom_schema.json",
                 "artifact_type":"ywe_topology_axiom_format_cases","artifact_version":"1.0.0",
                 "evidence_scope":"AUTHORED_WIRE_FORMAT_ONLY_NO_PERSISTENCE_OR_LIVE_EFFECT_CLAIM",
                 "cases":[{"case_id":"authored:measure","schema_definition":"AxiomMeasure",
                           "value":{"selected-body-is-checked-separately":True}}]}
        self.validator("TopologyAxiomCaseCatalog").validate(catalog)
        self.assertRejected("AxiomMeasure",catalog["cases"][0]["value"],[],"additionalProperties")
        for changed,path,keyword in ((dict(catalog,unregistered=True),[],"additionalProperties"),
                                     (dict(catalog,cases=[]),["cases"],"minItems"),
                                     (dict(catalog,cases=catalog["cases"]*257),["cases"],"maxItems")):
            self.assertRejected("TopologyAxiomCaseCatalog",changed,path,keyword)
        changed=deepcopy(catalog);changed["cases"][0]["schema_definition"]="ModuleEnvelope"
        self.assertRejected("TopologyAxiomCaseCatalog",changed,["cases",0,"schema_definition"],"enum")
        rejection=deepcopy(catalog)
        rejection["artifact_type"]="ywe_topology_axiom_rejection_cases"
        rejection["evidence_scope"]="AUTHORED_REJECTION_CONTROL_ONLY_NO_RUNTIME_EFFECT_CLAIM"
        rejection["cases"][0].update(expected_keyword="additionalProperties",expected_path=[])
        self.validator("TopologyAxiomRejectionCatalog").validate(rejection)
        changed=deepcopy(rejection);changed["cases"][0]["expected_keyword"]="invented"
        self.assertRejected("TopologyAxiomRejectionCatalog",changed,["cases",0,"expected_keyword"],"enum")
        changed=deepcopy(rejection);changed["cases"][0]["expected_path"]=[True]
        self.assertRejected("TopologyAxiomRejectionCatalog",changed,["cases",0,"expected_path",0],"type")


if __name__ == "__main__":
    unittest.main()
