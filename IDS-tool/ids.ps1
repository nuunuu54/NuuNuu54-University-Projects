param(
    [Parameter(ValueFromRemainingArguments=$true)]
    $Args
)

# PowerShell wrapper to run the Python CLI. Usage: .\ids.ps1 train
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venv = Join-Path $root '.venv\Scripts\python.exe'
if (Test-Path $venv) {
    $py = $venv
} else {
    $py = 'python'
}

& $py -m src.cli @Args
