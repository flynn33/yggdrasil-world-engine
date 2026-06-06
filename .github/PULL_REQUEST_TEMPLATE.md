## Summary

Brief description of changes.

## Type of Change

- [ ] Specification change (main branch)
- [ ] Engine implementation (engine branch)
- [ ] Documentation update
- [ ] Tooling / scripts
- [ ] Bug fix

## ASH Compliance

- [ ] No ASH cosmological violations introduced
- [ ] All procedural generation derives from ASH cosmic pattern state under the ASH Model of the Universe
- [ ] No independent random generators for meaningful content

## Authority Stack Guardrails

- [ ] Authority stack reviewed: yes/no
- [ ] The ASH Model of the Universe remains the mathematical and ontological foundation
- [ ] Yggdrasil World Engine remains the agnostic simulation framework
- [ ] ASH Pattern System remains a YWE component for pattern integrity, diagnostics, recovery, containment, conformance, code resilience, update safety, and patch stability
- [ ] Where Ravens Wait: Eternal Reckoning remains the game and narrative layer
- [ ] This PR keeps ASH Pattern System subordinate to the ASH Model of the Universe
- [ ] This PR preserves wolves as complementary non-moral companion opposites
- [ ] This PR preserves wolf indestructibility
- [ ] This PR preserves engine/game separation
- [ ] Files deleted: none/list
- [ ] Accepted canon or architecture files deleted: none/list
- [ ] Existing checks run: yes/no
- [ ] New guardrails run: yes/no
- [ ] Destructive changes approved: not_applicable/approval_link
- [ ] Rollback plan included: yes/no

## Checklist

- [ ] `scripts/run_checks.sh` passes
- [ ] JSON schemas are valid
- [ ] `python scripts/check_json_integrity.py` passes
- [ ] `python scripts/check_required_contracts.py` passes
- [ ] `python scripts/check_authority_stack.py --config data/validation/repository_drift_guardrail_rules.json` passes
- [ ] `python scripts/check_repository_attribution_policy.py .` passes
- [ ] `python scripts/check_non_destructive_diff.py --base origin/main --head HEAD` passes when applicable
- [ ] No engine-specific code on main branch (if targeting main)
- [ ] Layer dependencies respected
- [ ] Documentation updated (if applicable)

## Full Local Guardrail Reproduction

```bash
bash scripts/run_checks.sh
python3 scripts/check_json_integrity.py .
python3 scripts/check_required_contracts.py .
python3 scripts/check_phase_8_9_required_artifacts.py .
python3 scripts/check_authority_stack.py --config data/validation/repository_drift_guardrail_rules.json .
python3 scripts/check_branch_reality_guardrail.py .
python3 scripts/check_phase_9_schema_semantics.py .
python3 scripts/check_phase_8_9_package_boundary.py .
python3 scripts/check_player_runtime_state.py .
python3 scripts/check_worldstate_location_mutation.py .
python3 scripts/check_quest_npc_lore_generation.py .
python3 scripts/check_source_truth_alignment.py .
python3 scripts/check_repository_attribution_policy.py .
python3 scripts/check_non_destructive_diff.py --base origin/main --head HEAD .
git diff --check
```
