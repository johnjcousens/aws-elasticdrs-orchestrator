# Development Environment Setup

This guide covers setting up your local development environment with all required tools for the DR Orchestration Platform.

## Prerequisites

- Python 3.12+
- Node.js 18+ and npm
- Ruby 2.6+ (for cfn_nag)
- AWS CLI configured with credentials
- Git

## Quick Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd aws-elasticdrs-orchestrator

# 2. Setup Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements-dev.txt

# 4. Install frontend dependencies
cd frontend
npm install
cd ..

# 5. Install cfn_nag (CloudFormation security scanner)
gem install cfn-nag

# 6. Verify installation
./scripts/verify-dev-tools.sh
```

## Detailed Setup

### Python Environment

The project uses a virtual environment to isolate Python dependencies:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (run this in every new terminal session)
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
```

**Installed tools:**
- `cfn-lint` - CloudFormation template validation
- `flake8` - Python linting
- `black` - Python code formatting
- `isort` - Import sorting
- `bandit` - Python security scanning
- `detect-secrets` - Credential scanning
- `safety` - Dependency vulnerability scanning
- `pytest` - Testing framework
- `hypothesis` - Property-based testing
- `moto` - AWS service mocking

### Frontend Environment

```bash
cd frontend
npm install
```

**Installed tools:**
- TypeScript compiler
- Vite (build tool)
- Vitest (testing framework)
- ESLint (linting)

### CloudFormation Security Scanner (cfn_nag)

`cfn_nag` is a Ruby gem that scans CloudFormation templates for security issues.

**Note:** cfn_nag currently has compatibility issues with Ruby 4.0+. It works best with Ruby 2.7-3.x.

**Option 1: Skip cfn_nag (Recommended for now)**
The deploy script treats cfn_nag as optional and will continue without it.

**Option 2: Install with compatible Ruby version**
```bash
# Install Ruby 3.x via rbenv or rvm
brew install rbenv
rbenv install 3.3.0
rbenv global 3.3.0

# Install cfn_nag
gem install cfn-nag

# Verify installation
cfn_nag --version
```

**Option 3: Use Docker**
```bash
# Run cfn_nag via Docker
docker run --rm -v $(pwd):/templates stelligent/cfn_nag /templates/cfn/
```

### Optional: Shell Script Linting (shellcheck)

```bash
# macOS
brew install shellcheck

# Linux
sudo apt-get install shellcheck  # Debian/Ubuntu
sudo yum install shellcheck      # RHEL/CentOS
```

## Verification

Run the verification script to check all tools are installed:

```bash
./scripts/verify-dev-tools.sh
```

Expected output:
```
✓ Python 3.12+
✓ Node.js 18+
✓ cfn-lint
✓ flake8
✓ black
✓ bandit
✓ detect-secrets
✓ safety
✓ pytest
✓ cfn_nag
✓ shellcheck (optional)
```

## IDE Setup

### VS Code

Recommended extensions:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- ESLint (dbaeumer.vscode-eslint)
- CloudFormation Linter (kddejong.vscode-cfn-lint)

### PyCharm

1. Configure Python interpreter to use `.venv`
2. Enable Black as code formatter
3. Configure flake8 as external tool

## Running Validations Locally

```bash
# Full validation (what deploy script runs)
./scripts/deploy.sh dev --validate-only

# Individual tools
source .venv/bin/activate

# CloudFormation validation
cfn-lint cfn/**/*.yaml

# Python linting
flake8 lambda/

# Python formatting check
black --check lambda/

# Security scanning
bandit -r lambda/
detect-secrets scan
cfn_nag_scan --input-path cfn/

# Run tests
pytest tests/unit/
cd frontend && npm test
```

## Troubleshooting

### Python packages not found

Make sure virtual environment is activated:
```bash
source .venv/bin/activate
```

### cfn_nag not found

Install Ruby and cfn_nag:
```bash
# Check Ruby is installed
ruby --version

# Install cfn_nag
gem install cfn-nag

# If permission denied, use --user-install
gem install --user-install cfn-nag
```

### npm packages not found

Install frontend dependencies:
```bash
cd frontend
npm install
```

### AWS credentials not configured

Configure AWS CLI:
```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

## Next Steps

- Review [CI/CD Workflow Enforcement](../../.kiro/steering/cicd-workflow-enforcement.md)
- Read [Developer Guide](../guides/DEVELOPER_GUIDE.md)
- Check [Deployment Guide](QUICK_START_GUIDE.md)
