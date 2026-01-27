#!/bin/bash
#
# Integrated Deployment Workflow
# Complete CI/CD pipeline: Validate → Security → Build → Test → Deploy
#
# Repository Structure:
#   This script works from the repository root directory.
#   All paths are relative to the repository root.
#
# Usage:
#   ./scripts/integrated-deploy.sh [environment] [options]
#
# Arguments:
#   environment: dev (default), test, prod
#
# Options:
#   --skip-validation    Skip validation stage
#   --skip-security      Skip security scans
#   --skip-tests         Skip unit tests
#   --quick              Skip all checks (DANGEROUS)
#   --frontend-only      Deploy frontend only
#   --lambda-only        Deploy Lambda functions only
#   --dry-run            Show what would be deployed
#   --help               Show this help message

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root for all operations
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-dev}"
SKIP_VALIDATION=false
SKIP_SECURITY=false
SKIP_TESTS=false
DEPLOYMENT_TYPE="full"
DRY_RUN=false

# Parse options
shift || true
for arg in "$@"; do
    case $arg in
        --skip-validation)
            SKIP_VALIDATION=true
            ;;
        --skip-security)
            SKIP_SECURITY=true
            ;;
        --skip-tests)
            SKIP_TESTS=true
            ;;
        --quick)
            SKIP_VALIDATION=true
            SKIP_SECURITY=true
            SKIP_TESTS=true
            ;;
        --frontend-only)
            DEPLOYMENT_TYPE="frontend-only"
            ;;
        --lambda-only)
            DEPLOYMENT_TYPE="lambda-only"
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        --help)
            echo "Integrated Deployment Workflow"
            echo ""
            echo "Usage: $0 [environment] [options]"
            echo ""
            echo "Arguments:"
            echo "  environment          dev (default), test, prod"
            echo ""
            echo "Options:"
            echo "  --skip-validation    Skip validation stage"
            echo "  --skip-security      Skip security scans"
            echo "  --skip-tests         Skip unit tests"
            echo "  --quick              Skip all checks (DANGEROUS)"
            echo "  --frontend-only      Deploy frontend only"
            echo "  --lambda-only        Deploy Lambda functions only"
            echo "  --dry-run            Show what would be deployed"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 dev                           # Full deployment with all checks"
            echo "  $0 dev --quick                   # Quick deployment (skip checks)"
            echo "  $0 dev --lambda-only             # Update Lambda functions only"
            echo "  $0 dev --skip-tests              # Deploy without running tests"
            echo "  $0 dev --dry-run                 # Preview deployment"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AWS DRS Orchestration - Integrated Deployment            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Environment:${NC}      $ENVIRONMENT"
echo -e "${GREEN}Deployment Type:${NC}  $DEPLOYMENT_TYPE"
echo -e "${GREEN}Dry Run:${NC}          $DRY_RUN"
echo ""

# Show warnings for skipped checks
if [ "$SKIP_VALIDATION" = true ] || [ "$SKIP_SECURITY" = true ] || [ "$SKIP_TESTS" = true ]; then
    echo -e "${YELLOW}⚠️  WARNING: Quality gates are being skipped!${NC}"
    [ "$SKIP_VALIDATION" = true ] && echo -e "${YELLOW}   - Validation checks skipped${NC}"
    [ "$SKIP_SECURITY" = true ] && echo -e "${YELLOW}   - Security scans skipped${NC}"
    [ "$SKIP_TESTS" = true ] && echo -e "${YELLOW}   - Unit tests skipped${NC}"
    echo ""
fi

# Call the integrated deployment script
./scripts/deploy-with-validation.sh "$ENVIRONMENT" \
    $([ "$SKIP_VALIDATION" = true ] && echo "--skip-validation") \
    $([ "$SKIP_SECURITY" = true ] && echo "--skip-security") \
    $([ "$SKIP_TESTS" = true ] && echo "--skip-tests") \
    $([ "$DEPLOYMENT_TYPE" = "frontend-only" ] && echo "--frontend-only") \
    $([ "$DEPLOYMENT_TYPE" = "lambda-only" ] && echo "--lambda-only") \
    $([ "$DRY_RUN" = true ] && echo "--dry-run")

