# Adopted N3 session lifecycle contract companions

The [lifecycle contract](../../../architecture/m3_session_lifecycle_contract.md)
and [independent safety policy](../../../architecture/m3_session_lifecycle_policy.md)
were adopted on October 11, 2026 before dependent implementation under
YWE-REQ-0044 and ADR-0033. M3 remains active. Adoption and the representation
controls below do not establish N3 runtime acceptance.

[BUSINESS_API_INVENTORY.json](BUSINESS_API_INVENTORY.json) defines the 38 closed
business types, 35 ports, finite domains and planned runtime allocations.
[SAFE_FIELDS_AND_LIMITS.json](SAFE_FIELDS_AND_LIMITS.json) defines the safe
supporting graph. [CAPACITY_AND_RETENTION.md](CAPACITY_AND_RETENTION.md) connects
that graph to actual admission, once completion, final observation and retention
obligations. Its observed implementation boundaries name the preparation
revision; they do not describe unimplemented N3 behavior as already present.

[ARTIFACT_INDEX.json](ARTIFACT_INDEX.json) records the frozen external proposal
hashes, reconciled adopted policy and inventory hashes, and exact repository
artifact hashes. The adopted policy hash includes its actual adopted status;
the frozen proposal bytes remain preserved separately. ADR-0034 adopts the
closed fresh-origin failure amendment before its dependent implementation.
ACTUAL_READ_SOURCE_HASHES.json now names normalized committed cdbcb68 source
blobs; the preceding checkout-byte hashes remain in the base commit and
external adoption receipts. Current runtime edits are excluded from this proof.
The adopted artifact hashes and byte lengths use UTF-8 without a BOM and LF
line endings, matching committed Git blobs. Normalize checkout line endings
before comparing them; the frozen proposal hashes retain their original bytes.

The portable controls are `replay_independent.py`, `generate_graph_control.py`
and `raw_business_guard_controls.py`. Run them in a fresh external copy of this
directory with Python 3.12.10. They regenerate structural maxima, the distinct
key index and compact JSON sizing controls. Compare the outputs with the
indexed repository reports. The controls do not exercise session admission,
state publication, capture acknowledgments, concurrency or native storage.
Their synthetic values and storage status labels are representation specimens,
not accepted semantic lifecycle packets.

The calculated ordinary and terminal bounds are 324,066 and 645,088 bytes,
within fixed 327,680 and 655,360 byte reservations. Existing retained and
reserved collector capacity can still refuse admission. No automatic purge,
capacity increase or shortened history makes an operation fit.
