# Inventory Sync Refactoring - Implementation Tasks

## Overview
This task list implements the refactoring of `handle_sync_source_server_inventory` into smaller, focused functions. This spec must be implemented AFTER active-region-filtering is complete.

---

## Phase 1: Shared Utilities Foundation

- [ ] 1. Create lambda/shared/dynamodb_tables.py module
  - [ ] 1.1 Create `lambda/shared/dynamodb_tables.py` module
  - [ ] 1.2 Implement `get_protection_groups_table()` function
  - [ ] 1.3 Implement `get_recovery_plans_table()` function
  - [ ] 1.4 Implement `get_source_servers_table()` function
  - [ ] 1.5 Implement `get_region_status_table()` function
  - [ ] 1.6 Add comprehensive docstrings with type hints
  - [ ] 1.7 Write unit tests for all table getter functions (target: 100% coverage)

**Acceptance Criteria:**
- All DynamoDB table getters consolidated in single module
- Functions use environment variables for table names
- Type hints on all function signatures
- Docstrings follow PEP 257 format
- Unit tests achieve 100% coverage

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/shared/dynamodb_tables.py --max-line-length=120
.venv/bin/black --check --line-length=120 lambda/shared/dynamodb_tables.py
.venv/bin/bandit -r lambda/shared/dynamodb_tables.py
.venv/bin/pytest tests/unit/test_dynamodb_tables.py -v --cov=lambda.shared.dynamodb_tables
```

**Files to Create:**
- `lambda/shared/dynamodb_tables.py`
- `tests/unit/test_dynamodb_tables.py`

---

- [ ] 2. Update handlers to use shared dynamodb_tables module
  - [ ] 2.1 Update query-handler to import from `dynamodb_tables.py`
  - [ ] 2.2 Update data-management-handler to import from `dynamodb_tables.py`
  - [ ] 2.3 Remove duplicate table getter functions from both handlers
  - [ ] 2.4 Update all function calls to use new module
  - [ ] 2.5 Run all existing tests to verify no behavioral changes

**Acceptance Criteria:**
- No duplicate table getter functions in handlers
- All handlers use shared `dynamodb_tables.py` module
- All existing tests pass
- No behavioral changes detected

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/query-handler/index.py --max-line-length=120
.venv/bin/flake8 lambda/data-management-handler/index.py --max-line-length=120
.venv/bin/black --check --line-length=120 lambda/query-handler/index.py
.venv/bin/black --check --line-length=120 lambda/data-management-handler/index.py
.venv/bin/pytest tests/unit/ -v
```

**Files to Modify:**
- `lambda/query-handler/index.py`
- `lambda/data-management-handler/index.py`

---

## Phase 2: Extract Functions One-by-One

- [ ] 3. Extract collect_accounts_to_query() function
  - [ ] 3.1 Create `collect_accounts_to_query()` function in query-handler
  - [ ] 3.2 Move account collection logic from main function
  - [ ] 3.3 Add type hints and comprehensive docstring
  - [ ] 3.4 Use `dynamodb_tables.get_target_accounts_table()`
  - [ ] 3.5 Write unit tests (target: 95% coverage)
  - [ ] 3.6 Write property-based tests for account filtering
  - [ ] 3.7 Update main function to call extracted function
  - [ ] 3.8 Run comparison test to verify identical output

**Acceptance Criteria:**
- Function signature: `collect_accounts_to_query() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]`
- Returns tuple of (target_accounts, staging_accounts)
- Handles empty tables gracefully
- Proper error handling for DynamoDB errors
- Unit tests achieve 95%+ coverage
- Comparison test shows identical output

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/query-handler/index.py --max-line-length=120
.venv/bin/black --check --line-length=120 lambda/query-handler/index.py
.venv/bin/bandit -r lambda/query-handler/index.py
.venv/bin/pytest tests/unit/test_collect_accounts.py -v --cov=lambda.query-handler.index
.venv/bin/pytest tests/comparison/test_inventory_sync_comparison.py::test_collect_accounts -v
```

**Files to Modify:**
- `lambda/query-handler/index.py`

**Files to Create:**
- `tests/unit/test_collect_accounts.py`
- `tests/comparison/test_inventory_sync_comparison.py` (if not exists)

---

- [ ] 4. Extract get_account_credentials() function
  - [ ] 4.1 Create `get_account_credentials()` function in query-handler
  - [ ] 4.2 Move credential management logic from main function
  - [ ] 4.3 Add type hints and comprehensive docstring
  - [ ] 4.4 Use `cross_account.get_cross_account_session()`
  - [ ] 4.5 Write unit tests with mocked STS calls (target: 95% coverage)
  - [ ] 4.6 Write property-based tests for credential caching
  - [ ] 4.7 Update main function to call extracted function
  - [ ] 4.8 Run comparison test to verify identical behavior

**Acceptance Criteria:**
- Function signature: `get_account_credentials(account_id: str, role_name: str) -> Optional[Dict[str, str]]`
- Returns credentials dict or None on failure
- Handles AssumeRole failures gracefully
- Logs credential acquisition attempts
- Unit tests achieve 95%+ coverage
- Comparison test shows identical behavior

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/query-handler/index.py --max-line-length=120
.venv/bin/black --check --line-length=120 lambda/query-handler/index.py
.venv/bin/bandit -r lambda/query-handler/index.py
.venv/bin/pytest tests/unit/test_get_account_credentials.py -v --cov=lambda.query-handler.index
.venv/bin/pytest tests/comparison/test_inventory_sync_comparison.py::test_credentials -v
```

**Files to Modify:**
- `lambda/query-handler/index.py`

**Files to Create:**
- `tests/unit/test_get_account_credentials.py`

---

- [ ] 5. Extract query_drs_single_region() function
  - [ ] 5.1 Create `query_drs_single_region()` function in query-handler
  - [ ] 5.2 Move single-region DRS query logic from main function
  - [ ] 5.3 Add type hints and comprehensive docstring
  - [ ] 5.4 Use `cross_account.create_drs_client()`
  - [ ] 5.5 Implement all 8 error type handlers (AccessDenied, Throttling, etc.)
  - [ ] 5.6 Write unit tests for each error type (target: 95% coverage)
  - [ ] 5.7 Write property-based tests for pagination handling
  - [ ] 5.8 Update main function to call extracted function
  - [ ] 5.9 Run comparison test to verify identical error handling

**Acceptance Criteria:**
- Function signature: `query_drs_single_region(session: boto3.Session, region: str, account_id: str) -> Tuple[List[Dict], Optional[str]]`
- Returns tuple of (servers, error_message)
- Handles all 8 DRS error types correctly
- Logs region query attempts and results
- Unit tests achieve 95%+ coverage
- Comparison test shows identical error handling

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/query-handler/index.py --max-line-length=120
.venv/bin/black --check --line-length=120 lambda/query-handler/index.py
.venv/bin/bandit -r lambda/query-handler/index.py
.venv/bin/pytest tests/unit/test_query_drs_single_region.py -v --cov=lambda.query-handler.index
.venv/bin/pytest tests/comparison/test_inventory_sync_comparison.py::test_single_region -v
```

**Files to Modify:**
- `lambda/query-handler/index.py`

**Files to Create:**
- `tests/unit/test_query_drs_single_region.py`

---

- [ ] 6. Extract query_drs_all_regions() function
  - [ ] 6.1 Create `query_drs_all_regions()` function in query-handler
  - [ ] 6.2 Move parallel multi-region query logic from main function
  - [ ] 6.3 Add type hints and comprehensive docstring
  - [ ] 6.4 Use `active_region_filter.get_active_regions()`
  - [ ] 6.5 Use `active_region_filter.update_region_status()`
  - [ ] 6.6 Implement ThreadPoolExecutor with max_workers=10
  - [ ] 6.7 Write unit tests for parallel execution (target: 90% coverage)
  - [ ] 6.8 Write property-based tests for region filtering
  - [ ] 6.9 Update main function to call extracted function
  - [ ] 6.10 Run comparison test to verify identical results

**Acceptance Criteria:**
- Function signature: `query_drs_all_regions(session: boto3.Session, account_id: str, active_regions: List[str]) -> List[Dict[str, Any]]`
- Returns list of all servers from all regions
- Executes regions in parallel (max 10 concurrent)
- Updates region status for each query
- Handles partial failures gracefully
- Unit tests achieve 90%+ coverage
- Comparison test shows identical results

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/query-handler/index.py --max-line-length=120
.venv/bin/black --check --line-length=120 lambda/query-handler/index.py
.venv/bin/bandit -r lambda/query-handler/index.py
.venv/bin/pytest tests/unit/test_query_drs_all_regions.py -v --cov=lambda.query-handler.index
.venv/bin/pytest tests/comparison/test_inventory_sync_comparison.py::test_all_regions -v
```

**Files to Modify:**
- `lambda/query-handler/index.py`

**Files to Create:**
- `tests/unit/test_query_drs_all_regions.py`

---

- [ ] 7. Extract query_ec2_instances() function
  - [ ] 7.1 Create `query_ec2_instances()` function in query-handler
  - [ ] 7.2 Move EC2 API interaction logic from main function
  - [ ] 7.3 Add type hints and comprehensive docstring
  - [ ] 7.4 Use `cross_account.create_ec2_client()`
  - [ ] 7.5 Implement pagination for describe_instances
  - [ ] 7.6 Write unit tests with mocked EC2 calls (target: 95% coverage)
  - [ ] 7.7 Write property-based tests for instance filtering
  - [ ] 7.8 Update main function to call extracted function
  - [ ] 7.9 Run comparison test to verify identical EC2 data

**Acceptance Criteria:**
- Function signature: `query_ec2_instances(session: boto3.Session, region: str, instance_ids: List[str]) -> Dict[str, Dict[str, Any]]`
- Returns dict mapping instance_id to EC2 metadata
- Handles missing instances gracefully
- Implements pagination correctly
- Unit tests achieve 95%+ coverage
- Comparison test shows identical EC2 data

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/query-handler/index.py --max-line-length=120
.venv/bin/black --check --line-length=120 lambda/query-handler/index.py
.venv/bin/bandit -r lambda/query-handler/index.py
.venv/bin/pytest tests/unit/test_query_ec2_instances.py -v --cov=lambda.query-handler.index
.venv/bin/pytest tests/comparison/test_inventory_sync_comparison.py::test_ec2_query -v
```

**Files to Modify:**
- `lambda/query-handler/index.py`

**Files to Create:**
- `tests/unit/test_query_ec2_instances.py`

---

- [ ] 8. Extract enrich_with_ec2_metadata() function
  - [ ] 8.1 Create `enrich_with_ec2_metadata()` function in query-handler
  - [ ] 8.2 Move EC2 metadata enrichment logic from main function
  - [ ] 8.3 Add type hints and comprehensive docstring
  - [ ] 8.4 Handle cross-account EC2 queries
  - [ ] 8.5 Write unit tests for enrichment logic (target: 95% coverage)
  - [ ] 8.6 Write property-based tests for metadata merging
  - [ ] 8.7 Update main function to call extracted function
  - [ ] 8.8 Run comparison test to verify identical enrichment

**Acceptance Criteria:**
- Function signature: `enrich_with_ec2_metadata(servers: List[Dict], account_credentials: Dict[str, Dict]) -> List[Dict[str, Any]]`
- Returns enriched server list with EC2 metadata
- Handles missing EC2 data gracefully
- Preserves all original DRS fields
- Unit tests achieve 95%+ coverage
- Comparison test shows identical enrichment

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/query-handler/index.py --max-line-length=120
.venv/bin/black --check --line-length=120 lambda/query-handler/index.py
.venv/bin/bandit -r lambda/query-handler/index.py
.venv/bin/pytest tests/unit/test_enrich_ec2_metadata.py -v --cov=lambda.query-handler.index
.venv/bin/pytest tests/comparison/test_inventory_sync_comparison.py::test_enrichment -v
```

**Files to Modify:**
- `lambda/query-handler/index.py`

**Files to Create:**
- `tests/unit/test_enrich_ec2_metadata.py`

---

- [ ] 9. Extract write_inventory_to_dynamodb() function
  - [ ] 9.1 Create `write_inventory_to_dynamodb()` function in query-handler
  - [ ] 9.2 Move DynamoDB batch write logic from main function
  - [ ] 9.3 Add type hints and comprehensive docstring
  - [ ] 9.4 Use `dynamodb_tables.get_source_servers_table()`
  - [ ] 9.5 Implement batch writing with 25-item batches
  - [ ] 9.6 Write unit tests with mocked DynamoDB (target: 95% coverage)
  - [ ] 9.7 Write property-based tests for batch handling
  - [ ] 9.8 Update main function to call extracted function
  - [ ] 9.9 Run comparison test to verify identical writes

**Acceptance Criteria:**
- Function signature: `write_inventory_to_dynamodb(servers: List[Dict[str, Any]]) -> int`
- Returns count of servers written
- Handles batch write failures with retry
- Logs write progress and errors
- Unit tests achieve 95%+ coverage
- Comparison test shows identical DynamoDB writes

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/query-handler/index.py --max-line-length=120
.venv/bin/black --check --line-length=120 lambda/query-handler/index.py
.venv/bin/bandit -r lambda/query-handler/index.py
.venv/bin/pytest tests/unit/test_write_inventory.py -v --cov=lambda.query-handler.index
.venv/bin/pytest tests/comparison/test_inventory_sync_comparison.py::test_dynamodb_write -v
```

**Files to Modify:**
- `lambda/query-handler/index.py`

**Files to Create:**
- `tests/unit/test_write_inventory.py`

---

## Phase 3: Integration and Comparison Testing

- [ ] 10. Create comprehensive comparison test suite
  - [ ] 10.1 Create comparison test framework in `tests/comparison/`
  - [ ] 10.2 Implement side-by-side execution of original and refactored
  - [ ] 10.3 Add 10+ test scenarios covering all edge cases
  - [ ] 10.4 Implement output comparison logic
  - [ ] 10.5 Add performance comparison metrics
  - [ ] 10.6 Document any acceptable differences
  - [ ] 10.7 Run comparison tests against dev environment

**Test Scenarios:**
1. Empty account list
2. Single account, single region
3. Multiple accounts, multiple regions
4. Account with no DRS servers
5. Account with AccessDenied error
6. Account with Throttling error
7. Mixed success and failure regions
8. Large inventory (100+ servers)
9. Cross-account EC2 enrichment
10. Partial EC2 metadata availability

**Acceptance Criteria:**
- All 10 scenarios pass comparison tests
- Output differences documented and justified
- Performance metrics show improvement
- No behavioral regressions detected

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/pytest tests/comparison/ -v --tb=short
```

**Files to Create:**
- `tests/comparison/test_inventory_sync_comparison.py`
- `tests/comparison/conftest.py`
- `tests/comparison/README.md`

---

- [ ] 11. Create integration test suite
  - [ ] 11.1 Create integration test framework in `tests/integration/`
  - [ ] 11.2 Implement tests against real AWS services in dev
  - [ ] 11.3 Add setup/teardown for test data
  - [ ] 11.4 Test full end-to-end flow
  - [ ] 11.5 Test error handling with real AWS errors
  - [ ] 11.6 Test performance under load
  - [ ] 11.7 Document integration test requirements

**Acceptance Criteria:**
- Integration tests pass in dev environment
- Tests clean up after themselves
- Tests handle AWS rate limits gracefully
- Performance meets targets (< 30s for 50 servers)

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/pytest tests/integration/ -v --tb=short
```

**Files to Create:**
- `tests/integration/test_inventory_sync_integration.py`
- `tests/integration/conftest.py`
- `tests/integration/README.md`

---

- [ ] 12. Update orchestrator function
  - [ ] 12.1 Refactor `handle_sync_source_server_inventory()` to orchestrator
  - [ ] 12.2 Reduce to < 50 lines by calling extracted functions
  - [ ] 12.3 Add comprehensive docstring
  - [ ] 12.4 Implement error aggregation and logging
  - [ ] 12.5 Preserve original function signature
  - [ ] 12.6 Run all tests to verify no regressions
  - [ ] 12.7 Run comparison tests to verify behavioral equivalence

**Acceptance Criteria:**
- Orchestrator function < 50 lines
- Calls all 7 extracted functions in correct order
- Preserves original function signature
- All tests pass (unit, comparison, integration)
- No behavioral changes detected

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/query-handler/index.py --max-line-length=120
.venv/bin/black --check --line-length=120 lambda/query-handler/index.py
.venv/bin/pytest tests/ -v --cov=lambda.query-handler.index --cov-report=term
.venv/bin/pytest tests/comparison/ -v
```

**Files to Modify:**
- `lambda/query-handler/index.py`

---

## Phase 4: Feature Flag and Rollback Safety

- [ ] 13. Implement feature flag mechanism
  - [ ] 13.1 Preserve original as `handle_sync_source_server_inventory_legacy()`
  - [ ] 13.2 Add environment variable `USE_REFACTORED_INVENTORY_SYNC`
  - [ ] 13.3 Implement routing logic in handler
  - [ ] 13.4 Add logging for which implementation is used
  - [ ] 13.5 Write tests for feature flag routing
  - [ ] 13.6 Document feature flag usage in README

**Acceptance Criteria:**
- Original function preserved as `_legacy()`
- Feature flag defaults to refactored implementation
- Routing logic < 10 lines
- Tests verify both implementations accessible
- Documentation updated

**Validation Commands:**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/query-handler/index.py --max-line-length=120
.venv/bin/pytest tests/unit/test_feature_flag.py -v
```

**Files to Modify:**
- `lambda/query-handler/index.py`
- `README.md`

**Files to Create:**
- `tests/unit/test_feature_flag.py`

---

- [ ] 14. Test rollback procedure
  - [ ] 14.1 Deploy with refactored implementation enabled
  - [ ] 14.2 Verify functionality in dev environment
  - [ ] 14.3 Switch to legacy implementation via environment variable
  - [ ] 14.4 Verify functionality with legacy implementation
  - [ ] 14.5 Switch back to refactored implementation
  - [ ] 14.6 Document rollback procedure
  - [ ] 14.7 Create rollback runbook

**Acceptance Criteria:**
- Rollback works without redeployment
- Both implementations function correctly
- Rollback procedure documented
- Runbook created for operations team

**Validation Commands:**
```bash
# Test with refactored (default)
aws lambda invoke --function-name hrp-drs-tech-adapter-query-handler-dev \
  --payload '{"action":"sync_source_server_inventory"}' response.json

# Switch to legacy
aws lambda update-function-configuration \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --environment Variables={USE_REFACTORED_INVENTORY_SYNC=false}

# Test with legacy
aws lambda invoke --function-name hrp-drs-tech-adapter-query-handler-dev \
  --payload '{"action":"sync_source_server_inventory"}' response.json

# Switch back to refactored
aws lambda update-function-configuration \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --environment Variables={USE_REFACTORED_INVENTORY_SYNC=true}
```

**Files to Create:**
- `docs/ROLLBACK_PROCEDURE.md`
- `docs/runbooks/inventory-sync-rollback.md`

---

- [ ]* 15. Deploy and monitor (24-hour monitoring - optional)
  - [ ] 15.1 Deploy to dev environment using deploy script
  - [ ] 15.2 Monitor CloudWatch metrics for 24 hours
  - [ ] 15.3 Compare performance metrics (execution time, memory, errors)
  - [ ] 15.4 Verify no increase in error rate
  - [ ] 15.5 Verify performance improvement (target: 50% reduction)
  - [ ] 15.6 Document deployment results
  - [ ] 15.7 Create post-deployment report

**Acceptance Criteria:**
- Deployment successful via `./scripts/deploy.sh dev`
- All validation stages pass
- CloudWatch metrics show improvement
- No increase in error rate
- Execution time reduced by 50%+ (45s → 22s or better)
- Memory usage under 512MB

**Validation Commands:**
```bash
# Deploy
./scripts/deploy.sh dev

# Monitor metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=hrp-drs-tech-adapter-query-handler-dev \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average,Maximum

aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=hrp-drs-tech-adapter-query-handler-dev \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

**Files to Create:**
- `docs/deployment/inventory-sync-refactoring-deployment.md`

---

## Summary

**Total Tasks:** 15 tasks (14 required, 1 optional)
**Estimated Duration:** 3-4 weeks
**Critical Path:** Tasks 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 12 → 13 → 14

**Key Milestones:**
- Phase 1 Complete: Shared utilities foundation ready
- Phase 2 Complete: All functions extracted and tested
- Phase 3 Complete: Integration and comparison testing complete
- Phase 4 Complete: Feature flag implemented and deployed

**Success Criteria:**
- ✅ All 14 required tasks completed
- ✅ All validation stages pass
- ✅ 90%+ code coverage achieved
- ✅ All comparison tests pass
- ✅ Performance improved by 50%+
- ✅ No behavioral regressions
- ✅ Rollback procedure tested and documented
