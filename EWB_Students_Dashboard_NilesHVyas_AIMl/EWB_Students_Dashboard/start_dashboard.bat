@echo off
cd /d "%~dp0"

if exist "...venv\Scripts\python.exe" (
set "PYTHON=...venv\Scripts\python.exe"
) else (
set "PYTHON=.venv\Scripts\python.exe"
)

if not exist "%PYTHON%" (
echo Python virtual environment not found.
echo Please check the .venv folder.
pause
exit /b 1
)

start "EWB Student Dashboard" cmd /k ""%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000/"
