from fastapi import FastAPI

from coach.web.api_key_routes import router as api_key_router
from coach.web.strava_oauth import router as strava_router


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(strava_router)
    app.include_router(api_key_router)
    return app


app = create_app()
