# Diagnostic Schema — canonical specification (Canonical Baseline)

## Purpose

This specification defines the **shared diagnostic envelope** used across all diagnostic contexts in the ASH Pattern System.

Every diagnostic record produced by the system — whether for state validity, recovery, fallback, containment, or safe halt — must conform to this schema. This ensures that the full diagnostic chain from initial detection through terminal halt is structurally consistent, auditable, and machine-readable.

This schema is **canonical** (Design Package D). Downstream implementation repositories must not invent local diagnostic structures.

## Shared diagnostic envelope

```text
TYPE DiagnosticEnvelope
    diagnostic_kind          : DiagnosticKind
    severity                 : Severity
    stage                    : Stage
    disposition              : Disposition
    subject_reference        : reference to the state, action, or entity being diagnosed
    parent_diagnostic_reference : DiagnosticEnvelope or NONE
    chain_root_reference     : DiagnosticEnvelope or NONE
    rule_ids                 : List of String (must conform to rule-id-taxonomy.md)
    summary                  : String (one-line human-readable summary)
    notes                    : List of String (detailed human-readable annotations)
END TYPE
```

## Diagnostic kind conventions

```text
ENUM DiagnosticKind
    STATE_VALIDITY           -- produced by state-validity diagnosis
    RECOVERY                 -- produced by correction or re-derivation actions
    FALLBACK                 -- produced by fallback selection
    CONTAINMENT              -- produced by containment entry or management
    SAFE_HALT                -- produced by safe-halt entry
    REALM_ENCODING           -- produced by REALM_ENCODER
    TRANSITION               -- produced by TRANSITION_REGISTRY
    TOPOLOGY                 -- produced by TOPOLOGY_GENERATOR
    AXIOM                    -- produced by AXIOM_EVALUATOR
    GENERATION_PLAN          -- produced by GENERATION_PLANNER
    ARTIFACT_EMISSION        -- produced by ARTIFACT_EMITTER
END ENUM
```

Every diagnostic must declare exactly one kind. The kind determines which specification governs the diagnostic content.

## Severity conventions

```text
ENUM Severity
    INFO                     -- normal operation, no action required
    WARNING                  -- condition detected, action may be required
    ERROR                    -- condition requires recovery or escalation
    CRITICAL                 -- condition requires containment or safe halt
END ENUM
```

Severity must reflect the actual system impact, not the diagnostic source. A `STATE_VALIDITY` diagnostic may be `ERROR` if the state is inadmissible, or `INFO` if the state is stable.

## Stage conventions

```text
ENUM Stage
    DETECTION                -- initial detection of a condition (state-validity diagnosis)
    CLASSIFICATION           -- system-state classification and recoverability mapping
    PROCESSING               -- pure module processing or artifact materialization
    RECOVERY                 -- correction, re-derivation, or fallback selection
    ESCALATION               -- escalation from recovery to containment
    TERMINAL                 -- safe halt (no further stages)
END ENUM
```

Stages are monotonically ordered. A diagnostic at stage `ESCALATION` must have a parent at stage `RECOVERY` or `CLASSIFICATION`. A diagnostic at stage `TERMINAL` must have a parent at stage `ESCALATION` or `RECOVERY`.

## Disposition conventions

```text
ENUM Disposition
    RESOLVED                 -- the condition was resolved (e.g., correction succeeded)
    PENDING                  -- the condition is awaiting resolution (e.g., containment awaiting operator)
    BLOCKED                  -- the condition cannot proceed (e.g., malformed input)
    ESCALATED                -- the condition was escalated to a more severe stage
    TERMINAL                 -- the system has halted; no further disposition changes
END ENUM
```

## Chaining requirements

Diagnostics form a **chain** from initial detection through terminal halt:

1. **`parent_diagnostic_reference`** — links to the immediately preceding diagnostic in the chain. The root diagnostic (typically a `STATE_VALIDITY` diagnostic at stage `DETECTION`) has `parent_diagnostic_reference = NONE`.

2. **`chain_root_reference`** — links to the originating diagnostic at the root of the chain. Every diagnostic in a chain shares the same `chain_root_reference`. This enables reconstruction of the full chain from any point.

3. **Chain integrity** — every diagnostic except the root must have a non-NONE `parent_diagnostic_reference`. Every diagnostic must have a non-NONE `chain_root_reference` (which equals itself for the root).

4. **No orphan diagnostics** — a diagnostic must not exist without a chain. Even a standalone `STATE_VALIDITY` diagnostic for a `STABLE` state must set its `chain_root_reference` to itself.

## Rule-ID requirements

1. Every diagnostic must include at least one `rule_id` in its `rule_ids` list.
2. All `rule_id` values must conform to the canonical pattern defined in `specs/interfaces/rule-id-taxonomy.md`.
3. Rule-free diagnostics are prohibited. If a diagnostic cannot cite a specific rule, it must cite a catch-all rule from the appropriate family (e.g., `ASH-STATE-GENERAL-001`).

## Explanation requirements

1. The `summary` field must contain a one-line human-readable summary of the diagnostic.
2. The `notes` list must contain at least one entry explaining the condition, action taken, or reason for the disposition.
3. Empty summaries and empty notes lists are prohibited.

## Deterministic output expectations

1. The same input conditions must always produce the same diagnostic output (same kind, severity, stage, disposition, rule_ids, and summary).
2. Notes may vary in non-semantic detail (e.g., timestamps) but must convey the same diagnostic meaning for the same conditions.
3. Diagnostic output must not depend on randomness, external state, or platform-specific behavior.

## Prohibition on silent omission

1. Every step in the recovery/escalation chain must produce a diagnostic record. No step may be silently skipped.
2. If a step completes without producing a diagnostic, the implementation is nonconformant.
3. Silent escalation (changing severity or stage without emitting a diagnostic) is prohibited.
4. Semantic diagnostic production must not be deferred, batched, or conditionally suppressed. Pure producer construction and subsequent ordered persistence follow the YWE-M3-MODULES amendment below.

## Relation to other specifications

- **state-validity-diagnostics.pseudo.md** — produces `STATE_VALIDITY` diagnostics conforming to this schema
- **recovery-fallback-semantics.pseudo.md** — produces `RECOVERY` and `FALLBACK` diagnostics conforming to this schema
- **containment-safe-failure-semantics.pseudo.md** — produces `CONTAINMENT` and `SAFE_HALT` diagnostics conforming to this schema
- **rule-id-taxonomy.md** — governs the `rule_ids` field
- **semantic-contracts.md** — requires downstream implementations to expose diagnostics conforming to this schema
- **fallback-policy-registry.md** — fallback diagnostics must reference the registry policy_id

## Design Package YWE-M3-MODULES — finite producer extension

The six added kinds are governed by the correspondingly named module contracts.
They use PROCESSING after actual StateModel DETECTION/CLASSIFICATION and before
RECOVERY. The exact order is DETECTION < CLASSIFICATION < PROCESSING < RECOVERY
< ESCALATION < TERMINAL. PROCESSING permits only a DETECTION, CLASSIFICATION or
PROCESSING parent. It cannot follow RECOVERY, ESCALATION or TERMINAL, and no
diagnostic may follow a parent whose disposition is TERMINAL. Existing
ESCALATION and TERMINAL parent restrictions remain exact. DETECTION has a null
parent and its own reference as root; every other stage has an actual predecessor
and the same actual StateModel root. Recovered or externally replaced states use
a new actual StateModel root and typed dependency links outside this envelope.
Every PROCESSING envelope preserves the actual originating DETECTION envelope's
subject_reference; producer-specific entity identifiers remain typed payload facts.

Success is INFO/RESOLVED at current impact; malformed/refused processing is
ERROR/BLOCKED. A false axiom is WARNING/BLOCKED. An inapplicable enumerated
transition is INFO/RESOLVED with applicability=false: absence is an observed
catalog decision, not failure of the entire resolution. A producer preserves the
maximum observed envelope severity along its chain even when a subsequent check
passes; payload current_impact preserves that check's own result. Axiom checks
continue after false results and overall_pass is computed only after all five.
The fifth check retains its actual component result; its final disposition is
RESOLVED exactly when overall_pass is true, otherwise BLOCKED. A1 through A4
use RESOLVED exactly when their own component passes, otherwise BLOCKED.

Every evaluated semantic step constructs its immutable typed envelope and payload
immediately, before the next semantic step. A pure producer performs no clock,
filesystem, network, collector, storage or arbitrary callback effect. It returns
its ordered owned records as part of the bounded result. Composition subsequently
persists each actual record in order and reports actual acknowledgments and once
completion. This ordered persistence is not deferred diagnostic production;
production never suppresses, combines or invents records. Capture failure does
not erase the constructed prefix or become confirmation. An effectful emitter
reserves the whole operation before first effect, captures actual dispatch and
receipt steps between effects, and stops further dispatch after failed capture.
No existing effectful StateModel/RecoveryEngine capture is moved or suppressed.
