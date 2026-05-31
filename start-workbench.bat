@echo off
setlocal EnableExtensions
chcp 65001 >nul

cd /d "%~dp0"
title ChenFlow Workbench Launcher

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-workbench.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
  echo ChenFlow Workbench startup failed with exit code %EXIT_CODE%.
) else (
  echo ChenFlow Workbench launcher exited.
)
pause
exit /b %EXIT_CODE%
