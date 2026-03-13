#!/bin/bash
set -euo pipefail

readonly APP_DIR="/usr/local/bin/gadget/server"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SERVICE_NAME="gadget-server.service"

readonly HEALTH_URL="http://localhost:3000/status"
readonly HEALTH_TIMEOUT=30
readonly HEALTH_RETRIES=10

BACKUP_DIR=""

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

setup_device_name() {
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

stop_service() {
    log_info "Stopping $SERVICE_NAME service"

    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        sudo systemctl stop "$SERVICE_NAME"
        log_info "Service stopped"
    else
        log_info "Service was not running"
    fi
}

backup_existing() {
    if [[ -d "$APP_DIR" ]]; then
        BACKUP_DIR="$APP_DIR.backup-$(date +%Y%m%d-%H%M%S)"
        log_info "Backing up existing installation to $BACKUP_DIR"
        sudo mv "$APP_DIR" "$BACKUP_DIR"
    else
        log_info "No existing installation found"
    fi
}

install_files() {
    log_info "Installing application files to $APP_DIR"

    sudo mkdir -p "$APP_DIR"
    sudo cp -r "$SCRIPT_DIR"/* "$APP_DIR"/
    sudo rm -f "$APP_DIR/install.sh"

    log_info "Files installed successfully"
}

setup_python_env() {
    log_info "Setting up Python virtual environment"

    if [[ -d "$APP_DIR/venv" ]]; then
        sudo rm -rf "$APP_DIR/venv"
    fi

    sudo python3 -m venv "$APP_DIR/venv"

    log_info "Installing Python dependencies"
    sudo "$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
    sudo "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

    log_info "Python environment configured"
}

setup_port_forwarding() {
    log_info "Setting up port forwarding from 80 to 3000"

    sudo systemctl enable nftables 2>/dev/null || true
    sudo systemctl start nftables 2>/dev/null || true

    sudo nft add table ip nat
    sudo nft 'add chain ip nat prerouting { type nat hook prerouting priority 0 ; }'

    if ! sudo nft list chain ip nat prerouting 2>/dev/null | grep -q "tcp dport 80 redirect to :3000"; then
        sudo nft add rule ip nat prerouting tcp dport 80 redirect to :3000
        log_info "Port forwarding rule added"
    else
        log_info "Port forwarding rule already exists"
        return 0
    fi

    sudo nft list ruleset | sudo tee /etc/nftables.conf >/dev/null

    log_info "Port forwarding configured - service will be accessible on port 80"
}

configure_service() {
    log_info "Configuring systemd service"

    local service_file="$SCRIPT_DIR/$SERVICE_NAME"
    if [[ ! -e "$service_file" ]]; then
        log_error "Service file not found: $service_file"
        exit 1
    fi

    sudo cp "$service_file" /etc/systemd/system/
    log_info "Installed service: $(basename "$service_file")"

    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    sudo systemctl start "$SERVICE_NAME"

    log_info "Service configuration completed"
}

check_server_health() {
    log_info "Checking server health at $HEALTH_URL"

    local retries=0
    while [[ $retries -lt $HEALTH_RETRIES ]]; do
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

restore_backup() {
    if [[ -n "$BACKUP_DIR" && -d "$BACKUP_DIR" ]]; then
        log_warn "Restoring previous installation from backup"

        sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true

        if [[ -d "$APP_DIR" ]]; then
            sudo rm -rf "$APP_DIR"
        fi

        sudo mv "$BACKUP_DIR" "$APP_DIR"

        sudo systemctl start "$SERVICE_NAME"

        log_info "Previous installation restored"
    else
        log_warn "No backup available to restore"
    fi
}

cleanup_backup() {
    if [[ -n "$BACKUP_DIR" && -d "$BACKUP_DIR" ]]; then
        log_info "Removing backup directory $BACKUP_DIR"
        sudo rm -rf "$BACKUP_DIR"
        log_info "Backup cleaned up"
    fi
}

main() {
    log_info "Starting gadget server installation"
    log_info "Source directory: $SCRIPT_DIR"
    log_info "Installation directory: $APP_DIR"

    check_privileges
    setup_device_name
    stop_service
    backup_existing
    install_files
    setup_python_env
    setup_port_forwarding
    configure_service

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

main "$@"
