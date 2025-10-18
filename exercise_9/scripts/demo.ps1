# Demo script for Exercise 9
# - Uploads sample docs
# - Starts a run for high-value test
# - Shows how to approve HITL
# - Prints export URLs for quick recording

param(
  [string]$ApiBase = "http://localhost:8000"
)

function Invoke-JsonPost($Url, $Body) {
  return Invoke-RestMethod -Uri $Url -Method Post -Body ($Body | ConvertTo-Json -Depth 10) -ContentType 'application/json'
}

Write-Host "Uploading sample documents..." -ForegroundColor Cyan
$highValuePath = Join-Path $PSScriptRoot "..\data\sample_documents\high_value_test.md"
$baselinePath = Join-Path $PSScriptRoot "..\data\sample_documents\pii_baseline_test.md"
$contextPath = Join-Path $PSScriptRoot "..\data\sample_documents\context_pii_test.md"

$high = Invoke-WebRequest -Uri "$ApiBase/api/documents/upload" -Method Post -InFile $highValuePath -ContentType 'text/plain' | ConvertFrom-Json
$base = Invoke-WebRequest -Uri "$ApiBase/api/documents/upload" -Method Post -InFile $baselinePath -ContentType 'text/plain' | ConvertFrom-Json
$ctx  = Invoke-WebRequest -Uri "$ApiBase/api/documents/upload" -Method Post -InFile $contextPath -ContentType 'text/plain' | ConvertFrom-Json

Write-Host "Uploaded:" $high.name "," $base.name "," $ctx.name -ForegroundColor Green

Write-Host "Starting review run for high-value doc..." -ForegroundColor Cyan
$run = Invoke-JsonPost "$ApiBase/api/run" @{ doc_id = $high.doc_id }
$runId = $run.run_id
Write-Host "Run ID:" $runId -ForegroundColor Yellow

Start-Sleep -Seconds 2
$current = Invoke-RestMethod "$ApiBase/api/run/$runId"
Write-Host "Status:" $current.status -ForegroundColor Yellow

if ($current.status -eq 'awaiting_hitl') {
  Write-Host "Fetching HITL queue..." -ForegroundColor Cyan
  $queue = Invoke-RestMethod "$ApiBase/api/hitl/queue"
  $hitl = $queue | Where-Object { $_.run_id -eq $runId } | Select-Object -First 1
  if ($null -ne $hitl) {
    Write-Host "Approving HITL:" $hitl.hitl_id -ForegroundColor Yellow
    $resp = Invoke-JsonPost "$ApiBase/api/hitl/$($hitl.hitl_id)/respond" @{ hitl_id = $hitl.hitl_id; decisions = @(@{ item_id = "approve_all"; decision = "approve" }) }
    Start-Sleep -Seconds 1
  }
}

# Poll until completed or failed (timeout 30s)
$deadline = (Get-Date).AddSeconds(30)
do {
  $current = Invoke-RestMethod "$ApiBase/api/run/$runId"
  Write-Host "Status:" $current.status -ForegroundColor Yellow
  if ($current.status -in 'completed','failed') { break }
  Start-Sleep -Seconds 2
} while ((Get-Date) -lt $deadline)

Write-Host "Redline URL: $ApiBase/api/export/run/$runId/redline" -ForegroundColor Green
Write-Host "Final URL:    $ApiBase/api/export/run/$runId/final" -ForegroundColor Green

