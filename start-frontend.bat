@echo off
setlocal

set "FRONTEND_DIR=%~dp0astro-blog"

if not exist "%FRONTEND_DIR%\package.json" (
    echo [ERROR] astro-blog not found
    pause
    exit /b 1
)

cd /d "%FRONTEND_DIR%"
echo Starting frontend on http://localhost:4321
echo.
call npm run dev
pause