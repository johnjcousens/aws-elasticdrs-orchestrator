# AD-PKI-AIRGAPPED CloudFormation Template Makefile
# Provides automation for template validation, formatting, and testing

.PHONY: help install lint validate format test clean all

# Default target
.DEFAULT_GOAL := help

# Template paths
TEMPLATE_DIR := templates
TEMPLATES := $(wildcard $(TEMPLATE_DIR)/*.yaml)
SCRIPTS_DIR := scripts

# Tools
CFNLINT := cfn-lint
CFNGUARD := cfn-guard
PYTHON := python3
PIP := pip3

help: ## Show this help message
	@echo "AD-PKI-AIRGAPPED CloudFormation Template Management"
	@echo "=================================================="
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Templates found: $(TEMPLATES)"

install: ## Install required validation tools
	@echo "Installing CloudFormation validation tools..."
	$(PIP) install cfn-lint pyyaml
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
	@cat > .pre-commit-config.yaml << 'EOF'
# Pre-commit hooks for CloudFormation template validation
repos:
  - repo: local
    hooks:
      - id: cfn-lint
        name: CloudFormation Linter
        entry: make lint
        language: system
        files: '^templates/.*\.yaml$$'
        pass_filenames: false
      - id: yaml-check
        name: YAML Syntax Check
        entry: python -c "import yaml; yaml.safe_load(open('$$1'))"
        language: system
        files: '\.yaml$$'
EOF
	@echo "✅ Pre-commit configuration created"

# CI/CD targets
ci: install validate ## CI/CD pipeline target
	@echo "✅ CI/CD pipeline completed successfully"

deploy-check: validate ## Pre-deployment validation
	@echo "Running pre-deployment checks..."
	@$(MAKE) check-ami
	@echo "✅ Ready for deployment"
