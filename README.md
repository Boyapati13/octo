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

## 🔒 Local-First Data Privacy & Zero-Telemetry Guarantee

OCTO-Pro is built from the ground up as a **100% local-first application**. Your personal information, files, database configurations, trading suggestions, chat histories, and API credentials **NEVER leave your local device** (desktop or laptop), except for direct encrypted HTTPS requests made directly to official generative model providers you configure.

- **Zero Third-Party Telemetry**: We do not collect, intercept, or upload any user analytics, system data, model inputs/outputs, or usage telemetry to third parties.
- **Strictly Local Storage**: All API credentials and configuration options are saved locally inside `config/api_keys.json`, `config/gateway.json`, and `~/.fcc/.env`. They are never stored in a cloud database or transmitted to any middleman.
- **Local Sandbox Execution**: The DeerFlow sub-agent sandbox is mapped to local loopback directories or isolated local Docker containers to keep your code execution secure and private.
- **Independent MT5 Suggested Workflows**: Reconciliations between your technical candles and the Google TimesFM 2.5 predictions run completely on your machine.

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

### 🚀 1-Click Install (Windows — Recommended)

```powershell
# 1. Clone the repository
git clone https://github.com/Boyapati13/octo.git
cd octo

# 2. Run the installer (installs all deps, checks Ollama, Node.js, ffmpeg, etc.)
Set-ExecutionPolicy -Scope Process Bypass
.\install_octo.ps1
```

The installer will:
- Install all Python packages from `requirements.txt`
- Install Playwright browser binaries
- Check for Node.js (MCP servers), ffmpeg (audio), ripgrep (file search)
- Check for Ollama + show model pull commands (Gemma 3, Llama 3.2, Mistral, etc.)
- Create default config files
- Offer to launch OCTO immediately

### Manual Install (macOS / Linux)

```bash
# 1. Clone & Enter Repository
git clone https://github.com/Boyapati13/octo.git
cd octo/octo

# 2. Install Dependencies
pip install -r requirements.txt
playwright install

# 3. Start the Monolith (Voice loop + Model Proxy + DeerFlow Gateway + Hermes engine)
python server.py
```

### Monolith Configuration & Command Line Options

You can control which parts of the monolith start using command-line arguments:

```bash
# Headless Mode: Run model proxy + DeerFlow gateway only (no PyQt/Voice loop)
python server.py --no-voice

# Skip Model Proxy (if running your own proxy elsewhere)
python server.py --no-proxy

# Skip DeerFlow Gateway
python server.py --no-gateway

# Specify Custom Ports
python server.py --proxy-port 8082 --gateway-port 2026
```

### 📡 Configuring Multi-Channel Gateway

All channel settings are centrally managed in [config.yaml](file:///c:/Users/Tenders/octo/octo/config.yaml) in the project root:

1. Open `config.yaml`
2. Locate the `channels` section:
   ```yaml
   channels:
     telegram:
       enabled: true
       bot_token: "YOUR_TELEGRAM_BOT_TOKEN"
     discord:
       enabled: false
       bot_token: ""
   ```
3. Alternatively, use the **OCTO Desktop → Gateway** page to configure channels with a GUI form.

### 🤖 Ollama — Local AI Backup Models (No API Key Needed)

OCTO supports any model available through [Ollama](https://ollama.ai) as a **Haiku-tier backup** through the built-in proxy. This means if all cloud API keys are offline, OCTO falls back to your local model automatically.

```bash
# Install Ollama (Windows/macOS/Linux)
# → https://ollama.ai/download

# Pull your preferred backup model (pick one):
ollama pull gemma3:4b         # Google Gemma 3 4B  — fast, low VRAM
ollama pull gemma3:12b        # Google Gemma 3 12B — higher quality
ollama pull llama3.2:latest   # Meta Llama 3.2
ollama pull mistral:latest    # Mistral 7B
ollama pull deepseek-r1:8b    # DeepSeek R1 8B (reasoning)
```

Then in the OCTO Desktop **Proxy** page → **OLLAMA — LOCAL MODEL BACKUP**:
1. Set the URL to `http://localhost:11434`
2. Click **Detect Models** — your installed models appear in the dropdown
3. Select your preferred backup model and click **Save**

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
│   ├── slack_channel.py         # Slack Bot + Socket Mode
│   ├── whatsapp_channel.py      # WhatsApp via Twilio
│   ├── dingtalk.py              # DingTalk group robot webhook
│   └── feishu.py                # Feishu / Lark open platform
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
