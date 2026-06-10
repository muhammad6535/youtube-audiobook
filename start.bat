@echo off
echo Starting YouTube Audiobook Generator...
echo.

echo [0/2] Installing dependencies...
call %~dp0venv\Scripts\pip install -q -r %~dp0backend\requirements.txt

echo [1/2] Starting backend (FastAPI)...
start "Backend" cmd /c "cd /d %~dp0backend && ..\venv\Scripts\uvicorn app:app --host 127.0.0.1 --port 8000"

echo [2/2] Starting frontend (Vite)...
start "Frontend" cmd /c "cd /d %~dp0frontend && npx vite --host 127.0.0.1 --port 5173"

echo.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo.
pause
