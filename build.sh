#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
flask db upgrade

# Optional: Sync with Google Sheet (uncomment if needed)
# flask sync-sheet 