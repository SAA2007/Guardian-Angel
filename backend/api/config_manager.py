"""Guardian Angel -- Config Manager

Thread-safe config read/write for the API.  Loads config.json
and optionally merges config.dev.json on top when dev_mode
is enabled.

Usage:
    mgr = ConfigManager("config.json")
    val = mgr.get("detection.sensitivity")
    mgr.update({"detection": {"sensitivity": 0.8}})
"""

import json
import os
import tempfile
import threading


class ConfigManager:
    """Thread-safe configuration manager.

    Reads config.json at startup.  If dev_mode is True,
    also reads config.dev.json and merges its values on top.
    Updates are written atomically via temp-file + rename.
    """

    def __init__(self, config_path):
        """Initialise config manager.

        Args:
            config_path: absolute path to config.json.
        """
        self._config_path = config_path
        self._config_dir = os.path.dirname(config_path)
        self._lock = threading.Lock()
        self._config = {}
        self.reload()

    def reload(self):
        """Re-read config.json (and config.dev.json) from disk."""
        with self._lock:
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)

            # Merge dev config on top if dev_mode is enabled
            if self._config.get("dev_mode", False):
                dev_path = os.path.join(
                    self._config_dir, "config.dev.json"
                )
                if os.path.exists(dev_path):
                    with open(dev_path, "r", encoding="utf-8") as f:
                        dev_config = json.load(f)
                    self._deep_merge(self._config, dev_config)

    def _deep_merge(self, base, override):
        """Recursively merge override dict into base dict.

        Args:
            base: dict to merge into (mutated in place).
            override: dict with values to overlay.
        """
        for key, value in override.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key, default=None):
        """Get a config value by dot-separated key path.

        Args:
            key: config key, e.g. "detection.sensitivity".
            default: value to return if key not found.

        Returns:
            The config value, or default.
        """
        with self._lock:
            parts = key.split(".")
            current = self._config
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current

    def get_all(self):
        """Return a deep copy of the full config.

        Returns:
            dict: complete configuration.
        """
        with self._lock:
            return json.loads(json.dumps(self._config))

    def update(self, updates):
        """Update config values and write to disk atomically.

        Only keys present in updates are modified.  Writes to
        a temp file first, then renames over the original.

        Args:
            updates: dict of key-value pairs to update.
        """
        with self._lock:
            self._deep_merge(self._config, updates)

            # Atomic write: temp file → rename
            fd, tmp_path = tempfile.mkstemp(
                dir=self._config_dir, suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=2)
                    f.write("\n")
                os.replace(tmp_path, self._config_path)
            except Exception:
                # Clean up temp file on failure
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
                raise
