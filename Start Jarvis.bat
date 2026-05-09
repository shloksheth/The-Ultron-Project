@echo off
title J.A.R.V.I.S. Launcher
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

echo.
echo ================================================
echo        J.A.R.V.I.S.  -  SYSTEM BOOT
echo ================================================
echo.

:: ─── [1/3] Start Ollama in background ──────────────────────────────────────
echo [1/3] Starting Ollama Server...
start /min cmd /c "ollama serve"

:: Poll http://localhost:11434 for readiness (max 30 s).
:: curl ships with Windows 10 build 1803+ and all Windows 11 installs.
:: If curl is missing we fall through after 30 s anyway — no hang.
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

:: ─── [2/3] Locate Python and run countdown.py ──────────────────────────────
echo.
echo [2/3] Initialising interface...
echo.

::
:: Detection priority:
::   1. py.exe launcher (C:\Windows\py.exe) — present on all official installs
::   2. python in system/user PATH
::   3. Common user-local install paths (Python 3.10 – 3.13)
::   4. Microsoft Store Python (via AppData alias)
::

set PYTHON_CMD=

:: --- 1. py launcher ---
if exist "%SystemRoot%\py.exe" (
    set PYTHON_CMD="%SystemRoot%\py.exe"
    goto :run_countdown
)

:: --- 2. python in PATH ---
where python >nul 2>&1
if !errorlevel!==0 (
    set PYTHON_CMD=python
    goto :run_countdown
)

:: --- 3. User-local installs (most common for developer machines) ---
for %%V in (313 312 311 310 39 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :run_countdown
    )
)

:: --- 4. System-wide installs ---
for %%V in (313 312 311 310 39 38) do (
    if exist "C:\Python%%V\python.exe" (
        set PYTHON_CMD="C:\Python%%V\python.exe"
        goto :run_countdown
    )
    if exist "C:\Program Files\Python%%V\python.exe" (
        set PYTHON_CMD="C:\Program Files\Python%%V\python.exe"
        goto :run_countdown
    )
)

:: --- 5. Microsoft Store Python alias ---
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
    goto :run_countdown
)

:: No Python found
echo ERROR: Python not found. Install Python 3.8+ and ensure it is on PATH.
goto :done

:run_countdown
echo      Using: !PYTHON_CMD!
!PYTHON_CMD! "%~dp0countdown.py"

:: ─── [3/3] Done ─────────────────────────────────────────────────────────────
:done
echo.
echo [3/3] J.A.R.V.I.S. boot sequence complete.
:: NOTE: No 'pause' — when launched hidden from RunJarvisHidden.vbs the
:: console is invisible; pause would block the process indefinitely.
endlocal