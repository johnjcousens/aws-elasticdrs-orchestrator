#!/bin/bash

# Document Sync Script
# Syncs OneDrive documents to WorkDocs every 2 hours
# Can be run manually or via launchd

SOURCE_DIR="/Users/jocousen/Library/CloudStorage/OneDrive-amazon.com/DOCUMENTS"
TARGET_DIR="/Users/jocousen/Library/CloudStorage/WorkDocsDrive-Documents/DOCUMENTS"
LOG_FILE="$HOME/Library/Logs/document-sync.log"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to perform sync
sync_documents() {
    log_message "Starting document sync..."
    
    # Check if source directory exists
    if [ ! -d "$SOURCE_DIR" ]; then
        log_message "ERROR: Source directory does not exist: $SOURCE_DIR"
        exit 1
    fi
    
    # Create target directory if it doesn't exist
    if [ ! -d "$TARGET_DIR" ]; then
        log_message "Creating target directory: $TARGET_DIR"
        mkdir -p "$TARGET_DIR"
    fi
    
    # Perform sync using rsync
    if rsync -av --delete "$SOURCE_DIR/" "$TARGET_DIR/"; then
        log_message "Sync completed successfully"
    else
        log_message "ERROR: Sync failed with exit code $?"
        exit 1
    fi
}

# Main execution
sync_documents