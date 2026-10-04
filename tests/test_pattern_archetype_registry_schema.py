from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_fixture_catalog as fixture_check


class PatternArchetypeRegistrySchemaTests(unittest.TestCase):
    SCHEMA_PATH = "data/schemas/pattern_archetype_registry_schema.json"
    SOURCE_PATH = "data/pattern_archetypes/ash_pattern_registry_schema.yaml"
    BUNDLE_PATH = "examples/contract_foundation/pattern_archetype_registry_cases.example.yaml"
    FAMILY_PATHS = {
        "character": "data/pattern_archetypes/character_archetypes.yaml",
        "quest": "data/quest_archetypes/quest_archetypes.yaml",
        "region": "data/pattern_archetypes/region_archetypes.yaml",
        "faction": "data/pattern_archetypes/faction_archetypes.yaml",
        "transformation": "data/pattern_archetypes/transformation_archetypes.yaml",
        "event": "data/pattern_archetypes/event_archetypes.yaml",
        "cluster": "data/pattern_archetypes/pattern_clusters.yaml",
    }

    @classmethod
    def setUpClass(cls):
        cls.schema = fixture_check.load_json(ROOT / cls.SCHEMA_PATH)
        cls.source = fixture_check.load_instance(ROOT / cls.SOURCE_PATH)
        cls.bundle = fixture_check.load_instance(ROOT / cls.BUNDLE_PATH)
        cls.registry = Registry().with_resource(
            cls.schema["$id"], Resource.from_contents(cls.schema)
        )

    def signatures(self, instance, definition="ArchetypeRecord"):
        target = fixture_check.resolve_schema_target(
            self.registry, self.schema["$id"] + "#/$defs/" + definition
        )
        validator = Draft202012Validator(
            target.contents, registry=self.registry, _resolver=target.resolver
        )
        return sorted(
            (
                fixture_check.error_signature(leaf)
                for error in validator.iter_errors(instance)
                for leaf in fixture_check.leaf_errors(error)
            ),
            key=fixture_check.signature_key,
        )

    def assert_exact_error(self, instance, error_id, instance_pointer, schema_pointer,
                           definition="ArchetypeRecord", **details):
        self.assertEqual([{
            "error_id": error_id,
            "instance_pointer": instance_pointer,
            "schema_pointer": schema_pointer,
            **details,
        }], self.signatures(instance, definition))

    def archetype(self):
        return copy.deepcopy(self.bundle["positive"]["archetype"])

    def cluster(self):
        return copy.deepcopy(self.bundle["positive"]["cluster"])

    def definition_for_case(self, name):
        if "_family_document" in name:
            return "ClusterFamilyDocument" if name.startswith("cluster") else "CharacterFamilyDocument"
        return "Registry" if name.startswith("registry") else (
            "ClusterRecord" if name.startswith("cluster") else "ArchetypeRecord"
        )

    def test_schema_is_valid_under_the_repository_dialect(self):
        self.assertEqual(fixture_check.DIALECT, self.schema["$schema"])
        Draft202012Validator.check_schema(self.schema)

    def test_required_fields_and_property_surfaces_match_the_declared_source(self):
        source = self.source["schema"]["ArchetypeRecord"]
        base = self.schema["$defs"]["ArchetypeRecord"]
        self.assertEqual(source["required"], base["required"])
        self.assertEqual(set(source["properties"]), set(base["properties"]))
        cluster = self.source["schema"]["ClusterRecord"]
        extension = self.schema["$defs"]["ClusterRecord"]["allOf"][1]
        self.assertEqual(cluster["additional_required"], extension["required"])
        self.assertEqual(set(cluster["properties"]), set(extension["properties"]))
        for field in ("wolf_bias", "downstream_affinities"):
            self.assertEqual(
                source["properties"][field]["required"],
                base["properties"][field]["required"],
            )

    def test_all_declared_enum_references_use_the_source_values(self):
        properties = self.schema["$defs"]["ArchetypeRecord"]["properties"]
        for field, enum_name, item_enum in (
            ("family", "family", False),
            ("status", "record_status", False),
            ("realm_bias", "realm", True),
            ("player_phase_bias", "player_phase", True),
        ):
            with self.subTest(field=field):
                target = properties[field]["items"] if item_enum else properties[field]
                self.assertEqual(self.source["enums"][enum_name], target["enum"])
        self.assertEqual(
            self.source["enums"]["cluster_stability"],
            self.schema["$defs"]["ClusterRecord"]["allOf"][1]
            ["properties"]["stability_mode"]["enum"],
        )

    def test_registry_family_routes_match_the_declared_source(self):
        families = self.schema["$defs"]["Registry"]["properties"]["families"]
        self.assertEqual(set(self.source["registry_shape"]["families"]),
                         set(families["properties"]))
        for family, descriptor in self.source["registry_shape"]["families"].items():
            with self.subTest(family=family):
                self.assertEqual(
                    {"type": "array", "items": {"$ref": "#/$defs/" + descriptor["items_ref"]}},
                    families["properties"][family],
                )

    def test_all_47_original_records_and_two_source_seed_records_validate(self):
        count = 0
        for family, path in self.FAMILY_PATHS.items():
            definition = "ClusterRecord" if family == "cluster" else "ArchetypeRecord"
            document = fixture_check.load_instance(ROOT / path)
            for record in document["records"]:
                with self.subTest(path=path, record=record["id"]):
                    self.assertEqual([], self.signatures(record, definition))
                count += 1
        for record in self.source["seed_registry"]["families"]["character"]:
            with self.subTest(seed=record["id"]):
                self.assertEqual([], self.signatures(record))
            count += 1
        self.assertEqual(49, count)

    def test_source_seed_registry_validates_at_its_exact_selected_node(self):
        self.assertEqual([], self.signatures(self.source["seed_registry"], "Registry"))

    def test_all_seven_original_family_documents_validate_at_the_root(self):
        for family, path in self.FAMILY_PATHS.items():
            with self.subTest(path=path):
                document = fixture_check.load_instance(ROOT / path)
                self.assertEqual([], self.signatures(document, family.title() + "FamilyDocument"))

    def test_family_document_required_root_fields_and_authority_members_are_enforced(self):
        template = self.bundle["positive"]["character_family_document"]
        for field in ("registry_version", "status", "authority", "family", "records"):
            with self.subTest(field=field):
                document = copy.deepcopy(template)
                del document[field]
                self.assert_exact_error(
                    document, "JSON_SCHEMA_REQUIRED", "", "/allOf/0/required",
                    definition="CharacterFamilyDocument", missing_properties=[field],
                )
        for field in ("prose_spec", "schema_ref", "downstream_contract"):
            with self.subTest(authority_member=field):
                document = copy.deepcopy(template)
                del document["authority"][field]
                self.assert_exact_error(
                    document, "JSON_SCHEMA_REQUIRED", "/authority",
                    "/allOf/0/properties/authority/required",
                    definition="CharacterFamilyDocument", missing_properties=[field],
                )

    def test_family_document_routes_record_family_and_identifier_prefix(self):
        for family, path in self.FAMILY_PATHS.items():
            definition = family.title() + "FamilyDocument"
            template = fixture_check.load_instance(ROOT / path)
            for member, value, keyword in (
                ("family", "character" if family != "character" else "quest", "CONST"),
                ("id", "wrong_prefix", "PATTERN"),
            ):
                with self.subTest(family=family, member=member):
                    document = copy.deepcopy(template)
                    document["records"][0][member] = value
                    self.assert_exact_error(
                        document, "JSON_SCHEMA_" + keyword, "/records/0/" + member,
                        "/allOf/1/properties/records/items/allOf/1/properties/"
                        + member + "/" + keyword.lower(), definition=definition,
                    )

    def test_family_document_records_are_nonempty_arrays(self):
        template = self.bundle["positive"]["character_family_document"]
        for value, keyword in (([], "MINITEMS"), ("fixture", "TYPE")):
            with self.subTest(records=value):
                document = copy.deepcopy(template)
                document["records"] = value
                self.assert_exact_error(
                    document, "JSON_SCHEMA_" + keyword, "/records",
                    "/allOf/0/properties/records/" + ("minItems" if keyword == "MINITEMS" else "type"),
                    definition="CharacterFamilyDocument",
                )

    def test_cluster_family_document_preserves_the_record_member_minimum(self):
        document = copy.deepcopy(self.bundle["positive"]["cluster_family_document"])
        document["records"][0]["members"] = ["fixture"]
        self.assert_exact_error(
            document, "JSON_SCHEMA_MINITEMS", "/records/0/members",
            "/allOf/1/properties/records/items/allOf/0/allOf/1/properties/members/minItems",
            definition="ClusterFamilyDocument",
        )

    def test_each_common_required_field_has_an_exact_missing_member_witness(self):
        for field in self.source["schema"]["ArchetypeRecord"]["required"]:
            with self.subTest(field=field):
                instance = self.archetype()
                del instance[field]
                self.assert_exact_error(instance, "JSON_SCHEMA_REQUIRED", "", "/required",
                                        missing_properties=[field])

    def test_clusters_inherit_every_common_required_field(self):
        for field in self.source["schema"]["ArchetypeRecord"]["required"]:
            with self.subTest(field=field):
                instance = self.cluster()
                del instance[field]
                self.assert_exact_error(instance, "JSON_SCHEMA_REQUIRED", "", "/allOf/0/required",
                                        definition="ClusterRecord", missing_properties=[field])

    def test_each_cluster_required_field_has_an_exact_missing_member_witness(self):
        for field in self.source["schema"]["ClusterRecord"]["additional_required"]:
            with self.subTest(field=field):
                instance = self.cluster()
                del instance[field]
                self.assert_exact_error(instance, "JSON_SCHEMA_REQUIRED", "", "/allOf/1/required",
                                        definition="ClusterRecord", missing_properties=[field])

    def test_every_nested_required_member_is_enforced(self):
        properties = self.source["schema"]["ArchetypeRecord"]["properties"]
        for field in ("wolf_bias", "downstream_affinities"):
            for member in properties[field]["required"]:
                with self.subTest(field=field, member=member):
                    instance = self.archetype()
                    del instance[field][member]
                    self.assert_exact_error(
                        instance, "JSON_SCHEMA_REQUIRED", "/" + field,
                        "/properties/" + field + "/required", missing_properties=[member],
                    )

    def test_numeric_wolf_bias_accepts_integers_and_rejects_strings_and_booleans(self):
        for member in ("white", "dark"):
            for value in (0, 1, -1, 0.5):
                with self.subTest(member=member, accepted=value):
                    instance = self.archetype()
                    instance["wolf_bias"][member] = value
                    self.assertEqual([], self.signatures(instance))
            for value in ("0.5", True, None):
                with self.subTest(member=member, rejected=value):
                    instance = self.archetype()
                    instance["wolf_bias"][member] = value
                    self.assert_exact_error(
                        instance, "JSON_SCHEMA_TYPE", "/wolf_bias/" + member,
                        "/properties/wolf_bias/properties/" + member + "/type",
                    )

    def test_all_declared_enum_values_accept_and_unknown_values_reject(self):
        for field, enum_name, array in (
            ("family", "family", False), ("status", "record_status", False),
            ("realm_bias", "realm", True), ("player_phase_bias", "player_phase", True),
        ):
            for value in self.source["enums"][enum_name]:
                with self.subTest(field=field, accepted=value):
                    instance = self.archetype()
                    instance[field] = [value] if array else value
                    self.assertEqual([], self.signatures(instance))
            instance = self.archetype()
            instance[field] = ["unsupported"] if array else "unsupported"
            self.assert_exact_error(
                instance, "JSON_SCHEMA_ENUM", "/" + field + ("/0" if array else ""),
                "/properties/" + field + ("/items" if array else "") + "/enum",
            )

    def test_cluster_member_minimum_is_exactly_two(self):
        minimum = self.source["schema"]["ClusterRecord"]["properties"]["members"]["min_items"]
        self.assertEqual(2, minimum)
        for length in (0, 1):
            with self.subTest(length=length):
                instance = self.cluster()
                instance["members"] = ["fixture"] * length
                self.assert_exact_error(
                    instance, "JSON_SCHEMA_MINITEMS", "/members",
                    "/allOf/1/properties/members/minItems", definition="ClusterRecord",
                )
        instance = self.cluster()
        instance["members"] = ["fixture", "fixture"]
        self.assertEqual([], self.signatures(instance, "ClusterRecord"))

    def test_cluster_stability_uses_every_declared_value(self):
        for value in self.source["enums"]["cluster_stability"]:
            with self.subTest(value=value):
                instance = self.cluster()
                instance["stability_mode"] = value
                self.assertEqual([], self.signatures(instance, "ClusterRecord"))

    def test_source_hints_and_absent_constraints_are_not_promoted_to_assertions(self):
        base = self.schema["$defs"]["ArchetypeRecord"]
        self.assertNotIn("pattern", base["properties"]["id"])
        for member in ("white", "dark"):
            self.assertEqual({"type": "number"}, base["properties"]["wolf_bias"]["properties"][member])
        for name, instance in self.bundle["boundary"].items():
            with self.subTest(boundary=name):
                self.assertEqual([], self.signatures(instance, self.definition_for_case(name)))

    def test_every_bundle_reject_has_an_executed_assertion_witness(self):
        for name, instance in self.bundle["reject"].items():
            with self.subTest(case=name):
                self.assertTrue(self.signatures(instance, self.definition_for_case(name)))


if __name__ == "__main__":
    unittest.main()
