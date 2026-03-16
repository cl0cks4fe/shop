#!/bin/bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly GADGET_IMAGE="/gadget.img"
readonly GADGET_SIZE_MB=2048
readonly SERVICE_NAME="gadget.service"

log_info() {
    echo "[INFO] $*"
}

log_warn() {
    echo "[WARN] $*" >&2
}

log_error() {
    echo "[ERROR] $*" >&2
}

check_privileges() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root. Use sudo when needed."
        exit 1
    fi

    if ! sudo -n true 2>/dev/null; then
        log_error "This script requires sudo privileges."
        exit 1
    fi
}

detect_boot_directory() {
    if [[ -d "/boot/firmware" ]]; then
        echo "/boot/firmware"
    elif [[ -d "/boot" ]]; then
        echo "/boot"
    else
        log_error "Could not find boot directory"
        exit 1
    fi
}

configure_usb_gadget() {
    local boot_dir
    boot_dir=$(detect_boot_directory)

    log_info "Configuring USB gadget mode"
    log_info "Using boot directory: $boot_dir"

    if sed -n '/^\[all\]/,$p' "$boot_dir/config.txt" | grep -q '^dtoverlay=dwc2'; then
        log_info "config.txt already configured, skipping..."
    else
        echo "dtoverlay=dwc2" | sudo tee -a "$boot_dir/config.txt" >/dev/null
        log_info "Added dtoverlay=dwc2 to config.txt"
    fi

    if grep -q "g_mass_storage" "$boot_dir/cmdline.txt"; then
        log_info "cmdline.txt already configured, skipping..."
    else
        sudo sed -i '1s/$/ modules-load=dwc2,g_mass_storage file=\/gadget.img/' "$boot_dir/cmdline.txt"
        log_info "Updated cmdline.txt with USB gadget parameters"
    fi
}

create_storage_image() {
    log_info "Creating USB storage image"

    if [[ -f "$GADGET_IMAGE" ]]; then
        log_warn "Gadget image already exists at $GADGET_IMAGE"
        read -p "Overwrite existing image? (y/N): " -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Keeping existing image"
            return 0
        fi
        sudo rm -f "$GADGET_IMAGE"
    fi

    log_info "Creating ${GADGET_SIZE_MB}MB image file at $GADGET_IMAGE"
    sudo dd if=/dev/zero of="$GADGET_IMAGE" bs=1M count="$GADGET_SIZE_MB" status=progress

    log_info "Formatting image as FAT32"
    sudo mkfs.vfat -F 32 "$GADGET_IMAGE" >/dev/null

    sudo chmod 644 "$GADGET_IMAGE"

    log_info "USB storage image created successfully"
}

install_service() {
    log_info "Installing systemd service"
    local service_file="$SCRIPT_DIR/$SERVICE_NAME"
    if [[ ! -e "$service_file" ]]; then
        log_error "Service file not found: $service_file"
        exit 1
    fi

    sudo cp "$service_file" /etc/systemd/system/
    log_info "Installed service: $(basename "$service_file")"

    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"

    log_info "Service installed and enabled"
}

initiate_reboot() {
    log_info "Bootstrap completed successfully"
    log_info "Rebooting system in 5 seconds (Ctrl+C to cancel)..."
    sleep 5 &
    wait $! 2>/dev/null || { log_warn "Reboot cancelled"; exit 0; }
    sudo reboot
}

main() {
    log_info "Starting system bootstrap"

    check_privileges
    configure_usb_gadget
    create_storage_image
    install_service
    initiate_reboot
}

main "$@"[Unit]
