# Yggdrasil World Engine — Project Record

**Record ID:** YWE-RECOVERY-20260918  
**Revision:** planning-8  
**Date:** September 19, 2026  
**Authoritative planning branch:** `design-planning/m2-foundations`  
**Location:** `docs/design-planning/Project_Record.md`  
**Persistence identity:** The containing two-parent commit records the reconciliation of `9fd7625241fee529452570cca6f1742cb6976856` and `c4d505b71e4db829fdb1b84f3c368bf164ea8c31`. Remote ref advancement and ancestry are checked separately at closeout; no future commit hash is predicted here.

This is the single current planning record. It supersedes planning-7's statement that the two planning histories are separate, not accepted engine contracts or experimental evidence. Both complete predecessor histories remain reachable. Current handoff: [continuation and cleanup](handoffs/2026-09-19-consumer-compatibility.md).

## 1. Identity and current working brief

| Concern | Current state |
|---|---|
| Product / owner | Yggdrasil World Engine / Flynn; repository owner `flynn33` |
| Product purpose | Platform-neutral, strictly object-oriented and modular engine specification |
| Repository | `flynn33/yggdrasil-world-engine` |
| Accepted product baseline | v2.0.23; main inspected at `2db1230f638cd065d791c05f1adb7b4b51505c57` |
| Roadmap | M0/M1 acceptance preserved; M2 active; no new gate accepted |
| Current activity | Consolidate existing planning histories before checked main integration |
| Current planning lineage | Both inspected planning tips retained as parents of the reconciliation commit |
| Main integration | Not performed; classification/scope, discovery and full checkout checks remain open |
| Branch deletion | Not performed; no ref-deletion action is exposed by the current connection |
| Owner checkout / unpublished work | Not inspected; unknown |
| Native products / hardware | Deferred through M10; not applicable to this cleanup |
| Assurance profile | No new profile selected |

The machine-readable roadmap remains milestone/status authority. Focused accepted contracts and the requirement/governance registers remain engineering authority. This record does not supersede them.

### Development method and continuity

Raven Forge Development remains the standing method. The previously adopted project revision is unrecovered. Inspected version 0.6.2 at `ed0028a46bac9c5b92876a6ad6589ca421fd9499` remains an inspection reference only, not an adopted upgrade. The source registers preserve inherited mandatory-core coverage and its limits. No new complete source-reading or linked-realization acceptance is claimed.

The [location decision](decisions/2026-09-19-planning-location.md) governs repository storage. Earlier directions to file all records in an assumed external workspace remain superseded. Only issued coding-agent instruction packages must stay in the external instructions workspace.

## 2. Purpose, scope and exclusions

The specification is the product. ASH Model Cosmology, APS and Aeostara supply reference semantics/design, not runtime repositories to import. YWE owns its object contracts. WRW and Ravenfall remain reference profiles, not universal Core truth.

The current cleanup retains needed work and both histories on one existing planning lineage. It does not create another branch, change the accepted packet artifact, modify the value candidate, approve wire choices, introduce dependencies, resolve disputed normalization, change platform gates, or start implementation. Main is not advanced merely because preservation succeeded.

## 3. Users and workflows

Maintainers start at the directory README, this record and its current handoff. Older Project Records and handoffs are historical snapshots, not competing current authorities. The [branch reconciliation](publication/Branch_Reconciliation.md) supplies a per-file disposition for every earlier planning path.

The previously completed compatibility review demonstrates a checked-input mapping into the existing helper, not a drop-in replacement. Signature fields, ordered sequences and compatibility aliases remain preserved on the tested path. Branch preservation, main integration, compatibility and design acceptance are separate outcomes.

## 4. Requirements and acceptance

No new normative requirement ID, candidate approval, debt closure, protocol version or milestone acceptance is issued. Existing accepted sources, product versions, M0/M1 evidence and roadmap files are unchanged.

Inherited M1 evidence reports 18 requirements, 27 governance records, 119 glossary terms, ten authority nodes and a pinned 32-file corpus. Inherited M2 schema debt remains 132 findings across 119 paths: 31 missing identifiers, 13 annotation-only schemas, 49 descriptive schema-named documents and 39 unbound examples. These remain inherited observations, not fresh whole-repository measurements.

The [readiness review](m2/readiness/M2_Readiness_Review.md) retains its permissive-root and direct-conversion findings. Storage or testing of a candidate does not resolve the registered debt.

## 5. Architecture, sources and open decisions

The [two-value contract](m2/ash-values/Ash_Value_Contract.candidate.md) and [candidate decisions](m2/ash-values/candidate-decisions.json) remain proposed. State representation, codeword membership, operational admission and mutation authority remain distinct. Immutable values own coordinates; actual membership is checked, not trusted from metadata.

The parent packet contains nine local descriptions and twenty-one delegated records. Only two values have the experimental contract. No other domain is redesigned.

The [value source register](m2/ash-values/source-register.json), [readiness source register](m2/readiness/source-register.json) and [compatibility review](m2/consumer-compatibility/README.md) retain source pins, roles, actual reading, exclusions and execution limits. Further governance/package consumers remain discovery-only where the earlier review did not read them completely.

The compatibility review found seven input-acceptance differences: the baseline coerces fractional, Boolean and string coordinates and accepts padded/Unicode signatures. Direct out-of-contract dataclass construction can retain mutable storage or accept short tuples; normal factory tuples are not claimed mutable. Property/method API shape and exact schema-target selection also require explicit migration treatment.

After cleanup, the proposed direction remains a narrow checked-input boundary preserving signature fields and aliases. Do not globally replace normalization, add membership fields to string sequences, close entire envelopes, or infer writer compatibility from helper comparisons.

Still open: the previous method binding; reviewed linked System Realization Contracts and independent acceptance/preflight; normalization/classification source reconciliation; Forsetti interface scope; field-specific references and aliases; complete standalone-record consumer inventory; and approval/versioning for membership, closedness, raw numeric parsing, writer output and schema-target binding. Hold only dependent work. No broad reset is required.

## 6. Experience and resources

No UI, branding, production asset, device requirement or user workflow changed. The owner need not download, sort or reconstruct archives. Further design expansion remains secondary to the requested branch cleanup.

## 7. Evidence and verification

Original candidate evidence remains unchanged: 512 represented states, sixteen accepted codewords out of 512 candidates, 8,192 transformations, 56 named fixtures, raw parsing/precision, ownership/order, offline references, ten detected schema faults and repeated equal result sections. These are bounded experiment results, not whole-engine or independent acceptance.

The [compatibility results](m2/consumer-compatibility/compatibility-results.json) retain 8,192 matching transformations, 2,048 matching snapshots, 2,048 matching plans, fifteen boundary probes with seven differences, and four unchanged identity tests. Its repeated result-section hash is `43e7f34ad8e185d82eaac5ae5dc887960fda50024b43244c6714aff680e0b8c2`. The verdict remains `not_drop_in_compatible`; these comparisons reuse the existing helper and do not independently prove all its semantics.

[Reconciliation checks](publication/Branch_Reconciliation_Checks.json) add eight exact compact-JSON blob matches, three identical verification-file blobs, and a link-only contract difference. A fresh isolated candidate execution passed ten groups and reproduced result hash `630cade04dadfc8ae236e34ffdcc1238703695b856b4d336fa0043d68d4ac113`.

The earlier distinct publication run is retained byte-for-byte in [its verification summary](m2/ash-values/evidence/verification-summary.json). [Its publication manifest](publication/Earlier_Planning_Publication_Manifest.json) describes the earlier snapshot and original hashes, not today's formatting or current routing. Other earlier variants remain in second-parent history.

No full repository suite, current complete checkout, owner-local inspection, native build, complete consumer inventory, realization preflight/delivery, independent approval or physical-device qualification is claimed. An available older archive was not a verified current checkout and was not used to change source authority. Direct network/archive access did not supply a current checkout. The connection exposes no branch/ref deletion action; discovery did not supply another suitable route. Do not use workflow or permission changes to manufacture an execution channel.

## 8. Reconciliation and persistence

The two source tips are `9fd7625241fee529452570cca6f1742cb6976856` on the current branch and `c4d505b71e4db829fdb1b84f3c368bf164ea8c31` on the earlier branch. The merge retains both as parents. The current candidate, fixtures, verification code and detailed original evidence remain unchanged. The earlier ignore rules, publication manifest and unique verification summary are retained. Earlier routing records remain historical rather than being restored as current authorities.

The [per-file resolution](publication/Branch_Reconciliation.md) explains all 24 earlier paths; this is not a blanket one-side conflict resolution. Main, product files, active metadata, protections, workflows and releases are unchanged. The source branch names have not been deleted. A successful consolidation does not establish completed cleanup or main integration.

The existing [publication receipt](publication/GitHub_Publication.json) remains historical evidence of the first branch save. This record's containing commit supplies the new reconciliation identity; remote parent and branch read-backs establish actual publication. No cryptographic signature or owner-checkout synchronization is implied.

## 9. Decisions and permissions

| Decision | State |
|---|---|
| Agnosticism, OO modularity, reference-only systems and existing acceptance | Preserved owner/project direction |
| Dedicated repository planning directory | Owner approved September 19, 2026 |
| Owner-account publishing and existing admin bypass if required | Permission retained; no force or protection changes |
| Merge needed branches; delete branches no longer needed | Explicit current owner authorization; no additional approval needed |
| Reconcile older publication with current planning | Preserve both histories; keep one current record and the later candidate files |
| Candidate adoption or method/source upgrade | Not performed |
| Main integration | Still subject to the recorded technical checks; not claimed completed |
| Release or platform implementation | Not authorized by cleanup |

## 10. Current step and next action

**Current step:** Planning histories reconciled on the existing planning branch; main integration and ref deletion remain unfinished.

**Completed:** Per-file reconciliation, retained original histories and unique evidence, exact formatting/code checks, fresh isolated candidate execution, and updated current continuity.

**Next action:** Complete classification/scope and experimental-discovery integration plus full pre/post repository checks against a verified checkout; advance main with the reconciled history; verify both original tips are ancestors of remote main; then remove the redundant refs through an authenticated deletion-capable route. Do not redo the already completed two-lineage reconciliation or create another planning branch.

**Needed from you:** No further permission, file sorting or reconstructed history. Execution still needs a current checkout for the outstanding checks and a branch-ref deletion capability.

**Saved at:** `docs/design-planning/` on `design-planning/m2-foundations`; the containing merge commit and remote read-back identify this revision. Main integration and deletion remain separate uncompleted actions.
