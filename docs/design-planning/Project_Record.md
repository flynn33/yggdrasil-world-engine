# Yggdrasil World Engine — Project Record

**Record ID:** YWE-RECOVERY-20260918
**Revision:** repository-planning-1
**Updated:** September 19, 2026.
**Supersedes:** prepared-2 as the current continuity view, under the [owner-approved storage decision](Storage_Decision.md). No accepted engineering decision is superseded.

## 1. Identity and working brief

| Concern | Current state |
|---|---|
| Product / owner | Yggdrasil World Engine / Flynn |
| Goal | Platform-agnostic, strictly object-oriented, modular engine specification |
| Repository | `flynn33/yggdrasil-world-engine` |
| Inspected integration baseline | `main` at `2db1230f638cd065d791c05f1adb7b4b51505c57` |
| Repository version | `v2.0.23`, unchanged |
| Milestone | Existing M0 and M1 acceptance retained; M2 in progress |
| Working branch | `planning/m2-design-records` |
| Current activity | Preserve design and planning artifacts in their repository home; candidate compatibility review follows |
| Candidate status | Tested proposal, not adopted normative semantics or an implemented engine feature |
| Current record | `docs/design-planning/Project_Record.md`; revision identified by Git history |
| Current handoff | `docs/design-planning/Session_Handoff.md` |
| Owner-local checkout | Uninspected; unpublished work is unknown and must not be overwritten |
| Platform / hardware work | Deferred through M10; no native candidate or hardware phase in this task |

## 2. Authority and method

The machine-readable roadmap, focused normative contracts, requirement/governance registers, and accepted M0/M1 evidence remain engineering authorities. Historical chats and candidate experiments do not reopen milestones or approve designs.

Raven Forge Development remains the standing method. The existing project's adopted immutable revision has not been recovered. The previously inspected reference is version 0.6.2 at `ed0028a46bac9c5b92876a6ad6589ca421fd9499`; it remains an inspection reference, not an adopted replacement. The earlier full README, Project Start, mandatory core, System Catalog, and record/handoff reading is inherited and identified in the candidate source register. No new method revision is selected by this publication.

The owner has now authorized repository storage and a scoped push for design and planning. This resolves the earlier unknown saving location for the current working record. It does not authorize merger, release, platform work, an upstream edit, or adoption of the candidate wire choices.

## 3. Purpose, scope, and constraints

The specification is the product. ASH Model Cosmology supplies foundational reference material; APS supplies integrity semantics; Aeostara supplies operation-governance reference design. They are not package, build, module, runtime, or whole-repository dependencies of YWE.

Objects own their invariants; codecs express boundary representations. WRW and Ravenfall remain reference profiles rather than mandatory neutral-Core game truth. Existing approved work is preserved.

The current candidate concerns `AshState`, `CanonicalCodeword`, immutable construction, exact-set membership, pure XOR, and field-specific JSON representations. It does not implement or decide operational admissibility, normalization-as-repair, recovery, fallback, containment, safe halt, whole packet schemas, planner/emitter realization, framework decoupling, or game features.

## 4. Completed work and evidence

The earlier readiness review found that the descriptive parent packet did not provide effective standard instance validation, that eight standalone record descriptions were invalid schemas, and that direct promotion of Boolean metadata changed its meaning. These are preserved historical findings, not a full-engine failure claim.

The two-value candidate and its experimental schema, fixtures, and verification model are retained under `m2/ash-values/`. Its source-established finite constraints are distinct from proposed wire rules in `candidate-decisions.json`.

The preserved experiment covers 512 state values, all 512 possible codeword candidates with exactly 16 admitted, 8,192 state/codeword transformations, 56 bound valid/reject fixtures, raw JSON and precision cases, ownership/order, offline references, and ten detected deliberate faults. The experiment was rerun during publication preparation and reproduced the prior result section. The verification report records the scope and actual evidence.

Both supplied archive manifests were checked before extraction: 28 entries in the value-contract bundle and 21 entries in the readiness bundle matched. No nested archive, duplicate historical record, or upstream repository is imported as product implementation.

## 5. Decisions and open matters

| Item | State |
|---|---|
| Store planning in this repository directory | Approved by the owner's September 19 instruction; see Storage_Decision.md |
| Preserve M0/M1 and continue M2 | Existing repository state; no new acceptance judgment |
| Prior suggested M1 expansion | Historical proposal, not an adopted roadmap reversal |
| Represented state versus codeword membership | Existing finite-source distinction retained |
| `membership: true`, closed records, exact numeric parsing, writer ordering, and field-specific encodings | Tested proposals; consumer compatibility and incorporation remain open |
| Normalization/recovery disagreement | Unresolved; excluded from this value-boundary experiment |
| Prior adopted method pin | Unrecovered; no silent substitute |
| Reviewed linked realization contracts and independent acceptance | Not recovered or newly issued; dependent implementation prerequisites remain |
| Full repository validation | Not performed in this publication environment; remote reads are not a local checkout |
| Classification and scope metadata for this new directory | Must be reconciled under existing policy before merge; draft publication is not policy acceptance |

The inherited schema-quality backlog remains 132 category occurrences across 119 paths; no debt reduction is claimed. The earlier reported 18 requirements, 27 governance records, 119 glossary terms, ten authority nodes, and 32-file pinned source corpus remain inherited acceptance observations, not fresh measurements.

## 6. Permissions and integrity

Authorized: inspect relevant sources; organize these existing design/planning artifacts; maintain this current record and handoff; create and push the scoped review branch; prepare a draft review change; run the existing verification-only experiment.

Not exercised or implied: merge, force push, branch deletion, tag, release, changes to permissions or paid workflows, native builds, changes to accepted semantics/source pins, dependency additions, or edits to upstream systems.

The connected repository access is the owner account. Publication must use the existing baseline tree and add only the dedicated planning directory. Remote file/tree identities are checked after writing. A GitHub save does not establish that the owner's local checkout is synchronized.

## 7. Next eligible action

Review the candidate against actual packet consumers and fixtures, concentrating on the Boolean membership assertion, closedness, arrays versus signatures, exact numeric parsing, and type-specific schema binding. Produce an evidence-backed accept/change recommendation without a source upgrade.

Before merge, reconcile classification/scope/path snapshots and execute the full repository checks from a real checkout; see Integration_Review.md. Before normative incorporation, resolve any governing-method/realization prerequisites that affect that work. Do not reopen unrelated accepted work or ask the owner to reconstruct recorded history.

## 8. Persistence

This file and the current handoff are the repository-backed continuity records selected by the owner. The published revision is the containing commit; successful persistence is confirmed by remote read-back in the session closeout, not by a self-referential future hash in this file. The draft branch is not merged into main. Older downloadable prepared records are superseded as working views; their historical evidence remains provenance.
