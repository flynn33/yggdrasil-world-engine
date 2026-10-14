"""Closed world wire contracts with an explicit offline schema registry."""
import copy
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from core.world_location_state import WorldLocationPolicy
from tests.m4_world_location_fixture import inputs


def unavailable(uri):
    raise NoSuchResource(ref=uri)


class WorldLocationSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args, cls.view, _ = inputs("realm_shift")
        cls.schemas = cls.args[6]
        cls.registry = Registry(retrieve=unavailable).with_resources(
            (s["$id"], Resource.from_contents(s)) for s in cls.schemas.values())

    def validator(self, key, definition=None):
        schema = self.schemas[key]
        if definition:
            schema = {"$ref": schema["$id"] + "#/$defs/" + definition}
        return Draft202012Validator(schema, registry=self.registry)

    def test_all_four_schemas_check_and_actual_profile_catalog_initial_and_output_validate(self):
        for kind in ("source", "profile", "state", "update"):
            Draft202012Validator.check_schema(self.schemas[kind])
        for kind in ("fact", "location", "realm_shift"):
            args, view, _ = inputs(kind)
            owner = WorldLocationPolicy(*args)
            packet = owner.packet({"narrative_principal": "narrative:owner", "realm_principal": None if kind == "fact" else "realm:owner"}, "request:world", "update:world")
            self.validator("profile").validate(args[1])
            self.validator("state").validate(owner.initial_state())
            for record in args[4]:
                self.validator("source").validate(record)
            self.validator("update").validate(args[5][0])
            self.validator("update", "Packet").validate(packet)
            self.validator("state").validate(owner.reduce(owner.initial_state(), packet, view))

    def test_typed_values_are_one_closed_shared_contract(self):
        validator = self.validator("state", "TypedValue")
        for value in ({"kind":"token","token":"open"}, {"kind":"boolean","value":False},
                      {"kind":"integer","value":-9007199254740991}, {"kind":"reference","ref":"source:one"},
                      {"kind":"references","refs":[]}):
            validator.validate(value)
        for value in ({"kind":"token","value":"open"}, {"kind":"integer","value":True},
                      {"kind":"integer","value":9007199254740992}, {"kind":"references","refs":["a","a"]},
                      {"kind":"reference","ref":"a","accepted":True}, {"kind":"patch","value":{}}):
            self.assertFalse(validator.is_valid(value), value)

    def test_unknown_update_operation_fields_and_untyped_changes_fail(self):
        update = copy.deepcopy(self.args[5][0])
        for mutate in (lambda d:d["resolutions"][0].update(path="spine.realm"),
                       lambda d:d["resolutions"][0].update(kind="patch"),
                       lambda d:d.update(accepted=True), lambda d:d.update(resolutions=[])):
            item = copy.deepcopy(update)
            mutate(item)
            self.assertFalse(self.validator("update").is_valid(item))

    def test_closed_source_condition_and_anchor_fields(self):
        for ref in ("condition:permission", "source:permission", "anchor:law", "anchor:geography", "resolution:one"):
            record = copy.deepcopy(next(r for r in self.args[4] if r["ref"] == ref))
            record["document"]["accepted"] = True
            self.assertFalse(self.validator("source").is_valid(record), ref)
        record = copy.deepcopy(next(r for r in self.args[4] if r["ref"] == "condition:permission"))
        record["document"] = {"kind":"current_fact","slot_id":"fact:gate","expected_value":{"kind":"token","token":"open"}}
        self.assertFalse(self.validator("source").is_valid(record))

    def test_complete_heads_digest_formats_and_forged_effect_fields_fail(self):
        head = copy.deepcopy(self.view["components"][0])
        del head["state"]
        for mutate in (lambda d:d.pop("head_digest"), lambda d:d.update(policy_id="old"),
                       lambda d:d.update(state_sha256="A"*64), lambda d:d.update(revision=True)):
            item = copy.deepcopy(head)
            mutate(item)
            self.assertFalse(self.validator("source", "ComponentHead").is_valid(item))
        state = copy.deepcopy(self.args[2])
        state["consumed_effects"] = [{"effect_id":"effect","delta_ref":"delta","delta_sha256":"0"*64,"accepted":True}]
        self.assertFalse(self.validator("state").is_valid(state))

    def test_profile_and_current_location_are_closed(self):
        profile = copy.deepcopy(self.args[1])
        profile["mutable_rules"][0]["predicate"] = "anything"
        self.assertFalse(self.validator("profile").is_valid(profile))
        current = copy.deepcopy(self.args[1]["mutable_rules"][0]["source_current"])
        current["base_location_ref"] = "rewritten"
        self.assertFalse(self.validator("state", "LocationCurrent").is_valid(current))


if __name__ == "__main__":
    unittest.main()
