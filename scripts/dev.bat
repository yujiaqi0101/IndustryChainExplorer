@echo off
REM Dev mode: start backend + frontend together
REM Usage: scripts\dev.bat
REM Backend: http://127.0.0.1:8000  Frontend: http://localhost:8501
REM Stop: Close this window to stop both

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

set "PYTHON="
set "CANDS=.venv\Scripts\python.exe;C:\Users\AAA\.workbuddy\binaries\python\envs\default\Scripts\python.exe;D:\Program Files\Python312\python.exe"

for %%P in ("%CANDS:;=" "%") do (
    if exist "%%~P" (
        "%%~P" -c "import fastapi, uvicorn, streamlit" >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON=%%~P"
            goto :found
        )
    )
)

python -c "import fastapi, uvicorn, streamlit" >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON=python"
    goto :found
)

echo [ERROR] Missing dependencies (fastapi/uvicorn/streamlit).
echo Install with: pip install fastapi "uvicorn[standard]" streamlit
exit /b 1

:found
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=8501"

echo ==========================================
echo   IndustryChainExplorer Dev Mode
echo ==========================================
echo   Python  : %PYTHON%
echo   Backend : http://127.0.0.1:%BACKEND_PORT%
echo   Docs    : http://127.0.0.1:%BACKEND_PORT%/docs
echo   Frontend: http://localhost:%FRONTEND_PORT%
echo   Stop    : Close this window
echo ==========================================
echo.

echo [1/2] Starting backend (FastAPI)...
start "ICE Backend" %PYTHON% -m uvicorn api.app:app --host 127.0.0.1 --port %BACKEND_PORT%

timeout /t 2 /nobreak >nul

echo [2/2] Starting frontend (Streamlit)...
%PYTHON% -m streamlit run ui\streamlit\app.py --server.port %FRONTEND_PORT% --server.headless true

taskkill /FI "WindowTitle eq ICE Backend*" /F >nul 2>&1

endlocal
