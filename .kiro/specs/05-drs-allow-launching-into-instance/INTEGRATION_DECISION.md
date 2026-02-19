# Lambda Integration Decision: Integrate into Existing Handlers

## Executive Summary

**DECISION**: Integrate AllowLaunchingIntoThisInstance functionality into existing Lambda handlers based on operation type, NOT as a new handler.

**RATIONALE**: AllowLaunchingIntoThisInstance operations are fundamentally CRUD and execution operations that naturally align with existing handler responsibilities:
- **Configuration operations** (configure DRS settings, manage instance pairs) → data-management-handler
- **Execution operations** (failover, failback) → execution-handler  
- **Query operations** (status, instance matching, validation) → query-handler

**KEY INSIGHT**: The separation should be by **operation type** (CRUD vs execution vs query), not by **feature** (AllowLaunchingIntoThisInstance vs standard DRS). Creating a new handler would violate the existing architectural pattern where handlers are organized by operation type.

**EXCEPTION**: DRS Agent Deployer remains a separate Lambda handler because agent deployment is a distinct infrastructure operation that can be invoked independently by multiple features.

## Analysis of Existing Lambda Handlers

### 1. Data Management Handler (`lambda/data-management-handler/index.py`)

**Size**: 7,893 lines  
**Purpose**: Protection Groups and Recovery Plans CRUD operations

**Current Responsibilities**:
- Create/update/delete Protection Groups
- Create/update/delete Recovery Plans
- Resolve tag-based server selection
- Validate server assignments
- Import/export configuration
- Manage target accounts
- Manage staging accounts
- Tag synchronization

**Why INTEGRATE AllowLaunchingIntoThisInstance Configuration Operations**:
- ✅ **Configuration operations ARE CRUD operations** - Configuring DRS settings, managing instance pairs, storing IP mappings are all data management tasks
- ✅ **Consistent with existing pattern** - Already manages Protection Groups (server groupings), Recovery Plans (execution configurations), and staging accounts
- ✅ **Natural fit** - Instance pair configuration is analogous to Protection Group configuration (both define server relationships)
- ✅ **Shared validation logic** - Can reuse existing server validation, conflict detection, and uniqueness checks
- ✅ **Same API namespace** - Configuration endpoints naturally belong under `/protection-groups/*` or `/config/*`

**AllowLaunchingIntoThisInstance Operations to Add**:
```python
# NEW: Configure instance pairs for AllowLaunchingIntoThisInstance
def configure_instance_pairs(body: Dict) -> Dict:
    """Configure source-to-target instance mappings"""
    # Validates instance pairs exist
    # Stores instance pair configuration in DynamoDB
    # Validates no conflicts with existing configurations
    # Returns configuration ID

# NEW: Update instance pair configuration
def update_instance_pair_config(config_id: str, body: Dict) -> Dict:
    """Update existing instance pair configuration"""
    # Validates configuration exists
    # Updates instance pairs
    # Returns updated configuration

# NEW: Delete instance pair configuration
def delete_instance_pair_config(config_id: str) -> Dict:
    """Delete instance pair configuration"""
    # Validates no active executions using this config
    # Deletes configuration from DynamoDB
    # Returns success

# NEW: Configure DRS launch settings for AllowLaunchingIntoThisInstance
def configure_drs_launch_settings(body: Dict) -> Dict:
    """Configure DRS launchIntoEC2InstanceID parameter"""
    # Calls DRS UpdateLaunchConfiguration API
    # Sets launchIntoEC2InstanceID for each source server
    # Stores configuration in DynamoDB
    # Returns configuration status
```

**API Endpoints to Add**:
- `POST /protection-groups/{id}/instance-pairs` - Configure instance pairs
- `PUT /protection-groups/{id}/instance-pairs/{pairId}` - Update instance pair
- `DELETE /protection-groups/{id}/instance-pairs/{pairId}` - Delete instance pair
- `POST /protection-groups/{id}/configure-allow-launching` - Configure DRS launch settings

**Integration Approach**:
- Add new route handlers in `handle_api_gateway_request()`
- Add new operation handlers in `handle_direct_invocation()`
- Create new DynamoDB table: `InstancePairConfigurations`
- Reuse existing validation functions: `validate_unique_pg_name()`, `validate_server_assignments()`

---

### 2. Execution Handler (`lambda/execution-handler/index.py`)

**Size**: 5,826 lines  
**Purpose**: DRS execution lifecycle management

**Current Responsibilities**:
- Execute recovery plans (API Gateway entry point)
- Manage execution state (PENDING → RUNNING → COMPLETED/FAILED)
- Poll DRS job status
- Track wave completion
- Handle pause/resume workflows
- Check for existing recovery instances
- Validate DRS service limits

**Why INTEGRATE AllowLaunchingIntoThisInstance Execution Operations**:
- ✅ **Execution operations ARE execution operations** - Failover and failback are execution workflows, just like standard DRS recovery
- ✅ **Consistent with existing pattern** - Already manages execution lifecycle, job monitoring, and state tracking
- ✅ **Shared infrastructure** - Can reuse execution history table, job polling logic, and state management
- ✅ **Same API namespace** - Execution endpoints naturally belong under `/executions/*`
- ✅ **Unified monitoring** - All executions (standard DRS and AllowLaunchingIntoThisInstance) tracked in same table

**AllowLaunchingIntoThisInstance Operations to Add**:
```python
# NEW: Execute failover with AllowLaunchingIntoThisInstance
def execute_allow_launching_failover(body: Dict) -> Dict:
    """Execute failover using AllowLaunchingIntoThisInstance pattern"""
    # Validates instance pair configuration exists
    # Validates target instances are available
    # Captures private IPs from source instances
    # Starts DRS recovery with launchIntoEC2InstanceID
    # Tracks execution in execution_history_table
    # Returns execution ID

# NEW: Execute failback with reverse replication
def execute_allow_launching_failback(body: Dict) -> Dict:
    """Execute failback using reverse replication"""
    # Validates original source instances still exist
    # Invokes DRS Agent Deployer to install agents
    # Initiates reverse replication to original staging account
    # Monitors replication progress
    # Starts recovery back to original instances
    # Returns execution ID

# NEW: Monitor AllowLaunchingIntoThisInstance execution
def poll_allow_launching_execution(execution_id: str) -> Dict:
    """Poll status of AllowLaunchingIntoThisInstance execution"""
    # Queries DRS job status
    # Validates IP preservation
    # Updates execution history
    # Returns current status
```

**API Endpoints to Add**:
- `POST /executions/allow-launching/failover` - Execute failover
- `POST /executions/allow-launching/failback` - Execute failback
- `GET /executions/{id}/allow-launching/status` - Get execution status

**Integration Approach**:
- Add new route handlers in `handle_api_gateway_request()`
- Add new operation handlers for direct invocation
- Extend `execution_history_table` schema to include AllowLaunchingIntoThisInstance metadata
- Reuse existing job polling logic: `poll_drs_job_status()`

---

### 3. Query Handler (`lambda/query-handler/index.py`)

**Size**: 4,755 lines  
**Purpose**: Read-only DRS and EC2 infrastructure queries

**Current Responsibilities**:
- Query DRS source servers
- Query EC2 resources (subnets, security groups, instance types)
- Get DRS service limits
- Export configuration
- Get user permissions
- Validate staging accounts
- Get combined capacity

**Why INTEGRATE AllowLaunchingIntoThisInstance Query Operations**:
- ✅ **Query operations ARE query operations** - Instance matching, status checks, and validation are all read-only queries
- ✅ **Consistent with existing pattern** - Already queries DRS servers, EC2 instances, and infrastructure resources
- ✅ **Shared query logic** - Can reuse existing DRS and EC2 query functions
- ✅ **Same API namespace** - Query endpoints naturally belong under `/drs/*` or `/ec2/*`
- ✅ **No state changes** - All operations are read-only, matching query handler's purpose

**AllowLaunchingIntoThisInstance Operations to Add**:
```python
# NEW: Match source instances to target instances by Name tag
def match_instances_by_name(body: Dict) -> Dict:
    """Match source instances to pre-provisioned target instances"""
    # Queries DRS source servers in primary account
    # Queries EC2 instances in DR account
    # Matches by Name tag
    # Returns matched pairs and unmatched instances

# NEW: Validate instance pair configuration
def validate_instance_pairs(body: Dict) -> Dict:
    """Validate instance pairs are valid for AllowLaunchingIntoThisInstance"""
    # Validates target instances exist and are stopped
    # Validates no conflicts with other configurations
    # Validates network compatibility
    # Returns validation results

# NEW: Get AllowLaunchingIntoThisInstance execution status
def get_allow_launching_status(execution_id: str) -> Dict:
    """Get detailed status of AllowLaunchingIntoThisInstance execution"""
    # Queries execution history table
    # Queries DRS job status
    # Validates IP preservation
    # Returns detailed status

# NEW: Validate private IP preservation
def validate_ip_preservation(body: Dict) -> Dict:
    """Validate private IPs can be preserved during failover"""
    # Queries source instance IPs
    # Queries target subnet CIDR ranges
    # Validates IPs are within target subnet ranges
    # Returns validation results
```

**API Endpoints to Add**:
- `POST /drs/instances/match` - Match instances by Name tag
- `POST /drs/instances/validate-pairs` - Validate instance pairs
- `GET /drs/executions/{id}/status` - Get execution status
- `POST /drs/instances/validate-ip` - Validate IP preservation

**Integration Approach**:
- Add new route handlers in `handle_api_gateway_request()`
- Add new operation handlers in `handle_direct_invocation()`
- Reuse existing query functions: `get_drs_source_servers()`, `get_ec2_instances()`
- Add new validation functions for instance pairs and IP preservation

### 4. DRS Agent Deployer Handler (`lambda/drs-agent-deployer/index.py`)

**Purpose**: DRS agent installation on EC2 instances

**Current Responsibilities**:
- Install DRS agents on EC2 instances
- Configure agent replication settings
- Validate agent installation
- Support cross-account agent deployment

**Why KEEP as Separate Handler**:
- ✅ **Distinct infrastructure operation** - Agent deployment is a standalone operation that can be invoked by multiple features
- ✅ **Already exists** - No need to refactor existing working code
- ✅ **Reusable** - Can be invoked by standard DRS recovery, AllowLaunchingIntoThisInstance, and other features
- ✅ **Independent lifecycle** - Agent deployment has its own execution lifecycle separate from recovery operations

**AllowLaunchingIntoThisInstance Integration**:
- Execution handler will invoke DRS Agent Deployer during failback
- No changes needed to DRS Agent Deployer itself
- Integration via direct Lambda invocation

**Example Invocation**:
```python
# From execution-handler during failback
lambda_client.invoke(
    FunctionName='drs-agent-deployer-dev',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'source_account_id': dr_account_id,
        'staging_account_id': primary_account_id,
        'instance_ids': [recovery_instance_id],
        'region': region
    })
)
```

---

## Integration Strategy by Operation Type

### Configuration Operations → Data Management Handler

**Operations**:
1. Configure instance pairs (source-to-target mappings)
2. Update instance pair configuration
3. Delete instance pair configuration
4. Configure DRS launch settings (launchIntoEC2InstanceID)
5. Store IP preservation mappings

**Why Data Management Handler**:
- These are CRUD operations on configuration data
- Similar to Protection Group and Recovery Plan management
- Requires validation, conflict detection, and persistence
- No execution logic - just data management

**Implementation**:
- Add new DynamoDB table: `InstancePairConfigurations`
- Add new API endpoints under `/protection-groups/*` or `/config/*`
- Reuse existing validation functions
- Add new configuration management functions

---

### Execution Operations → Execution Handler

**Operations**:
1. Execute failover with AllowLaunchingIntoThisInstance
2. Execute failback with reverse replication
3. Monitor execution progress
4. Handle execution state transitions
5. Invoke DRS Agent Deployer for failback

**Why Execution Handler**:
- These are execution workflows with state management
- Similar to standard DRS recovery execution
- Requires job monitoring, state tracking, and error handling
- Uses same execution history table

**Implementation**:
- Add new execution functions for failover/failback
- Extend execution history table schema
- Add new API endpoints under `/executions/*`
- Reuse existing job polling and state management logic

---

### Query Operations → Query Handler

**Operations**:
1. Match instances by Name tag
2. Validate instance pairs
3. Get execution status
4. Validate IP preservation
5. List available target instances

**Why Query Handler**:
- These are read-only query operations
- Similar to existing DRS and EC2 queries
- No state changes - just data retrieval and validation
- Returns information for frontend decision-making

**Implementation**:
- Add new query functions for instance matching and validation
- Add new API endpoints under `/drs/*` or `/ec2/*`
- Reuse existing DRS and EC2 query logic
- Add new validation functions

---

## Comparison: Integrate vs New Handler

| Aspect | Integrate into Existing | Create New Handler |
|--------|------------------------|-------------------|
| **Architectural Consistency** | ✅ Maintains operation-type separation | ❌ Introduces feature-based separation |
| **Code Reuse** | ✅ Direct access to existing functions | ❌ Requires shared modules |
| **Maintainability** | ✅ Fewer handlers to maintain | ❌ More handlers to maintain |
| **Testing** | ✅ Extend existing test suites | ❌ New isolated test suites |
| **Deployment** | ✅ Deploy with existing handlers | ❌ New deployment pipeline |
| **API Design** | ✅ Consistent with existing endpoints | ❌ New endpoint namespace |
| **Complexity** | ⚠️ Adds to existing handlers | ✅ Isolated complexity |
| **Learning Curve** | ✅ Developers already know handlers | ❌ New handler to learn |

**Key Insight**: The slight increase in handler complexity is outweighed by maintaining architectural consistency and avoiding unnecessary handler proliferation.

---

## Decision Matrix

| Handler | Operation Type | Fit Score | Recommendation |
|---------|---------------|-----------|----------------|
| data-management-handler | Configuration (CRUD) | 9/10 | ✅ **INTEGRATE** |
| execution-handler | Execution (failover/failback) | 9/10 | ✅ **INTEGRATE** |
| query-handler | Query (read-only) | 9/10 | ✅ **INTEGRATE** |
| drs-agent-deployer | Infrastructure (agent install) | 10/10 | ✅ **KEEP SEPARATE** |
| **NEW handler** | Mixed operations | 2/10 | ❌ **DON'T CREATE** |

---

## Conclusion

**FINAL DECISION**: Integrate AllowLaunchingIntoThisInstance into existing handlers based on operation type.

**Rationale**:
1. ✅ **Maintains architectural consistency** - Handlers organized by operation type, not feature
2. ✅ **Maximizes code reuse** - Direct access to existing validation, query, and execution logic
3. ✅ **Simplifies deployment** - No new handler to deploy and maintain
4. ✅ **Consistent API design** - Endpoints follow existing patterns
5. ✅ **Easier for developers** - Work with familiar handlers and patterns
6. ✅ **Reduces handler proliferation** - Avoids creating handlers for every new feature

**Integration Summary**:
- **Data Management Handler**: Configuration operations (instance pairs, DRS settings)
- **Execution Handler**: Execution operations (failover, failback, monitoring)
- **Query Handler**: Query operations (instance matching, validation, status)
- **DRS Agent Deployer**: Remains separate (infrastructure operation)

**Implementation Approach**:
1. Add new functions to each handler for AllowLaunchingIntoThisInstance operations
2. Add new API routes in existing `handle_api_gateway_request()` functions
3. Add new operation handlers in existing `handle_direct_invocation()` functions
4. Extend existing DynamoDB tables or create new tables as needed
5. Reuse existing shared modules and validation logic

**Estimated Impact**:
- Data Management Handler: +500-700 lines (configuration operations)
- Execution Handler: +800-1000 lines (execution operations)
- Query Handler: +400-600 lines (query operations)
- Total: +1,700-2,300 lines distributed across 3 handlers

This is a reasonable increase that maintains handler focus while avoiding unnecessary handler creation.

---

**Decision Date**: 2026-02-03  
**Decision By**: AWS DRS Orchestration Project Team  
**Status**: ✅ APPROVED - Integrate into existing handlers
