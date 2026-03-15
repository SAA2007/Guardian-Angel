@echo off
title Guardian Angel — Stop
echo Stopping Guardian Angel...
taskkill /FI "WINDOWTITLE eq Guardian Angel — Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Guardian Angel — Frontend*" /T /F >nul 2>&1
echo All Guardian Angel processes stopped.
pause
