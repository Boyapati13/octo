# 🐙 OCTO-Pro

**The Ultimate Open-Source Personal AI Platform**  
Voice · Vision · System Control · Deep Research · Multi-Platform Messaging

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()

---

## ✨ What is OCTO-Pro?

OCTO-Pro is a fully local, open-source personal AI that hears, sees, and controls your computer — available 24/7 on every device you use. It combines the best of three powerful systems:

| System | What it contributes |
|---|---|
| **OCTO** (core) | Real-time voice, screen vision, system control, UI |
| **[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)** | Context compression, MCP tools, skills, extended engine |
| **[bytedance/deer-flow](https://github.com/bytedance/deer-flow)** | LangGraph sub-agents, deep research, multi-channel gateway |

---

## 🚀 Capabilities

| Feature | Description |
|---|---|
| 🎙️ Real-time Voice | Ultra-low latency Gemini Live conversation |
| 🖥️ System Control | Volume, brightness, WiFi, apps, files, windows |
| 🧩 Autonomous Tasks | Multi-step planning + native execution |
| 👁️ Visual Awareness | Screen capture + webcam vision |
| 🧠 Persistent Memory | Remembers projects, preferences, context |
| 🗜️ Context Compression | Hermes-style summarisation — never lose context in long sessions |
| 🔌 MCP Tools | Connect filesystem, GitHub, Postgres, Brave Search, Puppeteer & more |
| 🤖 Extended Engine | 70+ tools: terminal, git, docker, cron, code execution |
| 🐮 DeerFlow Agent | Sub-agent orchestration, sandboxed code, skills catalog |
| 📡 Multi-Channel | Telegram · Discord · Slack · WhatsApp — one agent everywhere |
| ⚙️ Scheduler | Cron-style recurring tasks |

---

## ⚡ Quick Start

```bash
git clone https://github.com/Boyapati13/octo.git
cd octo
pip install -r requirements.txt
playwright install
python main.py
```

### Optional: DeerFlow backend (for deep research & sub-agents)
```bash
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow && pip install -e backend
uvicorn backend.app.gateway.app:app --port 2026
```

---

## 🏗️ Architecture

```
OCTO-Pro
├── main.py                  # Entry point (voice + UI)
├── ui.py                    # PyQt6 main window
├── ui_pages/                # Settings, MCP, Gateway, Skills, Memory, Scheduler
│
├── agent/
│   ├── planner.py           # Task decomposition (LLM-driven)
│   ├── executor.py          # Step execution + code generation
│   ├── error_handler.py     # Retry/fix logic
│   ├── task_queue.py        # Async task queue
│   ├── hermes_bridge.py     # ① Hermes extended engine bridge
│   ├── context_compressor.py# ② Context window compression (Hermes-inspired)
│   └── mcp_bridge.py        # ③ MCP server client
│
├── channels/                # Multi-platform messaging (DeerFlow-inspired)
│   ├── manager.py           # Channel orchestrator
│   ├── telegram_channel.py
│   ├── discord_channel.py
│   ├── slack_channel.py
│   └── whatsapp_channel.py
│
├── actions/                 # 15+ action modules
│   ├── web_search.py        ├── browser_control.py
│   ├── computer_settings.py ├── screen_processor.py
│   ├── file_controller.py   ├── dev_agent.py
│   ├── deerflow_task.py     ├── deep_research.py
│   └── ...
│
├── memory/memory_manager.py # Persistent memory (JSON)
├── skills/skill_manager.py  # DeerFlow skills discovery
├── core/                    # LLM client + system prompt
└── config/                  # API keys, gateway, MCP servers
```

---

## 🔌 MCP Servers

Connect any MCP server in **Settings → MCP** or edit `config/mcp_servers.json`:

```json
{
  "servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/Desktop"]
    },
    {
      "name": "github",
      "url": "https://mcp.github.com/sse",
      "headers": {"Authorization": "Bearer ghp_..."}
    }
  ]
}
```

---

## 📡 Multi-Channel Gateway

Configure in **Settings → Gateway** (or `config/gateway.json`):

| Platform | Required credentials |
|---|---|
| **Telegram** | Bot token from @BotFather |
| **Discord** | Bot token + Message Content Intent enabled |
| **Slack** | xoxb- bot token + xapp- Socket Mode token |
| **WhatsApp** | Meta Cloud API token + Phone Number ID |

---

## 📋 Requirements

- Python 3.11 or 3.12
- Windows 10/11, macOS, or Linux
- Gemini API key (free tier works — gemini-2.5-flash)
- Optional: Ollama for local models

---

## 🧠 Model Support

- **Gemini 2.5 Flash** (default, free tier)
- **Gemini Pro / Ultra** via API key
- **Ollama** (local models: gemma4, llama3, mistral, etc.)
- Any OpenAI-compatible endpoint

---

## 🤝 Credits

Built on the shoulders of giants:
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — context engine, MCP, skills
- [bytedance/deer-flow](https://github.com/bytedance/deer-flow) — LangGraph research agent, channels
- [FatihMakes/Mark-XXXIX](https://github.com/FatihMakes/Mark-XXXIX) — core voice assistant foundation
