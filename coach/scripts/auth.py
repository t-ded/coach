import typer

from coach.auth.google import setup_google_ai_key
from coach.auth.openai import setup_openai_key
from coach.auth.setup.strava import setup_strava_oauth
from coach.auth.supabase_auth import setup_supabase_login
from coach.config.credentials import CredentialsStore
from coach.persistence.repositories.users import SupabaseUsersRepository
from coach.persistence.session import load_session

auth_app = typer.Typer(help='Authentication and setup commands')


def _add_already_configured_info(original_string: str, is_configured: bool, provider: str) -> str:
    if is_configured:
        return original_string + f' - already configured, please run "coach auth {provider}" to reconfigure'
    return original_string


@auth_app.command('setup')
def setup_all() -> None:
    store = CredentialsStore()
    has_supabase = store.has_supabase_session()
    has_strava = store.has_strava_credentials()
    has_google = store.has_google_credentials()
    has_openai = store.has_openai_credentials()
    has_ai = has_google or has_openai

    if has_supabase and has_strava and has_ai:
        typer.echo('✓ All required credentials configured!')
        typer.echo('\nTo reconfigure:')
        typer.echo('  coach auth login')
        typer.echo('  coach auth strava')
        typer.echo('  coach auth google')
        typer.echo('  coach auth openai')
        return

    typer.echo('=== Coach Authentication Setup ===\n')

    if has_supabase:
        typer.echo('[1/3] ✓ Already logged in')
    else:
        typer.echo('[1/3] Logging in...')
        setup_supabase_login()

    if has_strava:
        typer.echo('\n[2/3] ✓ Strava already configured')
    else:
        typer.echo('\n[2/3] Setting up Strava...')
        _setup_strava_and_save_user_id()

    typer.echo('\n[3/3] Setting up AI provider...')
    typer.echo('Coach uses an AI model to analyze your training - please select your desired integration.\n')
    typer.echo(_add_already_configured_info(original_string='  [1] Google AI Studio (free, recommended)', is_configured=has_google, provider='google'))
    typer.echo(_add_already_configured_info(original_string='  [2] OpenAI (requires credits)', is_configured=has_openai, provider='openai'))
    typer.echo('  [3] Both\n')

    choice = typer.prompt('Choose provider')

    if choice == '1':
        if not has_google:
            setup_google_ai_key()
    elif choice == '2':
        if not has_openai:
            setup_openai_key()
    elif choice == '3':
        if not has_google:
            setup_google_ai_key()
        if not has_openai:
            setup_openai_key()
    else:
        typer.echo('Invalid choice, skipping AI provider configuration')
        return

    typer.echo('\n' + '=' * 40)
    typer.echo('✓ Setup complete!')
    typer.echo('\nNext:')
    typer.echo('  coach sync strava  - Sync your activities')
    typer.echo('  coach chat         - Start chatting with your coach')


@auth_app.command('login')
def login() -> None:
    store = CredentialsStore()
    if store.has_supabase_session() and not typer.confirm('Already logged in. Re-authenticate?'):
        typer.echo('Cancelled.')
        return
    setup_supabase_login()


def _setup_strava_and_save_user_id() -> None:
    strava_user_id = setup_strava_oauth()
    session = load_session()
    SupabaseUsersRepository(session.client, session.user_id).set_strava_user_id(strava_user_id)


@auth_app.command('strava')
def setup_strava() -> None:
    store = CredentialsStore()
    if store.has_strava_credentials() and not typer.confirm('Reconfigure Strava?'):
        typer.echo('Cancelled.')
        return
    _setup_strava_and_save_user_id()


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
    typer.echo(f'{"✓" if store.has_supabase_session() else "✗"} Personal Profile Storage (Google)')
    typer.echo(f'{"✓" if store.has_strava_credentials() else "✗"} Strava')
    typer.echo(f'{"✓" if store.has_google_credentials() else "✗"} Google AI')
    typer.echo(f'{"✓" if store.has_openai_credentials() else "✗"} OpenAI')

    if not store.has_supabase_session() or not store.has_strava_credentials() or not (store.has_google_credentials() or store.has_openai_credentials()):
        typer.echo('\nRun "coach auth setup" to configure.')
