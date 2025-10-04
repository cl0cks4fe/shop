#!/bin/bash
set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly GADGET_IMAGE="/gadget.img"
readonly GADGET_SIZE_MB=2048
readonly SERVICE_NAME="gadget.service"

# Logging functions
log_info() {
    echo "[INFO] $*"
}

log_warn() {
    echo "[WARN] $*" >&2
}

log_error() {
    echo "[ERROR] $*" >&2
}

# Check if running as root or with sudo
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

# Check if system is already bootstrapped
check_bootstrap_status() {
    log_info "Checking bootstrap status"

    if grep -q "g_mass_storage" /boot/cmdline.txt 2>/dev/null; then
        log_info "System already bootstrapped, exiting"
        exit 0
    fi

    log_info "System not bootstrapped, proceeding with setup"
}

# Determine boot directory
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

# Configure USB gadget mode
configure_usb_gadget() {
    local boot_dir
    boot_dir=$(detect_boot_directory)

    log_info "Configuring USB gadget mode"
    log_info "Using boot directory: $boot_dir"

    # Add dtoverlay to config.txt
    echo "dtoverlay=dwc2" | sudo tee -a "$boot_dir/config.txt" >/dev/null
    log_info "Added dtoverlay=dwc2 to config.txt"

    # Update cmdline.txt
    sudo sed -i 's/$/ modules-load=dwc2,g_mass_storage file=\/gadget.img/' "$boot_dir/cmdline.txt"
    log_info "Updated cmdline.txt with USB gadget parameters"
}

# Create USB storage image
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
    sudo dd if=/dev/zero of="$GADGET_IMAGE" bs=1M count="$GADGET_SIZE_MB" status=progress 2>/dev/null

    log_info "Formatting image as FAT32"
    sudo mkfs.vfat -F 32 "$GADGET_IMAGE" >/dev/null

    # Set appropriate permissions
    sudo chmod 644 "$GADGET_IMAGE"

    log_info "USB storage image created successfully"
}

# Install systemd services
install_services() {
    log_info "Installing systemd services"

    local service_files=("$SCRIPT_DIR/files"/*.service)
    if [[ ! -e "${service_files[0]}" ]]; then
        log_error "No service files found in $SCRIPT_DIR/files/"
        exit 1
    fi

    # Copy service files
    for service_file in "${service_files[@]}"; do
        local service_name
        service_name=$(basename "$service_file")
        sudo cp "$service_file" /etc/systemd/system/
        log_info "Installed service: $service_name"
    done

    # Reload systemd and enable services
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"

    log_info "Services installed and enabled"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation"

    # Check if gadget image exists and is properly sized
    if [[ ! -f "$GADGET_IMAGE" ]]; then
        log_error "Gadget image not found at $GADGET_IMAGE"
        return 1
    fi

    local image_size
    image_size=$(stat -c%s "$GADGET_IMAGE" 2>/dev/null || echo 0)
    local expected_size=$((GADGET_SIZE_MB * 1024 * 1024))

    if [[ "$image_size" -ne "$expected_size" ]]; then
        log_warn "Gadget image size mismatch (expected: $expected_size, actual: $image_size)"
    else
        log_info "Gadget image size verified"
    fi

    # Check if service is enabled
    if sudo systemctl is-enabled "$SERVICE_NAME" >/dev/null 2>&1; then
        log_info "Service $SERVICE_NAME is enabled"
    else
        log_error "Service $SERVICE_NAME is not enabled"
        return 1
    fi

    log_info "Installation verification completed"
}

# Initiate system reboot
initiate_reboot() {
    log_info "Bootstrap completed successfully"
    log_info "System reboot required to activate USB gadget mode"

    read -p "Reboot now? (Y/n): " -r response
    if [[ "$response" =~ ^[Nn]$ ]]; then
        log_info "Reboot postponed. Please reboot manually to complete setup."
        return 0
    fi

    log_info "Rebooting system in 5 seconds..."
    sleep 5
    sudo reboot
}

# Main bootstrap function
main() {
    log_info "Starting system bootstrap"

    check_privileges
    check_bootstrap_status
    configure_usb_gadget
    create_storage_image
    install_services
    verify_installation
    initiate_reboot
}

# Run main function
main "$@"
