#!/bin/bash
# picklecut launcher (Traditional Chinese interface) - double-click to start.
# First time only: run  chmod +x picklecut.command  in Terminal, or
# right-click > Open. Keep the Terminal window open while using picklecut.
cd "$(dirname "$0")"
python3 picklecut_v1_1.py "$@" || {
  echo
  echo "picklecut exited with an error. Is Python 3 installed?"
  read -n 1 -s -p "Press any key to close..."
}
