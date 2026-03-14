param(
  [Parameter(Mandatory = $true)]
  [string]$Repository,

  [Parameter(Mandatory = $true)]
  [string]$Token,

  [string]$ConfigPath = '.github/wiki-sync.json'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ConfigPath)) {
  throw "Wiki sync config not found: $ConfigPath"
}

$config = Get-Content -Raw $ConfigPath | ConvertFrom-Json
$wikiDir = Join-Path $env:RUNNER_TEMP ('wiki-' + [guid]::NewGuid().ToString())
$wikiUrl = "https://x-access-token:$Token@github.com/$Repository.wiki.git"

try {
  git clone $wikiUrl $wikiDir | Out-Null
} catch {
  Write-Host "GitHub wiki is not available or not enabled yet. Skipping wiki sync."
  exit 0
}

if (-not (Test-Path $wikiDir)) {
  Write-Host "GitHub wiki clone did not succeed. Skipping wiki sync."
  exit 0
}

foreach ($page in $config.pages) {
  $sourcePath = Join-Path (Get-Location) $page.source
  if (-not (Test-Path $sourcePath)) {
    throw "Wiki sync source file not found: $($page.source)"
  }

  $destinationPath = Join-Path $wikiDir $page.destination
  $destinationDir = Split-Path -Parent $destinationPath
  if ($destinationDir) {
    New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
  }

  Copy-Item -Path $sourcePath -Destination $destinationPath -Force
}

$sidebarLines = @('# Wiki Pages', '')
foreach ($page in $config.pages) {
  $label = [System.IO.Path]::GetFileNameWithoutExtension($page.destination).Replace('-', ' ')
  $target = [System.IO.Path]::GetFileNameWithoutExtension($page.destination)
  $sidebarLines += "- [${label}]($target)"
}
[System.IO.File]::WriteAllText((Join-Path $wikiDir '_Sidebar.md'), ($sidebarLines -join "`r`n") + "`r`n")

$changes = git -C $wikiDir status --short
if (-not $changes) {
  Write-Host "Wiki is already up to date."
  exit 0
}

git -C $wikiDir config user.name 'github-actions[bot]'
git -C $wikiDir config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git -C $wikiDir add .
git -C $wikiDir commit -m 'docs: sync wiki pages from repository sources' | Out-Null
git -C $wikiDir push origin HEAD
