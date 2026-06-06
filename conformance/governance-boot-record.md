# Governance Boot Record

Date: 2026-05-10

## Active Authority

`YWE_ASP_CORE_MATH_REBUILD_PACKAGE` is the active controlling package for the
ASH/ASP core-math rebuild and supersedes older alignment or build packages
where they conflict.

Forsetti is not the active authority for ASH/ASP math, YWE cosmology truth,
codewords, diagnostics, generation semantics, or conformance acceptance.

YWE remains code-agnostic: this repository defines contracts, schemas,
validators, data records, diagnostics, and completion evidence; engine adapters and
host implementations may materialize only from `GenerationPlan` outputs and
must not author ASH truth or YWE domain truth.

## Local MCP Governance

Local MCP health evidence is recorded at:

`/Volumes/NVME/ywe_project_ops/logs/mcp_stack_health.json`

The health record verifies the package-mandated 20 of 20 required local MCP
server IDs. The current local stack also records a 23 of 23 operational
superset for the additional local tool roles requested for this branch.

## Required Role Records

Role completion records are stored under:

`/Volumes/NVME/ywe_project_ops/sub_agents/`

Required roles completed:

- architect
- sentinel
- planner
- reviewer
- debugger
- test-writer
- refactorer
- documenter
- performance-engineer
- security-auditor
- git-manager
- build-resolver
- coordinator
- multi-file-specialist

## Source-Edit Boundary

The source alignment is intentionally code-agnostic. It adds or normalizes
schemas, interfaces, validation contracts, adapter materialization boundaries,
and conformance evidence. It does not add host runtime implementation code.

This branch preserves the restored planning and engine design records. Existing
documents and data records are extended in place with ASH provenance and
materialization contracts rather than replaced by abbreviated package summaries.
