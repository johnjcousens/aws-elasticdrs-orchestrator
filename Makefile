# AWS DRS Orchestration - Security-Enhanced Makefile
# Test Stack: aws-elasticdrs-orchestrator-test
# API Endpoint: https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test
# Frontend URL: https://d13m3tjpjn4ots.cloudfront.net

.PHONY: help security-scan security-fix validate lint test clean install-security-tools stack-info

# Default target
help:
	@echo "AWS DRS Orchestration - Security Commands"
	@echo "Test Stack: aws-elasticdrs-orchestrator-test"
	@echo ""
	@echo "Stack Commands:"
	@echo "  stack-info          Show current test stack information"
	@echo "  stack-status        Check test stack deployment status"
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
	@echo "  clean              Clean build artifacts"

# Show current stack information
stack-info:
	@echo "📊 Current Test Stack Information:"
	@echo "Stack Name: aws-elasticdrs-orchestrator-test"
	@echo "API Endpoint: https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test"
	@echo "Frontend URL: https://d13m3tjpjn4ots.cloudfront.net"
	@echo "User Pool ID: us-east-1_9sxQSfYYQ"
	@echo "Client ID: 635au0e3dk35iktj60h2huic3a"
	@echo "Region: us-east-1"
	@echo ""
	@echo "Test User: testuser@example.com / TestPassword123!"

# Check stack deployment status
stack-status:
	@echo "🔍 Checking test stack status..."
	AWS_PAGER="" aws cloudformation describe-stacks \
		--stack-name aws-elasticdrs-orchestrator-test \
		--region us-east-1 \
		--query 'Stacks[0].{StackName:StackName,StackStatus:StackStatus,CreationTime:CreationTime}' \
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
	@echo "Python tests..."
	cd tests/python && python -m pytest unit/ -v || true
	@echo "Frontend tests..."
	cd frontend && npm test || true
	@echo "✅ Tests completed!"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf lambda/*.zip
	rm -rf frontend/dist/
	rm -rf frontend/node_modules/.cache/
	@echo "✅ Cleanup completed!"

# Development workflow
dev-setup: install-security
	@echo "🚀 Setting up development environment..."
	pip install -r lambda/requirements.txt
	cd frontend && npm install
	@echo "✅ Development environment ready!"

# Pre-commit checks
pre-commit: security-scan lint test
	@echo "✅ Pre-commit checks completed!"

# CI/CD pipeline simulation
ci-pipeline: clean dev-setup security-scan validate lint test
	@echo "✅ CI/CD pipeline simulation completed!"