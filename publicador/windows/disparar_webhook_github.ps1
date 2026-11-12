# Dispara o workflow do GitHub Actions instantaneamente via Webhook repository_dispatch
$envPath = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line.Split("=", 2)
            [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
        }
    }
}

$token = $env:GITHUB_TOKEN
if (-not $token) {
    Write-Error "GITHUB_TOKEN não encontrado no arquivo .env"
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Accept" = "application/vnd.github+json"
    "User-Agent" = "Otalogia-Publisher"
}

$body = @{
    "event_type" = "daily_publish"
} | ConvertTo-Json

Write-Host "🚀 Disparando GitHub Actions instantâneo (repository_dispatch)..." -ForegroundColor Cyan
$response = Invoke-RestMethod -Uri "https://api.github.com/repos/otaluiz/otalogia-post/dispatches" -Method Post -Headers $headers -Body $body

Write-Host "✅ Webhook enviado com sucesso! O GitHub Actions iniciará a publicação em instantes." -ForegroundColor Green
