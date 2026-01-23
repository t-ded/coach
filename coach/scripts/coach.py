from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Optional

import typer

from coach.builders.training_state import build_training_state
from coach.domain.models import CoachResponse
from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteActivityRepository
from coach.reasoning.adapter import LLMCoachReasoner
from coach.reasoning.clients import OpenAILLMClient
from coach.reasoning.context import ChatHistory
from coach.reasoning.context import ChatTurn

coach_app = typer.Typer(help='Coach reasoning commands')


class Coach:
    def __init__(self, model: str) -> None:
        self._model = model

        self._db = Database('coach.db')
        self._activity_repo = SQLiteActivityRepository(self._db)

        self._last_week_state = build_training_state(
            activities=self._activity_repo.list_all(),
            window_start=datetime.now(tz=UTC).date() - timedelta(days=7),
            window_end=datetime.now(tz=UTC).date(),
        )

        self._llm_client = OpenAILLMClient(model=self._model)
        self._reasoner = LLMCoachReasoner(self._llm_client)
        self._history = ChatHistory(max_turns=6)

    def run_chat_loop(self) -> None:
        typer.echo('Coach ready. Type your questions (Ctrl+C to exit).\n')

        while True:
            user_input = self._get_user_input()
            if user_input is None:
                break
            coach_response = self._get_coach_response(user_input)

            typer.echo('\nCoach:\n')
            typer.echo(coach_response)
            typer.echo('')

    def _get_user_input(self) -> Optional[str]:
        try:
            user_input = typer.prompt('You')
            self._history.add(ChatTurn(role='user', content=user_input))
            return user_input
        except (EOFError, KeyboardInterrupt):
            typer.echo('\nGoodbye.')
            return None

    def _get_coach_response(self, user_input: str) -> str:
        coach_response = self._reasoner.reason(training_state=self._last_week_state, user_prompt=user_input)
        coach_text = self._format_response(coach_response)
        self._history.add(ChatTurn(role='coach', content=coach_text))
        return coach_text

    @staticmethod
    def _format_response(response: CoachResponse) -> str:
        return (
            f'Summary:\n{response.summary}\n\n'
            f'Observations:\n' + '\n'.join(f'- {o}' for o in response.observations) + '\n\n'
            'Recommendations:\n' + '\n'.join(f'- {r}' for r in response.recommendations) + '\n\n'
            f"Confidence Notes:\n{response.confidence_notes or 'None'}"
        )


@coach_app.callback(invoke_without_command=True)
def chat_callback(ctx: typer.Context, model: str = typer.Option('gpt-5-nano', help='Open AI model')) -> None:
    coach = Coach(model=model)
    ctx.obj = coach

    if ctx.invoked_subcommand is None:
        coach.run_chat_loop()
