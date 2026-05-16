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
- [ ] All procedural generation derives from ASH patterns
- [ ] No independent random generators for meaningful content

## Authority Stack Guardrails

- [ ] Authority stack reviewed: yes/no
- [ ] Where Ravens Wait: Eternal Reckoning remains the game/narrative layer
- [ ] Yggdrasil World Engine remains the agnostic game engine
- [ ] ASH Cosmological Model remains the upstream foundation for YWE and its systems
- [ ] ASH Pattern System remains a YWE component for diagnostics, pattern integrity, recovery, containment, resilience, conformance, and update/patch stability
- [ ] Files deleted: none/list
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
- [ ] `python scripts/check_non_destructive_diff.py --base origin/main --head HEAD` passes when applicable
- [ ] No engine-specific code on main branch (if targeting main)
- [ ] Layer dependencies respected
- [ ] Documentation updated (if applicable)
