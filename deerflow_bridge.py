"""
deerflow_bridge.py
==================
OCTO ↔ DeerFlow integration layer.

Connects OCTO's voice/action runtime to DeerFlow's LangGraph super-agent
backend, enabling long-horizon research, sub-agents, skills, and persistent
memory that survive across sessions.

DeerFlow API reference: http://localhost:2026/api
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from typing import Callable, Generator
from pathlib import Path

# ── optional httpx / requests fallback ───────────────────────────────────────
try:
    import httpx as _http_lib
    _USE_HTTPX = True
except ImportError:
    import urllib.request as _http_lib  # type: ignore
    _USE_HTTPX = False

DEERFLOW_BASE      = "http://localhost:2026"
GATEWAY_API        = f"{DEERFLOW_BASE}/api"
LANGGRAPH_API      = f"{DEERFLOW_BASE}/api/langgraph"
CONNECT_TIMEOUT    = 3.0   # seconds
REQUEST_TIMEOUT    = 120.0

_session_thread_id: dict[str, str] = {}   # thread_id per OCTO session


# ─────────────────────────────────────────────────────────────────────────────
# Low-level HTTP helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get(path: str, timeout: float = REQUEST_TIMEOUT) -> dict:
    url = f"{GATEWAY_API}{path}"
    if _USE_HTTPX:
        with _http_lib.Client(timeout=timeout) as c:
            r = c.get(url)
            r.raise_for_status()
            return r.json()
    else:
        req = _http_lib.Request(url)
        with _http_lib.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())


def _post(path: str, body: dict, timeout: float = REQUEST_TIMEOUT) -> dict:
    url = f"{GATEWAY_API}{path}"
    data = json.dumps(body).encode()
    if _USE_HTTPX:
        with _http_lib.Client(timeout=timeout) as c:
            r = c.post(url, content=data, headers={"Content-Type": "application/json"})
            r.raise_for_status()
            return r.json()
    else:
        req = _http_lib.Request(url, data=data,
                                headers={"Content-Type": "application/json"})
        with _http_lib.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())


def _stream_post(path: str, body: dict, timeout: float = REQUEST_TIMEOUT) -> Generator[str, None, None]:
    """Yield SSE lines from a streaming POST."""
    url = f"{GATEWAY_API}{path}"
    data = json.dumps(body).encode()
    if _USE_HTTPX:
        with _http_lib.Client(timeout=timeout) as c:
            with c.stream("POST", url, content=data,
                          headers={"Content-Type": "application/json",
                                   "Accept": "text/event-stream"}) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        yield line
    else:
        req = _http_lib.Request(url, data=data,
                                headers={"Content-Type": "application/json",
                                         "Accept": "text/event-stream"})
        with _http_lib.urlopen(req, timeout=timeout) as r:
            for raw in r:
                line = raw.decode("utf-8").rstrip("\n")
                if line:
                    yield line


# ─────────────────────────────────────────────────────────────────────────────
# Health / availability
# ─────────────────────────────────────────────────────────────────────────────

def is_running() -> bool:
    """Return True if DeerFlow is reachable."""
    try:
        _get("/health", timeout=CONNECT_TIMEOUT)
        return True
    except Exception:
        return False


def wait_until_ready(timeout: float = 30.0) -> bool:
    """Block until DeerFlow is up, or until *timeout* seconds elapse."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_running():
            return True
        time.sleep(1.5)
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Thread / conversation management
# ─────────────────────────────────────────────────────────────────────────────

def new_thread() -> str:
    """Create a new DeerFlow conversation thread and return its ID."""
    result = _post("/threads", {})
    tid = result.get("thread_id") or result.get("id") or str(uuid.uuid4())
    return tid


def get_or_create_thread(session_id: str = "default") -> str:
    if session_id not in _session_thread_id:
        _session_thread_id[session_id] = new_thread()
    return _session_thread_id[session_id]


# ─────────────────────────────────────────────────────────────────────────────
# Chat / research
# ─────────────────────────────────────────────────────────────────────────────

def chat(
    message: str,
    session_id: str = "default",
    model: str | None = None,
    thinking: bool = False,
    subagents: bool = False,
) -> str:
    """
    Send *message* to DeerFlow and return the assistant's text reply.
    Uses the existing thread for *session_id* (creates one if needed).
    """
    thread_id = get_or_create_thread(session_id)
    body: dict = {
        "message": message,
        "thread_id": thread_id,
    }
    if model:
        body["model"] = model
    if thinking:
        body["thinking_enabled"] = True
    if subagents:
        body["subagent_enabled"] = True

    result = _post("/chat", body)
    content = result.get("content") or result.get("message") or str(result)
    return content.strip()


def deep_research(
    topic: str,
    session_id: str = "default",
    on_progress: Callable[[str], None] | None = None,
) -> str:
    """
    Submit a deep-research task to DeerFlow and stream progress events.
    Returns the final compiled report text.
    """
    thread_id = get_or_create_thread(session_id)
    body = {
        "message": topic,
        "thread_id": thread_id,
        "thinking_enabled": True,
        "subagent_enabled": True,
    }

    chunks: list[str] = []
    try:
        for line in _stream_post("/chat/stream", body):
            if line.startswith("data: "):
                raw = line[6:]
                if raw.strip() in ("", "[DONE]"):
                    continue
                try:
                    ev = json.loads(raw)
                    text = (
                        ev.get("content")
                        or ev.get("text")
                        or ev.get("data", {}).get("content", "")
                    )
                    if text:
                        chunks.append(text)
                        if on_progress:
                            on_progress(text)
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        # Fallback to non-streaming if SSE not supported
        try:
            result = _post("/chat", body)
            return result.get("content", str(result))
        except Exception as e2:
            return f"DeerFlow error: {e2}"

    return "".join(chunks).strip() or "Research complete — no text returned."


# ─────────────────────────────────────────────────────────────────────────────
# Skills catalog
# ─────────────────────────────────────────────────────────────────────────────

_LOCAL_SKILLS_PATH = Path(__file__).parent / "deer-flow" / "skills" / "public"


def list_local_skills() -> list[dict]:
    """List all skills bundled from the cloned DeerFlow repo."""
    skills = []
    if not _LOCAL_SKILLS_PATH.exists():
        return skills
    for skill_dir in sorted(_LOCAL_SKILLS_PATH.iterdir()):
        md = skill_dir / "SKILL.md"
        if not md.exists():
            continue
        content = md.read_text(encoding="utf-8", errors="replace")
        # Parse YAML frontmatter
        name = skill_dir.name
        description = ""
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                frontmatter = content[3:end]
                for line in frontmatter.splitlines():
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip()
                    elif line.startswith("description:"):
                        description = line.split(":", 1)[1].strip()
        if not description:
            # Grab first non-header line as description
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("---") and not line.startswith("name:") and not line.startswith("description:"):
                    description = line[:120]
                    break
        skills.append({
            "id":          skill_dir.name,
            "name":        name,
            "description": description,
            "path":        str(md),
        })
    return skills


def search_skills(query: str) -> list[dict]:
    """
    Search local DeerFlow skills by keyword.
    Falls back to DeerFlow API if running.
    """
    q = query.lower()
    local = [
        s for s in list_local_skills()
        if q in s["id"].lower() or q in s["name"].lower() or q in s["description"].lower()
    ]

    # Also try DeerFlow API
    if is_running():
        try:
            api_result = _get("/skills")
            api_skills = api_result.get("skills", [])
            seen_ids = {s["id"] for s in local}
            for s in api_skills:
                sid = s.get("id") or s.get("name", "")
                if sid not in seen_ids:
                    if (q in sid.lower()
                            or q in s.get("name", "").lower()
                            or q in s.get("description", "").lower()):
                        local.append(s)
                        seen_ids.add(sid)
        except Exception:
            pass

    return local


def get_skill_content(skill_id: str) -> str | None:
    """Return the full SKILL.md content for a given skill ID."""
    md_path = _LOCAL_SKILLS_PATH / skill_id / "SKILL.md"
    if md_path.exists():
        return md_path.read_text(encoding="utf-8", errors="replace")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Memory sync (OCTO → DeerFlow)
# ─────────────────────────────────────────────────────────────────────────────

def push_memory_to_deerflow(octo_memory: dict) -> bool:
    """
    Flatten OCTO's memory dict and upsert key facts into DeerFlow's memory.
    Returns True on success.
    """
    if not is_running():
        return False
    try:
        facts: list[dict] = []
        for category, items in octo_memory.items():
            if not isinstance(items, dict):
                continue
            for key, entry in items.items():
                if isinstance(entry, dict) and "value" in entry:
                    facts.append({
                        "content": f"[{category}] {key}: {entry['value']}"
                    })
        if facts:
            _post("/memory/upsert", {"facts": facts})
        return True
    except Exception:
        return False


def pull_memory_from_deerflow() -> list[str]:
    """Retrieve DeerFlow memory facts as plain strings."""
    if not is_running():
        return []
    try:
        result = _get("/memory")
        return [m.get("content", "") for m in result.get("memories", [])]
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────

def list_models() -> list[str]:
    """Return model names available in DeerFlow."""
    if not is_running():
        return []
    try:
        result = _get("/models")
        return [m.get("name") or m.get("id", "") for m in result.get("models", [])]
    except Exception:
        return []
