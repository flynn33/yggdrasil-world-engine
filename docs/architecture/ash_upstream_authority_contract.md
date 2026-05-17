# ASH Upstream Authority Contract

Date: 2026-05-10  
Project: Yggdrasil World Engine  
Status: Superseded component packet-spine contract
Scope: Engine-agnostic authority, generation flow, feature-engine boundaries

---

## Supersession Notice

This document is superseded by `ywe_cosmology_authority_contract.md` and
`ash_pattern_system_component_contract.md`.

Current authority stack: ASH Cosmological Model is the upstream foundation for
YWE and its systems. ASH Pattern System remains important, but it is a
component of YWE for pattern integrity, diagnostics, recovery, containment,
resilience, conformance, and update/patch stability. The packet spine,
diagnostic, conformance, and materialization-boundary content in this document
is preserved as ASH Pattern System component evidence.

Historical wording below may describe ASH Pattern System as upstream authority.
That framing is no longer current.

Phase 9 note: this document is historical/partial if it frames ASH Pattern
System as the top-level authority. Current hierarchy: ASH Cosmological Model is
the upstream foundation for YWE and its systems; ASH Pattern System is a YWE
component for pattern integrity, diagnostics, recovery, containment,
conformance, resilience, and update/patch stability.

---

## 1. Purpose

This document establishes the ASH Pattern System as the upstream mathematical and generative authority for the Yggdrasil World Engine.

YWE does not define, mutate, replace, or extend ASH math. YWE consumes ASH-derived state, diagnostics, codeword traces, and generation plans, then interprets that lawful pattern output into playable world, narrative, and system manifestations.

---

## 2. Canonical Architecture Law

```text
ASH Pattern System
  -> Yggdrasil World Engine
    -> YWE game systems / feature engines
      -> platform-specific runtime implementations
```

This dependency order is mandatory.

ASH is upstream. YWE is downstream. Feature engines are downstream of YWE interpretation. Host runtimes are downstream materialization surfaces.

---

## 3. ASH Authority

ASH owns the mathematical authority layer:

```text
canonical state space
canonical codeword set
canonical transition rules
canonical diagnostics
canonical generation-planning semantics
pattern structure
admissibility and conformance
```

ASH may emit or authorize:

```text
AshStateSnapshot
CanonicalCodewordTrace
DiagnosticEnvelope
GenerationPlan
SourceASHRefs
```

ASH authority may not be redefined by:

```text
ywe_core_services
feature_engines
platform_adapters
authoring_tools
local_runtime_implementations
```

---

## 4. YWE Authority

YWE owns downstream interpretation and game-domain contracts:

```text
cosmology interpretation
realm truth
player narrative state
worldstate delta recording
quest manifestation
NPC manifestation
creature manifestation
artifact manifestation
myth and prophecy boundaries
perception boundaries
faction claim boundaries
host adapter handoff contracts
```

YWE consumes:

```text
AshStateSnapshot
CanonicalCodewordTrace
DiagnosticEnvelope
GenerationPlan
SourceASHRefs
```

YWE may emit:

```text
YWEGenerationContextPacket
YWEInterpretationPacket
SystemManifest
WorldstateDeltaPacket
DiagnosticNoOp
FutureGenerationBiasUpdate
```

YWE must not:

```text
redefine ASH math
create independent symbolic truth
bypass ASH diagnostics
materialize meaningful content without a generation plan
allow feature engines to claim math authority
allow host adapters to author truth
```

---

## 5. Player Action and Exploration Rule

Player action does not mutate ASH math.

Player action changes the YWE context submitted into ASH-governed generation requests and recorded as worldstate consequence. This lets the world respond to the player without allowing YWE to replace the upstream mathematical authority.

```text
Player explores or acts
  -> YWE records action/context and worldstate deltas
  -> YWE submits generation context to ASH-governed generation
  -> ASH provides lawful pattern structure, diagnostics, and generation plan
  -> YWE interprets output into world/game-domain meaning
  -> feature engines emit manifests
  -> host adapter materializes approved content
  -> result creates worldstate delta or DiagnosticNoOp
  -> future generation bias updates context for later ASH-governed generation
```

---

## 6. Exploration-Driven World Generation

When the player approaches an unresolved frontier, crosses a realm threshold, enters a thin veil site, or reaches an unresolved Yggdrasil node, YWE must not invent meaningful space directly.

The required flow is:

```text
ExplorationFrontierRequest
  -> YWEGenerationContextPacket
  -> ASHUpstreamGenerationEnvelope
  -> YWEInterpretationPacket
  -> WorldRegionManifest / RealmSiteManifest / ThresholdManifest / EncounterFieldManifest
  -> HostAdapterMaterializationRequest
  -> MaterializationResult
  -> WorldstateDeltaPacket or DiagnosticNoOp
```

YWE may use authored geography, handcrafted anchors, and safe author overrides, but any meaningful procedural generation must preserve ASH provenance.

---

## 7. Player-Action-Driven Quest Generation

Quest generation must derive from ASH-governed pattern output interpreted through player history, local worldstate, faction topology, myth pressure, prophecy pressure, realm context, and consequence memory.

The required flow is:

```text
PlayerActionTrace
  -> WorldstateDeltaPacket
  -> FutureGenerationBiasUpdate
  -> YWEGenerationContextPacket
  -> ASHUpstreamGenerationEnvelope
  -> YWEInterpretationPacket
  -> QuestChainManifest
```

Quest templates are interpretive containers. They do not generate symbolic truth independently.

---

## 8. Player-Action-Driven NPC Generation

NPC synthesis must derive from ASH-governed pattern output interpreted through local worldstate, player action history, faction topology, myth records, prophecy pressure, and perception state.

The required flow is:

```text
PlayerActionTrace / LocalWorldstateContext
  -> YWEGenerationContextPacket
  -> ASHUpstreamGenerationEnvelope
  -> YWEInterpretationPacket
  -> NPCManifest
  -> NPCMemoryHooks
  -> WorldstateDeltaPacket or DiagnosticNoOp
```

NPCs may hold incorrect beliefs, faction claims, myths, or partial interpretations. These may affect perception, social memory, faction pressure, or future generation context. They do not automatically become shared world truth.

---

## 9. Consequence and Future Generation Bias

Worldstate deltas are how YWE remembers consequences.

Future generation bias is how remembered consequences influence later generation without mutating ASH math.

Allowed bias sources include:

```text
quest resolution
NPC memory update
artifact use or binding
creature encounter resolution
realm transition
faction claim change
myth emergence
prophecy pressure change
perception state change
player progression event
wolf resonance shift
ability unlock pressure
```

Future generation bias must be represented as downstream context. It must never be represented as an edit to ASH canonical math.

---

## 10. Shared Packet Spine

Every meaningful generation request should pass through this packet spine:

```text
YWEGenerationContextPacket
  -> ASHUpstreamGenerationEnvelope
  -> YWEInterpretationPacket
  -> SystemManifestHandoff
  -> WorldstateDeltaPacket or DiagnosticNoOp
  -> FutureGenerationBiasUpdate
```

### `YWEGenerationContextPacket`

Carries YWE-side context into ASH-governed generation.

Required concepts:

```text
request_id
trigger_kind
requested_manifest_kind
player_runtime_state_ref
realm_context_ref
worldstate_delta_refs
perception_state_ref
```

### `ASHUpstreamGenerationEnvelope`

Carries upstream ASH authority references and proves lawful provenance.

Required concepts:

```text
request_id
requested_manifest_kind
ywe_context_packet_ref
ash_state_snapshot_ref
canonical_codeword_trace_ref
diagnostic_ref
generation_plan_ref
source_ash_refs
authority_chain
```

### `YWEInterpretationPacket`

Carries YWE interpretation of ASH-derived output into feature engines.

Required concepts:

```text
source_ash_refs
diagnostic_ref
generation_plan_ref
requested_manifest_kind
realm_interpretation
player_relevance
manifestation_target
allowed_feature_engine
worldstate_delta_policy
```

---

## 11. Feature Engine Obligations

Every feature engine must preserve ASH provenance and declare how it consumes the shared packet spine.

| Engine | Consumes | Emits | Must preserve |
|---|---|---|---|
| Realm Engine | `YWEInterpretationPacket` | `RealmSiteManifest`, `RealmTransitionResolution` | realm truth boundary |
| Quest Engine | `YWEInterpretationPacket` | `QuestChainManifest`, `QuestResolutionPayload` | consequence routing |
| NPC Synthesis | `YWEInterpretationPacket` | `NPCManifest`, `NPCMemoryHooks` | belief/truth boundary |
| Creature Engine | `YWEInterpretationPacket` | `CreatureManifest`, `EncounterPlan` | ASH provenance |
| Artifact Engine | `YWEInterpretationPacket` | `ArtifactManifest`, `UseConsequenceRoute` | meaning before power |
| Myth Engine | `WorldstateDeltaHistory` | `MythRecord` | myth is not truth rewrite |
| Prophecy Engine | `PatternPressureAndWorldstateContext` | `ProphecyRecord` | prophecy is not deterministic script |
| Perception Engine | `PlayerRuntimeStateAndContext` | `PerceptionStateRecord` | perception does not rewrite shared truth |
| Faction Topology | `WorldstateDeltaPacket` | `FactionDelta`, `ClaimRecord` | claims are not automatic truth |
| Character Progression | `YWEInterpretationPacket` | `ProgressionDelta` | player state remains ASH-derived |

---

## 12. Materialization Boundary

Host adapters may materialize approved manifests into platform-specific scenes, actors, entities, UI, audio, navigation surfaces, or persistence formats.

Host adapters must never:

```text
author symbolic truth
create ASH state
create ASH codewords
invent meaningful generation independently
bypass DiagnosticEnvelope
bypass GenerationPlan
rewrite realm truth
rewrite shared world truth
```

---

## 13. Validation Rules

A meaningful manifest is invalid unless it can prove ASH provenance.

```pseudo
function validate_meaningful_manifest(manifest):
    require manifest.source_ash_refs exists
    require manifest.diagnostic_ref exists
    require manifest.generation_plan_ref exists
    require manifest.requested_manifest_kind exists
    require manifest.worldstate_delta_policy exists

    reject if manifest.created_from_local_symbolic_rng
    reject if manifest.redefines_ash_state_space
    reject if manifest.redefines_codeword_set
    reject if manifest.claims_8_plus_1_state_model
    reject if manifest.uses_derived_ninth_bit
    reject if manifest.materialized_before_generation_plan
    reject if manifest.adapter_authored_truth
    reject if manifest.feature_engine_claims_math_authority

    return VALID
```

---

## 14. Forbidden Authority Drift

The following claims are invalid outside rejection tests or explanatory warnings:

```text
YWE owns ASH math
YWE defines ASH math
YWE mutates ASH math
YWE replaces ASH math
YWE core math
local ASH math
local codeword set
local symbolic grammar authority
feature engine authored pattern truth
adapter authored truth
```

Use instead:

```text
YWE consumes ASH authority.
YWE interprets ASH-derived pattern output.
YWE records consequence and future-generation context.
```

---

## 15. Integration Targets

This contract should be referenced by:

```text
docs/architecture/ash_downstream_contract.md
core/narrative_engine/ash_runtime_generation_flow.yaml
data/schemas/ash_generation_packet_schema.json
data/validation/ash_generation_gate_contract.json
docs/master_specification/YWE_MASTER_SPECIFICATION.md
docs/architecture/ywe_module_design_contracts.md
docs/architecture/ywe_cross_module_dependency_map.md
docs/architecture/ywe_invariant_guardrails.md
docs/architecture/README.md
```

---

## 16. Final Rule

ASH is the upstream mathematical and generative authority. YWE is the downstream world and gameplay interpretation engine.

The world can unfold as the player explores because YWE submits exploration and action context into ASH-governed generation, receives lawful pattern structure, interprets it through realm/world/player truth, and materializes it through feature engines and host adapters.

No meaningful world, quest, NPC, artifact, creature, myth, prophecy, perception, ability, faction, wolf companion, or player-progression output is valid unless it preserves ASH provenance and follows the planning-before-materialization boundary.
