# =================================================================
# gen-cert.ps1  ─  self-signed TLS cert を ops\cert.pem / key.pem に生成
# =================================================================
$ErrorActionPreference = 'Stop'

# 1. フォルダと出力パス
$opsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$certPath = Join-Path $opsDir 'cert.pem'
$keyPath = Join-Path $opsDir 'key.pem'

# 2. 既にあるならスキップ   ← ★ TEST-PATH を () で囲む！
if ( (Test-Path $certPath) -and (Test-Path $keyPath) ) {
    Write-Host "cert.pem / key.pem already exist -> $opsDir"
    exit 0
}

# 3. OpenSSL コマンド確認
if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
    Write-Error "OpenSSL not found in PATH.  Re-open a shell after installing."
    exit 1
}

# 4. PEM 生成 (10 年, RSA2048, CN=localhost)
$args = @(
    'req', '-x509', '-nodes', '-days', '3650',
    '-newkey', 'rsa:2048',
    '-subj', '/CN=localhost',
    '-keyout', $keyPath,
    '-out', $certPath
)
& openssl $args | Out-Null

Write-Host "PEM files generated -> $opsDir"
