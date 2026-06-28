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
Invoke-ValidationCheck -Name 'ASH Canonical Semantic Integrity' -Command ($pythonCmd + @("$rootDir\.github\scripts\semantic_integrity_check.py", $rootDir))
Invoke-ValidationCheck -Name 'ASH Math Integrity' -Command ($pythonCmd + @("$rootDir\.github\scripts\math_integrity_check.py", $rootDir))
Invoke-ValidationCheck -Name 'ASH Downstream Conformance Artifacts' -Command ($pythonCmd + @("$rootDir\.github\scripts\downstream_conformance_check.py", $rootDir))
Invoke-ValidationCheck -Name 'YWE Package Acceptance Tests' -Command ($pythonCmd + @("$rootDir\.github\scripts\ywe_package_acceptance_check.py", $rootDir))
Invoke-ValidationCheck -Name 'Phase 8-9 Package Boundary Guardrail' -Command ($pythonCmd + @("$scriptDir\check_phase_8_9_package_boundary.py", $rootDir))
Invoke-ValidationCheck -Name 'Player Runtime State Guardrail' -Command ($pythonCmd + @("$scriptDir\check_player_runtime_state.py", $rootDir))
Invoke-ValidationCheck -Name 'Worldstate Location Mutation Guardrail' -Command ($pythonCmd + @("$scriptDir\check_worldstate_location_mutation.py", $rootDir))
Invoke-ValidationCheck -Name 'Quest NPC Lore Generation Guardrail' -Command ($pythonCmd + @("$scriptDir\check_quest_npc_lore_generation.py", $rootDir))
Invoke-ValidationCheck -Name 'Source Truth Alignment Guardrail' -Command ($pythonCmd + @("$scriptDir\check_source_truth_alignment.py", $rootDir))
Invoke-ValidationCheck -Name 'Ability Power Engine Guardrail' -Command ($pythonCmd + @("$scriptDir\check_ability_power_engine.py", $rootDir))
Invoke-ValidationCheck -Name 'Phase 15A Companion and Reward Foundation Guardrail' -Command ($pythonCmd + @("$scriptDir\check_phase_15a_companion_reward_foundation.py", $rootDir))
Invoke-ValidationCheck -Name 'Phase 16-17 Recovery and Phase 18 Unblock Guardrail' -Command ($pythonCmd + @("$scriptDir\check_phase_16_17_recovery.py", $rootDir))
Invoke-ValidationCheck -Name 'Repository Attribution Policy Guardrail' -Command ($pythonCmd + @("$scriptDir\check_repository_attribution_policy.py", $rootDir))

Write-Host "=========================================="
Write-Host "Results: $pass passed, $fail failed"
Write-Host "=========================================="

if ($fail -gt 0) {
  Write-Host 'VALIDATION FAILED'
  exit 1
}

Write-Host 'ALL CHECKS PASSED'
exit 0
