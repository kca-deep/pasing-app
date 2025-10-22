#!/usr/bin/env pwsh
<#
.SYNOPSIS
    FastAPI 백엔드 시작 스크립트 (한글 인코딩 수정)

.DESCRIPTION
    UTF-8 인코딩을 설정하고 FastAPI 백엔드를 시작합니다.
#>

# UTF-8 인코딩 설정
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# 콘솔 코드페이지를 UTF-8로 설정
chcp 65001 | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FastAPI 백엔드 서버 시작" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ UTF-8 인코딩 설정 완료" -ForegroundColor Green
Write-Host ""

# 백엔드 디렉토리로 이동
Set-Location -Path "$PSScriptRoot\backend"

# 가상환경 활성화
Write-Host "가상환경 활성화 중..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# 서버 시작
Write-Host ""
Write-Host "FastAPI 서버 시작 중..." -ForegroundColor Yellow
Write-Host "  주소: http://localhost:8000" -ForegroundColor White
Write-Host "  API 문서: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "종료하려면 Ctrl+C를 누르세요" -ForegroundColor Gray
Write-Host ""

# Uvicorn 실행
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
