"""Guardian Angel -- Silero VAD Filter

Filters non-speech audio chunks before Whisper transcription,
cutting CPU load by 60-80%.  Only speech chunks are sent to
the transcriber.

Fails open: on any error, returns True (is_speech) so that
we over-transcribe rather than miss explicit content.

Usage:
    vad = VADFilter()
    if vad.is_speech(chunk, sample_rate=16000):
        # send to transcriber
"""

import json
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


class VADFilter:
    """Silero Voice Activity Detection filter.

    Loads the Silero VAD model lazily on first use via
    ``torch.hub``.  Returns True if a chunk contains speech
    above the configured threshold.
    """

    def __init__(self):
        cfg = _load_config()
        audio_cfg = cfg.get("audio", {})

        self._speech_threshold = audio_cfg.get(
            "speech_threshold", 0.5
        )
        self._model = None
        self._model_loaded = False

    def _ensure_loaded(self):
        """Load Silero VAD model via torch.hub if not loaded."""
        if self._model_loaded:
            return

        try:
            import torch
            model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                onnx=False,
            )
            self._model = model
            self._get_speech_timestamps = utils[0]
            self._model_loaded = True
        except Exception:
            traceback.print_exc()
            print("[WARNING] Silero VAD failed to load — "
                  "all chunks will be treated as speech.")
            self._model_loaded = False

    def is_speech(self, chunk, sample_rate):
        """Check whether an audio chunk contains speech.

        Args:
            chunk: raw PCM int16 bytes.
            sample_rate: sample rate of the audio.

        Returns:
            bool: True if speech detected (or on error — fail open).
        """
        try:
            self._ensure_loaded()
            if not self._model_loaded or self._model is None:
                return True  # fail open

            import torch

            # Convert int16 PCM bytes to float32 tensor
            n_samples = len(chunk) // 2  # 2 bytes per int16
            samples = struct.unpack("<{}h".format(n_samples), chunk)
            audio_float = [s / 32768.0 for s in samples]
            tensor = torch.FloatTensor(audio_float)

            # Silero VAD expects mono 16kHz — resample if needed
            if sample_rate != 16000:
                # Simple decimation for common rates
                ratio = sample_rate // 16000
                if ratio > 1:
                    tensor = tensor[::ratio]

            # Run VAD
            speech_prob = self._model(tensor, 16000).item()
            return speech_prob >= self._speech_threshold

        except Exception:
            # Fail open — better to over-transcribe than miss
            return True

    @property
    def model_loaded(self):
        """Whether the VAD model is loaded."""
        return self._model_loaded
