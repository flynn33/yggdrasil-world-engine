# Yggdrasil World Engine — Design and Planning

**Purpose:** Maintain YWE design work, planning decisions, review drafts, experimental checks, and supporting evidence with the project.
**Location:** `docs/design-planning/`
**Publication route:** Owner-authorized branch `design-planning/m2-foundations`. Commit and read-back status is maintained in [Project Record](Project_Record.md). Integration into `main` is a separate, unfinished step.

## Start here

Read [Project Record](Project_Record.md) for the current state and [latest handoff](handoffs/2026-09-19-planning-publication.md) for continuation. The [storage decision](decisions/2026-09-19-planning-location.md) records the owner's approval to keep this work in the repository.

This directory is the selected home for design/planning records. It is not a replacement for accepted contracts, the machine-readable roadmap, or acceptance evidence elsewhere in the repository. A draft's presence in Git does not approve its content.

## Directory map

| Location | Contents |
|---|---|
| `Project_Record.md` | One current continuation record, including accepted decisions, proposals, limits, and the next action |
| `handoffs/` | Dated handoffs pointing to that record, not competing specifications |
| `decisions/` | Planning decisions with their actual authority and scope |
| `m2/readiness/` | Earlier packet readiness review, packet draft, source references, and diagnostic evidence |
| `m2/ash-values/` | Two-value candidate contract, proposed decisions, experimental schema, fixtures, verification tools, and original reports |
| `publication/` | File-transfer evidence and outstanding repository-integration requirements |

## Status and authority

**Approved storage decision** means the owner authorized this location and publication scope. **Draft/proposed** means not adopted as an engine requirement. **Tested candidate** means the recorded experiment produced the stated results; it is not design acceptance. **Historical evidence** retains its original source, date, and limits.

Only a separately recorded design acceptance and integration change can promote these proposals into active contracts. Preserve M0/M1 acceptance, M2 status, v2.0.23, the existing source pins, and the closed platform gate. Do not import any reference repository or change an engine rule merely to place documents here.

## What stays outside

Issued coding-agent instruction packages remain in the external project-instructions workspace. They are different from product design, planning, and test evidence. Do not commit the original transport ZIPs, nested archives, redundant source snapshots, or obsolete copies of the current Project Record.

## Branch publication and main-integration gate

This directory is published as planning work on the named design branch. It is not merged into `main`. The [integration requirements](publication/Repository_Integration_Requirements.md) remain mandatory before main integration: synchronize artifact/scope coverage, review generic discovery, and run the repository suite. The existing catch-all normative classification must not silently make experimental content authoritative. Publishing the branch preserves work; it does not pass those gates.

The raw experimental schema and fixtures are review material. Their own local catalogs do not register them in the engine's production validation catalog. No successful repository-suite result is claimed here.

`publication/File_Transfer_Manifest.json` and `publication/Preparation_Checks.json` preserve the earlier preparation state. Their pending/no-push fields are historical, not the current publication status. The current record and publication receipt take precedence for persistence.
