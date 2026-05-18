@echo off
title OCTO-Pro Launcher
color 0A

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║          OCTO-Pro × DeerFlow  Launcher          ║
echo  ║   Personal AI + Super-Agent Harness             ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ─── Paths ───────────────────────────────────────────────────────────────────
set "OCTO_DIR=%~dp0"
set "DEERFLOW_DIR=%OCTO_DIR%deer-flow"
set "PYTHON=python"

:: ─── Check DeerFlow exists ───────────────────────────────────────────────────
if not exist "%DEERFLOW_DIR%\Makefile" (
    echo [WARN] DeerFlow not found at %DEERFLOW_DIR%
    echo [INFO] Cloning DeerFlow...
    git clone https://github.com/bytedance/deer-flow.git "%DEERFLOW_DIR%"
    if errorlevel 1 (
        echo [WARN] Clone failed - OCTO will run without DeerFlow.
        goto :launch_octo
    )
)

:: ─── Start DeerFlow in background ────────────────────────────────────────────
echo [1/3] Starting DeerFlow backend...
if exist "%DEERFLOW_DIR%\Makefile" (
    start "DeerFlow" /min cmd /c "cd /d "%DEERFLOW_DIR%" && make dev 2>&1 | findstr /v DEBUG"
    echo [INFO] DeerFlow launching at http://localhost:2026
    echo [INFO] Waiting 8s for backend to warm up...
    timeout /t 8 /nobreak >nul
) else (
    echo [WARN] DeerFlow Makefile missing - skipping backend.
)

:launch_octo
:: ─── Launch OCTO-Pro ─────────────────────────────────────────────────────────
echo [2/3] Starting OCTO-Pro voice engine...
cd /d "%OCTO_DIR%"

:: Run silently via VBS wrapper if present, otherwise direct
if exist "%OCTO_DIR%\octo_silent.vbs" (
    cscript //nologo "%OCTO_DIR%\octo_silent.vbs"
) else (
    %PYTHON% main.py
)

echo.
echo [3/3] OCTO-Pro session ended.
pause
