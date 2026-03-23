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

**Run the Chainlit app:**
```bash
chainlit run coach/web/chainlit_app.py
# Required env vars: SUPABASE_SECRET_KEY, STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET,
#   OAUTH_GOOGLE_CLIENT_ID, OAUTH_GOOGLE_CLIENT_SECRET, CHAINLIT_AUTH_SECRET
# CHAINLIT_APP_ROOT must point to the repo root (set in .env)
# STRAVA_REDIRECT_URI must be http://localhost:8000/oauth/auth/strava/callback
#   (the FastAPI callback app is mounted at /oauth on Chainlit's Starlette server)
# CHAINLIT_URL defaults to http://localhost:8000 — Strava callback redirects here after success
```

## Architecture

The app is a multi-user Chainlit web app. Users authenticate with Google, connect Strava, and chat with an AI coach that always has their recent training context.

**Layer flow (web):**
1. `coach/web/chainlit_app.py` — Chainlit entry point; handles OAuth callback, chat start (resolves LLM key, syncs Strava, loads profile), message routing, and action callbacks
2. `coach/web/coaching.py` — `init_coach_session`, `load_coaching_data`, `get_llm_config`; owns shared session key constants
3. `coach/web/profile_flow.py` — profile setup/editing flow handlers
4. `coach/builders/` — Transforms raw `Activity` objects into structured summaries (`RecentTrainingHistory`, `RunningPersonalBestsSummary`, `TrainingGoal`)
5. `coach/reasoning/` — `Coach`/`ProfileAssistant` (extend `Assistant`); `create_llm_client` and `resolve_provider_and_key` in `providers.py`; thin client wrappers in `clients.py`

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
**Web app** (`coach/web/`):
- `coach/web/app.py` — FastAPI app factory (`create_app()`); runnable via `uvicorn coach.web.app:app`
- `coach/web/strava_oauth.py` — `generate_strava_auth_url(user_id, secret_client)` inserts CSRF state + returns auth URL; `GET /auth/strava/callback` verifies state, exchanges code, stores tokens, redirects to `CHAINLIT_URL`; mounted at `/oauth` on Chainlit's Starlette server
- `coach/web/session.py` — auth session helpers (`init_user_session`, `get_authenticated_client`, `get_user_id`) + shared session key constants for auth tokens; imported by `chainlit_app.py` and `profile_flow.py`
- `coach/web/coaching.py` — `init_coach_session`, `load_coaching_data`, `get_display_name`, `get_llm_config`; owns shared session key constants (`SESSION_ACTIVITIES`, `SESSION_DISPLAY_NAME`, `SESSION_CURRENT_PROFILE`, `SESSION_COACH`, `SESSION_MODE`, `SESSION_LLM_PROVIDER`, `SESSION_LLM_API_KEY`, `MODE_COACH`, `MODE_PROFILE`) imported by `profile_flow.py` and `chainlit_app.py`
- `coach/web/profile_flow.py` — profile setup/editing flow: `handle_profile_message`, `handle_start_profile_setup`, `handle_skip_to_coaching`, `handle_skip_section`, `handle_edit_profile`, `handle_edit_section`; `prompt_profile_setup`; pure helpers `is_done`, `strip_done`, `setup_progress_message`; deduplication via `_advance_profile_flow(profile, done_message)`
- `coach/web/chainlit_app.py` — thin Chainlit wiring only: `@cl.oauth_callback`, `@cl.on_chat_start`, `@cl.on_message`, and `@cl.action_callback` stubs that delegate to `session`/`coaching`/`profile_flow`; FastAPI sub-app mounted via `cl.server.app.router.routes.insert(0, Mount('/oauth', app=...))` — **not** `cl.server.app.mount()`, which would append after Chainlit's SPA catch-all and never be reached
- Uses the Supabase **secret key** (`SUPABASE_SECRET_KEY`) for all Vault RPC calls; uses anon key + user JWT to verify caller identity
- Testing: inject mock client via `app.dependency_overrides[create_secret_client] = lambda: mock` (import `create_secret_client` from `coach.persistence.database`); mock Supabase fluent chain as `mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [...]`
- `FastAPI TestClient` requires `httpx` as a dev dependency

**Chainlit quirks:**
- `@cl.oauth_callback` signature must include `id_token: Optional[str] = None` even though Chainlit never passes it — mypy fails without it
- `cl.Action` (Chainlit 2.x): use `payload={}` (a `dict`), not `value=...` (removed)
- `cl.User.metadata` must be JSON-serializable — store `datetime` as `.isoformat()`, parse back with `datetime.fromisoformat()` in `_init_user_session`

**User personalization:**
- Profile stored as structured fields in the Supabase `profiles` table per user (`coach/persistence/repositories/profiles.py`)
- Goals are parsed from the profile's `goals` JSONB column by `coach/builders/training_goal.py` into typed `TrainingGoal` objects
- `user_id` derived from the Google OAuth session (no env var needed)

**Adding a new LLM provider:** implement `LLMClient` in `coach/reasoning/clients.py`, add an entry to `_ENV_KEYS` and cases in `create_llm_client` / `resolve_provider_and_key` in `coach/reasoning/providers.py`.

## Product vision

The end goal is a hosted, multi-user web coaching app — think ChatGPT or Claude.ai, but with Strava activities and a personal profile always wired in the background. Users log in via Google, connect Strava, and get a personalized AI coaching chat that is always aware of their recent training. No CLI, no config files, no technical setup required.

Key characteristics of the end state:
- **Multi-user hosted**: a single deployment serves many users, each with isolated data
- **Google login**: users authenticate via Google OAuth through Supabase Auth — no account creation form, no passwords
- **Strava integration**: users connect Strava once; activities sync automatically in the background
- **Google AI Studio key provided by default**: the operator provides the API key; users can optionally supply their own via the Chainlit env dialog
- **Chainlit UI**: the chat interface is built on Chainlit; no CLI exists

The core domain and reasoning logic (`coach/domain/`, `coach/builders/`, `coach/reasoning/`) must remain UI-agnostic and user-agnostic (no hardcoded users, no assumptions about how keys are sourced).

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
- [x] `coach/auth/strava_tokens.py` — `StravaTokens` dataclass + `StravaTokenRepository` ABC + `SupabaseStravaTokenRepository` (calls RPC functions with secret key)
- [x] Refactor `StravaAuth` to accept `user_id` + `StravaTokenRepository`; reads `STRAVA_CLIENT_ID`/`STRAVA_CLIENT_SECRET` from env for refresh
- [x] Refactor `StravaClient` to accept `user_id` + `StravaTokenRepository`
- [x] `coach/ingestion/strava/sync.py` — `sync_strava_for_user(strava_client, activity_repo, *, fresh=False) -> int` pure callable
- [x] `coach/web/app.py` + `coach/web/strava_oauth.py` — FastAPI app with `GET /auth/strava` (initiates OAuth) and `GET /auth/strava/callback` (exchanges code, stores tokens, returns success page); runnable standalone via `uvicorn coach.web.app:app`

### Phase 3 — Chainlit web app ✅
- [x] Basic Chainlit app with the same coaching chat loop
- [x] Google OAuth login via Supabase Auth
- [x] Strava connect flow in the web UI: detect missing `strava_user_id` on `chat_start`, show "Connect Strava" action button; mount `coach/web/` FastAPI app on Chainlit's underlying Starlette app
- [x] Incremental Strava sync on `chat_start` (calls `sync_strava_for_user`)
- [x] Per-user profile editing in the web UI
- [x] Operator-provided Google AI Studio key; users can optionally supply their own via Chainlit `user_env`
- [x] Coach icon branding (`public/coach_icon.png`, configured in `.chainlit/config.toml`)
- [x] CLI removal: `coach/cli/`, `coach/scripts/`, CLI auth flows, `CredentialsStore` deleted; `typer` removed from deps

### Phase 4 — Launch ✅
- [x] Deployment on Railway (Dockerfile-based, GitHub-connected, live at https://coach-production-e0b4.up.railway.app/)
- [x] README rewritten for hosted app (no installation required for end users)
- [ ] Enable `pg_cron` extension in Supabase and schedule periodic cleanup of expired `strava_oauth_state` rows
- [ ] Activity feed / history view in the UI

### Phase 5 — User API key management
- [ ] Per-user API key storage in Supabase Vault, keyed by `(user_id, provider)`; same Vault pattern as Strava tokens (SECURITY DEFINER RPCs, secret key only)
- [ ] Load stored key at chat start; fallback chain: user Vault key → operator env key
- [ ] UI flow: detect missing key, prompt user to enter one, save to Vault; allow removal
- [ ] Support both `google` and `openai` providers

### Phase 6 — Chat persistence
- [ ] Store chat threads and messages in Supabase (new `threads` / `messages` tables with RLS)
- [ ] Load the most recent thread on chat start; restore `ChatHistory` from it
- [ ] Thread list / history view in the UI sidebar

## Testing conventions

- Test class name mirrors the class under test: `TestRecentTrainingHistoryBuilder` tests `RecentTrainingHistoryBuilder`
- Use `setup_method` to share common setup and set sensible defaults; individual tests override only what is specific to them
- When all tests in a class share the same function call, make that call in `setup_method` and store the result; individual tests then assert on a single aspect (e.g. `assert self._profile is ...`)
- Prefer testing through public interfaces. Private helpers may be tested directly when (a) the public interface is not unit-testable (e.g. Chainlit handlers) and (b) the helper has meaningful standalone logic worth specifying. Do not create a separate module just to make a private helper importable — test it directly from the module it lives in.
- Always cover unhappy paths and edge cases (missing data, expired state, invalid input, None returns) alongside the happy path
- Prefer **fakes** over **mocks** for your own abstractions: write a minimal in-memory implementation of the ABC (e.g. `FakeStravaTokenRepository` storing tokens in a dict) rather than a `MagicMock`. Fakes are readable, catch interface changes, and have no magic. Reserve `MagicMock`/`patch` for genuinely external things you cannot control: Supabase `Client`, HTTP calls (`requests.post`), time.
- Use `setup_method`/`teardown_method` for class-scoped patches (start patcher in `setup_method`, stop in `teardown_method`); avoid `@pytest.fixture(autouse=True)` inside test classes
- Focus on simple, focused unit tests; avoid complex integration tests unless necessary
- Tests live in a `tests/` subdirectory next to the module they test (e.g. `coach/builders/tests/`)
- Importing private helpers from a Chainlit app file in tests requires stubbing `chainlit.server.server` before import — do this in a `conftest.py` in the same `tests/` directory (see `coach/web/tests/conftest.py`)

## Code conventions

- Python 3.13+, strict mypy, ruff linting (line length 200)
- All functions must be fully typed; `Optional[]` preferred over `X | None`
- Single-quote strings enforced by ruff (`Q001`)
- Imports are force-single-line (isort setting)
- Prefer `ABC` + `@abstractmethod` over `Protocol` for interfaces — explicit inheritance and runtime enforcement are preferred over structural subtyping
- Use `setup_method` for shared test setup; avoid `@pytest.fixture(autouse=True)` inside test classes
- Avoid docstrings and comments that restate what the code already says; only add a comment when the intent cannot be made clear through naming, structure, or a well-named helper method
- Prefer intermediate variable assignments over deeply nested calls — clarity beats brevity. Example: `raw = client.fetch(); result = process(raw)` is preferable to `result = process(client.fetch())`
- Prefer private helpers within a module over extracting a separate helper module for logic tightly coupled to a single caller — a new module is only warranted when logic is genuinely reused or completely independent. The same applies to wrapper functions: a one-liner that only adds a fixed set of arguments to another constructor or function call is not worth naming.
- Functions should have a single, non-overlapping responsibility. Avoid "halfway abstractions" where a function takes pre-constructed dependencies but also owns loading/fetching internally — that halfway position makes the function hard to test and unclear to read. Either own the full setup (construct deps + do the work) or accept pre-loaded data and act on it.
- After making any change, review the affected code for simplification opportunities, duplication, and best-practice violations before considering the task done
- Use `datetime.UTC` alias instead of `timezone.UTC` for consistency

## GitHub workflow

- `master` is a protected branch — never push directly to it. All changes go through a PR.
- Group commits into logical units — each commit should represent one coherent, independently buildable change (e.g. one refactor, one feature, one fix). Never mix unrelated changes in a single commit.
- Always prefer **rebase merge** (`gh pr merge --rebase`) over squash or merge commits to keep a clean linear history
- **Always `git push` before `gh pr merge --rebase`** — the command merges the remote branch; local-only commits not yet pushed will be silently left behind
- `gh issue close` accepts one issue at a time — use a loop: `for i in 1 2 3; do gh issue close $i; done`
- `gh issue view` emits a GraphQL deprecation warning to stderr; use `--json title,body` to suppress it
- `.claude/CLAUDE.md` is tracked by git (`.claude/*` is ignored except `CLAUDE.md`); no stashing needed for commits, but `gh pr merge` with an open worktree may still require care
