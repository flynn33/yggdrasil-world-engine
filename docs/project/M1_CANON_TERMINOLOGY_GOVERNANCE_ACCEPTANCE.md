# M1 Canon Terminology and Governance Acceptance

## Baseline

| Field | Accepted value |
|---|---|
| Repository version | `2.0.23` |
| Base reference | `origin/main` |
| Base and merge-base SHA | `dba8ad31f35e680507cb990792e71ef3b173daee` |
| Implementation branch | `governance/m1-canon-terminology` |
| Pull request | [#69](https://github.com/flynn33/yggdrasil-world-engine/pull/69) |
| Publication state | `unreleased` |
| Platform work authorized | `false` |

The machine-readable evidence is
`data/governance/m1_acceptance_evidence.json`. The repository-state digest
excludes exactly that file and this document so that the acceptance pair does
not hash itself. The frozen non-evidence repository digest is
`dddf0d72267fdc3a692f76c64fdda2aa9141943708de5e30e3b7697325a65633`.

## Acceptance State

M1 passes when its ten deliverables, three exit criteria, ten assigned debts,
local validation, pull-request-context validation, ASH mirror check, math-change
review, and immutable M0 preservation all pass against one frozen repository
snapshot. The final recorded outcome is `pass`, with no unresolved issues.

## M1 Deliverables

| ID | Judgment | Durable evidence |
|---|---|---|
| `m1-d1` | PASS | Normative-language policy, `YWE-REQ-0001` through `YWE-REQ-0018`, register schema, and M1 checker |
| `m1-d2` | PASS | Typed governance policy and 27-record decision/proposal/risk/deviation/question register |
| `m1-d3` | PASS | Glossary ontology/worldstate/perception definitions, truth lattice, and scoped delta rules |
| `m1-d4` | PASS | Canonical coordinate vocabulary, term index, realm registry, and WRW coordinate projection |
| `m1-d5` | PASS | Symbolic-grammar ownership decision and content-addressed ASH dependency identity |
| `m1-d6` | PASS | Canonical `wolf_resonance` field with read-only `wolf_alignment` migration alias |
| `m1-d7` | PASS | Event-history, current-state-effect, reversal, and compensating-delta semantics |
| `m1-d8` | PASS | Ten-node typed truth and authority lattice with schema and conformance checks |
| `m1-d9` | PASS | Normative YWE Core/WRW scope contract and completed WRW source authorities |
| `m1-d10` | PASS | Canonical ASH source tree, deterministic mirror, identity digest, sync checker, and tests |

## M1 Exit Criteria

| ID | Judgment | Verification |
|---|---|---|
| `m1-e1` | PASS | The M1 checker rejects contradictory invariants, wrong authority edges, scope leakage, and the superseded static-world wording. |
| `m1-e2` | PASS | Every material M1 decision has an accepted ADR with context, decision, rationale, consequences, and requirement/debt links. |
| `m1-e3` | PASS | All 119 canonical terms have exactly one glossary heading and one term-index record; aliases cannot define competing concepts. |

## M1 Debt Closures

The inventory retains path-level evidence for compatibility and adds the exact
locators below for deterministic review.

| Debt | Judgment | Precise resolution locator |
|---|---|---|
| `QD-PH-dd00c6d30da8` | RESOLVED | `lore/wrw_cosmology/canon_scope.md` headings `Canonical Sources`; `In Scope`; `Out of Scope`; `Cross-Scope Rules` |
| `QD-PH-37cd25fd2cac` | RESOLVED | `lore/wrw_cosmology/source_notes.md` headings `Source Register`; `Provenance Rules`; `Source-to-Claim Map` |
| `QD-OW-001` | RESOLVED | `data/governance/specification_roadmap.json#/subsystems/0/open_work` is the accepted empty list; authority-boundary maturity is complete |
| `QD-063` | RESOLVED | `docs/glossary/ywe_design_glossary.md` headings `Ontology`; `Perception Overlay`; `Worldstate` |
| `QD-064` | RESOLVED | Glossary headings `Structural Coordinate`; `Coordinate Index`; `Presentation Order`; `Realm`; `Ordinal`; `ASH State Vector`; `State Identity` |
| `QD-065` | RESOLVED | `data/governance/ash_dependency_identity.json#/dependency_id` and truth-lattice heading `Symbolic-Grammar Ownership` |
| `QD-066` | RESOLVED | Glossary heading `Wolf Resonance`; `data/player_schema.json#/wolf_alias_policy` |
| `QD-067` | RESOLVED | `core/narrative_engine/worldstate_delta_rules.yaml` path `history_and_reversal_semantics.compatibility_aliases.reversals_require_new_worldstate_delta` |
| `QD-068` | RESOLVED | Scope-contract headings `YWE Core`; `WRW Reference Profile`; `Dependency Direction`; `Routing Rules` |
| `QD-069` | RESOLVED | `data/governance/ash_dependency_identity.json#/aggregate_sha256`; synchronization is enforced by `scripts/sync_ash_specifications.py --check` |

Inventory summary after closure: 81 total debts, 60 open, 20 resolved, and one
accepted exception. No debt assigned to M1 remains open.

## Requirement and Governance Metrics

| Metric | Accepted value |
|---|---:|
| Stable normative requirements | 18 |
| Typed governance records | 27 |
| Canonical glossary terms | 119 |
| Truth-authority nodes | 10 |
| ASH authoritative source files | 32 |

## Classification and Scope Coverage

The final 1,010-path snapshot has exactly one classification and one scope
assignment per path.

| Classification | Count |
|---|---:|
| Normative | 744 |
| Informative | 43 |
| Example | 160 |
| Historical | 12 |
| Deprecated | 1 |
| Superseded | 6 |
| Placeholder | 44 |

| Scope partition | Count |
|---|---:|
| YWE Core | 117 |
| YWE extension profile | 121 |
| ASH dependency material | 66 |
| WRW reference profile | 289 |
| Governance and validation | 339 |
| Historical evidence | 19 |
| Later-release work | 59 |

## ASH Dependency Identity and Mirror State

The dependency identifier is `ash_cosmological_model.f2_9.canonical`. Its 32
normalized authoritative files and synchronized mirrors have aggregate SHA-256
`0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb`.
The pinned markers remain nine dimensions, 512 states, and 16 codewords.

## Validation Results

| Context | Completed at | Result | Summary SHA-256 |
|---|---|---|---|
| Local | `2026-07-19T19:29:37Z` | 29/29 passed; zero blocking failures; zero advisories | `689ff79eb894f8383094add369f6fd8f703186ad46e2282d2589c9f4494e67cb` |
| Pull request | `2026-07-19T19:32:42Z` | 30/30 passed; zero blocking failures; zero advisories | `0157bc1be60330d3fe044c43b3b9aa0484148fb00a7fd54332df4b4f8c47cb57` |

The pull-request context uses `origin/main` as its base and includes the
non-destructive diff check.

## Diff Review

The final historical review records 22 created files, 91 patched files, zero
deleted files, and zero renamed files. The repository-state digest is
`dddf0d72267fdc3a692f76c64fdda2aa9141943708de5e30e3b7697325a65633`;
the binary-diff digest is
`af28b1ebe02e520752828ae0ecfde6f8de6dd09b6c274607fff90c1ccf6c3646`.
The two immutable M0 acceptance artifacts have no content change.

## Math-Change Review

The contemporaneous note is
`governance/math-change-notes/2026-07-19-ash-source-authority-and-realm-identity.md`.
GitHub records the `baseline-approved` label on PR #69, applied by `flynn33` at
`2026-07-19T18:51:44Z`. The accepted change corrects identity terminology and
source ownership while preserving the F2^9 baseline shape.

## M0 Immutability Confirmation

The M0 checker verifies byte-normalized equality to each artifact's
introduction commit for:

- `data/governance/m0_acceptance_evidence.json`
- `docs/project/M0_TRUTHFUL_BASELINE_ACCEPTANCE.md`

`VERSION` and `version.txt` both remain `2.0.23`. Publication remains
`unreleased`; no GitHub Release or specification release is created; platform
work remains unauthorized through the M10 gate.

## Roadmap Transition

The accepted transition is `M1 complete -> M2 in_progress`. M2 is the sole
active milestone and `current_milestone` is `M2`. Remaining M4 work is limited
to branch-merge/runtime-state semantics and perception persistence/location
conformance; M1 terminology is not carried forward as open work.

## Acceptance Judgment

M1 Canon Terminology and Governance is accepted only when the machine evidence,
this document, both complete validation contexts, and GitHub CI agree on the
same immutable evidence-introduction snapshot. The accepted snapshot has an
empty unresolved-issues list and does not authorize publication or platform
implementation.
