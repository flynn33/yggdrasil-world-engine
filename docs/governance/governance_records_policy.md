# Governance Records Policy

Date: 2026-07-19
Status: active M1 governance policy
Machine register: `data/governance/governance_record_register.json`

## Purpose

This policy makes material governance work durable, typed, traceable, and
reviewable. Architecture decisions, change proposals, risks, deviations, and
semantic questions MUST be recorded when they can change conformance, canon,
authority, scope, compatibility, or accepted repository behavior.
[YWE-REQ-0004]

Every material decision MUST preserve its context, decision, rationale,
consequences, owner, requirement references, and source references.
[YWE-REQ-0017]

## Register Authority

`data/governance/governance_record_register.json` is the machine-readable
authority for current governance records and lifecycle state. This document is
the human-readable lifecycle and review policy. Historical source logs remain
provenance and are not rewritten or deleted when their records are normalized
into the current register.

## Record Types

| Type | Prefix | Purpose | Active lifecycle states |
| --- | --- | --- | --- |
| Architecture decision | `ADR-NNNN` | Records a durable architecture, terminology, canon, or authority decision. | `proposed`, `accepted`, `superseded`, `rejected` |
| Change proposal | `CP-NNNN` | Proposes and tracks a bounded governance or specification change. | `draft`, `under_review`, `accepted`, `implemented`, `rejected`, `withdrawn` |
| Risk | `RISK-NNNN` | Records a material uncertainty, failure mode, control, and residual exposure. | `open`, `mitigated`, `accepted`, `closed` |
| Deviation | `DEV-NNNN` | Records a departure from an accepted requirement or package authority. | `requested`, `approved`, `expired`, `resolved`, `rejected` |
| Question | `Q-NNNN` | Records a semantic question whose answer can alter normative meaning. | `open`, `resolved`, `deferred`, `withdrawn` |

Identifiers are monotonically allocated within each type. They are never
renumbered, reused for another meaning, or removed after allocation. Terminal
records remain present so citations and historical review stay valid.

## When a Record Is Required

A durable typed record is required when a proposed or observed change can:

- change the meaning of a normative requirement;
- select one authority, source, scope, vocabulary, or migration rule over
  another;
- permit an exception to `SHOULD` or `SHOULD NOT` wording;
- introduce, accept, mitigate, or close a material risk;
- depart from an accepted requirement or authority package;
- resolve competing interpretations of canon or system behavior; or
- change how an authoritative source and a generated mirror synchronize.

Routine spelling, formatting, and mechanically generated updates that cannot
change meaning do not require a new record. If reviewers disagree about whether
meaning can change, a question record is required before acceptance.

## Required Record Content

Every record contains:

- a permanent typed identifier;
- a concise title and lifecycle status;
- the record date and accountable owner role;
- enough context to identify the problem without relying on conversation
  history;
- the disposition, resolution, mitigation, or decision;
- links to affected requirements and durable repository sources; and
- type-specific evidence such as rationale, consequences, controls, follow-up,
  or implementation artifacts.

References use repository-relative forward-slash paths. JSON Pointer fragments
may follow `#`. References to untracked local files, transient conversations,
or external branch names are not durable evidence.

## Architecture Decisions

An accepted ADR states the chosen rule, why it was selected, and its expected
consequences. Replacing an accepted decision requires a new ADR; the earlier ADR
is retained as `superseded` and links to its replacement. Accepted decision text
is not silently rewritten to represent a later choice.

## Change Proposals

A CP defines a bounded proposal and its implementation evidence. `implemented`
means every listed implementation artifact exists and the proposal's accepted
scope is present; it does not by itself claim milestone acceptance. Withdrawal
or rejection remains recorded.

## Risks

A risk records likelihood, impact, mitigation, controls, and residual risk.
`mitigated` means the named controls exist and reduce the risk; it does not mean
the failure mode is impossible. `accepted` requires a durable rationale and
owner rather than an undocumented waiver.

The M1 seed explicitly controls:

- migration-alias ambiguity around `wolf_alignment` and `wolf_resonance`;
- WRW reference-profile scope leaking into normative YWE Core; and
- drift between the authoritative ASH source and generated `specs` mirror.

## Deviations and Historical IDs

The current deviation series uses `DEV-NNNN`. Historical `D-NNN` identifiers in
`conformance/deviation-log.md` remain unchanged as provenance. The current
register maps `DEV-0001` through `DEV-0005` one-to-one to legacy `D-001`
through `D-005`. The mapping supplements the historical log; it does not erase
or retroactively rename it.

A `requested` deviation identifies the affected authority, duration,
containment, owner, and resolution criteria. `approved` records explicit
authorization; `expired` records the end of a time-bounded authorization;
`resolved` requires a recorded resolution; and `rejected` records that the
requested departure was not authorized. None may be presented as ordinary
conformance without its recorded disposition.

## Questions

A semantic question remains `open` until one accepted decision record answers
it. A `resolved` question links exactly to its controlling ADR and restates the
answer without creating a competing authority. `deferred` identifies a future
milestone or condition and cannot be used to imply a current decision.
`withdrawn` retains a question that no longer requires an answer without
presenting it as resolved.

The M1 seed resolves the eight semantic questions governed by ADR-0003 through
ADR-0010: ontology and worldstate, realm-coordinate vocabulary, ASH ownership
and identity, wolf resonance migration, history and reversal, truth authority,
Core/WRW separation, and ASH source/mirror synchronization.

## Review and Integrity Rules

Before a governance-register change is accepted, reviewers must verify:

1. identifiers are unique, correctly typed, and monotonically allocated;
2. every cross-reference resolves to an existing record, requirement, or
   durable repository source;
3. status-specific fields support the claimed lifecycle state;
4. each resolved question points to one accepted decision;
5. each mitigated risk names concrete controls and residual exposure;
6. historical deviation mappings are complete and do not delete history;
7. summaries equal the record collections; and
8. the register conforms to its Draft 2020-12 JSON Schema.
