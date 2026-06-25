@echo off
REM Backend startup script (FastAPI + Uvicorn)
REM Usage: scripts\start_backend.bat [port]
REM Default port: 8000

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

REM Detect Python: try candidates, pick first that can import fastapi+uvicorn
set "PYTHON="
set "CANDS=.venv\Scripts\python.exe;C:\Users\AAA\.workbuddy\binaries\python\envs\default\Scripts\python.exe;D:\Program Files\Python312\python.exe"

for %%P in ("%CANDS:;=" "%") do (
    if exist "%%~P" (
        "%%~P" -c "import fastapi, uvicorn" >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON=%%~P"
            goto :found
        )
    )
)

REM Fallback: system python on PATH
python -c "import fastapi, uvicorn" >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON=python"
    goto :found
)

echo [ERROR] fastapi/uvicorn not found in any Python.
echo Install with: pip install fastapi "uvicorn[standard]" streamlit
exit /b 1

:found
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8000"
set "HOST=127.0.0.1"

echo ==========================================
echo   IndustryChainExplorer Backend
echo ==========================================
echo   Python : %PYTHON%
echo   Dir    : %CD%
echo   URL    : http://%HOST%:%PORT%
echo   Docs   : http://%HOST%:%PORT%/docs
echo   Stop   : Ctrl+C
echo ==========================================

%PYTHON% -m uvicorn api.app:app --reload --host %HOST% --port %PORT%

endlocal
