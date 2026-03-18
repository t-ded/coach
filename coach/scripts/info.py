import typer

from coach.builders.personal_bests import build_running_personal_bests_summary
from coach.persistence.supabase.repositories.activities import SupabaseActivityRepository
from coach.persistence.supabase.session import load_session
from coach.reasoning.coach.context import render_running_pbs

info_app = typer.Typer(help='Activity history information')


@info_app.callback(invoke_without_command=True)
def info_callback(pbs: bool = typer.Option(False, help='Summarize running personal bests within the stored data')) -> None:
    session = load_session()
    activity_repo = SupabaseActivityRepository(session.client, session.user_id)
    all_activities = activity_repo.list_all()

    if pbs:
        pbs_summary = build_running_personal_bests_summary(activities=all_activities)
        typer.echo(render_running_pbs(pbs_summary))
