@echo off
chcp 65001 >nul
title Dung Modular RAG - IT & Logistics
echo ==========================================================
echo    DUNG HE THONG MODULAR RAG CHO IT & LOGISTICS          
echo ==========================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop.ps1"
pause
