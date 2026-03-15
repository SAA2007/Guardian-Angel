"""Guardian Angel -- Thread-based Supervisor

Spawns and manages detection, overlay, and audio as
daemon threads sharing a single process.  Monitors
health and can restart stopped threads.

Usage:
    supervisor = ProcessSupervisor()
    supervisor.start()
    # ...later...
    print(supervisor.get_status())
    supervisor.stop()
"""

import os
import sys
import threading
import traceback

from .shared_state import SharedState
from .process_detection import run_detection_process
from .process_overlay import run_overlay_process
from .process_audio import run_audio_process


def _project_root():
    """Return the absolute project root path."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


class ProcessSupervisor:
    """Spawns and supervises detection, overlay, and audio threads.

    Manages:
        - Detection thread (screen capture + NudeNet)
        - Overlay thread (Win32 transparent window)
        - Audio thread (WASAPI loopback + VAD + Whisper)
    """

    def __init__(self, config_path=None):
        """Initialise supervisor.

        Args:
            config_path: path to config.json (default: auto-detect).
        """
        if config_path is None:
            config_path = os.path.join(
                _project_root(), "config.json"
            )
        self._config_path = config_path
        self._state = SharedState()
        self._threads = {}

    def start(self):
        """Spawn all 3 threads."""
        print("[SUPERVISOR] Starting all threads...")

        targets = {
            "detection": run_detection_process,
            "overlay": run_overlay_process,
            "audio": run_audio_process,
        }

        for name, target in targets.items():
            t = threading.Thread(
                target=target,
                args=(self._state, self._config_path),
                name="GA-{}".format(name),
                daemon=True,
            )
            self._threads[name] = t
            t.start()
            print("[SUPERVISOR] Started {} thread".format(name))

        print("[SUPERVISOR] All threads started.")

    def stop(self):
        """Stop all threads gracefully.

        Signals stop, waits up to 5 seconds per thread.
        """
        print("[SUPERVISOR] Stopping all threads...")

        self._state.signal_stop()

        for name, t in self._threads.items():
            t.join(timeout=5.0)
            if t.is_alive():
                print(
                    "[SUPERVISOR] {} did not stop cleanly".format(
                        name
                    )
                )

        self._threads.clear()
        print("[SUPERVISOR] All threads stopped.")

    def get_status(self):
        """Return current status of all threads.

        Returns:
            dict: status information for all threads.
        """
        return {
            "detection_alive": self._threads.get(
                "detection", threading.Thread()
            ).is_alive(),
            "overlay_alive": self._threads.get(
                "overlay", threading.Thread()
            ).is_alive(),
            "audio_alive": self._threads.get(
                "audio", threading.Thread()
            ).is_alive(),
            "fps_actual": self._state.get_fps(),
            "detection_count": self._state.get_detection_count(),
            "audio_trigger": self._state.get_audio_trigger(),
        }

    def restart_process(self, name):
        """Restart a single thread by name.

        Can only restart a thread that has already stopped.
        Daemon threads cannot be forcibly killed — they must
        exit their run loop via shared_state.is_alive().

        Args:
            name: thread name (detection/overlay/audio).

        Returns:
            bool: True if restarted successfully.
        """
        targets = {
            "detection": run_detection_process,
            "overlay": run_overlay_process,
            "audio": run_audio_process,
        }
        if name not in targets:
            print("[SUPERVISOR] Unknown thread: {}".format(name))
            return False

        old = self._threads.get(name)
        if old and old.is_alive():
            print(
                "[SUPERVISOR] {} thread still running, "
                "cannot restart cleanly".format(name)
            )
            return False

        try:
            t = threading.Thread(
                target=targets[name],
                args=(self._state, self._config_path),
                name="GA-{}".format(name),
                daemon=True,
            )
            self._threads[name] = t
            t.start()
            print("[SUPERVISOR] Restarted {} thread".format(name))
            return True
        except Exception:
            traceback.print_exc()
            print(
                "[SUPERVISOR] Failed to restart {}.".format(name)
            )
            return False

    @property
    def shared_state(self):
        """Direct access to SharedState (for advanced use)."""
        return self._state
