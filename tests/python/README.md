# AWS DRS Orchestration - Automated E2E Testing

Complete end-to-end automated testing framework for AWS DRS Orchestration system.

## Overview

The `automated_e2e_test.py` script provides comprehensive automated testing that:
1. **Triggers** recovery drill executions via API Gateway
2. **Monitors** orchestration system (DynamoDB) for execution progress
3. **Validates** DRS jobs directly via DRS API
4. **Verifies** EC2 instances launched successfully
5. **Reports** detailed results with timing and diagnostics

## Prerequisites

```bash
# Install dependencies
pip install boto3 requests

# Configure AWS credentials
aws configure
# or set environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

## Usage

### Basic Usage

```bash
python3 automated_e2e_test.py \
  --api-endpoint https://your-api-gateway-url \
  --plan-id test-plan-3waves-6servers
```

### Options

```bash
--api-endpoint URL    # Required: API Gateway endpoint URL
--plan-id ID          # Required: Recovery plan ID to execute
--region REGION       # Optional: AWS region (default: us-east-1)
--recovery            # Optional: Run recovery instead of drill
```

### Examples

**Run drill execution test**:
```bash
python3 automated_e2e_test.py \
  --api-endpoint https://abc123.execute-api.us-east-1.amazonaws.com/prod \
  --plan-id test-plan-3waves-6servers \
  --region us-east-1
```

**Run recovery execution test**:
```bash
python3 automated_e2e_test.py \
  --api-endpoint https://abc123.execute-api.us-east-1.amazonaws.com/prod \
  --plan-id production-plan \
  --recovery
```

## Test Phases

### Phase 1: Trigger Execution
- Sends POST request to API Gateway
- Payload: `{"isDrill": true/false}`
- Returns: Execution ID

### Phase 2: Monitor Orchestration
- Polls DynamoDB execution table every 15 seconds
- Tracks status transitions: PENDING → POLLING → LAUNCHING → COMPLETED/FAILED
- Timeout: 30 minutes
- Collects wave and server data

### Phase 3: Monitor DRS Jobs
- Retrieves job IDs from execution data
- Calls DRS DescribeJobs API for each job
- Checks server launch statuses:
  - `LAUNCHED` = Success ✅
  - `LAUNCH_FAILED`, `FAILED`, `TERMINATED` = Failure ❌
- Identifies which servers failed

### Phase 4: Validate EC2 Instances
- Extracts EC2 instance IDs from DRS results
- Calls EC2 DescribeInstances API
- Verifies instances in `running` state
- Collects instance details:
  - Instance type
  - Private/public IPs
  - Subnet and VPC
  - Launch time

### Phase 5: Generate Report
- Summarizes results from all phases
- Calculates test duration
- Lists errors and warnings
- Determines overall pass/fail

## Output

### Console Output

```
================================================================================
STARTING END-TO-END AUTOMATED TEST
Plan ID: test-plan-3waves-6servers
Execution Type: DRILL
================================================================================

[PHASE 1] Triggering execution via API...
✅ Execution triggered: 9fc2230b-3669-4819-9a93-271bb4a5e86c

[PHASE 2] Monitoring orchestration system...
  [0s] Status: PENDING
  [15s] Status: POLLING
  [30s] Status: LAUNCHING
  [180s] Status: COMPLETED
✅ Orchestration monitoring complete

[PHASE 3] Monitoring DRS jobs...
  Monitoring DRS job drs:recovery-job:xyz123 (Wave wave-1)...
    ✅ All servers LAUNCHED (2 servers)
  Monitoring DRS job drs:recovery-job:xyz456 (Wave wave-2)...
    ✅ All servers LAUNCHED (2 servers)
✅ DRS monitoring complete

[PHASE 4] Validating EC2 instances...
  Validating 4 EC2 instance(s)...
    ✅ Instance i-0123456789abcdef0: running (t3.medium)
    ✅ Instance i-0123456789abcdef1: running (t3.medium)
    ✅ Instance i-0123456789abcdef2: running (t3.medium)
    ✅ Instance i-0123456789abcdef3: running (t3.medium)
✅ EC2 validation complete

================================================================================
TEST RESULTS SUMMARY
================================================================================

Execution ID: 9fc2230b-3669-4819-9a93-271bb4a5e86c
Execution Status: COMPLETED
Test Duration: 3m 15s

Waves: 2
  - Wave wave-1: COMPLETED
  - Wave wave-2: COMPLETED

DRS Jobs: 2
  - Job drs:recovery-job:xyz123: ✅ SUCCESS
  - Job drs:recovery-job:xyz456: ✅ SUCCESS

EC2 Instances: 4
  - Running: 4/4

================================================================================
✅ TEST PASSED - All validations successful
================================================================================

Results saved to: test_results_9fc2230b-3669-4819-9a93-271bb4a5e86c.json
```

### JSON Results File

```json
{
  "test_start_time": "2025-11-28T22:30:00.000000+00:00",
  "test_end_time": "2025-11-28T22:33:15.000000+00:00",
  "execution_id": "9fc2230b-3669-4819-9a93-271bb4a5e86c",
  "execution_status": "COMPLETED",
  "waves": [
    {
      "wave_id": "wave-1",
      "status": "COMPLETED",
      "job_id": "drs:recovery-job:xyz123",
      "server_count": 2
    }
  ],
  "drs_jobs": [
    {
      "job_id": "drs:recovery-job:xyz123",
      "wave_id": "wave-1",
      "job_status": "COMPLETED",
      "servers": [
        {
          "source_server_id": "s-0123456789",
          "launch_status": "LAUNCHED",
          "instance_id": "i-0123456789abcdef0",
          "hostname": "server1"
        }
      ],
      "all_launched": true,
      "any_failed": false,
      "success": true
    }
  ],
  "ec2_instances": [
    {
      "instance_id": "i-0123456789abcdef0",
      "state": "running",
      "instance_type": "t3.medium",
      "private_ip": "10.0.1.10",
      "public_ip": "54.123.45.67",
      "subnet_id": "subnet-123456",
      "vpc_id": "vpc-123456",
      "launch_time": "2025-11-28T22:31:30+00:00",
      "running": true
    }
  ],
  "success": true,
  "errors": [],
  "warnings": []
}
```

## Success Criteria

Test passes when ALL of the following are true:
- ✅ Execution status = `COMPLETED`
- ✅ All waves status = `COMPLETED`
- ✅ All DRS jobs: `all_launched = true` and `any_failed = false`
- ✅ All EC2 instances: `state = running`

Test fails if ANY of the following occur:
- ❌ Execution status = `FAILED` or `TIMEOUT`
- ❌ Any wave status = `FAILED`
- ❌ Any DRS job: `any_failed = true`
- ❌ Any EC2 instance: `state != running`
- ❌ Exceptions during test execution

## Exit Codes

- `0` - Test passed (all validations successful)
- `1` - Test failed (see errors in output)

## Troubleshooting

### API Gateway Connection Failed
```
Error: Failed to trigger execution: Connection refused
```
**Solution**: Verify API endpoint URL is correct and accessible

### AWS Credentials Error
```
Error: Unable to locate credentials
```
**Solution**: Configure AWS credentials via `aws configure` or environment variables

### DRS Permission Denied
```
Error: AccessDeniedException when calling DRS DescribeJobs
```
**Solution**: Ensure IAM role/user has `drs:DescribeJobs` permission

### Execution Timeout
```
Error: Orchestration monitoring timed out after 1800s
```
**Solution**: 
- Check if DRS jobs are actually running
- Investigate DRS job failure causes
- Check source server replication status

### No EC2 Instances Found
```
Warning: No EC2 instances to validate
```
**Solution**:
- Verify DRS jobs launched successfully
- Check if `recoveryInstanceID` is present in DRS job data
- Ensure sufficient EC2 capacity in target region

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: E2E Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Install Dependencies
        run: pip install boto3 requests
      
      - name: Run E2E Test
        run: |
          python3 tests/python/automated_e2e_test.py \
            --api-endpoint ${{ secrets.API_ENDPOINT }} \
            --plan-id test-plan-3waves-6servers
      
      - name: Upload Results
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: test-results
          path: test_results_*.json
```

## Advanced Usage

### Programmatic Usage

```python
from automated_e2e_test import AutomatedE2ETest

# Initialize test
test = AutomatedE2ETest(
    api_endpoint='https://your-api-gateway-url',
    plan_id='test-plan-3waves-6servers',
    region='us-east-1'
)

# Run test
results = test.run_test(is_drill=True)

# Check results
if results['success']:
    print("✅ Test passed")
    print(f"Duration: {results['test_duration']}")
    print(f"EC2 Instances: {len(results['ec2_instances'])}")
else:
    print("❌ Test failed")
    for error in results['errors']:
        print(f"Error: {error}")
```

### Custom Configuration

```python
# Customize timeouts and intervals
test.max_wait_time = 3600  # 1 hour
test.poll_interval = 30     # 30 seconds

# Run test
results = test.run_test(is_drill=True)
```

## Metrics and Monitoring

The test collects comprehensive metrics:

**Timing Metrics**:
- Total test duration
- Time to trigger execution
- Time to complete orchestration
- Time for DRS job completion
- Time for EC2 validation

**Success Metrics**:
- Execution success rate
- Wave success rate
- DRS job success rate
- EC2 instance launch success rate

**Resource Metrics**:
- Number of waves
- Number of DRS jobs
- Number of EC2 instances
- Instance types launched

## Known Issues

1. **DRS Job Status Delay**: DRS jobs may take 2-5 minutes to appear in DescribeJobs API
2. **EC2 Instance State**: Instances may be "pending" for 1-2 minutes after DRS reports "LAUNCHED"
3. **Network Latency**: API Gateway calls may timeout on slow connections

## Support

For issues or questions:
1. Check CloudWatch logs for Lambda functions
2. Verify DRS console for job status
3. Review execution history in DynamoDB
4. Check test results JSON for detailed diagnostics

---

**Created**: November 28, 2025  
**Version**: 1.0  
**Status**: Production Ready
