#!/bin/bash
# Package frontend-builder Lambda with Python dependencies AND React source code
# This creates a self-contained Lambda that can build and deploy the frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="$PROJECT_ROOT/lambda"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "================================================"
echo "Packaging frontend-builder Lambda with dependencies + frontend source"
echo "================================================"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap 'rm -rf $TEMP_DIR' EXIT

cd "$TEMP_DIR"

echo "Step 1: Copy Python source files from lambda directory..."
cp "$LAMBDA_DIR/build_and_deploy.py" . 2>/dev/null || {
    echo "ERROR: build_and_deploy.py not found in $LAMBDA_DIR"
    exit 1
}

cp "$LAMBDA_DIR/requirements.txt" . 2>/dev/null || {
    # Try to extract requirements.txt from existing zip as fallback
    unzip -q "$LAMBDA_DIR/frontend-builder.zip" "requirements.txt" 2>/dev/null || {
        echo "ERROR: requirements.txt not found"
        exit 1
    }
}

echo "Step 2: Install Python dependencies..."
echo "Installing: $(cat requirements.txt)"
pip3 install -r requirements.txt -t . --upgrade --quiet

echo "Step 3: Build React frontend..."
cd "$FRONTEND_DIR"
echo "  Installing npm dependencies..."
npm ci --silent
echo "  Building production bundle..."
npx vite build
BUILD_SIZE=$(du -sh dist 2>/dev/null | awk '{print $1}' || echo "N/A")
echo "  ✅ Build complete (dist size: $BUILD_SIZE)"
cd "$TEMP_DIR"

echo "Step 4: Copy frontend source WITH pre-built dist/..."
mkdir -p frontend
rsync -av \
  --exclude 'node_modules' \
  --exclude '.git' \
  --exclude '.DS_Store' \
  --exclude '*.log' \
  --exclude 'dev.sh' \
  "$FRONTEND_DIR/" frontend/

echo "Step 5: Create new frontend-builder.zip with ALL components..."
zip -r "$LAMBDA_DIR/frontend-builder.zip" . -q

# Get size information
NEW_SIZE=$(du -h "$LAMBDA_DIR/frontend-builder.zip" | awk '{print $1}')
FILE_COUNT=$(unzip -l "$LAMBDA_DIR/frontend-builder.zip" | tail -1 | awk '{print $2}')

echo ""
echo "================================================"
echo "✅ Success! frontend-builder.zip rebuilt with dependencies"
echo "================================================"
echo "Package size: $NEW_SIZE"
echo "Total files: $FILE_COUNT"
echo ""
echo "Package contents (first 30 files):"
unzip -l "$LAMBDA_DIR/frontend-builder.zip" | head -35
echo ""
echo "Python dependencies installed:"
ls -1 | grep -E "^(crhelper|boto3|botocore)" | head -10
echo ""
echo "Frontend source bundled: $(find frontend -type f | wc -l) files"
echo ""
echo "Lambda package ready for deployment!"
