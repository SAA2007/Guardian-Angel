"""Guardian Angel — Screen Capture Module

Multi-monitor screen capture using mss.
Reads FPS settings from config.json.
"""

import json
import os

import numpy as np
import cv2
import mss


def _load_config():
    """Load config.json from the project root."""
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    config_path = os.path.join(project_root, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class ScreenCapture:
    """Captures screen frames from one or more monitors using mss."""

    def __init__(self):
        config = _load_config()
        detection_cfg = config.get("detection", {})

        self._fps_max = detection_cfg.get("fps_max", 60)
        self._fps_min = detection_cfg.get("fps_min", 2)
        self._fps_current = detection_cfg.get("fps_current", self._fps_max)

        # Detect all connected monitors via mss
        self._sct = mss.mss()
        # mss.monitors[0] is the virtual "all-in-one" monitor;
        # mss.monitors[1:] are the individual physical monitors.
        self._monitors = []
        for i, mon in enumerate(self._sct.monitors[1:], start=1):
            self._monitors.append({
                "id": i,
                "x": mon["left"],
                "y": mon["top"],
                "width": mon["width"],
                "height": mon["height"],
            })

    # ── public API ──────────────────────────────────────────────

    def get_monitors(self) -> list[dict]:
        """Return list of monitor info dicts (id, x, y, width, height)."""
        return list(self._monitors)

    def capture_frame(self, monitor_id: int | None = None) -> np.ndarray:
        """Capture a single monitor and return a BGR numpy array.

        Parameters
        ----------
        monitor_id : int or None
            1-based monitor id.  ``None`` captures the primary monitor.
        """
        if monitor_id is None:
            monitor_id = 1  # primary

        # mss indices: 0 = combined, 1..N = physical
        if monitor_id < 1 or monitor_id > len(self._monitors):
            raise ValueError(
                f"Invalid monitor_id {monitor_id}. "
                f"Available: 1–{len(self._monitors)}"
            )

        raw = self._sct.grab(self._sct.monitors[monitor_id])
        # mss returns BGRA; convert to BGR for OpenCV
        frame = np.array(raw)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    def capture_all(self) -> list[np.ndarray]:
        """Capture all monitors and return a list of BGR arrays."""
        frames = []
        for mon in self._monitors:
            frames.append(self.capture_frame(mon["id"]))
        return frames

    def get_fps(self) -> float:
        """Return the current FPS setting."""
        return float(self._fps_current)

    def set_fps(self, fps: int) -> None:
        """Update current FPS, clamped to [fps_min, fps_max]."""
        self._fps_current = max(self._fps_min, min(self._fps_max, int(fps)))
