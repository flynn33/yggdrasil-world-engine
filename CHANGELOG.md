# Changelog

All notable changes to the Yggdrasil World Engine are documented here.

---


## [2.0.2] — 2026-05-10

### Added
- Merge pull request #38 from flynn33/codex/ash-upstream-authority-clean
- Address upstream authority packet requirements
- Add ASH upstream authority contract

### Changed
- Update project documentation


---

## [Unreleased] — 2026-05-10

### Documentation
- Added the ASH upstream mathematical and generative authority contract and
  linked it through the downstream, runtime generation, master specification,
  module contract, dependency map, and invariant guardrail documentation.
- Added the shared upstream generation packet spine for exploration-driven
  world generation, player-action-driven quest/NPC generation, and
  consequence-driven future generation bias.
- Expanded README coverage for the ASH/ASP math baseline, system architecture, packet flow, and validation surfaces.
- Rebuilt the GitHub wiki as a comprehensive reference for architecture, engines, schemas, adapters, validation, and lore.
- Added visual workflow and logic diagrams for ASH state transformation, generation planning, materialization boundaries, realm/lore structure, and module interactions.
- Updated wiki lore coverage for WRW cosmology, wolf canon, and bloodline history.

### Schemas
- Added upstream-generation packet schemas for
  `ASHUpstreamGenerationEnvelope`, `YWEGenerationContextPacket`,
  `YWEInterpretationPacket`, `PlayerActionTrace`,
  `ExplorationFrontierRequest`, and `FutureGenerationBiasUpdate`.
- Added `ash_upstream_authority_gate_contract.json` and expanded the existing
  generation gate with upstream packet-spine markers and provenance fields.


## [2.0.1] — 2026-05-10

### Added
- Add discussion moderation bot
- Add repo-grounded discussion topic seeder
- Add repo-grounded discussion response agents
- Add no-AI contributor enforcement workflow
- feat: add faction topology state schema
- feat: add no-ai contributor validation agent
- feat: add repository governance agents [skip version]
- feat: add GitHub automation agents [skip version]
- Add GitHub automation: wiki sync, versioning, changelog, and Forsetti compliance

### Changed
- Merge duplicate repo history from flynn33/Yggdrasil-World-Engine-v2.0 into authoritative main (excluding workflow file changes)
- chore: update version and changelog to v0.4.0 [skip version]
- chore: update version and changelog to v0.3.0 [skip version]
- chore: update version and changelog to v0.2.0 [skip version]
- Add GitHub automation: wiki sync, versioning, changelog, and Forsetti compliance

### Fixed
- Fix Forsetti engine contract compliance
- Fix Forsetti compliance workflow to match actual schema field names
- Fix bash arithmetic in run_checks.sh for Linux compatibility


---

## [2.0.0] — 2026-03-11

### Added
- Complete repository rebuild from master specification
- Five core engines: Cosmology, Realm, ASH Pattern, Narrative, Perception
- Five expansion modules: Quest, Myth, Prophecy, Artifact, Creature
- Canonical data schemas for player state, realms, patterns, quests, myths, bloodlines
- Nine canonical realm definitions with expanded metadata
- Lore documentation: WRW Cosmology, Wolf Canon, Bloodline History
- Adapter specifications for Unity, Unreal, and Godot
- Architecture documentation with layer hierarchy
- ASH compliance rules and milestone checklist
- Forsetti Framework governance integration (v0.1.0)
- Validation scripts: architecture, schema, and ASH compliance
- CI workflows: main validation, branch guard, stale issue management
- Proprietary license (Jim Daley, all rights reserved)
- Contributor License Agreement
- GitHub wiki with comprehensive documentation
- Automated wiki sync workflow
- Automated versioning and changelog workflow
- Forsetti compliance enforcement workflow
