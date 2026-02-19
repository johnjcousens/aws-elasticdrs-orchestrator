the goals# Generic Orchestration Refactoring - Requirements

**Feature**: generic-orchestration-refactoring  
**Status**: Requirements Phase  
**Created**: January 31, 2026  
**Last Updated**: February 3, 2026

---

## Executive Summary

Simplify the DRS orchestration architecture by moving DRS-specific logic from the `orchestration-stepfunctions` Lambda into the existing handler Lambdas where it logically belongs.

**Primary Objective**: Make the orchestration Lambda generic by moving its DRS-specific functions (~720 lines) into the appropriate existing handler Lambdas.

**Core Problem**: The current `orchestration-stepfunctions` Lambda contains DRS-specific operations that should live in the existing handler Lambdas.

**Solution**: Move 4 DRS functions from orchestration Lambda to existing handlers:
- `start_wave_recovery()` + `apply_launch_config_before_recovery()` → `execution-handler` (~275 lines)
- `update_wave_status()` + `query_drs_servers_by_tags()` → `query-handler` (~445 lines)

**Refactoring Strategy**: Create NEW Lambda directory (`dr-orchestration-stepfunction`) alongside existing one for safe parallel development. Keep original code intact as reference.

**Scope**: Move 4 functions, create new Lambda, update CloudFormation. Keep all handler Lambdas DRS-specific.

---

## Problem Statement

### Current Architecture

```
lambda/orchestration-stepfunctions/
└── index.py  ← Contains 4 DRS-specific functions (~720 lines)
    ├── start_wave_recovery()                    # ~125 lines - starts DRS recovery
    ├── apply_launch_config_before_recovery()    # ~150 lines - applies launch config
    ├── update_wave_status()                     # ~346 lines - polls DRS job status
    ├── query_drs_servers_by_tags()              # ~99 lines - queries DRS servers
    └── orchestration logic                      # Generic wave management

lambda/execution-handler/
└── index.py  ← Already handles DRS execution operations (5,825 lines)
    └── (existing DRS execution logic)

lambda/query-handler/
└── index.py  ← Already handles DRS query operations (4,754 lines)
    └── (existing DRS query logic)
```

**Issues:**
- DRS-specific functions in orchestration Lambda
- Orchestration Lambda makes direct DRS API calls
- Logic is in wrong place (orchestration should just coordinate)

### Target Architecture

**Parallel Lambda Strategy** (safe refactoring):

```
lambda/orchestration-stepfunctions/    # KEEP: Original (unchanged, reference)
└── index.py  ← Original code with DRS functions

lambda/dr-orchestration-stepfunction/  # NEW: Refactored (no 's')
└── index.py  ← Pure orchestration (NO DRS code)
    ├── begin_wave_plan()              # Generic - invokes execution-handler
    ├── poll_wave_status()             # Generic - invokes query-handler
    └── orchestration logic            # Generic wave management

lambda/execution-handler/              # MODIFIED
└── index.py  ← Receives functions from orchestration (~6,100 lines)
    ├── start_wave_recovery()          # Moved from orchestration (~125 lines)
    ├── apply_launch_config_before_recovery()  # Moved (~150 lines)
    └── (existing DRS execution logic)

lambda/query-handler/                  # MODIFIED
└── index.py  ← Receives functions from orchestration (~5,199 lines)
    ├── poll_wave_status()             # Moved from orchestration (~346 lines)
    ├── query_drs_servers_by_tags()    # Moved from orchestration (~99 lines)
    └── (existing DRS query logic)
```

**Benefits:**
- ✅ Original code preserved as reference
- ✅ Easy rollback (switch Step Functions ARN)
- ✅ Side-by-side comparison during development
- ✅ Zero risk to existing working code
- ✅ Orchestration Lambda is pure coordination logic
- ✅ DRS operations live in appropriate handler Lambdas
- ✅ Clear separation of concerns
- ✅ No new handler Lambdas needed
- ✅ Simpler architecture

## User Stories

### 1. As a Platform Engineer
**I want** the orchestration Lambda to only coordinate waves  
**So that** DRS-specific logic lives in the appropriate handler Lambdas  
**Acceptance Criteria:**
- New orchestration Lambda (`dr-orchestration-stepfunction`) has zero DRS API calls
- New orchestration Lambda invokes execution-handler to start waves
- New orchestration Lambda invokes query-handler to poll status
- All existing DRS functionality preserved
- Original Lambda kept as reference during development
- Step Functions updated to use new Lambda
- Easy rollback to original Lambda if needed

### 2. As a Developer
**I want** DRS operations in the correct handler Lambdas  
**So that** the codebase is organized logically  
**Acceptance Criteria:**
- `start_wave_recovery()` + `apply_launch_config_before_recovery()` moved to execution-handler
- `update_wave_status()` (renamed `poll_wave_status`) moved to query-handler
- `query_drs_servers_by_tags()` moved to query-handler
- New orchestration Lambda only coordinates wave sequencing
- All tests pass after refactoring
- Original code available for reference during development
- Can compare old vs new implementation side-by-side

### 3. As a System Administrator
**I want** consistent execution tracking  
**So that** I can monitor orchestration uniformly  
**Acceptance Criteria:**
- Execution state format unchanged
- Wave results structure unchanged
- DynamoDB schema unchanged
- Frontend displays work without changes
- CloudWatch logs maintain same format

## Refactoring Scope

### Functions to Move

**From `orchestration-stepfunctions/index.py` to NEW `dr-orchestration-stepfunction/index.py`:**

Create new Lambda directory with refactored code (DRS functions removed).

**Functions to Move to Handlers (from orchestration, ~720 lines total):**

1. **`start_wave_recovery(state, wave_number)`** → Move to `execution-handler`
   - **Lines**: 745-870 (~125 lines)
   - **Purpose**: Starts DRS recovery for a wave
   - **Operations**: 
     - Retrieves Protection Group from DynamoDB
     - Resolves servers using tag-based discovery
     - Applies launch configuration
     - Creates DRS job via `drs_client.start_recovery()`
     - Updates state with job details
   - **Destination**: `lambda/execution-handler/index.py`
   - **New handler action**: `start_wave_recovery`

2. **`apply_launch_config_before_recovery(...)`** → Move to `execution-handler`
   - **Lines**: 200-350 (~150 lines)
   - **Purpose**: Applies Protection Group launch configuration to DRS servers
   - **Operations**:
     - Updates DRS launch settings
     - Updates EC2 launch templates
     - Supports per-server configuration overrides
   - **Destination**: `lambda/execution-handler/index.py`
   - **Note**: Helper function called by `start_wave_recovery()`

3. **`update_wave_status(event)`** → Move to `query-handler` (rename to `poll_wave_status`)
   - **Lines**: 873-1219 (~346 lines)
   - **Purpose**: Polls DRS job status and tracks server launch progress
   - **Operations**:
     - Checks for execution cancellation
     - Polls DRS job via `drs_client.describe_jobs()`
     - Tracks individual server launch status
     - Determines wave completion
     - Starts next wave or completes execution
   - **Destination**: `lambda/query-handler/index.py`
   - **New handler action**: `poll_wave_status`

4. **`query_drs_servers_by_tags(region, tags, account_context)`** → Move to `query-handler`
   - **Lines**: 645-744 (~99 lines)
   - **Purpose**: Queries DRS servers matching ALL specified tags
   - **Operations**:
     - Creates cross-account DRS client
     - Paginates through all source servers
     - Filters by tag matching (case-insensitive, AND logic)
   - **Destination**: `lambda/query-handler/index.py`
   - **New handler action**: `query_servers_by_tags`

### What Goes in New Orchestration Lambda

**Create `lambda/dr-orchestration-stepfunction/index.py` with:**
- `lambda_handler()` - routes to appropriate handlers
- `begin_wave_plan()` - initializes wave execution, invokes execution-handler
- `store_task_token()` - pause/resume support
- `resume_wave()` - resume after pause, invokes execution-handler
- Wave sequencing logic
- State management
- DynamoDB execution tracking
- Helper functions: `get_account_context()`, `DecimalEncoder`, table getters
- **NO DRS-specific functions** (all moved to handlers)

### Changes to Orchestration Lambda

**Before (Direct DRS calls):**
```python
def begin_wave_plan(event):
    # ... initialization ...
    start_wave_recovery(state, 0)  # Direct DRS call in same Lambda
    return state

def update_wave_status(event):
    # ... DRS polling logic ...
    drs_client.describe_jobs(...)  # Direct DRS API call
    return state
```

**After (Handler invocation):**
```python
def begin_wave_plan(event):
    # ... initialization ...
    # Invoke execution-handler to start wave
    response = lambda_client.invoke(
        FunctionName=os.environ['EXECUTION_HANDLER_ARN'],
        Payload=json.dumps({
            'action': 'start_wave_recovery',
            'state': state,
            'wave_number': 0
        })
    )
    # Update state with response
    result = json.loads(response['Payload'].read())
    state.update(result)
    return state

def poll_wave_status(event):
    # Invoke query-handler to poll status
    response = lambda_client.invoke(
        FunctionName=os.environ['QUERY_HANDLER_ARN'],
        Payload=json.dumps({
            'action': 'poll_wave_status',
            'state': state
        })
    )
    # Update state with response
    result = json.loads(response['Payload'].read())
    state.update(result)
    return state
```

## Success Criteria

- New orchestration Lambda (`dr-orchestration-stepfunction`) has zero DRS imports (except shared utilities)
- New orchestration Lambda has zero DRS API calls
- 4 DRS functions moved to appropriate handlers
- Original orchestration Lambda (`orchestration-stepfunctions`) kept intact as reference
- All existing tests pass
- Execution behavior unchanged
- DynamoDB schema unchanged
- Frontend works without changes
- Handler Lambdas remain DRS-specific (no refactoring to generic)
- Step Functions updated to use new Lambda
- Easy rollback available (switch Step Functions ARN)
- CloudFormation includes both Lambdas during transition
- Can delete original Lambda after validation period

## Out of Scope

**NOT doing in this refactoring:**
- Creating new adapter Lambdas
- Making handlers generic/technology-agnostic
- Extracting ALL DRS code from handlers
- 4-phase lifecycle architecture
- Module factory pattern
- Multi-technology support
- Moving additional functions beyond the 3 specified
- Refactoring shared utilities
- Changing handler Lambda architectures

**Scope**: Move 4 functions (~720 lines) from orchestration to handlers. Create new orchestration Lambda directory. Update CloudFormation.

## Detailed Acceptance Criteria

### 1. Function Movement

#### 1.0 Create New Orchestration Lambda Directory
- [ ] Create `lambda/dr-orchestration-stepfunction/` directory
- [ ] Copy code from `lambda/orchestration-stepfunctions/` to new directory
- [ ] Keep original directory intact as reference

#### 1.1 start_wave_recovery() → execution-handler
- [ ] Function copied to `lambda/execution-handler/index.py`
- [ ] Helper function `apply_launch_config_before_recovery()` included
- [ ] All required imports added
- [ ] Action handler `start_wave_recovery` implemented in lambda_handler
- [ ] Unit tests written and passing
- [ ] Function removed from NEW orchestration Lambda (not original)

#### 1.2 update_wave_status() → query-handler  
- [ ] Function copied to `lambda/query-handler/index.py` (renamed to `poll_wave_status`)
- [ ] All required imports and constants added
- [ ] Updated to invoke execution-handler for next wave (not direct call)
- [ ] Action handler `poll_wave_status` implemented in lambda_handler
- [ ] Unit tests written and passing
- [ ] Function removed from NEW orchestration Lambda (not original)

#### 1.3 query_drs_servers_by_tags() → query-handler
- [ ] Function copied to `lambda/query-handler/index.py`
- [ ] All required imports added
- [ ] Action handler `query_servers_by_tags` implemented in lambda_handler
- [ ] Unit tests written and passing
- [ ] Function removed from NEW orchestration Lambda (not original)

### 2. Orchestration Lambda Updates

#### 2.1 Handler Invocation Pattern
- [ ] `begin_wave_plan()` updated to invoke execution-handler
- [ ] New `poll_wave_status()` function created to invoke query-handler
- [ ] `resume_wave()` updated to invoke execution-handler
- [ ] Lambda client properly configured
- [ ] Error handling for invocation failures
- [ ] State updates from handler responses

#### 2.2 Code Cleanup
- [ ] All DRS-specific functions removed
- [ ] DRS imports removed (except shared utilities)
- [ ] No direct DRS API calls remain
- [ ] Generic orchestration logic preserved

### 3. Infrastructure Updates

#### 3.1 New Lambda Resource
- [ ] `DrOrchestrationStepFunctionFunction` added to CloudFormation
- [ ] S3Key set to `lambda/dr-orchestration-stepfunction.zip`
- [ ] Function name: `${ProjectName}-dr-orch-sf-${Environment}`
- [ ] Original Lambda resource kept in CloudFormation

#### 3.2 Environment Variables
- [ ] `EXECUTION_HANDLER_ARN` added to new orchestration Lambda
- [ ] `QUERY_HANDLER_ARN` added to new orchestration Lambda
- [ ] `EXECUTION_HANDLER_ARN` added to query-handler Lambda
- [ ] `EXECUTION_HISTORY_TABLE` added to query-handler Lambda
- [ ] `PROTECTION_GROUPS_TABLE` added to execution-handler Lambda
- [ ] `EXECUTION_HISTORY_TABLE` added to execution-handler Lambda

#### 3.3 IAM Permissions
- [ ] New orchestration Lambda can invoke execution-handler
- [ ] New orchestration Lambda can invoke query-handler
- [ ] Query-handler Lambda can invoke execution-handler
- [ ] Execution-handler Lambda can read Protection Groups table
- [ ] Execution-handler Lambda can write Execution History table
- [ ] Query-handler Lambda can read/write Execution History table
- [ ] CloudFormation templates updated

#### 3.4 Step Functions Update
- [ ] Step Functions state machine updated to use new Lambda ARN
- [ ] Original Lambda ARN kept in comments for rollback

#### 3.5 Package Script Update
- [ ] `package_lambda.py` updated to include new Lambda
- [ ] Both Lambdas included in build (original + new)

### 4. Testing Requirements

#### 4.1 Unit Tests
- [ ] Orchestration Lambda invocation tests
- [ ] Execution-handler action tests
- [ ] Query-handler action tests
- [ ] All existing tests still pass

#### 4.2 Integration Tests
- [ ] Single-wave execution end-to-end
- [ ] Multi-wave execution (3 waves)
- [ ] Pause/resume workflow
- [ ] Error handling scenarios

#### 4.3 Backward Compatibility
- [ ] All 47 API endpoints functional
- [ ] Frontend displays unchanged
- [ ] DynamoDB schema unchanged
- [ ] Execution behavior identical

### 5. Performance Validation
- [ ] Execution time within ±5% of baseline
- [ ] CloudWatch metrics reviewed
- [ ] No performance degradation

### 6. Code Quality (CI/CD Pipeline Requirements)

**CRITICAL: All code must pass deploy.sh validation pipeline before deployment**

The `./scripts/deploy.sh` script enforces strict quality gates in 5 stages:

**Stage 1: Validation (BLOCKING - deployment fails if errors)**
- [ ] **cfn-lint**: CloudFormation templates pass validation
  - Uses `.venv/bin/cfn-lint` or system cfn-lint
  - Config: `.cfnlintrc.yaml`
  - Command: `cfn-lint cfn/*.yaml --config-file .cfnlintrc.yaml -f quiet`
  - **BLOCKING**: Any errors (E-level) fail deployment
- [ ] **flake8**: Python code passes linting
  - Uses `.venv/bin/flake8` or system flake8
  - Config: `.flake8`
  - Command: `flake8 lambda/ --config .flake8 --count -q`
  - **NON-BLOCKING**: Warnings allowed but should be fixed
- [ ] **black**: Python code is properly formatted
  - Uses `.venv/bin/black` or system black
  - Line length: 79 characters
  - Command: `black --check --quiet --line-length 79 lambda/`
  - **BLOCKING**: Unformatted code fails deployment
  - Fix: `black --line-length 79 lambda/`
- [ ] **TypeScript**: Frontend code passes type checking
  - Command: `npm run type-check`
  - **BLOCKING**: Type errors fail deployment

**Stage 2: Security (NON-BLOCKING - warnings only)**
- [ ] **bandit**: Python SAST security scanning
  - Uses `.venv/bin/bandit` or system bandit
  - Command: `bandit -r lambda/ -ll -q`
  - Severity: Low and Medium issues only
  - **NON-BLOCKING**: Issues logged but don't fail deployment
- [ ] **cfn_nag**: CloudFormation security validation
  - Uses Ruby gem: `cfn_nag_scan`
  - Config: `.cfn_nag_deny_list.yml`
  - Command: `cfn_nag_scan --input-path cfn/ --deny-list-path .cfn_nag_deny_list.yml`
  - **NON-BLOCKING**: Issues logged but don't fail deployment
- [ ] **detect-secrets**: Credential scanning
  - Uses `.venv/bin/detect-secrets` or system detect-secrets
  - Baseline: `.secrets.baseline`
  - Command: `detect-secrets scan --baseline .secrets.baseline`
  - **NON-BLOCKING**: Potential secrets logged but don't fail deployment
- [ ] **shellcheck**: Shell script security (Lambda scripts only)
  - Command: `shellcheck -S warning lambda/**/*.sh`
  - **NON-BLOCKING**: Issues logged but don't fail deployment
- [ ] **npm audit**: Frontend dependency vulnerabilities
  - Command: `npm audit --audit-level=critical`
  - **NON-BLOCKING**: Vulnerabilities logged but don't fail deployment

**Stage 3: Tests (BLOCKING - deployment fails if tests fail)**
- [ ] **pytest**: Python unit and integration tests
  - Uses `.venv/bin/pytest` or system pytest
  - Command: `pytest tests/unit/ tests/integration/ -q --tb=no`
  - **BLOCKING**: Test failures fail deployment
  - Must pass ALL existing tests
  - Must pass ALL new handler tests
- [ ] **vitest**: Frontend tests (integration tests skipped)
  - Command: `npm run test:skip-integration`
  - **BLOCKING**: Test failures fail deployment

**Stage 4: Git Push (ALWAYS runs)**
- [ ] Uncommitted changes warning
- [ ] Push to remote repository

**Stage 5: Deploy**
- [ ] Lambda packages built
- [ ] Artifacts synced to S3
- [ ] CloudFormation stack deployed

**Pre-Commit Hooks (Automated - runs before commit):**
- [ ] **pre-commit install**: Hooks installed locally
- [ ] **bandit**: Python security scanning (medium+ severity)
- [ ] **semgrep**: Multi-language security scanning
- [ ] **safety**: Python dependency vulnerabilities
- [ ] **cfn-lint**: CloudFormation validation
- [ ] **npm-audit**: Frontend dependency vulnerabilities
- [ ] **eslint-security**: Frontend security scanning
- [ ] **black**: Python formatting (auto-fix)
- [ ] **isort**: Import sorting (auto-fix)
- [ ] **check-yaml**: YAML syntax validation
- [ ] **check-json**: JSON syntax validation
- [ ] **trailing-whitespace**: Remove trailing whitespace (auto-fix)
- [ ] **end-of-file-fixer**: Fix file endings (auto-fix)

**Code Quality Standards (PEP 8 + Project Standards)**
- [ ] Line length: 79 characters maximum (enforced by black)
- [ ] Indentation: 4 spaces (NO TABS)
- [ ] String quotes: Double quotes `"text"`
- [ ] Imports: Standard library → Third-party → Local
- [ ] Type hints on all functions (checked by mypy if configured)
- [ ] Google-style docstrings on all public functions
- [ ] Zero Flake8 errors (warnings acceptable)
- [ ] No temporal comments (TODO, FIXME, HACK)
- [ ] All security scans pass or have documented exceptions

**Virtual Environment Requirements**
- [ ] `.venv` activated before running deploy.sh
- [ ] All tools installed: `pip install -r requirements-dev.txt`
- [ ] Tools used from `.venv/bin/` when available
- [ ] Fallback to system tools if `.venv` not found (with warning)

**Validation Commands (Run Before Committing)**
```bash
# Activate virtual environment
source .venv/bin/activate

# Install pre-commit hooks (one-time)
pip install pre-commit
pre-commit install

# Format code (auto-fix)
black --line-length 79 lambda/

# Check linting
flake8 lambda/ --config .flake8

# Run tests
pytest tests/unit/ -v
pytest tests/integration/ -v

# Validate CloudFormation
cfn-lint cfn/*.yaml --config-file .cfnlintrc.yaml

# Security scan
bandit -r lambda/ -ll

# Run all pre-commit hooks manually
pre-commit run --all-files

# Full validation (no deployment)
./scripts/deploy.sh test --validate-only
```

**Pre-Deployment Checklist**
- [ ] Pre-commit hooks installed and passing
- [ ] Code formatted with black (79 char lines)
- [ ] No flake8 errors
- [ ] All tests passing locally
- [ ] CloudFormation templates valid
- [ ] No security issues in bandit scan
- [ ] Changes committed to git
- [ ] Virtual environment activated
- [ ] `./scripts/deploy.sh test --validate-only` passes

### 7. Documentation
- [ ] Architecture documentation updated
- [ ] Function location documented (which handler has which function)
- [ ] Deployment guide updated (environment variables, IAM permissions)
- [ ] Refactoring summary document created

## Implementation Timeline

**Total Duration**: 1-2 weeks

### Week 1: Function Movement and Testing
- Days 1-2: Move `start_wave_recovery()` to execution-handler
- Days 2-3: Move `update_wave_status()` to query-handler  
- Day 3: Move `query_drs_servers_by_tags()` to query-handler
- Days 4-5: Update orchestration Lambda to invoke handlers
- Day 5: Update CloudFormation infrastructure

### Week 2: Integration Testing and Deployment
- Days 1-3: Integration testing (single-wave, multi-wave, pause/resume)
- Day 3: Performance validation
- Day 4: Documentation updates
- Day 5: Deploy to test environment and validate

## Risk Mitigation

### Technical Risks

**Risk 1: Breaking Existing DRS Functionality**
- **Likelihood**: Medium
- **Impact**: High
- **Mitigation**: 
  - Comprehensive unit tests for moved functions
  - Integration tests for end-to-end workflows
  - Deploy to test environment first
  - Keep old code in git history for quick rollback
- **Fallback**: Revert CloudFormation stack to previous version

**Risk 2: Lambda Invocation Overhead**
- **Likelihood**: Low
- **Impact**: Low
- **Mitigation**:
  - Lambda invocations add ~50-100ms overhead
  - Acceptable for orchestration workflows (minutes duration)
  - Monitor CloudWatch metrics for performance
- **Acceptance**: ±5% execution time variance acceptable

**Risk 3: State Management Complexity**
- **Likelihood**: Low
- **Impact**: Medium
- **Mitigation**:
  - State object structure unchanged
  - Handlers return updated state
  - Orchestration merges state updates
  - Extensive testing of state transitions
- **Validation**: Compare state objects before/after refactoring
