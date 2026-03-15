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


r1 = kill_port(8421)
r2 = kill_port(8422)
print('Backend stopped.' if r1 else 'Backend was not running.')
print('Frontend stopped.' if r2 else 'Frontend was not running.')
