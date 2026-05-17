# YWE Cross-Module Dependency Map

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: one-way dependency baseline

## Dependency Law

YWE aligns to ASH Cosmological Model authority and Forsetti's one-way
dependency rule:

```text
ASH Cosmological Model
  -> YWE Core Contracts
      -> ASH Pattern System component and runtime systems
          -> Feature Engines
              -> Host Adapters
```

ASH Cosmological Model is the upstream foundation for YWE and its systems. ASH
Pattern System is a YWE component that provides diagnostics, pattern integrity,
recovery, containment, resilience, conformance, and update/patch stability.
YWE interprets ASH-derived meaning into world and gameplay manifests. Host
adapters remain downstream materialization surfaces.

Phase 9 adds the runtime-cosmology foundation between the ASH Cosmological
Model and later feature systems:

```text
ASH Cosmological Model
  -> YWE Runtime Cosmology Contracts
    -> Branch Reality Resolver
      -> Feature Engines

ASH Pattern System Component
  -> diagnostics, conformance, recovery, and containment support across those systems
```

## Direct Runtime Dependencies

- `ywe_cosmology_authority_contract.md`: authoritative architecture contract
  for current game/engine/foundation/component authority.
- `ash_pattern_system_component_contract.md`: component contract for ASH
  Pattern System diagnostics, conformance, recovery, containment, resilience,
  and update/patch stability.
- `ash_upstream_authority_contract.md`: preserved packet-spine contract; earlier
  ASH Pattern System as topmost authority phrasing is superseded by the current
  cosmology authority contract.
- `runtime_cosmology_foundation_contract.md`: Phase 9 contract for base ontology,
  branch events, branch-generation context, diagnostics, and manifestation
  boundaries.
- `leaf_branch_reality_contract.md`: Phase 9 contract for runtime-generated
  player branch realities and branch divergence boundaries.
- `branch_event_contract.md`: Phase 9 contract for meaningful player-choice
  events that may create branch realities and future generation bias.
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
