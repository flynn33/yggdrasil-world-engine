# Phase 12 Conformance — Existential Quest, NPC, and Lore Generation

## Conformance Statement

Phase 12 is conformant when all generated quest, NPC, and lore candidates include:

```text
cosmology provenance
branch context
player context
location/worldstate context
axiom or consequence pressure
existence potential
pattern vector
truth scope
rejection policy
downstream handoff target
```

## Non-Conformant Cases

```text
generic random quest generation
NPC without relation context
conscious NPC without self-reference classification
lore without pattern trace
content without truth scope
content without provenance
content that rewrites shared truth without worldstate delta
```

## Result

Implementation result:

```text
phase_12_conformance_status: implemented
checks_run:
  - python3 scripts/check_quest_npc_lore_generation.py .
  - python3 scripts/check_phase_8_9_package_boundary.py .
  - python3 scripts/check_branch_reality_guardrail.py
  - git diff --check
  - repository JSON parse check
  - bash scripts/run_checks.sh
open_deviations: []
```
