# Post-commit hook: regenerate Understand-Anything knowledge graph
# when harness documentation changes.

$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel

# Check if the commit touched any files in the documented scope
$changed = git diff-tree --no-commit-id --name-only -r HEAD -- `
    "manual/" `
    "regs/omni-regs/ssot/" `
    2>$null

if (-not $changed) {
    exit 0
}

Write-Host "[post-commit] Harness docs changed - regenerating knowledge graph..."

try {
    Push-Location $repoRoot
    claude --print "Run the understand skill to regenerate the knowledge graph. Target: manual/ and regs/omni-regs/ssot/. Output to .understand-anything/ at repo root. Do not ask questions, just run it."
    Pop-Location
    Write-Host "[post-commit] Knowledge graph regenerated."
} catch {
    Pop-Location
    Write-Host "[post-commit] Warning: knowledge graph regeneration failed. Run 'understand' manually."
    exit 0
}
