# YWE ASH/ASP Core-Math Rebuild Handoff

Date: 2026-05-10

## Authority Chain

1. `YWE_ASP_CORE_MATH_REBUILD_PACKAGE`
2. Active ASH Pattern System research baseline after semantic-integrity corrections
3. YWE master specification
4. YWE repository bootstrap prompt
5. Existing YWE architecture and governance docs where they do not conflict

The active package supersedes older remediation or build packages where they
conflict.

Forsetti is not the active authority for ASH/ASP math, YWE cosmology truth,
codewords, diagnostics, generation semantics, or conformance acceptance.

## Rebuild Boundary

YWE remains code-agnostic. This repository defines contracts, schemas,
validators, data records, diagnostics, and handoff evidence. Engine adapters and
host implementations may materialize only from `GenerationPlan` outputs and
must not author ASH truth or YWE domain truth.

The rebuild is additive against the restored repository baseline. Existing
planning documents, engine contracts, schemas, rule records, and handoff
material are extended in place with ASH/ASP provenance and materialization
requirements instead of being deleted or replaced by package summaries.

## Primary Source Changes

- Added shared ASH packet and generation gate contracts.
- Added package acceptance tests under `.github/scripts/`.
- Normalized ASH runtime snapshot and plan packet fields.
- Added character/progression, worldstate, creature, artifact, NPC, codex/lore,
  realm-transition, myth, prophecy, perception, and quest manifest schemas.
- Normalized quest, creature, artifact, myth, prophecy, narrative, perception,
  and realm interfaces around `CosmicPatternSnapshot`, `DiagnosticEnvelope`, and
  `GenerationPlan`.
- Updated adapter docs so Unity, Unreal, and Godot materialize plans only and do
  not author truth.
- Updated conformance, source inventory, and deviation records.

## Validation Entry Points

- `bash scripts/run_checks.sh`
- `python3 .github/scripts/ywe_package_acceptance_check.py .`
- `python3 .github/scripts/semantic_integrity_check.py`
- `python3 .github/scripts/math_integrity_check.py`
- `python3 .github/scripts/downstream_conformance_check.py`
- `python3 scripts/validate_architecture.py`
- `python3 scripts/validate_ash_compliance.py`
- `python3 scripts/validate_schemas.py`

## Remaining Scope

No open deviations remain for the code-agnostic repository scope. Runtime host
implementations remain outside this repository and must run the same acceptance
checks before claiming adapter-level conformance.
