# Ash Value Contract — Planning Candidate

Read [the candidate contract](Ash_Value_Contract.candidate.md) and [its verification report](Verification_Report.md). The schema, model, fixtures, and reports were prepared for this two-value experiment. They are not active engine implementation or approved serialization requirements.

## Provenance

Candidate `YWE-ASH-VALUES-20260918-1` remains tied to product commit `2db1230f638cd065d791c05f1adb7b4b51505c57`. Original evidence is retained byte-for-byte. The candidate document has only a relative-reference correction pointing to the parent packet draft in `../readiness/`; no object rule was changed during placement.

Dates and environment paths in historical reports describe the original run, not a new execution. Historical archive paths in `source-register.json` identify members of the original conversation transport archive; that nested ZIP is deliberately not committed. `../../publication/File_Transfer_Manifest.json` preserves both archive identities and all transferred file hashes.

## Reproduction

The experimental runner reads the local schema and fixture catalogs. From this directory, run it in the approved test environment, using a new report path outside the checked-in evidence:

```text
python verification/verify_contract.py --report <new-output-path>/ash-values-report.json
```

Use the testing versions recorded in `verification/requirements.txt`; these are not application runtime dependencies. The runner refuses to overwrite existing evidence. A passing experiment is not a passing repository regression suite, compatibility review, independent approval, or M2 acceptance.

## Next design work

Check actual packet consumers before adopting required `membership: true`, closed records, precise numeric parsing, fixed writer output, or exact schema-target binding. Source/method and realization prerequisites remain separately tracked in the Project Record.
