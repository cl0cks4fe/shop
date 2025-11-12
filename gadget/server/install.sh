set -euo pipefail

# Configuration
readonly APP_DIR="/usr/local/bin/gadget/server"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SERVICE_NAME="gadget-server"
readonly HEALTH_URL="http://localhost:3000/ping"
readonly HEALTH_TIMEOUT=30
readonly HEALTH_RETRIES=10

# Global variables
BACKUP_DIR=""

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

# Setup device configuration
setup_device() {
    log_info "Setting up device configuration"

    if [[ ! -f /etc/gadget-device-name ]]; then
        read -p "Enter device name: " -r DEVICE_NAME
        if [[ -z "$DEVICE_NAME" ]]; then
            log_error "Device name cannot be empty"
            exit 1
        fi
        echo "$DEVICE_NAME" | sudo tee /etc/gadget-device-name >/dev/null
        log_info "Device name set to: $DEVICE_NAME"
    else
        log_info "Device name: $(cat /etc/gadget-device-name)"
    fi
}

# Stop the service if running
stop_service() {
    log_info "Stopping $SERVICE_NAME service"

    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        sudo systemctl stop "$SERVICE_NAME"
        log_info "Service stopped"
    else
        log_info "Service was not running"
    fi
}

# Backup existing installation
backup_existing() {
    if [[ -d "$APP_DIR" ]]; then
        BACKUP_DIR="$APP_DIR.backup-$(date +%Y%m%d-%H%M%S)"
        log_info "Backing up existing installation to $BACKUP_DIR"
        sudo mv "$APP_DIR" "$BACKUP_DIR"
    else
        log_info "No existing installation found"
    fi
}

# Install application files
install_files() {
    log_info "Installing application files to $APP_DIR"

    sudo mkdir -p "$APP_DIR"
    sudo cp -r "$SCRIPT_DIR"/* "$APP_DIR"/
    sudo rm -f "$APP_DIR/install.sh"

    log_info "Files installed successfully"
}

# Setup Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment"

    # Remove old virtual environment if it exists
    if [[ -d "$APP_DIR/venv" ]]; then
        sudo rm -rf "$APP_DIR/venv"
    fi

    # Create new virtual environment
    sudo python3 -m venv "$APP_DIR/venv"

    # Install requirements
    log_info "Installing Python dependencies"
    sudo "$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
    sudo "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

    log_info "Python environment configured"
}

# Setup port forwarding from 80 to 3000
setup_port_forwarding() {
    log_info "Setting up port forwarding from 80 to 3000"

    # Ensure nftables is installed
    if ! command -v nft &> /dev/null; then
        log_info "Installing nftables"
        sudo apt-get update -qq
        sudo apt-get install -y nftables
    fi

    # Enable and start nftables service
    sudo systemctl enable nftables
    sudo systemctl start nftables

    # Create nat table if it doesn't exist
    sudo nft add table ip nat 2>/dev/null || true

    # Create prerouting chain if it doesn't exist
    sudo nft add chain ip nat prerouting { type nat hook prerouting priority -100 \; } 2>/dev/null || true

    # Check if rule already exists and add it if not
    if ! sudo nft list chain ip nat prerouting 2>/dev/null | grep -q "tcp dport 80 redirect to :3000"; then
        sudo nft add rule ip nat prerouting tcp dport 80 redirect to :3000
        log_info "Port forwarding rule added"
    else
        log_info "Port forwarding rule already exists"
    fi

    # Save the configuration
    sudo nft list ruleset > /tmp/nftables.conf
    sudo mv /tmp/nftables.conf /etc/nftables.conf

    log_info "Port forwarding configured - service will be accessible on port 80"
}

# Configure and start systemd service
configure_service() {
    log_info "Configuring systemd service"

    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    sudo systemctl start "$SERVICE_NAME"

    log_info "Service configuration completed"
}

# Check server health
check_server_health() {
    log_info "Checking server health at $HEALTH_URL"

    local retries=0
    while [[ $retries -lt $HEALTH_RETRIES ]]; do
        # Wait before checking (give server time to start)
        sleep 3

        if curl --silent --fail --max-time 5 "$HEALTH_URL" >/dev/null 2>&1; then
            log_info "Server health check passed"
            return 0
        fi

        retries=$((retries + 1))
        log_info "Health check attempt $retries/$HEALTH_RETRIES failed, retrying..."
    done

    log_error "Server health check failed after $HEALTH_RETRIES attempts"
    return 1
}

# Restore backup if installation failed
restore_backup() {
    if [[ -n "$BACKUP_DIR" && -d "$BACKUP_DIR" ]]; then
        log_warn "Restoring previous installation from backup"

        # Stop the failed service
        sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true

        # Remove failed installation
        if [[ -d "$APP_DIR" ]]; then
            sudo rm -rf "$APP_DIR"
        fi

        # Restore backup
        sudo mv "$BACKUP_DIR" "$APP_DIR"

        # Restart service with old version
        sudo systemctl start "$SERVICE_NAME"

        log_info "Previous installation restored"
    else
        log_warn "No backup available to restore"
    fi
}

# Clean up backup after successful installation
cleanup_backup() {
    if [[ -n "$BACKUP_DIR" && -d "$BACKUP_DIR" ]]; then
        log_info "Removing backup directory $BACKUP_DIR"
        sudo rm -rf "$BACKUP_DIR"
        log_info "Backup cleaned up"
    fi
}

# Main installation function
main() {
    log_info "Starting gadget server installation"
    log_info "Source directory: $SCRIPT_DIR"
    log_info "Installation directory: $APP_DIR"

    check_privileges
    setup_device
    stop_service
    backup_existing
    install_files
    setup_python_env
    configure_service
    setup_port_forwarding

    # Test if the server is working correctly
    if check_server_health; then
        log_info "Installation completed successfully"
        log_info "Service status: $(sudo systemctl is-active "$SERVICE_NAME")"
        cleanup_backup
    else
        log_error "Installation failed - server health check failed"
        restore_backup
        exit 1
    fi
}

# Run main function
main "$@"
