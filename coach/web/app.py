from fastapi import FastAPI

from coach.web.strava_oauth import router


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


app = create_app()
