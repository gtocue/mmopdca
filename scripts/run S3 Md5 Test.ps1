# File: scripts/run S3 Md5 Test.ps1
param(
    [int]$WaitSeconds = 60
)

# ① Compose に渡す引数を配列で定義
$composeArgs = @(
    "--env-file", ".env",
    "-f", ".\docker\compose.core.yml",
    "-f", ".\docker\compose.db.yml",
    "-f", ".\docker\compose.redis.yml"
)

Write-Host "🛠 Building & starting services..."
docker compose @composeArgs build --no-cache
docker compose @composeArgs up -d --build

Write-Host "⏳ Waiting $WaitSeconds seconds for Beat to schedule jobs..."
Start-Sleep -Seconds $WaitSeconds

Write-Host "🔍 Inspecting scheduled tasks on worker..."
docker compose @composeArgs exec worker celery -A core.celery_app:celery_app inspect scheduled

Write-Host "🔍 Checking Beat logs for scheduling events..."
docker compose @composeArgs logs beat --tail 50

Write-Host "🔍 Checking Worker logs for execution events..."
docker compose @composeArgs logs worker --tail 50

Write-Host "✅ All checks passed. Bringing services down..."
docker compose @composeArgs down
