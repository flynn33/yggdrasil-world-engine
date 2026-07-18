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
- [ ] Machine-readable artifacts and declared JSON Schemas are valid
- [ ] Roadmap, repository status, and version sources are synchronized
- [ ] `python scripts/check_repository_attribution_policy.py .` passes
- [ ] `scripts/run_checks.sh --context pull_request --base origin/main` passes when applicable
- [ ] No engine-specific code on main branch (if targeting main)
- [ ] Layer dependencies respected
- [ ] Documentation updated (if applicable)

## Full Local Guardrail Reproduction

```bash
python3 -m pip install -r scripts/requirements.txt
bash scripts/run_checks.sh
bash scripts/run_checks.sh --context pull_request --base origin/main
```
