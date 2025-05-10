<#
    reset.ps1  –  dev 環境の簡易リセット
      1. uvicorn / celery プロセスを kill
      2. localhost:6379 を LISTEN している Redis を kill
      3. __pycache__ を掃除
      4. Redis コンテナを再生成 (-p 6379:6379)
#>

Write-Host "▶ stopping uvicorn / celery …"
Get-Process -Name uvicorn, celery -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "▶ killing local Redis on 6379 if exists …"
$redisPid = (Get-NetTCPConnection -State Listen -LocalPort 6379 -ErrorAction SilentlyContinue |
             Select-Object -First 1 -ExpandProperty OwningProcess)

if ($redisPid) {
    Stop-Process -Id $redisPid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Write-Host "▶ cleaning __pycache__ …"
Get-ChildItem -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "▶ recreating Redis container (6379:6379) …"
docker rm -f redis_nopass 2>$null | Out-Null
docker run -d --name redis_nopass -p 6379:6379 redis:7-alpine | Out-Null

Write-Host "✅ Redis should now be listening on localhost:6379"
