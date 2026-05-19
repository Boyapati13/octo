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

:: ─── Check Additional Repositories ─────────────────────────────────────────────
if not exist "%DEERFLOW_DIR%\Makefile" (
    echo [INFO] Cloning DeerFlow...
    git clone https://github.com/bytedance/deer-flow.git "%DEERFLOW_DIR%"
)
if not exist "%OCTO_DIR%hermes-agent" (
    echo [INFO] Cloning Hermes Agent...
    git clone https://github.com/NousResearch/hermes-agent.git "%OCTO_DIR%hermes-agent"
)
if not exist "%OCTO_DIR%Mark-XXXIX" (
    echo [INFO] Cloning Mark-XXXIX...
    git clone https://github.com/FatihMakes/Mark-XXXIX.git "%OCTO_DIR%Mark-XXXIX"
)
if not exist "%OCTO_DIR%free-claude-code" (
    echo [INFO] Cloning Free Claude Code...
    git clone https://github.com/Alishahryar1/free-claude-code.git "%OCTO_DIR%free-claude-code"
    if not errorlevel 1 (
        echo [INFO] Installing Free Claude Code...
        cd /d "%OCTO_DIR%free-claude-code"
        %PYTHON% -m pip install -e .
        cd /d "%OCTO_DIR%"
    )
)

:: ─── Start DeerFlow in background ────────────────────────────────────────────
echo [1/4] Starting DeerFlow backend...
if exist "%DEERFLOW_DIR%\Makefile" (
    start "DeerFlow" /min cmd /c "cd /d "%DEERFLOW_DIR%" && make dev 2>&1 | findstr /v DEBUG"
    echo [INFO] DeerFlow launching at http://localhost:2026
    echo [INFO] Waiting 8s for backend to warm up...
    timeout /t 8 /nobreak >nul
) else (
    echo [WARN] DeerFlow Makefile missing - skipping backend.
)

:launch_octo
:: ─── Start Free Claude Code ───────────────────────────────────────────────────
echo [2/4] Starting Free Claude Code backend...
if exist "%OCTO_DIR%free-claude-code" (
    start "FreeClaudeCode" /min cmd /c "cd /d "%OCTO_DIR%free-claude-code" && fcc-server"
    echo [INFO] Free Claude Code running in background.
)

:: ─── Launch OCTO-Pro ─────────────────────────────────────────────────────────
echo [3/4] Starting OCTO-Pro voice engine...
cd /d "%OCTO_DIR%"

:: Run silently via VBS wrapper if present, otherwise direct
if exist "%OCTO_DIR%\octo_silent.vbs" (
    cscript //nologo "%OCTO_DIR%\octo_silent.vbs"
) else (
    %PYTHON% main.py
)

echo.
echo [4/4] OCTO-Pro session ended.
:: Cleanup fcc-server if running
taskkill /FI "WINDOWTITLE eq FreeClaudeCode*" /T /F >nul 2>&1
pause
