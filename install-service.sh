#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/multivision-ui.service"

if [ ! -f "$SERVICE_FILE" ]; then
  echo "Error: multivision-ui.service not found in $SCRIPT_DIR"
  exit 1
fi

echo "Installing MultiVision UI service..."
echo "Make sure you've edited multivision-ui.service with your username and paths first!"
echo ""

sudo cp "$SERVICE_FILE" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable multivision-ui
sudo systemctl start multivision-ui
sudo systemctl status multivision-ui
