param(
    [int]$TimeoutSeconds = 60
)

# fail-fast
$ErrorActionPreference = 'Stop'

# 0) 事前クリーン
Write-Host "🧹 Cleaning up previous stack..."
docker compose --env-file .env.ci -f docker/compose.ci.yml down -v --remove-orphans

# 1) .env コピー
Copy-Item .env .env.ci -Force

# 2) ビルド（キャッシュなし）
Write-Host "🚀 Building full CI stack (no cache)..."
docker compose --env-file .env.ci `
    -f docker/compose.ci.yml `
    build --no-cache

# 3) デタッチ起動
Write-Host "🚀 Starting full CI stack..."
docker compose --env-file .env.ci `
    -f docker/compose.ci.yml `
    up -d

try {
    # 4) /docs ヘルスチェック
    Write-Host "⏳ Waiting for API at http://localhost:8001/docs ..."
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            Invoke-WebRequest http://localhost:8001/docs -UseBasicParsing -TimeoutSec 5 | Out-Null
            Write-Host "✅ API is healthy"
            break
        } catch {
            Write-Host "…still waiting"
            Start-Sleep -Seconds 3
        }
    }
    if ([DateTime]::UtcNow -ge $deadline) {
        throw "❌ API did not become healthy within $TimeoutSeconds seconds"
    }

    # 5) E2E テスト実行
    Write-Host "🧪 Running end-to-end tests..."
    pytest tests/it --maxfail=1 --disable-warnings -v
    $testExit = $LASTEXITCODE
} finally {
    # 6) 後片付け
    Write-Host "🛑 Tearing down Docker Compose stack..."
    docker compose --env-file .env.ci -f docker/compose.ci.yml down -v --remove-orphans
}

exit $testExit

