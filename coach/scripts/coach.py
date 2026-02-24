from datetime import UTC
from datetime import datetime
from typing import Optional

import typer

from coach.builders.personal_bests import build_running_personal_bests_summary
from coach.builders.recent_training_history import build_recent_training_history
from coach.domain.chat import ChatHistory
from coach.domain.chat import ChatTurn
from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteActivityRepository
from coach.reasoning.adapter import LLMCoachReasoner
from coach.reasoning.clients import OpenAILLMClient

coach_app = typer.Typer(help='Coach reasoning commands')


class Coach:
    def __init__(self, model: str, num_history_weeks: int) -> None:
        self._model = model

        self._db = Database('coach.db')
        self._activity_repo = SQLiteActivityRepository(self._db)

        all_activities = self._activity_repo.list_all()

        self._recent_training_history = build_recent_training_history(
            activities=all_activities,
            generated_at=datetime.now(tz=UTC),
            num_history_weeks=num_history_weeks,
        )

        self._pbs = build_running_personal_bests_summary(activities=all_activities)

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
        chat_history = None if self._history.has_no_coach_response() else self._history.render()
        coach_response = self._reasoner.chat(running_pbs=self._pbs, recent_training_history=self._recent_training_history, user_prompt=user_input, chat_history=chat_history)
        self._history.add(ChatTurn(role='coach', content=coach_response))
        return coach_response


@coach_app.callback(invoke_without_command=True)
def chat_callback(
        ctx: typer.Context,
        model: str = typer.Option(default='gpt-5-nano', help='Open AI model'),
        num_history_weeks: int = typer.Option(
            default=2,
            help='Number of weeks used to build a summary of the current training state. Weeks are indexed from monday and the current week is always included.',
        ),
) -> None:
    coach = Coach(model=model, num_history_weeks=num_history_weeks)
    ctx.obj = coach

    if ctx.invoked_subcommand is None:
        coach.run_chat_loop()
