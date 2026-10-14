"""Actual owner effects, source qualification and refusal isolation."""
import copy
import hashlib
from dataclasses import replace
import unittest
from unittest.mock import patch

from core import core_values as cv
from core.realm_engine.realm import RealmEngine
from core.state_journal import CommitJournal, JournalError, TruthScope, _encode, _object_bytes
from core.world_location_state import WorldLocationPolicy
from tests.m4_world_location_fixture import build, inputs, digest, source, record, shared_veil_basis, WORLD


def change_record(args, ref, mutate):
    row = next(x for x in args[4] if x["ref"] == ref)
    mutate(row["document"])
    row["sha256"] = digest(row["document"])
    if ref in args[2]["records"]:
        args[2]["records"][ref] = copy.deepcopy(row)


def ready(args, view):
    owner = WorldLocationPolicy(*args)
    realm = None if all(x["kind"] == "fact" for x in args[5][0]["resolutions"]) else "realm:owner"
    packet = owner.packet({"narrative_principal": "narrative:owner", "realm_principal": realm}, "request:world", "update:world")
    return owner, packet, view


class WorldLocationTests(unittest.TestCase):
    def rejects(self, code, action):
        with self.assertRaises(JournalError) as caught:
            action()
        self.assertEqual(caught.exception.code, code)

    def test_fact_effect_is_detached_exact_and_single_use(self):
        owner, packet, view = build()
        state = owner.initial_state()
        originals = copy.deepcopy((state, packet, view))
        after = owner.reduce(state, packet, view)
        self.assertEqual(after["facts"][0]["value"], {"kind": "token", "token": "open"})
        self.assertEqual((state, packet, view), originals)
        self.assertEqual(after, owner.reduce(state, packet, view))
        self.rejects("POLICY_REJECTED", lambda: owner.reduce(after, packet, view))
        projection = owner.project_facts(after)
        projection["facts"][0]["value"]["token"] = "broken"
        self.assertEqual(after["facts"][0]["value"]["token"], "open")
        definition = owner.definition("definition:fact:gate")
        definition["subject_ref"] = "foreign"
        self.assertEqual(owner.definition("definition:fact:gate")["subject_ref"], "location:one")

    def test_location_rule_changes_actual_current_access_and_preserves_source(self):
        owner, packet, view = build("location")
        before = owner.initial_state()
        after = owner.reduce(before, packet, view)
        row = next(x for x in after["locations"] if x["location_id"] == "location:one")
        self.assertEqual(row["current_record_ref"], "location:one:open")
        current = after["records"][row["current_record_ref"]]["document"]["current"]
        self.assertEqual((current["status"], current["access"][0]["state"]), ("activated", "open"))
        self.assertEqual(after["records"]["location:one:initial"], before["records"]["location:one:initial"])
        self.assertEqual(len(row["history_event_refs"]), 2)

    def test_realm_accessor_returns_actual_binding_and_detached_mapping(self):
        args, view, _ = inputs()
        owner = WorldLocationPolicy(*args)
        definition = next(x for x in args[7].profile_realms if x.realm_id == "realm:echo")
        expected = {"definition": definition.to_record(), "plane_id": "P4_Mental"}
        self.assertEqual(owner.realm("realm:echo"), expected)
        detached = owner.realm("realm:echo")
        detached["definition"]["realm_id"] = "realm:foreign"
        detached["plane_id"] = "plane:foreign"
        self.assertEqual(owner.realm("realm:echo"), expected)
        self.rejects("UNKNOWN_EVIDENCE", lambda: owner.realm("realm:missing"))
        args[1]["realm_plane_bindings"] = [x for x in args[1]["realm_plane_bindings"] if x["realm_id"] != "realm:echo"]
        without_mapping = WorldLocationPolicy(*args)
        self.rejects("UNKNOWN_EVIDENCE", lambda: without_mapping.realm("realm:echo"))
        for malformed in (None, [], {}, True, 3, "", "bad id"):
            with self.subTest(malformed=malformed):
                self.rejects("INVALID_VALUE", lambda: owner.realm(malformed))

    def test_actual_realm_results_and_replay_remain_proposal_only(self):
        owner, packet, view = build("realm_shift")
        first = owner.reduce(owner.initial_state(), packet, view)
        checks = first["events"][0]["realm_checks"][0]
        self.assertEqual(checks["access_result"]["effect_status"], "NONE")
        self.assertEqual(checks["shift_result"]["effect_status"], "PROPOSED_ONLY")
        self.assertEqual(first["occupancies"][0]["realm_id"], "realm:echo")
        with patch.object(RealmEngine, "evaluate_access", autospec=True, side_effect=RealmEngine.evaluate_access) as call:
            again = owner.reduce(owner.initial_state(), packet, view)
        self.assertGreaterEqual(call.call_count, 2)
        self.assertEqual(first, again)

    def test_realm_threshold_false_and_missing_veil_refuse(self):
        for options in ({"threshold": 10001}, {"veil": "FALSE"}, {"veil": "UNAVAILABLE"}):
            with self.subTest(options=options):
                owner, packet, view = build("realm_shift", **options)
                initial = owner.initial_state()
                self.rejects("POLICY_REJECTED", lambda: owner.reduce(initial, packet, view))
                self.assertEqual(initial, owner.initial_state())

    def test_same_issuer_wrong_request_and_wrong_access_are_not_this_operation(self):
        owner, packet, view = build("realm_shift")
        access, propose = RealmEngine.evaluate_access, RealmEngine.propose_shift
        def wrong_request(engine, request):
            return access(engine, replace(request, request_ref="other:request"))
        with patch.object(RealmEngine, "evaluate_access", wrong_request):
            self.rejects("POLICY_REJECTED", lambda: owner.reduce(owner.initial_state(), packet, view))
        def wrong_access(engine, original, *, proposal_ref):
            other = access(engine, replace(original.request, location_ref="other:location"))
            return propose(engine, other.value, proposal_ref=proposal_ref)
        with patch.object(RealmEngine, "propose_shift", wrong_access):
            self.rejects("POLICY_REJECTED", lambda: owner.reduce(owner.initial_state(), packet, view))

    def test_serialized_and_foreign_realm_results_cannot_supply_issuance(self):
        owner, packet, view = build("realm_shift")
        access = RealmEngine.evaluate_access
        def copied(engine, request):
            return copy.deepcopy(access(engine, request))
        with patch.object(RealmEngine, "evaluate_access", copied):
            self.rejects("POLICY_REJECTED", lambda: owner.reduce(owner.initial_state(), packet, view))

    def test_read_closure_is_derived_and_stale_body_or_head_refuses(self):
        owner, packet, view = build()
        self.assertEqual([x["component_id"] for x in owner.requirements(packet)["reads"]], ["component:branch", "component:player"])
        for change in (lambda v: v["components"].pop(),
                       lambda v: v["components"][0].update(head_digest="0" * 64),
                       lambda v: v["components"][1]["state"].update(player_id="player:other")):
            invalid = copy.deepcopy(view)
            change(invalid)
            self.rejects("POLICY_REJECTED", lambda: owner.reduce(owner.initial_state(), packet, invalid))

    def test_false_declared_condition_does_not_pass_by_catalog_presence(self):
        args, view, _ = inputs()
        change_record(args, "source:permission", lambda d: d["value"].update(value=False))
        changed = next(x for x in args[4] if x["ref"] == "source:permission")
        change_record(args, "condition:permission", lambda d: d.update(source_sha256=changed["sha256"]))
        owner, packet, view = ready(args, view)
        self.rejects("POLICY_REJECTED", lambda: owner.reduce(owner.initial_state(), packet, view))

    def test_before_mismatch_and_late_field_mismatch_leave_inputs_untouched(self):
        for kind in ("fact", "location"):
            args, view, _ = inputs(kind)
            if kind == "fact":
                args[5][0]["resolutions"][0]["before"]["token"] = "open"
            else:
                change_record(args, "mutation:one", lambda d: d["changed_fields"][0].update(field_path="arbitrary.path"))
            owner, packet, view = ready(args, view)
            initial = owner.initial_state()
            original = copy.deepcopy((initial, packet, view))
            self.rejects("POLICY_REJECTED", lambda: owner.reduce(initial, packet, view))
            self.assertEqual((initial, packet, view), original)

    def test_exact_genesis_fact_location_occupancy_subject_value_and_scope(self):
        for ref, mutation in (("genesis:gate", lambda r: r["document"].update(subject_ref="foreign")),
                              ("genesis:gate", lambda r: r["document"]["value"].update(token="open")),
                              ("genesis:gate", lambda r: r.update(scope=TruthScope(WORLD,"leaf_branch_state","branch:foreign").to_record())),
                              ("genesis:location:one", lambda r: r["document"]["value"].update(token="0"*64)),
                              ("genesis:occupancy", lambda r: r["document"].update(subject_ref="player:other"))):
            with self.subTest(ref=ref):
                args, _, _ = inputs()
                row = next(x for x in args[4] if x["ref"] == ref)
                mutation(row)
                row["sha256"] = digest(row["document"])
                args[2]["records"][ref] = copy.deepcopy(row)
                self.rejects("INVALID_POLICY", lambda: WorldLocationPolicy(*args))

    def test_immutable_anchor_and_scope_relabeling_are_refused(self):
        args, view, _ = inputs("location", leaf=True)
        args[5][0]["scope"]["subject_id"] = "branch:other"
        self.rejects("INVALID_POLICY", lambda: WorldLocationPolicy(*args))
        args, _, _ = inputs()
        args[2]["geography_sha256"] = "0" * 64
        self.rejects("INVALID_POLICY", lambda: WorldLocationPolicy(*args))

    def test_appendable_unused_catalog_does_not_change_identity_or_packet(self):
        args, view, _ = inputs()
        first, packet, _ = ready(args, view)
        args[4].append(source("unused:evidence"))
        second, again, _ = ready(args, view)
        self.assertEqual(first.policy_id, second.policy_id)
        self.assertEqual(packet, again)
        self.assertEqual(first.reduce(first.initial_state(), packet, view), second.reduce(second.initial_state(), again, view))

    def test_minor_action_uncovered_target_and_missing_role_refuse(self):
        for change in (lambda d: d.update(significance="minor_record"), lambda d: d.update(affected_entity_refs=[])):
            args, view, _ = inputs()
            change_record(args, "action:world", change)
            owner, packet, view = ready(args, view)
            self.rejects("POLICY_REJECTED", lambda: owner.reduce(owner.initial_state(), packet, view))
        owner, _, _ = build("location")
        self.rejects("UNAUTHORIZED_WRITER", lambda: owner.packet({"narrative_principal":"narrative:owner","realm_principal":None},"request","update:world"))

    def test_hostile_schemas_and_public_wire_inputs_use_stable_errors(self):
        args, _, _ = inputs()
        args[6]["source"]["type"] = 42
        self.rejects("INVALID_POLICY", lambda: WorldLocationPolicy(*args))
        owner, packet, view = build()
        for invalid in (None, [], True, 1, {}):
            with self.subTest(value=invalid):
                with self.assertRaises(JournalError):
                    owner.packet(invalid, "request", "update:world")
                with self.assertRaises(JournalError):
                    owner.reduce(owner.initial_state(), packet, invalid)

    def test_leaf_current_fact_stays_leaf(self):
        owner, packet, view = build(leaf=True)
        result = owner.reduce(owner.initial_state(), packet, view)
        self.assertEqual(result["scope"]["truth_scope"], "leaf_branch_state")
        self.assertEqual(owner.project_facts(result)["scope"], result["scope"])
        self.assertEqual(result["records"]["anchor:geography"]["scope"]["truth_scope"], "shared_worldstate")

    def test_leaf_realm_requires_actual_current_shared_owner_true_basis(self):
        owner, packet, view = build("realm_shift", leaf=True)
        self.rejects("POLICY_REJECTED", lambda: owner.reduce(owner.initial_state(), packet, view))
        for value in ("TRUE", "FALSE", "UNAVAILABLE"):
            args, view, _ = inputs("realm_shift", leaf=True)
            shared = shared_veil_basis(args, view, value)
            owner, packet, view = ready(args, view)
            self.assertIn(shared.policy_id, [x["owner_policy_id"] for x in owner.requirements(packet)["reads"]])
            if value == "TRUE":
                after = owner.reduce(owner.initial_state(), packet, view)
                self.assertEqual(after["occupancies"][0]["realm_id"], "realm:echo")
            else:
                self.rejects("POLICY_REJECTED", lambda: owner.reduce(owner.initial_state(), packet, view))

    def test_current_fact_condition_reads_value_not_just_slot_presence(self):
        args, view, _ = inputs("realm_shift", leaf=True)
        shared_veil_basis(args, view, "FALSE")
        change_record(args, "condition:shared-veil", lambda d:d.update(expected_value={"kind":"token","token":"TRUE"}))
        owner, packet, view = ready(args, view)
        self.rejects("POLICY_REJECTED", lambda: owner.reduce(owner.initial_state(), packet, view))

    def test_oversized_complete_result_refuses_after_valid_inputs_without_mutation(self):
        args, view, _ = inputs()
        refs = []
        for i in range(12):
            ref = "large:" + str(i)
            refs.append(ref)
            args[4].append(source(ref, value={"kind":"references","refs":[str(j).zfill(2)+"x"*120 for j in range(32)]}))
        change_record(args, "action:world", lambda d:d.update(source_refs=sorted(refs)))
        owner, packet, view = ready(args, view)
        state = owner.initial_state()
        original = copy.deepcopy((state, packet, view))
        self.rejects("VALUE_LIMIT", lambda:owner.reduce(state, packet, view))
        self.assertEqual((state, packet, view), original)

    def test_nonnull_event_from_actual_branch_owner_envelope_resolves(self):
        from tests.m4_branch_fixture import fork_case
        actual = fork_case()
        args, view, _ = inputs()
        rows = [actual["component"], actual["after_player"]]
        rows.sort(key=lambda x:x["component_id"])
        view["components"] = rows
        heads = [{k:v for k,v in row.items() if k != "state"} for row in rows]
        args[5][0]["source_read_vector_sha256"] = hashlib.sha256(_encode(heads)).hexdigest()
        args[5][0]["delta_ref"] = "delta:left"
        delta = next(x for x in args[4] if x["ref"] == "delta:one")
        delta["ref"] = "delta:left"
        delta["document"].update(delta_id="delta:left",current_leaf_branch_ref="branch:left",source_branch_event_ref="event:left")
        delta["sha256"] = digest(delta["document"])
        change_record(args,"action:world",lambda d:d.update(branch_ref="branch:left",resulting_worldstate_delta_refs=["delta:left"]))
        change_record(args,"resolution:one",lambda d:d.update(branch_head=heads[0],player_head=heads[1],delta_ref="delta:left"))
        owner, packet, view = ready(args,view)
        self.assertEqual(owner.reduce(owner.initial_state(),packet,view)["events"][0]["delta_ref"],"delta:left")
        altered = copy.deepcopy(view)
        altered["components"][0]["state"]["events"]["event:left"]["target_branch_id"]="branch:other"
        self.rejects("POLICY_REJECTED",lambda:owner.reduce(owner.initial_state(),packet,altered))

    def test_compensation_and_journal_replay_keep_original_effect(self):
        args, view, _ = inputs()
        originals = {x["ref"]:x for x in args[4]}
        for old,new in (("action:world","action:undo"),("resolution:one","resolution:undo"),("delta:one","delta:undo")):
            row=copy.deepcopy(originals[old]); row["ref"]=new; doc=row["document"]
            if old.startswith("action"):
                doc.update(action_trace_id=new,resulting_worldstate_delta_refs=["delta:undo"])
            elif old.startswith("resolution"):
                doc.update(resolution_id=new,delta_ref="delta:undo",action_refs=["action:undo"])
            else:
                doc.update(delta_id=new,source_resolution_payload="resolution:undo",sequence_id=1)
            row["sha256"]=digest(doc);args[4].append(row)
        inverse=copy.deepcopy(args[5][0]);inverse.update(update_ref="update:undo",effect_id="effect:undo",delta_ref="delta:undo",compensates_effect_id="effect:world")
        op=inverse["resolutions"][0];op["before"],op["after"]=op["after"],op["before"]
        args[5].append(inverse)
        owner,packet,view=ready(args,view)
        undo=owner.packet(packet["principals"],"request:undo","update:undo")
        reducer=lambda scope,state,p:owner.reduce(state,p,view)
        journal=CommitJournal(owner.scope,owner.policy_id,owner.initial_state(),reducer)
        journal.commit("request:world",0,packet)
        journal.commit("request:undo",1,undo)
        state=journal.state()
        self.assertEqual(state["facts"][0]["value"]["token"],"closed")
        self.assertEqual([e["effect_id"] for e in state["events"]],["effect:world","effect:undo"])
        raw,head=journal.checkpoint()
        restored=CommitJournal.load(raw,owner.scope,owner.policy_id,reducer,head)
        self.assertEqual(restored.checkpoint(),journal.checkpoint())

    def test_actual_legacy_overlay_source_object_binds_typed_leaf_access(self):
        args, view, _ = inputs("location",leaf=True)
        args[1]["mutable_rules"][0]["target_current"]["status"]="base"
        change_record(args,"location:one:open",lambda d:(d["current"].update(status="base"),d.update(source_mutation_ref="overlay:one")))
        change_record(args,"resolution:one",lambda d:d.update(location_mutation_refs=[]))
        change_record(args,"delta:one",lambda d:(d.update(location_mutation_refs=[]),d["mutations"][0].update(operation="append_ref")))
        op=args[5][0]["resolutions"][0];op.update(kind="overlay",overlay_ref="overlay:one");op.pop("mutation_ref")
        overlay={"schema_id":"ywe.location_branch_overlay.v1","version":"1.0.0","overlay_id":"overlay:one",
            "location_id":"location:one","branch_id":"branch:one","truth_scope":"leaf_branch_truth",
            "source_refs":{"worldstate_delta_refs":["delta:one"],"player_state_snapshot_ref":"component:player","location_state_record_ref":"location:one:initial"},
            "overlay_body":{"access_changes":["The gate is available in this branch."]},
            "validation":{"does_not_rewrite_base_ontology":True,"does_not_claim_shared_truth_without_delta":True,"is_runtime_generated_not_pregenerated_tree":True}}
        args[4].append(record("overlay:one","overlay",overlay,args[0]))
        owner,packet,view=ready(args,view)
        state=owner.reduce(owner.initial_state(),packet,view)
        self.assertEqual(state["records"]["location:one:open"]["document"]["current"]["access"][0]["state"],"open")
        self.assertEqual(state["scope"]["truth_scope"],"leaf_branch_state")
        change_record(args,"overlay:one",lambda d:d["source_refs"].update(player_state_snapshot_ref="player:foreign"))
        owner,packet,view=ready(args,view)
        self.rejects("POLICY_REJECTED",lambda:owner.reduce(owner.initial_state(),packet,view))

    def test_unused_unqualified_source_and_misclassified_mutation_are_refused(self):
        args,_,_=inputs()
        extra=source("unused:bad");extra["document"]["source_refs"]=["missing:source"];extra["sha256"]=digest(extra["document"])
        args[4].append(extra)
        self.rejects("INVALID_POLICY",lambda:WorldLocationPolicy(*args))
        args,view,_=inputs("location")
        change_record(args,"mutation:one",lambda d:d.update(mutation_kind="plane_pressure_shift"))
        owner,packet,view=ready(args,view)
        self.rejects("POLICY_REJECTED",lambda:owner.reduce(owner.initial_state(),packet,view))

    def test_realm_update_cannot_use_its_own_new_veil_value(self):
        args,view,_=inputs("realm_shift",veil="FALSE")
        args[5][0]["resolutions"].insert(0,{"kind":"fact","operation_id":"operation:veil","slot_id":"fact:veil",
            "before":{"kind":"token","token":"FALSE"},"after":{"kind":"token","token":"TRUE"},"condition_refs":["condition:permission"]})
        change_record(args,"delta:one",lambda d:d["mutations"].insert(0,{"operation_id":"operation:veil","domain":"local_world_condition",
            "operation":"commit_public_fact","target_ref":"fact:veil","evidence_refs":["condition:permission"]}))
        change_record(args,"action:world",lambda d:d.update(affected_entity_refs=["fact:veil","player:one"]))
        owner,packet,view=ready(args,view)
        original=owner.initial_state()
        self.rejects("POLICY_REJECTED",lambda:owner.reduce(original,packet,view))
        self.assertEqual(original,owner.initial_state())


if __name__ == "__main__":
    unittest.main()
