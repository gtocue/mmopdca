<#
.SYNOPSIS
  本番ジョブの登録＆動作確認を自動化するテストスクリプト

.PARAMETER WaitSeconds
  Beat がジョブをスケジュールするまでの待機秒数。デフォルト 70 秒。
#>
param(
    [int]$WaitSeconds = 70
)

# Compose に渡すファイル群
$composeArgs = @(
    "--env-file", ".env",
    "-f", "docker\compose.core.yml",
    "-f", "docker\compose.db.yml",
    "-f", "docker\compose.redis.yml"
)

Write-Host "🛠 Building & starting services..."
docker compose @composeArgs build --no-cache
docker compose @composeArgs up -d --build

Write-Host "⏳ Waiting $WaitSeconds seconds for Beat to schedule jobs..."
Start-Sleep -Seconds $WaitSeconds

# 1) Beat ログのスケジューリング確認
Write-Host "🔍 Checking Beat logs for scheduling events..."
$beatLogs = docker compose @composeArgs logs beat --tail 100
if ($beatLogs | Select-String "Scheduler: Sending due task print-heartbeat-every-minute") {
    Write-Host "✅ Beat logged scheduling event."
}
else {
    Write-Error "❌ Beat did not log scheduling of the job."
    docker compose @composeArgs down
    exit 1
}

# 2) Worker ログの実行確認
Write-Host "🔍 Checking Worker logs for execution events..."
$workerLogs = docker compose @composeArgs logs worker --tail 100
if ($workerLogs | Select-String "\[heartbeat\]") {
    Write-Host "✅ Worker logged heartbeat execution."
}
else {
    Write-Error "❌ Worker did not log the heartbeat execution."
    docker compose @composeArgs down
    exit 1
}

# 成功時はサービスをクリーンアップ
Write-Host "✅ All checks passed. Bringing services down..."
docker compose @composeArgs down

Write-Host "✅ Test complete."
