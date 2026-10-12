# Script dung he thong Modular RAG cho IT & Logistics
$ErrorActionPreference = "Continue"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   DUNG HE THONG MODULAR RAG CHO IT & LOGISTICS          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dang dung cac containers Docker..." -ForegroundColor Yellow
docker compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[THANH CONG] Toan bo he thong da duoc dung an toan." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[THONG BAO] Hoan tat lenh dung he thong." -ForegroundColor Gray
}
Write-Host ""
