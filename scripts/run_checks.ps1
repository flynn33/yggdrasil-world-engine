#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = if (Get-Command py -ErrorAction SilentlyContinue) {
  @('py', '-3')
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
  @('python3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  @('python')
} else {
  throw 'No supported Python launcher found (tried py -3, python3, python).'
}

$runner = $python[0]
$pythonArgs = if ($python.Length -gt 1) { $python[1..($python.Length - 1)] } else { @() }
& $runner @pythonArgs "$scriptDir\validate_repository.py" @args
exit $LASTEXITCODE
