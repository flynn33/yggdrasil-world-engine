# Yggdrasil World Engine -- Forsetti Framework Integration Rules

> Built on the [Forsetti Framework v0.1.0](https://github.com/flynn33/Forsetti-Framework)

## 1. Purpose

The Yggdrasil World Engine (YWE) is a code-agnostic cosmic narrative simulation
engine governed by the [Forsetti Framework](https://github.com/flynn33/Forsetti-Framework).
Every branch in this repository remains agnostic specification work. Concrete
platform products belong in separate downstream repositories after M10 acceptance.

## 2. Design Principles

Five principles govern all work on the engine:

| Principle | Summary |
|-----------|---------|
| **Native-first** | Future downstream platform repositories use native types, idioms, and toolchains after M10 authorization |
| **Contract-first** | Define the interface in `core/*/engine_interface.json` before any implementation |
| **Boundary-first** | Layers have strict dependency direction; violations are build errors |
| **Policy-first** | ASH compliance rules are hard constraints, not suggestions |
| **Host-agnostic modules** | This repository remains engine-agnostic; engine-specific code belongs only in authorized downstream repositories |

## 3. Layer Architecture

```
Core <- Data <- Runtime <- Presentation <- Editor
```

| Layer | Responsibility | Depends On |
|-------|---------------|------------|
| **Core** | Engine interfaces, cosmology rules, pattern detection, invariants | Nothing |
| **Data** | JSON schemas, data loading, registry parsing, data models | Core |
| **Runtime** | Quest generation, myth formation, prophecy tracking, creature spawning | Core, Data |
| **Presentation** | Realm overlays, perception rendering, UI, temporary environments | Core, Data, Runtime |
| **Editor** | Build tools, inspectors, world builders | All above |

Reverse dependencies are forbidden. No circular dependencies.

## 4. Integration Boundaries

- Every branch in this repository contains only agnostic interfaces, schemas, documentation, governance, validation, and reference material.
- Concrete platform implementation is deferred through M10 and then belongs in separate downstream repositories when explicitly authorized.
- If a solution requires changing the spec, redesign the solution.

## 5. ASH Compliance (Non-Negotiable)

All systems must comply with the ASH cosmological model:

- Nine realms are fixed and immutable
- All procedural generation derives from ASH pattern detection
- No independent random generators for meaningful content
- White Wolf and Dark Wolf are informational forces, not morality
- The world does not change; player perception changes
- Prophecies are probability weights, not fixed scripts
- Bloodlines influence eligibility, never lock destiny

## 6. Module Rules

- Each module owns exactly one responsibility
- No reverse dependencies
- No dependency cycles
- All expansion modules must consume ASH Model-grounded state through YWE contracts and may use ASH Pattern System component diagnostics
- Modules communicate through events and framework services

## 7. Enforcement

- `scripts/validate_architecture.py` checks structural compliance
- `scripts/validate_schemas.py` validates JSON schemas plus canonical YAML and doc artifacts
- `bash scripts/run_checks.sh` runs the authoritative local validation suite on POSIX shells
- `scripts/run_checks.ps1` runs the Windows PowerShell wrapper where available; verify parity before treating it as a full replacement for the Bash suite
- CI guardrails block merges on any violation

## 8. Developer Workflow

1. Fork or clone the repository.
2. Create a feature branch from `main`; the branch remains specification work.
3. Change the agnostic interfaces, schemas, documentation, or validation needed by the specification.
4. Run `bash scripts/run_checks.sh` from the repository root and confirm all checks pass. On Windows, use `pwsh -File scripts/run_checks.ps1` only where it is known to cover the same active guardrail set.
5. Open a pull request against `main` for specification work, or against a separately authorized downstream repository for post-M10 platform work.

## 9. Non-Compliance

Non-compliant code must be refactored before merge. CI will block it automatically. Exceptions require written rationale and a follow-up resolution plan.
