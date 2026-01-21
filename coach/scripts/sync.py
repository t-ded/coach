import typer

from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.mapper import StravaMapper
from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteActivityRepository

sync_app = typer.Typer(help='Data ingestion commands')


@sync_app.command('strava')
def sync_strava() -> None:
    client = StravaClient()
    mapper = StravaMapper()

    db = Database('coach.db')
    activity_repo = SQLiteActivityRepository(db)
    current_num_activities_in_db = activity_repo.count()

    typer.echo('Fetching activities from Strava...')
    activities = [mapper.map_strava_activity(raw_activity) for raw_activity in client.list_activities()]
    num_all_strava_activities = len(activities)

    typer.echo(f'Saving {num_all_strava_activities - current_num_activities_in_db} new activities to database...')
    activity_repo.save_many(activities)

    typer.echo(f'Synced {len(activities)} activities.')
