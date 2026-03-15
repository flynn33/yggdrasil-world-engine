# GitHub Automation Agents

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: expanded automation governance baseline

## Purpose

This document describes the GitHub automation added to this repository for release governance, design validation, and Forsetti-aligned repository enforcement.

## Release Governance Agent

The release-governance workflow is responsible for:
- maintaining `VERSION`
- prepending entries to `CHANGELOG.md`
- syncing selected repository docs into the GitHub wiki when the wiki is available

Versioning policy:
- `BREAKING CHANGE` or `!:` bumps major
- `feat:` bumps minor
- all other pushed commits bump patch
- `[skip version]` or `[skip release]` disables the automatic bump for that push

## Forsetti Compliance Agent

The compliance workflow validates that pushed changes still respect the repository's Forsetti alignment rules.

It checks:
- required governance and architecture docs still exist
- every core and feature runtime folder still has a Forsetti manifest template
- manifest templates keep required fields and do not request `ui_theme_mask`
- core runtime dependencies do not point at feature modules
- feature runtime dependencies point only at core runtime modules
- adapter capability profiles preserve their non-truth-owning host-bridge role

## Wiki Sync Behavior

The wiki sync step updates a curated set of wiki pages from repository sources. If the GitHub wiki is not enabled, the sync step exits cleanly without failing the workflow.

## Source Completeness Agent

The source-completeness workflow refreshes `docs/handoff/missing_source_documents.md` from the tracked placeholder inventory in `SOURCE_AVAILABILITY_MANIFEST.md`.

It:
- preserves the manually authored context in the report
- regenerates the `Intentional Placeholder-Backed Artifacts` section from repository truth
- auto-commits the refreshed inventory on `main` when the placeholder set changes

## Schema Integrity Agent

The schema-integrity workflow validates canonical JSON contracts across `data/` with extra focus on `data/schemas/`.

It checks:
- file naming conventions for shared schema files
- required fields in player, prophecy, myth, pattern, quest, bloodline, and realm records
- placeholder expansion schema structure
- cross-file dependency references for shared schema expansions
- the ASH registry schema exists and the canonical family registries keep required fields, family values, ID prefixes, and allowed status values
- the canonical faction-topology schema exists in `data/faction_topology/` and preserves the required relational state surfaces
- the canonical module capability manifest schema exists in `data/module_capability/` and preserves delegation and truth-boundary rules
- the applied module capability manifests in `data/module_capability/manifests/` exist for the current core engines and feature modules and stay aligned with their Forsetti template module IDs
- the canonical lore files under `lore/wrw_cosmology/` and `lore/wolf_canon/` exist and preserve the corrected Dark Star, wolf-balance, and Trial of Return canon

## Module Contract Coverage Agent

The module-contract-coverage workflow validates that each planned runtime folder still carries the full documentation and contract scaffold expected for a code-agnostic design branch.

It checks:
- required core and feature runtime directories are present
- every runtime folder includes `README.md`, `module_description.md`, `schema_notes.md`, `engine_interface.json`, and `forsetti_module_manifest.template.json`
- special rule and schema companion files remain present where required
- contract markdown files preserve core sections such as Purpose, Inputs, Outputs, Dependencies, and Invariants

## Docs Link And Glossary Agent

The docs-link-and-glossary workflow validates repository documentation hygiene.

It checks:
- internal markdown links resolve
- sandbox-only handoff links do not remain in repository docs
- wiki sync mappings reference real source files and unique destination pages
- the design glossary still contains required canonical terms

## Architecture Drift Agent

The architecture-drift workflow guards against design changes landing without their companion documentation updates.

It requires related documentation updates when:
- runtime interface contracts or manifest templates change
- canonical schemas or realm registry files change
- applied module capability manifests change
- lore canon documents change
- faction topology schema files change
- core and feature rule files change
- adapter capability profiles change
- ASH foundation authority files or family registries change

## Canonical Truth Boundary Agent

The canonical-truth-boundary workflow enforces the split between YWE truth ownership and downstream host realization.

It checks:
- governance and architecture docs preserve the rule that Forsetti governs activation while YWE governs truth
- adapter profiles remain non-truth-owning downstream execution connectors
- adapter docs continue to describe host work as realization rather than canon authorship

## Discussion Response Agents

The discussion-response workflow routes new GitHub Discussions topics and new discussion comments to one of three repo-grounded agents:
- Technical Discussion Agent
- Support Discussion Agent
- Lore Discussion Agent

It works by:
- classifying each new discussion post or comment into technical, support, or lore scope
- searching only repository-tracked source material for matching information
- replying with file-grounded references from the repo when relevant sources exist
- falling back to `There is not information available at this time. Check back soon.` when the repository does not currently answer the question

Boundary rules:
- the agents respond only from repository truth and do not invent unsupported answers
- lore responses are grounded in canonical lore and master-spec surfaces
- support responses prefer README, guides, governance docs, and operating instructions
- technical responses prefer engine, module, schema, workflow, adapter, and architecture surfaces

## Discussion Topic Seeder Agent

The discussion-topic-seeder workflow scans repository truth on a schedule and opens category-level GitHub Discussions topics when equivalent seeded topics do not already exist.

It works by:
- reading repository-driven topic sources such as `wiki.md`, `.github/wiki-sync.json`, and `docs/architecture/README.md`
- deriving candidate topics from wiki sections, wiki-sync pages, and architecture headings
- classifying each candidate into the technical, support, or lore family using the same repo-grounded routing logic as the response agents
- selecting at most one new topic per family and at most three total topics per run
- creating discussions only when the seeded topic marker or exact topic title is not already present on the discussion board

Boundary rules:
- generated topics must be derived from repository truth, not invented freeform prompts
- topic bodies must point back to the repository source path and include a repository-grounded summary
- when no new seeded topics are needed, the workflow exits without creating anything

## Discussion Moderation Agent

The discussion-moderation workflow enforces the repository code of conduct on GitHub Discussions content.

It works by:
- moderating newly created or edited discussions and discussion comments
- rescanning recent discussion content on a six-hour schedule
- deleting discussion threads or comments that match the repository moderation policy
- logging moderation incidents to a repository-owned issue for maintainer review
- attempting user blocking for severe violations only when an owner-supplied admin token is available

Boundary rules:
- the moderation rules come from `CODE_OF_CONDUCT.md` and `docs/governance/discussion_moderation_policy.md`
- the bot removes content rather than rewriting it in place
- owner reporting stays inside the repository issue tracker
- automated blocking is best-effort only and requires `DISCUSSION_MODERATION_ADMIN_TOKEN`

## No AI Contributor Agent

The no-ai-contributor workflow protects repository attribution hygiene.

It checks:
- pushed and pull request commit authors do not use blocked AI identity terms
- committers do not use blocked AI identity terms
- commit messages do not include `Co-authored-by` trailers for blocked AI identities
- infrastructure bots remain allowed unless they present themselves as blocked AI contributors

## Release Readiness Agent

The release-readiness workflow is a final gate for tagged or manually requested release checks.

It verifies:
- version and changelog state are coherent
- the missing source inventory is current
- wiki sync configuration is intact
- the repository passes the Forsetti, schema, module, docs, truth-boundary, and contributor-identity checks

## Operating Notes

- workflow-authored commits use `github-actions[bot]`
- automation commits that should not cause release bumps include `[skip version]`
- validation agents fail fast when design structure drifts; they do not invent or rewrite canon on their own
- discussion agents answer from repo truth only; when the repo has no answer they must use the configured fallback response
- discussion moderation removes violating discussion content and records the action for maintainer review
