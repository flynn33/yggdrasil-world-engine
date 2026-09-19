# YWE Design and Planning

This directory is the working home for Yggdrasil World Engine design proposals, planning records, experiments, and their evidence. Start here rather than downloading and organizing separate archives.

## Current work

M2 remains the active roadmap milestone. The current candidate defines `AshState` and `CanonicalCodeword` as distinct immutable values and proposes their message formats. Compatibility review is next; these proposals are not accepted engine requirements.

| Read | Purpose |
|---|---|
| [Project Record](Project_Record.md) | One current continuity record: decisions, permissions, unresolved questions, and next action |
| [Session Handoff](Session_Handoff.md) | Resume the current work without reconstructing the conversation |
| [Storage Decision](Storage_Decision.md) | Owner-approved repository location and publication boundary |
| [Two-value contract](m2/ash-values/Ash_Value_Contract.candidate.md) | Candidate object responsibilities, construction rules, and wire formats |
| [Verification report](m2/ash-values/Verification_Report.md) | Actual experimental results and limitations |
| [Earlier readiness review](m2/readiness/M2_Readiness_Review.md) | Why direct promotion of the descriptive packet file is unsafe |
| [Parent packet draft](m2/readiness/M2_Packet_Contract.prepared.md) | Scope and ownership of the broader packet work |
| [Integration review](Integration_Review.md) | Remaining repository and compatibility checks before merge |

## Status and authority

The owner approved saving design and planning work in a dedicated repository directory on September 19, 2026. That approves storage and a review branch, not the candidate's semantic choices, milestone completion, a method upgrade, or a release.

The existing [machine-readable roadmap](../../data/governance/specification_roadmap.json), accepted M0/M1 evidence, focused normative contracts, source pins, and version remain unchanged. This directory does not replace those authorities. The Project Record is authoritative for the current working brief and storage decision; it links to, rather than duplicates or overrides, the accepted engineering records.

This is a draft review branch. The repository-wide classification and scope manifests still require reconciliation for these new paths before merge. Candidate headings do not override the current machine-readable classification policy. See the integration review; no full repository validation pass is claimed.

## What belongs here

Design drafts, planning decisions, review notes, experimental schemas and fixtures, verification-only tools, and evidence belong here while under review. Accepted artifacts may be promoted to their established repository locations through an explicit reviewed change with traceability.

Issued coding-agent instruction packages remain in the external project-instructions workspace. Whole reference repositories, nested transport ZIPs, copied upstream source trees, and platform implementations are not stored here.

## Reproduce the candidate experiment

From `m2/ash-values/`, use the testing versions in `verification/requirements.txt` and run:

```text
python verification/verify_contract.py --report evidence/local-new-run.json
```

The tool refuses to overwrite an existing report. Python is verification tooling, not production engine source. A passing experiment does not approve the candidate or complete M2.
