import typer

from coach.auth.google import setup_google_ai_key
from coach.auth.openai import setup_openai_key
from coach.auth.setup.strava import setup_strava_oauth
from coach.config.credentials import CredentialsStore

auth_app = typer.Typer(help='Authentication and setup commands')


@auth_app.command('setup')
def setup_all() -> None:
    store = CredentialsStore()
    has_strava = store.has_strava_credentials()
    has_google = store.has_google_credentials()

    if has_strava and has_google:
        typer.echo('✓ All credentials configured!')
        typer.echo('\nTo reconfigure:')
        typer.echo('  coach auth strava')
        typer.echo('  coach auth google')
        return

    typer.echo('=== Coach Authentication Setup ===\n')

    if has_strava:
        typer.echo('[1/2] ✓ Strava already configured')
    else:
        typer.echo('[1/2] Setting up Strava...')
        setup_strava_oauth()

    if has_google:
        typer.echo('[2/2] ✓ Google AI already configured')
    else:
        typer.echo('\n[2/2] Setting up Google AI...')
        setup_google_ai_key()

    typer.echo('\n' + '=' * 40)
    typer.echo('✓ Setup complete!')
    typer.echo('\nNext:')
    typer.echo('  coach sync strava  - Sync activities')
    typer.echo('  coach chat         - Start chatting')


@auth_app.command('strava')
def setup_strava() -> None:
    store = CredentialsStore()
    if store.has_strava_credentials() and not typer.confirm('Reconfigure Strava?'):
        typer.echo('Cancelled.')
        return
    setup_strava_oauth()


@auth_app.command('google')
def setup_google() -> None:
    store = CredentialsStore()
    if store.has_google_credentials() and not typer.confirm('Reconfigure Google AI?'):
        typer.echo('Cancelled.')
        return
    setup_google_ai_key()


@auth_app.command('openai')
def setup_openai() -> None:
    store = CredentialsStore()
    if store.has_openai_credentials() and not typer.confirm('Reconfigure OpenAI?'):
        typer.echo('Cancelled.')
        return
    setup_openai_key()


@auth_app.command('status')
def check_status() -> None:
    store = CredentialsStore()
    typer.echo('Authentication Status:\n')
    typer.echo(f'{"✓" if store.has_strava_credentials() else "✗"} Strava')
    typer.echo(f'{"✓" if store.has_google_credentials() else "✗"} Google AI')
    typer.echo(f'{"✓" if store.has_openai_credentials() else "✗"} OpenAI')

    if not store.has_strava_credentials() or not store.has_google_credentials():
        typer.echo('\nRun "coach auth setup" to configure.')
