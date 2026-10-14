"""Domain semantics use explicitly qualified local evidence, not remote claims."""

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from core.player_state_rules import ABILITY_STATES, IDENTITY_STATES, PlayerDomainPolicy
from core.state_journal import JournalError


ROOT = Path(__file__).resolve().parents[1]


def profile():
    return json.loads((ROOT / "data/profiles/wrw_player_progression.json").read_text(encoding="utf-8"))


def context(initial=False):
    return {"world_id": "world:one", "player_id": "player:one", "mortal_identity_ref": "identity:mortal",
            "branch_ref": "branch:one", "initial": initial,
            "evidence_refs": ["evidence:new", "condition:one", "event:new", "event:recovery", "event:transfer", "event:unseal"]}


def identity(state="veiled", evidence=None):
    return {"schema_id": "ywe.celestial_identity_state.v1", "schema_version": "0.1.0",
            "identity_state": state, "reveal_status": profile()["identity_reveal_statuses"][state],
            "evidence_refs": [] if evidence is None else evidence, "known_fragments": [], "forbidden": []}


def ability(state="latent", history=None):
    return {"schema_id": "ywe.ability_state.v2", "schema_version": "2.0.0", "ability_id": "ability:one",
            "player_id": "player:one", "branch_ref": "branch:one", "current_state": state,
            "source_refs": ["source:ability"], "history_refs": [] if history is None else history,
            "sealed_reason_refs": ["reason:seal"] if state == "sealed" else []}


def raven(status="active"):
    return {"companion_id": profile()["raven_companion_id"], "bound_player_identity": "identity:mortal",
            "presence_rule": "always_with_player", "runtime_status": status,
            "absence_rule": "Presentation never removes the persistent slot.", "source_refs": ["source:raven"]}


def manifestation():
    return {"manifestation_event_id": "manifest:one", "manifesting_companions": ["white_wolf", "dark_wolf"],
            "source_refs": ["source:manifest"], "manifestation_trigger": {"criteria_met": ["Threshold crossed"]},
            "manifestation_duration": {"begins_at": "event:start", "ends_at": "event:end"},
            "dismissal_condition": "The threshold event completes."}


class PlayerDomainPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = PlayerDomainPolicy(profile())

    def reject(self, function, *args):
        with self.assertRaises(JournalError) as raised:
            function(*args)
        self.assertEqual("POLICY_REJECTED", raised.exception.code)

    def test_profile_requires_complete_canonical_states_and_matching_reveal_statuses(self):
        mutations = [lambda p: p.update(extra=True), lambda p: p["identity_states"].pop(),
            lambda p: p["ability_states"].pop(),
            lambda p: p["identity_reveal_statuses"].update(veiled="identity_integrated"),
            lambda p: p["reversible_slots"].append("celestial"),
            lambda p: p.update(wolf_companions=[])]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                value = profile()
                mutate(value)
                self.reject(PlayerDomainPolicy, value)

    def test_profile_rejects_duplicate_missing_invalid_or_unreachable_edges(self):
        changes = [lambda p: p["identity_transitions"].append(p["identity_transitions"][0]),
            lambda p: p["identity_transitions"].pop(0),
            lambda p: p["identity_transitions"][0].update(to_state="veiled"),
            lambda p: p["identity_transitions"].append({"from_state": "integrated", "to_state": "suspected"}),
            lambda p: p["ability_transitions"].append({"from_state": "latent", "to_state": "absent"}),
            lambda p: p.update(ability_transitions=[r for r in p["ability_transitions"] if r["from_state"] != "decohered"]),
            lambda p: p.update(ability_transitions=[r for r in p["ability_transitions"] if r["from_state"] != "sealed"])]
        for mutate in changes:
            value = profile()
            mutate(value)
            self.reject(PlayerDomainPolicy, value)

    def test_profile_is_detached_and_other_companion_identifiers_are_not_hardcoded(self):
        value = profile()
        value["raven_companion_id"] = "witness:other"
        policy = PlayerDomainPolicy(value)
        value["raven_companion_id"] = "mutated"
        doc = raven()
        doc["companion_id"] = "witness:other"
        policy.validate("raven", doc, context(True))
        self.reject(policy.validate, "raven", raven(), context(True))

    def test_initial_identity_cannot_contain_revealed_name_fragment_or_state(self):
        self.policy.validate("celestial", identity(), context(True))
        documents = [identity("suspected", ["evidence:new"])]
        for key in ("celestial_name_ref", "epithet_ref", "last_reveal_event_ref"):
            documents.append({**identity(), key: "revealed:value"})
        documents.append({**identity(), "known_fragments": [{"fragment_id": "fragment:one", "source_refs": ["source:one"]}]})
        for doc in documents:
            self.reject(self.policy.validate, "celestial", doc, context(True))

    def test_identity_reveal_status_and_fragment_identity_are_semantic(self):
        doc = identity("suspected", ["evidence:new"])
        doc["reveal_status"] = "identity_integrated"
        self.reject(self.policy.validate, "celestial", doc, context())
        doc = identity("suspected", ["evidence:new"])
        fragment = {"fragment_id": "fragment:one", "source_refs": ["source:one"]}
        doc["known_fragments"] = [fragment, fragment]
        self.reject(self.policy.validate, "celestial", doc, context())

    def test_identity_transitions_follow_edges_and_need_new_qualified_evidence(self):
        before, after = identity(), identity("suspected", ["evidence:new"])
        snapshot = copy.deepcopy((before, after))
        self.policy.transition("celestial", before, after, context(), [])
        self.assertEqual(snapshot, (before, after))
        self.reject(self.policy.transition, "celestial", before, identity("integrated", ["evidence:new"]), context(), [])
        self.reject(self.policy.transition, "celestial", before, identity("suspected", ["unqualified:ref"]), context(), [])
        self.reject(self.policy.transition, "celestial", after, after, context(), [])

    def test_identity_preserves_prior_fragment_contents_evidence_and_revealed_name(self):
        before = identity("fragmented", ["evidence:old"])
        before["known_fragments"] = [{"fragment_id": "fragment:one", "source_refs": ["source:one"]}]
        before["celestial_name_ref"] = "name:one"
        after = copy.deepcopy(before)
        after.update(identity_state="named_fragment", reveal_status="name_partially_revealed")
        after["evidence_refs"].append("evidence:new")
        self.policy.transition("celestial", before, after, context(), [])
        for mutate in (lambda d: d["known_fragments"].clear(),
                       lambda d: d["known_fragments"][0].update(source_refs=["source:other"]),
                       lambda d: d["evidence_refs"].pop(0), lambda d: d.update(celestial_name_ref="name:other")):
            invalid = copy.deepcopy(after)
            mutate(invalid)
            self.reject(self.policy.transition, "celestial", before, invalid, context(), [])

    def test_initial_bloodline_and_wolf_semantics_without_invented_score_sum(self):
        bloodline = {"source_refs": ["source:one"], "signals": [{"bloodline_id": "bloodline:one", "status": "dormant",
            "score_q6": 900000, "revealed_to_player": False, "source_refs": ["source:one"]}]}
        self.policy.validate("bloodline", bloodline, context(True))
        bloodline["signals"][0]["revealed_to_player"] = True
        self.reject(self.policy.validate, "bloodline", bloodline, context(True))
        bloodline["signals"][0].update(revealed_to_player=False, status="awakened")
        self.reject(self.policy.validate, "bloodline", bloodline, context(True))
        wolf = {"source_refs": ["source:one"], "white_wolf": {"source_refs": ["source:one"], "resonance_q6": 900000, "signal_state": "latent"},
            "dark_wolf": {"source_refs": ["source:one"], "resonance_q6": 800000, "signal_state": "latent"},
            "twin_coherence": {"source_refs": ["source:one"], "coherence_q6": 100000}}
        self.policy.validate("wolf", wolf, context(True))
        wolf["white_wolf"]["signal_state"] = "active"
        self.reject(self.policy.validate, "wolf", wolf, context(True))
        self.policy.validate("wolf", wolf, context())

    def test_plane_scores_are_exact_and_provenance_is_not_optional(self):
        doc = {"source_refs": ["source:one"], "planes": {"plane:one": {"source_refs": ["source:one"], "score_q6": 1000000}}}
        self.policy.validate("plane", doc, context())
        for value in (True, 1.0, -1, 1000001):
            doc["planes"]["plane:one"]["score_q6"] = value
            self.reject(self.policy.validate, "plane", doc, context())
        doc["planes"]["plane:one"] = {"source_refs": [], "score_q6": 0}
        self.reject(self.policy.validate, "plane", doc, context())

    def test_raven_identity_binding_and_story_separation(self):
        before, after = raven(), raven("story_separated")
        self.reject(self.policy.transition, "raven", before, after, context(), [])
        self.policy.transition("raven", before, after, context(), ["condition:one"])
        self.reject(self.policy.transition, "raven", after, before, context(), [])
        self.policy.transition("raven", after, before, context(), ["condition:one"])
        self.policy.transition("raven", before, raven("offscreen_active"), context(), [])
        for key in ("bound_player_identity", "companion_id"):
            invalid = {**before, key: "other:identity"}
            self.reject(self.policy.validate, "raven", invalid, context())
        empty = {**context(True), "evidence_refs": []}
        self.reject(self.policy.validate, "raven", after, empty)

    def test_manifestation_requires_actual_criteria_duration_and_dismissal(self):
        self.policy.validate("manifestation", manifestation(), context())
        self.reject(self.policy.validate, "manifestation", manifestation(), context(True))
        mutations = [lambda d: d["manifestation_trigger"].update(criteria_met=[]),
            lambda d: d["manifestation_trigger"].update(criteria_met=[" "]),
            lambda d: d["manifestation_duration"].update(begins_at=""),
            lambda d: d["manifestation_duration"].update(ends_at=" "),
            lambda d: d["manifestation_duration"].update(ends_at="event:start"),
            lambda d: d.update(dismissal_condition=""),
            lambda d: d.update(manifesting_companions=["other:wolf"])]
        for mutate in mutations:
            doc = manifestation()
            mutate(doc)
            self.reject(self.policy.validate, "manifestation", doc, context())

    def test_all_ability_states_and_profile_edges_are_exercised(self):
        for state in ABILITY_STATES:
            self.policy.validate("ability", ability(state), context())
        for edge in profile()["ability_transitions"]:
            before, after = ability(edge["from_state"]), ability(edge["to_state"], ["event:new"])
            self.policy.transition("ability", before, after, context(), ["condition:one"])
        for state in IDENTITY_STATES:
            self.policy.validate("celestial", identity(state, ["evidence:new"]), context())

    def test_ability_creation_is_latent_and_transitions_cannot_skip(self):
        new = ability()
        new["source_refs"].append("evidence:new")
        self.policy.transition("ability", None, new, context(), [])
        self.reject(self.policy.transition, "ability", None, ability(), context(), [])
        self.reject(self.policy.transition, "ability", None, ability("unlocked"), context(), [])
        self.reject(self.policy.validate, "ability", ability("unlocked"), context(True))
        self.reject(self.policy.transition, "ability", ability(), ability("mastered", ["event:new"]), context(), [])

    def test_ability_identity_and_history_are_preserved(self):
        before, after = ability("pressured", ["event:old"]), ability("eligible", ["event:old", "event:new"])
        self.policy.transition("ability", before, after, context(), [])
        for mutate in (lambda d: d.update(ability_id="ability:other"),
                       lambda d: d.update(history_refs=["event:new"]),
                       lambda d: d.update(history_refs=["event:old"]),
                       lambda d: d.update(history_refs=["event:old", "unqualified:history"]),
                       lambda d: d.update(player_id="player:other"),
                       lambda d: d.update(branch_ref="branch:other")):
            invalid = copy.deepcopy(after)
            mutate(invalid)
            self.reject(self.policy.transition, "ability", before, invalid, context(), [])

    def test_transformation_preserves_provenance_and_decoherence_recovers(self):
        before, after = ability("coherent"), ability("transformed", ["event:new"])
        after["source_refs"].append("source:new")
        self.policy.transition("ability", before, after, context(), [])
        after["source_refs"] = ["source:new"]
        self.reject(self.policy.transition, "ability", before, after, context(), [])
        self.policy.transition("ability", ability("decohered"), ability("coherent", ["event:recovery"]), context(), [])

    def test_ability_branch_rebinding_retains_identity_state_provenance_and_history(self):
        before = ability("coherent", ["event:old"])
        after = {**copy.deepcopy(before), "branch_ref": "branch:next", "history_refs": ["event:old", "event:transfer"]}
        next_context = {**context(), "branch_ref": "branch:next"}
        self.policy.transition("ability", before, after, next_context, [])
        self.assertEqual(before["ability_id"], after["ability_id"])
        self.assertEqual(before["current_state"], after["current_state"])
        self.assertEqual(before["source_refs"], after["source_refs"])
        for mutate in (lambda d: d.update(ability_id="ability:other"),
                       lambda d: d.update(source_refs=["source:replacement"]),
                       lambda d: d.update(history_refs=["event:transfer"]),
                       lambda d: d.update(history_refs=["event:old"])):
            invalid = copy.deepcopy(after)
            mutate(invalid)
            self.reject(self.policy.transition, "ability", before, invalid, next_context, [])

    def test_sealed_exit_requires_qualified_condition_and_seal_requires_reason(self):
        before, after = ability("sealed"), ability("unlocked", ["event:unseal"])
        self.reject(self.policy.transition, "ability", before, after, context(), [])
        self.reject(self.policy.transition, "ability", before, after, context(), ["unqualified:condition"])
        self.policy.transition("ability", before, after, context(), ["condition:one"])
        before["sealed_reason_refs"] = []
        self.reject(self.policy.validate, "ability", before, context())

    def test_exact_coherence_accepts_negative_large_and_tiny_values_without_unit_interval(self):
        schema = json.loads((ROOT / "data/schemas/m4_ability_state_schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        for coefficient, exponent in (("-12345", 10000), ("9" * 128, -10000), ("0", 0), ("1234567", -7)):
            doc = ability()
            doc["coherence"] = {"coefficient": coefficient, "exponent": exponent, "status": "qualified"}
            validator.validate(doc)
            self.policy.validate("ability", doc, context())

    def test_noncanonical_or_inexact_coherence_is_rejected_by_schema_and_policy(self):
        schema = json.loads((ROOT / "data/schemas/m4_ability_state_schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        values = [("-0", 0), ("01", 0), ("10", 0), ("+1", 0), ("1.2", 0), ("1\n", 0),
                  ("1", True), ("1", 10001), ("0", 3), ("9" * 129, 0)]
        for coefficient, exponent in values:
            doc = ability()
            doc["coherence"] = {"coefficient": coefficient, "exponent": exponent, "status": "qualified"}
            self.assertFalse(validator.is_valid(doc), (coefficient, exponent))
            self.reject(self.policy.validate, "ability", doc, context())

    def test_ability_schema_is_closed_bounded_and_requires_qualified_sources(self):
        validator = Draft202012Validator(json.loads((ROOT / "data/schemas/m4_ability_state_schema.json").read_text(encoding="utf-8")))
        mutations = [lambda d: d.update(extra=True), lambda d: d.update(source_refs=[]),
            lambda d: d.update(player_id="player:one\n"), lambda d: d.update(history_refs=["same", "same"]),
            lambda d: d.update(schema_version="0.1.0"),
            lambda d: d.update(current_state="sealed", sealed_reason_refs=[])]
        for mutate in mutations:
            doc = ability()
            mutate(doc)
            self.assertFalse(validator.is_valid(doc))

    def test_agent_and_history_keep_player_branch_and_record_identity(self):
        agent = {"agent_id": "agent:one", "agent_kind": "player_mortal_instance", "mortal_instance_id": "identity:mortal",
            "current_leaf_branch_ref": "branch:one", "asp_resilience": {"asp_diagnostic_refs": ["diagnostic:one"]}}
        self.policy.validate("agent", agent, context(True))
        self.reject(self.policy.validate, "agent", {**agent, "mortal_instance_id": "identity:other"}, context())
        self.reject(self.policy.validate, "agent", {**agent, "current_leaf_branch_ref": "branch:other"}, context())
        self.reject(self.policy.transition, "agent", agent, {**agent, "agent_id": "agent:other"}, context(), [])
        history = {"player_id": "player:one", "current_leaf_branch_ref": "branch:one", "entries": []}
        self.policy.validate("branch_history", history, context(True))
        self.reject(self.policy.validate, "branch_history", {**history, "player_id": "player:other"}, context())
        entry = {"branch_event_ref": "event:one", "leaf_branch_ref": "branch:one", "source_action_trace_ref": "action:one",
                 "chosen_action": "Choose a path", "source_refs": ["source:one"]}
        after = {**history, "entries": [entry]}
        self.policy.transition("branch_history", history, after, context(), [])
        self.reject(self.policy.transition, "branch_history", after, history, context(), [])

    def test_actions_and_memories_bind_actual_player_and_branch(self):
        action = {"action_trace_id": "action:one", "player_id": "player:one", "branch_ref": "branch:one",
                  "significance": "meaningful", "source_refs": ["source:one"]}
        self.policy.validate("action", action, context())
        for key, value in (("player_id", "player:other"), ("branch_ref", "branch:other"), ("significance", "minor_record")):
            self.reject(self.policy.validate, "action", {**action, key: value}, context())
        memory = {"memory_id": "memory:one", "source_action_trace_ref": "action:one", "branch_ref": "branch:one", "source_refs": ["source:one"]}
        self.policy.validate("memory", memory, context())
        self.reject(self.policy.validate, "memory", {**memory, "branch_ref": "branch:other"}, context())

    def test_hostile_values_fail_with_stable_code_and_leave_arguments_unchanged(self):
        for value in (None, [], {}, "text", True, {"identity_state": []}):
            self.reject(self.policy.validate, "celestial", value, context())
        for value in (None, [], {}, {**context(), "initial": 1}, {**context(), "extra": "x"}):
            self.reject(self.policy.validate, "celestial", identity(), value)
        for kind in (None, [], "unknown"):
            self.reject(self.policy.validate, kind, {}, context())
        self.reject(self.policy.transition, "ability", None, {}, context(), [])
        self.reject(self.policy.transition, "ability", ability(), ability(), context(), "not-a-list")
        before, after = ability("latent"), ability("mastered", ["event:new"])
        snapshot = copy.deepcopy((before, after))
        self.reject(self.policy.transition, "ability", before, after, context(), [])
        self.assertEqual(snapshot, (before, after))


if __name__ == "__main__":
    unittest.main()
