@echo off
title Guardian Angel - Stop
echo Stopping Guardian Angel...
C:\Users\DELL\AppData\Local\Programs\Python\Python311\python.exe scripts/kill_ports.py
echo Done.
pause
