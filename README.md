# 🏃 Coach

An AI-powered training coach that provides personalized coaching advice based on your Strava activity data. The coach analyzes your recent training history and engages in interactive conversations to help you achieve your training goals.

## ✨ Features

- **🔗 Strava Integration**: Automatically sync your activities from Strava
- **🤖 AI-Powered Analysis**: Get intelligent insights about your training based on your recent activities, personal bests and training profile
- **💬 Interactive Chat**: Have follow-up conversations with your coach for detailed guidance
- **🎯 Personalized Goals**: Customize your training goals, constraints, and preferences
- **📝 Private Notes Integration**: Extract contextual information from Strava private notes using `$...$` delimiters

## 📋 Prerequisites

- Python 3.10+
- Strava account and API credentials
- OpenAI API key

## 🚀 Setup

1. **Install dependencies**:
   ```bash
   pip install -e .
   ```

2. **Configure environment variables**:

   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

   Required variables:
   - `STRAVA_CLIENT_ID`: Your Strava application client ID
   - `STRAVA_CLIENT_SECRET`: Your Strava application client secret
   - `STRAVA_REFRESH_TOKEN`: Your Strava refresh token
   - `OPENAI_API_KEY`: Your OpenAI API key

3. **Personalize your coaching profile**:

   Copy `coach/config/coach.md.example` to `coach/config/coach.md` and customize it:
   ```bash
   cp coach/config/coach.md.example coach/config/coach.md
   ```

   Edit `coach/config/coach.md` to set your training goals, constraints, and preferences. This file is used by the AI coach to provide personalized advice tailored to your objectives.

## 💻 Usage

### Available Commands

The application provides two main command groups:

#### 🔄 Sync Commands

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

#### 💭 Chat Commands

Start an interactive coaching session:

```bash
coach chat
```

**Options**:
- `--model`: Specify the OpenAI model to use (default: `gpt-5-nano`)
- `--num-history-weeks`: Number of weeks to include in the training state analysis (default: `2`)

Example with a specific model and extended history:
```bash
coach chat --model gpt-4o --num-history-weeks 4
```

The coach will:
1. Build training state from recent weeks (specified by `--num-history-weeks` parameter)
2. Analyze your training state on the first question
3. Provide structured feedback with summary, observations, recommendations, and confidence notes
4. Continue the conversation with follow-up questions in a natural chat format

**Note**: Weeks are indexed from Monday and the current week is always included in the analysis.

### Typical Workflow

1. **First time setup**:
   ```bash
   coach sync strava
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

## ⚙️ Personalization

### Training Instructions, Goals and Preferences

Create your personal `coach/config/coach.md` from the example template and customize:

- **Personal history and details**: Personal information, lifestyle, training experience, etc.
- **Constraints**: Training frequency, preferred workout times, weekly long run schedule
- **Preferences**: Workout variety, intensity focus, training style
- **Goals**: Specific goals you want to achieve. The format of individual goals is specified by the template and is not to be changed. Not all fields need to be present for all goals though.

The AI coach uses this information to provide advice aligned with your specific situation and goals.

*Note: Keep the **Goals** section at the bottom and do not change its name to maintain correct parsing.*

### Example Configuration

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
- Biggest struggle is ...

### Constraints:
- Maximum of 4–5 training days per week
- Prefer evening workouts
- Long run on weekends, not on weekdays
- Stay injury-free
- Maintain strength training at least once per week

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

- Bench 120 kg
    - Sport: WeightTraining
    - Goal date: N/A
```

## 💾 Data Storage

Activities are stored in a local SQLite database (`coach.db`) in the project directory. This allows for quick analysis without repeatedly calling the Strava API.

## 📝 Using Private Notes

You can provide additional context to the coach by adding information to your Strava activity private notes. To ensure the coach analyzes specific portions of your notes, wrap them between dollar signs (`$...$`).

### Example

In your Strava activity private notes, you can write:

```
$VO2 max 5x1 @4:30 1:30 in between session, felt extremely hard, especially the last lap$
```

The coach will extract this information and use it to provide more accurate analysis and recommendations. Anything outside the dollar signs will be ignored, allowing you to keep personal notes separate from coaching-relevant information.
