"""Guardian Angel -- Process Cleanup

Kills the Guardian Angel process by:
1. Reading PID file (single main process PID)
2. Port-based kill as fallback (8421, 8422)
"""

import os
import time

import psutil


killed = []

# ── Step 1: kill by PID file ────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
pid_file = os.path.join(project_root, "data", "guardian_angel.pid")

if os.path.exists(pid_file):
    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())
        p = psutil.Process(pid)
        p.kill()
        killed.append("main (PID {})".format(pid))
        os.remove(pid_file)
    except Exception as e:
        print("PID kill failed: {}".format(e))
        try:
            os.remove(pid_file)
        except Exception:
            pass

# ── Step 2: kill by port as fallback ────────────────────────────
for port in [8421, 8422]:
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.pid:
                try:
                    p = psutil.Process(conn.pid)
                    p.kill()
                    killed.append("port {} (PID {})".format(
                        port, conn.pid
                    ))
                except Exception:
                    pass
    except Exception:
        pass

time.sleep(0.5)

if killed:
    print("Stopped: {}".format(", ".join(killed)))
else:
    print("No Guardian Angel processes found.")
