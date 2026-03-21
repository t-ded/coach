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

**Run the web app (Strava OAuth):**
```bash
SUPABASE_SECRET_KEY=... STRAVA_CLIENT_ID=... STRAVA_CLIENT_SECRET=... uvicorn coach.web.app:app
# Routes: GET /auth/strava (initiate), GET /auth/strava/callback
# STRAVA_REDIRECT_URI defaults to http://localhost:8000/auth/strava/callback
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

**Web app** (`coach/web/`):
- `coach/web/app.py` — FastAPI app factory (`create_app()`); runnable via `uvicorn coach.web.app:app`
- `coach/web/strava_oauth.py` — `GET /auth/strava` (initiates OAuth, inserts CSRF state) + `GET /auth/strava/callback` (verifies state, exchanges code, stores tokens in Vault, updates `users.strava_user_id`); designed to be mounted on Chainlit's Starlette app in Phase 3 without modification
- Uses the Supabase **secret key** (`SUPABASE_SECRET_KEY`) for all Vault RPC calls; uses anon key + user JWT to verify caller identity
- Testing: inject mock client via `app.dependency_overrides[get_secret_client] = lambda: mock`; mock Supabase fluent chain as `mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [...]`
- `FastAPI TestClient` requires `httpx` as a dev dependency

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

### Phase 2 — Multi-user foundation (Strava + Supabase integration) ✅

**Architecture decisions:**
- Operator-owned Strava API app (single `STRAVA_CLIENT_ID`/`STRAVA_CLIENT_SECRET` as server env vars — users never touch the Strava developer portal)
- Per-user tokens stored in `private.strava_tokens` (Vault-backed: `access_token_vault_id`, `refresh_token_vault_id` UUIDs) — never exposed via Data API
- Vault reads/writes go through `SECURITY DEFINER` Postgres functions in `public` schema, called via `supabase.rpc()` with the **secret key** (server-side only; **publishable key** used everywhere else)
- `public.strava_oauth_state` table (RLS-protected) for CSRF state during OAuth dance
- Incremental Strava sync triggered on chat start (not background/webhook); 2-week lookback buffer on `sync_cursor()` to catch backdated or edited activities
- Core sync logic extracted into a callable function usable by both CLI and web

**Supabase steps (Dashboard → SQL Editor):**
- [x] Create `public.strava_oauth_state` table with RLS (`auth.uid() = user_id`)
- [x] Create `public.upsert_strava_tokens(p_user_id, p_access_token, p_refresh_token, p_expires_at)` — SECURITY DEFINER, writes to Vault + `private.strava_tokens`
- [x] Create `public.get_strava_tokens(p_user_id)` — SECURITY DEFINER, returns decrypted tokens from Vault
- [x] Create `public.delete_strava_tokens(p_user_id)` — SECURITY DEFINER, removes Vault secrets + table row
- [x] RLS policies on all `public` tables enforcing per-user data isolation

**Code steps:**
- [x] `coach/auth/strava_tokens.py` — `StravaTokens` dataclass + `StravaTokenRepository` ABC + `SupabaseStravaTokenRepository` (calls RPC functions with secret key) + `CredentialsStoreStravaTokenRepository` (CLI path)
- [x] Refactor `StravaAuth` to accept `user_id` + `StravaTokenRepository`; reads `STRAVA_CLIENT_ID`/`STRAVA_CLIENT_SECRET` from env for refresh
- [x] Refactor `StravaClient` to accept `user_id` + `StravaTokenRepository`
- [x] `coach/ingestion/strava/sync.py` — `sync_strava_for_user(strava_client, activity_repo, *, fresh=False) -> int` pure callable; CLI `sync strava` is a thin wrapper
- [x] `coach/web/app.py` + `coach/web/strava_oauth.py` — FastAPI app with `GET /auth/strava` (initiates OAuth) and `GET /auth/strava/callback` (exchanges code, stores tokens, returns success page); runnable standalone via `uvicorn coach.web.app:app`

### Phase 3 — Chainlit web app
- [ ] Basic Chainlit app with the same coaching chat loop
- [ ] Google OAuth login via Supabase Auth (no CLI auth needed)
- [ ] Strava connect flow in the web UI: detect missing `strava_user_id` on `chat_start`, show "Connect Strava" action button; mount `coach/web/` FastAPI app on Chainlit's underlying Starlette app
- [ ] Incremental Strava sync on `chat_start` (calls `sync_strava_for_user`)
- [ ] Per-user profile editing in the web UI
- [ ] Operator-provided Google AI Studio key (no user configuration needed)

### Phase 4 — Launch
- [ ] Deployment (e.g. Fly.io, Railway, or similar)
- [ ] User-supplied API keys (for users who want to bring their own)
- [ ] Activity feed / history view in the UI

## Testing conventions

- Test class name mirrors the class under test: `TestRecentTrainingHistoryBuilder` tests `RecentTrainingHistoryBuilder`
- Use `setup_method` to share common setup and set sensible defaults; individual tests override only what is specific to them
- Only test public methods/attributes — do not reach into private internals
- Always cover unhappy paths and edge cases (missing data, expired state, invalid input, None returns) alongside the happy path
- Focus on simple, focused unit tests; avoid complex integration tests unless necessary
- Tests live in a `tests/` subdirectory next to the module they test (e.g. `coach/builders/tests/`)

## Code conventions

- Python 3.13+, strict mypy, ruff linting (line length 200)
- All functions must be fully typed; `Optional[]` preferred over `X | None`
- Single-quote strings enforced by ruff (`Q001`)
- Imports are force-single-line (isort setting)
- Prefer `ABC` + `@abstractmethod` over `Protocol` for interfaces — explicit inheritance and runtime enforcement are preferred over structural subtyping
- Use `setup_method` for shared test setup; avoid `@pytest.fixture(autouse=True)` inside test classes
- Avoid docstrings and comments that restate what the code already says; only add a comment when the intent cannot be made clear through naming, structure, or a well-named helper method
- Prefer intermediate variable assignments over deeply nested calls — clarity beats brevity. Example: `raw = client.fetch(); result = process(raw)` is preferable to `result = process(client.fetch())`
- After making any change, review the affected code for simplification opportunities, duplication, and best-practice violations before considering the task done

## GitHub workflow

- Always prefer **rebase merge** (`gh pr merge --rebase`) over squash or merge commits to keep a clean linear history
- `gh issue close` accepts one issue at a time — use a loop: `for i in 1 2 3; do gh issue close $i; done`
- `gh issue view` emits a GraphQL deprecation warning to stderr; use `--json title,body` to suppress it
- `.claude/CLAUDE.md` is tracked by git (`.claude/*` is ignored except `CLAUDE.md`); no stashing needed for commits, but `gh pr merge` with an open worktree may still require care
