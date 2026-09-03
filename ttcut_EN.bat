@echo off
rem ttcut launcher (English interface, table tennis) - double-click to start.
rem Keep this window open while using ttcut; closing it stops the tool.
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 ttcut_v2_4_EN.py %*
) else (
  python ttcut_v2_4_EN.py %*
)
if errorlevel 1 (
  echo.
  echo ttcut exited with an error. Is Python 3 installed?
  echo Get it from https://www.python.org/downloads/ and tick "Add to PATH".
  pause
)
endlocal
