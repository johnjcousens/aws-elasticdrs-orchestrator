#!/bin/bash
set -e

# Automated E2E Test Runner
# Runs Playwright tests against deployed CloudFront application

echo "=========================================="
echo "AWS DRS Orchestration - Automated E2E Tests"
echo "=========================================="
echo ""

# Check if we're in the project root
if [ ! -f "playwright.config.ts" ] && [ ! -d "tests/playwright" ]; then
    echo "❌ Error: Must run from project root or tests/playwright directory"
    exit 1
fi

# Navigate to playwright tests directory
cd tests/playwright

# Check if .env.test exists
if [ ! -f "../../.env.test" ]; then
    echo "❌ Error: .env.test not found"
    echo "Please create .env.test with test credentials"
    exit 1
fi

echo "📦 Installing dependencies..."
npm ci --silent

echo ""
echo "🧪 Running Protection Group selection test..."
echo ""

# Run the specific test file
npx playwright test protection-group-selection.spec.ts \
    --reporter=list \
    --reporter=html

TEST_EXIT_CODE=$?

echo ""
echo "=========================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    echo "=========================================="
    echo ""
    echo "Test Report: tests/playwright/test-results/html-report/index.html"
    exit 0
else
    echo "❌ TESTS FAILED"
    echo "=========================================="
    echo ""
    echo "Check test output above for details"
    echo "Test Report: tests/playwright/test-results/html-report/index.html"
    exit 1
fi
