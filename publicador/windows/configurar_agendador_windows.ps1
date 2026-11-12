# Configura a Tarefa Agendada no Windows para disparar o publicador as 06:30 (Horário de Cuiabá)
$taskName = "Otalogia_Instagram_Publisher"
$scriptPath = Join-Path $PSScriptRoot "disparar_webhook_github.ps1"

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At "06:30AM"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Disparo diario do Instagram @otalogia pontual as 06:30 Cuiaba" -Force

Write-Host "✅ Tarefa agendada '$taskName' registrada com sucesso no Windows!" -ForegroundColor Green
Write-Host "⏰ Disparo diário programado para às 06:30 (Horário de Cuiabá)." -ForegroundColor Cyan
Write-Host "⚡ Se o PC estiver desligado às 06:30, a tarefa disparará assim que o PC for ligado (StartWhenAvailable)." -ForegroundColor Cyan
