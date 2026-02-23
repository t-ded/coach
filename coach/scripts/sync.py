import typer

from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.mapper import StravaMapper
from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteActivityRepository

sync_app = typer.Typer(help='Data ingestion commands')


@sync_app.command('strava')
def sync_strava(fresh: bool = typer.Option(False, help='Force a fresh sync')) -> None:
    client = StravaClient()
    mapper = StravaMapper()

    db = Database('coach.db')
    activity_repo = SQLiteActivityRepository(db)
    if fresh:
        typer.echo('Dropping activities table...')
        activity_repo.reset_table()
    last_synced_activity_ts = activity_repo.last_activity_timestamp() or 0

    typer.echo('Fetching activities from Strava...')
    raw_unsynced_activities = list(client.list_activities(detailed=True, after=last_synced_activity_ts))
    unsynced_activities = mapper.map_activities(raw_unsynced_activities)

    typer.echo(f'Saving {len(unsynced_activities)} new activities to database...')
    activity_repo.save_many(unsynced_activities)

    typer.echo(f'{activity_repo.count()} total activities stored in the database.')
