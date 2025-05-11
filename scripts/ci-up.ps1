<#
.SYNOPSIS
  CI用 Docker スタック起動スクリプト

.DESCRIPTION
  このスクリプトは以下を自動化します。
    1) 既存コンテナ、ネットワーク、ボリュームの完全削除
    2) Docker Buildx およびシステムキャッシュのクリーンアップ
    3) キャッシュなしでのイメージビルド＆スタック起動（--wait で全サービスの起動完了を待機）
    4) 起動中コンテナの一覧表示
    5) HTTP エンドポイントの疎通チェック

.EXAMPLE
  .\ci-up.ps1
  # デフォルトの compose.ci.yml と .env を使って実行
#>
param(
  [string]$ComposeFile = ".\docker\compose.ci.yml",
  [string]$EnvFile     = ".env"
)

# 1) プロジェクトルート確認
Write-Host "🌱 Starting CI up from" (Get-Location)

# 2) スタック停止＆完全削除
Write-Host "`n🚧 Stopping & removing all resources..."
docker compose --env-file $EnvFile -f $ComposeFile down -v --remove-orphans

# 3) ビルダーキャッシュとシステムキャッシュをクリーンアップ
Write-Host "`n🧹 Pruning builder and system caches..."
docker buildx prune --all --force
docker system prune --all --volumes --force

# 4) イメージのビルド＆バックグラウンド起動 (--no-cache)
Write-Host "`n🔨 Building images (no-cache) & starting stack..."
docker compose --env-file $EnvFile -f $ComposeFile build --no-cache
docker compose --env-file $EnvFile -f $ComposeFile up -d --wait

# 5) 起動中コンテナの一覧表示
Write-Host "`n📦 Containers status:"
docker compose --env-file $EnvFile -f $ComposeFile ps

# 6) HTTP エンドポイント疎通チェック
$urls = @(
  "http://localhost:8001/docs",
  "http://localhost:9090/-/ready",
  "http://localhost:9121/metrics",
  "http://localhost:9808/metrics"
)

Write-Host "`n🔎 Checking endpoints..."
for ($i = 1; $i -le 12; $i++) {
  Write-Host "  Try $i/12..."
  $allOK = $true
  foreach ($u in $urls) {
    try {
      Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 3 | Out-Null
      Write-Host "    $u → OK"
    } catch {
      Write-Host "    $u → NG" -ForegroundColor Red
      $allOK = $false
    }
  }
  if ($allOK) {
    Write-Host "✅ All endpoints are healthy!"
    break
  }
  Start-Sleep -Seconds 5
}

if (-not $allOK) {
  Write-Error "❌ Some endpoints failed to respond. Please check logs."
  exit 1
}

Write-Host "`n🎉 CI stack is up and healthy!"