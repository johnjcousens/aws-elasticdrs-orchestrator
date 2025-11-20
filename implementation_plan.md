# Implementation Plan: Recovery Plan Bug Fixes

## [Overview]
Fix two critical bugs preventing production deployment of Recovery Plans functionality: (1) wave data transformation corruption during edit operations, and (2) delete operation failures due to execution history query issues.

This implementation plan addresses the P1 bugs identified in Session 33 that block production use of Recovery Plans. The wave data transformation bug causes inconsistent data when editing plans with renamed waves, leading to UI errors and potential data loss. The delete failure prevents cleanup of test/draft plans. Both issues stem from data serialization and query pattern problems in the Lambda API handler.

The fix involves:
- Standardizing wave data serialization across create/update/read operations
- Implementing robust ServerIds handling with defensive type checking
- Fixing the delete operation's execution history query pattern
- Adding comprehensive error handling and logging for debugging
- Creating unit tests to prevent regression

**Priority**: P1 - Blocks production deployment
**Estimated Effort**: 4-6 hours
**Risk Level**: Medium (data transformation changes require careful testing)

## [Types]
Define type safety improvements and data structure clarifications.

### Backend Type Definitions (Python)

```python
# Wave data structure (backend DynamoDB format - PascalCase)
WaveBackendSchema = {
    'WaveId': str,              # e.g., "wave-0", "wave-1"
    'WaveName': str,            # User-defined wave name
    'WaveDescription': str,     # Optional description
    'ExecutionOrder': int,      # 0-based index
    'ProtectionGroupId': str,   # UUID of Protection Group
    'ServerIds': List[str],     # Array of DRS source server IDs
    'ExecutionType': str,       # "sequential" or "parallel"
    'Dependencies': List[Dict]  # [{'DependsOnWaveId': 'wave-N'}]
}

# Wave data structure (frontend API format - camelCase)
WaveFrontendSchema = {
    'waveNumber': int,           # 0-based index
    'name': str,                 # User-defined wave name
    'description': str,          # Optional description
    'serverIds': List[str],      # Array of DRS source server IDs (CRITICAL: must be list)
    'executionType': str,        # "sequential" or "parallel"
    'dependsOnWaves': List[int], # [0, 1, 2] - wave numbers this depends on
    'protectionGroupId': str,    # UUID of Protection Group
    'protectionGroupIds': List[str]  # Array format for multi-PG support
}
```

### Type Safety Rules

1. **ServerIds MUST always be a Python list**, never string or other type
2. **Defensive type checking** required before accessing ServerIds
3. **Boto3 deserialization** can return unexpected types - validate before use
4. **PascalCase ↔ camelCase** transformation must preserve all fields
5. **Dependencies extraction** must handle missing or malformed data gracefully

## [Files]
Files to be modified for bug fixes.

### Modified Files

**lambda/index.py** (Lines 1303-1370)
- **Function**: `transform_rp_to_camelcase(rp: Dict) -> Dict`
- **Changes**:
  - Add defensive ServerIds type checking (line ~1325)
  - Add detailed logging for wave transformation (line ~1335)
  - Simplify ServerIds extraction logic (remove complex fallbacks)
  - Add exception handling for malformed data
  - Ensure consistent field transformation (PascalCase → camelCase)

**lambda/index.py** (Lines 519-545)
- **Function**: `delete_recovery_plan(plan_id: str) -> Dict`
- **Changes**:
  - Replace scan with query using GSI (if exists) or optimize FilterExpression
  - Add proper error handling for DynamoDB operations
  - Improve error messages for debugging
  - Add logging for delete operations

**lambda/index.py** (Lines 475-517)
- **Function**: `update_recovery_plan(plan_id: str, body: Dict) -> Dict`
- **Changes**:
  - Add pre-transform logging of incoming wave data
  - Ensure consistent wave data structure before DynamoDB write
  - Add validation for ServerIds field type
  - Return transformed data consistently

### Test Files to Create

**tests/python/unit/test_wave_transformation.py** (NEW)
- Unit tests for `transform_rp_to_camelcase`
- Test cases for various ServerIds formats
- Test cases for missing/malformed data
- Test cases for dependency extraction

**tests/python/unit/test_recovery_plan_operations.py** (NEW)
- Unit tests for delete_recovery_plan
- Mock DynamoDB responses
- Test active execution blocking
- Test successful deletion

## [Functions]
Function-level changes required for bug fixes.

### 1. transform_rp_to_camelcase (lambda/index.py:1303)

**Current Issue**: Complex ServerIds extraction with multiple fallbacks can fail when boto3 deserializes DynamoDB data inconsistently.

**Required Changes**:

```python
def transform_rp_to_camelcase(rp: Dict) -> Dict:
    """Transform Recovery Plan from DynamoDB PascalCase to frontend camelCase"""
    
    # Transform waves array from backend PascalCase to frontend camelCase
    waves = []
    for idx, wave in enumerate(rp.get('Waves', [])):
        # CRITICAL FIX: Defensive ServerIds extraction
        server_ids = wave.get('ServerIds', [])
        
        # DEFENSIVE: Ensure we have a list (boto3 deserialization issue)
        if not isinstance(server_ids, list):
            print(f"ERROR: ServerIds is not a list for wave {idx}, got type {type(server_ids)}: {server_ids}")
            # Attempt recovery: wrap in list if string, empty list otherwise
            if isinstance(server_ids, str):
                server_ids = [server_ids]
            else:
                server_ids = []
        
        # LOGGING: Track transformation for debugging
        print(f"Transforming wave {idx}: name={wave.get('WaveName')}, serverIds={server_ids}, count={len(server_ids)}")
        
        # Extract dependency wave numbers from WaveId format
        depends_on_waves = []
        for dep in wave.get('Dependencies', []):
            wave_id = dep.get('DependsOnWaveId', '')
            if wave_id and '-' in wave_id:
                try:
                    wave_num = int(wave_id.split('-')[-1])
                    depends_on_waves.append(wave_num)
                except (ValueError, IndexError) as e:
                    print(f"WARNING: Failed to parse dependency wave ID '{wave_id}': {e}")
        
        waves.append({
            'waveNumber': idx,
            'name': wave.get('WaveName', ''),
            'description': wave.get('WaveDescription', ''),
            'serverIds': server_ids,  # Now guaranteed to be a list
            'executionType': wave.get('ExecutionType', 'sequential'),
            'dependsOnWaves': depends_on_waves,
            'protectionGroupId': wave.get('ProtectionGroupId'),
            'protectionGroupIds': [wave.get('ProtectionGroupId')] if wave.get('ProtectionGroupId') else []
        })
    
    # Transform top-level fields
    return {
        'id': rp.get('PlanId'),
        'name': rp.get('PlanName'),
        'description': rp.get('Description', ''),
        'accountId': rp.get('AccountId'),
        'region': rp.get('Region'),
        'owner': rp.get('Owner'),
        'rpo': rp.get('RPO'),
        'rto': rp.get('RTO'),
        'waves': waves,
        'createdAt': rp.get('CreatedDate'),
        'updatedAt': rp.get('LastModifiedDate'),
        'lastExecutedAt': rp.get('LastExecutedDate'),
        'waveCount': len(waves)
    }
```

**Test Coverage**:
- Test with properly formatted ServerIds list
- Test with single string ServerIds (edge case)
- Test with missing ServerIds field
- Test with empty Waves array
- Test with complex Dependencies

### 2. delete_recovery_plan (lambda/index.py:519)

**Current Issue**: Uses `scan()` with FilterExpression which is inefficient and may fail with large datasets or when GSI doesn't exist.

**Required Changes**:

```python
def delete_recovery_plan(plan_id: str) -> Dict:
    """Delete a Recovery Plan if no active executions exist"""
    try:
        # OPTION 1: Query with GSI if available (preferred)
        # Check CloudFormation template for ExecutionHistory table GSI
        # If PlanIdIndex exists:
        try:
            executions_result = execution_history_table.query(
                IndexName='PlanIdIndex',
                KeyConditionExpression=Key('PlanId').eq(plan_id),
                FilterExpression=Attr('Status').eq('RUNNING'),
                Limit=1  # Only need to find one
            )
        except Exception as gsi_error:
            # FALLBACK: GSI doesn't exist or error, use scan
            print(f"GSI query failed, falling back to scan: {gsi_error}")
            executions_result = execution_history_table.scan(
                FilterExpression=Attr('PlanId').eq(plan_id) & Attr('Status').eq('RUNNING'),
                Limit=1
            )
        
        # Check if any active executions found
        if executions_result.get('Items'):
            active_count = len(executions_result['Items'])
            print(f"Cannot delete plan {plan_id}: {active_count} active execution(s)")
            return response(409, {  # Conflict
                'error': 'PLAN_HAS_ACTIVE_EXECUTIONS',
                'message': f'Cannot delete Recovery Plan with {active_count} active execution(s)',
                'activeExecutions': active_count,
                'planId': plan_id
            })
        
        # No active executions, safe to delete
        print(f"Deleting Recovery Plan: {plan_id}")
        recovery_plans_table.delete_item(Key={'PlanId': plan_id})
        
        print(f"Successfully deleted Recovery Plan: {plan_id}")
        return response(200, {
            'message': 'Recovery Plan deleted successfully',
            'planId': plan_id
        })
        
    except Exception as e:
        print(f"Error deleting Recovery Plan {plan_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {
            'error': 'DELETE_FAILED',
            'message': f'Failed to delete Recovery Plan: {str(e)}',
            'planId': plan_id
        })
```

**Test Coverage**:
- Test with no executions (should succeed)
- Test with active RUNNING execution (should fail with 409)
- Test with COMPLETED executions only (should succeed)
- Test with non-existent plan ID
- Test DynamoDB error handling

### 3. update_recovery_plan (lambda/index.py:475)

**Enhancement**: Add pre-write validation and logging.

```python
def update_recovery_plan(plan_id: str, body: Dict) -> Dict:
    """Update an existing Recovery Plan"""
    try:
        # ... existing validation ...
        
        # NEW: Pre-write validation for Waves
        if 'Waves' in body:
            print(f"Updating plan {plan_id} with {len(body['Waves'])} waves")
            
            # DEFENSIVE: Validate ServerIds in each wave
            for idx, wave in enumerate(body['Waves']):
                server_ids = wave.get('ServerIds', [])
                if not isinstance(server_ids, list):
                    print(f"ERROR: Wave {idx} ServerIds is not a list: {type(server_ids)}")
                    return response(400, {
                        'error': 'INVALID_WAVE_DATA',
                        'message': f'Wave {idx} has invalid ServerIds format (must be array)',
                        'waveIndex': idx
                    })
                print(f"Wave {idx}: {wave.get('WaveName')} - {len(server_ids)} servers")
        
        # ... rest of existing code ...
    except Exception as e:
        print(f"Error updating Recovery Plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': str(e)})
```

## [Classes]
No class changes required (Python Lambda uses functional programming).

## [Dependencies]
No new dependencies required - using existing boto3 and Python 3.12 standard library.

### Existing Dependencies
- boto3: AWS SDK (DynamoDB, Step Functions, DRS clients)
- Python 3.12 standard library (json, os, uuid, time, typing)

## [Testing]
Comprehensive test coverage for bug fixes.

### Unit Tests (tests/python/unit/test_wave_transformation.py)

```python
import pytest
from unittest.mock import MagicMock
from lambda.index import transform_rp_to_camelcase

class TestWaveTransformation:
    """Test wave data transformation logic"""
    
    def test_transform_with_valid_server_ids_list(self):
        """Test transformation with properly formatted ServerIds"""
        rp = {
            'PlanId': 'plan-123',
            'PlanName': 'Test Plan',
            'Waves': [{
                'WaveId': 'wave-0',
                'WaveName': 'Wave 1',
                'ServerIds': ['s-123', 's-456'],
                'ProtectionGroupId': 'pg-789'
            }]
        }
        result = transform_rp_to_camelcase(rp)
        assert result['waves'][0]['serverIds'] == ['s-123', 's-456']
    
    def test_transform_with_string_server_ids(self):
        """Test recovery from string ServerIds (edge case)"""
        rp = {
            'PlanId': 'plan-123',
            'Waves': [{
                'WaveId': 'wave-0',
                'ServerIds': 's-123'  # STRING instead of list
            }]
        }
        result = transform_rp_to_camelcase(rp)
        assert isinstance(result['waves'][0]['serverIds'], list)
    
    def test_transform_with_missing_server_ids(self):
        """Test handling of missing ServerIds field"""
        rp = {
            'PlanId': 'plan-123',
            'Waves': [{
                'WaveId': 'wave-0'
                # ServerIds missing
            }]
        }
        result = transform_rp_to_camelcase(rp)
        assert result['waves'][0]['serverIds'] == []
```

### Integration Tests (tests/python/integration/test_recovery_plan_delete.py)

```python
import pytest
import boto3
from moto import mock_dynamodb
from lambda.index import delete_recovery_plan

@mock_dynamodb
class TestRecoveryPlanDelete:
    """Test delete operation with mocked DynamoDB"""
    
    def test_delete_with_no_executions(self, setup_tables):
        """Should succeed when no active executions"""
        response = delete_recovery_plan('plan-123')
        assert response['statusCode'] == 200
    
    def test_delete_with_active_execution(self, setup_tables, create_running_execution):
        """Should fail with 409 when active execution exists"""
        response = delete_recovery_plan('plan-123')
        assert response['statusCode'] == 409
        assert 'active execution' in response['body'].lower()
```

## [Implementation Order]
Step-by-step implementation sequence to minimize risk.

**Step 1**: Fix transform_rp_to_camelcase function (30 min)
- Add defensive ServerIds type checking
- Add comprehensive logging
- Simplify extraction logic
- Test with various input formats

**Step 2**: Fix delete_recovery_plan function (20 min)
- Add GSI query with scan fallback
- Improve error handling
- Add detailed logging
- Test with active/inactive executions

**Step 3**: Enhance update_recovery_plan validation (15 min)
- Add pre-write ServerIds validation
- Add logging for debugging
- Test with malformed input

**Step 4**: Create unit tests (45 min)
- Write test_wave_transformation.py
- Write test_recovery_plan_operations.py
- Achieve 90%+ coverage of modified functions
- Run pytest to verify

**Step 5**: Manual testing (30 min)
- Deploy to TEST environment
- Create Recovery Plan with 2 waves
- Edit plan and rename waves
- Verify wave data persists correctly
- Test delete with/without active executions
- Verify CloudWatch logs show detailed diagnostics

**Step 6**: Documentation (15 min)
- Update PROJECT_STATUS.md with bug fix session
- Document the root cause and fix
- Add troubleshooting notes

**Total Estimated Time**: 2.5 hours for implementation + 1.5 hours for testing = 4 hours
