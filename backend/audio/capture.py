"""Guardian Angel -- WASAPI Loopback Audio Capture

Captures system audio output via pyaudiowpatch WASAPI loopback.
No VB-Cable or virtual audio device required.

Usage:
    capture = AudioCapture()
    capture.start()
    chunk = capture.read_chunk()  # bytes | None
    capture.stop()
"""

import collections
import json
import os
import threading


# ── config helpers ──────────────────────────────────────────────

def _project_root():
    """Return the absolute project root path."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def _load_config():
    """Load config.json from the project root."""
    config_path = os.path.join(_project_root(), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── AudioCapture ────────────────────────────────────────────────

class AudioCapture:
    """Capture system audio via WASAPI loopback (pyaudiowpatch).

    Reads sample_rate, chunk_size, channels from config.json.
    Buffers captured chunks in a thread-safe deque (max 50).
    """

    def __init__(self):
        cfg = _load_config()
        audio_cfg = cfg.get("audio", {})

        # Audio parameters — defaults match standard WASAPI loopback
        self._sample_rate = audio_cfg.get("sample_rate", 44100)
        self._chunk_size = audio_cfg.get("chunk_size", 1024)
        self._channels = audio_cfg.get("channels", 2)

        self._buffer = collections.deque(maxlen=50)
        self._stream = None
        self._pa = None
        self._running = False
        self._lock = threading.Lock()

    def get_loopback_device(self):
        """Find and return default WASAPI loopback device info.

        Returns:
            dict: pyaudio device info dictionary.

        Raises:
            RuntimeError: if no WASAPI loopback device found.
        """
        import pyaudiowpatch as pyaudio

        pa = pyaudio.PyAudio()
        try:
            wasapi_info = pa.get_host_api_info_by_type(
                pyaudio.paWASAPI
            )
        except OSError:
            pa.terminate()
            raise RuntimeError(
                "WASAPI not available on this system."
            )

        # Find the default WASAPI loopback device
        default_speakers = pa.get_device_info_by_index(
            wasapi_info["defaultOutputDevice"]
        )

        # pyaudiowpatch exposes loopback devices — find the one
        # that matches the default output
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            if dev.get("isLoopbackDevice", False):
                # Match against default speakers by name prefix
                if default_speakers["name"] in dev["name"]:
                    pa.terminate()
                    return dev

        # Fallback: return any loopback device
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            if dev.get("isLoopbackDevice", False):
                pa.terminate()
                return dev

        pa.terminate()
        raise RuntimeError(
            "No WASAPI loopback device found. Check audio drivers."
        )

    def start(self):
        """Open WASAPI loopback stream and begin capturing.

        Note: WASAPI loopback only generates audio data when the
        system is actually outputting sound.  On a silent desktop,
        zero chunks is expected behaviour.
        """
        if self._running:
            return

        import pyaudiowpatch as pyaudio

        loopback = self.get_loopback_device()

        # Use the loopback device's native format
        self._sample_rate = int(loopback["defaultSampleRate"])
        self._channels = int(loopback["maxInputChannels"])

        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=self._channels,
            rate=self._sample_rate,
            input=True,
            input_device_index=loopback["index"],
            frames_per_buffer=self._chunk_size,
            stream_callback=self._audio_callback,
        )
        self._stream.start_stream()
        self._running = True

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Stream callback — pushes raw bytes into buffer."""
        import pyaudiowpatch as pyaudio

        if in_data is not None:
            with self._lock:
                self._buffer.append(in_data)
        return (in_data, pyaudio.paContinue)

    def stop(self):
        """Close stream cleanly."""
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._pa is not None:
            try:
                self._pa.terminate()
            except Exception:
                pass
            self._pa = None

    def read_chunk(self):
        """Return oldest chunk from buffer, or None if empty.

        Returns:
            bytes | None: raw PCM audio data.
        """
        with self._lock:
            if self._buffer:
                return self._buffer.popleft()
        return None

    def is_running(self):
        """Return whether capture stream is active.

        Returns:
            bool: True if stream is open and capturing.
        """
        return self._running

    @property
    def sample_rate(self):
        """Current sample rate (updated after start)."""
        return self._sample_rate

    @property
    def channels(self):
        """Current channel count (updated after start)."""
        return self._channels

    @property
    def chunk_size(self):
        """Chunk size in frames."""
        return self._chunk_size
