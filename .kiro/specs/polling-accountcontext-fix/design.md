# Polling AccountContext Fix - Design

## Overview

This design addresses the bug where `get_execution_details_realtime()` fails to pass `accountContext` to `reconcile_wave_status_with_drs()`, causing cross-account DRS queries to fail during polling operations.

## Architecture

### Current Flow (Broken)

```
get_execution_details_realtime(execution_id)
  ↓
Query DynamoDB → execution record (contains accountContext)
  ↓
reconcile_wave_status_with_drs(execution)  ← Missing account_context parameter!
  ↓
create_drs_client(region, account_context)  ← account_context is None
  ↓
❌ Failed to assume role None
```

### Fixed Flow

```
get_execution_details_realtime(execution_id)
  ↓
Query DynamoDB → execution record (contains accountContext)
  ↓
Extract: account_context = execution.get("accountContext")
  ↓
reconcile_wave_status_with_drs(execution, account_context)  ← Pass account_context!
  ↓
create_drs_client(region, account_context)  ← account_context has roleArn
  ↓
✅ Successfully assume role and query DRS
```

## Implementation Details

### Code Change Location

**File**: `lambda/execution-handler/index.py`  
**Function**: `get_execution_details_realtime()`  
**Line**: 3671

### Current Code (Broken)

```python
# REAL-TIME WAVE STATUS: Reconcile wave status with actual DRS job results
try:
    print("Reconciling wave status with real-time DRS data")
    execution = reconcile_wave_status_with_drs(execution)  # ← Missing account_context!
except Exception as reconcile_error:
    print(f"Error reconciling wave status: {reconcile_error}")
```

### Fixed Code

```python
# REAL-TIME WAVE STATUS: Reconcile wave status with actual DRS job results
try:
    print("Reconciling wave status with real-time DRS data")
    
    # Get account context from execution record for cross-account DRS queries
    account_context = execution.get("accountContext")
    if account_context:
        print(f"Using account context for polling: accountId={account_context.get('accountId')}, "
              f"isCurrentAccount={account_context.get('isCurrentAccount')}")
    
    execution = reconcile_wave_status_with_drs(execution, account_context)
except Exception as reconcile_error:
    print(f"Error reconciling wave status: {reconcile_error}")
```

## Data Structures

### AccountContext Structure

Stored in execution record at creation time (line 674):

```python
{
    "accountId": "160885257264",           # Target AWS account ID
    "assumeRoleName": "DRSOrchestrationCrossAccountRole",  # IAM role name
    "isCurrentAccount": False,             # True if no role assumption needed
    "externalId": "optional-external-id"   # Optional external ID for role assumption
}
```

### Execution Record Structure

```python
{
    "executionId": "394362de-b17f-426b-a301-433f265ad21f",
    "planId": "c5621161-98af-41ed-8e06-652cd3f88152",
    "status": "RUNNING",
    "accountContext": {                    # ← This is what we need to extract
        "accountId": "160885257264",
        "assumeRoleName": "DRSOrchestrationCrossAccountRole",
        "isCurrentAccount": False
    },
    "waves": [...],
    ...
}
```

## Function Signatures

### reconcile_wave_status_with_drs()

```python
def reconcile_wave_status_with_drs(
    execution: Dict, 
    account_context: Optional[Dict] = None
) -> Dict:
    """
    Reconcile wave status with actual DRS job results - REAL-TIME DATA.
    
    Args:
        execution: Execution data with waves to reconcile
        account_context: Optional cross-account context with roleArn and externalId
    
    Returns:
        Updated execution with reconciled wave statuses
    """
```

### create_drs_client()

From `lambda/shared/cross_account.py`:

```python
def create_drs_client(
    region: str, 
    account_context: Optional[Dict] = None
):
    """
    Create DRS client with optional cross-account IAM role assumption.
    
    Args:
        region: AWS region for DRS operations
        account_context: Optional dict with accountId and assumeRoleName
    
    Returns:
        boto3 DRS client configured for target account and region
    """
```

## Consistency Check

### Other Callers of reconcile_wave_status_with_drs()

1. **Line 2201** - `get_execution_details()` (non-realtime):
   ```python
   account_context = execution.get("accountContext")
   execution = reconcile_wave_status_with_drs(execution, account_context)
   ```
   ✅ **Already correct** - passes account_context

2. **Line 3671** - `get_execution_details_realtime()` (polling):
   ```python
   execution = reconcile_wave_status_with_drs(execution)
   ```
   ❌ **BROKEN** - missing account_context (this is what we're fixing)

### Verification

After the fix, both callers will consistently pass `account_context`:
- Non-realtime endpoint: ✅ Passes account_context
- Realtime endpoint (polling): ✅ Will pass account_context after fix

## Error Handling

### Backwards Compatibility

Handle executions created before accountContext was added:

```python
account_context = execution.get("accountContext")
# If None, reconcile_wave_status_with_drs() will use current account credentials
```

### Logging Strategy

```python
if account_context:
    print(f"Using account context for polling: accountId={account_context.get('accountId')}, "
          f"isCurrentAccount={account_context.get('isCurrentAccount')}")
else:
    print("No account context found - using current account credentials")
```

## Testing Strategy

### Unit Test Cases

1. **Test with cross-account execution**:
   - Execution record has `accountContext` with `isCurrentAccount=False`
   - Verify `account_context` is extracted and passed
   - Verify cross-account DRS client is created

2. **Test with same-account execution**:
   - Execution record has `accountContext` with `isCurrentAccount=True`
   - Verify `account_context` is extracted and passed
   - Verify no role assumption occurs

3. **Test with missing accountContext**:
   - Execution record has no `accountContext` field
   - Verify `None` is passed to reconciliation function
   - Verify current account credentials are used

### Integration Test

1. Start TargetAccountOnly recovery drill (execution ID: 394362de-b17f-426b-a301-433f265ad21f)
2. Wait for DRS job to start
3. Poll via frontend: `GET /executions/{executionId}?realtime=true`
4. Check CloudWatch logs for:
   - ✅ "Using account context for polling: accountId=160885257264"
   - ✅ "Created cross-account DRS client for region us-east-1"
   - ❌ No "Failed to assume role None" errors
5. Verify UI shows server statuses updating from PENDING to LAUNCHED

## Deployment

### Deployment Method

```bash
./scripts/deploy.sh test --lambda-only
```

### Verification Steps

1. Deploy Lambda code
2. Check Lambda version updated:
   ```bash
   AWS_PAGER="" aws lambda get-function \
     --function-name hrp-drs-tech-adapter-execution-handler-dev \
     --query 'Configuration.LastModified'
   ```
3. Start a recovery drill
4. Monitor CloudWatch logs for successful cross-account queries
5. Verify frontend shows real-time status updates

## Rollback Plan

If the fix causes issues:

1. Revert the code change (restore line 3671 to original)
2. Redeploy: `./scripts/deploy.sh test --lambda-only`
3. Investigate why the fix failed
4. Check if `accountContext` structure changed
5. Verify cross-account role configuration

## Related Code

### Files Modified
- `lambda/execution-handler/index.py` (line 3671)

### Files Referenced (No Changes)
- `lambda/shared/cross_account.py` (create_drs_client, create_ec2_client)
- `lambda/execution-handler/index.py` (reconcile_wave_status_with_drs function)

## Success Metrics

1. **Zero Role Assumption Errors**: No "Failed to assume role None" in CloudWatch logs
2. **Successful DRS Queries**: All DRS job status queries succeed during polling
3. **UI Updates**: Server statuses update correctly in frontend
4. **No Regressions**: Same-account executions continue working
5. **Consistent Logging**: All polling operations log account context usage

## Future Improvements

1. **Centralized AccountContext Retrieval**: Create a helper function to extract and validate accountContext
2. **Type Hints**: Add TypedDict for accountContext structure
3. **Validation**: Add validation to ensure accountContext has required fields
4. **Monitoring**: Add CloudWatch metric for cross-account query success rate
