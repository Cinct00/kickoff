# Set up ai-toolkit on this device (Windows PowerShell / pwsh).
#
#   irm https://raw.githubusercontent.com/Cinct00/ai-toolkit/main/install.ps1 | iex
#   .\install.ps1 --dry-run            # any toolkit.py install options pass through
#
# Clones (or updates) the toolkit into $env:AI_TOOLKIT_HOME (default ~\.ai-toolkit),
# then runs `toolkit.py install`. Skills are copied, not symlinked, on Windows.
$ErrorActionPreference = 'Stop'

$Repo = if ($env:AI_TOOLKIT_REPO) { $env:AI_TOOLKIT_REPO } else { 'https://github.com/Cinct00/ai-toolkit.git' }
$HomeDir = if ($env:AI_TOOLKIT_HOME) { $env:AI_TOOLKIT_HOME } else { Join-Path $HOME '.ai-toolkit' }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git is required' }
$Py = @('python3', 'python', 'py') | Where-Object { Get-Command $_ -ErrorAction SilentlyContinue } | Select-Object -First 1
if (-not $Py) { throw 'Python 3.9+ is required' }

if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot 'toolkit.json'))) {
    $HomeDir = $PSScriptRoot
} elseif (Test-Path (Join-Path $HomeDir '.git')) {
    git -C $HomeDir pull --ff-only
} else {
    git clone $Repo $HomeDir
}

& $Py (Join-Path $HomeDir 'scripts/toolkit.py') install @args
exit $LASTEXITCODE
