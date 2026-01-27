#!/bin/bash
# Safe push script with local CI/CD pipeline validation
# Mimics GitHub Actions workflow locally before pushing to GitLab
# Usage: ./scripts/safe-push.sh [branch] [options]

set -e

# Configuration
DEFAULT_BRANCH="main"
FORCE_PUSH=false
SKIP_VALIDATION=false
SKIP_SECURITY=false
SKIP_TESTS=false
SKIP_BUILD=false
DEPLOY_FRONTEND=false
TARGET_BRANCH=""
GITLAB_HOST="code.aws.dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_PUSH=true
            SKIP_VALIDATION=true
            SKIP_SECURITY=true
            SKIP_TESTS=true
            SKIP_BUILD=true
            echo -e "${YELLOW}🚨 FORCE MODE: Skipping ALL quality checks${NC}"
            shift
            ;;
        --skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --skip-security)
            SKIP_SECURITY=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --quick)
            SKIP_SECURITY=true
            SKIP_TESTS=true
            echo -e "${YELLOW}⚡ QUICK MODE: Skipping security and tests${NC}"
            shift
            ;;
        --deploy)
            DEPLOY_FRONTEND=true
            echo -e "${CYAN}🚀 DEPLOY MODE: Will deploy frontend after push (if changed)${NC}"
            shift
            ;;
        --help)
            echo "Usage: $0 [branch] [options]"
            echo ""
            echo "Safe push script with local CI/CD pipeline validation"
            echo "Mimics GitHub Actions workflow before pushing to GitLab"
            echo ""
            echo "Arguments:"
            echo "  branch              Target branch (default: current branch or main)"
            echo ""
            echo "Options:"
            echo "  --force             Skip ALL checks (emergency only)"
            echo "  --quick             Skip security and tests (faster)"
            echo "  --deploy            Deploy frontend after push"
            echo "  --skip-validation   Skip validation stage"
            echo "  --skip-security     Skip security scans"
            echo "  --skip-tests        Skip unit tests"
            echo "  --skip-build        Skip build stage"
            echo "  --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Full CI/CD pipeline + push"
            echo "  $0 main                      # Push to main with full checks"
            echo "  $0 --quick                   # Quick validation + push"
            echo "  $0 --force                   # Emergency push (skip all checks)"
            echo ""
            echo "🚀 RECOMMENDED WORKFLOW:"
            echo "  git add ."
            echo "  git commit -m 'description'"
            echo "  $0                           # Safe push with full CI/CD"
            echo ""
            echo "⚡ QUICK DEVELOPMENT WORKFLOW:"
            echo "  git add ."
            echo "  git commit -m 'description'"
            echo "  $0 --quick                   # Quick validation + push"
            echo ""
            echo "🔒 QUALITY GATES (mirrors GitHub Actions):"
            echo "  1. Validation    - CloudFormation, Python, Frontend, CloudScape"
            echo "  2. Security Scan - Bandit, Semgrep, Safety, NPM Audit"
            echo "  3. Build         - Lambda packages, Frontend validation"
            echo "  4. Test          - Python unit tests, Frontend tests"
            echo "  5. Push          - Git push to GitLab"
            exit 0
            ;;
        *)
            if [ -z "$TARGET_BRANCH" ]; then
                TARGET_BRANCH="$1"
            else
                echo "Unknown option: $1"
                echo "Run '$0 --help' for usage information"
                exit 1
            fi
            shift
            ;;
    esac
done

# Determine target branch
if [ -z "$TARGET_BRANCH" ]; then
    if git rev-parse --git-dir > /dev/null 2>&1; then
        TARGET_BRANCH=$(git branch --show-current 2>/dev/null || echo "$DEFAULT_BRANCH")
    else
        TARGET_BRANCH="$DEFAULT_BRANCH"
    fi
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Safe Push with Local CI/CD Pipeline                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Target Branch:${NC}    $TARGET_BRANCH"
echo -e "${GREEN}Force Mode:${NC}       $FORCE_PUSH"
echo -e "${GREEN}Skip Validation:${NC}  $SKIP_VALIDATION"
echo -e "${GREEN}Skip Security:${NC}    $SKIP_SECURITY"
echo -e "${GREEN}Skip Tests:${NC}       $SKIP_TESTS"
echo -e "${GREEN}Skip Build:${NC}       $SKIP_BUILD"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes${NC}"
    echo ""
    echo "Uncommitted files:"
    git status --porcelain
    echo ""
    echo "Please commit your changes first:"
    echo "  git add ."
    echo "  git commit -m 'your commit message'"
    echo "  $0"
    exit 1
fi

# Show warning for skipped checks
if [ "$SKIP_VALIDATION" = true ] || [ "$SKIP_SECURITY" = true ] || [ "$SKIP_TESTS" = true ]; then
    echo -e "${YELLOW}⚠️  WARNING: Quality gates are being skipped!${NC}"
    [ "$SKIP_VALIDATION" = true ] && echo -e "${YELLOW}   - Validation checks skipped${NC}"
    [ "$SKIP_SECURITY" = true ] && echo -e "${YELLOW}   - Security scans skipped${NC}"
    [ "$SKIP_TESTS" = true ] && echo -e "${YELLOW}   - Unit tests skipped${NC}"
    [ "$SKIP_BUILD" = true ] && echo -e "${YELLOW}   - Build stage skipped${NC}"
    echo ""
    echo -e "${YELLOW}This is NOT recommended for production code.${NC}"
    echo ""
    
    if [ "$FORCE_PUSH" = false ]; then
        read -p "Continue anyway? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            echo "Push cancelled."
            exit 1
        fi
        echo ""
    fi
fi

# ============================================================================
# LOCAL CI/CD PIPELINE (mirrors GitHub Actions)
# ============================================================================

if [ "$FORCE_PUSH" = false ]; then
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  LOCAL CI/CD PIPELINE (GitHub Actions Simulation)${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    PIPELINE_START=$(date +%s)
    
    # Build CI check arguments
    CI_CHECK_ARGS=""
    [ "$SKIP_TESTS" = true ] && CI_CHECK_ARGS="$CI_CHECK_ARGS --skip-tests"
    [ "$SKIP_SECURITY" = true ] && CI_CHECK_ARGS="$CI_CHECK_ARGS --skip-security"
    
    # Run CI checks (unless all validation is skipped)
    if [ "$SKIP_VALIDATION" = false ] || [ "$SKIP_SECURITY" = false ] || [ "$SKIP_TESTS" = false ]; then
        echo -e "${BLUE}Running CI/CD quality checks...${NC}"
        echo ""
        
        if ./scripts/local-ci-checks.sh $CI_CHECK_ARGS; then
            echo ""
            echo -e "${GREEN}✅ All CI/CD quality checks passed${NC}"
        else
            echo ""
            echo -e "${RED}❌ CI/CD quality checks failed${NC}"
            echo ""
            echo "Fix the issues above before pushing, or use:"
            echo "  $0 $TARGET_BRANCH --quick      # Skip security and tests"
            echo "  $0 $TARGET_BRANCH --force      # Skip all checks (emergency only)"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  All CI/CD checks skipped${NC}"
    fi
    
    # Build stage (unless skipped)
    if [ "$SKIP_BUILD" = false ]; then
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${CYAN}  BUILD STAGE${NC}"
        echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        
        # Get log directory from local-ci-checks.sh (use latest symlink)
        BUILD_LOG_DIR="docs/logs/latest/build"
        if [ ! -d "$BUILD_LOG_DIR" ]; then
            # Fallback if latest doesn't exist yet
            TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
            BUILD_LOG_DIR="docs/logs/runs/$TIMESTAMP/build"
            
            # Clean up logs older than 30 days
            if [ -d "docs/logs/runs" ]; then
                find "docs/logs/runs" -type d -mindepth 1 -maxdepth 1 -mtime +30 -exec rm -rf {} + 2>/dev/null || true
            fi
            
            mkdir -p "$BUILD_LOG_DIR"
        fi
        
        echo -e "${BLUE}Building Lambda packages...${NC}"
        BUILD_START=$(date +%s)
        
        if python3 package_lambda.py > "$BUILD_LOG_DIR/lambda-build.log" 2>&1; then
            BUILD_END=$(date +%s)
            BUILD_DURATION=$((BUILD_END - BUILD_START))
            
            echo -e "${GREEN}✅ Lambda packages built successfully (${BUILD_DURATION}s)${NC}"
            echo ""
            echo "Package sizes:"
            ls -lh build/lambda/*.zip | awk '{print "  " $9 ": " $5}' | tee "$BUILD_LOG_DIR/package-sizes.txt"
            
            # Log build metadata
            cat > "$BUILD_LOG_DIR/build-metadata.txt" << EOF
Lambda Build Metadata
=====================
Build Time: $(date)
Duration: ${BUILD_DURATION}s
Status: SUCCESS
Packages Built: $(ls -1 build/lambda/*.zip 2>/dev/null | wc -l)
Total Size: $(du -sh build/lambda 2>/dev/null | awk '{print $1}')

Package Details:
$(ls -lh build/lambda/*.zip 2>/dev/null)
EOF
        else
            BUILD_END=$(date +%s)
            BUILD_DURATION=$((BUILD_END - BUILD_START))
            
            echo -e "${RED}❌ Lambda package build failed (${BUILD_DURATION}s)${NC}"
            echo "See log: $BUILD_LOG_DIR/lambda-build.log"
            tail -20 "$BUILD_LOG_DIR/lambda-build.log"
            
            # Log build failure
            cat > "$BUILD_LOG_DIR/build-metadata.txt" << EOF
Lambda Build Metadata
=====================
Build Time: $(date)
Duration: ${BUILD_DURATION}s
Status: FAILED

Error Log:
$(tail -50 "$BUILD_LOG_DIR/lambda-build.log")
EOF
            exit 1
        fi
        
        echo ""
        echo -e "${BLUE}Validating frontend dependencies...${NC}"
        if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
            cd frontend
            if [ ! -d "node_modules" ]; then
                echo "Installing frontend dependencies..."
                npm ci --silent > "../$BUILD_LOG_DIR/frontend-install.log" 2>&1
            fi
            
            # Log frontend dependency info
            npm list --depth=0 > "../$BUILD_LOG_DIR/frontend-dependencies.txt" 2>&1 || true
            
            echo -e "${GREEN}✅ Frontend dependencies validated${NC}"
            echo -e "${CYAN}ℹ️  Frontend will be built by FrontendBuilder Lambda during deployment${NC}"
            cd ..
        else
            echo -e "${YELLOW}⚠️  Frontend directory not found${NC}"
        fi
        
        echo ""
        echo "📊 Build logs saved to: $BUILD_LOG_DIR"
    else
        echo ""
        echo -e "${YELLOW}⚠️  Build stage skipped${NC}"
    fi
    
    PIPELINE_END=$(date +%s)
    PIPELINE_DURATION=$((PIPELINE_END - PIPELINE_START))
    
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  PIPELINE SUMMARY${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}✅ Local CI/CD pipeline completed successfully${NC}"
    echo -e "${GREEN}Duration: ${PIPELINE_DURATION}s${NC}"
    echo ""
    echo "Pipeline stages completed:"
    [ "$SKIP_VALIDATION" = false ] && echo "  ✅ Validation (CloudFormation, Python, Frontend, CloudScape)"
    [ "$SKIP_SECURITY" = false ] && echo "  ✅ Security Scan (Bandit, Semgrep, Safety, NPM Audit)"
    [ "$SKIP_BUILD" = false ] && echo "  ✅ Build (Lambda packages, Frontend validation)"
    [ "$SKIP_TESTS" = false ] && echo "  ✅ Test (Python unit tests, Frontend tests)"
    echo ""
    echo "📊 Reports available in: reports/"
    echo ""
else
    echo -e "${YELLOW}⚠️  FORCE MODE: Skipping entire CI/CD pipeline${NC}"
    echo ""
fi

# ============================================================================
# GIT PUSH
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  GIT PUSH${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo "🚀 Pushing to $TARGET_BRANCH..."

# Perform the git push
if git push origin "$TARGET_BRANCH"; then
    echo ""
    echo -e "${GREEN}✅ Successfully pushed to $TARGET_BRANCH${NC}"
    echo ""
    
else
    echo ""
    echo -e "${RED}❌ Push failed${NC}"
    echo ""
    echo "Common solutions:"
    echo "  1. Pull latest changes: git pull origin $TARGET_BRANCH"
    echo "  2. Resolve any merge conflicts"
    echo "  3. Try pushing again: $0 $TARGET_BRANCH"
    exit 1
fi

# ============================================================================
# FRONTEND DEPLOYMENT (if --deploy flag and frontend changed)
# ============================================================================

if [ "$DEPLOY_FRONTEND" = true ]; then
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  FRONTEND DEPLOYMENT CHECK${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Check if frontend files changed in recent commits (last 5 commits vs origin)
    FRONTEND_CHANGED=$(git diff --name-only origin/$TARGET_BRANCH HEAD -- frontend/ 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$FRONTEND_CHANGED" -gt 0 ] 2>/dev/null; then
        echo -e "${BLUE}📦 Frontend changes detected ($FRONTEND_CHANGED files)${NC}"
        echo ""
        
        # Trigger FrontendBuilder Lambda to rebuild and deploy
        echo -e "${BLUE}🚀 Triggering FrontendBuilder Lambda...${NC}"
        
        # Get the FrontendBuilder Lambda function name
        FRONTEND_BUILDER_LAMBDA="aws-drs-orch-frontend-builder-dev"
        
        # Invoke the Lambda to rebuild frontend
        if AWS_PAGER="" aws lambda invoke \
            --function-name "$FRONTEND_BUILDER_LAMBDA" \
            --payload '{"RequestType": "Update", "ResourceProperties": {"TriggerRebuild": "true"}}' \
            --cli-binary-format raw-in-base64-out \
            /tmp/frontend-builder-response.json \
            --region us-east-1 > /dev/null 2>&1; then
            
            echo -e "${GREEN}✅ FrontendBuilder Lambda triggered${NC}"
            
            # Check response
            if [ -f /tmp/frontend-builder-response.json ]; then
                RESPONSE=$(cat /tmp/frontend-builder-response.json)
                if echo "$RESPONSE" | grep -q '"statusCode": 200\|"Status": "SUCCESS"'; then
                    echo -e "${GREEN}✅ Frontend deployed successfully${NC}"
                else
                    echo -e "${YELLOW}⚠️  Frontend deployment response: $RESPONSE${NC}"
                fi
                rm -f /tmp/frontend-builder-response.json
            fi
        else
            echo -e "${YELLOW}⚠️  Could not trigger FrontendBuilder Lambda${NC}"
            echo "You can manually deploy with: ./scripts/local-deploy.sh dev full"
        fi
    else
        echo -e "${GREEN}✅ No frontend changes detected - skipping deployment${NC}"
    fi
    echo ""
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Safe Push Complete                                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ Local CI/CD pipeline passed${NC}"
echo -e "${GREEN}✅ Code pushed to GitLab${NC}"
[ "$DEPLOY_FRONTEND" = true ] && [ "$FRONTEND_CHANGED" -gt 0 ] 2>/dev/null && echo -e "${GREEN}✅ Frontend deployed${NC}"
echo ""
echo "Your code has been validated locally and pushed to GitLab."
[ "$DEPLOY_FRONTEND" = false ] && echo "Use ./scripts/local-deploy.sh to deploy to AWS."
echo ""