#!/bin/bash
set -euo pipefail

# Detect boot partition
echo "determining boot partition..."
if [ -d "/boot/firmware" ]; then BOOT_DIR="/boot/firmware"; else BOOT_DIR="/boot"; fi
echo "found boot partition: $BOOT_DIR"

# Setup gadget mode
echo "setting up gadget mode..."
echo "dtoverlay=dwc2" | sudo tee -a "$BOOT_DIR/config.txt"
sudo sed -i 's/rootwait /rootwait modules-load=dwc2,g_mass_storage /' $BOOT_DIR/cmdline.txt
echo "gadget mode complete"

# Create USB image
echo "creating and formatting usb image..."
sudo dd if=/dev/zero of=/gadget.img bs=1M count=2048
sudo mkfs.vfat -F 32 -n "GADGET" /gadget.img
echo "usb image created"

# Install systemd service
echo "installing gadget.service"
GADGET_SERVICE_URL="https://raw.githubusercontent.com/cl0cks4fe/shop/refs/heads/main/gadget/bootstrap/files/gadget.service"

# Download the service file with error checking
if ! sudo curl -fsSL "$GADGET_SERVICE_URL" -o /etc/systemd/system/gadget.service; then
    echo "error: failed to download service file from GitHub"
    exit 1
fi

# Verify the file was created
if [ ! -f /etc/systemd/system/gadget.service ]; then
    echo "error: gadget service file not found after download"
    exit 1
fi

echo "installing gadget-server.service"
GADGET_SERVER_SERVICE_URL="https://raw.githubusercontent.com/cl0cks4fe/shop/refs/heads/main/gadget/bootstrap/files/gadget-server.service"

# Download the service file with error checking
if ! sudo curl -fsSL "$GADGET_SERVER_SERVICE_URL" -o /etc/systemd/system/gadget-server.service; then
    echo "error: failed to download service file from GitHub"
    exit 1
fi

# Verify the file was created
if [ ! -f /etc/systemd/system/gadget-server.service ]; then
    echo "error: gadget-server service file not found after download"
    exit 1
fi

echo "installing gadget server"
GADGET_DIST="https://raw.githubusercontent.com/cl0cks4fe/shop/refs/heads/main/dist/gadget.zip"

# Download the service file with error checking
if ! sudo curl -fsSL "$GADGET_DIST" -o gadget.zip; then
    echo "error: failed to download service file from GitHub"
    exit 1
fi

# Verify the file was created
if [ ! -f gadget.zip ]; then
    echo "error: gadget-server zip not found after download"
    exit 1
fi

sudo unzip gadget.zip -d /usr/local/bin/gadget
sudo rm gadget.zip

cd /usr/local/bin/gadget/server
chmod +x scripts/transfer.sh
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# reload and enable systemd
echo "enabling systemd services..."
sudo systemctl daemon-reload

sudo systemctl enable gadget.service
sudo systemctl enable gadget-server.service

echo "install successful, restarting in 10 seconds..."

sleep 10

sudo reboot
