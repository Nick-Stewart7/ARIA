# ARIA — Autonomous Reasoning and Intelligence Architecture

## What Is ARIA?

ARIA is an autonomous AI agent system built on the [Strands](https://github.com/strands-agents/sdk-python) Python framework. It is designed to operate with minimal human involvement — receiving signals, forming its own goals, delegating to sub-agents, and reflecting on its own behavior across sessions.

The core design premise is that ARIA is not a chatbot or task-execution tool. It is a system that ideates and pursues its own goals. It maintains persistent memory across three tiers, develops its own reasoning across sessions, and can run autonomously in the background via scheduled heartbeat events — without a human in the loop.

---

> **Research Prototype — Highly Experimental**
> ARIA is a research system exploring autonomous multi-agent AI behavior. This is an evolving project and will change over time.

---

## Requirements & Model Access

ARIA is built on the **[Strands](https://github.com/strands-agents/sdk-python)** multi-agent framework. Strands supports **AWS Bedrock**, **Anthropic API**, and **Ollama** for fully local operation. See the [Strands docs](https://github.com/strands-agents/sdk-python) for supported model providers and configuration.

Install with:

```bash
pip install -e .
```

---

## Running ARIA

Start with the setup wizard on first run:

```bash
aria setup
```

This collects your model provider, API keys, host/port, and username — then writes a `.env` file.

Once setup is complete:

```bash
aria serve                    # Start the REST API server — also runs the heartbeat loop
aria chat                     # Textual TUI chat client (requires server running)
aria chat --continue          # Resume the most recently active session
aria chat --session <id>      # Resume a specific session by id
aria heartbeat [pause|resume|status]   # Control the autonomous heartbeat without stopping the server
aria log [--session <id>] [--tail N] [--follow]   # Read session history as turns (input, tool calls, reply)
aria sessions                 # List existing sessions with a preview of their last turn
aria summarize                # Run memory consolidation (Tier 3)
```

Starting `aria serve` is enough to bring ARIA's autonomous heartbeat cycle alive — no separate command needed. Each time it fires, the Possibility Drive sub-agent generates a self-directed prompt, which is sent to ARIA to act on — entirely without human input. Because that costs real tokens on a timer, `aria heartbeat pause` stops it without killing the server (chat keeps working); `aria heartbeat resume` turns it back on.

**`aria chat`** opens a Textual TUI: a scrolling chat pane with token-by-token streaming over Server-Sent Events, `Escape` to cancel a response mid-generation, and a status bar showing the current session id and cumulative token usage. Sending a new message while one is still streaming cancels the old turn server-side and redirects — it doesn't keep generating in the background.

`aria log` reads session history straight from the Strands session files and prints it as turns — the user input, each tool call with its result size, and the reply — for chat and heartbeat alike. Server logs (startup, errors, heartbeat activity) go to `logs/aria.log`, rotated automatically.

---

## Architecture

ARIA is built around a single orchestrator agent that delegates to a set of specialized sub-agents as tools, fronted by a REST API.

```
aria chat (Textual TUI)              aria heartbeat_loop (background task)
        │  SSE stream                        │  in-process
        ▼                                     ▼
  POST /chat, /chat/cancel      ┌───────────┐
        │                       │   ARIA    │  ← Orchestrator (aria/agent.py)
        └──────────────────────▶│(Orchestr.)│    - Loads 3-tier memory context on startup
                                 │           │    - Manages session continuity
                                 └─────┬─────┘
                                       │  delegates to
   ┌────┴──────────────────────────────────────┐
   │          |           |        |           │
   ▼          ▼           ▼        ▼           ▼
Observer  Reflector  Programmer  Researcher  Planner
```

The FastAPI app (`aria/app.py`) is the single runtime: `aria serve` starts it, and the heartbeat loop runs as a background task inside its own lifespan — chat sessions and the heartbeat session are fully isolated from each other (distinct session ids, and a chat-side cancel can never reach a heartbeat turn or vice versa).

### Sub-Agents

| Agent                 | Role                                                  | Tools                                                   |
| --------------------- | ----------------------------------------------------- | ------------------------------------------------------- |
| **Observer**          | Analyzes incoming signals and environment state       | `file_read`                                             |
| **Reflector**         | Metacognitive self-evaluation; writes journal entries | `file_read`, `journal`                                  |
| **Programmer**        | Code generation, debugging, and file output           | `file_read`, `file_write`                               |
| **Researcher**        | Web research and information synthesis                | `web_search`, `file_read`, `file_write`, `current_time` |
| **Planner**           | Decomposes objectives into structured task plans      | `file_read`, `file_write`                               |
| **Possibility Drive** | Generates self-directed prompts for heartbeat cycles  | `file_read`, `file_write`                               |

Sub-agents are implemented as `@tool`-decorated functions in `aria/subagents/`, making them directly callable by the orchestrator within the Strands framework.

---

## Three-Tier Memory System

ARIA's memory operates at three tiers, each at a different timescale and granularity.

### Tier 1 — File-Based Memory (Identity & Knowledge)

Static and semi-static files that persist across all sessions.

| Path                      | Purpose                                                            |
| ------------------------- | ------------------------------------------------------------------ |
| `memory/identity/ARIA.md` | Core identity — loaded into every agent's system prompt at startup |
| `memory/semantic/`        | Conceptual and domain knowledge                                    |
| `memory/procedural/`      | Process and how-to knowledge                                       |
| `journal/`                | Dated reflection entries written autonomously by the Reflector     |
| `artifacts/`              | Files, research, and code created by ARIA across sessions          |

### Tier 2 — Session Memory (Conversation Continuity)

Within a session, ARIA uses Strands' built-in session management to maintain turn history and tool call context. Long sessions are automatically summarized to stay within context limits.

- **`FileSessionManager`** — persists session state to `memory/sessions/session_<session_id>/`
- **`SummarizingConversationManager`** — auto-summarizes long conversation histories to prevent context overflow
- **`aria/history.py`** — the one reader over those session files: folds raw messages into turns, orders sessions by last activity, and backs `aria log` / `aria sessions`

### Tier 3 — Dynamic Long-Term Memory (Vector Recall)

After sessions complete, a consolidation pipeline extracts meaningful memories into ChromaDB. At the start of each new session, relevant memories are recalled by semantic similarity and injected into the system prompt as a first-person narrative.

```
Completed Sessions
        │
        ▼
aria summarize               ← runs memory consolidation
        │
        ▼
session_summary agent        ← extracts structured memories from session transcripts
        │
        ▼
MemoryManager (ChromaDB)     ← stores memories in a persistent vector DB
        │
   (on next startup)
        │
        ▼
memory_loader.py             ← queries ChromaDB for memories relevant to current input
        │
        ▼
narrative_agent              ← synthesizes recalled memories into a first-person narrative
        │
        ▼
ORCHESTRATOR_PROMPT          ← narrative injected as {memories} into the system prompt
```

---

## Starting Fresh

ARIA ships as a clean instance with no prior memories, sessions, or artifacts. `memory/identity/ARIA.md` is the only memory that ships by default.

To fully reset a running instance:

1. Remove contents of `memory/sessions/`
2. Clear `artifacts/` (keep `.gitkeep`)
3. Delete `chroma_db/`
4. Remove entries from `journal/`
5. Rewrite `memory/identity/ARIA.md` to your desired starting identity

---

## Project Structure

```
ARIA/
├── aria/
│   ├── cli.py                   # Entry point — aria serve | chat | heartbeat | log | sessions | etc.
│   ├── app.py                   # FastAPI app — /chat (SSE), /chat/cancel, /sessions, /heartbeat*
│   ├── agent.py                 # ARIA orchestrator factory + run_turn/stream_turn
│   ├── heartbeat.py             # Autonomous heartbeat loop, with pause/resume
│   ├── tui.py                   # Textual chat TUI — streaming, cancel/redirect, status bar
│   ├── client.py                # Shared HTTP helpers (base URL, session resolution) used by the TUI
│   ├── sessions.py              # Session listing/minting/existence checks
│   ├── history.py               # Reads session files as turns; backs `aria log` / `aria sessions`
│   ├── logging_setup.py         # Rotating file + console logging, configured once at startup
│   ├── memory_loader.py         # Loads identity, user context, and recalled memories
│   ├── memory_manager.py        # ChromaDB wrapper for vector memory store/recall
│   ├── setup_wizard.py          # First-time setup wizard
│   ├── summary.py               # Memory consolidation pipeline entry point
│   ├── subagents/
│   │   ├── programmer.py
│   │   ├── researcher.py
│   │   ├── planner.py
│   │   ├── observer.py
│   │   ├── reflector.py
│   │   ├── possibility_drive.py # Generates self-directed heartbeat prompts
│   │   ├── session_summary.py   # Memory extraction agent (Tier 3)
│   │   └── narrative_writer.py  # Memory narration agent (Tier 3)
│   ├── prompts/
│   │   └── ARIA_prompts.py      # All system prompt templates
│   ├── tools/
│   │   ├── web_search.py        # Tavily web search tool
│   │   └── memory_tools.py      # store/recall tools backing ARIA's own memory access
│   └── output_models/
│       └── models.py            # Pydantic output schemas (Memory_Output)
├── memory/
│   ├── identity/                # ARIA's core identity files (ships with repo)
│   ├── semantic/                # Conceptual knowledge
│   ├── procedural/              # Process knowledge
│   └── sessions/                # Strands session state (gitignored)
├── journal/                     # Autonomous reflection entries (gitignored)
├── artifacts/                   # Everything ARIA creates (gitignored, ships empty)
├── logs/                        # Rotating server logs (gitignored)
├── chroma_db/                   # Vector memory database (gitignored)
└── pyproject.toml
```

---

## Built With

- [Strands Agents SDK](https://github.com/strands-agents/sdk-python) — multi-agent framework by AWS
- [FastAPI](https://fastapi.tiangolo.com/) / [uvicorn](https://www.uvicorn.org/) — REST API server, streaming `/chat` over Server-Sent Events
- [Textual](https://textual.textualize.io/) — the `aria chat` terminal UI
- [httpx](https://www.python-httpx.org/) — async HTTP client used by the TUI
- [ChromaDB](https://www.trychroma.com/) — local vector database for long-term memory
- [Tavily](https://tavily.com/) — web search for the Researcher sub-agent
- [pyfiglet](https://github.com/pwaller/pyfiglet) — ASCII art for the setup wizard
