#!/bin/bash
# sync_from_drive.sh
# Copies code changes from your Google Drive working folder to your local Git repo
# Then commits and pushes to GitHub.

set -e  # Exit if any command fails

# --- Paths ---
DRIVE_DIR="/Users/christopherhenderson/Library/CloudStorage/GoogleDrive-clhenderson@gmail.com/My Drive/PubCoDatabase"
LOCAL_DIR="/Users/christopherhenderson/Documents/PubCoDatabaseLocal"

echo "🔄 Syncing from Drive → Local..."
rsync -av --exclude '.git' "$DRIVE_DIR/" "$LOCAL_DIR/"

cd "$LOCAL_DIR"

echo "🧾 Checking Git status..."
git add .

# Commit only if there are actual changes
if git diff --cached --quiet; then
  echo "✅ No new changes to commit."
else
  COMMIT_MSG="Sync from Google Drive on $(date '+%Y-%m-%d %H:%M:%S')"
  git commit -m "$COMMIT_MSG"
  git push
  echo "🚀 Changes pushed to GitHub successfully."
fi

echo "✅ Sync complete."
