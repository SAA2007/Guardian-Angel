import os
import psutil


def kill_port(port):
    killed = False
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.pid:
                try:
                    proc = psutil.Process(conn.pid)
                    proc.kill()
                    killed = True
                except Exception:
                    pass
    except Exception:
        pass
    return killed


# Try PID file first (most reliable)
pid_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "guardian_angel.pid"
)
if os.path.exists(pid_file):
    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())
        proc = psutil.Process(pid)
        proc.kill()
        os.remove(pid_file)
        print("Backend process killed via PID file.")
    except Exception as e:
        print("PID kill failed: {}".format(e))

# Port-based kill as fallback
r1 = kill_port(8421)
r2 = kill_port(8422)
print("Backend stopped." if r1 else "Backend was not running.")
print("Frontend stopped." if r2 else "Frontend was not running.")
