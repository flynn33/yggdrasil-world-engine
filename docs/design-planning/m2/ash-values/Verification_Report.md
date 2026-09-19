# Two-Value Contract — Verification Report

**Date:** September 18, 2026  
**Candidate:** YWE-ASH-VALUES-20260918-1  
**Overall result:** All ten experimental check groups passed in three runs.  
**Meaning:** The draft rules, experimental schemas, and verification model agree on the tested scope. The project repository has not been changed.

## In plain language

The previous packet description accepted incorrect data because it mostly described rules rather than enforcing them. This experiment supplies working candidate checks for just two small value types.

The checks accept every correctly formed nine-bit state. They recognize exactly the sixteen allowed codewords and reject the other 496 patterns when a codeword is required. A message claiming membership does not bypass that check.

The transformation tests also confirm that applying an allowed codeword gives the expected nine-bit result without changing the original value. Applying it twice restores the original value.

## Results actually executed

| Check | Observed result |
|---|---|
| Schema/fixture setup | One complete schema resource and seven definitions pass meta-schema checks; all 56 named fixtures are bound |
| Named fixtures | 13 accepted and 43 rejected as expected; intended rejection reasons verified |
| Source enumeration | Sixteen members match independently computed closure of the four pinned generators |
| Codeword subgroup check | All 256 pairs remain in the pinned set under XOR |
| State coverage | All 512 state records and 512 state signatures accepted |
| Codeword coverage | All 512 candidate vectors checked: exactly 16 accepted and 496 rejected |
| Value round trips | 512 states and 16 codewords survive write/read without changing value |
| Transformations | All 8,192 state/codeword pairs agree with a separate integer-XOR calculation |
| Reversibility and input preservation | All 8,192 transformations return to the original value when repeated; original inputs unchanged |
| Raw JSON cases | 12 specified cases behave as expected, including exact decimal values, duplicate keys and malformed text |
| Tool safety | Invalid UTF-8 and a verification-only oversize input reject |
| Ownership/order | 12 checks cover defensive copying, immutable fields, construction, operand types and sequence preservation |
| Root dispatch | 41 record cases checked; record-specific consumers must use their specific schema target |
| Deliberately broken schemas | All ten injected faults caught by the fixture suite |
| Offline resolution | Normal validation made zero external retrieval attempts; an intentionally unresolved reference was blocked locally |
| Repeatability | Three runs with hash seeds 0, 17 and 71 produced identical source-bound result sections |

Counts describe different, overlapping checks. They are not a project-completion percentage or a claim that every engine behavior was tested.

## Important edge cases covered

A state with its ninth coordinate set to one is accepted as a represented state but is not a codeword. Correct length and even parity alone do not establish codeword membership. A false or incorrectly typed membership assertion is rejected, and a true assertion cannot rescue a nonmember.

JSON numeric `1.0` is treated as the value one, while `true` and `"1"` are not bits. A tiny fractional difference from one and a tiny nonzero value are preserved by the raw-text parser and correctly rejected rather than rounded into acceptance. Writers use integer tokens.

Signatures cannot contain spaces, a newline, Unicode lookalike digits, or extra characters. Sequence order and repeated codewords are preserved.

A generic root check may recognize a record as AshState even when a particular consumer wanted CanonicalCodeword. This is expected and documented, not hidden: consumers must bind the exact type-specific schema and decoder.

## Evidence

- `evidence/verification-initial.json` and corresponding log/exit code.
- `evidence/verification-repeat-17.json` and corresponding log/exit code.
- `evidence/verification-repeat-71.json` and corresponding log/exit code.
- `evidence/repeatability.json`.
- `fixtures/catalog.json`, `fixtures/instances.json`, and `fixtures/raw-json-cases.json`.
- `verification/value_model.py` and `verification/verify_contract.py`.

The reports record environment versions, input-file hashes, per-case results and error locations, and deterministic result hashes. The independently written coordinate-loop and integer calculations are algorithmic cross-checks within this review, not two independent reviewers.

## Limits

These are tests of an external review prototype. They are not tests of changed YWE production source, a complete native engine, the whole repository, operational admissibility, recovery, a generation pipeline, or physical hardware.

The candidate's serialization choices still require compatibility review and incorporation. The previous source pin, M0/M1 records, roadmap, runtime boundaries, and debt inventory are unchanged. No independent contract acceptance, realization preflight/delivery, milestone acceptance, commit, push, or release is claimed.

The previous environment's direct Git retrieval failed; it was not repeated unchanged. Current remote identity was read through the connected GitHub tool, not inferred from a local checkout.

## Reproduction

Use the versions recorded in `verification/requirements.txt` in an approved testing environment. No dependencies were installed during this run.

```text
python verification/verify_contract.py --report evidence/local-new-run.json
```

Choose a new report filename: the runner deliberately refuses to overwrite earlier evidence. Exit code zero means all experimental groups passed. A nonzero result requires inspection; it does not authorize weakening a rule.
