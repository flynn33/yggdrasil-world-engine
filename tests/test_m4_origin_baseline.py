"""Imported origin history retains its source binding and consumed credit."""

import copy
import hashlib
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from core.narrative_engine.origin_progression import OriginProgressionPolicy
from core.state_journal import CommitJournal, JournalError, _object_bytes
from tests.test_m4_origin_progression import configuration, document, evidence, provenance


def baseline():
    history = evidence("retained")
    return {"format": "ywe.origin_baseline.v1", "world_id": "world:one", "player_id": "player:one",
        "profile_id": "wrw.origin.v1", "source_sha256": "a" * 64, "import_anchor": "b" * 64,
        "current_phase": "first_stirrings", "actions": history["actions"], "memories": history["memories"],
        "consumed_action_refs": [row["action_trace_id"] for row in history["actions"]], "provenance": provenance()}


def reused(source, name, operation="advance", prior="first_stirrings", target="memory_recovery"):
    bundle = evidence(name, prior, target, 1, operation)
    bundle["actions"] = [copy.deepcopy(source["actions"][0])]
    bundle["memories"][0]["source_action_trace_ref"] = bundle["actions"][0]["action_trace_id"]
    return bundle


def journal_for(policy):
    def reduce(scope, state, packet):
        if scope != policy.scope:
            raise JournalError("POLICY_REJECTED")
        return policy.reduce(state, packet)
    return CommitJournal(policy.scope, policy.policy_id, policy.initial_state(), reduce), reduce


class OriginBaselineTests(unittest.TestCase):
    def assert_code(self, code, function, *args):
        with self.assertRaises(JournalError) as caught:
            function(*args)
        self.assertEqual(code, caught.exception.code)

    def test_profile_is_read_only_detached_and_equal_for_fresh_and_imported_policy(self):
        args = configuration()
        expected = copy.deepcopy(args[2])
        policies = (OriginProgressionPolicy(*args), OriginProgressionPolicy.from_baseline(baseline(), *args))
        args[2]["phases"].clear()
        for policy in policies:
            self.assertEqual(expected, policy.profile)
            exposed = policy.profile
            exposed["phases"].clear()
            self.assertEqual(expected, policy.profile)
            with self.assertRaises(AttributeError):
                policy.profile = {}

    def test_import_is_detached_retains_exact_history_and_invents_no_advances(self):
        source = baseline()
        source["memories"].reverse()
        source["actions"][0]["affected_entity_refs"] = ["entity:two", "entity:one"]
        source["memories"][0]["cosmological_tags"] = ["tag:two", "tag:one"]
        before = copy.deepcopy(source)
        with patch("core.narrative_engine.origin_progression.CommitJournal",
                   side_effect=AssertionError("import policy must not publish")):
            policy = OriginProgressionPolicy.from_baseline(source, *configuration())
        self.assertIs(type(policy), OriginProgressionPolicy)
        state = policy.initial_state()
        self.assertEqual("ywe.origin_progression.v2", state["format"])
        self.assertEqual("first_stirrings", state["current_phase"])
        self.assertEqual("veiled", state["creation"]["identity_status"])
        self.assertEqual(before["actions"], state["actions"])
        self.assertEqual(before["memories"], state["memories"])
        self.assertEqual([], state["advances"])
        self.assertEqual({key: before[key] for key in ("source_sha256", "import_anchor",
            "consumed_action_refs", "provenance")}, state["import_baseline"])
        expected = copy.deepcopy(state)
        source["actions"].clear()
        source["provenance"]["source_ash_refs"].clear()
        state["import_baseline"]["consumed_action_refs"].clear()
        state["memories"][0]["cosmological_tags"].clear()
        self.assertEqual(expected, policy.initial_state())
        self.assertFalse(hasattr(policy, "_journal"))

    def test_policy_binds_complete_baseline_and_original_policy_without_catalog_churn(self):
        source, args = baseline(), configuration()
        original = OriginProgressionPolicy(*args)
        imported = OriginProgressionPolicy.from_baseline(source, *args)
        binding = {"format": "ywe.origin_progression.v2", "original_policy_id": original.policy_id,
                   "baseline": source}
        self.assertEqual("origin.v2:" + hashlib.sha256(_object_bytes(binding)).hexdigest(), imported.policy_id)
        variations = []
        for key, value in (("source_sha256", "c" * 64), ("import_anchor", "d" * 64),
                           ("current_phase", "memory_recovery"), ("consumed_action_refs", [])):
            changed = copy.deepcopy(source)
            changed[key] = value
            variations.append(changed)
        changed = copy.deepcopy(source)
        changed["provenance"]["diagnostic_ref"] = "diagnostic:changed"
        variations.append(changed)
        changed = copy.deepcopy(source)
        changed["memories"][0]["visibility_state"] = "known_to_player"
        variations.append(changed)
        changed = copy.deepcopy(source)
        changed["actions"].reverse()
        variations.append(changed)
        for changed in variations:
            self.assertNotEqual(imported.policy_id, OriginProgressionPolicy.from_baseline(changed, *args).policy_id)
        extended = configuration([evidence("first"), evidence("unused")])
        self.assertEqual(imported.policy_id, OriginProgressionPolicy.from_baseline(source, *extended).policy_id)
        changed_args = copy.deepcopy(args)
        changed_args[4]["memory:owner"] = ["advance", "remember"]
        self.assertNotEqual(imported.policy_id, OriginProgressionPolicy.from_baseline(source, *changed_args).policy_id)

    def test_invalid_binding_history_versions_links_and_consumption_are_refused(self):
        variants = []
        def change(path, value):
            item = copy.deepcopy(baseline())
            target = item
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            variants.append((path, item))
        for key, value in (("format", "ywe.origin_baseline.v2"), ("world_id", "other"),
                ("player_id", "other"), ("profile_id", "other"), ("current_phase", "unknown"),
                ("source_sha256", "A" * 64), ("import_anchor", "b" * 63),
                ("source_sha256", "a" * 63 + "\n"), ("import_anchor", True),
                ("actions", {}), ("memories", None), ("consumed_action_refs", ["missing"]),
                ("consumed_action_refs", ["retained:action:0", "retained:action:0"]), ("extra", True)):
            change((key,), value)
        for path, value in ((("actions", 0, "schema_version"), "9.0.0"),
                (("actions", 0, "player_id"), "other"), (("actions", 0, "action_trace_id"), "bad value"),
                (("actions", 0, "action_trace_id"), "retained:action:1"),
                (("actions", 0, "source_refs"), []), (("actions", 0, "branch_ref"), "bad value"),
                (("memories", 0, "schema_version"), "9.0.0"),
                (("memories", 0, "memory_id"), "retained:memory:1"),
                (("memories", 0, "source_action_trace_ref"), "missing"),
                (("memories", 0, "branch_ref"), "branch:other"),
                (("memories", 0, "source_refs"), []), (("provenance", "source_ash_refs"), [])):
            change(path, value)
        missing = baseline()
        del missing["consumed_action_refs"]
        variants.append(("missing consumption is not empty", missing))
        for name, item in variants:
            with self.subTest(case=name):
                before = copy.deepcopy(item)
                self.assert_code("INVALID_POLICY", OriginProgressionPolicy.from_baseline, item, *configuration())
                self.assertEqual(before, item)

    def test_complete_history_may_include_minor_actions_without_invented_memory(self):
        source = baseline()
        source["actions"][0]["significance"] = "minor_record"
        source["memories"] = []
        source["consumed_action_refs"] = []
        policy = OriginProgressionPolicy.from_baseline(source, *configuration())
        self.assertEqual(source["actions"], policy.initial_state()["actions"])
        self.assertEqual([], policy.initial_state()["memories"])
        source.update(actions=[], current_phase="mortal_unknowing")
        self.assertEqual([], OriginProgressionPolicy.from_baseline(source, *configuration()).initial_state()["actions"])

    def test_imported_and_new_consumption_refuse_credit_but_allow_fresh_memory(self):
        source = baseline()
        remember = reused(source, "remember", "remember", target="first_stirrings")
        old_credit = reused(source, "old-credit")
        fresh = evidence("new-credit", "first_stirrings", "memory_recovery", 1)
        local_credit = reused(fresh, "local-credit", prior="memory_recovery", target="identity_conflict")
        args = configuration([remember, old_credit, fresh, local_credit])
        policy = OriginProgressionPolicy.from_baseline(source, *args)
        journal, reducer = journal_for(policy)
        before = journal.checkpoint()
        packet = policy.packet("narrative:owner", "credit", "old-credit")
        self.assert_code("POLICY_REJECTED", journal.commit, "credit", 0, packet)
        self.assertEqual(before, journal.checkpoint())
        packet = policy.packet("memory:owner", "remember", "remember")
        receipt = journal.commit("remember", 0, packet)
        self.assertEqual(source["actions"], journal.state()["actions"])
        self.assertEqual(3, len(journal.state()["memories"]))
        self.assertEqual([], journal.state()["advances"])
        journal.commit("credit", 1, policy.packet("narrative:owner", "credit", "new-credit"))
        self.assertEqual("memory_recovery", journal.state()["current_phase"])
        self.assertEqual(1, len(journal.state()["advances"]))
        before = journal.checkpoint()
        self.assert_code("POLICY_REJECTED", journal.commit, "local", 2,
            policy.packet("narrative:owner", "local", "local-credit"))
        self.assertEqual(before, journal.checkpoint())
        restored = CommitJournal.load(before[0], policy.scope, policy.policy_id, reducer, before[1])
        self.assertEqual(before, restored.checkpoint())
        with patch.object(OriginProgressionPolicy, "reduce", side_effect=AssertionError("retry reduced")):
            self.assertEqual(receipt, restored.commit("remember", 0, packet))

    def test_import_identity_and_consumption_cannot_be_removed_from_reduction_input(self):
        source = baseline()
        policy = OriginProgressionPolicy.from_baseline(source, *configuration([reused(source, "credit")]))
        packet = policy.packet("narrative:owner", "credit", "credit")
        for change in ("ledger", "anchor", "format", "missing"):
            state = policy.initial_state()
            if change == "ledger":
                state["import_baseline"]["consumed_action_refs"].clear()
            elif change == "anchor":
                state["import_baseline"]["import_anchor"] = "c" * 64
            elif change == "format":
                state["format"] = "ywe.origin_progression.v1"
            else:
                del state["import_baseline"]
            before = copy.deepcopy((state, packet))
            self.assert_code("POLICY_REJECTED", policy.reduce, state, packet)
            self.assertEqual(before, (state, packet))

    def test_import_and_continuation_bound_complete_state_without_partial_publication(self):
        source = baseline()
        source["memories"][0]["cosmological_tags"] = ["x" * 34000]
        large = evidence("large", "first_stirrings", "first_stirrings", 1, "remember")
        large["memories"][0]["cosmological_tags"] = ["y" * 34000]
        small = evidence("small", "first_stirrings", "first_stirrings", 1, "remember")
        policy = OriginProgressionPolicy.from_baseline(source, *configuration([large, small]))
        state, packet = policy.initial_state(), policy.packet("memory:owner", "request", "large")
        before = copy.deepcopy((state, packet))
        self.assert_code("VALUE_LIMIT", policy.reduce, state, packet)
        self.assertEqual(before, (state, packet))
        journal, _ = journal_for(policy)
        before = journal.checkpoint()
        self.assert_code("POLICY_REJECTED", journal.commit, "request", 0, packet)
        self.assertEqual(before, journal.checkpoint())
        self.assertEqual(1, journal.commit("request", 0, policy.packet("memory:owner", "request", "small")).revision)
        oversized = baseline()
        oversized["memories"][0]["cosmological_tags"] = ["x" * 65536]
        self.assert_code("INVALID_POLICY", OriginProgressionPolicy.from_baseline, oversized, *configuration())

    def test_retained_actions_have_their_own_capacity_even_without_memories(self):
        source = baseline()
        template = source["actions"][0]
        source.update(actions=[{**template, "action_trace_id": "retained:" + str(i)} for i in range(128)],
                      memories=[], consumed_action_refs=[])
        fresh = evidence("fresh", "first_stirrings", "first_stirrings", 1, "remember")
        policy = OriginProgressionPolicy.from_baseline(source, *configuration([fresh]))
        state = policy.initial_state()
        self.assert_code("VALUE_LIMIT", policy.reduce, state, policy.packet("memory:owner", "fresh", "fresh"))
        self.assertEqual(128, len(state["actions"]))
        source["actions"].append({**template, "action_trace_id": "retained:128"})
        self.assert_code("INVALID_POLICY", OriginProgressionPolicy.from_baseline, source, *configuration())

    def test_baseline_change_refuses_replay_and_future_catalog_extension_preserves_it(self):
        source = baseline()
        fresh = evidence("fresh", "first_stirrings", "memory_recovery", 1)
        args = configuration([fresh])
        policy = OriginProgressionPolicy.from_baseline(source, *args)
        journal, _ = journal_for(policy)
        journal.commit("fresh", 0, policy.packet("narrative:owner", "fresh", "fresh"))
        raw, head = journal.checkpoint()
        extended = OriginProgressionPolicy.from_baseline(source, *configuration([fresh, evidence("unused")]))
        _, reducer = journal_for(extended)
        self.assertEqual((raw, head), CommitJournal.load(raw, extended.scope, extended.policy_id, reducer, head).checkpoint())
        source["import_anchor"] = "c" * 64
        changed = OriginProgressionPolicy.from_baseline(source, *args)
        _, reducer = journal_for(changed)
        self.assert_code("INVALID_ARCHIVE", CommitJournal.load, raw, changed.scope, changed.policy_id, reducer, head)

    def test_new_schemas_validate_actual_initial_and_continued_imports_and_close_fields(self):
        names = ("m4_origin_baseline", "m4_origin_imported_state", "m4_origin_state",
                 "player_action_trace", "player_memory_record")
        schemas = {name: document("data/schemas/" + name + "_schema.json") for name in names}
        registry = Registry().with_resources((value["$id"], Resource.from_contents(value)) for value in schemas.values())
        validators = {name: Draft202012Validator(schema, registry=registry) for name, schema in schemas.items()}
        for schema in schemas.values():
            Draft202012Validator.check_schema(schema)
        source = baseline()
        fresh = evidence("fresh", "first_stirrings", "memory_recovery", 1)
        policy = OriginProgressionPolicy.from_baseline(source, *configuration([fresh]))
        first = policy.initial_state()
        continued = policy.reduce(first, policy.packet("narrative:owner", "fresh", "fresh"))
        validators["m4_origin_baseline"].validate(source)
        for state in (first, continued):
            validators["m4_origin_imported_state"].validate(state)
            self.assertFalse(validators["m4_origin_state"].is_valid(state))
        for name, instance in (("m4_origin_baseline", source), ("m4_origin_imported_state", first)):
            self.assertFalse(validators[name].is_valid({**instance, "extra": True}))
            bad = copy.deepcopy(instance)
            bad["actions"][0]["schema_version"] = "9.0.0"
            self.assertFalse(validators[name].is_valid(bad))
        bad = copy.deepcopy(first)
        bad["import_baseline"]["extra"] = True
        self.assertFalse(validators["m4_origin_imported_state"].is_valid(bad))


if __name__ == "__main__":
    unittest.main()
