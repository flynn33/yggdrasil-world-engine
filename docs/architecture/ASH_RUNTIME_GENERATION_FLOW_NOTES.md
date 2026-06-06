# ASH Runtime Generation Flow Notes

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: superseded by active runtime flow contract

## Purpose
Historical notes for the ASH runtime generation flow. The active contract is
now `../../core/narrative_engine/ash_runtime_generation_flow.yaml`, governed by
`ash_upstream_authority_contract.md`.

## Active Flow

```text
RuntimeGenerationTrigger
  -> YWEGenerationContextPacket
  -> ASHUpstreamGenerationEnvelope
  -> YWEInterpretationPacket
  -> SystemManifestExchange
  -> HostAdapterMaterializationRequest
  -> MaterializationResult
  -> ResolutionPayload
  -> WorldstateDeltaPacket or DiagnosticNoOp
  -> FutureGenerationBiasUpdate
```

## Authority Rule

ASH is the upstream mathematical and generative authority for YWE. YWE consumes
ASH-derived state, diagnostics, codeword traces, and generation plans, then
interprets them into world and gameplay manifestations.

## Invariants
- all meaningful generation must remain ASH-derived
- player actions influence future generation context; they do not mutate ASH math
- host adapters materialize approved manifests but do not author truth
- fixed cosmology must remain locked
- perception must not rewrite shared-world truth
- Forsetti governs activation; YWE governs truth
