"""Regression cases from independent player-aggregate admission review."""

import copy
import unittest

from core.narrative_engine.origin_progression import OriginProgressionPolicy
from core.player_state import PlayerStateStore
from core.state_journal import JournalError
from tests import m4_player_fixture as fixture


def selected(arguments, reference):
    return next(row for row in arguments[5] if row["ref"] == reference)


class PlayerReviewTests(unittest.TestCase):
    def assert_code(self, expected, function, *arguments):
        with self.assertRaises(JournalError) as caught:
            function(*arguments)
        self.assertEqual(expected, caught.exception.code)

    def publish(self, owner):
        return owner.publish(owner.writer(fixture.PRINCIPAL), "request:first", 0, "update:first")

    def test_catalog_extension_cannot_turn_nonreference_strings_into_dependencies(self):
        owner = PlayerStateStore(*fixture.configuration())
        receipt = self.publish(owner)
        checkpoint = owner.checkpoint()
        extended = list(fixture.configuration())
        # These are source-system, operation, action, and phase values, not refs.
        for reference in ("narrative_engine", "origin", "advance", "choice", "meaningful",
                          "mortal_unknowing", "first_stirrings"):
            extended[5].append(fixture.reference(reference, "unused"))
        restored = PlayerStateStore.load(*checkpoint, *extended)
        self.assertEqual(checkpoint, restored.checkpoint())
        self.assertEqual(receipt, self.publish(restored))

    def test_initial_catalog_qualification_is_bound_even_when_document_is_unchanged(self):
        owner = PlayerStateStore(*fixture.configuration())
        checkpoints = [owner.checkpoint()]
        self.publish(owner)
        checkpoints.append(owner.checkpoint())
        for field in ("diagnostic", "source", "branch"):
            changed = list(fixture.configuration())
            raven = selected(changed, "raven:initial")
            if field == "diagnostic":
                raven["provenance"]["diagnostic_ref"] = "diagnostic:changed"
            elif field == "source":
                raven["provenance"]["source_ash_refs"] = ["ash:changed"]
            else:
                raven["branch_ref"] = "branch:changed"
            for checkpoint in checkpoints:
                with self.subTest(field=field, empty=checkpoint == checkpoints[0]):
                    self.assert_code("INVALID_ARCHIVE", PlayerStateStore.load, *checkpoint, *changed)

    def test_selected_historical_catalog_qualification_is_bound(self):
        owner = PlayerStateStore(*fixture.configuration())
        self.publish(owner)
        for reference in ("celestial:suspected", "plane:stirring", "ability:latent", "consequence:first"):
            with self.subTest(reference=reference):
                changed = list(fixture.configuration())
                selected(changed, reference)["provenance"]["generation_plan_ref"] = "plan:changed"
                self.assert_code("INVALID_ARCHIVE", PlayerStateStore.load, *owner.checkpoint(), *changed)

    def test_nested_agent_diagnostic_qualification_is_bound_to_its_accepting_packet(self):
        arguments = list(fixture.configuration())
        agent = copy.deepcopy(selected(arguments, "agent:initial")["document"])
        agent["asp_resilience"]["asp_diagnostic_refs"] = ["diagnostic:later"]
        arguments[5].extend([fixture.reference("diagnostic:later", "asp_diagnostic_refs"),
                             fixture.record("agent:later", "agent", agent)])
        arguments[6][0]["operations"].append({"kind": "replace", "slot": "agent",
            "previous_ref": "agent:initial", "next_ref": "agent:later", "condition_refs": []})
        owner = PlayerStateStore(*arguments)
        self.publish(owner)
        selected(arguments, "diagnostic:later")["provenance"]["diagnostic_ref"] = "diagnostic:changed"
        self.assert_code("INVALID_ARCHIVE", PlayerStateStore.load, *owner.checkpoint(), *arguments)

    def test_wrong_category_or_unlinked_evidence_cannot_advance_identity(self):
        for mode in ("wrong_category", "unlinked"):
            with self.subTest(mode=mode):
                arguments = list(fixture.configuration())
                if mode == "wrong_category":
                    selected(arguments, "evidence:play")["document"]["category"] = "unrelated_category"
                else:
                    arguments[5].append(fixture.reference("evidence:unrelated", "evidence_refs"))
                    arguments[6][0]["evidence_refs"] = ["evidence:unrelated"]
                    selected(arguments, "celestial:suspected")["document"]["evidence_refs"] = ["evidence:unrelated"]
                owner = PlayerStateStore(*arguments)
                before = owner.checkpoint()
                self.assert_code("POLICY_REJECTED", self.publish, owner)
                self.assertEqual(before, owner.checkpoint())

    def test_missing_and_cyclic_local_schema_refs_have_stable_policy_errors(self):
        for mode in ("missing", "unused_missing", "recursive", "mutual_cycle"):
            with self.subTest(mode=mode):
                arguments = list(fixture.configuration())
                schema = arguments[7]["spine"]
                if mode == "missing":
                    schema["allOf"].append({"$ref": "#/$defs/not_present"})
                elif mode == "unused_missing":
                    schema["$defs"]["unused"] = {"$ref": "#/$defs/not_present"}
                elif mode == "recursive":
                    schema["$defs"]["loop"] = {"$ref": "#/$defs/loop"}
                    schema["allOf"].append({"$ref": "#/$defs/loop"})
                else:
                    schema["$defs"]["first"] = {"$ref": "#/$defs/second"}
                    schema["$defs"]["second"] = {"$ref": "#/$defs/first"}
                    schema["allOf"].append({"$ref": "#/$defs/first"})
                self.assert_code("INVALID_POLICY", PlayerStateStore, *arguments)

    def test_initial_agent_cannot_smuggle_unresolved_links_or_unreplayed_actions(self):
        for field in ("diagnostic", "action", "branch_event", "pattern", "snapshot"):
            with self.subTest(field=field):
                arguments = list(fixture.configuration())
                agent = selected(arguments, "agent:initial")["document"]
                if field == "diagnostic":
                    agent["asp_resilience"]["asp_diagnostic_refs"] = ["diagnostic:missing"]
                elif field == "action":
                    agent["recent_action_trace_refs"] = ["action:missing"]
                elif field == "branch_event":
                    agent["branch_event_refs"] = ["event:missing"]
                elif field == "pattern":
                    agent["pattern_vector_ref"] = "pattern:missing"
                else:
                    agent["asp_resilience"]["last_valid_snapshot_ref"] = "snapshot:missing"
                self.assert_code("INVALID_POLICY", PlayerStateStore, *arguments)

    def test_observer_evidence_cannot_authorize_objective_player_changes(self):
        arguments = list(fixture.configuration())
        selected(arguments, "evidence:play")["document"]["truth_scope"] = "player_perception"
        owner = PlayerStateStore(*arguments)
        before = owner.checkpoint()
        self.assert_code("POLICY_REJECTED", self.publish, owner)
        self.assertEqual(before, owner.checkpoint())

    def test_observer_record_cannot_masquerade_as_an_objective_action_result(self):
        for category in ("worldstate_delta_refs", "branch_event_ref"):
            with self.subTest(category=category):
                arguments = list(fixture.configuration())
                source = arguments[8].evidence("origin:first")
                arguments[5].append(fixture.reference("result:observer", category, "player_perception"))
                if category == "worldstate_delta_refs":
                    source["actions"][0]["resulting_worldstate_delta_refs"] = ["result:observer"]
                    selected(arguments, "consequence:first")["document"]["external_result_refs"] = ["result:observer"]
                else:
                    source["actions"][0]["branch_event_ref"] = "result:observer"
                arguments[6][0]["operations"] = arguments[6][0]["operations"][:1]
                arguments[8] = OriginProgressionPolicy(fixture.WORLD, fixture.PLAYER,
                    fixture.document("data/profiles/wrw_origin_progression.json")["profile"],
                    {"mortal_identity_ref": "identity:mortal", "identity_status": "veiled",
                     "provenance": fixture.provenance()},
                    {fixture.PRINCIPAL: ["advance", "remember"]}, [source],
                    arguments[7]["action"], arguments[7]["memory"])
                owner = PlayerStateStore(*arguments)
                before = owner.checkpoint()
                self.assert_code("POLICY_REJECTED", self.publish, owner)
                self.assertEqual(before, owner.checkpoint())


if __name__ == "__main__":
    unittest.main()
