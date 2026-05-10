# Materialization Boundary

YWE preserves the ASH materialization boundary: `GenerationPlanner` emits a
side-effect-free `GenerationPlan`; `ArtifactEmitter` and host adapters may
materialize only from that plan. Adapters do not own ASH truth.

Unity, Unreal, Godot, and any future host adapter must preserve
`CosmicPatternSnapshot`, `DiagnosticEnvelope`, and `generation_plan_ref`
provenance. Adapters must not author ASH state, codewords, diagnostics,
cosmology, myths, prophecies, character meaning, or YWE domain truth.
