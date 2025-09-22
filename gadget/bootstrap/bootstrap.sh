#!/bin/bash
set -euo pipefail

echo "Starting bootstrap..."

# check if already configured
if grep -q "g_mass_storage" /boot/cmdline.txt; then
  echo "Already bootstrapped, skipping."
  exit 0
fi

# figure out which boot dir we're using
BOOT_DIR=$( [ -d "/boot/firmware" ] && echo "/boot/firmware" || echo "/boot" )
echo "Using boot dir: $BOOT_DIR"

# configure usb gadget
echo "Setting up USB gadget mode..."
echo "dtoverlay=dwc2" | sudo tee -a "$BOOT_DIR/config.txt" >/dev/null
echo "  added dtoverlay"
sudo sed -i 's/$/ modules-load=dwc2,g_mass_storage file=\/gadget.img/' "$BOOT_DIR/cmdline.txt"
echo "  updated cmdline.txt"

# create usb storage image
echo "Creating 2GB image file..."
sudo dd if=/dev/zero of=/gadget.img bs=1M count=2048 >/dev/null
echo "  created image"
echo "Formatting as FAT32..."
sudo mkfs.vfat -F 32 /gadget.img >/dev/null
echo "  formatted"

# install systemd services
echo "Installing services..."
sudo cp ./files/*.service /etc/systemd/system/
sudo systemctl daemon-reload >/dev/null
sudo systemctl enable gadget.service >/dev/null
echo "  services installed"

# done, reboot now
echo "Bootstrap complete. Rebooting..."
sleep 3
sudo reboot
