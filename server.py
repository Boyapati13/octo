"""
OCTO-Pro Monolith Server
========================
Single entry point that boots all four subsystems in-process:

  ① OCTO voice loop          — Gemini Live, UI, OS actions          (main thread)
  ② Proxy (port 8082)        — free-claude-code model routing proxy  (daemon thread)
  ③ Gateway (port 2026)      — DeerFlow LangGraph super-agent        (daemon thread)
  ④ Hermes context engine    — embedded modules                      (daemon thread)

Usage:
    python server.py                   # full stack
    python server.py --no-voice        # headless (proxy + gateway only)
    python server.py --no-proxy        # skip model proxy
    python server.py --no-gateway      # skip DeerFlow gateway
    python server.py --proxy-port 9090 --gateway-port 3000
"""
from __future__ import annotations

import argparse
import logging
import os
import socket
import sys
import threading
import time
from pathlib import Path

# ── Path bootstrap ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
for _p in [ROOT, ROOT / "deerflow", ROOT / "gateway"]:
    s = str(_p)
    if s not in sys.path:
        sys.path.insert(0, s)

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


# ─────────────────────────────────────────────────────────────────────────────
# ① Model Proxy  (free-claude-code — octo/proxy/)
# ─────────────────────────────────────────────────────────────────────────────

def _start_proxy(host: str = PROXY_HOST, port: int = PROXY_PORT) -> threading.Thread:
    def _run():
        try:
            import uvicorn
            # Wire all proxy internal imports BEFORE importing the app
            sys.path.insert(0, str(ROOT / "proxy"))
            import proxy_path_shim  # noqa: F401  — side-effect: sets up aliases
            from proxy.app import create_asgi_app  # type: ignore
            app = create_asgi_app()
            log.info("🔌 Proxy starting on http://%s:%d", host, port)
            uvicorn.run(app, host=host, port=port, log_level="warning",
                        timeout_graceful_shutdown=5)
        except ImportError as e:
            log.warning("Proxy unavailable (missing deps): %s", e)
            log.info("  → pip install fastapi uvicorn loguru pydantic-settings")
        except Exception as e:
            log.error("Proxy crashed: %s", e, exc_info=True)

    t = threading.Thread(target=_run, name="octo-proxy", daemon=True)
    t.start()
    return t


# ─────────────────────────────────────────────────────────────────────────────
# ② DeerFlow Gateway  (octo/gateway/ + octo/deerflow/)
# ─────────────────────────────────────────────────────────────────────────────

def _start_gateway(host: str = GATEWAY_HOST, port: int = GATEWAY_PORT) -> threading.Thread:
    def _run():
        try:
            import uvicorn
            from octo_gateway_shim import create_gateway_app  # type: ignore
            app = create_gateway_app()
            log.info("🧠 DeerFlow gateway starting on http://%s:%d", host, port)
            uvicorn.run(app, host=host, port=port, log_level="warning",
                        timeout_graceful_shutdown=5)
        except ImportError as e:
            log.warning("DeerFlow gateway unavailable (missing deps): %s", e)
            log.info("  → pip install langgraph langchain-core langgraph-sdk")
        except Exception as e:
            log.error("DeerFlow gateway crashed: %s", e, exc_info=True)

    t = threading.Thread(target=_run, name="octo-gateway", daemon=True)
    t.start()
    return t


# ─────────────────────────────────────────────────────────────────────────────
# ③ Hermes — warm-start in background
# ─────────────────────────────────────────────────────────────────────────────

def _init_hermes() -> None:
    try:
        from agent.hermes_bridge import get_compressor, get_mcp_tools
        get_compressor()
        get_mcp_tools()
        log.info("💾 Hermes context engine initialised")
    except Exception as e:
        log.debug("Hermes init skipped: %s", e)


# ─────────────────────────────────────────────────────────────────────────────
# Health helpers
# ─────────────────────────────────────────────────────────────────────────────

def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

def _wait_for_port(host: str, port: int, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_open(host, port): return True
        time.sleep(0.5)
    return False


def _print_banner() -> None:
    print("""
+--------------------------------------------------------------+
|           (o)  OCTO-Pro  Super Model  --  Monolith           |
+--------------------------------------------------------------+
|  Voice Loop   : Gemini Live (this process)                   |
|  Model Proxy  : http://127.0.0.1:8082  (free-claude-code)    |
|  DeerFlow     : http://127.0.0.1:2026  (LangGraph gateway)   |
|  Hermes       : embedded context compressor + MCP            |
+--------------------------------------------------------------+
""")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="OCTO-Pro Monolith")
    parser.add_argument("--no-voice",     action="store_true")
    parser.add_argument("--no-proxy",     action="store_true")
    parser.add_argument("--no-gateway",   action="store_true")
    parser.add_argument("--proxy-port",   type=int, default=PROXY_PORT)
    parser.add_argument("--gateway-port", type=int, default=GATEWAY_PORT)
    args = parser.parse_args()

    _print_banner()

    # ── Start background services ─────────────────────────────────────────────
    if not args.no_proxy:
        _start_proxy(port=args.proxy_port)
    if not args.no_gateway:
        _start_gateway(port=args.gateway_port)

    time.sleep(1.5)

    # ── Hermes warm-start ─────────────────────────────────────────────────────
    threading.Thread(target=_init_hermes, daemon=True).start()

    # ── Health report ─────────────────────────────────────────────────────────
    if not args.no_proxy:
        ok = _wait_for_port(PROXY_HOST, args.proxy_port, timeout=15)
        log.info("Proxy  : %s", "✅ ready" if ok else "⚠️  still starting…")
    if not args.no_gateway:
        ok = _wait_for_port(GATEWAY_HOST, args.gateway_port, timeout=25)
        log.info("Gateway: %s", "✅ ready" if ok else "⚠️  still starting…")

    # ── Voice loop or headless park ───────────────────────────────────────────
    if args.no_voice:
        log.info("Headless mode — Ctrl-C to quit.")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            log.info("Shutdown.")
    else:
        from main import main as octo_main   # type: ignore
        octo_main()


if __name__ == "__main__":
    main()
