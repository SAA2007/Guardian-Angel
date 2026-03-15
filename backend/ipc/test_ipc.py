"""Guardian Angel -- IPC Integration Test

Starts the ProcessSupervisor with all 3 threads,
waits 8 seconds, prints status, then stops cleanly.

This test runs on your real desktop — detection will
capture your screen, overlay will open, audio will
attempt WASAPI loopback.  No NSFW content needed.

Usage:
    python backend/ipc/test_ipc.py
"""

import os
import sys
import time

# Ensure project root is on the Python path
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, _project_root)


def main():
    from backend.ipc.supervisor import ProcessSupervisor

    print("=" * 60)
    print("Guardian Angel -- IPC Integration Test")
    print("=" * 60)

    config_path = os.path.join(_project_root, "config.json")
    supervisor = ProcessSupervisor(config_path=config_path)

    print("\nStarting all threads...")
    supervisor.start()

    print("Running for 8 seconds...")
    for i in range(8):
        time.sleep(1)
        status = supervisor.get_status()
        print(
            "  [{}/8] det={} ovr={} aud={} fps={:.1f} "
            "detections={} audio_trigger={}".format(
                i + 1,
                status["detection_alive"],
                status["overlay_alive"],
                status["audio_alive"],
                status["fps_actual"],
                status["detection_count"],
                status["audio_trigger"],
            )
        )

    print("\nFinal status:")
    final = supervisor.get_status()
    for k, v in final.items():
        print("  {}: {}".format(k, v))

    print("\nStopping all threads...")
    supervisor.stop()

    print("IPC test complete.")


if __name__ == "__main__":
    main()
