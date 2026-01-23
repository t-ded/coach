from datetime import UTC
from datetime import datetime
from datetime import timedelta

import typer

from coach.builders.training_state import build_training_state
from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteActivityRepository
from coach.reasoning.adapter import LLMCoachReasoner
from coach.reasoning.clients import OpenAILLMClient
from coach.reasoning.context import ChatHistory
from coach.reasoning.context import ChatTurn

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
    history = ChatHistory(max_turns=6)

    typer.echo('Coach ready. Type your questions (Ctrl+C to exit).\n')

    while True:
        try:
            user_input: str = typer.prompt('You')
        except (EOFError, KeyboardInterrupt):
            typer.echo('\nGoodbye.')
            break

        history.add(ChatTurn(role='user', content=user_input))

        response = reasoner.reason(
            training_state=last_week_state,
            user_prompt=user_input,
            chat_history=history.render()
        )

        coach_text = (
            f'Summary:\n{response.summary}\n\n'
            f'Observations:\n' + '\n'.join(f'- {o}' for o in response.observations) + '\n\n'
            'Recommendations:\n' + '\n'.join(f'- {r}' for r in response.recommendations) + '\n\n'
            f"Confidence Notes:\n{response.confidence_notes or 'None'}"
        )

        history.add(ChatTurn(role='coach', content=coach_text))

        typer.echo('\nCoach:\n')
        typer.echo(coach_text)
        typer.echo('')
