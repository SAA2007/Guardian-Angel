"""Guardian Angel -- API Route Handlers

All FastAPI endpoint handlers.  Uses APIRouter so they
can be included into the main FastAPI app.

Dependencies (supervisor, config_manager, stats_manager,
shared_state) are accessed via request.app.state.
"""

import threading
import time
import traceback

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .models import (
    AudioStatusResponse,
    ConfigResponse,
    ConfigUpdateRequest,
    OverlayStatusResponse,
    StatsResponse,
    StatusResponse,
    TriggerRequest,
)

router = APIRouter()


# ── Helpers ─────────────────────────────────────────────────────

def _get_deps(request):
    """Extract dependencies from app.state.

    Returns:
        tuple: (supervisor, config_manager, stats_manager,
                shared_state)
    """
    state = request.app.state
    return (
        state.supervisor,
        state.config_manager,
        state.stats_manager,
        state.shared_state,
    )


def _error_response(msg, status_code=500):
    """Return a JSON error response.

    Args:
        msg: error message string.
        status_code: HTTP status code.

    Returns:
        JSONResponse: error response.
    """
    return JSONResponse(
        status_code=status_code,
        content={"error": str(msg)},
    )


# ── GET /status ─────────────────────────────────────────────────

@router.get("/status", response_model=StatusResponse)
def get_status(request: Request):
    """Return system status from supervisor."""
    try:
        supervisor, _, _, _ = _get_deps(request)
        status = supervisor.get_status()
        return StatusResponse(
            detection_alive=status.get("detection_alive", False),
            overlay_alive=status.get("overlay_alive", False),
            audio_alive=status.get("audio_alive", False),
            fps_actual=status.get("fps_actual", 0.0),
            detection_count=status.get("detection_count", 0),
            audio_trigger=status.get("audio_trigger", False),
            is_running=True,
        )
    except Exception as e:
        traceback.print_exc()
        return _error_response(e)


# ── GET /config ─────────────────────────────────────────────────

@router.get("/config", response_model=ConfigResponse)
def get_config(request: Request):
    """Return current configuration."""
    try:
        _, config_mgr, _, _ = _get_deps(request)
        cfg = config_mgr.get_all()
        return ConfigResponse(
            censor_style=cfg.get("censor", {}).get(
                "style", "guardian_angel"
            ),
            sensitivity=cfg.get("detection", {}).get(
                "sensitivity", 0.6
            ),
            fps_max=cfg.get("detection", {}).get("fps_max", 60),
            fps_min=cfg.get("detection", {}).get("fps_min", 2),
            fps_auto_drop=cfg.get("detection", {}).get(
                "fps_auto_drop", True
            ),
            audio_action=cfg.get("audio", {}).get(
                "mute_style", "silence"
            ),
            dev_mode=cfg.get("dev_mode", False),
        )
    except Exception as e:
        traceback.print_exc()
        return _error_response(e)


# ── PATCH /config ───────────────────────────────────────────────

@router.patch("/config", response_model=ConfigResponse)
def update_config(request: Request, body: ConfigUpdateRequest):
    """Update configuration with partial data."""
    try:
        _, config_mgr, _, _ = _get_deps(request)
        updates = {}

        if body.censor_style is not None:
            updates.setdefault("censor", {})["style"] = (
                body.censor_style
            )
        if body.sensitivity is not None:
            updates.setdefault("detection", {})["sensitivity"] = (
                body.sensitivity
            )
        if body.fps_max is not None:
            updates.setdefault("detection", {})["fps_max"] = (
                body.fps_max
            )
        if body.fps_min is not None:
            updates.setdefault("detection", {})["fps_min"] = (
                body.fps_min
            )
        if body.fps_auto_drop is not None:
            updates.setdefault("detection", {})["fps_auto_drop"] = (
                body.fps_auto_drop
            )
        if body.audio_action is not None:
            updates.setdefault("audio", {})["mute_style"] = (
                body.audio_action
            )
        if body.dev_mode is not None:
            updates["dev_mode"] = body.dev_mode

        if updates:
            config_mgr.update(updates)

        # Return updated config
        return get_config(request)

    except Exception as e:
        traceback.print_exc()
        return _error_response(e)


# ── GET /overlay ────────────────────────────────────────────────

@router.get("/overlay", response_model=OverlayStatusResponse)
def get_overlay(request: Request):
    """Return overlay status."""
    try:
        supervisor, config_mgr, _, shared_state = _get_deps(request)
        status = supervisor.get_status()
        boxes = shared_state.get_boxes()
        cfg = config_mgr.get_all()
        return OverlayStatusResponse(
            active=status.get("overlay_alive", False),
            box_count=len(boxes),
            censor_style=cfg.get("censor", {}).get(
                "style", "guardian_angel"
            ),
        )
    except Exception as e:
        traceback.print_exc()
        return _error_response(e)


# ── GET /audio ──────────────────────────────────────────────────

@router.get("/audio", response_model=AudioStatusResponse)
def get_audio(request: Request):
    """Return audio pipeline status."""
    try:
        supervisor, config_mgr, _, shared_state = _get_deps(request)
        status = supervisor.get_status()
        cfg = config_mgr.get_all()
        return AudioStatusResponse(
            active=status.get("audio_alive", False),
            trigger_count=status.get("detection_count", 0),
            audio_action=cfg.get("audio", {}).get(
                "mute_style", "silence"
            ),
        )
    except Exception as e:
        traceback.print_exc()
        return _error_response(e)


# ── GET /stats ──────────────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse)
def get_stats(request: Request):
    """Return combined session + cumulative stats."""
    try:
        _, _, stats_mgr, _ = _get_deps(request)
        combined = stats_mgr.get_combined()
        return StatsResponse(**combined)
    except Exception as e:
        traceback.print_exc()
        return _error_response(e)


# ── POST /stats/trigger ────────────────────────────────────────

@router.post("/stats/trigger")
def record_trigger(request: Request, body: TriggerRequest):
    """Record a trigger event."""
    try:
        _, _, stats_mgr, _ = _get_deps(request)
        trigger_type = body.type
        if trigger_type not in ("video", "audio"):
            return _error_response(
                "type must be 'video' or 'audio'", 400
            )
        stats_mgr.record_trigger(trigger_type)
        return {"ok": True}
    except Exception as e:
        traceback.print_exc()
        return _error_response(e)


# ── GET /telemetry ──────────────────────────────────────────────

@router.get("/telemetry")
def get_telemetry(request: Request):
    """Return telemetry payload (dev_mode only)."""
    try:
        _, config_mgr, _, _ = _get_deps(request)
        cfg = config_mgr.get_all()
        if not cfg.get("dev_mode", False):
            return {"enabled": False}

        return {
            "enabled": True,
            "uuid": cfg.get("telemetry", {}).get(
                "user_id_anonymous", ""
            ) or "",
            "trigger_count": cfg.get("stats", {}).get(
                "total_triggers_video", 0
            ),
            "fps_avg": 0.0,
            "errors": [],
            "version": cfg.get("app_version", "0.1.0"),
        }
    except Exception as e:
        traceback.print_exc()
        return _error_response(e)


# ── POST /quit ──────────────────────────────────────────────────

@router.post("/quit")
def quit_app(request: Request):
    """Stop all processes and shut down the server."""
    try:
        supervisor, _, stats_mgr, _ = _get_deps(request)

        # Record session end for stats
        try:
            stats_mgr.record_session_end()
        except Exception:
            pass

        # Stop supervisor in a background thread so the
        # response can be sent first
        def _shutdown():
            time.sleep(1.0)
            supervisor.stop()
            # Signal uvicorn to shut down
            import os
            import signal
            os.kill(os.getpid(), signal.SIGTERM)

        t = threading.Thread(target=_shutdown, daemon=True)
        t.start()

        return {"ok": True}
    except Exception as e:
        traceback.print_exc()
        return _error_response(e)
