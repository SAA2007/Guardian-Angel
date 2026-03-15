"""Guardian Angel -- Audio Pipeline Orchestrator

Orchestrates the full audio processing loop:
  capture → ring buffer → VAD → classifier → transcriber →
  output with retroactive mute.

Usage:
    pipeline = AudioPipeline()
    pipeline.start_loop(callback=my_callback)
    # ...later...
    pipeline.stop()
"""

import json
import os
import time
import threading
import traceback

from .capture import AudioCapture
from .ring_buffer import RingBuffer
from .vad import VADFilter
from .classifier import AudioClassifier
from .transcriber import AudioTranscriber
from .output import AudioOutput


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


class AudioPipeline:
    """Full audio detection pipeline.

    Flow per iteration:
    1. Read chunk from AudioCapture
    2. Push to RingBuffer
    3. Play via AudioOutput
    4. Run VADFilter.is_speech
    5. If speech: run AudioTranscriber.transcribe
    6. Always run AudioClassifier.classify
    7. If either is_explicit:
         - RingBuffer.mute_last(3)
         - Apply audio_action forward (mute or bleep)
         - Increment trigger_count
    """

    def __init__(self):
        cfg = _load_config()
        audio_cfg = cfg.get("audio", {})

        self._dev_mode = cfg.get("dev_mode", False)
        self._audio_action = audio_cfg.get(
            "mute_style", "silence"
        )
        # Normalise: "silence" -> "mute", "bleep" stays "bleep"
        if self._audio_action == "silence":
            self._audio_action = "mute"

        self._buffer_seconds = audio_cfg.get(
            "buffer_seconds", 1.0
        )
        self._vad_enabled = audio_cfg.get("vad_enabled", True)
        self._yamnet_enabled = audio_cfg.get("yamnet_enabled", True)

        # Instantiate all components
        self._capture = AudioCapture()
        self._vad = VADFilter()
        self._classifier = AudioClassifier()
        self._transcriber = AudioTranscriber()
        self._output = AudioOutput()

        # Ring buffer is created after capture starts (needs
        # actual sample_rate/channels from the loopback device)
        self._ring = None

        self._trigger_count = 0
        self._running = False
        self._loop_thread = None

    def _setup_ring_buffer(self):
        """Create ring buffer using capture's actual parameters."""
        self._ring = RingBuffer(
            sample_rate=self._capture.sample_rate,
            channels=self._capture.channels,
            chunk_size=self._capture.chunk_size,
            buffer_seconds=self._buffer_seconds,
        )

        # Update output to match capture's format
        self._output.set_sample_rate(self._capture.sample_rate)
        self._output.set_channels(self._capture.channels)

    def run_once(self):
        """Execute one pipeline iteration.

        Returns:
            dict: {
                "chunk_processed": bool,
                "speech_detected": bool,
                "is_explicit": bool,
                "trigger_count": int,
            }
        """
        result = {
            "chunk_processed": False,
            "speech_detected": False,
            "is_explicit": False,
            "trigger_count": self._trigger_count,
        }

        try:
            # 1. Read chunk from capture
            chunk = self._capture.read_chunk()
            if chunk is None:
                return result

            result["chunk_processed"] = True

            # 2. Push to ring buffer
            if self._ring is not None:
                self._ring.push(chunk)

            # 3. Play via output
            self._output.play_chunk(chunk)

            # 4. Run VAD
            speech = False
            if self._vad_enabled:
                speech = self._vad.is_speech(
                    chunk, self._capture.sample_rate
                )
            result["speech_detected"] = speech

            # 5. If speech, run transcriber
            transcription_explicit = False
            if speech:
                t_result = self._transcriber.transcribe(
                    chunk, self._capture.sample_rate
                )
                transcription_explicit = t_result.get(
                    "is_explicit", False
                )

            # 6. Always run classifier (if enabled)
            classifier_explicit = False
            if self._yamnet_enabled:
                c_result = self._classifier.classify(
                    chunk, self._capture.sample_rate
                )
                classifier_explicit = c_result.get(
                    "is_explicit", False
                )

            # 7. If either detected explicit content
            is_explicit = (
                transcription_explicit or classifier_explicit
            )
            result["is_explicit"] = is_explicit

            if is_explicit:
                # Retroactive mute of buffered audio
                if self._ring is not None:
                    self._ring.mute_last(3)

                # Apply action going forward
                if self._audio_action == "bleep":
                    self._output.play_bleep(3)
                else:
                    self._output.play_silence(3)

                self._trigger_count += 1
                result["trigger_count"] = self._trigger_count

            # Dev mode logging
            if self._dev_mode:
                action = "none"
                if is_explicit:
                    action = self._audio_action
                print(
                    "[GA-DEV-AUDIO] speech={} | explicit={} | "
                    "action={} | triggers={}".format(
                        speech, is_explicit, action,
                        self._trigger_count
                    )
                )

        except Exception:
            traceback.print_exc()

        return result

    def start_loop(self, callback=None):
        """Start the pipeline loop in a background thread.

        Args:
            callback: optional callable(status_dict) called
                      each iteration.
        """
        if self._running:
            return

        # Start capture
        self._capture.start()
        self._setup_ring_buffer()
        self._output.start()
        self._running = True

        def _loop():
            while self._running:
                status = self.run_once()
                if callback is not None:
                    try:
                        callback(status)
                    except Exception:
                        pass
                # Small sleep to prevent tight loop when no audio
                if not status["chunk_processed"]:
                    time.sleep(0.01)

        self._loop_thread = threading.Thread(
            target=_loop, daemon=True
        )
        self._loop_thread.start()

    def stop(self):
        """Stop the pipeline loop and all components."""
        self._running = False

        if self._loop_thread is not None:
            self._loop_thread.join(timeout=2.0)
            self._loop_thread = None

        self._capture.stop()
        self._output.stop()

    def get_trigger_count(self):
        """Return the total number of triggers detected.

        Returns:
            int: cumulative trigger count.
        """
        return self._trigger_count

    @property
    def is_running(self):
        """Whether the pipeline loop is active."""
        return self._running
