# Handoff Documentation Index

Date: 2026-05-10
Project: Yggdrasil World Engine
Status: active handoff index

## Purpose
Introduces the documents stored in `docs/handoff` and their role in preserving
architecture decisions, source provenance, restoration context, and package
handoff records.

## Current Handoff Records

| File | Purpose |
|---|---|
| `YWE_NEXT_THREAD_BRIEF_2026-03-13_v2.md` | Earlier thread brief and repository continuity notes |
| `YWE_Planning_Phase_0.md` | Original planning phase record |
| `YWE_ASP_CORE_MATH_REBUILD_HANDOFF_2026-05-09.md` | Accepted ASH/ASP core-math rebuild handoff |
| `YWE_ASH_UPSTREAM_AUTHORITY_HANDOFF_2026-05-10.md` | Historical/superseded ASH upstream authority handoff; retained for packet-spine provenance, not as the current top-level authority diagram |
| `YWE_COSMOLOGY_AUTHORITY_REMEDIATION_HANDOFF_2026-05-16.md` | Accepted Phase 0-6 cosmology-authority remediation handoff |
| `YWE_PHASE_7_POST_REMEDIATION_ACCEPTANCE_AUDIT_2026-05-16.md` | Phase 7 post-remediation acceptance audit |
| `YWE_POST_REMEDIATION_BASELINE_2026-05-16.md` | Phase 8 post-remediation baseline freeze and restore point |
| `YWE_POST_PHASE_7_BASELINE_2026-05-17.md` | Phase 8-9 package baseline freeze before Phase 9 foundation work |
| `YWE_PHASE_9_RUNTIME_COSMOLOGY_BRANCH_REALITY_HANDOFF_2026-05-17.md` | Phase 9 runtime cosmology and branch reality foundation handoff |
| `YWE_PHASE_10_PLAYER_RUNTIME_STATE_HANDOFF_2026-05-17.md` | Phase 10 Player Runtime State v1 handoff |
| `YWE_PHASE_11_WORLDSTATE_LOCATION_MUTATION_HANDOFF_2026-05-17.md` | Phase 11 worldstate and location mutation handoff |
| `repo_implementation_mapping.md` | Repository implementation mapping |
| `missing_source_documents.md` | Missing source document inventory |

## Historical Handoff Note

`YWE_ASH_UPSTREAM_AUTHORITY_HANDOFF_2026-05-10.md` is retained as historical
evidence for the ASH-derived packet spine and generation-flow work. Its
`Architecture law` diagram is superseded by the 2026-05-16 cosmology-authority
remediation and the Phase 7 acceptance audit. The current authority sequence is
the one recorded below.

## Authority Sequence

The active architecture authority sequence is:

```text
Where Ravens Wait: Eternal Reckoning
  = game / narrative layer

Yggdrasil World Engine
  = agnostic game engine

ASH Cosmological Model
  = upstream foundation for YWE and its systems

ASH Pattern System
  = component inside YWE for pattern integrity, diagnostics, recovery,
    containment, code resilience, conformance, and update/patch stability
```

The ASH Cosmological Model is the upstream foundation for YWE and its systems.
The ASH Pattern System is a component inside YWE for integrity, diagnostics,
recovery, containment, conformance, code resilience, and update/patch stability.
YWE consumes ASH-derived state, diagnostics, codeword traces, and generation
plans without making ASH Pattern System the topmost cosmology authority.

## Invariants
- all meaningful generation must remain ASH-derived
- player actions influence future generation context; they do not mutate ASH math
- host adapters materialize approved manifests but do not author truth
- fixed cosmology must remain locked
- perception must not rewrite shared-world truth
- Forsetti governs activation; YWE governs truth
