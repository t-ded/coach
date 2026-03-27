# CLAUDE.md

## Commands

```bash
uv sync --group dev                             # install
chainlit run coach/web/chainlit_app.py          # run app
```

Required env vars: `SUPABASE_SECRET_KEY`, `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `OAUTH_GOOGLE_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_SECRET`, `CHAINLIT_AUTH_SECRET`
Set `CHAINLIT_APP_ROOT` to repo root and `STRAVA_REDIRECT_URI=http://localhost:8000/oauth/auth/strava/callback` in `.env`.

## Architecture

Multi-user Chainlit web app: Google OAuth → Strava → AI coaching chat with recent training context.
Live at https://coach-production-e0b4.up.railway.app/ (Railway, Dockerfile-based).

Layer flow:
1. `coach/web/chainlit_app.py` — thin Chainlit wiring only; delegates everything to session/coaching/profile_flow
2. `coach/web/session.py` — auth helpers + session key constants
3. `coach/web/coaching.py` — coach session init, data loading, LLM config; owns `SESSION_*`/`MODE_*` constants
4. `coach/web/profile_flow.py` — profile setup/editing flow
5. `coach/builders/` — `Activity` → `RecentTrainingHistory`, `RunningPersonalBestsSummary`, `TrainingGoal`
6. `coach/reasoning/` — `Coach`/`ProfileAssistant`; `providers.py` for LLM key resolution; `clients.py` for LLM wrappers
7. `coach/persistence/` — Supabase repos; Vault RPC via `SUPABASE_SECRET_KEY` for Strava tokens + API keys

## Skills

Use these slash commands for task-specific guidance:
- `/python-conventions` — code style rules (always apply when writing Python)
- `/write-tests` — testing conventions (always apply when writing tests)
- `/chainlit-code` — Chainlit quirks and patterns (always apply when touching `coach/web/`)
- `/github-workflow` — git/PR rules (always apply before committing or merging)
- `/run-checks` — how to verify changes are clean
- `/add-provider` — recipe for adding a new LLM provider

## Roadmap

See `.claude/docs/roadmap.md` for Phase 6 and deferred items.
