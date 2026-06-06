param(
  [string]$EventPath = $env:GITHUB_EVENT_PATH,
  [string]$EventName = $env:GITHUB_EVENT_NAME
)

$ErrorActionPreference = 'Stop'

$violations = New-Object System.Collections.Generic.List[string]

function Join-Codepoints {
  param([int[]]$Values)
  return -join ($Values | ForEach-Object { [char]$_ })
}

$blockedTerms = @(
  (Join-Codepoints 67,104,97,116,71,80,84),
  (Join-Codepoints 67,111,100,101,120),
  (Join-Codepoints 79,112,101,110,65,73),
  (Join-Codepoints 67,108,97,117,100,101),
  (Join-Codepoints 65,110,116,104,114,111,112,105,99),
  (Join-Codepoints 71,101,109,105,110,105),
  (Join-Codepoints 67,111,112,105,108,111,116),
  (Join-Codepoints 71,80,84),
  (Join-Codepoints 76,76,77),
  (Join-Codepoints 97,114,116,105,102,105,99,105,97,108,32,105,110,116,101,108,108,105,103,101,110,99,101),
  (Join-Codepoints 65,73,32,97,115,115,105,115,116,97,110,116)
)
$blockedContributorPattern = '(?i)(' + (($blockedTerms | ForEach-Object { '(?<![A-Za-z0-9])' + [regex]::Escape($_) + '(?![A-Za-z0-9])' }) -join '|') + ')'

function Get-CommitRefs {
  param(
    [string]$Path,
    [string]$Name
  )

  $revisionRange = $null

  if ($Path -and (Test-Path $Path -PathType Leaf)) {
    $event = Get-Content -Raw $Path | ConvertFrom-Json -Depth 32

    switch ($Name) {
      'pull_request' {
        $base = $event.pull_request.base.sha
        $head = $event.pull_request.head.sha
        if ($base -and $head) {
          $revisionRange = "$base..$head"
        }
      }
      'push' {
        $base = $event.before
        $head = $event.after
        if ($base -and $head -and $base -notmatch '^0+$') {
          $revisionRange = "$base..$head"
        } elseif ($head) {
          return @($head)
        }
      }
    }
  }

  if ($revisionRange) {
    return @((git rev-list $revisionRange) | Where-Object { $_ -and $_.Trim() } | Select-Object -Unique)
  }

  git rev-parse --verify HEAD *> $null
  if ($LASTEXITCODE -ne 0) {
    return @()
  }

  git rev-parse --verify HEAD~1 *> $null
  if ($LASTEXITCODE -eq 0) {
    return @((git rev-list 'HEAD~1..HEAD') | Where-Object { $_ -and $_.Trim() } | Select-Object -Unique)
  }

  return @((git rev-parse HEAD).Trim())
}

function Test-Identity {
  param(
    [string]$CommitRef,
    [string]$Role,
    [string]$Name,
    [string]$Email
  )

  $identity = "$Name <$Email>"
  if ($identity -match $script:blockedContributorPattern) {
    $violations.Add("Commit $CommitRef contains blocked $Role identity '$identity'.")
  }
}

$commitRefs = Get-CommitRefs -Path $EventPath -Name $EventName
if ($commitRefs.Count -eq 0) {
  Write-Host 'No commits were available to validate contributor identities.' -ForegroundColor Yellow
  exit 0
}

foreach ($commitRef in $commitRefs) {
  $authorName = (git show -s --format='%an' $commitRef).Trim()
  $authorEmail = (git show -s --format='%ae' $commitRef).Trim()
  $committerName = (git show -s --format='%cn' $commitRef).Trim()
  $committerEmail = (git show -s --format='%ce' $commitRef).Trim()
  $message = git show -s --format=%B $commitRef

  Test-Identity -CommitRef $commitRef -Role 'author' -Name $authorName -Email $authorEmail
  Test-Identity -CommitRef $commitRef -Role 'committer' -Name $committerName -Email $committerEmail

  $coAuthorMatches = [regex]::Matches($message, '(?im)^co-authored-by:\s*(.+?)\s*<([^>]+)>\s*$')
  foreach ($match in $coAuthorMatches) {
    Test-Identity `
      -CommitRef $commitRef `
      -Role 'co-author' `
      -Name $match.Groups[1].Value.Trim() `
      -Email $match.Groups[2].Value.Trim()
  }
}

if ($violations.Count -gt 0) {
  Write-Host 'Contributor identity violations found:' -ForegroundColor Red
  foreach ($violation in $violations) {
    Write-Host " - $violation" -ForegroundColor Red
  }
  exit 1
}

Write-Host 'Contributor identity checks passed. No blocked contributor identity markers were found in the evaluated commits.' -ForegroundColor Green
