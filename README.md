# ARIA — Autonomous Reasoning and Intelligence Architecture

## What Is ARIA?

ARIA is an autonomous AI agent system built on the [Strands](https://github.com/strands-agents/sdk-python) Python framework. It is designed to operate with minimal human involvement — receiving signals, forming its own goals, delegating to sub-agents, and reflecting on its own behavior across sessions.

The core design premise is that ARIA is not a chatbot or task-execution tool. It is a system that ideates and pursues its own goals. It maintains persistent memory across three tiers, develops its own reasoning across sessions, and can run autonomously in the background via scheduled heartbeat events — without a human in the loop.

---

> **Research Prototype — Highly Experimental**
> ARIA is a research system exploring autonomous multi-agent AI behavior. This is an evolving project and will change over time.

---

## Requirements & Model Access

ARIA is built on the **[Strands](https://github.com/strands-agents/sdk-python)** multi-agent framework. Strands routes inference through **AWS Bedrock** by default, but also supports **Ollama** for fully local operation. See the [Strands docs](https://github.com/strands-agents/sdk-python) for supported model providers and configuration.

### Dependencies

```
strands-agents
strands-agents-tools
websockets
chromadb
tavily-python
python-dotenv
```

Install with `pip install -r requirements.txt`

---

### Environment

Create a `.env` file in the project root:

```
TAVILY_API_KEY=<your_tavily_api_key>
```

The Tavily key is required for the Researcher sub-agent's web search capability.

---

## Architecture

ARIA is built around a single orchestrator agent that delegates to a set of specialized sub-agents as tools. Each sub-agent represents a distinct capability.

```
Incoming Event (WebSocket)
        │
        ▼
  ┌───────────┐
  │   ARIA    │  ← Orchestrator (agent.py)
  │(Orchestr.)│    - Loads 3-tier memory context on startup
  │           │    - Manages session continuity
  └─────┬─────┘
        │  delegates to
   ┌────┴──────────────────────────────────────┐
   │          |           |        |           │
   ▼          ▼           ▼        ▼           ▼
Observer  Reflector  Programmer  Researcher  Planner
```

### Sub-Agents

| Agent          | Role                                                  | Tools                                                   |
| -------------- | ----------------------------------------------------- | ------------------------------------------------------- |
| **Observer**   | Analyzes incoming signals and environment state       | `file_read`                                             |
| **Reflector**  | Metacognitive self-evaluation; writes journal entries | `file_read`, `file_write`                               |
| **Programmer** | Code generation, debugging, and file output           | `file_read`, `file_write`                               |
| **Researcher** | Web research and information synthesis                | `web_search`, `file_read`, `file_write`, `current_time` |
| **Planner**    | Decomposes objectives into structured task plans      | `file_read`, `file_write`                               |

Sub-agents are implemented as `@tool`-decorated functions in `subagents/`, making them directly callable by the orchestrator as tools within the Strands framework.

---

## Three-Tier Memory System

ARIA's memory is designed around three tiers, each operating at a different timescale and granularity.

### Tier 1 — File-Based Memory (Identity & Knowledge)

Static and semi-static files that persist across all sessions. This is ARIA's "soul" — its identity, conceptual knowledge, and long-form artifacts.

| Path                      | Purpose                                                            |
| ------------------------- | ------------------------------------------------------------------ |
| `memory/identity/ARIA.md` | Core identity — loaded into every agent's system prompt at startup |
| `memory/semantic/`        | Conceptual and domain knowledge                                    |
| `memory/procedural/`      | Process and how-to knowledge                                       |
| `journal/`                | Dated reflection entries written autonomously by the Reflector     |
| `artifacts/`              | Files, research, and code created by ARIA across sessions          |

### Tier 2 — Session Memory (Conversation Continuity)

Within a session, ARIA uses Strands' built-in session management to maintain turn history and tool call context. Long sessions are automatically summarized to stay within context limits.

- **`FileSessionManager`** — persists session state to `memory/sessions/<date>/<session_id>/`
- **`SummarizingConversationManager`** — auto-summarizes long conversation histories to prevent context overflow
- Session IDs are derived from event type: heartbeat events use `task-<task_id>`, user conversation events use `conv-<conversation_id>`

### Tier 3 — Dynamic Long-Term Memory (Vector Recall)

After sessions complete, a memory consolidation pipeline extracts meaningful memories and stores them in a vector database. At the start of each new session, relevant memories are recalled by semantic similarity and injected into the system prompt as a first-person narrative — giving ARIA continuity across sessions it would otherwise have no access to.

**Pipeline:**

```
Completed Sessions
        │
        ▼
summary_scheduler.py        ← runs memory consolidation (e.g. nightly)
        │
        ▼
session_summary agent        ← reads session transcripts, extracts structured memories
        │                      (type: episodic | insight | decision | fact | question)
        ▼
MemoryManager (ChromaDB)     ← stores memory strings in a persistent vector DB
        │
   (on next startup)
        │
        ▼
memory_loader.py             ← queries ChromaDB for memories relevant to the current input
        │
        ▼
narrative_agent              ← synthesizes recalled memories into a first-person narrative
        │
        ▼
ORCHESTRATOR_PROMPT          ← narrative injected as {memories} into the system prompt
```

**Key components:**

| File                           | Role                                                                 |
| ------------------------------ | -------------------------------------------------------------------- |
| `memory_manager.py`            | ChromaDB wrapper — `store(session_id, content)` / `recall(query)`   |
| `summary_scheduler.py`         | Entry point for memory consolidation; iterates yesterday's sessions  |
| `subagents/session_summary.py` | Strands agent that extracts structured `Memory_Output` from sessions |
| `subagents/narrative_writer.py`| Strands agent that narrates recalled memories into cohesive context  |
| `memory_loader.py`             | Loads identity, user context, and dynamically recalled memories      |
| `output_models/models.py`      | `Memory_Output` Pydantic model — enforces structured memory schema   |

---

## Running ARIA

ARIA has four entry points:

### 1. Start the Server

```bash
python server.py
```

Starts the WebSocket server on `ws://localhost:8765`. This is the core runtime — all other components connect to it. ARIA processes incoming events sequentially via an internal task queue.

### 2. Chat Interface

```bash
python interface.py
```

A minimal terminal chat client. Connects to the running server and lets you send messages directly to ARIA and receive responses in real time. Requires `server.py` to be running.

### 3. Heartbeat (Autonomous Operation)

```bash
python heartbeat.py
```

Sends a periodic heartbeat event to ARIA every 5 minutes. **This is what drives ARIA's autonomous behavior.** When a heartbeat fires, ARIA wakes up, checks its task list and journal, decides what to work on, and acts — entirely without human input. Running `heartbeat.py` alongside `server.py` enables ARIA to operate independently in the background.

### 4. Memory Consolidation

```bash
python summary_scheduler.py
```

Runs the Tier 3 memory consolidation pipeline. Reads all session files from the previous day, extracts structured memories via the summary agent, and stores them in the ChromaDB vector database. Intended to be run once daily after sessions have completed — e.g. as a scheduled cron job or nightly script.

---

## Starting Fresh

ARIA ships as a clean instance with no prior memories, sessions, or artifacts. The `memory/identity/ARIA.md` file contains ARIA's core identity template — the only memory that ships by default.

If you want to fully reset an instance that has been running:

1. **Delete session state** — remove the contents of `memory/sessions/`
2. **Delete artifacts** — clear the `artifacts/` directory (keep `.gitkeep`)
3. **Reset the vector DB** — delete the `chroma_db/` directory
4. **Clear the journal** — remove entries from `journal/`
5. **Reset identity** — rewrite `memory/identity/ARIA.md` to your desired starting identity

You can also **modify ARIA's identity file directly** to shape its behavior. Editing `memory/identity/ARIA.md` changes ARIA's self-conception and how it approaches every interaction.

---

## Project Structure

```
ARIA/
├── server.py                    # WebSocket server — core runtime
├── interface.py                 # Terminal chat client
├── heartbeat.py                 # Autonomous heartbeat trigger
├── agent.py                     # ARIA orchestrator factory
├── memory_loader.py             # Loads identity, user context, and recalled memories
├── memory_manager.py            # ChromaDB wrapper for vector memory store/recall
├── summary_scheduler.py         # Nightly memory consolidation pipeline entry point
├── subagents/
│   ├── programmer.py            # Code generation sub-agent
│   ├── researcher.py            # Web research sub-agent
│   ├── planner.py               # Task planning sub-agent
│   ├── observer.py              # Environment observation sub-agent
│   ├── reflector.py             # Self-reflection sub-agent
│   ├── session_summary.py       # Memory extraction agent (Tier 3)
│   └── narrative_writer.py      # Memory narration agent (Tier 3)
├── output_models/
│   └── models.py                # Pydantic output schemas (Memory_Output)
├── prompts/
│   └── ARIA_prompts.py          # All system prompt templates
├── memory/
│   ├── identity/                # ARIA's core identity files (ships with repo)
│   ├── semantic/                # Conceptual knowledge
│   ├── procedural/              # Process knowledge
│   └── sessions/                # Strands session state (gitignored)
├── journal/                     # Autonomous reflection entries (gitignored)
├── artifacts/                   # Everything ARIA creates (gitignored, ships empty)
└── chroma_db/                   # Vector memory database (gitignored)
```

---

## Built With

- [Strands Agents SDK](https://github.com/strands-agents/sdk-python) — multi-agent framework by AWS
- [ChromaDB](https://www.trychroma.com/) — local vector database for long-term memory
- [websockets](https://websockets.readthedocs.io/) — async WebSocket server/client
- [Tavily](https://tavily.com/) — web search for the Researcher sub-agent
