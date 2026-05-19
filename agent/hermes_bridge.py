"""
agent/hermes_bridge.py
=======================
OCTO extended agent engine.

Integrates three systems:
  ① OCTO native planner/executor        — actions, voice, UI
  ② NousResearch/hermes-agent runtime   — context compression, memory, skills, MCP
  ③ bytedance/deer-flow LangGraph       — sub-agents, deep research, tool sandboxing

All branding says OCTO. No third-party names surface to the user.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ── Internal paths ────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent.parent
CFG_PATH     = BASE_DIR / "config" / "api_keys.json"
GW_CFG_PATH  = BASE_DIR / "config" / "gateway.json"
MEM_DIR      = Path(os.environ.get("USERPROFILE", Path.home())) / ".octo"
_GEMINI_COMPAT = "https://generativelanguage.googleapis.com/v1beta/openai/"

logger = logging.getLogger(__name__)


# ── Config helpers ────────────────────────────────────────────────────────────

def _api_key() -> str:
    try:
        return json.loads(CFG_PATH.read_text(encoding="utf-8")).get("gemini_api_key", "")
    except Exception:
        return ""

def _load_gateway_cfg() -> dict:
    if GW_CFG_PATH.exists():
        try:
            return json.loads(GW_CFG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


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
        logger.debug("[OCTO] Memory synced to MEMORY.md")
    except Exception as e:
        logger.warning("[OCTO] Memory sync: %s", e)


# ── Context compression ────────────────────────────────────────────────────────

_compressor = None
_compressor_lock = threading.Lock()


def get_compressor():
    """Lazy-init the context compressor (Hermes-inspired)."""
    global _compressor
    with _compressor_lock:
        if _compressor is None:
            try:
                from agent.context_compressor import ContextCompressor
                _compressor = ContextCompressor(context_limit=1_000_000)  # Gemini 1M ctx
                logger.info("[OCTO] Context compressor initialised")
            except Exception as e:
                logger.warning("[OCTO] Context compressor unavailable: %s", e)
        return _compressor


def maybe_compress(messages: list, system_prompt: str = "") -> list:
    """Compress message history if needed. Returns (possibly shorter) list."""
    try:
        comp = get_compressor()
        if comp and comp.should_compress(messages):
            logger.info("[OCTO] Compressing context (%d messages)…", len(messages))
            return comp.compress(messages, system_prompt=system_prompt)
    except Exception as e:
        logger.warning("[OCTO] Compression error: %s", e)
    return messages


# ── MCP tools ─────────────────────────────────────────────────────────────────

_mcp_started = False
_mcp_lock    = threading.Lock()


def get_mcp_tools() -> list:
    """Start MCP servers (once) and return all available tools."""
    global _mcp_started
    with _mcp_lock:
        if not _mcp_started:
            try:
                from agent.mcp_bridge import start_all
                result = start_all()
                if result:
                    total = sum(len(v) for v in result.values())
                    logger.info("[OCTO] MCP: %d servers, %d tools", len(result), total)
                _mcp_started = True
            except Exception as e:
                logger.debug("[OCTO] MCP init: %s", e)
    try:
        from agent.mcp_bridge import get_all_tools
        return get_all_tools()
    except Exception:
        return []


def call_mcp_tool(server_name: str, tool_name: str, arguments: dict) -> str:
    """Call an MCP tool and return its result."""
    try:
        from agent.mcp_bridge import call_tool
        return call_tool(server_name, tool_name, arguments)
    except Exception as e:
        return f"[MCP] {e}"


# ── Smart router ───────────────────────────────────────────────────────────────

_EXTENDED_KEYWORDS = {
    "terminal", "bash", "script", "execute", "run command", "shell",
    "install package", "pip install", "npm install", "git clone",
    "code execution", "compile", "docker", "schedule", "cron",
    "every day", "every hour", "every week", "at midnight",
    "skill", "delegation", "subagent", "mcp",
}

def should_use_extended(goal: str) -> bool:
    gl = goal.lower()
    return any(kw in gl for kw in _EXTENDED_KEYWORDS)


# ── Extended agent executor ───────────────────────────────────────────────────

def run_extended(goal: str, speak: Callable | None = None, max_turns: int = 20) -> str:
    """
    Run goal through the extended 70+ tool engine.
    Falls back gracefully to OCTO's native planner if the extended engine is unavailable.
    """
    # Sync memory before starting
    threading.Thread(target=sync_memory, daemon=True).start()

    # Inject MCP tools into environment if available
    mcp_tools = get_mcp_tools()
    if mcp_tools and speak:
        speak(f"Loading {len(mcp_tools)} MCP tools.")

    key = _api_key()
    if not key:
        return _native_fallback(goal, speak)

    try:
        import sys
        _add_engine_path()

        # Try to import the underlying run_agent
        from run_agent import AIAgent  # type: ignore  # noqa: F401

        env_backup = {}
        env_patch  = {
            "OPENAI_API_KEY":  key,
            "OPENAI_BASE_URL": _GEMINI_COMPAT,
        }
        for k, v in env_patch.items():
            env_backup[k] = os.environ.get(k, "")
            os.environ[k] = v

        try:
            agent  = AIAgent.__new__(AIAgent)
            result = agent.run_goal(goal, max_turns=max_turns)
            return result or "Done."
        finally:
            for k, v in env_backup.items():
                os.environ[k] = v

    except ImportError:
        pass
    except Exception as e:
        logger.error("[OCTO Extended] Error: %s", e)

    return _native_fallback(goal, speak)


def _native_fallback(goal: str, speak: Callable | None = None) -> str:
    """Fall back to OCTO's native planner/executor."""
    try:
        from agent.planner  import create_plan
        from agent.executor import execute_plan
        if speak:
            speak("Using native agent.")
        plan   = create_plan(goal)
        result = execute_plan(plan, speak=speak)
        return result
    except Exception as e:
        return f"Could not execute task: {e}"


def _add_engine_path():
    """Add extended engine location to sys.path if needed."""
    engine_path = str(MEM_DIR.parent / ".hermes_engine")
    if engine_path not in sys.path and Path(engine_path).exists():
        sys.path.insert(0, engine_path)


# ── Gateway integration ────────────────────────────────────────────────────────

_gateway_manager: Optional[object] = None
_gateway_lock = threading.Lock()


def get_gateway():
    """Lazy-init the multi-platform channel manager."""
    global _gateway_manager
    with _gateway_lock:
        if _gateway_manager is None:
            try:
                from channels.manager import ChannelManager
                _gateway_manager = ChannelManager()
                logger.info("[OCTO] Channel manager initialised")
            except Exception as e:
                logger.debug("[OCTO] Gateway init: %s", e)
        return _gateway_manager


def start_gateway(on_message: Callable[[str, str, str], None] | None = None) -> list:
    """
    Start all configured messaging channels.

    on_message: callback(channel_name, user_id, text)
    Returns list of started channel names.
    """
    mgr = get_gateway()
    if not mgr:
        return []
    if on_message:
        mgr.on_message(on_message)
    return mgr.start_all()


def send_via_gateway(channel: str, user_id: str, text: str) -> None:
    """Send a reply on a specific channel."""
    mgr = get_gateway()
    if mgr:
        mgr.send(channel, user_id, text)


def gateway_status() -> dict:
    """Return running status of all channels."""
    mgr = get_gateway()
    return mgr.status() if mgr else {}


# ═══════════════════════════════════════════════════════════════════════════════
# Scheduler — in-process SQLite job store
# ═══════════════════════════════════════════════════════════════════════════════

import sqlite3, uuid as _uuid, datetime as _dt

_SCHED_DB = BASE_DIR / "config" / "scheduler.db"
_SCHED_LOCK = threading.Lock()

def _sched_con():
    con = sqlite3.connect(str(_SCHED_DB), check_same_thread=False)
    con.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, prompt TEXT NOT NULL, schedule TEXT NOT NULL,
        label TEXT, enabled INTEGER DEFAULT 1, created_at TEXT
    )""")
    con.commit()
    return con

def create_scheduled(prompt: str, schedule: str, label: str = "") -> dict | None:
    """Create a new scheduled job. Returns the job dict or None on failure."""
    try:
        _validate_cron(schedule)
        jid = str(_uuid.uuid4())[:8]
        now = _dt.datetime.now().isoformat()
        with _SCHED_LOCK:
            con = _sched_con()
            con.execute("INSERT INTO jobs VALUES (?,?,?,?,1,?)",
                        (jid, prompt, schedule, label or "", now))
            con.commit(); con.close()
        logger.info("[Scheduler] Created job %s: %s @ %s", jid, label or prompt[:30], schedule)
        return {"id": jid, "prompt": prompt, "schedule": schedule,
                "label": label, "enabled": True}
    except Exception as e:
        logger.error("[Scheduler] create_scheduled: %s", e)
        return None

# Alias used by main.py
create_cron_job = create_scheduled

def list_scheduled() -> list:
    """Return all scheduled jobs."""
    try:
        with _SCHED_LOCK:
            con = _sched_con()
            rows = con.execute(
                "SELECT id,prompt,schedule,label,enabled,created_at FROM jobs ORDER BY created_at DESC"
            ).fetchall()
            con.close()
        return [{"id": r[0], "prompt": r[1], "schedule": r[2],
                 "label": r[3], "enabled": bool(r[4]), "created_at": r[5]} for r in rows]
    except Exception:
        return []

# Aliases used by ProjectWidget and ui.py
list_cron_jobs = list_scheduled

def delete_scheduled(job_id: str) -> None:
    """Delete a scheduled job by ID."""
    try:
        with _SCHED_LOCK:
            con = _sched_con()
            con.execute("DELETE FROM jobs WHERE id=?", (job_id,))
            con.commit(); con.close()
        logger.info("[Scheduler] Deleted job %s", job_id)
    except Exception as e:
        logger.error("[Scheduler] delete: %s", e)

def _validate_cron(expr: str):
    """Raise ValueError if expr is not a valid 5-part cron expression."""
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {expr!r} (need 5 parts)")


# ── Scheduler runner ──────────────────────────────────────────────────────────

def start_scheduler(octo_speak: "Callable | None" = None) -> None:
    """Start the background scheduler thread. Runs jobs via OCTO's native planner."""
    threading.Thread(target=_scheduler_loop, args=(octo_speak,), daemon=True,
                     name="octo-scheduler").start()
    logger.info("[Scheduler] Background runner started")

def _scheduler_loop(speak):
    import time, re as _re
    logger.info("[Scheduler] Runner active")
    while True:
        try:
            now = _dt.datetime.now()
            for job in list_scheduled():
                if not job.get("enabled"):
                    continue
                if _cron_matches(job["schedule"], now):
                    logger.info("[Scheduler] Firing job %s: %s", job["id"], job.get("label") or job["prompt"][:40])
                    threading.Thread(target=_run_job, args=(job, speak), daemon=True).start()
        except Exception as e:
            logger.error("[Scheduler] Loop error: %s", e)
        time.sleep(60 - _dt.datetime.now().second)  # align to next minute

def _run_job(job: dict, speak):
    goal = job.get("prompt", "")
    try:
        result = _native_fallback(goal, speak)
        logger.info("[Scheduler] Job %s done: %s", job["id"], str(result)[:80])
    except Exception as e:
        logger.error("[Scheduler] Job %s failed: %s", job["id"], e)

def _cron_matches(expr: str, now: "_dt.datetime") -> bool:
    """Check if cron expression matches the current minute."""
    try:
        parts = expr.strip().split()
        if len(parts) != 5:
            return False
        minute, hour, dom, month, dow = parts
        return (
            _cron_part(minute, now.minute) and
            _cron_part(hour,   now.hour)   and
            _cron_part(month,  now.month)  and
            _cron_part(dom,    now.day)    and
            _cron_part(dow,    now.weekday())
        )
    except Exception:
        return False

def _cron_part(expr: str, val: int) -> bool:
    if expr == "*":
        return True
    if expr.startswith("*/"):
        step = int(expr[2:])
        return val % step == 0
    if "-" in expr:
        lo, hi = expr.split("-", 1)
        return int(lo) <= val <= int(hi)
    if "," in expr:
        return val in {int(x) for x in expr.split(",")}
    return int(expr) == val


# ═══════════════════════════════════════════════════════════════════════════════
# Skills — proxy to deerflow_bridge
# ═══════════════════════════════════════════════════════════════════════════════

def list_skills() -> list:
    """Return installed/available skills from DeerFlow."""
    try:
        from deerflow_bridge import list_local_skills
        skills = list_local_skills()
        return [{"name": s.get("name", s.get("id", "")),
                 "description": s.get("description", ""),
                 "id": s.get("id", "")} for s in skills]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Gateway config writer — called by UI on Save
# ═══════════════════════════════════════════════════════════════════════════════

def write_gateway_config(data: dict) -> None:
    """Persist gateway.json and hot-reload the channel manager if running."""
    try:
        GW_CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
        GW_CFG_PATH.write_text(
            __import__("json").dumps(data, indent=4), encoding="utf-8"
        )
        logger.info("[Gateway] Config written: %s platforms", len(data))
    except Exception as e:
        logger.error("[Gateway] write_gateway_config: %s", e)


# ═══════════════════════════════════════════════════════════════════════════════
# Sync alias (legacy name used by old main.py schedule_task handler)
# ═══════════════════════════════════════════════════════════════════════════════

def sync_memory_to_hermes() -> None:
    """Alias for sync_memory (legacy name)."""
    sync_memory()
