$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$repoRoot = Resolve-Path (Join-Path $root "..")
$source = Join-Path $root "agents\clerk.md"
$targetDir = Join-Path $repoRoot ".claude\agents"
$target = Join-Path $targetDir "clerk.md"

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
if (Test-Path -LiteralPath $target) {
    Remove-Item -LiteralPath $target -Force
}

try {
    New-Item -ItemType SymbolicLink -Path $target -Target $source | Out-Null
} catch {
    New-Item -ItemType HardLink -Path $target -Target $source | Out-Null
}

Write-Host "Linked $target -> $source"
