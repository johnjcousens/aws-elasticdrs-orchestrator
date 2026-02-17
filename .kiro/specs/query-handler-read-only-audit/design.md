# Query Handler Read-Only Audit - Design

## Overview

This design document provides a detailed refactoring plan to move sync operations from query-handler to the appropriate handlers (data-management-handler and execution-handler), ensuring query-handler remains strictly read-only while maintaining clean architecture and avoiding Lambda size constraints.

## Architecture Principles

### Handler Responsibility Pattern (ENFORCED)

```
data-management-handler: CRUD Operations + Data Sync
  ├── Protection Groups, Recovery Plans
  ├── Tag sync, Launch configs
  ├── Recovery instance sync
  ├── Source server inventory sync (MOVE HERE)
  └── Staging account sync (MOVE HERE)

execution-handler: Recovery Actions + Wave Completion Sync
  ├── Start recovery, Cancel execution
  ├── Terminate instances, Apply configs
  └── Wave completion sync (MOVE HERE - poll_wave_status updates)

query-handler: Read Operations ONLY
  ├── List executions, Poll DRS jobs
  ├── Server status, Dashboard data
  ├── NO WRITES, NO SYNC OPERATIONS
  └── Audit logging for all read operations
```

### Dual Invocation Mode Architecture

The query-handler supports two invocation modes, each with different authentication and audit logging requirements:

**1. API Gateway Invocations (Frontend)**
```
User → CloudFront → API Gateway → Cognito JWT Validation → query-handler
                                                              ↓
                                                    RBAC Middleware Check
                                                              ↓
                                                    Audit Log (Cognito User)
```

**Authentication**: Cognito JWT token in Authorization header
**Principal**: Cognito user email from JWT claims
**RBAC**: Role-based permissions from Cognito groups
**Audit Trail**: User email, operation, timestamp, parameters

**2. Direct Lambda Invocations (Step Functions, EventBridge)**
```
Step Functions → Direct Lambda Invoke → query-handler
                                          ↓
                                IAM Principal Extraction
                                          ↓
                                Audit Log (IAM Role/User)
```

**Authentication**: IAM role/user from Lambda context
**Principal**: IAM ARN from context.invoked_function_arn
**RBAC**: Not applicable (service-to-service)
**Audit Trail**: IAM ARN, principal type, session name, operation, timestamp

### Key Design Decisions

1. **No New Lambda Functions**: All operations move to existing handlers
2. **EventBridge Direct Routing**: No cross-handler Lambda invocations
3. **Shared Utilities**: Extract common code to `lambda/shared/`
4. **Size Management**: Monitor Lambda deployment package sizes
5. **Zero Downtime**: Deploy new handlers before removing old code
6. **Dual Audit Trails**: Separate audit logging for API Gateway vs Direct Lambda invocations

## IAM Principal Extraction for Direct Lambda Invocations

### Overview

When query-handler is invoked directly (not via API Gateway), authentication is based on IAM roles/users rather than Cognito JWT tokens. The `iam_utils.py` module provides functions to extract IAM principal information from the Lambda context for audit logging.

### IAM Principal Types

**1. IAM Role (AssumedRole)**
```python
# Lambda context for Step Functions invocation
context.invoked_function_arn = "arn:aws:sts::891376951562:assumed-role/ExecutionRole/session-name"

# Extracted principal
{
    "principal_type": "AssumedRole",
    "principal_arn": "arn:aws:iam::891376951562:role/ExecutionRole",
    "session_name": "session-name",
    "account_id": "891376951562"
}
```

**2. IAM User**
```python
# Lambda context for direct user invocation
context.invoked_function_arn = "arn:aws:iam::891376951562:user/admin-user"

# Extracted principal
{
    "principal_type": "User",
    "principal_arn": "arn:aws:iam::891376951562:user/admin-user",
    "session_name": None,
    "account_id": "891376951562"
}
```

**3. AWS Service**
```python
# Lambda context for EventBridge invocation
context.invoked_function_arn = "arn:aws:events::891376951562:rule/inventory-sync"

# Extracted principal
{
    "principal_type": "Service",
    "principal_arn": "arn:aws:events::891376951562:rule/inventory-sync",
    "session_name": None,
    "account_id": "891376951562"
}
```

### Implementation Pattern

**Using iam_utils.extract_principal_from_context()**:

```python
from lambda.shared.iam_utils import extract_principal_from_context

def lambda_handler(event, context):
    """Query handler with dual invocation mode support."""
    
    # Determine invocation mode
    if "requestContext" in event:
        # API Gateway invocation - use Cognito JWT
        invocation_mode = "API_GATEWAY"
        user_email = event["requestContext"]["authorizer"]["claims"]["email"]
        principal_info = {
            "principal_type": "CognitoUser",
            "principal_arn": f"cognito:user:{user_email}",
            "session_name": None,
            "account_id": os.environ["AWS_ACCOUNT_ID"]
        }
    else:
        # Direct Lambda invocation - extract IAM principal
        invocation_mode = "DIRECT_LAMBDA"
        principal_info = extract_principal_from_context(context)
    
    # Log audit trail with principal information
    audit_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": event.get("operation"),
        "invocation_mode": invocation_mode,
        "principal_type": principal_info["principal_type"],
        "principal_arn": principal_info["principal_arn"],
        "session_name": principal_info.get("session_name"),
        "account_id": principal_info["account_id"],
        "parameters": mask_sensitive_parameters(event)
    }
    
    # Write audit log to DynamoDB
    write_audit_log(audit_log)
    
    # Process request
    return process_query(event, principal_info)
```

### Authorized Role Pattern Validation

The `iam_utils.py` module also provides role pattern validation to ensure only authorized roles can invoke Lambda functions directly:

```python
from lambda.shared.iam_utils import validate_authorized_role

# Define authorized role patterns
AUTHORIZED_ROLE_PATTERNS = [
    r"^arn:aws:iam::\d{12}:role/ExecutionRole$",
    r"^arn:aws:iam::\d{12}:role/StepFunctionsRole$",
    r"^arn:aws:iam::\d{12}:role/EventBridgeRole$"
]

def lambda_handler(event, context):
    """Query handler with role validation."""
    
    # Extract IAM principal
    principal_info = extract_principal_from_context(context)
    
    # Validate authorized role (for direct invocations only)
    if principal_info["principal_type"] == "AssumedRole":
        if not validate_authorized_role(principal_info["principal_arn"], AUTHORIZED_ROLE_PATTERNS):
            return error_response(403, "Unauthorized IAM role")
    
    # Process request
    return process_query(event, principal_info)
```

## RBAC Integration

## Detailed Refactoring Plan

### Operation 1: Source Server Inventory Sync

**Current Location**: `lambda/query-handler/index.py` lines 5631-6100

**Target Location**: `lambda/data-management-handler/index.py`

**Rationale**: Consistent with existing tag sync pattern (already in data-management-handler)

#### Code to Move

**Function**: `handle_sync_source_server_inventory()`
- **Lines**: 5631-6100 (approximately 470 lines)
- **DynamoDB Writes**:
  - `inventory_table.batch_writer()` - Batch writes to inventory table
  - `region_status_table.batch_writer()` - Batch writes to region status table
  - `inventory_table.delete_item()` - Deletes stale records
- **DRS/EC2 API Calls**:
  - `drs_client.describe_source_servers()` - Queries DRS across all accounts/regions
  - `ec2_client.describe_instances()` - Enriches with EC2 details

#### Integration Changes

**EventBridge Rule Update**:
```yaml
# Current (WRONG):
Target: query-handler
Input: {"operation": "sync_inventory"}

# New (CORRECT):
Target: data-management-handler
Input: {"operation": "handle_sync_source_server_inventory"}
```

**CloudFormation Template**:
```yaml
# cfn/nested-stacks/eventbridge-rules.yaml
SourceServerInventorySyncRule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: rate(5 minutes)
    Targets:
      - Arn: !GetAtt DataManagementHandler.Arn  # Changed from QueryHandler
        Input: '{"operation": "handle_sync_source_server_inventory"}'
```

**API Gateway Routes**: No changes needed (not exposed via API)

#### Implementation Steps

1. Copy `handle_sync_source_server_inventory()` to data-management-handler
2. Update EventBridge rule to target data-management-handler
3. Deploy CloudFormation stack update
4. Test inventory sync operation
5. Remove function from query-handler
6. Deploy final cleanup

### Operation 2: Staging Account Sync

**Current Location**: `lambda/query-handler/index.py` lines 5417-5630

**Target Location**: `lambda/data-management-handler/index.py`

**Rationale**: Account management operation, consistent with target account CRUD

#### Code to Move

**Function**: `handle_sync_staging_accounts()`
- **Lines**: 5417-5630 (approximately 214 lines)
- **DRS API Writes**:
  - `extend_source_server()` - DRS API write operation to extend servers
- **Helper Function**: `auto_extend_staging_servers()`
  - May need to move to `lambda/shared/staging_utils.py` if reused

#### Integration Changes

**EventBridge Rule Update**:
```yaml
# Current (WRONG):
Target: query-handler
Input: {"operation": "sync_staging_accounts"}

# New (CORRECT):
Target: data-management-handler
Input: {"operation": "handle_sync_staging_accounts"}
```

**CloudFormation Template**:
```yaml
# cfn/nested-stacks/eventbridge-rules.yaml
StagingAccountSyncRule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: rate(15 minutes)
    Targets:
      - Arn: !GetAtt DataManagementHandler.Arn  # Changed from QueryHandler
        Input: '{"operation": "handle_sync_staging_accounts"}'
```

**API Gateway Routes**: No changes needed (not exposed via API)

#### Implementation Steps

1. Copy `handle_sync_staging_accounts()` to data-management-handler
2. Evaluate if `auto_extend_staging_servers()` should move to shared utility
3. Update EventBridge rule to target data-management-handler
4. Deploy CloudFormation stack update
5. Test staging account sync operation
6. Remove functions from query-handler
7. Deploy final cleanup

### Operation 3: Wave Status Polling Updates

**Current Location**: `lambda/query-handler/index.py` lines 2588-2900+

**Target Location**: Split between query-handler (reads) and execution-handler (writes)

**Rationale**: Wave completion sync is part of recovery actions (execution-handler responsibility)

#### Analysis: Read vs Write Operations

**Read Operations (KEEP in query-handler)**:
- `drs_client.describe_jobs()` - Query DRS job status
- `drs_client.describe_job_log_items()` - Query job events
- Server launch status tracking (no DynamoDB writes)

**Write Operations (MOVE to execution-handler)**:
- `get_execution_history_table().update_item()` - Updates execution status
  - Line 2634: Update cancellation status
  - Line 2870: Update pause status
  - Line 2899: Update pause before wave
  - Line 2962: Update completion status
- All DynamoDB writes for wave completion, pause, resume, cancel

#### Refactoring Strategy

**Option A: Split Function (RECOMMENDED)**
- Keep `poll_wave_status()` in query-handler for DRS job queries
- Create `update_wave_completion_status()` in execution-handler for DynamoDB writes
- Step Functions calls both handlers sequentially

**Option B: Move Entire Function**
- Move entire `poll_wave_status()` to execution-handler
- Step Functions calls execution-handler for wave polling
- Simpler but execution-handler becomes larger

**Decision**: Use Option A (split function) to maintain clean separation

#### Code Changes

**query-handler** (Read-Only Version):
```python
def poll_wave_status(state: Dict) -> Dict:
    """
    Poll DRS job status and track server launch progress (READ-ONLY).
    
    Returns job status and server launch progress WITHOUT updating DynamoDB.
    Execution-handler is responsible for persisting wave completion status.
    """
    # Query DRS job status
    job_response = drs_client.describe_jobs(filters={"jobIDs": [job_id]})
    
    # Track server launch progress
    # ... (existing logic for counting launched/failed servers)
    
    # Return status WITHOUT DynamoDB writes
    return {
        "job_status": job_status,
        "launched_count": launched_count,
        "failed_count": failed_count,
        "server_statuses": server_statuses,
        "wave_completed": wave_completed,
        # NO DynamoDB updates here
    }
```

**execution-handler** (New Function):
```python
def update_wave_completion_status(execution_id: str, plan_id: str, 
                                   wave_number: int, status: str, 
                                   wave_data: Dict) -> Dict:
    """
    Update execution history with wave completion status.
    
    Called by Step Functions after query-handler polls DRS job status.
    Persists wave completion, pause, resume, and cancellation states.
    """
    # Update execution history table
    get_execution_history_table().update_item(
        Key={"executionId": execution_id, "planId": plan_id},
        UpdateExpression="SET #status = :status, ...",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":status": status,
            # ... other wave completion data
        },
    )
    
    return {"statusCode": 200, "message": "Wave status updated"}
```

#### Step Functions State Machine Update

**Current (WRONG)**:
```json
{
  "WavePoll": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:query-handler",
    "Parameters": {
      "operation": "poll_wave_status",
      "state.$": "$"
    },
    "Next": "CheckWaveComplete"
  }
}
```

**New (CORRECT)**:
```json
{
  "WavePoll": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:query-handler",
    "Parameters": {
      "operation": "poll_wave_status",
      "state.$": "$"
    },
    "Next": "UpdateWaveStatus"
  },
  "UpdateWaveStatus": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:execution-handler",
    "Parameters": {
      "action": "update_wave_completion_status",
      "executionId.$": "$.execution_id",
      "planId.$": "$.plan_id",
      "waveNumber.$": "$.current_wave_number",
      "status.$": "$.status",
      "waveData.$": "$"
    },
    "Next": "CheckWaveComplete"
  }
}
```

#### Implementation Steps

1. Create `update_wave_completion_status()` in execution-handler
2. Refactor `poll_wave_status()` in query-handler to remove DynamoDB writes
3. Update Step Functions state machine definition
4. Deploy CloudFormation stack update
5. Test wave polling with DynamoDB updates
6. Verify no data loss during wave transitions
7. Deploy final cleanup

## Shared Utilities Strategy

### Existing Shared Utilities (Already Available)

The codebase already has 18 comprehensive shared utility modules in `lambda/shared/` that will be leveraged during refactoring:

**Core Utilities (Already Exist):**

**`drs_utils.py` (1,172 lines)** - DRS API normalization and operations
- `normalize_drs_response()` - Convert PascalCase to camelCase at AWS API boundaries
- `extract_recovery_instance_details()` - Extract normalized instance data
- `batch_describe_ec2_instances()` - Efficient EC2 instance queries with batching
- `enrich_server_data()` - Enrich servers with DRS and EC2 details
- `drs_api_call_with_backoff()` - Rate-limited DRS API calls with exponential backoff
- `transform_drs_server_for_frontend()` - Transform raw DRS server to frontend format
- **Refactoring Usage**: Inventory sync already uses these functions - no changes needed

**`cross_account.py`** - Cross-account IAM role assumption (hub-and-spoke pattern)
- `determine_target_account_context()` - Determine target account from recovery plan
- `create_drs_client()` - Create DRS client with optional cross-account assumption
- `create_ec2_client()` - Create EC2 client with optional cross-account assumption
- `get_cross_account_session()` - Assume cross-account IAM role via STS
- **Refactoring Usage**: Inventory and staging sync already use these - maintain imports

**`account_utils.py`** - Account validation and management
- `construct_role_arn()` - Build standardized role ARN from account ID
- `validate_account_id()` - Validate 12-digit account ID format
- `get_target_accounts()` - List all configured target accounts from DynamoDB
- `validate_target_account()` - Validate account access and permissions
- **Refactoring Usage**: All account operations already use these functions

**`execution_utils.py`** - Execution state management
- `can_terminate_execution()` - Determine if execution can be terminated
- `normalize_wave_status()` - Normalize wave status to lowercase
- `get_execution_progress()` - Calculate progress metrics for dashboard
- **Refactoring Usage**: Wave polling already uses `normalize_wave_status()` - maintain import

**`response_utils.py`** - API Gateway response formatting
- `response()` - API Gateway response with CORS and security headers
- `error_response()` - Standardized error response for direct invocations
- `DecimalEncoder` - JSON encoder for DynamoDB Decimal types
- **Refactoring Usage**: All API operations already use these functions

**`security_utils.py`** - Input validation and sanitization
- `sanitize_string()` - Remove dangerous characters with performance optimization
- `validate_drs_server_id()` - Validate DRS server ID format (s-[a-f0-9]{17})
- `validate_aws_account_id()` - Validate 12-digit account ID
- `sanitize_dynamodb_input()` - Sanitize data before DynamoDB write
- **Refactoring Usage**: All input operations already use these functions

**`notifications.py`** - SNS notifications for execution lifecycle
- `send_execution_started()`, `send_execution_completed()`, `send_execution_failed()`
- `send_wave_completed()`, `send_wave_failed()`
- `publish_recovery_plan_notification()` - Publish plan-scoped notifications
- **Refactoring Usage**: Non-blocking notifications for all major operations

**Supporting Utilities (Already Exist):**
- `drs_regions.py` - Centralized list of DRS-available regions
- `drs_limits.py` - DRS service limits and quotas
- `iam_utils.py` - IAM role and permission utilities
- `rbac_middleware.py` - Role-based access control
- `launch_config_service.py` - Launch configuration management
- `launch_config_validation.py` - Launch config validation
- `conflict_detection.py` (1,172 lines) - Conflict detection logic
- `config_merge.py` - Configuration merging utilities
- `staging_account_models.py` - Staging account data models

### Key Patterns (Already Established)

**Data Format Convention:**
- All data uses camelCase (DynamoDB storage and API responses)
- AWS API responses normalized to camelCase at boundaries using `normalize_drs_response()`
- NO snake_case fallback patterns - data must be in correct format
- **Refactoring Impact**: Sync operations already follow this pattern - no changes needed

**Cross-Account Pattern:**
- Hub-and-Spoke: Hub assumes IAM role in spoke accounts via STS
- `determine_target_account_context()` extracts account from recovery plan
- `create_drs_client()` handles optional cross-account assumption
- **Refactoring Impact**: Inventory and staging sync already use this pattern - maintain imports

**DynamoDB Pattern:**
- Lazy initialization: Resources initialized on first use
- Decimal handling: Automatic conversion via `DecimalEncoder`
- Batch operations: Use `batch_writer()` for efficient writes
- **Refactoring Impact**: All sync operations already follow this pattern - no changes needed

**Validation Pattern:**
- Comprehensive input validation at entry points
- Sanitization with performance optimizations (skip safe strings)
- Account ID validation: `validate_account_id()` for 12-digit format
- Server ID validation: `validate_drs_server_id()` for s-[a-f0-9]{17} format
- **Refactoring Impact**: All operations already validated - maintain security_utils imports

**Error Handling Pattern:**
- Rate limiting: `drs_api_call_with_backoff()` with exponential backoff
- Non-blocking notifications: SNS notifications don't block operations
- Standardized responses: `response()` and `error_response()` for consistency
- **Refactoring Impact**: All operations already follow this pattern - no changes needed

### Refactoring Strategy (Leverage Existing Utilities + New Extractions)

**Phase 1: Move Sync Operations (No New Utilities Needed)**

All sync operations already use existing shared utilities - no extraction phase needed:

**1. Move `handle_sync_source_server_inventory()` to data-management-handler**
   - **Existing imports to maintain**:
     ```python
     from lambda.shared.drs_utils import normalize_drs_response, batch_describe_ec2_instances
     from lambda.shared.cross_account import create_drs_client, create_ec2_client
     from lambda.shared.account_utils import get_target_accounts
     from lambda.shared.security_utils import sanitize_dynamodb_input
     ```
   - **No new utilities needed** - all DRS/EC2 operations already use shared functions
   - **Action**: Copy function with existing imports to data-management-handler

**2. Move `handle_sync_staging_accounts()` to data-management-handler**
   - **Existing imports to maintain**:
     ```python
     from lambda.shared.staging_account_models import StagingAccount
     from lambda.shared.drs_utils import normalize_drs_response, drs_api_call_with_backoff
     from lambda.shared.cross_account import create_drs_client
     from lambda.shared.account_utils import validate_account_id
     ```
   - **No new utilities needed** - staging models and DRS operations already shared
   - **Action**: Copy function with existing imports to data-management-handler

**3. Split `poll_wave_status()` (read in query-handler, write in execution-handler)**
   - **query-handler keeps** (read-only):
     ```python
     from lambda.shared.drs_utils import normalize_drs_response
     from lambda.shared.execution_utils import normalize_wave_status
     ```
   - **execution-handler adds** (write operations):
     ```python
     from lambda.shared.execution_utils import normalize_wave_status
     from lambda.shared.response_utils import DecimalEncoder
     from lambda.shared.notifications import send_wave_completed, send_wave_failed
     ```
   - **No new utilities needed** - execution state management already shared
   - **Action**: Split function, maintain existing imports in both handlers

**Phase 2: Extract Large Functions to Shared Utilities**

Three functions exceed 400 lines and should be extracted to reduce handler sizes and improve maintainability:

### 2.1 High Priority: Wave Status Service (Supports FR4)

**Purpose**: Support `poll_wave_status()` split by extracting reusable wave status logic

**New Module**: `lambda/shared/wave_status_service.py`

**Functions to Extract**:

```python
def calculate_wave_progress(launched_count: int, failed_count: int, 
                           total_count: int) -> Dict[str, Any]:
    """
    Calculate wave progress metrics.
    
    Extracted from query-handler poll_wave_status() lines 2700-2750.
    Reusable by both query-handler (read) and execution-handler (write).
    
    Args:
        launched_count: Number of successfully launched servers
        failed_count: Number of failed server launches
        total_count: Total number of servers in wave
        
    Returns:
        Dictionary with progress metrics:
        - percent_complete: Percentage of wave completion (0-100)
        - remaining_count: Number of servers not yet launched
        - success_rate: Percentage of successful launches
    """
    pass

def determine_wave_completion(job_status: str, 
                              server_statuses: List[Dict]) -> bool:
    """
    Determine if wave is complete based on DRS job status and server states.
    
    Extracted from query-handler poll_wave_status() lines 2800-2850.
    Reusable by both query-handler (read) and execution-handler (write).
    
    Args:
        job_status: DRS job status (PENDING, STARTED, COMPLETED, etc.)
        server_statuses: List of server status dictionaries
        
    Returns:
        True if wave is complete, False otherwise
    """
    pass
```

**Impact**:
- Reduces `poll_wave_status()` from 420 to ~200 lines (read-only version)
- Supports Task 4 (Phase 2): Split wave status polling
- Aligns with FR4: Move Wave Status Updates to Execution Handler
- Reusable by both query-handler and execution-handler

### 2.2 Medium Priority: Protection Group Validation (Supports FR5)

**Purpose**: Reduce `create_protection_group()` (429 lines) and `update_protection_group()` (523 lines)

**New Module**: `lambda/shared/protection_group_validation.py`

**Functions to Extract**:

```python
def validate_protection_group_name(name: str, 
                                   existing_groups: List[Dict]) -> None:
    """
    Validate protection group name (uniqueness, format, length).
    
    Extracted from data-management-handler create_protection_group() 
    lines 1570-1590.
    
    Args:
        name: Protection group name to validate
        existing_groups: List of existing protection groups
        
    Raises:
        ValidationError: If name is invalid or already exists
    """
    pass

def validate_protection_group_tags(tags: List[str]) -> None:
    """
    Validate tag format and existence.
    
    Extracted from data-management-handler create_protection_group() 
    lines 1600-1620.
    
    Args:
        tags: List of tag names to validate
        
    Raises:
        ValidationError: If any tag is invalid
    """
    pass

def validate_protection_group_servers(server_ids: List[str], 
                                     region: str) -> None:
    """
    Validate server IDs and check for conflicts.
    
    Extracted from data-management-handler create_protection_group() 
    lines 1630-1680.
    
    Args:
        server_ids: List of DRS source server IDs
        region: AWS region where servers are located
        
    Raises:
        ValidationError: If any server ID is invalid
        ConflictError: If server is already in another group
    """
    pass

def check_protection_group_quota(current_count: int) -> None:
    """
    Check if protection group quota exceeded.
    
    Extracted from data-management-handler create_protection_group() 
    lines 1690-1700.
    
    Args:
        current_count: Current number of protection groups
        
    Raises:
        QuotaExceededError: If quota is exceeded
    """
    pass
```

**Impact**:
- Reduces `create_protection_group()` from 429 to ~200 lines
- Reduces `update_protection_group()` from 523 to ~250 lines (reuses validation)
- Aligns with FR5: Maintain Lambda Size Constraints
- Aligns with NFR3: Code Maintainability

### 2.3 Medium Priority: Server Resolution Service (Supports FR5, NFR3)

**Purpose**: Extract tag-based server resolution logic reusable across handlers

**New Module**: `lambda/shared/server_resolution_service.py`

**Functions to Extract**:

```python
def query_inventory_servers_by_tags(tags: List[str], 
                                    region: str) -> List[Dict[str, Any]]:
    """
    Query inventory table for servers matching tags.
    
    Extracted from data-management-handler create_protection_group() 
    lines 1750-1850.
    
    Uses existing shared utilities:
    - drs_utils.normalize_drs_response()
    - cross_account.create_drs_client()
    
    Args:
        tags: List of tag names to match
        region: AWS region to query
        
    Returns:
        List of server dictionaries matching tags
    """
    pass

def resolve_servers_from_tags_and_ids(tags: List[str], 
                                     server_ids: List[str],
                                     region: str) -> List[str]:
    """
    Resolve final server list from combination of tags and explicit IDs.
    
    Handles deduplication and validation.
    
    Args:
        tags: List of tag names to resolve
        server_ids: List of explicit server IDs
        region: AWS region
        
    Returns:
        Deduplicated list of server IDs
    """
    pass
```

**Impact**:
- Reduces `create_protection_group()` by ~100 lines
- Reduces `update_protection_group()` by ~100 lines (reuses resolution)
- Reusable across data-management-handler operations
- Aligns with FR5: Maintain Lambda Size Constraints
- Aligns with NFR3: Code Maintainability

**Phase 2 Decision Criteria**:
- Extract ONLY if function is used by 2+ handlers
- Extract ONLY if function is 50+ lines and reusable
- Prefer keeping code in handlers if used once

**Benefits of Phase 2 Extractions**:
- ✅ Reduces handler sizes significantly (create_protection_group: 429→200, update_protection_group: 523→250, poll_wave_status: 420→200)
- ✅ Supports core refactoring goals (FR4, FR5, NFR3)
- ✅ Improves code reusability and maintainability
- ✅ Keeps all handlers under 15,000 lines
- ✅ Consistent with existing shared utility patterns

**Implementation Timeline**:
1. **Week 1**: Move sync operations with existing imports (Phase 1)
2. **Week 2**: Create new shared utilities (Phase 2) - wave_status_service.py, protection_group_validation.py, server_resolution_service.py
3. **Week 3**: Update EventBridge rules and Step Functions
4. **Week 4**: Test all sync operations, remove old code

## Large Function Extraction Analysis

### Overview

During the refactoring audit, three functions exceeding 400 lines were identified that should be addressed to maintain code quality and handler size constraints:

1. **data-management-handler: `create_protection_group()` - 429 lines**
2. **data-management-handler: `update_protection_group()` - 523 lines**
3. **query-handler: `poll_wave_status()` - 420 lines** ⚠️ CRITICAL FOR REFACTORING

### Extraction Priority Matrix

| Function | Lines | Priority | Refactoring Alignment | Target Size After Extraction |
|----------|-------|----------|----------------------|------------------------------|
| `poll_wave_status()` | 420 | **HIGH** | Directly supports FR4 (Task 4) | ~200 lines (read-only) |
| `create_protection_group()` | 429 | **MEDIUM** | Supports FR5 (size constraints) | ~200 lines |
| `update_protection_group()` | 523 | **MEDIUM** | Supports FR5 (size constraints) | ~250 lines |

### Enhanced Extraction Details

This section provides line-by-line breakdown of what code blocks should be extracted from each large function, with specific line numbers and extraction targets.

#### Function 1: create_protection_group() - 429 Lines (1561-1990)

**Extraction Breakdown**:

| Line Range | Code Block | Extraction Target | Lines |
|------------|------------|-------------------|-------|
| 1570-1590 | Name validation (uniqueness, format, length) | `protection_group_validation.py::validate_protection_group_name()` | 20 |
| 1600-1620 | Tag format validation | `protection_group_validation.py::validate_protection_group_tags()` | 20 |
| 1630-1680 | Server ID validation and conflict checks | `protection_group_validation.py::validate_protection_group_servers()` | 50 |
| 1690-1700 | Protection group quota check | `protection_group_validation.py::check_protection_group_quota()` | 10 |
| 1750-1850 | Tag-based server resolution from inventory | `server_resolution_service.py::query_inventory_servers_by_tags()` | 100 |
| 1860-1900 | Server deduplication and final resolution | `server_resolution_service.py::resolve_servers_from_tags_and_ids()` | 40 |
| 1910-1990 | DynamoDB write, response formatting (KEEP) | Remains in create_protection_group() | 80 |

**Total Extractable**: ~240 lines → Reduces function to ~189 lines

**Shared Utilities Created**:
- `protection_group_validation.py` - 100 lines (4 validation functions)
- `server_resolution_service.py` - 140 lines (2 resolution functions)

#### Function 2: update_protection_group() - 523 Lines (2067-2590)

**Extraction Breakdown**:

| Line Range | Code Block | Extraction Target | Lines |
|------------|------------|-------------------|-------|
| 2080-2100 | Optimistic locking version check | `optimistic_locking_service.py::check_version_conflict()` | 20 |
| 2110-2130 | Name validation (reuse from create) | `protection_group_validation.py::validate_protection_group_name()` | REUSE |
| 2140-2160 | Tag validation (reuse from create) | `protection_group_validation.py::validate_protection_group_tags()` | REUSE |
| 2170-2220 | Server validation (reuse from create) | `protection_group_validation.py::validate_protection_group_servers()` | REUSE |
| 2230-2330 | Tag resolution (reuse from create) | `server_resolution_service.py::resolve_servers_from_tags_and_ids()` | REUSE |
| 2340-2440 | DynamoDB update expression building | `dynamodb_update_builder.py::build_update_expression()` | 100 |
| 2450-2590 | DynamoDB update, response formatting (KEEP) | Remains in update_protection_group() | 140 |

**Total Extractable**: ~120 lines (new) + reuse validation → Reduces function to ~263 lines

**Shared Utilities Created**:
- `optimistic_locking_service.py` - 50 lines (version conflict checking)
- `dynamodb_update_builder.py` - 100 lines (safe update expression builder)
- Reuses `protection_group_validation.py` (4 functions)
- Reuses `server_resolution_service.py` (2 functions)

#### Function 3: poll_wave_status() - 420 Lines (2588-3008)

**Extraction Breakdown**:

| Line Range | Code Block | Extraction Target | Lines |
|------------|------------|-------------------|-------|
| 2600-2650 | DRS job status query and normalization | Remains in poll_wave_status() (READ) | 50 |
| 2660-2750 | Server launch progress tracking | Remains in poll_wave_status() (READ) | 90 |
| 2760-2810 | Wave progress calculation | `wave_status_service.py::calculate_wave_progress()` | 50 |
| 2820-2870 | Wave completion determination | `wave_status_service.py::determine_wave_completion()` | 50 |
| 2880-2950 | DRS job polling with server state tracking | `drs_job_polling_service.py::poll_drs_job_with_servers()` | 70 |
| 2960-3008 | DynamoDB execution updates (MOVE) | execution-handler: `update_wave_completion_status()` | 48 |

**Total Extractable**: ~170 lines → Reduces function to ~200 lines (re

**Current State**:
- **Location**: `lambda/query-handler/index.py` lines 2588-2900+
- **Size**: 420 lines
- **Violations**: Performs DynamoDB writes (violates read-only principle)
- **Refactoring Alignment**: Directly implements FR4 and Task 4 (Phase 2)

**Extraction Strategy**:

**Step 1: Create wave_status_service.py (Optional Helper)**

```python
# lambda/shared/wave_status_service.py

from typing import Dict, List, Any


def calculate_wave_progress(
    launched_count: int,
    failed_count: int,
    total_count: int
) -> Dict[str, Any]:
    """
    Calculate wave progress metrics.
    
    Extracted from query-handler poll_wave_status() lines 2700-2750.
    Reusable by both query-handler (read) and execution-handler (write).
    
    Args:
        launched_count: Number of successfully launched servers
        failed_count: Number of failed server launches
        total_count: Total number of servers in wave
        
    Returns:
        Dictionary with progress metrics:
        - percent_complete: Percentage of wave completion (0-100)
        - remaining_count: Number of servers not yet launched
        - success_rate: Percentage of successful launches
    """
    if total_count == 0:
        return {
            "percent_complete": 0,
            "remaining_count": 0,
            "success_rate": 0
        }
    
    completed_count = launched_count + failed_count
    percent_complete = (completed_count / total_count) * 100
    remaining_count = total_count - completed_count
    success_rate = (
        (launched_count / completed_count) * 100
        if completed_count > 0
        else 0
    )
    
    return {
        "percent_complete": round(percent_complete, 2),
        "remaining_count": remaining_count,
        "success_rate": round(success_rate, 2)
    }


def determine_wave_completion(
    job_status: str,
    server_statuses: List[Dict]
) -> bool:
    """
    Determine if wave is complete based on DRS job status and server states.
    
    Extracted from query-handler poll_wave_status() lines 2800-2850.
    Reusable by both query-handler (read) and execution-handler (write).
    
    Args:
        job_status: DRS job status (PENDING, STARTED, COMPLETED, etc.)
        server_statuses: List of server status dictionaries
        
    Returns:
        True if wave is complete, False otherwise
    """
    # Job must be in terminal state
    if job_status not in ["COMPLETED", "FAILED"]:
        return False
    
    # All servers must be in terminal state
    for server in server_statuses:
        server_state = server.get("state", "").upper()
        if server_state not in ["LAUNCHED", "FAILED", "TERMINATED"]:
            return False
    
    return True
```

**Step 2: Refactor query-handler (Read-Only Version)**

```python
# lambda/query-handler/index.py

from lambda.shared.drs_utils import normalize_drs_response
from lambda.shared.execution_utils import normalize_wave_status
from lambda.shared.wave_status_service import (
    calculate_wave_progress,
    determine_wave_completion
)


def poll_wave_status(state: Dict) -> Dict:
    """
    Poll DRS job status and track server launch progress (READ-ONLY).
    
    Returns job status and server launch progress WITHOUT updating DynamoDB.
    Execution-handler is responsible for persisting wave completion status.
    
    This function has been refactored to remove all DynamoDB writes as part
    of the query-handler read-only audit (FR4).
    
    Args:
        state: Step Functions state containing execution context
        
    Returns:
        Dictionary with wave status:
        - job_status: DRS job status
        - launched_count: Number of successfully launched servers
        - failed_count: Number of failed server launches
        - server_statuses: List of server status dictionaries
        - wave_completed: Boolean indicating wave completion
        - progress_metrics: Progress calculation results
    """
    # Extract execution context
    job_id = state.get("job_id")
    execution_id = state.get("execution_id")
    wave_number = state.get("current_wave_number")
    
    # Query DRS job status (READ-ONLY)
    drs_client = boto3.client("drs")
    job_response = drs_client.describe_jobs(
        filters={"jobIDs": [job_id]}
    )
    
    if not job_response.get("items"):
        return {
            "error": "Job not found",
            "job_id": job_id
        }
    
    job = normalize_drs_response(job_response["items"][0])
    job_status = normalize_wave_status(job.get("status"))
    
    # Track server launch progress (READ-ONLY)
    server_statuses = []
    launched_count = 0
    failed_count = 0
    total_count = len(state.get("servers", []))
    
    for server in state.get("servers", []):
        server_id = server.get("sourceServerId")
        
        # Query server launch status from DRS job
        server_status = {
            "sourceServerId": server_id,
            "state": "PENDING"  # Default state
        }
        
        # Extract server state from job participating servers
        for participating_server in job.get("participatingServers", []):
            if participating_server.get("sourceServerId") == server_id:
                launch_status = participating_server.get("launchStatus")
                server_status["state"] = launch_status
                
                if launch_status == "LAUNCHED":
                    launched_count += 1
                elif launch_status == "FAILED":
                    failed_count += 1
                
                break
        
        server_statuses.append(server_status)
    
    # Calculate progress metrics
    progress_metrics = calculate_wave_progress(
        launched_count,
        failed_count,
        total_count
    )
    
    # Determine wave completion
    wave_completed = determine_wave_completion(
        job_status,
        server_statuses
    )
    
    # Return status WITHOUT DynamoDB writes
    return {
        "job_status": job_status,
        "job_id": job_id,
        "execution_id": execution_id,
        "wave_number": wave_number,
        "launched_count": launched_count,
        "failed_count": failed_count,
        "total_count": total_count,
        "server_statuses": server_statuses,
        "wave_completed": wave_completed,
        "progress_metrics": progress_metrics,
        # NO DynamoDB updates here - execution-handler handles persistence
    }
```

**Step 3: Create execution-handler (Write Operations)**

```python
# lambda/execution-handler/index.py

from lambda.shared.execution_utils import normalize_wave_status
from lambda.shared.response_utils import DecimalEncoder
from lambda.shared.notifications import (
    send_wave_completed,
    send_wave_failed
)


def update_wave_completion_status(
    execution_id: str,
    plan_id: str,
    wave_number: int,
    status: str,
    wave_data: Dict
) -> Dict:
    """
    Update execution history with wave completion status.
    
    Called by Step Functions after query-handler polls DRS job status.
    Persists wave completion, pause, resume, and cancellation states.
    
    This function was created as part of the query-handler read-only audit
    to move DynamoDB writes from query-handler to execution-handler (FR4).
    
    Args:
        execution_id: Unique execution identifier
        plan_id: Recovery plan identifier
        wave_number: Current wave number
        status: Wave status (completed, failed, paused, etc.)
        wave_data: Complete wave status data from poll_wave_status()
        
    Returns:
        Dictionary with status code and message
    """
    # Get execution history table
    execution_table = get_execution_history_table()
    
    # Normalize status
    normalized_status = normalize_wave_status(status)
    
    # Build update expression
    update_expression = (
        "SET #status = :status, "
        "#wave_number = :wave_number, "
        "#launched_count = :launched_count, "
        "#failed_count = :failed_count, "
        "#total_count = :total_count, "
        "#wave_completed = :wave_completed, "
        "#last_updated = :last_updated"
    )
    
    expression_attribute_names = {
        "#status": "status",
        "#wave_number": "waveNumber",
        "#launched_count": "launchedCount",
        "#failed_count": "failedCount",
        "#total_count": "totalCount",
        "#wave_completed": "waveCompleted",
        "#last_updated": "lastUpdated"
    }
    
    expression_attribute_values = {
        ":status": normalized_status,
        ":wave_number": wave_number,
        ":launched_count": wave_data.get("launched_count", 0),
        ":failed_count": wave_data.get("failed_count", 0),
        ":total_count": wave_data.get("total_count", 0),
        ":wave_completed": wave_data.get("wave_completed", False),
        ":last_updated": datetime.utcnow().isoformat()
    }
    
    # Update execution history table
    execution_table.update_item(
        Key={
            "executionId": execution_id,
            "planId": plan_id
        },
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values
    )
    
    # Send notifications (non-blocking)
    if wave_data.get("wave_completed"):
        if normalized_status == "completed":
            send_wave_completed(execution_id, plan_id, wave_number)
        elif normalized_status == "failed":
            send_wave_failed(execution_id, plan_id, wave_number)
    
    return {
        "statusCode": 200,
        "message": f"Wave {wave_number} status updated to {normalized_status}"
    }
```

**Impact**:
- ✅ Reduces `poll_wave_status()` from 420 to ~200 lines (read-only version)
- ✅ New `update_wave_completion_status()` in execution-handler (~100 lines)
- ✅ Maintains clean separation: query-handler = read, execution-handler = write
- ✅ Directly implements FR4: Move Wave Status Updates to Execution Handler
- ✅ Aligns with spec's core goal: "query-handler performs ZERO DynamoDB writes"

#### 2. create_protection_group() Extraction (MEDIUM PRIORITY)

**Current State**:
- **Location**: `lambda/data-management-handler/index.py` lines 1570-1990
- **Size**: 429 lines
- **Refactoring Alignment**: Supports FR5 (Maintain Lambda Size Constraints)
- **Note**: This function is NOT moving during refactoring (stays in data-management-handler)

**Extraction Strategy**:

**Step 1: Create protection_group_validation.py**

```python
# lambda/shared/protection_group_validation.py

from typing import List, Dict
from lambda.shared.security_utils import (
    validate_drs_server_id,
    sanitize_string
)


class ValidationError(Exception):
    """Validation error exception."""
    pass


class ConflictError(Exception):
    """Conflict error exception."""
    pass


class QuotaExceededError(Exception):
    """Quota exceeded error exception."""
    pass


def validate_protection_group_name(
    name: str,
    existing_groups: List[Dict]
) -> None:
    """
    Validate protection group name (uniqueness, format, length).
    
    Extracted from data-management-handler create_protection_group()
    lines 1570-1590.
    
    Args:
        name: Protection group name to validate
        existing_groups: List of existing protection groups
        
    Raises:
        ValidationError: If name is invalid or already exists
    """
    # Validate name format
    if not name or not isinstance(name, str):
        raise ValidationError("Protection group name is required")
    
    # Sanitize name
    sanitized_name = sanitize_string(name)
    
    # Validate length (3-128 characters)
    if len(sanitized_name) < 3:
        raise ValidationError(
            "Protection group name must be at least 3 characters"
        )
    
    if len(sanitized_name) > 128:
        raise ValidationError(
            "Protection group name must not exceed 128 characters"
        )
    
    # Check uniqueness
    for group in existing_groups:
        if group.get("name", "").lower() == sanitized_name.lower():
            raise ConflictError(
                f"Protection group '{sanitized_name}' already exists"
            )


def validate_protection_group_tags(tags: List[str]) -> None:
    """
    Validate tag format and existence.
    
    Extracted from data-management-handler create_protection_group()
    lines 1600-1620.
    
    Args:
        tags: List of tag names to validate
        
    Raises:
        ValidationError: If any tag is invalid
    """
    if not tags:
        return  # Tags are optional
    
    if not isinstance(tags, list):
        raise ValidationError("Tags must be a list")
    
    for tag in tags:
        if not tag or not isinstance(tag, str):
            raise ValidationError("Each tag must be a non-empty string")
        
        # Sanitize tag
        sanitized_tag = sanitize_string(tag)
        
        # Validate tag length (1-128 characters)
        if len(sanitized_tag) < 1:
            raise ValidationError("Tag must not be empty")
        
        if len(sanitized_tag) > 128:
            raise ValidationError(
                f"Tag '{sanitized_tag}' exceeds 128 characters"
            )


def validate_protection_group_servers(
    server_ids: List[str],
    region: str
) -> None:
    """
    Validate server IDs and check for conflicts.
    
    Extracted from data-management-handler create_protection_group()
    lines 1630-1680.
    
    Args:
        server_ids: List of DRS source server IDs
        region: AWS region where servers are located
        
    Raises:
        ValidationError: If any server ID is invalid
        ConflictError: If server is already in another group
    """
    if not server_ids:
        raise ValidationError(
            "At least one server ID or tag is required"
        )
    
    if not isinstance(server_ids, list):
        raise ValidationError("Server IDs must be a list")
    
    # Validate each server ID format
    for server_id in server_ids:
        if not validate_drs_server_id(server_id):
            raise ValidationError(
                f"Invalid server ID format: {server_id}"
            )
    
    # Check for duplicate server IDs
    if len(server_ids) != len(set(server_ids)):
        raise ValidationError("Duplicate server IDs detected")
    
    # TODO: Check if servers are already in another protection group
    # This requires querying the protection groups table
    # Implementation depends on DynamoDB table structure


def check_protection_group_quota(current_count: int) -> None:
    """
    Check if protection group quota exceeded.
    
    Extracted from data-management-handler create_protection_group()
    lines 1690-1700.
    
    Args:
        current_count: Current number of protection groups
        
    Raises:
        QuotaExceededError: If quota is exceeded
    """
    MAX_PROTECTION_GROUPS = 100  # Configurable limit
    
    if current_count >= MAX_PROTECTION_GROUPS:
        raise QuotaExceededError(
            f"Protection group quota exceeded "
            f"(max: {MAX_PROTECTION_GROUPS})"
        )
```

**Step 2: Create server_resolution_service.py**

```python
# lambda/shared/server_resolution_service.py

from typing import List, Dict, Any
from lambda.shared.drs_utils import normalize_drs_response
from lambda.shared.cross_account import create_drs_client


def query_inventory_servers_by_tags(
    tags: List[str],
    region: str
) -> List[Dict[str, Any]]:
    """
    Query inventory table for servers matching tags.
    
    Extracted from data-management-handler create_protection_group()
    lines 1750-1850.
    
    Uses existing shared utilities:
    - drs_utils.normalize_drs_response()
    - cross_account.create_drs_client()
    
    Args:
        tags: List of tag names to match
        region: AWS region to query
        
    Returns:
        List of server dictionaries matching tags
    """
    if not tags:
        return []
    
    # Get inventory table
    inventory_table = get_inventory_table()
    
    # Query servers by tags
    matching_servers = []
    
    for tag in tags:
        # Query inventory table for servers with this tag
        response = inventory_table.query(
            IndexName="TagIndex",
            KeyConditionExpression="tag = :tag",
            ExpressionAttributeValues={":tag": tag}
        )
        
        matching_servers.extend(response.get("Items", []))
    
    return matching_servers


def resolve_servers_from_tags_and_ids(
    tags: List[str],
    server_ids: List[str],
    region: str
) -> List[str]:
    """
    Resolve final server list from combination of tags and explicit IDs.
    
    Handles deduplication and validation.
    
    Args:
        tags: List of tag names to resolve
        server_ids: List of explicit server IDs
        region: AWS region
        
    Returns:
        Deduplicated list of server IDs
    """
    # Start with explicit server IDs
    resolved_servers = set(server_ids) if server_ids else set()
    
    # Add servers from tags
    if tags:
        tagged_servers = query_inventory_servers_by_tags(tags, region)
        for server in tagged_servers:
            server_id = server.get("sourceServerId")
            if server_id:
                resolved_servers.add(server_id)
    
    return list(resolved_servers)
```

**Step 3: Update create_protection_group() to use extracted utilities**

```python
# lambda/data-management-handler/index.py

from lambda.shared.protection_group_validation import (
    validate_protection_group_name,
    validate_protection_group_tags,
    validate_protection_group_servers,
    check_protection_group_quota,
    ValidationError,
    ConflictError,
    QuotaExceededError
)
from lambda.shared.server_resolution_service import (
    resolve_servers_from_tags_and_ids
)


def create_protection_group(event, context):
    """
    Create a new protection group.
    
    This function has been refactored to use shared validation utilities
    as part of the query-handler read-only audit (FR5).
    
    Reduced from 429 lines to ~200 lines by extracting:
    - protection_group_validation.py (validation logic)
    - server_resolution_service.py (tag resolution logic)
    """
    try:
        # Extract parameters
        name = event.get("name")
        tags = event.get("tags", [])
        server_ids = event.get("serverIds", [])
        region = event.get("region", "us-east-2")
        
        # Get existing protection groups
        existing_groups = list_protection_groups()
        
        # Validate inputs using shared utilities
        validate_protection_group_name(name, existing_groups)
        validate_protection_group_tags(tags)
        check_protection_group_quota(len(existing_groups))
        
        # Resolve servers from tags and explicit IDs
        resolved_server_ids = resolve_servers_from_tags_and_ids(
            tags,
            server_ids,
            region
        )
        
        # Validate resolved servers
        validate_protection_group_servers(resolved_server_ids, region)
        
        # Create protection group (remaining logic ~150 lines)
        # ... (DynamoDB write, response formatting, etc.)
        
    except ValidationError as e:
        return error_response(400, str(e))
    except ConflictError as e:
        return error_response(409, str(e))
    except QuotaExceededError as e:
        return error_response(429, str(e))
    except Exception as e:
        logger.exception("Failed to create protection group")
        return error_response(500, "Internal server error")
```

**Impact**:
- ✅ Reduces `create_protection_group()` from 429 to ~200 lines
- ✅ Validation logic reusable by `update_protection_group()` (523 lines)
- ✅ Server resolution reusable across data-management-handler operations
- ✅ Aligns with FR5: Maintain Lambda Size Constraints
- ✅ Aligns with NFR3: Code Maintainability

#### 3. update_protection_group() Extraction (MEDIUM PRIORITY)

**Current State**:
- **Location**: `lambda/data-management-handler/index.py` lines 2000-2523
- **Size**: 523 lines (largest function in codebase)
- **Refactoring Alignment**: Supports FR5 (Maintain Lambda Size Constraints)

**Extraction Strategy**:

**Step 1: Reuse protection_group_validation.py** (already created above)

**Step 2: Update update_protection_group() to use extracted utilities**

```python
# lambda/data-management-handler/index.py

def update_protection_group(event, context):
    """
    Update an existing protection group.
    
    This function has been refactored to use shared validation utilities
    as part of the query-handler read-only audit (FR5).
    
    Reduced from 523 lines to ~250 lines by reusing:
    - protection_group_validation.py (validation logic)
    - server_resolution_service.py (tag resolution logic)
    """
    try:
        # Extract parameters
        group_id = event.get("groupId")
        name = event.get("name")
        tags = event.get("tags")
        server_ids = event.get("serverIds")
        region = event.get("region", "us-east-2")
        
        # Get existing protection group
        existing_group = get_protection_group(group_id)
        if not existing_group:
            return error_response(404, "Protection group not found")
        
        # Get all protection groups for name validation
        all_groups = list_protection_groups()
        
        # Validate inputs using shared utilities (if provided)
        if name:
            validate_protection_group_name(name, all_groups)
        
        if tags is not None:
            validate_protection_group_tags(tags)
        
        # Resolve servers if tags or server_ids provided
        if tags is not None or server_ids is not None:
            resolved_server_ids = resolve_servers_from_tags_and_ids(
                tags or existing_group.get("tags", []),
                server_ids or existing_group.get("serverIds", []),
                region
            )
            validate_protection_group_servers(resolved_server_ids, region)
        
        # Update protection group (remaining logic ~200 lines)
        # ... (optimistic locking, DynamoDB update, response formatting)
        
    except ValidationError as e:
        return error_response(400, str(e))
    except ConflictError as e:
        return error_response(409, str(e))
    except Exception as e:
        logger.exception("Failed to update protection group")
        return error_response(500, "Internal server error")
```

**Impact**:
- ✅ Reduces `update_protection_group()` from 523 to ~250 lines
- ✅ Reuses validation logic from `protection_group_validation.py`
- ✅ Reuses server resolution from `server_resolution_service.py`
- ✅ Aligns with FR5: Maintain Lambda Size Constraints
- ✅ Aligns with NFR3: Code Maintainability

### Summary: Extraction Priorities

| Priority | Function | Extraction Target | Spec Alignment | Size Reduction |
|----------|----------|-------------------|----------------|----------------|
| **HIGH** | `poll_wave_status()` | wave_status_service.py | FR4 (Task 4) | 420 → 200 lines |
| **MEDIUM** | `create_protection_group()` | protection_group_validation.py, server_resolution_service.py | FR5, NFR3 | 429 → 200 lines |
| **MEDIUM** | `update_protection_group()` | Reuse validation utilities | FR5, NFR3 | 523 → 250 lines |

**Total Handler Size Reduction**: ~650 lines across all handlers

**Alignment with Spec Requirements**:
- ✅ FR4: `poll_wave_status()` split directly implements this requirement
- ✅ FR5: Extractions keep all handlers under 15,000 lines
- ✅ NFR3: Shared utilities improve maintainability
- ✅ Existing Utilities: Leverage 18 existing modules in `lambda/shared/`
- ✅ No New Lambda Functions: All operations move to existing handlers

## Lambda Size Management

### Current Sizes (Estimated)

```
query-handler:        7,248 lines
data-management:      9,867 lines
execution-handler:    7,731 lines
```

### After Refactoring (Estimated)

```
query-handler:        6,564 lines (-684 lines: -470 inventory, -214 staging)
data-management:     10,551 lines (+684 lines: +470 inventory, +214 staging)
execution-handler:    7,831 lines (+100 lines: wave completion updates)
```

### Size Constraints

**Lambda Deployment Package Limits**:
- Uncompressed: 250 MB
- Compressed (zipped): 50 MB

**CloudFormation Template Limit**:
- 1 MB (template body size)

**Mitigation Strategies**:
1. Monitor deployment package sizes after each change
2. Extract shared utilities if handlers exceed 12,000 lines
3. Use Lambda layers for large dependencies (boto3, etc.)
4. Compress CloudFormation templates (remove comments, whitespace)

### Size Monitoring Commands

```bash
# Measure Lambda deployment package size
cd lambda/data-management-handler
zip -r /tmp/handler.zip . -x "*.pyc" -x "__pycache__/*"
ls -lh /tmp/handler.zip

# Count lines of code
wc -l lambda/*/index.py

# Measure CloudFormation template size
ls -lh cfn/master-template.yaml
```

## Deployment Strategy

### Phase 1: Add New Operations (Zero Downtime)

1. **Deploy data-management-handler with new operations**:
   - Add `handle_sync_source_server_inventory()`
   - Add `handle_sync_staging_accounts()`
   - Test operations via direct invocation

2. **Deploy execution-handler with new operation**:
   - Add `update_wave_completion_status()`
   - Test operation via direct invocation

3. **Update EventBridge rules**:
   - Point inventory sync to data-management-handler
   - Point staging sync to data-management-handler
   - Test scheduled sync operations

4. **Update Step Functions state machine**:
   - Add `UpdateWaveStatus` state after `WavePoll`
   - Test wave polling with DynamoDB updates

### Phase 2: Remove Old Operations (Cleanup)

1. **Refactor query-handler**:
   - Remove `handle_sync_source_server_inventory()`
   - Remove `handle_sync_staging_accounts()`
   - Refactor `poll_wave_status()` to remove DynamoDB writes

2. **Deploy query-handler cleanup**:
   - Test all read operations still work
   - Verify no sync operations remain

3. **Verify zero regressions**:
   - All sync operations work
   - No data loss
   - No performance degradation

### Rollback Plan

**If EventBridge routing fails**:
1. Revert EventBridge rule to target query-handler
2. Deploy CloudFormation stack rollback
3. Investigate routing issue

**If Step Functions state machine fails**:
1. Revert state machine definition to previous version
2. Test wave polling
3. Investigate state machine issue

**If data loss occurs**:
1. Stop all sync operations immediately
2. Restore DynamoDB tables from backup
3. Investigate data loss root cause

## Testing Strategy

### Unit Tests

**data-management-handler**:
- Test `handle_sync_source_server_inventory()` with mocked DRS/EC2 clients
- Test `handle_sync_staging_accounts()` with mocked DRS client
- Verify DynamoDB batch writes

**execution-handler**:
- Test `update_wave_completion_status()` with mocked DynamoDB
- Verify wave completion, pause, resume, cancel updates

**query-handler**:
- Test refactored `poll_wave_status()` returns correct status
- Verify NO DynamoDB writes occur

### Integration Tests

**EventBridge Sync Operations**:
1. Trigger inventory sync via EventBridge
2. Verify inventory table updated
3. Verify region status table updated

**Step Functions Wave Polling**:
1. Start recovery plan execution
2. Verify wave polling calls query-handler
3. Verify wave completion calls execution-handler
4. Verify execution history table updated

### End-to-End Tests

**Complete Recovery Plan Execution**:
1. Create Protection Group with servers
2. Create Recovery Plan with multiple waves
3. Start execution
4. Verify wave polling works
5. Verify wave completion updates
6. Verify pause/resume works
7. Verify cancellation works

## Success Metrics

### Functional Metrics

- ✅ Zero DynamoDB writes in query-handler
- ✅ Zero DRS API writes in query-handler
- ✅ All sync operations work after migration
- ✅ No data loss during wave transitions
- ✅ All tests pass

### Performance Metrics

- ✅ No additional Lambda cold starts
- ✅ No additional cross-handler invocations
- ✅ EventBridge direct invocation (no routing overhead)
- ✅ Maintain current concurrency limits

### Size Metrics

- ✅ All Lambda functions < 15,000 lines
- ✅ All deployment packages < 200 MB uncompressed
- ✅ CloudFormation template < 800 KB

## Open Questions

### Q1: Should `poll_wave_status()` be split or moved entirely?

**Answer**: Split function (Option A) to maintain clean separation of concerns.

**Rationale**:
- query-handler remains read-only (DRS job queries)
- execution-handler handles wave completion sync (DynamoDB writes)
- Step Functions orchestrates both handlers

### Q2: Should shared utilities be extracted?

**Answer**: Extract ONLY if reused by multiple handlers.

**Rationale**:
- Avoid premature abstraction
- Keep code close to where it's used
- Extract later if duplication emerges

### Q3: Should we consolidate query-handler into data-management-handler?

**Answer**: NO - maintain separate handlers with shared utilities.

**Detailed Analysis**:

**query-handler Operations (30+ read-only functions)**:
- DRS Infrastructure: `get_drs_source_servers`, `get_drs_service_limits`, `get_drs_accounts`, `get_drs_capacity_*`
- EC2 Resources: `get_ec2_subnets`, `get_ec2_security_groups`, `get_ec2_instance_types`, `get_ec2_instance_profiles`
- Account Info: `get_current_account_info`, `get_protection_group_servers`, `get_server_launch_config_direct`
- Configuration: `export_configuration`, `get_tag_sync_status_direct`, `get_staging_accounts_direct`
- User Management: `handle_user_permissions`, `handle_user_profile`, `handle_user_roles`
- Wave Polling: `poll_wave_status` (DRS job queries)

**data-management-handler Operations (20+ write functions)**:
- Protection Groups: `create_protection_group`, `update_protection_group`, `delete_protection_group`
- Recovery Plans: `create_recovery_plan`, `update_recovery_plan`, `delete_recovery_plan`
- Launch Configs: `update_server_launch_config`, `delete_server_launch_config`
- Target Accounts: `create_target_account`, `update_target_account`, `delete_target_account`
- Staging Accounts: `handle_add_staging_account`, `handle_remove_staging_account`
- Tag Sync: `handle_drs_tag_sync`, `update_tag_sync_settings`

**Consolidation Impact**:
```
Current:
  query-handler:        7,248 lines (30+ read operations)
  data-management:      9,867 lines (20+ write operations)
  Total:               17,115 lines

After Consolidation:
  data-management:     17,115 lines (50+ operations)
  
Size Concerns:
  - Single handler becomes very large (17K+ lines)
  - Harder to maintain and test
  - Longer cold start times
  - Deployment package size increases
```

**Recommended Architecture**:

**Option 1: Keep Separate Handlers (RECOMMENDED)**
```
query-handler (6,564 lines after refactoring):
  - All read-only operations
  - API Gateway endpoints for frontend
  - Direct invocation for Step Functions
  - Imports shared utilities from lambda/shared/

data-management-handler (10,551 lines after refactoring):
  - All write operations (CRUD)
  - All sync operations (tag, inventory, staging, recovery instance)
  - Imports shared utilities from lambda/shared/

lambda/shared/ (new utilities):
  - drs_utils.py: Common DRS API calls
  - ec2_utils.py: Common EC2 API calls
  - dynamodb_utils.py: Common DynamoDB patterns
  - account_utils.py: Account context handling
```

**Option 2: Consolidate Everything (NOT RECOMMENDED)**
```
data-management-handler (17,115+ lines):
  - All operations (read + write)
  - Single Lambda for everything
  - Harder to maintain
  - Longer cold starts
  - Larger deployment package
```

**Rationale for Keeping Separate**:
1. **Clear Separation of Concerns**: Read operations vs write operations
2. **API Gateway Routing**: Frontend needs fast read operations (query-handler optimized for this)
3. **Lambda Size Management**: Two medium handlers better than one huge handler
4. **Cold Start Performance**: Smaller handlers = faster cold starts
5. **Testing**: Easier to test read vs write operations separately
6. **Deployment**: Can deploy read operations independently of write operations
7. **Shared Utilities**: Extract common code to `lambda/shared/` to avoid duplication

**Shared Utilities Strategy**:
- Extract common DRS/EC2/DynamoDB code to `lambda/shared/`
- Both handlers import from shared utilities
- Reduces duplication without consolidating handlers
- Keeps handlers focused on their responsibilities

### Q4: What is the current deployment package size?

**Answer**: Measure after Phase 1 deployment.

**Action**: Run size monitoring commands and document results.

## References

- Handler Responsibility Pattern (from user)
- Recovery Instance Sync Spec: `.kiro/specs/recovery-instance-sync/`
- Lambda Size Limits: https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html
- CloudFormation Limits: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
- Step Functions State Machine: `cfn/nested-stacks/step-functions.yaml`
- EventBridge Rules: `cfn/nested-stacks/eventbridge-rules.yaml`


### Overview

The query-handler enforces role-based access control (RBAC) using the `rbac_middleware.py` module. All query operations require specific permissions based on the user's role.

### RBAC Roles and Permissions

**5 Roles**:
1. **Admin**: Full access to all operations
2. **Operator**: Execute recovery operations, manage resources
3. **Viewer**: Read-only access to operational data
4. **Auditor**: Read-only access to audit logs and compliance data
5. **Planner**: Create and manage recovery plans

**16 Granular Permissions**:
```python
# Protection Group Permissions
"protection_groups:read"    # View protection groups
"protection_groups:write"   # Create/update/delete protection groups

# Recovery Plan Permissions
"recovery_plans:read"       # View recovery plans
"recovery_plans:write"      # Create/update/delete recovery plans
"recovery_plans:execute"    # Start recovery executions

# Server Permissions
"servers:read"              # View source servers
"servers:write"             # Update server configurations

# Account Permissions
"accounts:read"             # View target accounts
"accounts:write"            # Create/update/delete target accounts

# Audit Permissions
"audit:read"                # View audit logs
"audit:write"               # Create audit log entries (system only)

# Configuration Permissions
"config:read"               # View configurations
"config:write"              # Update configurations

# Execution Permissions
"executions:read"           # View execution status
"executions:write"          # Control executions (pause/resume/cancel)
```

### Permission-to-Operation Mapping

**query-handler Operations (Read-Only)**:

| Operation | Required Permission | Roles with Access |
|-----------|-------------------|-------------------|
| `get_drs_source_servers` | `servers:read` | Admin, Operator, Viewer, Auditor, Planner |
| `get_protection_groups` | `protection_groups:read` | Admin, Operator, Viewer, Auditor, Planner |
| `get_recovery_plans` | `recovery_plans:read` | Admin, Operator, Viewer, Auditor, Planner |
| `get_execution_status` | `executions:read` | Admin, Operator, Viewer, Auditor |
| `get_audit_logs` | `audit:read` | Admin, Auditor |
| `get_target_accounts` | `accounts:read` | Admin, Operator, Viewer, Planner |
| `get_launch_configs` | `config:read` | Admin, Operator, Viewer, Planner |

### RBAC Middleware Usage

**Decorator Pattern**:

```python
from lambda.shared.rbac_middleware import require_permission

@require_permission("servers:read")
def get_drs_source_servers(event, context):
    """Get DRS source servers (requires servers:read permission)."""
    # Query DRS API
    servers = drs_client.describe_source_servers()
    return response(200, servers)

@require_permission("audit:read")
def get_audit_logs(event, context):
    """Get audit logs (requires audit:read permission - Auditor role)."""
    # Query audit log table
    logs = audit_table.query(...)
    return response(200, logs)
```

**Permission Extraction from Cognito JWT**:

```python
def extract_permissions_from_jwt(event):
    """Extract user permissions from Cognito JWT token."""
    claims = event["requestContext"]["authorizer"]["claims"]
    
    # Cognito groups map to roles
    groups = claims.get("cognito:groups", "").split(",")
    
    # Map groups to permissions
    permissions = set()
    for group in groups:
        if group == "Admin":
            permissions.update(ALL_PERMISSIONS)
        elif group == "Operator":
            permissions.update(OPERATOR_PERMISSIONS)
        elif group == "Viewer":
            permissions.update(VIEWER_PERMISSIONS)
        elif group == "Auditor":
            permissions.update(AUDITOR_PERMISSIONS)
        elif group == "Planner":
            permissions.update(PLANNER_PERMISSIONS)
    
    return list(permissions)
```

### Auditor Role vs Viewer Role

**Auditor Role**:
- **Purpose**: Compliance and security auditing
- **Permissions**: `audit:read`, `servers:read`, `protection_groups:read`, `recovery_plans:read`, `executions:read`
- **Access**: Audit logs, operational data (read-only)
- **Use Case**: Security teams, compliance officers

**Viewer Role**:
- **Purpose**: Operational monitoring
- **Permissions**: `servers:read`, `protection_groups:read`, `recovery_plans:read`, `executions:read`, `config:read`
- **Access**: Operational data (read-only), NO audit logs
- **Use Case**: Operations teams, monitoring dashboards

**Key Difference**: Auditor can view audit logs, Viewer cannot.

## Audit Log Schema

### Expanded Schema with IAM Principal Details

**Complete Audit Log Schema**:

```python
{
    # Timestamp and Operation
    "timestamp": "2025-02-17T10:30:45.123Z",  # ISO 8601 UTC
    "operation": "get_drs_source_servers",     # Operation name
    
    # Invocation Mode
    "invocation_mode": "API_GATEWAY",          # API_GATEWAY | DIRECT_LAMBDA
    
    # Principal Information (API Gateway - Cognito)
    "principal_type": "CognitoUser",           # CognitoUser | AssumedRole | User | Service
    "principal_arn": "cognito:user:admin@example.com",
    "user_email": "admin@example.com",         # Cognito user email
    "cognito_groups": ["Admin", "Operator"],   # Cognito groups
    "session_name": None,                      # Not applicable for Cognito
    
    # OR Principal Information (Direct Lambda - IAM)
    "principal_type": "AssumedRole",           # AssumedRole | User | Service
    "principal_arn": "arn:aws:iam::891376951562:role/ExecutionRole",
    "session_name": "step-functions-session",  # For assumed roles
    "user_email": None,                        # Not applicable for IAM
    "cognito_groups": None,                    # Not applicable for IAM
    
    # Account Context
    "account_id": "891376951562",              # AWS account ID
    "source_account": "891376951562",          # Hub account
    "target_account": "123456789012",          # Target account (if cross-account)
    
    # Request Details
    "parameters": {                            # Masked sensitive parameters
        "region": "us-east-2",
        "server_id": "s-1234567890abcdef0",
        "password": "***MASKED***",            # Sensitive data masked
        "api_key": "***MASKED***"
    },
    "request_id": "abc123-def456-ghi789",      # Lambda request ID
    
    # Response Details
    "status_code": 200,                        # HTTP status code
    "response_size": 1024,                     # Response size in bytes
    "duration_ms": 150,                        # Operation duration
    
    # Error Details (if applicable)
    "error_type": "ValidationError",           # Error type
    "error_message": "Invalid server ID",      # Error message
    
    # Metadata
    "lambda_function": "query-handler",        # Lambda function name
    "lambda_version": "$LATEST",               # Lambda version
    "environment": "dev"                       # Environment (dev/test/prod)
}
```

### Audit Log Examples

**Example 1: API Gateway Invocation (Cognito User)**:

```json
{
    "timestamp": "2025-02-17T10:30:45.123Z",
    "operation": "get_drs_source_servers",
    "invocation_mode": "API_GATEWAY",
    "principal_type": "CognitoUser",
    "principal_arn": "cognito:user:admin@example.com",
    "user_email": "admin@example.com",
    "cognito_groups": ["Admin"],
    "session_name": null,
    "account_id": "891376951562",
    "parameters": {
        "region": "us-east-2"
    },
    "status_code": 200,
    "duration_ms": 150
}
```

**Example 2: Direct Lambda Invocation (Step Functions)**:

```json
{
    "timestamp": "2025-02-17T10:35:20.456Z",
    "operation": "poll_wave_status",
    "invocation_mode": "DIRECT_LAMBDA",
    "principal_type": "AssumedRole",
    "principal_arn": "arn:aws:iam::891376951562:role/ExecutionRole",
    "session_name": "step-functions-session",
    "user_email": null,
    "cognito_groups": null,
    "account_id": "891376951562",
    "parameters": {
        "execution_id": "exec-123",
        "wave_number": 1
    },
    "status_code": 200,
    "duration_ms": 250
}
```

**Example 3: Direct Lambda Invocation (EventBridge)**:

```json
{
    "timestamp": "2025-02-17T10:40:00.789Z",
    "operation": "handle_sync_source_server_inventory",
    "invocation_mode": "DIRECT_LAMBDA",
    "principal_type": "Service",
    "principal_arn": "arn:aws:events::891376951562:rule/inventory-sync",
    "session_name": null,
    "user_email": null,
    "cognito_groups": null,
    "account_id": "891376951562",
    "parameters": {},
    "status_code": 200,
    "duration_ms": 5000
}
```

### Parameter Masking for Sensitive Data

**Sensitive Parameter Patterns**:

```python
from lambda.shared.iam_utils import mask_sensitive_parameters

SENSITIVE_PATTERNS = [
    "password",
    "api_key",
    "secret",
    "token",
    "credential",
    "private_key",
    "access_key"
]

def mask_sensitive_parameters(parameters):
    """Mask sensitive parameters in audit logs."""
    masked = {}
    for key, value in parameters.items():
        if any(pattern in key.lower() for pattern in SENSITIVE_PATTERNS):
            masked[key] = "***MASKED***"
        else:
            masked[key] = value
    return masked
```

## Security Considerations

### Input Validation Before Audit Logging

All input parameters are validated and sanitized using `security_utils.py` before being logged to audit trails:

**Validation Pattern**:

```python
from lambda.shared.security_utils import (
    sanitize_string,
    validate_drs_server_id,
    validate_aws_account_id,
    sanitize_dynamodb_input
)

def lambda_handler(event, context):
    """Query handler with input validation."""
    
    # Extract parameters
    server_id = event.get("server_id")
    account_id = event.get("account_id")
    region = event.get("region")
    
    # Validate inputs
    if server_id and not validate_drs_server_id(server_id):
        return error_response(400, "Invalid server ID format")
    
    if account_id and not validate_aws_account_id(account_id):
        return error_response(400, "Invalid account ID format")
    
    # Sanitize string inputs
    region = sanitize_string(region) if region else None
    
    # Sanitize before audit logging
    sanitized_params = sanitize_dynamodb_input({
        "server_id": server_id,
        "account_id": account_id,
        "region": region
    })
    
    # Log audit trail with sanitized parameters
    audit_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": event.get("operation"),
        "parameters": mask_sensitive_parameters(sanitized_params)
    }
    write_audit_log(audit_log)
    
    # Process request
    return process_query(event, context)
```

### Security Protections

**1. SQL Injection Prevention**:
- All DynamoDB queries use parameterized expressions
- No string concatenation in query expressions
- Expression attribute names and values properly escaped

**2. XSS Protection**:
- All user input sanitized before storage
- HTML special characters escaped
- No direct HTML rendering of user input

**3. Command Injection Blocking**:
- No shell command execution with user input
- All AWS API calls use boto3 SDK (no CLI)
- Input validation prevents command injection

**4. Credential Scanning**:
- detect-secrets scans for hardcoded credentials
- Sensitive parameters masked in audit logs
- No credentials stored in DynamoDB

### Audit Log Storage Security

**DynamoDB Table Security**:

```yaml
# cfn/nested-stacks/dynamodb-tables.yaml
AuditLogTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub "${ProjectName}-audit-logs-${Environment}"
    BillingMode: PAY_PER_REQUEST
    PointInTimeRecoverySpecification:
      PointInTimeRecoveryEnabled: true  # Enable PITR for compliance
    SSESpecification:
      SSEEnabled: true                   # Encrypt at rest
      SSEType: KMS
      KMSMasterKeyId: !Ref AuditLogKMSKey
    StreamSpecification:
      StreamViewType: NEW_AND_OLD_IMAGES # Enable streams for SIEM integration
    Tags:
      - Key: Compliance
        Value: AuditLog
      - Key: DataClassification
        Value: Confidential
```

**Access Control**:
- Only Admin and Auditor roles can read audit logs
- Only Lambda execution role can write audit logs
- No public access to audit log table
- KMS encryption for data at rest
- TLS encryption for data in transit

## Error Handling for Audit Logging

### Audit Logging Failure Modes

**1. DynamoDB Write Failure**:
- **Cause**: Throttling, network error, table unavailable
- **Impact**: Audit log not persisted
- **Mitigation**: Retry with exponential backoff, fallback to CloudWatch Logs

**2. Parameter Masking Failure**:
- **Cause**: Unexpected parameter format
- **Impact**: Sensitive data may be logged
- **Mitigation**: Fail-safe masking (mask entire parameter if error)

**3. IAM Principal Extraction Failure**:
- **Cause**: Unexpected Lambda context format
- **Impact**: Principal information incomplete
- **Mitigation**: Log error, use fallback principal (UNKNOWN)

### Error Handling Strategy

**Synchronous Audit Logging (Default)**:

```python
def lambda_handler(event, context):
    """Query handler with synchronous audit logging."""
    
    try:
        # Extract principal
        principal_info = extract_principal_from_context(context)
        
        # Process request
        result = process_query(event, principal_info)
        
        # Write audit log (synchronous)
        try:
            audit_log = build_audit_log(event, context, principal_info, result)
            write_audit_log_with_retry(audit_log)
        except Exception as audit_error:
            # Log audit failure to CloudWatch Logs (fallback)
            logger.error(f"Audit log write failed: {audit_error}")
            logger.info(f"Audit log (fallback): {json.dumps(audit_log)}")
            # DO NOT fail the operation - audit logging is non-blocking
        
        return result
        
    except Exception as e:
        # Log error audit trail
        try:
            error_audit_log = build_error_audit_log(event, context, e)
            write_audit_log_with_retry(error_audit_log)
        except Exception as audit_error:
            logger.error(f"Error audit log write failed: {audit_error}")
        
        return error_response(500, str(e))
```

**Retry Logic with Exponential Backoff**:

```python
import time
from botocore.exceptions import ClientError

def write_audit_log_with_retry(audit_log, max_retries=3):
    """Write audit log with exponential backoff retry."""
    
    for attempt in range(max_retries):
        try:
            audit_table.put_item(Item=audit_log)
            return  # Success
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            
            if error_code == "ProvisionedThroughputExceededException":
                # Throttling - retry with backoff
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                else:
                    # Max retries exceeded - fallback to CloudWatch Logs
                    logger.error(f"Audit log write failed after {max_retries} retries")
                    logger.info(f"Audit log (fallback): {json.dumps(audit_log)}")
                    raise
            else:
                # Non-retryable error - fallback to CloudWatch Logs
                logger.error(f"Audit log write failed: {error_code}")
                logger.info(f"Audit log (fallback): {json.dumps(audit_log)}")
                raise
```

### Trade-offs: Reliability vs Performance

**Synchronous Audit Logging (Current)**:
- ✅ Guaranteed audit trail before operation completes
- ✅ Easier to debug (audit log always written)
- ❌ Adds latency to operation (DynamoDB write time)
- ❌ Operation fails if audit log write fails (after retries)

**Asynchronous Audit Logging (Alternative)**:
- ✅ No latency added to operation
- ✅ Operation succeeds even if audit log write fails
- ❌ Audit trail may be incomplete (if async write fails)
- ❌ Harder to debug (audit log written after response)

**Decision**: Use synchronous audit logging with retry and CloudWatch Logs fallback for compliance requirements.

## Cross-Account Audit Logging

### Hub-and-Spoke Audit Trail

When query-handler performs cross-account operations (querying DRS servers in target accounts), the audit log captures both hub and target account context:

**Cross-Account Operation Flow**:

```
Hub Account (891376951562)
  ↓
query-handler invoked
  ↓
Assume IAM role in Target Account (123456789012)
  ↓
Query DRS API in Target Account
  ↓
Audit log written to Hub Account DynamoDB
```

**Cross-Account Audit Log Schema**:

```python
{
    "timestamp": "2025-02-17T10:45:00.123Z",
    "operation": "get_drs_source_servers",
    "invocation_mode": "API_GATEWAY",
    "principal_type": "CognitoUser",
    "principal_arn": "cognito:user:admin@example.com",
    "user_email": "admin@example.com",
    
    # Hub Account Context
    "account_id": "891376951562",              # Hub account
    "source_account": "891376951562",          # Where Lambda runs
    
    # Target Account Context
    "target_account": "123456789012",          # Target account queried
    "assumed_role_arn": "arn:aws:iam::123456789012:role/DRSCrossAccountRole",
    "cross_account_session": "hub-to-target-session",
    
    # Operation Details
    "parameters": {
        "region": "us-east-2",
        "target_account": "123456789012"
    },
    "status_code": 200,
    "duration_ms": 300
}
```

### Cross-Account Context Extraction

**Using account_utils.py**:

```python
from lambda.shared.account_utils import get_target_accounts, validate_target_account
from lambda.shared.cross_account import determine_target_account_context, create_drs_client

def get_drs_source_servers_cross_account(event, context):
    """Get DRS source servers from target account."""
    
    # Extract target account from request
    target_account_id = event.get("target_account")
    
    # Validate target account
    if not validate_target_account(target_account_id):
        return error_response(400, "Invalid or unauthorized target account")
    
    # Determine target account context
    account_context = determine_target_account_context(target_account_id)
    
    # Create cross-account DRS client
    drs_client = create_drs_client(
        region=event.get("region"),
        account_id=target_account_id,
        role_name="DRSCrossAccountRole"
    )
    
    # Query DRS API in target account
    servers = drs_client.describe_source_servers()
    
    # Write audit log with cross-account context
    audit_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": "get_drs_source_servers",
        "source_account": os.environ["AWS_ACCOUNT_ID"],  # Hub account
        "target_account": target_account_id,              # Target account
        "assumed_role_arn": account_context["role_arn"],
        "cross_account_session": account_context["session_name"],
        "parameters": mask_sensitive_parameters(event)
    }
    write_audit_log(audit_log)
    
    return response(200, servers)
```

### Audit Log Aggregation

**Hub Account Audit Log Table**:
- All audit logs written to hub account DynamoDB table
- Centralized audit trail for all cross-account operations
- Easier compliance reporting (single source of truth)

**Query Patterns**:

```python
# Query all operations for specific target account
audit_table.query(
    IndexName="TargetAccountIndex",
    KeyConditionExpression="target_account = :account",
    ExpressionAttributeValues={":account": "123456789012"}
)

# Query all cross-account operations
audit_table.scan(
    FilterExpression="attribute_exists(target_account)"
)

# Query operations by specific user across all accounts
audit_table.query(
    IndexName="UserEmailIndex",
    KeyConditionExpression="user_email = :email",
    ExpressionAttributeValues={":email": "admin@example.com"}
)
```
