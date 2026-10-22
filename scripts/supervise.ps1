# Run one command forever: if it stops or crashes, wait 30s and start it again.
# Output goes to logs\<Name>.out. Started by scripts\start_all.ps1; not usually run by hand.
param([Parameter(Mandatory)][string]$Name, [Parameter(Mandatory)][string]$Cmd)

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$log = Join-Path $root "logs\$Name.out"
$env:PYTHONIOENCODING = "utf-8"

while ($true) {
    cmd /c "echo [%date% %time%] starting $Name>> `"$log`""
    cmd /c "`"$Cmd >> `"$log`" 2>&1`""   # outer quotes: cmd strips one pair
    cmd /c "echo [%date% %time%] $Name exited with code %errorlevel%; restarting in 30s>> `"$log`""
    Start-Sleep 30
}
