# Development Guidelines

## Code Quality Standards

### Python Code Formatting (Lambda Functions)

**Docstrings and Documentation**
- Module-level docstrings at top of every file describing purpose
- Function docstrings with Args, Returns, and Examples sections for complex functions
- Inline comments for critical business logic and DRS API interactions
- Example pattern from `index.py`:
```python
"""
AWS DRS Orchestration - API Handler Lambda
Handles REST API requests for Protection Groups, Recovery Plans, and Executions
"""

def validate_servers_exist_in_drs(region: str, server_ids: List[str]) -> List[str]:
    """
    Validate that server IDs actually exist in DRS
    
    Args:
    - region: AWS region to check
    - server_ids: List of server IDs to validate
    
    Returns:
    - List of invalid server IDs (empty list if all valid)
    """
```

**Type Hints**
- All function parameters and return types use type hints
- Import from `typing` module: `Dict, Any, List, Optional`
- Example: `def response(status_code: int, body: Any, headers: Optional[Dict] = None) -> Dict:`

**Naming Conventions**
- Functions: `snake_case` (e.g., `get_protection_group`, `validate_unique_pg_name`)
- Variables: `snake_case` (e.g., `execution_id`, `server_ids`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `PROTECTION_GROUPS_TABLE`, `SUCCESS`, `FAILED`)
- Classes: `PascalCase` (e.g., `DecimalEncoder`, `CfnResource`)

**Error Handling Pattern**
- Try-except blocks with detailed logging
- Print full traceback for debugging: `traceback.print_exc()`
- Return structured error responses with error codes
- Example from `index.py`:
```python
try:
    # Operation
    result = operation()
    return response(200, result)
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    return response(500, {'error': str(e)})
```

### TypeScript Code Formatting (Frontend)

**Interface Definitions**
- Comprehensive type definitions in `types/index.ts`
- JSDoc comments for complex types
- Organized by domain (Protection Groups, Recovery Plans, Executions, DRS)
- Example pattern:
```typescript
/**
 * TypeScript Type Definitions
 * 
 * These types mirror the backend DynamoDB schema and API responses.
 */

export interface ProtectionGroup {
  id: string;
  protectionGroupId: string;  // Alias for backward compatibility
  name: string;
  description?: string;
  region: string;
  sourceServerIds: string[];
  createdAt: number;
  updatedAt: number;
}
```

**Naming Conventions**
- Interfaces: `PascalCase` (e.g., `ProtectionGroup`, `RecoveryPlan`)
- Properties: `camelCase` (e.g., `sourceServerIds`, `executionType`)
- Types: `PascalCase` (e.g., `ExecutionStatus`, `ApiResponse<T>`)
- Enums: `PascalCase` with UPPER_CASE values

**Optional Properties**
- Use `?` for optional fields consistently
- Document backward compatibility aliases
- Example: `description?: string;`

### Test Code Standards

**Test Organization**
- Group tests by functionality using classes
- Descriptive test names: `test_<action>_<scenario>_<expected_result>`
- Example from `test_execution_poller.py`:
```python
class TestLambdaHandler:
    """Tests for main Lambda handler function."""
    
    def test_handler_success_polling_in_progress(self, mock_env, mock_clients):
        """Test successful polling with waves still in progress."""
```

**Fixtures and Mocking**
- Use pytest fixtures for common setup
- Mock AWS clients at module level
- Generate dynamic test data to avoid timeouts
- Example pattern:
```python
@pytest.fixture
def mock_env(monkeypatch):
    """Set up environment variables for tests."""
    monkeypatch.setenv('EXECUTION_HISTORY_TABLE', 'test-execution-table')

@pytest.fixture
def mock_clients():
    """Mock all AWS clients."""
    with patch('execution_poller.dynamodb') as mock_dynamodb:
        yield {'dynamodb': mock_dynamodb}
```

**Assertions**
- Multiple assertions per test for comprehensive validation
- Check both success and error paths
- Verify mock call arguments for API interactions

## Architectural Patterns

### API Response Pattern

**Consistent Response Structure**
- All API endpoints return standardized format
- CORS headers included automatically
- Custom JSON encoder for DynamoDB Decimal types
- Example from `index.py`:
```python
def response(status_code: int, body: Any, headers: Optional[Dict] = None) -> Dict:
    """Generate API Gateway response with CORS headers"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, cls=DecimalEncoder)
    }
```

### Data Transformation Pattern

**Backend to Frontend Conversion**
- Backend uses PascalCase (DynamoDB convention)
- Frontend expects camelCase (JavaScript convention)
- Transform functions for each entity type
- Timestamp conversion: seconds → milliseconds for JavaScript Date()
- Example from `index.py`:
```python
def transform_pg_to_camelcase(pg: Dict) -> Dict:
    """Transform Protection Group from DynamoDB PascalCase to frontend camelCase"""
    created_at = pg.get('CreatedDate')
    return {
        'protectionGroupId': pg.get('GroupId'),
        'name': pg.get('GroupName'),
        'createdAt': int(created_at * 1000) if created_at else None,
        'sourceServerIds': pg.get('SourceServerIds', [])
    }
```

### Validation Pattern

**Multi-Layer Validation**
- Required field validation first
- Business logic validation second
- External system validation third (DRS API)
- Return specific error codes for each failure type
- Example from `index.py`:
```python
# 1. Required fields
if 'GroupName' not in body:
    return response(400, {'error': 'GroupName is required'})

# 2. Business logic
if not validate_unique_pg_name(name):
    return response(409, {
        'error': 'PG_NAME_EXISTS',
        'message': f'A Protection Group named "{name}" already exists'
    })

# 3. External validation
invalid_servers = validate_servers_exist_in_drs(region, server_ids)
if invalid_servers:
    return response(400, {
        'error': 'INVALID_SERVER_IDS',
        'invalidServers': invalid_servers
    })
```

### DRS Integration Pattern

**Job-Based Orchestration**
- One DRS job per wave (not per server)
- All servers in wave launched with single `start_recovery()` call
- Poll job status using `describe_jobs()` with job ID
- Trust LAUNCHED status without requiring `recoveryInstanceID`
- Example from `index.py`:
```python
def start_drs_recovery_for_wave(server_ids: List[str], region: str, is_drill: bool) -> Dict:
    """
    Launch DRS recovery for all servers in a wave with ONE API call
    
    CRITICAL PATTERN:
    - Launches ALL servers with SINGLE start_recovery() call
    - Returns ONE job ID for entire wave
    - This job ID is what ExecutionPoller tracks for wave completion
    """
    source_servers = [{'sourceServerID': sid} for sid in server_ids]
    
    response = drs_client.start_recovery(
        sourceServers=source_servers,
        isDrill=is_drill
    )
    
    job_id = response['job']['jobID']
    return {'JobId': job_id, 'Servers': server_results}
```

### Error Handling Pattern

**Defensive Programming**
- Validate data types before processing
- Handle missing keys gracefully with `.get()` method
- Log errors with context for debugging
- Return user-friendly error messages
- Example from `index.py`:
```python
# Defensive ServerIds extraction
server_ids = wave.get('ServerIds', [])
if not isinstance(server_ids, list):
    print(f"ERROR: ServerIds is not a list, got type {type(server_ids)}")
    if isinstance(server_ids, str):
        server_ids = [server_ids]  # Recovery attempt
    else:
        server_ids = []
```

### Async Execution Pattern

**Lambda Async Invocation**
- API handler returns immediately (202 Accepted)
- Invokes itself asynchronously for long-running work
- Stores initial status in DynamoDB (PENDING)
- Worker updates status as execution progresses
- Example from `index.py`:
```python
def execute_recovery_plan(body: Dict) -> Dict:
    """Execute a Recovery Plan - Async pattern to avoid API Gateway timeout"""
    # Create initial execution record
    history_item = {
        'ExecutionId': execution_id,
        'Status': 'PENDING',
        'StartTime': timestamp
    }
    execution_history_table.put_item(Item=history_item)
    
    # Invoke async worker
    lambda_client.invoke(
        FunctionName=current_function_name,
        InvocationType='Event',  # Async
        Payload=json.dumps(worker_payload)
    )
    
    # Return immediately
    return response(202, {
        'executionId': execution_id,
        'status': 'PENDING',
        'message': 'Execution started'
    })
```

## Internal API Usage Patterns

### DynamoDB Operations

**Query with GSI Fallback**
- Try GSI query first for performance
- Fallback to scan if GSI doesn't exist
- Example from `index.py`:
```python
try:
    result = execution_history_table.query(
        IndexName='PlanIdIndex',
        KeyConditionExpression=Key('PlanId').eq(plan_id),
        FilterExpression=Attr('Status').eq('RUNNING')
    )
except Exception as gsi_error:
    # Fallback to scan
    result = execution_history_table.scan(
        FilterExpression=Attr('PlanId').eq(plan_id) & Attr('Status').eq('RUNNING')
    )
```

**Composite Key Operations**
- DynamoDB tables use composite keys (ExecutionId + PlanId)
- Always provide both keys for get_item, update_item, delete_item
- Use query() for single partition key lookups
- Example:
```python
# Correct - composite key
execution_history_table.update_item(
    Key={'ExecutionId': execution_id, 'PlanId': plan_id},
    UpdateExpression='SET #status = :status'
)
```

### AWS DRS API Patterns

**Server Discovery**
- Use `describe_source_servers()` with pagination
- Filter by region and replication state
- Enrich with EC2 tags for display names
- Example from `index.py`:
```python
drs_client = boto3.client('drs', region_name=region)
servers_response = drs_client.describe_source_servers(maxResults=200)

# Enrich with EC2 Name tags
ec2_client = boto3.client('ec2', region_name=region)
ec2_response = ec2_client.describe_instances(InstanceIds=source_instance_ids)
```

**Recovery Job Initiation**
- Use `start_recovery()` with sourceServers array
- Do NOT pass tags parameter (causes conversion phase to be skipped)
- Trust LAUNCHED status from job response
- Example:
```python
response = drs_client.start_recovery(
    sourceServers=[{'sourceServerID': sid} for sid in server_ids],
    isDrill=is_drill
    # NO TAGS - they cause DRS to skip conversion!
)
```

**Job Status Polling**
- Use `describe_jobs()` with jobIDs filter
- Check `participatingServers[].launchStatus` for per-server status
- LAUNCHED status is reliable without `recoveryInstanceID`
- Example from `orchestration_stepfunctions.py`:
```python
DRS_JOB_SERVERS_COMPLETE_SUCCESS_STATES = ['LAUNCHED']

for server in participating_servers:
    launch_status = server.get('launchStatus', 'PENDING')
    if launch_status in DRS_JOB_SERVERS_COMPLETE_SUCCESS_STATES:
        launched_count += 1
        print(f"✅ Server {server_id} LAUNCHED successfully")
```

### Step Functions Integration

**State Machine Input Format**
- Use specific structure expected by state machine
- Include execution metadata and plan details
- Example from `index.py`:
```python
sfn_input = {
    'Execution': {'Id': execution_id},
    'Plan': {
        'PlanId': plan_id,
        'PlanName': plan.get('PlanName'),
        'Waves': plan.get('Waves', [])
    },
    'IsDrill': is_drill
}

stepfunctions.start_execution(
    stateMachineArn=state_machine_arn,
    name=execution_id,
    input=json.dumps(sfn_input)
)
```

## Frequently Used Code Idioms

### Environment Variable Access
```python
# Always provide defaults for optional variables
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN', '')
TIMEOUT_THRESHOLD = int(os.environ.get('TIMEOUT_THRESHOLD_SECONDS', '1800'))

# Required variables without defaults
PROTECTION_GROUPS_TABLE = os.environ['PROTECTION_GROUPS_TABLE']
```

### Timestamp Handling
```python
# Generate Unix timestamp (seconds)
timestamp = int(time.time())

# Convert to milliseconds for JavaScript
created_at_ms = int(created_at * 1000) if created_at else None

# Validate timestamp
if timestamp <= 0:
    print(f"WARNING: Invalid timestamp: {timestamp}")
    timestamp = int(time.time())
```

### DynamoDB Update Expressions
```python
# Build dynamic update expression
update_expression = "SET LastModifiedDate = :timestamp"
expression_values = {':timestamp': int(time.time())}
expression_names = {}

if 'Description' in body:
    update_expression += ", #desc = :desc"
    expression_values[':desc'] = body['Description']
    expression_names['#desc'] = 'Description'  # Reserved word

update_args = {
    'Key': {'PlanId': plan_id},
    'UpdateExpression': update_expression,
    'ExpressionAttributeValues': expression_values,
    'ReturnValues': 'ALL_NEW'
}

if expression_names:
    update_args['ExpressionAttributeNames'] = expression_names

result = table.update_item(**update_args)
```

### Cognito User Extraction
```python
def get_cognito_user_from_event(event: Dict) -> Dict:
    """Extract Cognito user info from API Gateway authorizer"""
    try:
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        return {
            'email': claims.get('email', 'system'),
            'userId': claims.get('sub', 'system'),
            'username': claims.get('cognito:username', 'system')
        }
    except Exception as e:
        print(f"Error extracting Cognito user: {e}")
        return {'email': 'system', 'userId': 'system', 'username': 'system'}
```

### Pagination Pattern
```python
# Handle DynamoDB pagination
scan_args = {'Limit': 50}
if next_token:
    scan_args['ExclusiveStartKey'] = json.loads(next_token)

result = table.scan(**scan_args)
items = result.get('Items', [])

# Return next token if more results
response_data = {'items': items}
if 'LastEvaluatedKey' in result:
    response_data['nextToken'] = json.dumps(result['LastEvaluatedKey'])
```

## Common Annotations and Decorators

### Pytest Fixtures
```python
@pytest.fixture
def mock_env(monkeypatch):
    """Set up environment variables for tests."""
    monkeypatch.setenv('TABLE_NAME', 'test-table')

@pytest.fixture
def mock_clients():
    """Mock all AWS clients."""
    with patch('module.boto3') as mock_boto3:
        yield mock_boto3
```

### CloudFormation Custom Resource
```python
from crhelper import CfnResource

helper = CfnResource(json_logging=False, log_level='DEBUG')

@helper.create
def create(event, context):
    """Handle CloudFormation CREATE event"""
    return physical_resource_id

@helper.update
def update(event, context):
    """Handle CloudFormation UPDATE event"""
    return physical_resource_id

@helper.delete
def delete(event, context):
    """Handle CloudFormation DELETE event"""
    pass
```

## Deployment and CI/CD Patterns

### GitLab CI/CD Pipeline

The project uses GitLab CI/CD with Amazon ECR Public images (to avoid Docker Hub rate limits).

**Pipeline Stages**:

```mermaid
flowchart LR
    V[validate] --> L[lint] --> B[build] --> T[test] --> DI[deploy-infra] --> DF[deploy-frontend]
```

**Docker Images** (ECR Public to avoid rate limits):
- Python: `public.ecr.aws/docker/library/python:3.12`
- Node.js: `public.ecr.aws/docker/library/node:22-alpine`
- AWS CLI: `public.ecr.aws/aws-cli/aws-cli:latest`

**Key Jobs**:
- `validate:cloudformation` - cfn-lint + AWS CLI validation
- `validate:frontend-types` - TypeScript type checking
- `lint:python` - pylint, black, flake8
- `lint:frontend` - ESLint
- `build:lambda` - Creates individual zip packages
- `build:frontend` - Vite production build
- `deploy:upload-artifacts` - Sync to S3 deployment bucket
- `deploy:cloudformation` - Deploy nested stacks
- `deploy:frontend` - S3 sync + CloudFront invalidation

**Note**: Test jobs are disabled until `tests/` directory is added to git.

### Local Deployment Script

**Primary Deployment Script**: `./scripts/sync-to-deployment-bucket.sh`

```bash
# Sync all code to S3 deployment bucket
./scripts/sync-to-deployment-bucket.sh

# Build frontend and deploy everything via CloudFormation
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-cfn

# Fast Lambda code updates (bypass CloudFormation, ~5 seconds)
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Deploy Lambda stack only via CloudFormation (~30 seconds)
./scripts/sync-to-deployment-bucket.sh --deploy-lambda

# Build and deploy frontend only
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend

# Preview changes without making them
./scripts/sync-to-deployment-bucket.sh --dry-run

# Use specific AWS profile
./scripts/sync-to-deployment-bucket.sh --profile MyProfile
```

**S3 Deployment Bucket Structure**:

```
aws-drs-orchestration/
├── cfn/                    # CloudFormation templates
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
│   ├── step-functions-stack.yaml
│   ├── security-stack.yaml
│   └── frontend-stack.yaml
├── lambda/                 # Lambda source files (NOT zip packages)
│   ├── index.py            # API handler
│   ├── drs_orchestrator.py # Legacy orchestrator
│   ├── orchestration_stepfunctions.py  # Step Functions handler
│   ├── build_and_deploy.py # Frontend builder
│   └── poller/
│       ├── execution_finder.py
│       └── execution_poller.py
├── frontend/
│   ├── dist/               # Built frontend (when --build-frontend used)
│   └── src/                # Frontend source
├── scripts/                # Automation scripts
├── ssm-documents/          # SSM automation documents
└── docs/                   # Documentation
```

**Note**: `deployment-package.zip` is only created during `--deploy-cfn` or `--deploy-lambda` operations, not during basic sync.

### Lambda Packaging Pattern

**CI/CD Creates Individual Packages** - Each Lambda function gets its own zip:

```bash
# CI/CD creates these packages:
lambda/api-handler.zip        # index.py + dependencies
lambda/orchestration.zip      # drs_orchestrator.py + dependencies
lambda/execution-finder.zip   # poller/execution_finder.py + dependencies
lambda/execution-poller.zip   # poller/execution_poller.py + dependencies
```

**Lambda Functions (6 deployed)**:
- `api-handler` - REST API endpoints (index.py)
- `orchestration-stepfunctions` - Step Functions orchestration engine
- `orchestration` - Legacy orchestrator (deprecated)
- `frontend-builder` - CloudFormation custom resource for frontend deployment
- `execution-finder` - EventBridge scheduled poller
- `execution-poller` - DRS job status updates

**Note**: `orchestration-stepfunctions.zip` and `frontend-builder.zip` are NOT built by CI/CD - they use inline code or are deployed separately.

### Environment Configuration Pattern

**Environment Files**:
- `.env.dev` - Development environment (API endpoints, Cognito config)
- `.env.test` - Test environment
- `.env.qa` - QA environment
- `.env.deployment` - Deployment bucket configuration

**Lambda Environment Variables**:

```python
# Standard environment variables for all functions
PROTECTION_GROUPS_TABLE = os.environ['PROTECTION_GROUPS_TABLE']
RECOVERY_PLANS_TABLE = os.environ['RECOVERY_PLANS_TABLE']
EXECUTION_HISTORY_TABLE = os.environ['EXECUTION_HISTORY_TABLE']
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN', '')
TIMEOUT_THRESHOLD_SECONDS = int(os.environ.get('TIMEOUT_THRESHOLD_SECONDS', '1800'))
```

### Frontend Build Pattern

**Automated Configuration Injection**:
- CI/CD generates `aws-config.js` from CloudFormation stack outputs
- CloudFormation custom resource can also build frontend with correct API endpoints
- No manual configuration file editing required

**aws-config.js Structure** (CRITICAL - must match this format):

```javascript
// Frontend expects this EXACT structure in aws-config.js
window.AWS_CONFIG = {
  Auth: {
    Cognito: {
      region: 'us-east-1',
      userPoolId: 'us-east-1_XXXXXXX',
      userPoolClientId: 'XXXXXXXXXXXXXXXXXXXXXXXXXX',  // NOT cognito.clientId
      loginWith: {
        email: true
      }
    }
  },
  API: {
    REST: {
      DRSOrchestration: {
        endpoint: 'https://XXXXXXXXXX.execute-api.us-east-1.amazonaws.com/ENV',
        region: 'us-east-1'
      }
    }
  }
};
```

**Common Mistake**: Using `cognito.clientId` instead of `Auth.Cognito.userPoolClientId` will cause authentication failures.

## Best Practices Summary

### Deployment Best Practices

1. **Always sync to S3 before deployment** - Use `./scripts/sync-to-deployment-bucket.sh`
2. **Use ECR Public images in CI/CD** - Avoid Docker Hub rate limits
3. **Fast Lambda updates** - Use `--update-lambda-code` for quick iterations (~5s)
4. **Full deployments** - Use `--deploy-cfn` for infrastructure changes (5-10 min)
5. **Verify S3 artifacts are current** - Check timestamps after deployment
6. **Use correct aws-config.js structure** - `Auth.Cognito.userPoolClientId` not `cognito.clientId`

### Code Quality Best Practices

7. **Validate input data** - Check types, required fields, and business rules
8. **Use type hints** - Makes code self-documenting and enables IDE autocomplete
9. **Log extensively** - Include context in error messages for debugging
10. **Handle errors gracefully** - Return structured error responses with codes
11. **Transform data at boundaries** - Convert between PascalCase and camelCase

### AWS Integration Best Practices

12. **Trust DRS LAUNCHED status** - Don't require recoveryInstanceID from job response
13. **Use composite keys correctly** - DynamoDB requires both partition and sort keys
14. **Implement GSI fallback** - Query with GSI, fallback to scan if unavailable
15. **Avoid API Gateway timeouts** - Use async Lambda invocation for long operations
16. **Test with mocks** - Mock AWS services for fast, reliable unit tests

### CLI Best Practices

17. **Always use `--no-pager` for git commands** - Prevents terminal hangs
18. **Always use `AWS_PAGER=""` for AWS CLI** - Prevents interactive pager issues
