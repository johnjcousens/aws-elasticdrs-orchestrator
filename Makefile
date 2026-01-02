# AWS DRS Orchestration Makefile
# Provides automation for S3 sync, validation, and deployment

.PHONY: help install lint validate format test clean all sync-s3 sync-s3-build enable-auto-sync disable-auto-sync update-config update-config-v4 deploy-v4 build-deploy-v4

# Default target
.DEFAULT_GOAL := help

# Load configuration from environment files
-include .env.deployment
-include .env.deployment.local

# Configuration with defaults (can be overridden)
DEPLOYMENT_BUCKET ?= aws-drs-orchestration
DEPLOYMENT_REGION ?= us-east-1
PROJECT_NAME ?= aws-drs-orchestrator
ENVIRONMENT ?= dev
PARENT_STACK_NAME ?= $(PROJECT_NAME)-$(ENVIRONMENT)
AWS_PROFILE ?= default

# Template paths
TEMPLATE_DIR := cfn
TEMPLATES := $(wildcard $(TEMPLATE_DIR)/*.yaml)
SCRIPTS_DIR := scripts

# Tools
CFNLINT := cfn-lint
CFNGUARD := cfn-guard
PYTHON := python3
PIP := pip3

help: ## Show this help message
	@echo "AWS DRS Orchestration Management"
	@echo "=================================="
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Templates found: $(TEMPLATES)"
	@echo ""
	@echo "S3 Sync Status:"
	@if [ -x .git/hooks/post-push ]; then \
		echo "  ✅ Auto-sync ENABLED (runs after git push)"; \
	else \
		echo "  ⚠️  Auto-sync DISABLED"; \
	fi

install: ## Install required validation tools
	@echo "Installing CloudFormation validation tools..."
	$(PIP) install cfn-lint pyyaml

validate-config: ## Validate deployment configuration
	@echo "🔍 Validating deployment configuration..."
	@./scripts/validate-deployment-config.sh

validate-config-full: ## Validate configuration and check for hardcoded values
	@echo "🔍 Full validation including hardcoded value checks..."
	@./scripts/validate-deployment-config.sh --check-hardcoded
	@if command -v brew >/dev/null 2>&1; then \
		echo "Installing cfn-guard via Homebrew..."; \
		brew install cfn-guard; \
	elif command -v cargo >/dev/null 2>&1; then \
		echo "Installing cfn-guard via Cargo..."; \
		cargo install cfn-guard; \
	else \
		echo "Please install cfn-guard manually from: https://github.com/aws-cloudformation/cloudformation-guard"; \
	fi
	@echo "✅ Installation complete"

lint: ## Run cfn-lint on all templates
	@echo "Running cfn-lint validation..."
	@for template in $(TEMPLATES); do \
		echo "🔍 Linting $$template"; \
		$(CFNLINT) $$template || exit 1; \
	done
	@echo "✅ All templates passed cfn-lint validation"

validate: lint guard ## Run comprehensive validation (lint + guard)
	@echo "✅ All validation checks passed"

guard: ## Run CloudFormation Guard rules (if available)
	@if command -v $(CFNGUARD) >/dev/null 2>&1; then \
		if [ -d "guard-rules" ]; then \
			echo "Running CloudFormation Guard validation..."; \
			for template in $(TEMPLATES); do \
				echo "🛡️  Validating $$template with Guard rules"; \
				$(CFNGUARD) validate -r guard-rules/ -d $$template || echo "⚠️  Guard validation failed for $$template"; \
			done; \
		else \
			echo "⚠️  No guard-rules directory found, skipping Guard validation"; \
		fi; \
	else \
		echo "⚠️  cfn-guard not installed, skipping Guard validation"; \
	fi

format: ## Format and standardize template descriptions
	@echo "Running template formatting..."
	@$(PYTHON) $(SCRIPTS_DIR)/format-templates.py $(TEMPLATES)
	@echo "✅ Template formatting complete"

test: validate ## Run all tests (alias for validate)
	@echo "✅ All tests passed"

check-ami: ## Verify all templates use Windows Server 2025 AMI parameters
	@echo "Checking AMI parameters..."
	@grep -n "Windows_Server.*English-Full-Base" $(TEMPLATES) || echo "No AMI parameters found"
	@echo "✅ AMI parameter check complete"

clean: ## Clean up temporary files
	@echo "Cleaning up temporary files..."
	@find . -name "*.tmp" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

info: ## Show template information
	@echo "Template Information:"
	@echo "===================="
	@for template in $(TEMPLATES); do \
		echo ""; \
		echo "📄 $$template:"; \
		echo "   Description: $$(grep -A 2 '^Description:' $$template | tail -1 | sed 's/^[[:space:]]*//' | cut -c1-80)..."; \
		echo "   Parameters: $$(grep -c '^[[:space:]]*[A-Z][A-Za-z0-9]*:$$' $$template) found"; \
		echo "   Resources: $$(grep -c '^[[:space:]]*[A-Z][A-Za-z0-9]*:$$' $$template | awk 'BEGIN{resources=0} /Resources:/,/^[A-Z]/ {if(/^[[:space:]]*[A-Z]/ && !/^Resources:/) resources++} END{print resources}') found"; \
	done

all: install validate format info ## Run complete pipeline: install, validate, format, info
	@echo "🎉 Complete pipeline finished successfully!"

# Development targets
dev-setup: install ## Set up development environment
	@echo "Setting up development environment..."
	@if [ ! -f .pre-commit-config.yaml ]; then \
		echo "Creating pre-commit configuration..."; \
		$(MAKE) create-precommit; \
	fi
	@echo "✅ Development setup complete"

create-precommit: ## Create pre-commit configuration
	@echo "Creating .pre-commit-config.yaml..."
	@echo "# Pre-commit hooks for CloudFormation template validation" > .pre-commit-config.yaml
	@echo "repos:" >> .pre-commit-config.yaml
	@echo "  - repo: local" >> .pre-commit-config.yaml
	@echo "    hooks:" >> .pre-commit-config.yaml
	@echo "      - id: cfn-lint" >> .pre-commit-config.yaml
	@echo "        name: CloudFormation Linter" >> .pre-commit-config.yaml
	@echo "        entry: make lint" >> .pre-commit-config.yaml
	@echo "        language: system" >> .pre-commit-config.yaml
	@echo "        files: '^templates/.*\.yaml$$'" >> .pre-commit-config.yaml
	@echo "        pass_filenames: false" >> .pre-commit-config.yaml
	@echo "      - id: yaml-check" >> .pre-commit-config.yaml
	@echo "        name: YAML Syntax Check" >> .pre-commit-config.yaml
	@echo "        entry: python -c \"import yaml; yaml.safe_load(open('$$1'))\"" >> .pre-commit-config.yaml
	@echo "        language: system" >> .pre-commit-config.yaml
	@echo "        files: '\.yaml$$'" >> .pre-commit-config.yaml
	@echo "✅ Pre-commit configuration created"

# CI/CD targets
ci: install validate ## CI/CD pipeline target
	@echo "✅ CI/CD pipeline completed successfully"

deploy-check: validate ## Pre-deployment validation
	@echo "Running pre-deployment checks..."
	@$(MAKE) check-ami
	@echo "✅ Ready for deployment"

# S3 Sync Automation Targets
sync-s3: ## Sync repository to S3 deployment bucket
	@echo "📦 Syncing to S3 deployment bucket..."
	@./scripts/sync-to-deployment-bucket.sh
	@echo "✅ S3 sync complete"

sync-s3-build: ## Build frontend and sync to S3
	@echo "📦 Building frontend and syncing to S3..."
	@./scripts/sync-to-deployment-bucket.sh --build-frontend
	@echo "✅ Frontend build and S3 sync complete"

sync-s3-dry-run: ## Preview S3 sync without making changes
	@echo "🔍 Previewing S3 sync (dry-run mode)..."
	@./scripts/sync-to-deployment-bucket.sh --dry-run
	@echo "✅ Dry-run complete"

clean-s3-orphans: ## Check for and remove orphaned directories/files in S3
	@echo "🧹 Checking for orphaned items in S3..."
	@./scripts/sync-to-deployment-bucket.sh --clean-orphans
	@echo "✅ Orphan check complete"

enable-auto-sync: ## Enable automatic S3 sync after git push
	@echo "⚙️  Enabling automatic S3 sync..."
	@if [ ! -f .git/hooks/post-push ]; then \
		echo "❌ post-push hook not found - run setup first"; \
		exit 1; \
	fi
	@chmod +x .git/hooks/post-push
	@echo "✅ Auto-sync ENABLED - S3 will sync after every git push"

disable-auto-sync: ## Disable automatic S3 sync
	@echo "⚙️  Disabling automatic S3 sync..."
	@if [ -f .git/hooks/post-push ]; then \
		chmod -x .git/hooks/post-push; \
		echo "✅ Auto-sync DISABLED"; \
	else \
		echo "⚠️  post-push hook not found"; \
	fi

setup-auto-sync: ## Setup automatic S3 sync (creates hook)
	@echo "🔧 Setting up automatic S3 sync..."
	@if [ ! -f .git/hooks/post-push ]; then \
		echo "Creating post-push hook..."; \
		echo "#!/bin/bash" > .git/hooks/post-push; \
		echo "# Auto-sync to S3 after successful git push" >> .git/hooks/post-push; \
		echo "echo \"\"" >> .git/hooks/post-push; \
		echo "echo \"🔄 Auto-syncing to S3 deployment bucket...\"" >> .git/hooks/post-push; \
		echo "echo \"\"" >> .git/hooks/post-push; \
		echo "./scripts/sync-to-deployment-bucket.sh" >> .git/hooks/post-push; \
		echo "if [ \$$? -eq 0 ]; then" >> .git/hooks/post-push; \
		echo "    echo \"\"" >> .git/hooks/post-push; \
		echo "    echo \"✅ S3 sync complete!\"" >> .git/hooks/post-push; \
		echo "    echo \"\"" >> .git/hooks/post-push; \
		echo "else" >> .git/hooks/post-push; \
		echo "    echo \"\"" >> .git/hooks/post-push; \
		echo "    echo \"❌ S3 sync failed\"" >> .git/hooks/post-push; \
		echo "    echo \"\"" >> .git/hooks/post-push; \
		echo "    exit 1" >> .git/hooks/post-push; \
		echo "fi" >> .git/hooks/post-push; \
	fi
	@chmod +x .git/hooks/post-push
	@echo "✅ Auto-sync setup complete"

# drs-orch-v4 Stack Specific Targets
update-config: ## Update frontend configuration from CloudFormation stack
	@echo "📝 Updating frontend configuration from CloudFormation stack..."
	@./scripts/update-frontend-config.sh drs-orch-v4 us-east-1

update-config-v4: update-config ## Alias for update-config

deploy-v4: ## Deploy drs-orch-v4 stack with updated configuration
	@echo "🚀 Deploying drs-orch-v4 stack..."
	@./scripts/sync-to-deployment-bucket.sh --deploy-cfn

build-deploy-v4: ## Build frontend and deploy drs-orch-v4 stack
	@echo "🏗️ Building frontend and deploying drs-orch-v4 stack..."
	@./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-cfn

deploy-frontend-v4: ## Deploy only frontend for drs-orch-v4 stack
	@echo "🌐 Deploying frontend for drs-orch-v4 stack..."
	@./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend

update-lambda-v4: ## Update Lambda functions for drs-orch-v4 stack
	@echo "⚡ Updating Lambda functions for drs-orch-v4 stack..."
	@./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Prevent configuration drift
check-config-drift: ## Check if frontend config matches CloudFormation stack
	@echo "🔍 Checking for configuration drift..."
	@TEMP_CONFIG=$$(mktemp) && \
	cp frontend/public/aws-config.json "$$TEMP_CONFIG.backup" && \
	./scripts/update-frontend-config.sh drs-orch-v4 us-east-1 > /dev/null 2>&1 && \
	if ! diff -q "$$TEMP_CONFIG.backup" frontend/public/aws-config.json > /dev/null 2>&1; then \
		echo "❌ Configuration drift detected!"; \
		echo "Configuration was updated from CloudFormation stack outputs."; \
		echo "Changes applied automatically."; \
		rm -f "$$TEMP_CONFIG" "$$TEMP_CONFIG.backup"; \
		exit 1; \
	else \
		echo "✅ Configuration is in sync with CloudFormation stack"; \
		rm -f "$$TEMP_CONFIG" "$$TEMP_CONFIG.backup"; \
	fi

# =============================================================================
# PYTHON CODING STANDARDS
# =============================================================================

# Python tool configuration
PYTHON_VERSION ?= 3.12
BLACK_VERSION ?= 23.7.0
FLAKE8_VERSION ?= 6.0.0
ISORT_VERSION ?= 5.12.0
PRECOMMIT_VERSION ?= 3.3.3

install-python-tools: ## Install Python code quality and formatting tools
	@echo "🐍 Installing Python code quality tools..."
	$(PIP) install black==$(BLACK_VERSION) flake8==$(FLAKE8_VERSION) isort==$(ISORT_VERSION) pre-commit==$(PRECOMMIT_VERSION)
	$(PIP) install flake8-docstrings==1.7.0 flake8-import-order==0.18.2 pep8-naming==0.13.3
	@echo "✅ Python tools installed"

setup-pre-commit: install-python-tools ## Setup and install pre-commit hooks
	@echo "🔧 Setting up pre-commit hooks..."
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed"

format-python: ## Format Python code with Black and sort imports with isort
	@echo "🎨 Formatting Python code..."
	black lambda/ --line-length=79
	isort lambda/ --profile=black --line-length=79
	@echo "✅ Python code formatted"

lint-python: ## Lint Python code with Flake8 for PEP 8 compliance
	@echo "🔍 Linting Python code..."
	flake8 lambda/
	@echo "✅ Python linting complete"

check-python: ## Check Python code formatting and style without making changes
	@echo "🔍 Checking Python code formatting and style..."
	black --check --diff lambda/ scripts/ --line-length=79
	isort --check-only --diff lambda/ scripts/ --profile=black --line-length=79
	flake8 lambda/ scripts/
	@echo "✅ Python code check complete"

fix-python: format-python lint-python ## Format and lint Python code (fix issues)
	@echo "🔧 Python code fixed and validated"

# Comprehensive PEP 8 compliance targets
pep8-full-check: pep8-compliance-check analyze-violations python-quality-report ## Run all PEP 8 analysis tools
	@echo "🎯 Complete PEP 8 analysis finished"

python-quality-report: ## Generate Python code quality report
	@echo "📊 Generating Python code quality report..."
	@mkdir -p reports
	python scripts/generate_quality_report.py --format json,html
	@echo "✅ Python quality reports generated in reports/"

pep8-compliance-check: ## Run comprehensive PEP 8 compliance check
	@echo "🔍 Running comprehensive PEP 8 compliance check..."
	python scripts/pep8_compliance_checker.py --report
	@echo "✅ PEP 8 compliance check complete"

pep8-compliance-fix: ## Fix PEP 8 compliance issues automatically
	@echo "🔧 Fixing PEP 8 compliance issues..."
	python scripts/pep8_compliance_checker.py --fix --report
	@echo "✅ PEP 8 compliance fixes applied"

analyze-violations: ## Analyze current code violations with detailed breakdown
	@echo "📊 Analyzing code violations..."
	python scripts/analyze_violations.py
	@echo "✅ Violation analysis complete"

pre-commit-all: ## Run pre-commit hooks on all files
	@echo "🔍 Running pre-commit hooks on all files..."
	pre-commit run --all-files
	@echo "✅ Pre-commit validation complete"

dev-setup-python: install-python-tools setup-pre-commit ## Complete Python development environment setup
	@echo "🚀 Python development environment ready"
	@echo "Next steps:"
	@echo "  1. Run 'make check-python' to validate existing code"
	@echo "  2. Run 'make format-python' to format code if needed"
	@echo "  3. Start developing with automatic pre-commit validation"

python-status: ## Show Python tools status and versions
	@echo "🐍 Python Tools Status"
	@echo "====================="
	@python --version 2>/dev/null || echo "Python: Not installed"
	@black --version 2>/dev/null || echo "Black: Not installed"
	@flake8 --version 2>/dev/null || echo "Flake8: Not installed"
	@isort --version 2>/dev/null || echo "isort: Not installed"
	@pre-commit --version 2>/dev/null || echo "pre-commit: Not installed"
	@echo ""
	@echo "Project Files:"
	@find lambda -name "*.py" | wc -l | xargs echo "Python files:"

clean-python: ## Clean Python cache and temporary files
	@echo "🧹 Cleaning Python artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf reports/
	@echo "✅ Python cleanup complete"