@echo off
:: ┌──────────────────────────────────────────────────────────────┐
:: │          OCTO-Pro Super Model — Unified Launcher             │
:: │  Starts: Voice Loop + Model Proxy + DeerFlow + Hermes        │
:: │  └──────────────────────────────────────────────────────────────┘
cd /d "%~dp0"

:: Set environment variables for robust UTF-8 console output
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Starting OCTO-Pro Monolith Server...
where uv >nul 2>&1 && (
    echo [Launcher] uv detected. Running via uv...
    uv run py server.py %*
) || (
    echo [Launcher] Running via global python...
    py server.py %*
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] OCTO-Pro exited with error code %ERRORLEVEL%.
    pause
)
