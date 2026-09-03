@echo off
rem Build standalone Windows executables for both language versions.
rem Needs Python plus PyInstaller:  pip install pyinstaller
rem Output lands in dist\ as picklecut.exe / picklecut_EN.exe (pickleball)
rem and ttcut.exe / ttcut_EN.exe (table tennis); zh-TW / English pairs.
rem
rem IMPORTANT: antivirus software commonly flags freshly built PyInstaller
rem exes as a false positive and silently deletes them mid-build (seen with
rem F-Secure on 2026-08-31; Defender does it too). If the build fails with
rem PermissionError / set_exe_build_timestamp errors or the exe vanishes,
rem add this project folder to your antivirus exclusions first, then rebuild.
rem Ship each exe together with an ffmpeg.exe placed in the SAME folder
rem (picklecut looks for ffmpeg next to itself; it is licensed separately
rem and must not be bundled inside the exe).
setlocal
cd /d "%~dp0"
python -m PyInstaller --onefile --clean --name picklecut     picklecut_v1_1.py    || goto :fail
python -m PyInstaller --onefile --clean --name picklecut_EN  picklecut_v1_1_EN.py || goto :fail
python -m PyInstaller --onefile --clean --name ttcut         ttcut_v2_4.py      || goto :fail
python -m PyInstaller --onefile --clean --name ttcut_EN      ttcut_v2_4_EN.py   || goto :fail
echo.
echo Done. Executables are in dist\ -- put ffmpeg.exe in the same folder
echo as the exe before sharing.
goto :eof
:fail
echo.
echo Build failed. Is PyInstaller installed?  pip install pyinstaller
pause
endlocal
