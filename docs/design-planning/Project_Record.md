# Yggdrasil World Engine — Project Record

**Record ID:** YWE-RECOVERY-20260918  
**Revision:** planning-10  
**Date:** September 19, 2026  
**Authoritative branch:** `main`  
**Location:** `docs/design-planning/Project_Record.md`  
**Verified merge anchor:** `13ee11704691b1c562e8e0099ca2b2e4533cb39e`.  
**Verified post-deletion baseline:** `90f3c00f8b286aa064114575e607f7ce60e13df2`.

This is the single current planning record. It supersedes planning-9's statement that the redundant branch names remain. The owner reported deleting the branches; subsequent remote enumeration returned only main. Both planning histories remain reachable from main. Current handoff: [main continuation](handoffs/2026-09-19-consumer-compatibility.md). This record describes observed state; its containing commit supplies its revision identity.

## 1. Identity and current working brief

| Concern | Current state |
|---|---|
| Product / owner | Yggdrasil World Engine / Flynn; repository owner `flynn33` |
| Product purpose | Platform-neutral, strictly object-oriented and modular engine specification |
| Repository | `flynn33/yggdrasil-world-engine` |
| Accepted product version | v2.0.23; unchanged |
| Roadmap | M0/M1 acceptance preserved; M2 active; no new gate accepted |
| Authoritative record location | This path on `main`; no other remote branch remains at the latest inspection |
| Main before consolidation | `2db1230f638cd065d791c05f1adb7b4b51505c57` |
| Main after verified fast-forward | `13ee11704691b1c562e8e0099ca2b2e4533cb39e` |
| Main at post-deletion inspection | `90f3c00f8b286aa064114575e607f7ce60e13df2` |
| Planning histories | Both included in main; the last inspected tips of both deleted branches are ancestors of main |
| Branch reference deletion | Completed by the owner; subsequent remote enumeration returned only `main` |
| Recovery required | None identified for committed work at the two verified former branch tips |
| Validation integration | Classification/scope, experimental discovery and full repository checks remain unfinished |
| Owner checkout / unpublished work | Not inspected; no local synchronization claim |
| Native products / hardware | Deferred through M10; not applicable to this verification |
| Assurance profile | No new profile selected |

The machine-readable roadmap remains milestone/status authority. Focused accepted contracts and requirement/governance registers remain engineering authority. Repository storage does not approve candidate semantics.

### Development method and continuity

Raven Forge Development remains the standing method. The previously adopted revision remains unrecovered. Inspected version 0.6.2 at `ed0028a46bac9c5b92876a6ad6589ca421fd9499` remains an inspection reference, not an adopted upgrade. Source registers retain inherited mandatory-core coverage, source pins and reading limits. No new linked-realization acceptance is claimed.

The [storage decision](decisions/2026-09-19-planning-location.md) remains applicable. Current planning records belong in this repository directory. Only issued coding-agent instruction packages remain in the external instructions workspace.

## 2. Purpose, scope and exclusions

The specification is the product. ASH Model Cosmology, APS and Aeostara supply reference semantics/design, not runtime repositories to import. YWE owns its object contracts. WRW and Ravenfall remain reference profiles, not universal Core truth.

The owner explicitly directed merging needed work or deleting unneeded branches and then directed completing the cleanup. The resulting administrative consolidation advanced main to the already reconciled planning history. It did not modify existing engine files, approve the two-value candidate, change source pins, introduce dependencies, resolve normalization, alter platform gates, create another branch or publish a release.

The owner subsequently completed the outstanding branch deletion. This follow-up verifies surviving committed work and updates only the current record and handoff. It does not recreate deleted branches, redo preserved design work, or claim that the deletion was performed by the current session.

## 3. Users and workflows

Maintainers start on `main` at the directory README, this record and the current handoff. Deleted branches are not recreated for continuation. Earlier records remain historical snapshots, not competing authorities.

The [per-file reconciliation](publication/Branch_Reconciliation.md) documents the disposition of all 24 earlier planning paths. Both source histories remain reachable from main. The current candidate and detailed evidence were retained, while earlier ignore rules, distinct verification summary and publication manifest were preserved. Redundant routing records remain in history.

## 4. Requirements and acceptance

No new normative requirement ID, candidate approval, debt closure, protocol version or milestone acceptance was issued. M0/M1 evidence, product version, source pins, the roadmap and active engine contracts are unchanged.

Inherited M1 evidence reports 18 requirements, 27 governance records, 119 glossary terms, ten authority nodes and a pinned 32-file corpus. Inherited M2 schema debt remains 132 findings across 119 paths: 31 missing identifiers, 13 annotation-only schemas, 49 descriptive schema-named documents and 39 unbound examples. These are inherited counts, not a fresh whole-repository measurement.

The [readiness review](m2/readiness/M2_Readiness_Review.md) retains its permissive-root and direct-conversion findings. A planning merge does not resolve the registered debt or establish a passing repository suite.

## 5. Architecture, sources and unresolved decisions

The [two-value contract](m2/ash-values/Ash_Value_Contract.candidate.md) and [candidate decisions](m2/ash-values/candidate-decisions.json) remain proposed. State representation, codeword membership, operational admission and mutation authority remain distinct. Immutable values own coordinates; actual membership is checked rather than trusted from metadata.

The parent packet contains nine local descriptions and twenty-one delegated records. Only two values have the experimental contract. Other domains are not redesigned.

The [value source register](m2/ash-values/source-register.json), [readiness source register](m2/readiness/source-register.json) and [compatibility review](m2/consumer-compatibility/README.md) preserve pins, source roles, actual reading and exclusions. Further governance/package consumers remain discovery-only where not read completely.

The bounded compatibility review found seven input-acceptance differences, including fractional/Boolean/string coordinate coercion and padded/Unicode signatures. Direct out-of-contract dataclass construction can retain mutable storage or accept a short tuple; normal factory tuples are not claimed mutable. Property/method API shape and exact schema-target selection require explicit migration treatment.

The proposed next design remains a narrow checked-input boundary preserving signature fields, ordered sequences and aliases. Do not globally replace normalization, add membership fields to string sequences, close entire envelopes or infer writer compatibility from helper comparisons.

Still unresolved: prior method binding; reviewed linked System Realization Contracts and independent acceptance/preflight; normalization/classification source reconciliation; Forsetti interface scope; field-specific references/aliases; complete standalone-record consumer inventory; and approval/versioning for membership, closedness, raw parsing, writer output and schema-target binding. Hold only dependent work; do not restart the project.

## 6. Experience and resources

No UI, branding, production asset or device requirement changed. The owner need not download, sort or reconstruct archives. Work is available from the repository's default and only remaining branch, main.

## 7. Verification and limitations

Inherited candidate evidence remains unchanged: 512 represented states, sixteen accepted codewords out of 512 candidates, 8,192 transformations, 56 named fixtures, raw parsing/precision, ownership/order, offline references, ten detected schema faults and repeated equal result sections. The reconciliation's fresh isolated run passed ten groups with result-section hash `630cade04dadfc8ae236e34ffdcc1238703695b856b4d336fa0043d68d4ac113`.

The [compatibility results](m2/consumer-compatibility/compatibility-results.json) retain 8,192 matching transformations, 2,048 matching snapshots, 2,048 matching plans, fifteen boundary probes with seven differences, and four unchanged identity tests. Repeated result hash: `43e7f34ad8e185d82eaac5ae5dc887960fda50024b43244c6714aff680e0b8c2`. The verdict remains `not_drop_in_compatible`. These comparisons reuse the existing helper and do not independently prove its complete semantics.

The earlier consolidation verified the live branch identities, read the complete planning-8 record and handoff, read the reconciliation commit's two parents, compared the reconciled history with main, performed a non-forced main ref update and read back the branch collection. The pre-merge comparison reported seven commits ahead, zero behind, and additions confined to `docs/design-planning/`. No pre-existing main file was modified or deleted by that fast-forward.

The earlier comparison from branch tip `c4d505b71e4db829fdb1b84f3c368bf164ea8c31` to merged main reported five ahead, zero behind, with that earlier tip as merge base. The newer branch tip was identical to merged main. Both inspected planning histories were preserved in main before branch deletion.

### Post-deletion verification — September 19, 2026

The owner reported deleting the extra branches. A fresh GET of the repository branch collection with `per_page=100` returned exactly one branch, `main`, at `90f3c00f8b286aa064114575e607f7ce60e13df2`. The complete planning-9 Project Record and current handoff were read at that immutable commit.

Two fresh comparisons used that main commit as base and the former branch tips as heads:

| Former branch | Verified former tip | Result relative to main | Merge base |
|---|---|---|---|
| `design-planning/m2-foundations` | `13ee11704691b1c562e8e0099ca2b2e4533cb39e` | `behind`; zero ahead, one behind, zero head-only commits | Exact former tip |
| `planning/m2-design-records` | `c4d505b71e4db829fdb1b84f3c368bf164ea8c31` | `behind`; zero ahead, six behind, zero head-only commits | Exact former tip |

Both known tips are ancestors of the inspected main. No committed history from either verified tip was lost by removing the branch references, and no reconstruction of that work is required. This conclusion covers the known remote tips; it is not a claim about uninspected owner-local or never-pushed work. History preservation is not a new file-by-file semantic review or a passing test result.

No new experiment run, full repository suite, complete current checkout, owner-local inspection, native build, complete consumer inventory, realization preflight/delivery or independent acceptance is claimed. Earlier direct network acquisition remained unavailable. A recovered historical archive had inconsistent version markers and lacked the current governance manifests; it was not substituted for the current repository or used to claim current validation.

## 8. Administrative merge and remaining technical obligations

The non-forced update of `main` from `2db1230f638cd065d791c05f1adb7b4b51505c57` to `13ee11704691b1c562e8e0099ca2b2e4533cb39e` succeeded. Read-back returned that exact main tip. The target merge commit retains parents `9fd7625241fee529452570cca6f1742cb6976856` and `c4d505b71e4db829fdb1b84f3c368bf164ea8c31` and identifies Jim Daley as author and committer. No force update, protection/configuration change or new workflow was used.

The owner completed deletion of the redundant branch references. Subsequent enumeration and ancestry checks establish the current single-branch state and preservation of the known committed work. The previous session left the deletion unfinished; this follow-up records the owner's action rather than claiming it executed that deletion. No deleted reference was recreated and no missing committed work was identified.

The previously recorded classification/scope snapshots, nonnormative experimental treatment, discovery review and full pre/post checks were not completed before the administrative merge. They remain outstanding on main; no passing result or completed acceptance is inferred from the owner's merge direction or branch deletion. The existing catch-all classification is not evidence that a candidate has been approved. [Repository Integration Requirements](publication/Repository_Integration_Requirements.md) records the remaining technical work.

The older [publication receipt](publication/GitHub_Publication.json), [reconciliation checks](publication/Branch_Reconciliation_Checks.json), [earlier verification summary](m2/ash-values/evidence/verification-summary.json) and [earlier publication manifest](publication/Earlier_Planning_Publication_Manifest.json) retain their original dates, hashes and limitations. This record controls current storage and cleanup status; historical no-merge or pending-deletion fields are not current instructions.

## 9. Decisions and permissions

| Decision | State |
|---|---|
| Agnosticism, OO modularity, reference-only systems and prior acceptance | Preserved |
| Dedicated planning directory | Owner approved September 19, 2026 |
| Owner-account publishing and existing admin bypass if required | Permission retained; normal non-forced updates used |
| Merge needed branches or delete unneeded branches | Both inspected histories included in main; owner completed reference deletion |
| Authoritative record location | Same path on main; no competing current record |
| Branch-name deletion | Owner-reported action; absence of both names independently verified through GitHub |
| Missing work | Recreate only a demonstrated missing requirement or artifact; no redo is needed for the preserved branch histories |
| Candidate adoption, method/source upgrade, release or platform work | Not performed or implied |
| Repository-wide technical acceptance | Not established; outstanding obligations remain visible |

## 10. Current step and next action

**Current step:** Owner-completed branch cleanup verified; committed planning histories remain preserved on main.

**Completed:** Confirmed only main remains, retrieved the full current record and handoff, and verified both former branch tips are ancestors of main. No missing committed history was identified; no branch or design work was recreated.

**Next action:** Finish the existing planning-directory classification/scope and discovery integration on main, separating inherited failures from regressions through repository checks. Then resume the narrow input-boundary specification. Do not recreate deleted branches, repeat the completed reconciliation, or redo preserved work.

**Needed from you:** Nothing to approve, download, sort or reconstruct.

**Saved at:** `docs/design-planning/` on `main`; post-deletion baseline `90f3c00f8b286aa064114575e607f7ce60e13df2`. This update's containing commit identifies planning-10. Record publication is verified separately by remote read-back.
