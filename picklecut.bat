@echo off
rem picklecut launcher (Traditional Chinese interface) - double-click to start.
rem Keep this window open while using picklecut; closing it stops the tool.
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 picklecut_v1_1.py %*
) else (
  python picklecut_v1_1.py %*
)
if errorlevel 1 (
  echo.
  echo picklecut exited with an error. Is Python 3 installed?
  echo Get it from https://www.python.org/downloads/ and tick "Add to PATH".
  pause
)
endlocal
