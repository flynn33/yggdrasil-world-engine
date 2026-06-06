# YWE Cross-Module Dependency Map

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: one-way dependency baseline

## Dependency Law

YWE aligns to ASH Model of the Universe authority and Forsetti's one-way
dependency rule:

```text
ASH Model of the Universe
  -> YWE Core Contracts
      -> ASH Pattern System component and runtime systems
          -> Feature Engines
              -> Host Adapters
```

ASH Model of the Universe is the mathematical and ontological foundation for
YWE and its systems. ASH Pattern System is a YWE component that provides
diagnostics, pattern integrity, recovery, containment, resilience, conformance,
code resilience, update safety, and patch stability. YWE interprets ASH-derived
meaning into world and gameplay manifests. Host adapters remain downstream
materialization surfaces.

Phase 9 adds the runtime-cosmology foundation between the ASH Model of the
Universe and later feature systems:

```text
ASH Model of the Universe
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
- `player_runtime_state_v1.md`: Phase 10 contract for player-specific runtime
  truth, branch context references, identity phase, resonance, perception,
  worldstate consequence refs, and generation-context references.
- `worldstate_location_mutation_v1.md`: Phase 11 contract for persistent
  consequence, scoped location mutation, worldstate commit records,
  diagnostic no-ops, and future generation bias routing.
- `quest_npc_lore_generation_v1.md`: Phase 12 contract for ASH-derived quest
  chains, NPC manifests, NPC memory deltas, lore archive records, myth records,
  and social distribution deltas.

ACCEPTED - Phase 10 through Phase 12 entries are active contracts layered on
the accepted Phase 9 runtime cosmology foundation. The active dependency
boundary remains: ASH Model of the Universe -> YWE Runtime Cosmology Contracts
-> Branch Reality Resolver -> Feature Engines. Player state, worldstate,
location mutation, and quest/NPC/lore generation consume that boundary through
records and references; they do not rewrite base ontology or ASH math.

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
- location mutation may react to accepted `WorldstateDeltaPacket` records but
  must stay scoped and event-mediated
- quest, NPC, lore, myth, and social distribution records may react to
  `WorldstateDeltaPacket` and `FutureGenerationBiasUpdate` records but must
  route new persistence through worldstate, diagnostic no-op, or future-bias
  contracts

## Forbidden Dependencies

- YWE systems must not depend on repository-local mathematical authority,
  repository-local codeword sets, or local symbolic grammar authority
- core services must not depend on feature modules
- truth services must not depend on adapters or platform code
- feature modules must not directly couple to peer implementations as a hard runtime requirement
- adapters must not invert truth ownership
- host adapters must not materialize meaningful content before
  `GenerationPlan`
- quest, NPC, lore, myth, and social distribution modules must not turn claims,
  myths, or perception overlays into shared truth without worldstate evidence
