# YWE Source Truth Alignment Handoff

Date: 2026-05-19
Branch: `remediation/source-truth-twin-wolf-alignment`
Authoring record: repository maintainer

## Baseline checks

- Existing checks run before edits: `bash scripts/run_checks.sh`
- Baseline result: 14 passed, 0 failed
- Baseline notes: file inventory and drift search were recorded before remediation edits; no destructive action occurred before the baseline was known.

## Files added

Architecture contracts:

- `docs/architecture/ash_model_engine_cosmology_contract.md`
- `docs/architecture/cosmology_framework_extensibility_contract.md`
- `docs/architecture/dual_variable_alignment_model_contract.md`
- `docs/architecture/engine_vs_game_layer_contract.md`
- `docs/architecture/lineage_resonance_model_contract.md`
- `docs/architecture/twin_wolf_companion_canon_contract.md`

Schema contracts:

- `data/schemas/ash_pattern_system_component_role_schema.json`
- `data/schemas/dual_variable_alignment_state_schema.json`
- `data/schemas/engine_authority_stack_schema.json`
- `data/schemas/engine_cosmology_framework_schema.json`
- `data/schemas/lineage_resonance_state_schema.json`
- `data/schemas/twin_wolf_companion_state_schema.json`

Validation contracts and check specs:

- `data/validation/ash_model_cosmology_validation_rules.json`
- `data/validation/ash_pattern_system_component_validation_rules.json`
- `data/validation/check_ash_model_authority.spec.json`
- `data/validation/check_ash_pattern_system_component_role.spec.json`
- `data/validation/check_dual_variable_alignment_model.spec.json`
- `data/validation/check_engine_game_layer_separation.spec.json`
- `data/validation/check_lineage_resonance_model.spec.json`
- `data/validation/check_no_ash_pattern_system_topmost_authority.spec.json`
- `data/validation/check_no_wolf_morality_meter.spec.json`
- `data/validation/check_non_destructive_diff_source_truth.spec.json`
- `data/validation/check_wolf_companion_canon.spec.json`
- `data/validation/forbidden_language_patterns.json`
- `data/validation/github_checks_matrix.json`
- `data/validation/non_destructive_change_budget.json`
- `data/validation/required_artifacts.json`
- `data/validation/source_truth_alignment_contract.json`
- `data/validation/twin_wolf_canon_validation_rules.json`

Guardrail implementation:

- `scripts/check_source_truth_alignment.py`

Handoff:

- `docs/handoff/YWE_SOURCE_TRUTH_ALIGNMENT_HANDOFF_2026-05-19.md`

## Files modified

- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/ywe_repository_guardrails.yml`
- `README.md`
- `core/ash_pattern_engine/README.md`
- `core/cosmology_engine/cosmology_schema.json`
- `data/player_schema.json`
- `data/schemas/README.md`
- `data/schemas/player_schema.json`
- `docs/architecture/README.md`
- `docs/architecture/ash_downstream_contract.md`
- `docs/architecture/ash_pattern_system_component_contract.md`
- `docs/architecture/ywe_cross_module_dependency_map.md`
- `docs/architecture/ywe_invariant_guardrails.md`
- `docs/architecture/ywe_module_design_contracts.md`
- `docs/handoff/README.md`
- `docs/master_specification/YWE_MASTER_SPECIFICATION.md`
- `lore/wolf_canon/two_wolves_and_balance.md`
- `scripts/run_checks.sh`
- `scripts/validate_ash_compliance.py`
- `scripts/validate_schemas.py`

## Files intentionally not modified

- Platform runtime implementation files were not added or changed.
- Accepted feature-phase contracts were preserved and only aligned where source-truth wording was in scope.
- Package template text was not copied directly into this repository handoff; this file records the applied remediation result.

## Authority stack confirmation

Confirmed:

- ASH Model of the Universe is engine foundation.
- Yggdrasil World Engine is agnostic simulation framework.
- ASH Pattern System is YWE component.
- Where Ravens Wait: Eternal Reckoning is game / narrative layer.

## Twin Wolf canon confirmation

Confirmed:

- White Wolf and Dark Wolf are complementary opposites.
- The wolves are non-moral and are not good and evil.
- The wolves are embodied companions.
- The wolves assist quests.
- The wolves assist combat.
- The wolves cannot die.
- The wolves can temporarily decohere and return.
- Each wolf has what the other needs.

## Validation results

- `python3 scripts/validate_schemas.py .`: passed; 297 JSON files parsed and canonical checks passed.
- `python3 scripts/validate_ash_compliance.py .`: passed.
- `python3 scripts/check_source_truth_alignment.py .`: passed.
- `bash scripts/run_checks.sh`: passed; 15 passed, 0 failed.

## GitHub checks added or planned

Added:

- Repository guardrails workflow now runs `python scripts/check_source_truth_alignment.py`.
- Source-truth check specs and `github_checks_matrix.json` were added.
- `scripts/check_source_truth_alignment.py` enforces required artifacts, source-truth language, Twin Wolf canon phrases, forbidden source-truth drift, JSON integrity, required matrix specs, and non-destructive diff budget.
- The non-destructive diff guardrail resolves a real base ref and uses `git diff --name-status --find-renames` plus staged, unstaged, and untracked paths.

Planned:

- Separate workflow job names may be split out later if review wants each matrix check exposed as an individual check line. Current enforcement is active through the source-truth guardrail script.

## Deferred work

- No new feature-system package was started.
- Example fixtures from the remediation package remain optional because the accepted gate requires contracts, schemas, validation rules, check specs, and guardrail enforcement.

## Risks or review notes

- Existing historical handoffs and validation files still contain prior authority wording for provenance and compatibility. Active architecture and package-scope files now point to the ASH Model of the Universe foundation and ASH Pattern System component role.
- The remediation stayed within the non-destructive file budget: no deleted files and fewer than 25 existing files modified.
