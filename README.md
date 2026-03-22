<div align="center">
  <img src="public/coach_icon.png" alt="Coach" width="96" />

  # Coach

  **An AI training coach that knows your Strava data**

  *Sign in with Google · Connect Strava · Chat with your coach*

</div>

---

Coach is a personalized AI coaching assistant that lives in your browser. It reads your recent Strava activities, personal bests, and training profile — and gives you thoughtful, data-grounded advice in a natural chat.

No setup, no CLI, no CSV exports. Just log in and start coaching.

---

## ⚡ Quick start

> Already have access to a running deployment? You're three steps away from your first coaching session.

**1. Sign in** — open the app and click **Continue with Google**. No registration form, no password.

**2. Connect Strava** — click the **Connect Strava** button and authorize the app. This is a one-time step; your activities will sync automatically from then on.

**3. Set up your profile** *(optional but recommended)* — the app will offer a short guided setup for your goals, training preferences, and constraints. Each section is a brief conversation — just describe yourself in plain language and the AI captures the key points. You can skip any section or come back to edit later via **Edit Profile**.

**That's it.** Ask your coach anything — *"How is my training going?"*, *"Give me a plan for next week"*, *"Why am I not improving my 5K time?"* — and it will answer based on your actual Strava data.

---

## ✨ Features

| | |
|---|---|
| 🔗 **Strava sync** | Activities sync automatically each session — free Strava account supported |
| 💬 **AI chat** | Multi-turn coaching conversations with your full training context always in view |
| 👤 **Personalized profile** | Guided setup for goals, constraints, training preferences, and communication style |
| 🔐 **Google login** | No account creation — sign in with your existing Google account |
| 📝 **Private notes** | Annotate Strava activities with coaching context using `$...$` delimiters |
| 🔑 **Bring your own key** | Optionally supply a Google AI or OpenAI API key; falls back to the operator key silently |

---

## 🚀 How it works

1. **Sign in with Google** — one click, no passwords
2. **Connect Strava** — authorize once; activities sync at the start of every session
3. **Set up your profile** — a 5-section guided flow (chat style, training preferences, background, constraints, and goals); each section is a short AI-powered conversation
4. **Start coaching** — ask about your week, request a training plan, or dig into your progress

---

## 📸 Screenshots

<table>
  <tr>
    <td align="center"><b>Login</b></td>
    <td align="center"><b>Strava connect</b></td>
  </tr>
  <tr>
    <td><img src="public/screenshots/login.png" alt="Login screen" /></td>
    <td><img src="public/screenshots/strava_connect.png" alt="Strava connect" /></td>
  </tr>
  <tr>
    <td align="center"><b>Profile setup</b></td>
    <td align="center"><b>Coaching chat</b></td>
  </tr>
  <tr>
    <td><img src="public/screenshots/profile_setup.png" alt="Profile setup" /></td>
    <td><img src="public/screenshots/coaching_chat.png" alt="Coaching chat" /></td>
  </tr>
</table>

---

## 🛠 Running the app

### Environment variables

**Required:**

| Variable | Description |
|---|---|
| `SUPABASE_SECRET_KEY` | Supabase service role key (used for Vault RPC calls) |
| `STRAVA_CLIENT_ID` | Strava API application client ID |
| `STRAVA_CLIENT_SECRET` | Strava API application client secret |
| `OAUTH_GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `OAUTH_GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `CHAINLIT_AUTH_SECRET` | Random secret for Chainlit session signing |
| `GOOGLE_AI_API_KEY` | Operator-provided Google AI Studio key |

**Optional / local overrides:**

| Variable | Default | Description |
|---|---|---|
| `SUPABASE_URL` | project default | Supabase project URL |
| `SUPABASE_ANON_KEY` | project default | Supabase anonymous key |
| `STRAVA_REDIRECT_URI` | `http://localhost:8000/oauth/auth/strava/callback` | Strava OAuth callback URL |
| `CHAINLIT_URL` | `http://localhost:8000` | Base URL Strava redirects to after OAuth |
| `CHAINLIT_APP_ROOT` | — | Path to repo root (set in `.env`) |

### Start

```bash
chainlit run coach/web/chainlit_app.py
```

---

## 📝 Private notes

Add coaching-relevant context to any Strava activity's private notes using `$...$` delimiters:

```
$5x1km VO2max session @4:30 — felt very hard, knee a bit sore on the last rep$
```

The coach extracts and uses this information when analysing your training. Anything outside the delimiters is ignored, so you can keep personal notes alongside coaching notes in the same field.

---

## 🧑‍💻 Development

```bash
uv sync --group dev   # install with dev dependencies
pytest                # run tests
ruff check .          # lint
ruff format .         # format
mypy .                # type-check
```
