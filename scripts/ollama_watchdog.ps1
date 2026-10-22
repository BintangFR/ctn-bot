# Ollama can hang with the model loaded: the process lives but every request times out,
# so the bot falls back to the slow, rate-limited competition model. Every 5 minutes, send
# a one-token request; after two failures in a row, kill Ollama so its supervisor restarts it.
$fails = 0
while ($true) {
    Start-Sleep 300
    $body = '{"model":"qwen2.5:7b","prompt":"hi","stream":false,"options":{"num_predict":1}}'
    try {
        Invoke-RestMethod -Method Post http://localhost:11434/api/generate -Body $body `
            -ContentType "application/json" -TimeoutSec 120 | Out-Null
        $fails = 0
    } catch {
        $fails++
        "[$(Get-Date -Format s)] ollama probe failed ($fails): $($_.Exception.Message)"
        if ($fails -ge 2) {
            Get-Process ollama*, llama* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
            "[$(Get-Date -Format s)] killed ollama; its supervisor restarts it"
            $fails = 0
        }
    }
}
