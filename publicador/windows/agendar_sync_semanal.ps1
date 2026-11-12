# Script para criar a tarefa agendada automática no Windows
# Sincroniza a fila semanal do Google Drive para a nuvem do GitHub Actions

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " ⚙️ AGENDAR SINCRONIZAÇÃO SEMANAL AUTOMÁTICA (WINDOWS)    " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$TaskName = "Otalogia-Sync-Semanal-Nuvem"
$PythonExe = (Get-Command python).Source
$ScriptPath = Join-Path $PSScriptRoot "..\sync_semanal_drive.py"

# Executa em segundo plano sem janela
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ScriptPath`"" -WorkingDirectory $PSScriptRoot

# Dispara todo domingo às 22:00 (ou segunda às 06:00 de Cuiabá)
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday, Monday -At 06:00AM

# Configurações de resiliência (se o PC estiver dormindo, roda assim que acordar)
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15)

# Registrar a tarefa
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Sincroniza automaticamente a fila semanal de carrosséis da Otalogia do Google Drive para o GitHub Actions" | Out-Null

if ($LASTEXITCODE -eq 0 -or (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)) {
    Write-Host "`n✅ SUCESSO! A tarefa semanal foi registrada no Windows com sucesso!" -ForegroundColor Green
    Write-Host "Nome da tarefa: $TaskName" -ForegroundColor White
    Write-Host "Frequência: Semanal (Domingos e Segundas às 06:00 da manhã)" -ForegroundColor White
    Write-Host "Modo: 100% silencioso em segundo plano" -ForegroundColor Cyan
} else {
    Write-Host "`n⚠️ Não foi possível registrar automaticamente. Execute o terminal como Administrador." -ForegroundColor Red
}
