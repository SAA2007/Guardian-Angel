"""Guardian Angel — NSFW Detection Module

Runs NudeNet inference on captured frames and returns
bounding boxes with confidence and labels.
"""

import json
import os
import traceback

import numpy as np


def _load_config():
    """Load config.json from the project root."""
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    config_path = os.path.join(project_root, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class NSFWDetector:
    """Lazy-loaded NudeNet detector that returns bounding boxes."""

    def __init__(self):
        config = _load_config()
        detection_cfg = config.get("detection", {})

        self._sensitivity: float = detection_cfg.get("sensitivity", 0.6)
        self._detector = None
        self.model_loaded: bool = False

    # ── internal ────────────────────────────────────────────────

    def _ensure_loaded(self) -> None:
        """Load the NudeNet model if not already loaded."""
        if self.model_loaded:
            return
        try:
            from nudenet import NudeDetector

            self._detector = NudeDetector()
            self.model_loaded = True
        except Exception as exc:  # noqa: BLE001
            print(f"[GA-ERROR] Failed to load NudeNet model: {exc}")
            traceback.print_exc()

    # ── public API ──────────────────────────────────────────────

    def detect(
        self,
        frame: np.ndarray,
        monitor_id: int = 0,
        monitor_offset: tuple[int, int] = (0, 0),
    ) -> list[dict]:
        """Run NudeNet on *frame* and return filtered bounding boxes.

        Each result dict contains:
            x, y          – absolute screen coordinates (with monitor offset)
            width, height – box dimensions
            confidence    – detection confidence (0–1)
            label         – NudeNet class label
            monitor_id    – which monitor this detection came from

        Returns an empty list if the model failed to load or
        no detections exceed the sensitivity threshold.
        """
        self._ensure_loaded()
        if self._detector is None:
            return []

        try:
            # NudeNet expects a file path or PIL image.
            # We save to a temp buffer to avoid disk I/O.
            import cv2
            import tempfile

            tmp_path = os.path.join(tempfile.gettempdir(), "_ga_detect.jpg")
            cv2.imwrite(tmp_path, frame)
            raw_results = self._detector.detect(tmp_path)

            results: list[dict] = []
            for det in raw_results:
                confidence = det.get("score", 0.0)
                if confidence < self._sensitivity:
                    continue

                box = det.get("box", [0, 0, 0, 0])
                # NudeNet box format: [x1, y1, x2, y2]
                x1, y1, x2, y2 = box
                width = x2 - x1
                height = y2 - y1

                results.append({
                    "x": int(x1 + monitor_offset[0]),
                    "y": int(y1 + monitor_offset[1]),
                    "width": int(width),
                    "height": int(height),
                    "confidence": float(confidence),
                    "label": det.get("class", "UNKNOWN"),
                    "monitor_id": monitor_id,
                })

            return results

        except Exception as exc:  # noqa: BLE001
            print(f"[GA-ERROR] Detection failed: {exc}")
            traceback.print_exc()
            return []

    @staticmethod
    def get_tier(width: int, height: int) -> str:
        """Return size tier string based on bounding box dimensions.

        Tiers (from SPEC.md):
            full   – >= 200×200
            medium – >= 80×80
            small  – >= 40×40
            micro  – anything smaller
        """
        if width >= 200 and height >= 200:
            return "full"
        if width >= 80 and height >= 80:
            return "medium"
        if width >= 40 and height >= 40:
            return "small"
        return "micro"
