"""Guardian Angel -- YAMNet Audio Classifier

Layer 1 of audio detection.  YAMNet classifies sound type to
catch non-verbal explicit audio that transcription would miss
(moans, groans, screaming, etc.).

Falls back gracefully if tensorflow_hub is not installed —
returns is_explicit=False with yamnet_available=False.

Usage:
    clf = AudioClassifier()
    result = clf.classify(chunk, sample_rate=16000)
    if result["is_explicit"]:
        # trigger censor
"""

import struct
import traceback


class AudioClassifier:
    """YAMNet-based audio event classifier.

    Detects explicit non-verbal audio by classifying sound
    events against a curated list of explicit classes from
    YAMNet's 521-class ontology.
    """

    # Classes from YAMNet's AudioSet ontology that indicate
    # potentially explicit audio content.
    _EXPLICIT_CLASSES = [
        "Groan",
        "Moan",
        "Whimper",
        "Screaming",
        "Sexual activity",
        "Grunt",
        "Sigh",
        "Gasp",
        "Pant",
        "Crying, sobbing",
    ]

    def __init__(self):
        self._model = None
        self._class_names = None
        self._model_loaded = False
        self._yamnet_available = False
        self.explicit_classes = list(self._EXPLICIT_CLASSES)

    def _ensure_loaded(self):
        """Load YAMNet model via tensorflow_hub if available."""
        if self._model_loaded:
            return

        try:
            import tensorflow_hub as hub
            import numpy as np
            import csv
            import io

            # Load YAMNet from TF Hub
            self._model = hub.load(
                "https://tfhub.dev/google/yamnet/1"
            )

            # Load class map
            class_map_path = self._model.class_map_path().numpy()
            with open(class_map_path, "r") as f:
                reader = csv.DictReader(f)
                self._class_names = [
                    row["display_name"] for row in reader
                ]

            self._model_loaded = True
            self._yamnet_available = True

        except ImportError:
            print("[INFO] tensorflow_hub not installed — "
                  "YAMNet classifier disabled.")
            self._yamnet_available = False
            self._model_loaded = True  # don't retry

        except Exception:
            traceback.print_exc()
            print("[WARNING] YAMNet failed to load.")
            self._yamnet_available = False
            self._model_loaded = True  # don't retry

    def classify(self, chunk, sample_rate):
        """Classify an audio chunk for explicit content.

        Args:
            chunk: raw PCM int16 bytes.
            sample_rate: sample rate of the audio.

        Returns:
            dict: {
                "is_explicit": bool,
                "top_class": str,
                "confidence": float,
                "yamnet_available": bool,
            }
        """
        result = {
            "is_explicit": False,
            "top_class": "",
            "confidence": 0.0,
            "yamnet_available": self._yamnet_available,
        }

        try:
            self._ensure_loaded()

            if not self._yamnet_available or self._model is None:
                result["yamnet_available"] = False
                return result

            import numpy as np

            # Convert int16 PCM bytes to float32 numpy array
            n_samples = len(chunk) // 2
            samples = struct.unpack("<{}h".format(n_samples), chunk)
            audio = np.array(samples, dtype=np.float32) / 32768.0

            # YAMNet expects mono 16kHz
            if sample_rate != 16000:
                ratio = sample_rate // 16000
                if ratio > 1:
                    audio = audio[::ratio]

            # Run YAMNet
            scores, embeddings, spectrogram = self._model(audio)
            scores_np = scores.numpy()

            # Get top prediction
            top_idx = scores_np.mean(axis=0).argmax()
            top_class = ""
            if self._class_names and top_idx < len(self._class_names):
                top_class = self._class_names[top_idx]

            confidence = float(scores_np.mean(axis=0)[top_idx])

            result["top_class"] = top_class
            result["confidence"] = confidence
            result["yamnet_available"] = True
            result["is_explicit"] = (
                top_class in self.explicit_classes
                and confidence > 0.3
            )

        except Exception:
            traceback.print_exc()
            result["is_explicit"] = False
            result["yamnet_available"] = self._yamnet_available

        return result

    @property
    def yamnet_available(self):
        """Whether YAMNet model is loaded and usable."""
        return self._yamnet_available

    @property
    def model_loaded(self):
        """Whether model loading has been attempted."""
        return self._model_loaded
