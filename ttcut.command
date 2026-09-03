#!/bin/bash
# ttcut launcher (Traditional Chinese interface, table tennis) - double-click to start.
# First time only: run  chmod +x ttcut.command  in Terminal, or
# right-click > Open. Keep the Terminal window open while using ttcut.
cd "$(dirname "$0")"
python3 ttcut_v2_4.py "$@" || {
  echo
  echo "ttcut exited with an error. Is Python 3 installed?"
  read -n 1 -s -p "Press any key to close..."
}
