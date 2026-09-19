# Yggdrasil World Engine — Project Record

**Record ID:** YWE-RECOVERY-20260918  
**Revision:** planning-7  
**Date:** September 19, 2026  
**Authoritative planning branch:** `design-planning/m2-foundations`  
**Location:** `docs/design-planning/Project_Record.md`  
**Persistence anchor:** Predecessor planning-6 was read in full at `91cb28ea328ff8a480e082c035a376cbc7f42833`. This revision's containing commit supplies its storage identity. No merge or branch deletion is claimed by this record update.

This is the single current planning record. It supersedes planning-6's next-work priority, not accepted engine contracts or original evidence. The complete predecessor is preserved in Git history. Current handoff: [continuation and branch cleanup](handoffs/2026-09-19-consumer-compatibility.md).

## 1. Identity and current state

| Concern | Current state |
|---|---|
| Product / owner | Yggdrasil World Engine / Flynn; repository owner `flynn33` |
| Product purpose | Platform-neutral, strictly object-oriented and modular engine specification |
| Repository | `flynn33/yggdrasil-world-engine` |
| Accepted product baseline | v2.0.23; main observed at `2db1230f638cd065d791c05f1adb7b4b51505c57` |
| Roadmap | Existing M0/M1 acceptance preserved; M2 active; no new gate accepted |
| Initial planning publication | `56abad1d6db1829feb074c6459466089930bf2a6` |
| Starting planning branch head | `91cb28ea328ff8a480e082c035a376cbc7f42833` |
| Current activity | Owner-requested branch cleanup takes priority over further M2 design |
| Main integration | Authorized by the current cleanup request; integration prerequisites remain unmet; not performed |
| Owner checkout / unpublished work | Not inspected; unknown |
| Native products / hardware | Deferred through M10; not applicable to this cleanup |
| Assurance profile | No new profile selected |

The machine-readable roadmap remains the milestone/status authority. Focused accepted contracts remain implementation-detail authority. This record does not supersede either.

### Development method and continuity

Raven Forge Development remains the standing method. The previously adopted project revision is unrecovered. Inspected version 0.6.2 at `ed0028a46bac9c5b92876a6ad6589ca421fd9499` remains an inspection reference only, not an adopted upgrade. Mandatory-core reading and its inherited coverage remain in the source registers; no new full-repository reading is claimed.

The owner approved this repository directory and owner-account publishing, with existing admin bypass permitted if needed. The current instruction additionally authorizes merging extra branches into main and deleting branches whose work is already merged. That instruction establishes the cleanup priority; it does not establish that unperformed checks passed. Earlier directions to file all records in an assumed external workspace were superseded by the [location decision](decisions/2026-09-19-planning-location.md). Issued coding-agent packages remain external.

## 2. Purpose, scope, and exclusions

The specification is the product. ASH Model Cosmology, APS, and Aeostara supply reference semantics/design, not runtime repositories to import. YWE owns its object contracts. WRW and Ravenfall remain reference profiles, not universal Core truth.

This step inspects the extra branches and preserves the actual cleanup state. It does not approve the value candidate, replace the active packet artifact, change source pins, introduce dependencies, add gameplay, resolve disputed normalization, or start native implementation. No new branch is needed for cleanup. Original archives and source snapshots remain outside the committed planning directory.

## 3. Users and workflows

Maintainers and future implementers start at the directory README and this record, then consult controlling contracts and exact candidate/source/evidence files. Candidate value construction validates representation and actual membership where appropriate, creates immutable values, and performs pure transformations without world-mutation authority.

The completed compatibility review demonstrates an explicit checked-input mapping into the existing helper, not a drop-in API replacement. Signature fields, ordered sequences and compatibility aliases are preserved in the tested outputs. Branch publication, consumer compatibility, main integration and specification acceptance remain distinct conclusions.

## 4. Requirements and acceptance

Existing requirement and governance registers control. No new normative requirement ID, candidate approval, debt closure, protocol version or milestone acceptance was issued.

Inherited M1 evidence reports 18 requirements, 27 governance records, 119 glossary terms, ten authority nodes, and a pinned 32-file corpus. Inherited M2 debt is 132 findings over 119 paths: 31 missing identifiers, 13 annotation-only schemas, 49 descriptive schema-named documents, and 39 unbound examples. These remain historical observations, not newly measured counts.

The [readiness review](m2/readiness/M2_Readiness_Review.md) preserves the demonstrated permissive schema behavior and direct-conversion hazards. Publishing or testing a candidate does not close that debt. Merging planning records must not silently turn candidates into accepted engine requirements.

## 5. Architecture, sources, and unresolved decisions

The [two-value contract](m2/ash-values/Ash_Value_Contract.candidate.md) and [candidate decisions](m2/ash-values/candidate-decisions.json) remain proposed. State representation is distinct from codeword membership, operational admission and mutation authority. Values own coordinates; exact membership is not trusted from metadata.

The parent packet has nine local descriptions and twenty-one delegated records. Only two values have this experimental contract. Other domains are not redesigned here.

The [value source register](m2/ash-values/source-register.json), [readiness source register](m2/readiness/source-register.json) and [compatibility review](m2/consumer-compatibility/README.md) preserve pins, source roles, actual reading, execution limits and exclusions. The preceding review read the complete existing helper, exports, four-test file, and broader engine interface. It executed hash-verified selected files, not a full checkout. Further governance/package-check consumers were located through search but not fully reviewed.

Preserved findings: the baseline helper coerces fractional, Boolean and string coordinates, and accepts padded/Unicode-digit signatures; seven input acceptance differences were reproduced. Direct out-of-contract dataclass construction can retain a mutable list or accept a short tuple. Normal helper-created tuple values are not claimed to be mutable. The candidate also changes the signature property into a method and requires exact consumer-selected schema targets.

Proposed direction after cleanup: preserve existing signature-bearing packet fields and aliases; specify a separate checked input boundary and compatibility facade. Do not globally replace `normalize_bits`, add membership members to string sequences, close whole envelopes, or claim standalone writer compatibility from helper tests.

Still unresolved: prior method binding; complete linked System Realization Contracts and independent acceptance/preflight; normalization/classification source reconciliation; Forsetti interface scope; field-specific reference/alias rules; complete standalone-record consumer inventory; approval/versioning for membership, closure, raw numeric parsing, writer output and schema-target binding. These obligations remain scoped; no broad project reset is needed.

## 6. Experience and resources

The README remains the front door; this record is the current working state; the handoff points back to it. No UI, branding, production asset or device requirement changed. The owner need not download or sort archives. Further design expansion is deferred until the requested branch cleanup is addressed.

## 7. Verification and limitations

Original candidate evidence is unchanged: 512 represented states, sixteen accepted codewords out of 512 candidates, 8,192 transformations, 56 named fixtures, raw JSON/precision and ownership/order checks, ten detected schema mutations, offline references, and three repeated result sections. These are bounded experimental findings, not independent or whole-engine acceptance.

During the earlier publication, a fresh run passed all ten candidate groups and reproduced result hash `630cade04dadfc8ae236e34ffdcc1238703695b856b4d336fa0043d68d4ac113`. [Publication checks](publication/Publication_Checks.json) preserve that evidence. All 41 M2 payload files matched the prepared subtree and all 49 initial publication files matched the local planning tree. Relative links and attribution scanning were checked then.

The [compatibility results](m2/consumer-compatibility/compatibility-results.json) add six executed groups: 512 represented-state comparisons; identical sixteen-word enumeration; 8,192 matching transformations; 2,048 matching snapshots plus 2,048 matching plans; fifteen boundary probes with seven acceptance differences; construction/ownership/API and exact-schema-target checks; and four unchanged identity tests. These counts overlap within the six groups and are not a combined test-count metric.

Two compatibility runs produced identical result sections with SHA-256 `43e7f34ad8e185d82eaac5ae5dc887960fda50024b43244c6714aff680e0b8c2`. [Reproduction checks](m2/consumer-compatibility/reproduction-checks.json) record source-preservation verification, refusal to execute altered source and refusal to overwrite a report. Reports were serialized compactly for publication without changing their fields.

The verdict remains `not_drop_in_compatible`. Successful review execution means the differences were reproduced, not that the candidate is adopted. Packet equality uses a review-only comparison encoding and the same existing helper; it is not an independent semantics oracle, global canonical-JSON decision or native-output proof.

No new candidate run, full repository suite, owner-checkout inspection, complete consumer inventory, native build, realization preflight/delivery, independent approval or physical-device qualification is claimed in this cleanup step.

## 8. Execution and persistence

The [publication receipt](publication/GitHub_Publication.json) records the first successful connected write and read-back. The initial commit added 49 files under `docs/design-planning/`, with no unrelated changes or deletions; its planning subtree was `54e35e319184101d7a425b39cb5baaa788bc6479`. Subsequent record and compatibility commits remain in history. Previous commits identify Jim Daley / `flynn33`; they are unsigned. Content verification is not a cryptographic-signature claim.

Main-integration obligations in [Repository Integration Requirements](publication/Repository_Integration_Requirements.md) remain pending: complete checkout inspection, classification/scope path snapshots, nonnormative experimental treatment, production discovery, navigation and full pre/post checks. The older branch's `Integration_Review.md` independently records the same unmet conditions. No validator or classification rule was changed to avoid them.

### Branch cleanup observations — September 19, 2026

The GitHub branch collection returned exactly three branches at inspection:

| Branch | Inspected tip | Comparison with inspected main |
|---|---|---|
| `main` | `2db1230f638cd065d791c05f1adb7b4b51505c57` | Retain as integration branch |
| `design-planning/m2-foundations` | `91cb28ea328ff8a480e082c035a376cbc7f42833` | Three commits ahead, zero behind; 55 added planning paths |
| `planning/m2-design-records` | `c4d505b71e4db829fdb1b84f3c368bf164ea8c31` | Two commits ahead, zero behind; 24 added planning paths |

The direct branch comparison reports `diverged`, with three commits on the newer lineage and two on the older lineage, sharing main as their merge base. Neither branch was already merged into main, and neither is a history ancestor of the other. The compare service returns merge-base-relative file statistics; those statistics are not a complete two-tip content-equivalence proof.

The older planning subtree `8d9c5ad78d34059fe5303c5c58bdf765cb11cf01` was inventoried completely. It includes older continuation/storage/publication records and a verification-summary file not present at the same paths in the newer lineage. Its verification-code subtree `4de2652d6bf1779cf4d2964098d35b0e32cee687` matches the newer published experiment, but that does not prove every other file is redundant. The newer branch remains the current-record authority until an explicitly reconciled main integration succeeds.

The available connection confirms owner-level repository permissions, but exposes no branch/ref deletion action. Tool discovery and relevant plugin discovery did not produce another applicable deletion route. The container has Git but no GitHub CLI or configured GH_TOKEN/GITHUB_TOKEN, and current DNS resolution for GitHub endpoints failed. The alternative archive-download routes did not obtain a complete checkout. An available transport archive of planning files is not a complete repository checkout.

No branch was created, merged, deleted, force-updated or renamed during this inspection. Main, the older branch, protections, workflows, source pins, versions and accepted evidence are unchanged. Only this record and its existing handoff are updated to preserve the cleanup priority and observed blockers; those documentation commits do not complete cleanup.

## 9. Decisions and permissions

| Decision | Status |
|---|---|
| Agnosticism, OO modularity, reference-only systems, existing acceptance | Existing owner/project direction retained |
| Dedicated repository planning directory | Owner approved September 19, 2026 |
| Owner-account publishing; existing admin bypass if required; no attribution | Explicit permission retained; no force or protection changes |
| Merge extra branches into main; delete branches already merged | Current owner instruction; execution pending the recorded integration checks and required tools |
| Two-value wire/construction choices | Tested proposals; approval fields unchanged |
| Compatibility disposition | Preserve tested outputs; explicit boundary migration proposed, not approved |
| Method/source upgrade | Not performed; prior method binding remains unresolved |
| Release or platform implementation | Not authorized by branch cleanup |
| External-record filing assumption | Superseded; only issued instruction packages must remain external |

## 10. Current step and next action

**Current step:** Branch cleanup requested; branch history audit completed; merge/deletion not completed.

**Completed:** Retrieved the full current record and handoff, enumerated all remote branches, compared each extra branch against main and the branches against each other, inventoried the older planning subtree, confirmed the integration blockers and tool limits, and preserved all work.

**Next action:** In a complete authenticated checkout, reconcile both existing planning lineages without creating another remote branch; keep one current Project Record; preserve unique work and both histories; synchronize classification/scope and experimental discovery; run required pre/post repository checks; integrate into main; verify the inspected branch tips are ancestors of the resulting main (or document equivalent preservation for a reviewed squash); only then delete the extra branch refs and verify the final branch list. Do not blanket-resolve all conflicts with one side or delete a branch merely because its name is old.

**Needed from you:** A Git-enabled authenticated development session capable of complete checkout validation and branch deletion. No additional approval, download sorting or reconstructed project history is needed.

**Saved at:** `flynn33/yggdrasil-world-engine`, branch `design-planning/m2-foundations`, `docs/design-planning/`. The containing commit identifies this checkpoint. A saved cleanup checkpoint is not a completed merge or deletion.
