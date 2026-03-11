# Yggdrasil World Engine -- Forsetti Framework Integration Rules

> Built on the [Forsetti Framework v0.1.0](https://github.com/flynn33/Forsetti-Framework)

## 1. Purpose

The Yggdrasil World Engine (YWE) is a code-agnostic cosmic narrative simulation engine governed by the [Forsetti Framework](https://github.com/flynn33/Forsetti-Framework) -- an architecture governance framework that enforces module contracts, runtime policy, and structural integrity. The `main` branch is the sealed, code-agnostic specification. Engine branches implement it in native idioms. This guide defines the Forsetti rules every contributor and AI agent must follow.

## 2. Design Principles

Five principles govern all work on the engine:

| Principle | Summary |
|-----------|---------|
| **Native-first** | Engine branches use native types, idioms, and toolchains |
| **Contract-first** | Define the interface in `core/*/engine_interface.json` before any implementation |
| **Boundary-first** | Layers have strict dependency direction; violations are build errors |
| **Policy-first** | ASH compliance rules are hard constraints, not suggestions |
| **Host-agnostic modules** | Core specification is engine-agnostic; engine-specific code lives only in implementation branches |

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

- `main` is the sealed specification. It contains engine interfaces, schemas, documentation, and governance -- no engine-specific code.
- Engine branches implement the spec. They never modify `main`.
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
- All expansion modules must read from the ASH Pattern Engine
- Modules communicate through events and framework services

## 7. Enforcement

- `scripts/validate_architecture.py` checks structural compliance
- `scripts/validate_schemas.py` validates JSON schemas
- `scripts/run_checks.sh` runs the full validation suite
- CI guardrails block merges on any violation

## 8. Developer Workflow

1. Fork or clone the repository.
2. Branch from the appropriate engine branch (or `main` for spec changes).
3. Implement against the interfaces defined in `core/*/engine_interface.json`.
4. Run `scripts/run_checks.sh` and confirm all checks pass.
5. Open a pull request against the appropriate branch.

## 9. Non-Compliance

Non-compliant code must be refactored before merge. CI will block it automatically. Exceptions require written rationale and a follow-up resolution plan.
