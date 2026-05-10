# Diagnostics Conformance

YWE uses `DiagnosticEnvelope` as the required diagnostic record shape. State
diagnostics cite ASH rule IDs, preserve parent/root chain fields, and classify
state validity before downstream generation, recovery, containment, or safe
halt behavior.

Package rebuild interfaces require `diagnostic_ref` on character,
creature, quest, NPC, artifact, myth, prophecy, perception, faction,
worldstate, codex/lore, and realm-transition surfaces. Meaningful resolutions
that do not alter shared state must emit an explicit `DiagnosticNoOp` instead
of silently skipping the worldstate delta route.
