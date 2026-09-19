# Repository Integration Requirements

**Current status:** The owner-directed administrative merge into main completed at `13ee11704691b1c562e8e0099ca2b2e4533cb39e`. Technical integration checks below remain outstanding; merging did not establish a passing result.  
**Original main baseline:** `2db1230f638cd065d791c05f1adb7b4b51505c57`.  
**Current record:** [Project Record](../Project_Record.md) on main.

## Completed repository consolidation

The planning histories were reconciled with both parents retained. Main was then advanced without force to that reconciliation commit and read back successfully. The comparison with original main contained only additions under `docs/design-planning/`. Both inspected extra branch tips are now included in main; neither reference has been deleted. No existing engine file, product version, accepted M0/M1 evidence, source pin, roadmap gate, protection setting or workflow was changed by the merge.

## Outstanding technical work

1. Inspect a verified current checkout and preserve any owner-local staged, unstaged, untracked or ignored work. Do not treat a historical archive or remote metadata as a current owner checkout.
2. Maintain one Project Record at the existing main path and appropriate navigation. Do not restore historical records as competing authorities or promote candidate content by location alone.
3. Apply `docs/project/artifact_classification_policy.md`: reconcile active classification/scope manifests, exact path coverage, snapshots and counts. Use justified informative/example/historical dispositions for candidates, experiments and original evidence. Scoped continuity authority is not approval of candidate semantics. The current catch-all classification must not silently supply that approval.
4. Inspect schema/fixture discovery. Experimental catalogs are not production registration. Resolve false schema-debt findings for diagnostic reports without concealing actual schemas, increasing debt silently or weakening accepted checks. Keep experimental files outside runtime use.
5. Capture current repository results through the existing `scripts/validate_repository.py` route and compare against the original main baseline where reproducible. Preserve inherited failures separately from changes introduced by planning integration. Do not invent a pre-merge run or call a post-merge run historical pre-change evidence. Do not restore intentionally removed workflows or create runner spending to obtain an execution route.
6. Verify that accepted evidence, source pins, product version, roadmap status, platform gate and candidate approval states remain unchanged. Inspect final diffs and source/evidence hashes.
7. Remove the two redundant refs only through a deletion-capable authenticated route, after rereading their tips and confirming ancestry/preservation in main. Owner permission already exists. Do not force-push, disable protection or delete repository files as a substitute for deleting refs.

## Evidence boundary

The prior prerequisite list was not completed before the administrative merge. This document records that fact and retains each unfinished obligation; it does not claim a waiver, acceptance, full regression pass, debt closure or branch deletion. The source and original records remain available through the retained histories. Further candidate promotion remains dependent on the relevant technical and authority checks.

No coding-agent instruction package is issued by this document.
