"""Actual observer composition, persistence, trust-boundary and replay controls."""

from concurrent.futures import ThreadPoolExecutor
import copy
from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from core import core_values as cv
from core.perception_engine.perception import PerceptionEngine
from core.perception_engine.persistence import PerceptionStore
from core.state_journal import CommitJournal, JournalError, TruthScope
from tests.test_m3_core_cosmology_realm import pure_model


def inputs():
    binding, _ = pure_model()
    fact = cv.DeclaredTruthFact("door", "OBJECTIVE_SHARED", "world", "alice", "closed", ("evidence",))
    belief = cv.DeclaredTruthFact("door", "DERIVED_INTERPRETATION", "world", "alice", "open", ("belief",))
    truth = cv.TruthInputSnapshot("truth.one", "world", (fact, belief), ("door", "tree"), "DECLARED_INPUT")
    provenance = cv.CoreProvenance("snapshot", "diagnostic", "plan", ("ash",))
    rules = (cv.PerceptionRule("hide", 1, "alice", "door", ("door",), False, ("veiled",)),)
    return binding, rules, ((truth, provenance),)


class PerceptionPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.binding, self.rules, self.sources = inputs()
        self.owner = self.make()

    def make(self, **changes):
        arguments = dict(world_id="world", observer_id="alice", binding=self.binding,
                         rules=self.rules, sources=self.sources)
        arguments.update(changes)
        return PerceptionStore(**arguments)

    def reload(self, checkpoint=None, **changes):
        raw, head = checkpoint or self.owner.checkpoint()
        arguments = dict(world_id="world", observer_id="alice", binding=self.binding,
                         rules=self.rules, sources=self.sources)
        arguments.update(changes)
        return PerceptionStore.load(raw, head, **arguments)

    def assert_code(self, code, action):
        with self.assertRaises(JournalError) as caught:
            action()
        self.assertEqual(caught.exception.code, code)

    def test_actual_owner_output_matches_complete_persisted_overlay(self):
        truth, provenance = self.sources[0]
        original = cv.canonical_bytes(truth), cv.canonical_bytes(provenance)
        request = cv.PerceptionRequest("view", "alice", truth, self.rules, provenance)
        engine = PerceptionEngine(self.binding)
        result = engine.compose_overlay(request)
        self.assertTrue(engine.validate_owned_result(result))
        receipt = self.owner.publish("view", 0, "truth.one")
        state = self.owner.state()
        self.assertEqual(receipt.revision, 1)
        self.assertEqual(state["overlay"], result.value.to_record())
        self.assertEqual(state["overlay"]["hidden_entities"], ["door"])
        self.assertEqual(state["overlay"]["contradiction_refs"], ["door"])
        self.assertEqual(state["objective_effects"], "NONE")
        self.assertEqual(original, (cv.canonical_bytes(truth), cv.canonical_bytes(provenance)))
        self.assertEqual(self.owner.checkpoint(), self.reload().checkpoint())
        self.assertEqual(original, (cv.canonical_bytes(truth), cv.canonical_bytes(provenance)))

    def test_two_observers_keep_distinct_views_of_identical_objective_truth(self):
        bob = self.make(observer_id="bob")
        self.owner.publish("view", 0, "truth.one")
        bob.publish("view", 0, "truth.one")
        a, b = self.owner.state()["overlay"], bob.state()["overlay"]
        self.assertEqual(a["hidden_entities"], ["door"])
        self.assertEqual(b["hidden_entities"], [])
        self.assertEqual(b["visible_entities"], ["door", "tree"])
        self.assertEqual(a["request"]["truth"], b["request"]["truth"])
        self.assertEqual(a["truth_sha256"], b["truth_sha256"])
        self.assert_code("INVALID_ARCHIVE", lambda: self.reload(observer_id="bob"))

    def test_empty_checkpoint_and_empty_entity_no_op_replay(self):
        self.assertEqual(self.owner.checkpoint(), self.reload().checkpoint())
        self.assertIsNone(self.owner.state()["overlay"])
        truth, provenance = self.sources[0]
        sources = ((replace(truth, entity_refs=(), facts=()), provenance),)
        owner = self.make(sources=sources, rules=())
        owner.publish("empty", 0, "truth.one")
        overlay = owner.state()["overlay"]
        self.assertEqual(overlay["visible_entities"], [])
        self.assertEqual(overlay["request"]["provenance"], provenance.to_record())
        self.assertEqual(owner.checkpoint(), self.reload(owner.checkpoint(), sources=sources, rules=()).checkpoint())

    def test_exact_retry_and_restored_retry_do_not_repeat_engine(self):
        receipt = self.owner.publish("view", 0, "truth.one")
        restored = self.reload()
        with patch.object(PerceptionEngine, "compose_overlay", side_effect=AssertionError("must not execute")):
            self.assertEqual(self.owner.publish("view", 0, "truth.one"), receipt)
            self.assertEqual(restored.publish("view", 0, "truth.one"), receipt)

    def test_conflicting_retry_and_stale_new_request_are_atomic(self):
        self.owner.publish("view", 0, "truth.one")
        before = self.owner.checkpoint()
        self.assert_code("IDENTITY_CONFLICT", lambda: self.owner.publish("view", 1, "truth.one"))
        self.assert_code("REVISION_CONFLICT", lambda: self.owner.publish("other", 0, "truth.one"))
        self.assertEqual(before, self.owner.checkpoint())

    def test_unknown_source_and_bad_identifiers_reserve_nothing(self):
        before = self.owner.checkpoint()
        self.assert_code("UNKNOWN_TRUTH", lambda: self.owner.publish("view", 0, "missing"))
        for value in (None, True, "bad value", "x" * 129, "valid\n"):
            self.assert_code("INVALID_VALUE", lambda: self.owner.publish(value, 0, "truth.one"))
        self.assertEqual(before, self.owner.checkpoint())
        self.assertEqual(self.owner.publish("view", 0, "truth.one").revision, 1)

    def test_original_result_validation_refuses_foreign_and_copied_results(self):
        truth, provenance = self.sources[0]
        foreign = PerceptionEngine(self.binding).compose_overlay(
            cv.PerceptionRequest("view", "alice", truth, self.rules, provenance))
        before = self.owner.checkpoint()
        for replacement in (foreign, copy.copy(foreign)):
            with patch.object(PerceptionEngine, "compose_overlay", return_value=replacement):
                self.assert_code("POLICY_REJECTED", lambda: self.owner.publish("view", 0, "truth.one"))
            self.assertEqual(before, self.owner.checkpoint())
        self.owner.publish("view", 0, "truth.one")

    def test_conflicting_objective_input_refuses_without_mutation(self):
        truth, provenance = self.sources[0]
        conflicting = replace(truth.facts[0], value_token="open")
        truth = replace(truth, facts=(*truth.facts, conflicting))
        owner = self.make(sources=((truth, provenance),))
        before = owner.checkpoint(), cv.canonical_bytes(truth)
        self.assert_code("POLICY_REJECTED", lambda: owner.publish("view", 0, "truth.one"))
        self.assertEqual(before, (owner.checkpoint(), cv.canonical_bytes(truth)))

    def test_unknown_rule_reference_refuses_atomically(self):
        owner = self.make(rules=(replace(self.rules[0], entity_ref="missing"),))
        before = owner.checkpoint()
        self.assert_code("POLICY_REJECTED", lambda: owner.publish("view", 0, "truth.one"))
        self.assertEqual(before, owner.checkpoint())

    def test_mutating_constructor_objects_or_returned_state_does_not_alias(self):
        truth, provenance = self.sources[0]
        expected_truth, expected_provenance = truth.to_record(), provenance.to_record()
        object.__setattr__(truth, "entity_refs", ())
        object.__setattr__(provenance, "generation_plan_ref", "changed")
        object.__setattr__(self.rules[0], "visible", True)
        object.__setattr__(self.binding, "policy_sha256", "0" * 64)
        self.owner.publish("view", 0, "truth.one")
        state = self.owner.state()
        self.assertEqual(state["overlay"]["request"]["truth"], expected_truth)
        self.assertEqual(state["overlay"]["request"]["provenance"], expected_provenance)
        self.assertEqual(state["overlay"]["hidden_entities"], ["door"])
        state["overlay"]["hidden_entities"].clear()
        self.assertEqual(self.owner.state()["overlay"]["hidden_entities"], ["door"])

    def test_catalog_extension_replays_but_missing_or_changed_history_refuses(self):
        self.owner.publish("view", 0, "truth.one")
        truth, provenance = self.sources[0]
        extension = (*self.sources, (replace(truth, snapshot_ref="truth.two"), provenance))
        restored = self.reload(sources=extension)
        self.assertEqual(self.owner.checkpoint(), restored.checkpoint())
        restored.publish("next", 1, "truth.two")
        self.assertEqual(restored.state()["truth_substrate_ref"], "truth.two")
        self.assert_code("INVALID_ARCHIVE", lambda: self.reload(sources=()))
        for pair in ((replace(truth, entity_refs=("door",)), provenance),
                     (truth, replace(provenance, diagnostic_ref="other"))):
            self.assert_code("INVALID_ARCHIVE", lambda: self.reload(sources=(pair,)))

    def test_changed_visibility_policy_refuses_replay(self):
        self.owner.publish("view", 0, "truth.one")
        self.assert_code("INVALID_ARCHIVE", lambda: self.reload(rules=(replace(self.rules[0], visible=True),)))

    def test_corrupt_overlay_packet_truncation_and_head_refuse(self):
        self.owner.publish("view", 0, "truth.one")
        raw, head = self.owner.checkpoint()
        original = json.loads(raw)
        variants = []
        for field in ("final_state", "initial_state"):
            damaged = copy.deepcopy(original)
            damaged[field]["objective_effects"] = "KNOWN_COMPLETE"
            variants.append(json.dumps(damaged).encode())
        damaged = copy.deepcopy(original)
        damaged["entries"][0]["packet"]["truth_sha256"] = "0" * 64
        variants.extend((json.dumps(damaged).encode(), raw[:-1]))
        for damaged in variants:
            self.assert_code("INVALID_ARCHIVE", lambda: self.reload((damaged, head)))
        self.assert_code("INVALID_ARCHIVE", lambda: self.reload((raw, "0" * 64)))
        self.assertEqual((raw, head), self.owner.checkpoint())

    def test_even_trusted_archive_cannot_supply_nonempty_initial_view(self):
        raw, _ = self.owner.checkpoint()
        header = json.loads(raw)
        altered = {**header["initial_state"], "truth_substrate_ref": "forged"}
        journal = CommitJournal(TruthScope(**header["scope"]), header["policy_id"], altered, lambda *args: {})
        self.assert_code("INVALID_ARCHIVE", lambda: self.reload(journal.checkpoint()))

    def test_concurrent_publication_has_one_revision_winner(self):
        def publish(identifier):
            try:
                return self.owner.publish(identifier, 0, "truth.one").revision
            except JournalError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(publish, ("one", "two")))
        self.assertCountEqual(results, [1, "REVISION_CONFLICT"])
        self.assertEqual(self.owner.checkpoint(), self.reload().checkpoint())

    def test_bad_construction_types_duplicate_sources_scope_and_limits(self):
        truth, provenance = self.sources[0]
        cases = [dict(binding={}), dict(rules=[]), dict(sources=[]), dict(sources=(truth,)),
                 dict(rules=(object(),)), dict(sources=((truth, {}),)),
                 dict(sources=(*self.sources, *self.sources)),
                 dict(sources=((replace(truth, scope_ref="other"), provenance),)),
                 dict(rules=self.rules * 257), dict(sources=self.sources * 129)]
        for arguments in cases:
            with self.subTest(arguments=tuple(arguments)):
                self.assert_code("INVALID_POLICY", lambda: self.make(**arguments))

    def test_large_valid_m3_overlay_is_rejected_atomically_by_journal_bound(self):
        truth, provenance = self.sources[0]
        rules = tuple(replace(self.rules[0], rule_id="rule." + str(i), condition_fact_refs=(),
                              interpretation_tags=()) for i in range(200))
        owner = self.make(rules=rules)
        request = cv.PerceptionRequest("view", "alice", truth, rules, provenance)
        result = PerceptionEngine(self.binding).compose_overlay(request)
        self.assertEqual(result.status, "COMPLETED")
        self.assertGreater(len(result.value.canonical_bytes()), 65536)
        before = owner.checkpoint()
        self.assert_code("POLICY_REJECTED", lambda: owner.publish("view", 0, "truth.one"))
        self.assertEqual(before, owner.checkpoint())

    def test_source_and_rule_byte_limits_are_enforced_without_clipping(self):
        truth, provenance = self.sources[0]
        facts = tuple(replace(truth.facts[0], fact_id="fact." + str(i), value_token="x" * 512)
                      for i in range(100))
        oversized = replace(truth, facts=facts)
        self.assertGreater(len(cv.canonical_bytes(oversized)), 65536)
        self.assert_code("INVALID_POLICY", lambda: self.make(sources=((oversized, provenance),)))
        large = replace(truth, facts=facts[:80])
        sources = tuple((replace(large, snapshot_ref="truth." + str(i)), provenance) for i in range(20))
        total = sum(len(cv.canonical_bytes(t)) + len(cv.canonical_bytes(p)) for t, p in sources)
        self.assertGreater(total, 1048576)
        self.assertLess(len(cv.canonical_bytes(large)) + len(cv.canonical_bytes(provenance)), 65536)
        self.assert_code("INVALID_POLICY", lambda: self.make(sources=sources))
        rules = tuple(replace(self.rules[0], rule_id="rule." + str(i),
                              interpretation_tags=("x" * 128, "y" * 128, "z" * 128)) for i in range(128))
        self.assertGreater(sum(len(cv.canonical_bytes(rule)) for rule in rules), 65536)
        self.assert_code("INVALID_POLICY", lambda: self.make(rules=rules))

    def test_exact_source_count_limit_and_long_identifier_are_accepted(self):
        truth, provenance = self.sources[0]
        sources = tuple((replace(truth, snapshot_ref="truth." + str(i)), provenance) for i in range(128))
        owner = self.make(sources=sources)
        owner.publish("r" * 128, 0, "truth.127")
        restored = self.reload(owner.checkpoint(), sources=sources)
        self.assertEqual(restored.checkpoint(), owner.checkpoint())


class PerceptionStateSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        def deny(uri):
            raise NoSuchResource(ref=uri)
        registry = Registry(retrieve=deny)
        catalog = json.loads((root / "data/validation/contract_catalog.json").read_text(encoding="utf-8"))
        for row in catalog["schemas"]:
            schema = json.loads((root / row["path"]).read_text(encoding="utf-8"))
            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
        schema = json.loads((root / "data/schemas/m4_perception_state_schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        cls.validator = Draft202012Validator(schema, registry=registry)

    def test_empty_and_actual_published_state_match_schema(self):
        binding, rules, sources = inputs()
        owner = PerceptionStore("world", "alice", binding, rules, sources)
        self.validator.validate(owner.state())
        owner.publish("view", 0, "truth.one")
        self.validator.validate(owner.state())
        fixture = Path(__file__).resolve().parents[1] / "examples/state_journal/observer_view.example.json"
        self.assertEqual(json.loads(fixture.read_text(encoding="utf-8")), owner.state())

    def test_schema_closed_fields_effect_and_empty_pair(self):
        binding, rules, sources = inputs()
        owner = PerceptionStore("world", "alice", binding, rules, sources)
        state = owner.state()
        for field in state:
            damaged = dict(state)
            del damaged[field]
            self.assertFalse(self.validator.is_valid(damaged), field)
        for field, value in (("extra", True), ("objective_effects", "KNOWN_COMPLETE"),
                             ("truth_substrate_ref", "truth.one"), ("observer_id", "bad\n")):
            self.assertFalse(self.validator.is_valid({**state, field: value}))
        owner.publish("view", 0, "truth.one")
        self.assertFalse(self.validator.is_valid({**owner.state(), "truth_substrate_ref": None}))


if __name__ == "__main__":
    unittest.main()
