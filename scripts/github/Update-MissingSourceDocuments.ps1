param(
  [string]$ManifestPath = 'SOURCE_AVAILABILITY_MANIFEST.md',
  [string]$ReportPath = 'missing_source_documents.md',
  [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'
$PlaceholderSectionHeader = '## Intentional Placeholder-Backed Artifacts'

function Set-WorkflowOutput {
  param(
    [string]$Name,
    [string]$Value
  )

  if ($env:GITHUB_OUTPUT) {
    Add-Content -Path $env:GITHUB_OUTPUT -Value "$Name=$Value"
  }
}

function Get-TrackedPlaceholderEntries {
  param([string]$Path)

  if (-not (Test-Path $Path -PathType Leaf)) {
    throw "Placeholder source manifest not found: $Path"
  }

  $entries = New-Object System.Collections.Generic.List[object]
  $inSection = $false

  foreach ($line in Get-Content $Path) {
    if ($line -match '^## Present as placeholders') {
      $inSection = $true
      continue
    }

    if ($inSection -and $line -match '^## ') {
      break
    }

    if ($inSection -and $line -match '^- `([^`]+)` -> `([^`]+)`') {
      $entries.Add([pscustomobject]@{
          Name = $Matches[1]
          TargetPath = $Matches[2]
        })
    }
  }

  return $entries
}

function Test-PlaceholderBacked {
  param([string]$Path)

  if (-not (Test-Path $Path -PathType Leaf)) {
    return $true
  }

  $content = Get-Content -Raw $Path
  $markers = @(
    'placeholder awaiting finalized content',
    'placeholder_awaiting_finalized_content',
    'document structure placeholder',
    'module interface contract placeholder'
  )

  foreach ($marker in $markers) {
    if ($content -match [regex]::Escape($marker)) {
      return $true
    }
  }

  return $false
}

function Set-PlaceholderSection {
  param(
    [string]$Content,
    [string[]]$Items
  )

  $replacementLines = New-Object System.Collections.Generic.List[string]
  $replacementLines.Add($PlaceholderSectionHeader)
  $replacementLines.Add('')

  if ($Items.Count -eq 0) {
    $replacementLines.Add('- none')
  } else {
    foreach ($item in $Items) {
      $replacementLines.Add("- $item")
    }
  }

  $lines = [System.Text.RegularExpressions.Regex]::Split($Content, '\r\n|\n|\r')
  $startIndex = -1
  $endIndex = $lines.Length

  for ($index = 0; $index -lt $lines.Length; $index++) {
    if ($lines[$index] -eq '## Still Placeholder-Backed' -or $lines[$index] -eq $PlaceholderSectionHeader) {
      $startIndex = $index
      continue
    }

    if ($startIndex -ge 0 -and $lines[$index] -match '^## ') {
      $endIndex = $index
      break
    }
  }

  if ($startIndex -lt 0) {
    $mergedLines = New-Object System.Collections.Generic.List[string]
    foreach ($line in $lines) {
      $mergedLines.Add($line)
    }
    if ($mergedLines.Count -gt 0 -and $mergedLines[$mergedLines.Count - 1] -ne '') {
      $mergedLines.Add('')
    }
    foreach ($line in $replacementLines) {
      $mergedLines.Add($line)
    }
    return ($mergedLines -join "`r`n").TrimEnd() + "`r`n"
  }

  $updatedLines = New-Object System.Collections.Generic.List[string]
  for ($index = 0; $index -lt $startIndex; $index++) {
    $updatedLines.Add($lines[$index])
  }

  foreach ($line in $replacementLines) {
    $updatedLines.Add($line)
  }

  if ($endIndex -lt $lines.Length -and $updatedLines[$updatedLines.Count - 1] -ne '') {
    $updatedLines.Add('')
  }

  for ($index = $endIndex; $index -lt $lines.Length; $index++) {
    $updatedLines.Add($lines[$index])
  }

  return ($updatedLines -join "`r`n").TrimEnd() + "`r`n"
}

$entries = Get-TrackedPlaceholderEntries -Path $ManifestPath
if ($entries.Count -eq 0) {
  throw "No tracked placeholder entries were found in $ManifestPath"
}

if (-not (Test-Path $ReportPath -PathType Leaf)) {
  throw "Missing source report not found: $ReportPath"
}

$stillPlaceholderBacked = New-Object System.Collections.Generic.List[string]
foreach ($entry in $entries) {
  if (Test-PlaceholderBacked -Path $entry.TargetPath) {
    $stillPlaceholderBacked.Add($entry.Name)
  }
}

$originalContent = Get-Content -Raw $ReportPath
$updatedContent = Set-PlaceholderSection -Content $originalContent -Items @($stillPlaceholderBacked)
$reportChanged = $updatedContent -ne $originalContent

if ($reportChanged -and -not $CheckOnly) {
  [System.IO.File]::WriteAllText((Resolve-Path $ReportPath), $updatedContent.TrimEnd() + "`r`n")
}

Set-WorkflowOutput -Name 'report_changed' -Value ($(if ($reportChanged) { 'true' } else { 'false' }))
Set-WorkflowOutput -Name 'placeholder_count' -Value $stillPlaceholderBacked.Count

if ($reportChanged -and $CheckOnly) {
  Write-Host "Missing source inventory is stale. Refresh $ReportPath before merging." -ForegroundColor Yellow
  exit 1
}

if ($reportChanged) {
  Write-Host "Updated $ReportPath with $($stillPlaceholderBacked.Count) placeholder-backed source entries." -ForegroundColor Green
} else {
  Write-Host "Missing source inventory is already current with $($stillPlaceholderBacked.Count) placeholder-backed source entries." -ForegroundColor Green
}
