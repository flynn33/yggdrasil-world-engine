$ErrorActionPreference = 'Stop'

$violations = New-Object System.Collections.Generic.List[string]

function Require-File {
  param([string]$Path)

  if (-not (Test-Path $Path -PathType Leaf)) {
    $violations.Add("Missing required module contract file: $Path")
  }
}

function Read-JsonFile {
  param([string]$Path)

  try {
    return Get-Content -Raw $Path | ConvertFrom-Json
  } catch {
    $violations.Add("Invalid JSON in $Path")
    return $null
  }
}

function Get-RepositoryRelativePath {
  param([string]$FullPath)

  $root = (Get-Location).Path.TrimEnd('\')
  return $FullPath.Substring($root.Length + 1).Replace('\', '/')
}

function Require-Properties {
  param(
    $Object,
    [string[]]$Properties,
    [string]$Label
  )

  if (-not $Object) {
    return
  }

  foreach ($property in $Properties) {
    if (-not $Object.PSObject.Properties[$property]) {
      $violations.Add("$Label is missing required property '$property'.")
    }
  }
}

function Test-MarkDownSections {
  param(
    [string]$Path,
    [string[]]$RequiredSections
  )

  if (-not (Test-Path $Path -PathType Leaf)) {
    return
  }

  $content = Get-Content -Raw $Path
  foreach ($section in $RequiredSections) {
    if ($content -notmatch "(?m)^$([regex]::Escape($section))\s*$") {
      $violations.Add("$Path is missing required section '$section'.")
    }
  }
}

$expectedCoreDirectories = @(
  'ash_pattern_engine',
  'cosmology_engine',
  'narrative_engine',
  'perception_engine',
  'realm_engine'
)

$expectedModuleDirectories = @(
  'artifact_engine',
  'creature_engine',
  'myth_engine',
  'prophecy_engine',
  'quest_engine'
)

$requiredRuntimeFiles = @(
  'README.md',
  'module_description.md',
  'schema_notes.md',
  'engine_interface.json',
  'forsetti_module_manifest.template.json'
)

$requiredMarkdownSections = @(
  '## Purpose',
  '## Inputs',
  '## Outputs',
  '## Dependencies',
  '## Invariants'
)

$specialFilesByDirectory = @{
  'core/narrative_engine' = @(
    'ash_runtime_generation_flow.yaml',
    'npc_synthesis_rules.yaml',
    'player_origin_arc_rules.yaml',
    'worldstate_delta_rules.yaml'
  )
  'core/perception_engine' = @(
    'perception_layer_persistence_schema.json'
  )
  'modules/artifact_engine' = @(
    'artifact_system_rules.yaml'
  )
  'modules/creature_engine' = @(
    'creature_system_rules.yaml'
  )
  'modules/myth_engine' = @(
    'myth_emergence_rules.yaml'
  )
  'modules/prophecy_engine' = @(
    'prophecy_activation_rules.yaml'
  )
  'modules/quest_engine' = @(
    'quest_chain_templates.yaml'
  )
}

$currentCoreDirectories = Get-ChildItem 'core' -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
$currentModuleDirectories = Get-ChildItem 'modules' -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name

foreach ($directory in $expectedCoreDirectories) {
  if (-not ($currentCoreDirectories -contains $directory)) {
    $violations.Add("Missing required core runtime directory: core/$directory")
  }
}

foreach ($directory in $expectedModuleDirectories) {
  if (-not ($currentModuleDirectories -contains $directory)) {
    $violations.Add("Missing required feature runtime directory: modules/$directory")
  }
}

foreach ($root in @('core', 'modules')) {
  $runtimeDirectories = Get-ChildItem $root -Directory -ErrorAction SilentlyContinue

  foreach ($directory in $runtimeDirectories) {
    $relativeDirectory = Get-RepositoryRelativePath -FullPath $directory.FullName

    foreach ($requiredFile in $requiredRuntimeFiles) {
      Require-File -Path (Join-Path $relativeDirectory $requiredFile)
    }

    if ($specialFilesByDirectory.ContainsKey($relativeDirectory)) {
      foreach ($specialFile in $specialFilesByDirectory[$relativeDirectory]) {
        Require-File -Path (Join-Path $relativeDirectory $specialFile)
      }
    }

    foreach ($markdownFile in @('README.md', 'module_description.md', 'schema_notes.md')) {
      Test-MarkDownSections -Path (Join-Path $relativeDirectory $markdownFile) -RequiredSections $requiredMarkdownSections
    }

    $interfacePath = Join-Path $relativeDirectory 'engine_interface.json'
    if (Test-Path $interfacePath -PathType Leaf) {
      $engineInterface = Read-JsonFile -Path $interfacePath
      Require-Properties -Object $engineInterface -Properties @(
        'moduleID',
        'displayName',
        'truthDomain',
        'directRuntimeDependencies',
        'semanticInputs',
        'outputs'
      ) -Label $interfacePath

      if ($engineInterface) {
        if ($relativeDirectory -like 'core/*' -and $engineInterface.moduleID -notmatch '^com\.ywe\.core\.') {
          $violations.Add("$interfacePath must use a com.ywe.core.* moduleID.")
        }

        if ($relativeDirectory -like 'modules/*' -and $engineInterface.moduleID -notmatch '^com\.ywe\.module\.') {
          $violations.Add("$interfacePath must use a com.ywe.module.* moduleID.")
        }
      }
    }

    $manifestPath = Join-Path $relativeDirectory 'forsetti_module_manifest.template.json'
    if (Test-Path $manifestPath -PathType Leaf) {
      $manifest = Read-JsonFile -Path $manifestPath
      Require-Properties -Object $manifest -Properties @(
        'schemaVersion',
        'moduleID',
        'displayName',
        'moduleVersion',
        'moduleType',
        'supportedPlatforms',
        'minForsettiVersion',
        'entryPoint'
      ) -Label $manifestPath
    }
  }
}

if ($violations.Count -gt 0) {
  Write-Host 'Module contract coverage violations found:' -ForegroundColor Red
  foreach ($violation in $violations) {
    Write-Host " - $violation" -ForegroundColor Red
  }
  exit 1
}

Write-Host 'Module contract coverage checks passed.' -ForegroundColor Green
