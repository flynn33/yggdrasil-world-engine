$ErrorActionPreference = 'Stop'

$violations = New-Object System.Collections.Generic.List[string]

function Resolve-RelativePath {
  param(
    [string]$MarkdownFile,
    [string]$Target
  )

  $pathPart = $Target.Split('#')[0]
  if (-not $pathPart) {
    return $null
  }

  if ($pathPart -match '^[A-Za-z]:\\') {
    return $pathPart
  }

  if ($pathPart.StartsWith('/')) {
    return Join-Path (Get-Location) ($pathPart.TrimStart('/', '\'))
  }

  return Join-Path (Split-Path -Parent $MarkdownFile) $pathPart
}

function Test-MarkdownLinks {
  param([string]$Path)

  $content = Get-Content -Raw $Path
  $matches = [regex]::Matches($content, '\[[^\]]+\]\(([^)]+)\)')

  foreach ($match in $matches) {
    $target = $match.Groups[1].Value.Trim()

    if ($target -match '^(https?://|mailto:|#)') {
      continue
    }

    if ($target -match '^sandbox:') {
      $violations.Add("$Path contains sandbox-only link '$target'.")
      continue
    }

    $resolvedTarget = Resolve-RelativePath -MarkdownFile $Path -Target $target
    if ($resolvedTarget -and -not (Test-Path $resolvedTarget)) {
      $violations.Add("$Path links to missing internal target '$target'.")
    }
  }
}

function Require-File {
  param([string]$Path)

  if (-not (Test-Path $Path -PathType Leaf)) {
    $violations.Add("Missing required documentation file: $Path")
  }
}

$markdownFiles = Get-ChildItem -Recurse -Filter '*.md' -ErrorAction SilentlyContinue
foreach ($markdownFile in $markdownFiles) {
  Test-MarkdownLinks -Path $markdownFile.FullName
}

$wikiConfigPath = '.github/wiki-sync.json'
Require-File -Path $wikiConfigPath
if (Test-Path $wikiConfigPath -PathType Leaf) {
  $wikiConfig = Get-Content -Raw $wikiConfigPath | ConvertFrom-Json

  if (-not @($wikiConfig.pages).Count) {
    $violations.Add('.github/wiki-sync.json must define at least one wiki page mapping.')
  }

  $destinationCounts = @{}
  foreach ($page in @($wikiConfig.pages)) {
    if (-not $page.source -or -not $page.destination) {
      $violations.Add('.github/wiki-sync.json contains an entry without both source and destination.')
      continue
    }

    if (-not (Test-Path $page.source -PathType Leaf)) {
      $violations.Add(".github/wiki-sync.json references missing source file '$($page.source)'.")
    }

    if ($page.destination -notmatch '\.md$') {
      $violations.Add(".github/wiki-sync.json destination '$($page.destination)' must end with .md.")
    }

    if (-not $destinationCounts.ContainsKey($page.destination)) {
      $destinationCounts[$page.destination] = 0
    }
    $destinationCounts[$page.destination] += 1
  }

  foreach ($destination in $destinationCounts.Keys) {
    if ($destinationCounts[$destination] -gt 1) {
      $violations.Add(".github/wiki-sync.json duplicates destination '$destination'.")
    }
  }
}

$glossaryPath = 'docs/glossary/ywe_design_glossary.md'
$glossarySourcePath = 'docs/glossary/YWE_Design_Glossary_source.txt'
Require-File -Path $glossaryPath
Require-File -Path $glossarySourcePath

if (Test-Path $glossaryPath -PathType Leaf) {
  $glossaryLines = Get-Content $glossaryPath
  $inGlossarySection = $false
  $glossaryTerms = New-Object System.Collections.Generic.List[string]

  foreach ($line in $glossaryLines) {
    if ($line -match '^# 3\. Glossary') {
      $inGlossarySection = $true
      continue
    }

    if ($inGlossarySection -and $line -match '^# 4\. ') {
      break
    }

    if ($inGlossarySection -and $line -match '^##\s+(.+)$') {
      $glossaryTerms.Add($Matches[1].Trim())
    }
  }

  $duplicateTerms = $glossaryTerms | Group-Object | Where-Object { $_.Count -gt 1 }
  foreach ($duplicate in $duplicateTerms) {
    $violations.Add("Glossary term '$($duplicate.Name)' is defined more than once.")
  }

  $requiredTerms = @(
    'Activation',
    'Adapter',
    'ASH Model',
    'Canonical Data Domain',
    'Engine Interface Contract',
    'Forsetti Framework',
    'Module Design Contract',
    'Myth',
    'Perception Layer',
    'Prophecy',
    'Realm',
    'YWE'
  )

  foreach ($term in $requiredTerms) {
    if (-not ($glossaryTerms -contains $term)) {
      $violations.Add("docs/glossary/ywe_design_glossary.md must define glossary term '$term'.")
    }
  }
}

if ($violations.Count -gt 0) {
  Write-Host 'Documentation and glossary violations found:' -ForegroundColor Red
  foreach ($violation in $violations) {
    Write-Host " - $violation" -ForegroundColor Red
  }
  exit 1
}

Write-Host 'Documentation and glossary checks passed.' -ForegroundColor Green
