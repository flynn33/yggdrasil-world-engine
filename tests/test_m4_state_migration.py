"""Exact legacy resonance conversion, complete preservation and replay evidence."""

import copy
from decimal import Decimal, Inexact, localcontext
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from core.state_journal import CommitJournal, TruthScope
from core.state_migration import MigrationError, StateMigration


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = {
    "plane_attunement_state": "plane_attunement_state_mixed_shadow_mental_causal.example.json",
    "bloodline_resonance_state": "bloodline_resonance_ravenson_seed.example.json",
    "wolf_resonance_summary": "wolf_resonance_summary_balanced.example.json",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def configured(stem):
    plans = json.loads((ROOT / "data/validation/m4_resonance_migration_plans.json").read_text(encoding="utf-8"))
    plan = next(p for p in plans["plans"] if p["migration_id"] == stem + ".v1_to_v2")
    source = json.loads((ROOT / f"data/schemas/{stem}_schema.json").read_text(encoding="utf-8"))
    target = json.loads((ROOT / f"data/schemas/m4_{stem}_schema.json").read_text(encoding="utf-8"))
    return plan, source, target


def source_bytes(stem):
    return (ROOT / "examples/player_runtime_state" / FIXTURES[stem]).read_bytes()


def at_pointer(value, pointer):
    for segment in pointer.split("/")[1:]:
        segment = segment.replace("~1", "/").replace("~0", "~")
        value = value[int(segment)] if type(value) is list else value[segment]
    return value


class StateMigrationTests(unittest.TestCase):
    def setUp(self):
        self.plan, self.source_schema, self.target_schema = configured("bloodline_resonance_state")
        self.owner = StateMigration(self.plan, self.source_schema, self.target_schema)
        self.raw = source_bytes("bloodline_resonance_state")

    def assert_code(self, code, action):
        with self.assertRaises(MigrationError) as caught:
            action()
        self.assertEqual(code, caught.exception.code)

    def with_score(self, token):
        self.assertEqual(self.raw.count(b'"score": 0.42'), 1)
        return self.raw.replace(b'"score": 0.42', b'"score": ' + token)

    def test_all_three_real_fixtures_preserve_every_other_field_and_exact_scores(self):
        for stem in FIXTURES:
            with self.subTest(stem=stem):
                plan, source_schema, target_schema = configured(stem)
                owner = StateMigration(plan, source_schema, target_schema)
                raw = source_bytes(stem)
                before = json.loads(raw, parse_float=Decimal)
                Draft202012Validator(source_schema).validate(before)
                result = owner.migrate(raw)
                Draft202012Validator(target_schema).validate(result["target"])
                restored = copy.deepcopy(result["target"])
                for row in result["conversions"]:
                    expected = at_pointer(before, row["source_pointer"])
                    self.assertEqual(Decimal(str(expected)), Decimal(row["target_q6"]) / Decimal(1000000))
                    parent_path, _, destination = row["target_pointer"].rpartition("/")
                    parent = at_pointer(restored, parent_path)
                    del parent[destination]
                    original_key = row["source_pointer"].rsplit("/", 1)[1]
                    parent[original_key] = expected
                restored["schema_id"], restored["schema_version"] = before["schema_id"], before["schema_version"]
                self.assertEqual(before, restored)
                self.assertTrue(owner.verify(raw, result))
                self.assertEqual(result["source_sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(result["target_sha256"], hashlib.sha256(canonical(result["target"])).hexdigest())
                self.assertEqual(raw, source_bytes(stem))

    def test_zero_one_one_tick_trailing_zeros_and_exponents_are_exact(self):
        for token, expected in ((b"0", 0), (b"-0.000000", 0), (b"1", 1000000),
                                (b"1.0000000", 1000000), (b"1e-6", 1),
                                (b"100e-8", 1), (b"4.200000E-1", 420000),
                                (b"0.999999", 999999), (b"0e-1024", 0)):
            with self.subTest(token=token):
                result = self.owner.migrate(self.with_score(token))
                self.assertEqual(result["target"]["signals"][0]["score_q6"], expected)

    def test_precision_outside_integer_millionths_never_rounds(self):
        for token in (b"0.0000001", b"0.9999999", b"1e-1024", b"0.42000000000000000000000000001"):
            self.assert_code("UNREPRESENTABLE_SCORE", lambda: self.owner.migrate(self.with_score(token)))

    def test_conversion_does_not_depend_on_decimal_precision_or_traps(self):
        expected = self.owner.migrate(self.with_score(b"0.123456"))
        with localcontext() as context:
            context.prec = 2
            context.traps[Inexact] = True
            self.assertEqual(expected, self.owner.migrate(self.with_score(b"0.123456")))
            self.assert_code("UNREPRESENTABLE_SCORE", lambda: self.owner.migrate(self.with_score(b"0.1234561")))

    def test_invalid_numeric_type_range_and_nonfinite_values_refuse(self):
        for token in (b"true", b"null", b'"0.42"', b"[]", b"-0.01", b"1.000001", b"NaN", b"Infinity"):
            self.assert_code("INVALID_SOURCE", lambda: self.owner.migrate(self.with_score(token)))

    def test_numeric_lexeme_and_exponent_limits_refuse_before_conversion(self):
        self.assert_code("MIGRATION_LIMIT", lambda: self.owner.migrate(self.with_score(b"0." + b"0" * 127)))
        for token in (b"0e-1025", b"0e1025", b"9007199254740992"):
            self.assert_code("INVALID_SOURCE", lambda: self.owner.migrate(self.with_score(token)))

    def test_duplicate_keys_invalid_utf8_surrogates_and_truncation_refuse(self):
        variants = (self.raw.replace(b'"score": 0.42', b'"score": 0.42, "score": 0.5'),
                    self.raw[:-1].rstrip()[:-1], b"\xff", self.raw.replace(b'"ravenson"', b'"\\ud800"'))
        for raw in variants:
            self.assert_code("INVALID_SOURCE", lambda: self.owner.migrate(raw))

    def test_missing_fields_unknown_fields_and_versions_refuse(self):
        source = json.loads(self.raw)
        for field in source:
            if field not in self.source_schema["required"]:
                continue
            changed = dict(source)
            del changed[field]
            self.assert_code("INVALID_SOURCE", lambda: self.owner.migrate(canonical(changed)))
        for field, value in (("schema_version", "0.2.0"), ("schema_id", "wrong.v1"), ("extra", True)):
            self.assert_code("INVALID_SOURCE", lambda: self.owner.migrate(canonical({**source, field: value})))

    def test_optional_absence_and_empty_lists_are_preserved_without_defaults(self):
        source = json.loads(self.raw)
        source.pop("forbidden")
        source.pop("dominant_bloodline_refs")
        source["signals"] = []
        result = self.owner.migrate(canonical(source))
        self.assertNotIn("forbidden", result["target"])
        self.assertNotIn("dominant_bloodline_refs", result["target"])
        self.assertEqual(result["target"]["signals"], [])
        self.assertEqual(result["conversions"], [])

    def test_output_plan_and_schema_aliases_are_isolated(self):
        before = self.owner.migrate(self.raw)
        self.plan["rules"].clear()
        self.source_schema.clear()
        self.target_schema.clear()
        damaged = self.owner.migrate(self.raw)
        damaged["target"]["signals"][0]["source_refs"].clear()
        damaged["conversions"].clear()
        self.assertEqual(before, self.owner.migrate(self.raw))

    def test_schema_digests_and_document_ids_must_match(self):
        for key in ("source_schema_sha256", "target_schema_sha256", "source_document_id", "target_document_id"):
            plan = copy.deepcopy(self.plan)
            plan[key] = "wrong"
            self.assert_code("INVALID_PLAN", lambda: StateMigration(plan, self.source_schema, self.target_schema))
        schema = copy.deepcopy(self.source_schema)
        schema["title"] = "changed schema bytes"
        self.assert_code("INVALID_PLAN", lambda: StateMigration(self.plan, schema, self.target_schema))

    def test_references_are_rejected_even_when_supplied_schema_hash_matches(self):
        for key in ("$ref", "$dynamicRef"):
            schema = {**self.source_schema, key: "https://unavailable.invalid/schema"}
            plan = {**self.plan, "source_schema_sha256": hashlib.sha256(canonical(schema)).hexdigest()}
            self.assert_code("INVALID_PLAN", lambda: StateMigration(plan, schema, self.target_schema))

    def test_closed_plan_rule_limits_and_duplicate_destinations(self):
        bad = [{**self.plan, "extra": True}, {**self.plan, "rules": []},
               {**self.plan, "rules": self.plan["rules"] * 33}]
        for change in ({"source_field": "schema_id"}, {"target_field": "score"},
                       {"parent_path": ["signals"] * 9}, {"extra": True}):
            bad.append({**self.plan, "rules": [{**self.plan["rules"][0], **change}]})
        bad.append({**self.plan, "rules": self.plan["rules"] * 2})
        for plan in bad:
            self.assert_code("INVALID_PLAN", lambda: StateMigration(plan, self.source_schema, self.target_schema))

    def test_missing_conversion_path_and_invalid_target_do_not_return_partial_state(self):
        plan = copy.deepcopy(self.plan)
        plan["rules"][0]["parent_path"] = ["missing"]
        owner = StateMigration(plan, self.source_schema, self.target_schema)
        self.assert_code("INVALID_SOURCE", lambda: owner.migrate(self.raw))
        plan["rules"][0]["parent_path"] = ["signals", "*"]
        plan["rules"][0]["target_field"] = "wrong_score"
        owner = StateMigration(plan, self.source_schema, self.target_schema)
        self.assert_code("INVALID_TARGET", lambda: owner.migrate(self.raw))
        self.assertTrue(self.owner.verify(self.raw, self.owner.migrate(self.raw)))

    def test_tampered_result_or_different_source_never_verifies(self):
        result = self.owner.migrate(self.raw)
        for field in ("migration_id", "plan_sha256", "source_sha256", "target_sha256"):
            self.assertFalse(self.owner.verify(self.raw, {**result, field: "wrong"}))
        changed = copy.deepcopy(result)
        changed["target"]["signals"][0]["score_q6"] += 1
        self.assertFalse(self.owner.verify(self.raw, changed))
        changed = copy.deepcopy(result)
        changed["conversions"][0]["source_decimal"] = "0.43"
        self.assertFalse(self.owner.verify(self.raw, changed))
        self.assertFalse(self.owner.verify(self.raw + b" ", result))
        self.assertFalse(self.owner.verify(self.raw, None))

    def test_bounded_input_depth_node_count_and_raw_size(self):
        self.assert_code("MIGRATION_LIMIT", lambda: self.owner.migrate(b" " * 65537))
        self.assert_code("INVALID_SOURCE", lambda: self.owner.migrate(self.raw.decode()))
        nested = {}
        for _ in range(33):
            nested = {"x": nested}
        self.assert_code("MIGRATION_LIMIT", lambda: self.owner.migrate(canonical(nested)))
        self.assert_code("MIGRATION_LIMIT", lambda: self.owner.migrate(canonical([0] * 4097)))

    def test_migrated_records_persist_and_replay_without_float_conversion(self):
        for stem in FIXTURES:
            owner = StateMigration(*configured(stem))
            source = source_bytes(stem)
            migration = owner.migrate(source)
            def reducer(scope, state, packet):
                if not owner.verify(source, packet):
                    raise ValueError("invalid migration")
                return packet["target"]
            scope = TruthScope("world", "player_state", "player")
            journal = CommitJournal(scope, "test.migration.v1", {}, reducer)
            receipt = journal.commit("migration", 0, migration)
            raw, head = journal.checkpoint()
            restored = CommitJournal.load(raw, scope, "test.migration.v1", reducer, head)
            self.assertEqual(migration["target"], restored.state())
            self.assertEqual((raw, head), restored.checkpoint())
            self.assertEqual(receipt, restored.commit("migration", 0, migration))

    def test_conversion_capacity_exact_limit_and_one_over(self):
        source, target = copy.deepcopy(self.source_schema), copy.deepcopy(self.target_schema)
        for schema, field in ((source, "score"), (target, "score_q6")):
            item = schema["properties"]["signals"]["items"]
            item["required"] = [field]
            item["properties"] = {field: item["properties"][field]}
        plan = {**self.plan, "source_schema_sha256": hashlib.sha256(canonical(source)).hexdigest(),
                "target_schema_sha256": hashlib.sha256(canonical(target)).hexdigest()}
        owner = StateMigration(plan, source, target)
        value = {"schema_id": plan["source_schema_id"], "schema_version": "0.1.0",
                 "source_refs": [], "signals": [{"score": 1}] * 256}
        self.assertEqual(len(owner.migrate(canonical(value))["conversions"]), 256)
        value["signals"].append({"score": 1})
        self.assert_code("MIGRATION_LIMIT", lambda: owner.migrate(canonical(value)))

    def test_oversize_result_does_not_clip_preserved_fields(self):
        source = json.loads(self.raw)
        source["source_refs"] = [""]
        source["source_refs"] = ["x" * (65500 - len(canonical(source)))]
        raw = canonical(source)
        self.assertEqual(len(raw), 65500)
        expected = self.owner.migrate(self.raw)
        expected["target"]["source_refs"] = source["source_refs"]
        self.assertLessEqual(len(canonical(expected["target"])), 65536)
        self.assertGreater(len(canonical(expected)), 65536)
        self.assert_code("MIGRATION_LIMIT", lambda: self.owner.migrate(raw))

    def test_rejected_migration_cannot_replace_existing_journal_state(self):
        from core.state_journal import JournalError
        result = self.owner.migrate(self.raw)
        def reducer(scope, state, packet):
            if not self.owner.verify(self.raw, packet):
                raise ValueError("unverified migration")
            return packet["target"]
        journal = CommitJournal(TruthScope("world", "player_state", "player"),
                                "test.migration.v1", {"original_ref": "retained"}, reducer)
        before = journal.checkpoint()
        damaged = copy.deepcopy(result)
        damaged["target"]["signals"][0]["score_q6"] = 1
        with self.assertRaises(JournalError):
            journal.commit("migration", 0, damaged)
        self.assertEqual(before, journal.checkpoint())
        self.assertEqual(journal.commit("migration", 0, result).revision, 1)


class StateMigrationSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def deny(uri):
            raise NoSuchResource(ref=uri)
        registry = Registry(retrieve=deny)
        catalog = json.loads((ROOT / "data/validation/contract_catalog.json").read_text(encoding="utf-8"))
        for row in catalog["schemas"]:
            schema = json.loads((ROOT / row["path"]).read_text(encoding="utf-8"))
            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
        cls.validator = Draft202012Validator({"$ref": "https://ywe.local/schemas/state_migration_result_schema.json"}, registry=registry)

    def test_all_actual_migration_receipts_validate(self):
        for stem in FIXTURES:
            result = StateMigration(*configured(stem)).migrate(source_bytes(stem))
            self.validator.validate(result)

    def test_published_receipts_bind_the_lf_source_fixture_bytes(self):
        for stem in FIXTURES:
            path = ROOT / "examples/state_journal" / (stem + "_migration.example.json")
            result = json.loads(path.read_text(encoding="utf-8"))
            raw = source_bytes(stem).replace(b"\r\n", b"\n")
            self.assertTrue(StateMigration(*configured(stem)).verify(raw, result))

    def test_receipt_shape_rejects_missing_unknown_and_out_of_range_fields(self):
        result = StateMigration(*configured("bloodline_resonance_state")).migrate(source_bytes("bloodline_resonance_state"))
        for field in result:
            changed = dict(result)
            del changed[field]
            self.assertFalse(self.validator.is_valid(changed))
        self.assertFalse(self.validator.is_valid({**result, "extra": True}))
        changed = copy.deepcopy(result)
        changed["conversions"][0]["target_q6"] = 1000001
        self.assertFalse(self.validator.is_valid(changed))


if __name__ == "__main__":
    unittest.main()
