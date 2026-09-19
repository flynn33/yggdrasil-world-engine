# Yggdrasil World Engine — Design and Planning

**Purpose:** Maintain YWE design work, planning decisions, review drafts, experimental checks and supporting evidence with the project.  
**Location:** `docs/design-planning/` on `main`.  
**Merge anchor:** `13ee11704691b1c562e8e0099ca2b2e4533cb39e` preserves both planning histories. The extra branch names are no longer working authorities.

## Start here

Read [Project Record](Project_Record.md) for current state and [latest handoff](handoffs/2026-09-19-consumer-compatibility.md) for continuation. The [storage decision](decisions/2026-09-19-planning-location.md) records the owner's approval to keep this work in the repository.

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

Preserve M0/M1 acceptance, M2 status, v2.0.23, existing source pins and the closed platform gate. No new dependency or changed engine rule is implied by this directory. Candidate promotion requires a separately recorded engineering decision and integration evidence.

## What stays outside

Issued coding-agent instruction packages remain in the external project-instructions workspace. Do not commit transport ZIPs, nested archives, redundant source snapshots or obsolete copies of the current Project Record.

## Merge status and technical follow-through

Both planning histories have been merged into main. The source branch refs have not been deleted. The Project Record contains the verified commit identities and ancestry observations.

The [integration requirements](publication/Repository_Integration_Requirements.md) remain unfinished technical work: synchronize classification/scope coverage, prevent experimental material from being treated as accepted engine authority, review generic discovery and run the repository suite. These checks were not completed before the administrative merge, and no full-suite success is claimed.

Experimental catalogs do not register their contents in the engine's production validation catalog. The existing catch-all classification must not be treated as design approval. Original publication/preparation reports retain historical pending/no-push/no-merge fields; the current Project Record controls present storage status.
