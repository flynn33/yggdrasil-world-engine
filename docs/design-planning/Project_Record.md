# Yggdrasil World Engine — Project Record

**Record ID:** YWE-RECOVERY-20260918
**Revision:** planning-27
**Date:** October 4, 2026
**Authoritative branch:** `main`
**Location:** `docs/design-planning/Project_Record.md`
**Supersedes:** planning-26; full history remains in Git.

## 1. Current working brief

| Concern | Current state |
|---|---|
| Product / owner | Yggdrasil World Engine / Flynn, repository owner `flynn33` |
| Product purpose | Platform-neutral, strictly object-oriented and modular engine specification |
| Accepted milestones | M0, M1 and M2 |
| Active milestone | M3 — Complete core deterministic semantics and the reference oracle |
| Next milestone | M4 remains planned; its dependency is M3 acceptance |
| M2 acceptance | Complete; immutable evidence records all six exit criteria and eight deliverables |
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
| Unbound JSON examples | 0; strict classified structured-fixture coverage passed |
| Fixture catalog | 672 exact bindings and 246 intended schema or semantic rejections; reviewed source-bound scenarios checked separately |
| Offline resolver | Explicit catalog covers 212 declared schemas; unknown resources remain denied |
| YAML structural schemas | All classified YAML fixture domains have exact format bindings; registered descriptor semantic grammars execute |
| Roadmap-derived M2 acceptance gate | All six criteria and eight deliverables passed with completed clean offline execution and historical replay |
| Durable M2 acceptance report | Immutable `data/governance/m2_acceptance_evidence.json` and `docs/project/M2_CONTRACT_SCHEMA_FOUNDATION_ACCEPTANCE.md` |
| M2 milestone evidence | Exact immutable evidence pair referenced in the roadmap |
| M3 activation | Active after verified M2 closure; no M3 acceptance or runtime completion claimed |

The earlier report that all M2 technical work was complete was not supported by the live
repository and is superseded. The owner's subsequent acceptance statement is not used as
milestone evidence because the stated exit conditions were not actually satisfied.

## 5. Active M3 work and preserved M2 controls

M2's six criteria and eight deliverables are discharged by the exact immutable
acceptance pair and its executed historical evaluator. Original failed candidate
reports and earlier partial checkpoints below remain historical evidence.

The first bounded M3 StateModel slice is implemented under adopted
YWE-REQ-0039 / ADR-0029. Immutable values own exact construction and packet
invariants; StateModel owns bounded decoding, profile-based diagnosis, source-ordered
contextual classification and its acknowledged diagnostic prefix. The legacy
facade, snapshot and planner use diagnosis-only records, preserving all 512
identities, fixed codewords and lossless aliases. Source/profile verification for
this reference assembly occurs during adoption and publication checks; constructors
compare immutable reviewed pins without claiming a fresh source load. Production
and native/platform assembly remain deferred.

Independent tests execute all 1,536 profile/state combinations and 64 classifier
cases, original identity tests, 8,192 codeword transforms, hostile input boundaries,
retained capture/evidence failures, twenty separately authored packet fixtures and
59 structural mutations with exact keyword/location witnesses. Normal repository
integration additionally checks isolated selected-root identity loading and the
exact approved reference paths. These are bounded reference/format checks, not
M3 acceptance or implemented recovery.
Subsequent M3 work includes actual normalization, recovery, fallback, containment,
safe halt, deterministic generation, serialization, lifecycle and resource bounds.
Maintain the M2 catalogs, intended rejection correspondence, permanent migration
proofs and immutable acceptance verifier as new contracts are added. The five M3
exit criteria remain outstanding; platform products are deferred through M10.

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
Working branch: `m2/yaml-module-manifests`, fast-forward integrated into `main`.
The initial checkout was clean.
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
debt entries are unchanged.

Implementation commit `ab1080b1c1b60a9e379d5cd25f52db2ec418a729` passed the
consolidated `python scripts/validate_repository.py` suite in a fresh local clone:
30 checks, zero failures or advisories, and all 323 unit tests passed. The clone
remained clean. Its pinned external runtime used Python 3.12.10, jsonschema
4.25.1, and PyYAML 6.0.3; catalog references resolved locally without schema
retrieval. The committed non-destructive diff check against the base passed with
15 modified files, four additions, and zero deletions or renames. Independent
review found no blocking findings, and the focused YAML suite passed 26 tests.

The implementation was pushed under the owner account; remote `main` was read
back at that exact revision. GitHub reported the authorized pull-request and
verified-signature rule bypass. The following documentation checkpoint records
those executed results without changing executable/schema/fixture/test content.

## 8. Continuous roadmap development

The owner explicitly authorized continued roadmap development and a goal to finish
it on October 4, 2026. Publication checkpoints do not end that work. Continue M2
until every deliverable and exit criterion has executed evidence, then proceed in
dependency order through M10. The development method and publication authorization
in sections 2–3 remain in force; no owner input is needed for the current work.

Working branch: `m2/acceptance-readiness`, starting from
`2dc31af8ff70054fa6899de34fb10a0809c05844`. This increment adds explicit bindings for
44 existing full-root examples and six historical/preview formats, restores four
observed legacy player object representations, and executes YAML pattern archetype
structure for 49 original records and a seed registry. Requirements 23–26 and
ADRs 14–16 record the scope. Original example and YAML source contents are preserved.

The strict report enumerates all classified structured examples, including inline
labels and examples outside `examples/`; legacy debt counts do not establish full
coverage. Definition validation is registered in the normal suite and explicitly
reports that it does not evaluate milestone acceptance. The report retains failed
and unverified obligations. Executed full-suite reports capture revision, catalog,
context, selected checks, return codes, tool versions, checkout state, and completion.
Incomplete final checkout capture cannot create passing evidence. Offline controls
cover schema retrieval and remote Git protocols, with dependencies prepared first.

The focused fixture check passed all 326 bindings and 121 intended rejections.
Additional legacy `scripts/github/Test-SchemaIntegrity.ps1` verification returned
22 findings on existing quest-seed, myth/perception/prophecy and wolf-canon paths.
Those paths are unchanged; this supplemental script is outside the canonical check
catalog. Its findings are recorded for investigation, not treated as passing.
Implementation commit `b0b0a6934fbc96f050d0cd656985a790d984c206` passed
`python scripts/validate_repository.py --offline --report <external-report.json>`
in a fresh local clone: 31 checks, zero blocking failures or advisories, and all
389 unit tests passed. The checkout was clean before and after the run. The
external runtime used Python 3.12.10, jsonschema 4.25.1, PyYAML 6.0.3, and
referencing 0.37.0. The committed non-destructive diff check against the base
passed with 21 modifications, eight additions, and zero deletions or renames.

The strict report accepted that executed checkout evidence for criterion M2-C6
and returned the expected failing readiness result. Ninety classified fixture
units lack successful exact bindings; intended rejection coverage, domain YAML,
positive requirement traceability, lifecycle categories, method-specific validation,
and durable milestone evidence remain incomplete. No M2 acceptance or M3
activation is recorded. Independent source/diff review found no blocking issue.

The earlier working-tree suite reported two blocking checks, including incorrect
Core routing for two new profile schemas and a boundary test loaded before the
concurrent family-schema update. Explicit profile/governance assignments and the
correct case targets resolved them; focused checks and the frozen clone suite
then passed. The first verification harness completed both checks but failed while
decoding Windows console output as UTF-8. The structured UTF-8 reports were read
successfully and the diff check was executed separately; no test pass was inferred
from the failed harness.

The first publication attempt received a connection reset. Remote state was read
back at the original base, the retry succeeded, and remote `main` was confirmed at
that exact implementation revision. GitHub reported the owner's authorized
pull-request and verified-signature rule bypass. This documentation checkpoint
records those executed results; development continues after publication.

## 8a. Descriptor and intended-rejection continuation

Working branch: `m2/descriptor-and-rejection-conformance`, starting from
`faec4b293160b4fb049ddd771e74ef1c73019d34`. Requirements 27-30 and ADRs 17-20
record four bounded changes: explicit YAML descriptor grammars and meta-reference
checks, existing ability invariants, source-bound intended rejection execution,
and exact protected Phase 9 representation corrections.

The catalog adds 23 original branch/Phase17 roots, 24 original Phase16 roots,
four unchanged Phase9 roots, negative-description format bindings, and independent
ability, descriptor and Phase9 positive/boundary/reject cases. Original example
and YAML source bytes are preserved. Format acceptance and selected assertion
projections do not certify complete runtime packets or domain algorithms.

The scenario checker binds source digests and values to executed assertions.
Independent review reproduced a same-valued-constant substitution that initially
allowed a morality description to be witnessed by a permanent-death error. The
corrected design links executed schema keywords and lexical terms to their exact
owning assertions, with explicit source mappings for local projections. Unrelated
errors, unaccepted mutation controls and unexecuted bound constraints cannot
establish intended rejection. A second shared-keyword review found that changing
the missing field under the same required array could retain its owner binding;
exact required-member ownership closes that substitution as well.

Further review reproduced unrelated string replacements under the same enum or
constant and numeric substitutes for Boolean values in constant-only schemas.
Scalar mutation bindings now select exact source literals or strictly Boolean
inverses of the executed constant at the same target. These obligations preserve
the intended rejected value as well as its error keyword.

A composed probe removed the wrong field and consumed the original required
member as an unrelated replacement literal. Required-member ownership is now an
independent obligation that only the actual missing-member witness can satisfy.
The fresh focused run passed 69 scenario tests and all 24 original controls.

The first working-tree full run reported 30 passing checks and three blocking
checks. The registered-check contract omitted the two new check identifiers;
the unit suite detected that mismatch, and the branch-language scanner found two
negative literals whose existing rejection context was too far away in the new
catalog serialization. The check contract and context placement were corrected.
The subsequent working-tree run passed all 33 checks and 525 tests; later
composed-probe fixes were verified separately in fresh focused processes. A frozen
clean-checkout run remains required before publication; this dirty run is not M2
checkout-acceptance evidence.

The first clean clone of implementation `3991ebf6e8d851c9e9726b61d9924056d8a7ec92`
passed 32 checks but failed the Phase10 added-code check. Its explicit validation
tool allowlist omitted the six newly registered check/test scripts. That dirty
working run compared committed history and had not inspected uncommitted file
additions. The existing allowlist now names those six exact validation paths;
the forbidden extension policy and general platform scanner remain in force.
The failed clone report is retained, and publication requires a fresh frozen run.

The Phase9 correction preserves every original migration record and hash and adds
exact whole-property assertion transitions. The permanent verifier reads the
actual pre-migration parent `b61b49eaf9dce30058a86b52fd4910087fc9e4da` and original
migration `5b30dd50533d00b4c0852d45df3dfac61b3a4147`, validates all eight original
proofs, and reconstructs each corrected original schema. The potential formula,
legacy example shapes, required fields and protected examples remain unchanged.
Empty containers and source-unrestricted string-list items remain permitted; the
old nonempty whole-string constraint remains in force.

The legacy QD-001 subledger is resolved: its four categories are empty and all
505 catalog bindings and offline references passed the focused evaluator. The
strict report still identifies
18 uncovered source roots and 20 YAML paths. The remaining JSON roots are recovery
minimum descriptions and Phase16 design previews; the realm YAML collection mixes
lawful records and unlawful descriptions and needs individual units. Positive
requirement traceability, lifecycle categories, method-specific validation and
durable acceptance remain outstanding. No M2 acceptance or M3 activation is
recorded. Development continues after the verification/publication checkpoint.

## 8b. Executed descriptor and rejection checkpoint

Implementation `358f4ad1a9db419ed9cc91b96c1f309f49bf946f` includes the descriptor,
ability, source-bound rejection and protected representation changes, plus the
exact Phase10 validation-tool allowlist correction. Both implementation commits
were authored and committed by Jim Daley under the repository owner's identity.

A fresh local clone passed the canonical offline runner: all 33 checks passed,
with zero blocking failures or advisories, and all 528 unit tests passed in
218.456 seconds. The checkout was clean before and after execution, and the
report captured its completed final state. The external runtime was Python
3.12.10, jsonschema 4.25.1, PyYAML 6.0.3 and referencing 0.37.0. The separate
non-destructive diff check against `faec4b293160b4fb049ddd771e74ef1c73019d34`
passed with 25 modifications, 15 additions, and zero deletions or renames.

Executed reports and logs are preserved outside the repository in
`C:/Users/james/AppData/Local/Temp/ywe-m2-descriptor-evidence-20261004-yalx_42f`.
The earlier failed clone evidence is preserved separately; it is not acceptance
evidence. Independent review passed all 24 original scenarios and rejected all
18 altered-catalog probes, including both composed source-consumption escapes.

The strict M2 report accepted the clean execution evidence for C6. C1, C2, C4
and C5 also passed. C3 still reports 18 uncovered source roots: 432 of 450
classified fixture units have successful exact bindings. All 24 designated
rejection units have executed intended witnesses, with 179 schema rejection
bindings and 24 source-bound scenarios. D4 still reports 20 unbound YAML paths;
D5 lacks governed positive identifiers; D6 lacks executable lifecycle categories;
D7 and D8 remain unverified. The overall readiness result remains false.

The owner-authorized push succeeded, and remote `main` was read back at the exact
implementation revision. GitHub reported the authorized pull-request and verified
signature rule bypass. M2 remains active, M3 remains planned, and development
continues with the remaining format bindings and acceptance evaluators.

## 8c. Remaining formats and validation operations

The seventeen original recovery-minimum and Phase16 preview roots now have
explicit typed formats. The twenty remaining YAML policy roots and five realm
collection records have exact structural bindings. Original source bytes remain
unchanged. Recovery-minimum descriptions retain `acceptance.complete=false`;
format acceptance does not promote descriptive previews to completed runtime
packets. Governed positive expectation identities establish actual fixture
selection and result matching, with narrower identities tied to resolved schema
ownership.

Four concrete validation operations execute recovery, replay and protected
migration proofs. The full registered descriptor semantic pipeline is included
in validation replay. Two scoped realm assertion scenarios bind the original
unlawful units to their actual violated rules, rejecting both cross-unit vector
swaps and omitted declared-rule witnesses. Focused checks passed 669 exact
bindings, including 246 structural or semantic rejections, 26 source-bound
scenarios, 49 fixture tests, 79 rejection tests and 35 operation tests. These
focused results do not establish clean-checkout M2 acceptance.

Independent review identified the ownership alias and replay semantic omissions
and the two realm correspondence escapes. The implementation includes regression
coverage for each. Eight-method execution now passes its actual consumers and focused tests.
Immutable acceptance evidence is being integrated next. No milestone promotion
is recorded.

The previous planning-18 checkpoint at
`3cd1ac6d81bc51ee9231b29e94d80558537d8154` also passed the manual Main CI run
`37211339161` on GitHub. That CI result belongs to the previous checkpoint.
The new increment still requires its normal suite, frozen checkout and final
diff verification before publication.

## 8d. Final integrated verification and rejection correspondence

The initial integrated normal run passed all 674 unit tests and 35 of its 36
applicable checks. The remaining branch-language check reported two rejected
literals whose expanded JSON formatting had separated them from their forbidden
source context. Serialization-only corrections preserved typed JSON values and
the scanner; the actual branch check now passes.

Independent review reproduced four original whole-execution substitutions:
both Phase17 wolf morality/permanent-death swaps and both player morality/ASP
authority swaps. Each retained its descriptor identity and reason but executed
an unrelated rejection, which the coverage consumer incorrectly counted.
YWE-REQ-0038 and ADR-0028 introduce a separate reviewed execution-contract ledger.
All 26 existing mappings were independently audited against their source owners
and exact scope. The evaluator executes the existing ownership and witness
checks, then requires exact approval correspondence before returning coverage.
Unknown, missing, altered, duplicate and unused approvals cannot clear the full
catalog check. The integrated focused rejection suite passed 95 tests in 24.332
seconds, including the four original substitutions.

The candidate now binds 672 instances, including 246 intended schema or semantic
rejections, with 26 separately approved source-bound scenario executions.
Repository classification covers 1,158 paths and 212 declared schemas. The four
legacy schema-debt categories remain empty. The frozen clean full-suite execution
and immutable M2 evidence introduction remain outstanding; M2 is still active
and M3 remains planned. README now includes this development checkpoint so the
owner can follow progress on GitHub between accepted milestone gates.

## 8e. Clean-candidate governance correction and introduction delta

The frozen candidate `f2b6896db3e5f25c59a13ebbfc6e280ca4c63461` ran all 36
applicable checks from a clean offline clone. It passed 34 checks; the unit suite
and M1 governance check failed on the same uncited new normative paragraph.
The unit run executed 688 tests in 430.974 seconds with that one failure. The
paragraph now carries its existing YWE-REQ-0038 citation; the actual M1 governance
check passes. This failed evidence is preserved at
`C:/Users/james/AppData/Local/Temp/ywe-m2-final-implementation-evidence-20261004-z6avb427`.

A synthetic history probe also showed that snapshot equality alone allowed an
acceptance introduction to restore an intervening source edit. The historical
verifier now checks the introduction's own changed paths against every parent,
permitting only the fixed evidence pair. Restoration during introduction and
second-parent restoration reject; restoration completed before introduction and
pair-only merges remain valid. The unchanged source-state, file-mode and immutable
history checks still apply. The focused historical suite passed all 38 tests in
41.407 seconds, and independent actual clone probes passed the relevant controls.
The corrected implementation still requires a new complete frozen clean run.

## 8f. Clean execution and deterministic evidence correction

The published implementation `7c17397e4844960430832a9c7c3745237dcf6df1`
passed all 36 applicable checks and 692 unit tests from a clean offline clone.
The captured report records no blocking or advisory check failures and a clean
checkout before and after execution. Manual GitHub Main CI run `37218826994`
also passed for that exact revision. These results establish the tested
implementation, not its immutable acceptance introduction.

An external pair-only introduction rehearsal at
`c5920d16d9502d87703461efea3df87497a4c957` failed its actual historical replay.
The actual comparison found that only the reference method's case-list order
differed; its complete duplicate-preserving cases, results and witnesses matched.
The pinned `referencing` 0.37.0 source traverses subschema keywords through sets.
The method producer preserved that process-dependent traversal order, which the
strict historical comparison correctly rejected. The failed introduction was
not imported into the authoritative repository.

The producer now sorts reference, effective-identifier and anchor enumeration
before executing and recording those cases. It retains every duplicate and
does not relax the immutable verifier. A focused subprocess regression executes
mixed keyword families, nested identifiers, anchors and duplicate references
under three hash seeds. It fails against the original implementation and passes
against this correction. A new frozen full execution and formation are required;
the previous implementation's report cannot discharge the corrected revision.

## 8g. Durable M2 closure and M3 activation

The immutable M2 record identifies the actual frozen implementation revision,
completed clean offline repository report, exact source digest and evaluated
formation judgments. The first accepted introduction changes only the fixed
record/document pair; subsequent status changes preserve both files verbatim.
The historical evaluator independently replays the exact implementation snapshot
and all concrete validation operation/method results. The strict gate passed all
six criteria and eight deliverables before this status transition.

M2 acceptance covers the contract/schema validation foundation. Its recovery,
replay and migration operations exercise validation tools; they do not establish
future runtime recovery, persistence or multiplayer behavior. M3 is activated with
its existing scope and five unchanged exit criteria. No release or platform
product authorization follows from M2 acceptance.

The referenced immutable record and document are the exact source for executed
suite counts, tool versions, implementation identity and acceptance judgments.
No later dirty-tree or selected-check report replaces that original evidence.

## 8h. First M3 StateModel reference slice

The assessment contract was adopted before implementation, with YWE-REQ-0039
and ADR-0029 appended while preserving prior registered records. The new separate
packet schema does not replace either accepted M2 diagnostic format. Its twenty
independently authored accepted format fixtures have exact catalog pointers and
requirement identities; fixture acceptance includes valid serialized failure
outcomes and does not assert recovery success.

Review reproduced a metaclass equality hook through tuple membership in type
guards; identity-only guards now avoid that hook. Constructor-to-wire review also
removed an unsupported assumption that every truncated string prefix implies an
original length above 64. A further frozen-revision review reproduced five additional
control separators accepted by the wire schema but rejected by the value owner;
the schema and exact-location negative tests now cover all ten one-line separators.
The earlier frozen run does not verify this subsequent correction. The three early
wire-test failures used the wrong closure keyword; corrected tests require the
actual unevaluatedProperties rejection at the intended instance location.

Reference-module integration requires selected-root package loading for M1's
identity check and two exact platform-guard reference-path approvals. Broader Core
runtime paths stay denied. M2's immutable evidence pair is preserved verbatim.

The first frozen full run passed 769 unit tests and 34 of 36 repository checks;
package acceptance still loaded the facade as a standalone file, and Phase 10's
exact added-path policy rejected the new reference/test sources. Both boundaries
now recognize the adopted reference package through scoped source loading and
exact reviewed Python roles. Loader regressions also reproduce and reject stale
and source-less bytecode without changing mathematical assertions. The subsequent
frozen revision `229cb78c1cbc1fea361f5592505e78d649187c30` passed all 36 local
repository checks and 791 unit tests from a clean unfiltered offline checkout.
It was pushed without force and independently read back from GitHub main;
Main CI run `37228903025` passed against that exact revision. Its README checkpoint
is published. These results do not replace M2's immutable evidence or accept M3.

## 8i. M3 N1 semantic normalization

The normalization contract and exact target policy were independently reviewed
and adopted before code as YWE-REQ-0040 / ADR-0030. Prior 39 requirements and
46 governance records were preserved. The policy is a downstream YWE decision:
keep a recognized original unchanged, otherwise select the lowest full signature
from the complete reachable recognized set. Canonical ASH sources remain unchanged.

StateModel's new pure planning and explicit validation require no normalization
capture. Actual application requires its separate explicit collaborator and
revalidates the original seven semantic fields, ordered source rules, detection
envelope, full profile and complete target/proof before use. A foreign or forged
origin retains the submitted diagnosis and current bindings with no inherited
confirmation or capture call. Scope creation and interface checks precede XOR;
normalization output waits for computation and complete actual-result diagnostics
to receive matching confirmations. Each failure retains actual observations,
confirmed prefixes and complete attempted records.

Working-tree integration matched every one of the independently reviewed 2,048
profile/state cases. The final combined suite passed 115 tests in 33.877 seconds:
42 normalization, 68 assessment, four identity and one platform test. A separate
29-test loader and exact-reference-boundary run passed in 1.214 seconds.
The wire tests cover thirty actual producer packets and twenty independently
authored format packets; both new schemas independently passed offline review.
Constructor and scoped-capture review reproduced invalid post-validation after
a no-target refusal; both owners now reject it while retaining legitimate
before/after-computation failures. Named binding-mismatch witnesses must also
retain an actual difference in the named binding.

Frozen revision `5328f018f341b80ad58cdb82f64708992ee2d6ae` passed all 36 applicable
repository checks, with 833 unit tests in 705.007 seconds. The completed report
records no selections, offline file-only Git protocols, an empty dirty state
before and after execution, and no blocking or advisory check failures. The exact
revision was pushed without force and read back through Git and GitHub's API;
the remote README bytes matched the frozen implementation. Main CI run
`37233715205` was dispatched for that exact revision and was still running at this
record's preparation. Its eventual result must be observed before claiming success.
No operational session, recovery success, full Diagnostics or M3 gate is claimed.

## 8j. N2 recovery and reference Diagnostics contract adoption

The complete exact N2 interface and wire package was independently reviewed
outside the repository before adoption. It now becomes active under
YWE-REQ-0041, YWE-REQ-0042 and ADR-0031. The preceding 40 requirements and 47
governance records retain their meanings and identities. The adopted documents
include their exact machine inventories and current fifteen primary source pins
plus the complete 32-file canonical aggregate; implementation has not yet passed
its new independent tests or wire/export acceptance checks.

Recovery retains the verified source class, current full model bindings, supplied
correction proof or certified ordered registry snapshot, every actual computation,
fresh contextual postassessment and separately observed capture/completion.
Unknown evidence stops the operation; pending safety directives and the original
primary failure survive secondary completion failure. Canonical entry escalation
and separately named after-failure routes are explicit downstream policy decisions.

Reference Diagnostics owns a bounded safe graph, actual typed clock observations,
protected supporting/event commits before confirmation, explicit loss/health,
and consistent detailed JSON/Markdown export. Independent external arithmetic
checks verified the conservative byte/alias reservations. Actual Windows probes
demonstrated direct protected D-drive child storage and preserved the failed
C-drive ancestry and same-user rename controls. These are design/capability
evidence, not implemented collector or native product qualification.

N1 Main CI run 37233715205 and documentation checkpoint run 37234268088 are now
observed successful at their exact revisions. The earlier 8i preparation-time
running observation remains historical. N2 implementation starts only after this
contract adoption is committed. Actual session admission/state publication,
containment, safe halt and broader canonical producer coverage remain N3/later
work; unchanged M3 acceptance and M10 platform boundaries remain in force.

The N2 adoption revision `54c9a67beadf3c93dc3d36ea81133d60ede6de2b`
published with exact Git/GitHub and README-byte readback. Its Main CI run
`37238793118` passed 35 of 36 checks; package acceptance's existing
`test_rejects_8_plus_1_language` matched numeric budget formulas. The formulas
are now represented by exactly equivalent sum lists, independently recomputing
696 events and 5403 aliases. No guard, test, limit or contract field was weakened.
Replacement complete CI remains pending; this failure is preserved as evidence.
The separately reviewed registry route-timing clarification is committed at
`02b70bc7450e90503bb4825819dde8e8f4f9cc3d`; its clean selected roadmap/M0/M1
checks passed and its publication readback matched. Direct rejection precedes
admission; rejection after a real failed action retains that prior work and stops
before fallback effects.

The reviewed capture-retention amendment adds the exact physical purge port and
four API-only closed storage values before implementation. Independent review
identified the partial-deletion graph hazard and required two exclusive phases:
events first, actual outcomes applied, then support reachability recomputed from
retained/unknown roots before support deletion. Existing exported fields and limits
remain unchanged. The 1664 support-key maximum derives from all ten adopted safe
node domains. Recovery currently passes 43 integration and 23 value/registry tests
locally, including 131,072 actual two-codeword proof validations; full published
N2 acceptance remains pending while Diagnostics checks continue.

## 9. Historical publication continuity

An initial temporary correction workflow at commit `79322d90b7c8e22284064ec44174a866c79c0772`
failed before modifying roadmap files because its compressed transport payload was
corrupted. The replacement used an inline reviewed patch, removed the temporary workflow,
ran the roadmap and consolidated repository checks, and published this planning-13 record.
The containing commit is the authoritative save point.

## 10. Checkpoint

**Current step:** Implement the adopted N2 recovery and reference Diagnostics
contracts, including actual fallback execution, safe graph persistence and paired
exports. M2 remains accepted; M3 remains in progress.

**Completed:** M2 immutable foundation acceptance; verified first M3 StateModel
slice; N1 contract, normalization implementation, clean 36-check/833-test execution,
GitHub publication and exact successful CI; N2 contract, safety policy and exact
interface adoption with independent source/arithmetic review.

**Next action:** Execute independent N2 producer, failure, wire and export controls,
then freeze and verify the complete repository before publishing implementation
results. Continue through session/mode/terminal guards, remaining Diagnostics and
generation before evaluating unchanged M3 exit criteria.

**Needed from owner:** Nothing for continued authorized roadmap development.

**Saved at:** This planning-27 checkpoint follows published N1 implementation
`5328f018f341b80ad58cdb82f64708992ee2d6ae` and publication checkpoint
`4c01af5b01b4690da5cd2a97d5e6025e97a48e1c`. The containing committed revision
adopts N2 before its dependent code. Immutable milestone evidence and earlier
checkpoint identities remain preserved.
