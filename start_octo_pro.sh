#!/usr/bin/env bash
# ┌──────────────────────────────────────────────────────────────┐
# │          OCTO-Pro Super Model — Unified Launcher             │
# │  Starts: Voice Loop + Model Proxy + DeerFlow + Hermes        │
# └──────────────────────────────────────────────────────────────┘
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer uv if available
if command -v uv &>/dev/null; then
    PY="uv run python"
else
    PY="python3"
fi

echo "🐙 OCTO-Pro Monolith starting…"
exec $PY server.py "$@"
