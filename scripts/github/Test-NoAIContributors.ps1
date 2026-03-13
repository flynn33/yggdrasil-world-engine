param(
  [string]$EventPath = $env:GITHUB_EVENT_PATH,
  [string]$EventName = $env:GITHUB_EVENT_NAME
)

$ErrorActionPreference = 'Stop'

$violations = New-Object System.Collections.Generic.List[string]
$blockedContributorPattern = '(?i)(chatgpt|codex|openai|claude|anthropic|gemini|copilot|\bgpt(?:-\d+(?:\.\d+)*)?\b|\bllm\b|artificial intelligence|\bai assistant\b)'

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

Write-Host 'Contributor identity checks passed. No blocked AI contributors were found in the evaluated commits.' -ForegroundColor Green
