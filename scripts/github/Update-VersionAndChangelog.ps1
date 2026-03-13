param(
  [string]$VersionFile = 'VERSION',
  [string]$ChangelogFile = 'CHANGELOG.md',
  [string]$EventPath = $env:GITHUB_EVENT_PATH
)

$ErrorActionPreference = 'Stop'

function Set-WorkflowOutput {
  param(
    [string]$Name,
    [string]$Value
  )

  if ($env:GITHUB_OUTPUT) {
    Add-Content -Path $env:GITHUB_OUTPUT -Value "$Name=$Value"
  }
}

function Get-CommitSubjects {
  param([string]$Path)

  if (-not $Path -or -not (Test-Path $Path)) {
    return @()
  }

  $event = Get-Content -Raw $Path | ConvertFrom-Json
  if (-not $event.before -or -not $event.after -or $event.before -match '^0+$') {
    return @()
  }

  $subjects = git log --format=%s "$($event.before)..$($event.after)"
  return @($subjects | Where-Object { $_ -and $_.Trim() })
}

function Get-BumpLevel {
  param([string[]]$Subjects)

  if (-not $Subjects -or $Subjects.Count -eq 0) {
    return 'none'
  }

  if ($Subjects | Where-Object { $_ -match '\[(skip version|skip release)\]' }) {
    return 'none'
  }

  if ($Subjects | Where-Object { $_ -match 'BREAKING CHANGE' -or $_ -match '^[^:]+!:' }) {
    return 'major'
  }

  if ($Subjects | Where-Object { $_ -match '^feat(\(.+\))?:' }) {
    return 'minor'
  }

  return 'patch'
}

function Bump-Version {
  param(
    [version]$CurrentVersion,
    [string]$Level
  )

  switch ($Level) {
    'major' { return [version]::new($CurrentVersion.Major + 1, 0, 0) }
    'minor' { return [version]::new($CurrentVersion.Major, $CurrentVersion.Minor + 1, 0) }
    'patch' { return [version]::new($CurrentVersion.Major, $CurrentVersion.Minor, $CurrentVersion.Build + 1) }
    default { return $CurrentVersion }
  }
}

if (-not (Test-Path $VersionFile)) {
  throw "Version file not found: $VersionFile"
}

$currentVersion = [version]((Get-Content -Raw $VersionFile).Trim())
$subjects = Get-CommitSubjects -Path $EventPath
$bumpLevel = Get-BumpLevel -Subjects $subjects

if ($bumpLevel -eq 'none') {
  Set-WorkflowOutput -Name 'version_changed' -Value 'false'
  Set-WorkflowOutput -Name 'version' -Value $currentVersion.ToString()
  exit 0
}

$newVersion = Bump-Version -CurrentVersion $currentVersion -Level $bumpLevel
[System.IO.File]::WriteAllText((Resolve-Path $VersionFile), $newVersion.ToString() + "`r`n")

$header = "# Changelog`r`n`r`nAll notable changes to this repository are documented in this file."
$existingBody = ''
if (Test-Path $ChangelogFile) {
  $existingContent = Get-Content -Raw $ChangelogFile
  if ($existingContent -match '(?s)^# Changelog\s+All notable changes to this repository are documented in this file\.\s*(.*)$') {
    $existingBody = $Matches[1].Trim()
  }
}

$dateStamp = (Get-Date).ToString('yyyy-MM-dd')
$entryLines = @(
  "## [$($newVersion.ToString())] - $dateStamp",
  '',
  "- Automatic $bumpLevel version bump.",
  '- Included commits:'
)

foreach ($subject in $subjects) {
  $entryLines += "- $subject"
}

$newContent = $header + "`r`n`r`n" + ($entryLines -join "`r`n")
if ($existingBody) {
  $newContent += "`r`n`r`n" + $existingBody
}

[System.IO.File]::WriteAllText((Join-Path (Get-Location) $ChangelogFile), $newContent + "`r`n")

Set-WorkflowOutput -Name 'version_changed' -Value 'true'
Set-WorkflowOutput -Name 'version' -Value $newVersion.ToString()
