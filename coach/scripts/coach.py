from datetime import UTC
from datetime import datetime
from datetime import timedelta

import typer

from coach.builders.training_state import build_training_state
from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteActivityRepository
from coach.reasoning.adapter import LLMCoachReasoner
from coach.reasoning.clients import OpenAILLMClient

coach_app = typer.Typer(help='Coach reasoning commands')


@coach_app.callback(invoke_without_command=True)
def chat(model: str = typer.Option('gpt-5-nano', help='Open AI model')) -> None:
    db = Database('coach.db')
    activity_repo = SQLiteActivityRepository(db)
    last_week_state = build_training_state(
        activities=activity_repo.list_all(),
        window_start=datetime.now(tz=UTC).date() - timedelta(days=7),
        window_end=datetime.now(tz=UTC).date(),
    )

    llm_client = OpenAILLMClient(model=model)
    reasoner = LLMCoachReasoner(llm_client)

    typer.echo('Coach ready. Type your questions (Ctrl+C to exit).\n')

    while True:
        try:
            user_input = typer.prompt('You')
        except (EOFError, KeyboardInterrupt):
            typer.echo('\nGoodbye.')
            break

        response = reasoner.reason(
            training_state=last_week_state,
            user_prompt=user_input,
        )

        typer.echo('\nCoach:\n')
        typer.echo(f'Summary:\n{response.summary}\n')

        typer.echo('Observations:')
        for obs in response.observations:
            typer.echo(f'- {obs}')

        typer.echo('\nRecommendations:')
        for rec in response.recommendations:
            typer.echo(f'- {rec}')

        typer.echo('\nConfidence Notes:')
        typer.echo(response.confidence_notes or 'None')
        typer.echo('')
