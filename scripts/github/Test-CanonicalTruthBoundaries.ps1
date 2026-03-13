$ErrorActionPreference = 'Stop'

$violations = New-Object System.Collections.Generic.List[string]

function Require-File {
  param([string]$Path)

  if (-not (Test-Path $Path -PathType Leaf)) {
    $violations.Add("Missing required truth-boundary file: $Path")
  }
}

function Require-Text {
  param(
    [string]$Path,
    [string[]]$RequiredSnippets
  )

  if (-not (Test-Path $Path -PathType Leaf)) {
    return
  }

  $content = Get-Content -Raw $Path
  foreach ($snippet in $RequiredSnippets) {
    if ($content -notmatch [regex]::Escape($snippet)) {
      $violations.Add("$Path must preserve truth-boundary language containing '$snippet'.")
    }
  }
}

function Get-RepositoryRelativePath {
  param([string]$FullPath)

  $root = (Get-Location).Path.TrimEnd('\')
  return $FullPath.Substring($root.Length + 1).Replace('\', '/')
}

$requiredFiles = @(
  'README.md',
  'docs/governance/forsetti_governance_alignment.md',
  'docs/architecture/ywe_invariant_guardrails.md',
  'docs/architecture/engine_interface_contracts.md',
  'docs/architecture/ywe_module_design_contracts.md',
  'docs/architecture/ywe_cross_module_dependency_map.md'
)

foreach ($file in $requiredFiles) {
  Require-File -Path $file
}

$requiredDocSnippets = @{
  'README.md' = @(
    'Forsetti governs activation; YWE governs truth.',
    'Adapters remain downstream bridges'
  )
  'docs/governance/forsetti_governance_alignment.md' = @(
    'host environments may realize YWE outputs but may not redefine YWE truth'
  )
  'docs/architecture/ywe_invariant_guardrails.md' = @(
    'Forsetti governs activation while YWE governs truth'
  )
  'docs/architecture/engine_interface_contracts.md' = @(
    'host bridges may map to Forsetti `app` modules or host-layer integrations outside this branch'
  )
  'docs/architecture/ywe_module_design_contracts.md' = @(
    'They must never become sources of canonical YWE truth.'
  )
  'docs/architecture/ywe_cross_module_dependency_map.md' = @(
    'adapters must not invert truth ownership'
  )
}

foreach ($path in $requiredDocSnippets.Keys) {
  Require-Text -Path $path -RequiredSnippets $requiredDocSnippets[$path]
}

$adapterDirectories = Get-ChildItem 'adapters' -Directory -ErrorAction SilentlyContinue
foreach ($adapterDirectory in $adapterDirectories) {
  $adapterRoot = Get-RepositoryRelativePath -FullPath $adapterDirectory.FullName

  Require-Text -Path (Join-Path $adapterRoot 'README.md') -RequiredSnippets @(
    'without owning YWE truth'
  )
  Require-Text -Path (Join-Path $adapterRoot 'adapter_interface.md') -RequiredSnippets @(
    'keep execution concerns separate from truth ownership'
  )
  Require-Text -Path (Join-Path $adapterRoot 'environment_bridge.md') -RequiredSnippets @(
    'preserve YWE as the source of truth'
  )
  Require-Text -Path (Join-Path $adapterRoot 'delegation_boundary.md') -RequiredSnippets @(
    'does not own cosmology or generation truth'
  )
  Require-Text -Path (Join-Path $adapterRoot 'activation_policy_notes.md') -RequiredSnippets @(
    'Forsetti governs activation'
  )
  Require-Text -Path (Join-Path $adapterRoot 'entity_spawn_bridge.md') -RequiredSnippets @(
    'without redefining canonical truth'
  )

  $profilePath = Join-Path $adapterRoot 'capability_profile.yaml'
  Require-File -Path $profilePath
  if (Test-Path $profilePath -PathType Leaf) {
    $profileContent = Get-Content -Raw $profilePath

    foreach ($snippet in @(
        'host_role: downstream_execution_connector',
        'owns_canonical_truth: false',
        'may_realize_outputs: true',
        'may_rewrite_shared_world_truth: false',
        'ui_theme_mask'
      )) {
      if ($profileContent -notmatch [regex]::Escape($snippet)) {
        $violations.Add("$profilePath must contain '$snippet'.")
      }
    }
  }
}

if ($violations.Count -gt 0) {
  Write-Host 'Canonical truth-boundary violations found:' -ForegroundColor Red
  foreach ($violation in $violations) {
    Write-Host " - $violation" -ForegroundColor Red
  }
  exit 1
}

Write-Host 'Canonical truth-boundary checks passed.' -ForegroundColor Green
