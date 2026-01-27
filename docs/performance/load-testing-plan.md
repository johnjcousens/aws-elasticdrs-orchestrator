# Load Testing Plan: 1,000 Server / 4 Account Scenario

**Date**: 2026-01-24  
**Environment**: dev  
**Scope**: Validate performance at production scale

## Executive Summary

This plan validates system performance for production deployment supporting:
- **1,000 replicating servers total**
- **4 DRS accounts** (3 staging + 1 target)
- **~250 servers per account** (with room for growth to 300)
- **Cross-account operations** across all 4 accounts

## Test Scenarios

### Scenario 1: DRS Capacity Monitoring (Critical Path)

**Objective**: Validate Query Handler performance for DRS capacity monitoring across 4 accounts

**API Endpoint**: `GET /drs/quotas`

**Test Cases**:

1. **Single Account Capacity Query**
   - Query: `GET /drs/quotas?accountId=ACCOUNT_1&region=us-east-1`
   - Expected: 250 replicating servers, 300 max
   - Target: < 2 seconds response time
   - Validates: Per-account capacity monitoring

2. **All Accounts Capacity Query**
   - Query: `GET /drs/quotas?region=us-east-1` (aggregates all accounts)
   - Expected: 1,000 replicating servers across 4 accounts
   - Target: < 5 seconds response time
   - Validates: Cross-account aggregation performance

3. **Multi-Region Capacity Query**
   - Query: `GET /drs/quotas` (all regions, all accounts)
   - Expected: Aggregate capacity across us-east-1, us-west-2, us-east-2, us-west-1
   - Target: < 10 seconds response time
   - Validates: Full system capacity monitoring

**Performance Metrics**:
- Response time (p50, p95, p99)
- DRS API call count (should be 4 calls for 4 accounts)
- Lambda execution time
- Memory utilization
- Error rate

**Success Criteria**:
- ✅ Single account query < 2s
- ✅ All accounts query < 5s
- ✅ Multi-region query < 10s
- ✅ No throttling errors
- ✅ Accurate capacity reporting

---

### Scenario 2: Source Server Listing at Scale

**Objective**: Validate Query Handler performance listing 1,000 servers

**API Endpoint**: `GET /drs/source-servers`

**Test Cases**:

1. **Single Account Server List**
   - Query: `GET /drs/source-servers?accountId=ACCOUNT_1&region=us-east-1`
   - Expected: 250 servers returned
   - Target: < 3 seconds response time
   - Validates: Per-account server listing

2. **All Accounts Server List**
   - Query: `GET /drs/source-servers?region=us-east-1` (all accounts)
   - Expected: 1,000 servers returned
   - Target: < 8 seconds response time
   - Validates: Cross-account server aggregation

3. **Filtered Server List**
   - Query: `GET /drs/source-servers?region=us-east-1&tags=Purpose:Database`
   - Expected: Subset of servers matching tags
   - Target: < 5 seconds response time
   - Validates: Tag-based filtering performance

**Performance Metrics**:
- Response time per 100 servers
- Pagination efficiency
- Memory usage with large result sets
- JSON serialization time

**Success Criteria**:
- ✅ 250 servers < 3s
- ✅ 1,000 servers < 8s
- ✅ Filtered queries < 5s
- ✅ No memory errors
- ✅ Consistent pagination

---

### Scenario 3: Tag Resolution at Scale

**Objective**: Validate Data Management Handler tag resolution with 250 servers

**API Endpoint**: `POST /protection-groups/resolve`

**Test Cases**:

1. **Small Tag Resolution** (10-50 servers)
   - Body: `{"tags": {"Purpose": "Database"}, "region": "us-east-1", "accountId": "ACCOUNT_1"}`
   - Expected: 10-50 servers resolved
   - Target: < 2 seconds response time
   - Validates: Small protection group creation

2. **Medium Tag Resolution** (100-150 servers)
   - Body: `{"tags": {"Purpose": "Application"}, "region": "us-east-1", "accountId": "ACCOUNT_1"}`
   - Expected: 100-150 servers resolved
   - Target: < 4 seconds response time
   - Validates: Medium protection group creation

3. **Large Tag Resolution** (200-250 servers)
   - Body: `{"tags": {"Environment": "Production"}, "region": "us-east-1", "accountId": "ACCOUNT_1"}`
   - Expected: 200-250 servers resolved
   - Target: < 6 seconds response time
   - Validates: Large protection group creation (near account limit)

4. **Cross-Account Tag Resolution**
   - Body: `{"tags": {"Purpose": "Database"}, "region": "us-east-1"}` (all accounts)
   - Expected: Servers from all 4 accounts
   - Target: < 10 seconds response time
   - Validates: Multi-account protection groups

**Performance Metrics**:
- DRS API calls (describe_source_servers)
- Tag filtering efficiency
- Response time per server
- Memory usage

**Success Criteria**:
- ✅ 50 servers < 2s
- ✅ 150 servers < 4s
- ✅ 250 servers < 6s
- ✅ Cross-account < 10s
- ✅ Accurate tag matching

---

### Scenario 4: Recovery Plan Execution at Scale

**Objective**: Validate Execution Handler with large recovery plans

**API Endpoint**: `POST /recovery-plans/{planId}/execute`

**Test Cases**:

1. **Single Wave Execution** (100 servers)
   - Recovery Plan: 1 wave, 100 servers (DRS limit)
   - Expected: Step Functions execution started
   - Target: < 3 seconds response time
   - Validates: Maximum wave size handling

2. **Multi-Wave Execution** (250 servers)
   - Recovery Plan: 3 waves (100 + 100 + 50 servers)
   - Expected: Sequential wave execution
   - Target: < 5 seconds to start execution
   - Validates: Large recovery plan orchestration

3. **Multi-Account Execution** (1,000 servers)
   - Recovery Plan: 10 waves across 4 accounts
   - Expected: Cross-account orchestration
   - Target: < 10 seconds to start execution
   - Validates: Full-scale DR execution

**Performance Metrics**:
- Step Functions start time
- DynamoDB write latency
- Execution state tracking
- Wave validation time

**Success Criteria**:
- ✅ Single wave < 3s
- ✅ Multi-wave < 5s
- ✅ Multi-account < 10s
- ✅ No DRS limit violations
- ✅ Accurate execution tracking

---

### Scenario 5: Protection Group Management at Scale

**Objective**: Validate Data Management Handler with large protection groups

**API Endpoint**: `POST /protection-groups`, `GET /protection-groups`

**Test Cases**:

1. **Create Large Protection Group** (250 servers)
   - Body: Protection group with 250 server IDs
   - Expected: DynamoDB write success
   - Target: < 3 seconds response time
   - Validates: Maximum protection group size

2. **List All Protection Groups** (100+ groups)
   - Query: `GET /protection-groups`
   - Expected: All protection groups returned
   - Target: < 2 seconds response time
   - Validates: DynamoDB scan performance

3. **Update Large Protection Group** (250 servers)
   - Body: Update protection group with 250 servers
   - Expected: Optimistic locking success
   - Target: < 4 seconds response time
   - Validates: Large update operations

**Performance Metrics**:
- DynamoDB write capacity units
- Item size (should be < 400 KB limit)
- Query/scan performance
- Conflict detection time

**Success Criteria**:
- ✅ Create 250 servers < 3s
- ✅ List 100+ groups < 2s
- ✅ Update 250 servers < 4s
- ✅ No DynamoDB throttling
- ✅ Accurate conflict detection

---

### Scenario 6: Concurrent Operations

**Objective**: Validate system under concurrent load

**Test Cases**:

1. **Concurrent Capacity Queries** (10 simultaneous)
   - 10 users query DRS capacity simultaneously
   - Expected: All queries succeed
   - Target: < 5 seconds for all to complete
   - Validates: Lambda concurrency handling

2. **Concurrent Tag Resolutions** (5 simultaneous)
   - 5 users resolve tags simultaneously (50 servers each)
   - Expected: All resolutions succeed
   - Target: < 10 seconds for all to complete
   - Validates: DRS API rate limiting

3. **Concurrent Executions** (3 simultaneous)
   - 3 recovery plans execute simultaneously
   - Expected: All executions start successfully
   - Target: < 15 seconds for all to start
   - Validates: Step Functions concurrency

**Performance Metrics**:
- Lambda concurrent executions
- DRS API throttling rate
- DynamoDB throttling rate
- Error rate under load

**Success Criteria**:
- ✅ No Lambda throttling
- ✅ No DRS API throttling
- ✅ No DynamoDB throttling
- ✅ All operations succeed
- ✅ Consistent response times

---

## Test Environment Setup

### Prerequisites

1. **DRS Accounts** (4 accounts with test data):
   - Account 1: 250 replicating servers (us-east-1)
   - Account 2: 250 replicating servers (us-east-1)
   - Account 3: 250 replicating servers (us-east-1)
   - Account 4: 250 replicating servers (us-east-1)

2. **Test Data**:
   - Protection Groups: 20+ groups with varying sizes
   - Recovery Plans: 10+ plans with 1-10 waves each
   - Tags: Consistent tagging across all servers

3. **Monitoring**:
   - CloudWatch Logs enabled
   - X-Ray tracing enabled
   - Custom metrics for DRS API calls

### Test Execution Tools

**Option 1: Manual Testing** (Quick validation)
```bash
# Run load test script
./scripts/load-test-handlers.sh

# Measures:
# - DRS capacity queries (4 accounts)
# - Source server listing (1,000 servers)
# - Tag resolution (250 servers)
# - Concurrent operations (10 simultaneous)
```

**Option 2: Apache JMeter** (Comprehensive load testing)
- Thread groups for each scenario
- Ramp-up period: 60 seconds
- Duration: 10 minutes per scenario
- Assertions for response time and accuracy

**Option 3: AWS Distributed Load Testing** (Production-scale)
- CloudFormation-based load testing solution
- Distributed across multiple regions
- Real-time metrics and dashboards

---

## Performance Targets

### Response Time Targets

| Operation | Server Count | Target (p95) | Target (p99) |
|-----------|-------------|--------------|--------------|
| DRS capacity (single account) | 250 | < 2s | < 3s |
| DRS capacity (all accounts) | 1,000 | < 5s | < 8s |
| List servers (single account) | 250 | < 3s | < 5s |
| List servers (all accounts) | 1,000 | < 8s | < 12s |
| Tag resolution (small) | 50 | < 2s | < 3s |
| Tag resolution (medium) | 150 | < 4s | < 6s |
| Tag resolution (large) | 250 | < 6s | < 10s |
| Execute recovery plan (single wave) | 100 | < 3s | < 5s |
| Execute recovery plan (multi-wave) | 250 | < 5s | < 8s |
| Create protection group | 250 | < 3s | < 5s |

### Throughput Targets

| Operation | Target Throughput |
|-----------|------------------|
| Capacity queries | 100 requests/minute |
| Server listings | 50 requests/minute |
| Tag resolutions | 20 requests/minute |
| Recovery executions | 10 requests/minute |

### Resource Utilization Targets

| Resource | Target Utilization |
|----------|-------------------|
| Lambda memory | < 70% of allocated |
| Lambda duration | < 50% of timeout |
| DynamoDB read capacity | < 80% of provisioned |
| DynamoDB write capacity | < 80% of provisioned |
| DRS API rate limit | < 50% of limit |

---

## Test Execution Plan

### Phase 1: Baseline Testing (Week 1)
- Run all scenarios with current production data
- Establish baseline metrics
- Identify bottlenecks

### Phase 2: Load Testing (Week 2)
- Gradually increase load to 1,000 servers
- Test concurrent operations
- Monitor resource utilization

### Phase 3: Stress Testing (Week 3)
- Push beyond 1,000 servers (if possible)
- Test failure scenarios
- Validate error handling

### Phase 4: Optimization (Week 4)
- Implement performance improvements
- Re-test critical scenarios
- Document final results

---

## Success Criteria

### Functional Requirements
- ✅ All 1,000 servers discoverable across 4 accounts
- ✅ DRS capacity accurately reported per account
- ✅ Tag resolution works with 250 servers per account
- ✅ Recovery plans execute with 10 waves × 100 servers
- ✅ No data loss or corruption under load

### Performance Requirements
- ✅ All response times meet p95 targets
- ✅ No throttling errors under normal load
- ✅ Concurrent operations succeed without degradation
- ✅ Memory utilization < 70% of allocated
- ✅ Error rate < 0.1% under load

### Scalability Requirements
- ✅ System handles 1,000 servers without modification
- ✅ Linear scaling up to 300 servers per account
- ✅ Graceful degradation under extreme load
- ✅ Clear capacity limits documented

---

## Monitoring and Metrics

### CloudWatch Metrics

**Lambda Metrics**:
- Invocations
- Duration (p50, p95, p99)
- Errors
- Throttles
- Concurrent Executions
- Memory Utilization

**DynamoDB Metrics**:
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- UserErrors
- SystemErrors
- ThrottledRequests

**Custom Metrics**:
- DRS API calls per operation
- Servers processed per second
- Cross-account operation latency
- Tag resolution accuracy

### CloudWatch Dashboards

Create dashboard with:
- Response time trends
- Error rate trends
- Resource utilization
- DRS capacity status
- Concurrent execution count

### Alarms

Set alarms for:
- Response time p95 > target
- Error rate > 1%
- Lambda throttles > 0
- DynamoDB throttles > 0
- DRS capacity > 280 servers per account

---

## Risk Mitigation

### Identified Risks

1. **DRS API Rate Limiting**
   - Risk: Throttling with 4 accounts × multiple queries
   - Mitigation: Implement exponential backoff, cache results

2. **Lambda Timeout**
   - Risk: Queries timeout with 1,000 servers
   - Mitigation: Increase timeout, implement pagination

3. **DynamoDB Throttling**
   - Risk: Large protection groups exceed write capacity
   - Mitigation: Use on-demand billing, batch writes

4. **Memory Exhaustion**
   - Risk: Loading 1,000 servers into memory
   - Mitigation: Stream processing, pagination

### Rollback Plan

If performance targets not met:
1. Reduce concurrent operations
2. Implement caching layer
3. Increase Lambda memory/timeout
4. Switch DynamoDB to on-demand
5. Implement pagination for large queries

---

## Deliverables

1. **Load Test Script**: `scripts/load-test-handlers.sh`
2. **Test Results Report**: `docs/performance/load-test-results-YYYYMMDD.md`
3. **Performance Dashboard**: CloudWatch dashboard JSON
4. **Optimization Recommendations**: Based on test results
5. **Capacity Planning Guide**: For scaling beyond 1,000 servers

---

## Next Steps

1. Create load test script for automated testing
2. Set up test environment with 1,000 servers across 4 accounts
3. Execute Phase 1 baseline testing
4. Analyze results and identify optimizations
5. Document findings and update architecture

---

**Document Owner**: DR Orchestration Team  
**Review Frequency**: After each major release  
**Last Updated**: 2026-01-24
