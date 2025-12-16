#!/bin/bash

echo "🚀 Opening localhost test page..."
echo "📋 Manual steps:"
echo "1. Login with: testuser@example.com / TestPassword123!"
echo "2. Go to Protection Groups"
echo "3. Click 'Create Protection Group'"
echo "4. Select region 'us-west-2'"
echo "5. Check browser console (F12) for debug logs"
echo "6. Look for blue, red, and normal server components"
echo ""

# Try to open browser (works on macOS)
if command -v open &> /dev/null; then
    open "http://localhost:3000"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:3000"
elif command -v start &> /dev/null; then
    start "http://localhost:3000"
else
    echo "Please manually open: http://localhost:3000"
fi

echo "✅ Browser should be opening..."
echo "📊 Check the console output above for any errors"