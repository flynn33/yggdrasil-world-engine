# Remediation Baseline Inventory

Phase: `phase_0`  
Branch: `remediation/cosmology-authority-stack`  
Commit: `75ef9ec4ab969c8f2ca66c98bbce9aa9f3dfba00`  
Working tree: `clean`

## Repository Size

Tracked files: `361`

## Files By Extension

| Extension | Count |
|---|---:|
| `.json` | 68 |
| `.md` | 206 |
| `.ps1` | 12 |
| `.py` | 16 |
| `.sh` | 1 |
| `.txt` | 3 |
| `.yaml` | 42 |
| `.yml` | 10 |
| `[no extension]` | 3 |

## Existing Validation Scripts And Workflows

- `.github/workflows/branch-guard.yml`
- `.github/workflows/discussion-agents.yml`
- `.github/workflows/discussion-moderation.yml`
- `.github/workflows/discussion-topic-seeder.yml`
- `.github/workflows/forsetti-compliance.yml`
- `.github/workflows/main-ci.yml`
- `.github/workflows/no-ai-contributor-agent.yml`
- `.github/workflows/stale.yml`
- `.github/workflows/versioning.yml`
- `.github/workflows/wiki-sync.yml`
- `scripts/github/Sync-Wiki.ps1`
- `scripts/github/Test-ArchitectureDrift.ps1`
- `scripts/github/Test-CanonicalTruthBoundaries.ps1`
- `scripts/github/Test-DocsAndGlossary.ps1`
- `scripts/github/Test-ForsettiCompliance.ps1`
- `scripts/github/Test-ModuleContractCoverage.ps1`
- `scripts/github/Test-NoAIContributors.ps1`
- `scripts/github/Test-ReleaseReadiness.ps1`
- `scripts/github/Test-SchemaIntegrity.ps1`
- `scripts/github/Update-MissingSourceDocuments.ps1`
- `scripts/github/Update-VersionAndChangelog.ps1`
- `scripts/github/discussion_agent.py`
- `scripts/github/discussion_moderation_agent.py`
- `scripts/github/discussion_topic_agent.py`
- `scripts/requirements.txt`
- `scripts/run_checks.ps1`
- `scripts/run_checks.sh`
- `scripts/validate_architecture.py`
- `scripts/validate_ash_compliance.py`
- `scripts/validate_schemas.py`

## Baseline Check Results

| Check | Result | Notes |
|---|---|---|
| `bash scripts/run_checks.sh` | passed | 10 passed, 0 failed |
| `python3 scripts/validate_architecture.py .` | passed | Architecture validation passed |
| `python3 scripts/validate_schemas.py .` | passed | Schema validation passed |
| `python3 scripts/validate_ash_compliance.py .` | passed | ASH compliance validation passed |

## High-Risk Paths Expected To Be Touched

- `README.md`
- `docs/master_specification/YWE_MASTER_SPECIFICATION.md`
- `docs/architecture/README.md`
- `docs/architecture/ywe_invariant_guardrails.md`
- `docs/architecture/ywe_module_design_contracts.md`
- `docs/architecture/ywe_cross_module_dependency_map.md`
- `docs/architecture/ash_downstream_contract.md`
- `docs/architecture/ash_upstream_authority_contract.md`
- `docs/ash_compliance/ash_compliance_checklist.md`
- `core/narrative_engine/ash_runtime_generation_flow.yaml`
- `conformance/acceptance-judgment.md`
- `conformance/generation-system-conformance.md`
- `missing_source_documents.md`
- `SOURCE_AVAILABILITY_MANIFEST.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/scripts/ywe_package_acceptance_check.py`

## Paths Intentionally Preserved

- `core/ash_pattern_engine/canonical/**`
- `specs/**`
- `lore/**`
- `data/realm_registry/**`
- `data/bloodline_registry/**`
- `modules/*/engine_interface.json`
- `conformance/** (context notes only)`
- `docs/handoff/** (no destructive changes)`

## Phase 0 Gate

Gate 0 passed: baseline reports exist, no deletions occurred, existing checks passed, and high-risk paths are identified.
