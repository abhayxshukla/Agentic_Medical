@echo off
echo ========================================
echo Starting Medical Assistant - Full Stack
echo ========================================
echo.

cd /d "%~dp0"

echo Starting Backend Server (Port 5005)...
start "Backend Server" cmd /k "python main.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend Server (Port 8000)...
cd frontend-geo
start "Frontend Server" cmd /k "python -m http.server 8000"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo Servers Starting...
echo ========================================
echo Backend:  http://localhost:5005
echo Frontend: http://localhost:8000
echo.
echo Opening frontend in browser...
start http://localhost:8000
echo.
echo Press any key to exit (servers will keep running)...
pause >nul
