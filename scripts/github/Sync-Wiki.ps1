param(
  [string]$Repository = 'flynn33/yggdrasil-world-engine',
  [string]$SourceRoot = (Join-Path $PSScriptRoot '../..'),
  [string]$SourceRevision,
  [string]$WikiDirectory,
  [string]$Python = 'python',
  [switch]$Publish
)

$ErrorActionPreference = 'Stop'
if ($Repository -ne 'flynn33/yggdrasil-world-engine') {
  throw 'This publication route is limited to the owner repository.'
}
$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$wikiUrl = "https://github.com/$Repository.wiki.git"

function Invoke-WikiGit {
  param([string]$Directory, [string[]]$GitArguments)
  $value = & git -C $Directory @GitArguments
  if ($LASTEXITCODE -ne 0) { throw 'Wiki Git operation failed.' }
  return $value
}

if (-not $SourceRevision) {
  $SourceRevision = Invoke-WikiGit $SourceRoot @('rev-parse', 'HEAD')
}
if ($SourceRevision -notmatch '^[0-9a-f]{40}$') {
  throw 'Supply a complete source commit SHA.'
}

# Identity is verified only when this local invocation requests publication.
# Git continues to use the existing credential manager; no secret enters a URL.
if ($Publish) {
  $credentialOutput = "protocol=https`nhost=github.com`n`n" | git credential fill
  if ($LASTEXITCODE -ne 0) { throw 'The existing GitHub credential could not be read.' }
  $wikiCredential = @{}
  foreach ($line in $credentialOutput) {
    $pair = $line -split '=', 2
    if ($pair.Count -eq 2) { $wikiCredential[$pair[0]] = $pair[1] }
  }
  try {
    if (-not $wikiCredential.password) { throw 'No existing GitHub token is available.' }
    $account = Invoke-RestMethod -Uri 'https://api.github.com/user' -Headers @{
      Authorization = ('Bearer ' + $wikiCredential.password)
      Accept = 'application/vnd.github+json'
      'X-GitHub-Api-Version' = '2022-11-28'
    }
    if ($account.login -ne 'flynn33') { throw 'Wiki publication requires the flynn33 account.' }
  } finally {
    $wikiCredential.Clear()
    $credentialOutput = $null
  }
}

$remoteLine = & git ls-remote $wikiUrl refs/heads/master
if ($LASTEXITCODE -ne 0 -or -not $remoteLine) { throw 'Wiki master could not be read.' }
$baseRevision = ($remoteLine -split '\s+')[0]
if (-not $WikiDirectory) {
  $WikiDirectory = Join-Path $env:TEMP ('ywe-wiki-' + [guid]::NewGuid().ToString('N'))
  & git clone --no-hardlinks --branch master $wikiUrl $WikiDirectory
  if ($LASTEXITCODE -ne 0) { throw 'Wiki clone failed.' }
}
$WikiDirectory = (Resolve-Path -LiteralPath $WikiDirectory).Path
$wikiHead = Invoke-WikiGit $WikiDirectory @('rev-parse', 'HEAD')
if ($wikiHead -ne $baseRevision) { throw 'Wiki checkout does not match current remote master.' }
& git -C $WikiDirectory diff --cached --quiet
if ($LASTEXITCODE -ne 0) { throw 'Preserve existing staged wiki changes before this publication route.' }

$reportPrefix = Join-Path $env:TEMP ('ywe-wiki-readback-' + [guid]::NewGuid().ToString('N'))
$prepareReport = $reportPrefix + '-prepare.json'
$verifyReport = $reportPrefix + '-verify.json'
$generator = Join-Path $SourceRoot 'scripts/github/prepare_wiki.py'
& $Python -B $generator prepare --source-root $SourceRoot --wiki-root $WikiDirectory --source-revision $SourceRevision --report $prepareReport
if ($LASTEXITCODE -ne 0) { throw 'Wiki preparation refused.' }
& $Python -B $generator verify --source-root $SourceRoot --wiki-root $WikiDirectory --source-revision $SourceRevision --report $verifyReport
if ($LASTEXITCODE -ne 0) { throw 'Wiki readback refused.' }
Write-Host "Prepared wiki: $WikiDirectory"
Write-Host "Readback report: $verifyReport"
if (-not $Publish) { return }

$prepared = Get-Content -LiteralPath $prepareReport -Raw | ConvertFrom-Json
if ($prepared.changed_paths.Count -eq 0) {
  Write-Host 'Wiki already matches the pinned source projection.'
  return
}
Invoke-WikiGit $WikiDirectory @('config', 'user.name', 'Jim Daley') | Out-Null
Invoke-WikiGit $WikiDirectory @('config', 'user.email', '94642455+flynn33@users.noreply.github.com') | Out-Null
Invoke-WikiGit $WikiDirectory (@('add', '--') + @($prepared.changed_paths)) | Out-Null
Invoke-WikiGit $WikiDirectory @('-c', 'commit.gpgsign=false', 'commit', '-m', "Update wiki from repository $SourceRevision") | Out-Null
$wikiRevision = Invoke-WikiGit $WikiDirectory @('rev-parse', 'HEAD')
$remoteLine = & git ls-remote $wikiUrl refs/heads/master
if ($LASTEXITCODE -ne 0 -or ($remoteLine -split '\s+')[0] -ne $baseRevision) {
  throw 'Wiki master changed during preparation; reconcile the existing work before publishing.'
}
Invoke-WikiGit $WikiDirectory @('push', $wikiUrl, 'HEAD:refs/heads/master') | Out-Null
$remoteLine = & git ls-remote $wikiUrl refs/heads/master
if ($LASTEXITCODE -ne 0 -or ($remoteLine -split '\s+')[0] -ne $wikiRevision) {
  throw 'Published wiki revision did not match remote readback.'
}
& $Python -B $generator verify --source-root $SourceRoot --wiki-root $WikiDirectory --source-revision $SourceRevision --report ($reportPrefix + '-published.json')
if ($LASTEXITCODE -ne 0) { throw 'Published wiki projection failed local byte readback.' }
Write-Host "Published wiki master SHA verified: $wikiRevision; pinned page bytes verified in the local checkout."
