"""Guardian Angel -- Detection Subprocess Entry Point

Runs the DetectionPipeline in a loop, writing results to
SharedState.  Never lets an unhandled exception crash the
process — logs and continues.

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

    pipeline = None
    try:
        pipeline = DetectionPipeline()

        while shared_state.is_alive():
            try:
                results = pipeline.run_once()

                # Write results to shared state
                shared_state.update_boxes(results)

                # Update metrics
                try:
                    fps = pipeline.fps_manager.get_actual_fps()
                    shared_state.fps_actual.value = fps
                except Exception:
                    pass

                if results:
                    shared_state.detection_count.value += len(results)

            except Exception:
                traceback.print_exc()
                print("[DETECTION] Error in detection loop, "
                      "retrying in 1s...")
                time.sleep(1.0)

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
