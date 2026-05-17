# Remediation Changelog

## 2026-05-17 - Phase 8-9 Remediation Boundary Correction

### Added

- Added a Phase 8-9 package-boundary guardrail contract and script.
- Added explicit deferred-owner-review language for Phase 10 through Phase 12 artifacts that appeared before owner-approved package acceptance.
- Added Phase 9 handoff remediation notes using the Phase 8-9 review and handoff template.

### Changed

- Narrowly patched handoff, schema, architecture, and remediation indexes to state that Phase 10 through Phase 12 material is retained for owner review only.
- Added a master-spec supersession note using the Phase 8-9 authority language: the ASH Cosmological Model is the upstream foundation for YWE and its systems, and the ASH Pattern System is a YWE component for pattern integrity, diagnostics, recovery, containment, conformance, code resilience, and update/patch stability.
- Added controlled invalid-JSON and unreadable-file failure reporting to the Phase 8-9 package-boundary guardrail.
- Aligned `YWEInterpretationPacket` packet-index required fields with the referenced schema by adding `requested_manifest_kind`.

### Preserved

- Deleted no files.
- Preserved existing later-phase artifacts for owner review.
- Preserved accepted Phase 7 and Phase 8-9 artifacts.

## 2026-05-16 - Cosmology Authority Stack Alignment

### Added

- Added `docs/architecture/ywe_cosmology_authority_contract.md` for the current game/engine/foundation/component authority stack.
- Added `docs/architecture/ash_pattern_system_component_contract.md` to define ASH Pattern System as a YWE diagnostics, recovery, containment, conformance, resilience, and patch/update stability component.
- Added `docs/architecture/ash_cosmological_model_source_map.md` to map ASH Cosmological Model concepts to repository target areas.
- Added `data/schemas/authority_stack_schema.json`.
- Added `data/validation/cosmology_authority_gate_contract.json` and `data/validation/repository_drift_guardrail_rules.json`.
- Added repository guardrail scripts for JSON integrity, required contracts, authority-stack drift scanning, and non-destructive diff checks.
- Added `.github/workflows/ywe_repository_guardrails.yml`.
- Added baseline inventory and gate result remediation artifacts.

### Changed

- Updated README, master specification, architecture README, module contracts, dependency map, invariant guardrails, glossary, ASH compliance checklist, runtime generation flow metadata, source manifests, and selected conformance notes to reflect the corrected authority stack.
- Marked prior ASH upstream authority language as superseded component/packet-spine evidence instead of deleting it.
- Expanded the pull request template with authority-stack and destructive-change review fields.

### Preserved

- Preserved ASH Pattern System canonical math and conformance work.
- Preserved `specs/`, `core/ash_pattern_engine/canonical/`, `lore/`, `modules/`, and existing conformance artifacts.
- Deleted no files.
