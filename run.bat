@echo off
setlocal
title Minecraft Launcher
cd /d "%~dp0"

if not exist "main.py" (
    echo [ERROR] main.py not found in: %cd%
    pause & exit /b 1
)

REM جرّب B:\py أولاً (تثبيتك الحالي)
if exist "B:\py\python.exe" (
    "B:\py\python.exe" main.py
    goto :done
)

REM جرّب py launcher
where py >nul 2>nul && (py -3 main.py & goto :done)

REM جرّب python من PATH
where python >nul 2>nul && (python main.py & goto :done)

echo [ERROR] No working Python 3 found.
echo Expected at B:\py\python.exe or in PATH.
pause
exit /b 1

:done
if not "%errorlevel%"=="0" (
    echo.
    echo [Launcher exited with code %errorlevel%]
    pause
)
endlocal