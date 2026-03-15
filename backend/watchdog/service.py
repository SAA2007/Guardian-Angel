"""Guardian Angel — Watchdog Service

Monitors main process health.
"""

import json
import os
import threading
import time
import urllib.request
from datetime import datetime, timezone

def _load_config():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, "config.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class WatchdogService:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self._thread = None
        self._running = False
        
        self.root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.log_file = os.path.join(self.root, "data", "watchdog.log")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
            
        config = _load_config()
        if not config.get("watchdog_enabled", True):
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3)

    def _monitor_loop(self):
        config = _load_config()
        interval = config.get("watchdog_check_interval", 30)
        
        fails = 0
        
        while self._running:
            time.sleep(interval)
            
            try:
                # Ping the API
                req = urllib.request.Request("http://localhost:8421/status")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        fails = 0
                    else:
                        fails += 1
            except Exception:
                fails += 1
                
            if fails >= 3:
                self._log_failure()
                fails = 0 # reset after logging to prevent spam

    def _log_failure(self):
        ts = datetime.now(timezone.utc).isoformat()
        log_line = f"[{ts}] CRITICAL: Main process ping failed 3 times."
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
            print(log_line)
        except Exception:
            pass

    def get_health_log(self) -> list:
        if not os.path.exists(self.log_file):
            return []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            # Return last 20
            return [l.strip() for l in lines[-20:] if l.strip()]
        except Exception:
            return []
