$ErrorActionPreference = 'Stop'

function Invoke-CheckScript {
  param(
    [string]$Name,
    [string]$Path,
    [string[]]$Arguments = @()
  )

  Write-Host "Running $Name..." -ForegroundColor Cyan
  & pwsh -NoProfile -File $Path @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$Name failed."
  }
}

if (-not (Test-Path 'VERSION' -PathType Leaf)) {
  throw 'VERSION file is required for release readiness.'
}

$version = (Get-Content -Raw 'VERSION').Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') {
  throw "VERSION must contain semantic version text such as 0.1.0. Found '$version'."
}

if (-not (Test-Path 'CHANGELOG.md' -PathType Leaf)) {
  throw 'CHANGELOG.md is required for release readiness.'
}

$changelogContent = Get-Content -Raw 'CHANGELOG.md'
if ($changelogContent -notmatch "(?m)^## \[$([regex]::Escape($version))\]\s+-\s+\d{4}-\d{2}-\d{2}\s*$") {
  throw "CHANGELOG.md must include a heading for version $version."
}

if (-not (Test-Path '.github/wiki-sync.json' -PathType Leaf)) {
  throw '.github/wiki-sync.json is required for release readiness.'
}

$wikiConfig = Get-Content -Raw '.github/wiki-sync.json' | ConvertFrom-Json
if (-not @($wikiConfig.pages).Count) {
  throw '.github/wiki-sync.json must define at least one wiki page.'
}

if (-not (Test-Path 'docs/handoff/missing_source_documents.md' -PathType Leaf)) {
  throw 'docs/handoff/missing_source_documents.md is required for release readiness.'
}

Invoke-CheckScript -Name 'Missing source inventory freshness' -Path './scripts/github/Update-MissingSourceDocuments.ps1' -Arguments @('-CheckOnly')
Invoke-CheckScript -Name 'Forsetti compliance' -Path './scripts/github/Test-ForsettiCompliance.ps1'
Invoke-CheckScript -Name 'Schema integrity' -Path './scripts/github/Test-SchemaIntegrity.ps1'
Invoke-CheckScript -Name 'Module contract coverage' -Path './scripts/github/Test-ModuleContractCoverage.ps1'
Invoke-CheckScript -Name 'Docs and glossary validation' -Path './scripts/github/Test-DocsAndGlossary.ps1'
Invoke-CheckScript -Name 'Canonical truth-boundary validation' -Path './scripts/github/Test-CanonicalTruthBoundaries.ps1'

Write-Host "Release readiness checks passed for version $version." -ForegroundColor Green
