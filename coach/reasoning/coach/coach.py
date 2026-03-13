from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from coach.builders.personal_bests import build_running_personal_bests_summary
from coach.builders.recent_training_history import build_recent_training_history
from coach.domain.chat import ChatHistory
from coach.domain.chat import ChatTurn
from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteActivityRepository
from coach.reasoning.coach.context import render_recent_training_history
from coach.reasoning.coach.context import render_running_pbs
from coach.reasoning.coach.context import render_system_prompt
from coach.reasoning.coach.prompts import build_coach_prompt
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import create_llm_client
from coach.utils import parse_file


class Coach:
    def __init__(self, provider: LLMProvider, model: Optional[str], num_history_weeks: int) -> None:
        self._db = Database('coach.db')
        self._activity_repo = SQLiteActivityRepository(self._db)

        all_activities = self._activity_repo.list_all()

        self._recent_training_history = build_recent_training_history(
            activities=all_activities,
            generated_at=datetime.now(tz=UTC),
            num_history_weeks=num_history_weeks,
        )

        self._pbs = build_running_personal_bests_summary(activities=all_activities)

        self._llm_client = create_llm_client(provider=provider, model=model)
        self._rendered_system_prompt = render_system_prompt(parse_file(Path('coach/config/coach.md')))
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
        prompt = self._build_prompt(user_input)
        coach_response = self._llm_client.complete(prompt)
        self._history.add(ChatTurn(role='assistant', content=coach_response))
        return coach_response

    def _build_prompt(self, user_input: str) -> str:
        chat_history = None if self._history.has_no_assistant_response() else self._history.render()
        return build_coach_prompt(
            running_pbs=render_running_pbs(self._pbs),
            rendered_recent_training_history=render_recent_training_history(self._recent_training_history),
            user_prompt=user_input,
            rendered_system_prompt=self._rendered_system_prompt,
            chat_history=chat_history,
        )
