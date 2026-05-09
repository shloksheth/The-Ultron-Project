@echo off
title U.L.T.R.O.N. Launcher
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

echo.
echo ================================================
echo        U.L.T.R.O.N.  -  SYSTEM BOOT
echo ================================================
echo.

:: ─── [1/3] Start Ollama in background ──────────────────────────────────────
echo [1/3] Starting Ollama Server...
start /min cmd /c "ollama serve"

:: Poll http://localhost:11434 for readiness (max 30 s).
echo      Waiting for Ollama (up to 30 s)...
set /a _t=0

:wait_ollama
    timeout /t 1 /nobreak >nul
    set /a _t+=1
    curl -s --max-time 1 http://localhost:11434 >nul 2>&1
    if !errorlevel!==0 (
        echo      Ollama ready after !_t! s.
        goto :ollama_ok
    )
    if !_t! geq 30 (
        echo      Ollama not ready after 30 s — continuing anyway.
        goto :ollama_ok
    )
goto :wait_ollama

:ollama_ok

:: ─── [2/3] Locate Python and run ultron_boot.py ────────────────────────────
echo.
echo [2/3] Initialising interface...
echo.

set PYTHON_CMD=

if exist "%SystemRoot%\py.exe" (
    set PYTHON_CMD="%SystemRoot%\py.exe"
    goto :run_boot
)

where python >nul 2>&1
if !errorlevel!==0 (
    set PYTHON_CMD=python
    goto :run_boot
)

for %%V in (313 312 311 310 39 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :run_boot
    )
)

:run_boot
if "!PYTHON_CMD!"=="" (
    echo ERROR: Python not found.
    pause
    exit /b
)

echo      Using: !PYTHON_CMD!
:: Start the main system
start "" !PYTHON_CMD! "%~dp0ultron_main.py"
:: Run the boot screen in the foreground
!PYTHON_CMD! "%~dp0ultron_boot.py"

:: ─── [3/3] Done ─────────────────────────────────────────────────────────────
:done
echo.
echo [3/3] U.L.T.R.O.N. boot sequence complete.
endlocal
