<#
 start.ps1
 ── ３層構造 Compose の起動／停止スクリプト
 Usage: .\start.ps1 -Down -Up
#>

param(
  [switch]$Down,
  [switch]$Up
)

# 1) 第１層(core)＋第２層(ports) をベースに固定
$baseFlags = @(
  "--env-file", ".env",
  "-f", "docker/compose.core.yml",
  "-f", "docker/compose.ports.yml"
)

# 2) 第３層（オーバーライド）リスト
$overrides = @(
  "db",
  "redis",
  "exporter.redis",
  "exporter.celery",
  "beat",
  "worker",
  "flower",
  "prom",
  "grafana",
  "override-ports"
)

# 3) フラットなフラグ配列を組み立て
$flags = $baseFlags + ($overrides | ForEach-Object { "-f"; "docker/compose.$_.yml" })

function Check-Compose {
  Write-Host "▶ Compose 構文チェック…" -NoNewline
  & docker compose @flags config > $null 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ 構文エラーがあります: (${overrides -join ', '}) を確認してください" -ForegroundColor Red
    exit 1
  }
  Write-Host "`n✅ Compose 構文は有効です" -ForegroundColor Green
}

# ------------------------------------------------------------
# Redis ポート競合チェック
#   HOST_REDIS_PORT で指定されたポート (未指定なら 6379) が
#   既に LISTEN されていないか確認する。
# ------------------------------------------------------------
function Port-InUse([int]$port) {
  $listener = New-Object System.Net.Sockets.TcpListener([Net.IPAddress]::Loopback, $port)
  try {
    $listener.Start(); $listener.Stop(); return $false
  }
  catch {
    return $true
  }
}

function Check-RedisPort {
  $port = if ($Env:HOST_REDIS_PORT) { [int]$Env:HOST_REDIS_PORT } else { 6379 }
  if (Port-InUse $port) {
    Write-Host "`n❌ Port $port is already in use. Set HOST_REDIS_PORT to a free port." -ForegroundColor Red
    exit 1
  }
}

if ($Down) {
  Write-Host "▶ 停止 & リソース削除…" -ForegroundColor Cyan
  & docker compose @flags down -v --remove-orphans
}

if ($Up) {
  Check-Compose
  Check-RedisPort

  Write-Host "`n▶ サービス起動中… (worker=3)" -ForegroundColor Cyan
  & docker compose @flags up -d --build --scale worker=3

  Write-Host "`n▶ コンテナの起動状況：" -ForegroundColor Cyan
  & docker compose @flags ps
}

if (-not ($Down -or $Up)) {
  Write-Host "Usage: .\start.ps1 -Down -Up" -ForegroundColor Yellow
}
