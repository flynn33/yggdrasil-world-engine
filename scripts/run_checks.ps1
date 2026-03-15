#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

Write-Host "=========================================="
Write-Host "Yggdrasil World Engine -- Validation Suite"
Write-Host "=========================================="
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

$pass = 0
$fail = 0

function Resolve-PythonCommand {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return @('py', '-3')
  }

  if (Get-Command python3 -ErrorAction SilentlyContinue) {
    return @('python3')
  }

  if (Get-Command python -ErrorAction SilentlyContinue) {
    return @('python')
  }

  throw 'No supported Python launcher found (tried py -3, python3, python).'
}

function Invoke-ValidationCheck {
  param(
    [string]$Name,
    [string[]]$Command
  )

  Write-Host "--- $Name ---"
  $runner = $Command[0]
  $args = if ($Command.Length -gt 1) { $Command[1..($Command.Length - 1)] } else { @() }
  & $runner @args
  if ($LASTEXITCODE -eq 0) {
    Write-Host "PASS: $Name"
    $script:pass++
  } else {
    Write-Host "FAIL: $Name"
    $script:fail++
  }
  Write-Host ""
}

$pythonCmd = Resolve-PythonCommand

Invoke-ValidationCheck -Name 'Architecture Validation' -Command ($pythonCmd + @("$scriptDir\validate_architecture.py", $rootDir))
Invoke-ValidationCheck -Name 'Schema Validation' -Command ($pythonCmd + @("$scriptDir\validate_schemas.py", $rootDir))
Invoke-ValidationCheck -Name 'ASH Compliance Validation' -Command ($pythonCmd + @("$scriptDir\validate_ash_compliance.py", $rootDir))
Invoke-ValidationCheck -Name 'Discussion Agent Validation' -Command ($pythonCmd + @("$scriptDir\github\discussion_agent.py", "--validate-config", "--root", $rootDir))
Invoke-ValidationCheck -Name 'Discussion Topic Generator Validation' -Command ($pythonCmd + @("$scriptDir\github\discussion_topic_agent.py", "--validate-config", "--root", $rootDir))
Invoke-ValidationCheck -Name 'Discussion Moderation Validation' -Command ($pythonCmd + @("$scriptDir\github\discussion_moderation_agent.py", "--validate-config", "--root", $rootDir))

Write-Host "=========================================="
Write-Host "Results: $pass passed, $fail failed"
Write-Host "=========================================="

if ($fail -gt 0) {
  Write-Host 'VALIDATION FAILED'
  exit 1
}

Write-Host 'ALL CHECKS PASSED'
exit 0
