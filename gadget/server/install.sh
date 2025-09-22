#!/bin/bash
set -euo pipefail

echo "Installing gadget application..."

echo "Device setup..."
if [ ! -f /etc/gadget-device-name ]; then
    read -p "Enter device name: " -r DEVICE_NAME
    echo "$DEVICE_NAME" | sudo tee /etc/gadget-device-name > /dev/null
fi
echo "  device: $(cat /etc/gadget-device-name)"

APP_DIR="/usr/local/bin/gadget/server"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR=""

echo "Install dir: $APP_DIR"
echo "Source dir: $SCRIPT_DIR"

echo "Stopping service..."
if sudo systemctl stop gadget-server 2>/dev/null; then
    echo "  stopped"
else
    echo "  wasn't running"
fi

echo "Checking for existing install..."
if [ -d "$APP_DIR" ]; then
    BACKUP_DIR="$APP_DIR.bak-$(date +%s)"
    echo "  backing up existing files..."
    sudo mv "$APP_DIR" "$BACKUP_DIR"
    echo "  backed up to: $BACKUP_DIR"
else
    echo "  fresh install"
fi

# copy files
echo "Installing files..."
sudo mkdir -p "$APP_DIR"
echo "  created dir"

sudo cp -r "$SCRIPT_DIR"/* "$APP_DIR"/
echo "  copied files"

sudo rm -f "$APP_DIR/install.sh"
echo "  cleaned up installer"

# setup python env
echo "Setting up python environment..."
if [ -d "$APP_DIR/venv" ]; then
    echo "  removing old venv..."
    sudo rm -rf "$APP_DIR/venv"
fi

sudo python3 -m venv "$APP_DIR/venv"
echo "  created venv"

echo "Installing dependencies..."
sudo "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
echo "  pip install done"

# start service
echo "Starting service..."
sudo systemctl enable gadget-server >/dev/null
echo "  enabled for boot"

echo "Starting gadget-server..."
sudo systemctl start gadget-server >/dev/null
echo "  started"

# check if it worked
echo "Checking status..."
if sudo systemctl is-active --quiet gadget-server; then
    echo "  running ok"
else
    echo "  warning: service might not be running"
fi
echo "Install complete."
