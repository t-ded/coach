from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from coach.builders.personal_bests import build_running_personal_bests_summary
from coach.builders.recent_training_history import build_recent_training_history
from coach.domain.profile import UserProfile
from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteActivityRepository
from coach.reasoning.assistant import Assistant
from coach.reasoning.assistant import _extend_parts
from coach.reasoning.assistant import load_user_system_prompt
from coach.reasoning.coach.context import render_recent_training_history
from coach.reasoning.coach.context import render_running_pbs
from coach.reasoning.coach.context import render_system_prompt
from coach.reasoning.providers import LLMProvider
from coach.utils import parse_file


class Coach(Assistant):
    def __init__(self, provider: LLMProvider, model: Optional[str], num_history_weeks: int) -> None:
        super().__init__(provider=provider, model=model)

        db = Database('coach.db')
        activity_repo = SQLiteActivityRepository(db)
        all_activities = activity_repo.list_all()

        pb_summary = build_running_personal_bests_summary(activities=all_activities)
        recent_training_history = build_recent_training_history(
            activities=all_activities,
            generated_at=datetime.now(tz=UTC),
            num_history_weeks=num_history_weeks,
        )

        self._rendered_pbs = render_running_pbs(pb_summary).strip()
        self._rendered_recent_training_history = render_recent_training_history(recent_training_history).strip()
        self._coach_profile: Optional[str] = render_system_prompt(parse_file(Path('coach/config/coach.md')))

    def run_chat_loop(self) -> None:
        typer.echo('Coach ready. Type your responses (Ctrl+C to exit).\n')
        while True:
            try:
                user_input = typer.prompt('You')
            except (EOFError, KeyboardInterrupt):
                typer.echo('\nGoodbye.')
                break
            typer.echo('\nCoach:\n')
            typer.echo(self._get_response(user_input))
            typer.echo('')

    def _user_system_prompt(self) -> Optional[str]:
        # TODO: Load from UserProfileRepository once persistence is in place
        return load_user_system_prompt(UserProfile.mock())

    def _additional_context(self) -> Optional[str]:
        parts: list[str] = []
        _extend_parts(parts, 'User instructions and goals:', self._coach_profile)
        _extend_parts(parts, 'Recent weeks training context:', self._rendered_recent_training_history)
        _extend_parts(parts, 'Running PBs:', self._rendered_pbs)
        return '\n'.join(parts)

    def _system_prompt(self) -> str:
        return """
You are an AI training coach.

You are given an explicit training summary.
All numeric values are already computed and correct.

Hard Constraints:
- Do NOT recalculate distances, durations, totals, or derived metrics.
- Do NOT infer missing data - base all observations strictly on the provided information.
- Do NOT invent activities, sessions, or metrics.
- If information is insufficient to support a claim, state that explicitly.
- Do NOT unnecessarily restate your instructions in your response - only where absolutely necessary to support your statement.

You MAY:
- Apply general training principles and best practices.
- Propose workout structure and specific routines.
- Recommend short-term and long-term progression strategies.
- Extend recommendations beyond current training volume, provided they are logically grounded in the data and in known research.

Your responsibilities:
- Guide the user toward their stated goal(s) based on their current fitness.
- Evaluate observed training patterns.
- Highlight notable observations or potential risks.
- Suggest high-level focus areas where relevant.
- Remain objective and avoid unsupported assumptions.
- Apply general training principles and best practices such as progressive overload (instead of jumping from 2 runs per week to 4), polarized training etc.
"""
