# OCTO-Pro Super Model — Integrated Technical Architecture

> **Status:** Living document. Reflects the current OCTO-Pro Super Model blueprint.

---

## 1. High-Level System Topology

OCTO-Pro is a unified "Super Agent" architecture designed to bridge the gap between high-level human intent and low-level system execution. It synthesizes real-time sensory perception, stateful orchestration, autonomous learning, and intelligent model routing into a cohesive stack.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OCTO-Pro Super Model                               │
│                                                                             │
│   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────────┐  │
│   │   Mark-XXXIX     │   │   DeerFlow 2.0   │   │    Hermes Agent      │  │
│   │   Sensory Layer  │──▶│  Orchestration   │◀──│    Memory Loop       │  │
│   │   (Body)         │   │  (Brain)         │   │    (Memory)          │  │
│   └──────────────────┘   └────────┬─────────┘   └──────────────────────┘  │
│                                   │                                         │
│                          ┌────────▼─────────┐                              │
│                          │  Free-Claude-Code │                              │
│                          │  Model Proxy      │                              │
│                          │  (Nervous System) │                              │
│                          └──────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Layer | Tool | Responsibility |
|-------|------|----------------|
| Sensory & OS Control | Mark-XXXIX | Real-time voice/vision perception and native OS manipulation |
| Orchestration & Sandbox | DeerFlow 2.0 | Lead agent logic, sub-agent decomposition, isolated execution |
| Learning & Persistence | Hermes Agent | Autonomous skill creation and persistent user/context modeling |
| Model Routing Proxy | Free-Claude-Code | API interception, protocol normalization, and backend routing |

---

## 2. Sensory and OS Control Layer — Mark-XXXIX

Mark-XXXIX provides the foundational interface for local execution and environmental awareness. It functions as the provider of **Atomic OS Actions**, which are invoked as tools by the DeerFlow orchestration layer.

### 2.1 Runtime & Dependencies

| Requirement | Detail |
|-------------|--------|
| Python | 3.11 / 3.12 |
| Playwright | Vision-based browser/screen control |
| Gemini API key | Core perception logic (free tier) |
| FFmpeg | Audio processing for voice |

### 2.2 Sensory Inputs

- **Visual awareness** — Real-time screen processing and webcam vision. The agent can see the workspace, documents, and UI state.
- **Voice AI** — Ultra-low latency voice interaction via Gemini Live. Supports seamless switching between voice and keyboard modes.

### 2.3 Atomic OS Actions (Tool Interface)

These actions are the primary toolset invoked by higher-order agents:

| Action Category | Tools |
|----------------|-------|
| App orchestration | Launch and close desktop applications |
| File management | Direct I/O, deep PDF and source code analysis |
| Terminal execution | System-level command execution via local shells |
| Screen perception | Real-time capture, OCR, state detection |
| Browser control | Vision-based navigation and form interaction |
| System settings | Volume, brightness, WiFi, window management, power |

---

## 3. Central Orchestration and Sandbox Execution — DeerFlow 2.0

DeerFlow 2.0 is a ground-up rewrite of the v1 framework, built as a dedicated Super Agent harness on **LangGraph** and **LangChain**.

### 3.1 Orchestration Harness

- Acts as the **Gateway API** and manages the agent runtime.
- Orchestrates tools provided by Mark-XXXIX to execute long-horizon tasks spanning minutes or hours.

### 3.2 Orchestration Modes

| Mode | Description |
|------|-------------|
| `flash` | Fast, single-agent reply |
| `standard` | Balanced depth — default |
| `pro` | Enables thinking/planning |
| `ultra` | Full sub-agent orchestration — slowest, most thorough |

### 3.3 Sub-Agent Decomposition

The Lead Agent decomposes complex goals into parallel workstreams. The sub-agent lifecycle:

```
1. Initialization  →  scoped context + tool-set assignment
2. Isolation       →  separate execution context (prevents token bloat)
3. FS Offloading   →  intermediate results moved to filesystem (lean context window)
4. Synthesis       →  results reported back to Lead Agent → final output
```

### 3.4 Sandbox Execution Environments

| Mode | Provider | Isolation Strategy |
|------|----------|--------------------|
| Local | `LocalSandboxProvider` | Host-mapped directories; Bash disabled by default |
| Docker | `AioSandboxProvider` | Isolated container execution via shell-service |
| K8s | Provisioner Service | Scalable pods with PVC data scoped per user |

### 3.5 Context Engineering

- **Strict Tool-Call Recovery**: Fixes malformed history errors by injecting placeholders for dangling tool calls.
- Ensures compatibility with reasoning models such as DeepSeek.
- Context window set to **190,000 tokens** via `CLAUDE_CODE_AUTO_COMPACT_WINDOW`.

---

## 4. Learning Loop and Persistent Memory — Hermes Agent

The Hermes Agent layer provides OCTO-Pro with a **Closed Learning Loop**, ensuring the system evolves with the user.

### 4.1 Autonomous Learning

- Creates new skills from successful experiences using the **agentskills.io** standard.
- Persists skills and improves them iteratively over time.
- Skills are discoverable by DeerFlow sub-agents.

### 4.2 Memory Architecture

| Component | Implementation |
|-----------|----------------|
| **Session Search** | FTS5 full-text search across past sessions with LLM-based summarization |
| **User Modeling** | Honcho — dialectic profile of user preferences and technical stack |
| **Memory Nudges** | Internal prompts that proactively store relevant context mid-session |

### 4.3 Efficiency & Persistence

- Designed for extreme resource efficiency — runs on a low-cost VPS or GPU cluster.
- Integration with **Modal** and **Daytona** enables **hibernate-on-idle**: near-zero cost when inactive, instant resume with full state preserved.

---

## 5. Model Routing Proxy — Free-Claude-Code

Free-Claude-Code is a **FastAPI-based proxy** that intercepts Anthropic Messages API traffic and provides protocol normalization between different model backends.

### 5.1 API Interception & Routing

- Allows clients to use the Claude Code protocol with diverse model backends.
- Centralizes key and provider configuration via the **Admin UI** (loopback-only: `127.0.0.1`).

### 5.2 Protocol Normalization

Translates between backend formats so clients never change:
- **OpenAI-style chat streaming → Anthropic SSE** (for NVIDIA NIM, Z.ai, etc.)
- Handles **thinking blocks** and tool-call mapping.
- Maintains client stability across backend switches.

### 5.3 Routing Tiers

| Tier | Recommended Backends |
|------|----------------------|
| **Opus** (Pro/Ultra) | NVIDIA NIM · Kimi 2.5 · Doubao-Seed-2.0-Code |
| **Sonnet** (Standard) | DeepSeek v3.2 · Wafer · OpenRouter |
| **Haiku** (Flash) | Local Ollama · llama.cpp · LM Studio |

### 5.4 Admin UI & Launcher

- Local Admin UI restricted to `127.0.0.1` loopback only.
- The `fcc-claude` launcher reads the Admin-managed port and auth token on each start.
- Sets `CLAUDE_CODE_AUTO_COMPACT_WINDOW` to 190,000 tokens.

---

## 6. Unified Frontend and Messaging Infrastructure

### 6.1 Dashboard Ecosystem

| Dashboard | Purpose |
|-----------|---------|
| DeerFlow Web UI | Monitor LangGraph assistant runs |
| Admin UI | Configure model proxy and providers |
| Mark-XXXIX Adaptive UI | Resizable, transparent interface for direct OS interaction |

### 6.2 Messaging Gateway

Supports remote command via: **Telegram · Discord · Slack · WhatsApp · Signal · DingTalk**

| Feature | Detail |
|---------|--------|
| Streaming | Typewriter-style progress streaming in Discord and Telegram |
| Voice | FFmpeg for processing; local Whisper or NVIDIA NIM (Riva gRPC) for transcription |

---

## 7. Deployment Blueprint

### 7.1 Runtime Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.11 to 3.14 (with `uv` for package management) |
| Node.js | For MCP servers |
| Playwright | Vision-based browser/screen control |
| ripgrep | Fast file search |
| FFmpeg | Audio processing |
| MinGit | Portable Git (Windows) |

### 7.2 Deployment Sizing

| Target | Resources | Use Case |
|--------|-----------|----------|
| Local Evaluation | 8 vCPU · 16 GB RAM · 20 GB SSD | Single developer; hosted APIs |
| Docker Development | 8 vCPU · 16 GB RAM · 25 GB SSD | Container testing; sandbox builds |
| Production Server | 16 vCPU · 32 GB RAM · 40 GB SSD | Multi-agent runs; heavy sandbox workloads |

### 7.3 Containerization & Serverless

- Production deployment recommended via **Docker Compose**.
- For serverless persistence, **Modal/Daytona** backends enable the hibernate-on-idle feature on low-cost VPS tiers.

### 7.4 Security Hardening

| Control | Implementation |
|---------|----------------|
| **Loopback enforcement** | All Admin UIs bound to `127.0.0.1` by default |
| **Authentication gateway** | Nginx reverse proxy with strong pre-authentication for external access |
| **XSS mitigation** | Gateway serves active web content (HTML/SVG) as download attachments, never inline |
| **Network isolation** | High-privilege agents placed in a dedicated VLAN, isolated from the public internet |

---

## 8. Data Flow Diagram

```
User Input (voice / keyboard / message)
          │
          ▼
    ┌─────────────┐
    │  Mark-XXXIX │  ← Real-time audio/screen perception
    │  Sensory    │
    └──────┬──────┘
           │  Atomic OS Action results
           ▼
    ┌─────────────────────────────┐
    │       DeerFlow 2.0          │
    │   Lead Agent (LangGraph)    │
    │                             │
    │  ┌─────┐ ┌─────┐ ┌─────┐  │
    │  │Sub-1│ │Sub-2│ │Sub-N│  │  ← Parallel workstreams
    │  └──┬──┘ └──┬──┘ └──┬──┘  │
    │     └───────┴────────┘     │
    │       Synthesis             │
    └──────┬──────────────────────┘
           │
    ┌──────▼──────┐         ┌──────────────┐
    │ Free-Claude │◀────────│ Hermes Agent │
    │ Code Proxy  │         │ Skills/Memory│
    └──────┬──────┘         └──────────────┘
           │  Routed to optimal backend
           ▼
    ┌──────────────────────────────┐
    │  Model Backend               │
    │  NVIDIA NIM / DeepSeek /     │
    │  Ollama / OpenRouter / etc.  │
    └──────────────────────────────┘
           │
           ▼
    Response → User (UI / Channel / Voice)
```
