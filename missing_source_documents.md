# Missing Source Documents

This inventory tracks three distinct repo-truth states:

- resolved canonical artifacts now present and enforced
- blocking missing artifacts that would break the active authority or canonical chain
- intentional placeholder-backed artifacts that remain tracked follow-up work

## Inventory Status Summary

- Resolved canonical artifacts: `12`
- Blocking missing artifacts: `0`
- Intentional placeholder-backed artifacts: `14`
- Master spec authority artifact: present at `docs/master_specification/YWE_MASTER_SPECIFICATION.md`
- Bootstrap prompt authority artifact: present at `YWE_REPOSITORY_BOOTSTRAP_PROMPT.md`
- ASH/ASP core math rebuild overlay: present on `ash-remediation`

## Resolved Canonical Artifacts

| Artifact | Status | Notes |
|---|---|---|
| `data/perception/perception_overlay_rules.yaml` | Canonical | Promoted with validation and truth-boundary checks |
| `data/realm/realm_mechanics_rules.yaml` | Canonical | Promoted with validation for attunement, boundaries, bleed, and shift law |
| `data/module_capability/module_capability_manifest_schema.yaml` | Canonical | Promoted as the canonical capability declaration and delegation-governance schema |
| `data/module_capability/manifests/*.yaml` | Canonical | Applied canonical capability declarations for the current core engines and feature modules |
| `data/faction_topology/faction_topology_state_schema.yaml` | Canonical | Promoted as the canonical faction topology state schema |
| `data/realm/realm_boundary_profiles.yaml` | Canonical | Promoted as boundary profile support artifact for realm mechanics |
| `data/realm/realm_transition_examples.yaml` | Canonical | Promoted as lawful/unlawful transition guidance support artifact |
| `lore/wrw_cosmology/first_darkness_and_divine_core.md` | Canonical | Promoted as the corrected origin cosmology authority covering Dark Star, Divine Core, realms or planes, Architects, and first wolves |
| `lore/wrw_cosmology/trial_of_return_michael_lucifer_odin.md` | Canonical | Promoted as the corrected lore authority for the Great Trial, Michael, Lucifer, Odin, Yggdrasil, and mortal reintegration |
| `lore/wolf_canon/two_wolves_and_balance.md` | Canonical | Promoted as the corrected wolf canon authority for symbiosis, balance, and temporary coherence loss |
| `docs/architecture/authored_override_and_tooling_notes.md` | Canonical | Promoted as authored-control and tooling boundary authority |
| `docs/architecture/realm_truth_boundary_contract.md` | Canonical | Promoted as boundary contract separating truth and interpretive layers |

## ASH/ASP Core Math Rebuild Artifacts

These artifacts are present as the active remediation overlay. They do not
replace the restored planning documents; they extend the existing engine,
schema, and rule surfaces with the required ASH math provenance.

| Artifact | Status | Notes |
|---|---|---|
| `specs/` | Canonical math overlay | Mirrors the ASH `F2^9` state-space, codeword, transition, diagnostics, and verification specifications |
| `core/ash_pattern_engine/canonical/` | Canonical math overlay | Repo-local copy of the ASH canonical pseudo-spec surface |
| `data/schemas/ash_generation_packet_schema.json` | Canonical packet schema | Defines `CosmicPatternSnapshot`, `DiagnosticEnvelope`, and `GenerationPlan` |
| `data/validation/ash_generation_gate_contract.json` | Validation contract | Enumerates the rebuilt YWE generation systems and adapter boundaries |
| `conformance/` | Evidence | Records governance, deviation, materialization, module mapping, verification, and acceptance judgment |
| `.github/scripts/ywe_package_acceptance_check.py` | Validator | Blocks stale math language and missing ASH provenance across the rebuilt systems |

## Blocking Missing Artifacts

- None currently tracked in this repository snapshot.

## Intentional Placeholder-Backed Artifacts

These items remain intentionally placeholder-backed and are the clearest
remaining concrete follow-up targets before inventing new subsystem layers.

- `player_origin_arc_rules.yaml`
- `PLAYER_ORIGIN_ARC_NOTES.md`
- `npc_synthesis_rules.yaml`
- `NPC_SYNTHESIS_NOTES.md`
- `quest_chain_templates.yaml`
- `QUEST_CHAIN_TEMPLATE_NOTES.md`
- `ash_runtime_generation_flow.yaml`
- `ASH_RUNTIME_GENERATION_FLOW_NOTES.md`
- `worldstate_delta_rules.yaml`
- `WORLDSTATE_DELTA_RULES_NOTES.md`
- `myth_emergence_rules.yaml`
- `MYTH_EMERGENCE_RULES_NOTES.md`
- `prophecy_activation_rules.yaml`
- `PROPHECY_ACTIVATION_RULES_NOTES.md`

### Support Pass Status (2026-03-14)

- `FOUND` `data/faction_topology/faction_topology_state_schema.yaml`
- `FOUND` `docs/architecture/realm_truth_boundary_contract.md`
- `FOUND` `data/realm/realm_transition_examples.yaml`
- `FOUND` `data/realm/realm_boundary_profiles.yaml`
- `FOUND` `data/module_capability/module_capability_manifest_schema.yaml`
- `FOUND` `data/module_capability/manifests/*.yaml`
- `FOUND` `lore/wrw_cosmology/first_darkness_and_divine_core.md`
- `FOUND` `lore/wrw_cosmology/trial_of_return_michael_lucifer_odin.md`
- `FOUND` `lore/wolf_canon/two_wolves_and_balance.md`

### Inventory Interpretation

- The canonical promotion list above is current and validated.
- No blocking missing authority-chain or canonical artifacts are currently tracked.
- The placeholder-backed list above reflects tracked repo work that still needs finalized source-backed content.
- Structural placeholders outside this tracked set may still exist elsewhere in the repo, but they are not currently treated as promoted canonical-support gaps.

## Update Discipline

When promoting a canonical artifact in this repository:

1. Merge the artifact into canonical path.
2. Update this inventory in the same change set.
3. Update validation scripts in the same change set.
4. Run `bash scripts/run_checks.sh` on POSIX shells or `pwsh -File scripts/run_checks.ps1` on Windows before completion.
