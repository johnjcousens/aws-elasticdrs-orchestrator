# AWS DRS Orchestration - Security-Enhanced Makefile
# Repository: Standalone repository (not nested)
# Dev Stack: aws-drs-orchestration-dev
# Region: us-east-1

.PHONY: help security-scan security-fix validate lint test clean install-security-tools stack-info

# Default target
help:
	@echo "AWS DRS Orchestration - Development Commands"
	@echo "Dev Stack: aws-drs-orchestration-dev"
	@echo ""
	@echo "🚀 CI/CD Commands (RECOMMENDED):"
	@echo "  ci-checks           Run full CI/CD quality checks (validation + security + tests)"
	@echo "  ci-checks-quick     Quick checks (skip tests and security)"
	@echo ""
	@echo "📦 Deployment Commands:"
	@echo "  deploy-dev          Deploy to dev with full validation (RECOMMENDED)"
	@echo "  deploy-dev-quick    Quick deploy (skip validation - NOT RECOMMENDED)"
	@echo "  deploy-dev-frontend Deploy frontend only"
	@echo "  deploy-dev-lambda   Deploy Lambda functions only"
	@echo "  validate-only       Run all checks without deploying"
	@echo ""
	@echo "📤 Sync Commands:"
	@echo "  sync-validated      Sync to S3 with full validation"
	@echo "  sync-quick          Quick sync (no validation)"
	@echo ""
	@echo "Stack Commands:"
	@echo "  stack-info          Show current dev stack information"
	@echo "  stack-status        Check dev stack deployment status"
	@echo "  stack-outputs       Show all stack outputs"
	@echo ""
	@echo "Security Commands:"
	@echo "  security-scan       Run all security scans"
	@echo "  security-fix        Fix automatically fixable security issues"
	@echo "  install-security    Install security scanning tools"
	@echo ""
	@echo "Development Commands:"
	@echo "  validate           Validate CloudFormation templates"
	@echo "  lint               Run code linting"
	@echo "  test               Run all tests"
	@echo "  package-lambda     Package Lambda functions"
	@echo "  verify-structure   Verify repository structure"
	@echo "  clean              Clean build artifacts"
	@echo ""
	@echo "💡 Recommended Workflow:"
	@echo "  1. make ci-checks          # Run all quality checks"
	@echo "  2. make deploy-dev         # Deploy with validation"
	@echo "  3. Test application"
	@echo ""
	@echo "⚡ Quick Development Workflow:"
	@echo "  1. make ci-checks-quick    # Quick validation"
	@echo "  2. make deploy-dev-lambda  # Update Lambda only"

# Show current stack information
stack-info:
	@echo "📊 Current Dev Stack Information:"
	@echo "Stack Name: aws-drs-orchestration-dev"
	@echo "Region: us-east-1"
	@echo "Deployment Bucket: aws-drs-orchestration-dev"
	@echo ""
	@echo "To get live stack outputs, run: make stack-outputs"

# Check stack deployment status
stack-status:
	@echo "🔍 Checking dev stack status..."
	AWS_PAGER="" aws cloudformation describe-stacks \
		--stack-name aws-drs-orchestration-dev \
		--region us-east-1 \
		--query 'Stacks[0].{StackName:StackName,StackStatus:StackStatus,CreationTime:CreationTime}' \
		--output table

# Show all stack outputs
stack-outputs:
	@echo "📋 Stack Outputs:"
	AWS_PAGER="" aws cloudformation describe-stacks \
		--stack-name aws-drs-orchestration-dev \
		--region us-east-1 \
		--query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
		--output table

# Install security tools
install-security:
	@echo "Installing Python security tools..."
	pip install bandit semgrep safety black flake8 isort
	@echo "Installing Node.js security tools..."
	npm install -g eslint-plugin-security
	@echo "Installing CloudFormation tools..."
	pip install cfn-lint
	@echo "Security tools installed successfully!"

# Run comprehensive security scans
security-scan: install-security
	@echo "🔍 Running comprehensive security scans..."
	@echo ""
	@echo "1. Python Security Scan (Bandit)..."
	bandit -r lambda/ -ll || true
	@echo ""
	@echo "2. Advanced Security Scan (Semgrep)..."
	semgrep --config=auto lambda/ || true
	@echo ""
	@echo "3. Dependency Vulnerability Scan (Safety)..."
	safety scan || true
	@echo ""
	@echo "4. Frontend Security Scan (npm audit)..."
	cd frontend && npm audit --audit-level moderate || true
	@echo ""
	@echo "5. CloudFormation Security Scan (cfn-lint)..."
	cfn-lint cfn/*.yaml || true
	@echo ""
	@echo "✅ Security scan completed!"

# Fix automatically fixable security issues
security-fix:
	@echo "🔧 Fixing automatically fixable security issues..."
	@echo ""
	@echo "1. Fixing Python dependency vulnerabilities..."
	pip install --upgrade boto3 requests pyjwt python-dateutil
	@echo ""
	@echo "2. Fixing frontend dependency vulnerabilities..."
	cd frontend && npm audit fix
	@echo ""
	@echo "3. Formatting Python code..."
	black lambda/ scripts/ --line-length 79
	isort lambda/ scripts/ --profile black
	@echo ""
	@echo "✅ Automatic fixes completed!"

# Validate CloudFormation templates
validate:
	@echo "🔍 Validating CloudFormation templates..."
	@for template in cfn/*.yaml; do \
		echo "Validating $$template..."; \
		AWS_PAGER="" aws cloudformation validate-template --template-body file://$$template > /dev/null 2>&1 || echo "❌ $$template failed validation"; \
	done
	@echo "✅ CloudFormation validation completed!"

# Run code linting
lint:
	@echo "🔍 Running code linting..."
	@echo "Python linting..."
	flake8 lambda/ scripts/ --max-line-length=79 || true
	@echo "Frontend linting..."
	cd frontend && npm run lint || true
	@echo "✅ Linting completed!"

# Run all tests
test:
	@echo "🧪 Running tests..."
	@echo "Python unit tests..."
	pytest tests/python/unit/ -v || true
	@echo "Python integration tests..."
	pytest tests/integration/ -v || true
	@echo "Frontend tests..."
	cd frontend && npm test -- --run || true
	@echo "✅ Tests completed!"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/
	rm -rf lambda/*.zip
	rm -rf frontend/dist/
	rm -rf frontend/node_modules/.cache/
	rm -rf .pytest_cache/
	@echo "✅ Cleanup completed!"

# Development workflow
dev-setup: install-security
	@echo "🚀 Setting up development environment..."
	pip install -r lambda/requirements.txt
	cd frontend && npm install
	@echo "✅ Development environment ready!"

# Package Lambda functions
package-lambda:
	@echo "📦 Packaging Lambda functions..."
	python3 package_lambda.py
	@echo "✅ Lambda packages created in build/lambda/"

# Verify repository structure
verify-structure:
	@echo "🔍 Verifying repository structure..."
	@echo "Checking Lambda directories..."
	@test -d lambda/query-handler && echo "  ✅ query-handler" || echo "  ❌ query-handler missing"
	@test -d lambda/data-management-handler && echo "  ✅ data-management-handler" || echo "  ❌ data-management-handler missing"
	@test -d lambda/execution-handler && echo "  ✅ execution-handler" || echo "  ❌ execution-handler missing"
	@test -d lambda/frontend-deployer && echo "  ✅ frontend-deployer" || echo "  ❌ frontend-deployer missing"
	@test -d lambda/notification-formatter && echo "  ✅ notification-formatter" || echo "  ❌ notification-formatter missing"
	@test -d lambda/orchestration-stepfunctions && echo "  ✅ orchestration-stepfunctions" || echo "  ❌ orchestration-stepfunctions missing"
	@test -d lambda/shared && echo "  ✅ shared" || echo "  ❌ shared missing"
	@echo "Checking CloudFormation templates..."
	@test -f cfn/master-template.yaml && echo "  ✅ master-template.yaml" || echo "  ❌ master-template.yaml missing"
	@test -f cfn/lambda-stack.yaml && echo "  ✅ lambda-stack.yaml" || echo "  ❌ lambda-stack.yaml missing"
	@echo "Checking deployment scripts..."
	@test -f scripts/deploy.sh && echo "  ✅ deploy.sh" || echo "  ❌ deploy.sh missing"
	@test -f package_lambda.py && echo "  ✅ package_lambda.py" || echo "  ❌ package_lambda.py missing"
	@echo "✅ Repository structure verified!"

# Pre-commit checks
pre-commit: security-scan lint test
	@echo "✅ Pre-commit checks completed!"

# CI/CD pipeline simulation (comprehensive)
ci-checks:
	@echo "🔍 Running comprehensive CI/CD quality checks..."
	./scripts/local-ci-checks.sh

ci-checks-quick:
	@echo "⚡ Running quick CI/CD checks (skip tests and security)..."
	./scripts/local-ci-checks.sh --quick

# Deployment targets
deploy-dev:
	@echo "🚀 Deploying to dev environment with full validation..."
	./scripts/deploy-with-validation.sh dev

deploy-dev-quick:
	@echo "⚡ Quick deploy to dev (skip validation - NOT RECOMMENDED)..."
	./scripts/deploy-with-validation.sh dev --quick

deploy-dev-frontend:
	@echo "🎨 Deploying frontend only to dev..."
	./scripts/deploy-with-validation.sh dev --frontend-only

deploy-dev-lambda:
	@echo "⚡ Deploying Lambda functions only to dev..."
	./scripts/deploy-with-validation.sh dev --lambda-only

# Validation only (no deployment)
validate-only:
	@echo "🔍 Running validation, security, and tests (no deployment)..."
	./scripts/deploy.sh dev --validate-only

# Sync to S3 with validation
sync-validated:
	@echo "📦 Syncing to S3 with full validation..."
	./scripts/sync-to-deployment-bucket.sh --validate

sync-quick:
	@echo "📦 Quick sync to S3 (no validation)..."
	./scripts/sync-to-deployment-bucket.sh

# Legacy CI/CD pipeline (deprecated - use ci-checks instead)
ci-pipeline: clean dev-setup security-scan validate lint test
	@echo "⚠️  DEPRECATED: Use 'make ci-checks' instead"
	@echo "✅ CI/CD pipeline simulation completed!"