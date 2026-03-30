from datetime import UTC
from datetime import datetime
from typing import Optional

from coach.builders.personal_bests import build_running_personal_bests_summary
from coach.builders.recent_training_history import build_recent_training_history
from coach.domain.activity import Activity
from coach.domain.profile import UserProfile
from coach.reasoning.assistant import Assistant
from coach.reasoning.coach.context import build_coach_context
from coach.reasoning.providers import LLMProvider


class Coach(Assistant):
    def __init__(
        self,
        provider: LLMProvider,
        model: Optional[str],
        profile: Optional[UserProfile],
        activities: list[Activity],
        num_history_weeks: int,
        user_display_name: Optional[str] = None,
        api_key: Optional[str] = None,
        session_summary: Optional[str] = None,
        generated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(provider=provider, model=model, api_key=api_key)
        self._profile = profile
        self._first_name = user_display_name or 'Athlete'
        self._session_summary = session_summary
        effective_now = generated_at or datetime.now(tz=UTC)
        pb_summary = build_running_personal_bests_summary(activities=activities)
        recent_training_history = build_recent_training_history(
            activities=activities,
            generated_at=effective_now,
            num_history_weeks=num_history_weeks,
        )
        self._additional_context_attr = build_coach_context(
            profile=profile,
            recent_training_history=recent_training_history,
            pb_summary=pb_summary,
        )

    def _user_system_prompt(self) -> Optional[str]:
        return self._profile.chat_preferences if self._profile else None

    def _additional_context(self) -> Optional[str]:
        return self._additional_context_attr

    def _render_conversation_context(self) -> Optional[str]:
        in_session = super()._render_conversation_context()
        if not self._session_summary:
            return in_session
        summary = f'Summary of our previous conversation:\n{self._session_summary}'
        return f'{summary}\n\n{in_session}' if in_session else summary

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
