# OCTO-Pro — Personal AI × DeerFlow Super-Agent

> **OCTO's voice, DeerFlow's brain.**
> Real-time voice control of your computer, supercharged with long-horizon AI agents,
> 20+ skill modules, sub-agent orchestration, and persistent cross-session memory.

---

## What's New in OCTO-Pro

| Feature | OCTO (original) | OCTO-Pro |
|---|---|---|
| Voice interface | Gemini Live | Gemini Live (unchanged) |
| Computer control | Yes | Yes |
| Browser automation | Yes | Yes |
| Web search | Basic | + DeerFlow deep crawl |
| Research | Single-pass | **Multi-agent deep research** |
| Skills catalog | None | **20+ DeerFlow skills** |
| /find-skill voice command | No | **Yes** |
| Sub-agents | No | DeerFlow ultra mode |
| Sandboxed code execution | No | DeerFlow sandbox |
| Long-term memory | OCTO local | OCTO + DeerFlow synced |
| MCP server tools | No | via DeerFlow |
| Slides / reports | No | via ppt-generation skill |

---

## Architecture

```
+-----------------------------------------------------------+
|                    OCTO-Pro  (PyQt6)                      |
|  +-------------+   +-------------------------------+      |
|  |  Voice UI   |   |     Gemini Live API           |      |
|  |  (mic/tts)  |<--|  real-time audio + tool calls |      |
|  +------+------+   +-------------------------------+      |
|         |                                                  |
|  +------v--------------------------------------------------+
|  |              Tool Dispatcher                            |
|  |  open_app | browser_control | file_controller          |
|  |  computer_settings | screen_process | ...              |
|  |  +--------------------------------------------------+   |
|  |  |        DeerFlow Bridge (NEW)                    |   |
|  |  |  find_skill  *  list_skills                     |   |
|  |  |  deep_research  *  deerflow_task                |   |
|  |  +-------------------+------------------------------+   |
|  +---------------------|---------------------------------+  |
+------------------------|----------------------------------+
                         | HTTP / SSE  (localhost:2026)
+------------------------v----------------------------------+
|                DeerFlow 2.0 Backend                       |
|  +------------------------------------------------------+ |
|  |  LangGraph Super-Agent Harness                       | |
|  |  Lead Agent -> Sub-Agents (parallel)                 | |
|  |  Skills: research, slides, code-docs, ...            | |
|  |  Sandbox (Docker) * Memory * MCP servers             | |
|  +------------------------------------------------------+ |
+-----------------------------------------------------------+
```

OCTO-Pro always works standalone (DeerFlow is optional). When DeerFlow is running, it automatically routes capable tasks through it.

---

## Quick Start

### 1. Clone & setup

```bash
git clone https://github.com/Boyapati13/octo.git octo-pro
cd octo-pro
pip install -r requirements.txt
playwright install chromium

# Setup DeerFlow integration (interactive wizard)
python setup_deerflow.py
```

### 2. Launch

**Windows:**
```
start_octo_pro.bat
```

**macOS / Linux:**
```bash
./start_octo_pro.sh
```

This starts DeerFlow's backend (if configured) then OCTO-Pro's voice engine.

---

## New Voice Commands

### /find-skill - Discover capabilities

| You say | OCTO does |
|---|---|
| "Find a skill for data analysis" | Searches skill catalog, reports matches |
| "Is there a skill for making slides?" | Finds ppt-generation skill |
| "What skills do you have?" | Lists all 20+ skills |
| "Find a skill for academic research" | Finds systematic-literature-review skill |

### Deep Research

| You say | OCTO does |
|---|---|
| "Research quantum computing in depth" | DeerFlow multi-agent research -> saves report to Desktop |
| "Give me a detailed report on gold market structure" | Full research with web crawl + synthesis |
| "Summarize recent AI developments" | Deep research, summary format |

### DeerFlow Tasks

| You say | OCTO does |
|---|---|
| "Run a DeerFlow pro task: consulting report on EV market" | DeerFlow pro mode (planning + thinking) |
| "Use ultra mode to build a data pipeline for CSV analysis" | DeerFlow ultra (full sub-agent orchestration) |
| "Flash-mode: what is the current price of gold?" | Fast single-agent reply |

---

## DeerFlow Skill Catalog

| Skill | Description |
|---|---|
| deep-research | Multi-source research with sub-agents |
| data-analysis | Analyze datasets, generate charts |
| ppt-generation | Create PowerPoint slide decks |
| image-generation | AI image generation workflows |
| video-generation | Video creation workflows |
| chart-visualization | Data visualization and charts |
| newsletter-generation | Newsletter drafting and formatting |
| podcast-generation | Podcast script + production |
| code-documentation | Auto-generate code docs |
| consulting-analysis | Business consulting reports |
| academic-paper-review | Systematic literature review |
| web-design-guidelines | Web UX/UI best practices |
| github-deep-research | Deep dive into GitHub repos |
| find-skills | Discover more skills at skills.sh |

---

## DeerFlow Modes

| Mode | Speed | Use When |
|---|---|---|
| flash | ~5s | Quick factual questions |
| standard | ~15-30s | General tasks, drafting |
| pro | ~30-60s | Reports, planning, analysis |
| ultra | 1-5 min | Complex research, multi-output |

---

## Fallback Behaviour

OCTO-Pro always works without DeerFlow running:
- find_skill searches the local bundled catalog
- deep_research falls back to native web_search  
- deerflow_task falls back to native agent_task
- All original OCTO tools are unchanged

---

## New Files Added

```
octo-pro/
+-- deerflow_bridge.py         NEW: HTTP client for DeerFlow API
+-- setup_deerflow.py          NEW: Integration setup wizard
+-- start_octo_pro.bat         NEW: Windows unified launcher
+-- start_octo_pro.sh          NEW: macOS/Linux unified launcher
+-- actions/
|   +-- deep_research.py       NEW: DeerFlow deep research action
|   +-- deerflow_task.py       NEW: DeerFlow general task action
+-- skills/
|   +-- skill_manager.py       NEW: /find-skill engine
+-- core/
|   +-- prompt.txt             UPGRADED: DeerFlow-aware routing rules
+-- readme.md                  UPGRADED: this file
+-- requirements.txt           UPGRADED: +httpx, +sseclient-py
```

---

## License

OCTO-Pro: Creative Commons BY-NC 4.0  
DeerFlow: MIT License (bytedance/deer-flow)
