#!/bin/bash
#
# Development Tools Verification Script
# Checks that all required development tools are installed
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Verifying development tools installation..."
echo ""

FAILED=0

# Function to check command exists
check_command() {
    local cmd=$1
    local name=$2
    local required=$3
    
    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $name"
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗${NC} $name (required)"
            FAILED=1
        else
            echo -e "${YELLOW}⚠${NC} $name (optional)"
        fi
        return 1
    fi
}

# Function to check Python package
check_python_package() {
    local package=$1
    local name=$2
    
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "${RED}✗${NC} $name (required)"
        FAILED=1
        return 1
    fi
}

# Check Python
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓${NC} Python $VERSION"
else
    echo -e "${RED}✗${NC} Python 3.12+ (required)"
    FAILED=1
fi

# Check Node.js
if command -v node &> /dev/null; then
    VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js $VERSION"
else
    echo -e "${RED}✗${NC} Node.js 18+ (required)"
    FAILED=1
fi

# Check npm
check_command "npm" "npm" "true"

# Check Ruby (for cfn_nag)
if command -v ruby &> /dev/null; then
    VERSION=$(ruby --version | cut -d' ' -f2)
    echo -e "${GREEN}✓${NC} Ruby $VERSION"
else
    echo -e "${YELLOW}⚠${NC} Ruby (needed for cfn_nag)"
fi

# Check AWS CLI
check_command "aws" "AWS CLI" "true"

# Check Git
check_command "git" "Git" "true"

echo ""
echo "Python Development Tools:"

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠${NC} Virtual environment not activated (run: source .venv/bin/activate)"
    echo ""
    echo "Checking if tools are installed in .venv..."
    
    # Try to activate venv temporarily
    if [ -d ".venv" ]; then
        source .venv/bin/activate 2>/dev/null || true
    fi
fi

# Check Python tools
check_command "cfn-lint" "cfn-lint" "true"
check_command "flake8" "flake8" "true"
check_command "black" "black" "true"
check_command "isort" "isort" "true"
check_command "bandit" "bandit" "true"
check_command "detect-secrets" "detect-secrets" "true"
check_command "safety" "safety" "true"
check_command "pytest" "pytest" "true"

echo ""
echo "Security Scanning Tools:"

# Check cfn_nag
check_command "cfn_nag" "cfn_nag" "true"

# Check shellcheck (optional)
check_command "shellcheck" "shellcheck" "false"

echo ""
echo "Frontend Tools:"

# Check TypeScript
if [ -d "frontend/node_modules" ]; then
    if [ -f "frontend/node_modules/.bin/tsc" ]; then
        echo -e "${GREEN}✓${NC} TypeScript"
    else
        echo -e "${RED}✗${NC} TypeScript (run: cd frontend && npm install)"
        FAILED=1
    fi
else
    echo -e "${RED}✗${NC} Frontend dependencies (run: cd frontend && npm install)"
    FAILED=1
fi

echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All required tools are installed!${NC}"
    echo ""
    echo "You're ready to develop. Run:"
    echo "  ./scripts/deploy.sh dev --validate-only    # Test validation pipeline"
    exit 0
else
    echo -e "${RED}✗ Some required tools are missing${NC}"
    echo ""
    echo "Setup instructions:"
    echo "  1. Activate virtual environment: source .venv/bin/activate"
    echo "  2. Install Python tools: pip install -r requirements-dev.txt"
    echo "  3. Install cfn_nag: gem install cfn-nag"
    echo "  4. Install frontend deps: cd frontend && npm install"
    echo ""
    echo "See docs/deployment/DEV_ENVIRONMENT_SETUP.md for detailed setup guide"
    exit 1
fi
