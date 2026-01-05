#!/bin/bash

# Document Sync Setup Script
# Installs and manages the document sync service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync-documents.sh"
PLIST_FILE="$SCRIPT_DIR/com.user.document-sync.plist"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"
LAUNCHD_PLIST="$LAUNCHD_DIR/com.user.document-sync.plist"

# Function to display usage
usage() {
    echo "Usage: $0 {install|uninstall|start|stop|status|run}"
    echo "  install   - Install the sync service"
    echo "  uninstall - Remove the sync service"
    echo "  start     - Start the sync service"
    echo "  stop      - Stop the sync service"
    echo "  status    - Check service status"
    echo "  run       - Run sync manually"
    exit 1
}

# Function to install the service
install_service() {
    echo "Installing document sync service..."
    
    # Make sync script executable
    chmod +x "$SYNC_SCRIPT"
    
    # Create LaunchAgents directory if it doesn't exist
    mkdir -p "$LAUNCHD_DIR"
    
    # Copy plist file
    cp "$PLIST_FILE" "$LAUNCHD_PLIST"
    
    # Load the service
    launchctl load "$LAUNCHD_PLIST"
    
    echo "Service installed and started successfully"
    echo "Logs will be written to ~/Library/Logs/document-sync*.log"
}

# Function to uninstall the service
uninstall_service() {
    echo "Uninstalling document sync service..."
    
    # Unload the service
    launchctl unload "$LAUNCHD_PLIST" 2>/dev/null || true
    
    # Remove plist file
    rm -f "$LAUNCHD_PLIST"
    
    echo "Service uninstalled successfully"
}

# Function to start the service
start_service() {
    echo "Starting document sync service..."
    launchctl load "$LAUNCHD_PLIST"
    echo "Service started"
}

# Function to stop the service
stop_service() {
    echo "Stopping document sync service..."
    launchctl unload "$LAUNCHD_PLIST"
    echo "Service stopped"
}

# Function to check service status
check_status() {
    if launchctl list | grep -q "com.user.document-sync"; then
        echo "Document sync service is running"
        echo "Next run scheduled every 2 hours"
    else
        echo "Document sync service is not running"
    fi
}

# Function to run sync manually
run_sync() {
    echo "Running document sync manually..."
    "$SYNC_SCRIPT"
}

# Main execution
case "$1" in
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    status)
        check_status
        ;;
    run)
        run_sync
        ;;
    *)
        usage
        ;;
esac