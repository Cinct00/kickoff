# Set up Kickoff on this device (Windows PowerShell / pwsh).
#
#   irm https://raw.githubusercontent.com/Cinct00/kickoff/main/install.ps1 | iex
#   .\install.ps1 --dry-run            # any toolkit.py install options pass through
#
# Clones (or updates) the toolkit into $env:KICKOFF_HOME (default ~\.kickoff),
# then runs `toolkit.py install`. Skills are copied, not symlinked, on Windows.
# Everything runs inside a function so that, under `irm | iex`, a failure returns to the prompt instead of
# closing the user's PowerShell window, and $ErrorActionPreference does not leak into their session.
function Install-Kickoff {
    param([string[]]$PassThru)
    $ErrorActionPreference = 'Stop'

    $Repo = if ($env:KICKOFF_REPO) { $env:KICKOFF_REPO } else { 'https://github.com/Cinct00/kickoff.git' }
    $HomeDir = if ($env:KICKOFF_HOME) { $env:KICKOFF_HOME } else { Join-Path $HOME '.kickoff' }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Write-Error 'git is required' -ErrorAction Continue; return 1 }
    $Py = @('python3', 'python', 'py') | Where-Object { Get-Command $_ -ErrorAction SilentlyContinue } | Select-Object -First 1
    if (-not $Py) { Write-Error 'Python 3.9+ is required' -ErrorAction Continue; return 1 }

    if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot 'toolkit.json'))) {
        $HomeDir = $PSScriptRoot
    } elseif (Test-Path (Join-Path $HomeDir '.git')) {
        git -C $HomeDir pull --ff-only | Out-Host
        if ($LASTEXITCODE -ne 0) { Write-Error "git pull failed in $HomeDir" -ErrorAction Continue; return $LASTEXITCODE }
    } else {
        git clone $Repo $HomeDir | Out-Host
        if ($LASTEXITCODE -ne 0) { Write-Error "git clone of $Repo failed" -ErrorAction Continue; return $LASTEXITCODE }
    }

    & $Py (Join-Path $HomeDir 'scripts/toolkit.py') install @PassThru | Out-Host
    return $LASTEXITCODE
}

$code = Install-Kickoff -PassThru $args
$global:LASTEXITCODE = $code
# Only a script run from a file may exit; under `irm | iex` exit would close the user's terminal.
if ($PSCommandPath) { exit $code }
