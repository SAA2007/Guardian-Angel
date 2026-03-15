"""Guardian Angel -- Backend Entry Point

Starts the ProcessSupervisor (detection + overlay + audio
as threads) and launches the FastAPI server on localhost:8421.

Usage:
    python backend/main.py
"""

import json
import os
import sys
import time
import traceback

import psutil

# Ensure project root is importable
_project_root = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
sys.path.insert(0, _project_root)


def kill_port(port):
    """Kill any process holding the given port."""
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.pid:
                try:
                    proc = psutil.Process(conn.pid)
                    proc.kill()
                    time.sleep(1)
                    return True
                except Exception:
                    pass
    except Exception:
        pass
    return False


def main():
    """Main entry point — starts supervisor and API server."""
    config_path = os.path.join(_project_root, "config.json")

    # ── Clear stale processes on API and frontend ports ──
    if kill_port(8421):
        print("[MAIN] Cleared stale process on port 8421")
    if kill_port(8422):
        print("[MAIN] Cleared stale process on port 8422")

    # ── Load config ─────────────────────────────────────────
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    print("=" * 60)
    print("Guardian Angel v{} — Starting up...".format(
        cfg.get("app_version", "0.1.0")
    ))
    print("=" * 60)

    # ── Instantiate managers ────────────────────────────────
    from backend.api.config_manager import ConfigManager
    from backend.api.stats_manager import StatsManager
    from backend.ipc.supervisor import ProcessSupervisor

    config_manager = ConfigManager(config_path)
    stats_dir = os.path.join(_project_root, "data", "stats")
    stats_manager = StatsManager(stats_dir)

    # ── Start supervisor (spawns 3 threads) ─────────────────
    supervisor = ProcessSupervisor(config_path=config_path)
    supervisor.start()

    # ── Create FastAPI app ──────────────────────────────────
    from backend.api.server import create_app

    app = create_app(
        supervisor=supervisor,
        shared_state=supervisor.shared_state,
        config_manager=config_manager,
        stats_manager=stats_manager,
    )

    # ── Run uvicorn ─────────────────────────────────────────
    import uvicorn
    api_port = 8421

    # ── Write PID file (single process now) ─────────────────
    pid_file = os.path.join(
        _project_root, "data", "guardian_angel.pid"
    )
    os.makedirs(os.path.dirname(pid_file), exist_ok=True)
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    try:
        print("\n[API] Starting on http://localhost:{}".format(
            api_port
        ))
        uvicorn.run(
            app,
            host="localhost",
            port=api_port,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n[MAIN] Shutting down...")
    except Exception:
        traceback.print_exc()
    finally:
        supervisor.stop()
        if os.path.exists(pid_file):
            os.remove(pid_file)
        print("[MAIN] Guardian Angel stopped.")


if __name__ == "__main__":
    main()
