# Governance Documentation Index

Project: Yggdrasil World Engine
Status: active governance index
Current baseline: `v2.0.23`

## Purpose

Governance documents describe how the repository preserves architecture
authority, contributor workflow, automation, validation, and Forsetti-aligned
lifecycle rules.

## Documents

| File | Role |
|---|---|
| `forsetti_governance_alignment.md` | Maps YWE truth ownership to Forsetti-compatible governance boundaries. |
| `normative_language_and_requirement_id_policy.md` | Defines normative keywords and stable `YWE-REQ` identifiers. |
| `governance_records_policy.md` | Defines ADR, change-proposal, risk, deviation, and question lifecycles. |
| `github_automation_agents.md` | Documents repository workflow automation and validation responsibilities. |
| `../architecture/truth_authority_lattice.md` | Defines typed truth, state, interpretation, host, and lifecycle-governance relationships. |
| `../architecture/ywe_core_wrw_scope_contract.md` | Separates setting-neutral YWE Core from the WRW reference profile. |
| `../project/artifact_classification_policy.md` | Defines primary maturity classes and exact-one classification. |
| `../project/scope_partition_map.md` | Defines exact-one repository scope partitions. |
| `../project/release_and_publication_policy.md` | Defines baseline, tag, changelog, and publication semantics. |
| `../../data/governance/repository_truth_manifest.json` | Records current machine-readable repository truth. |
| `../../data/governance/public_promise_register.json` | Assigns or excludes reviewed public promises. |
| `../../data/governance/normative_requirement_register.json` | Records stable normative requirements and verification references. |
| `../../data/governance/governance_record_register.json` | Records typed governance decisions, proposals, risks, deviations, and questions. |
| `../../data/governance/truth_authority_lattice.json` | Records the machine-readable ten-node authority lattice. |
| `../../data/governance/ash_dependency_identity.json` | Pins the authoritative ASH dependency content identity. |
| `../../data/governance/canonical_term_index.json` | Indexes canonical glossary concepts without duplicating definition prose. |
| `../../data/validation/repository_quality_debt_inventory.json` | Registers ratcheted repository quality debt. |
| `../project/M0_TRUTHFUL_BASELINE_ACCEPTANCE.md` | Records the human-readable M0 acceptance evidence. |

## Workflow Entry Points

| Workflow | File |
|---|---|
| Canonical validation | `../../scripts/validate_repository.py` |
| Check catalog | `../../data/validation/repository_checks.json` |
| M1 canon and governance check | `../../scripts/check_m1_canon_governance.py` |
| ASH source/mirror synchronization | `../../scripts/sync_ash_specifications.py` |
| Main validation workflow | `../../.github/workflows/main-ci.yml` |
| Wiki sync | `../../.github/workflows/wiki-sync.yml` |
| Version and changelog | `../../.github/workflows/versioning.yml` |
| Contributor identity gate | [`../../.github/workflows/contributor-identity-policy.yml`](../../.github/workflows/contributor-identity-policy.yml) |

## Governance Rules

- Forsetti governs module lifecycle, activation policy, and structural
  consistency.
- YWE governs cosmology truth, source-truth hierarchy, runtime contracts, and
  domain meaning.
- ASH Pattern System remains a YWE component for diagnostics, recovery,
  containment, conformance, code resilience, update safety, and patch stability.
- Automation may validate, sync, seed, and moderate within documented
  boundaries; it does not invent canon or bypass accepted package gates.
- `VERSION` is the canonical repository-baseline source; publication remains
  unreleased until the M10 eligibility gate is accepted.
