# Yggdrasil World Engine — Project Record

**Record ID:** YWE-RECOVERY-20260918  
**Revision:** planning-11  
**Date:** September 19, 2026  
**Authoritative branch:** `main`  
**Location:** `docs/design-planning/Project_Record.md`  
**Verified predecessor:** `7aa5c1b18caf37bb01ca3bdfb0d73b59f8261009`, planning-10.

This is the single current planning record. It supersedes planning-10's next-work status and its overly broad no-new-branches interpretation, not accepted engine requirements or historical evidence. The complete predecessor remains in Git history. The current [handoff](handoffs/2026-09-19-consumer-compatibility.md) points here. This revision's containing commit identifies its storage; remote publication is verified separately rather than predicted.

## 1. Current working brief

| Concern | Current state |
|---|---|
| Product / owner | Yggdrasil World Engine / Flynn, repository owner `flynn33` |
| Product purpose | Platform-neutral, strictly object-oriented and modular engine specification |
| Repository | `flynn33/yggdrasil-world-engine` |
| Accepted product version | v2.0.23; unchanged |
| Roadmap | M0 and M1 accepted; M2 in progress; no new gate accepted |
| Current activity | Planning-directory integration: the reviewed-report discovery subtask is implemented and tested |
| Remaining integration | Classification/scope snapshots, remaining discovery coverage, and complete repository validation are not finished |
| Source used for this change | Hash-verified selected files from the predecessor, not a complete current checkout |
| Owner-local state | Uninspected; no local synchronization claim |
| Runtime/platform work | Deferred until M10 acceptance; not part of this change |
| Assurance profile | No new profile selected |

The machine-readable roadmap remains milestone/status authority. Focused accepted contracts and requirement/governance registers remain engineering authority. Storage, maintenance tests and a successful push do not approve an experimental engine design.

## 2. Approved direction and operating boundaries

The specification is the product. ASH Model Cosmology supplies the foundational cosmological reference; APS and Aeostara supply reference semantics and design. Their repositories are not package, build or runtime dependencies. YWE owns its object contracts. Preserve strict object orientation, explicit invariant ownership, modularity and platform neutrality. WRW and Ravenfall remain reference profiles, not universal Core truth.

The owner approved `docs/design-planning/` as the maintained home for product design, planning and continuity. Only issued coding-agent instruction packages remain in the external instructions workspace. Do not ask the owner to sort transport archives or reconstruct retrievable history.

**Branch lifecycle clarification, September 19, 2026:** The owner prefers working branches. The concern is abandoned finished branches, not branch creation itself. Use bounded working branches when the available route can complete their lifecycle. Retain needed work, merge completed work, and remove redundant references after verifying preservation. Unfinished work must have an explicit current status rather than being called finished. This clarification replaces the earlier general prohibition on new planning branches; it does not call for restoring the deleted branches.

Owner-account publishing and existing admin bypass, when necessary, remain authorized. No force push, protection change, workflow restoration, new runner spending, source upgrade, candidate approval or release is implied. The available connection still has no branch-reference deletion action. For this bounded repair, a reviewed commit object can be published by a normal main fast-forward without creating a remote reference that cannot be cleaned up.

## 3. Development method and source authority

Raven Forge Development remains the standing method. The previously adopted immutable revision remains unrecovered. Version 0.6.2 at `ed0028a46bac9c5b92876a6ad6589ca421fd9499` remains the recorded inspection reference, not a silently adopted upgrade. Preserve inherited source-reading limits and pins. Current maintenance consulted the applicable interpretation, enforcement, repository-catalog, testing and realization-contract guidance; it did not complete or approve the outstanding linked system-realization contracts.

This repair concerns the existing repository validation tool, not an APS/Aeostara implementation or semantic adoption. It neither resolves nor bypasses those separately scoped prerequisites. The [value source register](m2/ash-values/source-register.json), [readiness source register](m2/readiness/source-register.json) and [compatibility review](m2/consumer-compatibility/README.md) remain the detailed source/evidence records.

## 4. Preserved work and completed cleanup

Both former planning histories were retained through merge `13ee11704691b1c562e8e0099ca2b2e4533cb39e`; main then advanced to `90f3c00f8b286aa064114575e607f7ce60e13df2`. The owner deleted the redundant branch names. Post-deletion checks established that former tips `13ee11704691b1c562e8e0099ca2b2e4533cb39e` and `c4d505b71e4db829fdb1b84f3c368bf164ea8c31` are ancestors of main. This session's initial branch collection again contained only main at the verified predecessor.

No known committed work needs reconstruction and the completed cleanup is not reopened. The [per-file reconciliation](publication/Branch_Reconciliation.md), older publication manifests, unique earlier verification summary, original detailed evidence, and full preceding histories remain preserved. Never confuse retained history with a second current Project Record.

## 5. Substantive M2 design state

The [AshState / CanonicalCodeword candidate](m2/ash-values/Ash_Value_Contract.candidate.md) and its [decisions](m2/ash-values/candidate-decisions.json) remain unapproved proposals. Values own immutable coordinates. State representation, codeword membership, operational admission and mutation permission are distinct. The parent packet still contains nine local descriptions and twenty-one delegated records; this work does not redesign those other domains.

Inherited candidate evidence covers 512 represented states, exactly sixteen accepted codewords, 8,192 transformations, 56 named fixtures, raw parsing/precision, ownership/order, offline references and ten detected schema faults. Its preserved result-section hash is `630cade04dadfc8ae236e34ffdcc1238703695b856b4d336fa0043d68d4ac113`.

Inherited compatibility evidence covers 8,192 matching transformations, 2,048 matching snapshots, 2,048 matching plans, fifteen input probes with seven acceptance differences, and four unchanged identity tests. Its repeated result hash is `43e7f34ad8e185d82eaac5ae5dc887960fda50024b43244c6714aff680e0b8c2`; the verdict remains `not_drop_in_compatible`. These experiments were not rerun for this repair and do not independently prove all helper semantics.

The existing helper coerces fractional, Boolean and string coordinates and accepts padded/Unicode signatures. Direct out-of-contract construction can retain mutable storage or a short tuple; normal factory tuples are not claimed mutable. The next design remains an explicitly typed input boundary and compatibility facade preserving signature fields, ordered sequences and aliases. Do not replace global normalization, add membership members to string sequences, close entire envelopes or infer writer compatibility from the helper comparison.

## 6. New completed discovery subtask

Three preserved readiness diagnostic reports were incorrectly counted as schema-named JSON documents lacking declarations. The existing checker used the filename substring `schema`, even though these files record test observations rather than define schemas.

`ReviewedDiagnosticReports` in `scripts/check_machine_readable_artifacts.py` now recognizes only those three exact paths and their complete reviewed JSON-value fingerprints. Recognition is used solely by the schema-name heuristic. Changed metadata or nested results, copied reports at another path, label-only imitations and real schemas are not recognized. The registry is read-only. Its comparison encoding is local evidence fingerprinting, not a new engine serialization policy.

JSON parsing, YAML duplicate-key rejection, declared-schema meta-validation, reference checking, identifier uniqueness and all other quality-debt categories remain active. The original schema-quality baseline is unchanged; no known M2 debt was removed or increased. Original report bytes, candidate models, schemas, fixtures, source pins, versions, roadmap state and M0/M1 acceptance evidence are unchanged.

Sixteen regression tests were added to the existing `tests/test_validation_foundation.py`. No repository path was added, removed or renamed. Existing test classes were preserved; the main checker implementation and other existing functions were preserved apart from the specific debt predicate and added recognition class/imports. Details and reproduction are in [Repository Integration Requirements](publication/Repository_Integration_Requirements.md).

## 7. New verification and limits

The original checker and test file were reconstructed and matched their complete Git blob hashes. All three report files recovered from the transport archive matched their current remote blob hashes before use. The archive was not substituted for a complete checkout.

The original four machine-artifact tests passed. Against a disposable fixture containing only the three reviewed reports and an empty synthetic debt baseline, the original CLI exited 1 and reported all three false positives. The revised CLI exited 0. That fixture's zero debt is not the repository's debt count.

The four original tests plus sixteen new tests passed twice: 20 tests, zero failures/errors/skips, with hash seeds 17 and 71. Exact AST class extraction isolated these classes from unavailable unrelated imports; this was not execution of the entire test module or repository catalog. The tests invoked the actual checker CLI against disposable valid/invalid fixtures, including invalid schemas, unresolved references, duplicate identifiers, changed/copied reports, malformed JSON and duplicate YAML keys.

A final run on the uploaded test-file bytes also passed all 20 tests; whitespace-only presentation differences in existing tests were checked by complete syntax-tree equality.

Three intentionally broken checker copies were detected: bypassed fingerprints produced seven test failures, removed report recognition produced three, and disabled meta-schema validation produced one. These are mutation-test observations, not failures of the delivered checker. A combined mutation invocation timed out before its final report; the last mutation was rerun independently and completed. All original report bytes remained unchanged.

No complete current checkout, full repository suite, owner-local inspection, native build, new candidate acceptance, linked-realization preflight/delivery, independent review or physical-device qualification is claimed. Earlier DNS/archive acquisition failures remain recorded; no workflow or permission changes were used to manufacture an execution route.

## 8. Remaining obligations

The administrative main merge preceded complete technical integration. The primary classification/scope manifests and exact path snapshots remain unreconciled with the planning directory. This repair fixes one schema-discovery false-positive set; it does not finish classification, make experiments normative, or establish a passing repository baseline.

The registered M2 inventory still reports 132 findings across 119 paths: 31 missing identifiers, 13 annotation-only declarations, 49 schema-named descriptive documents and 39 unbound examples. These are inherited registered counts, not a newly executed whole-repository measurement. The [readiness review](m2/readiness/M2_Readiness_Review.md) still identifies the real packet-schema deficiencies.

Still open: prior playbook binding; reviewed linked System Realization Contracts; normalization/classification source reconciliation; Forsetti interface scope; field-specific references/aliases; complete consumer inventory; and approval/versioning of membership, closedness, numeric parsing, writer output and exact schema-target binding. Hold only dependent work. Do not restart accepted milestones.

## 9. Decisions and permissions

| Decision | State |
|---|---|
| Platform-neutral OO engine, reference-only systems, prior acceptance | Preserved |
| Planning storage and one current record | Existing approved directory on main |
| Branches | Preferred for bounded work; completion includes merge/preservation and cleanup, not permanent accumulation |
| Earlier branch cleanup | Completed by owner; verified; not reopened |
| Reviewed-report recognition | Scoped maintenance repair with focused tests; not a broad discovery exemption |
| Candidate semantics or method/source upgrade | Not approved or changed |
| Release/platform implementation | Not part of this task |
| Complete repository acceptance | Not established; outstanding checks remain visible |

## 10. Checkpoint

**Current step:** Reviewed diagnostic-report discovery defect corrected and locally verified; broader M2 integration remains open.

**Completed:** Exact source/report recovery, before/after CLI evidence, sixteen new regression tests, two passing 20-test runs, three detected intentional faults, and the owner's clarified branch lifecycle recorded.

**Next action:** Reconcile the current planning-directory classification/scope and exact repository path inventory against a verified full tree, then run the catalog checks and distinguish inherited failures from regressions. After integration, continue the already identified typed input-boundary specification.

**Needed from you:** Nothing to reconstruct, download, sort or reapprove for this bounded maintenance work.

**Saved at:** This record and the existing handoff retain their paths on main. The verified predecessor is above; the containing commit and remote read-back establish this revision's actual publication. No full-suite pass is implied by persistence.
