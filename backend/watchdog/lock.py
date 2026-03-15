"""Guardian Angel — Persistence Lock

Enforces the persistence lock state.
"""

import json
import os
from datetime import datetime, timezone

def _load_config():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, "config.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_config(config):
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, "config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

class PersistenceLock:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.state_file = os.path.join(data_dir, "persistence.json")
        os.makedirs(data_dir, exist_ok=True)
        self._load_state()

    def _load_state(self):
        # We read from config.json to sync mode
        config = _load_config()
        self.mode = config.get("persistence_mode", "off")
        self.duration_days = config.get("lock_duration_days", 30)

        # We keep the lock_start in local state file so it can't be easily edited by user in config.json
        self.lock_start = None
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    self.lock_start = state.get("lock_start")
            except Exception:
                pass

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump({"lock_start": self.lock_start}, f)

    def is_locked(self) -> bool:
        self._load_state()
        if self.mode == "off":
            return False
        if self.mode == "indefinite":
            return True
        if self.mode == "timed":
            if not self.lock_start:
                return False
            # Check duration
            try:
                start_dt = datetime.fromisoformat(self.lock_start)
                elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()
                total_duration = self.duration_days * 24 * 60 * 60
                return elapsed < total_duration
            except Exception:
                return False
        return False

    def get_remaining_seconds(self) -> float:
        self._load_state()
        if not self.is_locked() or self.mode != "timed" or not self.lock_start:
            return 0.0
        try:
            start_dt = datetime.fromisoformat(self.lock_start)
            elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()
            total = self.duration_days * 24 * 60 * 60
            remaining = total - elapsed
            return max(0.0, float(remaining))
        except Exception:
            return 0.0

    def start_lock(self):
        self._load_state()
        if self.mode == "timed":
            self.lock_start = datetime.now(timezone.utc).isoformat()
            self._save_state()

    def unlock(self):
        self.lock_start = None
        self._save_state()

    def get_mode(self) -> str:
        self._load_state()
        return self.mode

    def set_mode(self, mode: str, lock_duration_days: int = None):
        config = _load_config()
        config["persistence_mode"] = mode
        if lock_duration_days is not None:
            config["lock_duration_days"] = lock_duration_days
        _save_config(config)
        self.mode = mode
        if lock_duration_days:
            self.duration_days = lock_duration_days
        if mode == "timed" and not self.lock_start:
            self.start_lock()
