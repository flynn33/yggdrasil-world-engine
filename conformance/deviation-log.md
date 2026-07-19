# Deviation Log

Date: 2026-05-10

## Current Authority and Identifier Mapping

Current typed deviation authority is
`data/governance/governance_record_register.json`, governed by
`docs/governance/governance_records_policy.md`. The historical `D-NNN`
records below remain unchanged as provenance. Current `DEV-NNNN` identifiers
supplement them and do not erase, rename, or reopen the historical entries.

| Current record | Historical record | Current status |
| --- | --- | --- |
| `DEV-0001` | `D-001` | `resolved` |
| `DEV-0002` | `D-002` | `resolved` |
| `DEV-0003` | `D-003` | `resolved` |
| `DEV-0004` | `D-004` | `resolved` |
| `DEV-0005` | `D-005` | `resolved` |

## Active Status

No open deviations remain for the code-agnostic repository alignment scope.
Runtime host implementations remain outside this repository and must prove
adapter-level conformance separately.

The ASH upstream authority pass is an accepted post-alignment architecture
extension. It does not reopen the ASH/ASP core-math rebuild, does not change
canonical ASH math, and does not introduce platform runtime code.

## Resolved Items

| ID | Affected path | Gate/backlog item | Reason | Status | Follow-up |
| --- | --- | --- | --- | --- | --- |
| D-001 | Superseded authority-chain package | Authority chain | Superseded by the ASH/ASP core math rebuild. | Resolved | Do not use the superseded package as active authority. |
| D-002 | `specs/registries/fallback-policy-registry.md` | R-003 / G-003 / G-005 | The active package described an earlier fallback-policy blocker, but the live file already uses full 9-bit `VALID` / `STABLE` fallback-state language and semantic integrity passes. | Resolved | Preserve blocking semantic integrity checks. |
| D-003 | Runtime implementation surfaces | G-007 through G-010 | This repository is code-agnostic and does not host platform runtime implementations. Required rebuilds are represented as schemas, interfaces, rule records, and validators. | Resolved | Host implementations must materialize only from `GenerationPlan` outputs and run the same acceptance checks before claiming conformance. |
| D-004 | Restored planning and engine design records | Preservation boundary | The alignment branch must rebuild existing engines and documents around the ASH math rather than replacing them with package-only summaries. | Resolved | Existing files are extended in place with ASH provenance, diagnostic, and materialization contracts. |
| D-005 | `YWE_ASH_UPSTREAM_AUTHORITY_PACKAGE.zip` | Upstream authority architecture extension | Package scope adds explicit ASH upstream mathematical and generative authority after accepted alignment. | Resolved | New contract, runtime flow, packet schemas, and validation gate references are additive and preserve existing design content. |

## Deferred Items

None for the code-agnostic repository scope.
