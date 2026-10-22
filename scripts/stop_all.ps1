# Stop what scripts\start_all.ps1 started: the supervisors first (so nothing restarts),
# then the bot, the monitor and Ollama.
$procs = Get-CimInstance Win32_Process
$procs | Where-Object { $_.Name -eq "powershell.exe" -and $_.CommandLine -like "*supervise.ps1*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; "stopped supervisor $($_.ProcessId)" }
$procs | Where-Object { ($_.Name -eq "python.exe" -and $_.CommandLine -match "run_bot\.py|monitor\.py") -or
                        ($_.Name -eq "powershell.exe" -and $_.CommandLine -like "*ollama_watchdog.ps1*") } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; "stopped $($_.CommandLine -replace '.*scripts\\', '')" }
Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
"done"
