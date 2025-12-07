#!/bin/bash
# Package orchestration_stepfunctions Lambda function

set -e

echo "Packaging orchestration_stepfunctions Lambda..."

# Create temp directory
TEMP_DIR=$(mktemp -d)
echo "Using temp directory: $TEMP_DIR"

# Copy Lambda function
cp orchestration_stepfunctions.py "$TEMP_DIR/index.py"

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt -t "$TEMP_DIR" --quiet
fi

# Create ZIP file
cd "$TEMP_DIR"
zip -r ../orchestration-stepfunctions.zip . > /dev/null
cd -

# Move ZIP to lambda directory
mv orchestration-stepfunctions.zip .

# Cleanup
rm -rf "$TEMP_DIR"

echo "✅ Package created: orchestration-stepfunctions.zip"
ls -lh orchestration-stepfunctions.zip
