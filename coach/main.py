import typer

from coach.cli.app import app as cli_app
from coach.config.logging import configure_logging

configure_logging()

app = typer.Typer()
app.add_typer(cli_app)

if __name__ == "__main__":
    app()

SAMPLE_PIPELINE = """
if __name__ == "__main__":
    load_strava_settings()

    client = StravaClient()
    mapper = StravaMapper()
    db = Database('coach.db')

    activity_repo = SQLiteActivityRepository(db)
    activities = [mapper.map_strava_activity(raw_activity) for raw_activity in client.list_activities()]
    activity_repo.save_many(activities)

    state_repo = SQLiteTrainingStateRepository(db)
    current_state = build_training_state(
        activities=activities,
        window_start=date(2025, 1, 1),
        window_end=date(2026, 1, 1),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    state_repo.save(current_state)

    llm_client = OpenAILLMClient(model='gpt-5-nano')
    reasoner = LLMCoachReasoner(llm_client)

    reasoner.reason(training_state=current_state, user_prompt='Provide me with workout plan for the upcoming week')
"""
