@echo off
title Guardian Angel — Launcher
echo ============================================================
echo  Guardian Angel v0.1.0 — Starting...
echo ============================================================
echo.
echo Starting backend on http://localhost:8421
start "Guardian Angel — Backend" cmd /k "cd /d A:\projects\guardian-angel && C:\Users\DELL\AppData\Local\Programs\Python\Python311\python.exe backend/main.py"
echo Waiting for backend to initialise...
timeout /t 4 /nobreak >nul
echo Starting frontend on http://localhost:8422
start "Guardian Angel — Frontend" cmd /k "cd /d A:\projects\guardian-angel\frontend && npm run dev"
echo.
echo ============================================================
echo  Both services launching in separate windows.
echo  Backend:  http://localhost:8421
echo  Frontend: http://localhost:8422
echo  Dashboard: http://localhost:8422
echo ============================================================
echo.
echo Press any key to close this launcher window.
pause >nul
