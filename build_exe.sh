#!/bin/bash
# Build standalone executables for both language versions (macOS / Linux).
# Needs Python plus PyInstaller:  pip3 install pyinstaller
# Output lands in dist/ as picklecut / picklecut_EN (pickleball) and
# ttcut / ttcut_EN (table tennis); zh-TW / English pairs.
#
# Note: on Windows, antivirus software commonly deletes freshly built
# PyInstaller exes as a false positive - add the project folder to the AV
# exclusions before building. macOS Gatekeeper will require right-click >
# Open on first launch of the unsigned binary.
# Ship each binary together with an ffmpeg placed in the SAME folder
# (picklecut looks for ffmpeg next to itself; it is licensed separately
# and must not be bundled inside the binary).
set -e
cd "$(dirname "$0")"
python3 -m PyInstaller --onefile --clean --name picklecut    picklecut_v1_1.py
python3 -m PyInstaller --onefile --clean --name picklecut_EN picklecut_v1_1_EN.py
python3 -m PyInstaller --onefile --clean --name ttcut        ttcut_v2_4.py
python3 -m PyInstaller --onefile --clean --name ttcut_EN     ttcut_v2_4_EN.py
echo
echo "Done. Executables are in dist/ -- put ffmpeg in the same folder"
echo "as the binary before sharing."
