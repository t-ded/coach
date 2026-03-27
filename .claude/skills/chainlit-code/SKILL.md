---
name: chainlit-code
description: Chainlit-specific patterns and gotchas for the coach project. Use this skill whenever touching any file in coach/web/ — chainlit_app.py, session.py, coaching.py, profile_flow.py, strava_oauth.py, or any new web module. These quirks cause hard-to-debug failures if missed.
---

# Chainlit coding guide (coach project)

## Known quirks

**`@cl.oauth_callback` signature** — must include `id_token: Optional[str] = None` even though Chainlit never passes it. mypy fails without it.

**`cl.Action` (Chainlit 2.x)** — use `payload={}` (a dict), not `value=...` (the `value` parameter was removed).

**`cl.User.metadata`** — must be JSON-serializable. Store `datetime` as `.isoformat()`, parse back with `datetime.fromisoformat()`.

**Mounting FastAPI sub-apps** — use `router.routes.insert`, not `app.mount()`:
```python
# correct — inserts before SPA catch-all
cl.server.app.router.routes.insert(0, Mount('/oauth', app=create_app()))

# wrong — appended after Chainlit's SPA catch-all, never reached
cl.server.app.mount('/oauth', app=create_app())
```

## Architecture rules

`chainlit_app.py` must stay thin — only Chainlit wiring (`@cl.oauth_callback`, `@cl.on_chat_start`, `@cl.on_message`, `@cl.action_callback`). All logic delegates to `session`, `coaching`, or `profile_flow`.

## Supabase in web context

- Vault RPC calls (Strava tokens, API keys) require the **secret key** (`SUPABASE_SECRET_KEY`), not the anon key
- The anon key + user JWT is used everywhere else for per-user data access
- API keys must never enter the Chainlit chat stream — entry goes through the FastAPI form at `/oauth/api-key`

## Testing Chainlit handlers

Chainlit app handlers cannot be tested through the public interface. Test private helpers directly from the module. Stub `chainlit.server.server` in `conftest.py` before importing the app module — see `coach/web/tests/conftest.py`.
