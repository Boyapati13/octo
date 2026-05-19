#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
#  OCTO-Pro × DeerFlow launcher  (macOS / Linux)
# ─────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEERFLOW_DIR="$SCRIPT_DIR/deer-flow"
DEERFLOW_PORT=2026
DEERFLOW_PID_FILE="$SCRIPT_DIR/.deerflow.pid"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log() { echo -e "${CYAN}[OCTO-Pro]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
ok()  { echo -e "${GREEN}[OK]${NC} $*"; }

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║        OCTO-Pro × DeerFlow  Launcher            ║"
echo "  ║   Personal AI + Super-Agent Harness             ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""

# ── Clone Additonal Repos ─────────────────────────────────
if [[ ! -f "$DEERFLOW_DIR/Makefile" ]]; then
    warn "DeerFlow not found. Cloning..."
    git clone https://github.com/bytedance/deer-flow.git "$DEERFLOW_DIR" || {
        warn "Clone failed — OCTO will run without DeerFlow."; SKIP_DF=1
    }
fi
if [[ ! -d "$SCRIPT_DIR/hermes-agent" ]]; then
    log "Cloning Hermes Agent..."
    git clone https://github.com/NousResearch/hermes-agent.git "$SCRIPT_DIR/hermes-agent"
fi
if [[ ! -d "$SCRIPT_DIR/Mark-XXXIX" ]]; then
    log "Cloning Mark-XXXIX..."
    git clone https://github.com/FatihMakes/Mark-XXXIX.git "$SCRIPT_DIR/Mark-XXXIX"
fi
if [[ ! -d "$SCRIPT_DIR/free-claude-code" ]]; then
    log "Cloning Free Claude Code..."
    git clone https://github.com/Alishahryar1/free-claude-code.git "$SCRIPT_DIR/free-claude-code" && {
        log "Installing Free Claude Code..."
        cd "$SCRIPT_DIR/free-claude-code"
        pip install -e .
        cd "$SCRIPT_DIR"
    }
fi

# ── Start DeerFlow backend ────────────────────────────────
if [[ -z "${SKIP_DF:-}" && -f "$DEERFLOW_DIR/Makefile" ]]; then
    log "Starting DeerFlow backend at http://localhost:$DEERFLOW_PORT ..."
    cd "$DEERFLOW_DIR"
    # Check if already running
    if curl -sf "http://localhost:$DEERFLOW_PORT/api/health" &>/dev/null; then
        ok "DeerFlow already running."
    else
        make dev &>/tmp/deerflow.log &
        echo $! > "$DEERFLOW_PID_FILE"
        log "DeerFlow PID: $! — waiting 10s for warm-up..."
        sleep 10
        if curl -sf "http://localhost:$DEERFLOW_PORT/api/health" &>/dev/null; then
            ok "DeerFlow is live."
        else
            warn "DeerFlow did not respond — OCTO will fall back to native tools."
        fi
    fi
    cd "$SCRIPT_DIR"
fi

# ── Start Free Claude Code ────────────────────────────────
if [[ -d "$SCRIPT_DIR/free-claude-code" ]]; then
    log "Starting Free Claude Code server..."
    cd "$SCRIPT_DIR/free-claude-code"
    fcc-server &>/tmp/fcc.log &
    FCC_PID=$!
    echo $FCC_PID > "$SCRIPT_DIR/.fcc.pid"
    cd "$SCRIPT_DIR"
fi

# ── Launch OCTO-Pro ───────────────────────────────────────
log "Starting OCTO-Pro voice engine..."
cd "$SCRIPT_DIR"
python3 main.py

# ── Cleanup ───────────────────────────────────────────────
if [[ -f "$DEERFLOW_PID_FILE" ]]; then
    DF_PID=$(cat "$DEERFLOW_PID_FILE")
    log "Stopping DeerFlow (PID $DF_PID)..."
    kill "$DF_PID" 2>/dev/null || true
    rm -f "$DEERFLOW_PID_FILE"
fi
if [[ -f "$SCRIPT_DIR/.fcc.pid" ]]; then
    FCC_PID=$(cat "$SCRIPT_DIR/.fcc.pid")
    log "Stopping Free Claude Code (PID $FCC_PID)..."
    kill "$FCC_PID" 2>/dev/null || true
    rm -f "$SCRIPT_DIR/.fcc.pid"
fi
log "Session ended."
