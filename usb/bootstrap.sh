#!/bin/bash
set -euo pipefail

readonly CUR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly GADGET_IMAGE="/usb.img"
readonly GADGET_SIZE_MB=4096
readonly SERVICE="usb.service"
readonly USB_SCRIPT_DEST="/usr/local/bin/usb.sh"

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
    sudo fallocate -l "${GADGET_SIZE_MB}M" "$GADGET_IMAGE"

    log_info "Formatting image as FAT32"
    sudo mkfs.vfat -F 32 "$GADGET_IMAGE" >/dev/null

    sudo chmod 644 "$GADGET_IMAGE"

    log_info "USB storage image created successfully"
}

install_rclone() {
    if command -v rclone &>/dev/null; then
        log_info "rclone already installed: $(rclone --version | head -1)"
        return 0
    fi

    log_info "Installing rclone"
    sudo apt-get install -y rclone
    log_info "rclone installed: $(rclone --version | head -1)"
}

install_usb_script() {
    log_info "Installing usb.sh"
    local script_file="$CUR_DIR/usb.sh"
    if [[ ! -e "$script_file" ]]; then
        log_error "usb.sh not found: $script_file"
        exit 1
    fi

    sudo cp "$script_file" "$USB_SCRIPT_DEST"
    sudo chmod +x "$USB_SCRIPT_DEST"
    log_info "Installed usb.sh to $USB_SCRIPT_DEST"
}

install_service() {
    log_info "Installing systemd service"
    local service_file="$CUR_DIR/$SERVICE"
    if [[ ! -e "$service_file" ]]; then
        log_error "Service file not found: $service_file"
        exit 1
    fi

    sudo cp "$service_file" /etc/systemd/system/
    log_info "Installed service: $(basename "$service_file")"

    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE"

    log_info "Service installed and enabled"
}

configure_rclone() {
    sudo rclone config
}

main() {
    log_info "Starting system bootstrap"

    check_privileges
    configure_usb_gadget
    create_storage_image
    install_rclone
    configure_rclone
    install_usb_script
    install_service
}

main "$@"
