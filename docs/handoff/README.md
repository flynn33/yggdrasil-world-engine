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
| `YWE_ASH_UPSTREAM_AUTHORITY_HANDOFF_2026-05-10.md` | Post-remediation ASH upstream authority architecture handoff |
| `repo_implementation_mapping.md` | Repository implementation mapping |
| `missing_source_documents.md` | Missing source document inventory |

## Authority Sequence

The active architecture authority sequence is:

```text
ASH Pattern System
  -> Yggdrasil World Engine
    -> YWE game systems / feature engines
      -> platform-specific runtime implementations
```

ASH is the upstream mathematical and generative authority for YWE. YWE
consumes ASH-derived state, diagnostics, codeword traces, and generation plans.

## Invariants
- all meaningful generation must remain ASH-derived
- player actions influence future generation context; they do not mutate ASH math
- host adapters materialize approved manifests but do not author truth
- fixed cosmology must remain locked
- perception must not rewrite shared-world truth
- Forsetti governs activation; YWE governs truth
