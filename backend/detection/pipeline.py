"""Guardian Angel — Detection Pipeline

Orchestrates screen capture, motion detection, NSFW detection,
and FPS management into a single detection loop.
"""

import json
import os
import subprocess
import sys
import time

import numpy as np


def _load_config():
    """Load config.json from the project root."""
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    config_path = os.path.join(project_root, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_project_root() -> str:
    """Return absolute path to the project root."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def _devlog(message: str) -> None:
    """Invoke scripts/devlog.py to log a message."""
    root = _get_project_root()
    devlog_script = os.path.join(root, "scripts", "devlog.py")
    try:
        subprocess.run(
            [sys.executable, devlog_script, message],
            check=False,
            capture_output=True,
        )
    except Exception:  # noqa: BLE001
        pass  # logging failure should never crash detection


class DetectionPipeline:
    """Full detection loop: capture → motion check → NudeNet → FPS management."""

    def __init__(self):
        from .capture import ScreenCapture
        from .motion import MotionDetector
        from .detector import NSFWDetector
        from .fps_manager import FPSManager

        self.capture = ScreenCapture()
        self.motion = MotionDetector()
        self.detector = NSFWDetector()
        self.fps_manager = FPSManager()

        config = _load_config()
        detection_cfg = config.get("detection", {})
        self.dev_mode: bool = config.get("dev_mode", False)
        self.skip_frames: int = detection_cfg.get(
            "detection_skip_frames", 2
        )

        self.results: dict[int, list[dict]] = {}
        self._frame_count: int = 0
        self._frame_counter: int = 0
        self._last_results: list[dict] = []
        self._running: bool = False

    # ── public API ──────────────────────────────────────────────

    def run_once(self) -> list[dict]:
        """Execute one full detection pass across all monitors.

        Returns a flat list of detection dicts from all monitors.
        """
        all_detections: list[dict] = []
        monitors = self.capture.get_monitors()

        # Frame skip logic — skip NudeNet on non-skip frames
        self._frame_counter += 1
        run_detection = (self._frame_counter % self.skip_frames == 0)

        if not run_detection:
            return list(self._last_results)

        for mon in monitors:
            mid = mon["id"]
            offset = (mon["x"], mon["y"])

            try:
                # 1. Capture
                frame = self.capture.capture_frame(mid)

                # 2. Motion check
                if not self.motion.has_motion(frame, mid):
                    continue

                # 3. Detection
                detections = self.detector.detect(frame, mid, offset)

                # 4. Add tier to each result
                for det in detections:
                    det["tier"] = self.detector.get_tier(
                        det["width"], det["height"]
                    )

                self.results[mid] = detections
                all_detections.extend(detections)

            except Exception as exc:
                print("[DETECTION] Monitor {} error: {}".format(
                    mid, exc
                ))
                continue

        self._last_results = list(all_detections)

        # 5. FPS management
        self.fps_manager.tick()
        self._frame_count += 1

        if self.fps_manager.should_drop():
            old_fps = self.fps_manager.get_target_fps()
            dropped = self.fps_manager.drop_fps()
            if dropped:
                new_fps = self.fps_manager.get_target_fps()
                print(
                    "[FPS] Auto-dropped from {} to {}".format(
                        old_fps, new_fps
                    )
                )

        # Dev mode console output
        if self.dev_mode:
            actual = self.fps_manager.get_actual_fps()
            target = self.fps_manager.get_target_fps()
            print(
                f"[GA-DEV] Frame: {self._frame_count} | "
                f"Monitors: {len(monitors)} | "
                f"Detections: {len(all_detections)} | "
                f"FPS actual: {actual:.1f} | "
                f"FPS target: {target}"
            )

        return all_detections

    def get_latest_results(self) -> list[dict]:
        """Return the most recent detection results without re-running."""
        flat: list[dict] = []
        for dets in self.results.values():
            flat.extend(dets)
        return flat

    def start_loop(self, callback=None) -> None:
        """Run detection loop continuously at target FPS.

        Parameters
        ----------
        callback : callable or None
            If provided, called with ``callback(results)`` after
            each iteration.
        """
        self._running = True
        while self._running:
            loop_start = time.perf_counter()

            detections = self.run_once()

            if callback is not None:
                callback(detections)

            # Sleep to maintain target FPS
            elapsed_ms = (time.perf_counter() - loop_start) * 1000
            budget_ms = self.fps_manager.get_frame_budget_ms()
            sleep_ms = budget_ms - elapsed_ms
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)

    def stop(self) -> None:
        """Signal the detection loop to stop."""
        self._running = False
