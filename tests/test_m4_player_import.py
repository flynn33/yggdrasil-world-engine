"""Imported player continuation, source ownership and pre-migration archive compatibility."""

import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from core.narrative_engine.origin_progression import OriginProgressionPolicy
from core.player_state import PlayerStateStore
from core.player_state_migration import PlayerStateMigration
from core.state_journal import JournalError, _object_bytes
from tests.m4_player_fixture import (
    PRINCIPAL, WORLD, PLAYER, configuration, consequence, document, evidence, record, reference,
)
from tests.m4_player_migration_fixture import build, configuration_for, inputs
from tests.test_m4_player_state import add_branch_transfer, add_compensation, manifestation


def add_update(result, migration, args, name, operations, *, advance=False, source="narrative_engine",
               action_kind="choice", affected=()):
    args = copy.copy(list(args))
    args[4] = copy.deepcopy(args[4])
    args[5] = copy.deepcopy(args[5])
    args[6] = copy.deepcopy(args[6])
    prior = result["origin_baseline"]["current_phase"]
    target = "memory_recovery" if advance else prior
    update_ref, evidence_ref = "update:" + name, "origin:" + name
    bundle = evidence(evidence_ref, update_ref, prior, target, 1, "advance" if advance else "remember")
    bundle["actions"][0].update(action_kind=action_kind, affected_entity_refs=list(affected))
    principal = PRINCIPAL if source == "narrative_engine" else source + ":owner"
    args[4].setdefault(principal, {"source_system": source, "operations": ["origin"]})
    if "context" not in args[4][principal]["operations"]:
        args[4][principal]["operations"].append("context")
    args[5].append(consequence("consequence:" + name, update_ref, bundle))
    args[6].append({"update_ref": update_ref, "world_id": WORLD, "player_id": PLAYER,
        "branch_ref": args[3]["current_leaf_branch_ref"], "source_system": source,
        "operations": [{"kind": "origin", "evidence_ref": evidence_ref}] + operations,
        "evidence_refs": ["evidence:play"], "consequence_ref": "consequence:" + name,
        "provenance": copy.deepcopy(bundle["provenance"])})
    r = migration.resolution()
    origin_grants = {key: (["remember", "advance"] if grant["source_system"] == "narrative_engine" else ["remember"])
                     for key, grant in args[4].items()}
    sources = [args[8].evidence("origin:first"), args[8].evidence("origin:second"), bundle]
    args[8] = OriginProgressionPolicy.from_baseline(result["origin_baseline"], WORLD, PLAYER,
        r["origin_profile"], r["creation"], origin_grants, sources, args[7]["action"], args[7]["memory"])
    return args, principal, update_ref, bundle


def context_change(args, field, value, phase="first_stirrings", resolution=None):
    ref = "context:" + field
    document = {"field": field, "previous_value": copy.deepcopy(args[3]["runtime_context"][field]),
                "value": value, "phase": phase}
    if resolution is not None:
        document["resolution"] = resolution
    args[5].append(record(ref, "context", document))
    return {"kind": "context", "context_ref": ref, "condition_refs": ["evidence:play"]}


def imported_branch_transfer(shared=False):
    raw, sources, targets, resolution, old = inputs("historical_record_v1", True)
    ref = resolution["spine"]["runtime_context"]["active_realm_form_ref"]
    form = next(row for row in resolution["records"] if row["ref"] == ref)
    form["document"].update(truth_scope="shared_worldstate" if shared else "leaf_branch_state",
                            subject_id=WORLD if shared else form["branch_ref"])
    migration = PlayerStateMigration("historical_record_v1", sources, targets, resolution)
    result = migration.migrate(raw)
    args = list(configuration_for(result, resolution, targets, old))
    add_branch_transfer(args)
    bundle = args[8].evidence("origin:branch")
    args[8] = OriginProgressionPolicy.from_baseline(result["origin_baseline"], WORLD, PLAYER,
        resolution["origin_profile"], resolution["creation"], {PRINCIPAL: ["advance", "remember"]},
        [args[8].evidence("origin:first"), args[8].evidence("origin:second"), bundle],
        args[7]["action"], args[7]["memory"])
    if not shared:
        ref = resolution["spine"]["runtime_context"]["active_realm_form_ref"]
        form = copy.deepcopy(next(row for row in args[5] if row["ref"] == ref))
        form.update(ref="realm:physical:two", branch_ref="branch:two")
        form["document"]["subject_id"] = "branch:two"
        args[5].append(form)
        args[6][-1]["operations"][1]["next_realm_form_ref"] = form["ref"]
    return raw, migration, result, args


class PlayerImportTests(unittest.TestCase):
    def rejected(self, owner, principal, update_ref, request="request:new"):
        before = owner.checkpoint()
        with self.assertRaises(JournalError):
            owner.publish(owner.writer(principal), request, 0, update_ref)
        self.assertEqual(before, owner.checkpoint())

    def test_both_formats_both_lifecycles_are_exact_new_genesis(self):
        for adapter in ("closed_reference_v1", "historical_record_v1"):
            for continuing in (False, True):
                with self.subTest(adapter=adapter, continuing=continuing):
                    raw, migration, result, args = build(adapter, continuing)
                    owner = PlayerStateStore.from_migration(result, migration, raw, *args)
                    self.assertEqual(result["baseline"], owner.state())
                    archive, head = owner.checkpoint()
                    self.assertEqual([], json.loads(archive)["entries"])
                    restored = PlayerStateStore.load_migrated(archive, head, result, migration, raw, *args)
                    self.assertEqual((archive, head), restored.checkpoint())

    def test_checked_in_examples_are_actual_migration_and_resolution_outputs(self):
        raw, migration, result, args = build("historical_record_v1", True)
        self.assertEqual(document("examples/state_journal/player_migration.example.json"), result)
        args, principal, update, bundle = add_update(result, migration, args, "resolve", [],
            source="quest_engine", action_kind="quest_resolution", affected=["quest:second"])
        args[6][-1]["operations"].append(context_change(args, "active_quest_refs", ["quest:first"], resolution={
            "removed_refs": ["quest:second"], "action_refs": [bundle["actions"][0]["action_trace_id"]],
            "reason_refs": ["evidence:play"], "disposition": "resolved"}))
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        owner.publish(owner.writer(principal), "request:resolve", 0, update)
        self.assertEqual(document("examples/state_journal/player_context_update.example.json"), args[6][-1])
        self.assertEqual(document("examples/state_journal/player_imported_continuation.example.json"), owner.state())

    def test_continuing_import_retains_history_context_and_replays_new_memory(self):
        for adapter in ("closed_reference_v1", "historical_record_v1"):
            raw, migration, result, args = build(adapter, True)
            owner = PlayerStateStore.from_migration(result, migration, raw, *args)
            before = owner.state()
            receipt = owner.publish(owner.writer(PRINCIPAL), "request:new", 0, "update:second")
            after = owner.state()
            self.assertEqual(before["import_baseline"], after["import_baseline"])
            self.assertEqual(before["spine"]["memory_refs"]["player_memory_record_refs"],
                             after["spine"]["memory_refs"]["player_memory_record_refs"][:-1])
            if adapter == "historical_record_v1":
                old, new = before["spine"]["runtime_context"], after["spine"]["runtime_context"]
                self.assertEqual(old["active_quest_refs"], new["active_quest_refs"])
                self.assertEqual(old["unresolved_tension_refs"], new["unresolved_tension_refs"])
                self.assertEqual(old["sequence_id"] + 1, new["sequence_id"])
                self.assertEqual("origin:second:action:0", new["last_player_action_trace_ref"])
            archive, head = owner.checkpoint()
            restored = PlayerStateStore.load_migrated(archive, head, result, migration, raw, *args)
            self.assertEqual((archive, head), restored.checkpoint())
            with patch.object(OriginProgressionPolicy, "reduce", side_effect=AssertionError("retry reduced")):
                self.assertEqual(receipt, restored.publish(restored.writer(PRINCIPAL), "request:new", 0, "update:second"))

    def test_tampered_result_false_verification_and_source_cannot_activate(self):
        raw, migration, result, args = build()
        changed = copy.deepcopy(result)
        changed["baseline"]["spine"]["player_id"] = "player:other"
        for candidate, source in ((changed, raw), (result, raw + b" ")):
            with self.assertRaisesRegex(JournalError, "INVALID_MIGRATION"):
                PlayerStateStore.from_migration(candidate, migration, source, *args)
        with patch.object(type(migration), "verify", return_value=False):
            with self.assertRaisesRegex(JournalError, "INVALID_MIGRATION"):
                PlayerStateStore.from_migration(result, migration, raw, *args)

    def test_old_constructor_refuses_new_origin_policy_even_with_old_spine(self):
        raw, migration, result, args = build()
        old = list(configuration())
        old[8] = args[8]
        with self.assertRaisesRegex(JournalError, "INVALID_POLICY"):
            PlayerStateStore(*old)

    def test_import_rejects_changed_qualified_record_and_profile(self):
        raw, migration, result, args = build()
        modified = list(args)
        modified[5] = copy.deepcopy(args[5])
        modified[5][0]["provenance"]["diagnostic_ref"] = "diagnostic:changed"
        with self.assertRaisesRegex(JournalError, "INVALID_MIGRATION"):
            PlayerStateStore.from_migration(result, migration, raw, *modified)
        modified = list(args)
        modified[2] = copy.deepcopy(args[2])
        modified[2]["profile_id"] = "profile:changed"
        with self.assertRaisesRegex(JournalError, "INVALID_MIGRATION"):
            PlayerStateStore.from_migration(result, migration, raw, *modified)

    def test_unused_catalog_extension_preserves_checkpoint(self):
        raw, migration, result, args = build()
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        extended = list(args)
        extended[5] = args[5] + [reference("unused:future", "future_generation_bias_refs")]
        archive, head = owner.checkpoint()
        restored = PlayerStateStore.load_migrated(archive, head, result, migration, raw, *extended)
        self.assertEqual((archive, head), restored.checkpoint())

    def test_imported_request_update_and_effect_identities_remain_consumed(self):
        raw, migration, result, args = build(continuing=True)
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        self.rejected(owner, PRINCIPAL, "update:second", "request:historical:first")
        self.rejected(owner, PRINCIPAL, "update:first")
        modified = list(args)
        modified[5] = copy.deepcopy(args[5])
        first = next(row["document"] for row in args[5] if row["ref"] == "consequence:first")
        second = next(row["document"] for row in modified[5] if row["ref"] == "consequence:second")
        second.update(consequence_id=first["consequence_id"], effect_id=first["effect_id"])
        owner = PlayerStateStore.from_migration(result, migration, raw, *modified)
        self.rejected(owner, PRINCIPAL, "update:second")

    def test_phase_advance_requires_explicit_confidence_and_accepts_equal_numeric_value(self):
        raw, migration, result, original = build("historical_record_v1", True)
        args, principal, update, bundle = add_update(result, migration, original, "advance", [], advance=True)
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        self.rejected(owner, principal, update)
        operation = context_change(args, "phase_confidence", {"coefficient": "875", "exponent": -3}, "memory_recovery")
        args[6][-1]["operations"].append(operation)
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        owner.publish(owner.writer(principal), "request:advance", 0, update)
        state = owner.state()
        self.assertEqual("memory_recovery", state["records"]["origin:one"]["document"]["current_phase"])
        archive, head = owner.checkpoint()
        self.assertEqual((archive, head), PlayerStateStore.load_migrated(archive, head, result, migration, raw, *args).checkpoint())

    def test_named_context_owner_is_required(self):
        raw, migration, result, original = build("historical_record_v1", True)
        args, principal, update, bundle = add_update(result, migration, original, "quest", [])
        args[5].append(reference("quest:third", "active_quest_refs"))
        args[6][-1]["operations"].append(context_change(args, "active_quest_refs", ["quest:second", "quest:first", "quest:third"]))
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        self.rejected(owner, principal, update)

    def test_quest_removal_requires_resolution_actions_and_reasons(self):
        raw, migration, result, original = build("historical_record_v1", True)
        args, principal, update, bundle = add_update(result, migration, original, "resolve", [],
            source="quest_engine", action_kind="quest_resolution", affected=["quest:second"])
        operation = context_change(args, "active_quest_refs", ["quest:first"])
        args[6][-1]["operations"].append(operation)
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        self.rejected(owner, principal, update)
        context = args[5][-1]["document"]
        context["resolution"] = {"removed_refs": ["quest:second"],
            "action_refs": [bundle["actions"][0]["action_trace_id"]],
            "reason_refs": ["evidence:play"], "disposition": "resolved"}
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        owner.publish(owner.writer(principal), "request:resolve", 0, update)
        self.assertEqual(["quest:first"], owner.state()["spine"]["runtime_context"]["active_quest_refs"])
        self.assertIn(operation["context_ref"], owner.state()["records"])
        for key, value in (("removed_refs", ["quest:first"]), ("action_refs", ["action:unknown"]), ("reason_refs", ["reason:unknown"])):
            invalid = copy.copy(args)
            invalid[5] = copy.deepcopy(args[5])
            invalid[5][-1]["document"]["resolution"][key] = value
            owner = PlayerStateStore.from_migration(result, migration, raw, *invalid)
            self.rejected(owner, principal, update)

    def test_malformed_context_values_fail_at_configuration_boundary(self):
        raw, migration, result, original = build("historical_record_v1", True)
        for value in (7, None, True, {}, [7]):
            args, principal, update, bundle = add_update(result, migration, original, "bad", [])
            args[6][-1]["operations"].append(context_change(args, "narrative_memory_refs", value))
            with self.assertRaisesRegex(JournalError, "INVALID_MIGRATION"):
                PlayerStateStore.from_migration(result, migration, raw, *args)

    def test_awakening_fragment_cannot_change_to_shared_truth_scope(self):
        raw, sources, targets, resolution, old = inputs("historical_record_v1", True)
        fragment = {"fragment_id": "fragment:one", "fragment_kind": "memory", "source_refs": ["evidence:play"]}
        celestial = next(row for row in resolution["records"] if row["ref"] == "celestial:suspected")
        celestial["document"]["known_fragments"] = [fragment]
        migration = PlayerStateMigration("historical_record_v1", sources, targets, resolution)
        result = migration.migrate(raw)
        original = configuration_for(result, resolution, targets, old)
        args, principal, update, bundle = add_update(result, migration, original, "fragment", [])
        shared = reference("awakening:shared", "awakening_fragments", "shared_worldstate", WORLD)
        shared["document"]["source_sha256"] = hashlib.sha256(_object_bytes(fragment)).hexdigest()
        args[5].append(shared)
        args[6][-1]["operations"].append(context_change(args, "awakening_fragments", ["awakening:shared"]))
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        self.rejected(owner, principal, update)

    def test_realm_form_requires_configured_name_even_with_qualified_reference(self):
        raw, migration, result, original = build("historical_record_v1", True)
        args, principal, update, bundle = add_update(result, migration, original, "realm", [], source="realm_engine")
        args[5].append(reference("unconfigured:form", "active_realm_form", "leaf_branch_state", args[3]["current_leaf_branch_ref"]))
        args[6][-1]["operations"].append(context_change(args, "active_realm_form", "unconfigured:form"))
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        self.rejected(owner, principal, update)

    def test_dismissed_imported_manifestation_identity_cannot_reapply_by_alias(self):
        raw, sources, targets, resolution, old = inputs(continuing=True)
        event = manifestation()
        resolution["records"].append(record("manifestation:historical", "manifestation", event))
        resolution["consumed_manifestation_event_ids"] = [event["manifestation_event_id"]]
        resolution["manifestation_bindings"] = [{"manifestation_event_id": event["manifestation_event_id"],
                                                 "record_ref": "manifestation:historical"}]
        migration = PlayerStateMigration("closed_reference_v1", sources, targets, resolution)
        result = migration.migrate(raw)
        original = configuration_for(result, resolution, targets, old)
        args, principal, update, bundle = add_update(result, migration, original, "manifest", [
            {"kind": "manifest", "event_ref": "manifestation:alias"}])
        args[5].append(record("manifestation:alias", "manifestation", event))
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        self.rejected(owner, principal, update)

    def test_same_realm_name_survives_qualified_branch_transfer_and_replay(self):
        for shared in (False, True):
            with self.subTest(shared=shared):
                raw, migration, result, args = imported_branch_transfer(shared)
                owner = PlayerStateStore.from_migration(result, migration, raw, *args)
                before = owner.state()
                receipt = owner.publish(owner.writer(PRINCIPAL), "request:branch", 0, "update:branch")
                after = owner.state()
                self.assertEqual("branch:two", after["spine"]["current_leaf_branch_ref"])
                self.assertEqual("physical", after["spine"]["runtime_context"]["active_realm_form"])
                old_ref = before["spine"]["runtime_context"]["active_realm_form_ref"]
                self.assertEqual(old_ref if shared else "realm:physical:two",
                                 after["spine"]["runtime_context"]["active_realm_form_ref"])
                self.assertEqual(before["records"][old_ref], after["records"][old_ref])
                archive, head = owner.checkpoint()
                restored = PlayerStateStore.load_migrated(archive, head, result, migration, raw, *args)
                self.assertEqual((archive, head), restored.checkpoint())
                with patch.object(OriginProgressionPolicy, "reduce", side_effect=AssertionError("retry reduced")):
                    self.assertEqual(receipt, restored.publish(restored.writer(PRINCIPAL), "request:branch", 0, "update:branch"))

    def test_branch_transfer_cannot_reuse_old_leaf_form_binding(self):
        raw, migration, result, args = imported_branch_transfer()
        del args[6][-1]["operations"][1]["next_realm_form_ref"]
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        self.rejected(owner, PRINCIPAL, "update:branch")

    def test_branch_binding_cannot_change_realm_meaning_or_scope(self):
        for field, value in (("form_name", "mental"), ("plane_id", "P4_Mental"),
                             ("subject_id", "branch:foreign")):
            with self.subTest(field=field):
                raw, migration, result, args = imported_branch_transfer()
                form = next(row for row in args[5] if row["ref"] == "realm:physical:two")
                form["document"][field] = value
                if field == "subject_id":
                    form["branch_ref"] = value
                owner = PlayerStateStore.from_migration(result, migration, raw, *args)
                self.rejected(owner, PRINCIPAL, "update:branch")

    def test_realm_owned_context_changes_name_and_binding_together(self):
        raw, migration, result, original = build("historical_record_v1", True)
        args, principal, update, bundle = add_update(result, migration, original, "realm-change", [], source="realm_engine")
        ref = args[3]["runtime_context"]["active_realm_form_ref"]
        form = copy.deepcopy(next(row for row in args[5] if row["ref"] == ref))
        form["ref"] = "realm:mental:one"
        form["document"].update(form_name="mental", plane_id="P4_Mental")
        args[5].append(form)
        args[6][-1]["operations"].extend([
            context_change(args, "active_realm_form", "mental"),
            context_change(args, "active_realm_form_ref", form["ref"])])
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        owner.publish(owner.writer(principal), "request:realm-change", 0, update)
        self.assertEqual("mental", owner.state()["spine"]["runtime_context"]["active_realm_form"])
        archive, head = owner.checkpoint()
        self.assertEqual((archive, head), PlayerStateStore.load_migrated(archive, head, result, migration, raw, *args).checkpoint())

    def test_future_realm_binding_requires_an_existing_qualified_plane(self):
        raw, sources, targets, resolution, old = inputs("historical_record_v1", True)
        resolution["realm_name_map"]["mappings"]["newform"] = "P999_Nonexistent"
        migration = PlayerStateMigration("historical_record_v1", sources, targets, resolution)
        result = migration.migrate(raw)
        original = configuration_for(result, resolution, targets, old)
        args, principal, update, bundle = add_update(result, migration, original, "bad-plane", [], source="realm_engine")
        ref = args[3]["runtime_context"]["active_realm_form_ref"]
        form = copy.deepcopy(next(row for row in args[5] if row["ref"] == ref))
        form["ref"] = "realm:nonexistent"
        form["document"].update(form_name="newform", plane_id="P999_Nonexistent")
        args[5].append(form)
        args[6][-1]["operations"].extend([
            context_change(args, "active_realm_form", "newform"),
            context_change(args, "active_realm_form_ref", form["ref"])])
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        self.rejected(owner, principal, update)

    def test_retained_imported_action_supports_new_memory_without_new_action_credit(self):
        raw, migration, result, original = build(continuing=True)
        args, principal, update, bundle = add_update(result, migration, original, "remember-old", [])
        action = copy.deepcopy(result["origin_baseline"]["actions"][0])
        bundle["actions"] = [action]
        bundle["memories"][0]["source_action_trace_ref"] = action["action_trace_id"]
        next(row for row in args[5] if row["ref"] == "consequence:remember-old")["document"]["action_refs"] = [action["action_trace_id"]]
        r = migration.resolution()
        args[8] = OriginProgressionPolicy.from_baseline(result["origin_baseline"], WORLD, PLAYER,
            r["origin_profile"], r["creation"], {PRINCIPAL: ["advance", "remember"]}, [bundle],
            args[7]["action"], args[7]["memory"])
        owner = PlayerStateStore.from_migration(result, migration, raw, *args)
        owner.publish(owner.writer(principal), "request:remember-old", 0, update)
        origin = owner.state()["records"]["origin:one"]["document"]
        self.assertEqual(result["origin_baseline"]["actions"], origin["actions"])
        self.assertEqual(3, len(origin["memories"]))
        self.assertEqual([], origin["advances"])


class PreMigrationArchiveCompatibilityTests(unittest.TestCase):
    def test_actual_pre_migration_player_archive_hashes_remain_exact(self):
        # Captured from clean 59cdd141 before imported-state implementation.
        cases = [([], None, "93b724f8c92b36a573dda4b7aecf3c9ab5200738ea2714a76035d2cf2d69aad0"),
            (["first"], None, "eebf683642c972b23b44903965ce62ae9d080189ec9e63a81efb9b11ca160c6c"),
            (["first", "second"], None, "aca7c2647bdf9b6093da7f3b474ccbfbf48b2f241ffa708b87a457320ed38c18"),
            (["first", "second", "compensation"], add_compensation, "ee5a0dbcb19b7edf06b12ddd3100b279bf7403a442ffd5ab465c114ce8546862"),
            (["first", "branch"], add_branch_transfer, "d92a5af265b7ce99b4dd0d63ce04d39a0e9fbeecd2dcefb0ee403557fe49dad6")]
        for requests, prepare, digest in cases:
            with self.subTest(requests=requests):
                args = list(configuration())
                if prepare:
                    prepare(args)
                owner = PlayerStateStore(*args)
                for revision, name in enumerate(requests):
                    owner.publish(owner.writer(PRINCIPAL), "request:" + name, revision, "update:" + name)
                archive, head = owner.checkpoint()
                self.assertEqual(digest, hashlib.sha256(archive).hexdigest())
                self.assertEqual((archive, head), PlayerStateStore.load(archive, head, *args).checkpoint())


if __name__ == "__main__":
    unittest.main()
