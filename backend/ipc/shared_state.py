"""Guardian Angel -- Shared State for IPC

Thread-safe shared state using threading.Lock.
All worker threads read/write through this class.

Usage:
    state = SharedState()
    state.update_boxes([{"x": 10, "y": 20, ...}])
    boxes = state.get_boxes()
"""

import threading


class SharedState:
    """Thread-safe shared state for inter-thread communication.

    All attributes are protected by a single threading.Lock
    so they can be safely read/written from any thread.
    """

    def __init__(self):
        """Initialise shared state with lock-protected fields."""
        self._lock = threading.Lock()
        self._boxes = []
        self._audio_trigger = False
        self._is_running = True
        self._fps_actual = 0.0
        self._detection_count = 0

    # ── Box operations ──────────────────────────────────────────

    def update_boxes(self, new_boxes):
        """Replace current boxes atomically.

        Args:
            new_boxes: list of box dicts, each containing
                x, y, width, height, monitor_id, tier,
                confidence, label.
        """
        with self._lock:
            self._boxes = list(new_boxes)

    def get_boxes(self):
        """Return a copy of current bounding boxes.

        Returns:
            list[dict]: copy of box list.
        """
        with self._lock:
            return list(self._boxes)

    # ── Audio trigger ───────────────────────────────────────────

    def set_audio_trigger(self, val):
        """Set audio trigger flag.

        Args:
            val: True if explicit audio detected.
        """
        with self._lock:
            self._audio_trigger = val

    def get_audio_trigger(self):
        """Return audio trigger state.

        Returns:
            bool: True if audio pipeline detected explicit content.
        """
        with self._lock:
            return self._audio_trigger

    # ── Lifecycle ───────────────────────────────────────────────

    def signal_stop(self):
        """Signal all threads to stop."""
        with self._lock:
            self._is_running = False

    def is_alive(self):
        """Check if the system should keep running.

        Returns:
            bool: True if threads should continue.
        """
        with self._lock:
            return self._is_running

    # ── Metrics ─────────────────────────────────────────────────

    def set_fps(self, fps):
        """Set the current FPS value.

        Args:
            fps: current frames per second.
        """
        with self._lock:
            self._fps_actual = fps

    def get_fps(self):
        """Return current FPS value.

        Returns:
            float: current frames per second.
        """
        with self._lock:
            return self._fps_actual

    def increment_detection_count(self, n):
        """Increment total detection count.

        Args:
            n: number of detections to add.
        """
        with self._lock:
            self._detection_count += n

    def get_detection_count(self):
        """Return total detection count.

        Returns:
            int: total detections since startup.
        """
        with self._lock:
            return self._detection_count
