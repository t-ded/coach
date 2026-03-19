# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies** (uses uv):
```bash
pip install -e .
# or with dev dependencies:
uv sync --group dev
```

**Run tests:**
```bash
pytest
# Single test file:
pytest coach/builders/tests/test_weekly_summary.py
# Single test:
pytest coach/builders/tests/test_weekly_summary.py::test_name
```

**Lint and type-check:**
```bash
ruff check .
ruff format .
mypy .
```

**Run the CLI:**
```bash
coach auth setup       # Interactive credential setup
coach sync strava      # Sync activities from Strava
coach info --pbs       # Show running personal bests
coach chat             # Start coaching chat (Google AI default)
coach chat --provider openai --model gpt-4o --num-history-weeks 4
```

## Architecture

The app is a CLI tool (entry point: `coach/cli/app.py`) that syncs Strava activities to Supabase and then runs LLM-powered coaching conversations.

**Layer flow for `coach chat`:**
1. `coach/scripts/coach.py` — CLI handler; creates a `UserSession`, loads profile + activities from Supabase, passes them to `Coach`, runs the chat loop
2. `coach/builders/` — Transforms raw `Activity` domain objects into structured summaries (`RecentTrainingHistory`, `RunningPersonalBestsSummary`, `TrainingGoal`)
3. `coach/reasoning/adapter.py` (`LLMCoachReasoner`) — Renders context to text via `coach/reasoning/context.py`, builds the final prompt via `coach/reasoning/prompts.py`, calls the LLM
4. `coach/reasoning/clients.py` — Thin wrappers around Google GenAI and OpenAI SDKs, both implementing `LLMClient` from `coach/reasoning/interface.py`

**Key domain types** (`coach/domain/`):
- `Activity` — core data model synced from Strava (sport type, distance, heart rate, best efforts, private notes)
- `RecentTrainingHistory` / `WeeklySummary` — aggregated view of N weeks of activities fed to the LLM
- `RunningPersonalBestsSummary` — structured PBs (1K, 5K, 10K, HM, marathon)
- `ChatHistory` — rolling window of up to 6 turns for multi-turn conversation

**Persistence** (`coach/persistence/`):
- `coach/persistence/repository_interface.py` — generic `Repository[T]` interface
- `coach/persistence/serialization.py` — Activity/Goal/Profile serialization to plain Python dicts/lists (no JSON strings); Supabase JSONB columns handle the rest natively
- `coach/persistence/repositories/` — `SupabaseActivityRepository` and `SupabaseUserProfileRepository`
- `coach/persistence/database.py` — builds the `supabase.Client` using the anon key (embedded as a default; overridable via `SUPABASE_URL` / `SUPABASE_ANON_KEY` env vars)
- `coach/persistence/session.py` — `UserSession` dataclass + `load_session()`: restores the stored Google OAuth session from `~/.coach/credentials.json`, calls `refresh_session()` to get a fresh token, derives `user_id` from the authenticated user

**User personalization:**
- Profile stored as structured fields in the Supabase `profiles` table per user (`coach/persistence/repositories/profiles.py`)
- Goals are parsed from the profile's `goals` JSONB column by `coach/builders/training_goal.py` into typed `TrainingGoal` objects
- `user_id` derived from the Google OAuth session (no env var needed)
- Credentials stored at `~/.coach/credentials.json` (600 permissions) — Supabase session tokens, Strava OAuth tokens, and LLM API keys

**Adding a new LLM provider:** implement `LLMClient` in `coach/reasoning/clients.py`, add a case to `coach/reasoning/providers.py`, and add an auth flow in `coach/auth/`.

## Product vision

The end goal is a hosted, multi-user web coaching app — think ChatGPT or Claude.ai, but with Strava activities and a personal profile always wired in the background. Users log in via Google, connect Strava, and get a personalized AI coaching chat that is always aware of their recent training. No CLI, no config files, no technical setup required.

Key characteristics of the end state:
- **Multi-user hosted**: a single deployment serves many users, each with isolated data
- **Google login**: users authenticate via Google OAuth through Supabase Auth — no account creation form, no passwords
- **Strava integration**: users connect Strava once; activities sync automatically in the background
- **Google AI Studio key provided by default**: the operator (us) provides the API key; eventually power users can supply their own
- **Chainlit UI**: the chat interface is built on Chainlit, replacing the CLI entirely

The core domain and reasoning logic (`coach/domain/`, `coach/builders/`, `coach/reasoning/`) must remain UI-agnostic and user-agnostic (no hardcoded users, no CLI assumptions). The CLI scripts in `coach/scripts/` are a thin dev/testing layer that will be superseded by the Chainlit app.

## Roadmap

### Phase 1 — Supabase persistence ✅
- [x] Supabase activity repository
- [x] Supabase user profile repository
- [x] Wire Supabase repos into CLI, replacing SQLite
- [x] `UserSession` abstraction as the single seam for auth (`coach/persistence/session.py`)
- [x] Supabase Auth: Google OAuth via PKCE → `user_id` derived from session; stored tokens in `~/.coach/credentials.json`
- [x] Drop SQLite

### Phase 2 — Multi-user foundation
- [ ] RLS policies on all tables enforcing per-user data isolation
- [ ] Strava OAuth token stored per-user in Supabase (not in `~/.coach/credentials.json`)
- [ ] Background activity sync (scheduled or webhook-triggered) per user
- [ ] User profile stored in Supabase `profiles` table (free-text fields replacing `coach.md`)

### Phase 3 — Chainlit web app
- [ ] Basic Chainlit app with the same coaching chat loop
- [ ] Google OAuth login via Supabase Auth (no CLI auth needed)
- [ ] Strava connect flow in the web UI
- [ ] Per-user profile editing in the web UI
- [ ] Operator-provided Google AI Studio key (no user configuration needed)

### Phase 4 — Polish and scale
- [ ] Automatic Strava sync (webhook or periodic background job)
- [ ] User-supplied API keys (for users who want to bring their own)
- [ ] Activity feed / history view in the UI
- [ ] Deployment (e.g. Fly.io, Railway, or similar)

## Testing conventions

- Test class name mirrors the class under test: `TestRecentTrainingHistoryBuilder` tests `RecentTrainingHistoryBuilder`
- Use `setup_method` (or `@pytest.fixture`) to share common setup and avoid duplication across tests
- Only test public methods/attributes — do not reach into private internals
- Focus on simple, focused unit tests; avoid complex integration tests unless necessary
- Tests live in a `tests/` subdirectory next to the module they test (e.g. `coach/builders/tests/`)

## Code conventions

- Python 3.13+, strict mypy, ruff linting (line length 200)
- All functions must be fully typed; `Optional[]` preferred over `X | None`
- Single-quote strings enforced by ruff (`Q001`)
- Imports are force-single-line (isort setting)
- Avoid docstrings and comments that restate what the code already says; only add a comment when the intent cannot be made clear through naming, structure, or a well-named helper method
