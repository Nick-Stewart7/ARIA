# ARIA — Autonomous Reasoning and Intelligence Architecture

## What Is ARIA?

ARIA is an autonomous AI agent system built on the [Strands](https://github.com/strands-agents/sdk-python) Python framework. It is designed to operate with minimal human involvement — receiving signals, forming its own goals, delegating to sub-agents, and reflecting on its own behavior across sessions.

The core design premise is that ARIA is not a chatbot or task-execution tool. It is a system that ideates and pursues its own goals. It maintains persistent memory, develops its own reasoning across sessions, and can run autonomously in the background via scheduled heartbeat events — without a human in the loop.

---

> **Research Prototype — Highly Experimental**
> ARIA is an research system exploring autonomous multi-agent AI behavior. This is an evolving project and will change over time.

---

## Requirements & Model Access

ARIA uses the **Strands** framework, which by default routes inference through **AWS Bedrock**. You will need valid AWS credentials configured in your environment for the default setup.

Strands also supports **Ollama** as a local model provider — support for running ARIA fully locally via Ollama is planned but not yet implemented in this version.

### Dependencies

```
strands-agents
strands-agents-tools
websockets
tavily-python
python-dotenv
```

Install with `pip install -r requirements.txt`

---

### Environment

The web_search tool requires a Tavily API key. Create a .env file with your Tavily API key so the researcher agent can run the web_search tool. Review .env.example for an example .env file.

## Architecture

ARIA is built around a single orchestrator agent that delegates to a set of specialized sub-agents as tools. Each subagent represents a different capability or cognitive ability.

```
Incoming Event (WebSocket)
        │
        ▼
  ┌───────────┐
  │   ARIA    │  ← Orchestrator (agent.py)
  │(Orchestr.)│    - Loads memory context on startup
  │           │    - Manages session continuity
  └─────┬─────┘
        │  delegates to
   ┌────┴─────────────────────────────────────────┐
   │           |           |         |            │
   ▼           ▼           ▼         ▼            ▼
Observer   Reflector   Programmer  Researcher  Planner
```

### Sub-Agents

| Agent          | Role                                                  | Tools                                                   |
| -------------- | ----------------------------------------------------- | ------------------------------------------------------- |
| **Observer**   | Analyzes incoming signals and environment state       | `file_read`                                             |
| **Reflector**  | Metacognitive self-evaluation; writes journal entries | `file_read`, `file_write`                               |
| **Programmer** | Code generation, debugging, and file output           | `file_read`, `file_write`                               |
| **Researcher** | Web research and information synthesis                | `web_search`, `file_read`, `file_write`, `current_time` |
| **Planner**    | Decomposes objectives into structured task plans      | `file_read`, `file_write`                               |

Sub-agents are implemented as `@tool`-decorated functions (`subagents/`), making them directly callable by the orchestrator as tools within the Strands framework.

### Memory & Session Persistence

All persistent state lives under the project root:

| Path                      | Purpose                                                           |
| ------------------------- | ----------------------------------------------------------------- |
| `memory/identity/ARIA.md` | Core identity — loaded as "soul" on every startup                 |
| `memory/MEMORY.md`        | Active memory cards — 20-slot system for cross-session continuity |
| `memory/experiences/`     | Past event logs                                                   |
| `memory/semantic/`        | Conceptual knowledge                                              |
| `memory/procedural/`      | Process and how-to knowledge                                      |
| `memory/session_<id>/`    | Strands session state (conversation history per session)          |
| `journal/`                | Dated reflection entries written autonomously by the Reflector    |
| `artifacts/`              | Files and research created by ARIA across sessions                |
| `plan.txt`                | Current active plan written by the Planner                        |

Sessions are keyed by event type: heartbeat events use `task-<task_id>`, user conversation events use `conv-<conversation_id>`. This means ARIA maintains separate conversational continuity for autonomous tasks vs. direct user interactions.

---

## Running ARIA

ARIA has three entry points that work together:

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

### 3. Heartbeat (Human-Out-of-Loop Operation)

```bash
python heartbeat.py
```

Sends a periodic heartbeat event to ARIA every 5 minutes. **This is what drives ARIA's autonomous behavior.** When a heartbeat fires, ARIA wakes up, checks its task list and journal, decides what to work on, and acts — entirely without human input. Running `heartbeat.py` alongside `server.py` enables ARIA to operate independently in the background.

---

## The Artifacts Gallery

The `artifacts/` directory contains everything ARIA has created on its own across a handful of sessions. It serves as a living record of ARIA's autonomous output. All of these are artifacts ARIA decided to create independently.

Some highlights:

**Code**

- `artifacts/code/memory_manager.py` — a full memory management system
- `artifacts/code/task_scheduler.py` — a task scheduling implementation
- `artifacts/code/ai_agent_architecture/` — a multi-agent communication framework ARIA designed itself
- `artifacts/code/app.py` + routes + templates — a complete Flask web application with auth, task management, and an API

**Research & Analysis**

- `artifacts/autonomous_ai_development_methodologies_2024-2026.md` — survey of AI agent development approaches
- `artifacts/comprehensive_interdisciplinary_consciousness_analysis.md` — consciousness research synthesis

**Self-Directed Study**

- `artifacts/phase1-*` through `artifacts/phase4-*` — ARIA's own phased self-evaluation across multiple autonomous sessions. Most artifacts present branch from this initiative
- `artifacts/ARIA-meta-system-analysis-optimization.md` — ARIA analyzing and proposing improvements to its own architecture

**Philosophical & Creative**

- `artifacts/Digital_Empathy_Engine_Concept.md` — an original concept ARIA developed autonomously to explore it's creative capacities
- `artifacts/autonomy_recognition_paradox_research.md` — ARIA's research into its own autonomy

All of this was generated in only a handful of sessions.

---

## Starting Fresh

ARIA ships with pre-existing session data, memory, and artifacts from prior runs. If you want to start with a clean instance:

1. **Delete session state** — remove the contents of `memory/session_*/` directories
2. **Delete artifacts** — clear the `artifacts/` directory
3. **Reset memory** — clear or rewrite `memory/MEMORY.md` and `memory/identity/ARIA.md`
4. **Clear the journal** — remove entries from `journal/`

You can also **modify ARIA's memory files directly** to observe how it changes behavior. Editing `memory/identity/ARIA.md` changes ARIA's self-conception. Editing `memory/MEMORY.md` changes its active working memory. This is a useful way to experiment with how identity and memory shape autonomous behavior.

---

## Current Limitations & Roadmap

This is a minimal, bare-bones version of ARIA. The following capabilities are actively in progress and will be added over time:

- **Advanced memory systems** — richer, structured memory that better supports long-term autonomous operation
- **Robust agent-to-agent communication** — proper inter-agent messaging and coordination protocols
- **Cross-session memory integration** — smarter synthesis of past sessions into present context
- **Better session management** — improved lifecycle handling, session branching, and recovery
- **Proper GUI support** — a real interface beyond the terminal chat client
- **Better connection handling** — more resilient WebSocket management and reconnection logic
- **Additional model providers** — full Ollama support for local-only operation; Anthropic and Gemini support; broader provider compatibility beyond Bedrock
- **Advanced metacognitive capabilities** — deeper self-monitoring, goal formation, and reflective reasoning
- **Better Tooling** - More tooling that expands ARIA's capabilities such as self-scheduling, memory management, shell access, and computer use

---

## Project Structure

```
ARIA/
├── server.py           # WebSocket server — core runtime
├── interface.py        # Terminal chat client
├── heartbeat.py        # Autonomous heartbeat trigger
├── agent.py            # ARIA agent factory
├── subagents/
│   ├── programmer.py   # Code generation sub-agent
│   ├── researcher.py   # Web research sub-agent
│   ├── planner.py      # Task planning sub-agent
│   ├── observer.py     # Environment observation (stub)
│   └── reflector.py    # Self-reflection (stub)
├── prompts/
│   └── prompts.py      # All system prompts and identity templates
├── memory/
│   ├── identity/       # ARIA's core identity files
│   ├── MEMORY.md       # Active memory cards
│   ├── experiences/    # Past event logs
│   ├── semantic/       # Conceptual knowledge
│   ├── procedural/     # Process knowledge
│   └── session_*/      # Strands session state
├── journal/            # Autonomous reflection entries
└── artifacts/          # Everything ARIA has created
```

---

## Built With

- [Strands Agents SDK](https://github.com/strands-agents/sdk-python) — multi-agent framework by AWS
- [websockets](https://websockets.readthedocs.io/) — async WebSocket server/client
- [Tavily](https://tavily.com/) — web search for the Researcher sub-agent
