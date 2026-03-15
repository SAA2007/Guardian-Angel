"""Guardian Angel -- Whisper Audio Transcriber

Layer 2 of audio detection.  Transcribes speech using
openai-whisper (tiny.en by default) and checks for explicit
keywords in multiple languages (English, Arabic, Urdu).

Never crashes — all errors return safe defaults.

Usage:
    transcriber = AudioTranscriber()
    result = transcriber.transcribe(chunk, sample_rate=16000)
    if result["is_explicit"]:
        # trigger censor
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


# ── Default keywords (English + Arabic + Urdu) ─────────────────

_DEFAULT_KEYWORDS = [
    # English
    "porn", "sex", "naked", "nude", "explicit",
    "xxx", "adult content", "nsfw",
    # Arabic
    "\u0625\u0628\u0627\u062d\u064a",       # ibahi (pornographic)
    "\u0639\u0627\u0631\u064a",       # aari (nude)
    "\u062c\u0646\u0633\u064a",       # jinsi (sexual)
    "\u0641\u0627\u062d\u0634",       # fahish (obscene)
    # Urdu
    "\u0641\u062d\u0634",         # fahash (obscene)
    "\u0628\u0631\u0647\u0646\u06c1",        # barhana (naked)
    "\u06af\u0646\u062f\u0627",        # ganda (filthy)
]


class AudioTranscriber:
    """Whisper-based speech transcriber with keyword detection.

    Loads the Whisper model lazily on first call.  Supports
    multilingual keyword matching for English, Arabic, and Urdu.
    """

    def __init__(self):
        cfg = _load_config()
        audio_cfg = cfg.get("audio", {})

        self._whisper_model_name = audio_cfg.get(
            "whisper_model", "tiny.en"
        )

        # Load keyword list from config or use defaults
        self._keywords = list(
            audio_cfg.get("audio_keywords", _DEFAULT_KEYWORDS)
        )

        self._model = None
        self._model_loaded = False

    def _ensure_loaded(self):
        """Load Whisper model if not yet loaded."""
        if self._model_loaded:
            return

        try:
            import whisper
            self._model = whisper.load_model(
                self._whisper_model_name
            )
            self._model_loaded = True
        except ImportError:
            print("[WARNING] openai-whisper not installed — "
                  "transcription disabled.")
            self._model_loaded = True  # don't retry
        except Exception:
            traceback.print_exc()
            print("[WARNING] Whisper model failed to load.")
            self._model_loaded = True  # don't retry

    def transcribe(self, chunk, sample_rate):
        """Transcribe an audio chunk and check for explicit keywords.

        Args:
            chunk: raw PCM int16 bytes.
            sample_rate: sample rate of the audio.

        Returns:
            dict: {
                "text": str,
                "is_explicit": bool,
                "matched_keywords": list[str],
                "language": str,
            }
        """
        result = {
            "text": "",
            "is_explicit": False,
            "matched_keywords": [],
            "language": "",
        }

        try:
            self._ensure_loaded()

            if self._model is None:
                return result

            import numpy as np

            # Convert int16 PCM bytes to float32 numpy array
            n_samples = len(chunk) // 2
            samples = struct.unpack("<{}h".format(n_samples), chunk)
            audio = np.array(samples, dtype=np.float32) / 32768.0

            # Whisper expects mono 16kHz float32
            if sample_rate != 16000:
                ratio = sample_rate // 16000
                if ratio > 1:
                    audio = audio[::ratio]

            # Pad or trim to 30 seconds (Whisper requirement)
            import whisper
            audio = whisper.pad_or_trim(audio)

            # Transcribe
            transcription = self._model.transcribe(
                audio,
                fp16=False,
                language=None,  # auto-detect
            )

            text = transcription.get("text", "").strip()
            language = transcription.get("language", "")

            result["text"] = text
            result["language"] = language

            # Check for explicit keywords
            text_lower = text.lower()
            matched = []
            for keyword in self._keywords:
                if keyword.lower() in text_lower:
                    matched.append(keyword)

            result["matched_keywords"] = matched
            result["is_explicit"] = len(matched) > 0

        except Exception:
            traceback.print_exc()
            # Safe defaults — don't crash
            result["is_explicit"] = False

        return result

    def add_keyword(self, word):
        """Add a keyword to the detection list.

        Args:
            word: keyword string to add.
        """
        if word and word not in self._keywords:
            self._keywords.append(word)

    def get_keywords(self):
        """Return current keyword list.

        Returns:
            list[str]: copy of keyword list.
        """
        return list(self._keywords)

    @property
    def model_loaded(self):
        """Whether the Whisper model is loaded."""
        return self._model_loaded and self._model is not None
