# Source Availability Manifest

This manifest maps referenced source artifacts to their current repository
locations.
## Supplied with content
- `ASH_PATTERN_ARCHETYPE_LIBRARY_CANONICAL.md` -> `docs/architecture/ASH_PATTERN_ARCHETYPE_LIBRARY_CANONICAL.md`
- `ash_pattern_registry_schema.yaml` -> `data/pattern_archetypes/ash_pattern_registry_schema.yaml`
- `ash_downstream_contract.md` -> `docs/architecture/ash_downstream_contract.md`
- `ASH_PATTERN_ARCHETYPE_LIBRARY_V0_2_PRIOR_VERSION.md` -> `docs/architecture/ASH_PATTERN_ARCHETYPE_LIBRARY_V0_2.md`
- `faction_topology_state_schema.yaml` -> `data/faction_topology/faction_topology_state_schema.yaml`
- `module_capability_manifest_schema.yaml` -> `data/module_capability/module_capability_manifest_schema.yaml`
- `ywe_design_glossary.md` -> `docs/glossary/ywe_design_glossary.md`
- `ash_compliance_checklist.md` -> `docs/ash_compliance/ash_compliance_checklist.md`
- `artifact_system_rules.yaml` -> `modules/artifact_engine/artifact_system_rules.yaml`
- `creature_system_rules.yaml` -> `modules/creature_engine/creature_system_rules.yaml`
- `YWE_ASP_CORE_MATH_REBUILD_PACKAGE` -> `specs/`, `core/ash_pattern_engine/canonical/`, `data/schemas/ash_generation_packet_schema.json`, `data/validation/ash_generation_gate_contract.json`
- `YWE_ASP_CORE_MATH_REBUILD_PACKAGE.conformance` -> `conformance/`
- `YWE_ASP_CORE_MATH_REBUILD_PACKAGE.validators` -> `.github/scripts/ywe_package_acceptance_check.py`, `.github/scripts/semantic_integrity_check.py`, `.github/scripts/downstream_conformance_check.py`, `.github/scripts/math_integrity_check.py`
- `cosmology_authority_contracts` -> `docs/architecture/ywe_cosmology_authority_contract.md`, `docs/architecture/ash_pattern_system_component_contract.md`, `docs/architecture/ash_cosmological_model_source_map.md`, `data/validation/cosmology_authority_gate_contract.json`, `data/validation/repository_drift_guardrail_rules.json`

## Present as placeholders
- `player_origin_arc_rules.yaml` -> `core/narrative_engine/player_origin_arc_rules.yaml`
- `PLAYER_ORIGIN_ARC_NOTES.md` -> `docs/architecture/PLAYER_ORIGIN_ARC_NOTES.md`
- `npc_synthesis_rules.yaml` -> `core/narrative_engine/npc_synthesis_rules.yaml`
- `NPC_SYNTHESIS_NOTES.md` -> `docs/architecture/NPC_SYNTHESIS_NOTES.md`
- `quest_chain_templates.yaml` -> `modules/quest_engine/quest_chain_templates.yaml`
- `QUEST_CHAIN_TEMPLATE_NOTES.md` -> `docs/architecture/QUEST_CHAIN_TEMPLATE_NOTES.md`
- `ash_runtime_generation_flow.yaml` -> `core/narrative_engine/ash_runtime_generation_flow.yaml`
- `ASH_RUNTIME_GENERATION_FLOW_NOTES.md` -> `docs/architecture/ASH_RUNTIME_GENERATION_FLOW_NOTES.md`
- `worldstate_delta_rules.yaml` -> `core/narrative_engine/worldstate_delta_rules.yaml`
- `WORLDSTATE_DELTA_RULES_NOTES.md` -> `docs/architecture/WORLDSTATE_DELTA_RULES_NOTES.md`
- `myth_emergence_rules.yaml` -> `modules/myth_engine/myth_emergence_rules.yaml`
- `MYTH_EMERGENCE_RULES_NOTES.md` -> `docs/architecture/MYTH_EMERGENCE_RULES_NOTES.md`
- `prophecy_activation_rules.yaml` -> `modules/prophecy_engine/prophecy_activation_rules.yaml`
- `PROPHECY_ACTIVATION_RULES_NOTES.md` -> `docs/architecture/PROPHECY_ACTIVATION_RULES_NOTES.md`
- `repo_implementation_mapping.md` -> `docs/project/repository_map.md`
- `engine_interface_contracts.md` -> `docs/architecture/engine_interface_contracts.md`
- `forsetti_governance_alignment.md` -> `docs/governance/forsetti_governance_alignment.md`
- `ywe_module_design_contracts.md` -> `docs/architecture/ywe_module_design_contracts.md`
- `ywe_canonical_data_domains.md` -> `docs/architecture/ywe_canonical_data_domains.md`
- `ywe_cross_module_dependency_map.md` -> `docs/architecture/ywe_cross_module_dependency_map.md`
- `ywe_invariant_guardrails.md` -> `docs/architecture/ywe_invariant_guardrails.md`

## ASH/ASP core math rebuild

The current repository state includes the ASH/ASP core math rebuild as canonical
source content. Existing planning, engine, rule, data, and exchange documents
remain present; the alignment adds ASH provenance, diagnostic, and
materialization contracts in place rather than replacing the original design
content.

## Cosmology Authority Alignment

The current authority stack clarifies that the ASH Cosmological Model is the
upstream foundation for YWE and its systems, while the ASH Pattern System is a
YWE component for diagnostics, pattern integrity, recovery, containment,
resilience, conformance, and update/patch stability. Prior ASH Pattern System
conformance work remains accepted and preserved as component evidence under the
corrected authority stack.
