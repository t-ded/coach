from typing import Optional

import typer

from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteUserProfileRepository
from coach.reasoning.coach.context import render_profile
from coach.reasoning.profile_assistant.profile import ProfileAssistant
from coach.reasoning.profile_assistant.system_prompts import ProfileParts
from coach.reasoning.providers import LLMProvider

profile_app = typer.Typer(help='Manage your coaching profile')

_SECTION_NAMES = {p.name.lower(): p for p in ProfileParts}
_SECTION_CHOICES = ', '.join(_SECTION_NAMES)


def _get_repo() -> SQLiteUserProfileRepository:
    return SQLiteUserProfileRepository(Database('coach.db'))


def _get_assistant(provider: str, model: Optional[str]) -> ProfileAssistant:
    return ProfileAssistant(provider=LLMProvider(provider.lower()), model=model)


@profile_app.command('setup')
def setup_profile(
    provider: str = typer.Option(default='google', help='LLM provider (google or openai)'),
    model: Optional[str] = typer.Option(default=None, help='Model name (uses provider default if omitted)'),
) -> None:
    repo = _get_repo()

    if repo.load() is not None:
        typer.confirm('A profile already exists. Overwrite it?', abort=True)

    profile = _get_assistant(provider, model).setup_profile()
    repo.save(profile)
    typer.echo('Profile saved.')


@profile_app.command('edit')
def edit_section(
    section: str = typer.Argument(help=f'Section to edit: {_SECTION_CHOICES}'),
    provider: str = typer.Option(default='google', help='LLM provider (google or openai)'),
    model: Optional[str] = typer.Option(default=None, help='Model name (uses provider default if omitted)'),
) -> None:
    part = _SECTION_NAMES.get(section.lower())
    if part is None:
        typer.echo(f'Unknown section "{section}". Choose from: {_SECTION_CHOICES}')
        raise typer.Exit(1)

    repo = _get_repo()
    profile = repo.load()
    if profile is None:
        typer.echo('No profile found. Run `coach profile setup` first.')
        raise typer.Exit(1)

    updated = _get_assistant(provider, model).edit_section(part, profile)
    repo.save(updated)
    typer.echo('Profile updated.')


@profile_app.command('show')
def show_profile() -> None:
    profile = _get_repo().load()
    if profile is None:
        typer.echo('No profile found. Run `coach profile setup` first.')
        raise typer.Exit(1)
    typer.echo(render_profile(profile))


@profile_app.command('reset')
def reset_profile() -> None:
    typer.confirm('This will permanently delete your profile. Continue?', abort=True)
    _get_repo().delete()
    typer.echo('Profile deleted.')
