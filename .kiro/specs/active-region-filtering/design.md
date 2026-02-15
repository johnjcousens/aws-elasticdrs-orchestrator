# Design Document: Active Region Filtering

## Overview

This feature optimizes DRS region scanning operations by introducing active region filtering based on the existing DRSRegionStatusTable. Currently, the platform scans all 28 DRS-enabled regions for operations like tag synchronization, staging account sync, and source server inventory sync, even though most customers only use DRS in 2-5 regions. This results in unnecessary API calls, increased latency, and potential rate limiting issues.

The solution introduces a two-tier optimization strategy:
1. **Active Region Filtering**: Query the region status table to identify regions with active DRS servers (serverCount > 0) before scanning
2. **Inventory Database Usage**: Use the source server inventory database for queries instead of direct DRS/EC2 API calls

Additionally, this feature addresses an architectural issue where staging account sync operations are currently in query-handler despite performing write operations (DRS CreateExtendedSourceServer). These operations will be moved to data-management-handler to maintain proper separation of concerns.

**Expected Performance Improvements:**
- 80-90% reduction in DRS API calls for typical deployments (2-5 active regions vs 28 total regions)
- Sub-500ms response times for inventory-based queries
- Reduced risk of API throttling during frequent sync operations
- Faster tag sync, staging account sync, and inventory sync operations

## Architecture

### Current Architecture (Before Optimization)

```mermaid
flowchart TD
    EB[EventBridge Schedules] --> |Hourly| TagSync[Tag Sync]
    EB --> |Every 5 min| StagingSync[Staging Account Sync]
    EB --> |Every 15 min| InventorySync[Inventory Sync]
    
    TagSync --> |Scan ALL 28 regions| DRS1[DRS API]
    StagingSync --> |Scan ALL 28 regions| DRS2[DRS API]
    InventorySync --> |Scan ALL 28 regions| DRS3[DRS API]
    
    DRS1 --> |Slow, many calls| Result1[Results]
    DRS2 --> |Slow, many calls| Result2[Results]
    DRS3 --> |Slow, many calls| Result3[Results]
    
    style TagSync fill:#f9f,stroke:#333
    style StagingSync fill:#f9f,stroke:#333
    style InventorySync fill:#f9f,stroke:#333
```

**Problems:**
- All operations scan 28 regions regardless of actual DRS usage
- Each region scan requires multiple API calls (DescribeSourceServers, DescribeInstances, etc.)
- High API call volume increases latency and risk of throttling
- Staging account sync in wrong handler (query-handler instead of data-management-handler)


### Optimized Architecture (After Implementation)

```mermaid
flowchart TD
    EB[EventBridge Schedules] --> |Hourly| TagSync[Tag Sync]
    EB --> |Every 5 min| StagingSync[Staging Account Sync]
    EB --> |Every 15 min| InventorySync[Inventory Sync]
    
    TagSync --> RegionFilter1[Query Region Status Table]
    StagingSync --> RegionFilter2[Query Region Status Table]
    InventorySync --> RegionFilter3[Query Region Status Table]
    
    RegionFilter1 --> |Active regions only| InventoryDB1[Query Inventory DB]
    RegionFilter2 --> |Active regions only| InventoryDB2[Query Inventory DB]
    RegionFilter3 --> |Active regions only| DRS[DRS API - Update Inventory]
    
    InventoryDB1 --> |Fast, cached| Result1[Results]
    InventoryDB2 --> |Fast, cached| Result2[Results]
    DRS --> |Updates| InventoryDB[Inventory Database]
    InventoryDB --> Result3[Results]
    
    style RegionFilter1 fill:#9f9,stroke:#333
    style RegionFilter2 fill:#9f9,stroke:#333
    style RegionFilter3 fill:#9f9,stroke:#333
    style InventoryDB fill:#99f,stroke:#333
```

**Improvements:**
- Query region status table first to identify active regions (2-5 regions typically)
- Use inventory database for fast queries instead of DRS API calls
- Staging account sync moved to data-management-handler (proper separation)
- 80-90% reduction in API calls
- Sub-500ms response times for most operations

### Handler Responsibility Separation

```mermaid
flowchart LR
    subgraph "data-management-handler (Write Operations)"
        TagSync[Tag Sync]
        StagingSync[Staging Account Sync - MOVED]
        AddStaging[Add Staging Account]
        RemoveStaging[Remove Staging Account]
    end
    
    subgraph "query-handler (Read-Only Operations)"
        DiscoverStaging[Discover Staging Accounts]
        ValidateStaging[Validate Staging Account]
        QueryInventory[Query Inventory]
        GetCapacity[Get Capacity]
    end
    
    subgraph "Shared Utilities"
        RegionFilter[get_active_regions]
        InventoryQuery[query_inventory_db]
    end
    
    TagSync --> RegionFilter
    StagingSync --> RegionFilter
    DiscoverStaging --> RegionFilter
    QueryInventory --> InventoryQuery
    
    style StagingSync fill:#9f9,stroke:#333
    style RegionFilter fill:#ff9,stroke:#333
    style InventoryQuery fill:#ff9,stroke:#333
```


## Components and Interfaces

### 1. Active Region Filter Module (shared/active_region_filter.py)

New shared module that provides region filtering functionality for all handlers.

```python
def get_active_regions(
    region_status_table: Optional[Table] = None,
    cache_ttl: int = 60
) -> List[str]:
    """
    Get list of active DRS regions (regions with serverCount > 0).
    
    Uses caching to avoid repeated DynamoDB queries within TTL window.
    Falls back to all DRS_REGIONS if table is empty or unavailable.
    
    Args:
        region_status_table: DynamoDB table resource (optional, will use env var if None)
        cache_ttl: Cache time-to-live in seconds (default: 60)
        
    Returns:
        List of active region names (e.g., ['us-east-1', 'us-west-2'])
        
    Example:
        active_regions = get_active_regions()
        for region in active_regions:
            scan_region(region)
    """
    pass

def invalidate_region_cache() -> None:
    """
    Invalidate the region status cache.
    
    Should be called after source server inventory sync completes
    to ensure fresh data on next query.
    """
    pass

def update_region_status(
    region: str,
    server_count: int,
    error_message: Optional[str] = None
) -> None:
    """
    Update region status in DynamoDB table.
    
    Called by inventory sync to maintain accurate region status.
    
    Args:
        region: AWS region name
        server_count: Number of DRS source servers in region
        error_message: Optional error message if region scan failed
    """
    pass
```

### 2. Inventory Database Query Module (shared/inventory_query.py)

New shared module for querying the source server inventory database.

```python
def query_inventory_by_regions(
    regions: List[str],
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Query source server inventory database for specified regions.
    
    Provides fast access to server data without DRS API calls.
    Falls back to DRS API if inventory is stale or unavailable.
    
    Args:
        regions: List of regions to query
        filters: Optional filters (hostname, tags, replicationState, etc.)
        
    Returns:
        List of server dictionaries in frontend-compatible format
        
    Example:
        servers = query_inventory_by_regions(
            regions=['us-east-1', 'us-west-2'],
            filters={'replicationState': 'CONTINUOUS'}
        )
    """
    pass

def is_inventory_fresh(max_age_minutes: int = 15) -> bool:
    """
    Check if inventory database contains fresh data.
    
    Args:
        max_age_minutes: Maximum age in minutes to consider fresh
        
    Returns:
        True if inventory was updated within max_age_minutes
    """
    pass
```


### 3. Modified Tag Sync (data-management-handler/index.py)

Update existing tag sync to use active region filtering.

```python
def handle_drs_tag_sync(body: Dict = None) -> Dict:
    """
    Sync EC2 instance tags to DRS source servers across active DRS regions.
    
    OPTIMIZATION: Now queries region status table to identify active regions
    before scanning, reducing API calls by 80-90%.
    """
    # Get active regions instead of scanning all 28
    active_regions = get_active_regions()
    
    if not active_regions:
        # Fallback to all regions if table is empty
        active_regions = DRS_REGIONS
        logger.warning("Region status table empty, falling back to all regions")
    
    logger.info(f"Tag sync scanning {len(active_regions)} active regions "
                f"(skipping {len(DRS_REGIONS) - len(active_regions)} inactive)")
    
    # Existing tag sync logic, but only for active regions
    # ...
```

### 4. Moved Staging Account Sync (data-management-handler/index.py)

Move from query-handler to data-management-handler and add region filtering.

```python
def handle_sync_staging_accounts() -> Dict:
    """
    Auto-extend DRS servers from staging accounts to target accounts.
    
    MOVED from query-handler to data-management-handler for proper separation.
    OPTIMIZATION: Now uses active region filtering and inventory database.
    
    Called by EventBridge every 5 minutes.
    """
    # Get active regions
    active_regions = get_active_regions()
    
    if not active_regions:
        active_regions = DRS_REGIONS
        logger.warning("Region status table empty, falling back to all regions")
    
    logger.info(f"Staging account sync scanning {len(active_regions)} active regions")
    
    # Get target accounts
    target_accounts = get_target_accounts_table().scan().get("Items", [])
    
    # Auto-extend using active regions only
    result = auto_extend_staging_servers(target_accounts, active_regions)
    return response(200, result)

def auto_extend_staging_servers(
    target_accounts: List[Dict],
    active_regions: List[str]
) -> Dict:
    """
    Auto-extend new DRS source servers from staging to target accounts.
    
    OPTIMIZATION: Now accepts active_regions parameter to limit scanning.
    """
    # Existing logic, but only scan active_regions instead of DRS_REGIONS
    # ...

def get_staging_account_servers(
    staging_account_id: str,
    role_arn: str,
    external_id: str,
    active_regions: List[str]
) -> List[Dict]:
    """
    Get DRS source servers in staging account across active regions.
    
    OPTIMIZATION: Now accepts active_regions parameter.
    OPTIMIZATION: Uses inventory database if available.
    """
    # Try inventory database first
    if is_inventory_fresh():
        servers = query_inventory_by_regions(
            regions=active_regions,
            filters={'stagingAccountId': staging_account_id}
        )
        if servers:
            logger.info(f"Retrieved {len(servers)} servers from inventory database")
            return servers
    
    # Fallback to DRS API for active regions only
    # ...
```


### 5. Modified Inventory Sync (query-handler/index.py)

Update inventory sync to use active region filtering and update region status table.

```python
def handle_sync_source_server_inventory() -> Dict:
    """
    Sync source server inventory from DRS and EC2 into DynamoDB.
    
    OPTIMIZATION: Now uses active region filtering.
    RESPONSIBILITY: Updates region status table with current server counts.
    
    Called by EventBridge every 15 minutes.
    """
    # Get active regions (or all if table empty)
    active_regions = get_active_regions()
    
    if not active_regions:
        active_regions = DRS_REGIONS
        logger.info("Region status table empty, scanning all regions to populate")
    
    logger.info(f"Inventory sync scanning {len(active_regions)} regions")
    
    # Scan active regions and collect server data
    all_servers = []
    region_counts = {}
    
    for region in active_regions:
        try:
            servers = scan_region_for_servers(region)
            all_servers.extend(servers)
            region_counts[region] = len(servers)
            
            # Update region status table
            update_region_status(region, len(servers))
            
        except Exception as e:
            logger.error(f"Error scanning region {region}: {e}")
            update_region_status(region, 0, error_message=str(e))
    
    # Update inventory database
    update_inventory_database(all_servers)
    
    # Invalidate region cache so next operations get fresh data
    invalidate_region_cache()
    
    return response(200, {
        'totalServers': len(all_servers),
        'regionsScanned': len(active_regions),
        'regionCounts': region_counts
    })
```

## Data Models

### Region Status Table Schema

Existing table: `hrp-drs-tech-adapter-drs-region-status-dev`

```python
{
    "region": "us-east-1",           # HASH key (string)
    "status": "AVAILABLE",           # Status: AVAILABLE | ERROR | UNINITIALIZED
    "serverCount": 42,               # Number of DRS source servers (number)
    "replicatingCount": 38,          # Servers in CONTINUOUS replication (number)
    "lastChecked": "2026-02-15T06:00:00Z",  # ISO timestamp (string)
    "errorMessage": null             # Error message if status=ERROR (string, optional)
}
```

**Indexes:**
- Primary Key: `region` (HASH)
- No GSIs needed (small table, 28 regions max)

**Access Patterns:**
1. Scan all regions to get active list (get_active_regions)
2. Update single region status (update_region_status)
3. Query single region status (optional, for debugging)

### Source Server Inventory Table Schema

Existing table: `hrp-drs-tech-adapter-source-server-inventory-dev`

```python
{
    "sourceServerID": "s-abc123...",  # HASH key
    "replicationRegion": "us-east-1", # RANGE key
    "hostname": "web-server-01",
    "sourceAccountId": "123456789012",
    "stagingAccountId": "987654321098",
    "replicationState": "CONTINUOUS",
    "lastUpdated": "2026-02-15T06:00:00Z",
    "sourceTags": {"Environment": "production"},
    # ... other fields
}
```

**Indexes:**
- Primary Key: `sourceServerID` (HASH), `replicationRegion` (RANGE)
- GSI: `StagingAccountIndex` on `stagingAccountId`
- GSI: `SourceAccountIndex` on `sourceAccountId`

**Access Patterns:**
1. Query by staging account (for staging account sync)
2. Query by source account (for account-specific queries)
3. Query by region (for region-specific queries)
4. Scan all with filters (for general queries)


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Active Region Filtering Consistency

*For any* multi-region scan operation (tag sync, staging account sync, inventory sync), when the region status table contains entries with serverCount > 0, the operation should only scan those active regions and skip all regions with serverCount = 0.

**Validates: Requirements 1.2, 2.2, 3.2, 4.2, 9.2**

### Property 2: Fallback to All Regions

*For any* multi-region scan operation, when the region status table is empty, unavailable, or returns an error, the operation should fall back to scanning all 28 DRS regions and should populate the region status table with discovered server counts.

**Validates: Requirements 1.3, 1.4, 2.3, 3.3, 6.1, 6.2, 6.4, 8.1**

### Property 3: Region Status Table Updates

*For any* source server inventory sync operation, when scanning a region, the operation should update the region status table with the current server count for that region, and if the scan fails, should record the error message in the table.

**Validates: Requirements 5.1, 5.3, 5.4, 5.5**

### Property 4: Inventory Database Freshness Check

*For any* query operation that can use inventory data, when the inventory database contains data updated within the last 15 minutes, the operation should use the inventory database instead of making DRS API calls, and when the inventory is stale or unavailable, should fall back to DRS API calls.

**Validates: Requirements 12.3, 12.4, 12.8**

### Property 5: API Call Reduction

*For any* multi-region operation using active region filtering, when comparing to the same operation without filtering, the number of DRS API calls should be reduced by at least (28 - active_region_count) / 28 * 100 percent.

**Validates: Requirements 9.4, 12.5**

### Property 6: Cache Invalidation

*For any* sequence of operations where source server inventory sync completes, the region status cache should be invalidated, and the next call to get_active_regions should query DynamoDB instead of using cached data.

**Validates: Requirements 10.5**

### Property 7: Pagination Handling

*For any* region status table containing more than 28 entries, the get_active_regions function should handle DynamoDB pagination and return all active regions, not just the first page.

**Validates: Requirements 10.3**

### Property 8: Cache TTL Behavior

*For any* sequence of get_active_regions calls within a 60-second window, only the first call should query DynamoDB, and subsequent calls should return cached results until the TTL expires or cache is invalidated.

**Validates: Requirements 10.4**

### Property 9: Inventory Data Completeness

*For any* server record retrieved from the inventory database, the record should contain all required fields: sourceServerID, replicationRegion, replicationState, hostname, sourceAccountId, and sourceTags.

**Validates: Requirements 4.3, 12.9**

### Property 10: Inventory Database Updates During Fallback

*For any* operation that falls back to DRS API calls due to stale or missing inventory data, the operation should update the inventory database with the retrieved server data before returning results.

**Validates: Requirements 12.10**

### Property 11: Moved Functions Use Region Filtering

*For any* staging account sync function moved from query-handler to data-management-handler (handle_sync_staging_accounts, auto_extend_staging_servers, get_staging_account_servers), the function should call get_active_regions and use the filtered region list instead of scanning all DRS_REGIONS.

**Validates: Requirements 11.12**

### Property 12: Cross-Account IAM Assumptions Limited to Active Regions

*For any* cross-account operation querying extended source servers, the number of IAM role assumptions should equal the number of active regions, not the total number of DRS regions (28).

**Validates: Requirements 9.3**


## Failback Topology Preservation

### Overview

During disaster recovery operations, servers are recovered from a source region to a DR region. When performing a failback (restoring from DR back to production), the DRS agent must be reinstalled on the recovered servers. The agent installation requires knowing the original replication topology:

- **Original source region**: Where the server was originally replicated from
- **Original account**: Staging account or target account where replication was configured
- **Original replication configuration**: Subnet, security groups, replication settings

Without this information preserved in the inventory database, operators must manually look up the original topology during time-critical failback operations, which is error-prone and delays recovery.

### Inventory Database Schema Enhancement

The source server inventory table will be enhanced to include original topology fields:

```python
{
    "sourceServerID": "s-1234567890abcdef0",  # Existing
    "region": "us-west-2",                     # Existing - current region
    "hostname": "web-server-01",               # Existing
    "replicationState": "CONTINUOUS",          # Existing
    
    # NEW FIELDS FOR FAILBACK TOPOLOGY
    "originalSourceRegion": "us-east-1",       # Original region before DR
    "originalAccountId": "123456789012",       # Original AWS account
    "originalReplicationConfigTemplateId": "rct-abc123",  # Original config
    "topologyLastUpdated": "2025-02-15T10:30:00Z",  # When topology captured
    
    # Existing fields
    "tags": {...},
    "lastUpdated": "2025-02-15T10:30:00Z"
}
```

### Topology Capture Logic

**When to capture original topology:**

1. **During initial inventory sync**: When a server is first discovered, capture its current region/account as "original"
2. **During recovery operations**: When a server is recovered to DR, preserve original topology
3. **During normal replication**: Continuously validate and update topology

**Implementation in inventory sync:**

```python
def sync_source_server_inventory(region: str) -> None:
    """Sync inventory and preserve original topology."""
    servers = drs_client.describe_source_servers()
    
    for server in servers:
        server_id = server["sourceServerID"]
        
        # Check if server exists in inventory
        existing = inventory_table.get_item(
            Key={"sourceServerID": server_id}
        ).get("Item")
        
        if existing:
            # Preserve original topology from existing record
            original_region = existing.get(
                "originalSourceRegion", region
            )
            original_account = existing.get(
                "originalAccountId", get_current_account_id()
            )
        else:
            # New server - capture current state as original
            original_region = region
            original_account = get_current_account_id()
        
        # Update inventory with preserved topology
        inventory_table.put_item(Item={
            "sourceServerID": server_id,
            "region": region,  # Current region (may be DR)
            "originalSourceRegion": original_region,
            "originalAccountId": original_account,
            "topologyLastUpdated": datetime.utcnow().isoformat(),
            # ... other fields
        })
```

### Failback Query Interface

```python
def get_failback_topology(server_id: str) -> Dict[str, Any]:
    """
    Get original replication topology for failback operations.
    
    Returns original region, account, and config for DRS agent reinstall.
    """
    server = inventory_table.get_item(
        Key={"sourceServerID": server_id}
    ).get("Item")
    
    if not server:
        raise ValueError(f"Server {server_id} not found")
    
    if not server.get("originalSourceRegion"):
        logger.warning(
            f"Server {server_id} missing original topology"
        )
    
    return {
        "originalSourceRegion": server.get("originalSourceRegion"),
        "originalAccountId": server.get("originalAccountId"),
        "currentRegion": server.get("region"),
        "topologyLastUpdated": server.get("topologyLastUpdated")
    }
```

### Topology Preservation During Fallback

When falling back to DRS API (stale inventory), preserve existing topology:

```python
def query_with_fallback(regions: List[str]) -> List[Dict]:
    """Query inventory with fallback, preserving topology."""
    if is_inventory_fresh():
        return query_inventory_from_db(regions)
    
    # Fallback to DRS API
    servers = []
    for region in regions:
        drs_servers = drs_client.describe_source_servers(region)
        
        for server in drs_servers:
            # Preserve existing topology if available
            existing = inventory_table.get_item(
                Key={"sourceServerID": server["sourceServerID"]}
            ).get("Item")
            
            if existing and existing.get("originalSourceRegion"):
                server["originalSourceRegion"] = existing[
                    "originalSourceRegion"
                ]
                server["originalAccountId"] = existing[
                    "originalAccountId"
                ]
            
            servers.append(server)
    
    # Update inventory with preserved topology
    update_inventory_database(servers)
    return servers
```

**Validates: Requirement 13 (Preserve Replication Topology for Failback)**


## Error Handling

### Region Status Table Errors

**Scenario**: DynamoDB query fails when retrieving region status

**Handling**:
```python
try:
    region_statuses = region_status_table.scan()
except ClientError as e:
    logger.error(f"Failed to query region status table: {e}")
    logger.warning("Falling back to scanning all DRS regions")
    return DRS_REGIONS  # Fallback to all regions
```

**Recovery**: Automatic fallback to all regions, operation continues

### Inventory Database Errors

**Scenario**: Inventory database is unavailable or returns incomplete data

**Handling**:
```python
try:
    servers = query_inventory_by_regions(active_regions)
    if not servers or not is_inventory_fresh():
        raise ValueError("Inventory stale or empty")
except Exception as e:
    logger.warning(f"Inventory database unavailable: {e}, falling back to DRS API")
    servers = query_drs_api_directly(active_regions)
    # Update inventory for next time
    update_inventory_database(servers)
```

**Recovery**: Automatic fallback to DRS API, inventory updated for future queries

### DRS API Errors During Region Scan

**Scenario**: DRS API call fails for a specific region

**Handling**:
```python
for region in active_regions:
    try:
        servers = drs_client.describe_source_servers()
        update_region_status(region, len(servers))
    except ClientError as e:
        if e.response['Error']['Code'] == 'UninitializedAccountException':
            logger.info(f"DRS not initialized in {region}")
            update_region_status(region, 0)
        else:
            logger.error(f"DRS API error in {region}: {e}")
            update_region_status(region, 0, error_message=str(e))
        continue  # Continue with other regions
```

**Recovery**: Log error, mark region as having 0 servers, continue with remaining regions

### Cache Corruption

**Scenario**: Cached region data becomes invalid

**Handling**:
```python
# Cache includes timestamp validation
cached_data = _region_cache.get('active_regions')
if cached_data:
    age = time.time() - cached_data['timestamp']
    if age > CACHE_TTL:
        logger.debug("Cache expired, invalidating")
        _region_cache.clear()
        return None  # Force fresh query
```

**Recovery**: Automatic cache invalidation on expiry, fresh query from DynamoDB

### EventBridge Routing Errors

**Scenario**: EventBridge invokes wrong handler after refactoring

**Handling**:
- CloudFormation validation ensures correct handler ARNs
- Lambda function name validation in handler code
- Comprehensive integration tests verify routing

**Recovery**: Deployment validation catches routing errors before production


## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure correctness:

**Unit Tests**: Verify specific examples, edge cases, and error conditions
**Property Tests**: Verify universal properties across all inputs

Both are complementary and necessary for comprehensive coverage. Unit tests focus on specific scenarios while property tests validate behavior across randomized inputs.

### Property-Based Testing

**Library**: Hypothesis (Python)
**Configuration**: Minimum 100 iterations per property test
**Tagging**: Each property test must reference its design document property

**Property Test Examples**:

```python
from hypothesis import given, strategies as st
import pytest

# Property 1: Active Region Filtering Consistency
@given(
    region_statuses=st.lists(
        st.fixed_dictionaries({
            'region': st.sampled_from(DRS_REGIONS),
            'serverCount': st.integers(min_value=0, max_value=1000)
        }),
        min_size=1,
        max_size=28
    )
)
def test_active_region_filtering_consistency(region_statuses, mock_dynamodb):
    """
    Feature: active-region-filtering, Property 1: Active Region Filtering Consistency
    
    For any region status table state, get_active_regions should return only
    regions with serverCount > 0.
    """
    # Setup: Populate mock DynamoDB table
    for status in region_statuses:
        mock_dynamodb.put_item(Item=status)
    
    # Execute: Get active regions
    active_regions = get_active_regions()
    
    # Verify: Only regions with serverCount > 0 are returned
    expected_active = [s['region'] for s in region_statuses if s['serverCount'] > 0]
    assert set(active_regions) == set(expected_active)

# Property 2: Fallback to All Regions
@given(
    table_state=st.sampled_from(['empty', 'error', 'unavailable'])
)
def test_fallback_to_all_regions(table_state, mock_dynamodb):
    """
    Feature: active-region-filtering, Property 2: Fallback to All Regions
    
    For any error condition (empty table, DynamoDB error, unavailable),
    operations should fall back to scanning all 28 DRS regions.
    """
    # Setup: Simulate error condition
    if table_state == 'empty':
        # Table exists but has no items
        pass
    elif table_state == 'error':
        mock_dynamodb.side_effect = ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'Scan')
    elif table_state == 'unavailable':
        mock_dynamodb.side_effect = Exception("Table not found")
    
    # Execute: Get active regions
    active_regions = get_active_regions()
    
    # Verify: Falls back to all DRS regions
    assert set(active_regions) == set(DRS_REGIONS)
    assert len(active_regions) == 28

# Property 5: API Call Reduction
@given(
    active_region_count=st.integers(min_value=1, max_value=10)
)
def test_api_call_reduction(active_region_count, mock_drs_client):
    """
    Feature: active-region-filtering, Property 5: API Call Reduction
    
    For any number of active regions, the API call count should be reduced
    proportionally compared to scanning all 28 regions.
    """
    # Setup: Mock active regions
    active_regions = DRS_REGIONS[:active_region_count]
    
    # Execute: Scan with filtering
    with patch('shared.active_region_filter.get_active_regions', return_value=active_regions):
        scan_all_regions_with_filtering()
    
    # Verify: API calls match active region count, not total regions
    api_call_count = mock_drs_client.describe_source_servers.call_count
    assert api_call_count == active_region_count
    
    # Calculate reduction percentage
    reduction_pct = ((28 - active_region_count) / 28) * 100
    assert reduction_pct >= 0
```

### Unit Testing

**Focus Areas**:
1. Specific edge cases (empty table, single region, all regions active)
2. Error handling scenarios (DynamoDB errors, DRS API errors)
3. Cache behavior (TTL expiry, invalidation)
4. Integration points (EventBridge routing, API Gateway routing)

**Unit Test Examples**:

```python
def test_empty_region_status_table_fallback():
    """Test that empty table triggers fallback to all regions."""
    # Setup: Empty table
    mock_table = Mock()
    mock_table.scan.return_value = {'Items': []}
    
    # Execute
    active_regions = get_active_regions(region_status_table=mock_table)
    
    # Verify
    assert active_regions == DRS_REGIONS
    assert len(active_regions) == 28

def test_cache_ttl_expiry():
    """Test that cache expires after TTL."""
    # Setup: Populate cache
    _region_cache['active_regions'] = {
        'data': ['us-east-1'],
        'timestamp': time.time() - 61  # 61 seconds ago (expired)
    }
    
    # Execute
    active_regions = get_active_regions()
    
    # Verify: Cache was not used (DynamoDB queried)
    assert mock_dynamodb.scan.called

def test_staging_sync_moved_to_data_management_handler():
    """Test that staging account sync is in data-management-handler."""
    from lambda.data_management_handler import index as dm_handler
    
    # Verify function exists in data-management-handler
    assert hasattr(dm_handler, 'handle_sync_staging_accounts')
    assert hasattr(dm_handler, 'auto_extend_staging_servers')
    assert hasattr(dm_handler, 'extend_source_server')

def test_query_handler_has_no_write_operations():
    """Test that query-handler contains only read operations."""
    from lambda.query_handler import index as q_handler
    
    # Verify write functions are NOT in query-handler
    assert not hasattr(q_handler, 'handle_sync_staging_accounts')
    assert not hasattr(q_handler, 'auto_extend_staging_servers')
    assert not hasattr(q_handler, 'extend_source_server')
```


### Integration Testing

**Test Scenarios**:

1. **End-to-End Tag Sync with Region Filtering**
   - Populate region status table with 3 active regions
   - Trigger tag sync via EventBridge
   - Verify only 3 regions are scanned
   - Verify tags are synced correctly

2. **End-to-End Staging Account Sync After Refactoring**
   - Configure staging accounts in target account
   - Trigger staging account sync via EventBridge
   - Verify data-management-handler is invoked (not query-handler)
   - Verify servers are extended correctly
   - Verify only active regions are scanned

3. **Inventory Sync Updates Region Status Table**
   - Trigger inventory sync
   - Verify region status table is updated with current counts
   - Verify cache is invalidated
   - Verify next operation uses fresh region data

4. **Fallback Behavior When Table Empty**
   - Clear region status table
   - Trigger any multi-region operation
   - Verify all 28 regions are scanned
   - Verify region status table is populated

5. **API Gateway Routing After Refactoring**
   - Call POST /accounts/{id}/staging-accounts/sync via API Gateway
   - Verify data-management-handler is invoked
   - Verify response format is unchanged

6. **Direct Lambda Invocation Routing**
   - Invoke data-management-handler with operation=sync_staging_accounts
   - Verify function executes correctly
   - Verify active region filtering is applied

### Performance Testing

**Metrics to Validate**:

1. **API Call Reduction**
   - Baseline: Count API calls with no filtering (28 regions)
   - Optimized: Count API calls with filtering (2-5 regions typically)
   - Target: 80-90% reduction

2. **Response Time Improvement**
   - Baseline: Measure tag sync time scanning all regions
   - Optimized: Measure tag sync time with filtering
   - Target: 70-80% reduction in execution time

3. **Inventory Database Query Performance**
   - Measure query time for inventory database
   - Target: < 500ms for typical queries
   - Compare to DRS API query time (typically 2-5 seconds)

4. **Cache Effectiveness**
   - Measure cache hit rate for get_active_regions
   - Target: > 90% cache hit rate within TTL window

**Performance Test Example**:

```python
def test_api_call_reduction_performance():
    """Measure actual API call reduction with filtering."""
    # Setup: 3 active regions out of 28
    setup_region_status_table(active_regions=['us-east-1', 'us-west-2', 'eu-west-1'])
    
    # Baseline: Count API calls without filtering
    with patch('shared.drs_regions.DRS_REGIONS', DRS_REGIONS):
        baseline_calls = count_drs_api_calls(scan_all_regions_no_filter)
    
    # Optimized: Count API calls with filtering
    with patch('shared.active_region_filter.get_active_regions', return_value=['us-east-1', 'us-west-2', 'eu-west-1']):
        optimized_calls = count_drs_api_calls(scan_all_regions_with_filter)
    
    # Verify reduction
    reduction_pct = ((baseline_calls - optimized_calls) / baseline_calls) * 100
    assert reduction_pct >= 80, f"Expected 80%+ reduction, got {reduction_pct}%"
    assert optimized_calls == 3  # Only 3 active regions
    assert baseline_calls == 28  # All regions
```

### Test Coverage Requirements

**Minimum Coverage Targets**:
- Unit test coverage: 90% for new modules (active_region_filter.py, inventory_query.py)
- Unit test coverage: 80% for modified functions (tag sync, staging sync, inventory sync)
- Property test coverage: 100% of correctness properties (12 properties)
- Integration test coverage: All critical paths (6 scenarios)

**Coverage Verification**:
```bash
# Run tests with coverage
pytest tests/unit/ --cov=lambda/shared/active_region_filter --cov-report=term --cov-report=html

# Verify property tests
pytest tests/unit/ -k "property" --hypothesis-show-statistics

# Run integration tests
pytest tests/integration/ -v
```


## Implementation Notes

### CloudFormation Changes

**EventBridge Stack (cfn/eventbridge-stack.yaml)**:

```yaml
# BEFORE (incorrect - invokes query-handler for write operation)
StagingAccountSyncScheduleRule:
  Type: AWS::Events::Rule
  Properties:
    Targets:
      - Id: StagingAccountSyncTarget
        Arn: !Ref QueryHandlerFunctionArn  # WRONG HANDLER
        RoleArn: !GetAtt EventBridgeInvokeRole.Arn
        Input: '{"operation": "sync_staging_accounts"}'

# AFTER (correct - invokes data-management-handler)
StagingAccountSyncScheduleRule:
  Type: AWS::Events::Rule
  Properties:
    Targets:
      - Id: StagingAccountSyncTarget
        Arn: !Ref ApiHandlerFunctionArn  # CORRECT HANDLER (data-management)
        RoleArn: !GetAtt EventBridgeInvokeRole.Arn
        Input: '{"operation": "sync_staging_accounts"}'

# Update Lambda permission
StagingAccountSyncSchedulePermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref ApiHandlerFunctionArn  # Changed from QueryHandlerFunctionArn
    Action: lambda:InvokeFunction
    Principal: events.amazonaws.com
    SourceArn: !GetAtt StagingAccountSyncScheduleRule.Arn
```

**API Gateway Stack (cfn/api-gateway-infrastructure-methods-stack.yaml)**:

No changes needed - already routes to ApiHandlerFunctionArn (data-management-handler):

```yaml
AccountsTargetStagingAccountsSyncPostMethod:
  Type: AWS::ApiGateway::Method
  Properties:
    Integration:
      Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ApiHandlerFunctionArn}/invocations'
```

### Migration Strategy

**Phase 1: Add New Modules (No Breaking Changes)**
1. Create `shared/active_region_filter.py` with region filtering logic
2. Create `shared/inventory_query.py` with inventory database queries
3. Deploy and verify modules are available

**Phase 2: Update Existing Operations (Backward Compatible)**
1. Update tag sync to use `get_active_regions()` with fallback
2. Update inventory sync to use `get_active_regions()` and update region status table
3. Deploy and verify operations work with both empty and populated region status table

**Phase 3: Move Staging Account Sync (Breaking Change - Requires CloudFormation Update)**
1. Copy staging account sync functions from query-handler to data-management-handler
2. Update functions to use active region filtering
3. Update CloudFormation EventBridge stack to route to data-management-handler
4. Deploy CloudFormation changes
5. Verify EventBridge triggers correct handler
6. Remove old functions from query-handler

**Phase 4: Validation and Cleanup**
1. Run comprehensive integration tests
2. Monitor CloudWatch logs for errors
3. Verify performance improvements
4. Remove deprecated code from query-handler

### Rollback Plan

**If Issues Detected After Deployment**:

1. **Immediate Rollback** (< 5 minutes):
   ```bash
   # Revert CloudFormation stack to previous version
   aws cloudformation update-stack \
     --stack-name hrp-drs-tech-adapter-dev \
     --use-previous-template \
     --parameters UsePreviousValue=true
   ```

2. **Disable Region Filtering** (< 1 minute):
   ```python
   # Emergency flag in shared/active_region_filter.py
   ENABLE_REGION_FILTERING = os.environ.get('ENABLE_REGION_FILTERING', 'false')
   
   def get_active_regions():
       if ENABLE_REGION_FILTERING != 'true':
           return DRS_REGIONS  # Fallback to all regions
       # Normal filtering logic...
   ```

3. **Revert EventBridge Routing** (< 5 minutes):
   - Update EventBridge rule to point back to QueryHandlerFunctionArn
   - Restore staging account sync functions in query-handler

### Monitoring and Observability

**CloudWatch Metrics**:
```python
# Publish custom metrics
cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='DRSOrchestration',
    MetricData=[
        {
            'MetricName': 'ActiveRegionCount',
            'Value': len(active_regions),
            'Unit': 'Count'
        },
        {
            'MetricName': 'RegionsSkipped',
            'Value': 28 - len(active_regions),
            'Unit': 'Count'
        },
        {
            'MetricName': 'APICallReduction',
            'Value': ((28 - len(active_regions)) / 28) * 100,
            'Unit': 'Percent'
        }
    ]
)
```

**CloudWatch Logs Insights Queries**:

```sql
-- Query 1: Active region filtering effectiveness
fields @timestamp, @message
| filter @message like /active regions/
| parse @message "scanning * active regions" as region_count
| stats avg(region_count) as avg_regions, min(region_count) as min_regions, max(region_count) as max_regions

-- Query 2: API call reduction
fields @timestamp, @message
| filter @message like /API calls/
| parse @message "* API calls" as call_count
| stats sum(call_count) as total_calls by bin(5m)

-- Query 3: Fallback occurrences
fields @timestamp, @message
| filter @message like /falling back to all regions/
| count() as fallback_count by bin(1h)

-- Query 4: Inventory database usage
fields @timestamp, @message
| filter @message like /inventory database/
| parse @message "Retrieved * servers from inventory database" as server_count
| stats count() as inventory_hits, sum(server_count) as total_servers
```

**Alarms**:

```yaml
# CloudWatch Alarm for excessive fallbacks
FallbackAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub '${ProjectName}-region-filter-fallback-${Environment}'
    MetricName: FallbackCount
    Namespace: DRSOrchestration
    Statistic: Sum
    Period: 3600  # 1 hour
    EvaluationPeriods: 1
    Threshold: 10  # Alert if > 10 fallbacks per hour
    ComparisonOperator: GreaterThanThreshold
```


## Security Considerations

### IAM Permissions

**New Permissions Required**:

No new IAM permissions needed - all operations use existing permissions:
- DynamoDB: `dynamodb:Scan`, `dynamodb:PutItem`, `dynamodb:GetItem` (already granted)
- DRS: `drs:DescribeSourceServers` (already granted)
- CloudWatch: `cloudwatch:PutMetricData` (already granted)

**Cross-Account Permissions**:

Staging account sync requires cross-account IAM role assumption (already configured):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "drs:DescribeSourceServers",
        "drs:CreateExtendedSourceServer"
      ],
      "Resource": "*"
    }
  ]
}
```

### Data Privacy

**Region Status Table**:
- Contains only aggregate counts, no sensitive server data
- No PII or customer data stored
- Safe to cache for 60 seconds

**Inventory Database**:
- Contains server metadata (hostnames, IPs, tags)
- Already encrypted at rest (DynamoDB encryption)
- Access controlled via IAM policies
- No additional privacy concerns introduced

### Audit Trail

**CloudTrail Events**:
- All DynamoDB operations logged to CloudTrail
- EventBridge rule invocations logged
- Lambda function invocations logged
- No changes to existing audit trail

**Compliance**:
- No impact on SOC2, HIPAA, or other compliance frameworks
- Maintains existing data residency requirements
- No new data storage or processing locations

## Performance Characteristics

### Expected Performance Improvements

**Tag Sync Operation**:
- Before: 28 regions × 2 seconds = 56 seconds
- After: 3 regions × 2 seconds = 6 seconds
- Improvement: 89% faster

**Staging Account Sync Operation**:
- Before: 28 regions × 3 seconds = 84 seconds
- After: 3 regions × 0.5 seconds (inventory DB) = 1.5 seconds
- Improvement: 98% faster

**Inventory Sync Operation**:
- Before: 28 regions × 2 seconds = 56 seconds
- After: 3 regions × 2 seconds = 6 seconds
- Improvement: 89% faster

### Resource Utilization

**Lambda Memory**:
- No change to memory requirements
- Region filtering adds negligible memory overhead (< 1 KB)
- Inventory queries use existing DynamoDB client

**Lambda Duration**:
- Significant reduction in execution time (80-90%)
- Reduced Lambda costs due to shorter execution
- Reduced risk of timeout errors

**DynamoDB Capacity**:
- Region status table: < 1 RCU per query (28 items max)
- Inventory table: 5-10 RCUs per query (depends on filter)
- Negligible impact on DynamoDB costs

**API Rate Limits**:
- DRS API: Reduced from 28 calls to 2-5 calls per operation
- Significantly reduced risk of throttling
- Better compliance with AWS service quotas

## Future Enhancements

### 1. Predictive Region Activation

Monitor server creation patterns and pre-warm region status cache:
```python
def predict_active_regions(historical_data: List[Dict]) -> List[str]:
    """Predict which regions will have servers based on historical patterns."""
    # Analyze last 7 days of region activity
    # Return regions likely to have servers
    pass
```

### 2. Multi-Account Region Aggregation

Aggregate region status across multiple target accounts:
```python
def get_active_regions_multi_account(account_ids: List[str]) -> Dict[str, List[str]]:
    """Get active regions for multiple accounts."""
    # Return {account_id: [active_regions]}
    pass
```

### 3. Real-Time Region Status Updates

Use DynamoDB Streams to invalidate cache immediately when region status changes:
```python
def handle_region_status_stream(event: Dict) -> None:
    """Handle DynamoDB Stream events for region status changes."""
    for record in event['Records']:
        if record['eventName'] in ['INSERT', 'MODIFY']:
            invalidate_region_cache()
```

### 4. Intelligent Cache Warming

Pre-populate cache before scheduled operations:
```python
def warm_region_cache() -> None:
    """Pre-populate region cache before scheduled operations."""
    # Called 30 seconds before tag sync, staging sync, etc.
    get_active_regions()  # Populates cache
```

### 5. Region Health Monitoring

Track region health and automatically exclude unhealthy regions:
```python
def get_healthy_active_regions() -> List[str]:
    """Get active regions that are currently healthy."""
    active_regions = get_active_regions()
    # Filter out regions with recent errors
    return [r for r in active_regions if is_region_healthy(r)]
```


## Coding Standards Compliance

### PEP 8 Compliance

All Python code must follow PEP 8 standards as enforced by the deploy.sh validation pipeline:

**Line Length**: Maximum 120 characters (configured in pyproject.toml)
```python
# GOOD - under 120 characters
def get_active_regions(region_status_table: Optional[Table] = None, cache_ttl: int = 60) -> List[str]:
    """Get list of active DRS regions."""
    pass

# BAD - exceeds 120 characters
def get_active_regions_with_very_long_parameter_names(region_status_table_resource: Optional[Table] = None, cache_time_to_live_seconds: int = 60) -> List[str]:
```

**Indentation**: 4 spaces (NO TABS)
```python
# GOOD
def process_regions():
    for region in active_regions:
        if region_has_servers(region):
            process_region(region)

# BAD - inconsistent indentation
def process_regions():
  for region in active_regions:
      if region_has_servers(region):
        process_region(region)
```

**String Formatting**: Use f-strings (Python 3.6+)
```python
# GOOD
logger.info(f"Scanning {len(active_regions)} active regions")

# BAD - old-style formatting
logger.info("Scanning %s active regions" % len(active_regions))
logger.info("Scanning {} active regions".format(len(active_regions)))
```

**Import Organization**: Standard library → Third-party → Local
```python
# GOOD
import json
import os
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from shared.drs_regions import DRS_REGIONS
from shared.response_utils import response

# BAD - mixed order
from shared.drs_regions import DRS_REGIONS
import json
import boto3
```

**Type Hints**: Required for all function parameters and returns
```python
# GOOD
def update_region_status(
    region: str,
    server_count: int,
    error_message: Optional[str] = None
) -> None:
    """Update region status in DynamoDB."""
    pass

# BAD - missing type hints
def update_region_status(region, server_count, error_message=None):
    pass
```

**Docstrings**: Required for all public functions (PEP 257)
```python
# GOOD
def get_active_regions() -> List[str]:
    """
    Get list of active DRS regions from region status table.
    
    Returns:
        List of region names with serverCount > 0
        
    Example:
        >>> regions = get_active_regions()
        >>> print(regions)
        ['us-east-1', 'us-west-2']
    """
    pass

# BAD - missing docstring
def get_active_regions() -> List[str]:
    pass
```

### Validation Tools Compliance

**flake8** (Python linting):
```bash
# Must pass with no errors (max-line-length=120)
flake8 lambda/shared/active_region_filter.py --max-line-length=120
```

**black** (Python formatting):
```bash
# Must pass formatting check (line-length=120)
black --check --line-length=120 lambda/shared/active_region_filter.py
```

**bandit** (Python security):
```bash
# Must pass security scan
bandit -r lambda/shared/active_region_filter.py
```

**cfn-lint** (CloudFormation validation):
```bash
# Must pass CloudFormation validation
cfn-lint cfn/eventbridge-stack.yaml
```

**cfn_nag** (CloudFormation security):
```bash
# Must pass security scan
cfn_nag_scan --input-path cfn/eventbridge-stack.yaml
```

**detect-secrets** (Credential scanning):
```bash
# Must not contain hardcoded secrets
detect-secrets scan lambda/shared/active_region_filter.py
```

### Common Violations to Avoid

**❌ Line too long**:
```python
# BAD - exceeds 120 characters
logger.info(f"Scanning regions: {', '.join(active_regions)} with server counts: {server_counts} and replication states: {replication_states}")

# GOOD - under 120 characters
regions_str = ', '.join(active_regions)
logger.info(f"Scanning regions: {regions_str}")
logger.info(f"Server counts: {server_counts}, replication states: {replication_states}")
```

**❌ Missing type hints**:
```python
# BAD
def query_inventory(regions):
    pass

# GOOD
def query_inventory(regions: List[str]) -> List[Dict[str, Any]]:
    pass
```

**❌ Bare except clause**:
```python
# BAD
try:
    result = query_table()
except:
    return []

# GOOD
try:
    result = query_table()
except ClientError as e:
    logger.error(f"DynamoDB error: {e}")
    return []
```

**❌ Mutable default arguments**:
```python
# BAD
def process_regions(regions: List[str] = []) -> None:
    regions.append('us-east-1')

# GOOD
def process_regions(regions: Optional[List[str]] = None) -> None:
    if regions is None:
        regions = []
    regions.append('us-east-1')
```

**❌ Hardcoded credentials**:
```python
# BAD
aws_access_key = "AKIAIOSFODNN7EXAMPLE"

# GOOD
# Use IAM roles, no hardcoded credentials
```

### CloudFormation Best Practices

**Resource Naming**: Use !Sub for dynamic names
```yaml
# GOOD
StagingAccountSyncScheduleRule:
  Type: AWS::Events::Rule
  Properties:
    Name: !Sub '${ProjectName}-staging-account-sync-${Environment}'

# BAD - hardcoded name
StagingAccountSyncScheduleRule:
  Type: AWS::Events::Rule
  Properties:
    Name: 'staging-account-sync-dev'
```

**IAM Policies**: Least privilege principle
```yaml
# GOOD - specific actions
Policies:
  - PolicyName: InvokeLambda
    PolicyDocument:
      Statement:
        - Effect: Allow
          Action:
            - lambda:InvokeFunction
          Resource: !Ref ApiHandlerFunctionArn

# BAD - overly permissive
Policies:
  - PolicyName: InvokeLambda
    PolicyDocument:
      Statement:
        - Effect: Allow
          Action: lambda:*
          Resource: '*'
```

**Conditions**: Use for optional resources
```yaml
# GOOD
Conditions:
  EnableStagingAccountSyncCondition: !Equals [!Ref EnableStagingAccountSync, 'true']

Resources:
  StagingAccountSyncScheduleRule:
    Type: AWS::Events::Rule
    Condition: EnableStagingAccountSyncCondition
```

### Pre-Deployment Validation Checklist

Before running `./scripts/deploy.sh dev`, ensure:

- [ ] All Python files pass `flake8` with max-line-length=120
- [ ] All Python files pass `black --check` with line-length=120
- [ ] All Python files pass `bandit` security scan
- [ ] All CloudFormation templates pass `cfn-lint`
- [ ] All CloudFormation templates pass `cfn_nag`
- [ ] No secrets detected by `detect-secrets`
- [ ] All unit tests pass with `pytest`
- [ ] All property tests pass with `pytest --hypothesis-show-statistics`
- [ ] Type hints present on all functions
- [ ] Docstrings present on all public functions
- [ ] Import order follows PEP 8 (stdlib → third-party → local)


## Deployment Strategy

### ⛔ CRITICAL: Always Use Deploy Script

**NEVER use direct AWS CLI commands for deployment. ALWAYS use the deploy script:**

```bash
# ✅ CORRECT - Use deploy script
./scripts/deploy.sh dev

# ❌ WRONG - Direct AWS commands are BANNED
aws cloudformation deploy --stack-name hrp-drs-tech-adapter-dev
aws lambda update-function-code --function-name hrp-drs-tech-adapter-data-management-handler-dev
```

### Deployment Phases

**Phase 1: Add New Shared Modules (No Breaking Changes)**

```bash
# 1. Create new modules
# - lambda/shared/active_region_filter.py
# - lambda/shared/inventory_query.py

# 2. Commit changes
git add lambda/shared/active_region_filter.py lambda/shared/inventory_query.py
git commit -m "feat(active-region-filtering): add region filtering and inventory query modules"

# 3. Deploy using deploy script (runs validation, security, tests)
./scripts/deploy.sh dev

# 4. Verify deployment
aws cloudformation describe-stacks --stack-name hrp-drs-tech-adapter-dev --query 'Stacks[0].StackStatus'
```

**Phase 2: Update Existing Operations (Backward Compatible)**

```bash
# 1. Update tag sync, inventory sync to use get_active_regions()
# - lambda/data-management-handler/index.py (tag sync)
# - lambda/query-handler/index.py (inventory sync)

# 2. Commit changes
git add lambda/data-management-handler/index.py lambda/query-handler/index.py
git commit -m "feat(active-region-filtering): add region filtering to tag sync and inventory sync"

# 3. Deploy using deploy script
./scripts/deploy.sh dev

# 4. Monitor CloudWatch logs for region filtering
aws logs tail /aws/lambda/hrp-drs-tech-adapter-data-management-handler-dev --since 5m --follow
```

**Phase 3: Move Staging Account Sync (Breaking Change - CloudFormation Update)**

```bash
# 1. Copy staging account sync functions to data-management-handler
# 2. Update CloudFormation EventBridge stack
# - cfn/eventbridge-stack.yaml (change QueryHandlerFunctionArn to ApiHandlerFunctionArn)

# 3. Commit all changes
git add lambda/data-management-handler/index.py cfn/eventbridge-stack.yaml
git commit -m "refactor(active-region-filtering): move staging account sync to data-management-handler"

# 4. Deploy using deploy script (CloudFormation will update EventBridge routing)
./scripts/deploy.sh dev

# 5. Verify EventBridge routing
aws events list-targets-by-rule --rule hrp-drs-tech-adapter-staging-account-sync-dev

# 6. Remove old functions from query-handler
git add lambda/query-handler/index.py
git commit -m "refactor(active-region-filtering): remove staging account sync from query-handler"

# 7. Deploy cleanup
./scripts/deploy.sh dev
```

**Phase 4: Validation and Monitoring**

```bash
# 1. Run comprehensive tests
source .venv/bin/activate
.venv/bin/pytest tests/unit/ -v
.venv/bin/pytest tests/integration/ -v

# 2. Monitor CloudWatch metrics
# - Check ActiveRegionCount metric
# - Check APICallReduction metric
# - Check for errors in Lambda logs

# 3. Verify performance improvements
# - Compare execution times before/after
# - Verify API call reduction
```

### Validation Before Deployment

**ALWAYS run validation before deploying:**

```bash
# Run validation only (no deployment)
./scripts/deploy.sh dev --validate-only
```

This runs:
1. **cfn-lint**: CloudFormation template validation
2. **flake8**: Python linting (max-line-length=120)
3. **black**: Python formatting check (line-length=120)
4. **bandit**: Python security scan
5. **detect-secrets**: Credential scanning
6. **pytest**: Unit and property tests

### Rollback Procedure

**If issues detected after deployment:**

```bash
# Option 1: Revert to previous CloudFormation stack version
aws cloudformation update-stack \
  --stack-name hrp-drs-tech-adapter-dev \
  --use-previous-template \
  --parameters UsePreviousValue=true

# Option 2: Disable region filtering via environment variable
aws lambda update-function-configuration \
  --function-name hrp-drs-tech-adapter-data-management-handler-dev \
  --environment Variables={ENABLE_REGION_FILTERING=false}

# Option 3: Revert git commits and redeploy
git revert HEAD
./scripts/deploy.sh dev
```

### Deployment Checklist

Before deploying to production:

- [ ] All unit tests pass (`pytest tests/unit/`)
- [ ] All property tests pass (`pytest -k property`)
- [ ] All integration tests pass (`pytest tests/integration/`)
- [ ] Validation passes (`./scripts/deploy.sh dev --validate-only`)
- [ ] Code reviewed and approved
- [ ] Deployed and tested in dev environment
- [ ] Deployed and tested in test environment
- [ ] Performance metrics validated (80-90% API call reduction)
- [ ] CloudWatch alarms configured
- [ ] Rollback procedure documented
- [ ] Team notified of deployment

### Environment-Specific Deployment

```bash
# Development environment (primary)
./scripts/deploy.sh dev

# Test environment (integration testing)
./scripts/deploy.sh test

# Staging environment (pre-production)
./scripts/deploy.sh staging

# Production environment (requires approval)
./scripts/deploy.sh prod
```

### Lambda-Only Updates (Fast Iteration)

For code-only changes without CloudFormation updates:

```bash
# Update Lambda functions only (30-60 seconds)
./scripts/deploy.sh dev --lambda-only
```

This skips CloudFormation deployment and only updates Lambda function code.

### Monitoring Post-Deployment

```bash
# Monitor Lambda logs
aws logs tail /aws/lambda/hrp-drs-tech-adapter-data-management-handler-dev --follow

# Check CloudFormation stack status
aws cloudformation describe-stacks \
  --stack-name hrp-drs-tech-adapter-dev \
  --query 'Stacks[0].StackStatus'

# Verify EventBridge rule targets
aws events list-targets-by-rule \
  --rule hrp-drs-tech-adapter-staging-account-sync-dev

# Check DynamoDB region status table
aws dynamodb scan \
  --table-name hrp-drs-tech-adapter-drs-region-status-dev \
  --max-items 10
```


## Documentation and Comment Standards

### Core Principles

**Simple over Clever**: Code should be simple, clean, and maintainable. Readability is a PRIMARY CONCERN.

**YAGNI (You Aren't Gonna Need It)**: Don't add features we don't need right now. Keep implementation minimal.

**No Over-Engineering**: Use the simplest solution that solves the problem.

### Comment Guidelines

**Value-Adding Comments Only**: Comments should explain WHY, not WHAT

```python
# ✅ GOOD - Explains WHY
def get_active_regions(cache_ttl: int = 60) -> List[str]:
    """
    Get active DRS regions from status table.
    
    Uses caching to avoid repeated DynamoDB queries during burst operations
    like tag sync which may call this function multiple times per second.
    """
    # Cache prevents DynamoDB throttling during concurrent operations
    if _is_cache_valid(cache_ttl):
        return _region_cache['data']
    
    # Fallback to all regions if table is empty (new deployments)
    if not region_statuses:
        return DRS_REGIONS

# ❌ BAD - Redundant, explains WHAT (code already shows this)
def get_active_regions(cache_ttl: int = 60) -> List[str]:
    """Get active regions."""
    # Check if cache is valid
    if _is_cache_valid(cache_ttl):
        # Return cached data
        return _region_cache['data']
    
    # If no region statuses, return all DRS regions
    if not region_statuses:
        return DRS_REGIONS
```

**Evergreen Comments**: Comments describe code as it is NOW, not its history

```python
# ✅ GOOD - Describes current behavior
def query_inventory_by_regions(regions: List[str]) -> List[Dict]:
    """
    Query inventory database for servers in specified regions.
    
    Provides fast access to server data without DRS API calls.
    Falls back to DRS API if inventory is stale (> 15 minutes old).
    """
    pass

# ❌ BAD - References history/changes
def query_inventory_by_regions(regions: List[str]) -> List[Dict]:
    """
    Query inventory database for servers in specified regions.
    
    Recently refactored to use inventory database instead of DRS API.
    Moved from query-handler to shared module for reusability.
    """
    pass
```

**No Temporal References**: Never use "recently", "moved", "updated", "new", "old"

```python
# ✅ GOOD - Domain-focused names
def get_active_regions() -> List[str]:
    pass

def query_inventory_database() -> List[Dict]:
    pass

# ❌ BAD - Temporal/historical names
def get_active_regions_new() -> List[str]:  # Don't use "new"
    pass

def query_inventory_database_improved() -> List[Dict]:  # Don't use "improved"
    pass

def get_active_regions_v2() -> List[str]:  # Don't use version numbers
    pass
```

### Docstring Standards (PEP 257)

**All public functions must have docstrings:**

```python
def get_active_regions(
    region_status_table: Optional[Table] = None,
    cache_ttl: int = 60
) -> List[str]:
    """
    Get list of active DRS regions (regions with serverCount > 0).
    
    Queries the DRSRegionStatusTable to identify regions with active DRS servers.
    Uses caching to avoid repeated DynamoDB queries within TTL window.
    Falls back to all DRS_REGIONS if table is empty or unavailable.
    
    Args:
        region_status_table: DynamoDB table resource (optional, uses env var if None)
        cache_ttl: Cache time-to-live in seconds (default: 60)
        
    Returns:
        List of active region names (e.g., ['us-east-1', 'us-west-2'])
        
    Raises:
        ClientError: If DynamoDB query fails (falls back to all regions)
        
    Example:
        >>> active_regions = get_active_regions()
        >>> print(f"Scanning {len(active_regions)} regions")
        Scanning 3 regions
    """
    pass
```

**Docstring Structure**:
1. One-line summary (what the function does)
2. Detailed description (how it works, important behavior)
3. Args section (all parameters with types and descriptions)
4. Returns section (return type and description)
5. Raises section (exceptions that may be raised)
6. Example section (usage example with expected output)

### Code Organization

**Match Existing Style**: Consistency within a file trumps external standards

```python
# If existing code uses this style:
def existing_function():
    result = some_operation()
    return result

# New code should match:
def new_function():
    result = another_operation()
    return result

# Don't introduce different style:
def new_function():
    return another_operation()  # Different style - avoid
```

**Preserve Existing Comments**: Never remove comments unless they are provably false

```python
# If existing code has this comment:
# DRS API has 10 TPS limit per region, use exponential backoff
def query_drs_with_retry():
    pass

# Keep the comment even if refactoring:
# DRS API has 10 TPS limit per region, use exponential backoff
def query_drs_with_retry_and_cache():
    pass
```

### Naming Conventions

**Domain-Focused Names**: Names tell WHAT code does, not HOW or its history

```python
# ✅ GOOD - Domain-focused
def get_active_regions() -> List[str]:
    """Get regions with active DRS servers."""
    pass

def query_inventory_database() -> List[Dict]:
    """Query source server inventory from DynamoDB."""
    pass

def update_region_status(region: str, count: int) -> None:
    """Update region status with current server count."""
    pass

# ❌ BAD - Implementation-focused or historical
def scan_dynamodb_for_regions() -> List[str]:  # Too implementation-focused
    pass

def query_inventory_database_fast() -> List[Dict]:  # "fast" is relative
    pass

def update_region_status_new_version(region: str, count: int) -> None:  # Historical
    pass
```

**No Historical Context in Names**:

```python
# ✅ GOOD
active_regions = get_active_regions()
servers = query_inventory_database()

# ❌ BAD
active_regions_v2 = get_active_regions_v2()
servers_new = query_inventory_database_new()
servers_improved = query_inventory_database_improved()
```

### Module Documentation

**Each module should have a module-level docstring:**

```python
"""
Active Region Filtering Module

Provides region filtering functionality to optimize DRS multi-region operations.
Queries the DRSRegionStatusTable to identify regions with active DRS servers,
reducing API calls by 80-90% for typical deployments.

Key Functions:
- get_active_regions(): Get list of active regions
- update_region_status(): Update region status in DynamoDB
- invalidate_region_cache(): Clear cached region data

Usage:
    from shared.active_region_filter import get_active_regions
    
    active_regions = get_active_regions()
    for region in active_regions:
        scan_region(region)
"""

import time
from typing import Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key
```

### Minimal Changes Principle

**Make the SMALLEST reasonable changes to achieve the outcome:**

```python
# ✅ GOOD - Minimal change to add region filtering
def handle_drs_tag_sync(body: Dict = None) -> Dict:
    """Sync EC2 tags to DRS source servers."""
    # Get active regions instead of using all regions
    active_regions = get_active_regions()
    
    # Existing tag sync logic (unchanged)
    for region in active_regions:  # Changed from DRS_REGIONS
        sync_tags_in_region(region)

# ❌ BAD - Unnecessary refactoring while adding feature
def handle_drs_tag_sync(body: Dict = None) -> Dict:
    """Sync EC2 tags to DRS source servers."""
    # Get active regions
    active_regions = get_active_regions()
    
    # Completely rewritten tag sync logic (unnecessary)
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(sync_tags_in_region, r) for r in active_regions]
        results = [f.result() for f in futures]
    return aggregate_results(results)
```

