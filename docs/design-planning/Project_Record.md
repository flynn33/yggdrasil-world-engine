# Yggdrasil World Engine — Project Record

**Record ID:** YWE-RECOVERY-20260918
**Revision:** planning-13
**Date:** September 20, 2026
**Authoritative branch:** `main`
**Location:** `docs/design-planning/Project_Record.md`
**Supersedes:** planning-12; full history remains in Git.

## 1. Current working brief

| Concern | Current state |
|---|---|
| Product / owner | Yggdrasil World Engine / Flynn, repository owner `flynn33` |
| Product purpose | Platform-neutral, strictly object-oriented and modular engine specification |
| Accepted milestones | M0 and M1 |
| Active milestone | M2 — Build the canonical contract and schema foundation |
| Next milestone | M3 remains planned and is not active |
| M2 acceptance | Not recorded; exit criteria are not yet satisfied |
| Platform products | Deferred until M10 acceptance |
| Publication | Unreleased; no GitHub Release objects exist as verified September 20, 2026 |

The machine-readable roadmap is milestone and status authority. Focused accepted contracts,
governance records, schemas, fixtures, and validators remain engineering authority.

## 2. Preserved approved direction

ASH Model Cosmology, the ASH Pattern System, and Aeostara are reference specifications.
They are not package, build, module, runtime, source-code, or repository dependencies.
YWE owns its domain model, object contracts, serialization contracts, and conformance
requirements. Preserve strict object orientation, explicit invariant ownership,
modularity, platform neutrality, and Core/profile separation. WRW and Ravenfall remain
reference-profile evidence rather than universal Core truth.

Working branches are preferred for bounded work. A completed branch must be merged or
deleted after preservation is verified. Owner-account publication and admin bypass remain
authorized when needed. Commit authorship must remain owner-only, with no co-author trailers.

## 3. Development method and source authority

Raven Forge Development remains the standing method. The previously adopted immutable
revision remains unrecovered. Version 0.6.2 at
`ed0028a46bac9c5b92876a6ad6589ca421fd9499` remains an inspected reference only, not a
silently adopted replacement. This correction does not upgrade the method or change any
reference-system source pin.

## 4. Verified M2 state

The September 19 schema-foundation migration is preserved on `main`. Current repository
evidence establishes:

| M2 item | Verified state |
|---|---|
| JSON Schema profile and offline-reference policy | Present in `data/validation/m2_json_contract_profile.json` |
| Protected descriptive-record migrations | Present in `data/validation/m2_contract_migration_manifest.json` |
| Declared schemas missing identifiers | 0 |
| Annotation-only schema documents | 0 |
| Schema-named JSON lacking declarations | 0 |
| Unbound JSON examples | 39 |
| Complete fixture catalog | Not present |
| Roadmap-derived M2 acceptance gate | Not present |
| Durable M2 acceptance report | Not present |
| M2 milestone evidence | Empty in the roadmap |
| M3 activation | Not authorized or recorded |

The earlier report that all M2 technical work was complete was not supported by the live
repository and is superseded. The owner's subsequent acceptance statement is not used as
milestone evidence because the stated exit conditions were not actually satisfied.

## 5. Remaining M2 obligations

1. Bind all 39 remaining JSON examples to exact schemas, instance pointers, expected
   outcomes, and intended requirement or error identifiers.
2. Complete the fixture catalog across positive, boundary, reject, recovery, replay, and
   migration coverage.
3. Provide a roadmap-derived M2 acceptance gate that verifies meta-schema validity,
   offline references, fixture bindings, intended reject reasons, and empty M2 schema debt.
4. Produce durable acceptance evidence and run the consolidated checks and M2 gate from a
   clean offline checkout.
5. Only after those checks pass, record M2 acceptance and activate M3.

## 6. Publication result and continuity

An initial temporary correction workflow at commit `79322d90b7c8e22284064ec44174a866c79c0772`
failed before modifying roadmap files because its compressed transport payload was
corrupted. The replacement used an inline reviewed patch, removed the temporary workflow,
ran the roadmap and consolidated repository checks, and published this planning-13 record.
The containing commit is the authoritative save point.

## 7. Checkpoint

**Current step:** M2 remains in progress with 39 unbound examples and missing milestone
acceptance infrastructure.

**Completed:** Corrected roadmap/status truth, preserved completed schema migration work,
and removed false M2-complete/M3-active implications.

**Next action:** Bind the remaining examples and build the complete fixture catalog and M2
acceptance gate.

**Needed from owner:** Nothing for continued M2 engineering.

**Saved at:** `main`, in the commit containing this planning-13 record.
