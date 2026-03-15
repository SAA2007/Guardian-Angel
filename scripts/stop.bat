@echo off
title Guardian Angel - Stop
echo Stopping Guardian Angel...
C:\Users\DELL\AppData\Local\Programs\Python\Python311\python.exe -c "
import psutil
def kill_port(port):
    killed = False
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    proc.kill()
                    killed = True
        except Exception:
            continue
    return killed
r1 = kill_port(8421)
r2 = kill_port(8422)
print('Backend stopped.' if r1 else 'Backend was not running.')
print('Frontend stopped.' if r2 else 'Frontend was not running.')
"
echo Done.
pause
