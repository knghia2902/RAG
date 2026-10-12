@echo off
chcp 65001 >nul
title Khoi Dong Modular RAG - IT & Logistics

:: Kiem tra quyen Administrator, neu chua co thi tu dong xin quyen qua UAC
fltmc >nul 2>&1 || (
    echo Dang yeu cau quyen Administrator de khoi dong dich vu Docker...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"
echo ==========================================================
echo    KHOI DONG HE THONG MODULAR RAG CHO IT & LOGISTICS     
echo ==========================================================
echo.
echo Dang goi PowerShell de khoi dong cac dich vu Docker...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Co loi xay ra trong qua trinh khoi dong.
    echo Vui long kiem tra thong bao loi o tren hoac dam bao Docker Desktop dang chay.
    pause
    exit /b %ERRORLEVEL%
)
pause
