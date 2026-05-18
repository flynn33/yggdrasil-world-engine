# schemas Data Domain

Date: 2026-05-10
Project: Yggdrasil World Engine
Status: ASH upstream authority schema index

## Purpose
Documents the shared schema contracts used by YWE systems to consume
ASH-derived state, diagnostics, codeword traces, generation plans, and
downstream interpretation packets.

Current authority clarification: ASH Cosmological Model is the upstream
foundation for YWE and its systems. ASH Pattern System is a YWE component for
pattern integrity, diagnostics, recovery, containment, conformance, code
resilience, and update/patch stability. Earlier shorthand that described ASH as
upstream mathematical and generative authority should be read as referring to
the ASH Cosmological Model, not ASH Pattern System as an upstream authority.

## Upstream Generation Packet Spine

Meaningful generation uses this packet spine:

```text
YWEGenerationContextPacket
  -> ASHUpstreamGenerationEnvelope
  -> YWEInterpretationPacket
  -> SystemManifestHandoff
  -> QuestChainManifest / NPCManifest / CodexRecord / MythRecord
  -> WorldstateDeltaPacket or DiagnosticNoOp
  -> LocationMutationState or LocationMutationDelta
  -> FutureGenerationBiasUpdate
```

## Core Files

Rows without an inline deferred marker remain active within their accepted
phase boundary. The active Phase 8-9 schema boundary is the base world ontology,
leaf branch reality, branch event, branch generation context, pattern vector,
existence potential, axiom diagnostic packet, plane pressure state, and future
generation bias update foundation.

| File | Role |
|---|---|
| `ash_generation_packet_schema.json` | Shared ASH/YWE packet index and provenance spine |
| `ash_upstream_generation_envelope_schema.json` | ASH provenance envelope for meaningful generated output |
| `ywe_generation_context_packet_schema.json` | Player, realm, perception, and worldstate context submitted into ASH-governed generation |
| `ywe_interpretation_packet_schema.json` | YWE interpretation of ASH-derived output for feature-engine handoff |
| `player_action_trace_schema.json` | Phase 10 player action trace records that provide provenance for meaningful player-state updates |
| `player_runtime_state_schema.json` | Phase 10 player runtime state spine for branch, identity, resonance, memory, world links, and ASH Pattern System resilience references |
| `player_agent_state_schema.json` | Phase 10 branch-bound player agency state |
| `celestial_identity_state_schema.json` | Phase 10 veiled celestial identity and reveal-through-play evidence state |
| `plane_attunement_state_schema.json` | Phase 10 dynamic plane attunement pressure state |
| `bloodline_resonance_state_schema.json` | Phase 10 dynamic bloodline resonance pressure state |
| `wolf_resonance_summary_schema.json` | Phase 10 wolf resonance summary; not a morality meter |
| `player_memory_record_schema.json` | Phase 10 player memory record references |
| `player_branch_history_schema.json` | Phase 10 player branch history references |
| `player_progression_signal_schema.json` | Phase 10 progression signal references |
| `player_state_update_packet_schema.json` | Phase 10 controlled player-state mutation packet |
| `player_state_snapshot_schema.json` | Phase 10 player-state snapshot reference contract |
| `exploration_frontier_request_schema.json` | Frontier, threshold, thin-veil, and unresolved-node generation requests |
| `future_generation_bias_update_schema.json` | Consequence-derived pressure for later ASH-governed generation context |
| `worldstate_location_mutation_schema.json` | DEFERRED - Phase 9 boundary violation; do not consume until the matching owner-approved package is accepted. Phase 11 persistent worldstate consequence, scoped location mutation, commit records, and diagnostic no-ops |
| `quest_npc_lore_generation_schema.json` | DEFERRED - Phase 9 boundary violation; do not consume until the matching owner-approved package is accepted. Phase 12 quest chains, NPC manifests, NPC memory deltas, codex lore records, myth records, and social distribution deltas |

## Required Provenance

Every meaningful manifest must preserve:

- `source_ash_refs`
- `diagnostic_ref`
- `generation_plan_ref`
- `requested_manifest_kind`
- `worldstate_delta_policy`

## Invariants
- all meaningful generation must remain ASH-derived
- player actions influence future generation context; they do not mutate ASH math
- host adapters materialize approved manifests but do not author truth
- fixed cosmology must remain locked
- perception must not rewrite shared-world truth
- Forsetti governs activation; YWE governs truth
