# ARIA Install Experience — Design Spec
_2026-03-26_

## Goal

Make ARIA easy to clone, configure, and run for researchers and developers evaluating the project. The install flow should take someone from zero to a running ARIA instance in under 5 minutes without requiring prior knowledge of the codebase.

---

## Install Flow

```
git clone <repo>
cd ARIA
pip install -e .       # installs deps + registers `aria` CLI commands
aria setup             # interactive wizard: provider → credentials → user profile → .env
aria serve             # start the WebSocket server
aria chat              # start the terminal chat client (separate terminal)
aria heartbeat         # start the autonomous heartbeat loop
aria start             # convenience: launches all three processes
```

---

## New Files

| File | Purpose |
|---|---|
| `pyproject.toml` | Replaces `requirements.txt`. Defines dependencies and CLI entry points. |
| `cli.py` | CLI entry point. Parses subcommands and delegates to the appropriate script. |
| `setup_wizard.py` | Interactive setup wizard. Collects model provider, credentials, and user profile. Writes `.env`. |

`requirements.txt` is deleted. All existing runtime scripts (`server.py`, `heartbeat.py`, `interface.py`, `summary_scheduler.py`) are unchanged — the CLI wraps them.

---

## `pyproject.toml`

Declares project metadata, dependencies (migrated from `requirements.txt`), and a single CLI entry point:

```toml
[project.scripts]
aria = "cli:main"
```

After `pip install -e .`, the `aria` command is available system-wide in the active Python environment.

---

## `cli.py`

Thin dispatcher. Subcommands:

| Command | Action |
|---|---|
| `aria setup` | Runs `setup_wizard.py` |
| `aria serve` | Runs `server.py` |
| `aria chat` | Runs `interface.py` |
| `aria heartbeat` | Runs `heartbeat.py` |
| `aria summarize` | Runs `summary_scheduler.py` |
| `aria start` | Launches `serve`, `heartbeat`, and `chat` as subprocesses |

`aria start` launches serve + heartbeat as background subprocesses, then brings chat to the foreground. Ctrl-C on `aria start` terminates all three.

---

## `setup_wizard.py`

Sequential prompts, writes `.env` on completion.

### Step 1 — Model Provider

```
Which model provider would you like to use?
  [1] AWS Bedrock (Claude)
  [2] Claude API (Anthropic)
  [3] Ollama (local — Qwen3 40B)
```

### Step 2 — Credentials

Collected per provider:

| Provider | Env vars collected |
|---|---|
| AWS Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` |
| Claude API | `ANTHROPIC_API_KEY` |
| Ollama | `OLLAMA_BASE_URL` (default: `http://localhost:11434`), `OLLAMA_MODEL` (default: `qwen3:40b`) |

`MODEL_PROVIDER=bedrock|claude|ollama` is also written to `.env` so `config.py` knows which provider to instantiate at runtime.

### Step 3 — Tavily API Key (optional)

```
Tavily API key (for web search — press Enter to skip):
```

Writes `TAVILY_API_KEY` if provided. Web search is disabled gracefully if absent.

### Step 4 — User Profile

```
Your name (used as your user ID):
```

- Writes `USER_ID={name}` to `.env`
- Creates `memory/users/{name}.md` with a minimal template (name, blank collaboration notes)

### Step 5 — Done

Prints a summary of what was written and the next command to run (`aria serve`).

---

## Model Provider Wiring (`config.py`)

A new `get_model()` function reads `MODEL_PROVIDER` from the environment and returns the appropriate Strands model object:

- `bedrock` → default Strands/Bedrock model (no extra args needed)
- `claude` → `AnthropicModel(api_key=ANTHROPIC_API_KEY)`
- `ollama` → `OllamaModel(base_url=OLLAMA_BASE_URL, model_id=OLLAMA_MODEL)`

`agent.py` calls `get_model()` and passes the result as `model=` to the `Agent()` constructor. This is the only change to existing runtime code.

---

## Out of Scope

- Docker / containerization
- Windows service / launchd / systemd daemonization
- Additional model providers (can be added later)
- GUI or web-based setup
