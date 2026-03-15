"""Guardian Angel — FPS Management Module

Tracks achieved FPS, detects performance shortfall, and
auto-drops target FPS when the system cannot keep up.
"""

import json
import os
import time
from collections import deque


def _load_config():
    """Load config.json from the project root."""
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    config_path = os.path.join(project_root, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_config_path() -> str:
    """Return absolute path to config.json."""
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(project_root, "config.json")


class FPSManager:
    """Measures actual FPS and auto-drops target when performance lags."""

    # Number of recent tick intervals kept for rolling-average FPS
    _WINDOW_SIZE = 30
    # How many consecutive seconds of underperformance before triggering a drop
    _UNDERPERFORM_SECONDS = 3

    def __init__(self):
        config = _load_config()
        detection_cfg = config.get("detection", {})

        self._fps_max: int = detection_cfg.get("fps_max", 60)
        self._fps_min: int = detection_cfg.get("fps_min", 2)
        self._fps_auto_drop: bool = detection_cfg.get("fps_auto_drop", True)
        self._fps_drop_increment: int = detection_cfg.get("fps_drop_increment", 5)

        self.target_fps: int = self._fps_max

        # Timing state
        self._last_tick: float | None = None
        self._intervals: deque[float] = deque(maxlen=self._WINDOW_SIZE)

        # Under-performance tracking
        self._underperform_start: float | None = None

    # ── public API ──────────────────────────────────────────────

    def tick(self) -> None:
        """Call once per detection loop iteration to record timing."""
        now = time.perf_counter()
        if self._last_tick is not None:
            self._intervals.append(now - self._last_tick)
        self._last_tick = now

    def get_actual_fps(self) -> float:
        """Return rolling-average FPS based on the last 30 ticks."""
        if not self._intervals:
            return 0.0
        avg_interval = sum(self._intervals) / len(self._intervals)
        if avg_interval <= 0:
            return 0.0
        return 1.0 / avg_interval

    def get_target_fps(self) -> int:
        """Return the current target FPS value."""
        return self.target_fps

    def get_frame_budget_ms(self) -> float:
        """Return milliseconds available per frame at current target FPS."""
        if self.target_fps <= 0:
            return 0.0
        return 1000.0 / self.target_fps

    def should_drop(self) -> bool:
        """Return True if actual FPS has been >20% below target for 3+ seconds."""
        if not self._fps_auto_drop:
            return False

        actual = self.get_actual_fps()
        threshold = self.target_fps * 0.8

        if actual < threshold and actual > 0:
            now = time.perf_counter()
            if self._underperform_start is None:
                self._underperform_start = now
            elif (now - self._underperform_start) >= self._UNDERPERFORM_SECONDS:
                return True
        else:
            self._underperform_start = None

        return False

    def drop_fps(self) -> bool:
        """Reduce target_fps by drop_increment.

        Returns True if the drop happened, False if already at fps_min
        or auto-drop is disabled.
        """
        if not self._fps_auto_drop:
            return False
        if self.target_fps <= self._fps_min:
            return False

        self.target_fps = max(
            self._fps_min,
            self.target_fps - self._fps_drop_increment,
        )
        # Reset underperformance tracker after a drop
        self._underperform_start = None
        return True

    def write_current_fps_to_config(self) -> None:
        """Persist the current target_fps to config.json as fps_current."""
        config_path = _get_config_path()
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            config.setdefault("detection", {})["fps_current"] = self.target_fps
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as exc:  # noqa: BLE001
            print(f"[GA-ERROR] Failed to write fps_current to config: {exc}")
