"""Guardian Angel — Motion Detection Module

Skip frames where screen content has not changed significantly,
avoiding unnecessary NudeNet inference on static frames.
Uses SSIM (scikit-image) with a numpy-diff fallback.
"""

import json
import os

import numpy as np
import cv2

# Try to import SSIM from scikit-image; fall back to numpy diff.
try:
    from skimage.metrics import structural_similarity as ssim

    _HAS_SKIMAGE = True
except ImportError:  # pragma: no cover
    _HAS_SKIMAGE = False


def _load_config():
    """Load config.json from the project root."""
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    config_path = os.path.join(project_root, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _numpy_similarity(frame_a: np.ndarray, frame_b: np.ndarray) -> float:
    """Cheap pixel-level similarity fallback (0.0 = different, 1.0 = identical)."""
    if frame_a.shape != frame_b.shape:
        return 0.0
    diff = np.abs(frame_a.astype(np.float32) - frame_b.astype(np.float32))
    max_diff = 255.0 * frame_a.size
    return 1.0 - (diff.sum() / max_diff)


class MotionDetector:
    """Compares consecutive frames per monitor to detect significant change."""

    def __init__(self):
        config = _load_config()
        detection_cfg = config.get("detection", {})

        self._threshold: float = detection_cfg.get("motion_skip_threshold", 0.97)
        self._motion_skip_enabled: bool = detection_cfg.get(
            "motion_skip_enabled", True
        )
        # Store the previous frame per monitor id
        self._prev_frames: dict[int, np.ndarray] = {}

    # ── public API ──────────────────────────────────────────────

    def has_motion(self, frame: np.ndarray, monitor_id: int) -> bool:
        """Return True if the frame differs enough from the previous one.

        Always returns True on the first frame for a given monitor.
        Updates the stored previous frame after comparison.
        """
        # If motion skip is disabled, always report motion
        if not self._motion_skip_enabled:
            self._prev_frames[monitor_id] = frame
            return True

        prev = self._prev_frames.get(monitor_id)
        self._prev_frames[monitor_id] = frame

        if prev is None:
            return True  # first frame — nothing to compare

        # Convert to grayscale for comparison
        gray_a = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
        gray_b = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Resize for speed if the frame is large
        h, w = gray_a.shape
        if h > 480 or w > 640:
            scale = min(480 / h, 640 / w)
            new_size = (int(w * scale), int(h * scale))
            gray_a = cv2.resize(gray_a, new_size)
            gray_b = cv2.resize(gray_b, new_size)

        if _HAS_SKIMAGE:
            similarity = ssim(gray_a, gray_b)
        else:
            similarity = _numpy_similarity(gray_a, gray_b)

        return similarity < self._threshold  # True = motion detected

    def reset(self, monitor_id: int | None = None) -> None:
        """Clear stored previous frames.

        If *monitor_id* is ``None``, clear all monitors.
        """
        if monitor_id is None:
            self._prev_frames.clear()
        else:
            self._prev_frames.pop(monitor_id, None)
