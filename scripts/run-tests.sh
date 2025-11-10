#!/bin/bash

# AWS DRS Orchestration - Test Execution Script
# Wrapper for running Playwright tests via Cline MCP
# Usage: ./scripts/run-tests.sh [smoke|crud|all]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default to smoke tests
TEST_SUITE=${1:-smoke}

echo -e "${BLUE}=== AWS DRS Orchestration Test Suite ===${NC}"
echo ""

# Check if .env.test exists
if [ ! -f ".env.test" ]; then
    echo -e "${RED}Error: .env.test file not found${NC}"
    echo "Please run: ./scripts/create-test-user.sh first"
    exit 1
fi

# Load test environment
export $(grep -v '^#' .env.test | xargs)

echo -e "${GREEN}Test Configuration:${NC}"
echo "  Base URL: $CLOUDFRONT_URL"
echo "  API Endpoint: $API_ENDPOINT"
echo "  Test User: $TEST_USER_USERNAME"
echo "  Headless: ${HEADLESS:-false}"
echo ""

# Create test results directory
mkdir -p test-results/screenshots

case $TEST_SUITE in
  smoke)
    echo -e "${YELLOW}Running Smoke Tests...${NC}"
    echo "Note: Tests are expected to FAIL initially, confirming button issue"
    echo ""
    
    # Run smoke tests via Playwright MCP
    # User should use Cline's Playwright browser_action tool or
    # run npx playwright test smoke-tests.spec.ts
    echo -e "${BLUE}To run these tests:${NC}"
    echo "1. Via Cline: Use browser_action tool with smoke-tests.spec.ts"
    echo "2. Manually: cd tests/playwright && npx playwright test smoke-tests.spec.ts"
    echo ""
    echo -e "${YELLOW}Note: Playwright must be run via Cline MCP or local installation${NC}"
    ;;
    
  crud)
    echo -e "${YELLOW}Running CRUD Tests...${NC}"
    echo ""
    echo -e "${BLUE}To run these tests:${NC}"
    echo "1. Via Cline: Use browser_action tool with *crud.spec.ts files"
    echo "2. Manually: cd tests/playwright && npx playwright test *crud.spec.ts"
    ;;
    
  all)
    echo -e "${YELLOW}Running All Tests...${NC}"
    echo ""
    echo -e "${BLUE}To run these tests:${NC}"
    echo "1. Via Cline: Use browser_action tool with all spec files"
    echo "2. Manually: cd tests/playwright && npx playwright test"
    ;;
    
  *)
    echo -e "${RED}Error: Unknown test suite '$TEST_SUITE'${NC}"
    echo ""
    echo "Usage: $0 [smoke|crud|all]"
    echo ""
    echo "Test suites:"
    echo "  smoke - Quick validation tests (< 3 minutes)"
    echo "  crud  - Full CRUD operation tests (< 15 minutes)"
    echo "  all   - Complete test suite (< 20 minutes)"
    exit 1
    ;;
esac

echo ""
echo -e "${GREEN}Test execution instructions provided above${NC}"
echo -e "${YELLOW}Results will be saved to: test-results/${NC}"
echo ""
