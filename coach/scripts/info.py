import typer

from coach.builders.personal_bests import build_running_personal_bests_summary
from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteActivityRepository
from coach.reasoning.context import render_running_pbs

info_app = typer.Typer(help='Activity history information')


@info_app.callback(invoke_without_command=True)
def info_callback(pbs: bool = typer.Option(False, help='Summarize running personal bests within the stored data')) -> None:
    db = Database('coach.db')
    activity_repo = SQLiteActivityRepository(db)

    all_activities = activity_repo.list_all()

    if pbs:
        pbs_summary = build_running_personal_bests_summary(activities=all_activities)
        typer.echo(render_running_pbs(pbs_summary))
