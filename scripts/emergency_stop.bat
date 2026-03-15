@echo off
title Guardian Angel - Emergency Stop
echo Killing ALL Guardian Angel processes...
C:\Users\DELL\AppData\Local\Programs\Python\Python311\python.exe scripts/kill_ports.py
echo.
echo Force killing any remaining python processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Guardian*" >nul 2>&1
echo Done. All processes stopped.
pause
