param(
  [string]$EventPath = $env:GITHUB_EVENT_PATH,
  [string]$EventName = $env:GITHUB_EVENT_NAME
)

$ErrorActionPreference = 'Stop'

$violations = New-Object System.Collections.Generic.List[string]

function Get-ChangedFiles {
  param(
    [string]$Path,
    [string]$Name
  )

  $revisionRange = $null

  if ($Path -and (Test-Path $Path -PathType Leaf)) {
    $event = Get-Content -Raw $Path | ConvertFrom-Json -Depth 32

    switch ($Name) {
      'pull_request' {
        $base = $event.pull_request.base.sha
        $head = $event.pull_request.head.sha
        if ($base -and $head) {
          $revisionRange = "$base...$head"
        }
      }
      'push' {
        $base = $event.before
        $head = $event.after
        if ($base -and $head -and $base -notmatch '^0+$') {
          $revisionRange = "$base..$head"
        }
      }
    }
  }

  if (-not $revisionRange) {
    git rev-parse --verify HEAD~1 *> $null
    if ($LASTEXITCODE -ne 0) {
      return @()
    }
    $revisionRange = 'HEAD~1..HEAD'
  }

  $files = git diff --name-only $revisionRange
  return @($files | Where-Object { $_ -and $_.Trim() })
}

function Test-MatchesPattern {
  param(
    [string]$Value,
    [string[]]$Patterns
  )

  foreach ($pattern in $Patterns) {
    if ($Value -like $pattern) {
      return $true
    }
  }

  return $false
}

$rules = @(
  [pscustomobject]@{
    Name = 'Runtime contract drift'
    Watched = @(
      'core/*/engine_interface.json',
      'modules/*/engine_interface.json',
      'core/*/forsetti_module_manifest.template.json',
      'modules/*/forsetti_module_manifest.template.json'
    )
    RequiredDocs = @(
      'docs/architecture/engine_interface_contracts.md',
      'docs/architecture/ywe_module_design_contracts.md',
      'docs/architecture/ywe_cross_module_dependency_map.md',
      'docs/governance/forsetti_governance_alignment.md'
    )
  },
  [pscustomobject]@{
    Name = 'Canonical data drift'
    Watched = @(
      'data/schemas/*.json',
      'data/*/*schema*.json',
      'data/realm_registry/realms.json'
    )
    RequiredDocs = @(
      'docs/architecture/ywe_canonical_data_domains.md',
      'docs/master_specification/YWE_MASTER_SPECIFICATION.md',
      'docs/glossary/ywe_design_glossary.md'
    )
  },
  [pscustomobject]@{
    Name = 'Rule-set drift'
    Watched = @(
      'core/narrative_engine/*.yaml',
      'modules/artifact_engine/*.yaml',
      'modules/creature_engine/*.yaml',
      'modules/myth_engine/*.yaml',
      'modules/prophecy_engine/*.yaml',
      'modules/quest_engine/*.yaml'
    )
    RequiredDocs = @(
      'docs/architecture/ASH_RUNTIME_GENERATION_FLOW_NOTES.md',
      'docs/architecture/NPC_SYNTHESIS_NOTES.md',
      'docs/architecture/PLAYER_ORIGIN_ARC_NOTES.md',
      'docs/architecture/WORLDSTATE_DELTA_RULES_NOTES.md',
      'docs/architecture/MYTH_EMERGENCE_RULES_NOTES.md',
      'docs/architecture/PROPHECY_ACTIVATION_RULES_NOTES.md',
      'docs/architecture/QUEST_CHAIN_TEMPLATE_NOTES.md',
      'docs/architecture/YWE_Myth_Emergence_Design.md',
      'docs/handoff/repo_implementation_mapping.md'
    )
  },
  [pscustomobject]@{
    Name = 'Adapter capability drift'
    Watched = @(
      'adapters/*/capability_profile.yaml'
    )
    RequiredDocs = @(
      'README.md',
      'docs/governance/forsetti_governance_alignment.md',
      'docs/architecture/ywe_invariant_guardrails.md',
      'docs/architecture/engine_interface_contracts.md'
    )
  }
)

$changedFiles = Get-ChangedFiles -Path $EventPath -Name $EventName
if ($changedFiles.Count -eq 0) {
  Write-Host 'No architecture-affecting file changes were detected.' -ForegroundColor Green
  exit 0
}

foreach ($rule in $rules) {
  $triggeringFiles = @($changedFiles | Where-Object { Test-MatchesPattern -Value $_ -Patterns $rule.Watched })
  if ($triggeringFiles.Count -eq 0) {
    continue
  }

  $matchingDocChanges = @($changedFiles | Where-Object { Test-MatchesPattern -Value $_ -Patterns $rule.RequiredDocs })
  if ($matchingDocChanges.Count -eq 0) {
    $violations.Add(
      "$($rule.Name): changed $($triggeringFiles -join ', ') without also updating one of $($rule.RequiredDocs -join ', ')."
    )
  }
}

if ($violations.Count -gt 0) {
  Write-Host 'Architecture drift violations found:' -ForegroundColor Red
  foreach ($violation in $violations) {
    Write-Host " - $violation" -ForegroundColor Red
  }
  exit 1
}

Write-Host 'Architecture drift checks passed.' -ForegroundColor Green
