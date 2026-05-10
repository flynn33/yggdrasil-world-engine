# Missing Source Documents

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: updated after ASH foundation normalization, faction topology stabilization, and module capability application

## Source bundles merged

- C:\Users\james\Downloads\yggdrasil-world-engine-codex-handoff.zip
- C:\Users\james\Downloads\Forsetti-Framework-Windows-main.zip
- C:\Users\james\Downloads\ASH_FOUNDATION_PACK_FOR_CODEX.zip
- C:\Users\james\Downloads\faction_topology_state_schema.yaml

## Inventory Status Summary

- Resolved canonical artifacts in active repo inventory: `12`
- Blocking missing artifacts in active repo inventory: `0`
- Intentional placeholder-backed artifacts still tracked: `14`
- Master spec authority artifact: present at `docs/master_specification/YWE_MASTER_SPECIFICATION.md`
- Bootstrap prompt authority artifact: present at `YWE_REPOSITORY_BOOTSTRAP_PROMPT.md`
- ASH/ASP core math rebuild overlay: present on `ash-remediation`

## Resolved Canonical Artifacts (Active Repo Inventory)

- data/perception/perception_overlay_rules.yaml
- data/realm/realm_mechanics_rules.yaml
- data/module_capability/module_capability_manifest_schema.yaml
- data/module_capability/manifests/*.yaml
- data/faction_topology/faction_topology_state_schema.yaml
- data/realm/realm_boundary_profiles.yaml
- data/realm/realm_transition_examples.yaml
- lore/wrw_cosmology/first_darkness_and_divine_core.md
- lore/wrw_cosmology/trial_of_return_michael_lucifer_odin.md
- lore/wolf_canon/two_wolves_and_balance.md
- docs/architecture/authored_override_and_tooling_notes.md
- docs/architecture/realm_truth_boundary_contract.md

## Blocking Missing Artifacts (Active Repo Inventory)

- none currently tracked

## Finalized source documents now present

- YWE_CODEX_GITHUB_BUILD_PACKAGE.md
- YWE_MASTER_SPECIFICATION.md
- YWE_REPOSITORY_BOOTSTRAP_PROMPT.md
- ASH_PATTERN_ARCHETYPE_LIBRARY_CANONICAL.md
- ASH_PATTERN_ARCHETYPE_LIBRARY_V0_2_PRIOR_HANDOFF.md
- ash_pattern_registry_schema.yaml
- ash_downstream_contract.md
- faction_topology_state_schema.yaml
- ywe_design_glossary.md
- ash_compliance_checklist.md
- artifact_system_rules.yaml
- creature_system_rules.yaml
- specs/
- core/ash_pattern_engine/canonical/
- data/schemas/ash_generation_packet_schema.json
- data/validation/ash_generation_gate_contract.json
- conformance/
- .github/scripts/ywe_package_acceptance_check.py

## ASH/ASP Core Math Rebuild Overlay

The active `ash-remediation` branch applies the
`YWE_ASP_CORE_MATH_REBUILD_PACKAGE` to the restored repository baseline.
Existing planning documents, engine interfaces, rule files, data records, and
handoff records remain present. The rebuild extends those files with
`CosmicPatternSnapshot`, `DiagnosticEnvelope`, `GenerationPlan`, and
source-ASH provenance contracts rather than replacing the design content.

## Locally Authored During Forsetti Compliance Pass

- docs/governance/forsetti_governance_alignment.md
- docs/architecture/engine_interface_contracts.md
- docs/architecture/ywe_module_design_contracts.md
- docs/architecture/ywe_cross_module_dependency_map.md
- docs/architecture/ywe_invariant_guardrails.md
- docs/architecture/ywe_canonical_data_domains.md
- docs/handoff/repo_implementation_mapping.md
- docs/architecture/forsetti_module_manifest_conventions.md

## Locally Authored During ASH Normalization Pass

- data/pattern_archetypes/character_archetypes.yaml
- data/quest_archetypes/quest_archetypes.yaml
- data/pattern_archetypes/region_archetypes.yaml
- data/pattern_archetypes/faction_archetypes.yaml
- data/pattern_archetypes/transformation_archetypes.yaml
- data/pattern_archetypes/event_archetypes.yaml
- data/pattern_archetypes/pattern_clusters.yaml
- data/pattern_archetypes/generation_rules.yaml
- data/pattern_archetypes/compatibility_matrix.yaml
- docs/architecture/COMPATIBILITY_MATRIX_NOTES.md
- docs/architecture/ASH_PATTERN_ARCHETYPE_LIBRARY_V0_2.md

## Locally Authored During Faction Topology Stabilization Pass

- data/faction_topology/README.md
- legacy data/factions duplicate surfaces were retired during later canonical reconciliation

## Locally Authored During Module Capability Application Pass

- data/module_capability/manifests/cosmology_engine.yaml
- data/module_capability/manifests/realm_engine.yaml
- data/module_capability/manifests/ash_pattern_engine.yaml
- data/module_capability/manifests/narrative_engine.yaml
- data/module_capability/manifests/perception_engine.yaml
- data/module_capability/manifests/quest_engine.yaml
- data/module_capability/manifests/myth_engine.yaml
- data/module_capability/manifests/prophecy_engine.yaml
- data/module_capability/manifests/artifact_engine.yaml
- data/module_capability/manifests/creature_engine.yaml

## Locally Authored During Lore Canon Correction Pass

- lore/wrw_cosmology/first_darkness_and_divine_core.md
- lore/wrw_cosmology/trial_of_return_michael_lucifer_odin.md
- lore/wolf_canon/two_wolves_and_balance.md

## Intentional Placeholder-Backed Artifacts

- player_origin_arc_rules.yaml
- PLAYER_ORIGIN_ARC_NOTES.md
- npc_synthesis_rules.yaml
- NPC_SYNTHESIS_NOTES.md
- quest_chain_templates.yaml
- QUEST_CHAIN_TEMPLATE_NOTES.md
- ash_runtime_generation_flow.yaml
- ASH_RUNTIME_GENERATION_FLOW_NOTES.md
- worldstate_delta_rules.yaml
- WORLDSTATE_DELTA_RULES_NOTES.md
- myth_emergence_rules.yaml
- MYTH_EMERGENCE_RULES_NOTES.md
- prophecy_activation_rules.yaml
- PROPHECY_ACTIVATION_RULES_NOTES.md

## Extra Handoff Documents Added

- SOURCE_AVAILABILITY_MANIFEST.md
- docs/architecture/YWE_Myth_Emergence_Design.md
- docs/glossary/YWE_Design_Glossary_source.txt
- docs/handoff/YWE_NEXT_THREAD_BRIEF_2026-03-13_v2.md
- docs/handoff/YWE_Planning_Phase_0.md
