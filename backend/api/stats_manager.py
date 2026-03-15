"""Guardian Angel -- Stats Manager

Reads and writes session + cumulative stats to JSON files
in data/stats/.

Usage:
    mgr = StatsManager("data/stats")
    mgr.record_session_start()
    mgr.record_trigger("video")
    combined = mgr.get_combined()
"""

import json
import os
import threading
import time


class StatsManager:
    """Session and cumulative stats manager.

    Stores stats in two JSON files:
        session.json    — current session counters
        cumulative.json — lifetime counters
    """

    def __init__(self, stats_dir):
        """Initialise stats manager.

        Args:
            stats_dir: path to data/stats/ directory.
        """
        self._stats_dir = stats_dir
        self._lock = threading.Lock()

        # Ensure directory exists
        os.makedirs(stats_dir, exist_ok=True)

        self._session_path = os.path.join(stats_dir, "session.json")
        self._cumulative_path = os.path.join(
            stats_dir, "cumulative.json"
        )

        self._session = self._load_or_create(
            self._session_path,
            {
                "start_time": None,
                "triggers_video": 0,
                "triggers_audio": 0,
                "total_triggers": 0,
            },
        )

        self._cumulative = self._load_or_create(
            self._cumulative_path,
            {
                "days_protected": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "total_triggers": 0,
                "total_triggers_video": 0,
                "total_triggers_audio": 0,
                "total_sessions": 0,
                "total_uptime_seconds": 0.0,
            },
        )

    def _load_or_create(self, path, defaults):
        """Load JSON file or create with defaults.

        Args:
            path: absolute path to JSON file.
            defaults: dict to use if file doesn't exist.

        Returns:
            dict: loaded or default data.
        """
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        self._save(path, defaults)
        return dict(defaults)

    def _save(self, path, data):
        """Write data to JSON file.

        Args:
            path: file path.
            data: dict to serialise.
        """
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
        except OSError:
            pass

    def get_session(self):
        """Return current session stats.

        Returns:
            dict: copy of session stats.
        """
        with self._lock:
            return dict(self._session)

    def get_cumulative(self):
        """Return lifetime stats.

        Returns:
            dict: copy of cumulative stats.
        """
        with self._lock:
            return dict(self._cumulative)

    def record_trigger(self, trigger_type):
        """Increment trigger counts.

        Args:
            trigger_type: "video" or "audio".
        """
        with self._lock:
            key = "triggers_{}".format(trigger_type)
            if key in self._session:
                self._session[key] += 1
            self._session["total_triggers"] += 1

            cum_key = "total_triggers_{}".format(trigger_type)
            if cum_key in self._cumulative:
                self._cumulative[cum_key] += 1
            self._cumulative["total_triggers"] += 1

            self._save(self._session_path, self._session)
            self._save(self._cumulative_path, self._cumulative)

    def record_session_start(self):
        """Mark session start time and reset session counters."""
        with self._lock:
            self._session = {
                "start_time": time.time(),
                "triggers_video": 0,
                "triggers_audio": 0,
                "total_triggers": 0,
            }
            self._cumulative["total_sessions"] += 1
            self._save(self._session_path, self._session)
            self._save(self._cumulative_path, self._cumulative)

    def record_session_end(self):
        """Calculate session duration and update cumulative stats."""
        with self._lock:
            start = self._session.get("start_time")
            if start is not None:
                duration = time.time() - start
                self._cumulative["total_uptime_seconds"] += duration

                # Update days protected (round up partial days)
                days = duration / 86400.0
                if days >= 0.5:
                    self._cumulative["days_protected"] += 1

                # Update streak
                if self._session.get("total_triggers", 0) == 0:
                    self._cumulative["current_streak"] += 1
                    if (self._cumulative["current_streak"]
                            > self._cumulative["longest_streak"]):
                        self._cumulative["longest_streak"] = (
                            self._cumulative["current_streak"]
                        )
                else:
                    self._cumulative["current_streak"] = 0

            self._save(self._cumulative_path, self._cumulative)

    def get_combined(self):
        """Return merged stats view for the API.

        Returns:
            dict: combined session + cumulative stats.
        """
        with self._lock:
            uptime = 0.0
            start = self._session.get("start_time")
            if start is not None:
                uptime = time.time() - start

            return {
                "days_protected": self._cumulative.get(
                    "days_protected", 0
                ),
                "current_streak": self._cumulative.get(
                    "current_streak", 0
                ),
                "total_triggers": self._cumulative.get(
                    "total_triggers", 0
                ),
                "session_triggers": self._session.get(
                    "total_triggers", 0
                ),
                "uptime_seconds": uptime,
            }

    def record_event(self, trigger_type):
        """Append a trigger event to events.json.

        Args:
            trigger_type: "video" or "audio".
        """
        from datetime import datetime, timezone

        events_path = os.path.join(self._stats_dir, "events.json")
        with self._lock:
            events = []
            if os.path.exists(events_path):
                try:
                    with open(events_path, "r", encoding="utf-8") as f:
                        events = json.load(f)
                except (json.JSONDecodeError, OSError):
                    events = []

            events.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": trigger_type,
            })

            # Keep max 100 events, trim oldest
            if len(events) > 100:
                events = events[-100:]

            self._save(events_path, events)

    def get_recent_events(self, n=5):
        """Return the last n trigger events.

        Args:
            n: number of events to return.

        Returns:
            list: last n events.
        """
        events_path = os.path.join(self._stats_dir, "events.json")
        with self._lock:
            if not os.path.exists(events_path):
                return []
            try:
                with open(events_path, "r", encoding="utf-8") as f:
                    events = json.load(f)
                return events[-n:]
            except (json.JSONDecodeError, OSError):
                return []

