"""Guardian Angel -- Detection Subprocess Entry Point

Runs the DetectionPipeline in a loop, writing results to
SharedState.  Never lets an unhandled exception crash the
process -- logs and continues.

This module is spawned as a subprocess by ProcessSupervisor.
"""

import json
import os
import sys
import time
import traceback


def _project_root():
    """Return the absolute project root path."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def _load_config_safe(config_path):
    """Load config.json, return None on any error."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def run_detection_process(shared_state, config_path):
    """Entry point for the detection subprocess.

    Args:
        shared_state: SharedState instance (Manager-backed).
        config_path: absolute path to config.json.
    """
    # Ensure project root is importable
    root = _project_root()
    if root not in sys.path:
        sys.path.insert(0, root)

    from backend.detection.pipeline import DetectionPipeline

    print("[DETECTION] Subprocess started (PID {})".format(
        os.getpid()
    ))

    # ── B1: Startup health check ────────────────────────────────
    try:
        import mss
        import numpy as np
        import cv2
        with mss.mss() as sct:
            frame = np.array(sct.grab(sct.monitors[1]))
        from backend.detection.detector import NSFWDetector
        test_detector = NSFWDetector()
        test_result = test_detector.detect(frame, 0, (0, 0))
        print("[DETECTION-HEALTH] startup OK | "
              "frame={} | "
              "nudenet_result_count={}".format(
                  frame.shape, len(test_result)))
    except Exception as e:
        print("[DETECTION-HEALTH] startup FAILED: {}".format(e))
        traceback.print_exc()

    pipeline = None
    frame_counter = 0
    try:
        pipeline = DetectionPipeline()

        while shared_state.is_alive():
            try:
                # ── A1: Live config reload ──────────────────────
                cfg = _load_config_safe(config_path)
                if cfg is not None:
                    det_cfg = cfg.get("detection", {})
                    pipeline.detector._sensitivity = det_cfg.get(
                        "sensitivity",
                        pipeline.detector._sensitivity,
                    )
                    pipeline.detector._detection_scale = det_cfg.get(
                        "detection_scale",
                        pipeline.detector._detection_scale,
                    )
                    pipeline.detector._box_padding = det_cfg.get(
                        "detection_box_padding",
                        pipeline.detector._box_padding,
                    )
                    pipeline.detector._detection_classes = det_cfg.get(
                        "detection_classes",
                        pipeline.detector._detection_classes,
                    )
                    pipeline.skip_frames = det_cfg.get(
                        "detection_skip_frames",
                        pipeline.skip_frames,
                    )
                    pipeline.detector.dev_mode = cfg.get(
                        "dev_mode",
                        pipeline.detector.dev_mode,
                    )
                    pipeline.dev_mode = cfg.get(
                        "dev_mode",
                        pipeline.dev_mode,
                    )

                results = pipeline.run_once()

                # Write results to shared state
                if results:
                    print("[IPC-WRITE] writing {} boxes".format(
                        len(results)
                    ))
                shared_state.update_boxes(results)
                if results:
                    readback = shared_state.get_boxes()
                    print("[IPC-READBACK] confirmed {} boxes"
                          " in shared state".format(
                              len(readback)
                          ))

                # Update metrics
                try:
                    fps = pipeline.fps_manager.get_actual_fps()
                    shared_state.fps_actual.value = fps
                except Exception:
                    pass

                if results:
                    shared_state.detection_count.value += len(results)

                # ── B2: Heartbeat every 50 frames ───────────────
                frame_counter += 1
                if frame_counter % 50 == 0:
                    try:
                        hb_fps = pipeline.fps_manager.get_actual_fps()
                    except Exception:
                        hb_fps = 0.0
                    print(
                        "[DETECTION-ALIVE] frame={} | fps={:.1f} | "
                        "sensitivity={} | scale={} | "
                        "subprocess alive".format(
                            frame_counter,
                            hb_fps,
                            pipeline.detector._sensitivity,
                            pipeline.detector._detection_scale,
                        )
                    )

            except Exception:
                traceback.print_exc()
                print("[DETECTION] Error in detection loop, "
                      "retrying in 0.1s...")
                time.sleep(0.1)

    except Exception:
        traceback.print_exc()
        print("[DETECTION] Fatal error in detection process.")
    finally:
        if pipeline is not None:
            try:
                pipeline.stop()
            except Exception:
                pass
        print("[DETECTION] Subprocess exiting (PID {})".format(
            os.getpid()
        ))
