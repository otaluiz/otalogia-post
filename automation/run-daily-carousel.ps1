# Rotina local diária do otalogia: gera 1 carrossel por dia, alternando as variantes (T1, T1b, referência).
# Disparado pelo Windows Task Scheduler (tarefa "otalogia-carrossel-diario").
$ErrorActionPreference = "Stop"
$repo = "D:\claude\otalogia-brand"
$driveRoot = "C:\Users\luizr\Meu Drive (aidealabbr@gmail.com)\Clientes\otalogia"
$promptFile = Join-Path $repo "automation\daily-carousel-prompt.txt"
$logDir = Join-Path $repo "automation\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir ("run-{0}.log" -f (Get-Date -Format "yyyy-MM-dd_HH-mm-ss"))

# geração + render demoram mais que o teto padrão de tarefas em segundo plano do claude -p
$env:CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS = "0"

Set-Location $repo
$prompt = Get-Content -Raw -Encoding utf8 $promptFile

& claude -p $prompt `
    --dangerously-skip-permissions `
    --add-dir $driveRoot `
    --model claude-sonnet-5 `
    *>&1 | Tee-Object -FilePath $logFile
