# Yggdrasil World Engine — Project Record

**Record ID:** YWE-RECOVERY-20260918
**Revision:** planning-14
**Date:** October 3, 2026
**Authoritative branch:** `main`
**Location:** `docs/design-planning/Project_Record.md`
**Supersedes:** planning-13; full history remains in Git.

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

The owner's October 3 instruction to read and follow the development policy establishes
a deliberate current method intake: Raven Forge Development v0.7.0 at immutable commit
`87409bc36fb9d4782eab02189adb184f2b3962a7`. The source was retrieved through Git and its
mandatory and applicable documents were read. This is a recorded method binding, not an
upgrade of any ASH, APS, Aeostara, or Forsetti reference-system source pin.

The earlier inspected v0.6.2 at `ed0028a46bac9c5b92876a6ad6589ca421fd9499` and the prior
unrecovered adopted revision remain historical provenance. This increment concerns
platform-neutral specification validation tools; no external runtime system is acquired
or newly realized. Python remains repository testing/analysis/automation tooling.

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
| Unbound JSON examples | 19 after executed catalog bindings and Phase 12 corrections |
| Fixture catalog | Initial 102 structural bindings present; full coverage remains incomplete |
| Offline resolver | Explicit catalog covers 197 declared schemas and resolves references locally |
| Roadmap-derived M2 acceptance gate | Not present |
| Durable M2 acceptance report | Not present |
| M2 milestone evidence | Empty in the roadmap |
| M3 activation | Not authorized or recorded |

The earlier report that all M2 technical work was complete was not supported by the live
repository and is superseded. The owner's subsequent acceptance statement is not used as
milestone evidence because the stated exit conditions were not actually satisfied.

## 5. Remaining M2 obligations

1. Bind all remaining JSON examples to exact schemas, instance pointers, expected
   outcomes, and intended requirement or error identifiers.
2. Complete the fixture catalog across positive, boundary, reject, recovery, replay, and
   migration coverage.
3. Provide a roadmap-derived M2 acceptance gate that verifies meta-schema validity,
   offline references, fixture bindings, intended reject reasons, and empty M2 schema debt.
4. Produce durable acceptance evidence and run the consolidated checks and M2 gate from a
   clean offline checkout.
5. Only after those checks pass, record M2 acceptance and activate M3.

## 6. Current work and verification

Starting branch: `main`, base `fc25065304e2392b043c205a57d0564d33a49139`.
Working branch: `m2/fixture-catalog`. The initial checkout was clean.

The initial consolidated suite returned 26 passing checks and three blocking failures.
The failed unit, M0, and M1 checks all reported classification/scope snapshot drift:
`.github/workflows/m2-fixture-analysis.yml` was added after the last inventory refresh.
The inventory reconciliation retains the existing assignment rules and immutable M0/M1
acceptance records.

The new catalog selects exact schemas and pointers for 20 existing positive examples,
all 17 common contracts, field representation boundaries, and 49 single-constraint rejections. Failed
entries cannot clear debt. Rejection witnesses include keywords, instance/schema paths,
and exact missing required members. Independent regression checks cover catalog drift,
offline references, unused branches, target selection, duplicate resource identities,
pointer escapes, and mutations that change the expected result or reason.

Five Phase 12 fields now accept their existing string arrays as well as legacy
nonempty strings. The earlier generator's name-based string fallback caused these
schema/example disagreements. Forty exact field cases exercise compatible
acceptance and rejected values; three existing positive examples now pass. The
quest example's missing `quest_title_policy` remains unresolved because its required
status predates the migration and the repository does not define its intended value.

The accepted repository baseline remains `v2.0.23`; this is unreleased M2 work,
not a new baseline acceptance, Git tag, or specification publication.

The final working-tree consolidated run returned 29 passing checks and one unit-check
failure captured before the working-branch attribution correction. The exact failing
`LiveM1ContractTests.test_live_external_guardrails_pass` then passed after that correction;
the standalone attribution check also passed. Independent diff review found no blocking
findings. A fresh clean-checkout consolidated run and GitHub publication remain pending
before delivery. M2 acceptance and M3 activation remain unrecorded.

## 7. Historical publication continuity

An initial temporary correction workflow at commit `79322d90b7c8e22284064ec44174a866c79c0772`
failed before modifying roadmap files because its compressed transport payload was
corrupted. The replacement used an inline reviewed patch, removed the temporary workflow,
ran the roadmap and consolidated repository checks, and published this planning-13 record.
The containing commit is the authoritative save point.

## 8. Checkpoint

**Current step:** M2 fixture catalog, offline resolver, and source-backed schema
representation corrections; milestone acceptance remains outstanding.

**Completed:** Initial executable catalog and rejection witnesses; corrected stale
baseline inventories; recorded current development-policy intake.

**Next action:** Complete remaining fixture bindings and lifecycle coverage, then build
the roadmap-derived M2 acceptance gate and durable evidence.

**Needed from owner:** Nothing for continued M2 engineering.

**Saved at:** The Git commit containing this planning-14 record; publication pending
verification at the time of this draft.
