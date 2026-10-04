# YWE normalization target policy

Policy ID: `YWE-NORMALIZE-LEXICOGRAPHIC-001`.
Policy revision: `1.0.0`.
Authority: downstream YWE policy; this is not an upstream ASH rule ID.

Given an immutable original AshState, the fixed canonical C16 relation and an
explicit complete available ValidityProfile, compute every recognized target in
the original's codeword orbit. Order that complete target set by ascending full
nine-character ASCII bit signature, without a distance heuristic or coordinate
privilege.

If the original is recognized by the profile, select the original unchanged,
including when a lower recognized signature exists in its orbit. Preserve the
complete target set and use an empty codeword sequence.

If the original is not recognized and the complete target set is nonempty, select
its first member. The plan contains exactly the one canonical full-vector codeword
original XOR selected target. Application must compute that actual XOR and
re-diagnose the actual result as VALID under the same immutable source/profile
before it can publish normalization success.

If the complete target set is empty, no normalization target is selected. Rejected
input or unavailable evaluation blocks planning and must not be described as a
completely evaluated empty set. Preserve the original input evidence and any
already parsed well-formed state.

Planning and target selection alone do not execute a correction, acknowledge a
diagnostic, classify an operational system as STABLE, publish an active state or
prove successful recovery. Application revalidates the original diagnosis, bindings,
complete target set, selection and codeword before use.
