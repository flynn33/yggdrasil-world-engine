"""Authored safe-wire controls; schema acceptance does not certify capture effects."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/schemas/m3_reference_diagnostic_bundle_schema.json"
FIXTURES = ROOT / "examples/core_reference_diagnostics/diagnostic_bundle_cases.example.json"
MESSAGE = "Untrusted producer prose, previews, paths and exception material were omitted before persistence."
RULES = ["ASH-STATE-STRUCTURE-001", "ASH-ADMISSIBILITY-CLASSIFICATION-001", "ASH-STATE-VALIDITY-001"]


class ReferenceDiagnosticWireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

    def fragment(self, name):
        return Draft202012Validator({"$schema": self.schema["$schema"],
                                    "$defs": self.schema["$defs"], "$ref": "#/$defs/" + name},
                                   format_checker=FormatChecker())

    def valid(self, value, name=None):
        errors = list((self.fragment(name) if name else self.validator).iter_errors(value))
        self.assertEqual([], [f"{list(error.path)}: {error.message}" for error in errors])

    def rejected(self, value, name=None):
        self.assertTrue(list((self.fragment(name) if name else self.validator).iter_errors(value)))

    def test_both_authored_empty_profiles_preserve_explicit_unavailable_observations(self):
        Draft202012Validator.check_schema(self.schema)
        self.assertEqual(2, len(self.fixtures))
        for row in self.fixtures:
            self.valid(row)
            self.assertEqual([], row["events"])
            self.assertEqual("UNKNOWN", row["identity"]["source_provenance"]["status"])
            self.assertEqual("UNAVAILABLE", row["health"]["storage_state"])
            self.assertIsNone(row["generated_at_utc"])

    def test_missing_closed_fields_and_untrusted_material_are_refused(self):
        for field in self.fixtures[0]:
            with self.subTest(missing=field):
                row = copy.deepcopy(self.fixtures[0])
                del row[field]
                self.rejected(row)
        for path in ((), ("identity",), ("identity", "environment"), ("supporting_evidence",),
                     ("health",), ("retention", "configured_limits"), ("redaction",)):
            with self.subTest(path=path):
                row = copy.deepcopy(self.fixtures[0]); target = row
                for field in path:
                    target = target[field]
                target["raw_exception"] = "wire-secret-sentinel"
                self.rejected(row)
        for name in ("CaptureObjectKey", "CapturePurgeRequest", "CaptureRemovalObservation", "StoreCapturePurgeReceipt",
                     "RecoveryAdmissionReceipt", "DiagnosticsCompletionReceipt", "PrivateAcknowledgmentWitness"):
            row = copy.deepcopy(self.fixtures[0]); row["supporting_evidence"][name] = {}
            self.rejected(row)

    def test_unknown_time_reason_and_calendar_are_not_synthesized_into_valid_time(self):
        row = copy.deepcopy(self.fixtures[0]); row["generation_time_reason"] = None
        self.rejected(row)
        for stamp in ("0000-01-01T00:00:00.000000Z", "2026-02-29T00:00:00.000000Z",
                      "1900-02-29T00:00:00.000000Z", "2100-02-29T00:00:00.000000Z",
                      "2026-04-31T00:00:00.000000Z", "2026-10-04T24:00:00.000000Z",
                      "2026-10-04T00:00:60.000000Z", "2026-10-04T00:00:00Z",
                      "2026-10-04T00:00:00.000000+00:00"):
            with self.subTest(stamp=stamp):
                row = copy.deepcopy(self.fixtures[0]); row.update(generated_at_utc=stamp, generation_time_reason=None)
                self.rejected(row)
        row = copy.deepcopy(self.fixtures[0]); row.update(generated_at_utc="2024-02-29T23:59:59.999999Z",generation_time_reason=None)
        self.valid(row)
        for stamp in ("2000-02-29T00:00:00.000000Z","2400-02-29T00:00:00.000000Z",
                      "9999-12-31T23:59:59.999999Z","0001-01-01T00:00:00.000000Z"):
            row = copy.deepcopy(self.fixtures[0]); row.update(generated_at_utc=stamp,generation_time_reason=None)
            self.valid(row)
        clock = {"observed_utc": None, "monotonic_nanoseconds": None,
                 "utc_reason": "CLOCK_UNAVAILABLE", "monotonic_reason": "CLOCK_UNAVAILABLE"}
        self.valid(clock, "ClockObservation")
        for field, value in (("utc_reason",None), ("monotonic_reason",None), ("monotonic_nanoseconds",False),
                             ("monotonic_nanoseconds",18446744073709551616), ("monotonic_nanoseconds",-1)):
            altered = copy.deepcopy(clock); altered[field] = value
            self.rejected(altered, "ClockObservation")

    def test_source_status_and_profile_identity_pairs_are_closed(self):
        unknown = self.fixtures[0]["identity"]["source_provenance"]
        for fields in ({"verified_revision":"a"*40}, {"unavailable_reason":None}, {"dirty_path_aliases":["ref:000001"]}):
            altered = copy.deepcopy(unknown); altered.update(fields)
            self.rejected(altered, "SourceProvenance")
        clean = {"status":"VERIFIED_CLEAN", "verified_revision":"a"*40,
                 "dirty_path_aliases":[],"unavailable_reason":None}
        dirty = copy.deepcopy(clean); dirty.update(status="VERIFIED_DIRTY",dirty_path_aliases=["ref:000001"])
        self.valid(clean,"SourceProvenance"); self.valid(dirty,"SourceProvenance")
        for fields in ({"status":"VERIFIED_DIRTY"},{"verified_revision":None},{"dirty_path_aliases":["ref:000001"]}):
            altered = copy.deepcopy(clean); altered.update(fields)
            self.rejected(altered,"SourceProvenance")
        for selected in ("identity","profile"):
            row = copy.deepcopy(self.fixtures[0]); row[selected]["implementation_id"] = "REFERENCE_RELEASE_DIAGNOSTICS"
            self.rejected(row)
        row = copy.deepcopy(self.fixtures[0]); row["profile"]["development_payloads_enabled"] = False
        self.rejected(row)

    def test_whole_source_vectors_accept_legacy_and_current_and_reject_crossed_pins(self):
        text = (ROOT / "docs/architecture/m3_source_compatibility_contract.md").read_text(encoding="utf-8")
        inventory = json.loads(text.split("<!-- EXACT_SOURCE_COMPATIBILITY_INVENTORY -->", 1)[1].split("```json", 1)[1].split("```", 1)[0])
        rows = []
        for vector in inventory["vectors"]:
            pins = [{"source_kind": pin["source_kind"], "revision": inventory["legacy_commit"], "sha256": pin["sha256"]}
                for pin in vector["diagnostic_pin_fields"]]
            row = {"evidence_reference":"ref:000001", "dependency_id":"ash_cosmological_model.f2_9.canonical",
                "verified_pins":pins, "external_source_reference":None, "external_verification":"DECLARED_NOT_AUTHENTICATED"}
            self.valid(row, "SafeSourceEvidence")
            rows.append(row)
        for source, other in ((0,1),(1,0)):
            mixed = copy.deepcopy(rows[source])
            mixed["verified_pins"][7] = copy.deepcopy(rows[other]["verified_pins"][7])
            errors = list(self.fragment("SafeSourceEvidence").iter_errors(mixed))
            self.assertEqual([("oneOf", ())], [(error.validator, tuple(error.path)) for error in errors])
            self.assertEqual({("const", ("verified_pins",0,"sha256")), ("const", ("verified_pins",7,"sha256"))},
                {(error.validator, tuple(error.path)) for error in errors[0].context})
        reordered = copy.deepcopy(rows[0]); reordered["verified_pins"].reverse()
        self.rejected(reordered, "SafeSourceEvidence")
        invalid = copy.deepcopy(rows[1]); invalid["verified_pins"][0]["revision"] = "unverified"
        errors = list(self.fragment("SafeSourceEvidence").iter_errors(invalid))
        self.assertTrue(any(error.validator == "pattern" and tuple(error.path) == ("verified_pins",0,"revision") for error in errors))
        # A structural source node intentionally does not authenticate its Git revision.
        self.assertEqual(rows[0]["verified_pins"][0]["revision"], rows[1]["verified_pins"][0]["revision"])

    def test_coverage_and_counter_observations_are_complete_and_ordered(self):
        row = copy.deepcopy(self.fixtures[0]); row["coverage"].pop()
        self.rejected(row)
        row = copy.deepcopy(self.fixtures[0]); row["coverage"].reverse()
        self.rejected(row)
        health = copy.deepcopy(self.fixtures[0]["health"])
        health["counter_states"][0].update(status="UNAVAILABLE",reason="STORAGE_UNCONFIRMED")
        health["accepted_count"] = None
        self.valid(health,"DiagnosticsHealth")
        altered = copy.deepcopy(health); altered["accepted_count"] = 0
        self.rejected(altered,"DiagnosticsHealth")
        health["counter_states"][0].update(status="SATURATED",reason="COUNTER_LIMIT")
        health["accepted_count"] = 18446744073709551615
        self.valid(health,"DiagnosticsHealth")
        altered = copy.deepcopy(health); altered["accepted_count"] -= 1
        self.rejected(altered,"DiagnosticsHealth")
        altered = copy.deepcopy(health); altered["counter_states"].reverse()
        self.rejected(altered,"DiagnosticsHealth")

    def diagnostic(self, row):
        admissibility, compatibility, normalization, relevance, valid = row
        return {"input_state":{"kind":"ASH_STATE","state":"000000000","input_reference":"ref:000001","failure_code":None},
                "admissibility_status":admissibility,"transformation_compatibility":compatibility,
                "normalization_status":normalization,"recoverability_relevance":relevance,"is_valid":valid,
                "orbit_info":None if admissibility=="UNCLASSIFIED" else {"orbit_id":"000000000","member_count":16,
                        "contains_known_valid_state":admissibility!="TRANSFORMATION_INCOMPATIBLE"},
                "rule_ids":list(RULES),"notes":[MESSAGE]}

    def test_all_four_canonical_semantic_rows_and_rejected_input_coherence(self):
        rows = [("VALID","COMPATIBLE","ALREADY_VALID","NO_RECOVERY_NEEDED",True),
                ("TRANSFORMATION_COMPATIBLE","COMPATIBLE","NORMALIZABLE","RECOVERY_APPLICABLE",False),
                ("TRANSFORMATION_INCOMPATIBLE","INCOMPATIBLE","NOT_NORMALIZABLE","NOT_RECOVERABLE",False),
                ("UNCLASSIFIED","UNKNOWN","BLOCKED","CONTAINMENT_NEEDED",False)]
        for row in rows:
            diagnostic = self.diagnostic(row); self.valid(diagnostic,"SafeStateValidity")
            altered = copy.deepcopy(diagnostic); altered["is_valid"] = not altered["is_valid"]
            self.rejected(altered,"SafeStateValidity")
            altered = copy.deepcopy(diagnostic); altered["rule_ids"].append("ASH-FALLBACK-SELECTION-001")
            self.rejected(altered,"SafeStateValidity")
            if row[0] != "UNCLASSIFIED":
                altered = copy.deepcopy(diagnostic); altered["orbit_info"]["contains_known_valid_state"] = not altered["orbit_info"]["contains_known_valid_state"]
                self.rejected(altered,"SafeStateValidity")
        rejected = self.diagnostic(rows[-1]); rejected["input_state"].update(kind="REJECTED",state=None,failure_code="STATE_WIDTH")
        self.valid(rejected,"SafeStateValidity")
        altered = self.diagnostic(rows[0]); altered["input_state"] = rejected["input_state"]
        self.rejected(altered,"SafeStateValidity")
        repeated_notes = self.diagnostic(rows[0]); repeated_notes["notes"] = [MESSAGE,MESSAGE]
        self.valid(repeated_notes,"SafeStateValidity")

    def test_profile_and_predicate_absence_remain_explicit(self):
        profile = {"evidence_reference":"ref:000001","profile_reference":"ref:000002","availability":"AVAILABLE",
                   "source_reference":"ref:000003","source_digest_reference":"ref:000004","source_evidence_reference":"ref:000005",
                   "recognized_valid_states":[],"unavailable_reason":None}
        self.valid(profile,"SafeProfileEvidence")
        altered = copy.deepcopy(profile); altered["recognized_valid_states"] = None
        self.rejected(altered,"SafeProfileEvidence")
        altered.update(availability="UNAVAILABLE",unavailable_reason="NOT_PROVIDED")
        self.valid(altered,"SafeProfileEvidence")
        predicate = {"evaluation_status":"EVALUATED","value":False,"assessment_reference":"ref:000001",
                     "diagnosis_reference":"ref:000002","subject_reference":"ref:000003","profile_reference":"ref:000004",
                     "source_reference":"ref:000005","evidence_reference":"ref:000006"}
        self.valid(predicate,"SafePredicate")
        altered = copy.deepcopy(predicate); altered["value"] = None
        self.rejected(altered,"SafePredicate")
        altered["evaluation_status"] = "NOT_EVALUATED"
        self.valid(altered,"SafePredicate")
        altered["value"] = False
        self.rejected(altered,"SafePredicate")

    def test_repeated_supplied_codewords_are_valid_transport_and_full_index_is_retained(self):
        proof = {"evidence_reference":"ref:000001","correction_reference":"ref:000002","original_assessment_reference":"ref:000003",
                 "submitted_source_reference":"ref:000004","current_source_evidence_reference":"ref:000005",
                 "submitted_profile_evidence_reference":"ref:000006","current_profile_evidence_reference":"ref:000007",
                 "declared_source_authentication":"DECLARED_NOT_AUTHENTICATED","origin_validation_status":"VERIFIED",
                 "correction_validation_status":"VERIFIED","submitted_chain":["000000000","000000000"],
                 "claimed_target":"000000000","computed_target":"000000000","target_diagnostic_reference":"ref:000008",
                 "failed_field":None,"safe_failure":None}
        self.valid(proof,"SafeCorrectionProof")
        for field in ("computed_target","target_diagnostic_reference"):
            altered = copy.deepcopy(proof); altered[field] = None
            self.rejected(altered,"SafeCorrectionProof")
        altered = copy.deepcopy(proof); altered["submitted_chain"] *= 9
        self.rejected(altered,"SafeCorrectionProof")
        context = self.schema["$defs"]["SafeStateContext"]
        index = context["properties"]["step_index"]
        validator = Draft202012Validator(index)
        self.assertTrue(validator.is_valid(767))
        for invalid in (768,False,0.5,-1):
            self.assertFalse(validator.is_valid(invalid))

    def test_pure_target_rows_have_complete_evidence_without_an_invented_emission(self):
        target = {"evidence_reference":"ref:000001","source_evidence_reference":"ref:000002",
                  "profile_evidence_reference":"ref:000003",
                  "state_validity_diagnostic":self.diagnostic(("VALID","COMPATIBLE","ALREADY_VALID","NO_RECOVERY_NEEDED",True))}
        self.valid(target,"SafeTargetValidityEvidence")
        for field in target:
            altered = copy.deepcopy(target); del altered[field]
            self.rejected(altered,"SafeTargetValidityEvidence")
        for field in ("envelope","capture_receipt","assessment_reference"):
            altered = copy.deepcopy(target); altered[field] = None
            self.rejected(altered,"SafeTargetValidityEvidence")
        row = copy.deepcopy(self.fixtures[0])
        row["supporting_evidence"]["target_validity"] = [target] * 264
        self.valid(row)
        row["supporting_evidence"]["target_validity"].append(target)
        self.rejected(row)

    def test_purge_wire_controls_preserve_exclusive_phases_and_partial_observations(self):
        event = {"kind":"EVENT","sequence":0,"supporting_kind":None,"evidence_reference":None}
        support = {"kind":"SUPPORTING","sequence":None,"supporting_kind":"TARGET_VALIDITY","evidence_reference":"ref:000001"}
        for key in (event,support):
            self.valid(key,"CaptureObjectKey")
        altered = dict(support,sequence=0); self.rejected(altered,"CaptureObjectKey")
        self.valid({"event_sequences":[0,1],"supporting_keys":[]},"CapturePurgeRequest")
        self.valid({"event_sequences":[],"supporting_keys":[support]},"CapturePurgeRequest")
        for request in ({"event_sequences":[],"supporting_keys":[]},
                        {"event_sequences":[0],"supporting_keys":[support]},
                        {"event_sequences":[0,0],"supporting_keys":[]},
                        {"event_sequences":[],"supporting_keys":[event]}):
            self.rejected(request,"CapturePurgeRequest")
        maximum = {"event_sequences":[],"supporting_keys":[dict(support,evidence_reference=f"ref:{index:06d}") for index in range(1928)]}
        self.valid(maximum,"CapturePurgeRequest")
        maximum["supporting_keys"].append(dict(support,evidence_reference="ref:001928"))
        self.rejected(maximum,"CapturePurgeRequest")
        removed = {"key":event,"status":"REMOVED","removed_bytes":8,"failure_code":None}
        unknown = {"key":dict(event,sequence=1),"status":"UNCONFIRMED","removed_bytes":None,"failure_code":"STORAGE_COMMIT_UNCONFIRMED"}
        for observation in (removed,unknown):
            self.valid(observation,"CaptureRemovalObservation")
        altered = dict(unknown,removed_bytes=0); self.rejected(altered,"CaptureRemovalObservation")
        partial = {"status":"PARTIAL","observations":[removed,unknown],"failure_code":"STORAGE_COMMIT_UNCONFIRMED"}
        self.valid(partial,"StoreCapturePurgeReceipt")
        for receipt in (dict(partial,status="COMPLETED",failure_code=None),
                        dict(partial,status="REJECTED"),dict(partial,observations=[unknown]),
                        dict(partial,observations=[removed])):
            self.rejected(receipt,"StoreCapturePurgeReceipt")
        mixed = copy.deepcopy(partial); mixed["observations"][1]["key"] = support
        self.rejected(mixed,"StoreCapturePurgeReceipt")


if __name__ == "__main__":
    unittest.main()
