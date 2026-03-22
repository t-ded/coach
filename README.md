![Coach](public/coach_icon.png)

# Coach

An AI-powered training coach that provides **personalized coaching advice** based on your Strava activity data. Sign in with Google, connect Strava once, and get an AI coach that knows your recent training history, personal bests, and goals — always up to date.

---

## Features

- **Strava integration**: Activities sync automatically from Strava (free account supported)
- **AI coaching chat**: Interactive multi-turn conversations with context from your recent training
- **Personalized profile**: Set your goals, constraints, training preferences, and communication style through a guided setup flow
- **Private notes**: Add coaching-relevant context to Strava activity notes using `$...$` delimiters
- **Google login**: No account creation — sign in with your existing Google account
- **Bring your own key**: Optionally supply a Google AI or OpenAI API key; the app falls back to the operator-provided key when none is given

---

## How it works

1. **Sign in with Google** — authentication is handled via Google OAuth through Supabase Auth
2. **Connect Strava** — click the "Connect Strava" button; your activities sync automatically each session
3. **Set up your profile** — a guided 5-section flow collects your chat preferences, training style, background, constraints, and goals; each section is a short AI-powered conversation
4. **Start coaching** — ask about your training, request weekly plans, or explore your progress; the coach always has your latest Strava data in context

---

## Screenshots

### Login

![Login screen](public/screenshots/login.png)

### Strava connect prompt

![Strava connect](public/screenshots/strava_connect.png)

### Profile setup

![Profile setup](public/screenshots/profile_setup.png)

### Coaching chat

![Coaching chat](public/screenshots/coaching_chat.png)

---

## Running the app

### Required environment variables

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL (optional — defaults to the project default) |
| `SUPABASE_ANON_KEY` | Supabase anonymous key (optional — defaults to the project default) |
| `SUPABASE_SECRET_KEY` | Supabase service role key (used for Vault RPC calls) |
| `STRAVA_CLIENT_ID` | Strava API application client ID |
| `STRAVA_CLIENT_SECRET` | Strava API application client secret |
| `OAUTH_GOOGLE_CLIENT_ID` | Google OAuth client ID (for Chainlit login) |
| `OAUTH_GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `CHAINLIT_AUTH_SECRET` | Random secret for Chainlit session signing |
| `GOOGLE_AI_API_KEY` | Operator-provided Google AI Studio key (users can override via the UI) |
| `STRAVA_REDIRECT_URI` | Strava OAuth callback URL — must be `http://localhost:8000/oauth/auth/strava/callback` locally |
| `CHAINLIT_URL` | Base URL Strava redirects to after OAuth — defaults to `http://localhost:8000` |
| `CHAINLIT_APP_ROOT` | Path to the repo root (set in `.env`) |

### Start the app

```bash
chainlit run coach/web/chainlit_app.py
```

---

## Private notes

Add coaching-relevant context to any Strava activity's private notes using `$...$` delimiters:

```
$VO2 max 5x1 @4:30 — felt very hard, knee a bit sore on last rep$
```

The coach extracts and uses this information when analysing your training. Content outside the delimiters is ignored.

---

## Development

**Install with dev dependencies:**
```bash
uv sync --group dev
```

**Run tests:**
```bash
pytest
```

**Lint and type-check:**
```bash
ruff check .
ruff format .
mypy .
```
