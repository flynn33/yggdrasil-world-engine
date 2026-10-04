"""Verify reviewed YAML document structure without certifying domain execution."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource, Unresolvable

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "data/schemas"
CASE_BUNDLE = ROOT / "examples/contract_foundation/yaml_policy_document_cases.example.json"
BINDINGS_PATH = ROOT / "data/validation/fixture_catalog.json"
SCHEMA_FILES = (
    "ywe_core_policy_document_schema.json",
    "ywe_domain_policy_document_schema.json",
    "ywe_module_policy_document_schema.json",
)
SOURCE_TARGETS = {
    "core/narrative_engine/ash_runtime_generation_flow.yaml": ("core", "AshRuntimeGenerationFlowDocument"),
    "core/narrative_engine/character_creation_progression_rules.yaml": ("core", "CharacterCreationProgressionDocument"),
    "core/narrative_engine/lore_archive_generation_rules.yaml": ("core", "LoreArchiveGenerationDocument"),
    "core/narrative_engine/npc_synthesis_rules.yaml": ("core", "NpcSynthesisRulesDocument"),
    "core/narrative_engine/player_runtime_state_rules.yaml": ("core", "PlayerRuntimeStateRulesDocument"),
    "core/narrative_engine/quest_npc_lore_generation_rules.yaml": ("core", "QuestNpcLoreGenerationDocument"),
    "core/narrative_engine/worldstate_delta_rules.yaml": ("core", "WorldstateDeltaRulesDocument"),
    "core/narrative_engine/worldstate_location_mutation_rules.yaml": ("core", "WorldstateLocationMutationRulesDocument"),
    "data/ash_state/realm_bit_mapping.yaml": ("domain", "RealmBitMappingDocument"),
    "data/faction_topology/faction_topology_state_schema.yaml": ("domain", "FactionTopologyDescriptorDocument"),
    "data/pattern_archetypes/ash_codeword_projection.yaml": ("domain", "AshCodewordProjectionDocument"),
    "data/pattern_archetypes/compatibility_matrix.yaml": ("domain", "CompatibilityMatrixDocument"),
    "data/pattern_archetypes/generation_rules.yaml": ("domain", "PatternGenerationRulesDocument"),
    "data/perception/perception_overlay_rules.yaml": ("domain", "PerceptionOverlayRulesDocument"),
    "data/realm/realm_boundary_profiles.yaml": ("domain", "RealmBoundaryProfilesDocument"),
    "data/realm/realm_mechanics_rules.yaml": ("domain", "RealmMechanicsRulesDocument"),
    "data/realm/realm_transition_examples.yaml": ("domain", "RealmTransitionExampleCollectionDocument"),
    "modules/artifact_engine/artifact_system_rules.yaml": ("module", "ArtifactSystemRulesDocument"),
    "modules/creature_engine/creature_system_rules.yaml": ("module", "CreatureSystemRulesDocument"),
    "modules/quest_engine/quest_chain_templates.yaml": ("module", "QuestChainTemplatesDocument"),
}


def deny_retrieval(uri):
    raise NoSuchResource(ref=uri)


def schema_ref(family, definition):
    return f"https://ywe.local/schemas/ywe_{family}_policy_document_schema.json#/$defs/{definition}"


def replace_at(document, parts, value):
    parent = document
    for part in parts[:-1]:
        parent = parent[part]
    if parts:
        parent[parts[-1]] = value
        return document
    return value


class YamlPolicyDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_fixture_catalog import error_signature, json_pointer, leaf_errors, load_instance

        cls.error_signature = staticmethod(error_signature)
        cls.json_pointer = staticmethod(json_pointer)
        cls.leaf_errors = staticmethod(leaf_errors)
        cls.load_instance = staticmethod(load_instance)
        cls.schemas = {
            filename: json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
            for filename in SCHEMA_FILES
        }
        cls.registry = Registry(retrieve=deny_retrieval).with_resources(
            (schema["$id"], Resource.from_contents(schema)) for schema in cls.schemas.values()
        )
        document = json.loads(BINDINGS_PATH.read_text(encoding="utf-8"))
        catalog = document["fixtures"] if isinstance(document, dict) else document
        cls.bindings = [b for b in catalog if b["fixture_id"].startswith("m2.yaml_format.")]
        cls.cases = json.loads(CASE_BUNDLE.read_text(encoding="utf-8"))

    def errors(self, value, reference):
        return [
            self.error_signature(leaf)
            for error in Draft202012Validator({"$ref": reference}, registry=self.registry).iter_errors(value)
            for leaf in self.leaf_errors(error)
        ]

    def target(self, family, definition):
        return self.schemas[f"ywe_{family}_policy_document_schema.json"]["$defs"][definition]

    def observed_nodes(self, schema, value, parts=()):
        if "oneOf" in schema:
            valid = [
                child for child in schema["oneOf"]
                if Draft202012Validator(child, registry=self.registry).is_valid(value)
            ]
            self.assertEqual(len(valid), 1, parts)
            yield from self.observed_nodes(valid[0], value, parts)
            return
        yield schema, value, parts
        if isinstance(value, dict):
            for name, child in value.items():
                child_schema = schema.get("properties", {}).get(name)
                if child_schema is None:
                    child_schema = schema.get("additionalProperties")
                self.assertIsInstance(child_schema, dict, f"Untyped existing field {parts + (name,)}")
                yield from self.observed_nodes(child_schema, child, parts + (name,))
        elif isinstance(value, list) and value and "const" not in schema:
            for index, child in enumerate(value):
                yield from self.observed_nodes(schema["items"], child, parts + (index,))

    def sources(self):
        for path, (family, definition) in SOURCE_TARGETS.items():
            yield path, family, definition, self.load_instance(ROOT / path), self.target(family, definition)

    def test_schema_resources_are_valid_and_requirement_owned(self):
        for schema in self.schemas.values():
            Draft202012Validator.check_schema(schema)
            self.assertEqual(schema["x-ywe-requirement-id"], "YWE-REQ-0032")

    def test_all_twenty_original_documents_accept_exact_owned_definition(self):
        self.assertEqual(len(SOURCE_TARGETS), 20)
        for path, family, definition, value, _ in self.sources():
            with self.subTest(path=path):
                self.assertEqual(self.errors(value, schema_ref(family, definition)), [])

    def test_each_resource_union_accepts_its_whole_document_family(self):
        for path, family, _, value, _ in self.sources():
            with self.subTest(path=path):
                self.assertEqual(self.errors(value, f"https://ywe.local/schemas/ywe_{family}_policy_document_schema.json"), [])

    def test_resource_unions_reject_sources_from_other_families(self):
        for path, family, _, value, _ in self.sources():
            for other in ("core", "domain", "module"):
                if other != family:
                    with self.subTest(path=path, family=other):
                        self.assertTrue(self.errors(value, f"https://ywe.local/schemas/ywe_{other}_policy_document_schema.json"))

    def test_every_existing_nested_field_has_explicit_structure(self):
        for path, _, _, value, schema in self.sources():
            with self.subTest(path=path):
                self.assertGreater(len(list(self.observed_nodes(schema, value))), 1)

    def test_each_required_root_section_is_exercised_by_removal(self):
        for path, family, definition, value, schema in self.sources():
            for name in schema["required"]:
                with self.subTest(path=path, section=name):
                    changed = deepcopy(value)
                    changed.pop(name)
                    errors = self.errors(changed, schema_ref(family, definition))
                    required = [e for e in errors if e["error_id"] == "JSON_SCHEMA_REQUIRED"]
                    self.assertEqual(required, [{
                        "error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "", "schema_pointer": "/required",
                        "missing_properties": [name],
                    }])

    def test_known_nested_types_reject_wrong_representation_at_full_root(self):
        wrong = {"string": None, "boolean": 0, "integer": True, "number": "0", "array": {}, "object": []}
        for path, family, definition, value, schema in self.sources():
            visited = set()
            for node, _, parts in self.observed_nodes(schema, value):
                kind = node.get("type")
                if kind not in wrong or not parts:
                    continue
                # Array records repeat the same structural positions. One per
                # schema node covers its shape while preserving optional variants.
                if id(node) in visited:
                    continue
                visited.add(id(node))
                with self.subTest(path=path, pointer=parts):
                    changed = replace_at(deepcopy(value), parts, wrong[kind])
                    self.assertTrue(
                        any(e["error_id"] == "JSON_SCHEMA_TYPE" for e in self.errors(changed, schema_ref(family, definition)))
                    )

    def test_unspecified_string_and_array_bounds_stay_open(self):
        for path, _, _, value, schema in self.sources():
            for node, _, parts in self.observed_nodes(schema, value):
                kind = node.get("type")
                if kind not in {"string", "array"} or any(k in node for k in ("const", "enum", "pattern", "minLength", "minItems")):
                    continue
                with self.subTest(path=path, pointer=parts):
                    self.assertTrue(Draft202012Validator(node, registry=self.registry).is_valid("" if kind == "string" else []))

    def test_named_objects_remain_open_to_additive_fields(self):
        for path, _, _, value, schema in self.sources():
            visited = set()
            for node, instance, parts in self.observed_nodes(schema, value):
                if node.get("type") != "object" or node.get("additionalProperties") is not True or id(node) in visited:
                    continue
                visited.add(id(node))
                changed = deepcopy(instance)
                changed["draft_extension_field"] = {"values": [None, True, 1, ""]}
                with self.subTest(path=path, pointer=parts):
                    self.assertTrue(Draft202012Validator(node, registry=self.registry).is_valid(changed))

    def test_fixed_values_and_descriptor_tokens_match_exact_source_pointer(self):
        count = 0
        for _, _, _, value, schema in self.sources():
            for node, instance, _ in self.observed_nodes(schema, value):
                if "const" not in node:
                    continue
                count += 1
                owner = node["x-ywe-source-ref"]
                source = self.json_pointer(self.load_instance(ROOT / owner["path"]), owner["pointer"])
                self.assertIs(type(source), type(node["const"]))
                self.assertEqual(source, node["const"])
                self.assertIs(type(instance), type(source))
        self.assertGreater(count, 300)

    def test_each_fixed_value_rejects_same_type_substitution_at_full_root(self):
        for path, family, definition, value, schema in self.sources():
            for node, instance, parts in self.observed_nodes(schema, value):
                if "const" not in node:
                    continue
                altered = not instance if type(instance) is bool else instance + 1 if type(instance) in {int, float} else instance + "_substituted" if type(instance) is str else instance + ["_substituted"]
                with self.subTest(path=path, pointer=parts):
                    changed = replace_at(deepcopy(value), parts, altered)
                    self.assertTrue(any(e["error_id"] == "JSON_SCHEMA_CONST" for e in self.errors(changed, schema_ref(family, definition))))

    def test_all_compact_case_bindings_match_exact_witnesses_and_roles(self):
        bindings = [b for b in self.bindings if b["fixture_id"].startswith("m2.yaml_format.case.")]
        self.assertEqual(len(bindings), 54)
        self.assertEqual(sum(b["expected_result"] == "reject" for b in bindings), 30)
        self.assertEqual(self.cases["artifact_type"], "yaml_policy_document_cases")
        self.assertEqual(self.cases["artifact_version"], "1.0.0")
        expected_units = {"/" + group + "/" + name for group in ("positive", "boundary", "reject") for name in self.cases[group]}
        self.assertEqual({b["instance_pointer"] for b in bindings}, expected_units)
        for binding in bindings:
            with self.subTest(fixture=binding["fixture_id"]):
                value = self.json_pointer(self.cases, binding["instance_pointer"])
                errors = self.errors(value, binding["schema_id"])
                self.assertEqual(
                    {json.dumps(e, sort_keys=True) for e in errors},
                    {json.dumps(e, sort_keys=True) for e in binding["expected_errors"]},
                )
                group = binding["instance_pointer"].split("/")[1]
                self.assertEqual(binding["expected_result"], "reject" if group == "reject" else "accept")
                self.assertEqual(binding["category"], "positive" if group == "positive" else group)

    def test_source_bindings_cover_all_twenty_exact_roots(self):
        bindings = [b for b in self.bindings if b["instance_pointer"] == "" and b["path"] in SOURCE_TARGETS]
        self.assertEqual(len(bindings), 20)
        self.assertEqual({b["path"] for b in bindings}, set(SOURCE_TARGETS))
        for binding in bindings:
            family, definition = SOURCE_TARGETS[binding["path"]]
            self.assertEqual(binding["instance_pointer"], "")
            self.assertEqual(binding["schema_id"], schema_ref(family, definition))
            self.assertEqual(binding["expected_result"], "accept")
            self.assertEqual(binding["expected_errors"], [])

    def test_literal_descriptor_boolean_does_not_accept_runtime_boolean(self):
        reference = schema_ref("domain", "PerceptionOverlayRulesDocument") + "/properties/core_schema/properties/PerceptionOverlayRecord/properties/truth_boundary_profile/properties/cosmology_preserved"
        self.assertEqual(self.errors("boolean", reference), [])
        self.assertEqual({e["error_id"] for e in self.errors(True, reference)}, {"JSON_SCHEMA_TYPE", "JSON_SCHEMA_CONST"})

    def test_descriptor_string_array_is_not_a_runtime_list(self):
        reference = schema_ref("module", "ArtifactSystemRulesDocument") + "/properties/artifact_schema/properties/ArtifactManifest/properties/symbolic_signature"
        self.assertEqual(self.errors(["string"], reference), [])
        self.assertEqual({e["error_id"] for e in self.errors(["sample"], reference)}, {"JSON_SCHEMA_CONST"})
        self.assertEqual({e["error_id"] for e in self.errors([], reference)}, {"JSON_SCHEMA_CONST"})

    def test_location_pipeline_accepts_both_observed_representations(self):
        reference = schema_ref("core", "WorldstateLocationMutationRulesDocument") + "/properties/mutation_pipeline/items"
        for incoming in ("sample", ["sample"], []):
            for outgoing in ("sample", ["sample"], []):
                self.assertEqual(self.errors({"step": "", "input": incoming, "output": outgoing}, reference), [])
        self.assertEqual(len(self.errors({"step": "", "input": 1, "output": ""}, reference)), 2)

    def test_policy_flags_reject_boolean_as_integer(self):
        reference = schema_ref("core", "NpcSynthesisRulesDocument") + "/properties/synthesis_laws/properties/host_adapter_may_author_npc_truth"
        self.assertEqual(self.errors(False, reference), [])
        self.assertIn("JSON_SCHEMA_TYPE", {e["error_id"] for e in self.errors(0, reference)})

    def test_fixed_codeword_shape_rejects_trailing_newline(self):
        reference = schema_ref("domain", "AshCodewordProjectionDocument") + "/properties/codeword_projection_records/items/properties/codeword"
        self.assertEqual(self.errors("000000000", reference), [])
        self.assertEqual(self.errors("000000000\n", reference), [{
            "error_id": "JSON_SCHEMA_MAXLENGTH", "instance_pointer": "", "schema_pointer": "/maxLength",
        }])

    def test_realm_description_format_acceptance_does_not_claim_intended_rejection(self):
        reference = schema_ref("domain", "RealmTransitionUnlawfulDescription")
        source = self.load_instance(ROOT / "data/realm/realm_transition_examples.yaml")
        self.assertEqual(len(source["unlawful_examples"]), 2)
        for description in source["unlawful_examples"]:
            self.assertEqual(self.errors(description, reference), [])

    def test_realm_mapping_semantics_remain_owned_by_m1_checker(self):
        from check_m1_canon_governance import check_realm_mapping

        source = deepcopy(self.load_instance(ROOT / "data/ash_state/realm_bit_mapping.yaml"))
        source["realm_state_anchors"][0]["coordinate_index"] = -1
        self.assertEqual(self.errors(source, schema_ref("domain", "RealmBitMappingDocument")), [])
        errors = []
        check_realm_mapping(source, errors)
        self.assertTrue(errors)

    def test_unknown_schema_reference_is_rejected_offline(self):
        with self.assertRaises(Unresolvable):
            self.errors({}, "https://missing.invalid/not-registered.json")


if __name__ == "__main__":
    unittest.main()
