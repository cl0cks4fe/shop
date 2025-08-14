#!/bin/bash
set -euo pipefail

# Detect boot partition
echo "determining boot partition..."
if [ -d "/boot/firmware" ]; then BOOT_DIR="/boot/firmware"; else BOOT_DIR="/boot"; fi
echo "found boot partition: $BOOT_DIR"

# Setup kernel layers
echo "setting up kernel layers..."
echo "dtoverlay=dwc2" | sudo tee -a "$BOOT_DIR/config.txt"
sudo sed -i 's/rootwait /rootwait modules-load=dwc2,g_mass_storage /' $BOOT_DIR/cmdline.txt
echo "kernel layers complete"

# Create USB image
echo "creating and formatting usb image..."
sudo dd if=/dev/zero of=/gadget.img bs=1M count=2048
sudo mkfs.vfat -F 32 -n "GADGET" /gadget.img
echo "usb image created"

# Install systemd service
echo "installing systemd service"
GADGET_URL="https://raw.githubusercontent.com/cl0cks4fe/shop/refs/heads/main/gadget/bootstrap/files/gadget.service"

# Download the service file with error checking
if ! sudo curl -fsSL "$GADGET_URL" -o /etc/systemd/system/gadget.service; then
    echo "error: failed to download service file from GitHub"
    exit 1
fi

# Verify the file was created
if [ ! -f /etc/systemd/system/gadget.service ]; then
    echo "error: service file not found after download"
    exit 1
fi

# reload and enable systemd
echo "enabling systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable gadget.service
sudo systemctl start gadget.service

echo "install successful, restarting in 10 seconds..."
sleep 10
sudo reboot
