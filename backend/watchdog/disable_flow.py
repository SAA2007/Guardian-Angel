"""Guardian Angel — Disable Flow

Manages the multi-step disable sequence.
"""

import json
import os
import time
from datetime import datetime, timezone

class DisableFlow:
    def __init__(self, lock, stats_manager, config_manager=None):
        self.lock = lock
        self.stats = stats_manager
        self.config = config_manager
        
        self.state = "DONE"
        self.wait_start_time = 0
        self.reason = ""
    
    def _get_root(self):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def start(self) -> dict:
        if self.lock.is_locked():
            self.state = "LOCKED"
            return self.get_state()
            
        self.state = "WAITING"
        self.wait_start_time = time.time()
        self.reason = ""
        return self.get_state()
        
    def get_state(self) -> dict:
        if self.state == "LOCKED":
            return {
                "state": "LOCKED",
                "remaining_seconds": self.lock.get_remaining_seconds(),
                "message": "Guardian Angel is locked."
            }
        elif self.state == "WAITING":
            elapsed = time.time() - self.wait_start_time
            rem = max(0, 60 - elapsed)
            return {
                "state": "WAITING",
                "remaining_seconds": rem
            }
        elif self.state == "REASON":
            return {"state": "REASON"}
        elif self.state == "STATS":
            return {
                "state": "STATS",
                "stats": self.get_stats_for_display()
            }
        elif self.state == "NOTIFY":
            return {"state": "NOTIFY"}
        elif self.state == "DONE":
            return {"state": "DONE"}
            
        return {"state": "UNKNOWN"}

    def advance(self, payload: dict) -> dict:
        if self.state == "WAITING":
            elapsed = time.time() - self.wait_start_time
            if elapsed >= 60:
                self.state = "REASON"
                
        elif self.state == "REASON":
            reason = payload.get("reason", "").strip()
            if len(reason) >= 10:
                self.reason = reason
                self.state = "STATS"
                
        elif self.state == "STATS":
            self.state = "NOTIFY"
            
        elif self.state == "NOTIFY":
            self.notify_contact(self.reason)
            self.lock.unlock()
            self.state = "DONE"
            
        return self.get_state()

    def get_stats_for_display(self) -> dict:
        if not self.stats:
            return {}
        try:
            cfg = self.stats.get_stats()
            # fallback mapping if config keys differ
            return {
                "days_protected": cfg.get("total_days_protected", 0),
                "streak": cfg.get("current_streak_days", 0),
                "total_triggers": cfg.get("total_triggers", cfg.get("total_triggers_video", 0) + cfg.get("total_triggers_audio", 0)),
                "session_triggers": 0  # Not in current stats model, would pull from session state in full app
            }
        except Exception:
            return {}

    def notify_contact(self, reason: str):
        config_path = os.path.join(self._get_root(), "config.json")
        email = ""
        try:
            with open(config_path, "r") as f:
                cfg = json.load(f)
                email = cfg.get("accountability_email", "")
        except Exception:
            pass
            
        if not email:
            return
            
        # Log to file to simulate send
        notif_file = os.path.join(self._get_root(), "data", "notifications.json")
        os.makedirs(os.path.dirname(notif_file), exist_ok=True)
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "to": email,
            "stats": self.get_stats_for_display()
        }
        
        history = []
        if os.path.exists(notif_file):
            try:
                with open(notif_file, "r") as f:
                    history = json.load(f)
            except Exception:
                pass
                
        history.append(entry)
        
        try:
            with open(notif_file, "w") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass
