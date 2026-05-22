# Governance Documentation Index

Project: Yggdrasil World Engine
Status: active governance index
Current baseline: `v2.0.16`

## Purpose

Governance documents describe how the repository preserves architecture
authority, contributor workflow, discussion policy, automation, validation, and
Forsetti-aligned lifecycle rules.

## Documents

| File | Role |
|---|---|
| `forsetti_governance_alignment.md` | Maps YWE truth ownership to Forsetti-compatible governance boundaries. |
| `github_automation_agents.md` | Documents repository workflow automation and validation responsibilities. |
| `discussion_moderation_policy.md` | Defines GitHub Discussions moderation policy and enforcement scope. |

## Workflow Entry Points

| Workflow | File |
|---|---|
| Main validation | `../../.github/workflows/main-ci.yml` |
| Repository guardrails | `../../.github/workflows/ywe_repository_guardrails.yml` |
| Forsetti compliance | `../../.github/workflows/forsetti-compliance.yml` |
| Wiki sync | `../../.github/workflows/wiki-sync.yml` |
| Version and changelog | `../../.github/workflows/versioning.yml` |
| Discussion routing | `../../.github/workflows/discussion-agents.yml` |
| Discussion moderation | `../../.github/workflows/discussion-moderation.yml` |
| Discussion topic seeding | `../../.github/workflows/discussion-topic-seeder.yml` |
| Contributor identity gate | [`../../.github/workflows/no-ai-contributor-agent.yml`](../../.github/workflows/no-ai-contributor-agent.yml) |

## Governance Rules

- Forsetti governs module lifecycle, activation policy, and structural
  consistency.
- YWE governs cosmology truth, source-truth hierarchy, runtime contracts, and
  domain meaning.
- ASH Pattern System remains a YWE component for diagnostics, recovery,
  containment, conformance, code resilience, update safety, and patch stability.
- Automation may validate, sync, seed, and moderate within documented
  boundaries; it does not invent canon or bypass accepted package gates.
