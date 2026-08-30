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
echo.
"%VENV_PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port 1235 --reload --reload-exclude "*uploads*" --reload-exclude "*chroma_db*" --reload-exclude "*logs*" --reload-exclude "*__pycache__*"
pause