# Yggdrasil World Engine — Project Record

**Record ID:** YWE-RECOVERY-20260918  
**Revision:** planning-6  
**Date:** September 19, 2026  
**Authoritative planning branch:** `design-planning/m2-foundations`  
**Location:** `docs/design-planning/Project_Record.md`  
**Persistence anchor:** Predecessor planning-5 was read and verified at `4b5e7b9a5428df37491bec1b820074054b4fef90`. When this revision is read on the named branch, its containing Git commit supplies its storage identity; no future commit hash is predicted here.

This is the single current planning record. It supersedes planning-5's working status, not accepted engine contracts or original evidence. The complete predecessor remains in Git history. Current handoff: [consumer compatibility](handoffs/2026-09-19-consumer-compatibility.md).

## 1. Identity and current state

| Concern | Current state |
|---|---|
| Product / owner | Yggdrasil World Engine / Flynn; authenticated GitHub account `flynn33` |
| Product purpose | Platform-neutral, strictly object-oriented and modular engine specification |
| Repository | `flynn33/yggdrasil-world-engine` |
| Accepted product baseline | v2.0.23; main rechecked at `2db1230f638cd065d791c05f1adb7b4b51505c57` |
| Roadmap | Existing M0/M1 acceptance preserved; M2 active; no new gate accepted |
| Initial planning publication | `56abad1d6db1829feb074c6459466089930bf2a6` |
| Starting planning branch head | `4b5e7b9a5428df37491bec1b820074054b4fef90` |
| Current activity | First bounded consumer-compatibility review completed; input-boundary specification next |
| Main integration | Still pending; no merge or complete repository validation |
| Owner checkout / unpublished work | Not inspected; unknown |
| Native products / hardware | Deferred through M10; not applicable to this review |
| Assurance profile | No new profile selected |

The machine-readable roadmap remains the milestone/status authority. Focused accepted contracts remain implementation-detail authority. This record does not supersede either.

### Development method and continuity

Raven Forge Development remains the standing method. The previously adopted project revision is unrecovered. Inspected version 0.6.2 at `ed0028a46bac9c5b92876a6ad6589ca421fd9499` remains an inspection reference only, not an adopted upgrade. Mandatory-core reading and its actual inherited coverage remain in the source registers; no new full-repository reading is claimed.

The owner approved this repository directory and owner-account publishing, with existing admin bypass permitted if needed. The previous branch push succeeded without force or bypass. No change to permissions, protections, workflows, releases or main is authorized merely by this review. Earlier directions to file all records in an assumed external workspace were superseded by the [location decision](decisions/2026-09-19-planning-location.md). Issued coding-agent packages remain external.

## 2. Purpose, scope, and exclusions

The specification is the product. ASH Model Cosmology, APS, and Aeostara supply reference semantics/design, not runtime repositories to import. YWE owns its object contracts. WRW and Ravenfall remain reference profiles, not universal Core truth.

The current work compares the existing finite helper and packet outputs with the two-value candidate. It does not approve that candidate, replace the active packet artifact, change source pins, introduce dependencies, add gameplay, resolve disputed normalization, or start native implementation. Original archives and source snapshots remain outside the committed planning directory.

## 3. Users and workflows

Maintainers and future implementers start at the directory README and this record, then consult controlling contracts and exact candidate/source/evidence files. Candidate value construction validates representation and actual membership where appropriate, creates immutable values, and performs pure transformations without world-mutation authority.

The new review demonstrates an explicit checked-input mapping into the existing helper, not a drop-in API replacement. Signature fields, ordered sequences and compatibility aliases are preserved in the tested outputs. Branch publication, consumer compatibility, main integration and specification acceptance remain distinct conclusions.

## 4. Requirements and acceptance

Existing requirement and governance registers control. No new normative requirement ID, candidate approval, debt closure, protocol version or milestone acceptance was issued.

Inherited M1 evidence reports 18 requirements, 27 governance records, 119 glossary terms, ten authority nodes, and a pinned 32-file corpus. Inherited M2 debt is 132 findings over 119 paths: 31 missing identifiers, 13 annotation-only schemas, 49 descriptive schema-named documents, and 39 unbound examples. These remain historical observations, not newly measured counts.

The [readiness review](m2/readiness/M2_Readiness_Review.md) preserves the demonstrated permissive schema behavior and direct-conversion hazards. Publishing or testing a candidate does not close that debt.

## 5. Architecture, sources, and unresolved decisions

The [two-value contract](m2/ash-values/Ash_Value_Contract.candidate.md) and [candidate decisions](m2/ash-values/candidate-decisions.json) remain proposed. State representation is distinct from codeword membership, operational admission and mutation authority. Values own coordinates; exact membership is not trusted from metadata.

The parent packet has nine local descriptions and twenty-one delegated records. Only two values have this experimental contract. Other domains are not redesigned here.

The [value source register](m2/ash-values/source-register.json), [readiness source register](m2/readiness/source-register.json) and [new compatibility review](m2/consumer-compatibility/README.md) preserve pins, source roles, actual reading, execution limits and exclusions. The review read the complete existing helper, exports, four-test file, and broader engine interface. It executed hash-verified selected files, not a full checkout. Further governance/package-check consumers were located through search but not fully reviewed.

New findings: the baseline helper coerces fractional, Boolean and string coordinates, and accepts padded/Unicode-digit signatures; seven input acceptance differences were reproduced. Direct out-of-contract dataclass construction can retain a mutable list or accept a short tuple. Normal helper-created tuple values are not claimed to be mutable. The candidate also changes the signature property into a method and requires exact consumer-selected schema targets.

Proposed direction: preserve existing signature-bearing packet fields and aliases; specify a separate checked input boundary and compatibility facade. Do not globally replace `normalize_bits`, add membership members to string sequences, close whole envelopes, or claim standalone writer compatibility from helper tests.

Still unresolved: prior method binding; complete linked System Realization Contracts and independent acceptance/preflight; normalization/classification source reconciliation; Forsetti interface scope; field-specific reference/alias rules; complete standalone-record consumer inventory; approval/versioning for membership, closure, raw numeric parsing, writer output and schema-target binding. Hold only dependent work. No broad project reset is needed.

## 6. Experience and resources

The README remains the front door; this record is the current working state; dated handoffs point back to it. No UI, branding, production asset or device requirement changed. The owner need not download or sort archives.

## 7. Verification and limitations

Original candidate evidence is unchanged: 512 represented states, sixteen accepted codewords out of 512 candidates, 8,192 transformations, 56 named fixtures, raw JSON/precision and ownership/order checks, ten detected schema mutations, offline references, and three repeated result sections. These are bounded experimental findings, not independent or whole-engine acceptance.

During the previous publication, a fresh run passed all ten candidate groups and reproduced result hash `630cade04dadfc8ae236e34ffdcc1238703695b856b4d336fa0043d68d4ac113`. [Publication checks](publication/Publication_Checks.json) preserve that evidence. All 41 M2 payload files matched the prepared subtree and all 49 initial publication files matched the local planning tree. Relative links and attribution scanning were checked then.

The current [compatibility results](m2/consumer-compatibility/compatibility-results.json) add six executed groups: 512 represented-state comparisons; identical sixteen-word enumeration; 8,192 matching transformations; 2,048 matching snapshots plus 2,048 matching plans; fifteen boundary probes with seven acceptance differences; construction/ownership/API and exact-schema-target checks; and four unchanged identity tests. These counts overlap within the six groups and are not a combined test-count metric.

Two runs produced identical result sections with SHA-256 `43e7f34ad8e185d82eaac5ae5dc887960fda50024b43244c6714aff680e0b8c2`. [Reproduction checks](m2/consumer-compatibility/reproduction-checks.json) also record source-preservation verification, refusal to execute altered source and refusal to overwrite a report. Reports were serialized compactly for publication without changing their fields.

The verdict is `not_drop_in_compatible`. Successful review execution means the differences were reproduced, not that the candidate is adopted. Packet equality uses a review-only comparison encoding and the same existing helper; it is not an independent semantics oracle, global canonical-JSON decision or native-output proof.

No full repository suite, owner-checkout inspection, readiness rerun, complete consumer inventory, native build, realization preflight/delivery, independent approval or physical-device qualification is claimed. The direct checkout failed on GitHub DNS resolution; archive retrieval also failed. No complete checkout was obtained. Source files used by the review were individually hash-verified and remained unchanged.

## 8. Execution and persistence

The existing [publication receipt](publication/GitHub_Publication.json) records the first successful connected write and read-back. The initial commit added 49 files under `docs/design-planning/`, with no unrelated changes or deletions; its planning subtree was `54e35e319184101d7a425b39cb5baaa788bc6479`. The follow-up planning-5 commit is the verified predecessor of this revision. Both previous commits identify Jim Daley / `flynn33`; they are unsigned. Content verification is not a cryptographic-signature claim.

The current change preserves the same planning branch and adds the review, reproducible probe, results and handoff while updating this record and navigation. It does not install a new source repository or change the candidate model, production schema, accepted evidence, active metadata, product version or roadmap. Source and artifact hashes accompany the review.

Main-integration obligations in [Repository Integration Requirements](publication/Repository_Integration_Requirements.md) remain pending: complete checkout inspection, classification/scope path snapshots, nonnormative experimental treatment, production discovery, navigation and full pre/post checks. Do not merge under the default normative catch-all or equate a successful branch save with passing those gates.

An older remote branch, `planning/m2-design-records` at `c4d505b71e4db829fdb1b84f3c368bf164ea8c31`, was observed and left untouched. It does not replace the named authoritative planning branch or create a second current record.

## 9. Decisions and permissions

| Decision | Status |
|---|---|
| Agnosticism, OO modularity, reference-only systems, existing acceptance | Existing owner/project direction retained |
| Dedicated repository planning directory | Owner approved September 19, 2026 |
| Owner-account publishing; existing admin bypass if required; no attribution | Explicit permission retained; no force or protection changes |
| Two-value wire/construction choices | Tested proposals; approval fields unchanged |
| Compatibility disposition | Preserve tested outputs; explicit boundary migration proposed, not approved |
| Method/source upgrade | Not performed; prior method binding remains unresolved |
| Main integration or release | Not performed; integration checks pending |
| External-record filing assumption | Superseded; only issued instruction packages must remain external |

## 10. Current step and next action

**Current step:** First bounded packet-consumer compatibility slice completed.

**Completed:** Verified saved checkpoint; preserved original sources/candidates; executed six review groups, four existing tests and repeatability/safeguard checks; recorded actual incompatibilities and a proposed migration boundary.

**Next action:** Specify the narrow typed packet-to-value input boundary and its compatibility facade using the review: preserve signature fields and aliases, identify explicit rejection behavior, and keep standalone membership/closure/writer choices pending remaining consumer evidence. Continue independent design work; full-checkout main integration remains a separate unmet prerequisite.

**Needed from you:** Nothing to download, organize or reconstruct.

**Saved at:** `flynn33/yggdrasil-world-engine`, branch `design-planning/m2-foundations`, `docs/design-planning/`. The containing commit identifies this record revision; the verified predecessor is named above.
