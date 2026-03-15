"""Guardian Angel -- Audio Subprocess Entry Point

Runs the AudioPipeline, writing trigger state to SharedState.
Never crashes — logs errors and continues.

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


def run_audio_process(shared_state, config_path):
    """Entry point for the audio subprocess.

    Args:
        shared_state: SharedState instance (Manager-backed).
        config_path: absolute path to config.json.
    """
    root = _project_root()
    if root not in sys.path:
        sys.path.insert(0, root)

    from backend.audio.pipeline import AudioPipeline

    print("[AUDIO] Subprocess started (PID {})".format(
        os.getpid()
    ))

    pipeline = None
    try:
        pipeline = AudioPipeline()

        def callback(status):
            """Pipeline callback — sets audio trigger on detection."""
            if status.get("is_explicit", False):
                shared_state.set_audio_trigger(True)

        pipeline.start_loop(callback=callback)

        # Keep alive until stop signal
        while shared_state.is_alive():
            time.sleep(0.5)

    except Exception:
        traceback.print_exc()
        print("[AUDIO] Fatal error in audio process.")
    finally:
        if pipeline is not None:
            try:
                pipeline.stop()
            except Exception:
                pass
        print("[AUDIO] Subprocess exiting (PID {})".format(
            os.getpid()
        ))
