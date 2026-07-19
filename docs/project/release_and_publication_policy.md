# Release and Publication Policy

Status: current M0 governance authority
Machine-readable authority: `../../data/governance/release_publication_policy.json`

## Current State

The Yggdrasil World Engine agnostic specification is **unreleased**. There are
no GitHub Release objects and no agnostic specification releases. Repository
baseline `2.0.23` identifies the current repository state; it is not a
publication claim.

## Version Authority

`VERSION` is the canonical repository-baseline source. `version.txt` and the
version-bearing governance and documentation surfaces are synchronized mirrors.
A mismatch is a validation failure; a mirror does not override `VERSION`.

## Tags and Changelog

Existing `v2.0.x` tags identify repository baselines. A tag, including a
historical annotation that uses release wording, does not by itself publish the
agnostic specification or create a GitHub Release object.

`CHANGELOG.md` records repository history. Its `Unreleased` section records
pending repository changes, and its versioned headings record prior repository
baselines. Neither heading type independently establishes publication.

## Eligibility Gate

Publication eligibility is deferred until M10 is accepted and the roadmap's
release measures pass. Until then:

- publication state remains `unreleased`;
- release eligibility remains false;
- platform work remains unauthorized;
- branch names do not activate a platform implementation mode; and
- concrete platform products and adapters belong only in separately authorized
  downstream repositories after M10 acceptance.

Passing an earlier phase gate or roadmap milestone does not imply normative
completion, conformance completion, release readiness, or publication.

## Update Discipline

A future publication change must update the machine-readable publication
policy, roadmap publication state, repository status, and applicable release
evidence together. Creating a tag or changing changelog text alone is
insufficient.
