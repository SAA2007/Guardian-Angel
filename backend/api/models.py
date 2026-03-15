"""Guardian Angel -- Pydantic Models for API

Request and response models for all FastAPI endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel


# ── Response models ─────────────────────────────────────────────

class StatusResponse(BaseModel):
    """GET /status response."""
    detection_alive: bool = False
    overlay_alive: bool = False
    audio_alive: bool = False
    fps_actual: float = 0.0
    detection_count: int = 0
    audio_trigger: bool = False
    is_running: bool = False


class ConfigResponse(BaseModel):
    """GET /config response."""
    censor_style: str = "guardian_angel"
    sensitivity: float = 0.6
    fps_max: int = 60
    fps_min: int = 2
    fps_auto_drop: bool = True
    detection_scale: float = 0.5
    detection_skip_frames: int = 2
    onnx_threads: int = 2
    audio_action: str = "silence"
    dev_mode: bool = False


class ConfigUpdateRequest(BaseModel):
    """PATCH /config request — all fields optional."""
    censor_style: Optional[str] = None
    sensitivity: Optional[float] = None
    fps_max: Optional[int] = None
    fps_min: Optional[int] = None
    fps_auto_drop: Optional[bool] = None
    detection_scale: Optional[float] = None
    detection_skip_frames: Optional[int] = None
    onnx_threads: Optional[int] = None
    audio_action: Optional[str] = None
    dev_mode: Optional[bool] = None


class OverlayStatusResponse(BaseModel):
    """GET /overlay response."""
    active: bool = False
    box_count: int = 0
    censor_style: str = "guardian_angel"


class AudioStatusResponse(BaseModel):
    """GET /audio response."""
    active: bool = False
    trigger_count: int = 0
    audio_action: str = "silence"


class StatsResponse(BaseModel):
    """GET /stats response."""
    days_protected: int = 0
    current_streak: int = 0
    total_triggers: int = 0
    session_triggers: int = 0
    uptime_seconds: float = 0.0


class TelemetryPayload(BaseModel):
    """Telemetry data model."""
    uuid: str = ""
    trigger_count: int = 0
    fps_avg: float = 0.0
    errors: List[str] = []
    version: str = "0.1.0"


class TriggerRequest(BaseModel):
    """POST /stats/trigger request."""
    type: str  # "video" or "audio"
