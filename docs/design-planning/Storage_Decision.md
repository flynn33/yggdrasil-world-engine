# Design and Planning Storage Decision

**Decision ID:** YWE-PLAN-STORAGE-20260919
**Status:** Owner approved for storage and scoped GitHub publication.
**Date:** September 19, 2026.

## Owner direction

> agreed, we will push this to GitHub as part of the designing and planning. We will keep them in a dedicated directory for designing and planning.

The selected repository location is `docs/design-planning/` in `flynn33/yggdrasil-world-engine`. The review branch is `planning/m2-design-records`, starting from `2db1230f638cd065d791c05f1adb7b4b51505c57`.

## Treatment

- Maintain one current `Project_Record.md` and one current `Session_Handoff.md` here. Git history preserves prior revisions.
- Retain candidate status, evidence limitations, source identities, and unresolved decisions when bringing the existing work into the repository.
- Keep issued coding-agent packages external. These design artifacts are not an issued implementation package.
- Publish a bounded review change without merging, tagging, releasing, changing platform gates, or modifying accepted engine semantics.
- Verify the actual remote commit and file identities before reporting a successful save.

## Superseded guidance

Earlier prepared records incorrectly asked the owner to reconcile files into an unverified external project-record workspace and to keep all review material outside the repository. That storage instruction is superseded by this decision. The earlier experimental results and candidate choices are not superseded.

No prior authoritative external record location was recovered. The repository record is the current continuity home established by this storage decision; it does not assert that an unknown external record was edited or migrated.

## Unchanged boundaries

M0/M1 acceptance, M2 status, v2.0.23, the pinned product baseline, reference-only system treatment, strict object orientation, modularity, and the deferred platform gate remain unchanged. The previously adopted playbook revision remains unresolved; the inspected revision is not silently adopted.
