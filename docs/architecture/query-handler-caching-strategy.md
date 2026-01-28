# Query Handler Caching Strategy

**Date**: 2026-01-24  
**Status**: Design Proposal  
**Owner**: DR Orchestration Team

## Problem Statement

Query Handler makes expensive AWS API calls for data that changes infrequently:
- **DRS quotas**: Changes only when servers are added/removed (minutes to hours)
- **EC2 metadata**: Subnets, security groups, instance types (rarely changes)
- **Current performance**: 300-600ms per query due to AWS API latency

**Goal**: Reduce query response time from 300-600ms to < 100ms for cached data.

---

## Solution: Multi-Layer Caching

### Layer 1: In-Memory Cache (Lambda Container)
**TTL**: 5 minutes  
**Scope**: Per Lambda container  
**Use Case**: Warm invocations within same container

### Layer 2: DynamoDB Cache Table
**TTL**: Configurable per data type (5-60 minutes)  
**Scope**: Cross-container, cross-invocation  
**Use Case**: Cold starts and container recycling

### Layer 3: API Gateway Cache (Optional)
**TTL**: 5 minutes  
**Scope**: Per API endpoint  
**Use Case**: High-traffic read-only endpoints

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Query Handler                            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Check In-Memory Cache (5 min TTL)               │  │
│  │     ↓ MISS                                           │  │
│  │  2. Check DynamoDB Cache (configurable TTL)         │  │
│  │     ↓ MISS                                           │  │
│  │  3. Call AWS API (DRS, EC2)                         │  │
│  │     ↓                                                │  │
│  │  4. Store in DynamoDB Cache                         │  │
│  │     ↓                                                │  │
│  │  5. Store in In-Memory Cache                        │  │
│  │     ↓                                                │  │
│  │  6. Return to caller                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## DynamoDB Cache Table Schema

### Table: `drs-orchestration-query-cache-{env}`

**Primary Key**:
- `cacheKey` (String, HASH) - Composite key: `{dataType}#{region}#{accountId}`
- Examples:
  - `drs-quotas#us-east-1#438465159935`
  - `ec2-subnets#us-west-2#438465159935`
  - `ec2-instance-types#us-east-1#global`

**Attributes**:
- `cacheKey` (String) - Primary key
- `dataType` (String) - Type of cached data (drs-quotas, ec2-subnets, etc.)
- `region` (String) - AWS region
- `accountId` (String) - AWS account ID (or "global" for region-wide data)
- `data` (Map) - Cached data payload
- `ttl` (Number) - DynamoDB TTL (Unix timestamp)
- `createdAt` (Number) - Cache creation timestamp
- `expiresAt` (Number) - Cache expiration timestamp (application-level)

**Indexes**:
- GSI: `dataType-createdAt-index` (for cache invalidation by type)

**TTL**: Enabled on `ttl` attribute (automatic cleanup)

---

## Cache TTL Configuration

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| DRS Quotas | 5 minutes | Changes when servers added/removed |
| DRS Source Servers | 2 minutes | Replication state changes frequently |
| EC2 Subnets | 60 minutes | Rarely changes |
| EC2 Security Groups | 60 minutes | Rarely changes |
| EC2 Instance Profiles | 60 minutes | Rarely changes |
| EC2 Instance Types | 24 hours | Static data per region |
| DRS Accounts | 60 minutes | Cross-account config rarely changes |

---

## Implementation

### 1. Create Cache Utility Module

**File**: `lambda/shared/cache_utils.py`

```python
import time
import json
from typing import Optional, Dict, Any
from decimal import Decimal

# In-memory cache (per Lambda container)
_memory_cache: Dict[str, Dict[str, Any]] = {}

class CacheConfig:
    """Cache TTL configuration per data type"""
    TTL_CONFIG = {
        'drs-quotas': 300,           # 5 minutes
        'drs-source-servers': 120,   # 2 minutes
        'ec2-subnets': 3600,         # 60 minutes
        'ec2-security-groups': 3600, # 60 minutes
        'ec2-instance-profiles': 3600, # 60 minutes
        'ec2-instance-types': 86400, # 24 hours
        'drs-accounts': 3600,        # 60 minutes
    }
    
    @classmethod
    def get_ttl(cls, data_type: str) -> int:
        """Get TTL in seconds for data type"""
        return cls.TTL_CONFIG.get(data_type, 300)  # Default 5 minutes


def get_cache_key(data_type: str, region: str, account_id: str = 'global') -> str:
    """Generate cache key"""
    return f"{data_type}#{region}#{account_id}"


def get_from_memory_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get data from in-memory cache"""
    if cache_key not in _memory_cache:
        return None
    
    cached = _memory_cache[cache_key]
    if time.time() > cached['expiresAt']:
        # Expired - remove from cache
        del _memory_cache[cache_key]
        return None
    
    return cached['data']


def set_in_memory_cache(cache_key: str, data: Dict[str, Any], ttl_seconds: int):
    """Store data in in-memory cache"""
    _memory_cache[cache_key] = {
        'data': data,
        'expiresAt': time.time() + ttl_seconds
    }


def get_from_dynamodb_cache(
    dynamodb_client,
    table_name: str,
    cache_key: str
) -> Optional[Dict[str, Any]]:
    """Get data from DynamoDB cache"""
    try:
        response = dynamodb_client.get_item(
            TableName=table_name,
            Key={'cacheKey': {'S': cache_key}}
        )
        
        if 'Item' not in response:
            return None
        
        item = response['Item']
        expires_at = int(item['expiresAt']['N'])
        
        # Check if expired (application-level TTL)
        if time.time() > expires_at:
            return None
        
        # Parse data (handle DynamoDB JSON format)
        data = json.loads(item['data']['S'])
        return data
        
    except Exception as e:
        print(f"Error reading from DynamoDB cache: {e}")
        return None


def set_in_dynamodb_cache(
    dynamodb_client,
    table_name: str,
    cache_key: str,
    data_type: str,
    region: str,
    account_id: str,
    data: Dict[str, Any],
    ttl_seconds: int
):
    """Store data in DynamoDB cache"""
    try:
        now = int(time.time())
        expires_at = now + ttl_seconds
        ttl = expires_at + 3600  # DynamoDB TTL: 1 hour after expiration
        
        dynamodb_client.put_item(
            TableName=table_name,
            Item={
                'cacheKey': {'S': cache_key},
                'dataType': {'S': data_type},
                'region': {'S': region},
                'accountId': {'S': account_id},
                'data': {'S': json.dumps(data)},
                'createdAt': {'N': str(now)},
                'expiresAt': {'N': str(expires_at)},
                'ttl': {'N': str(ttl)}
            }
        )
    except Exception as e:
        print(f"Error writing to DynamoDB cache: {e}")


def get_cached_data(
    dynamodb_client,
    table_name: str,
    data_type: str,
    region: str,
    account_id: str,
    fetch_function: callable
) -> Dict[str, Any]:
    """
    Get data with multi-layer caching
    
    Args:
        dynamodb_client: Boto3 DynamoDB client
        table_name: DynamoDB cache table name
        data_type: Type of data (drs-quotas, ec2-subnets, etc.)
        region: AWS region
        account_id: AWS account ID
        fetch_function: Function to fetch data from AWS API (called on cache miss)
    
    Returns:
        Cached or freshly fetched data
    """
    cache_key = get_cache_key(data_type, region, account_id)
    ttl_seconds = CacheConfig.get_ttl(data_type)
    
    # Layer 1: Check in-memory cache
    data = get_from_memory_cache(cache_key)
    if data is not None:
        print(f"Cache HIT (memory): {cache_key}")
        return data
    
    # Layer 2: Check DynamoDB cache
    data = get_from_dynamodb_cache(dynamodb_client, table_name, cache_key)
    if data is not None:
        print(f"Cache HIT (DynamoDB): {cache_key}")
        # Store in memory cache for next invocation
        set_in_memory_cache(cache_key, data, ttl_seconds)
        return data
    
    # Layer 3: Fetch from AWS API
    print(f"Cache MISS: {cache_key} - fetching from AWS API")
    data = fetch_function()
    
    # Store in both caches
    set_in_dynamodb_cache(
        dynamodb_client,
        table_name,
        cache_key,
        data_type,
        region,
        account_id,
        data,
        ttl_seconds
    )
    set_in_memory_cache(cache_key, data, ttl_seconds)
    
    return data


def invalidate_cache(
    dynamodb_client,
    table_name: str,
    data_type: Optional[str] = None,
    region: Optional[str] = None,
    account_id: Optional[str] = None
):
    """
    Invalidate cache entries
    
    Args:
        dynamodb_client: Boto3 DynamoDB client
        table_name: DynamoDB cache table name
        data_type: Optional data type filter
        region: Optional region filter
        account_id: Optional account ID filter
    """
    # Clear in-memory cache
    global _memory_cache
    if data_type or region or account_id:
        # Selective invalidation
        keys_to_delete = []
        for key in _memory_cache.keys():
            parts = key.split('#')
            if (not data_type or parts[0] == data_type) and \
               (not region or parts[1] == region) and \
               (not account_id or parts[2] == account_id):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del _memory_cache[key]
    else:
        # Clear all
        _memory_cache = {}
    
    # Clear DynamoDB cache (scan and delete)
    # Note: This is expensive for large caches - use sparingly
    try:
        if data_type:
            # Use GSI to query by data type
            response = dynamodb_client.query(
                TableName=table_name,
                IndexName='dataType-createdAt-index',
                KeyConditionExpression='dataType = :dt',
                ExpressionAttributeValues={':dt': {'S': data_type}}
            )
            
            for item in response.get('Items', []):
                cache_key = item['cacheKey']['S']
                dynamodb_client.delete_item(
                    TableName=table_name,
                    Key={'cacheKey': {'S': cache_key}}
                )
        else:
            # Full table scan (expensive - avoid in production)
            print("WARNING: Full cache invalidation - scanning entire table")
            response = dynamodb_client.scan(TableName=table_name)
            for item in response.get('Items', []):
                cache_key = item['cacheKey']['S']
                dynamodb_client.delete_item(
                    TableName=table_name,
                    Key={'cacheKey': {'S': cache_key}}
                )
    except Exception as e:
        print(f"Error invalidating DynamoDB cache: {e}")
```

---

### 2. Update Query Handler to Use Cache

**File**: `lambda/query-handler/index.py`

```python
import os
import boto3
from shared.cache_utils import get_cached_data, invalidate_cache

# Initialize clients
dynamodb_client = boto3.client('dynamodb')
drs_client = boto3.client('drs')
ec2_client = boto3.client('ec2')

# Cache table name from environment
CACHE_TABLE_NAME = os.environ.get('CACHE_TABLE_NAME', 'drs-orchestration-query-cache-dev')

def get_drs_account_capacity(region: str, account_id: str) -> dict:
    """Get DRS capacity with caching"""
    
    def fetch_from_api():
        # Original API call logic
        response = drs_client.describe_source_servers()
        servers = response.get('items', [])
        
        replicating_servers = [
            s for s in servers
            if s.get('dataReplicationInfo', {}).get('dataReplicationState') == 'CONTINUOUS'
        ]
        
        return {
            'accountId': account_id,
            'region': region,
            'replicatingServers': len(replicating_servers),
            'maxReplicatingServers': 300,
            'utilizationPercent': (len(replicating_servers) / 300) * 100
        }
    
    # Use cache
    return get_cached_data(
        dynamodb_client=dynamodb_client,
        table_name=CACHE_TABLE_NAME,
        data_type='drs-quotas',
        region=region,
        account_id=account_id,
        fetch_function=fetch_from_api
    )


def get_ec2_subnets(region: str) -> dict:
    """Get EC2 subnets with caching"""
    
    def fetch_from_api():
        # Original API call logic
        response = ec2_client.describe_subnets()
        subnets = response.get('Subnets', [])
        
        return {
            'subnets': [
                {
                    'subnetId': s['SubnetId'],
                    'vpcId': s['VpcId'],
                    'cidrBlock': s['CidrBlock'],
                    'availabilityZone': s['AvailabilityZone'],
                    'tags': s.get('Tags', [])
                }
                for s in subnets
            ]
        }
    
    # Use cache
    return get_cached_data(
        dynamodb_client=dynamodb_client,
        table_name=CACHE_TABLE_NAME,
        data_type='ec2-subnets',
        region=region,
        account_id='global',  # Subnets are region-wide
        fetch_function=fetch_from_api
    )


def get_ec2_instance_types(region: str) -> dict:
    """Get EC2 instance types with caching (24 hour TTL)"""
    
    def fetch_from_api():
        # Original API call logic
        response = ec2_client.describe_instance_types()
        instance_types = response.get('InstanceTypes', [])
        
        return {
            'instanceTypes': [
                {
                    'instanceType': it['InstanceType'],
                    'vcpus': it['VCpuInfo']['DefaultVCpus'],
                    'memory': it['MemoryInfo']['SizeInMiB'],
                    'networkPerformance': it.get('NetworkInfo', {}).get('NetworkPerformance', 'Unknown')
                }
                for it in instance_types
            ]
        }
    
    # Use cache (24 hour TTL - instance types rarely change)
    return get_cached_data(
        dynamodb_client=dynamodb_client,
        table_name=CACHE_TABLE_NAME,
        data_type='ec2-instance-types',
        region=region,
        account_id='global',
        fetch_function=fetch_from_api
    )


def handle_cache_invalidation(event: dict) -> dict:
    """
    Admin endpoint to invalidate cache
    
    POST /cache/invalidate
    Body: {
        "dataType": "drs-quotas",  # Optional
        "region": "us-east-1",     # Optional
        "accountId": "123456789"   # Optional
    }
    """
    body = json.loads(event.get('body', '{}'))
    
    data_type = body.get('dataType')
    region = body.get('region')
    account_id = body.get('accountId')
    
    invalidate_cache(
        dynamodb_client=dynamodb_client,
        table_name=CACHE_TABLE_NAME,
        data_type=data_type,
        region=region,
        account_id=account_id
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Cache invalidated',
            'dataType': data_type,
            'region': region,
            'accountId': account_id
        })
    }
```

---

### 3. Add Cache Table to CloudFormation

**File**: `cfn/database-stack.yaml`

```yaml
  QueryCacheTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${ProjectName}-query-cache-${Environment}'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: cacheKey
          AttributeType: S
        - AttributeName: dataType
          AttributeType: S
        - AttributeName: createdAt
          AttributeType: N
      KeySchema:
        - AttributeName: cacheKey
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: dataType-createdAt-index
          KeySchema:
            - AttributeName: dataType
              KeyType: HASH
            - AttributeName: createdAt
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
      TimeToLiveSpecification:
        AttributeName: ttl
        Enabled: true
      Tags:
        - Key: Project
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

Outputs:
  QueryCacheTableName:
    Description: Query cache table name
    Value: !Ref QueryCacheTable
    Export:
      Name: !Sub '${AWS::StackName}-QueryCacheTableName'
  
  QueryCacheTableArn:
    Description: Query cache table ARN
    Value: !GetAtt QueryCacheTable.Arn
    Export:
      Name: !Sub '${AWS::StackName}-QueryCacheTableArn'
```

---

### 4. Update Lambda IAM Permissions

**File**: `cfn/lambda-stack.yaml`

Add DynamoDB permissions to Query Handler role:

```yaml
  QueryHandlerCachePolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: QueryHandlerCachePolicy
      Roles:
        - !Ref UnifiedOrchestrationRole
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Action:
              - dynamodb:GetItem
              - dynamodb:PutItem
              - dynamodb:DeleteItem
              - dynamodb:Query
            Resource:
              - !Sub 'arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ProjectName}-query-cache-${Environment}'
              - !Sub 'arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ProjectName}-query-cache-${Environment}/index/*'
```

---

### 5. Add Cache Table Name to Lambda Environment

**File**: `cfn/lambda-stack.yaml`

```yaml
  QueryHandlerFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${ProjectName}-query-handler-${Environment}'
      Runtime: python3.12
      Handler: index.lambda_handler
      Role: !GetAtt UnifiedOrchestrationRole.Arn
      Code:
        S3Bucket: !Ref SourceBucket
        S3Key: lambda/query-handler.zip
      MemorySize: 256
      Timeout: 60
      Environment:
        Variables:
          ENVIRONMENT: !Ref Environment
          CACHE_TABLE_NAME: !Sub '${ProjectName}-query-cache-${Environment}'
          LOG_LEVEL: INFO
```

---

## Performance Impact

### Before Caching

| Endpoint | Response Time | AWS API Calls |
|----------|---------------|---------------|
| GET /drs/quotas | 500ms | 1 (DRS API) |
| GET /ec2/subnets | 300ms | 1 (EC2 API) |
| GET /ec2/instance-types | 600ms | 1 (EC2 API) |

### After Caching (Cache Hit)

| Endpoint | Response Time | AWS API Calls |
|----------|---------------|---------------|
| GET /drs/quotas | 50ms | 0 (DynamoDB read) |
| GET /ec2/subnets | 50ms | 0 (DynamoDB read) |
| GET /ec2/instance-types | 50ms | 0 (DynamoDB read) |

**Improvement**: 83-92% faster response times on cache hits

---

## Cost Analysis

### DynamoDB Cache Table

**Assumptions**:
- 1,000 queries/day
- 80% cache hit rate (800 hits, 200 misses)
- Average item size: 5 KB
- Cache entries: ~100 items (10 data types × 10 regions/accounts)

**Monthly Cost**:
- Storage: 100 items × 5 KB = 0.5 MB = $0.00 (free tier)
- Reads: 800 reads/day × 30 days = 24,000 reads = $0.03
- Writes: 200 writes/day × 30 days = 6,000 writes = $0.01
- **Total**: ~$0.04/month (negligible)

**Savings**:
- Reduced Lambda duration: 200 queries × 450ms saved = 90 seconds/day
- Monthly Lambda savings: 90s × 30 days × $0.0000166667/GB-s × 0.256 GB = $0.12
- **Net Savings**: $0.08/month (plus improved UX)

---

## Cache Invalidation Strategy

### Automatic Invalidation

1. **DynamoDB TTL**: Automatic cleanup after expiration + 1 hour
2. **Application TTL**: Checked on every read (expires_at)
3. **EventBridge Schedule**: Optional periodic refresh (every 5 minutes)

### Manual Invalidation

**Admin Endpoint**: `POST /cache/invalidate`

```bash
# Invalidate all DRS quotas
curl -X POST "${API_ENDPOINT}/cache/invalidate" \
  -H "Authorization: $ID_TOKEN" \
  -d '{"dataType":"drs-quotas"}'

# Invalidate specific region
curl -X POST "${API_ENDPOINT}/cache/invalidate" \
  -H "Authorization: $ID_TOKEN" \
  -d '{"dataType":"drs-quotas","region":"us-east-1"}'

# Invalidate all cache
curl -X POST "${API_ENDPOINT}/cache/invalidate" \
  -H "Authorization: $ID_TOKEN" \
  -d '{}'
```

### Event-Driven Invalidation

Invalidate cache when data changes:

```python
# In Data Management Handler - after creating protection group
from shared.cache_utils import invalidate_cache

def create_protection_group(event):
    # ... create protection group logic ...
    
    # Invalidate DRS source servers cache (servers now in protection group)
    invalidate_cache(
        dynamodb_client=dynamodb_client,
        table_name=CACHE_TABLE_NAME,
        data_type='drs-source-servers',
        region=region,
        account_id=account_id
    )
```

---

## Monitoring

### CloudWatch Metrics

**Custom Metrics**:
- `CacheHitRate` - Percentage of cache hits
- `CacheSize` - Number of items in cache
- `CacheLatency` - Time to read from cache

**Implementation**:
```python
import boto3
cloudwatch = boto3.client('cloudwatch')

def record_cache_hit(data_type: str, hit: bool):
    cloudwatch.put_metric_data(
        Namespace='DROrchestration/QueryCache',
        MetricData=[
            {
                'MetricName': 'CacheHit',
                'Value': 1 if hit else 0,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'DataType', 'Value': data_type}
                ]
            }
        ]
    )
```

### CloudWatch Alarms

```yaml
  CacheHitRateAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub '${ProjectName}-query-cache-hit-rate-low-${Environment}'
      AlarmDescription: Cache hit rate below 70%
      MetricName: CacheHit
      Namespace: DROrchestration/QueryCache
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 0.7
      ComparisonOperator: LessThanThreshold
```

---

## Testing

### Unit Tests

```python
# tests/python/unit/test_cache_utils.py
import pytest
from shared.cache_utils import get_cached_data, CacheConfig

def test_cache_ttl_configuration():
    assert CacheConfig.get_ttl('drs-quotas') == 300
    assert CacheConfig.get_ttl('ec2-instance-types') == 86400
    assert CacheConfig.get_ttl('unknown-type') == 300  # Default

def test_in_memory_cache():
    # Test cache hit/miss logic
    pass

def test_dynamodb_cache():
    # Test with moto
    pass
```

### Integration Tests

```bash
# Test cache hit
curl -X GET "${API_ENDPOINT}/drs/quotas?region=us-east-1"
# Response time: ~500ms (cache miss)

curl -X GET "${API_ENDPOINT}/drs/quotas?region=us-east-1"
# Response time: ~50ms (cache hit)

# Test cache invalidation
curl -X POST "${API_ENDPOINT}/cache/invalidate" \
  -H "Authorization: $ID_TOKEN" \
  -d '{"dataType":"drs-quotas"}'

curl -X GET "${API_ENDPOINT}/drs/quotas?region=us-east-1"
# Response time: ~500ms (cache miss after invalidation)
```

---

## Rollout Plan

### Phase 1: Infrastructure (Week 1)
- [ ] Create DynamoDB cache table
- [ ] Add IAM permissions
- [ ] Deploy cache_utils.py module

### Phase 2: Implementation (Week 2)
- [ ] Update Query Handler to use cache
- [ ] Add cache invalidation endpoint
- [ ] Add CloudWatch metrics

### Phase 3: Testing (Week 3)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Load testing with cache

### Phase 4: Production (Week 4)
- [ ] Deploy to dev environment
- [ ] Monitor cache hit rate
- [ ] Deploy to production

---

## Alternatives Considered

### 1. API Gateway Caching
**Pros**: No code changes, built-in feature  
**Cons**: Only works for API Gateway, not direct Lambda invocations  
**Decision**: Use as Layer 3 (optional) in addition to DynamoDB cache

### 2. ElastiCache Redis
**Pros**: Sub-millisecond latency, advanced features  
**Cons**: Additional cost ($50+/month), VPC complexity  
**Decision**: Overkill for this use case, DynamoDB sufficient

### 3. S3 + CloudFront
**Pros**: Global CDN, very low cost  
**Cons**: Not designed for dynamic data, complex invalidation  
**Decision**: Not suitable for frequently changing data

---

## Related Documentation

- [Query Handler Architecture](api-handler-decomposition.md)
- [Performance Benchmark Results](../performance/benchmark-results-20260124.md)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)

---

**Document Owner**: DR Orchestration Team  
**Review Frequency**: Quarterly  
**Last Updated**: 2026-01-24
