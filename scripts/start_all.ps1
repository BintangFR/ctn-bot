# Start Ollama, the bot (live, every active account) and the monitor, each in a hidden
# window that restarts it if it stops. Safe to run twice: anything already running is left alone.
#
#   powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1      # start now
#   powershell -ExecutionPolicy Bypass -File scripts\stop_all.ps1       # stop everything
#
# The "CTN bot" scheduled task runs this at logon, so the bot survives reboots and closed
# terminals. Logs: logs\bot.out, logs\monitor.out, logs\ollama.out.

$root = Split-Path $PSScriptRoot -Parent
$py = Join-Path $root ".venv\Scripts\python.exe"
$jobs = [ordered]@{
    # If another Ollama already holds the port this one exits and retries, taking over if that one stops.
    ollama  = "ollama serve"
    watchdog = "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ollama_watchdog.ps1"
    bot     ="`"$py`" -u scripts\run_bot.py --all --live-after 0"
    monitor = "`"$py`" -u scripts\monitor.py --every 120"
}

function Test-Supervised($name) {
    [bool](Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
        Where-Object { $_.CommandLine -like "*supervise.ps1*-Name $name *" })
}

foreach ($name in $jobs.Keys) {
    if (Test-Supervised $name) { "$name already running"; continue }
    $cmd = $jobs[$name] -replace '"', '\"'
    Start-Process powershell -WindowStyle Hidden -ArgumentList (
        "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\supervise.ps1`" -Name $name -Cmd `"$cmd`"")
    "$name started"
    if ($name -eq "ollama") {
        # Give the model server a head start so the bot's first drafts use it.
        for ($i = 0; $i -lt 30; $i++) {
            try { Invoke-WebRequest -UseBasicParsing http://localhost:11434/api/tags -TimeoutSec 2 | Out-Null; break }
            catch { Start-Sleep 2 }
        }
    }
}
