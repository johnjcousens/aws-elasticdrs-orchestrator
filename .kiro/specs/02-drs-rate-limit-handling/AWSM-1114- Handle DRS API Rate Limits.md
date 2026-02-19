# AWSM-1114: DRS Capacity Monitoring and Rate Limit Handling

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5492572189/AWSM-1114%3A%20Handle%20DRS%20API%20Rate%20Limits

**Document Type**: Implementation Guide  
**Audience**: Platform Engineers, DR Architects, Operations Teams  
**JIRA**: [AWSM-1114](https://healthedge.atlassian.net/browse/AWSM-1114)  
**Epic**: [AWSM-1112 - DRS Integration and EC2 Recovery](https://healthedge.atlassian.net/browse/AWSM-1112)

---

## Executive Summary

This document describes the **DRS capacity monitoring implementation** for the AWS DR Orchestration Platform. The platform provides comprehensive cross-account DRS capacity monitoring across all 15 DRS-enabled regions, enabling proactive capacity planning and preventing service quota violations.

**Scope**: This document focuses on DRS capacity monitoring and basic rate limit handling. For complete platform architecture, see [AWSM-1103: Enterprise Wave-Based Orchestration](../../AWSM-1103-Enterprise-Wave-Orchestration.md).

---

## Table of Contents

1. [Original Requirements](#original-requirements)
2. [Implementation Status](#implementation-status)
3. [DRS Capacity Monitoring](#drs-capacity-monitoring)
4. [Cross-Account Support](#cross-account-support)
5. [API Reference](#api-reference)
6. [Integration Guide](#integration-guide)
7. [Operations Guide](#operations-guide)
8. [Future Enhancements](#future-enhancements)

---

## Original Requirements

### User Story

As a DR Operations Engineer, I want DRS API calls to handle rate limits gracefully, so that large-scale recovery operations complete successfully.

### Acceptance Criteria

1. **Exponential Backoff Retry Logic**: *Given* DRS API rate limit exceeded *When* making API calls *Then* exponential backoff retry logic is applied
2. **Throttling for Concurrent Jobs**: *Given* multiple concurrent recovery jobs *When* creating jobs *Then* job creation is throttled to stay within rate limits
3. **Error Logging and Escalation**: *Given* rate limit errors *When* retries are exhausted *Then* error is logged and escalated

### Definition of Done

- Exponential backoff logic implemented
- Rate limit detection and handling implemented
- Throttling mechanism for concurrent jobs
- Rate limit testing performed
- Monitoring for rate limit errors configured

---

## Implementation Status

### DRS Capacity Monitoring

The platform provides comprehensive DRS capacity monitoring across all regions with cross-account support:

**Features**:
- Cross-account DRS capacity queries
- Multi-region concurrent capacity aggregation (15 regions)
- Per-region capacity breakdown with status indicators
- Account-wide capacity status determination
- Replicating server count vs 300-server limit tracking
- Extended source server detection (staging accounts)
- Capacity planning metrics and available slots calculation
- Hub-and-spoke architecture support

**Code Location**: 
- [lambda/query-handler/index.py](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/query-handler/index.py) - Main capacity monitoring implementation
- [get_drs_account_capacity_all_regions()](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/query-handler/index.py#L1050-L1370) - Account-wide capacity aggregation
- [get_drs_regional_capacity()](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/query-handler/index.py#L985-L1048) - Single region capacity query
- [_count_drs_servers()](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/query-handler/index.py#L280-L360) - Server counting with extended source server detection

### Rate Limit Handling

Basic rate limit handling with graceful degradation:

**Features**:
- Basic `ConflictException` retry in execution handler
- Concurrent regional queries with thread pooling (max 10 threads)
- Graceful degradation for failed regions

**Planned Enhancements**:
- Comprehensive exponential backoff retry logic
- Token bucket rate limiting
- DRS API throttling with semaphore control
- CloudWatch metrics for rate limit errors
- CloudWatch alarms and SNS notifications
- Comprehensive rate limit testing

---

## DRS Capacity Monitoring

### Architecture Overview

The platform monitors DRS capacity across three dimensions:

1. **Per-Region Capacity**: Each region has independent 300-server replication limit
2. **Account-Wide Capacity**: Aggregated view across all 15 DRS regions
3. **Cross-Account Capacity**: Hub-and-spoke monitoring of multiple target accounts

### DRS Service Quotas

| Quota Name | Limit | Scope | Description |
|-----------|-------|-------|-------------|
| Replicating Source Servers | 300 | Per Region | Maximum servers actively replicating TO this account |
| Source Servers (Total) | 4,000 | Per Region | Maximum total servers including extended source servers |
| Recovery Instances per Job | 100 | Per Job | Maximum instances per single recovery job |
| Concurrent Recovery Jobs | 20 | Per Region | Maximum simultaneous recovery jobs |
| Servers in All Active Jobs | 500 | Per Region | Maximum servers across all active jobs |

**Important Notes**:
- **Extended Source Servers**: Servers from staging accounts do NOT count toward the 300 replicating limit
- **Per-Region Quotas**: Each region has independent quotas (e.g., 300 in us-east-1 + 300 in us-west-2 = 600 total)
- **Recovery Capacity**: Total source servers (including extended) count toward 4,000 recovery limit

### Capacity Status Determination

| Status | Condition | Threshold | Action Required |
|--------|-----------|-----------|-----------------|
| CRITICAL | Any region >= 300 replicating servers | 100% | IMMEDIATE: Stop new replication, review capacity |
| WARNING | Any region >= 270 replicating servers | 90% | SOON: Plan capacity expansion or cleanup |
| INFO | Any region >= 240 replicating servers | 80% | MONITOR: Track growth trends |
| OK | All regions < 240 replicating servers | < 80% | Normal operations |

**Status Logic**:
- Status is determined per-region (each region has 300-server limit)
- Overall status = worst region status
- Example: 200 servers in us-east-1 + 280 servers in us-west-2 = WARNING (due to us-west-2)

---

## Cross-Account Support

### Hub-and-Spoke Architecture

The platform supports cross-account DRS capacity monitoring using IAM role assumption:

```
┌─────────────────────────────────────────────────────────────┐
│                      Hub Account                             │
│                  (Orchestration Platform)                    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Query Handler Lambda                        │    │
│  │  - Queries DRS capacity across all regions         │    │
│  │  - Assumes cross-account roles                     │    │
│  │  - Aggregates capacity metrics                     │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ AssumeRole                        │
│                          ▼                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Spoke Account │  │ Spoke Account │  │ Spoke Account │
│      #1       │  │      #2       │  │      #3       │
│               │  │               │  │               │
│  DRS Servers  │  │  DRS Servers  │  │  DRS Servers  │
│  (300 limit)  │  │  (300 limit)  │  │  (300 limit)  │
└───────────────┘  └───────────────┘  └───────────────┘
```

### Cross-Account Configuration

**Target Accounts Table** (`target-accounts`):
```json
{
  "accountId": "123456789012",
  "accountName": "Production DR Account",
  "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationCrossAccountRole",
  "assumeRoleName": "DRSOrchestrationCrossAccountRole",
  "externalId": "unique-external-id-12345",
  "regions": ["us-east-1", "us-west-2"],
  "status": "ACTIVE"
}
```

### IAM Role Requirements

**Hub Account Lambda Role** needs:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::*:role/DRSOrchestrationCrossAccountRole"
    }
  ]
}
```

**Spoke Account Cross-Account Role** needs:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "drs:DescribeSourceServers",
        "drs:DescribeJobs",
        "drs:DescribeRecoveryInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

**Trust Policy** (Spoke Account Role):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::HUB_ACCOUNT_ID:role/QueryHandlerRole"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id-12345"
        }
      }
    }
  ]
}
```

---

## API Reference

### 1. Get Account-Wide DRS Capacity

Query DRS capacity across all 15 regions for an account.

**Direct Lambda Invocation**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='query-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_drs_account_capacity_all_regions"
    })
)

result = json.loads(response['Payload'].read())
```

**Response**:
```json
{
  "totalSourceServers": 325,
  "replicatingServers": 280,
  "maxReplicatingServers": 300,
  "maxSourceServers": 4000,
  "availableReplicatingSlots": 320,
  "status": "WARNING",
  "message": "WARNING: 1 region(s) approaching limit: us-east-1 (280/300)",
  "regionalBreakdown": [
    {
      "region": "us-east-1",
      "totalServers": 325,
      "replicatingServers": 280,
      "maxReplicating": 300,
      "availableSlots": 20,
      "percentUsed": 93.3,
      "status": "WARNING"
    },
    {
      "region": "us-west-2",
      "totalServers": 0,
      "replicatingServers": 0,
      "maxReplicating": 300,
      "availableSlots": 300,
      "percentUsed": 0.0,
      "status": "OK"
    }
  ],
  "failedRegions": [],
  "activeRegions": 1,
  "totalRegionalCapacity": 300
}
```

**Implementation**: [get_drs_account_capacity_all_regions()](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/query-handler/index.py#L1050-L1370)

### 2. Get Regional DRS Capacity

Query DRS capacity for a specific region.

**Direct Invocation**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='query-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_drs_regional_capacity",
        "queryParams": {"region": "us-east-1"}
    })
)

result = json.loads(response['Payload'].read())
print(f"Region: {result['region']}")
print(f"Replicating Servers: {result['replicatingServers']}")
print(f"Status: {result['status']}")
```

**Response**:
```json
{
  "region": "us-east-1",
  "totalSourceServers": 125,
  "replicatingServers": 120,
  "status": "OK"
}
```

**Status Values**:
- `OK`: Region operational with servers
- `NOT_INITIALIZED`: DRS not initialized in region
- `ACCESS_DENIED`: Insufficient permissions
- `ERROR`: Other errors occurred

**Implementation**: [get_drs_regional_capacity()](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/query-handler/index.py#L985-L1048)

### 3. Get Cross-Account Capacity

Query DRS capacity for a target account (cross-account).

**Direct Invocation**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='query-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_drs_account_capacity_all_regions",
        "queryParams": {
            "account_context": {
                "accountId": "123456789012"
            }
        }
    })
)

result = json.loads(response['Payload'].read())
print(f"Total Servers: {result['totalSourceServers']}")
print(f"Replicating: {result['replicatingServers']}")
print(f"Status: {result['status']}")
```

**Response**: Same format as endpoint #1 (account-wide capacity)

**Implementation**: [get_drs_account_capacity_all_regions()](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/query-handler/index.py#L1050-L1370) with `account_context` parameter

---

## Integration Guide

### Python Integration (Orchestration Role)

**Query Account Capacity**:
```python
import boto3
import json

def get_drs_capacity(account_id=None):
    """Get DRS capacity for an account"""
    lambda_client = boto3.client('lambda')
    
    payload = {
        "operation": "get_drs_account_capacity_all_regions"
    }
    
    if account_id:
        payload["queryParams"] = {
            "account_context": {"accountId": account_id}
        }
    
    response = lambda_client.invoke(
        FunctionName='query-handler',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    return json.loads(response['Payload'].read())

# Usage
capacity = get_drs_capacity()
print(f"Status: {capacity['status']}")
print(f"Replicating Servers: {capacity['replicatingServers']}")
print(f"Available Slots: {capacity['availableReplicatingSlots']}")

# Check if at capacity
if capacity['status'] == 'CRITICAL':
    print("WARNING: DRS at capacity limit!")
    for region in capacity['regionalBreakdown']:
        if region['status'] == 'CRITICAL':
            print(f"  - {region['region']}: {region['replicatingServers']}/300")
```

### AWS CLI Integration (Orchestration Role)

**Direct Lambda Invocation**:
```bash
# Get account capacity
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation": "get_drs_account_capacity_all_regions"}' \
  response.json

cat response.json | jq '.status'

# Get regional capacity
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation": "get_drs_regional_capacity", "queryParams": {"region": "us-east-1"}}' \
  response.json

cat response.json | jq '.'
```

---

## Operations Guide

### Monitoring DRS Capacity

**Daily Capacity Check Script**:
```bash
#!/bin/bash
# check-drs-capacity.sh

FUNCTION_NAME="query-handler"
ALERT_THRESHOLD=270  # 90% of 300

echo "Checking DRS capacity across all regions..."

# Invoke Lambda
aws lambda invoke \
  --function-name $FUNCTION_NAME \
  --payload '{"operation": "get_drs_account_capacity_all_regions"}' \
  response.json > /dev/null

# Parse response
STATUS=$(cat response.json | jq -r '.status')
REPLICATING=$(cat response.json | jq -r '.replicatingServers')
MESSAGE=$(cat response.json | jq -r '.message')

echo "Status: $STATUS"
echo "Replicating Servers: $REPLICATING"
echo "Message: $MESSAGE"

# Check for critical regions
CRITICAL_REGIONS=$(cat response.json | jq -r '.regionalBreakdown[] | select(.status == "CRITICAL") | .region')

if [ ! -z "$CRITICAL_REGIONS" ]; then
  echo ""
  echo "⚠️  CRITICAL: The following regions are at capacity limit:"
  echo "$CRITICAL_REGIONS"
  
  # Send alert (example using SNS)
  aws sns publish \
    --topic-arn "arn:aws:sns:us-east-1:123456789012:drs-capacity-alerts" \
    --subject "DRS Capacity Alert: CRITICAL" \
    --message "DRS capacity limit reached in: $CRITICAL_REGIONS"
fi

# Cleanup
rm response.json
```

### Capacity Planning

**Calculate Available Capacity**:
```python
def calculate_capacity_headroom(capacity_data):
    """Calculate how many more servers can be added"""
    regional_breakdown = capacity_data['regionalBreakdown']
    
    # Find regions with available capacity
    available_regions = []
    for region in regional_breakdown:
        if region['availableSlots'] > 0:
            available_regions.append({
                'region': region['region'],
                'available': region['availableSlots'],
                'current': region['replicatingServers']
            })
    
    # Sort by most available capacity
    available_regions.sort(key=lambda x: x['available'], reverse=True)
    
    print("Capacity Planning Report")
    print("=" * 60)
    print(f"Total Available Slots: {capacity_data['availableReplicatingSlots']}")
    print(f"Active Regions: {capacity_data['activeRegions']}")
    print()
    print("Regional Capacity:")
    for region in available_regions:
        print(f"  {region['region']}: {region['available']} slots available ({region['current']}/300 used)")
    
    return available_regions

# Usage
capacity = get_drs_capacity()
available = calculate_capacity_headroom(capacity)

# Recommend action
if capacity['availableReplicatingSlots'] < 50:
    print("\n⚠️  WARNING: Less than 50 slots available across all regions")
    print("Recommended Actions:")
    print("  1. Review and remove unused source servers")
    print("  2. Consider expanding to additional regions")
    print("  3. Implement staging account architecture for extended capacity")
```

### CloudWatch Monitoring

**Create CloudWatch Dashboard**:
```bash
# Create dashboard for DRS capacity monitoring
aws cloudwatch put-dashboard \
  --dashboard-name "DRS-Capacity-Monitoring" \
  --dashboard-body file://drs-dashboard.json
```

**Dashboard Configuration** (`drs-dashboard.json`):
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "Capacity Queries"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "DRS Capacity Query Rate"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/lambda/query-handler'\n| fields @timestamp, @message\n| filter @message like /DRS capacity/\n| sort @timestamp desc\n| limit 20",
        "region": "us-east-1",
        "title": "Recent Capacity Checks"
      }
    }
  ]
}
```

---

## Future Enhancements

The following features are planned:

### 1. Comprehensive Exponential Backoff Retry Logic

**Planned Implementation**:
```python
# lambda/shared/drs_client.py (PLANNED)
import time
from functools import wraps
from botocore.exceptions import ClientError

def drs_api_call_with_retry(max_retries=5, base_delay=1):
    """
    Decorator for DRS API calls with exponential backoff retry logic.
    
    Handles:
    - ThrottlingException
    - RequestLimitExceeded
    - ServiceUnavailable
    """
```

### 2. Token Bucket Rate Limiting

**Planned Implementation**:
```python
# lambda/shared/rate_limiter.py (PLANNED)
import time
import threading

class TokenBucket:
    """
    Token bucket rate limiter for DRS API calls.
    
    Ensures API calls stay within rate limits by controlling
    request rate using token bucket algorithm.
    """
    def __init__(self, rate, capacity):
        self.rate = rate  # Tokens per second
        self.capacity = capacity  # Max tokens
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()
```

### 3. CloudWatch Metrics and Alarms

**Planned Implementation**:
```python
# Publish rate limit metrics to CloudWatch (PLANNED)
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_rate_limit_metric(error_type, region):
    """Publish rate limit error to CloudWatch"""
    cloudwatch.put_metric_data(
        Namespace='DRS/RateLimits',
        MetricData=[
            {
                'MetricName': 'RateLimitErrors',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'ErrorType', 'Value': error_type},
                    {'Name': 'Region', 'Value': region}
                ]
            }
        ]
    )
```

---

## Shared Utilities

The DRS capacity monitoring implementation uses several shared utility modules from `lambda/shared/` for cross-cutting concerns:

### 1. Account Management (`account_utils.py`)

**Purpose**: Account identification, validation, and target account management

**Functions Used**:
- `get_account_name(account_id)` - Get account name/alias from IAM or Organizations
- `get_target_accounts()` - List all configured target accounts from DynamoDB
- `construct_role_arn(account_id)` - Build standardized cross-account role ARN
- `validate_account_id(account_id)` - Validate 12-digit account ID format

**Code Location**: [lambda/shared/account_utils.py](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/account_utils.py)

**Usage in Capacity Monitoring**:
```python
from shared.account_utils import get_account_name, get_target_accounts

# Get friendly account name for display
account_name = get_account_name(current_account_id)

# List all target accounts for multi-account capacity queries
accounts = get_target_accounts()
```

### 2. Conflict Detection (`conflict_detection.py`)

**Purpose**: Server availability validation and Protection Group resolution

**Functions Used**:
- `query_drs_servers_by_tags(region, tags, account_context)` - Resolve tag-based Protection Groups to server IDs
- `get_servers_in_active_drs_jobs(region, account_context)` - Query DRS API for servers in active jobs
- `check_concurrent_jobs_limit(region, account_context)` - Validate 20 concurrent jobs limit

**Code Location**: [lambda/shared/conflict_detection.py](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/conflict_detection.py)

**Usage in Capacity Monitoring**:
```python
from shared.conflict_detection import query_drs_servers_by_tags

# Resolve Protection Group servers by tags
servers = query_drs_servers_by_tags(
    region="us-east-1",
    tags={"Environment": "Production", "DR": "Enabled"},
    account_context={"accountId": "123456789012"}
)
```

### 3. Cross-Account Access (`cross_account.py`)

**Purpose**: IAM role assumption for hub-and-spoke architecture

**Functions Used**:
- `get_current_account_id()` - Get current AWS account ID via STS
- `create_drs_client(region, account_context)` - Create DRS client with optional cross-account role assumption
- `get_cross_account_session(role_arn, external_id)` - Assume IAM role and return boto3 session

**Code Location**: [lambda/shared/cross_account.py](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/cross_account.py)

**Usage in Capacity Monitoring**:
```python
from shared.cross_account import create_drs_client, get_current_account_id

# Get current account
current_account = get_current_account_id()

# Create DRS client for current account
drs_client = create_drs_client(region="us-east-1")

# Create DRS client for cross-account access
account_context = {
    "accountId": "123456789012",
    "assumeRoleName": "DRSOrchestrationCrossAccountRole",
    "isCurrentAccount": False
}
drs_client = create_drs_client(region="us-east-1", account_context=account_context)
```

### 4. DRS Service Limits (`drs_limits.py`)

**Purpose**: DRS service quota constants and validation

**Constants Used**:
- `DRS_LIMITS["MAX_REPLICATING_SERVERS"]` - 300 servers per region limit
- `DRS_LIMITS["MAX_SOURCE_SERVERS"]` - 4,000 total servers per region
- `DRS_LIMITS["MAX_SERVERS_PER_JOB"]` - 100 servers per job limit
- `DRS_LIMITS["MAX_CONCURRENT_JOBS"]` - 20 concurrent jobs limit
- `DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"]` - 500 servers across all jobs

**Functions Used**:
- `validate_concurrent_jobs(region, drs_client)` - Check concurrent jobs limit
- `validate_servers_in_all_jobs(region, new_count, drs_client)` - Check total servers limit
- `validate_wave_server_count(wave, pg_cache, account_context)` - Check per-job server limit

**Code Location**: [lambda/shared/drs_limits.py](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/drs_limits.py)

**Usage in Capacity Monitoring**:
```python
from shared.drs_limits import DRS_LIMITS, validate_concurrent_jobs

# Use constants for capacity calculations
max_replicating = DRS_LIMITS["MAX_REPLICATING_SERVERS"]  # 300
available_slots = max_replicating - current_replicating

# Validate concurrent jobs before starting new job
validation = validate_concurrent_jobs(region="us-east-1")
if not validation["valid"]:
    print(f"At concurrent jobs limit: {validation['currentJobs']}/20")
```

### 5. DRS Utilities (`drs_utils.py`)

**Purpose**: DRS API response normalization and data transformation

**Functions Used**:
- `map_replication_state_to_display(state)` - Convert DRS replication state to display-friendly format
- `normalize_drs_response(drs_data)` - Convert PascalCase to camelCase
- `transform_drs_server_for_frontend(server)` - Transform DRS server to frontend format

**Code Location**: [lambda/shared/drs_utils.py](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/drs_utils.py)

**Usage in Capacity Monitoring**:
```python
from shared.drs_utils import map_replication_state_to_display

# Convert DRS replication state for display
display_state = map_replication_state_to_display("CONTINUOUS")
# Returns: "READY_FOR_RECOVERY"

display_state = map_replication_state_to_display("INITIAL_SYNC")
# Returns: "SYNCING"
```

### 6. Response Utilities (`response_utils.py`)

**Purpose**: Standardized API Gateway responses with CORS and security headers

**Functions Used**:
- `response(status_code, body, headers)` - Generate API Gateway response with CORS
- `DecimalEncoder` - JSON encoder for DynamoDB Decimal types

**Code Location**: [lambda/shared/response_utils.py](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/response_utils.py)

**Usage in Capacity Monitoring**:
```python
from shared.response_utils import response

# Success response
return response(200, {
    "totalSourceServers": 325,
    "replicatingServers": 280,
    "status": "WARNING"
})

# Error response
return response(500, {
    "error": "Failed to query DRS capacity",
    "details": str(exception)
})
```

### Integration Architecture

The shared utilities provide a layered architecture for DRS capacity monitoring:

```
┌─────────────────────────────────────────────────────────────┐
│                  Query Handler Lambda                        │
│              (DRS Capacity Monitoring)                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Uses
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Shared Utilities Layer                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Account    │  │    Cross     │  │     DRS      │     │
│  │    Utils     │  │   Account    │  │    Limits    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Conflict   │  │     DRS      │  │   Response   │     │
│  │  Detection   │  │    Utils     │  │    Utils     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Calls
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      AWS Services                            │
│                                                              │
│    DRS API    │    STS    │  DynamoDB  │  IAM/Orgs         │
└─────────────────────────────────────────────────────────────┘
```

**Key Benefits**:
- **Separation of Concerns**: Each utility module has a single responsibility
- **Reusability**: Shared utilities used across multiple Lambda functions
- **Testability**: Utilities can be unit tested independently
- **Maintainability**: Changes to cross-cutting concerns in one place
- **Consistency**: Standardized patterns for common operations

---

## References

### AWS Documentation

- **DRS API Reference**: https://docs.aws.amazon.com/drs/latest/APIReference/Welcome.html
- **DRS Service Quotas**: https://docs.aws.amazon.com/drs/latest/userguide/service-quotas.html
- **DRS Best Practices**: https://docs.aws.amazon.com/drs/latest/userguide/best-practices.html
- **AWS Service Quotas**: https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html

### Platform Documentation

- **AWSM-1103: Enterprise Wave-Based Orchestration**: [AWSM-1103-Enterprise-Wave-Orchestration.md](../../AWSM-1103-Enterprise-Wave-Orchestration.md)
- **Query Handler Source Code**: [lambda/query-handler/index.py](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/query-handler/index.py)
  - [get_drs_account_capacity_all_regions()](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/query-handler/index.py#L1050-L1370) - Multi-region capacity aggregation
  - [get_drs_regional_capacity()](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/query-handler/index.py#L985-L1048) - Single region capacity
  - [_count_drs_servers()](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/query-handler/index.py#L280-L360) - Server counting logic
- **Cross-Account Utilities**: [lambda/shared/cross_account.py](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/cross_account.py)
  - [create_drs_client()](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/cross_account.py#L50-L120) - Cross-account DRS client creation
  - [get_current_account_id()](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/cross_account.py#L20-L30) - Get current AWS account ID
- **DRS Limits Module**: [lambda/shared/drs_limits.py](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/drs_limits.py)
  - [DRS_LIMITS](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/drs_limits.py#L10-L30) - DRS service quota constants

### Related User Stories

- **AWSM-1112**: DRS Integration and EC2 Recovery (Parent Epic)
- **AWSM-1113**: DRS Source Server Discovery
- **AWSM-1115**: DRS Recovery Job Orchestration
- **AWSM-1116**: DRS Launch Configuration Management

