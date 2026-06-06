$ErrorActionPreference = 'Stop'

$violations = New-Object System.Collections.Generic.List[string]

function Require-File {
  param([string]$Path)
  if (-not (Test-Path $Path -PathType Leaf)) {
    $violations.Add("Missing required file: $Path")
  }
}

function Read-JsonFile {
  param([string]$Path)
  return Get-Content -Raw $Path | ConvertFrom-Json
}

$requiredDocs = @(
  'README.md',
  'docs/governance/forsetti_governance_alignment.md',
  'docs/architecture/engine_interface_contracts.md',
  'docs/architecture/ywe_module_design_contracts.md',
  'docs/architecture/ywe_cross_module_dependency_map.md',
  'docs/architecture/ywe_invariant_guardrails.md',
  'docs/architecture/forsetti_module_manifest_conventions.md'
)

foreach ($doc in $requiredDocs) {
  Require-File -Path $doc
}

$coreManifestFiles = Get-ChildItem 'core' -Recurse -Filter 'forsetti_module_manifest.template.json' -ErrorAction SilentlyContinue
$moduleManifestFiles = Get-ChildItem 'modules' -Recurse -Filter 'forsetti_module_manifest.template.json' -ErrorAction SilentlyContinue
$allTemplateFiles = @($coreManifestFiles + $moduleManifestFiles)

if ($allTemplateFiles.Count -ne 10) {
  $violations.Add("Expected 10 Forsetti manifest templates across core and modules, found $($allTemplateFiles.Count).")
}

$requiredManifestFields = @(
  'schemaVersion',
  'moduleID',
  'displayName',
  'moduleVersion',
  'moduleType',
  'supportedPlatforms',
  'minForsettiVersion',
  'entryPoint'
)

foreach ($manifestFile in $allTemplateFiles) {
  $manifest = Read-JsonFile -Path $manifestFile.FullName

  foreach ($field in $requiredManifestFields) {
    if (-not $manifest.PSObject.Properties[$field]) {
      $violations.Add("$($manifestFile.FullName) is missing required field '$field'.")
    }
  }

  if ($manifest.capabilitiesRequested -contains 'ui_theme_mask') {
    $violations.Add("$($manifestFile.FullName) requests reserved capability 'ui_theme_mask'.")
  }
}

$coreInterfaces = Get-ChildItem 'core' -Recurse -Filter 'engine_interface.json' -ErrorAction SilentlyContinue
foreach ($interfaceFile in $coreInterfaces) {
  $interface = Read-JsonFile -Path $interfaceFile.FullName
  foreach ($dependency in @($interface.directRuntimeDependencies)) {
    if ($dependency -match '^com\.ywe\.module\.') {
      $violations.Add("$($interfaceFile.FullName) illegally depends on feature module '$dependency'.")
    }
  }
}

$moduleInterfaces = Get-ChildItem 'modules' -Recurse -Filter 'engine_interface.json' -ErrorAction SilentlyContinue
foreach ($interfaceFile in $moduleInterfaces) {
  $interface = Read-JsonFile -Path $interfaceFile.FullName
  foreach ($dependency in @($interface.directRuntimeDependencies)) {
    if ($dependency -notmatch '^com\.ywe\.core\.') {
      $violations.Add("$($interfaceFile.FullName) has non-core runtime dependency '$dependency'.")
    }
  }
}

$adapterProfiles = Get-ChildItem 'adapters' -Recurse -Filter 'capability_profile.yaml' -ErrorAction SilentlyContinue
foreach ($profileFile in $adapterProfiles) {
  $content = Get-Content -Raw $profileFile.FullName
  if ($content -notmatch 'owns_canonical_truth:\s*false') {
    $violations.Add("$($profileFile.FullName) must state owns_canonical_truth: false.")
  }
  if ($content -notmatch 'ui_theme_mask') {
    $violations.Add("$($profileFile.FullName) must forbid ui_theme_mask.")
  }
}

if ($violations.Count -gt 0) {
  Write-Host 'Forsetti compliance violations found:' -ForegroundColor Red
  foreach ($violation in $violations) {
    Write-Host " - $violation" -ForegroundColor Red
  }
  exit 1
}

Write-Host 'Forsetti compliance checks passed.' -ForegroundColor Green
