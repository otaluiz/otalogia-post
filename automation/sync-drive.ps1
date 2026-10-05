# Puxa o repositório (commits da rotina na nuvem) e copia cada carrossel em rascunho para o Drive local.
# Disparado pelo Windows Task Scheduler (tarefa "otalogia-sync-drive"): no logon e de hora em hora.
$ErrorActionPreference = "Stop"
$repo = "D:\claude\otalogia-post"
$destino = "C:\Users\luizr\Meu Drive (aidealabbr@gmail.com)\Clientes\otalogia\04-Carrosseis"
$log = Join-Path $repo "automation\logs\sync-drive.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
function Log($m) { "$(Get-Date -Format s) $m" | Add-Content -Encoding utf8 $log }

Set-Location $repo
git pull --ff-only --quiet 2>&1 | ForEach-Object { Log "git: $_" }

Get-ChildItem (Join-Path $repo "carrosseis") -Directory | ForEach-Object {
    $meta = Join-Path $_.FullName "png\metadata.json"
    if (-not (Test-Path $meta)) { return }
    $status = (Get-Content -Raw -Encoding utf8 $meta | ConvertFrom-Json).status
    if ($status -ne "rascunho") { return }
    $alvo = Join-Path $destino $_.Name
    if (Test-Path (Join-Path $alvo "metadata.json")) { return }   # já enviado
    New-Item -ItemType Directory -Force -Path $alvo | Out-Null
    Copy-Item (Join-Path $_.FullName "png\*") $alvo
    $leg = Join-Path $_.FullName "legenda.md"
    if (Test-Path $leg) { Copy-Item $leg $alvo }
    Log "enviado: $($_.Name)"
}
