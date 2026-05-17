# schemas Data Domain

Date: 2026-05-10
Project: Yggdrasil World Engine
Status: ASH upstream authority schema index

## Purpose
Documents the shared schema contracts used by YWE systems to consume
ASH-derived state, diagnostics, codeword traces, generation plans, and
downstream interpretation packets.

ASH is the upstream mathematical and generative authority for YWE. YWE is the
downstream world, narrative, and manifestation engine built on ASH authority.

## Upstream Generation Packet Spine

Meaningful generation uses this packet spine:

```text
YWEGenerationContextPacket
  -> ASHUpstreamGenerationEnvelope
  -> YWEInterpretationPacket
  -> SystemManifestHandoff
  -> WorldstateDeltaPacket or DiagnosticNoOp
  -> FutureGenerationBiasUpdate
```

## Core Files

| File | Role |
|---|---|
| `ash_generation_packet_schema.json` | Shared ASH/YWE packet index and provenance spine |
| `ash_upstream_generation_envelope_schema.json` | ASH provenance envelope for meaningful generated output |
| `ywe_generation_context_packet_schema.json` | Player, realm, perception, and worldstate context submitted into ASH-governed generation |
| `ywe_interpretation_packet_schema.json` | YWE interpretation of ASH-derived output for feature-engine handoff |
| `player_action_trace_schema.json` | Player action and consequence inputs that may influence future generation context |
| `exploration_frontier_request_schema.json` | Frontier, threshold, thin-veil, and unresolved-node generation requests |
| `future_generation_bias_update_schema.json` | Consequence-derived pressure for later ASH-governed generation context |

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
