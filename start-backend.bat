@echo off
setlocal

set "VENV_PYTHON=%~dp0..\.venv\Scripts\python.exe"
set "BACKEND_DIR=%~dp0python-backend"

if not exist "%BACKEND_DIR%\.env" (
    echo [ERROR] .env not found in python-backend\
    echo Please configure .env first
    pause
    exit /b 1
)

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual env not found
    pause
    exit /b 1
)

cd /d "%BACKEND_DIR%"
echo Starting backend on http://localhost:1235
echo API docs: http://localhost:1235/docs
echo (close this window to stop; crashes auto-restart in 3s)
echo.

:restart
"%VENV_PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port 1235 --reload --reload-exclude "*uploads*" --reload-exclude "*chroma_db*" --reload-exclude "*logs*" --reload-exclude "*__pycache__*"
echo.
echo [WARN] Backend exited. Auto-restarting in 3 seconds... (close window to stop)
timeout /t 3 /nobreak >nul
goto restart