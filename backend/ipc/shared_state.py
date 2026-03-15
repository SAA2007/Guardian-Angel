"""Guardian Angel -- Shared State for IPC

Thread- and process-safe shared memory container using
multiprocessing.Manager().  Passes bounding box results
from detection to overlay without copying large frames.

Usage:
    from multiprocessing import Manager
    manager = Manager()
    state = SharedState(manager)
    state.update_boxes([{"x": 10, "y": 20, ...}])
    boxes = state.get_boxes()
"""



class SharedState:
    """Process-safe shared state for inter-process communication.

    All attributes are backed by a multiprocessing.Manager()
    so they can be safely read/written from any subprocess.
    """

    def __init__(self, manager):
        """Initialise shared state with Manager-backed structures.

        Args:
            manager: a multiprocessing.Manager() instance.
        """
        # Current bounding boxes from detection
        self._boxes = manager.list()

        # Audio trigger flag
        self._audio_trigger = manager.Value("b", False)

        # Global running flag — False signals all processes to stop
        self._is_running = manager.Value("b", True)

        # FPS metrics
        self._fps_actual = manager.Value("d", 0.0)

        # Total detection count
        self._detection_count = manager.Value("i", 0)



    # ── Box operations ──────────────────────────────────────────

    def update_boxes(self, new_boxes):
        """Replace current boxes atomically.

        Uses slice assignment which is a single Manager RPC
        call — safe for concurrent reads from other processes.

        Args:
            new_boxes: list of box dicts, each containing
                x, y, width, height, monitor_id, tier,
                confidence, label.
        """
        try:
            self._boxes[:] = new_boxes
        except Exception as e:
            print("[SHARED-STATE] update_boxes error: {}".format(e))

    def get_boxes(self):
        """Return a copy of current bounding boxes.

        Returns:
            list[dict]: copy of box list.
        """
        return list(self._boxes)

    # ── Audio trigger ───────────────────────────────────────────

    def set_audio_trigger(self, val):
        """Set audio trigger flag.

        Args:
            val: True if explicit audio detected.
        """
        self._audio_trigger.value = val

    def get_audio_trigger(self):
        """Return audio trigger state.

        Returns:
            bool: True if audio pipeline detected explicit content.
        """
        return self._audio_trigger.value

    # ── Lifecycle ───────────────────────────────────────────────

    def signal_stop(self):
        """Signal all processes to stop."""
        self._is_running.value = False

    def is_alive(self):
        """Check if the system should keep running.

        Returns:
            bool: True if processes should continue.
        """
        return self._is_running.value

    # ── Metrics ─────────────────────────────────────────────────

    @property
    def fps_actual(self):
        """Proxy to the shared fps_actual Value."""
        return self._fps_actual

    @property
    def detection_count(self):
        """Proxy to the shared detection_count Value."""
        return self._detection_count
