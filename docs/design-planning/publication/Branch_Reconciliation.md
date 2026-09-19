# Planning Branch Reconciliation

**Date:** September 19, 2026  
**Scope:** Reconcile the existing planning histories without creating another branch, changing accepted engine semantics, or representing branch preservation as main integration.  
**Current lineage:** `design-planning/m2-foundations` at `9fd7625241fee529452570cca6f1742cb6976856`.  
**Earlier lineage:** `planning/m2-design-records` at `c4d505b71e4db829fdb1b84f3c368bf164ea8c31`.  
**Common main baseline:** `2db1230f638cd065d791c05f1adb7b4b51505c57`.

## Reconciliation outcome

Use a two-parent merge retaining both inspected tips, with the current lineage as first parent. The retained working content is resolved per file below. The earlier branch is not discarded as though it never contained useful work. Its full original snapshot and both original commits remain reachable through the second parent. No independent current Project Record or second active handoff is created.

This is consolidation on the existing planning branch, not a merge into main. Full main-integration prerequisites in [Repository Integration Requirements](Repository_Integration_Requirements.md) remain open. Ref deletion was not performed. The containing commit and subsequent remote ancestry checks identify the actual saved result.

## Per-file disposition of the earlier branch

Paths are relative to `docs/design-planning/` in the earlier snapshot.

| Earlier path | Retained treatment and reason |
|---|---|
| `.gitignore` | Retain its exact blob at the same path; it excludes bytecode, a local environment and explicitly local experiment reports. |
| `Integration_Review.md` | Preserve in the second-parent history. Current integration requirements retain its prerequisites; its unique publication/403 history remains accessible at the original commit. Do not add a competing active review. |
| `Project_Record.md` | Keep and update the later current record. The earlier record explicitly predates consumer compatibility and does not approve a different design. Its complete contents remain in history. |
| `Publication_Manifest.json` | Retain exact bytes as `publication/Earlier_Planning_Publication_Manifest.json`, explicitly historical provenance for the earlier snapshot. |
| `README.md` | Keep the current directory navigation and its single-record routing, rather than the earlier branch and handoff destinations. |
| `Session_Handoff.md` | Preserve in second-parent history; use the existing current handoff under `handoffs/` for continuation. |
| `Storage_Decision.md` | Preserve in second-parent history. Its approved directory and reference-only constraints agree with the current decision; its earlier branch choice is not the current routing. |
| `m2/ash-values/Ash_Value_Contract.candidate.md` | Keep current bytes. Compared with the hash-verified original, the sole change is the relative path `../readiness/M2_Packet_Contract.prepared.md`; no construction or wire rule differs. |
| `m2/ash-values/Verification_Report.md` | Keep the current full-evidence navigation. Retain the earlier distinct publication run through its exact verification summary below and the original report in history. Do not equate the reports' dates or layouts. |
| `m2/ash-values/candidate-decisions.json` | Same JSON by exact compact re-encoding; retain current formatting and unchanged proposal statuses. |
| `m2/ash-values/evidence/verification-summary.json` | Retain exact original bytes at the same path as historical evidence of the earlier publication run. |
| `m2/ash-values/fixtures/catalog.json` | Same JSON by exact compact re-encoding; retain current bytes. |
| `m2/ash-values/fixtures/instances.json` | Same JSON by exact compact re-encoding, including Unicode escaping; retain current bytes. |
| `m2/ash-values/fixtures/pinned-codewords.json` | Same JSON by exact compact re-encoding; retain current bytes. |
| `m2/ash-values/fixtures/raw-json-cases.json` | Same JSON by exact compact re-encoding; retain current bytes. |
| `m2/ash-values/schemas/ash-values.candidate.schema.json` | Same JSON by exact compact re-encoding; retain current bytes and candidate status. |
| `m2/ash-values/schemas/catalog.json` | Same JSON by exact compact re-encoding; retain current bytes. |
| `m2/ash-values/source-register.json` | Keep the current detailed source register. The earlier compact register identifies the same product/method inspection pins but reorganizes provenance; do not claim byte or complete record equality. Preserve the original in history and its hashes in the earlier publication manifest. |
| `m2/ash-values/verification/requirements.txt` | Identical Git blob; retain unchanged. |
| `m2/ash-values/verification/value_model.py` | Identical Git blob; retain unchanged. |
| `m2/ash-values/verification/verify_contract.py` | Identical Git blob; retain unchanged. |
| `m2/readiness/M2_Packet_Contract.prepared.md` | Keep the current repository-routed draft and original evidence links. Earlier historical-storage notice and report wording remain in history; no new object rule is adopted by this selection. |
| `m2/readiness/M2_Readiness_Review.md` | Keep the current review with its detailed evidence available locally. The earlier variant points to an external original bundle; its full version remains in history. |
| `m2/readiness/source-register.json` | Same JSON by exact compact re-encoding; retain current bytes. |

## Verification

[Reconciliation checks](Branch_Reconciliation_Checks.json) record the eight exact JSON re-encoding matches, three unchanged verification-file identities, contract link-only change, and fresh candidate result. These are content and bounded experiment checks, not the full repository suite.

For the JSON comparison, parse the current file, serialize with `ensure_ascii=True`, `sort_keys=False`, `separators=(',', ':')` and one final newline, and compute the Git blob SHA-1 over `blob <byte-count>\0<bytes>`. Every resulting SHA matches the corresponding earlier remote blob. This verifies formatting-only differences without treating different byte hashes as different semantics.

A fresh candidate run passed its ten groups with result-section SHA-256 `630cade04dadfc8ae236e34ffdcc1238703695b856b4d336fa0043d68d4ac113`, equal to the preserved result. No candidate model, schema, fixture or existing detailed evidence is changed.

The earlier manifest and verification summary describe their original snapshot. Their input hashes are not assertions that today's differently formatted files have those byte hashes. Their original timestamps and limitations remain unchanged.

## Remaining cleanup

Main remains at the inspected baseline. Exact classification/scope snapshots, experimental discovery and full repository pre/post validation remain required for main integration. Do not waive those obligations or restore paid workflows to manufacture an execution route. The current connection has no branch/ref deletion action; no deletion or final one-branch state is claimed.

After checked main integration, verify both inspected original tips are ancestors of remote main, then delete both redundant branch references using an available authenticated route. Until that integration, the earlier tip is preserved by the consolidated planning lineage, not by main.
