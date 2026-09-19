# M2 Two-Value Consumer Compatibility Review

**Review ID:** YWE-M2-COMPATIBILITY-20260919  
**Date:** September 19, 2026  
**Status:** Completed bounded review; candidate remains unapproved and is not a drop-in replacement.  
**Baseline:** YWE v2.0.23 at `2db1230f638cd065d791c05f1adb7b4b51505c57`.  
**Planning parent:** `4b5e7b9a5428df37491bec1b820074054b4fef90` on `design-planning/m2-foundations`.

## Outcome in plain language

Correct existing patterns can keep their current messages. The proposed value checker can sit in front of the existing helper without changing the tested snapshot or plan contents. It must not simply replace that helper: they accept different inputs, expose different object APIs, and protect construction differently.

This is the next bounded design result after the [two-value candidate](../ash-values/Ash_Value_Contract.candidate.md), not a new roadmap review or engine reset. M0/M1 acceptance, M2 status, reference-only systems, source pins, and the platform gate remain unchanged.

## Verified scope

The review executed the exact existing `core/ash_pattern_engine/ash_canonical.py`, its package exports, and its four identity tests. Each recovered file was checked against its Git blob hash before execution and again afterward. The candidate model and schema were likewise pinned. This was a selected-file extraction, not a full checkout or an inspection of the owner's machine.

The complete recovered candidate directory reproduced the published subtree `587a819b47a02629361e423b84d2d475884ae928`. The baseline's full `core/ash_pattern_engine/engine_interface.json` was also read. It describes a broader interface, not a promise that the small Python helper is the complete engine implementation.

Searches for `normalize_bits`, `ash_canonical`, and `plan_generation` identified additional governance/package-check consumers. Those search hits are discovery evidence only. Their entire files, all external consumers, and the full repository test suite were not reviewed or executed here.

## Actual results

| Experiment | Observed result |
|---|---|
| All represented states | All 512 yield the same coordinate values through the candidate boundary. |
| Canonical set | All sixteen vectors and their order match exactly. |
| State/codeword combinations | All 8,192 transformations agree. |
| Whole helper packet comparisons | 2,048 snapshots and 2,048 plans retain the same contents after checked-value conversion. |
| Input-boundary probes | Fifteen executed; seven acceptance differences reproduced. |
| Existing identity regression tests | Four tests passed unchanged. |
| Reproduction and safeguards | Two result sections match; altered-source execution and report overwrite are rejected. |

The packet comparison uses sorted-key compact JSON only as a comparison encoding. It is not a new wire-standard decision or proof that another serializer emits identical bytes. The boundary experiment deliberately calls the same existing helper on both sides; it proves checked input mapping preserves those outputs, not that the helper's admission or diagnostic semantics are independently correct.

[Full results](compatibility-results.json) contain every boundary probe and source identity. [Reproduction checks](reproduction-checks.json) preserve repeatability and safeguard results. The result-section SHA-256 is `43e7f34ad8e185d82eaac5ae5dc887960fda50024b43244c6714aff680e0b8c2`.

## Compatibility findings and proposed disposition

| Concern | Existing behavior / evidence | Proposed disposition; not an approval |
|---|---|---|
| Signature fields and ordered codeword sequences | Snapshots and plans use nine-character signatures. Empty, zero, repeated, and nontrivial sequences preserve order in the comparisons. | Retain these field encodings; use explicit signature readers. Do not rewrite sequence items as standalone records. |
| Lossy coordinate conversion | `normalize_bits` converts each input with `int` before checking its range. `0.9`, `1.9`, and `-0.1` are accepted as 0, 1, and 0 respectively. | Validate exact values before conversion. Treat removal of the old coercions as an explicit compatibility change, not a transparent refactor. |
| Boolean, string, padded and Unicode inputs | Boolean/string array elements and padded/Unicode-digit signatures are accepted by the helper but rejected by the candidate. | Document the boundary grammar and migration policy. Do not silently rely on Python conversion behavior as the future native contract. |
| Direct object construction | The dataclass accepts an out-of-contract mutable list and a short tuple. Caller mutation of that list changes its signature. Normal helper factories produce tuples; no claim that normal factory results are mutable. | Guard public construction and own coordinates. Preserve an explicit compatibility facade where an existing caller needs the old API. |
| Object API shape | The helper exposes `signature` as a property; the candidate exposes `signature()` as a method. The existing package exports functions, not a drop-in candidate object API. | Do not substitute classes or imports blindly. Specify the facade and entry-point mapping before a production change. |
| Membership assertion | Existing codeword sequence items are strings. The candidate's standalone record requires Boolean `membership: true`. | Do not add that member to existing sequence strings. Standalone-record membership encoding remains a versioned proposal pending actual consumer inventory. Actual set membership must always be checked. |
| Exact expected type | A record without `membership` can pass the schema root as an AshState, but fails the codeword-specific target. | A codeword receiver must select `CanonicalCodewordRecord` or its explicit decoder; root success is insufficient. |
| Closed records | The candidate rejects an additional `note` member. No complete inventory of existing standalone record extensions was obtained. | Keep closure unapproved until those consumers are inventoried; do not apply the value-record schema to entire snapshots or envelopes. |
| Canonical writer and raw JSON safety | The helper is not a raw JSON reader or a standalone-record writer. | Do not claim compatibility for duplicate-key policy, exact-decimal parsing, member order or a new writer from these helper tests. Existing candidate tests remain separate evidence. |

The seven acceptance differences are intentional findings, not seven failed test executions. `review_checks_passed` means the recorded observations were reproduced. The compatibility verdict is still `not_drop_in_compatible`.

## Proposed migration boundary

Preserve the existing signature-bearing packet fields and compatibility aliases. Add a separately specified, typed input boundary that validates a state or codeword before passing an owned nine-coordinate value to the existing operation. Keep JSON arrays, signature strings, domain tuples and application iterables as distinct entry points; a JSON-array rule must not accidentally ban an existing iterable API.

Do not globally change `normalize_bits`, replace the full StateModel, remove aliases, close whole envelopes, add membership flags to string sequences, or promote the review URN to a production schema namespace in this slice. Successful value construction is not operational admission or world-mutation permission. Disputed normalization/classification semantics remain separately unresolved.

Before any production migration, the specification must identify the affected entry points, field shapes, version/deprecation treatment, construction failures, facade API, and consumer-specific schema target. This review supplies evidence for that decision; it does not approve a new protocol version or implementation.

## Source and reading record

| Source | Coverage / immutable identity |
|---|---|
| Existing Project Record and handoff | Read in full at planning parent; authority and permissions retained. |
| `core/ash_pattern_engine/ash_canonical.py` | Full source read and executed; Git blob `1d7f34f03747f494542ce9594d3ec955ae892942`. |
| `core/ash_pattern_engine/__init__.py` | Full source read and exercised by existing tests; blob `f46f3264c323aa741eb4968c2a42e641ed2c44fe`. |
| `tests/test_ash_canonical.py` | Full source read; four unchanged tests executed; blob `135975db2f8b703acaaf90175403793bd143139f`. |
| `core/ash_pattern_engine/engine_interface.json` | Full source read only; blob reported by GitHub `e5000084e35dfc6cdd25a31c73e2db5cbdcf7940`. |
| Two-value contract, decision list, model and schema | Read for this review; original candidate bytes and approval list unchanged. Executed model/schema hashes are in the results. |
| Prior source registers and method core | Inherited coverage retained, not relabeled as new full-repository reading. Inspected Raven Forge 0.6.2 at `ed0028a46bac9c5b92876a6ad6589ca421fd9499` is not a newly adopted binding. |
| Other governance/package-check consumers | Search discovery only; remaining review explicitly pending. |

## Reproduce without modifying source

Use the unchanged dependencies recorded in [the candidate's verification requirements](../ash-values/verification/requirements.txt). From the repository root:

```text
python docs/design-planning/m2/consumer-compatibility/verify_compatibility.py --baseline-root . --candidate-root docs/design-planning/m2/ash-values --report /absolute/external/evidence/compatibility-results.json
```

The report path must not already exist. Source hashes, not a guessed checkout path or branch name, guard the selected executed files. A mismatch blocks execution and requires a fresh review; never bypass it by relabeling a different source as this baseline. No engine file is copied into this review directory.

## Integration and next step

The full-checkout attempt failed on GitHub DNS resolution. An archive-retrieval attempt also failed; no archive or complete working tree was obtained. Therefore pre/post full repository validation, active classification/scope synchronization and a main merge remain pending. The earlier remote `planning/m2-design-records` branch was observed and left untouched; it does not replace the current planning record.

This directory is review material: the README is informative, the probe is experimental verification, and reports preserve bounded evidence. These dispositions must be reconciled with active manifests before main integration; no automatic normative promotion is intended.

**Next substantive action:** Specify the narrow packet-to-value input boundary and its compatibility facade using these findings, starting with preserved signature fields and explicit rejection of lossy inputs. Complete remaining consumer discovery before approving standalone membership, closure or writer changes. Continue independent design work while full-checkout integration prerequisites remain unresolved.
