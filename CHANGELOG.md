# Changelog

All notable changes to the Yggdrasil World Engine are documented here.

---


## [2.0.12] — 2026-05-18

### Added
- Merge pull request #49 from flynn33/phase-10-player-runtime-state-v1
- Address Phase 10 follow-up review
- Address Phase 10 review feedback
- Implement Phase 10 player runtime state

### Changed
- Refactor Phase 10 JSON target parsing

### Fixed
- Resolve Phase 10 review findings


---


## [2.0.11] — 2026-05-17

### Added
- Add Phase 8-9 boundary remediation

### Fixed
- Merge pull request #48 from flynn33/audit-fix/phase-8-9-remediation


---


## [2.0.10] — 2026-05-17

### Added
- Merge pull request #46 from flynn33/codex/phase-12-quest-npc-lore-generation-v1
- docs: add phase 12 quest npc lore generation


---


## [2.0.9] — 2026-05-17

### Added
- Merge pull request #45 from flynn33/codex/phase-11-worldstate-location-mutation-v1
- docs: add phase 11 worldstate location mutation

### Fixed
- fix: tighten worldstate mutation validation


---


## [2.0.8] — 2026-05-17

### Added
- Merge pull request #44 from flynn33/phase/phase-10-player-runtime-state-v1
- docs: add phase 10 player runtime state

### Fixed
- fix: harden player runtime guardrail JSON handling


---


## [2.0.7] — 2026-05-17

### Added
- Merge pull request #43 from flynn33/phase/phase-8-9-branch-reality-foundation
- fix: address phase 9 review comments
- docs: add phase 9 branch reality foundation

### Fixed
- fix: address phase 9 review comments


---


## [2.0.6] — 2026-05-17

### Changes
- Merge pull request #42 from flynn33/phase/phase-8-baseline-freeze
- docs: freeze post-remediation baseline

---


## [2.0.5] — 2026-05-17

### Changes
- Merge pull request #41 from flynn33/phase/phase-7-acceptance-audit-resolution
- docs: accept phase 7 audit

---


## [2.0.4] — 2026-05-17

### Added
- Merge pull request #40 from flynn33/phase/phase-7-acceptance-audit-package
- docs: address phase 7 review feedback
- docs: add phase 7 acceptance audit


---


## [2.0.3] — 2026-05-16

### Changes
- Merge pull request #39 from flynn33/remediation/cosmology-authority-stack
- docs: align cosmology authority stack

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
