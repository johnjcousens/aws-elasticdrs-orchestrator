#!/bin/bash
#
# Setup Development Environment
# Installs all tools required by ./scripts/deploy.sh
#
# Usage: ./scripts/setup-dev-environment.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Setting up development environment...${NC}\n"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

# 1. Python Virtual Environment
echo -e "${BLUE}[1/4] Python Environment${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}  ✓ Created .venv${NC}"
else
    echo -e "${YELLOW}  ⚠ .venv already exists${NC}"
fi

source .venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements-dev.txt > /dev/null 2>&1
echo -e "${GREEN}  ✓ Installed Python packages${NC}\n"

# 2. Ruby Environment (for cfn_nag)
echo -e "${BLUE}[2/4] Ruby Environment${NC}"
if [ "$OS" = "macos" ]; then
    if ! command -v rbenv &> /dev/null; then
        brew install rbenv
        echo -e "${GREEN}  ✓ Installed rbenv${NC}"
    else
        echo -e "${YELLOW}  ⚠ rbenv already installed${NC}"
    fi
    
    eval "$(rbenv init - bash 2>/dev/null || rbenv init - zsh 2>/dev/null || true)"
    
    if ! rbenv versions | grep -q "3.3.6"; then
        rbenv install 3.3.6
        echo -e "${GREEN}  ✓ Installed Ruby 3.3.6${NC}"
    else
        echo -e "${YELLOW}  ⚠ Ruby 3.3.6 already installed${NC}"
    fi
    
    echo "3.3.6" > .ruby-version
    rbenv local 3.3.6
    
    if ! gem list | grep -q "cfn-nag"; then
        gem install cfn-nag
        echo -e "${GREEN}  ✓ Installed cfn-nag${NC}"
    else
        echo -e "${YELLOW}  ⚠ cfn-nag already installed${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ Ruby setup only supported on macOS${NC}"
    echo -e "${YELLOW}    Install manually: apt-get install ruby-full && gem install cfn-nag${NC}"
fi
echo ""

# 3. System Tools
echo -e "${BLUE}[3/4] System Tools${NC}"
TOOLS=("shellcheck" "grype" "syft" "git-secrets" "jq")

if [ "$OS" = "macos" ]; then
    for tool in "${TOOLS[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            brew install "$tool"
            echo -e "${GREEN}  ✓ Installed $tool${NC}"
        else
            echo -e "${YELLOW}  ⚠ $tool already installed${NC}"
        fi
    done
else
    echo -e "${YELLOW}  ⚠ System tools setup only supported on macOS${NC}"
    echo -e "${YELLOW}    Install manually: apt-get install shellcheck jq${NC}"
    echo -e "${YELLOW}    grype/syft: https://github.com/anchore/grype${NC}"
fi
echo ""

# 4. Node.js (frontend)
echo -e "${BLUE}[4/4] Node.js Environment${NC}"
if [ -d "frontend" ]; then
    cd frontend
    if [ -f "package.json" ]; then
        npm install > /dev/null 2>&1
        echo -e "${GREEN}  ✓ Installed frontend dependencies${NC}"
    fi
    cd ..
else
    echo -e "${YELLOW}  ⚠ frontend/ directory not found${NC}"
fi
echo ""

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Development environment ready${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Activate Python environment: source .venv/bin/activate"
echo "Run deployment: ./scripts/deploy.sh dev"
