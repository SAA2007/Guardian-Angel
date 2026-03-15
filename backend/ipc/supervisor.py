"""Guardian Angel -- Process Supervisor (Process A)

Spawns and manages detection, overlay, and audio as
subprocesses.  Monitors health and restarts crashed
processes automatically.

Usage:
    supervisor = ProcessSupervisor()
    supervisor.start()
    # ...later...
    print(supervisor.get_status())
    supervisor.stop()
"""

import json
import multiprocessing
import os
import sys
import threading
import time
import traceback

from .shared_state import SharedState
from .process_detection import run_detection_process
from .process_overlay import run_overlay_process
from .process_audio import run_audio_process


# ── config helper ───────────────────────────────────────────────

def _project_root():
    """Return the absolute project root path."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


class ProcessSupervisor:
    """Process A — spawns and supervises all subprocesses.

    Manages:
        - Detection process (screen capture + NudeNet)
        - Overlay process (Win32 transparent window)
        - Audio process (WASAPI loopback + VAD + Whisper)

    Automatically restarts any subprocess that crashes.
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

        # Force spawn method on Windows (required for pywin32)
        try:
            multiprocessing.set_start_method("spawn", force=True)
        except RuntimeError:
            pass  # already set

        self._manager = multiprocessing.Manager()
        self._state = SharedState(self._manager)

        # Process registry
        self._processes = {}
        self._health_thread = None
        self._health_running = False

    def _spawn_process(self, name, target):
        """Spawn a named subprocess.

        Args:
            name: process name (detection/overlay/audio).
            target: callable entry point function.

        Returns:
            Process: the started subprocess.
        """
        p = multiprocessing.Process(
            target=target,
            args=(self._state, self._config_path),
            name="GA-{}".format(name),
            daemon=True,
        )
        p.start()
        print("[SUPERVISOR] Started {} (PID {})".format(
            name, p.pid
        ))
        return p

    def start(self):
        """Spawn all 3 subprocesses and start health monitor."""
        print("[SUPERVISOR] Starting all processes...")

        self._processes["detection"] = self._spawn_process(
            "detection", run_detection_process
        )
        self._processes["overlay"] = self._spawn_process(
            "overlay", run_overlay_process
        )
        self._processes["audio"] = self._spawn_process(
            "audio", run_audio_process
        )

        # Start health monitor
        self._health_running = True
        self._health_thread = threading.Thread(
            target=self._health_monitor, daemon=True
        )
        self._health_thread.start()

        print("[SUPERVISOR] All processes started.")

    def _health_monitor(self):
        """Background thread — checks subprocess health every 5s.

        Restarts any crashed subprocess automatically.
        """
        targets = {
            "detection": run_detection_process,
            "overlay": run_overlay_process,
            "audio": run_audio_process,
        }

        while self._health_running and self._state.is_alive():
            time.sleep(5.0)

            for name, proc in list(self._processes.items()):
                if proc is None:
                    continue

                if not proc.is_alive() and self._state.is_alive():
                    exit_code = proc.exitcode
                    print(
                        "[SUPERVISOR] {} crashed (exit code {}). "
                        "Restarting...".format(name, exit_code)
                    )
                    try:
                        self._processes[name] = self._spawn_process(
                            name, targets[name]
                        )
                        print(
                            "[SUPERVISOR] {} restarted.".format(name)
                        )
                    except Exception:
                        traceback.print_exc()
                        print(
                            "[SUPERVISOR] Failed to restart "
                            "{}.".format(name)
                        )

    def stop(self):
        """Stop all processes gracefully.

        Signals stop, waits up to 5 seconds, then force-kills
        any remaining processes.
        """
        print("[SUPERVISOR] Stopping all processes...")

        # Signal all to stop
        self._state.signal_stop()
        self._health_running = False

        # Wait for graceful shutdown
        for name, proc in self._processes.items():
            if proc is None or not proc.is_alive():
                continue
            proc.join(timeout=5.0)
            if proc.is_alive():
                print(
                    "[SUPERVISOR] Force-terminating {}...".format(name)
                )
                proc.terminate()
                proc.join(timeout=2.0)

        # Wait for health thread
        if self._health_thread is not None:
            self._health_thread.join(timeout=2.0)
            self._health_thread = None

        # Cleanup Manager
        try:
            self._manager.shutdown()
        except Exception:
            pass

        self._processes.clear()
        print("[SUPERVISOR] All processes stopped.")

    def get_status(self):
        """Return current status of all subprocesses.

        Returns:
            dict: status information for all processes.
        """
        status = {
            "detection_alive": False,
            "overlay_alive": False,
            "audio_alive": False,
            "fps_actual": 0.0,
            "detection_count": 0,
            "audio_trigger": False,
        }

        proc_d = self._processes.get("detection")
        if proc_d is not None:
            status["detection_alive"] = proc_d.is_alive()

        proc_o = self._processes.get("overlay")
        if proc_o is not None:
            status["overlay_alive"] = proc_o.is_alive()

        proc_a = self._processes.get("audio")
        if proc_a is not None:
            status["audio_alive"] = proc_a.is_alive()

        try:
            status["fps_actual"] = float(
                self._state.fps_actual.value
            )
        except Exception:
            pass

        try:
            status["detection_count"] = int(
                self._state.detection_count.value
            )
        except Exception:
            pass

        try:
            status["audio_trigger"] = bool(
                self._state.get_audio_trigger()
            )
        except Exception:
            pass

        return status

    def restart_process(self, name):
        """Restart a single subprocess by name.

        Terminates the process, waits up to 3 seconds,
        force-kills if needed, then spawns a fresh one.

        Args:
            name: process name (detection/overlay/audio).

        Returns:
            bool: True if restarted successfully.
        """
        targets = {
            "detection": run_detection_process,
            "overlay": run_overlay_process,
            "audio": run_audio_process,
        }
        if name not in targets:
            print("[SUPERVISOR] Unknown process: {}".format(name))
            return False

        proc = self._processes.get(name)
        if proc is not None and proc.is_alive():
            print("[SUPERVISOR] Terminating {}...".format(name))
            proc.terminate()
            proc.join(timeout=3.0)
            if proc.is_alive():
                print("[SUPERVISOR] Force-killing {}...".format(
                    name
                ))
                proc.kill()
                proc.join(timeout=2.0)

        try:
            self._processes[name] = self._spawn_process(
                name, targets[name]
            )
            print("[SUPERVISOR] {} restarted.".format(name))

            # Update PID file with new subprocess PID
            try:
                pid_file = os.path.join(
                    _project_root(), "data", "guardian_angel.pid"
                )
                if os.path.exists(pid_file):
                    with open(pid_file, "r") as f:
                        pids = json.load(f)
                    pids[name] = self._processes[name].pid
                    with open(pid_file, "w") as f:
                        json.dump(pids, f)
            except Exception:
                pass

            return True
        except Exception:
            traceback.print_exc()
            print("[SUPERVISOR] Failed to restart {}.".format(
                name
            ))
            return False

    @property
    def shared_state(self):
        """Direct access to SharedState (for advanced use)."""
        return self._state
