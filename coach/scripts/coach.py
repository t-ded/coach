from typing import Optional

import typer

from coach.reasoning.coach.coach import Coach
from coach.reasoning.providers import LLMProvider

coach_app = typer.Typer(help='Coach reasoning commands')


@coach_app.callback(invoke_without_command=True)
def chat_callback(
        ctx: typer.Context,
        provider: str = typer.Option(default='google', help='LLM provider (google (default) or openai)'),
        model: Optional[str] = typer.Option(default=None, help='Model name (uses provider default if not specified)'),
        num_history_weeks: int = typer.Option(
            default=2,
            help='Number of weeks used to build a summary of the current training state. Weeks are indexed from monday and the current week is always included.',
        ),
) -> None:
    llm_provider = LLMProvider(provider.lower())
    coach = Coach(provider=llm_provider, model=model, num_history_weeks=num_history_weeks)
    ctx.obj = coach

    if ctx.invoked_subcommand is None:
        coach.run_chat_loop()
