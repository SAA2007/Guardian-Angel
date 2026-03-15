"""Guardian Angel -- Audio Output

Plays buffered audio to speakers/headphones with support for
muting and bleeping on trigger detection.

Usage:
    out = AudioOutput()
    out.start()
    out.play_chunk(chunk)
    out.play_silence(3)   # 3 chunks of silence
    out.play_bleep(3)     # 3 chunks of 1kHz bleep
    out.stop()
"""

import json
import math
import os
import struct
import traceback


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


class AudioOutput:
    """Audio playback via pyaudiowpatch.

    Supports normal playback, silence injection, and
    1kHz bleep tone generation for censor triggers.
    """

    def __init__(self):
        cfg = _load_config()
        audio_cfg = cfg.get("audio", {})

        self._sample_rate = audio_cfg.get("sample_rate", 44100)
        self._channels = audio_cfg.get("channels", 2)
        self._chunk_size = audio_cfg.get("chunk_size", 1024)
        self._bleep_freq = audio_cfg.get(
            "bleep_frequency_hz", 1000
        )

        self._stream = None
        self._pa = None
        self._running = False

    def start(self):
        """Open output audio stream."""
        if self._running:
            return

        try:
            import pyaudiowpatch as pyaudio

            self._pa = pyaudio.PyAudio()
            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=self._channels,
                rate=self._sample_rate,
                output=True,
                frames_per_buffer=self._chunk_size,
            )
            self._running = True
        except Exception:
            traceback.print_exc()
            print("[WARNING] Audio output failed to start.")
            self._running = False

    def stop(self):
        """Close output stream cleanly."""
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

    def play_chunk(self, chunk):
        """Write a chunk of audio to the output stream.

        Args:
            chunk: raw PCM int16 bytes.
        """
        if not self._running or self._stream is None:
            return
        try:
            self._stream.write(chunk)
        except Exception:
            pass

    def play_silence(self, n_chunks):
        """Write zeroed (silent) audio for *n_chunks* chunks.

        Args:
            n_chunks: number of silent chunks to play.
        """
        if not self._running or self._stream is None:
            return

        # Each frame = channels * 2 bytes (int16)
        bytes_per_chunk = self._chunk_size * self._channels * 2
        silence = b"\x00" * bytes_per_chunk

        for _ in range(n_chunks):
            try:
                self._stream.write(silence)
            except Exception:
                break

    def play_bleep(self, n_chunks):
        """Generate and play a 1kHz sine wave bleep.

        Args:
            n_chunks: number of chunks of bleep tone to play.
        """
        if not self._running or self._stream is None:
            return

        # Generate sine wave at bleep frequency
        total_frames = self._chunk_size * n_chunks
        samples = []
        for i in range(total_frames):
            t = float(i) / self._sample_rate
            val = math.sin(2.0 * math.pi * self._bleep_freq * t)
            sample = int(val * 16000)  # ~50% volume
            # Duplicate for each channel
            for _ in range(self._channels):
                samples.append(sample)

        bleep_bytes = struct.pack(
            "<{}h".format(len(samples)), *samples
        )

        # Write in chunk-sized pieces
        bytes_per_chunk = self._chunk_size * self._channels * 2
        offset = 0
        while offset < len(bleep_bytes):
            chunk = bleep_bytes[offset:offset + bytes_per_chunk]
            try:
                self._stream.write(chunk)
            except Exception:
                break
            offset += bytes_per_chunk

    def is_running(self):
        """Return whether the output stream is active.

        Returns:
            bool: True if stream is open.
        """
        return self._running

    def set_sample_rate(self, rate):
        """Update sample rate (call before start).

        Args:
            rate: new sample rate in Hz.
        """
        self._sample_rate = rate

    def set_channels(self, channels):
        """Update channel count (call before start).

        Args:
            channels: number of audio channels.
        """
        self._channels = channels
