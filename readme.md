# OCTO — Personal AI Assistant

A real-time voice AI that hears, sees, and controls your computer.  
Built on Gemini Live API with a local Ollama fallback for text tasks.

---

## Features

| Capability | Description |
|---|---|
| Real-time Voice | Live two-way audio — speak and OCTO responds instantly |
| Screen & Camera Vision | Analyzes your screen or webcam on demand |
| System Control | Launch apps, manage files, adjust volume, control windows |
| Browser Automation | Navigate, click, fill forms, screenshot any browser |
| File Processing | Summarize PDFs, analyze images, edit code, process CSVs |
| YouTube | Play videos, summarize transcripts, browse trending |
| Flight Search | Find and compare flights via Google Flights |
| Game Updater | Update Steam and Epic Games on a schedule |
| Reminders | Set timed reminders via Windows Task Scheduler |
| Persistent Memory | Remembers your name, preferences, projects across sessions |
| Autonomous Tasks | Multi-step goal execution with planning |
| Dev Agent | Builds complete multi-file projects from scratch |
| Text Input | Type commands when voice is not available |
| File Upload | Drop any file onto the interface for analysis |

---

## Quick Start

```bash
git clone https://github.com/Boyapati13/octo.git
cd octo
pip install -r requirements.txt
playwright install chromium
python main.py
```

On first launch a setup screen appears — paste your Gemini API key, click **Detect Models** to auto-fill the voice model, then **Initialise Systems**.

---

## Requirements

| Requirement | Details |
|---|---|
| OS | Windows 10/11, macOS, Linux |
| Python | 3.11 or 3.12 (3.12 recommended) |
| Gemini API key | Free key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| Microphone | Required for voice input |
| Ollama (optional) | Local AI backup — [ollama.com](https://ollama.com) |

---

## Model Architecture

| Role | Model | Notes |
|---|---|---|
| Voice (Live API) | `gemini-3.1-flash-live-preview` | Real-time audio — configurable |
| Text / Vision | `gemini-2.5-flash` | Free-tier quota — configurable |
| Local fallback | Auto-detected via `ollama list` | Prefers `gemma4`, then `llama3`, `mistral` |

Voice always uses the Gemini Live API regardless of text model setting.  
If Gemini text calls fail, OCTO falls back to your locally installed Ollama model automatically.

---

## Configuration

### First launch
The setup screen appears automatically when no valid API key is found.

1. Enter your **Gemini API key**
2. Click **⟳ Detect Models** — fetches available models for your key
3. The **Voice Model** field is filled automatically (edit if needed)
4. Set **Ollama URL** if you want local fallback (`http://localhost:11434`)
5. Click **▸ Initialise Systems**

### Changing settings later
Click the **⚙** button in the top-left header at any time.

- Update API key
- Switch voice model (type or detect)
- Choose text model: `gemini-2.5-flash` / `gemini-3.1-pro-preview` / Ollama only
- Set Ollama URL and click **⟳ Detect Models** to see your local models

---

## Ollama Local Backup

If you have [Ollama](https://ollama.com) installed with local models, OCTO uses them automatically when Gemini text calls are unavailable or rate-limited.

Check your installed models:
```bash
ollama list
```

OCTO selects the best available model in this priority order:  
`gemma4` → `gemma3` → `llama3.x` → `qwen2.5` → `mistral` → first available

Cloud-proxied Ollama models (tagged `:cloud`) are skipped for the local fallback.

To pull a recommended model:
```bash
ollama pull gemma3
```

---

## Auto-launch on Windows

A startup shortcut is created automatically at:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\OCTO.lnk
```

OCTO will start silently when you log in. To disable, delete that shortcut.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `F4` | Toggle microphone mute |
| `F11` | Toggle fullscreen |
| Enter (text field) | Send text command |

---

## Security

- `config/api_keys.json` is **gitignored** and never committed
- Never share or publish your API key
- Generate a new key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) if leaked

---

## Project Structure

```
octo/
├── main.py                 # Voice engine (Gemini Live API)
├── ui.py                   # PyQt6 interface + setup/settings overlays
├── core/
│   ├── text_llm.py         # Gemini text → Ollama fallback router
│   └── prompt.txt          # System prompt
├── actions/                # Tool implementations
│   ├── browser_control.py
│   ├── screen_processor.py
│   ├── file_processor.py
│   ├── computer_control.py
│   └── ...
├── agent/                  # Planner + executor for multi-step tasks
├── memory/                 # Persistent memory manager
├── config/
│   └── api_keys.json       # Local only — gitignored
├── requirements.txt
└── octo.bat                # Windows launcher
```

---

## License

Personal and non-commercial use only.  
Licensed under [Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
