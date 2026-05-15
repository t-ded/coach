<div align="center">
  <img src="public/coach_icon_transparent.png" alt="Coach" width="180" style="display:block; margin-bottom: 0;" />
  <h1 style="margin-top: -15px;">Coach</h1>

  <p><strong>A personalized AI training coach that actually knows what you've been up to</strong></p>

  <p><em>Sign in with Google · Connect Strava · Chat with your coach</em></p>

  <p>
    <a href="https://coach-production-e0b4.up.railway.app/">
      <strong>Open Coach →</strong>
    </a>
  </p>
</div>

---

You know the drill — you copy your last few runs into ChatGPT, describe your goals, ask for advice, and get something pretty generic back. Next week you do it all over again. **Coach was built to fix exactly that.**

Coach lives in your browser and reads your Strava automatically. It knows your recent workouts, your personal bests, your goals, and how you like to be talked to. You just chat.
Click the button above, then start your stopwatch - you are most likely going to be **finished with the initial setup before the clock hits 3 minutes!**

---

## ⚡ Getting started

1. Open **[coach-production-e0b4.up.railway.app](https://coach-production-e0b4.up.railway.app/)**
2. Sign in with your Google account
3. Connect an AI provider key — see [Setting up your AI provider key](#-setting-up-your-ai-provider-key) below
4. Connect your Strava account — see [Connecting Strava](#-connecting-strava) below
5. Set up your profile *(optional but recommended — takes about 5-10 minutes)*
6. Start chatting

Your activities sync automatically at the start of each session, so the coach always has your latest training in view.

---

## 🎬 In action

<img src="public/first_look.png" alt="First look at Coach" />

> <details>
> <summary>More screenshots — coaching chat and profile editing</summary>
> 
> > <details>
> > <summary>Coaching examples</summary>
> > <img src="public/chat_example_1.png" alt="Coaching example - progress summary" />
> > <img src="public/chat_example_2.png" alt="Coaching example - training plan" />
> > </details>
> > 
> > <details>
> > <summary>Profile editing</summary>
> > <img src="public/edit_profile.png" alt="Profile editing" />
> > </details>
> 
> </details>

---

## 🔑 Setting up your AI provider key<a name="api-key-setup"></a>

Coach uses an AI language model to power the coaching conversation. You bring your own key — it stays encrypted in our database and we never have access to the raw key.

**Option A — Google AI Studio (recommended, free)**

Only a Google account is needed. No credit card, no paid subscription.

1. Go to **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)**
2. Sign in with your Google account
3. Click **Create API key**, then copy the key it generates
4. Back in Coach, click **Connect Google AI Studio** and paste the key

**Option B — OpenAI**

1. Go to **[platform.openai.com/api-keys](https://platform.openai.com/api-keys)**
2. Click **Create new secret key**, copy it
3. Back in Coach, click **Connect OpenAI** and paste the key

**Option C — Anthropic (Claude)**

1. Go to **[console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)**
2. Create a new key and copy it
3. Back in Coach, click **Connect Anthropic** and paste the key

**Security note:** your key is stored encrypted using Supabase Vault. The operator (whoever runs this Coach instance) never has access to your raw key — only you do.

You can manage your keys at any time using the **Manage AI Provider** button in the chat.

---

## 🔗 Connecting Strava

Connecting Strava lets Coach see your recent training — workouts, distances, heart rate, personal bests. It's a one-time step and uses the standard Strava authorisation flow.

1. After setting up your AI key, click **Connect Strava** in the chat
2. You'll be taken to the Strava website to authorise Coach
3. Once you approve, you're redirected back and the coach is ready to go

Coach only reads your activity data — it cannot post or modify anything on your Strava account. A free Strava account is all you need.

---

## ✨ What Coach can do

|                             |                                                                                                |
|-----------------------------|------------------------------------------------------------------------------------------------|
| 🔗 **Strava sync**          | Activities sync automatically each session — free Strava account supported                     |
| 💬 **AI chat**              | Ask follow-up questions, push back, explore — it's a dialogue, not a report               |
| 👤 **Personalized profile** | Guided setup across 5 sections so the coach understands who you are and what you're working toward |
| 🔐 **Google login**         | No account creation — sign in with your existing Google account                                |
| 📝 **Private notes**        | Annotate Strava activities with coaching context that only the AI sees                         |
| 📜 **Chat history**         | Sessions auto-save and you can resume past conversations — the coach gets a summary so it remembers what you discussed |

---

## 🧐 What Coach is — and what it isn't

Knowing where Coach fits (and where it doesn't) will help you get the most out of it.

### How it compares

|                                                           | **Garmin Coach / Insights** | **Strava / Runna**            | **ChatGPT / Claude directly**         | **Coach**                    |
|-----------------------------------------------------------|-----------------------------|-------------------------------|---------------------------------------|------------------------------|
| Automatically up-to-date with recent training             | ✅                          | ✅                            | ❌ you paste manually                  | ✅                            |
| You can provide any additional context to your activities | ❌                          | ❌                            | 🟡 you paste manually                 | ✅                            |
| Full back-and-forth coaching chat and advice on anything  | ❌                          | ❌                            | ✅                                     | ✅                            |
| Remembers your goals, preferences and past conversations  | 🟡 very limited             | ✅ goals & training plan      | 🟡 per session + system prompt        | ✅                            |
| Free                                                      | ❌ needs Garmin              | ❌                            | ✅                                     | ✅                            |
| Semi-professional plan building                           | ✅                          | ✅                            | ❌                                     | ❌                            |
| Full body data integration (HR, sleep, stress etc.)       | ✅                          | 🟡 via Strava sync            | 🟡 you give context manually          | 🟡 you give context manually |

**The short version:** Garmin and Strava / Runna are great at what they do — tracking, community, and structured plan building. ChatGPT is a brilliant conversationalist - can give advice not only on the next run, but also on nutrition and how that stressful Friday meeting affects your training. But it knows nothing about your actual training unless you tell it.

**Coach combines both**: the AI conversation quality of a frontier model with the training context that only Strava has. **Use them all — they complement each other!**

---

## 🗺 What's next

A rough picture of what's coming:

- **❤️ Heart rate analysis** — deeper use of HR data for load, recovery, and aerobic fitness signals
- **📊 Better statistics** — richer summaries for you and more structured context for the coach
- **🚴 More activity types** — cycling, swimming, and other sports - all are supported, but running has richer features
- **🇺🇸 Improved unit support** — but you can always try forcing Coach to measure progress in football fields via profile settings  

---

## 👤 Your profile

Your profile is what makes coaching genuinely personal rather than generic. After connecting Strava, you'll be guided through five short sections. Fill in as many or as few as you like — you can skip anything and come back to edit it all later via the **Edit Profile** button.

### 💬 Chat preferences
How do you want the coach to talk to you? Prefer concise and direct? Want it to be motivational and warm? Happy to read in another language? This is the place to say so.

### 🏃 Training preferences
What you actually enjoy — and what you can't stand — in training. Workout types, formats, recovery habits. This isn't about structuring your plan (the coach figures that out); it's about making sure advice lands in a way that suits how you like to train.

### 🧍 Personal background
Who you are as an athlete. Mention fitness history, sports background, current activity level, occupation or lifestyle factors that affect how much energy you have. Any health context you're comfortable sharing.

### 📅 Constraints
Your hard limits. How many days a week you can train, preferred time of day, any scheduling restrictions. The coach treats these as non-negotiable when suggesting sessions or weekly structure.

### 🎯 Goals
What you're actually working toward. For each goal, you'll describe the sport, the target (a time, a distance, a race), when you want to hit it, and how much it matters relative to everything else. Goals are parsed into structured data so the coach can reason about them precisely.

---

## 📝 Private notes

You can give the coach extra context about any session by adding a note to the **private notes** field on a Strava activity. Wrap the coaching-relevant part in `$...$`:

```
$5×1km VO2max session at 4:30 — felt very hard, knee slightly sore on the last rep$
```

The coach picks this up automatically. Anything outside the `$...$` markers is ignored, so your personal notes stay yours.

---

## ⚠️ Disclaimer

Coach is an AI assistant, not a certified running coach or medical professional. The advice it gives is based on your Strava data and what you tell it about yourself — it cannot see things like injuries, illness, or stress that you haven't shared. Use your own judgement, listen to your body, and consult a qualified professional for anything health-related. Training hard is great; training smart is better; both require you in the loop.

---

## 🔒 Data & Privacy

### What data Coach stores

| Data | Stored?         | Notes |
|------|-----------------|-------|
| Google account email and display name | Yes             | Used to identify your account |
| Strava activity data | Yes             | Synced at session start or via webhook |
| Your coaching chat messages | Yes             | Stored to power session history; does not include Strava social activity (comments, kudos) |
| Your coaching profile | Yes             | The profile you set up guides the AI |
| Private activity notes (`$...$`) | Yes             | Stored as part of your activity data |
| LLM API key | Yes - encrypted | Stored in Supabase Vault; never accessible in plaintext |
| Strava access and refresh tokens | Yes - encrypted | Stored in Supabase Vault; never accessible in plaintext |

Coach does not store payment information, health records, or any data beyond what is listed above.

### Read-only Strava access

Coach requests **read-only** permission (`activity:read_all`). It cannot create, edit, delete, or post anything to your Strava account. It can only read your activity history.

### Who can see your data

- **You**: you see your own activities and coaching chat history in the app.
- **The operator** (whoever runs this Coach instance) has access to your profile data, stored activities, and coaching chat messages via the Supabase dashboard. The operator cannot see your LLM API key or Strava tokens in plaintext - these are stored encrypted in Supabase Vault and are never logged. Always ensure that the website you are using matches the link provided at the top of this README.

### How your Strava data is used

Your Strava activity data is used **solely** to provide coaching context within Coach. It is not sold, shared with third parties, or used for advertising. Specifically:

- Activity data is passed to the AI model you have configured (e.g. OpenAI, Google Gemini, Anthropic Claude) in order to generate coaching responses. By using Coach you should be aware that this data leaves Coach and is processed by that third-party provider under their own terms of service and privacy policy.
- Activity data is not shared with any other third party.
- Activity data is not used to train models, build profiles for advertising, or for any purpose other than generating your coaching responses.

This use of Strava data is in line with the [Strava API Agreement](https://www.strava.com/legal/api).

### What happens when you disconnect Strava

When you disconnect Coach from [strava.com/settings/apps](https://www.strava.com/settings/apps), Strava sends a deauthorization event to Coach. Upon receiving it, Coach immediately and atomically:

1. Deletes your Strava tokens from Vault
2. Deletes all stored activity data
3. Clears the Strava connection from your account

This happens automatically - you do not need to take any action inside Coach and you have full control over your data.

---

## 🛠 For developers

> This section is for people who want to run their own instance or contribute to the codebase. If you're just here to use Coach, everything above is all you need.

### Prerequisites

- Python 3.13+
- A Supabase project with the required schema (see CLAUDE.md for SQL steps)
- A Strava API app (strava.com/settings/api)
- A Google Cloud OAuth client
- A Google AI Studio, OpenAI, or Anthropic API key

### Running locally

```bash
git clone https://github.com/t-ded/coach.git
cd coach
pip install -e .
cp .env.example .env   # fill in your credentials
chainlit run coach/web/chainlit_app.py
```

Open [http://localhost:8000](http://localhost:8000).

### Development commands

```bash
uv sync --group dev   # install with dev dependencies
pytest                # run tests
ruff check .          # lint
ruff format .         # format
mypy .                # type-check
```

### Deploying to Railway

The repository includes a `Dockerfile` and `railway.toml`. Connect the repo in Railway, set the required environment variables (see `.env.example`), and Railway builds and deploys automatically on every push to `master`.

Key env vars to set: `STRAVA_REDIRECT_URI`, `CHAINLIT_URL`, `OAUTH_GOOGLE_CLIENT_SECRET`, `STRAVA_CLIENT_SECRET`, `SUPABASE_SECRET_KEY`, `CHAINLIT_AUTH_SECRET`.
