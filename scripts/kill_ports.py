"""Guardian Angel -- Process Cleanup

Kills all Guardian Angel processes by:
1. Reading PID file (main + 3 subprocesses)
2. Port-based kill as fallback (8421, 8422)
3. Scanning for any remaining guardian-angel python processes
"""

import json
import os
import time

import psutil


killed = []

# ── Step 1: kill by PID file ────────────────────────────────────
pid_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "guardian_angel.pid"
)
if os.path.exists(pid_file):
    try:
        with open(pid_file) as f:
            pids = json.load(f)
        for name, pid in pids.items():
            try:
                p = psutil.Process(int(pid))
                p.kill()
                killed.append("{} (PID {})".format(name, pid))
            except Exception:
                pass
        os.remove(pid_file)
    except Exception as e:
        print("PID file error: {}".format(e))

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

# ── Step 3: kill remaining guardian-angel python processes ──────
for proc in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        if proc.info["name"] in ("python.exe", "python3.exe"):
            cmdline = " ".join(proc.info["cmdline"] or [])
            if "guardian-angel" in cmdline.lower():
                if proc.pid != os.getpid():
                    proc.kill()
                    killed.append(
                        "guardian-angel python (PID {})".format(
                            proc.pid
                        )
                    )
    except Exception:
        pass

time.sleep(0.5)

if killed:
    print("Stopped: {}".format(", ".join(killed)))
else:
    print("No Guardian Angel processes found.")
