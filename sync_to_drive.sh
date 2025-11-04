#!/bin/bash
# sync_to_drive.sh
# Copies files from your local Git repo to your Google Drive working folder.
# Use this after pulling or committing new changes to GitHub.

set -e  # Exit if anything fails

# --- Paths ---
LOCAL_DIR="/Users/christopherhenderson/Documents/PubCoDatabaseLocal"
DRIVE_DIR="/Users/christopherhenderson/Library/CloudStorage/GoogleDrive-clhenderson@gmail.com/My Drive/PubCoDatabase"

echo "🔁 Syncing Local → Drive..."
rsync -av --exclude '.git' "$LOCAL_DIR/" "$DRIVE_DIR/"

echo "✅ Drive copy updated successfully."
