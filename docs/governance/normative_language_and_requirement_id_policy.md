# Normative Language and Requirement Identifier Policy

Date: 2026-07-19
Status: active M1 governance policy
Machine register: `data/governance/normative_requirement_register.json`

## Purpose

This policy defines how Yggdrasil World Engine specifications express binding
requirements and how those requirements receive permanent, reviewable
identifiers. It applies to normative prose, schemas, rule records, interfaces,
and governance artifacts in this repository.

## Normative Keywords

Only the exact uppercase keywords in this table carry normative force.
Lowercase uses are ordinary descriptive language. Text inside quotations, code
examples, fixtures, and historical records is not normative merely because it
contains an uppercase keyword. [YWE-REQ-0001]

| Keyword | Meaning |
| --- | --- |
| `MUST` | An unconditional requirement for conformance. |
| `MUST NOT` | An unconditional prohibition for conformance. |
| `SHOULD` | A requirement that may be departed from only when a documented, reviewed reason justifies the exception. |
| `SHOULD NOT` | A prohibition that may be departed from only when a documented, reviewed reason justifies the exception. |
| `MAY` | A permitted option; implementations remain conformant whether or not the option is used. |

When a `SHOULD` or `SHOULD NOT` exception is exercised, the exception must be
traceable to a typed governance record under
`governance_records_policy.md`. An uppercase keyword without a requirement
identifier is a drafting defect, not an unregistered requirement.

## Requirement Identifiers

A requirement identifier has the form `YWE-REQ-NNNN`, where `NNNN` is a
zero-padded decimal sequence. Every new or materially changed normative clause
MUST cite at least one stable requirement identifier. [YWE-REQ-0002]

Identifiers are allocated monotonically from the next available sequence
number. Once allocated, an identifier MUST NOT be renumbered, reused for a
different meaning, or deleted. Superseded, retired, or otherwise terminal
records remain in the register with their final status and replacement link
when applicable. [YWE-REQ-0003]

The citation form in Markdown is `[YWE-REQ-NNNN]`. Machine-readable artifacts
use the bare identifier string. A clause may cite multiple identifiers when it
implements multiple independently testable obligations. A single identifier
may be cited from multiple artifacts when those artifacts are mirrors or
different realizations of the same obligation.

## Requirement Record Fields

Each machine-readable requirement record includes:

- `normative_level`: `MUST`, `MUST_NOT`, `SHOULD`, `SHOULD_NOT`, `MAY`, or
  `mixed` when one statement intentionally contains more than one level;
- `authority_node`: the canonical truth-authority node that owns the rule;
- `scope_partition`: the canonical repository partition governed by the rule;
- `verification_refs`: durable repository checks that can evaluate the rule;
- `aliases`: retained alternative requirement identifiers, empty unless an
  accepted record explicitly establishes one; and
- `supersedes`: earlier stable requirement identifiers replaced by this
  record, empty when the requirement replaces none.

An alias does not create a second requirement identity. A superseded record
remains present with terminal status and links forward to its replacement.
Authority nodes are defined by
`data/governance/truth_authority_lattice.json`; scope partitions are defined by
`data/governance/scope_partition_manifest.json`.

## Allocation and Change Control

1. Reserve the next unused identifier in the machine register.
2. Record one concise, independently testable normative statement.
3. Record its owner, status, source references, and governing decision records.
4. Add the identifier citation to every new or changed normative clause that
   expresses the requirement.
5. Review semantic changes through a durable typed governance record.
6. If a meaning changes materially, allocate a new identifier and supersede the
   old record; do not rewrite the old identifier to mean something else.

Editorial clarification that does not change conformance behavior may retain
the identifier. Any uncertainty about whether behavior changed is resolved as
a material change and receives a new identifier.

## Typed Governance Requirement

Material architecture decisions, change proposals, risks, deviations, and
semantic questions MUST have durable typed records. [YWE-REQ-0004] Every
material decision MUST retain a durable rationale. [YWE-REQ-0017]

The record lifecycle, required fields, and current registers are defined by
`governance_records_policy.md` and
`data/governance/governance_record_register.json`.

## M1 Canonical Semantic Requirements

The following clauses establish the M1 terminology and authority baseline.
Their machine-readable statements are authoritative in the normative
requirement register.

- The nine-coordinate base ontology MUST remain immutable.
  [YWE-REQ-0005]
- Every mutable state change MUST be truth-scoped, typed, and
  provenance-bearing. [YWE-REQ-0006]
- Perception state MUST NOT rewrite shared truth. [YWE-REQ-0007]
- A coordinate index or bit position, an ordinal, a presentation order, a
  realm/plane identity, and a full vector or state identity MUST be treated as
  distinct concepts and MUST NOT be inferred from one another without an
  explicit mapping. [YWE-REQ-0008]
- The ASH Cosmological Model MUST own the upstream symbolic grammar used by
  YWE. [YWE-REQ-0009]
- The ASH dependency identity MUST be content-addressed and pinned by a
  deterministic digest. [YWE-REQ-0010]
- `wolf_resonance` MUST be the canonical field; `wolf_alignment` MAY be
  accepted only as a read or migration alias; the dual-variable model MUST NOT
  be interpreted as a moral axis. [YWE-REQ-0011]
- Accepted event history MUST be append-only. [YWE-REQ-0012]
- A reversal or correction MUST be represented by a new compensating delta and
  MUST NOT erase or rewrite the accepted event. [YWE-REQ-0013]
- A lower truth-authority layer MUST NOT overwrite a higher layer's
  constraints. [YWE-REQ-0014]
- A WRW-specific rule MUST NOT become normative YWE Core truth.
  [YWE-REQ-0015]
- `core/ash_pattern_engine/canonical` MUST be the authoritative ASH
  specification source, and `specs` MUST remain its deterministically
  synchronized generated mirror. [YWE-REQ-0016]
- Each glossary concept MUST have exactly one canonical definition.
  [YWE-REQ-0018]

## Register Authority and Review

The machine register is authoritative for identifier allocation, lifecycle
status, normative statement text, and decision traceability. This document is
the human-readable policy. A discrepancy between the two is a governance
defect and blocks acceptance until they agree.

Reviewers must verify:

- every new or changed uppercase normative clause cites an active or retained
  terminal requirement record;
- current identifiers are unique and ordered monotonically;
- terminal identifiers remain present and are never recycled;
- material semantic changes cite a typed governance record;
- source and decision references resolve to durable repository artifacts; and
- no lowercase descriptive wording is treated as binding merely by implication.
