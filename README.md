# 🐙 OCTO-Pro Super Model

**Unified Open-Source Super Agent · Voice · Vision · OS Control · Deep Research · Multi-Platform Messaging**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()
[![DeerFlow](https://img.shields.io/badge/Orchestration-DeerFlow%202.0-orange)](https://github.com/bytedance/deer-flow)
[![Hermes](https://img.shields.io/badge/Memory-Hermes%20Agent-purple)](https://github.com/NousResearch/hermes-agent)

---

## ✨ What is OCTO-Pro?

OCTO-Pro is a **unified Super Agent** that bridges the gap between high-level human intent and low-level system execution. It synthesizes real-time sensory perception, stateful orchestration, autonomous learning, and intelligent model routing into a single, cohesive ecosystem.

Unlike disparate AI toolkits, OCTO-Pro functions as one platform where sensory inputs from the edge feed into a central orchestration harness, backed by a persistent memory layer and a high-performance model proxy.

---

## 🧱 System Architecture — Four Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                         OCTO-Pro Super Model                        │
├──────────────────┬────────────────┬─────────────────┬──────────────┤
│  Sensory & OS    │ Orchestration  │  Learning Loop  │ Model Proxy  │
│  Mark-XXXIX      │ DeerFlow 2.0   │  Hermes Agent   │ Free-Claude  │
│  (Body)          │ (Brain)        │  (Memory)       │ (Nervous Sys)│
└──────────────────┴────────────────┴─────────────────┴──────────────┘
```

| Layer | Tool | Role |
|-------|------|------|
| 🖥️ **Sensory & OS Control** | [Mark-XXXIX](https://github.com/FatihMakes/Mark-XXXIX) | Real-time voice/vision perception and native OS manipulation — the "body" |
| 🧠 **Orchestration & Sandbox** | [DeerFlow 2.0](https://github.com/bytedance/deer-flow) | Lead agent logic, sub-agent decomposition, isolated execution — the "brain" |
| 💾 **Learning & Persistence** | [Hermes Agent](https://github.com/NousResearch/hermes-agent) | Autonomous skill creation and persistent user/context modeling — the "memory" |
| ⚡ **Model Routing Proxy** | [Free-Claude-Code](https://github.com/Alishahryar1/free-claude-code) | API interception, protocol normalization, and backend routing — the "nervous system" |

---

## 🚀 Capabilities

| Feature | Description |
|---------|-------------|
| 🎙️ **Real-time Voice** | Ultra-low latency Gemini Live conversation with seamless voice ↔ keyboard switching |
| 👁️ **Visual Awareness** | Real-time screen processing and webcam vision — the agent sees your workspace |
| 🖥️ **OS Control** | App orchestration, file I/O, terminal execution, volume, brightness, WiFi |
| 🤖 **Sub-Agent Orchestration** | DeerFlow decomposes complex goals into parallel workstreams |
| 🧠 **Persistent Memory** | FTS5 session search, Honcho user modeling, and memory nudges |
| 📚 **Autonomous Skill Creation** | Hermes creates and improves skills from successful experiences |
| 🔌 **MCP Tools** | Connect filesystem, GitHub, Postgres, Brave Search, Puppeteer, and more |
| ⚡ **Model Proxy** | Route requests to NVIDIA NIM, DeepSeek, Kimi, Ollama — transparently |
| 📡 **Multi-Channel Gateway** | Telegram · Discord · Slack · WhatsApp · Signal · DingTalk |
| 🔒 **Security Hardened** | Loopback-only Admin UI, Nginx pre-auth, VLAN isolation for high-privilege agents |
| 🌙 **Hibernate-on-Idle** | Modal/Daytona backends — near-zero cost when idle, instant resume |

---

## ⚡ Quick Start

### Prerequisites

```bash
# Required
python 3.11–3.14    (uv recommended for package management)
node.js             (for MCP servers)
playwright          (for vision/browser control)
ffmpeg              (for audio processing)
ripgrep             (for file search)
```

### Install & Run

```bash
git clone https://github.com/Boyapati13/octo.git
cd octo
pip install -r requirements.txt
playwright install
python main.py
```

### Optional: DeerFlow 2.0 Orchestration Backend

```bash
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow
pip install -e backend
uvicorn backend.app.gateway.app:app --port 2026
```

### Optional: Free-Claude-Code Model Proxy

```bash
git clone https://github.com/Alishahryar1/free-claude-code.git
cd free-claude-code
pip install -r requirements.txt
python main.py   # Admin UI at http://127.0.0.1:<port>
```

> **Note:** The Admin UI is bound to `127.0.0.1` loopback only. For external access, place an Nginx reverse proxy with strong pre-authentication in front of it.

### Optional: Hermes Agent Memory Engine

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
pip install -e .
```

---

## 🏗️ Detailed Architecture

```
octo/
├── main.py                      # Entry point — Gemini Live voice loop + tool dispatch
├── ui.py                        # PyQt6 adaptive UI (resizable, transparent)
├── ui_pages/                    # Settings, MCP, Gateway, Skills, Memory, Scheduler
│
├── agent/                       # 🧠 Orchestration layer
│   ├── planner.py               # LLM-driven task decomposition
│   ├── executor.py              # Step execution + code generation
│   ├── error_handler.py         # Strict Tool-Call Recovery + retry logic
│   ├── task_queue.py            # Async task queue
│   ├── context_compressor.py    # Context window compression (Hermes-inspired)
│   ├── hermes_bridge.py         # Hermes Agent integration bridge
│   └── mcp_bridge.py            # MCP server client
│
├── channels/                    # 📡 Multi-platform messaging gateway
│   ├── manager.py               # Channel orchestrator
│   ├── telegram_channel.py      # Typewriter-style streaming
│   ├── discord_channel.py       # Typewriter-style streaming
│   ├── slack_channel.py
│   └── whatsapp_channel.py
│
├── actions/                     # ⚙️ Atomic OS Actions (Mark-XXXIX layer)
│   ├── browser_control.py       # Vision-based browser automation
│   ├── computer_control.py      # Mouse, keyboard, window management
│   ├── computer_settings.py     # Volume, brightness, WiFi, power
│   ├── screen_processor.py      # Real-time screen capture + analysis
│   ├── file_controller.py       # File I/O operations
│   ├── file_processor.py        # Deep PDF and source code analysis
│   ├── dev_agent.py             # Terminal + git + docker execution
│   ├── deep_research.py         # Long-horizon web crawling + synthesis
│   ├── deerflow_task.py         # DeerFlow sub-agent dispatch
│   └── ...                      # 15+ additional action modules
│
├── memory/                      # 💾 Hermes learning loop
│   └── memory_manager.py        # FTS5 session search + persistent JSON store
│
├── skills/                      # 📚 Autonomous skill management
│   └── skill_manager.py         # agentskills.io standard discovery
│
├── deerflow_bridge.py           # DeerFlow 2.0 integration
├── core/
│   ├── prompt.txt               # OCTO-Pro v2.0 system prompt
│   └── text_llm.py              # LLM client (Gemini / OpenAI-compatible)
└── config/
    ├── api_keys.json            # API key store
    └── mcp_servers.json         # MCP server definitions
```

---

## ⚡ Model Routing & Proxy Tiers

Free-Claude-Code intercepts Anthropic Messages API traffic and routes to the optimal backend:

| Tier | Recommended Backends |
|------|----------------------|
| **Opus** (Pro/Ultra) | NVIDIA NIM · Kimi 2.5 · Doubao-Seed-2.0-Code |
| **Sonnet** (Standard) | DeepSeek v3.2 · Wafer · OpenRouter |
| **Haiku** (Flash) | Local Ollama · llama.cpp · LM Studio |

The proxy handles **protocol normalization** — translating OpenAI-style chat streaming into Anthropic SSE format, including thinking blocks and tool-call mapping, so clients never need to change.

### Context Management

- `CLAUDE_CODE_AUTO_COMPACT_WINDOW` is set to **190,000 tokens**
- DeerFlow uses **Strict Tool-Call Recovery** to fix malformed history by injecting placeholders for dangling calls

---

## 🧠 DeerFlow Orchestration Modes

| Mode | Description |
|------|-------------|
| `flash` | Single-agent reply — fastest |
| `standard` | Balanced depth — default |
| `pro` | Enables thinking and planning |
| `ultra` | Full sub-agent orchestration — most thorough |

### Sub-Agent Lifecycle

```
Lead Agent → decompose goal
    ↓
Sub-agents (parallel workstreams)
    ├── Initialization: scoped context + tool-set
    ├── Isolation: separate context (prevents token bloat)
    ├── Filesystem offload: intermediate results → disk
    └── Synthesis: results → Lead Agent → final output
```

### Sandbox Execution Modes

| Mode | Provider | Isolation Strategy |
|------|----------|--------------------|
| Local | `LocalSandboxProvider` | Host-mapped directories; Bash disabled by default |
| Docker | `AioSandboxProvider` | Isolated container via shell-service |
| K8s | Provisioner Service | Scalable pods with PVC data scoped by user |

---

## 💾 Hermes Memory Architecture

| Feature | Implementation |
|---------|----------------|
| **Session Search** | FTS5 full-text search with LLM-based summarization |
| **User Modeling** | Honcho dialectic profile — preferences, tech stack |
| **Memory Nudges** | Internal prompts that proactively store relevant context |
| **Skill Creation** | Auto-creates skills from successful experiences (agentskills.io) |
| **Hibernate-on-Idle** | Modal + Daytona: near-zero cost when inactive, instant resume |

---

## 📡 Multi-Channel Gateway

Configure in **Settings → Gateway**:

| Platform | Credentials |
|----------|-------------|
| **Telegram** | Bot token from @BotFather |
| **Discord** | Bot token + Message Content Intent |
| **Slack** | `xoxb-` bot token + `xapp-` Socket Mode token |
| **WhatsApp** | Meta Cloud API token + Phone Number ID |
| **Signal** | Signal CLI instance |
| **DingTalk** | App key + secret |

Voice interactions use **FFmpeg** for audio processing and either local **Whisper** or **NVIDIA NIM (Riva gRPC)** for transcription. Discord and Telegram support typewriter-style progress streaming.

---

## 🔌 MCP Servers

Edit `config/mcp_servers.json` or use **Settings → MCP**:

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
      "headers": { "Authorization": "Bearer ghp_..." }
    },
    {
      "name": "postgres",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"]
    }
  ]
}
```

---

## 🚀 Deployment Sizing

| Target | Resources | Use Case |
|--------|-----------|----------|
| **Local Evaluation** | 8 vCPU · 16 GB RAM · 20 GB SSD | Single developer; hosted APIs |
| **Docker Development** | 8 vCPU · 16 GB RAM · 25 GB SSD | Container testing; sandbox builds |
| **Production Server** | 16 vCPU · 32 GB RAM · 40 GB SSD | Multi-agent runs; heavy sandbox workloads |

Production deployment recommended via **Docker Compose**. For serverless persistence, Modal/Daytona backends enable **hibernate-on-idle** on low-cost VPS tiers.

---

## 🔒 Security Hardening

- **Loopback enforcement**: All Admin UIs bound to `127.0.0.1` by default
- **Authentication gateway**: Nginx reverse proxy with strong pre-authentication for any external access
- **XSS mitigation**: Gateway serves active web content (HTML/SVG) as download attachments, never inline
- **Network isolation**: High-privilege agents executing system commands placed in a dedicated VLAN, isolated from the public internet
- **Key management**: All API keys stored locally in `config/api_keys.json` — never transmitted externally

---

## 📋 Requirements

```
Python 3.11–3.14
Windows 10/11 · macOS · Linux
Gemini API key (free tier: gemini-2.5-flash)
Node.js (for MCP servers)
FFmpeg (for audio)
Playwright (for vision)
ripgrep (for file search)
```

Optional for full stack:
- Docker / Docker Compose (sandbox execution)
- Kubernetes (production scale)
- Modal or Daytona account (hibernate-on-idle)
- NVIDIA NIM API key (high-performance transcription + routing)

---

## 🧠 Model Support

| Provider | Models |
|----------|--------|
| **Gemini** (default) | 2.5 Flash, 2.5 Pro, Ultra (free tier works) |
| **NVIDIA NIM** | Opus-tier — high-performance routing |
| **DeepSeek** | v3.2 — Sonnet-tier standard |
| **Kimi / Doubao** | Opus-tier alternatives |
| **Ollama (local)** | gemma4, llama3, mistral, qwen — Haiku-tier |
| **OpenAI-compatible** | Any endpoint via Free-Claude-Code proxy |

---

## 🤝 Credits

OCTO-Pro stands on the shoulders of these open-source projects:

| Project | Contribution |
|---------|-------------|
| [FatihMakes/Mark-XXXIX](https://github.com/FatihMakes/Mark-XXXIX) | Core voice assistant · OS sensory foundation |
| [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | LangGraph orchestration · sub-agent decomposition · sandbox execution |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | Context engine · MCP tools · skill creation · persistent memory |
| [Alishahryar1/free-claude-code](https://github.com/Alishahryar1/free-claude-code) | Model routing proxy · protocol normalization · multi-backend support |

---

## 📄 License

MIT — see [LICENSE](LICENSE)
