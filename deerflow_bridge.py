"""
deerflow_bridge.py
==================
OCTO ↔ DeerFlow integration.

Priority order:
  1. Embedded DeerFlow — imported from octo/deerflow/  (zero network)
  2. Local HTTP        — localhost:2026                 (separate process)
  3. Graceful error   — human-readable fallback string
"""

from __future__ import annotations

import json
import logging
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Callable, Generator

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
for _p in [ROOT, ROOT / "deerflow"]:
    s = str(_p)
    if s not in sys.path:
        sys.path.insert(0, s)

DEERFLOW_BASE   = "http://localhost:2026"
GATEWAY_API     = f"{DEERFLOW_BASE}/api"
CONNECT_TIMEOUT = 3.0
REQUEST_TIMEOUT = 120.0

_session_thread_id: dict[str, str] = {}
_embedded_ready: bool | None = None
_embedded_lock  = threading.Lock()


# ── Embedded client ───────────────────────────────────────────────────────────

def _get_embedded_client():
    global _embedded_ready
    with _embedded_lock:
        if _embedded_ready is None:
            try:
                from deerflow.client import DeerFlowClient  # type: ignore
                _embedded_ready = True
            except ImportError:
                _embedded_ready = False
    if not _embedded_ready:
        return None
    try:
        from deerflow.client import DeerFlowClient  # type: ignore
        return DeerFlowClient()
    except Exception:
        return None


# ── HTTP helpers ──────────────────────────────────────────────────────────────

try:
    import httpx as _hx
    _USE_HTTPX = True
except ImportError:
    _USE_HTTPX = False


def _http_get(path: str, timeout: float = REQUEST_TIMEOUT) -> dict:
    url = f"{GATEWAY_API}{path}"
    if _USE_HTTPX:
        with _hx.Client(timeout=timeout) as c:
            r = c.get(url); r.raise_for_status(); return r.json()
    import urllib.request
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def _http_post(path: str, body: dict, timeout: float = REQUEST_TIMEOUT) -> dict:
    url  = f"{GATEWAY_API}{path}"
    data = json.dumps(body).encode()
    if _USE_HTTPX:
        with _hx.Client(timeout=timeout) as c:
            r = c.post(url, content=data, headers={"Content-Type": "application/json"})
            r.raise_for_status(); return r.json()
    import urllib.request
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _http_stream(path: str, body: dict, timeout: float = REQUEST_TIMEOUT) -> Generator[str, None, None]:
    url  = f"{GATEWAY_API}{path}"
    data = json.dumps(body).encode()
    if _USE_HTTPX:
        with _hx.Client(timeout=timeout) as c:
            with c.stream("POST", url, content=data,
                          headers={"Content-Type": "application/json",
                                   "Accept": "text/event-stream"}) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line: yield line
    else:
        import urllib.request
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json",
                                              "Accept": "text/event-stream"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for raw in r:
                line = raw.decode("utf-8").rstrip("\n")
                if line: yield line


# ── Health ────────────────────────────────────────────────────────────────────

def is_embedded() -> bool:
    return _get_embedded_client() is not None

def is_http_running() -> bool:
    try:
        _http_get("/health", timeout=CONNECT_TIMEOUT); return True
    except Exception:
        return False

def is_running() -> bool:
    return is_embedded() or is_http_running()

def wait_until_ready(timeout: float = 30.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_running(): return True
        time.sleep(1.5)
    return False


# ── Thread management ─────────────────────────────────────────────────────────

def new_thread() -> str:
    try:
        r = _http_post("/threads", {})
        return r.get("thread_id") or r.get("id") or str(uuid.uuid4())
    except Exception:
        return str(uuid.uuid4())

def get_or_create_thread(session_id: str = "default") -> str:
    if session_id not in _session_thread_id:
        _session_thread_id[session_id] = new_thread()
    return _session_thread_id[session_id]


# ── Chat ──────────────────────────────────────────────────────────────────────

def chat(message: str, session_id: str = "default", model: str | None = None,
         thinking: bool = False, subagents: bool = False) -> str:
    # 1. Embedded
    client = _get_embedded_client()
    if client:
        try:
            return client.chat(message, model=model, thinking=thinking, subagents=subagents)
        except Exception:
            pass
    # 2. HTTP
    if is_http_running():
        tid  = get_or_create_thread(session_id)
        body: dict = {"message": message, "thread_id": tid}
        if model:     body["model"]            = model
        if thinking:  body["thinking_enabled"] = True
        if subagents: body["subagent_enabled"] = True
        try:
            r = _http_post("/chat", body)
            return (r.get("content") or r.get("message") or str(r)).strip()
        except Exception as e:
            return f"DeerFlow HTTP error: {e}"
    return "DeerFlow unavailable — run `python server.py` to start."


# ── Deep research ─────────────────────────────────────────────────────────────

def deep_research(topic: str, session_id: str = "default",
                  on_progress: Callable[[str], None] | None = None) -> str:
    # 1. Embedded
    client = _get_embedded_client()
    if client:
        try:
            return client.deep_research(topic, on_progress=on_progress)
        except Exception:
            pass
    # 2. HTTP streaming
    if is_http_running():
        tid  = get_or_create_thread(session_id)
        body = {"message": topic, "thread_id": tid,
                "thinking_enabled": True, "subagent_enabled": True}
        chunks: list[str] = []
        try:
            for line in _http_stream("/chat/stream", body):
                if not line.startswith("data: "): continue
                raw = line[6:]
                if raw.strip() in ("", "[DONE]"): continue
                try:
                    ev = json.loads(raw)
                    t  = ev.get("content") or ev.get("text") or ""
                    if t:
                        chunks.append(t)
                        if on_progress: on_progress(t)
                except json.JSONDecodeError:
                    pass
        except Exception:
            try:
                r = _http_post("/chat", body)
                return r.get("content", str(r))
            except Exception as e2:
                return f"DeerFlow error: {e2}"
        return "".join(chunks).strip() or "Research complete."
    return "DeerFlow unavailable — run `python server.py` to start."


# ── Skills ────────────────────────────────────────────────────────────────────

_SKILLS_PATH = ROOT / "deerflow" / "skills"

def list_local_skills() -> list[dict]:
    skills = []
    for md in sorted(_SKILLS_PATH.rglob("SKILL.md")):
        content = md.read_text(encoding="utf-8", errors="replace")
        name, desc = md.parent.name, ""
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                for line in content[3:end].splitlines():
                    if line.startswith("name:"):        name = line.split(":",1)[1].strip()
                    elif line.startswith("description:"): desc = line.split(":",1)[1].strip()
        if not desc:
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith(("#","---","name:","description:")):
                    desc = line[:120]; break
        skills.append({"id": md.parent.name, "name": name, "description": desc, "path": str(md)})
    return skills

def search_skills(query: str) -> list[dict]:
    q = query.lower()
    return [s for s in list_local_skills()
            if q in s["id"].lower() or q in s["name"].lower() or q in s["description"].lower()]

def get_skill_content(skill_id: str) -> str | None:
    for md in _SKILLS_PATH.rglob(f"{skill_id}/SKILL.md"):
        return md.read_text(encoding="utf-8", errors="replace")
    return None


# ── Memory sync ───────────────────────────────────────────────────────────────

def push_memory_to_deerflow(octo_memory: dict) -> bool:
    if not is_http_running(): return False
    try:
        facts = [{"content": f"[{c}] {k}: {e['value']}"}
                 for c, items in octo_memory.items() if isinstance(items, dict)
                 for k, e in items.items() if isinstance(e, dict) and "value" in e]
        if facts: _http_post("/memory/upsert", {"facts": facts})
        return True
    except Exception:
        return False

def pull_memory_from_deerflow() -> list[str]:
    if not is_http_running(): return []
    try:
        return [m.get("content","") for m in _http_get("/memory").get("memories",[])]
    except Exception:
        return []

def list_models() -> list[str]:
    if not is_http_running(): return []
    try:
        return [m.get("name") or m.get("id","") for m in _http_get("/models").get("models",[])]
    except Exception:
        return []
