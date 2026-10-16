param(
    [int]$Port = 8000,
    [string]$UserId = "wx_user_001",
    [string]$SessionId = "sess_debug_001"
)

$ErrorActionPreference = "Stop"

Write-Host "== Wenlv Agent Debug Runner ==" -ForegroundColor Cyan
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "[1/6] Creating virtual environment..."
    python -m venv .venv
}

Write-Host "[2/6] Installing dependencies..."
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt | Out-Null

Write-Host "[3/6] Starting FastAPI server on port $Port..."
$uvicornArgs = @(
    "-m", "uvicorn",
    "app.main:app",
    "--host", "127.0.0.1",
    "--port", "$Port",
    "--reload"
)
$serverProcess = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList $uvicornArgs -PassThru

try {
    Write-Host "[4/6] Waiting for server to become healthy..."
    $healthy = $false
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -Method Get
            if ($health.status -eq "ok") {
                $healthy = $true
                break
            }
        } catch {
            # keep waiting
        }
    }
    if (-not $healthy) {
        throw "Server did not become healthy in time."
    }

    Write-Host "[5/6] Sending debug chat request..."
    $chatBody = @{
        user_id    = $UserId
        session_id = $SessionId
        message    = "我想看文物和非遗，顺便规划路线"
        location   = "古城街区"
        weather    = "小雨"
    } | ConvertTo-Json -Depth 5
    $chatResp = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$Port/api/v1/chat" -ContentType "application/json" -Body $chatBody

    Write-Host "[6/6] Sending feedback event and fetching reports..."
    $eventBody = @{
        user_id       = $UserId
        session_id    = $SessionId
        event_type    = "feedback"
        theme         = "culture"
        clicked       = 1
        converted     = 0
        dwell_seconds = 90
        metadata      = @{
            location = "古城街区"
            poi_id   = "site_old_street"
        }
    } | ConvertTo-Json -Depth 8
    $null = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$Port/api/v1/events" -ContentType "application/json" -Body $eventBody

    $features = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$Port/api/v1/users/$UserId/features?session_id=$SessionId"
    $abReport = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$Port/api/v1/ops/ab-report"
    $grounded = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$Port/api/v1/knowledge/grounded-answer?query=请介绍古城街区里的非遗皮影戏"

    Write-Host ""
    Write-Host "=== Debug Results ===" -ForegroundColor Green
    Write-Host "Chat answer:" -ForegroundColor Yellow
    Write-Host $chatResp.answer
    Write-Host ""
    Write-Host "Intent state:" -ForegroundColor Yellow
    $chatResp.intent_state | ConvertTo-Json -Depth 5
    Write-Host ""
    Write-Host "Recommendations:" -ForegroundColor Yellow
    $chatResp.recommendations | ConvertTo-Json -Depth 5
    Write-Host ""
    Write-Host "Feature snapshot + interest graph:" -ForegroundColor Yellow
    $features | ConvertTo-Json -Depth 8
    Write-Host ""
    Write-Host "A/B report:" -ForegroundColor Yellow
    $abReport | ConvertTo-Json -Depth 8
    Write-Host ""
    Write-Host "Grounded answer citations:" -ForegroundColor Yellow
    $grounded | ConvertTo-Json -Depth 8
    Write-Host ""
    Write-Host "Service docs: http://127.0.0.1:$Port/docs" -ForegroundColor Cyan
    Write-Host "Server is still running (PID: $($serverProcess.Id)). Stop it with:" -ForegroundColor Cyan
    Write-Host "Stop-Process -Id $($serverProcess.Id)" -ForegroundColor Cyan
} catch {
    Write-Error $_
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -Force
    }
    exit 1
}
