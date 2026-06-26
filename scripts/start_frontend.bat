@echo off
REM Frontend startup script (Streamlit)
REM Usage: scripts\start_frontend.bat [port]
REM Default port: 8501

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

set "PYTHON="
set "CANDS=.venv\Scripts\python.exe;C:\Users\AAA\.workbuddy\binaries\python\envs\default\Scripts\python.exe;D:\Program Files\Python312\python.exe"

for %%P in ("%CANDS:;=" "%") do (
    if exist "%%~P" (
        "%%~P" -c "import streamlit" >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON=%%~P"
            goto :found
        )
    )
)

python -c "import streamlit" >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON=python"
    goto :found
)

echo [ERROR] streamlit not found in any Python.
echo Install with: pip install streamlit
exit /b 1

:found
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8501"

echo ==========================================
echo   Industry Knowledge OS Frontend
echo ==========================================
echo   Python : %PYTHON%
echo   Dir    : %CD%
echo   URL    : http://localhost:%PORT%
echo   Stop   : Ctrl+C
echo ==========================================

%PYTHON% -m streamlit run ui\streamlit\app.py --server.port %PORT% --server.headless true

endlocal
