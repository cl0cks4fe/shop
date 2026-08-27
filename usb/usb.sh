#!/bin/bash
set -euo pipefail

RCLONE_REMOTE="gdrive:Engineering/VF2 RUN FILES/POLISH"
MOUNT_POINT="/mnt/usb_mount"
GADGET_IMAGE="/usb.img"

cleanup() {
    echo "Re-enabling USB Gadget..."
    modprobe g_mass_storage file="$GADGET_IMAGE" removable=1 stall=0
}

trap cleanup EXIT

modprobe -r g_mass_storage || true

mkdir -p "$MOUNT_POINT"

echo "Mounting image..."
mount -o loop "$GADGET_IMAGE" "$MOUNT_POINT"

echo "Starting Rclone Sync..."
rclone sync "$RCLONE_REMOTE" "$MOUNT_POINT" --drive-shared-with-me || echo "Sync failed!"

echo "Unmounting image..."
umount "$MOUNT_POINT"
