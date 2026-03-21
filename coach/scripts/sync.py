import typer

from coach.auth.strava_tokens import CredentialsStoreStravaTokenRepository
from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.sync import sync_strava_for_user
from coach.persistence.repositories.activities import SupabaseActivityRepository
from coach.persistence.session import load_session

sync_app = typer.Typer(help='Data ingestion commands')


@sync_app.command('strava')
def sync_strava(fresh: bool = typer.Option(False, help='Force a fresh sync')) -> None:
    session = load_session()
    token_repo = CredentialsStoreStravaTokenRepository()
    client = StravaClient(user_id=session.user_id, token_repo=token_repo)
    activity_repo = SupabaseActivityRepository(session.client, session.user_id)
    if fresh:
        typer.echo('Resetting activity history...')
    typer.echo('Syncing activities from Strava...')
    synced = sync_strava_for_user(client, activity_repo, fresh=fresh)
    typer.echo(f'Done. {synced} activities synced, {activity_repo.count()} total stored.')
