@echo off
echo Starting The Lenny Growth Assistant...
start "Lenny Backend" powershell -NoExit -Command "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"
start "Lenny Frontend" powershell -NoExit -Command "cd frontend; npm run dev"
timeout /t 3 /nobreak >nul
start http://localhost:3000
