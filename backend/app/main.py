"""FastAPI application factory."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routes import (
    evaluate,
    languages,
    meetings,
    notes,
    settings as settings_route,
    transcript,
    translate,
    vocabulary,
)
from .services.transcription import TranscriptionService


def create_app(engine=None, diarizer=None, init_on_startup: bool = True) -> FastAPI:
    app = FastAPI(title="Multilingual Meeting Transcription", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.transcription_service = TranscriptionService(engine, diarizer)

    if init_on_startup:

        @app.on_event("startup")
        def on_startup() -> None:
            init_db()

    for router in (
        languages.router,
        meetings.router,
        transcript.router,
        notes.router,
        translate.router,
        vocabulary.router,
        settings_route.router,
        evaluate.router,
    ):
        app.include_router(router, prefix="/api")

    # Serve the frontend (repo_root/frontend) at "/".
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    return app


app = create_app()
