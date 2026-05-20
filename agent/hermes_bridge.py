"""
agent/hermes_bridge.py
======================
OCTO extended context engine — powered by embedded Hermes modules.

All Hermes source files were pulled directly into octo/agent/*_hermes.py.
This module re-exports clean aliases so the rest of OCTO never needs to
know where the code came from.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger(__name__)

BASE_DIR    = Path(__file__).resolve().parent.parent
CFG_PATH    = BASE_DIR / "config" / "api_keys.json"
GW_CFG_PATH = BASE_DIR / "config" / "gateway.json"
MEM_DIR     = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".octo"

# Ensure agent/ is on path so *_hermes imports work
_agent_dir = str(BASE_DIR / "agent")
if _agent_dir not in sys.path:
    sys.path.insert(0, _agent_dir)


# ── Config helpers ────────────────────────────────────────────────────────────

def _api_key() -> str:
    try:
        return json.loads(CFG_PATH.read_text(encoding="utf-8")).get("gemini_api_key", "")
    except Exception:
        return ""


# ── Memory sync ───────────────────────────────────────────────────────────────

def sync_memory() -> None:
    """Export OCTO memory → MEMORY.md for the extended engine."""
    try:
        from memory.memory_manager import load_memory
        memory = load_memory()
        MEM_DIR.mkdir(parents=True, exist_ok=True)
        lines = ["# OCTO User Memory\n\n"]
        for cat, items in memory.items():
            if not isinstance(items, dict) or not items:
                continue
            lines.append(f"## {cat.title()}\n")
            for key, entry in items.items():
                val = entry.get("value") if isinstance(entry, dict) else str(entry)
                if val:
                    lines.append(f"- **{key.replace('_',' ').title()}**: {val}\n")
            lines.append("\n")
        (MEM_DIR / "MEMORY.md").write_text("".join(lines), encoding="utf-8")
    except Exception as e:
        log.debug("Memory sync: %s", e)

# Alias used by main.py scheduler integration
sync_memory_to_hermes = sync_memory


# ── Context compression (Hermes embedded) ─────────────────────────────────────

_compressor      = None
_compressor_lock = threading.Lock()


def get_compressor():
    """Lazy-init the embedded Hermes context compressor."""
    global _compressor
    with _compressor_lock:
        if _compressor is None:
            try:
                # Try the OCTO native one first
                from agent.context_compressor import ContextCompressor
                _compressor = ContextCompressor(context_limit=1_000_000)
                log.info("[Hermes] Native ContextCompressor loaded")
            except Exception:
                try:
                    # Fall back to the pulled-in Hermes version
                    from agent.context_compressor_hermes import ContextCompressor  # type: ignore
                    _compressor = ContextCompressor(context_limit=1_000_000)
                    log.info("[Hermes] Hermes ContextCompressor loaded")
                except Exception as e:
                    log.debug("[Hermes] Compressor unavailable: %s", e)
    return _compressor


def maybe_compress(messages: list, system_prompt: str = "") -> list:
    """Compress message history if needed."""
    try:
        comp = get_compressor()
        if comp and comp.should_compress(messages):
            log.info("[Hermes] Compressing %d messages…", len(messages))
            return comp.compress(messages, system_prompt=system_prompt)
    except Exception as e:
        log.debug("Compression error: %s", e)
    return messages


# ── MCP tools ─────────────────────────────────────────────────────────────────

_mcp_started = False
_mcp_lock    = threading.Lock()


def get_mcp_tools() -> list:
    """Start MCP servers once, return tool list."""
    global _mcp_started
    with _mcp_lock:
        if not _mcp_started:
            try:
                from agent.mcp_bridge import start_all
                result = start_all()
                if result:
                    total = sum(len(v) for v in result.values())
                    log.info("[MCP] %d servers, %d tools", len(result), total)
                _mcp_started = True
            except Exception as e:
                log.debug("[MCP] init: %s", e)
    try:
        from agent.mcp_bridge import get_all_tools
        return get_all_tools()
    except Exception:
        return []


def call_mcp_tool(server_name: str, tool_name: str, arguments: dict) -> str:
    try:
        from agent.mcp_bridge import call_tool
        return call_tool(server_name, tool_name, arguments)
    except Exception as e:
        return f"[MCP] {e}"


# ── Skill utilities (Hermes embedded) ─────────────────────────────────────────

def load_skill_bundle(name: str) -> dict | None:
    """Load a skill bundle by name (Hermes embedded)."""
    try:
        from agent.skill_bundles_hermes import load_bundle  # type: ignore
        return load_bundle(name)
    except Exception:
        return None


def preprocess_skill(content: str, context: dict) -> str:
    """Apply Hermes skill preprocessing."""
    try:
        from agent.skill_preprocessing_hermes import preprocess  # type: ignore
        return preprocess(content, context)
    except Exception:
        return content


# ── Smart router ───────────────────────────────────────────────────────────────

_EXTENDED_KEYWORDS = {
    "terminal", "bash", "script", "execute", "run command", "shell",
    "install package", "pip install", "npm install", "git clone",
    "code execution", "compile", "docker", "schedule", "cron",
    "every day", "every hour", "every week", "at midnight",
    "skill", "delegation", "subagent", "mcp",
}


def should_use_extended(goal: str) -> bool:
    return any(kw in goal.lower() for kw in _EXTENDED_KEYWORDS)


# ── Extended agent executor ───────────────────────────────────────────────────

def run_extended(goal: str, speak: Callable | None = None, max_turns: int = 20) -> str:
    """Run goal through the extended engine (native planner)."""
    threading.Thread(target=sync_memory, daemon=True).start()
    mcp_tools = get_mcp_tools()
    if mcp_tools and speak:
        speak(f"Loading {len(mcp_tools)} MCP tools.")
    return _native_fallback(goal, speak)


def _native_fallback(goal: str, speak: Callable | None = None) -> str:
    try:
        from agent.planner  import create_plan
        from agent.executor import execute_plan
        if speak:
            speak("Using native agent.")
        return execute_plan(create_plan(goal), speak=speak)
    except Exception as e:
        return f"Could not execute task: {e}"


# ── Cron scheduling ───────────────────────────────────────────────────────────

def create_cron_job(prompt: str, schedule: str, label: str = "") -> dict | None:
    """Register a cron job in the scheduler."""
    try:
        from agent.task_queue import get_queue
        q = get_queue()
        job = q.schedule(prompt=prompt, cron=schedule, label=label)
        return job
    except Exception as e:
        log.warning("[Cron] %s", e)
        return None


# ── Gateway ───────────────────────────────────────────────────────────────────

_gateway_manager: Optional[object] = None
_gateway_lock = threading.Lock()


def get_gateway():
    global _gateway_manager
    with _gateway_lock:
        if _gateway_manager is None:
            try:
                from channels.manager import ChannelManager  # type: ignore
                _gateway_manager = ChannelManager()
                log.info("[Gateway] ChannelManager initialised")
            except Exception as e:
                log.debug("[Gateway] init: %s", e)
    return _gateway_manager


def start_gateway(on_message: Callable | None = None) -> list:
    mgr = get_gateway()
    if not mgr:
        return []
    if on_message:
        mgr.on_message(on_message)
    return mgr.start_all()


def send_via_gateway(channel: str, user_id: str, text: str) -> None:
    mgr = get_gateway()
    if mgr:
        mgr.send(channel, user_id, text)


def gateway_status() -> dict:
    mgr = get_gateway()
    return mgr.status() if mgr else {}


# ── Backward-compat aliases ───────────────────────────────────────────────────
# task_queue.py calls these names — map them to the new functions above.
should_use_hermes = should_use_extended
run_with_hermes   = run_extended
