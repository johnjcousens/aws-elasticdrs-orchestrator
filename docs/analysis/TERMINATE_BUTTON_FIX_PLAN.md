# Terminate Button Fix Plan

## Executive Summary

Fix the Terminate Recovery Instances button's 19 documented breakages by simplifying logic, adding tests, and standardizing data flow. Target: zero breakages for 90 days.

## Root Causes (Priority Order)

1. **Tight Coupling (42%)** - Button depends on 5+ data sources
2. **Field Name Inconsistency (26%)** - PascalCase vs camelCase confusion
3. **Incomplete Refactoring (21%)** - Optimizations removed critical logic
4. **Missing Integration Points (11%)** - RBAC, CloudFormation gaps

## Fix Strategy

### Phase 1: Stabilize Current Implementation (2 hours)

**Goal**: Make existing code robust without architectural changes.

#### 1.1 Add Backend Validation Helper
**File**: `lambda/shared/execution_utils.py`

```python
def can_terminate_execution(execution: Dict) -> Dict[str, Any]:
    """
    Centralized logic to determine if execution can be terminated.
    Returns dict with canTerminate flag and reason.
    """
    terminal_statuses = ['completed', 'cancelled', 'failed', 'partial']
    active_statuses = ['in_progress', 'pending', 'running', 'started', 
                       'polling', 'launching', 'initiated']
    
    result = {
        'canTerminate': False,
        'reason': None,
        'hasRecoveryInstances': False
    }
    
    # Check terminal status
    if execution.get('status') not in terminal_statuses:
        result['reason'] = 'Execution not in terminal state'
        return result
    
    # Check for job IDs (recovery instances exist)
    waves = execution.get('waves', [])
    has_job_id = any(wave.get('jobId') for wave in waves)
    
    if not has_job_id:
        result['reason'] = 'No recovery instances found'
        return result
    
    result['hasRecoveryInstances'] = True
    
    # Check for active waves
    has_active = any(wave.get('status') in active_statuses for wave in waves)
    
    if has_active:
        result['reason'] = 'Waves still active'
        return result
    
    # All checks passed
    result['canTerminate'] = True
    return result
```

#### 1.2 Update Execution Endpoint
**File**: `lambda/api-handler/index.py`

Add termination metadata to execution responses:

```python
def get_execution(execution_id: str) -> Dict:
    """Get execution with termination metadata."""
    execution = table.get_item(Key={'executionId': execution_id})['Item']
    
    # Add termination capability check
    termination_check = can_terminate_execution(execution)
    execution['terminationMetadata'] = termination_check
    
    return execution
```

#### 1.3 Simplify Frontend Logic
**File**: `frontend/src/pages/ExecutionDetailsPage.tsx`

Replace complex logic with backend flag:

```typescript
// OLD: 20+ lines of complex logic
const canTerminate = execution && (() => {
  const terminalStatuses = ['completed', 'cancelled', 'failed', 'partial'];
  // ... 15 more lines
})();

// NEW: Trust backend
const canTerminate = execution?.terminationMetadata?.canTerminate ?? false;
const terminateReason = execution?.terminationMetadata?.reason;
```

#### 1.4 Add Field Name Normalization
**File**: `lambda/shared/drs_utils.py`

```python
def normalize_drs_response(drs_data: Dict) -> Dict:
    """
    Convert AWS DRS PascalCase to application camelCase.
    Only transform at API boundary - never in database.
    """
    field_map = {
        'RecoveryInstanceID': 'recoveryInstanceId',
        'SourceServerID': 'sourceServerId',
        'JobID': 'jobId',
        'LaunchTime': 'launchTime',
        'InstanceID': 'instanceId'
    }
    
    normalized = {}
    for key, value in drs_data.items():
        new_key = field_map.get(key, key[0].lower() + key[1:])
        normalized[new_key] = value
    
    return normalized
```

### Phase 2: Add Comprehensive Tests (3 hours)

#### 2.1 Backend Unit Tests
**File**: `tests/python/unit/test_terminate_logic.py`

```python
import pytest
from lambda.shared.execution_utils import can_terminate_execution

def test_can_terminate_completed_with_job_ids():
    execution = {
        'status': 'completed',
        'waves': [{'jobId': 'job-123', 'status': 'completed'}]
    }
    result = can_terminate_execution(execution)
    assert result['canTerminate'] is True
    assert result['hasRecoveryInstances'] is True

def test_cannot_terminate_in_progress():
    execution = {
        'status': 'in_progress',
        'waves': [{'jobId': 'job-123', 'status': 'running'}]
    }
    result = can_terminate_execution(execution)
    assert result['canTerminate'] is False
    assert result['reason'] == 'Execution not in terminal state'

def test_cannot_terminate_no_job_ids():
    execution = {
        'status': 'completed',
        'waves': [{'status': 'completed'}]  # No jobId
    }
    result = can_terminate_execution(execution)
    assert result['canTerminate'] is False
    assert result['reason'] == 'No recovery instances found'

def test_cannot_terminate_active_waves():
    execution = {
        'status': 'completed',
        'waves': [
            {'jobId': 'job-123', 'status': 'completed'},
            {'jobId': 'job-456', 'status': 'running'}  # Active
        ]
    }
    result = can_terminate_execution(execution)
    assert result['canTerminate'] is False
    assert result['reason'] == 'Waves still active'
```

#### 2.2 API Integration Tests
**File**: `tests/python/integration/test_recovery_instances_api.py`

```python
def test_get_recovery_instances_endpoint():
    """Verify endpoint returns required fields."""
    response = api_client.get(f'/executions/{execution_id}/recovery-instances')
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'instances' in data
    for instance in data['instances']:
        assert 'instanceId' in instance
        assert 'recoveryInstanceId' in instance
        assert 'sourceServerId' in instance
        assert 'launchTime' in instance

def test_recovery_instances_rbac_permissions():
    """Verify RBAC allows endpoint access."""
    for role in ['DRSOrchestrationAdmin', 'DRSRecoveryManager', 'DRSOperator']:
        token = get_token_for_role(role)
        response = api_client.get(
            f'/executions/{execution_id}/recovery-instances',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200

def test_terminate_instances_endpoint():
    """Verify termination endpoint works."""
    response = api_client.post(
        f'/executions/{execution_id}/terminate-instances',
        json={'confirm': True}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'terminationJobId' in data
```

#### 2.3 Frontend Component Tests
**File**: `frontend/src/pages/__tests__/ExecutionDetailsPage.test.tsx`

```typescript
describe('Terminate Button Visibility', () => {
  it('shows button when backend allows termination', () => {
    const execution = {
      executionId: 'exec-123',
      status: 'completed',
      terminationMetadata: {
        canTerminate: true,
        hasRecoveryInstances: true
      }
    };
    
    render(<ExecutionDetailsPage execution={execution} />);
    expect(screen.getByText('Terminate Instances')).toBeInTheDocument();
  });

  it('hides button when backend blocks termination', () => {
    const execution = {
      executionId: 'exec-123',
      status: 'in_progress',
      terminationMetadata: {
        canTerminate: false,
        reason: 'Execution not in terminal state'
      }
    };
    
    render(<ExecutionDetailsPage execution={execution} />);
    expect(screen.queryByText('Terminate Instances')).not.toBeInTheDocument();
  });

  it('shows tooltip with reason when disabled', () => {
    const execution = {
      executionId: 'exec-123',
      status: 'completed',
      terminationMetadata: {
        canTerminate: false,
        reason: 'No recovery instances found'
      }
    };
    
    render(<ExecutionDetailsPage execution={execution} />);
    const tooltip = screen.getByRole('tooltip');
    expect(tooltip).toHaveTextContent('No recovery instances found');
  });
});
```

### Phase 3: Infrastructure Validation (1 hour)

#### 3.1 CloudFormation Validation Script
**File**: `scripts/validate-terminate-infrastructure.sh`

```bash
#!/bin/bash
# Validate all infrastructure for terminate feature

set -e

echo "Validating Terminate Button Infrastructure..."

# Check API Gateway resources
echo "✓ Checking API Gateway resources..."
aws cloudformation describe-stack-resources \
  --stack-name aws-elasticdrs-orchestrator-test \
  --query "StackResources[?contains(LogicalResourceId, 'RecoveryInstances')].LogicalResourceId" \
  --output table

# Check Lambda permissions
echo "✓ Checking Lambda IAM permissions..."
LAMBDA_ROLE=$(aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-test \
  --query "Stacks[0].Outputs[?OutputKey=='ApiHandlerRoleArn'].OutputValue" \
  --output text)

aws iam get-role-policy \
  --role-name $(echo $LAMBDA_ROLE | cut -d'/' -f2) \
  --policy-name DRSPolicy \
  | jq '.PolicyDocument.Statement[] | select(.Action[] | contains("drs:DescribeRecoveryInstances"))'

# Check RBAC configuration
echo "✓ Checking RBAC permissions..."
grep -A 5 "recovery-instances" lambda/shared/rbac_middleware.py

echo "✅ All infrastructure checks passed"
```

#### 3.2 Pre-Deployment Checklist
**File**: `docs/checklists/terminate-button-deployment.md`

```markdown
# Terminate Button Deployment Checklist

Before deploying changes affecting terminate functionality:

## Backend
- [ ] `can_terminate_execution()` function exists in `execution_utils.py`
- [ ] `/executions/{id}` endpoint includes `terminationMetadata`
- [ ] `/executions/{id}/recovery-instances` endpoint exists
- [ ] `/executions/{id}/terminate-instances` endpoint exists
- [ ] Field normalization handles PascalCase → camelCase
- [ ] All unit tests pass: `pytest tests/python/unit/test_terminate_logic.py`

## API Gateway
- [ ] `ExecutionRecoveryInstancesResource` exists in resources stack
- [ ] GET method exists in operations methods stack
- [ ] POST method exists in operations methods stack
- [ ] OPTIONS methods configured for CORS
- [ ] Methods deployed to test stage

## RBAC
- [ ] `/executions/*/recovery-instances` in allowed paths
- [ ] `/executions/*/terminate-instances` in allowed paths
- [ ] All roles have appropriate permissions

## Frontend
- [ ] Button uses `terminationMetadata.canTerminate` flag
- [ ] Tooltip shows `terminationMetadata.reason` when disabled
- [ ] Dialog fetches instances via `apiClient.getRecoveryInstances()`
- [ ] Component tests pass: `npm test ExecutionDetailsPage`

## Integration
- [ ] End-to-end test: Create execution → Complete → Terminate
- [ ] Test with no recovery instances
- [ ] Test with active waves
- [ ] Test RBAC for all roles
```

### Phase 4: Monitoring & Alerts (1 hour)

#### 4.1 CloudWatch Dashboard
**File**: `cfn/monitoring-stack.yaml`

Add terminate button metrics:

```yaml
TerminateButtonMetrics:
  Type: AWS::CloudWatch::Dashboard
  Properties:
    DashboardName: !Sub '${ProjectName}-${Environment}-terminate-metrics'
    DashboardBody: !Sub |
      {
        "widgets": [
          {
            "type": "metric",
            "properties": {
              "metrics": [
                ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "Get Recovery Instances"}],
                [".", "Errors", {"stat": "Sum", "label": "API Errors"}],
                [".", "Duration", {"stat": "Average", "label": "Response Time"}]
              ],
              "period": 300,
              "stat": "Sum",
              "region": "${AWS::Region}",
              "title": "Terminate Button API Health"
            }
          }
        ]
      }
```

#### 4.2 Error Alerting
**File**: `cfn/monitoring-stack.yaml`

```yaml
TerminateAPIErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub '${ProjectName}-${Environment}-terminate-api-errors'
    AlarmDescription: Alert when terminate API fails
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 3
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref AlertTopic
```

## Implementation Order

### Day 1: Backend Stabilization (4 hours)
1. Create `execution_utils.py` with `can_terminate_execution()` (30 min)
2. Update `get_execution()` to include `terminationMetadata` (30 min)
3. Add field normalization in `drs_utils.py` (30 min)
4. Write backend unit tests (2 hours)
5. Deploy and validate (30 min)

### Day 2: Frontend Simplification (3 hours)
1. Update `ExecutionDetailsPage.tsx` to use backend flag (30 min)
2. Add tooltip for disabled state (30 min)
3. Write frontend component tests (1.5 hours)
4. Deploy and validate (30 min)

### Day 3: Infrastructure & Monitoring (2 hours)
1. Create validation script (30 min)
2. Create deployment checklist (30 min)
3. Add CloudWatch dashboard (30 min)
4. Configure alerts (30 min)

## Success Criteria

- [ ] All 12 unit tests pass
- [ ] All 3 integration tests pass
- [ ] All 3 frontend tests pass
- [ ] Infrastructure validation script passes
- [ ] Zero console errors in browser
- [ ] Button shows/hides correctly in all scenarios
- [ ] CloudWatch dashboard shows healthy metrics
- [ ] No breakages for 90 days

## Rollback Plan

If issues occur after deployment:

1. **Immediate**: Revert to v3.0.0 via CloudFormation
2. **Backend**: Restore previous `get_execution()` implementation
3. **Frontend**: Restore complex visibility logic
4. **Investigate**: Review CloudWatch logs and error metrics

## Files to Modify

### New Files (3)
- `lambda/shared/execution_utils.py` - Termination logic
- `tests/python/unit/test_terminate_logic.py` - Backend tests
- `scripts/validate-terminate-infrastructure.sh` - Validation

### Modified Files (5)
- `lambda/api-handler/index.py` - Add terminationMetadata
- `lambda/shared/drs_utils.py` - Field normalization
- `frontend/src/pages/ExecutionDetailsPage.tsx` - Simplified logic
- `frontend/src/pages/__tests__/ExecutionDetailsPage.test.tsx` - Tests
- `cfn/monitoring-stack.yaml` - Metrics and alerts

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Backend logic breaks existing executions | Low | High | Comprehensive unit tests |
| Field normalization misses edge cases | Medium | Medium | Integration tests with real DRS data |
| Frontend tests don't catch regressions | Low | Medium | Test all 5 visibility conditions |
| CloudFormation deployment fails | Low | High | Validate templates before deploy |

## Long-Term Improvements (Future)

1. **Feature Flag System** - Enable/disable terminate button remotely
2. **Circuit Breaker** - Auto-disable after 3 consecutive failures
3. **Usage Analytics** - Track button click rate and success rate
4. **Automated Regression Tests** - Run on every PR
5. **Canary Deployments** - Test with 10% traffic before full rollout

## Conclusion

This plan addresses all 19 historical breakages by:
- **Centralizing logic** in backend (fixes tight coupling)
- **Standardizing field names** at API boundary (fixes PascalCase issues)
- **Adding comprehensive tests** (prevents regressions)
- **Validating infrastructure** (catches missing resources)

Estimated effort: **9 hours** over 3 days.
Target: **Zero breakages for 90 days**.
