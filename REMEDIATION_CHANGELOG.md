# Remediation Changelog

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
