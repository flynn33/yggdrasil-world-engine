from __future__ import annotations

import unittest

from core.ash_pattern_engine import (
    build_cosmic_pattern_snapshot,
    encode_realm_identity,
    encode_state_identity,
    plan_generation,
)


class AshCanonicalIdentityTests(unittest.TestCase):
    def test_state_identity_uses_vertex_id_and_preserves_legacy_aliases(self) -> None:
        identity = encode_state_identity("100000000")

        self.assertEqual("100000000", identity["state_signature"])
        self.assertEqual("ash_state_100000000", identity["vertex_id"])
        self.assertEqual(identity["vertex_id"], identity["realm_id"])
        self.assertEqual(identity, encode_realm_identity("100000000"))

    def test_different_states_have_different_vertex_identities(self) -> None:
        first = encode_state_identity("000000000")
        second = encode_state_identity("000000001")

        self.assertNotEqual(first["vertex_id"], second["vertex_id"])

    def test_snapshot_exposes_equal_canonical_and_compatibility_fields(self) -> None:
        snapshot = build_cosmic_pattern_snapshot("100000000")

        self.assertEqual(snapshot["state_identity"], snapshot["realm_identity"])

    def test_plan_exposes_equal_canonical_and_compatibility_fields(self) -> None:
        plan = plan_generation(
            project_name="identity-contract-test",
            seed_state="100000000",
            transition_codewords=["000011110"],
        )

        self.assertEqual(plan["source_state_identity"], plan["source_realm"])
        self.assertEqual(plan["destination_state_identity"], plan["destination_realm"])
        self.assertEqual(
            plan["destination_state_identity"],
            encode_state_identity(plan["normalized_state"]),
        )


if __name__ == "__main__":
    unittest.main()
