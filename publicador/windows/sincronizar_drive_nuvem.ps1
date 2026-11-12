# Script de sincronização: Google Drive local -> Repositório Nuvem (GitHub)
# Copia carrosséis da pasta do Drive para a pasta carrosseis/ e faz push no GitHub

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " ☁️ SINCRONIZAR GOOGLE DRIVE COM A NUVEM DO GITHUB        " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$DriveQueue = "C:\Users\luizr\Meu Drive (aidealabbr@gmail.com)\Clientes\otalogia\06-Aprovados-para-Postar"
$RepoQueue = Join-Path $PSScriptRoot "..\..\fila"

if (-not (Test-Path $DriveQueue)) {
    Write-Host "❌ Pasta do Google Drive não encontrada: $DriveQueue" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $RepoQueue)) {
    New-Item -ItemType Directory -Path $RepoQueue -Force | Out-Null
}

Write-Host "Copiando carrosséis de:" -ForegroundColor Cyan
Write-Host "  $DriveQueue" -ForegroundColor White
Write-Host "Para a nuvem local em:" -ForegroundColor Cyan
Write-Host "  $RepoQueue" -ForegroundColor White

Copy-Item -Path "$DriveQueue\*" -Destination $RepoQueue -Recurse -Force

Write-Host "`nEnviando atualizações para o GitHub..." -ForegroundColor Yellow
git add fila/
git commit -m "chore(sync): sincronizar carrosseis aprovados do Google Drive para a nuvem"
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Sincronização concluída com sucesso! A nuvem do GitHub agora tem os carrosséis mais recentes." -ForegroundColor Green
} else {
    Write-Host "`nℹ️ Nenhuma alteração pendente para enviar ao GitHub." -ForegroundColor Gray
}
