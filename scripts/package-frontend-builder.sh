#!/bin/bash
# Package frontend-builder Lambda with React source code bundled
# This creates a self-contained Lambda that can build and deploy the frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="$PROJECT_ROOT/lambda"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "================================================"
echo "Packaging frontend-builder Lambda with frontend source"
echo "================================================"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "Step 1: Extract existing frontend-builder.zip..."
cd "$TEMP_DIR"
unzip -q "$LAMBDA_DIR/frontend-builder.zip"

echo "Step 2: Copy frontend source (excluding build artifacts)..."
mkdir -p frontend
rsync -av \
  --exclude 'node_modules' \
  --exclude 'dist' \
  --exclude '.git' \
  --exclude '.DS_Store' \
  --exclude '*.log' \
  --exclude 'dev.sh' \
  "$FRONTEND_DIR/" frontend/

echo "Step 3: Create new frontend-builder.zip..."
zip -r "$LAMBDA_DIR/frontend-builder.zip" . -q

# Get size information
OLD_SIZE=$(unzip -l "$LAMBDA_DIR/frontend-builder.zip" 2>/dev/null | tail -1 | awk '{print $1}')
NEW_SIZE=$(du -h "$LAMBDA_DIR/frontend-builder.zip" | awk '{print $1}')

echo ""
echo "================================================"
echo "✅ Success! frontend-builder.zip updated"
echo "================================================"
echo "Package size: $NEW_SIZE"
echo "Contents:"
unzip -l "$LAMBDA_DIR/frontend-builder.zip" | head -20
echo ""
echo "Total files: $(unzip -l "$LAMBDA_DIR/frontend-builder.zip" | tail -1 | awk '{print $2}')"
echo ""
echo "Frontend source is now bundled with Lambda!"
echo "Lambda can access frontend at: /var/task/frontend/"
