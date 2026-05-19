@echo off
:: ┌──────────────────────────────────────────────────────────────┐
:: │          OCTO-Pro Super Model — Unified Launcher             │
:: │  Starts: Voice Loop + Model Proxy + DeerFlow + Hermes        │
:: └──────────────────────────────────────────────────────────────┘
cd /d "%~dp0"
where uv >nul 2>&1 && (
    uv run python server.py %*
) || (
    python server.py %*
)
