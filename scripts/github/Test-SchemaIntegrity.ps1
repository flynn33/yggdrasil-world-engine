$ErrorActionPreference = 'Stop'

$violations = New-Object System.Collections.Generic.List[string]

function Require-File {
  param([string]$Path)

  if (-not (Test-Path $Path -PathType Leaf)) {
    $violations.Add("Missing required schema file: $Path")
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

function Require-ArrayContains {
  param(
    [object[]]$Values,
    [string]$Expected,
    [string]$Label
  )

  if (-not (@($Values) -contains $Expected)) {
    $violations.Add("$Label must contain '$Expected'.")
  }
}

$requiredFiles = @(
  'data/schemas/player_schema.json',
  'data/schemas/prophecy_schema.json',
  'data/schemas/myth_record_schema_expansion.json',
  'data/schemas/perception_layer_persistence_schema.json',
  'data/schemas/prophecy_schema_expansion.json',
  'data/pattern_archetypes/pattern_schema.json',
  'data/quest_archetypes/quest_seed_schema.json',
  'data/myth_archetypes/myth_schema.json',
  'data/bloodline_registry/bloodline_schema.json',
  'data/realm_registry/realms.json'
)

foreach ($path in $requiredFiles) {
  Require-File -Path $path
}

$schemaFiles = Get-ChildItem 'data/schemas' -Filter '*.json' -ErrorAction SilentlyContinue
foreach ($schemaFile in $schemaFiles) {
  if ($schemaFile.Name -notmatch '^[a-z0-9_]+_schema(?:_expansion)?\.json$') {
    $violations.Add("$($schemaFile.FullName) does not follow the expected *_schema.json or *_schema_expansion.json naming pattern.")
  }
}

$playerSchema = Read-JsonFile -Path 'data/schemas/player_schema.json'
Require-Properties -Object $playerSchema -Properties @(
  'origin',
  'celestial_memory',
  'realm_attunement',
  'wolf_alignment',
  'bloodline_resonance',
  'awakening_fragments'
) -Label 'data/schemas/player_schema.json'

if ($playerSchema) {
  if ($playerSchema.origin -ne 'mortal') {
    $violations.Add("data/schemas/player_schema.json must keep origin set to 'mortal'.")
  }

  if ($playerSchema.celestial_memory -ne 'veiled') {
    $violations.Add("data/schemas/player_schema.json must keep celestial_memory set to 'veiled'.")
  }

  if (-not $playerSchema.PSObject.Properties['wolf_alignment']) {
    $violations.Add("data/schemas/player_schema.json must define wolf_alignment.")
  } else {
    Require-Properties -Object $playerSchema.wolf_alignment -Properties @('white_wolf', 'dark_wolf') -Label 'data/schemas/player_schema.json wolf_alignment'
  }
}

$prophecySchema = Read-JsonFile -Path 'data/schemas/prophecy_schema.json'
Require-Properties -Object $prophecySchema -Properties @('prophecy_id', 'condition', 'status') -Label 'data/schemas/prophecy_schema.json'
if ($prophecySchema -and $prophecySchema.status -ne 'dormant') {
  $violations.Add("data/schemas/prophecy_schema.json must keep status set to 'dormant'.")
}

$patternSchema = Read-JsonFile -Path 'data/pattern_archetypes/pattern_schema.json'
Require-Properties -Object $patternSchema -Properties @('pattern_id', 'type', 'realm_bias', 'strength') -Label 'data/pattern_archetypes/pattern_schema.json'

$questSchema = Read-JsonFile -Path 'data/quest_archetypes/quest_seed_schema.json'
Require-Properties -Object $questSchema -Properties @('quest_seed_id', 'pattern_id', 'interpretations') -Label 'data/quest_archetypes/quest_seed_schema.json'

$mythSchema = Read-JsonFile -Path 'data/myth_archetypes/myth_schema.json'
Require-Properties -Object $mythSchema -Properties @('myth_id', 'source_event', 'title', 'faction_versions') -Label 'data/myth_archetypes/myth_schema.json'

$bloodlineSchema = Read-JsonFile -Path 'data/bloodline_registry/bloodline_schema.json'
Require-Properties -Object $bloodlineSchema -Properties @('bloodline_id', 'mythic_origin', 'resonance_effects') -Label 'data/bloodline_registry/bloodline_schema.json'

$realmRegistry = Read-JsonFile -Path 'data/realm_registry/realms.json'
Require-Properties -Object $realmRegistry -Properties @('realms') -Label 'data/realm_registry/realms.json'
if ($realmRegistry) {
  $expectedRealms = @(
    'divine_core',
    'celestial',
    'causal',
    'mental',
    'astral',
    'etheric',
    'physical',
    'shadow',
    'void'
  )

  if (@($realmRegistry.realms).Count -ne $expectedRealms.Count) {
    $violations.Add("data/realm_registry/realms.json must list exactly $($expectedRealms.Count) canonical realms.")
  }

  foreach ($realm in $expectedRealms) {
    Require-ArrayContains -Values @($realmRegistry.realms) -Expected $realm -Label 'data/realm_registry/realms.json realms'
  }
}

$placeholderExpansionFiles = @(
  @{
    Path = 'data/schemas/myth_record_schema_expansion.json'
    Dependencies = @('data/myth_archetypes/myth_schema.json', 'modules/myth_engine')
  },
  @{
    Path = 'data/schemas/perception_layer_persistence_schema.json'
    Dependencies = @('core/perception_engine', 'perception divergence rules')
  },
  @{
    Path = 'data/schemas/prophecy_schema_expansion.json'
    Dependencies = @('data/schemas/prophecy_schema.json', 'modules/prophecy_engine')
  }
)

$requiredPlaceholderFields = @(
  'status',
  'system',
  'purpose',
  'inputs',
  'outputs',
  'dependencies',
  'invariants'
)

$requiredPlaceholderInvariants = @(
  'all_meaningful_generation_must_be_ash_derived',
  'fixed_cosmology_must_remain_locked',
  'perception_must_not_rewrite_shared_world_truth',
  'forsetti_governs_activation_ywe_governs_truth'
)

foreach ($placeholderSchema in $placeholderExpansionFiles) {
  $content = Read-JsonFile -Path $placeholderSchema.Path
  Require-Properties -Object $content -Properties $requiredPlaceholderFields -Label $placeholderSchema.Path

  if (-not $content) {
    continue
  }

  if ($content.status -ne 'placeholder_awaiting_finalized_content') {
    $violations.Add("$($placeholderSchema.Path) must keep status set to 'placeholder_awaiting_finalized_content' until finalized content replaces it.")
  }

  foreach ($dependency in $placeholderSchema.Dependencies) {
    Require-ArrayContains -Values @($content.dependencies) -Expected $dependency -Label "$($placeholderSchema.Path) dependencies"
  }

  foreach ($invariant in $requiredPlaceholderInvariants) {
    Require-ArrayContains -Values @($content.invariants) -Expected $invariant -Label "$($placeholderSchema.Path) invariants"
  }
}

if ($violations.Count -gt 0) {
  Write-Host 'Schema integrity violations found:' -ForegroundColor Red
  foreach ($violation in $violations) {
    Write-Host " - $violation" -ForegroundColor Red
  }
  exit 1
}

Write-Host 'Schema integrity checks passed.' -ForegroundColor Green
