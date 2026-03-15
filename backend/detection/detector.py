"""Guardian Angel — NSFW Detection Module

Runs NudeNet inference on captured frames and returns
bounding boxes with confidence and labels.
"""

import json
import os
import traceback

import cv2
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
        self._detection_scale: float = detection_cfg.get(
            "detection_scale", 0.5
        )
        self._onnx_threads: int = detection_cfg.get("onnx_threads", 2)
        self._detector = None
        self.model_loaded: bool = False
        self.dev_mode: bool = config.get("dev_mode", False)

        # Limit ONNX threads via environment before model load
        os.environ["OMP_NUM_THREADS"] = str(self._onnx_threads)

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
            import tempfile

            # Convert BGRA/BGR to RGB for NudeNet
            if frame.shape[2] == 4:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            else:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Scale down for faster inference
            frame_input = frame_rgb
            if self._detection_scale < 1.0:
                h = int(frame_rgb.shape[0] * self._detection_scale)
                w = int(frame_rgb.shape[1] * self._detection_scale)
                frame_input = cv2.resize(
                    frame_rgb, (w, h), interpolation=cv2.INTER_AREA
                )

            # Save first frame for debugging (one-time)
            if not hasattr(self, '_debug_saved'):
                self._debug_saved = True
                project_root = os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(os.path.abspath(__file__))
                    )
                )
                debug_path = os.path.join(
                    project_root, "data", "debug_frame.jpg"
                )
                cv2.imwrite(debug_path, frame)
                if self.dev_mode:
                    print("[DETECT] Saved debug frame to {}".format(
                        debug_path
                    ))

            # NudeNet v3: pass numpy array directly (RGB)
            raw_results = self._detector.detect(frame_input)

            # Debug: show all raw NudeNet results before filtering
            if self.dev_mode:
                print("[DETECT-RAW] {}".format(raw_results))

            results: list[dict] = []
            for det in raw_results:
                confidence = det.get("score", 0.0)
                if confidence < self._sensitivity:
                    continue

                # NudeNet v3 box format: [x, y, width, height]
                box = det.get("box", [0, 0, 0, 0])
                x, y, width, height = box

                results.append({
                    "x": int(x + monitor_offset[0]),
                    "y": int(y + monitor_offset[1]),
                    "width": int(width),
                    "height": int(height),
                    "confidence": float(confidence),
                    "label": det.get("class", "UNKNOWN"),
                    "monitor_id": monitor_id,
                })

            # Scale coordinates back to original resolution
            if self._detection_scale < 1.0:
                inv = 1.0 / self._detection_scale
                for box_dict in results:
                    box_dict["x"] = int(box_dict["x"] * inv)
                    box_dict["y"] = int(box_dict["y"] * inv)
                    box_dict["width"] = int(box_dict["width"] * inv)
                    box_dict["height"] = int(
                        box_dict["height"] * inv
                    )

            return results

        except Exception as exc:  # noqa: BLE001
            print("[GA-ERROR] Detection failed: {}".format(exc))
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
