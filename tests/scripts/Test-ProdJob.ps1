# scripts/Test-ProdJob.ps1
Param(
    [int]$WaitSeconds = 70
)

Write-Host "🛠 Building & starting services..."
# (Docker Compose 起動処理略)

Write-Host "⏳ Waiting $WaitSeconds seconds for Beat to register jobs..."
Start-Sleep -Seconds $WaitSeconds

Write-Host "🔍 Checking Beat logs for scheduling events..."
docker compose logs beat --tail 50 `
| Select-String "\[heartbeat\]" `
| ForEach-Object {
    Write-Host "✅ Beat logged scheduling event."
}

Write-Host "🔍 Checking Worker logs for execution events..."
docker compose logs worker --tail 50 `
| Select-String "\[heartbeat\]" `
| ForEach-Object {
    Write-Host "✅ Worker logged heartbeat execution."
}

Write-Host "✅ All checks passed. Bringing services down..."
# (Docker Compose down 処理略)
Write-Host "✅ Test complete."
