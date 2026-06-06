# Source Inventory

This index lists current source-truth assets and open placeholder-backed areas.
It replaces process-era source notes with stable repository routing.

## Current Authority Statements

- Yggdrasil World Engine is built on the ASH Model of the Universe.
- The ASH Model of the Universe is the mathematical and ontological foundation of the engine simulation layer.
- The ASH Pattern System is a YWE component for pattern integrity, diagnostics, recovery, containment, conformance, code resilience, update safety, and patch stability.
- Where Ravens Wait: Eternal Reckoning is the game and narrative layer.

## Twin Wolf Canon

- The White Wolf and Dark Wolf are complementary opposites.
- They are not good and evil.
- They are not a morality system.
- Each wolf has what the other needs.
- They physically walk with the player, assist in quests, and assist in combat.
- They cannot be killed; they can temporarily decohere and later return.

## Canonical Artifacts

| Area | Current source |
|---|---|
| Master specification | `docs/master_specification/YWE_MASTER_SPECIFICATION.md` |
| Repository map | `docs/project/repository_map.md` |
| Cosmology authority | `docs/architecture/ywe_cosmology_authority_contract.md` |
| ASH component role | `docs/architecture/ash_pattern_system_component_contract.md` |
| Realm truth boundary | `docs/architecture/realm_truth_boundary_contract.md` |
| Authored override boundary | `docs/architecture/authored_override_and_tooling_notes.md` |
| ASH math surface | `specs/`, `core/ash_pattern_engine/canonical/` |
| Generation packets | `data/schemas/ash_generation_packet_schema.json` |
| Source-truth validation | `data/validation/source_truth_alignment_contract.json` |
| Twin Wolf validation | `data/validation/twin_wolf_canon_validation_rules.json` |

## Placeholder-Backed Areas

These tracked files remain follow-up targets for finalized content:

- `core/narrative_engine/player_origin_arc_rules.yaml`
- `docs/architecture/PLAYER_ORIGIN_ARC_NOTES.md`
- `core/narrative_engine/npc_synthesis_rules.yaml`
- `docs/architecture/NPC_SYNTHESIS_NOTES.md`
- `modules/quest_engine/quest_chain_templates.yaml`
- `docs/architecture/QUEST_CHAIN_TEMPLATE_NOTES.md`
- `core/narrative_engine/ash_runtime_generation_flow.yaml`
- `docs/architecture/ASH_RUNTIME_GENERATION_FLOW_NOTES.md`
- `core/narrative_engine/worldstate_delta_rules.yaml`
- `docs/architecture/WORLDSTATE_DELTA_RULES_NOTES.md`
- `modules/myth_engine/myth_emergence_rules.yaml`
- `docs/architecture/MYTH_EMERGENCE_RULES_NOTES.md`
- `modules/prophecy_engine/prophecy_activation_rules.yaml`
- `docs/architecture/PROPHECY_ACTIVATION_RULES_NOTES.md`

## Update Discipline

When a placeholder-backed artifact is promoted, update this inventory, the
corresponding validation contract, and the local validation suite in the same
change set.
