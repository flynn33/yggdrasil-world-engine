# Repository Integration Requirements

**Status:** Main-integration obligations remain pending. A dedicated planning-branch save is authorized separately; it does not establish that these checks passed.
**Prepared baseline:** `flynn33/yggdrasil-world-engine`, `main`, `2db1230f638cd065d791c05f1adb7b4b51505c57`.

## Required integration review

1. Inspect the actual checkout, worktree, branches, and remote before applying these files. Preserve unpublished work. Reconcile any pre-existing authoritative record before replacing it.
2. Add this dedicated directory and a concise navigation link from the appropriate existing project index. Keep candidate content visibly unapproved.
3. Apply `docs/project/artifact_classification_policy.md`: update the active classification and scope manifests in the same change, with exact path coverage and counts. Use justified informative/example/historical dispositions for drafts, experimental material, and original evidence rather than the default normative catch-all. Approved planning-record authority is not approval of candidate engine semantics.
4. Inspect actual schema/fixture discovery before including experiments. A local experimental catalog is not a production registration. Do not create new schema debt or weaken accepted validation simply to store review examples. Where the existing system cannot represent the distinction safely, separate the documentation-only publication from experimental-file integration and record the held paths.
5. Capture pre-change and post-change results through the existing `scripts/validate_repository.py` / `scripts/run_checks.sh` route. Preserve inherited failures separately from regressions. Do not restore intentionally removed hosted workflows or add runner spending.
6. Confirm no accepted M0/M1 evidence, ASH source pin, normative rule, product version, release status, platform gate, or candidate decision approval was changed. Inspect the final diff and file-transfer hashes.
7. Commit and push using the owner's authenticated route and existing branch policy. The owner has explicitly authorized use of the existing admin bypass if needed. Do not disable protections, force-push, or claim remote integration from a local commit alone. Record the resulting commit and read back the target files and hashes.

## Scope limit

This prepared directory is not advertised as an immediately mergeable patch: full checkout inspection, active manifest synchronization, production-discovery review, and repository regression execution remain pending. Connected GitHub write capability was subsequently verified under `flynn33`. The chosen preservation route is branch `design-planning/m2-foundations`, leaving `main` unchanged until these integration obligations are satisfied.

No implementation package is issued by this document. It records obligations that travel with the design work and its eventual publication.
