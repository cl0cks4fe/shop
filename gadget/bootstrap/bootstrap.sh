#!/bin/bash
set -euo pipefail

echo "🔧 Starting bootstrap..."

# IDEMPOTENT: Safe to run multiple times
if grep -q "g_mass_storage" /boot/cmdline.txt; then
  echo "✅ Already bootstrapped! Skipping hardware setup."
  exit 0
fi

# Hardware configuration ONLY
BOOT_DIR=$( [ -d "/boot/firmware" ] && echo "/boot/firmware" || echo "/boot" )
echo "📁 Using boot directory: $BOOT_DIR"

# Make USB storage persistent
echo "⚙️  Configuring USB gadget mode..."
echo "dtoverlay=dwc2" | sudo tee -a "$BOOT_DIR/config.txt" >/dev/null
echo "  ✓ Added dtoverlay to config.txt"
sudo sed -i 's/$/ modules-load=dwc2,g_mass_storage file=\/gadget.img/' "$BOOT_DIR/cmdline.txt"
echo "  ✓ Modified cmdline.txt"

# Create image (idempotent)
echo "💾 Creating 2GB USB storage image..."
sudo dd if=/dev/zero of=/gadget.img bs=1M count=2048 >/dev/null
echo "  ✓ USB image created"
echo "💾 Formatting existing empty image..."
sudo mkfs.vfat -F 32 /gadget.img >/dev/null
echo "  ✓ USB image formatted"

# Install services
echo "🌎 Installing services..."
sudo cp ./files/*.service /etc/systemd/system/
sudo systemctl daemon-reload >/dev/null
sudo systemctl enable gadget.service >/dev/null
echo "  ✓ Services installed"

# Reboot
echo "✅ Bootstrapped! Rebooting..."
sleep 3
sudo reboot
