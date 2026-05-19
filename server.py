"""
OCTO-Pro Monolith Server
========================
Single entry point that boots all four subsystems in-process:

  ① OCTO voice loop          — Gemini Live, UI, OS actions          (this process)
  ② Proxy (port 8082)        — free-claude-code model routing proxy  (thread)
  ③ Gateway (port 2026)      — DeerFlow LangGraph super-agent        (thread)
  ④ Hermes context engine    — loaded as importable module           (embedded)

Run with:
    python server.py              # full stack (voice + proxy + gateway)
    python server.py --no-voice   # headless (proxy + gateway only)
    python server.py --no-proxy   # skip model proxy
    python server.py --no-gateway # skip DeerFlow gateway
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import time
from pathlib import Path

# ── Path bootstrap ────────────────────────────────────────────────────────────
# Make all embedded sub-packages importable from the repo root.
ROOT = Path(__file__).resolve().parent
for pkg in [ROOT, ROOT / "proxy", ROOT / "proxy" / "config_fcc",
            ROOT / "proxy" / "core_fcc", ROOT / "deerflow",
            ROOT / "gateway"]:
    p = str(pkg)
    if p not in sys.path:
        sys.path.insert(0, p)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("octo.server")

PROXY_HOST   = "127.0.0.1"
PROXY_PORT   = 8082
GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 2026

_services: dict[str, threading.Thread] = {}


# ─────────────────────────────────────────────────────────────────────────────
# ① Model Proxy  (free-claude-code — octo/proxy/)
# ─────────────────────────────────────────────────────────────────────────────

def _start_proxy(host: str = PROXY_HOST, port: int = PROXY_PORT) -> threading.Thread:
    """Start the free-claude-code FastAPI proxy in a daemon thread."""
    def _run():
        try:
            import uvicorn
            # The proxy's create_asgi_app is in proxy/api/app.py
            sys.path.insert(0, str(ROOT / "proxy"))
            from api.app import create_asgi_app  # type: ignore
            app = create_asgi_app()
            log.info("🔌 Proxy starting on http://%s:%d", host, port)
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="warning",
                timeout_graceful_shutdown=5,
            )
        except ImportError as e:
            log.warning("Proxy unavailable (missing deps): %s", e)
        except Exception as e:
            log.error("Proxy crashed: %s", e)

    t = threading.Thread(target=_run, name="octo-proxy", daemon=True)
    t.start()
    return t


# ─────────────────────────────────────────────────────────────────────────────
# ② DeerFlow Gateway  (octo/gateway/ + octo/deerflow/)
# ─────────────────────────────────────────────────────────────────────────────

def _start_gateway(host: str = GATEWAY_HOST, port: int = GATEWAY_PORT) -> threading.Thread:
    """Start the DeerFlow LangGraph gateway in a daemon thread."""
    def _run():
        try:
            import uvicorn
            # Make the deerflow package importable as 'deerflow.*'
            sys.path.insert(0, str(ROOT))
            sys.path.insert(0, str(ROOT / "gateway" / ".."))   # app.gateway.*

            # The gateway expects 'app.gateway.app' — wire it via a shim
            from octo_gateway_shim import create_gateway_app  # type: ignore
            app = create_gateway_app()
            log.info("🧠 DeerFlow gateway starting on http://%s:%d", host, port)
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="warning",
                timeout_graceful_shutdown=5,
            )
        except ImportError as e:
            log.warning("DeerFlow gateway unavailable (missing deps): %s", e)
            log.info("  → Install: pip install langgraph langchain-core langgraph-sdk")
        except Exception as e:
            log.error("DeerFlow gateway crashed: %s", e)

    t = threading.Thread(target=_run, name="octo-gateway", daemon=True)
    t.start()
    return t


# ─────────────────────────────────────────────────────────────────────────────
# ③ Hermes context engine  (loaded in-process)
# ─────────────────────────────────────────────────────────────────────────────

def _init_hermes() -> None:
    """Warm-start the Hermes context compressor and memory provider."""
    try:
        from agent.hermes_bridge import get_compressor, get_mcp_tools
        get_compressor()
        get_mcp_tools()
        log.info("💾 Hermes context engine initialised")
    except Exception as e:
        log.debug("Hermes init skipped: %s", e)


# ─────────────────────────────────────────────────────────────────────────────
# ④ OCTO voice loop  (main.py)
# ─────────────────────────────────────────────────────────────────────────────

def _start_voice() -> None:
    """Start the Gemini Live voice loop (blocks until exit)."""
    from main import main as octo_main  # type: ignore
    octo_main()


# ─────────────────────────────────────────────────────────────────────────────
# Health check helpers
# ─────────────────────────────────────────────────────────────────────────────

def _wait_for_port(host: str, port: int, timeout: float = 15.0) -> bool:
    import socket
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def _print_banner(args: argparse.Namespace) -> None:
    print("""
╔══════════════════════════════════════════════════════════╗
║          🐙  OCTO-Pro  Super Model  — Monolith           ║
╠══════════════════════════════════════════════════════════╣
║  Voice Loop  : Gemini Live (this process)                ║
║  Model Proxy : http://127.0.0.1:8082  (free-claude-code) ║
║  DeerFlow    : http://127.0.0.1:2026  (LangGraph)        ║
║  Hermes      : embedded context compressor               ║
╚══════════════════════════════════════════════════════════╝
""")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="OCTO-Pro Monolith")
    parser.add_argument("--no-voice",   action="store_true", help="Skip voice loop (headless)")
    parser.add_argument("--no-proxy",   action="store_true", help="Skip model proxy")
    parser.add_argument("--no-gateway", action="store_true", help="Skip DeerFlow gateway")
    parser.add_argument("--proxy-port",   type=int, default=PROXY_PORT)
    parser.add_argument("--gateway-port", type=int, default=GATEWAY_PORT)
    args = parser.parse_args()

    _print_banner(args)

    # ── Start background services ─────────────────────────────────────────────
    if not args.no_proxy:
        _services["proxy"]   = _start_proxy(port=args.proxy_port)
    if not args.no_gateway:
        _services["gateway"] = _start_gateway(port=args.gateway_port)

    # Give services a moment to bind
    time.sleep(1.5)

    # ── Warm Hermes in background ─────────────────────────────────────────────
    threading.Thread(target=_init_hermes, daemon=True).start()

    # ── Health report ─────────────────────────────────────────────────────────
    if not args.no_proxy:
        ok = _wait_for_port(PROXY_HOST, args.proxy_port, timeout=12)
        log.info("Proxy  : %s", "✅ ready" if ok else "⚠️  not yet ready")
    if not args.no_gateway:
        ok = _wait_for_port(GATEWAY_HOST, args.gateway_port, timeout=20)
        log.info("Gateway: %s", "✅ ready" if ok else "⚠️  still starting")

    # ── Voice loop (or park) ──────────────────────────────────────────────────
    if args.no_voice:
        log.info("Headless mode — Ctrl-C to stop.")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            log.info("Shutdown.")
    else:
        _start_voice()   # blocks until window is closed / Ctrl-C


if __name__ == "__main__":
    main()
