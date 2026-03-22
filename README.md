<div align="center">
  <img src="public/coach_icon.png" alt="Coach" width="96" />

  # Coach

  **An AI training coach that knows your Strava data**

  *Sign in with Google · Connect Strava · Chat with your coach*

</div>

---

Coach is a personalized AI coaching assistant that lives in your browser. It reads your recent Strava activities, personal bests, and training profile — and gives you thoughtful, data-grounded advice in a natural chat.

> **Note:** Coach is not yet publicly hosted — for now you run it on your own computer by following the steps below. A hosted version (no installation required) is on the roadmap.

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

## ⚡ Getting started

Follow these steps once and you'll be chatting with your coach in about 10 minutes.

---

### Step 1 — Install Python

Coach requires **Python 3.13 or newer**.

- **Check if you already have it:** open a terminal (on Mac: *Terminal*, on Windows: *Command Prompt*) and type `python --version`. If it shows 3.13 or higher, skip to Step 2.
- **Install it:** download the installer from [python.org/downloads](https://www.python.org/downloads/) and run it. On Windows, tick **"Add Python to PATH"** during installation.

---

### Step 2 — Download Coach

[Download this repository as a ZIP](../../archive/refs/heads/master.zip), unzip it somewhere convenient (e.g. your Documents folder), and note the folder path — you will need it in Step 4.

Alternatively, if you have git: `git clone https://github.com/t-ded/coach.git`

---

### Step 3 — Get a Google AI Studio API key

Coach uses Google's AI models to power the chat. Getting a key is free and takes about 30 seconds:

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **"Create API key"**
4. Copy the key (it looks like `AIzaSy...`) — you will need it in the next step

---

### Step 4 — Set up the configuration file

1. In the Coach folder, find the file called **`.env.example`** and make a copy of it in the same folder named **`.env`** (just remove the `.example` part).

   > On Windows, `.env` files can be tricky to create — open `.env.example` in Notepad, make your edits, and use *Save As* → type `.env` as the filename and choose *All files* as the file type.

2. Open `.env` in a text editor (Notepad on Windows, TextEdit on Mac).

3. **Paste your Google AI Studio key** on the line that says `GOOGLE_AI_API_KEY=` — paste it right after the `=` sign, no spaces or quotes needed:
   ```
   GOOGLE_AI_API_KEY=AIzaSyYourKeyHere
   ```

4. **Set your project path** on the line that says `CHAINLIT_APP_ROOT=` — paste the full path to the Coach folder:
   ```
   # Windows example:
   CHAINLIT_APP_ROOT=C:\Users\YourName\Documents\coach

   # Mac/Linux example:
   CHAINLIT_APP_ROOT=/Users/yourname/Documents/coach
   ```

5. **Fill in the private credentials** on the four blank lines — you will have received these from the person who shared Coach with you:
   ```
   OAUTH_GOOGLE_CLIENT_SECRET=...
   STRAVA_CLIENT_SECRET=...
   SUPABASE_SECRET_KEY=...
   CHAINLIT_AUTH_SECRET=...
   ```

6. Save and close the file.

---

### Step 5 — Install dependencies

Open a terminal, navigate to the Coach folder, and run:

```bash
pip install -e .
```

This installs everything Coach needs. It may take a minute or two.

---

### Step 6 — Run Coach

In the same terminal, run:

```bash
chainlit run coach/web/chainlit_app.py
```

Your browser will open automatically. If it doesn't, open it and go to [http://localhost:8000](http://localhost:8000).

---

### Step 7 — First-time setup (in the browser)

**1. Sign in with Google** — click *Continue with Google* and sign in with your Google account. No new account or password needed.

**2. Connect Strava** — click the *Connect Strava* button and authorize the app. This is a one-time step; your activities will sync automatically from then on.

**3. Set up your profile** *(optional but recommended)* — you'll be guided through 5 short sections: chat preferences, training style, personal background, constraints (available days, etc.), and goals. For each one, just describe yourself in plain language — the AI captures the key points. You can skip any section or come back to edit later via the *Edit Profile* button.

**4. Start coaching** — the coach is ready. Ask anything:

> *"How is my training going?"*
> *"Give me a plan for next week."*
> *"Why am I not improving my 5K time?"*

---

## 📸 Screenshots

> Screenshots coming soon.

---

## 📝 Private notes

You can give the coach extra context about specific sessions by adding notes to any Strava activity's **private notes** field. Wrap the coaching-relevant part in `$...$`:

```
$5x1km VO2max session @4:30 — felt very hard, knee a bit sore on the last rep$
```

The coach picks this up automatically. Anything outside the `$...$` markers is ignored, so your personal notes stay private.

---

## 🧑‍💻 Development

```bash
uv sync --group dev   # install with dev dependencies
pytest                # run tests
ruff check .          # lint
ruff format .         # format
mypy .                # type-check
```
