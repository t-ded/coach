from typing import Optional

import typer

from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteUserProfileRepository
from coach.reasoning.profile_assistant.profile import ProfileAssistant
from coach.reasoning.providers import LLMProvider

profile_app = typer.Typer(help='User profile setup')


@profile_app.command('setup')
def setup_profile(
    provider: str = typer.Option(default='google', help='LLM provider (google (default) or openai)'),
    model: Optional[str] = typer.Option(default=None, help='Model name (uses provider default if not specified)'),
) -> None:
    db = Database('coach.db')
    profile_repo = SQLiteUserProfileRepository(db)

    llm_provider = LLMProvider(provider.lower())
    profile_assistant = ProfileAssistant(provider=llm_provider, model=model)
    profile = profile_assistant.setup_profile()

    typer.echo('Saving profile...')
    profile_repo.save(profile)
    typer.echo('Done.')


@profile_app.command('show')
def show_profile() -> None:
    db = Database('coach.db')
    profile_repo = SQLiteUserProfileRepository(db)
    profile = profile_repo.load()

    if profile is None:
        typer.echo('No profile found. Run `coach profile setup` first.')
        raise typer.Exit(1)

    typer.echo(profile)
