#!/bin/bash
set -euo pipefail

echo "🚀 Starting gadget application installation..."


APP_DIR="/usr/local/bin/gadget/server"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR=""

echo "📁 Installation directory: $APP_DIR"
echo "📦 Source files location: $SCRIPT_DIR"

echo "🛑 Stopping gadget-server service (if running)..."
if sudo systemctl stop gadget-server 2>/dev/null; then
    echo "   ✓ Service stopped successfully"
else
    echo "   ℹ Service was not running"
fi

echo "🔍 Checking for existing installation..."
if [ -d "$APP_DIR" ]; then
    BACKUP_DIR="$APP_DIR.bak-$(date +%s)"
    echo "   📦 Found existing installation, creating backup..."
    sudo mv "$APP_DIR" "$BACKUP_DIR"
    echo "   ✓ Backed up to: $BACKUP_DIR"
else
    echo "   ℹ No existing installation found (first-time install)"
fi

# Install new version
echo "📋 Installing application files..."
sudo mkdir -p "$APP_DIR"
echo "   ✓ Created application directory"

sudo cp -r "$SCRIPT_DIR"/* "$APP_DIR"/
echo "   ✓ Copied all application files"

sudo rm -f "$APP_DIR/install.sh"
echo "   ✓ Removed installer script from directory"

# Setup virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ -d "$APP_DIR/venv" ]; then
    echo "   🗑️ Removing old virtual environment..."
    sudo rm -rf "$APP_DIR/venv"
fi

sudo python3 -m venv "$APP_DIR/venv"
echo "   ✓ Created new virtual environment"

echo "   📦 Installing Python dependencies..."
sudo "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
echo "   ✓ Dependencies installed successfully"

# Start service
echo "⚙️  Configuring system service..."
sudo systemctl enable gadget-server >/dev/null
echo "   ✓ Service enabled for auto-start on boot"

echo "   🔄 Starting gadget-server service..."
sudo systemctl start gadget-server >/dev/null
echo "   ✓ Service started successfully"

# Verify service is running
echo "🔍 Verifying installation..."
if sudo systemctl is-active --quiet gadget-server; then
    echo "   ✅ Service is running correctly"
else
    echo "   ❌ Warning: Service may not have started properly"
fi
echo "🚀 Application installed successfully!"
