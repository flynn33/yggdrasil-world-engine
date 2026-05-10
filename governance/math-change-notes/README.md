# Math Change Notes

This directory holds the change notes that the Math Integrity Agent requires when any math-critical file in the canonical ASH Pattern System repository is edited.

See `governance/github-agents-governance.md` for the agent's full policy and for the current list of math-critical paths.

## When a note is required

A math-change note must be committed **in the same push or pull request** as any edit to a file in the protected math-critical set. Editing a math-critical file without a corresponding note will fail the Math Integrity Agent whenever that workflow runs in blocking mode.

## Required note structure

Every note in this directory (other than this README) must contain all three of the following headings, in any order:

```text
## What changed
## Why
## Baseline preservation statement
```

The Math Integrity Agent's check is literal: each heading string must appear verbatim.

## Suggested filename convention

Filenames are not enforced by the agent, but the recommended convention is:

```text
YYYY-MM-DD-short-slug.md
```

## Human review on pull requests

When a math-critical edit is proposed via a pull request, the Math Integrity Agent additionally requires one of the following labels on the PR before it will pass:

- `math-reviewed`
- `human-reviewed`
- `baseline-approved`

## Scope boundary

A math-change note exists only to document what changed in the locked canonical baseline and to record human sign-off. It is not a design document or a specification. Canonical changes still belong in the appropriate file under `specs/`.
