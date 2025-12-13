#!/usr/bin/env python3
"""
Comprehensive API Test Suite for DRS Orchestration
Tests all API operations from top to bottom including:
- Protection Groups (CRUD + validation)
- Recovery Plans (CRUD + validation)
- Executions (CRUD + actions)
- DRS Integration (source servers, quotas)
- Optimistic Locking (version conflicts)
- Error handling
"""
import boto3
import json
import re
import time
import sys
from datetime import datetime

# Configuration
PROFILE = '438465159935_AdministratorAccess'
REGION = 'us-east-1'
FUNC = 'drs-orchestration-api-handler-dev'

# Test tracking
TESTS_RUN = 0
TESTS_PASSED = 0
TESTS_FAILED = 0
FAILED_TESTS = []

# Initialize AWS clients
session = boto3.Session(profile_name=PROFILE, region_name=REGION)
lambda_client = session.client('lambda')

# Unique timestamp for test resources
TS = str(int(time.time()))

def invoke(method, path, body=None, query_params=None):
    """Invoke Lambda with API Gateway event format"""
    path_params = {}
    
    # Auto-extract path parameters
    exec_match = re.match(r'/executions/([^/]+)(/.*)?', path)
    if exec_match:
        path_params['executionId'] = exec_match.group(1)
    pg_match = re.match(r'/protection-groups/([^/]+)$', path)
    if pg_match:
        path_params['id'] = pg_match.group(1)
    rp_match = re.match(r'/recovery-plans/([^/]+)$', path)
    if rp_match:
        path_params['id'] = rp_match.group(1)
    
    event = {
        'httpMethod': method,
        'path': path,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body) if body else None,
        'queryStringParameters': query_params,
        'pathParameters': path_params if path_params else None
    }
    
    resp = lambda_client.invoke(FunctionName=FUNC, Payload=json.dumps(event))
    result = json.loads(resp['Payload'].read())
    status = result.get('statusCode', 0)
    body_str = result.get('body', '{}')
    return status, json.loads(body_str) if body_str else {}

def test(name, method, path, body=None, query_params=None, 
         expected_status=None, expected_error=None, check_fn=None):
    """Run a test and track results"""
    global TESTS_RUN, TESTS_PASSED, TESTS_FAILED, FAILED_TESTS
    TESTS_RUN += 1
    
    print(f"\n[{TESTS_RUN}] {name}")
    print(f"    {method} {path}")
    
    status, resp = invoke(method, path, body, query_params)
    
    passed = True
    fail_reason = None
    
    if expected_status and status != expected_status:
        passed = False
        fail_reason = f"Expected status {expected_status}, got {status}"
    
    if expected_error and resp.get('error') != expected_error:
        passed = False
        fail_reason = f"Expected error '{expected_error}', got '{resp.get('error')}'"
    
    if check_fn and not check_fn(status, resp):
        passed = False
        fail_reason = "Custom check failed"
    
    if passed:
        TESTS_PASSED += 1
        print(f"    ✅ PASSED (status={status})")
    else:
        TESTS_FAILED += 1
        FAILED_TESTS.append(name)
        print(f"    ❌ FAILED: {fail_reason}")
        print(f"    Response: {json.dumps(resp, indent=2)[:300]}")
    
    return status, resp

def section(title):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")

# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║         DRS ORCHESTRATION - COMPREHENSIVE API TEST SUITE             ║
║                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                           ║
╚══════════════════════════════════════════════════════════════════════╝
""")

# Store created resources for cleanup
created_pgs = []
created_rps = []
created_execs = []

try:
    # ========================================================================
    section("1. HEALTH CHECK")
    # ========================================================================
    test("Health check endpoint", "GET", "/health", expected_status=200)

    # ========================================================================
    section("2. PROTECTION GROUPS - VALIDATION")
    # ========================================================================
    
    test("PG: Missing GroupName", "POST", "/protection-groups",
         {"Region": "us-east-1", "ServerSelectionTags": {"test": "val"}},
         expected_status=400, expected_error="MISSING_FIELD")
    
    test("PG: Empty GroupName", "POST", "/protection-groups",
         {"GroupName": "   ", "Region": "us-east-1", "ServerSelectionTags": {"test": "val"}},
         expected_status=400, expected_error="INVALID_NAME")
    
    test("PG: Missing Region", "POST", "/protection-groups",
         {"GroupName": "Test", "ServerSelectionTags": {"test": "val"}},
         expected_status=400, expected_error="MISSING_FIELD")
    
    test("PG: No selection method (no tags or servers)", "POST", "/protection-groups",
         {"GroupName": "Test", "Region": "us-east-1"},
         expected_status=400)
    
    test("PG: Name too long (65 chars)", "POST", "/protection-groups",
         {"GroupName": "A" * 65, "Region": "us-east-1", "ServerSelectionTags": {"t": "v"}},
         expected_status=400, expected_error="INVALID_NAME")
    
    test("PG: Get non-existent", "GET", "/protection-groups/nonexistent-id",
         expected_status=404)
    
    test("PG: Update non-existent", "PUT", "/protection-groups/nonexistent-id",
         {"GroupName": "New"}, expected_status=404)

    # ========================================================================
    section("3. PROTECTION GROUPS - CRUD OPERATIONS")
    # ========================================================================
    
    # Create PG
    pg_name = f"TestPG-{TS}"
    status, pg = test("PG: Create with tags", "POST", "/protection-groups",
         {"GroupName": pg_name, "Region": "us-east-1", 
          "ServerSelectionTags": {"test-suite": f"run-{TS}"}},
         expected_status=201)
    
    pg_id = pg.get('id') or pg.get('protectionGroupId')
    if pg_id:
        created_pgs.append(pg_id)
        print(f"    Created PG: {pg_id}")
        
        # List PGs
        test("PG: List all", "GET", "/protection-groups",
             expected_status=200,
             check_fn=lambda s, r: len(r.get('groups', [])) > 0)
        
        # Get single PG
        test("PG: Get by ID", "GET", f"/protection-groups/{pg_id}",
             expected_status=200,
             check_fn=lambda s, r: r.get('name') == pg_name)
        
        # Check version field exists
        test("PG: Has version field", "GET", f"/protection-groups/{pg_id}",
             expected_status=200,
             check_fn=lambda s, r: 'version' in r)
        
        # Update PG
        test("PG: Update name", "PUT", f"/protection-groups/{pg_id}",
             {"GroupName": f"{pg_name}-Updated"},
             expected_status=200,
             check_fn=lambda s, r: r.get('name') == f"{pg_name}-Updated")
        
        # Duplicate name test
        test("PG: Duplicate name rejected", "POST", "/protection-groups",
             {"GroupName": f"{pg_name}-Updated", "Region": "us-east-1",
              "ServerSelectionTags": {"other": "tag"}},
             expected_status=409, expected_error="PG_NAME_EXISTS")
        
        # Region change blocked
        test("PG: Region change blocked", "PUT", f"/protection-groups/{pg_id}",
             {"Region": "us-west-2"},
             expected_status=400)

    # ========================================================================
    section("4. OPTIMISTIC LOCKING - PROTECTION GROUPS")
    # ========================================================================
    
    if pg_id:
        # Get current version
        _, pg_data = invoke("GET", f"/protection-groups/{pg_id}")
        current_version = pg_data.get('version', 1)
        print(f"    Current PG version: {current_version}")
        
        # Update with correct version (should succeed)
        test("PG: Update with correct version", "PUT", f"/protection-groups/{pg_id}",
             {"GroupName": f"{pg_name}-V{current_version+1}", "version": current_version},
             expected_status=200)
        
        # Update with stale version (should fail)
        test("PG: Update with stale version", "PUT", f"/protection-groups/{pg_id}",
             {"GroupName": f"{pg_name}-Stale", "version": current_version},
             expected_status=409, expected_error="VERSION_CONFLICT")

    # ========================================================================
    section("5. RECOVERY PLANS - VALIDATION")
    # ========================================================================
    
    test("RP: Missing PlanName", "POST", "/recovery-plans",
         {"Waves": [{"WaveName": "W1"}]},
         expected_status=400, expected_error="MISSING_FIELD")
    
    test("RP: Empty PlanName", "POST", "/recovery-plans",
         {"PlanName": "   ", "Waves": [{"WaveName": "W1"}]},
         expected_status=400, expected_error="INVALID_NAME")
    
    test("RP: No waves", "POST", "/recovery-plans",
         {"PlanName": "Test", "Waves": []},
         expected_status=400, expected_error="MISSING_FIELD")
    
    test("RP: Name too long (65 chars)", "POST", "/recovery-plans",
         {"PlanName": "A" * 65, "Waves": [{"WaveName": "W1"}]},
         expected_status=400, expected_error="INVALID_NAME")
    
    test("RP: Get non-existent", "GET", "/recovery-plans/nonexistent-id",
         expected_status=404)
    
    test("RP: Update non-existent", "PUT", "/recovery-plans/nonexistent-id",
         {"PlanName": "New"}, expected_status=404)

    # ========================================================================
    section("6. RECOVERY PLANS - CRUD OPERATIONS")
    # ========================================================================
    
    if pg_id:
        rp_name = f"TestRP-{TS}"
        status, rp = test("RP: Create with wave", "POST", "/recovery-plans",
             {"PlanName": rp_name, 
              "Waves": [{"WaveId": "wave-0", "WaveName": "Wave 1", 
                        "ProtectionGroupId": pg_id, "ServerIds": ["s-test123"]}]},
             expected_status=201)
        
        rp_id = rp.get('PlanId')
        if rp_id:
            created_rps.append(rp_id)
            print(f"    Created RP: {rp_id}")
            
            # List RPs
            test("RP: List all", "GET", "/recovery-plans",
                 expected_status=200,
                 check_fn=lambda s, r: len(r.get('plans', [])) > 0)
            
            # Get single RP
            test("RP: Get by ID", "GET", f"/recovery-plans/{rp_id}",
                 expected_status=200,
                 check_fn=lambda s, r: r.get('name') == rp_name)
            
            # Check version field
            test("RP: Has version field", "GET", f"/recovery-plans/{rp_id}",
                 expected_status=200,
                 check_fn=lambda s, r: 'version' in r)
            
            # Update RP
            test("RP: Update name", "PUT", f"/recovery-plans/{rp_id}",
                 {"PlanName": f"{rp_name}-Updated"},
                 expected_status=200)
            
            # Duplicate name
            test("RP: Duplicate name rejected", "POST", "/recovery-plans",
                 {"PlanName": f"{rp_name}-Updated",
                  "Waves": [{"WaveName": "W1", "ProtectionGroupId": pg_id}]},
                 expected_status=409, expected_error="RP_NAME_EXISTS")
            
            # PG in use - cannot delete
            test("PG: Delete blocked (in use by RP)", "DELETE", f"/protection-groups/{pg_id}",
                 expected_status=409, expected_error="PG_IN_USE")

    # ========================================================================
    section("7. OPTIMISTIC LOCKING - RECOVERY PLANS")
    # ========================================================================
    
    if rp_id:
        # Get current version
        _, rp_data = invoke("GET", f"/recovery-plans/{rp_id}")
        rp_version = rp_data.get('version', 1)
        print(f"    Current RP version: {rp_version}")
        
        # Update with correct version
        test("RP: Update with correct version", "PUT", f"/recovery-plans/{rp_id}",
             {"PlanName": f"{rp_name}-V{rp_version+1}", "version": rp_version},
             expected_status=200)
        
        # Update with stale version
        test("RP: Update with stale version", "PUT", f"/recovery-plans/{rp_id}",
             {"PlanName": f"{rp_name}-Stale", "version": rp_version},
             expected_status=409, expected_error="VERSION_CONFLICT")

    # ========================================================================
    section("8. EXECUTIONS - VALIDATION")
    # ========================================================================
    
    test("Exec: Missing PlanId", "POST", "/executions",
         {"ExecutionType": "DRILL", "InitiatedBy": "test"},
         expected_status=400, expected_error="MISSING_FIELD")
    
    test("Exec: Missing ExecutionType", "POST", "/executions",
         {"PlanId": "fake-id", "InitiatedBy": "test"},
         expected_status=400, expected_error="MISSING_FIELD")
    
    test("Exec: Invalid ExecutionType", "POST", "/executions",
         {"PlanId": "fake-id", "ExecutionType": "INVALID", "InitiatedBy": "test"},
         expected_status=400, expected_error="INVALID_EXECUTION_TYPE")
    
    test("Exec: Plan not found", "POST", "/executions",
         {"PlanId": "nonexistent-plan", "ExecutionType": "DRILL", "InitiatedBy": "test"},
         expected_status=404, expected_error="RECOVERY_PLAN_NOT_FOUND")
    
    test("Exec: Get non-existent", "GET", "/executions/fake-exec-id",
         expected_status=404)

    # ========================================================================
    section("9. EXECUTION ACTIONS - VALIDATION")
    # ========================================================================
    
    test("Exec: Cancel non-existent", "POST", "/executions/fake-id/cancel",
         expected_status=404, expected_error="EXECUTION_NOT_FOUND")
    
    test("Exec: Pause non-existent", "POST", "/executions/fake-id/pause",
         expected_status=404, expected_error="EXECUTION_NOT_FOUND")
    
    test("Exec: Resume non-existent", "POST", "/executions/fake-id/resume",
         expected_status=404, expected_error="EXECUTION_NOT_FOUND")
    
    test("Exec: Terminate instances non-existent", "POST", "/executions/fake-id/terminate-instances",
         expected_status=404, expected_error="EXECUTION_NOT_FOUND")
    
    test("Exec: Job logs non-existent", "GET", "/executions/fake-id/job-logs",
         expected_status=404)

    # ========================================================================
    section("10. EXECUTIONS - LIST & BULK DELETE")
    # ========================================================================
    
    test("Exec: List all", "GET", "/executions",
         expected_status=200,
         check_fn=lambda s, r: 'items' in r or isinstance(r, list))
    
    test("Exec: Bulk delete completed", "DELETE", "/executions",
         expected_status=200,
         check_fn=lambda s, r: 'deletedCount' in r or 'message' in r)

    # ========================================================================
    section("11. DRS INTEGRATION")
    # ========================================================================
    
    test("DRS: Source servers - missing region", "GET", "/drs/source-servers",
         expected_status=400)
    
    test("DRS: Source servers - valid region", "GET", "/drs/source-servers",
         query_params={"region": "us-east-1"},
         expected_status=200)
    
    test("DRS: Quotas - missing region", "GET", "/drs/quotas",
         expected_status=400)
    
    test("DRS: Quotas - valid region", "GET", "/drs/quotas",
         query_params={"region": "us-east-1"},
         expected_status=200)

    # ========================================================================
    section("12. PROTECTION GROUP TAG RESOLUTION")
    # ========================================================================
    
    test("PG Resolve: Missing region", "POST", "/protection-groups/resolve",
         {"tags": {"test": "value"}},
         expected_status=400)
    
    test("PG Resolve: Missing tags", "POST", "/protection-groups/resolve",
         {"region": "us-east-1"},
         expected_status=400)
    
    test("PG Resolve: Valid request", "POST", "/protection-groups/resolve",
         {"region": "us-east-1", "tags": {"test": "value"}},
         expected_status=200)

finally:
    # ========================================================================
    section("CLEANUP")
    # ========================================================================
    
    print("\nCleaning up test resources...")
    
    # Delete RPs first (they reference PGs)
    for rp_id in created_rps:
        status, _ = invoke("DELETE", f"/recovery-plans/{rp_id}")
        print(f"    Deleted RP {rp_id}: {status}")
    
    # Then delete PGs
    for pg_id in created_pgs:
        status, _ = invoke("DELETE", f"/protection-groups/{pg_id}")
        print(f"    Deleted PG {pg_id}: {status}")

# ============================================================================
# SUMMARY
# ============================================================================

print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                         TEST SUMMARY                                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  Total Tests:  {TESTS_RUN:4d}                                                 ║
║  Passed:       {TESTS_PASSED:4d}  ✅                                              ║
║  Failed:       {TESTS_FAILED:4d}  {'❌' if TESTS_FAILED > 0 else '  '}                                              ║
╚══════════════════════════════════════════════════════════════════════╝
""")

if FAILED_TESTS:
    print("Failed Tests:")
    for t in FAILED_TESTS:
        print(f"  ❌ {t}")
    print()

# Exit with error code if tests failed
sys.exit(0 if TESTS_FAILED == 0 else 1)
