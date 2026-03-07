# 🏃 Coach

An AI-powered training coach that provides **personalized coaching advice** based on your Strava activity data. The coach analyzes your recent training history and engages in interactive conversations to help you achieve your training goals.

It integrates even with a **free Strava account** and by default uses Google AI studio to provide **free LLM chat integration**.

<details>
<summary>💬 Example Session</summary>

```
coach sync strava
coach chat --num-history-weeks=8
```

```
You: How is my training going? Give me a plan for the upcoming week.

Coach: 
How your training is going (brief):
- Solid overall consistency: regular running with recent interval work and a mix of easy and longer runs. 
- You’ve shown good ability to handle VO2-style work (5x1k at around 4:15/km in the recent window) and you’ve built longer endurance without major stalls.
- Some recurring risk signals to watch: knee sensitivity on downhills and GI issues during hard or long efforts. These will respond best to careful pacing, solid warmups, and mindful fueling/recovery. Strength work has supported stability, but shoulder/knee load should remain controlled if any pain flares.
- Your current fitness shows speed and endurance potential toward the half and the 5K goals, but the HM target pace (about 4:58/km) will require steady progression and careful recovery to stay healthy.

Plan for the upcoming week (5 training days, evenings, long run on weekend, stay injury-free)
- Thursday: Easy run + strides
  - 40–50 minutes easy pace
  - Finish with 6 x 20-second strides (built-in accelerations, relaxed breathing)
  - Rationale: maintains aerobic base, reinforces running form without overloading knees.

- Friday: Strength training (full body with knee-friendly emphasis)
  - 50–60 minutes
  - Core post-work and posterior-chain emphasis (examples: hip hinge work like Romanian deadlifts or hip thrusts, glute bridges, step-ups or lunges with light load, upper-body work as tolerated)
  - Keep loads moderate and technique solid; avoid high-impact jumping if knees feel off.
  - Rationale: preserves strength and joint stability with lower knee risk while you maintain training frequency.

- Saturday: Tempo/threshold run (shorter tempo block)
  - 15–20 minute easy warm-up
  - 3–5 km at tempo/threshold effort (roughly 5:10–5:25 per km depending on how you feel)
  - 5–10 minute cooldown
  - Rationale: reinforces HM-specific pace tolerance without pushing you into a long, high-stress run.

- Sunday: Long run (easy to moderate)
  - 75–95 minutes at an easy to steady pace (target breathing comfortable, generally ~5:20–5:40/km depending on how you feel)
  - Optional: finish last 5–10 minutes with gentle pickups if you feel good (not mandatory)
  - Rationale: builds aerobic base and endurance with a comfortable stimulus to avoid GI or knee overload.

- Tuesday: Intervals (your high-intensity work for the week)
  - 15–20 minute easy warm-up
  - 5 x 1 km @ ~4:15/km with 90 seconds easy jog between repetitions
  - 10 minute cooldown
  - Rationale: maintains VO2 efficiency and speed, aligns with your recent interval work, while the easy jogs help recovery.

Notes and practical tips
- GI and fueling: to help bowel comfort during hard sessions, consider keeping meals 2–3 hours before workouts, or adjust timing/fiber load on training days. Practice fueling plans (gel, drink, snacks) during long-ish days to find what works for you.
- Knee care: keep warm, use a soft surface when possible, and include a brief dynamic warm-up before runs. If downhills irritate knees, reduce downhill volume or substitute with flatter routes temporarily.
- Progression guardrails: if you feel unusually fatigued or notice knee flare, swap a tempo day for an easy run and reduce the long run by ~10–15 minutes that week. Look for a smooth, steady buildup rather than big jumps.
- Strength strategy: aim to maintain at least 1 strength session weekly; if you can add a second brief session every other week, that can help with injury prevention and running economy, as long as it doesn’t spike overall fatigue.
- 12-week context: this week emphasizes a mix of easy, tempo, and interval work with a weekend long run, which is a sensible structure while moving toward HM peak. In the weeks ahead, you’ll generally want to keep 1 tempo/threshold week, 1 interval week, and 1 longer endurance week with conservative increases, then taper appropriately for the May target.

If you’d like, I can tailor exact paces, distances, and session timings to match your actual weekly schedule, preferred training days, and how your knee and GI symptoms respond over the next couple of weeks. Also tell me if you want me to include a brief, progressive HM-specific build (e.g., a focused 4–6 week HM progression) after this upcoming week.


You: Why did you go for a long run on Sunday?

Coach: [RESPONSE HERE]
```
</details>

---

## ✨ Features

- **🔗 Strava Integration**: Automatically sync your activities from Strava (even with a free account!)
- **🤖 AI-Powered Analysis**: Get intelligent insights about your training based on your recent activities, personal bests, and training profile
- **💬 Interactive Chat**: Have follow-up conversations with your coach for detailed guidance
- **🎯 Personalized Goals**: Customize and prioritize your training goals, constraints, and preferences
- **📝 Easily Access Summary**: Get a quick breakdown of training history and personal bests with a single command
- **🏃 Private Notes Integration**: Extract contextual information from Strava private notes using `$...$` delimiters

---

## 📋 Prerequisites

- Python 3.10+
- Strava account (free)
- Google account (for Google AI Studio - free tier available)

**Optional:**
- OpenAI API key (Optional - only for OpenAI integration)

---

## 🚀 Setup

### Quick Start (Recommended)

1. **Install dependencies**:
   ```bash
   pip install -e .
   ```
<br>

2. **Run the authentication setup**:
   ```bash
   coach auth setup
   ```

   This interactive command will:
   - Open your browser to authorize Strava
   - Open your browser to get a free Google AI API key
   - Optionally, open your browser to get OpenAI API key (free but credits are then required for the use of OpenAI models)
   - Store credentials securely in `~/.coach/credentials.json`

<br>

3. **Personalize your coaching profile**:

   Copy `coach/config/coach.md.example` to `coach/config/coach.md` and customize it:
   ```bash
   cp coach/config/coach.md.example coach/config/coach.md
   ```

   Edit `coach/config/coach.md` to set your training goals, constraints, and preferences. This file is used by the AI coach to provide personalized advice tailored to you.

### Authentication Commands

- `coach auth setup` - Interactive setup for all credentials
- `coach auth strava` - Setup/reconfigure Strava only
- `coach auth google` - Setup/reconfigure Google AI only
- `coach auth openai` - Setup/reconfigure OpenAI only
- `coach auth status` - Check which credentials are configured

---

## 💻 Usage

### Available Commands

The application provides three main command groups:

<details>
<summary>🔄 Sync Commands</summary>

Sync your activities from Strava to the local database:

```bash
coach sync strava
```

This fetches all your activities from Strava and stores them locally for analysis.

**Options**:
- `--fresh`: Remove all existing entries from the database and re-ingest all activities

Example for a fresh sync:
```bash
coach sync strava --fresh
```

</details>

<details>
<summary>📝 Info Commands</summary>

Get a summary of the training history stored in the database.

```bash
coach info <option_1> <option_2> ...
```

**Options**:
- `--pbs`: Get summary of running personal bests (note that a Strava sync should always precede this)

Example for a summary with running personal bests:
```bash
coach info --pbs
```

</details>

<details>
<summary>💭 Chat Commands</summary>

Start an interactive coaching session:

```bash
coach chat
```

**Options**:
- `--provider`: LLM provider to use: `google` (default) or `openai`
- `--model`: Model name (uses provider default if not specified)
  - Google default: `gemini-2.5-flash`
  - OpenAI default: `gpt-5-nano`
- `--num-history-weeks`: Number of weeks to include in the training state analysis (default: `2`)

Example with default Google AI provider:
```bash
coach chat --num-history-weeks 4
```

Example with OpenAI provider and specific model:
```bash
coach chat --provider openai --model gpt-4o --num-history-weeks 4
```

The coach will:
1. Build training state from recent weeks (specified by `--num-history-weeks` parameter)
2. Analyze your training state on the first question
3. Provide structured feedback with summary, observations, recommendations, and confidence notes
4. Continue the conversation with follow-up questions in a natural chat format

**Note**: Weeks are indexed from Monday and the current week is always included in the analysis.

</details>

### Typical Workflow

1. **First time setup**:
   ```bash
   coach auth setup    # Authenticate with Strava and Google AI
   coach sync strava   # Sync your activities
   ```

2. **Get coaching advice**:
   ```bash
   coach chat
   ```

   Example conversation:
   ```
   You: How is my training going? Give me a plan for the upcoming week.
   Coach: [Provides analysis of your recent training and answers the question]

   You: Why did you go for a long run on day 5?
   Coach: [Gives personalized answer given the available chat history]
   ```

3. **Regular updates**: Run `coach sync strava` periodically to keep your data up to date.
4. **Measure progress:** Run `coach info --pbs` to get a summary of personal bests.

---

## 📝 Using Private Notes

You can provide additional context to the coach by adding information to your Strava activity private notes. To ensure the coach analyzes specific portions of your notes, wrap them between dollar signs (`$...$`).

### Example

In your Strava activity private notes, you can write:

```
$VO2 max 5x1 @4:30 1:30 in between session, felt extremely hard, especially the last lap$
```

The coach will extract this information and use it to provide more accurate analysis and recommendations. Anything outside the dollar signs will be ignored, allowing you to keep personal notes separate from coaching-relevant information.

---

## ⚙️ Personalization

### Training Instructions, Goals, and Preferences

Create your personal `coach/config/coach.md` from the example template and customize:

- **Personal history and details**: Personal information, lifestyle, training experience, etc.
- **Constraints**: Training frequency, preferred workout times, weekly long run schedule
- **Preferences**: Workout variety, intensity focus, training style
- **Goals**: Specific goals you want to achieve. The format of individual goals is specified by the template and is not to be changed. Not all fields need to be present for all goals, though.

The AI coach uses this information to provide advice aligned with your specific situation and goals.

*Note: Keep the **Goals** section at the bottom and do not change its name to maintain correct parsing.*

<details>
<summary>⚙️ Example Configuration</summary>

```markdown
# Training Instructions

### Personal history and details:
- Age, weight, height
- Started running in ..., weight lifting in ..., now mostly ...
- Competitive ... from X years old (used to 4+ training sessions a week, camps on weekends and heavy camps with daily multiphase trainings)
- Struggled with knee pain and shin splints during the peak of my first running summer in 2025
    - Up and especially down hills triggered both a lot
    - High quality warmup before and stretching after helped a lot (also keeping my knees warm in colder weather)
- Work as a ..., spending most of my day ...
- Typical diet ...
- The biggest struggle is ...
- No need to overly focus or mention any of the above in the response, just to give context

### Constraints:
- Maximum of 4–5 training days per week
- Prefer evening workouts
- Long run on weekends, not on weekdays
- Stay injury-free
- Maintain strength training at least once per week
- Concise answer, not unnecessarily wordy (avoid restating instructions)
    - If summarizing current state and recent training history, do so briefly

### Preferences:
- Strong variety in workout types
- Focus on heavy workouts (VO2 Max intervals, tempo/threshold runs, etc.)

### Goals:
- Sub20 5K
    - Sport: Run
    - Goal date: 2026-06-30
    - Distance: 5 km
    - Total duration: 00:20:00
    - Notes: Would like to try for the PB before the race so that I go into the race knowing I can make it
    - Priority: Very high

- Bench 120 kg
    - Sport: WeightTraining
    - Goal date: N/A
    - Priority: low
```

</details>

---

## 💾 Data Storage

Activities are stored in a local SQLite database (`coach.db`) in the project directory. This allows for quick analysis without repeatedly calling the Strava API.
