# Repository Cleanup Plan

## Current State Analysis

The repository has accumulated significant troubleshooting files during the execution polling system fix. This cleanup plan will restore the repository to a clean, maintainable state while preserving valuable insights.

## Files to Remove (Immediate Cleanup)

### 🗑️ Debug and Troubleshooting Scripts (25 files)
```bash
# Debug scripts created during troubleshooting
cancel_execution.py
cancel_execution.sh
check_missing_fields.py
debug_api_response.py
debug_current_execution.py
debug_dynamodb_structure.py
debug_execution_data.py
debug_execution_stuck.py
debug_recovery_instances.py
debug_wave_structure.py
diagnose_execution_detailed.py
diagnose_execution.py
execution_analysis.py
fix_execution_manually.py
fix_server_instance_ids.py
fix_server_recovery_instances.py
fix_stuck_execution.py
local_test_environment.py
populate_server_details.py
test_api_fields.py
test_enhanced_api.py
test_frontend_data.py
test_orchestration_locally.py
test_reconcile_function.py
test_reconcile_simple.py
test_terminate_logic.py
trigger_reconcile.py
working_rbac_middleware.py
```

### 🗑️ Test Payload Files (15 files)
```bash
# JSON payload files used for testing
clean-poller-payload.json
current-execution-payload.json
execution-poller-payload.json
finder-response.json
orchestration-response.json
payload-base64.txt
poller-payload.json
poller-test-payload.json
response.json
test-execution-poller-payload-b64.txt
test-execution-poller-payload.json
test-orchestration-payload.json
test-payload.json
test-poller-payload.json
```

### 🗑️ Temporary Shell Scripts (12 files)
```bash
# Shell scripts created for testing/deployment
create-archive-s3-bucket.sh
create-archive-test-user.sh
deploy-archive-properly.md
deploy-archive-test-stack.sh
deploy-archive-test.py
deploy-working-archive.sh
emergency-deploy-archive.sh
mark_execution_failed.sh
test_execution_poller_fix.sh
test-archive-stack.sh
test-archive-vs-current.sh
verify-multi-stack-deployment.sh
```

### 🗑️ Analysis Documents (15 files)
```bash
# Markdown files documenting troubleshooting process
API_GATEWAY_SPLIT_PLAN.md
COMPREHENSIVE_DRS_API_IMPLEMENTATION.md
CRITICAL_FIX_SUMMARY.md
DEEP_ANALYSIS_WORKING_ARCHIVE.md
DEPLOYMENT_FIX.md
EXECUTION_POLLING_ANALYSIS.md
FRESH_STACK_DEPLOYMENT_SUMMARY.md
GITHUB_SECRETS_SETUP.md
MULTI_STACK_IMPLEMENTATION_SUMMARY.md
ORCHESTRATION_FIX_LOG.md
ORCHESTRATION_FIX_PLAN.md
RESTORATION_PLAN.md
SYSTEMATIC_COMMIT_ANALYSIS.md
WORKING_PERIOD_ANALYSIS.md
WORKING_STATE_SUMMARY.md
```

### 🗑️ Reference Files (3 files)
```bash
# Reference files from other implementations
reference-App.tsx
reference-ExecutionDetailsPage.tsx
```

### 🗑️ Miscellaneous (5 files)
```bash
# Other temporary files
commit_list.txt
force-update.yaml
manual_cancel_commands.md
update-github-oidc-permissions.sh
update-github-oidc-qa-permissions.sh
```

## Files to Keep (Core Repository)

### ✅ Essential Configuration
- `.gitignore`, `.bandit`, `.cfnlintrc.yaml`, `.flake8`, `.pre-commit-config.yaml`
- `pyproject.toml`, `Makefile`, `mise.toml`
- `.env.deployment.fresh`, `.env.deployment.template`
- `aws-config.json`

### ✅ Core Documentation
- `README.md`, `CHANGELOG.md`, `SECURITY.md`

### ✅ Core Directories
- `cfn/` - CloudFormation templates
- `lambda/` - Lambda functions
- `frontend/` - React application
- `scripts/` - Deployment and utility scripts
- `tests/` - Unit and integration tests
- `docs/` - Official documentation
- `.github/` - GitHub Actions workflows
- `.kiro/` - AI assistant configuration

## Cleanup Execution Plan

### Phase 1: Archive Important Analysis (OPTIONAL)
```bash
# Create archive of troubleshooting insights
mkdir -p archive/troubleshooting-2026-01-10/
mv CRITICAL_FIX_SUMMARY.md archive/troubleshooting-2026-01-10/
mv EXECUTION_POLLING_ANALYSIS.md archive/troubleshooting-2026-01-10/
mv SYSTEMATIC_COMMIT_ANALYSIS.md archive/troubleshooting-2026-01-10/
```

### Phase 2: Remove Debug Scripts
```bash
# Remove all debug and troubleshooting scripts
rm -f cancel_execution.py cancel_execution.sh check_missing_fields.py
rm -f debug_*.py diagnose_*.py execution_analysis.py
rm -f fix_*.py test_*.py trigger_reconcile.py
rm -f local_test_environment.py populate_server_details.py
rm -f working_rbac_middleware.py
```

### Phase 3: Remove Test Payloads
```bash
# Remove JSON payload files
rm -f *-payload*.json *-response.json response.json
rm -f payload-base64.txt finder-response.json
rm -f clean-poller-payload.json
```

### Phase 4: Remove Temporary Scripts
```bash
# Remove shell scripts
rm -f create-archive-*.sh deploy-archive-*.sh deploy-working-archive.sh
rm -f emergency-deploy-archive.sh mark_execution_failed.sh
rm -f test_execution_poller_fix.sh test-archive-*.sh
rm -f verify-multi-stack-deployment.sh update-github-oidc-*-permissions.sh
```

### Phase 5: Remove Analysis Documents
```bash
# Remove markdown analysis files
rm -f API_GATEWAY_SPLIT_PLAN.md COMPREHENSIVE_DRS_API_IMPLEMENTATION.md
rm -f CRITICAL_FIX_SUMMARY.md DEEP_ANALYSIS_WORKING_ARCHIVE.md
rm -f DEPLOYMENT_FIX.md EXECUTION_POLLING_ANALYSIS.md
rm -f FRESH_STACK_DEPLOYMENT_SUMMARY.md GITHUB_SECRETS_SETUP.md
rm -f MULTI_STACK_IMPLEMENTATION_SUMMARY.md ORCHESTRATION_FIX_*.md
rm -f RESTORATION_PLAN.md SYSTEMATIC_COMMIT_ANALYSIS.md
rm -f WORKING_*_ANALYSIS.md WORKING_STATE_SUMMARY.md
```

### Phase 6: Remove Reference Files
```bash
# Remove reference files
rm -f reference-*.tsx reference-*.py
rm -f commit_list.txt force-update.yaml manual_cancel_commands.md
```

## Post-Cleanup Repository Structure

```
aws-elasticdrs-orchestrator/
├── .github/workflows/          # GitHub Actions CI/CD
├── .kiro/                      # AI assistant configuration
├── cfn/                        # CloudFormation templates
├── docs/                       # Official documentation
├── frontend/                   # React application
├── lambda/                     # Lambda functions
├── scripts/                    # Deployment scripts
├── tests/                      # Unit/integration tests
├── .gitignore                  # Git ignore rules
├── .bandit                     # Security scan config
├── .cfnlintrc.yaml            # CloudFormation linting
├── .flake8                     # Python linting
├── .pre-commit-config.yaml     # Pre-commit hooks
├── aws-config.json             # AWS configuration
├── CHANGELOG.md                # Version history
├── Makefile                    # Build automation
├── mise.toml                   # Development environment
├── pyproject.toml              # Python project config
├── README.md                   # Project documentation
└── SECURITY.md                 # Security guidelines
```

## Benefits of Cleanup

### 🎯 **Improved Maintainability**
- Clear separation between core code and temporary files
- Easier navigation for new developers
- Reduced cognitive load when browsing repository

### 🔍 **Better Code Review**
- Cleaner git diffs focusing on actual changes
- Easier to identify important files vs temporary scripts
- Reduced noise in repository searches

### 📦 **Smaller Repository Size**
- Faster clone times
- Reduced storage requirements
- Cleaner CI/CD artifact builds

### 🛡️ **Security Benefits**
- Remove potential sensitive data in debug files
- Eliminate unused scripts that could become attack vectors
- Cleaner security scanning results

## Execution Timeline

1. **Immediate** (Today): Remove debug scripts and payloads (Phase 2-3)
2. **Short-term** (This week): Remove analysis docs and references (Phase 4-6)
3. **Optional**: Archive important insights (Phase 1)

## Risk Mitigation

- All files are in Git history and can be recovered if needed
- Core functionality remains untouched
- Cleanup can be done incrementally
- Each phase can be committed separately for easy rollback

## Success Metrics

- Repository file count reduced by ~75 files
- Root directory contains only essential files
- Clear separation between core code and configuration
- Improved developer experience when navigating repository