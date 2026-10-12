# M3 unit evidence and acceptance instruction — proposed for review

This instruction is a proposal for the remaining M3 work. It grants no runtime,
conformance, roadmap completion, or publication claim. The primary checkout is
frozen at c468b35439e2b0254a71b22be3117a711f557b9b during its clean full run.

The observed catalog executes Python unittest discovery over every test_*.py
under tests. The existing repository report records return codes, revision,
catalog hash, clean state, and offline Git restriction; it does not record each
test's outcome. check_specification_roadmap.py pins the current catalog command.
check_m2_historical_acceptance.py reads its immutable historical catalog and
schema from the historical Git snapshot. These are separate current and
historical contracts.

## Authorized scope after review and adoption

Root owns scripts/run_validation_unit_tests.py, scripts/check_m3_acceptance.py,
their narrow tests, explicit schemas and fixture/catalog registrations, and the
current canonical runner/roadmap command integration. Core owns its existing
planned conformance test and invariant mapping. Root and Core agree the exact
mapping before implementation. Product owner authorization already covers M3.

The recorder MUST retain standard unittest discovery, order, fail/error/skip,
expected-failure/unexpected-success, subtest, setup/teardown, cleanup, and exit
semantics. It MUST run the same unfiltered discover('tests', pattern='test_*.py')
suite once through TextTestRunner and the installed unittest.TestProgram CLI
semantics, including the installed version's zero-test exit code. It MUST NOT nest exhaustive invariant tests
inside a separate discovered conformance or acceptance test. [YWE-REQ-0051]

The recorder MUST seed every discovered case as NOT_RUN and observe actual
TestResult start/stop and outcome callbacks. Failed subtests MUST fail the parent
case; class/module setup errors MUST remain visible even when no case starts.
Skipped, expected-failure, unexpected-success, duplicate, missing, interrupted,
or unavailable mapped cases MUST NOT count as passing evidence. [YWE-REQ-0051]

Source receipts MUST use the explicit repository-relative file, direct class,
and method selector. Body hashes MUST match the reviewed algorithm: UTF-8 text
with universal newline normalization, ast.parse, direct ClassDef/FunctionDef,
ast.get_source_segment for the FunctionDef, SHA-256 of its UTF-8 bytes, without
an added newline and excluding decorators. Whole-source LF hashes, starting
line, actual runtime selector, and before/after source equality MUST also be
recorded. Missing or ambiguous source MUST remain unavailable. [YWE-REQ-0051]

When a repository report is requested, the canonical validator MUST supply an
external unit-receipt path to the recorder and bind the unit result row to the
receipt's actual bytes/hash and complete runner transcript/hash. The validator
MUST capture and tee both actual stdout and stderr for the complete unit process,
including discovery/import output, test prints and the final summary; a hash of
TextTestRunner's summary stream alone is insufficient. The actual
command MUST be registered exactly in the current check catalog and roadmap
validator. No report request MUST manufacture a receipt. Existing report fields
and historical reports MUST remain accepted unchanged; an optional closed unit
evidence branch extends only current evidence. [YWE-REQ-0051]

The recorder MUST write an incomplete receipt before execution and mark its
child execution complete only after execution and source/revision/state readback
succeed. The parent validator MUST close its separate unit evidence only after
process return, transcript closure and both actual byte hashes succeed. Joint
acceptance MUST require both completions. A receipt inside the checkout MUST be visible as dirty and
cannot establish clean acceptance. Exceptions or changed revision/source MUST
leave evidence incomplete or explicitly failed. No credentials, external
services, new test framework, or dependency are involved. [YWE-REQ-0051]

The acceptance evaluator MUST preserve the exact seven M3 deliverables and five
exit criteria from the machine roadmap, all 28 canonical invariant IDs and
their actual statements/criteria/sources, all five canonical categories, and
every canonical per-module contract. It MUST consume actual matching completed
clean repository and selected-case evidence. It MUST recompute reviewed source
and mapping hashes, reject missing/failed/skipped/stale/reordered/filtered
evidence, and retain every unmet obligation. A name, aggregate test count,
placeholder reclassification, or authored specimen cannot prove conformance.
No partial conformance judgment is permitted. [YWE-REQ-0051]

The public evaluator seam is build_report(root, repository_report,
conformance_report), returning a plain bounded report. The conformance input is
executed per-case evidence, not an accepted assertion that all cases pass. The
CLI takes [root], --check-definition, --repository-report FILE,
--conformance-report FILE, --check-historical, and --output FILE. --check-definition validates
definitions and exact selectors without claiming execution or completion.

Root MUST bind final module/deliverable/exit coverage to actual read test bodies
and their source receipts after the implementations exist. No pending selector
or review-only proof grants acceptance. The accepted implementation revision
MUST pass the full ordinary repository suite in a clean offline checkout before
durable M3 acceptance publication. README and machine/document roadmap status
MUST continue to show M3 in progress until this evidence exists. M4 remains
unstarted, and the owner-requested pause follows completed M3 publication.
[YWE-REQ-0051]

## Narrow verification and review obligations

Recorder controls use small independent temporary test suites: pass, failure,
error, skip, expected failure, unexpected success, zero discovery, failed subtest, setupClass
failure with NOT_RUN cases, duplicate identity, source/body changes, interrupted
or missing final capture, and discovery/ordinary-run equivalence. Acceptance
controls mutate exact evidence fields: absent or filtered repository report,
dirty checkout, wrong revision/catalog/source/body/map, missing or duplicate
cases, non-pass statuses, missing category/module/roadmap obligation, and false
summary. Existing M2 evidence/report tests verify historical compatibility.

Reviewed implementation shape: the wrapper delegates CLI discovery/run/exit to
the installed unittest.TestProgram. A narrow subclass seeds its already loaded
suite immediately before super().runTests; it does not perform a second
discovery. The actual TextTestResult callback subclass records case outcomes.
For a requested repository report, the parent canonical validator streams the
unit process's combined stdout/stderr to its original output and an external
transcript, closes that transcript after the process returns, and binds both
the child's complete case receipt and the parent's transcript in the unit row.
This avoids a circular transcript hash inside output that changes its own hash.
Without a report request the normal inherited-stream path remains available.

Final acceptance consumes the already-executed exhaustive cases; it does not
run them again. No implementation starts from this proposal before the scoped
instruction accuracy and source-understanding review is complete.

## Actual runtime method binding clarification

Independent implementation review reproduced a PASS callback after replacing a
direct test method with a no-op while its original failing AST body and source
hashes remained unchanged. Case evidence therefore additionally records
`runtime_body_verified`. The recorder compiles the complete read source without
executing it, identifies the direct class/method code, and observes actual entry
into matching method code during the case. It immediately restores the previous
profile callback once that entry is observed; a displaced or unavailable observer
cannot establish body execution. Original unittest outcomes remain unchanged.
A wrapper grants body evidence only when the actual reviewed direct method code
enters. A mapped PASS requires this execution fact and no source error alongside
the original exact before/after receipts and actual callbacks. Filename, method
name, source hash or `inspect.unwrap` alone is insufficient. [YWE-REQ-0051]

## Durable publication after the executed implementation

The M3 verifier MUST also verify a closed pending/pass acceptance record. Pending
records discharge no obligation. A pass record MUST name the actual tested
implementation revision, its complete tracked source digest, and four immutable
byte archives: the actual repository report, child case receipt, parent transcript
and resulting CONFORMANT acceptance report. The first accepted introduction MUST
be a direct child of that tested revision and change only the fixed evidence
record, acceptance document and four archives. Every other tracked byte and file
mode MUST retain the tested source identity. [YWE-REQ-0051]

Historical verification MUST read local Git objects, verify the first accepted
introduction and every later evidence change, verify all archive byte lengths and
hashes, and evaluate the tested revision's own acceptance implementation in a
clean offline local snapshot. This replay consumes the archived receipt and
transcript against their original parent hashes; original external path strings
remain captured labels and need not exist on another host. It MUST NOT execute
unit tests or regenerate exhaustive proof. Its recomputed report MUST equal the
archived actual CONFORMANT report. The normal definition gate MUST verify this
durable record, and completed M3 MUST reference its exact evidence record and
acceptance document. README completion and the owner-requested pause follow this
verified immutable introduction. [YWE-REQ-0051]

The optional keyword-only archived_unit_evidence argument on build_report is
the historical worker's exact (child_receipt_bytes, transcript_bytes) pair. It
MUST preserve every original execution, revision, source, mapping, callback and
parent-hash check; it substitutes only byte retrieval for captured external path
lookup. A supplied pair is neither an assertion of acceptance nor a capability.
[YWE-REQ-0051]
