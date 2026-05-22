# Master Specification Index

Project: Yggdrasil World Engine
Status: active specification index
Current baseline: `v2.0.17`

## Purpose

This directory contains the foundational YWE master specification. It is the
long-form design baseline for the engine-first repository: cosmology, realm
structure, player model, wolf canon, procedural generation, data schemas,
adapter boundaries, validation expectations, and implementation principles.

## Primary Document

| File | Role |
|---|---|
| `YWE_MASTER_SPECIFICATION.md` | Foundational 25-section design specification for the code-agnostic engine layer. |

## How To Read It

1. Start with `Current Authority Stack` to confirm the ASH Model foundation,
   YWE engine layer, ASH Pattern System component role, and Where Ravens Wait
   game/narrative layer.
2. Read `Project Overview`, `Cosmology Canon`, and `Realm System` before
   consuming runtime or feature contracts.
3. Use `docs/architecture/README.md` for the accepted phase contract order and
   current package surfaces.
4. Use `docs/handoff/README.md` for provenance and package-history context.

## Active Companion Surfaces

| Surface | Path |
|---|---|
| Architecture index | `../architecture/README.md` |
| Authority stack contract | `../architecture/ywe_cosmology_authority_contract.md` |
| Source-truth remediation handoff | `../handoff/YWE_SOURCE_TRUTH_ALIGNMENT_HANDOFF_2026-05-19.md` |
| Phase 14 completion report | `../handoff/YWE_PHASE_14_ABILITY_POWER_ENGINE_COMPLETION_REPORT_2026-05-19.md` |
| Phase 15 completion report | `../handoff/YWE_PHASE_15_QUEST_REWARD_RESOLVER_COMPLETION_REPORT_2026-05-20.md` |
| Validation suite | `../../scripts/run_checks.sh` |

## Invariants

- All meaningful generation remains ASH-derived and diagnostic-backed.
- ASH math remains outside downstream feature authorship.
- Base ontology and the fixed realm structure remain stable.
- Player perception, myth, prophecy, and faction claims may layer meaning but
  cannot silently rewrite shared world truth.
- Host adapters materialize approved manifests and do not author YWE truth.
