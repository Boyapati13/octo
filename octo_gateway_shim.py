"""
octo_gateway_shim.py
====================
Adapts the DeerFlow gateway (originally at backend/app/gateway/app.py)
to run from inside the OCTO monolith.

Import paths are rewritten so that:
  - `app.gateway.*`  → `gateway.*`
  - `deerflow.*`     → `deerflow.*`  (already on sys.path)
  - `app.channels.*` → `channels.*`
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Ensure embedded packages are on path
for p in [ROOT, ROOT / "deerflow", ROOT / "gateway"]:
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

# Provide 'app.gateway' as an alias for our embedded 'gateway' package
# and 'app.channels' as an alias for our embedded 'channels' package
import types as _types

def _alias(real_name: str, alias_name: str) -> None:
    """Register sys.modules[alias_name] → sys.modules[real_name]."""
    try:
        real_mod = __import__(real_name)
        sys.modules[alias_name] = real_mod
        # Also register sub-packages that have already been imported
        for key in list(sys.modules):
            if key.startswith(real_name + "."):
                new_key = alias_name + key[len(real_name):]
                sys.modules.setdefault(new_key, sys.modules[key])
    except ImportError:
        pass

# Create a top-level 'app' namespace module
if "app" not in sys.modules:
    _app_mod = _types.ModuleType("app")
    _app_mod.__path__ = []  # type: ignore
    sys.modules["app"] = _app_mod

# Wire sub-packages
_alias("gateway", "app.gateway")
_alias("channels", "app.channels")

# Now we can import the real gateway app factory
def create_gateway_app():
    """Build and return the DeerFlow FastAPI application."""
    try:
        # Try the embedded gateway's create_app directly
        from gateway.app import create_app  # type: ignore
        return create_app()
    except (ImportError, AttributeError):
        pass

    # Minimal fallback: a FastAPI app with a /health endpoint
    try:
        from fastapi import FastAPI
        app = FastAPI(title="OCTO-Pro DeerFlow Gateway (minimal)")

        @app.get("/health")
        async def health():
            return {"status": "ok", "mode": "minimal"}

        @app.get("/api/health")
        async def api_health():
            return {"status": "ok"}

        return app
    except ImportError:
        raise RuntimeError(
            "FastAPI not installed. Run: pip install fastapi uvicorn"
        )
