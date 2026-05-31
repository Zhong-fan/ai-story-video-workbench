Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
& (Join-Path $RootDir "start-workbench.ps1") @args
