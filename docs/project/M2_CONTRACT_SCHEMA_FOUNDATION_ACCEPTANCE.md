# M2 contract and schema foundation acceptance

M2: ACCEPTED

Tested implementation revision: `4d6af228da3c95bcd082fc8f18faaf153aeb723a`.
Normalized source-state digest: `180749b46a87cc2139242e4aa24557ed9d716a5890df3b1be06bf92e5ae03dd3` (sha256_sorted_path_nul_normalized_utf8_lf_sha256_nul; 1156 files).

The paired machine-readable record preserves the actual clean, unfiltered, offline local repository execution, the actual formation judgments, and the complete lifecycle and validation-method results. The immutable introduction is verified by `scripts/check_m2_historical_acceptance.py` under YWE-REQ-0037.

The captured full suite passed all 36 applicable checks, with zero blocking failures and zero advisory check failures. The evidence report hash is `9b3652d2965a3ad9a4776345dae3fad4c7728fda8a51d2edd55df481e1d52df0`.

The source-state digest excludes only `data/governance/m2_acceptance_evidence.json` and this document. All other tracked source content and modes must match the tested implementation at introduction. Later repository development does not change this historical evidence.

Formation executed C1–C6 and D1–D7. Its D8 remains unverified until the immutable introduction is established. The recorded D8 acceptance judgment uses that introduction as its basis; catalog success alone does not discharge it.

- **M2-C1** — Every normative schema passes its meta-schema. Basis: actual formation pass; `/formation_report/criteria/0`.
- **M2-C2** — Every reference resolves without a network dependency. Basis: actual formation pass; `/formation_report/criteria/1`.
- **M2-C3** — Every normative fixture is bound to a schema. Basis: actual formation pass; `/formation_report/criteria/2`.
- **M2-C4** — Every reject fixture fails for its intended requirement. Basis: actual formation pass; `/formation_report/criteria/3`.
- **M2-C5** — The schema-quality debt inventory is empty. Basis: actual formation pass; `/formation_report/criteria/4`.
- **M2-C6** — A roadmap-derived M2 acceptance gate passes from a clean offline checkout. Basis: actual formation pass; `/formation_report/criteria/5`.
- **M2-D1** — One JSON Schema 2020-12 profile, URI namespace, catalog, and offline resolver. Basis: actual formation pass; `/formation_report/deliverables/0`.
- **M2-D2** — Convert descriptive schema-named records into schemas or rename them by their actual role. Basis: actual formation pass; `/formation_report/deliverables/1`.
- **M2-D3** — Common identifier, reference, version, time, ordering, request, result, event, provenance, diagnostic, error, transaction, compensation, idempotency, retry, extension, and deprecation contracts. Basis: actual formation pass; `/formation_report/deliverables/2`.
- **M2-D4** — YAML structural schemas. Basis: actual formation pass; `/formation_report/deliverables/3`.
- **M2-D5** — Explicit fixture catalog mapping schema, instance pointer, expected result, and expected requirement or error identifiers. Basis: actual formation pass; `/formation_report/deliverables/4`.
- **M2-D6** — Positive, boundary, reject, recovery, replay, and migration fixtures. Basis: actual formation pass; `/formation_report/deliverables/5`.
- **M2-D7** — Meta-schema, instance, reference, identifier, dependency, negative, property, and mutation validation. Basis: actual formation pass; `/formation_report/deliverables/6`.
- **M2-D8** — Roadmap-derived M2 acceptance gate and durable acceptance evidence. Basis: immutable introduction; `/source_state`.

Lifecycle scope is `schema_validation_operation`; method scope is `schema_validation_foundation`. These operations establish validation recovery, replay, and protected proof reconstruction. They do not claim domain runtime rollback or simulation execution.

Historical replay uses the prepared current runtime without network access. The original four tool versions are preserved in the machine-readable record; the verifier does not install or recreate a historical runtime.
