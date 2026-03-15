"""Guardian Angel -- Overlay Thread Entry Point

Reads bounding boxes from SharedState, updates the
OverlayRenderer at ~60Hz.  Never crashes.

This module runs as a daemon thread inside ProcessSupervisor.
The Win32 overlay renderer uses a message loop that runs
inside this thread — this thread IS the dedicated Win32
message thread.
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
    """Entry point for the overlay thread.

    Args:
        shared_state: SharedState instance (thread-safe).
        config_path: absolute path to config.json.
    """
    root = _project_root()
    if root not in sys.path:
        sys.path.insert(0, root)

    from backend.overlay.renderer import OverlayRenderer

    print("[OVERLAY] Thread started (PID {})".format(
        os.getpid()
    ))

    renderer = None
    try:
        renderer = OverlayRenderer()
        renderer.start()

        last_boxes = []
        last_detection_time = 0.0
        current_hold = 2.0

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
                    current_hold = (
                        4.0 if len(boxes) >= 2 else 2.0
                    )
                elif now - last_detection_time < current_hold:
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
        print("[OVERLAY] Fatal error in overlay thread.")
    finally:
        if renderer is not None:
            try:
                renderer.stop()
            except Exception:
                pass
        print("[OVERLAY] Thread exiting (PID {})".format(
            os.getpid()
        ))
