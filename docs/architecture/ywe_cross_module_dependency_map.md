# YWE Cross-Module Dependency Map

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: one-way dependency baseline

## Dependency Law

YWE aligns to ASH upstream authority and Forsetti's one-way dependency rule:

```text
ASH Pattern System -> YWE
ASH Pattern System
  -> YWE ASH consumption / interpretation layer
  -> Core truth services
  -> Feature manifestation services
  -> host adapters
```

ASH is the upstream mathematical and generative authority for YWE. YWE
consumes ASH-derived state, diagnostics, codeword traces, and generation plans,
then interprets them into world and gameplay manifests. Host adapters remain
downstream materialization surfaces.

## Direct Runtime Dependencies

- `ash_upstream_authority_contract.md`: authoritative architecture contract
  for upstream ASH authority and downstream YWE interpretation.
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
- future generation bias may react to `WorldstateDeltaPacket` records without
  mutating ASH math

## Forbidden Dependencies

- YWE systems must not depend on repository-local mathematical authority,
  repository-local codeword sets, or local symbolic grammar authority
- core services must not depend on feature modules
- truth services must not depend on adapters or platform code
- feature modules must not directly couple to peer implementations as a hard runtime requirement
- adapters must not invert truth ownership
- host adapters must not materialize meaningful content before
  `GenerationPlan`
