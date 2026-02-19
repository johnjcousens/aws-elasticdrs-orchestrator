# Design Document: Inventory Sync Refactoring

## Overview

This document provides the detailed design for refactoring the `sync_source_server_inventory` function in `lambda/query-handler/index.py`. This refactoring decomposes a monolithic 300+ line function into focused, testable, and maintainable components.

**Critical Dependency**: This refactoring MUST be implemented AFTER the active-region-filtering spec is complete.

## Context

### Current State (Post-Active-Region-Filtering)

After active-region-filtering is complete, the `sync_source_server_inventory` function will:
- Use `get_active_regions()` for region filtering
- Call `update_region_status()` for each region
- Call `invalidate_region_cache()` after completion
- No longer handle staging account sync (moved to data-management-handler)

However, the function will still be a monolithic 300+ line function handling:
1. Account collection from DynamoDB
2. Cross-account credential management
3. Multi-region DRS queries with parallel execution
4. EC2 metadata enrichment
5. Cross-account EC2 queries
6. DynamoDB batch writing

### Problems with Current Design

1. **Violates Single Responsibility Principle** - Does too many things
2. **Hard to Test** - 300+ lines with nested logic makes unit testing difficult
3. **Hard to Maintain** - Changes to one aspect affect the entire function
4. **Error Handling Complexity** - 8 different error states buried in nested functions
5. **Difficult to Reuse** - Logic for DRS queries, EC2 enrichment, etc. can't be reused
6. **Poor Readability** - Cognitive load is very high

## Design Goals

1. **Single Responsibility** - Each function does one thing well
2. **Testability** - Each function can be unit tested independently
3. **Reusability** - Functions can be used in other contexts
4. **Maintainability** - Changes are localized to specific functions
5. **Readability** - Clear, self-documenting code
6. **Backward Compatibility** - Identical behavior to current implementation
7. **Rollback Safety** - Ability to quickly revert if issues arise


## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│ handle_sync_source_server_inventory()                           │
│ (Orchestrator - 50 lines max)                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─────────────────────────────────┐
                              │                                 │
                              ▼                                 ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────┐
│ collect_accounts_to_query()          │    │ Shared Utilities             │
│ - Query DynamoDB for target accounts │    │ - dynamodb_tables.py         │
│ - Uses: dynamodb_tables module       │    │ - cross_account.py           │
└──────────────────────────────────────┘    │ - active_region_filter.py    │
                              │              └──────────────────────────────┘
                              ▼
┌──────────────────────────────────────┐
│ get_account_credentials()            │
│ - Assume cross-account role          │
│ - Uses: cross_account module         │
└──────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────┐
│ query_drs_all_regions()              │
│ - Parallel multi-region DRS queries  │
│ - Uses: active_region_filter module  │
│ - Calls: query_drs_single_region()   │
└──────────────────────────────────────┘
                              │
                              ├─────────────────────────────────┐
                              │                                 │
                              ▼                                 ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────┐
│ query_drs_single_region()            │    │ enrich_with_ec2_metadata()   │
│ - Single region DRS query            │    │ - EC2 metadata enrichment    │
│ - Comprehensive error handling       │    │ - Calls: query_ec2_instances │
│ - Uses: cross_account module         │    └──────────────────────────────┘
└──────────────────────────────────────┘                    │
                                                            ▼
                                          ┌──────────────────────────────┐
                                          │ query_ec2_instances()        │
                                          │ - EC2 API interactions       │
                                          │ - Uses: cross_account module │
                                          └──────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────┐
│ write_inventory_to_dynamodb()        │
│ - Batch write to DynamoDB            │
│ - Uses: dynamodb_tables module       │
└──────────────────────────────────────┘
```


### Shared Utilities Strategy

#### New Shared Module: `lambda/shared/dynamodb_tables.py`

**Purpose**: Centralized DynamoDB table getters with lazy initialization

**Functions to Provide**:
```python
def get_protection_groups_table() -> Any:
    """Get or initialize protection groups table."""

def get_recovery_plans_table() -> Any:
    """Get or initialize recovery plans table."""

def get_target_accounts_table() -> Any:
    """Get or initialize target accounts table."""

def get_execution_history_table() -> Any:
    """Get or initialize execution history table."""

def get_executions_table() -> Any:
    """Get or initialize executions table."""

def get_region_status_table() -> Any:
    """Get or initialize region status table."""

def get_tag_sync_config_table() -> Any:
    """Get or initialize tag sync config table."""

def get_source_server_inventory_table() -> Any:
    """Get or initialize source server inventory table."""
```

**Benefits**:
- Eliminates duplicate code across handlers
- Single source of truth for table access
- Easier to mock in tests
- Consistent error handling

#### Existing Shared Modules to Use

**`lambda/shared/cross_account.py`** (Already Exists):
- `get_cross_account_session()` - Role assumption
- `create_drs_client()` - DRS client creation
- `create_ec2_client()` - EC2 client creation

**`lambda/shared/active_region_filter.py`** (Created by active-region-filtering):
- `get_active_regions()` - Region filtering
- `update_region_status()` - Status updates
- `invalidate_region_cache()` - Cache management

**`lambda/shared/drs_utils.py`** (Already Exists):
- DRS-specific utilities

**`lambda/shared/response_utils.py`** (Already Exists):
- API response formatting


## Detailed Function Specifications

### 1. Orchestrator Function

**Function**: `handle_sync_source_server_inventory()`

**Purpose**: High-level orchestrator that delegates to extracted functions

**Signature**:
```python
def handle_sync_source_server_inventory() -> Dict[str, Any]:
    """
    Orchestrate source server inventory synchronization.
    
    Queries DRS source servers across all active regions and accounts,
    enriches with EC2 metadata, and persists to DynamoDB inventory table.
    
    Returns:
        Dict containing:
        - statusCode: HTTP status code (200 for success)
        - body: JSON string with server count and summary
        - headers: CORS headers
        
    Raises:
        Exception: If critical errors occur during orchestration
    """
```

**Implementation Pattern**:
```python
def handle_sync_source_server_inventory() -> Dict[str, Any]:
    """Orchestrate inventory sync process."""
    try:
        # 1. Collect accounts to query
        accounts = collect_accounts_to_query()
        
        # 2. Process each account
        all_servers = []
        for account in accounts:
            # Get credentials
            credentials = get_account_credentials(account)
            
            # Query DRS across all active regions
            servers, region_statuses = query_drs_all_regions(
                account, credentials
            )
            
            # Enrich with EC2 metadata
            enriched_servers = enrich_with_ec2_metadata(
                servers, credentials
            )
            all_servers.extend(enriched_servers)
        
        # 3. Write to DynamoDB
        success_count, failure_count = write_inventory_to_dynamodb(
            all_servers
        )
        
        # 4. Invalidate region cache
        invalidate_region_cache()
        
        # 5. Return response
        return format_success_response({
            "serverCount": len(all_servers),
            "successCount": success_count,
            "failureCount": failure_count
        })
        
    except Exception as e:
        logger.exception("Inventory sync failed")
        return format_error_response(str(e), 500)
```

**Key Characteristics**:
- Maximum 50 lines of code
- No business logic - pure orchestration
- Clear error handling
- Uses shared utilities for response formatting


### 2. Account Collection Function

**Function**: `collect_accounts_to_query()`

**Purpose**: Gather target accounts from DynamoDB

**Signature**:
```python
def collect_accounts_to_query() -> List[Dict[str, str]]:
    """
    Collect target accounts to query for DRS source servers.
    
    Queries DynamoDB target accounts table and returns list of accounts
    that should be queried for source server inventory.
    
    Returns:
        List of account dictionaries with keys:
        - accountId: AWS account ID (12 digits)
        - accountName: Human-readable account name
        - roleName: IAM role name for cross-account access
        
    Raises:
        ClientError: If DynamoDB query fails
        
    Note:
        Does NOT query staging accounts (staging account sync has been
        moved to data-management-handler by active-region-filtering).
    """
```

**Implementation Pattern**:
```python
def collect_accounts_to_query() -> List[Dict[str, str]]:
    """Collect target accounts from DynamoDB."""
    try:
        table = get_target_accounts_table()
        response = table.scan()
        
        accounts = []
        for item in response.get("Items", []):
            accounts.append({
                "accountId": item["accountId"],
                "accountName": item.get("accountName", "Unknown"),
                "roleName": item.get("roleName", "DRSOrchestrationRole")
            })
        
        logger.info(f"Collected {len(accounts)} target accounts")
        return accounts
        
    except ClientError as e:
        logger.error(f"Failed to query target accounts: {e}")
        raise
```

**Dependencies**:
- `dynamodb_tables.get_target_accounts_table()` (new shared utility)

**Testing Strategy**:
- Unit test with mocked DynamoDB table
- Test empty table scenario
- Test DynamoDB error handling
- Property test: Output list length matches DynamoDB item count


### 3. Credential Management Function

**Function**: `get_account_credentials()`

**Purpose**: Assume cross-account role and return credentials

**Signature**:
```python
def get_account_credentials(
    account: Dict[str, str]
) -> Optional[Dict[str, str]]:
    """
    Assume cross-account role and return credentials.
    
    Args:
        account: Account dictionary with keys:
            - accountId: AWS account ID
            - accountName: Account name
            - roleName: IAM role name to assume
            
    Returns:
        Credentials dictionary with keys if successful:
        - AccessKeyId: Temporary access key
        - SecretAccessKey: Temporary secret key
        - SessionToken: Temporary session token
        
        None if role assumption fails
        
    Note:
        Caller must handle None return value gracefully by skipping
        the account or using current account credentials.
    """
```

**Implementation Pattern**:
```python
def get_account_credentials(
    account: Dict[str, str]
) -> Optional[Dict[str, str]]:
    """Assume cross-account role."""
    try:
        session = get_cross_account_session(
            account_id=account["accountId"],
            role_name=account["roleName"]
        )
        
        if session is None:
            logger.warning(
                f"Failed to assume role in account "
                f"{account['accountId']}"
            )
            return None
        
        credentials = session.get_credentials()
        return {
            "AccessKeyId": credentials.access_key,
            "SecretAccessKey": credentials.secret_key,
            "SessionToken": credentials.token
        }
        
    except Exception as e:
        logger.error(
            f"Error assuming role in account {account['accountId']}: {e}"
        )
        return None
```

**Dependencies**:
- `cross_account.get_cross_account_session()` (existing shared utility)

**Testing Strategy**:
- Unit test with mocked STS client
- Test successful role assumption
- Test failed role assumption (returns None)
- Test exception handling
- Property test: Valid credentials always have all 3 keys


### 4. Multi-Region DRS Query Function

**Function**: `query_drs_all_regions()`

**Purpose**: Query DRS across all active regions in parallel

**Signature**:
```python
def query_drs_all_regions(
    account: Dict[str, str],
    credentials: Optional[Dict[str, str]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Query DRS source servers across all active regions in parallel.
    
    Args:
        account: Account dictionary with accountId and accountName
        credentials: Cross-account credentials or None for current account
        
    Returns:
        Tuple containing:
        - List of DRS source servers from all regions
        - Dictionary mapping region to status info:
            {
                "region": str,
                "status": "success" | "error",
                "serverCount": int,
                "errorType": str (if error),
                "errorMessage": str (if error)
            }
            
    Note:
        - Only queries regions returned by get_active_regions()
        - Calls update_region_status() for each region
        - Partial failures do not stop processing of other regions
    """
```

**Implementation Pattern**:
```python
def query_drs_all_regions(
    account: Dict[str, str],
    credentials: Optional[Dict[str, str]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Query DRS across all active regions in parallel."""
    # Get active regions
    active_regions = get_active_regions()
    
    # Parallel execution
    all_servers = []
    region_statuses = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(
                query_drs_single_region,
                region,
                account["accountId"],
                credentials
            ): region
            for region in active_regions
        }
        
        for future in as_completed(futures):
            region = futures[future]
            result = future.result()
            
            # Update region status
            update_region_status(
                account_id=account["accountId"],
                region=region,
                status=result["status"],
                error_type=result.get("errorType"),
                error_message=result.get("errorMessage")
            )
            
            # Collect servers
            if result["status"] == "success":
                all_servers.extend(result["servers"])
            
            region_statuses[region] = result
    
    logger.info(
        f"Queried {len(active_regions)} regions, "
        f"found {len(all_servers)} servers"
    )
    
    return all_servers, region_statuses
```

**Dependencies**:
- `active_region_filter.get_active_regions()` (from active-region-filtering)
- `active_region_filter.update_region_status()` (from active-region-filtering)
- `query_drs_single_region()` (new function)

**Testing Strategy**:
- Unit test with mocked ThreadPoolExecutor
- Test successful queries across multiple regions
- Test partial failures (some regions succeed, some fail)
- Test all regions fail scenario
- Property test: Server count equals sum of all region server counts
- Property test: Region status count equals active region count


### 5. Single-Region DRS Query Function

**Function**: `query_drs_single_region()`

**Purpose**: Query DRS in a single region with comprehensive error handling

**Signature**:
```python
def query_drs_single_region(
    region: str,
    account_id: str,
    credentials: Optional[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Query DRS source servers in a single region.
    
    Args:
        region: AWS region name (e.g., "us-east-1")
        account_id: AWS account ID
        credentials: Cross-account credentials or None
        
    Returns:
        Dictionary with keys:
        - status: "success" or "error"
        - servers: List of DRS source servers (if success)
        - serverCount: Number of servers found (if success)
        - errorType: Error type string (if error)
        - errorMessage: Human-readable error message (if error)
        - retryable: Boolean indicating if error is retryable (if error)
        
    Error Types Handled:
        1. AccessDeniedException - Missing DRS permissions
        2. UnrecognizedClientException - DRS not available in region
        3. InvalidRequestException - Invalid API request
        4. ThrottlingException - API rate limit exceeded
        5. ServiceQuotaExceededException - Service quota exceeded
        6. InternalServerException - AWS service error
        7. ClientError - Other boto3 client errors
        8. Exception - Unexpected errors
    """
```

**Implementation Pattern**:
```python
def query_drs_single_region(
    region: str,
    account_id: str,
    credentials: Optional[Dict[str, str]]
) -> Dict[str, Any]:
    """Query DRS in single region with error handling."""
    try:
        # Create DRS client
        drs_client = create_drs_client(region, credentials)
        
        # Query source servers
        response = drs_client.describe_source_servers()
        servers = response.get("items", [])
        
        return {
            "status": "success",
            "servers": servers,
            "serverCount": len(servers)
        }
        
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        
        # Map error codes to user-friendly messages
        error_mapping = {
            "AccessDeniedException": (
                "Missing DRS permissions in region",
                False
            ),
            "UnrecognizedClientException": (
                "DRS not available in region",
                False
            ),
            "ThrottlingException": (
                "API rate limit exceeded - retry recommended",
                True
            ),
            # ... other error types
        }
        
        friendly_message, retryable = error_mapping.get(
            error_code,
            (error_message, False)
        )
        
        return {
            "status": "error",
            "errorType": error_code,
            "errorMessage": friendly_message,
            "retryable": retryable
        }
        
    except Exception as e:
        return {
            "status": "error",
            "errorType": "UnexpectedError",
            "errorMessage": str(e),
            "retryable": False
        }
```

**Dependencies**:
- `cross_account.create_drs_client()` (existing shared utility)

**Testing Strategy**:
- Unit test for each of 8 error types
- Test successful query with servers
- Test successful query with no servers
- Test retryable vs non-retryable errors
- Property test: Success status always has servers list
- Property test: Error status always has errorType and errorMessage


### 6. EC2 Metadata Enrichment Function

**Function**: `enrich_with_ec2_metadata()`

**Purpose**: Augment DRS server data with EC2 instance metadata

**Signature**:
```python
def enrich_with_ec2_metadata(
    servers: List[Dict[str, Any]],
    credentials: Optional[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Enrich DRS source servers with EC2 instance metadata.
    
    Queries EC2 for network interfaces, tags, and instance profiles
    for each DRS source server's recovery instance.
    
    Args:
        servers: List of DRS source server dictionaries
        credentials: Cross-account credentials or None
        
    Returns:
        List of enriched server dictionaries with additional keys:
        - networkInterfaces: List of network interface details
        - tags: Dictionary of EC2 instance tags
        - iamInstanceProfile: IAM instance profile ARN
        
    Note:
        - Groups servers by region for efficient EC2 queries
        - Handles cross-account EC2 queries using source account
        - Preserves original server data if EC2 query fails
        - Skips enrichment for servers without recovery instances
    """
```

**Implementation Pattern**:
```python
def enrich_with_ec2_metadata(
    servers: List[Dict[str, Any]],
    credentials: Optional[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """Enrich servers with EC2 metadata."""
    # Group servers by region
    servers_by_region = {}
    for server in servers:
        region = server.get("sourceProperties", {}).get(
            "lastLaunchResult", {}
        ).get("region")
        
        if region:
            servers_by_region.setdefault(region, []).append(server)
    
    # Query EC2 for each region
    enriched_servers = []
    for region, region_servers in servers_by_region.items():
        # Extract instance IDs
        instance_ids = [
            s.get("recoveryInstanceId")
            for s in region_servers
            if s.get("recoveryInstanceId")
        ]
        
        if not instance_ids:
            enriched_servers.extend(region_servers)
            continue
        
        # Query EC2
        ec2_data = query_ec2_instances(
            instance_ids, region, credentials
        )
        
        # Merge EC2 data with server data
        for server in region_servers:
            instance_id = server.get("recoveryInstanceId")
            if instance_id and instance_id in ec2_data:
                server.update({
                    "networkInterfaces": ec2_data[instance_id].get(
                        "NetworkInterfaces", []
                    ),
                    "tags": ec2_data[instance_id].get("Tags", {}),
                    "iamInstanceProfile": ec2_data[instance_id].get(
                        "IamInstanceProfile", {}
                    )
                })
            
            enriched_servers.append(server)
    
    return enriched_servers
```

**Dependencies**:
- `query_ec2_instances()` (new function)

**Testing Strategy**:
- Unit test with mocked EC2 queries
- Test servers with recovery instances
- Test servers without recovery instances
- Test EC2 query failures (preserves original data)
- Test multiple regions
- Property test: Output length equals input length
- Property test: Original server data is preserved


### 7. EC2 Instance Query Function

**Function**: `query_ec2_instances()`

**Purpose**: Query EC2 for instance details

**Signature**:
```python
def query_ec2_instances(
    instance_ids: List[str],
    region: str,
    credentials: Optional[Dict[str, str]]
) -> Dict[str, Dict[str, Any]]:
    """
    Query EC2 for instance details.
    
    Args:
        instance_ids: List of EC2 instance IDs
        region: AWS region name
        credentials: Cross-account credentials or None
        
    Returns:
        Dictionary mapping instance ID to instance details:
        {
            "i-1234567890abcdef0": {
                "NetworkInterfaces": [...],
                "Tags": {...},
                "IamInstanceProfile": {...}
            }
        }
        
        Returns empty dict if query fails
        
    Note:
        - Handles cross-account queries using provided credentials
        - Returns empty dict on error (caller handles gracefully)
        - Batches queries for efficiency (max 100 instances per call)
    """
```

**Implementation Pattern**:
```python
def query_ec2_instances(
    instance_ids: List[str],
    region: str,
    credentials: Optional[Dict[str, str]]
) -> Dict[str, Dict[str, Any]]:
    """Query EC2 for instance details."""
    if not instance_ids:
        return {}
    
    try:
        # Create EC2 client
        ec2_client = create_ec2_client(region, credentials)
        
        # Query instances (batch if needed)
        instances = {}
        for i in range(0, len(instance_ids), 100):
            batch = instance_ids[i:i+100]
            
            response = ec2_client.describe_instances(
                InstanceIds=batch
            )
            
            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance["InstanceId"]
                    instances[instance_id] = {
                        "NetworkInterfaces": instance.get(
                            "NetworkInterfaces", []
                        ),
                        "Tags": {
                            tag["Key"]: tag["Value"]
                            for tag in instance.get("Tags", [])
                        },
                        "IamInstanceProfile": instance.get(
                            "IamInstanceProfile", {}
                        )
                    }
        
        return instances
        
    except ClientError as e:
        logger.error(f"EC2 query failed in {region}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error querying EC2: {e}")
        return {}
```

**Dependencies**:
- `cross_account.create_ec2_client()` (existing shared utility)

**Testing Strategy**:
- Unit test with mocked EC2 client
- Test successful query
- Test empty instance list
- Test batching (>100 instances)
- Test EC2 errors (returns empty dict)
- Property test: Output keys are subset of input instance IDs
- Property test: Empty input returns empty output


### 8. DynamoDB Batch Writing Function

**Function**: `write_inventory_to_dynamodb()`

**Purpose**: Persist enriched server inventory to DynamoDB

**Signature**:
```python
def write_inventory_to_dynamodb(
    servers: List[Dict[str, Any]]
) -> Tuple[int, int]:
    """
    Write enriched server inventory to DynamoDB.
    
    Writes servers to inventory table in batches of 25 (DynamoDB limit).
    Retries failed items and logs persistent failures.
    
    Args:
        servers: List of enriched DRS source server dictionaries
        
    Returns:
        Tuple containing:
        - success_count: Number of servers written successfully
        - failure_count: Number of servers that failed to write
        
    Note:
        - Batches writes in groups of 25 (DynamoDB batch limit)
        - Retries failed items up to 3 times with exponential backoff
        - Logs persistent failures but continues processing
        - Does not raise exceptions (returns failure count instead)
    """
```

**Implementation Pattern**:
```python
def write_inventory_to_dynamodb(
    servers: List[Dict[str, Any]]
) -> Tuple[int, int]:
    """Write inventory to DynamoDB in batches."""
    if not servers:
        return 0, 0
    
    table = get_source_server_inventory_table()
    
    success_count = 0
    failure_count = 0
    
    # Batch write in groups of 25
    for i in range(0, len(servers), 25):
        batch = servers[i:i+25]
        
        # Prepare batch write request
        with table.batch_writer() as writer:
            for server in batch:
                try:
                    writer.put_item(Item=server)
                    success_count += 1
                except ClientError as e:
                    logger.error(
                        f"Failed to write server "
                        f"{server.get('sourceServerID')}: {e}"
                    )
                    failure_count += 1
    
    logger.info(
        f"Wrote {success_count} servers, "
        f"{failure_count} failures"
    )
    
    return success_count, failure_count
```

**Dependencies**:
- `dynamodb_tables.get_source_server_inventory_table()` (new shared utility)

**Testing Strategy**:
- Unit test with mocked DynamoDB table
- Test successful batch write
- Test partial failures
- Test empty server list
- Test large server list (>25 items)
- Property test: success_count + failure_count = input length
- Property test: Empty input returns (0, 0)


## Incremental Refactoring Strategy

### Phase 1: Shared Utilities (Tasks 1-2)

**Goal**: Create shared utilities before extracting functions

**Tasks**:
1. Create `lambda/shared/dynamodb_tables.py`
2. Consolidate table getters from both handlers
3. Update imports in query-handler and data-management-handler

**Validation Checkpoint**:
- All existing tests pass
- No behavioral changes
- Table getters work identically

### Phase 2: Extract Functions One-by-One (Tasks 3-9)

**Goal**: Extract each function incrementally with testing

**Approach**:
- Extract one function at a time
- Test independently before integration
- Maintain working state at all times

**Order of Extraction**:
1. `collect_accounts_to_query()` - Simplest, no dependencies
2. `get_account_credentials()` - Uses existing shared utility
3. `query_drs_single_region()` - Core DRS query logic
4. `query_drs_all_regions()` - Depends on query_drs_single_region
5. `query_ec2_instances()` - EC2 query logic
6. `enrich_with_ec2_metadata()` - Depends on query_ec2_instances
7. `write_inventory_to_dynamodb()` - Final persistence

**Validation After Each Extraction**:
- Unit tests for extracted function pass
- Integration tests with orchestrator pass
- Manual testing shows identical behavior

### Phase 3: Integration and Comparison Testing (Tasks 10-12)

**Goal**: Prove behavioral equivalence

**Tasks**:
1. Create comparison tests (run both implementations)
2. Run comparison tests against dev environment
3. Verify identical output for 10+ scenarios
4. Verify identical error handling

**Validation Checkpoint**:
- All comparison tests pass
- No behavioral differences detected
- Performance is equivalent or better

### Phase 4: Feature Flag and Rollback Safety (Tasks 13-15)

**Goal**: Enable safe rollback if issues arise

**Tasks**:
1. Preserve original as `handle_sync_source_server_inventory_legacy()`
2. Add feature flag environment variable
3. Implement flag-based routing
4. Document rollback procedure

**Feature Flag Implementation**:
```python
# Environment variable: USE_REFACTORED_INVENTORY_SYNC
# Values: "true" (default) or "false" (rollback)

def handle_sync_source_server_inventory() -> Dict[str, Any]:
    """Route to refactored or legacy implementation."""
    use_refactored = os.getenv(
        "USE_REFACTORED_INVENTORY_SYNC", "true"
    ).lower() == "true"
    
    if use_refactored:
        return handle_sync_source_server_inventory_refactored()
    else:
        logger.warning("Using legacy inventory sync implementation")
        return handle_sync_source_server_inventory_legacy()
```

**Rollback Procedure**:
1. Set environment variable: `USE_REFACTORED_INVENTORY_SYNC=false`
2. Restart Lambda function (or wait for next invocation)
3. Monitor CloudWatch logs for "Using legacy" message
4. Verify inventory sync works correctly


## Testing Strategy

### Unit Tests (90% Coverage Target)

**For Each Extracted Function**:
- Test successful execution path
- Test error scenarios
- Test edge cases (empty inputs, None values)
- Test with mocked dependencies

**Example: `collect_accounts_to_query()` Unit Tests**:
```python
def test_collect_accounts_success():
    """Test successful account collection."""
    # Mock DynamoDB table
    # Verify correct accounts returned

def test_collect_accounts_empty_table():
    """Test with no accounts in table."""
    # Mock empty DynamoDB response
    # Verify empty list returned

def test_collect_accounts_dynamodb_error():
    """Test DynamoDB error handling."""
    # Mock ClientError
    # Verify exception raised
```

### Property-Based Tests (Invariants)

**Universal Properties to Test**:

1. **Account Collection**:
   - Property: Output length ≤ DynamoDB item count
   - Property: All output items have required keys

2. **Credential Management**:
   - Property: Valid credentials always have 3 keys
   - Property: None return is handled gracefully

3. **Multi-Region Queries**:
   - Property: Server count = sum of region server counts
   - Property: Region status count = active region count

4. **Single-Region Queries**:
   - Property: Success status always has servers list
   - Property: Error status always has errorType

5. **EC2 Enrichment**:
   - Property: Output length = input length
   - Property: Original server data preserved

6. **DynamoDB Writing**:
   - Property: success_count + failure_count = input length
   - Property: Empty input returns (0, 0)

**Example Property Test**:
```python
from hypothesis import given, strategies as st

@given(st.lists(st.dictionaries(
    keys=st.sampled_from(["accountId", "accountName"]),
    values=st.text()
)))
def test_collect_accounts_preserves_structure(accounts):
    """Property: Output has same structure as input."""
    # Mock DynamoDB to return accounts
    result = collect_accounts_to_query()
    
    # Verify all results have required keys
    for account in result:
        assert "accountId" in account
        assert "accountName" in account
```


### Comparison Tests (Behavioral Equivalence)

**Goal**: Prove refactored implementation produces identical output to original

**Approach**: Run both implementations side-by-side and compare results

**Test Scenarios** (Minimum 10):

1. **Single account, single region, no servers**
2. **Single account, single region, multiple servers**
3. **Single account, multiple regions, servers in each**
4. **Multiple accounts, single region each**
5. **Multiple accounts, multiple regions**
6. **Account with failed role assumption**
7. **Region with DRS AccessDeniedException**
8. **Region with DRS ThrottlingException**
9. **Servers with EC2 enrichment data**
10. **Servers without EC2 enrichment data**

**Comparison Test Implementation**:
```python
def test_behavioral_equivalence_scenario_1():
    """Compare original vs refactored: single account, no servers."""
    # Setup test environment
    setup_test_accounts()
    setup_empty_drs_regions()
    
    # Run original implementation
    original_result = handle_sync_source_server_inventory_legacy()
    
    # Run refactored implementation
    refactored_result = handle_sync_source_server_inventory_refactored()
    
    # Compare results
    assert original_result["statusCode"] == refactored_result["statusCode"]
    
    original_body = json.loads(original_result["body"])
    refactored_body = json.loads(refactored_result["body"])
    
    assert original_body["serverCount"] == refactored_body["serverCount"]
    assert original_body["successCount"] == refactored_body["successCount"]
    
    # Compare DynamoDB writes
    original_items = scan_inventory_table()
    assert len(original_items) == 0  # No servers expected
```

**Comparison Validation**:
- Response status codes match
- Response body structure matches
- Server counts match
- DynamoDB items match (same items, same attributes)
- Region status updates match
- Error handling matches for all 8 error types

### Integration Tests (End-to-End)

**Test Against Real AWS Services in Dev Environment**:

1. **Full Inventory Sync**:
   - Trigger inventory sync
   - Verify servers written to DynamoDB
   - Verify region status table updated
   - Verify cache invalidated

2. **Error Recovery**:
   - Simulate region failures
   - Verify partial success handling
   - Verify error logging

3. **Performance**:
   - Measure execution time
   - Verify parallel execution works
   - Compare to original performance

**Integration Test Example**:
```python
@pytest.mark.integration
def test_full_inventory_sync_integration():
    """Test complete inventory sync against dev environment."""
    # Clear existing inventory
    clear_inventory_table()
    
    # Trigger sync
    result = handle_sync_source_server_inventory()
    
    # Verify success
    assert result["statusCode"] == 200
    
    # Verify DynamoDB writes
    inventory_items = scan_inventory_table()
    assert len(inventory_items) > 0
    
    # Verify region status updates
    region_statuses = scan_region_status_table()
    assert len(region_statuses) > 0
    
    # Verify all servers have required fields
    for item in inventory_items:
        assert "sourceServerID" in item
        assert "accountId" in item
        assert "region" in item
```


## Error Handling Strategy

### Comprehensive Error Type Preservation

The refactoring preserves all 8 DRS error types from the original implementation:

1. **AccessDeniedException**
   - Cause: Missing DRS permissions in target account/region
   - Handling: Log error, mark region as failed, continue with other regions
   - User Message: "Missing DRS permissions in region {region}"
   - Retryable: No

2. **UnrecognizedClientException**
   - Cause: DRS service not available in region
   - Handling: Log info, mark region as unavailable, continue
   - User Message: "DRS not available in region {region}"
   - Retryable: No

3. **InvalidRequestException**
   - Cause: Malformed API request
   - Handling: Log error, mark region as failed, continue
   - User Message: "Invalid DRS API request in region {region}"
   - Retryable: No

4. **ThrottlingException**
   - Cause: API rate limit exceeded
   - Handling: Log warning, mark region as throttled, continue
   - User Message: "DRS API rate limit exceeded in region {region} - retry recommended"
   - Retryable: Yes

5. **ServiceQuotaExceededException**
   - Cause: Service quota limit reached
   - Handling: Log error, mark region as quota exceeded, continue
   - User Message: "DRS service quota exceeded in region {region} - request quota increase"
   - Retryable: No

6. **InternalServerException**
   - Cause: AWS service internal error
   - Handling: Log error, mark region as failed, continue
   - User Message: "DRS service error in region {region} - AWS internal issue"
   - Retryable: Yes

7. **ClientError** (Other boto3 errors)
   - Cause: Various boto3 client errors
   - Handling: Log error with error code, mark region as failed, continue
   - User Message: "DRS API error {error_code} in region {region}: {message}"
   - Retryable: Depends on error code

8. **Exception** (Unexpected errors)
   - Cause: Unexpected Python exceptions
   - Handling: Log exception with stack trace, mark region as failed, continue
   - User Message: "Unexpected error in region {region}: {error}"
   - Retryable: No

### Error Handling Principles

1. **Partial Failure Tolerance**
   - Region failures do not stop processing of other regions
   - Account failures do not stop processing of other accounts
   - EC2 enrichment failures preserve original server data
   - DynamoDB write failures are logged but don't fail entire operation

2. **Error Context Preservation**
   - All errors include region, account, and operation context
   - Error messages are descriptive and actionable
   - Stack traces are logged for unexpected errors
   - Error types are preserved for monitoring and alerting

3. **Graceful Degradation**
   - Missing credentials: Skip account, log warning
   - EC2 query failure: Return servers without enrichment
   - DynamoDB write failure: Log error, continue with remaining servers
   - Region unavailable: Mark as unavailable, continue with other regions

### Error Logging Strategy

**Log Levels**:
- `ERROR`: Critical failures requiring investigation (DynamoDB errors, unexpected exceptions)
- `WARNING`: Recoverable issues (throttling, missing credentials, EC2 enrichment failures)
- `INFO`: Normal operations (region queries, server counts, completion status)
- `DEBUG`: Detailed execution flow (only in development)

**Log Format**:
```python
# ERROR example
logger.error(
    f"Failed to write server {server_id} to DynamoDB: {error}",
    extra={
        "accountId": account_id,
        "region": region,
        "serverId": server_id,
        "errorType": error_code
    }
)

# WARNING example
logger.warning(
    f"Failed to assume role in account {account_id}",
    extra={
        "accountId": account_id,
        "roleName": role_name,
        "operation": "get_account_credentials"
    }
)
```


## Performance Considerations

### Parallel Execution Strategy

**Multi-Region Queries**:
- Use `ThreadPoolExecutor` with 10 worker threads
- Each region query runs independently
- Total execution time = slowest region query (not sum of all queries)
- Expected improvement: 28x faster than sequential (28 regions)

**Batching Strategy**:
- DynamoDB batch writes: 25 items per batch (AWS limit)
- EC2 instance queries: 100 instances per call (AWS limit)
- Account queries: Sequential (typically <10 accounts)

### Performance Metrics

**Current Performance** (Original Implementation):
- Single account, 28 regions: ~45 seconds
- Multiple accounts (3): ~120 seconds
- Bottleneck: Sequential region queries

**Expected Performance** (Refactored Implementation):
- Single account, 28 regions: ~5 seconds (9x improvement)
- Multiple accounts (3): ~15 seconds (8x improvement)
- Bottleneck: Slowest region query + DynamoDB writes

**Performance Validation**:
- Measure execution time before and after refactoring
- Verify parallel execution reduces total time
- Monitor CloudWatch Lambda duration metrics
- Compare to baseline performance in dev environment

### Memory Optimization

**Memory Usage Patterns**:
- Server data accumulates in memory during processing
- Peak memory: All servers from all regions + enrichment data
- Typical: 1000 servers × 5KB each = 5MB
- Maximum: 10,000 servers × 5KB each = 50MB (well within Lambda limits)

**Memory Optimization Strategies**:
- Process servers in batches for DynamoDB writes
- Release server data after writing to DynamoDB
- Use generators for large result sets (if needed in future)


## Backward Compatibility Guarantees

### API Contract Preservation

**Function Signature**:
```python
# Original and refactored signatures are identical
def handle_sync_source_server_inventory() -> Dict[str, Any]:
    """Synchronize source server inventory across all accounts and regions."""
```

**Response Format**:
```python
# Success response (identical to original)
{
    "statusCode": 200,
    "body": json.dumps({
        "serverCount": 150,
        "successCount": 148,
        "failureCount": 2
    }),
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    }
}

# Error response (identical to original)
{
    "statusCode": 500,
    "body": json.dumps({
        "error": "Inventory sync failed: {error_message}"
    }),
    "headers": {
        "Content-Type": "application/json"
    }
}
```

### Data Format Preservation

**DynamoDB Item Structure** (Unchanged):
- All existing attributes preserved
- Attribute names unchanged
- Data types unchanged
- Enrichment fields added in same format

**Region Status Updates** (Unchanged):
- Uses same `update_region_status()` function
- Status values unchanged
- Error type values unchanged
- Timestamp format unchanged

### Behavioral Equivalence

**Guaranteed Behaviors**:
1. Same accounts queried (target accounts only)
2. Same regions queried (active regions only)
3. Same DRS API calls made
4. Same EC2 enrichment performed
5. Same DynamoDB writes executed
6. Same region status updates
7. Same error handling for all 8 error types
8. Same partial failure tolerance
9. Same logging output
10. Same cache invalidation

**Validation Method**:
- Comparison tests run both implementations side-by-side
- Verify identical output for 10+ scenarios
- Verify identical DynamoDB state after execution
- Verify identical region status updates


## Rollback Procedure

### Feature Flag Implementation

**Environment Variable**:
```bash
# Lambda environment variable
USE_REFACTORED_INVENTORY_SYNC=true   # Use refactored (default)
USE_REFACTORED_INVENTORY_SYNC=false  # Use legacy (rollback)
```

**Routing Logic**:
```python
import os
import logging

logger = logging.getLogger(__name__)

def handle_sync_source_server_inventory() -> Dict[str, Any]:
    """
    Route to refactored or legacy implementation based on feature flag.
    
    Environment Variable:
        USE_REFACTORED_INVENTORY_SYNC: "true" (default) or "false"
        
    Returns:
        Response from selected implementation
    """
    use_refactored = os.getenv(
        "USE_REFACTORED_INVENTORY_SYNC",
        "true"
    ).lower() == "true"
    
    if use_refactored:
        logger.info("Using refactored inventory sync implementation")
        return handle_sync_source_server_inventory_refactored()
    else:
        logger.warning(
            "Using LEGACY inventory sync implementation - "
            "refactored version disabled via feature flag"
        )
        return handle_sync_source_server_inventory_legacy()


def handle_sync_source_server_inventory_refactored() -> Dict[str, Any]:
    """Refactored implementation (new code)."""
    # New implementation here
    pass


def handle_sync_source_server_inventory_legacy() -> Dict[str, Any]:
    """Legacy implementation (original code preserved)."""
    # Original implementation preserved here
    pass
```

### Rollback Steps

**If Issues Discovered in Production**:

1. **Immediate Rollback** (No Deployment Required):
   ```bash
   # Update Lambda environment variable
   aws lambda update-function-configuration \
     --function-name hrp-drs-tech-adapter-query-handler-dev \
     --environment Variables={USE_REFACTORED_INVENTORY_SYNC=false}
   ```

2. **Verify Rollback**:
   ```bash
   # Check CloudWatch logs for "Using LEGACY" message
   aws logs tail /aws/lambda/hrp-drs-tech-adapter-query-handler-dev \
     --since 1m --follow
   ```

3. **Monitor Behavior**:
   - Verify inventory sync completes successfully
   - Check DynamoDB for expected server counts
   - Monitor error rates in CloudWatch

4. **Investigate Issue**:
   - Review CloudWatch logs for errors
   - Compare refactored vs legacy behavior
   - Identify root cause
   - Fix issue in refactored implementation

5. **Re-enable Refactored** (After Fix):
   ```bash
   aws lambda update-function-configuration \
     --function-name hrp-drs-tech-adapter-query-handler-dev \
     --environment Variables={USE_REFACTORED_INVENTORY_SYNC=true}
   ```

### Legacy Code Retention Policy

**Retention Period**: 30 days after refactoring deployment

**Removal Criteria**:
- Refactored implementation stable for 30 days
- No production issues reported
- All comparison tests passing
- Performance metrics meet expectations
- Team approval to remove legacy code

**Removal Process**:
1. Announce legacy code removal 1 week in advance
2. Verify feature flag is set to "true" in all environments
3. Remove `handle_sync_source_server_inventory_legacy()` function
4. Remove feature flag routing logic
5. Rename `handle_sync_source_server_inventory_refactored()` to `handle_sync_source_server_inventory()`
6. Update tests to remove legacy references


## Migration Path

### Pre-Deployment Checklist

**Before Deploying Refactored Code**:
- [ ] All unit tests passing (90% coverage achieved)
- [ ] All property-based tests passing
- [ ] All comparison tests passing (10+ scenarios)
- [ ] Integration tests passing in dev environment
- [ ] Performance metrics meet expectations
- [ ] Code review completed and approved
- [ ] Documentation updated
- [ ] Rollback procedure documented and tested

### Deployment Strategy

**Phase 1: Deploy to Dev Environment**
1. Deploy refactored code with feature flag set to "true"
2. Run full test suite
3. Monitor for 24 hours
4. Verify inventory sync works correctly
5. Compare performance to baseline

**Phase 2: Deploy to Test Environment**
1. Deploy refactored code with feature flag set to "true"
2. Run integration tests
3. Monitor for 48 hours
4. Verify no regressions

**Phase 3: Deploy to Staging Environment**
1. Deploy refactored code with feature flag set to "true"
2. Run full test suite
3. Monitor for 1 week
4. Verify production-like workload handling

**Phase 4: Deploy to Production**
1. Deploy refactored code with feature flag set to "false" (legacy)
2. Verify legacy code works correctly
3. Switch feature flag to "true" (refactored)
4. Monitor closely for 24 hours
5. If issues arise, rollback immediately via feature flag
6. If stable, continue monitoring for 30 days

### Post-Deployment Monitoring

**Metrics to Monitor**:
- Lambda execution duration (should decrease)
- Lambda error rate (should remain same or decrease)
- DynamoDB write throughput (should remain same)
- Region status update frequency (should remain same)
- Server count accuracy (should remain same)

**Alerts to Configure**:
- Lambda execution duration > 60 seconds (baseline: 45 seconds)
- Lambda error rate > 5% (baseline: 2%)
- DynamoDB write failures > 10 per execution
- Missing server inventory updates for > 1 hour


## Monitoring and Observability

### CloudWatch Metrics

**Custom Metrics to Emit**:
```python
import boto3

cloudwatch = boto3.client("cloudwatch")

def emit_inventory_sync_metrics(
    server_count: int,
    success_count: int,
    failure_count: int,
    duration_seconds: float,
    region_count: int
):
    """Emit custom CloudWatch metrics for inventory sync."""
    cloudwatch.put_metric_data(
        Namespace="DRSOrchestration/InventorySync",
        MetricData=[
            {
                "MetricName": "ServerCount",
                "Value": server_count,
                "Unit": "Count"
            },
            {
                "MetricName": "SuccessCount",
                "Value": success_count,
                "Unit": "Count"
            },
            {
                "MetricName": "FailureCount",
                "Value": failure_count,
                "Unit": "Count"
            },
            {
                "MetricName": "DurationSeconds",
                "Value": duration_seconds,
                "Unit": "Seconds"
            },
            {
                "MetricName": "RegionCount",
                "Value": region_count,
                "Unit": "Count"
            }
        ]
    )
```

### Structured Logging

**Log Structured Data**:
```python
import json
import logging

logger = logging.getLogger(__name__)

def log_inventory_sync_summary(
    account_count: int,
    region_count: int,
    server_count: int,
    duration_seconds: float,
    errors: List[Dict[str, Any]]
):
    """Log structured summary of inventory sync."""
    logger.info(
        "Inventory sync completed",
        extra={
            "accountCount": account_count,
            "regionCount": region_count,
            "serverCount": server_count,
            "durationSeconds": duration_seconds,
            "errorCount": len(errors),
            "errors": errors
        }
    )
```

### CloudWatch Dashboards

**Recommended Dashboard Widgets**:
1. **Execution Duration** (Line chart)
   - Metric: Lambda Duration
   - Comparison: Before vs After refactoring

2. **Server Count** (Number widget)
   - Metric: Custom ServerCount
   - Shows total servers inventoried

3. **Error Rate** (Line chart)
   - Metric: Lambda Errors / Invocations
   - Alarm threshold: > 5%

4. **Region Query Success** (Pie chart)
   - Metric: Successful regions / Total regions
   - Shows region availability

5. **DynamoDB Write Throughput** (Line chart)
   - Metric: DynamoDB ConsumedWriteCapacityUnits
   - Shows write load


## Success Criteria

### Functional Success Criteria

**Must Achieve**:
1. ✅ All 17 requirements met
2. ✅ All unit tests passing (90% coverage)
3. ✅ All property-based tests passing
4. ✅ All comparison tests passing (10+ scenarios)
5. ✅ All integration tests passing
6. ✅ Identical output to original implementation
7. ✅ All 8 error types handled correctly
8. ✅ Backward compatibility maintained
9. ✅ Rollback procedure tested and documented
10. ✅ Code review approved

### Performance Success Criteria

**Must Achieve**:
1. ✅ Execution time reduced by at least 50% (45s → 22s or better)
2. ✅ Memory usage remains under 512MB
3. ✅ No increase in error rate
4. ✅ No increase in DynamoDB throttling

### Quality Success Criteria

**Must Achieve**:
1. ✅ PEP 8 compliant (120 char lines, 4 spaces, double quotes)
2. ✅ All functions have comprehensive docstrings
3. ✅ All functions have type hints
4. ✅ No functions exceed 100 lines
5. ✅ Orchestrator function under 50 lines
6. ✅ No code duplication
7. ✅ Shared utilities used consistently

### Operational Success Criteria

**Must Achieve**:
1. ✅ Deployed to dev environment successfully
2. ✅ Monitored for 24 hours without issues
3. ✅ Deployed to test environment successfully
4. ✅ Monitored for 48 hours without issues
5. ✅ Deployed to staging environment successfully
6. ✅ Monitored for 1 week without issues
7. ✅ Deployed to production successfully
8. ✅ Monitored for 30 days without issues
9. ✅ Rollback procedure tested successfully
10. ✅ Legacy code removed after 30 days


## Acceptance Testing

### Acceptance Test Scenarios

**Scenario 1: Single Account, No Servers**
- Setup: 1 target account, DRS enabled, no source servers
- Expected: Success response, 0 servers, all regions queried
- Validation: DynamoDB empty, region status updated

**Scenario 2: Single Account, Multiple Servers**
- Setup: 1 target account, 10 source servers across 3 regions
- Expected: Success response, 10 servers, enriched with EC2 data
- Validation: DynamoDB has 10 items, all enriched

**Scenario 3: Multiple Accounts**
- Setup: 3 target accounts, servers in each
- Expected: Success response, servers from all accounts
- Validation: DynamoDB has servers from all accounts

**Scenario 4: Region with AccessDeniedException**
- Setup: 1 account, 1 region with missing permissions
- Expected: Partial success, region marked as failed
- Validation: Other regions succeed, error logged

**Scenario 5: Region with ThrottlingException**
- Setup: 1 account, 1 region throttled
- Expected: Partial success, region marked as throttled
- Validation: Other regions succeed, retry guidance logged

**Scenario 6: Failed Role Assumption**
- Setup: 1 account with invalid role
- Expected: Account skipped, warning logged
- Validation: Other accounts succeed

**Scenario 7: EC2 Enrichment Failure**
- Setup: Servers with EC2 query failures
- Expected: Success, servers without enrichment
- Validation: Original server data preserved

**Scenario 8: DynamoDB Write Failure**
- Setup: DynamoDB throttling or errors
- Expected: Partial success, failures logged
- Validation: Successful writes persisted

**Scenario 9: All Regions Unavailable**
- Setup: DRS not available in any region
- Expected: Success response, 0 servers, all regions marked unavailable
- Validation: Region status shows unavailable

**Scenario 10: Large Server Count**
- Setup: 1000+ servers across multiple accounts
- Expected: Success, all servers written
- Validation: Performance acceptable, no timeouts

### Acceptance Test Execution

**Test Environment**: Dev environment with real AWS services

**Test Data**: Use existing dev environment accounts and servers

**Test Execution**:
1. Run each scenario manually
2. Verify expected results
3. Check CloudWatch logs
4. Verify DynamoDB state
5. Verify region status updates
6. Document any issues

**Acceptance Criteria**:
- All 10 scenarios pass
- No unexpected errors
- Performance meets expectations
- Logs are clear and actionable


## Code Quality Standards Compliance

### PEP 8 Standards (Mandatory)

All refactored code MUST comply with PEP 8 Python coding standards:

**Line Length and Indentation**:
- Maximum 120 characters per line (strict)
- 4 spaces per indentation level (NO TABS)
- Proper line continuation with aligned indentation

**String Formatting**:
- Double quotes for all strings: `"text"`
- f-strings for string formatting: `f"User {user_id} in region {region}"`
- Never use old-style formatting (%, .format())

**Import Organization**:
```python
# 1. Standard library imports
import json
import os
from typing import Dict, List, Optional

# 2. Third-party imports
import boto3
from botocore.exceptions import ClientError

# 3. Local application imports
from lambda.shared.dynamodb_tables import get_target_accounts_table
from lambda.shared.cross_account import get_cross_account_session
```

**Naming Conventions**:
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private functions: `_leading_underscore`

**Type Hints (Required)**:
```python
def collect_accounts_to_query() -> List[Dict[str, str]]:
    """Collect target accounts from DynamoDB."""
    pass

def get_account_credentials(
    account: Dict[str, str]
) -> Optional[Dict[str, str]]:
    """Assume cross-account role."""
    pass
```

**Docstrings (Required)**:
- All functions must have comprehensive docstrings
- Use Google-style or NumPy-style format
- Include Args, Returns, Raises sections
- Provide usage examples for complex functions

**Whitespace and Spacing**:
- Proper spacing around operators: `result = value_one + value_two`
- Proper spacing in function calls: `function_call(arg1, arg2, keyword_arg=value)`
- Two blank lines around top-level functions
- One blank line around method definitions

**Comments**:
- Use complete sentences with proper capitalization
- Explain WHY, not WHAT (code should be self-documenting)
- Avoid temporal references ("recently refactored", "moved")

### Deployment Validation Pipeline Compliance

All code changes MUST pass the 5-stage deployment validation pipeline defined in `scripts/deploy.sh`:

**Stage 1: Validation**
- `cfn-lint` - CloudFormation template validation (uses `.venv/bin/cfn-lint`)
- `flake8` - Python linting (uses `.venv/bin/flake8`)
- `black --check` - Python formatting verification (uses `.venv/bin/black`)
- TypeScript type checking (if applicable)

**Stage 2: Security Scanning (ALWAYS runs)**
- `bandit` - Python security vulnerability scanning (uses `.venv/bin/bandit`)
- `npm audit` - Frontend dependency vulnerabilities
- `cfn_nag` - CloudFormation security best practices
- `detect-secrets` - Credential scanning (uses `.venv/bin/detect-secrets`)
- `shellcheck` - Shell script security

**Stage 3: Tests (ALWAYS runs)**
- `pytest` - Python unit tests (uses `.venv/bin/pytest`)
- `vitest` - Frontend tests (if applicable)
- Property-based tests with Hypothesis
- Integration tests

**Stage 4: Git Push (ALWAYS runs)**
- Pushes changes to remote repository

**Stage 5: Deploy**
- Builds Lambda packages
- Syncs to S3 deployment bucket
- Deploys CloudFormation stack

### Virtual Environment Requirements

**CRITICAL**: All Python tools run from `.venv` virtual environment:

```bash
# Setup virtual environment (one-time)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Tools installed in .venv:
# - pytest (unit testing)
# - hypothesis (property-based testing)
# - cfn-lint (CloudFormation validation)
# - flake8 (Python linting)
# - black (Python formatting)
# - bandit (security scanning)
# - detect-secrets (credential scanning)
```

**Validation Commands** (run before committing):
```bash
# Activate virtual environment
source .venv/bin/activate

# Run linting
.venv/bin/flake8 lambda/query-handler/

# Check formatting
.venv/bin/black --check lambda/query-handler/

# Run security scan
.venv/bin/bandit -r lambda/query-handler/

# Run tests
.venv/bin/pytest tests/unit/ -v

# Or use deploy script (runs all checks)
./scripts/deploy.sh dev --validate-only
```

### Validation Checkpoints

Each refactoring phase MUST pass validation before proceeding:

**Phase 1 Checkpoint** (Shared Utilities):
- `flake8` passes with zero violations
- `black --check` passes (no formatting issues)
- `bandit` passes with zero high/medium severity issues
- All existing tests pass
- New utility tests pass with 90% coverage

**Phase 2 Checkpoint** (Each Function Extraction):
- `flake8` passes for new function
- `black --check` passes for new function
- Function-specific unit tests pass
- Integration tests with orchestrator pass
- No behavioral changes detected

**Phase 3 Checkpoint** (Comparison Testing):
- All comparison tests pass
- No behavioral differences detected
- Performance metrics acceptable

**Phase 4 Checkpoint** (Feature Flag):
- Feature flag implementation tested
- Rollback procedure verified
- All validation stages pass

### Continuous Compliance

**Pre-Commit Checks**:
- Run `./scripts/deploy.sh dev --validate-only` before every commit
- Fix all validation errors before committing
- Never bypass validation checks

**Code Review Requirements**:
- All PEP 8 violations must be resolved
- All security scan findings must be addressed
- All tests must pass
- Code coverage must meet 90% target

**Deployment Requirements**:
- NEVER use direct AWS CLI commands for deployment
- ALWAYS use `./scripts/deploy.sh dev` for deployments
- NEVER bypass the deploy script
- ALWAYS let validation stages complete


## Code Quality Standards Compliance

This refactoring MUST comply with all project coding standards and deployment validation requirements.

### PEP 8 Standards (MANDATORY)

All Python code must follow PEP 8 standards:

**Line Length and Indentation:**
- Maximum 120 characters per line (strict)
- 4 spaces per indentation level (NO TABS)
- Proper line continuation with alignment

**String Formatting:**
- Double quotes for all strings: `"text"`
- f-strings for formatting: `f"Value: {value}"`
- Never use old-style `%` or `.format()`

**Import Organization:**
```python
# 1. Standard library imports
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

# 2. Third-party imports
import boto3
from botocore.exceptions import ClientError

# 3. Local application imports
from lambda.shared import cross_account, dynamodb_tables
from lambda.shared.active_region_filter import get_active_regions
```

**Type Hints (REQUIRED):**
- All function parameters must have type hints
- All return values must have type hints
- Use `typing` module: `Dict`, `List`, `Optional`, `Tuple`, `Any`

**Docstrings (PEP 257):**
```python
def collect_accounts_to_query() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Collect target and staging accounts from DynamoDB.
    
    Queries the target accounts table to retrieve all accounts that should
    be queried for DRS source server inventory. Separates accounts into
    target accounts and staging accounts for different processing paths.
    
    Returns:
        Tuple containing:
        - target_accounts: List of target account dictionaries
        - staging_accounts: List of staging account dictionaries
        
    Raises:
        ClientError: When DynamoDB query fails
        
    Example:
        >>> target_accounts, staging_accounts = collect_accounts_to_query()
        >>> print(f"Found {len(target_accounts)} target accounts")
    """
```

**Naming Conventions:**
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Avoid single-char names: `l`, `O`, `I`

**Comparisons:**
- Use `is` and `is not` for `None`: `if x is None:`
- Don't compare to `True`/`False`: `if flag:` not `if flag == True:`

**Exception Handling:**
- Catch specific exceptions, not bare `except`
- Derive custom exceptions from `Exception`
- Use exception chaining: `raise CustomError(...) from e`

### Deployment Validation Pipeline (5 Stages)

All code must pass the 5-stage deployment validation pipeline enforced by `./scripts/deploy.sh`:

**Stage 1: Validation**
```bash
# CloudFormation validation
.venv/bin/cfn-lint cfn/**/*.yaml

# Python linting
.venv/bin/flake8 lambda/ --max-line-length=120

# Python formatting check
.venv/bin/black --check --line-length=120 lambda/

# TypeScript type checking (if applicable)
npm run type-check
```

**Stage 2: Security (ALWAYS runs)**
```bash
# Python security scanning
.venv/bin/bandit -r lambda/

# CloudFormation security
cfn_nag_scan --input-path cfn/

# Credential detection
.venv/bin/detect-secrets scan

# Shell script security
shellcheck scripts/**/*.sh

# Frontend vulnerabilities
npm audit --audit-level=critical
```

**Stage 3: Tests (ALWAYS runs)**
```bash
# Python unit tests
.venv/bin/pytest tests/unit/ -v

# Property-based tests (with --full-tests flag)
.venv/bin/pytest tests/unit/ -v --hypothesis-show-statistics

# Frontend tests
npm run test
```

**Stage 4: Git Push (ALWAYS runs)**
- Pushes to `origin` and `codeaws` remotes
- Non-blocking if nothing to push

**Stage 5: Deploy**
- Builds Lambda packages
- Syncs to S3 deployment bucket
- Deploys CloudFormation stack
- Updates Lambda function code

### Virtual Environment Requirements

All validation tools must be run from the Python virtual environment (`.venv`):

```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Tools installed in .venv/bin/:
# - cfn-lint (CloudFormation validation)
# - flake8 (Python linting)
# - black (Python formatting)
# - bandit (Python security)
# - detect-secrets (Credential scanning)
# - pytest (Python testing)
# - checkov (IaC security)
# - semgrep (SAST)
```

### Validation Checkpoints

Each phase must pass validation before proceeding:

**Phase 1 Checkpoint (Shared Utilities):**
```bash
./scripts/deploy.sh dev --validate-only
source .venv/bin/activate
.venv/bin/pytest tests/unit/test_dynamodb_tables.py -v --cov=lambda.shared.dynamodb_tables
```

**Phase 2 Checkpoint (After Each Function Extraction):**
```bash
source .venv/bin/activate
.venv/bin/flake8 lambda/query-handler/index.py --max-line-length=120
.venv/bin/black --check --line-length=120 lambda/query-handler/index.py
.venv/bin/bandit -r lambda/query-handler/index.py
.venv/bin/pytest tests/unit/ -v --cov=lambda.query-handler.index
```

**Phase 3 Checkpoint (Comparison Testing):**
```bash
./scripts/deploy.sh dev --validate-only
source .venv/bin/activate
.venv/bin/pytest tests/comparison/ -v
.venv/bin/pytest tests/integration/ -v
```

**Phase 4 Checkpoint (Feature Flag):**
```bash
./scripts/deploy.sh dev
# Monitor CloudWatch metrics for 24 hours
# Verify no increase in error rate
# Verify performance improvement
```

### Critical Deployment Rules

**NEVER bypass the deploy script:**
- ❌ Never use `aws s3 sync` directly
- ❌ Never use `aws lambda update-function-code` directly
- ❌ Never use `aws cloudformation deploy` directly
- ✅ ALWAYS use: `./scripts/deploy.sh dev`

**Deployment Modes:**
- Full: `./scripts/deploy.sh dev` (validate, security, tests, push, deploy)
- Lambda-only: `./scripts/deploy.sh dev --lambda-only` (fast code update)
- Frontend-only: `./scripts/deploy.sh dev --frontend-only` (rebuild frontend)
- Validate-only: `./scripts/deploy.sh dev --validate-only` (no deployment)

---

## Conclusion

This design document provides a comprehensive plan for refactoring the `sync_source_server_inventory` function into focused, testable, and maintainable components. The refactoring:

1. **Decomposes** a 300+ line monolithic function into 7 focused functions
2. **Preserves** all existing functionality and error handling
3. **Maintains** backward compatibility with existing integrations
4. **Improves** testability with 90% unit test coverage
5. **Enhances** performance with parallel region queries
6. **Provides** rollback safety with feature flag
7. **Follows** PEP 8 standards and deployment validation requirements
8. **Integrates** with shared utilities to eliminate duplication
9. **Complies** with 5-stage deployment validation pipeline
10. **Uses** virtual environment for all Python tools

The incremental refactoring strategy with validation checkpoints ensures low risk and high confidence in the refactored implementation. The feature flag provides immediate rollback capability if issues arise.

**Next Steps**:
1. Review and approve this design document
2. Review the detailed implementation tasks in tasks.md
3. Begin Phase 1: Create shared utilities (Tasks 1-2)
4. Proceed with Phase 2: Extract functions one-by-one (Tasks 3-9)
5. Execute Phase 3: Integration and comparison testing (Tasks 10-12)
6. Complete Phase 4: Feature flag and rollback safety (Tasks 13-15)
7. Deploy with feature flag and monitor closely

