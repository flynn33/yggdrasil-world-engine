# YWE Cross-Module Dependency Map

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: one-way dependency baseline

## Dependency Law

YWE aligns to Forsetti's one-way dependency rule:

```text
data assets -> core truth services -> feature manifestation services -> host bridges
```

## Direct Runtime Dependencies

- `com.ywe.core.cosmology-engine`: none
- `com.ywe.core.realm-engine`: cosmology
- `com.ywe.core.ash-pattern-engine`: cosmology, realm
- `com.ywe.core.narrative-engine`: ash-pattern, realm
- `com.ywe.core.perception-engine`: narrative, realm
- `com.ywe.module.quest-engine`: ash-pattern, narrative, realm
- `com.ywe.module.myth-engine`: narrative
- `com.ywe.module.prophecy-engine`: ash-pattern, narrative
- `com.ywe.module.artifact-engine`: ash-pattern, narrative
- `com.ywe.module.creature-engine`: ash-pattern, realm, narrative

## Event-Mediated Dependencies

When one downstream system needs awareness of another system's outcomes, that awareness must stay event-mediated through Forsetti rather than become a direct implementation dependency.

Examples:
- myth may react to quest and narrative consequence events
- prophecy may react to recurring pattern and myth pressure events
- artifact and creature systems may react to consequence events without owning narrative truth

## Forbidden Dependencies

- core services must not depend on feature modules
- truth services must not depend on adapters or platform code
- feature modules must not directly couple to peer implementations as a hard runtime requirement
- adapters must not invert truth ownership
