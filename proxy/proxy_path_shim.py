"""
proxy/proxy_path_shim.py
========================
Wires the free-claude-code proxy's internal flat imports so they resolve
correctly when running inside the OCTO monolith (where proxy/ is a sub-package
rather than the repo root).

Import this BEFORE importing anything else from the proxy.

Maps:
  from config.*   → proxy/config_fcc/*
  from core.*     → proxy/core_fcc/*
  from providers.*→ proxy/providers/*
  from messaging.*→ proxy/messaging/*
  from cli.*      → proxy/cli/*
  from api.*      → proxy itself (proxy/ is the 'api' namespace)
"""
from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

_PROXY_DIR = Path(__file__).resolve().parent

def _ensure_path(p: Path) -> None:
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

def _alias_package(real_path: Path, alias: str) -> None:
    """Make alias importable by inserting real_path into sys.path and
    registering a sys.modules shim so 'import alias' finds real_path's __init__."""
    _ensure_path(real_path.parent)
    real_name = real_path.name
    # If the real package is already importable under its real name, alias it
    if alias in sys.modules:
        return
    try:
        real_mod = importlib.import_module(real_name)
        sys.modules[alias] = real_mod
        # Alias all already-imported sub-modules
        for key in list(sys.modules):
            if key == real_name or key.startswith(real_name + "."):
                new_key = alias + key[len(real_name):]
                sys.modules.setdefault(new_key, sys.modules[key])
    except ImportError:
        # Create a minimal namespace package as placeholder
        mod = types.ModuleType(alias)
        mod.__path__ = [str(real_path)]   # type: ignore[assignment]
        mod.__package__ = alias
        sys.modules[alias] = mod

def _alias_self_as(alias: str) -> None:
    """Make the proxy directory importable under 'alias' (e.g. 'api')."""
    if alias in sys.modules:
        return
    mod = types.ModuleType(alias)
    mod.__path__ = [str(_PROXY_DIR)]   # type: ignore[assignment]
    mod.__package__ = alias
    sys.modules[alias] = mod

def setup() -> None:
    """Call once before importing anything from proxy internals."""
    # 1. proxy/ itself must be on path so flat imports (providers, messaging…) work
    _ensure_path(_PROXY_DIR)

    # 2. config → proxy/config_fcc
    _alias_package(_PROXY_DIR / "config_fcc", "config")

    # 3. core → proxy/core_fcc
    _alias_package(_PROXY_DIR / "core_fcc", "core")

    # 4. api → proxy/ itself  (e.g. 'from api.routes import router')
    _alias_self_as("api")

    # 5. providers / messaging / cli / models / web_tools are already in proxy/
    #    so they're importable once proxy/ is on sys.path (step 1).

# Auto-run on import
setup()
