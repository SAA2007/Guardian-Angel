"""Guardian Angel -- FastAPI Server

Factory function that creates the FastAPI app with all
routes, CORS, and lifecycle hooks wired up.

Usage:
    app = create_app(supervisor, shared_state,
                     config_manager, stats_manager)
    uvicorn.run(app, host="localhost", port=8421)
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import router


def _project_root():
    """Return the absolute project root path."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def create_app(supervisor, shared_state, config_manager,
               stats_manager):
    """Create and configure the FastAPI application.

    Args:
        supervisor: ProcessSupervisor instance.
        shared_state: SharedState instance.
        config_manager: ConfigManager instance.
        stats_manager: StatsManager instance.

    Returns:
        FastAPI: configured application.
    """
    app = FastAPI(
        title="Guardian Angel API",
        version="0.1.0",
        description=(
            "Backend API for Guardian Angel NSFW content filter."
        ),
    )

    # ── CORS ────────────────────────────────────────────────
    # Allow React frontend on localhost:8422
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8422",
            "http://127.0.0.1:8422",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Wire dependencies via app.state ─────────────────────
    app.state.supervisor = supervisor
    app.state.shared_state = shared_state
    app.state.config_manager = config_manager
    app.state.stats_manager = stats_manager

    # ── Include routes ──────────────────────────────────────
    app.include_router(router)

    # ── Static files (assets/ for angel art PNGs) ───────────
    assets_dir = os.path.join(_project_root(), "assets")
    if os.path.isdir(assets_dir):
        app.mount(
            "/assets",
            StaticFiles(directory=assets_dir),
            name="assets",
        )

    # ── Lifecycle hooks ─────────────────────────────────────

    @app.on_event("startup")
    def on_startup():
        """Record session start on server boot."""
        stats_manager.record_session_start()

    @app.on_event("shutdown")
    def on_shutdown():
        """Record session end on server shutdown."""
        stats_manager.record_session_end()

    return app
