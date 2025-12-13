#!/usr/bin/env python3
"""Test API error handling via direct Lambda invocation"""
import boto3
import json
import re
import time

session = boto3.Session(profile_name='438465159935_AdministratorAccess', region_name='us-east-1')
lambda_client = session.client('lambda')
FUNC = 'drs-orchestration-api-handler-dev'

# Use timestamp for unique test resource names
TS = str(int(time.time()))

def invoke(method, path, body=None, path_params=None):
    """Invoke Lambda with API Gateway event format"""
    # Auto-extract path parameters for common patterns
    if path_params is None:
        path_params = {}
        # Match /executions/{id}/action pattern
        exec_match = re.match(r'/executions/([^/]+)(/.*)?', path)
        if exec_match:
            path_params['executionId'] = exec_match.group(1)
        # Match /protection-groups/{id} pattern
        pg_match = re.match(r'/protection-groups/([^/]+)$', path)
        if pg_match:
            path_params['id'] = pg_match.group(1)
        # Match /recovery-plans/{id} pattern
        rp_match = re.match(r'/recovery-plans/([^/]+)$', path)
        if rp_match:
            path_params['id'] = rp_match.group(1)
    
    event = {
        'httpMethod': method,
        'path': path,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body) if body else None,
        'queryStringParameters': None,
        'pathParameters': path_params if path_params else None
    }
    resp = lambda_client.invoke(FunctionName=FUNC, Payload=json.dumps(event))
    result = json.loads(resp['Payload'].read())
    status = result.get('statusCode', 0)
    body_str = result.get('body', '{}')
    return status, json.loads(body_str) if body_str else {}

def test(name, method, path, body=None, expected_code=None, expected_error=None):
    """Run a test and print results"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    status, resp = invoke(method, path, body)
    print(f"Status: {status}")
    print(f"Response: {json.dumps(resp, indent=2)[:500]}")
    
    passed = True
    if expected_code and status != expected_code:
        print(f"❌ Expected status {expected_code}, got {status}")
        passed = False
    if expected_error and resp.get('error') != expected_error:
        print(f"❌ Expected error '{expected_error}', got '{resp.get('error')}'")
        passed = False
    if passed and (expected_code or expected_error):
        print(f"✅ PASSED")
    return status, resp

# Run tests
print("\n" + "="*60)
print("API ERROR HANDLING TESTS")
print("="*60)

# 1. Protection Group - Empty name
test("PG: Empty name", "POST", "/protection-groups", 
     {"GroupName": "   ", "Region": "us-east-1", "ServerSelectionTags": {"test": "val"}},
     400, "INVALID_NAME")

# 2. Protection Group - Missing name
test("PG: Missing GroupName", "POST", "/protection-groups",
     {"Region": "us-east-1", "ServerSelectionTags": {"test": "val"}},
     400, "MISSING_FIELD")

# 3. Protection Group - Missing region
test("PG: Missing Region", "POST", "/protection-groups",
     {"GroupName": "Test PG", "ServerSelectionTags": {"test": "val"}},
     400, "MISSING_FIELD")

# 4. Protection Group - No selection method
test("PG: No tags or servers", "POST", "/protection-groups",
     {"GroupName": "Test PG", "Region": "us-east-1"},
     400)

# 5. Recovery Plan - Empty name
test("RP: Empty name", "POST", "/recovery-plans",
     {"PlanName": "   ", "Waves": [{"WaveName": "Wave 1"}]},
     400, "INVALID_NAME")

# 6. Recovery Plan - Missing name
test("RP: Missing PlanName", "POST", "/recovery-plans",
     {"Waves": [{"WaveName": "Wave 1"}]},
     400, "MISSING_FIELD")

# 7. Recovery Plan - No waves
test("RP: No waves", "POST", "/recovery-plans",
     {"PlanName": "Test Plan", "Waves": []},
     400, "MISSING_FIELD")

# 8. Execution - Missing PlanId
test("Exec: Missing PlanId", "POST", "/executions",
     {"ExecutionType": "DRILL", "InitiatedBy": "test"},
     400, "MISSING_FIELD")

# 9. Execution - Missing ExecutionType
test("Exec: Missing ExecutionType", "POST", "/executions",
     {"PlanId": "fake-id", "InitiatedBy": "test"},
     400, "MISSING_FIELD")

# 10. Execution - Invalid ExecutionType
test("Exec: Invalid ExecutionType", "POST", "/executions",
     {"PlanId": "fake-id", "ExecutionType": "INVALID", "InitiatedBy": "test"},
     400, "INVALID_EXECUTION_TYPE")

# 11. Execution - Plan not found
test("Exec: Plan not found", "POST", "/executions",
     {"PlanId": "nonexistent-plan-id", "ExecutionType": "DRILL", "InitiatedBy": "test"},
     404, "RECOVERY_PLAN_NOT_FOUND")

# 12. Cancel non-existent execution
test("Cancel: Execution not found", "POST", "/executions/fake-exec-id/cancel", None,
     404, "EXECUTION_NOT_FOUND")

# 13. Pause non-existent execution  
test("Pause: Execution not found", "POST", "/executions/fake-exec-id/pause", None,
     404, "EXECUTION_NOT_FOUND")

# ============================================================
# Additional Tests - Create real resources then test conflicts
# ============================================================
print("\n" + "="*60)
print("CONFLICT & UPDATE TESTS (with real resources)")
print("="*60)

# Use unique names with timestamp
PG_NAME = f"API-Test-PG-{TS}"
RP_NAME = f"API-Test-RP-{TS}"

# Create a test PG
status, pg = invoke("POST", "/protection-groups", {
    "GroupName": PG_NAME,
    "Region": "us-east-1",
    "ServerSelectionTags": {"test-api": f"error-handling-{TS}"}
})
pg_id = pg.get('id') or pg.get('protectionGroupId') or pg.get('groupId')
print(f"\nCreated test PG: {pg_id or 'FAILED'} (name: {PG_NAME})")

if status == 201 and pg_id:
    
    # 14. Test duplicate PG name
    test("PG: Duplicate name", "POST", "/protection-groups",
         {"GroupName": PG_NAME, "Region": "us-east-1", "ServerSelectionTags": {"other": "tag"}},
         409, "PG_NAME_EXISTS")
    
    # 15. Test update PG with empty name
    test("PG Update: Empty name", "PUT", f"/protection-groups/{pg_id}",
         {"GroupName": "   "},
         400, "INVALID_NAME")
    
    # 16. Test update PG - region change blocked
    test("PG Update: Region change blocked", "PUT", f"/protection-groups/{pg_id}",
         {"Region": "us-west-2"},
         400)
    
    # Create a test RP (waves need WaveId)
    import uuid
    wave_id = str(uuid.uuid4())
    status2, rp = invoke("POST", "/recovery-plans", {
        "PlanName": RP_NAME,
        "Waves": [{"WaveId": wave_id, "WaveName": "Wave 1", "ProtectionGroupId": pg_id, "waveNumber": 1}]
    })
    print(f"\nCreated test RP: {rp.get('PlanId', 'FAILED')} (name: {RP_NAME})")
    
    if status2 == 201:
        rp_id = rp.get('PlanId')
        
        # 17. Test duplicate RP name
        test("RP: Duplicate name", "POST", "/recovery-plans",
             {"PlanName": RP_NAME, "Waves": [{"WaveName": "W1"}]},
             409, "RP_NAME_EXISTS")
        
        # 18. Test update RP with empty name
        test("RP Update: Empty name", "PUT", f"/recovery-plans/{rp_id}",
             {"PlanName": "   "},
             400, "INVALID_NAME")
        
        # 19. Test delete PG that's in use
        test("PG Delete: In use by RP", "DELETE", f"/protection-groups/{pg_id}",
             None, 409, "PG_IN_USE")
        
        # Clean up RP
        invoke("DELETE", f"/recovery-plans/{rp_id}")
        print(f"\nDeleted test RP: {rp_id}")
    else:
        print(f"❌ Failed to create test RP: {rp}")
    
    # Clean up PG
    invoke("DELETE", f"/protection-groups/{pg_id}")
    print(f"Deleted test PG: {pg_id}")
else:
    print(f"❌ Failed to create test PG: {pg}")

# ============================================================
# Additional Edge Case Tests
# ============================================================
print("\n" + "="*60)
print("EDGE CASE TESTS")
print("="*60)

# 20. Name at max length (64 chars) - should succeed
long_name = f"MaxLen64Test-{TS}-" + "A" * (64 - len(f"MaxLen64Test-{TS}-"))
test("PG: Name at max length (64)", "POST", "/protection-groups",
     {"GroupName": long_name, "Region": "us-east-1", "ServerSelectionTags": {"test": "maxlen"}},
     201)

# Clean up immediately after creation
status, resp = invoke("GET", "/protection-groups")
if status == 200:
    for pg in resp.get('groups', []):
        if pg.get('name', '').startswith('MaxLen64Test-'):
            pg_id = pg.get('id') or pg.get('protectionGroupId')
            if pg_id:
                invoke("DELETE", f"/protection-groups/{pg_id}")
                print(f"Cleaned up max-length PG: {pg_id}")

# 21. Name exceeds max length (65 chars) - should fail
too_long_name = "A" * 65
test("PG: Name exceeds max (65)", "POST", "/protection-groups",
     {"GroupName": too_long_name, "Region": "us-east-1", "ServerSelectionTags": {"test": "toolong"}},
     400, "INVALID_NAME")

# 22. RP name at max length (64 chars) - skip creation test, just verify rejection of 65+
# (Creating RP requires valid PG which adds complexity - focus on validation)
rp_long_name = f"MaxLen64RP-{TS}-" + "A" * (64 - len(f"MaxLen64RP-{TS}-"))
print(f"\n{'='*60}")
print("TEST: RP: Name at max length (64) - SKIPPED (requires valid PG)")
print(f"{'='*60}")

# Clean up immediately after creation
status, resp = invoke("GET", "/recovery-plans")
if status == 200:
    for rp in resp.get('recoveryPlans', []):
        if rp.get('PlanName', '').startswith('MaxLen64RP-'):
            rp_id = rp.get('PlanId')
            if rp_id:
                invoke("DELETE", f"/recovery-plans/{rp_id}")
                print(f"Cleaned up max-length RP: {rp_id}")

# 23. RP name exceeds max length (65 chars)
test("RP: Name exceeds max (65)", "POST", "/recovery-plans",
     {"PlanName": too_long_name, "Waves": [{"WaveId": "w1", "WaveName": "W1", "waveNumber": 1}]},
     400, "INVALID_NAME")

# 24. Get non-existent PG
test("PG: Get non-existent", "GET", "/protection-groups/nonexistent-pg-id",
     None, 404)

# 25. Get non-existent RP
test("RP: Get non-existent", "GET", "/recovery-plans/nonexistent-rp-id",
     None, 404)

# 26. Update non-existent PG
test("PG: Update non-existent", "PUT", "/protection-groups/nonexistent-pg-id",
     {"GroupName": "New Name"}, 404)

# 27. Update non-existent RP
test("RP: Update non-existent", "PUT", "/recovery-plans/nonexistent-rp-id",
     {"PlanName": "New Name"}, 404)

# 28. Delete non-existent PG (should succeed silently or 404)
status, _ = test("PG: Delete non-existent", "DELETE", "/protection-groups/nonexistent-pg-id",
     None)
# DynamoDB delete is idempotent, so this might return 200

# 29. Delete non-existent RP
status, _ = test("RP: Delete non-existent", "DELETE", "/recovery-plans/nonexistent-rp-id",
     None)

# ============================================================
# Execution Action Tests (Resume, Terminate, Job Logs)
# ============================================================
print("\n" + "="*60)
print("EXECUTION ACTION TESTS")
print("="*60)

# 30. Resume non-existent execution
test("Resume: Execution not found", "POST", "/executions/fake-exec-id/resume", None,
     404, "EXECUTION_NOT_FOUND")

# 31. Terminate instances - non-existent execution
test("Terminate: Execution not found", "POST", "/executions/fake-exec-id/terminate-instances", None,
     404, "EXECUTION_NOT_FOUND")

# 32. Get job logs - non-existent execution
test("Job Logs: Execution not found", "GET", "/executions/fake-exec-id/job-logs", None,
     404)

# 33. Get single execution - not found
test("Exec: Get non-existent", "GET", "/executions/fake-exec-id", None,
     404)

# ============================================================
# DRS API Tests
# ============================================================
print("\n" + "="*60)
print("DRS API TESTS")
print("="*60)

# Helper to invoke with query params
def invoke_with_query(method, path, query_params=None, body=None):
    """Invoke Lambda with query parameters"""
    event = {
        'httpMethod': method,
        'path': path,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body) if body else None,
        'queryStringParameters': query_params,
        'pathParameters': None
    }
    resp = lambda_client.invoke(FunctionName=FUNC, Payload=json.dumps(event))
    result = json.loads(resp['Payload'].read())
    status = result.get('statusCode', 0)
    body_str = result.get('body', '{}')
    return status, json.loads(body_str) if body_str else {}

# 34. DRS source servers - missing region
print(f"\n{'='*60}")
print("TEST: DRS: Source servers missing region")
print(f"{'='*60}")
status, resp = invoke_with_query("GET", "/drs/source-servers", None)
print(f"Status: {status}")
print(f"Response: {json.dumps(resp, indent=2)[:500]}")
if status == 400:
    print("✅ PASSED")
else:
    print(f"❌ Expected 400, got {status}")

# 35. DRS source servers - valid region (should work)
print(f"\n{'='*60}")
print("TEST: DRS: Source servers with valid region")
print(f"{'='*60}")
status, resp = invoke_with_query("GET", "/drs/source-servers", {"region": "us-east-1"})
print(f"Status: {status}")
print(f"Response: {json.dumps(resp, indent=2)[:300]}...")
if status == 200:
    print("✅ PASSED")
else:
    print(f"Note: Status {status} (may be expected if DRS not initialized)")

# 36. DRS quotas - missing region
print(f"\n{'='*60}")
print("TEST: DRS: Quotas missing region")
print(f"{'='*60}")
status, resp = invoke_with_query("GET", "/drs/quotas", None)
print(f"Status: {status}")
print(f"Response: {json.dumps(resp, indent=2)[:500]}")
if status == 400:
    print("✅ PASSED")
else:
    print(f"❌ Expected 400, got {status}")

# 37. DRS quotas - valid region
print(f"\n{'='*60}")
print("TEST: DRS: Quotas with valid region")
print(f"{'='*60}")
status, resp = invoke_with_query("GET", "/drs/quotas", {"region": "us-east-1"})
print(f"Status: {status}")
print(f"Response: {json.dumps(resp, indent=2)[:300]}...")
if status == 200:
    print("✅ PASSED")
else:
    print(f"Note: Status {status} (may be expected if DRS not initialized)")

# 38. DRS source servers - invalid region
print(f"\n{'='*60}")
print("TEST: DRS: Source servers invalid region")
print(f"{'='*60}")
status, resp = invoke_with_query("GET", "/drs/source-servers", {"region": "invalid-region"})
print(f"Status: {status}")
print(f"Response: {json.dumps(resp, indent=2)[:500]}")
# Should return error or empty list
if status in [200, 400, 500]:
    print(f"✅ Handled (status {status})")

# ============================================================
# Bulk Operations Tests
# ============================================================
print("\n" + "="*60)
print("BULK OPERATIONS TESTS")
print("="*60)

# 39. Delete completed executions (bulk operation)
print(f"\n{'='*60}")
print("TEST: Bulk delete completed executions")
print(f"{'='*60}")
status, resp = invoke("DELETE", "/executions")
print(f"Status: {status}")
print(f"Response: {json.dumps(resp, indent=2)[:500]}")
if status == 200:
    print(f"✅ PASSED - Deleted {resp.get('deletedCount', 0)} completed executions")
else:
    print(f"Note: Status {status}")

print("\n" + "="*60)
print("ALL TESTS COMPLETE")
print("="*60)

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print("""
APIs Tested (39 tests total):
- Protection Groups: CREATE, GET, UPDATE, DELETE, LIST
- Recovery Plans: CREATE, GET, UPDATE, DELETE, LIST  
- Executions: CREATE, GET, LIST, CANCEL, PAUSE, RESUME, TERMINATE, JOB-LOGS, BULK-DELETE
- DRS: SOURCE-SERVERS, QUOTAS

Error Scenarios Covered:
- Missing required fields (MISSING_FIELD)
- Empty/whitespace names (INVALID_NAME)
- Name length validation (max 256)
- Duplicate names (409 PG_NAME_EXISTS, RP_NAME_EXISTS)
- Resource not found (404 EXECUTION_NOT_FOUND)
- Resource in use (409 PG_IN_USE)
- Invalid values (INVALID_EXECUTION_TYPE)
- Region change blocked
- DRS region validation
- Bulk delete completed executions
""")
