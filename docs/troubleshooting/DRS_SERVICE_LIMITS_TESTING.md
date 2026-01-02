# DRS Service Limits Testing

Unit tests for AWS DRS service limits validation without requiring actual DRS infrastructure.

## Overview

These tests validate the frontend and backend validation logic for AWS DRS service quotas using mocked data and API responses. This approach allows comprehensive testing without deploying hundreds of DRS servers.

## AWS DRS Service Limits (2025)

| Limit | Value | Type | Quota Code |
|-------|-------|------|------------|
| Max servers per recovery job | 100 | Hard limit | L-B827C881 |
| Max concurrent recovery jobs | 20 | Hard limit | L-D88FAC3A |
| Max servers in all active jobs | 500 | Hard limit | L-05AFA8C6 |
| Max replicating source servers | 300 | Hard limit | L-C1D14A2B |
| Max source servers per account | 4000 | Adjustable | L-E28BE5E0 |

## Test Coverage

### Frontend Tests (21 tests)

Location: `frontend/src/services/__tests__/drsQuotaService.test.ts`

| Test Suite | Tests | Description |
|------------|-------|-------------|
| DRS_LIMITS Constants | 7 | Validates constants match AWS documented limits |
| validateWaveSize - valid | 3 | Tests valid wave sizes (1, 50, 100 servers) |
| validateWaveSize - invalid | 3 | Tests invalid wave sizes (101, 200, 500 servers) |
| validateWaveSize - edge cases | 2 | Tests edge cases (0, negative) |
| getCapacityStatusType | 6 | Tests status-to-color mapping |

### Backend Tests (27 tests)

Location: `tests/python/unit/test_drs_service_limits.py`

| Test Suite | Tests | Description |
|------------|-------|-------------|
| DRS_LIMITS Constants | 7 | Validates Lambda constants match AWS limits |
| validate_wave_sizes | 9 | Tests wave size validation with various inputs |
| validate_concurrent_jobs | 4 | Tests concurrent job limit with mocked DRS API |
| validate_servers_in_all_jobs | 3 | Tests total servers limit with mocked job data |
| validate_server_replication_states | 4 | Tests replication state validation |

## Running Tests

### Frontend Tests

```bash
cd frontend
npm install
npm run test           # Run all tests once
npm run test:watch     # Run tests in watch mode
npm run test:coverage  # Run tests with coverage report
```

### Backend Tests

```bash
cd tests/python
pip install -r requirements.txt
python -m pytest unit/test_drs_service_limits.py -v
```

## Test Results

### Frontend Test Results

```
 ✓ src/services/__tests__/drsQuotaService.test.ts (21 tests) 3ms
   ✓ DRS_LIMITS Constants > should have correct MAX_SERVERS_PER_JOB limit
   ✓ DRS_LIMITS Constants > should have correct MAX_CONCURRENT_JOBS limit
   ✓ DRS_LIMITS Constants > should have correct MAX_SERVERS_IN_ALL_JOBS limit
   ✓ DRS_LIMITS Constants > should have correct MAX_REPLICATING_SERVERS limit
   ✓ DRS_LIMITS Constants > should have correct MAX_SOURCE_SERVERS limit
   ✓ DRS_LIMITS Constants > should have WARNING_REPLICATING_THRESHOLD less than MAX_REPLICATING_SERVERS
   ✓ DRS_LIMITS Constants > should have CRITICAL_REPLICATING_THRESHOLD between WARNING and MAX
   ✓ validateWaveSize > valid wave sizes > should return null for wave size of 1 server
   ✓ validateWaveSize > valid wave sizes > should return null for wave size of 50 servers
   ✓ validateWaveSize > valid wave sizes > should return null for wave size at exactly the limit (100)
   ✓ validateWaveSize > invalid wave sizes > should return error for wave size of 101 servers (1 over limit)
   ✓ validateWaveSize > invalid wave sizes > should return error for wave size of 200 servers
   ✓ validateWaveSize > invalid wave sizes > should return error for wave size of 500 servers
   ✓ validateWaveSize > edge cases > should return null for wave size of 0 servers
   ✓ validateWaveSize > edge cases > should return null for negative server count
   ✓ getCapacityStatusType > should return "error" for CRITICAL status
   ✓ getCapacityStatusType > should return "warning" for WARNING status
   ✓ getCapacityStatusType > should return "info" for INFO status
   ✓ getCapacityStatusType > should return "success" for OK status
   ✓ getCapacityStatusType > should return "success" for UNKNOWN status (default)
   ✓ getCapacityStatusType > should return "success" for any unrecognized status

 Test Files  1 passed (1)
      Tests  21 passed (21)
```

### Backend Test Results

```
unit/test_drs_service_limits.py::TestDRSLimitsConstants::test_max_servers_per_job PASSED
unit/test_drs_service_limits.py::TestDRSLimitsConstants::test_max_concurrent_jobs PASSED
unit/test_drs_service_limits.py::TestDRSLimitsConstants::test_max_servers_in_all_jobs PASSED
unit/test_drs_service_limits.py::TestDRSLimitsConstants::test_max_replicating_servers PASSED
unit/test_drs_service_limits.py::TestDRSLimitsConstants::test_max_source_servers PASSED
unit/test_drs_service_limits.py::TestDRSLimitsConstants::test_warning_threshold_less_than_max PASSED
unit/test_drs_service_limits.py::TestDRSLimitsConstants::test_critical_threshold_between_warning_and_max PASSED
unit/test_drs_service_limits.py::TestValidateWaveSizes::test_valid_wave_single_server PASSED
unit/test_drs_service_limits.py::TestValidateWaveSizes::test_valid_wave_at_limit PASSED
unit/test_drs_service_limits.py::TestValidateWaveSizes::test_invalid_wave_over_limit PASSED
unit/test_drs_service_limits.py::TestValidateWaveSizes::test_invalid_wave_way_over_limit PASSED
unit/test_drs_service_limits.py::TestValidateWaveSizes::test_multiple_waves_one_invalid PASSED
unit/test_drs_service_limits.py::TestValidateWaveSizes::test_multiple_waves_all_invalid PASSED
unit/test_drs_service_limits.py::TestValidateWaveSizes::test_empty_wave PASSED
unit/test_drs_service_limits.py::TestValidateWaveSizes::test_no_waves PASSED
unit/test_drs_service_limits.py::TestValidateWaveSizes::test_missing_waves_key PASSED
unit/test_drs_service_limits.py::TestValidateConcurrentJobs::test_no_active_jobs PASSED
unit/test_drs_service_limits.py::TestValidateConcurrentJobs::test_some_active_jobs PASSED
unit/test_drs_service_limits.py::TestValidateConcurrentJobs::test_at_limit PASSED
unit/test_drs_service_limits.py::TestValidateConcurrentJobs::test_api_error_returns_valid_with_warning PASSED
unit/test_drs_service_limits.py::TestValidateServersInAllJobs::test_no_servers_in_jobs PASSED
unit/test_drs_service_limits.py::TestValidateServersInAllJobs::test_would_exceed_limit PASSED
unit/test_drs_service_limits.py::TestValidateServersInAllJobs::test_exactly_at_limit PASSED
unit/test_drs_service_limits.py::TestValidateServerReplicationStates::test_all_healthy_servers PASSED
unit/test_drs_service_limits.py::TestValidateServerReplicationStates::test_disconnected_server PASSED
unit/test_drs_service_limits.py::TestValidateServerReplicationStates::test_empty_server_list PASSED
unit/test_drs_service_limits.py::TestValidateServerReplicationStates::test_mixed_healthy_unhealthy PASSED

======================== 27 passed in 1.10s =========================
```

## Test Architecture

### Frontend Testing Stack

- **Vitest**: Fast unit test runner with native ESM support
- **jsdom**: Browser environment simulation
- **Setup file**: `frontend/src/test/setup.ts` mocks `window.AWS_CONFIG`

### Backend Testing Stack

- **pytest**: Python test framework
- **unittest.mock**: Mocks boto3 clients for DRS API calls
- **No real AWS calls**: All tests use mocked responses

## What These Tests Validate

### Validated (with mocked data)

- ✅ DRS_LIMITS constants match AWS documented limits
- ✅ Wave size validation rejects >100 servers
- ✅ Concurrent job validation with mocked job counts
- ✅ Total servers in jobs validation
- ✅ Server replication state validation
- ✅ Error handling when API calls fail
- ✅ Edge cases (empty waves, 0 servers, exactly at limits)

### Not Validated (requires real infrastructure)

- ❌ Actual DRS API responses
- ❌ Real-time quota consumption
- ❌ End-to-end execution flow
- ❌ CloudFormation deployment

## Related Documentation

- [DRS Service Limits Implementation Plan](../implementation/DRS_SERVICE_LIMITS_IMPLEMENTATION_PLAN.md)
- [Testing and Quality Assurance Guide](../guides/TESTING_AND_QUALITY_ASSURANCE.md)
- [AWS DRS Service Quotas](https://docs.aws.amazon.com/general/latest/gr/drs.html)