# Yggdrasil World Engine — Design and Planning

**Purpose:** Maintain YWE design work, planning decisions, review drafts, experimental checks and supporting evidence with the project.  
**Location:** `docs/design-planning/` on `main`.  
**Merge anchor:** `13ee11704691b1c562e8e0099ca2b2e4533cb39e` preserves both planning histories. The extra branch names are no longer working authorities.

## Start here

Read [Project Record](Project_Record.md) for current state and [latest handoff](handoffs/2026-10-03-m2-yaml-manifests.md) for continuation. The [storage decision](decisions/2026-09-19-planning-location.md) records the owner's approval to keep this work in the repository.

This directory is not a replacement for accepted contracts, the machine-readable roadmap or acceptance evidence elsewhere. A draft's presence on main does not approve its content.

## Directory map

| Location | Contents |
|---|---|
| `Project_Record.md` | One current continuation record: decisions, proposals, limits and next action |
| `handoffs/` | Handoffs pointing to that record; earlier revisions remain historical |
| `decisions/` | Planning decisions with actual authority and scope |
| `m2/readiness/` | Packet readiness review, packet draft, sources and diagnostic evidence |
| `m2/ash-values/` | Two-value candidate, proposed decisions, experimental schema, fixtures, tools and original reports |
| `m2/consumer-compatibility/` | Existing-helper comparisons, input/API differences and proposed migration boundary |
| `publication/` | Transfer/reconciliation evidence and outstanding integration requirements |

## Status and authority

An approved storage/merge decision is not an approved engine design. Drafts remain proposals. A tested candidate means only that its recorded experiment produced the stated results. Historical evidence retains its source, date and limits.

M0–M3 are accepted and M4 is in progress. The current repository baseline is
defined by [VERSION](../../VERSION) and mirrored in the Project Record. Preserve
accepted historical evidence, existing source pins and the closed platform gate.
No new dependency or changed engine rule is implied by this directory. Candidate
promotion requires a separately recorded engineering decision and integration evidence.

## What stays outside

Issued coding-agent instruction packages remain in the external project-instructions workspace. Do not commit transport ZIPs, nested archives, redundant source snapshots or obsolete copies of the current Project Record.

## Merge status and technical follow-through

Both planning histories were merged into main and remain reachable through the
merge anchor above. The Project Record contains verified commit identities,
ancestry observations and subsequent working-branch decisions.

The [integration requirements](publication/Repository_Integration_Requirements.md)
preserve the September 19 administrative-merge and discovery-repair history. The
current Project Record records subsequent inventory reconciliation, M2/M3
acceptance and exact-commit repository verification. Those later results do not
retroactively change what was verified before the administrative merge.

Experimental catalogs do not register their contents in the engine's production validation catalog. The existing catch-all classification must not be treated as design approval. Original publication/preparation reports retain historical pending/no-push/no-merge fields; the current Project Record controls present storage status.
