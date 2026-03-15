"""Guardian Angel -- API Integration Test

Starts the full app (supervisor + FastAPI) in a background
thread, hits each endpoint, then shuts down.

IMPORTANT: must use if __name__ == "__main__" for
multiprocessing on Windows.

Usage:
    python backend/api/test_api.py
"""

import json
import os
import sys
import threading
import time

# Ensure project root is importable
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, _project_root)


def run_server(app, port):
    """Run uvicorn in a separate thread."""
    import uvicorn
    uvicorn.run(app, host="localhost", port=port, log_level="error")


def main():
    import requests

    config_path = os.path.join(_project_root, "config.json")

    print("=" * 60)
    print("Guardian Angel -- API Integration Test")
    print("=" * 60)

    # ── Setup ───────────────────────────────────────────────
    from backend.api.config_manager import ConfigManager
    from backend.api.stats_manager import StatsManager
    from backend.api.server import create_app
    from backend.ipc.supervisor import ProcessSupervisor

    config_manager = ConfigManager(config_path)
    stats_dir = os.path.join(_project_root, "data", "stats")
    stats_manager = StatsManager(stats_dir)
    supervisor = ProcessSupervisor(config_path=config_path)

    # Start supervisor
    print("\nStarting supervisor...")
    supervisor.start()

    # Create app
    app = create_app(
        supervisor=supervisor,
        shared_state=supervisor.shared_state,
        config_manager=config_manager,
        stats_manager=stats_manager,
    )

    # Start server in background thread
    port = 8421
    base_url = "http://localhost:{}".format(port)

    server_thread = threading.Thread(
        target=run_server, args=(app, port), daemon=True
    )
    server_thread.start()

    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)

    # ── Hit endpoints ───────────────────────────────────────
    endpoints = [
        ("GET", "/status"),
        ("GET", "/config"),
        ("GET", "/stats"),
        ("GET", "/overlay"),
        ("GET", "/audio"),
    ]

    for method, path in endpoints:
        url = base_url + path
        try:
            resp = requests.get(url, timeout=5)
            print("\n{} {} → {}".format(method, path, resp.status_code))
            data = resp.json()
            for k, v in data.items():
                print("  {}: {}".format(k, v))
        except Exception as e:
            print("\n{} {} → ERROR: {}".format(method, path, e))

    # ── Shutdown ────────────────────────────────────────────
    print("\nStopping supervisor...")
    supervisor.stop()

    print("\nAPI test complete.")


if __name__ == "__main__":
    main()
