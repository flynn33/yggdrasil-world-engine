# Phase 16–17 Recovery and Phase 18 Unblock Contract

## Purpose

This contract exists because Phase 18 depends on Phase 17 Ravenfall Gate acceptance/playtest trace artifacts. If the repository baseline is Phase 15A, Phase 18 must not be applied until Phase 16 and Phase 17 artifacts are present and accepted.

## Required sequence

```text
Phase 15A baseline
  -> Phase 16 Ravenfall Gate Vertical Slice artifacts
  -> Phase 17 Acceptance and Playtest Trace artifacts
  -> Phase 18 Combat and Encounter System Foundation
```

## Phase 18 unblock prerequisites

Phase 18 is blocked until the repository contains:

- `data/schemas/vertical_slice_playtest_trace_schema.json`
- `data/schemas/ravenfall_gate_playtest_path_schema.json`
- `data/schemas/wolf_companion_trace_schema.json`
- `data/schemas/quest_reward_trace_schema.json`
- `data/schemas/future_generation_bias_trace_schema.json`
- Ravenfall Gate choice path coverage for Reveal, Conceal, Bind, Study, and Weaponize

## Repository boundary

This recovery work must remain agnostic. It must not add platform implementation code.
