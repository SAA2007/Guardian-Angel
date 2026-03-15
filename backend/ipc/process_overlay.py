"""Guardian Angel -- Overlay Subprocess Entry Point

Reads bounding boxes from SharedState, updates the
OverlayRenderer at ~60Hz.  Never crashes.

This module is spawned as a subprocess by ProcessSupervisor.
"""

import os
import sys
import time
import traceback


def _project_root():
    """Return the absolute project root path."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def run_overlay_process(shared_state, config_path):
    """Entry point for the overlay subprocess.

    Args:
        shared_state: SharedState instance (Manager-backed).
        config_path: absolute path to config.json.
    """
    root = _project_root()
    if root not in sys.path:
        sys.path.insert(0, root)

    from backend.overlay.renderer import OverlayRenderer

    print("[OVERLAY] Subprocess started (PID {})".format(
        os.getpid()
    ))

    renderer = None
    try:
        renderer = OverlayRenderer()
        renderer.start()

        last_boxes = []
        last_detection_time = 0

        while shared_state.is_alive():
            try:
                boxes = shared_state.get_boxes()
                now = time.time()
                if boxes:
                    print("[OVERLAY-READ] got {} boxes,"
                          " updating renderer".format(
                              len(boxes)
                          ))
                    last_boxes = boxes
                    last_detection_time = now
                elif now - last_detection_time < 0.8:
                    boxes = last_boxes  # hold last result
                else:
                    last_boxes = []
                    boxes = []
                renderer.update_boxes(boxes)
                time.sleep(0.016)  # ~60Hz refresh
            except Exception:
                traceback.print_exc()
                print("[OVERLAY] Error in overlay loop, "
                      "continuing...")
                time.sleep(0.1)

    except Exception:
        traceback.print_exc()
        print("[OVERLAY] Fatal error in overlay process.")
    finally:
        if renderer is not None:
            try:
                renderer.stop()
            except Exception:
                pass
        print("[OVERLAY] Subprocess exiting (PID {})".format(
            os.getpid()
        ))
