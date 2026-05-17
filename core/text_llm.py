"""Text LLM router: gemini-3.1-pro-preview first, Ollama fallback."""
from __future__ import annotations

import json
from pathlib import Path

_CFG_PATH          = Path(__file__).parent.parent / "config" / "api_keys.json"
TEXT_MODEL         = "gemini-3.1-pro-preview"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
# Preferred local models in priority order — first one found wins
_OLLAMA_PREFER = ["gemma3:latest", "gemma3", "gemma2", "llama3.2", "llama3", "mistral", "phi3"]


def _detect_ollama_model(base_url: str) -> str:
    """Return the best available local Ollama model."""
    try:
        import requests
        r = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=5)
        r.raise_for_status()
        installed = [m["name"] for m in r.json().get("models", [])]
        for pref in _OLLAMA_PREFER:
            for name in installed:
                if name.startswith(pref.split(":")[0]):
                    print(f"[TextLLM] Ollama model selected: {name}")
                    return name
        if installed:
            print(f"[TextLLM] Ollama fallback to first available: {installed[0]}")
            return installed[0]
    except Exception:
        pass
    return "gemma3"


def _cfg() -> dict:
    try:
        return json.loads(_CFG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def ask(
    prompt: str,
    system: str = "",
    image_bytes: bytes | None = None,
    mime_type: str = "image/jpeg",
) -> str:
    """Return a text response, honouring text_llm_provider from config."""
    cfg      = _cfg()
    provider = cfg.get("text_llm_provider", "auto").lower().strip()
    key      = cfg.get("gemini_api_key", "")
    has_key  = bool(key) and key not in ("", "YOUR_GEMINI_API_KEY_HERE")

    if provider == "ollama":
        return _ollama(prompt, system, cfg)

    # gemini-specific model override
    model = TEXT_MODEL
    if provider not in ("auto", "ollama", ""):
        model = provider      # e.g. "gemini-3.1-pro-preview-customtools"

    if provider != "ollama" and has_key:
        try:
            return _gemini(prompt, system, image_bytes, mime_type, key, model=model)
        except Exception as e:
            print(f"[TextLLM] Gemini failed ({e.__class__.__name__}: {e}) — trying Ollama")

    return _ollama(prompt, system, cfg)


def _gemini(
    prompt: str,
    system: str,
    image_bytes: bytes | None,
    mime_type: str,
    key: str,
    model: str = TEXT_MODEL,
) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    parts: list = []
    if image_bytes:
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
    parts.append(types.Part.from_text(text=prompt))

    cfg = types.GenerateContentConfig(system_instruction=system) if system else None
    resp = client.models.generate_content(
        model=model,
        contents=parts,
        config=cfg,
    )
    return (resp.text or "").strip()


def _ollama(prompt: str, system: str, cfg: dict) -> str:
    import requests

    base  = cfg.get("ollama_base_url", DEFAULT_OLLAMA_URL).rstrip("/")
    model = cfg.get("ollama_model") or _detect_ollama_model(base)
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        r = requests.post(
            f"{base}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["message"]["content"].strip()
    except Exception as e:
        raise RuntimeError(f"Ollama at {base} failed: {e}") from e
