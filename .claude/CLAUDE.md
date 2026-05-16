# CLAUDE.md

## Commands

```bash
uv sync --group dev                             # install
chainlit run coach/web/chainlit_app.py          # run app
ruff check . && ruff format . && mypy . && pytest   # full check suite (see /run-checks)
```

Required env vars: `SUPABASE_SECRET_KEY`, `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `OAUTH_GOOGLE_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_SECRET`, `CHAINLIT_AUTH_SECRET`
Set `CHAINLIT_APP_ROOT` to repo root and `STRAVA_REDIRECT_URI=http://localhost:8000/oauth/auth/strava/callback` in `.env`.
Optional (post-activity email insights): `RESEND_API_KEY`, `RESEND_FROM_EMAIL` — if absent, email notifications are silently disabled.
DB migration required for notifications: run `supabase/migrations/20260515_add_notification_columns.sql`.
Webhook path token: `STRAVA_WEBHOOK_PATH_TOKEN` — a random secret embedded in the webhook URL (`/oauth/webhook/strava/{token}`). Must match what is registered with Strava as the callback URL.

## Architecture

Multi-user Chainlit web app: Google OAuth → Strava → AI coaching chat with recent training context.
Live at https://coach-production-e0b4.up.railway.app/ (Railway, Dockerfile-based).

Layer flow:
1. `coach/web/chainlit_app.py` — thin Chainlit wiring only; delegates everything to session/coaching/profile_flow
   └ mounts `coach/web/app.py` (FastAPI) at `/oauth` for Strava OAuth callback + webhook events
2. `coach/web/session.py` — auth helpers + session key constants
3. `coach/web/coaching.py` — coach session init, data loading, LLM config; owns `SESSION_*`/`MODE_*` constants
4. `coach/web/profile_flow.py` — profile setup/editing flow
5. `coach/domain/` — immutable domain models (`Activity`, `Profile`, `TrainingSession`, `ActivityIntensityProfile`, etc.) shared across layers
6. `coach/builders/` — transforms raw Strava/domain data into coaching context objects (`RecentTrainingHistory`, `RunningPersonalBestsSummary`, `TrainingGoal`, `ActivityIntensityProfile`, weekly summaries, training trends)
7. `coach/reasoning/` — `providers.py` (LLM key resolution), `clients.py` (Google/OpenAI/Anthropic wrappers); `coach/` submodule contains `Coach` with `context.py` + `sections/` (one section per coaching context block); `profile_assistant/` for profile setup LLM flows
8. `coach/persistence/` — Supabase repos; Vault RPC via `SUPABASE_SECRET_KEY` for Strava tokens + API keys
   FastAPI routers: `strava_oauth.py` (OAuth callback), `strava_webhook.py` (activity + deauth events)
   Deauthorization service: `coach/ingestion/strava/deauthorize.py`
9. `coach/auth/` — Strava token helpers (exchange, refresh)
10. `coach/notifications/` — `NotificationService` with `ResendEmailBackend` (email) + `PushBackend` stub; `ActivityInsightGenerator` for post-activity LLM insights; triggered by Strava webhook on activity create

## Code style

Non-negotiables (enforced by code review, beyond what ruff/mypy catch automatically):
- **No single-letter variables** — name every variable for what it holds
- **`# type: ignore` and `typing.Any` are symptoms**, not solutions — investigate the root cause; if truly unavoidable, add a comment explaining why
- **Security first** — authentication, authorization, and input validation take precedence over feature completeness; never defer security hardening
- **Refactor before feature** — when adding a feature, first make the existing code ready to accept it cleanly; the feature itself should be indistinguishable from the surrounding code in style and structure

## Skills

Use these slash commands for task-specific guidance:
- `/python-conventions` — code style rules (always apply when writing Python)
- `/write-tests` — testing conventions (always apply when writing tests)
- `/chainlit-code` — Chainlit quirks and patterns (always apply when touching `coach/web/`)
- `/github-workflow` — git/PR rules (always apply before committing or merging)
- `/run-checks` — how to verify changes are clean
- `/add-provider` — recipe for adding a new LLM provider

## Roadmap

See `.claude/docs/roadmap.md` for next steps. Always keep these in mind to not introduce any roadblocks along the way.
