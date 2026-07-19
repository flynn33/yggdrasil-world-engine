from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_m1_canon_governance as m1
import sync_ash_specifications as ash_sync


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8-sig"))


def load_yaml(relative_path: str) -> dict:
    return yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8-sig"))


def write_text(root: Path, relative_path: str, value: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def assert_error_contains(test: unittest.TestCase, errors: list[str], fragment: str) -> None:
    test.assertTrue(
        any(fragment.casefold() in error.casefold() for error in errors),
        msg=f"Expected error containing {fragment!r}; found {errors}",
    )


def final_roadmap_from_live() -> dict:
    roadmap = copy.deepcopy(load_json(m1.ROADMAP_PATH))
    roadmap["current_milestone"] = "M2"
    milestones = {item["id"]: item for item in roadmap["milestones"]}
    milestones["M1"]["status"] = "complete"
    milestones["M1"]["acceptance_evidence"] = [
        m1.EVIDENCE_PATH,
        m1.EVIDENCE_DOCUMENT_PATH,
    ]
    milestones["M2"]["status"] = "in_progress"
    authority = next(
        item for item in roadmap["subsystems"] if item["id"] == "authority_boundaries"
    )
    authority["open_work"] = []
    for dimension in (
        "normative_artifact_complete",
        "executable_schema_complete",
        "conformance_tested",
        "release_ready",
    ):
        authority["maturity"][dimension] = "complete"
    return roadmap


class LiveM1ContractTests(unittest.TestCase):
    def test_live_closed_repository_passes_with_acceptance_evidence(self):
        self.assertEqual([], m1.validation_errors(ROOT, run_external=False))

    def test_live_external_guardrails_pass(self):
        errors: list[str] = []
        m1.check_external_guardrails(ROOT, errors)
        self.assertEqual([], errors)

    def test_clean_live_component_contracts_pass(self):
        errors: list[str] = []
        requirements = load_json(m1.REQUIREMENT_PATH)
        records = load_json(m1.GOVERNANCE_RECORD_PATH)
        terms = load_json(m1.TERM_INDEX_PATH)
        lattice = load_json(m1.LATTICE_PATH)
        identity = load_json(m1.ASH_IDENTITY_PATH)
        m1.check_requirements(ROOT, requirements, errors)
        m1.check_normative_clauses(ROOT, errors)
        m1.check_governance_records(ROOT, records, errors)
        m1.check_terms(ROOT, terms, errors)
        m1.check_lattice(lattice, errors)
        m1.check_semantic_surfaces(ROOT, errors)
        m1.check_ash_identity(ROOT, identity, errors)
        self.assertEqual([], errors)


class RequirementAndNormativeTests(unittest.TestCase):
    def test_duplicate_or_reused_requirement_identifier_rejects(self):
        document = copy.deepcopy(load_json(m1.REQUIREMENT_PATH))
        document["requirements"].append(copy.deepcopy(document["requirements"][0]))
        errors: list[str] = []
        m1.check_requirements(ROOT, document, errors)
        assert_error_contains(self, errors, "duplicate or reused")

    def test_changed_meaning_under_existing_identifier_rejects(self):
        document = copy.deepcopy(load_json(m1.REQUIREMENT_PATH))
        document["requirements"][0]["normative_statement"] = (
            "This identifier now carries a different semantic requirement."
        )
        errors: list[str] = []
        m1.check_requirements(ROOT, document, errors)
        assert_error_contains(self, errors, "meaning changed")

    def test_changed_authority_metadata_under_existing_identifier_rejects(self):
        document = copy.deepcopy(load_json(m1.REQUIREMENT_PATH))
        document["requirements"][0]["normative_level"] = "SHOULD"
        errors: list[str] = []
        m1.check_requirements(ROOT, document, errors)
        assert_error_contains(self, errors, "authority or normative force changed")

    def test_malformed_requirement_identifier_reports_error_without_crashing(self):
        document = copy.deepcopy(load_json(m1.REQUIREMENT_PATH))
        document["requirements"][0]["requirement_id"] = {"bad": 1}
        errors: list[str] = []
        m1.check_requirements(ROOT, document, errors)
        assert_error_contains(self, errors, "invalid identifier")

    def test_nonexistent_decision_reference_rejects(self):
        document = copy.deepcopy(load_json(m1.REQUIREMENT_PATH))
        document["requirements"][0]["decision_refs"] = ["ADR-9999"]
        errors: list[str] = []
        m1.check_requirements(ROOT, document, errors)
        assert_error_contains(self, errors, "nonexistent governance decision")

    def test_later_requirement_can_append_without_rewriting_m1_meanings(self):
        document = copy.deepcopy(load_json(m1.REQUIREMENT_PATH))
        appended = copy.deepcopy(document["requirements"][-1])
        appended.update(
            {
                "requirement_id": "YWE-REQ-0019",
                "title": "Later governed requirement",
                "normative_statement": "A later contract MUST retain stable traceability.",
                "status": "proposed",
                "introduced_milestone": "M2",
                "aliases": [],
                "supersedes": [],
            }
        )
        document["requirements"].append(appended)
        document["summary"] = {
            "total_requirements": 19,
            "active": 18,
            "proposed": 1,
            "terminal": 0,
            "next_identifier": "YWE-REQ-0020",
        }
        document["id_policy"]["next_available_id"] = "YWE-REQ-0020"
        errors: list[str] = []
        m1.check_requirements(ROOT, document, errors)
        self.assertEqual([], errors)

    def test_unknown_authority_node_rejects(self):
        document = copy.deepcopy(load_json(m1.REQUIREMENT_PATH))
        document["requirements"][0]["authority_node"] = "external_host_materialization"
        errors: list[str] = []
        m1.check_requirements(ROOT, document, errors)
        assert_error_contains(self, errors, "unknown truth-authority node")

    def test_new_uppercase_normative_clause_without_identifier_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path in m1.NORMATIVE_SURFACES:
                write_text(root, relative_path, "# Policy\n\nDescriptive text only.\n")
            write_text(
                root,
                m1.NORMATIVE_SURFACES[0],
                "# Policy\n\n- A new implementation MUST retain this behavior.\n",
            )
            errors: list[str] = []
            m1.check_normative_clauses(root, errors)
            assert_error_contains(self, errors, "without a requirement identifier")

    def test_citation_on_one_bullet_does_not_hide_uncited_next_bullet(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path in m1.NORMATIVE_SURFACES:
                write_text(root, relative_path, "# Policy\n\nDescriptive text only.\n")
            write_text(
                root,
                m1.NORMATIVE_SURFACES[0],
                (
                    "# Policy\n\n"
                    "- The first behavior MUST hold. [YWE-REQ-0001]\n"
                    "- The second behavior MUST also hold.\n"
                ),
            )
            errors: list[str] = []
            m1.check_normative_clauses(root, errors)
            self.assertEqual(1, sum("without a requirement identifier" in error for error in errors))

    def test_code_and_markdown_tables_do_not_create_normative_clauses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = (
                "# Policy\n\n"
                "| Example | Meaning |\n"
                "| MUST | illustrative |\n\n"
                + chr(96) * 3
                + "\nMUST remain an example\n"
                + chr(96) * 3
                + "\n"
            )
            for relative_path in m1.NORMATIVE_SURFACES:
                write_text(root, relative_path, value)
            errors: list[str] = []
            m1.check_normative_clauses(root, errors)
            self.assertEqual([], errors)


class GovernanceLifecycleTests(unittest.TestCase):
    def test_logical_record_arrays_flatten_deterministically(self):
        live = load_json(m1.GOVERNANCE_RECORD_PATH)
        arrays = {key: [] for key in m1.LOGICAL_RECORD_ARRAYS}
        type_to_key = {value: key for key, value in m1.LOGICAL_RECORD_ARRAYS.items()}
        for record in live["records"]:
            stripped = copy.deepcopy(record)
            stripped.pop("record_type")
            arrays[type_to_key[record["record_type"]]].append(stripped)
        flattened = m1.governance_records(arrays)
        self.assertEqual(27, len(flattened))
        self.assertEqual(
            [record["id"] for record in live["records"]],
            [record["id"] for record in flattened],
        )

    def test_invalid_lifecycle_state_rejects_for_every_record_type(self):
        live = load_json(m1.GOVERNANCE_RECORD_PATH)
        representatives = {
            "decision": "ADR-0001",
            "change_proposal": "CP-0001",
            "risk": "RISK-0001",
            "deviation": "DEV-0001",
            "question": "Q-0001",
        }
        for record_type, identifier in representatives.items():
            with self.subTest(record_type=record_type):
                document = copy.deepcopy(live)
                record = next(item for item in document["records"] if item["id"] == identifier)
                record["status"] = "open"
                errors: list[str] = []
                m1.check_governance_records(ROOT, document, errors)
                assert_error_contains(self, errors, "required M1 closure state")

    def test_question_resolution_to_wrong_decision_rejects(self):
        document = copy.deepcopy(load_json(m1.GOVERNANCE_RECORD_PATH))
        question = next(item for item in document["records"] if item["id"] == "Q-0001")
        question["resolution_record_ref"] = "ADR-0010"
        errors: list[str] = []
        m1.check_governance_records(ROOT, document, errors)
        assert_error_contains(self, errors, "invalid resolution record")

    def test_nonexistent_affected_and_related_record_refs_reject(self):
        for identifier, field in (
            ("CP-0001", "affected_record_refs"),
            ("RISK-0001", "related_record_refs"),
        ):
            with self.subTest(identifier=identifier):
                document = copy.deepcopy(load_json(m1.GOVERNANCE_RECORD_PATH))
                record = next(item for item in document["records"] if item["id"] == identifier)
                record[field] = ["ADR-9999"]
                errors: list[str] = []
                m1.check_governance_records(ROOT, document, errors)
                assert_error_contains(self, errors, f"invalid {field}")

    def test_supersession_links_must_be_reciprocal(self):
        document = copy.deepcopy(load_json(m1.GOVERNANCE_RECORD_PATH))
        source = next(item for item in document["records"] if item["id"] == "ADR-0002")
        target = next(item for item in document["records"] if item["id"] == "ADR-0001")
        source["supersedes"] = ["ADR-0001"]
        target["status"] = "superseded"
        target["superseded_by"] = []
        document["summary"] = m1.recompute_governance_summary(document["records"])
        errors: list[str] = []
        m1.check_governance_records(ROOT, document, errors)
        assert_error_contains(self, errors, "without a reciprocal")

    def test_malformed_supersession_array_reports_without_crashing(self):
        document = copy.deepcopy(load_json(m1.GOVERNANCE_RECORD_PATH))
        decision = next(item for item in document["records"] if item["id"] == "ADR-0010")
        decision["supersedes"] = 7
        errors: list[str] = []
        m1.check_governance_records(ROOT, document, errors)
        assert_error_contains(self, errors, "supersedes must be an array")

    def test_later_governance_record_can_append(self):
        document = copy.deepcopy(load_json(m1.GOVERNANCE_RECORD_PATH))
        appended = copy.deepcopy(document["records"][0])
        appended.update(
            {
                "id": "ADR-0011",
                "title": "Later decision",
                "status": "proposed",
                "supersedes": [],
                "superseded_by": [],
            }
        )
        document["records"].append(appended)
        document["summary"] = m1.recompute_governance_summary(document["records"])
        errors: list[str] = []
        m1.check_governance_records(ROOT, document, errors)
        self.assertEqual([], errors)


class GlossaryAndLatticeTests(unittest.TestCase):
    def test_duplicate_glossary_concept_rejects(self):
        document = copy.deepcopy(load_json(m1.TERM_INDEX_PATH))
        document["terms"].append(copy.deepcopy(document["terms"][0]))
        errors: list[str] = []
        m1.check_terms(ROOT, document, errors)
        assert_error_contains(self, errors, "duplicate term keys")
        assert_error_contains(self, errors, "duplicate glossary headings")

    def test_competing_alias_definition_rejects(self):
        document = copy.deepcopy(load_json(m1.TERM_INDEX_PATH))
        document["terms"][0]["aliases"].append(
            {"label": "competing label", "status": "presentation_alias", "migration": "Use A."}
        )
        document["terms"][1]["aliases"].append(
            {"label": "competing label", "status": "presentation_alias", "migration": "Use B."}
        )
        errors: list[str] = []
        m1.check_terms(ROOT, document, errors)
        assert_error_contains(self, errors, "competing canonical owners")

    def test_perception_or_host_authority_overwrite_rejects(self):
        document = copy.deepcopy(load_json(m1.LATTICE_PATH))
        perception = next(
            item
            for item in document["nodes"]
            if item["node_id"] == "perception_social_interpretation"
        )
        perception["forbidden_override_targets"].remove("shared_worldstate")
        errors: list[str] = []
        m1.check_lattice(document, errors)
        assert_error_contains(self, errors, "violates its authority boundary")

    def test_wrw_specific_rule_as_normative_core_rejects(self):
        document = copy.deepcopy(load_json(m1.LATTICE_PATH))
        document["scope_routing"]["wrw_reference_profile"][
            "may_universalize_profile_content"
        ] = True
        errors: list[str] = []
        m1.check_lattice(document, errors)
        assert_error_contains(self, errors, "setting-neutral Core authority")

    def test_reversed_materialization_relationship_rejects(self):
        document = copy.deepcopy(load_json(m1.LATTICE_PATH))
        edge = next(
            item
            for item in document["relationships"]
            if item["source_node"] == "perception_social_interpretation"
            and item["target_node"] == "host_materialization"
        )
        edge["source_node"], edge["target_node"] = edge["target_node"], edge["source_node"]
        errors: list[str] = []
        m1.check_lattice(document, errors)
        assert_error_contains(self, errors, "approved typed lattice")

    def test_byte_identical_sync_claim_rejects_normalized_equivalence(self):
        document = copy.deepcopy(load_json(m1.LATTICE_PATH))
        document["ash_dependency"]["synchronization_mode"] = "byte_identical_relative_paths"
        errors: list[str] = []
        m1.check_lattice(document, errors)
        assert_error_contains(self, errors, "dependency routing is stale")

    def test_human_lattice_must_list_extension_profile_truth_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scopes = [
                scope_id
                for scope_id in m1.EXPECTED_TRUTH_SCOPES
                if scope_id != "extension_profile_contract"
            ]
            write_text(
                root,
                "docs/architecture/truth_authority_lattice.md",
                "\n".join([*scopes, "normalized_utf8_lf_relative_paths"]),
            )
            errors: list[str] = []
            m1.check_lattice_document(root, errors)
            assert_error_contains(self, errors, "extension_profile_contract")

    def test_normative_core_wrw_marker_without_exception_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_text(
                root,
                "docs/architecture/ywe_core_wrw_scope_contract.md",
                "authority\n",
            )
            write_text(root, "core/contract.md", "White Wolf is required.\n")
            classification = {"ordered_rules": [], "overrides": []}
            scope = {"ordered_rules": [], "overrides": []}
            class_assignments = {
                "core/contract.md": {"classification": "normative"},
            }
            scope_assignments = {
                "core/contract.md": {"primary_partition": "ywe_core"},
            }
            with (
                patch.object(m1.m0_validation, "repository_candidate_paths", return_value=["core/contract.md"]),
                patch.object(
                    m1.m0_validation,
                    "effective_assignments",
                    side_effect=[class_assignments, scope_assignments],
                ),
            ):
                errors: list[str] = []
                m1.check_scope_separation(root, classification, scope, errors)
            assert_error_contains(self, errors, "without a per-path exception")

    def test_exact_per_path_wrw_reference_exception_accepts_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_text(
                root,
                "docs/architecture/ywe_core_wrw_scope_contract.md",
                "authority\n",
            )
            write_text(root, "core/contract.md", "White Wolf is an example only.\n")
            exception = {
                "markers": ["White Wolf"],
                "rationale": "This is a narrowly scoped compatibility example reference.",
                "authority_ref": "docs/architecture/ywe_core_wrw_scope_contract.md",
            }
            override = {
                "path": "core/contract.md",
                "primary_partition": "ywe_core",
                "wrw_reference_exception": exception,
            }
            classification = {"ordered_rules": [], "overrides": []}
            scope = {"ordered_rules": [], "overrides": [override]}
            with (
                patch.object(m1.m0_validation, "repository_candidate_paths", return_value=["core/contract.md"]),
                patch.object(
                    m1.m0_validation,
                    "effective_assignments",
                    side_effect=[
                        {"core/contract.md": {"classification": "normative"}},
                        {"core/contract.md": override},
                    ],
                ),
            ):
                errors: list[str] = []
                m1.check_scope_separation(root, classification, scope, errors)
            self.assertEqual([], errors)


class SemanticMigrationTests(unittest.TestCase):
    def test_normative_world_does_not_change_phrase_rejects(self):
        errors: list[str] = []
        m1.check_forbidden_semantic_phrases(
            "fixture.md",
            "The world does not change; only the observer changes.",
            errors,
        )
        assert_error_contains(self, errors, "static-world contradiction")

    def test_full_vector_as_one_of_nine_named_realms_rejects(self):
        errors: list[str] = []
        m1.check_forbidden_semantic_phrases(
            "fixture.md",
            "Every full F2^9 state vector is one of the nine named realms.",
            errors,
        )
        assert_error_contains(self, errors, "equates full ASH state vectors")

    def test_vertices_slash_realms_512_state_phrase_rejects(self):
        errors: list[str] = []
        m1.check_forbidden_semantic_phrases(
            "fixture.md",
            "There are 512 states (vertices / realms) in the state space.",
            errors,
        )
        assert_error_contains(self, errors, "equates full ASH state vectors")

    def test_duplicate_coordinate_index_and_ordinal_rejects(self):
        registry = copy.deepcopy(load_json("data/realm_registry/realms.json"))
        registry["coordinate_bindings"][1]["coordinate_index"] = 0
        registry["coordinate_bindings"][1]["ordinal"] = 1
        errors: list[str] = []
        m1.check_realm_registry(registry, errors)
        assert_error_contains(self, errors, "coordinate indices must be unique")
        assert_error_contains(self, errors, "ordinals must be unique")

    def test_boolean_coordinate_and_ordinal_do_not_pass_as_integers(self):
        registry = copy.deepcopy(load_json("data/realm_registry/realms.json"))
        registry["coordinate_bindings"][1]["coordinate_index"] = True
        registry["coordinate_bindings"][0]["ordinal"] = True
        errors: list[str] = []
        m1.check_realm_registry(registry, errors)
        assert_error_contains(self, errors, "coordinate indices must be unique")
        assert_error_contains(self, errors, "ordinals must be unique")

    def test_writer_that_emits_only_wolf_alignment_rejects(self):
        documents = {
            "writer.json": {
                "wolf_alignment": {"white_wolf": 1, "dark_wolf": 2},
            }
        }
        errors: list[str] = []
        m1.check_player_documents(documents, errors)
        assert_error_contains(self, errors, "does not define canonical wolf_resonance")

    def test_disagreeing_wolf_fields_reject(self):
        documents = {
            "record.json": {
                "wolf_resonance": {"white_wolf": 1, "dark_wolf": 2},
                "wolf_alignment": {"white_wolf": 1, "dark_wolf": 3},
            }
        }
        errors: list[str] = []
        m1.check_player_documents(documents, errors)
        assert_error_contains(self, errors, "disagree")

    def test_reversal_that_edits_prior_history_rejects(self):
        npc = load_yaml("core/narrative_engine/npc_synthesis_rules.yaml")
        worldstate = copy.deepcopy(
            load_yaml("core/narrative_engine/worldstate_delta_rules.yaml")
        )
        history = worldstate["history_and_reversal_semantics"]
        history["event_history"]["deletion_or_in_place_edit_allowed"] = True
        history["reversal"]["preserves_original_event"] = False
        errors: list[str] = []
        m1.check_history_documents(npc, worldstate, errors)
        assert_error_contains(self, errors, "erase or edit")
        assert_error_contains(self, errors, "no longer preserves")

    def test_perception_schema_shared_truth_overwrite_rejects(self):
        document = copy.deepcopy(load_json("core/perception_engine/perception_schema.json"))
        document["perception_rules"]["objective_state_change_requires_accepted_delta"] = False
        errors: list[str] = []
        m1.check_perception_document(document, errors)
        assert_error_contains(self, errors, "shared objective truth")

    def test_executable_identity_requires_equal_canonical_and_legacy_outputs(self):
        def encode_state(value: str) -> dict:
            return {
                "state_identity": value,
                "state_signature": value,
                "vertex_id": f"ash_state_{value}",
                "realm_id": f"ash_state_{value}",
                "orbit_id": value,
            }

        def encode_realm(value: str) -> dict:
            result = encode_state(value)
            result["realm_id"] = "conflict"
            return result

        canonical = encode_state("100000000")
        namespace = {
            "encode_state_identity": encode_state,
            "encode_realm_identity": encode_realm,
            "build_cosmic_pattern_snapshot": lambda value: {
                "normalized_state": value,
                "state_identity": canonical,
                "realm_identity": canonical,
            },
            "plan_generation": lambda _name, value: {
                "source_state_identity": canonical,
                "source_realm": canonical,
                "destination_state_identity": encode_state(value),
                "destination_realm": encode_state(value),
            },
        }
        errors: list[str] = []
        m1.check_executable_identity_namespace(namespace, errors)
        assert_error_contains(self, errors, "does not equal")


class AshIdentityAndMirrorTests(unittest.TestCase):
    def test_stale_ash_dependency_digest_rejects(self):
        document = copy.deepcopy(load_json(m1.ASH_IDENTITY_PATH))
        document["aggregate_sha256"] = "0" * 64
        errors: list[str] = []
        m1.check_ash_identity(ROOT, document, errors)
        assert_error_contains(self, errors, "stale")

    def test_missing_extra_and_changed_mirror_paths_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_text(root, "VERSION", "2.0.23\n")
            write_text(
                root,
                "core/ash_pattern_engine/canonical/core/one.md",
                "one\n",
            )
            write_text(
                root,
                "core/ash_pattern_engine/canonical/core/two.md",
                "two\n",
            )
            ash_sync.write_synchronized_state(root)
            (root / "specs/core/one.md").unlink()
            write_text(root, "specs/core/two.md", "changed\n")
            write_text(root, "specs/extra.md", "extra\n")
            errors, _manifest = ash_sync.synchronization_errors(root)
            assert_error_contains(self, errors, "missing mirror path")
            assert_error_contains(self, errors, "stale mirror path")
            assert_error_contains(self, errors, "extra mirror path")


class RoadmapBoundaryAndImmutabilityTests(unittest.TestCase):
    def test_open_m1_debt_rejects_when_roadmap_says_complete(self):
        roadmap = final_roadmap_from_live()
        debt = copy.deepcopy(load_json(m1.DEBT_PATH))
        target = next(
            item for item in debt["debts"] if item["debt_id"] == "QD-063"
        )
        target["status"] = "open"
        target["resolution_evidence"] = []
        target.pop("resolution_evidence_details", None)
        errors: list[str] = []
        m1.check_debt_and_roadmap(ROOT, roadmap, debt, errors)
        assert_error_contains(self, errors, "M1 debt is not resolved")

    def test_provisional_active_m1_state_accepts_open_assigned_debt(self):
        roadmap = copy.deepcopy(load_json(m1.ROADMAP_PATH))
        roadmap["current_milestone"] = "M1"
        milestones = {item["id"]: item for item in roadmap["milestones"]}
        milestones["M1"]["status"] = "in_progress"
        milestones["M1"]["acceptance_evidence"] = []
        milestones["M2"]["status"] = "planned"
        debt = copy.deepcopy(load_json(m1.DEBT_PATH))
        target = next(
            item for item in debt["debts"] if item["debt_id"] == "QD-063"
        )
        target["status"] = "open"
        target["resolution_evidence"] = []
        target.pop("resolution_evidence_details", None)
        errors: list[str] = []
        m1.check_provisional_debt_and_roadmap(roadmap, debt, errors)
        self.assertEqual([], errors)

    def test_precise_m1_debt_locators_resolve_and_stale_locator_rejects(self):
        debt = load_json(m1.DEBT_PATH)
        target_ids = {
            item["debt_id"]
            for item in debt["debts"]
            if item.get("assigned_milestone") == "M1"
        }
        self.assertEqual(m1.EXPECTED_M1_DEBT_IDS, target_ids)
        errors: list[str] = []
        for item in debt["debts"]:
            if item.get("debt_id") in target_ids:
                m1.check_evidence_locators(
                    ROOT,
                    item.get("resolution_evidence_details"),
                    item["debt_id"],
                    errors,
                )
        self.assertEqual([], errors)

        changed = copy.deepcopy(
            next(item for item in debt["debts"] if item["debt_id"] == "QD-063")
        )
        changed["resolution_evidence_details"][0]["locator"] = "Missing Heading"
        m1.check_evidence_locators(
            ROOT,
            changed["resolution_evidence_details"],
            changed["debt_id"],
            errors,
        )
        assert_error_contains(self, errors, "does not resolve")

    def test_source_reference_fragments_must_resolve(self):
        errors: list[str] = []
        m1.check_reference_paths(
            ROOT,
            ["data/governance/specification_roadmap.json#/milestones/99"],
            "wrong pointer",
            errors,
        )
        m1.check_reference_paths(
            ROOT,
            ["docs/architecture/truth_authority_lattice.md#missing-heading"],
            "wrong heading",
            errors,
        )
        self.assertEqual(2, sum("unresolved repository reference" in error for error in errors))

    def test_platform_or_publication_claim_rejects(self):
        roadmap = copy.deepcopy(load_json(m1.ROADMAP_PATH))
        roadmap["publication"]["state"] = "published"
        roadmap["platform_gate"]["platform_work_authorized"] = True
        errors: list[str] = []
        m1.check_provisional_debt_and_roadmap(roadmap, load_json(m1.DEBT_PATH), errors)
        assert_error_contains(self, errors, "publication")
        assert_error_contains(self, errors, "authorizes platform work")

    def test_m0_evidence_change_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path in m1.M0_IMMUTABLE_PATHS:
                write_text(root, relative_path, "changed\n")
            with (
                patch.object(m1, "introduction_commit", return_value="a" * 40),
                patch.object(m1, "git_blob", return_value=b"original\n"),
            ):
                errors: list[str] = []
                m1.check_m0_immutable(root, errors)
            self.assertEqual(2, sum("Immutable M0 acceptance artifact changed" in error for error in errors))

    def test_m1_evidence_may_use_non_parent_baseline_ancestor(self):
        baseline_sha = "a" * 40
        evidence_commit = "c" * 40
        evidence = {
            "baseline": {
                "base_ref": "origin/main",
                "base_sha": baseline_sha,
                "merge_base": baseline_sha,
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path in m1.M1_EVIDENCE_PATHS:
                write_text(root, relative_path, "{}\n")

            def introduction(_root: Path, relative_path: str) -> str:
                return evidence_commit if relative_path == m1.EVIDENCE_PATH else "d" * 40

            def git_blob(_root: Path, _commit: str, relative_path: str) -> bytes:
                return (root / relative_path).read_bytes()

            completed = subprocess.CompletedProcess([], 0, "", "")
            with (
                patch.object(m1, "introduction_commit", side_effect=introduction),
                patch.object(m1, "git_blob", side_effect=git_blob),
                patch.object(m1, "run_git", return_value=completed),
                patch.object(m1, "checked_git_value", return_value=baseline_sha),
            ):
                errors: list[str] = []
                m1.check_m1_evidence_immutable_and_historical(root, evidence, errors)
            self.assertEqual([], errors)

    def test_m1_evidence_change_after_introduction_rejects(self):
        evidence = {"baseline": {"base_sha": "a" * 40, "merge_base": "a" * 40}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path in m1.M1_EVIDENCE_PATHS:
                write_text(root, relative_path, "changed\n")
            completed = subprocess.CompletedProcess([], 0, "", "")
            with (
                patch.object(m1, "introduction_commit", return_value="c" * 40),
                patch.object(m1, "git_blob", return_value=b"original\n"),
                patch.object(m1, "run_git", return_value=completed),
                patch.object(m1, "checked_git_value", return_value="a" * 40),
            ):
                errors: list[str] = []
                m1.check_m1_evidence_immutable_and_historical(root, evidence, errors)
            self.assertEqual(2, sum("Immutable M1 acceptance artifact changed" in error for error in errors))

    def test_external_platform_and_attribution_failures_propagate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path in (
                m1.SYNC_SCRIPT_PATH,
                m1.PLATFORM_CHECK_PATH,
                m1.ATTRIBUTION_CHECK_PATH,
            ):
                write_text(root, relative_path, "# placeholder\n")
            results = [
                subprocess.CompletedProcess([], 0, "ok", ""),
                subprocess.CompletedProcess([], 1, "", "platform claim"),
                subprocess.CompletedProcess([], 1, "", "policy violation"),
            ]
            with patch.object(m1.subprocess, "run", side_effect=results):
                errors: list[str] = []
                m1.check_external_guardrails(root, errors)
            assert_error_contains(self, errors, "Platform boundary validation failed")
            assert_error_contains(self, errors, "Repository attribution policy validation failed")

    def test_schema_named_roadmap_transition_accepts_and_old_names_reject(self):
        evidence = {
            "roadmap_transition": {
                "completed_milestone": "M1",
                "activated_milestone": "M2",
                "current_milestone": "M2",
            }
        }
        errors: list[str] = []
        m1.check_evidence_transition(evidence, errors)
        self.assertEqual([], errors)
        evidence["roadmap_transition"] = {
            "completed_milestone": "M1",
            "next_milestone": "M2",
            "current_milestone_after_acceptance": "M2",
        }
        m1.check_evidence_transition(evidence, errors)
        assert_error_contains(self, errors, "roadmap transition is invalid")

    def test_m1_catalog_checks_require_literal_m1_group(self):
        catalog = copy.deepcopy(load_json(m1.CHECK_CATALOG_PATH))
        for check in catalog["checks"]:
            if check["id"] in {"ash_specification_sync", "m1_canon_governance"}:
                check["groups"] = [group for group in check["groups"] if group != "m1"]
        errors: list[str] = []
        m1.check_catalog_m1_groups(catalog, errors)
        self.assertEqual(2, sum("literal m1 group" in error for error in errors))

    def test_historical_catalog_and_digest_ignore_future_live_changes(self):
        catalog = {"checks": [{"contexts": ["always"]}]}
        catalog_bytes = json.dumps(catalog).encode("utf-8")
        snapshot = {
            "VERSION": b"2.0.23\n",
            m1.CHECK_CATALOG_PATH: catalog_bytes,
            "contract.md": b"accepted\n",
        }
        summary = "two checks passed"
        evidence = {
            "check_catalog": {
                "path": m1.CHECK_CATALOG_PATH,
                "hash_algorithm": "sha256_utf8_lf_normalized",
                "sha256": m1.hashlib.sha256(catalog_bytes).hexdigest(),
            },
            "validation_runs": [
                {
                    "context": "local",
                    "check_count": 1,
                    "passed": 1,
                    "result_summary": summary,
                    "result_summary_sha256": m1.hashlib.sha256(summary.encode()).hexdigest(),
                },
                {
                    "context": "pull_request",
                    "check_count": 1,
                    "passed": 1,
                    "result_summary": summary,
                    "result_summary_sha256": m1.hashlib.sha256(summary.encode()).hexdigest(),
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_text(root, m1.CHECK_CATALOG_PATH, '{"future": true}\n')
            errors: list[str] = []
            m1.check_evidence_catalog_and_runs(root, evidence, catalog, errors, snapshot)
            expected_digest = m1.repository_state_digest_from_files(
                snapshot,
                set(m1.M1_EVIDENCE_PATHS),
                errors,
            )
            write_text(root, "contract.md", "future change\n")
            actual_again = m1.repository_state_digest_from_files(
                snapshot,
                set(m1.M1_EVIDENCE_PATHS),
                errors,
            )
        self.assertEqual(expected_digest, actual_again)
        self.assertEqual([], errors)

    def test_historical_diff_excludes_evidence_pair_and_validates_counts(self):
        binary_diff = subprocess.CompletedProcess([], 0, b"binary diff", b"")
        name_status = subprocess.CompletedProcess(
            [],
            0,
            "A\tnew.md\nM\texisting.md\n",
            "",
        )
        errors: list[str] = []
        with patch.object(m1.subprocess, "run", side_effect=[binary_diff, name_status]) as runner:
            review = m1.historical_diff_review(
                ROOT,
                "a" * 40,
                "b" * 40,
                errors,
            )
        self.assertEqual([], errors)
        self.assertIsNotNone(review)
        assert review is not None
        self.assertEqual(1, review["files_created"])
        self.assertEqual(1, review["files_patched"])
        self.assertEqual(
            "sha256_git_diff_binary_excluding_m1_evidence",
            review["diff_hash_algorithm"],
        )
        for call in runner.call_args_list:
            arguments = call.args[0]
            self.assertIn(f":(exclude){m1.EVIDENCE_PATH}", arguments)
            self.assertIn(f":(exclude){m1.EVIDENCE_DOCUMENT_PATH}", arguments)

    def test_evidence_classification_and_scope_metrics_are_snapshot_derived(self):
        classification = {
            "tracked_path_snapshot": {"path_count": 12},
            "coverage": {
                "counts_by_class": {
                    "normative": 4,
                    "informative": 2,
                    "example": 1,
                    "historical": 2,
                    "deprecated": 1,
                    "superseded": 1,
                    "placeholder": 1,
                }
            },
        }
        scope = {
            "coverage": {
                "counts_by_partition": {
                    "ywe_core": 2,
                    "ywe_extension_profile": 2,
                    "ash_dependency_material": 2,
                    "wrw_reference_profile": 2,
                    "governance_validation": 2,
                    "historical_evidence": 1,
                    "later_release_work": 1,
                }
            }
        }
        self.assertEqual(
            {
                "tracked_paths": 12,
                "classified_paths": 12,
                "unclassified_paths": 0,
                "multiply_classified_paths": 0,
                "normative": 4,
                "informative": 2,
                "example": 1,
                "historical": 2,
                "deprecated": 1,
                "superseded": 1,
                "placeholder": 1,
            },
            m1.evidence_classification_metrics(classification),
        )
        self.assertEqual(
            scope["coverage"]["counts_by_partition"],
            m1.evidence_scope_metrics(scope),
        )

    def test_changed_normative_artifact_outside_static_tuple_requires_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_text(root, "contracts/new_rule.yaml", "rule: This MUST remain stable.\n")
            assignments = {
                "contracts/new_rule.yaml": {"classification": "normative"},
            }
            snapshot = {
                "contracts/new_rule.yaml": b"rule: descriptive baseline\n",
            }
            errors: list[str] = []
            m1.check_temporal_normative_clauses(root, assignments, snapshot, errors)
            assert_error_contains(self, errors, "lacks a stable requirement identifier")


if __name__ == "__main__":
    unittest.main()
