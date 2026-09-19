# Two-Value Contract — Verification Report

**Candidate:** YWE-ASH-VALUES-20260918-1  
**Original experiment:** September 18, 2026.  
**Repository-layout verification:** September 19, 2026, 11:51:28 UTC.  
**Result:** All ten experimental groups passed; the complete result section equals the original recorded result section.

## What was checked

The candidate distinguishes a represented nine-bit state from a permitted transformation codeword. Its schema and verification-only object model agree on the tested construction and wire rules. This report does not approve those choices or claim that the official engine implementation uses them.

| Check | Observed result |
|---|---|
| Schema/fixture setup | One schema resource and seven definitions pass meta-schema checks; all 56 named fixtures are bound |
| Named fixtures | 13 accepted and 43 rejected as expected, with intended rejection reasons |
| Source enumeration | Exactly sixteen members match closure of the four pinned generators |
| Subgroup check | All 256 codeword pairs remain in the pinned set under XOR |
| State coverage | All 512 records and 512 signatures accepted as represented states |
| Codeword coverage | All 512 candidates checked: exactly 16 accepted and 496 rejected |
| Value round trips | All 512 states and 16 codewords preserve their values |
| Transformation | All 8,192 state/codeword pairs agree with a separate integer-XOR calculation |
| Reversibility and ownership | All 8,192 cases preserve inputs and return to the initial value when the same codeword is applied twice |
| Raw JSON | 12 cases, including exact-decimal differences, duplicate keys, malformed input, and ordinary whitespace |
| Tool safeguards | Invalid UTF-8 and oversize probe input rejected |
| Ownership/order | 12 checks of copying, immutable fields, guarded construction, typed operands, sequence order, and repetitions |
| Root dispatch | 41 record cases; a consumer must select its required type-specific schema |
| Deliberate faults | All ten introduced schema faults detected |
| Offline references | Zero normal external retrievals; an unknown reference fails locally |

These are overlapping test groups, not a completion percentage. The independent algorithms are cross-checks within the experiment, not independent reviewer acceptance.

## Preserved edge cases

The ninth coordinate may be one in a represented state; this does not make that state a codeword. Correct length or even parity alone does not establish actual membership. A false or incorrectly typed membership assertion rejects, and a true assertion does not rescue a nonmember.

Exact numeric values such as JSON `1.0` are accepted as one, but Boolean `true`, string `"1"`, and values with a nonzero fractional part are not bits. The raw reader preserves decimal precision, so a near-one fraction or a tiny nonzero value cannot become accepted through rounding. Writers use integer tokens.

Signatures reject spaces, newlines, lookalike digits, and extra characters. Sequence order and duplicate codewords are preserved. The root schema can accept either record kind; a codeword consumer must use the codeword-specific definition rather than infer its expected type from a generic pass.

## Evidence retained

The machine-readable [verification summary](evidence/verification-summary.json) preserves the actual environment, input-file hashes, group outcomes, full-report hashes, and deterministic result digest. It is explicitly a projection of the detailed report, not a claim that omitted per-case output is physically present here.

The complete detailed report is reproducible using [the verifier](verification/verify_contract.py), [the model](verification/value_model.py), and [the fixture bindings](fixtures/catalog.json). The result section has SHA-256:

`630cade04dadfc8ae236e34ffdcc1238703695b856b4d336fa0043d68d4ac113`

The original September 18 bundle recorded three equal runs with hash seeds 0, 17, and 71. During publication preparation, the original experiment was rerun, then the reorganized files were rerun, then the final compact-JSON layout was rerun. The final result section equals the original. Source file hashes differ where JSON whitespace was deliberately compacted; parsed values and result sections do not. Archive provenance and transformations are recorded in [the publication manifest](../../Publication_Manifest.json).

## Limits and incorporation

The original experiment was external to the product repository. This change stores it as a design experiment under the owner-approved planning directory; it does not install it as official engine code or the M3 oracle. Python and the recorded libraries are testing-only.

Consumer compatibility, classification/scope metadata, full repository regression, independent review, and affected method/realization prerequisites remain open. No operational admissibility, repair, recovery, generation pipeline, native platform, hardware, release, or M2 acceptance is established by these results. Accepted source pins, M0/M1 records, version, roadmap, and debt inventory remain unchanged.

## Reproduce

From this directory, use the testing versions in `verification/requirements.txt` and run:

```text
python verification/verify_contract.py --report evidence/local-new-run.json
```

Choose a new filename: the verifier refuses to overwrite existing evidence. Exit zero means all experimental groups passed. Inspect any failure rather than weakening the rules. No new dependency installation was required for the recorded publication runs.
