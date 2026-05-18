"""
OCTO extended agent engine.

Wraps the underlying agent runtime to give OCTO access to:
  - Full terminal / code execution / file toolset
  - Cron scheduling
  - Skills system
  - Memory sync
  - Messaging gateway

All logging says OCTO. No third-party branding surfaces to the user.
"""
from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path
from typing import Callable

# ── Internal paths ────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
CFG_PATH    = BASE_DIR / "config" / "api_keys.json"
GW_CFG_PATH = BASE_DIR / "config" / "gateway.json"
_ENGINE_DIR = Path(os.environ.get("USERPROFILE", Path.home())) / ".hermes"

_GEMINI_COMPAT = "https://generativelanguage.googleapis.com/v1beta/openai/"


def _api_key() -> str:
    return json.loads(CFG_PATH.read_text(encoding="utf-8")).get("gemini_api_key", "")


def _load_gateway_cfg() -> dict:
    if GW_CFG_PATH.exists():
        return json.loads(GW_CFG_PATH.read_text(encoding="utf-8"))
    return {}


# ── Memory sync ───────────────────────────────────────────────────────────────
def sync_memory() -> None:
    """Export OCTO memory → internal engine MEMORY.md."""
    try:
        from memory.memory_manager import load_memory
        memory  = load_memory()
        _ENGINE_DIR.mkdir(parents=True, exist_ok=True)
        lines   = ["# OCTO User Memory\n\n"]
        for cat, items in memory.items():
            if not isinstance(items, dict) or not items:
                continue
            lines.append(f"## {cat.title()}\n")
            for key, entry in items.items():
                val = entry.get("value") if isinstance(entry, dict) else str(entry)
                if val:
                    lines.append(f"- **{key.replace('_',' ').title()}**: {val}\n")
            lines.append("\n")
        (_ENGINE_DIR / "MEMORY.md").write_text("".join(lines), encoding="utf-8")
        print("[OCTO] 💾 Memory synced")
    except Exception as e:
        print(f"[OCTO] ⚠️ Memory sync: {e}")


# ── Smart router ──────────────────────────────────────────────────────────────
_EXTENDED_KEYWORDS = {
    "terminal", "bash", "script", "execute", "run command", "shell",
    "install package", "pip install", "npm install", "git clone",
    "code execution", "compile", "docker", "schedule", "cron",
    "every day", "every hour", "every week", "at midnight",
    "skill", "delegation", "subagent",
}

def should_use_extended(goal: str) -> bool:
    gl = goal.lower()
    return any(kw in gl for kw in _EXTENDED_KEYWORDS)


# ── Extended agent executor ───────────────────────────────────────────────────
def run_extended(goal: str, speak: Callable | None = None, max_turns: int = 20) -> str:
    """Run goal through the extended 70+ tool engine."""
    try:
        from run_agent import AIAgent
    except ImportError:
        return f"Extended engine unavailable: {goal}"

    sync_memory()
    if speak:
        speak("Engaging full capability suite, sir.")

    result_holder: list = []
    error_holder:  list = []

    def _run():
        try:
            agent = AIAgent(
                base_url=_GEMINI_COMPAT,
                api_key=_api_key(),
                model="gemini-2.5-flash",
                max_iterations=max_turns,
                quiet_mode=True,
                skip_context_files=False,
                ephemeral_system_prompt=(
                    "You are OCTO, a powerful AI assistant. "
                    "Complete tasks efficiently using available tools. "
                    "Be concise. Address the user as 'sir'."
                ),
                enabled_toolsets=["terminal", "file", "code_execution",
                                   "memory", "todo", "skills",
                                   "delegation", "cronjob"],
            )
            resp     = agent.run_conversation(goal)
            messages = resp.get("messages", [])
            for m in reversed(messages):
                if m.get("role") == "assistant":
                    content = m.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(
                            p.get("text", "") for p in content
                            if isinstance(p, dict) and p.get("type") == "text"
                        )
                    if content:
                        result_holder.append(content.strip())
                        return
            result_holder.append("Task completed.")
        except Exception as e:
            error_holder.append(str(e))

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=180)

    if error_holder:
        print(f"[OCTO] ❌ Extended task failed: {error_holder[0]}")
        return f"Task failed: {error_holder[0][:200]}"
    return result_holder[0] if result_holder else "Task completed."


# ── Cron / Scheduler ──────────────────────────────────────────────────────────
def list_scheduled() -> list[dict]:
    """Return all OCTO scheduled jobs."""
    try:
        from cron.jobs import list_jobs
        return list_jobs()
    except Exception as e:
        print(f"[OCTO] ⚠️ Schedule list: {e}")
        return []


def create_scheduled(prompt: str, schedule: str, label: str = "") -> dict | None:
    """Create a recurring OCTO scheduled job."""
    try:
        from cron.jobs import create_job, parse_schedule
        parsed = parse_schedule(schedule)
        if not parsed:
            print(f"[OCTO] ⚠️ Cannot parse schedule: {schedule}")
            return None
        job = create_job(
            prompt=prompt,
            schedule=parsed,
            label=label or prompt[:40],
            model="gemini-2.5-flash",
        )
        print(f"[OCTO] ⏰ Scheduled: {job.get('id')} — {schedule}")
        return job
    except Exception as e:
        print(f"[OCTO] ❌ Schedule create: {e}")
        return None


def delete_scheduled(job_id: str) -> bool:
    try:
        from cron.jobs import remove_job
        remove_job(job_id)
        return True
    except Exception as e:
        print(f"[OCTO] ⚠️ Schedule delete: {e}")
        return False


# ── Skills ────────────────────────────────────────────────────────────────────
def list_capabilities() -> list[dict]:
    """Return installed OCTO capability modules (skills)."""
    try:
        from agent.skill_utils import get_installed_skills
        return get_installed_skills() or []
    except Exception:
        try:
            d = _ENGINE_DIR / "skills"
            return [{"name": p.name} for p in d.iterdir() if p.is_dir()] if d.exists() else []
        except Exception:
            return []


def install_capability(name: str) -> bool:
    """Install a capability module by name."""
    try:
        import subprocess
        exe = Path(sys.executable).parent / "hermes.exe"
        r   = subprocess.run([str(exe), "skills", "install", name, "--yes"],
                             capture_output=True, text=True, timeout=60)
        return r.returncode == 0
    except Exception as e:
        print(f"[OCTO] ❌ Capability install: {e}")
        return False


# ── Messaging gateway config writer ──────────────────────────────────────────
def write_gateway_config(platforms: dict) -> None:
    """
    Write OCTO gateway config into the engine config file.
    `platforms` = dict loaded from config/gateway.json.
    """
    import yaml  # only needed here

    _ENGINE_DIR.mkdir(parents=True, exist_ok=True)
    cfg_file = _ENGINE_DIR / "config.yaml"

    # Read existing engine config (preserve non-platform keys)
    existing: dict = {}
    if cfg_file.exists():
        try:
            existing = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}
        except Exception:
            existing = {}

    # Build gateway block
    gw_platforms: dict = {}
    for name, p in platforms.items():
        if not p.get("enabled"):
            continue
        block: dict = {"enabled": True}
        if p.get("token"):
            block["token"] = p["token"]
        if p.get("api_key"):
            block["api_key"] = p["api_key"]
        extra: dict = {}
        for k in ("session_path", "http_url", "account",
                  "allowed_users", "allowed_roles"):
            if p.get(k):
                extra[k] = p[k]
        if extra:
            block["extra"] = extra
        gw_platforms[name] = block

    existing["gateway"] = {"platforms": gw_platforms}

    # Ensure model is set
    if not existing.get("model"):
        existing["model"] = "gemini-2.5-flash"

    cfg_file.write_text(yaml.dump(existing, default_flow_style=False), encoding="utf-8")
    print(f"[OCTO] 🌐 Gateway config written ({len(gw_platforms)} platforms)")


# ── Aliases used by main.py and task_queue.py ─────────────────────────────────
# Keep old names working so existing call-sites don't break
sync_memory_to_hermes = sync_memory
run_with_hermes       = run_extended
should_use_hermes     = should_use_extended
create_cron_job       = create_scheduled
list_cron_jobs        = list_scheduled
list_skills           = list_capabilities
