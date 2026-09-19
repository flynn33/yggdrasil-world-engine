# Repository Integration Requirements

**Current status:** Administrative consolidation and owner-completed branch cleanup are complete. One reviewed-report discovery defect is now corrected and tested. Classification/scope and complete repository verification remain outstanding.  
**Integration baseline:** `7aa5c1b18caf37bb01ca3bdfb0d73b59f8261009`.  
**Original main baseline:** `2db1230f638cd065d791c05f1adb7b4b51505c57`.  
**Current authority:** [Project Record](../Project_Record.md).

## Completed repository consolidation

Both planning histories were preserved by reconciliation commit `13ee11704691b1c562e8e0099ca2b2e4533cb39e` and included in main. The owner subsequently removed the redundant branch names. Post-deletion ancestry checks and a fresh branch enumeration establish preservation of both known tips and the single-main state. Older no-merge and pending-deletion statements are historical, not unfinished current work.

The owner now explicitly prefers working branches, with merge/preservation and cleanup included when work is finished. This supersedes the earlier blanket no-new-branches interpretation. It does not require recreating deleted branches or leaving another completed branch behind.

## Completed discovery repair — September 19, 2026

The filename heuristic in `scripts/check_machine_readable_artifacts.py` treated the following diagnostic reports as schema-named documents without declarations:

| Preserved path relative to `docs/design-planning/m2/readiness/evidence/` | Verified Git blob | Complete JSON-value SHA-256 |
|---|---|---|
| `schema-readiness.json` | `7aa1d9844ebb6f9596cac64f6253b420d53a6bcb` | `3acefb7e8252bada9dc0403af05e0649f1740d10dca599417bba81a572b2e751` |
| `schema-readiness-final.json` | `f1ac159e3502dde0699a75f0c86f2fca1f48f127` | `9a1a3344a8566e70075882e91576d292f207a1c44f4b51c54a697dba9f492ee7` |
| `schema-readiness-repeat-initial.json` | `9b03a60c123f21f47bdcf4a5421cce6ac059a3c6` | `7fd57ee86274a17d33e20e52bbc862f531c0406841e43dc3e176a827bb82494f` |

These files contain recorded observations, input instances, schema-validation messages and stated limitations. They are not schema declarations. Their complete archived bytes matched the current Git blob identities before testing. No report was renamed or edited.

`ReviewedDiagnosticReports` owns a read-only exact-path/fingerprint registry used solely to disambiguate the schema-name heuristic. Fingerprints use `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` encoded as UTF-8 and SHA-256. This is an evidence comparison convention, not the engine's wire format.

Recognition requires the reviewed path, report type, absence of root schema declaration/constraint keywords, and the complete value fingerprint. Different paths, label-only claims, changed metadata or nested results, invalid values, and actual schemas are not exempt. JSON whitespace and member order alone do not change the fingerprint. Future or changed reports require another review; the directory is not a general exclusion. This narrow snapshot registry does not replace the still-required artifact-role inventory.

All ordinary JSON/YAML parsing and declared-schema, reference and duplicate-identifier checks still run. The other debt categories are unchanged. The registered `schema_quality_baseline.json` was not edited. This repair does not close any of its real M2 debt entries or establish primary artifact classifications.

## Executed verification

**Host:** Python 3.13.5; Linux-6.18.44-x86_64-with-glibc2.41; jsonschema 4.26.0; PyYAML 6.0.3. Verification dependencies are not new product/runtime dependencies.

**Source identity:** Original checker blob `9047aa75eb539a4ffefcfca2ccf462125dbaa4f9`; original test-file blob `c60b84209d74e6e8c1cf52f050fd310a3398a7da`. Both were reconstructed completely and hash-verified. This selected-file recovery is not a full checkout or an inspection of owner-local work.

| Check | Expected and observed result |
|---|---|
| Original `MachineArtifactTests` | Four tests pass unchanged. |
| Original CLI with three reports and an empty synthetic debt baseline | Exit 1; all three report paths reported as unregistered schema-name debt. |
| Revised CLI against that same disposable fixture | Exit 0; no schema-name debt. This is a fixture result, not the repository's debt count. |
| Four original plus sixteen new regression tests | 20 pass, zero failures/errors/skips, in each of two runs with hash seeds 17 and 71. |
| Actual CLI on malformed schema, unresolved local reference, duplicate identifier, changed/copied report, malformed JSON and duplicate YAML fixtures | Each rejects the intended invalid condition. |
| Bypassed content fingerprint mutation | Detected: seven failing tests, zero errors. |
| Removed report recognition mutation | Detected: three failing tests, zero errors. |
| Disabled meta-schema validation mutation | Detected: one failing test, zero errors. |
| Preservation | Original report bytes unchanged; all pre-existing test classes and unaffected checker functions structurally unchanged. |

The passing runs were recorded at `2026-09-19T16:05:36.356937+00:00` and `2026-09-19T16:06:10.422573+00:00`; their test-result and CLI-result sections agree. The combined mutation command reached its execution limit before completing its final report. The final mutation was rerun separately and completed with the expected failing assertion. Mutation failures are evidence that the regression tests detect faults, not failures of the delivered code.

Tests were executed by exact AST extraction of `MachineArtifactTests` and `ReviewedReportDiscoveryTests` into a namespace with the actual checker module and standard test dependencies. Unrelated test-module imports were unavailable. This did not execute the complete test module, test catalog, or repository suite. The real checker CLI was executed as a subprocess against disposable fixtures; no mocked checker result is presented as a CLI result.

Implementation SHA-256: `c1aa14f32549da6d3cec6324555d30b2d0ff4d726ca60e6b5d3f84ca91098cf5`.  
Updated test-file SHA-256: `7e09ce5bf27392119d2e14da1429a032a7a566c546262126a78072767a0b2d0e`.

The initial repeated runs used test-file hash `8188f73a63d3f091e12d2f7e55f002cdc761b29e8310705c317788d689c22665`. The uploaded test file has whitespace-only changes in existing tests; its entire parsed syntax tree is identical. The final uploaded bytes were matched to Git blob `f2f51f7b9d4cebfd30986c0bab60c9c8b52df4a1` and the 20 focused tests were rerun successfully at `2026-09-19T16:16:34.078096+00:00`.

### Reproduction from a complete checkout

With the repository's existing validation dependencies installed, run the two focused classes directly:

```sh
python tests/test_validation_foundation.py MachineArtifactTests ReviewedReportDiscoveryTests
```

This normal entry point additionally imports the rest of the test module; it was not available in the selected-file execution environment. Full integration still uses:

```sh
python scripts/validate_repository.py --context local
```

No successful full-catalog result is claimed. The new tests live in the existing validation-foundation test file, not in a separate unregistered test path. No repository file was added, removed or renamed by this maintenance slice.

## Outstanding technical work

1. Obtain a verified full current source snapshot; distinguish it from the owner's uninspected checkout and preserve any owner-local changes. Do not substitute an older archive or call remote metadata a local checkout.
2. Reconcile the primary classification/scope manifests and exact path snapshots for all planning material. Use appropriate informative/example/historical roles; the normative catch-all is not candidate approval. This reviewed-report repair is not completion of that work.
3. Complete remaining schema/fixture discovery and experimental-boundary review. Keep actual schemas subject to validation, preserve original evidence, and distinguish experimental catalogs from production registration. Do not grow known debt silently or weaken actual validation to make a report look successful.
4. Capture current catalog results and compare with the original main baseline when reproducible. Separate inherited failures from planning-integration regressions. A new baseline run is not evidence that a pre-merge run previously occurred. Do not restore intentionally removed workflows or create runner spending to obtain an execution route.
5. Confirm accepted M0/M1 evidence, source pins, v2.0.23, M2 status, platform gates and candidate approval fields remain unchanged. Review the final diff and all relevant source/evidence hashes.
6. Use the owner's preferred bounded branch lifecycle when supported: review, merge/preserve useful work, verify the remote result, and clean up redundant refs. Do not invent deletion capability or change repository permissions/workflows to manufacture it. An unreferenced reviewed commit followed by an authorized non-forced main update avoids leaving an unmanageable remote branch in this environment.

## Evidence boundary

The earlier administrative merge did not satisfy these technical obligations. The present change closes only the described reviewed-report discovery subtask. Complete repository acceptance, candidate adoption, debt closure, independent realization review and platform qualification remain unclaimed. No coding-agent instruction package is issued by this document.
