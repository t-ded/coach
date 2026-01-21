import typer

from coach.scripts.coach import coach_app
from coach.scripts.sync import sync_app

app = typer.Typer(help='AI-powered training coach')

app.add_typer(sync_app, name='sync')
app.add_typer(coach_app, name='chat')


def main() -> None:
    app()


if __name__ == '__main__':
    main()
