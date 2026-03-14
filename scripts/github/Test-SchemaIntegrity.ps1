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

function Read-TextFile {
  param([string]$Path)

  if (-not (Test-Path $Path -PathType Leaf)) {
    $violations.Add("Missing required text file: $Path")
    return $null
  }

  return Get-Content -Raw $Path
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

function Require-TextMatch {
  param(
    [string]$Content,
    [string]$Pattern,
    [string]$Message
  )

  if ($Content -notmatch $Pattern) {
    $violations.Add($Message)
  }
}

function Test-AshSchemaFile {
  param([string]$Path)

  $content = Read-TextFile -Path $Path
  if (-not $content) {
    return
  }

  $requiredPatterns = @(
    @{
      Pattern = '(?m)^version:\s+"1\.0"\s*$'
      Message = "$Path must declare version 1.0."
    },
    @{
      Pattern = '(?m)^meta:\s*$'
      Message = "$Path must define a meta section."
    },
    @{
      Pattern = '(?m)^  system:\s+ash_pattern_registry_schema\s*$'
      Message = "$Path must define meta.system as ash_pattern_registry_schema."
    },
    @{
      Pattern = '(?m)^enums:\s*$'
      Message = "$Path must define the canonical enum set."
    },
    @{
      Pattern = '(?m)^  record_status:\s*$'
      Message = "$Path must define record_status enum values."
    },
    @{
      Pattern = '(?m)^  cluster_stability:\s*$'
      Message = "$Path must define cluster_stability enum values."
    },
    @{
      Pattern = '(?m)^schema:\s*$'
      Message = "$Path must define the schema section."
    },
    @{
      Pattern = '(?m)^  ArchetypeRecord:\s*$'
      Message = "$Path must define ArchetypeRecord."
    },
    @{
      Pattern = '(?m)^  ClusterRecord:\s*$'
      Message = "$Path must define ClusterRecord."
    },
    @{
      Pattern = '(?m)^registry_shape:\s*$'
      Message = "$Path must define registry_shape."
    }
  )

  foreach ($requiredPattern in $requiredPatterns) {
    Require-TextMatch -Content $content -Pattern $requiredPattern.Pattern -Message $requiredPattern.Message
  }
}

function Test-AshRegistryRecord {
  param(
    [string]$Block,
    [string]$Path,
    [string]$RecordId,
    [string]$Family,
    [string]$IdPrefix,
    [bool]$IsCluster
  )

  if ($RecordId -notmatch ("^{0}[a-z0-9_]+$" -f [regex]::Escape($IdPrefix))) {
    $violations.Add("$Path contains record '$RecordId' which does not use the required $IdPrefix canonical ID prefix.")
  }

  $requiredFieldPatterns = @(
    @{
      Pattern = "(?m)^    family:\s+$Family\s*$"
      Message = "$Path record '$RecordId' must keep family set to '$Family'."
    },
    @{
      Pattern = '(?m)^    name:\s+.+$'
      Message = "$Path record '$RecordId' is missing name."
    },
    @{
      Pattern = '(?m)^    summary:\s+.+$'
      Message = "$Path record '$RecordId' is missing summary."
    },
    @{
      Pattern = '(?m)^    symbolic_function:\s+\[.+\]\s*$'
      Message = "$Path record '$RecordId' is missing symbolic_function."
    },
    @{
      Pattern = '(?m)^    truth_modes:\s+\[.+\]\s*$'
      Message = "$Path record '$RecordId' is missing truth_modes."
    },
    @{
      Pattern = '(?m)^    shadow_modes:\s+\[.*\]\s*$'
      Message = "$Path record '$RecordId' is missing shadow_modes."
    },
    @{
      Pattern = '(?m)^    realm_bias:\s+\[.+\]\s*$'
      Message = "$Path record '$RecordId' is missing realm_bias."
    },
    @{
      Pattern = '(?m)^    wolf_bias:\s+\{white:\s*-?\d+(?:\.\d+)?,\s*dark:\s*-?\d+(?:\.\d+)?\}\s*$'
      Message = "$Path record '$RecordId' must define wolf_bias.white and wolf_bias.dark."
    },
    @{
      Pattern = '(?m)^    player_phase_bias:\s+\[.+\]\s*$'
      Message = "$Path record '$RecordId' is missing player_phase_bias."
    },
    @{
      Pattern = '(?m)^    compatible_with:\s+\[.*\]\s*$'
      Message = "$Path record '$RecordId' is missing compatible_with."
    },
    @{
      Pattern = '(?m)^    friction_with:\s+\[.*\]\s*$'
      Message = "$Path record '$RecordId' is missing friction_with."
    },
    @{
      Pattern = '(?m)^    contradicts:\s+\[.*\]\s*$'
      Message = "$Path record '$RecordId' is missing contradicts."
    },
    @{
      Pattern = '(?m)^    downstream_affinities:\s*$'
      Message = "$Path record '$RecordId' is missing downstream_affinities."
    },
    @{
      Pattern = '(?m)^    manifestation_hints:\s+\[.+\]\s*$'
      Message = "$Path record '$RecordId' is missing manifestation_hints."
    },
    @{
      Pattern = '(?m)^    invariant_notes:\s+\[.+\]\s*$'
      Message = "$Path record '$RecordId' is missing invariant_notes."
    },
    @{
      Pattern = '(?m)^    status:\s+(canonical|provisional|deprecated)\s*$'
      Message = "$Path record '$RecordId' must keep status within canonical, provisional, or deprecated."
    }
  )

  foreach ($requiredField in $requiredFieldPatterns) {
    Require-TextMatch -Content $Block -Pattern $requiredField.Pattern -Message $requiredField.Message
  }

  foreach ($downstreamKey in @('npc', 'quest', 'myth', 'prophecy', 'artifact', 'creature')) {
    Require-TextMatch `
      -Content $Block `
      -Pattern ("(?m)^      {0}:\s+\[.*\]\s*$" -f [regex]::Escape($downstreamKey)) `
      -Message "$Path record '$RecordId' must define downstream_affinities.$downstreamKey."
  }

  if ($IsCluster) {
    $clusterPatterns = @(
      @{
        Pattern = '(?m)^    members:\s+\[.+\]\s*$'
        Message = "$Path cluster '$RecordId' must define members."
      },
      @{
        Pattern = '(?m)^    combined_summary:\s+.+$'
        Message = "$Path cluster '$RecordId' must define combined_summary."
      },
      @{
        Pattern = '(?m)^    lawful_basis:\s+\[.+\]\s*$'
        Message = "$Path cluster '$RecordId' must define lawful_basis."
      },
      @{
        Pattern = '(?m)^    contradiction_risk:\s+.+$'
        Message = "$Path cluster '$RecordId' must define contradiction_risk."
      },
      @{
        Pattern = '(?m)^    stability_mode:\s+(stable|unstable|cyclical|threshold_based)\s*$'
        Message = "$Path cluster '$RecordId' must define stability_mode using the allowed schema values."
      }
    )

    foreach ($clusterPattern in $clusterPatterns) {
      Require-TextMatch -Content $Block -Pattern $clusterPattern.Pattern -Message $clusterPattern.Message
    }
  }
}

function Test-AshRegistryFile {
  param(
    [string]$Path,
    [string]$Family,
    [string]$IdPrefix,
    [bool]$IsCluster = $false
  )

  $content = Read-TextFile -Path $Path
  if (-not $content) {
    return
  }

  $requiredRootPatterns = @(
    @{
      Pattern = '(?m)^registry_version:\s+"1\.0"\s*$'
      Message = "$Path must declare registry_version 1.0."
    },
    @{
      Pattern = '(?m)^status:\s+canonical\s*$'
      Message = "$Path must keep top-level status set to canonical."
    },
    @{
      Pattern = '(?m)^authority:\s*$'
      Message = "$Path must define authority metadata."
    },
    @{
      Pattern = '(?m)^  prose_spec:\s+docs/architecture/ASH_PATTERN_ARCHETYPE_LIBRARY_CANONICAL\.md\s*$'
      Message = "$Path must point authority.prose_spec to the canonical ASH specification."
    },
    @{
      Pattern = '(?m)^  schema_ref:\s+data/pattern_archetypes/ash_pattern_registry_schema\.yaml\s*$'
      Message = "$Path must point authority.schema_ref to data/pattern_archetypes/ash_pattern_registry_schema.yaml."
    },
    @{
      Pattern = '(?m)^  downstream_contract:\s+docs/architecture/ash_downstream_contract\.md\s*$'
      Message = "$Path must point authority.downstream_contract to the canonical ASH downstream contract."
    },
    @{
      Pattern = "(?m)^family:\s+$Family\s*$"
      Message = "$Path must keep top-level family set to '$Family'."
    },
    @{
      Pattern = '(?m)^records:\s*$'
      Message = "$Path must define a records list."
    }
  )

  foreach ($requiredRootPattern in $requiredRootPatterns) {
    Require-TextMatch -Content $content -Pattern $requiredRootPattern.Pattern -Message $requiredRootPattern.Message
  }

  if ($content -match 'placeholder awaiting finalized content|placeholder_awaiting_finalized_content') {
    $violations.Add("$Path must not remain placeholder-backed after ASH normalization.")
  }

  $recordMatches = [regex]::Matches($content, '(?m)^  - id:\s+([a-z0-9_]+)\s*$')
  if ($recordMatches.Count -eq 0) {
    $violations.Add("$Path must contain at least one canonical archetype record.")
    return
  }

  for ($index = 0; $index -lt $recordMatches.Count; $index++) {
    $start = $recordMatches[$index].Index
    $end = if ($index -lt ($recordMatches.Count - 1)) {
      $recordMatches[$index + 1].Index
    } else {
      $content.Length
    }

    $recordId = $recordMatches[$index].Groups[1].Value
    $block = $content.Substring($start, $end - $start)
    Test-AshRegistryRecord -Block $block -Path $Path -RecordId $recordId -Family $Family -IdPrefix $IdPrefix -IsCluster:$IsCluster
  }
}

function Test-FactionTopologySchema {
  param([string]$Path)

  $content = Read-TextFile -Path $Path
  if (-not $content) {
    return
  }

  if ($content -match 'placeholder awaiting finalized content|placeholder_awaiting_finalized_content') {
    $violations.Add("$Path must not remain placeholder-backed once faction topology has been stabilized.")
  }

  $requiredPatterns = @(
    @{
      Pattern = '(?m)^version:\s+"0\.2"\s*$'
      Message = "$Path must declare version 0.2."
    },
    @{
      Pattern = '(?m)^meta:\s*$'
      Message = "$Path must define metadata."
    },
    @{
      Pattern = '(?m)^  system:\s+faction_topology_state\s*$'
      Message = "$Path must keep meta.system set to faction_topology_state."
    },
    @{
      Pattern = '(?m)^core_schema:\s*$'
      Message = "$Path must define core_schema."
    },
    @{
      Pattern = '(?m)^  FactionTopologyState:\s*$'
      Message = "$Path must define FactionTopologyState."
    },
    @{
      Pattern = '(?m)^  FactionNode:\s*$'
      Message = "$Path must define FactionNode."
    },
    @{
      Pattern = '(?m)^  FactionEdge:\s*$'
      Message = "$Path must define FactionEdge."
    },
    @{
      Pattern = '(?m)^  ClaimRecord:\s*$'
      Message = "$Path must define ClaimRecord."
    },
    @{
      Pattern = '(?m)^  ReformCurrent:\s*$'
      Message = "$Path must define ReformCurrent."
    },
    @{
      Pattern = '(?m)^  SuccessionTrack:\s*$'
      Message = "$Path must define SuccessionTrack."
    },
    @{
      Pattern = '(?m)^relation_types:\s*$'
      Message = "$Path must define supported relation types."
    },
    @{
      Pattern = '(?m)^topology_update_packet_schema:\s*$'
      Message = "$Path must define topology_update_packet_schema."
    },
    @{
      Pattern = '(?m)^  FactionTopologyUpdatePacket:\s*$'
      Message = "$Path must define FactionTopologyUpdatePacket."
    },
    @{
      Pattern = '(?m)^validation_rules:\s*$'
      Message = "$Path must define validation_rules."
    },
    @{
      Pattern = '(?m)^implementation_notes:\s*$'
      Message = "$Path must define implementation_notes."
    },
    @{
      Pattern = '(?m)^    canonical_schema:\s+data/factions/faction_topology_state_schema\.yaml\s*$'
      Message = "$Path must keep implementation_notes.recommended_repo_locations.canonical_schema pointed at data/factions/faction_topology_state_schema.yaml."
    }
  )

  foreach ($requiredPattern in $requiredPatterns) {
    Require-TextMatch -Content $content -Pattern $requiredPattern.Pattern -Message $requiredPattern.Message
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

Test-AshSchemaFile -Path 'data/pattern_archetypes/ash_pattern_registry_schema.yaml'
Test-FactionTopologySchema -Path 'data/factions/faction_topology_state_schema.yaml'

$ashRegistryFiles = @(
  @{
    Path = 'data/pattern_archetypes/character_archetypes.yaml'
    Family = 'character'
    IdPrefix = 'char_'
    IsCluster = $false
  },
  @{
    Path = 'data/quest_archetypes/quest_archetypes.yaml'
    Family = 'quest'
    IdPrefix = 'quest_'
    IsCluster = $false
  },
  @{
    Path = 'data/pattern_archetypes/region_archetypes.yaml'
    Family = 'region'
    IdPrefix = 'region_'
    IsCluster = $false
  },
  @{
    Path = 'data/pattern_archetypes/faction_archetypes.yaml'
    Family = 'faction'
    IdPrefix = 'faction_'
    IsCluster = $false
  },
  @{
    Path = 'data/pattern_archetypes/transformation_archetypes.yaml'
    Family = 'transformation'
    IdPrefix = 'transformation_'
    IsCluster = $false
  },
  @{
    Path = 'data/pattern_archetypes/event_archetypes.yaml'
    Family = 'event'
    IdPrefix = 'event_'
    IsCluster = $false
  },
  @{
    Path = 'data/pattern_archetypes/pattern_clusters.yaml'
    Family = 'cluster'
    IdPrefix = 'cluster_'
    IsCluster = $true
  }
)

foreach ($ashRegistryFile in $ashRegistryFiles) {
  Test-AshRegistryFile `
    -Path $ashRegistryFile.Path `
    -Family $ashRegistryFile.Family `
    -IdPrefix $ashRegistryFile.IdPrefix `
    -IsCluster:$ashRegistryFile.IsCluster
}

if ($violations.Count -gt 0) {
  Write-Host 'Schema integrity violations found:' -ForegroundColor Red
  foreach ($violation in $violations) {
    Write-Host " - $violation" -ForegroundColor Red
  }
  exit 1
}

Write-Host 'Schema integrity checks passed.' -ForegroundColor Green
