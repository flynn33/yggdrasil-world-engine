# Yggdrasil World Engine — Project Record

**Record ID:** YWE-RECOVERY-20260918
**Revision:** planning-15
**Date:** October 3, 2026
**Authoritative branch:** `main`
**Location:** `docs/design-planning/Project_Record.md`
**Supersedes:** planning-14; full history remains in Git.

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
| Fixture catalog | 136 structural bindings, including YAML module manifests; full coverage remains incomplete |
| Offline resolver | Explicit catalog covers 198 declared schemas and resolves references locally |
| YAML structural schemas | Module capability contract covered; other YAML domains remain outstanding |
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

## 6. Fixture foundation verification

Starting branch: `main`, base `fc25065304e2392b043c205a57d0564d33a49139`.
Working branch: `m2/fixture-catalog`, fast-forward integrated into `main`.
The initial checkout was clean.

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

The fresh local clone at implementation commit
`f35911a4a77c93dc6fe32bb2e396c60bcf01fbc2` passed `bash scripts/run_checks.sh`:
30 checks passed, zero blocking failures, zero advisories, including all 297 unit tests.
The clone was clean before and after validation. Its external test environment used
Python 3.12.10, `jsonschema==4.25.1`, and `PyYAML==6.0.3`. Offline references were resolved
without schema retrieval. The committed non-destructive diff check against the original
`origin/main` base also passed (23 modified, zero deleted/renamed, ten added files).

The earlier working-tree run captured one attribution test failure before the branch
name was corrected; the exact failing test passed afterward and the fresh clone suite
passed in full. Independent diff review found no blocking findings.

Implementation commit `f35911a4a77c93dc6fe32bb2e396c60bcf01fbc2` was pushed under the
verified owner account and remote `main` was read back at that exact revision. GitHub
reported the owner's authorized bypass of pull-request and verified-signature rules.
The following documentation checkpoint records those executed results; executable
source, schema, fixture, and test contents are unchanged. M2 acceptance and M3 activation
remain unrecorded.

## 7. YAML structural continuation

Starting branch: `main`, base `88406268d1e3ef24c15e132fa49e9be7440319cf`.
Working branch: `m2/yaml-module-manifests`. The initial checkout was clean.
GitHub Main CI passed the published fixture foundation at that base revision:
`https://github.com/flynn33/yggdrasil-world-engine/actions/runs/37163320518`.

The existing module capability checker reads text markers and checks template
identifiers; it does not execute the YAML descriptor's field type and enum rules.
This continuation adds a formal JSON Schema for its 23 declared root properties,
16 required fields, typed nested members, enums, and the explicit minimum
non-delegable responsibility for foundational/structural authority. Requirement
`YWE-REQ-0022` and accepted decision `ADR-0013` record the scope and boundaries.

The loader parses YAML using the existing duplicate-key-rejecting SafeLoader and
preserves JSON scalar types. YAML-only values and non-string mapping keys cannot
enter JSON Schema validation. The catalog adds ten applied manifests, two embedded
source examples, and 22 positive/boundary/reject cases. All 136 bindings and 64
intended rejections passed the focused catalog check using the pinned runtime.

The original YAML descriptor and applied manifests are unchanged. Open objects,
optional nested fields, and unspecified empty-value boundaries remain open.
Registry uniqueness, dependency graphs, prose truth-boundary semantics, other
YAML domains, and lifecycle conformance remain outstanding. The 19 JSON binding
debt entries are unchanged. Consolidated clean-checkout verification and
publication of this continuation are pending at this draft checkpoint.

## 8. Historical publication continuity

An initial temporary correction workflow at commit `79322d90b7c8e22284064ec44174a866c79c0772`
failed before modifying roadmap files because its compressed transport payload was
corrupted. The replacement used an inline reviewed patch, removed the temporary workflow,
ran the roadmap and consolidated repository checks, and published this planning-13 record.
The containing commit is the authoritative save point.

## 9. Checkpoint

**Current step:** M2 YAML module-manifest structural conformance; milestone
acceptance remains outstanding.

**Completed:** Executable JSON fixture foundation and offline resolver, compatible
Phase 12 representations, current development-policy intake, and initial YAML
module-manifest structural schema and bindings.

**Next action:** Complete remaining fixture bindings and lifecycle coverage, then build
the roadmap-derived M2 acceptance gate and durable evidence.

**Needed from owner:** Nothing for continued M2 engineering.

**Saved at:** The commit containing this planning-15 record. The prior validated
implementation save point is `f35911a4a77c93dc6fe32bb2e396c60bcf01fbc2`, with its
published verification checkpoint at `88406268d1e3ef24c15e132fa49e9be7440319cf`.
