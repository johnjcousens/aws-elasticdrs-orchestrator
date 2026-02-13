make sure follow all blacvk# Design Document: Staging Accounts Management

## Overview

The Staging Accounts Management feature extends DRS replication capacity by enabling users to configure multiple staging accounts alongside their target account. Each account provides 300 servers of replication capacity, allowing organizations to scale beyond single-account limits. The system provides a comprehensive UI for managing staging accounts, validates access before configuration, and displays real-time capacity metrics across all accounts with intelligent warnings.

The design follows a multi-tier architecture with React/TypeScript frontend components, API Gateway endpoints, Python Lambda handlers for business logic, and DynamoDB for persistent storage. Capacity queries execute concurrently across all accounts and regions to provide fast, accurate metrics.

## Architecture

### System Components

```mermaid
flowchart TB
    subgraph Frontend["Frontend (React/TypeScript)"]
        Dashboard[Capacity Dashboard]
        SettingsModal[Target Account Settings Modal]
        AddModal[Add Staging Account Modal]
        DetailModal[Capacity Details Modal]
    end
    
    subgraph API["API Gateway"]
        ValidateEndpoint[POST /staging-accounts/validate]
        AddEndpoint[POST /accounts/{id}/staging-accounts]
        RemoveEndpoint[DELETE /accounts/{id}/staging-accounts/{stagingId}]
        CapacityEndpoint[GET /accounts/{id}/capacity]
    end
    
    subgraph Lambda["Lambda Handlers"]
        DataMgmt[Data Management Handler]
        Query[Query Handler]
    end
    
    subgraph Storage["DynamoDB"]
        TargetAccounts[(Target Accounts Table)]
    end
    
    subgraph AWS["AWS Services"]
        STS[STS - AssumeRole]
        DRS[DRS - DescribeSourceServers]
    end
    
    Dashboard --> CapacityEndpoint
    SettingsModal --> AddEndpoint
    SettingsModal --> RemoveEndpoint
    AddModal --> ValidateEndpoint
    DetailModal --> CapacityEndpoint
    
    ValidateEndpoint --> Query
    AddEndpoint --> DataMgmt
    RemoveEndpoint --> DataMgmt
    CapacityEndpoint --> Query
    
    DataMgmt --> TargetAccounts
    Query --> TargetAccounts
    Query --> STS
    Query --> DRS
```

### Data Flow

**Adding a Staging Account:**
1. User fills staging account form (account ID, name, role ARN, external ID, region)
2. User clicks "Validate Access"
3. Frontend calls `POST /staging-accounts/validate`
4. Query Lambda assumes role in staging account
5. Query Lambda checks DRS initialization and counts servers
6. Validation results returned to frontend
7. User clicks "Add Account"
8. Frontend calls `POST /accounts/{targetId}/staging-accounts`
9. Data Management Lambda updates Target Accounts table
10. Frontend refreshes capacity dashboard

**Querying Combined Capacity:**
1. Frontend calls `GET /accounts/{targetId}/capacity`
2. Query Lambda retrieves target account config from DynamoDB
3. Query Lambda extracts staging accounts list
4. Query Lambda queries target account + all staging accounts in parallel
5. For each account, Query Lambda queries all DRS regions concurrently
6. Query Lambda aggregates results and calculates combined metrics
7. Query Lambda determines status and generates warnings
8. Combined capacity data returned to frontend

## Components and Interfaces

### Frontend Components

#### CapacityDashboard.tsx

Displays combined capacity metrics with per-account breakdown and warnings.

**Props:**
```typescript
interface CapacityDashboardProps {
  targetAccountId: string;
  refreshInterval?: number; // milliseconds, default 30000
}
```

**State:**
```typescript
interface CapacityDashboardState {
  loading: boolean;
  error: string | null;
  capacityData: CombinedCapacityData | null;
  lastRefresh: Date | null;
}

interface CombinedCapacityData {
  combined: {
    totalReplicating: number;
    maxReplicating: number;
    percentUsed: number;
    status: 'OK' | 'INFO' | 'WARNING' | 'CRITICAL' | 'HYPER-CRITICAL';
    message: string;
  };
  accounts: AccountCapacity[];
  recoveryCapacity: {
    currentServers: number;
    maxRecoveryInstances: number;
    percentUsed: number;
    availableSlots: number;
  };
  warnings: string[];
}

interface AccountCapacity {
  accountId: string;
  accountName: string;
  accountType: 'target' | 'staging';
  replicatingServers: number;
  totalServers: number;
  maxReplicating: number;
  percentUsed: number;
  availableSlots: number;
  status: 'OK' | 'INFO' | 'WARNING' | 'CRITICAL' | 'HYPER-CRITICAL';
  regionalBreakdown: RegionalCapacity[];
  warnings: string[];
}

interface RegionalCapacity {
  region: string;
  totalServers: number;
  replicatingServers: number;
}
```

**Key Methods:**
- `fetchCapacity()`: Calls API to retrieve combined capacity data
- `getStatusColor(status)`: Returns CloudScape color for status indicator
- `formatCapacityBar(percentUsed)`: Renders progress bar with appropriate styling
- `renderWarnings()`: Displays warning alerts with actionable guidance

#### TargetAccountSettingsModal.tsx

Modal for editing target account configuration including staging accounts list.

**Props:**
```typescript
interface TargetAccountSettingsModalProps {
  targetAccount: TargetAccount;
  visible: boolean;
  onDismiss: () => void;
  onSave: (updatedAccount: TargetAccount) => Promise<void>;
}

interface TargetAccount {
  accountId: string;
  accountName: string;
  roleArn: string;
  externalId: string;
  stagingAccounts: StagingAccount[];
}

interface StagingAccount {
  accountId: string;
  accountName: string;
  roleArn: string;
  externalId: string;
  status?: 'connected' | 'error' | 'validating';
  serverCount?: number;
  replicatingCount?: number;
}
```

**State:**
```typescript
interface SettingsModalState {
  formData: TargetAccount;
  showAddStaging: boolean;
  saving: boolean;
  error: string | null;
}
```

**Key Methods:**
- `handleAddStagingAccount(staging)`: Adds staging account to list
- `handleRemoveStagingAccount(accountId)`: Removes staging account from list
- `handleSave()`: Saves updated configuration to backend
- `testStagingConnection(accountId)`: Tests connectivity to staging account

#### AddStagingAccountModal.tsx

Nested modal for adding a new staging account with validation.

**Props:**
```typescript
interface AddStagingAccountModalProps {
  visible: boolean;
  onDismiss: () => void;
  onAdd: (stagingAccount: StagingAccount) => void;
  targetAccountId: string;
}
```

**State:**
```typescript
interface AddStagingModalState {
  formData: {
    accountId: string;
    accountName: string;
    roleArn: string;
    externalId: string;
    region: string;
  };
  validating: boolean;
  validationResult: ValidationResult | null;
  errors: Record<string, string>;
}

interface ValidationResult {
  valid: boolean;
  roleAccessible: boolean;
  drsInitialized: boolean;
  currentServers: number;
  replicatingServers: number;
  totalAfter: number;
  error?: string;
}
```

**Key Methods:**
- `validateForm()`: Validates input fields (account ID format, ARN format, etc.)
- `handleValidate()`: Calls API to validate staging account access
- `handleAdd()`: Adds validated staging account
- `formatValidationResults()`: Renders validation results with status indicators

#### CapacityDetailsModal.tsx

Detailed view showing per-account and per-region capacity breakdown.

**Props:**
```typescript
interface CapacityDetailsModalProps {
  capacityData: CombinedCapacityData;
  visible: boolean;
  onDismiss: () => void;
}
```

**Key Methods:**
- `renderAccountDetails(account)`: Renders detailed metrics for single account
- `renderRegionalBreakdown(regions)`: Renders regional capacity table
- `renderCapacityPlanning()`: Shows capacity planning recommendations

### Backend Components

#### Data Management Lambda Handler

Handles staging account add/remove operations and DynamoDB updates.

**Operations:**
```python
def handle_add_staging_account(event: Dict) -> Dict:
    """
    Add staging account to target account configuration.
    
    Input:
    {
        "operation": "add_staging_account",
        "targetAccountId": "160885257264",
        "stagingAccount": {
            "accountId": "664418995426",
            "accountName": "STAGING_01",
            "roleArn": "arn:aws:iam::664418995426:role/DRSOrchestrationRole-test",
            "externalId": "drs-orchestration-test-664418995426"
        }
    }
    
    Output:
    {
        "success": true,
        "message": "Added staging account STAGING_01",
        "stagingAccounts": [...]
    }
    """
    pass

def handle_remove_staging_account(event: Dict) -> Dict:
    """
    Remove staging account from target account configuration.
    
    Input:
    {
        "operation": "remove_staging_account",
        "targetAccountId": "160885257264",
        "stagingAccountId": "664418995426"
    }
    
    Output:
    {
        "success": true,
        "message": "Removed staging account 664418995426",
        "stagingAccounts": [...]
    }
    """
    pass
```

**Key Functions:**
- `validate_staging_account_input(staging)`: Validates staging account structure
- `check_duplicate_staging_account(target_id, staging_id)`: Checks if staging account already exists
- `update_target_account_staging_accounts(target_id, staging_accounts)`: Updates DynamoDB

#### Query Lambda Handler

Handles capacity queries, validation, and multi-account DRS queries.

**Operations:**
```python
def handle_validate_staging_account(event: Dict) -> Dict:
    """
    Validate staging account access and DRS status.
    
    Input:
    {
        "operation": "validate_staging_account",
        "accountId": "664418995426",
        "roleArn": "arn:aws:iam::664418995426:role/DRSOrchestrationRole-test",
        "externalId": "drs-orchestration-test-664418995426",
        "region": "us-west-2"
    }
    
    Output:
    {
        "valid": true,
        "roleAccessible": true,
        "drsInitialized": true,
        "currentServers": 42,
        "replicatingServers": 42,
        "totalAfter": 267
    }
    """
    pass

def handle_get_combined_capacity(event: Dict) -> Dict:
    """
    Get combined capacity across target and staging accounts.
    
    Input:
    {
        "operation": "get_combined_capacity",
        "targetAccountId": "160885257264"
    }
    
    Output: CombinedCapacityData (see frontend interface)
    """
    pass
```

**Key Functions:**
- `assume_role_in_account(role_arn, external_id)`: Assumes role for cross-account access
- `check_drs_initialization(drs_client, region)`: Checks if DRS is initialized
- `count_drs_servers(drs_client)`: Counts total and replicating servers
- `query_account_capacity(account_config)`: Queries single account capacity
- `query_all_accounts_parallel(target, staging_list)`: Queries all accounts concurrently
- `calculate_combined_metrics(account_results)`: Aggregates results
- `determine_status_and_warnings(metrics)`: Calculates status and generates warnings

### API Endpoints

#### POST /api/staging-accounts/validate

Validates staging account access before adding.

**Request:**
```json
{
  "accountId": "664418995426",
  "roleArn": "arn:aws:iam::664418995426:role/DRSOrchestrationRole-test",
  "externalId": "drs-orchestration-test-664418995426",
  "region": "us-west-2"
}
```

**Response (Success):**
```json
{
  "valid": true,
  "roleAccessible": true,
  "drsInitialized": true,
  "currentServers": 42,
  "replicatingServers": 42,
  "totalAfter": 267
}
```

**Response (Error):**
```json
{
  "valid": false,
  "error": "Unable to assume role: Access Denied"
}
```

#### POST /api/accounts/{targetAccountId}/staging-accounts

Adds staging account to target account configuration.

**Request:**
```json
{
  "accountId": "664418995426",
  "accountName": "STAGING_01",
  "roleArn": "arn:aws:iam::664418995426:role/DRSOrchestrationRole-test",
  "externalId": "drs-orchestration-test-664418995426"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Added staging account STAGING_01",
  "stagingAccounts": [...]
}
```

#### DELETE /api/accounts/{targetAccountId}/staging-accounts/{stagingAccountId}

Removes staging account from target account configuration.

**Response:**
```json
{
  "success": true,
  "message": "Removed staging account 664418995426",
  "stagingAccounts": [...]
}
```

#### GET /api/accounts/{targetAccountId}/capacity

Retrieves combined capacity metrics.

**Response:** See `CombinedCapacityData` interface above.

## Data Models

### DynamoDB Schema

#### Target Accounts Table

**Table Name:** `hrp-drs-tech-adapter-target-accounts-{environment}`

**Primary Key:** `accountId` (String)

**Attributes:**
```json
{
  "accountId": "160885257264",
  "accountName": "DEMO_TARGET",
  "roleArn": "arn:aws:iam::160885257264:role/DRSOrchestrationRole-test",
  "externalId": "drs-orchestration-test-160885257264",
  "stagingAccounts": [
    {
      "accountId": "664418995426",
      "accountName": "STAGING_01",
      "roleArn": "arn:aws:iam::664418995426:role/DRSOrchestrationRole-test",
      "externalId": "drs-orchestration-test-664418995426"
    },
    {
      "accountId": "777777777777",
      "accountName": "STAGING_02",
      "roleArn": "arn:aws:iam::777777777777:role/DRSOrchestrationRole-test",
      "externalId": "drs-orchestration-test-777777777777"
    }
  ],
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-20T14:45:00Z"
}
```

**New Attribute:**
- `stagingAccounts` (List): Array of staging account configurations

### Capacity Status Thresholds

**Per-Account Status:**
- **OK**: 0-200 servers (0-67%)
- **INFO**: 200-225 servers (67-75%)
- **WARNING**: 225-250 servers (75-83%)
- **CRITICAL**: 250-280 servers (83-93%)
- **HYPER-CRITICAL**: 280-300 servers (93-100%)

**Operational Limit:** 250 servers per account (leaves 50-server safety buffer)
**Hard Limit:** 300 servers per account (AWS enforced)

**Combined Status Calculation:**
```python
def calculate_combined_status(total_replicating: int, num_accounts: int) -> str:
    operational_capacity = num_accounts * 250
    hard_capacity = num_accounts * 300
    
    if total_replicating >= hard_capacity:
        return "HYPER-CRITICAL"
    elif total_replicating >= operational_capacity:
        return "CRITICAL"
    
    percent_of_operational = (total_replicating / operational_capacity) * 100
    
    if percent_of_operational >= 93:
        return "WARNING"
    elif percent_of_operational >= 83:
        return "INFO"
    else:
        return "OK"
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Staging Account Persistence Round Trip

*For any* valid staging account configuration, adding it to a target account then retrieving the target account should return the staging account with all original fields (account ID, account name, role ARN, external ID) intact.

**Validates: Requirements 1.6, 8.1, 8.2, 8.3**

### Property 2: Staging Account Removal Completeness

*For any* target account with staging accounts, removing a specific staging account should result in that account no longer appearing in the staging accounts list while all other staging accounts remain unchanged.

**Validates: Requirements 2.2, 8.4**

### Property 3: Combined Capacity Aggregation

*For any* set of accounts (target + staging) with known server counts, the combined replicating servers should equal the sum of replicating servers across all accounts, and the maximum capacity should equal the number of accounts multiplied by 300.

**Validates: Requirements 4.2, 4.3, 9.6**

### Property 4: Per-Account Status Calculation

*For any* account with a given number of replicating servers, the status should be:
- OK when servers are 0-200 (0-67%)
- INFO when servers are 200-225 (67-75%)
- WARNING when servers are 225-250 (75-83%)
- CRITICAL when servers are 250-280 (83-93%)
- HYPER-CRITICAL when servers are 280-300 (93-100%)

**Validates: Requirements 5.3, 5.4, 5.5, 5.6**

### Property 5: Warning Generation Based on Thresholds

*For any* account capacity state, warnings should be generated when:
- Any account reaches 200-225 servers (INFO warning)
- Any account reaches 225-250 servers (WARNING)
- Any account reaches 250-280 servers (CRITICAL warning)
- Any account reaches 280-300 servers (HYPER-CRITICAL warning)
- Combined capacity exceeds operational limits (combined warning)

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**

### Property 6: Validation Result Completeness

*For any* staging account validation attempt, the validation result should include all required fields: role accessibility status (boolean), DRS initialization status (boolean), current server count (number), replicating server count (number), and projected combined capacity (number).

**Validates: Requirements 3.4, 1.4**

### Property 7: Validation Error Handling

*For any* validation failure scenario (role assumption failure or DRS not initialized), the validation result should have valid=false and include a descriptive error message explaining the failure reason.

**Validates: Requirements 3.5, 3.6, 1.5**

### Property 8: Multi-Account Query Parallelism

*For any* target account with N staging accounts, querying combined capacity should initiate N+1 concurrent account queries (target + all staging accounts), and each account query should initiate concurrent queries across all DRS-enabled regions.

**Validates: Requirements 9.1, 9.3**

### Property 9: Uninitialized Region Handling

*For any* account query where DRS is not initialized in a region, that region should contribute zero servers to the account's total count, and the query should continue successfully for other regions.

**Validates: Requirements 9.4**

### Property 10: Failed Account Resilience

*For any* combined capacity query where role assumption fails for one or more staging accounts, the query should mark those accounts as inaccessible, continue querying remaining accessible accounts, and return partial results with error indicators for failed accounts.

**Validates: Requirements 9.5**

### Property 11: Recovery Capacity Status Calculation

*For any* target account with a given number of replicating servers, the recovery capacity status should be:
- OK when servers are below 3,200 (< 80% of 4,000)
- WARNING when servers are 3,200-3,600 (80-90%)
- CRITICAL when servers exceed 3,600 (> 90%)

And recovery capacity should only count servers in the target account, excluding staging account servers.

**Validates: Requirements 10.2, 10.3, 10.4, 10.5**

### Property 12: Account Breakdown Completeness

*For any* combined capacity query result, the account breakdown should include all accounts (target + all staging accounts), and each account entry should contain all required fields: account ID, account name, account type, replicating servers, maximum capacity, percentage used, status, and regional breakdown.

**Validates: Requirements 5.1, 5.2, 5.7**

### Property 13: Empty Staging Accounts Default

*For any* target account where the stagingAccounts attribute does not exist in DynamoDB, querying the target account should return an empty list for staging accounts rather than null or undefined.

**Validates: Requirements 8.5**

### Property 14: CLI Operation Response Structure

*For any* CLI operation (add_staging_account, remove_staging_account, validate_staging_account, get_target_account), the response should be valid JSON containing either a success field (boolean) with relevant data, or an error field with a descriptive error message.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

### Property 15: Capacity Dashboard Refresh After Modification

*For any* staging account add or remove operation, the capacity dashboard should re-query combined capacity to reflect the updated account configuration.

**Validates: Requirements 1.7, 2.3**

## Error Handling

### Frontend Error Handling

**API Call Failures:**
- Display user-friendly error messages in Alert components
- Preserve form data when validation fails
- Provide retry mechanisms for transient failures
- Log errors to console for debugging

**Validation Errors:**
- Display field-level validation errors inline
- Prevent form submission until validation passes
- Highlight invalid fields with error styling
- Provide clear guidance on how to fix errors

**Network Errors:**
- Display "Unable to connect" messages
- Implement automatic retry with exponential backoff
- Show loading states during retries
- Allow manual retry via button

### Backend Error Handling

**Role Assumption Failures:**
```python
try:
    credentials = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName="drs-orchestration-staging-validation",
        ExternalId=external_id
    )
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'AccessDenied':
        return {
            "valid": False,
            "error": "Unable to assume role: Access Denied. Verify role trust policy and external ID."
        }
    elif error_code == 'InvalidClientTokenId':
        return {
            "valid": False,
            "error": "Invalid credentials. Verify role ARN is correct."
        }
    else:
        return {
            "valid": False,
            "error": f"Role assumption failed: {str(e)}"
        }
```

**DRS Uninitialized:**
```python
try:
    response = drs_client.describe_source_servers()
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'UninitializedAccountException':
        return {
            "valid": False,
            "error": "DRS is not initialized in this account. Initialize DRS before adding as staging account."
        }
    else:
        raise
```

**DynamoDB Errors:**
```python
try:
    response = table.update_item(...)
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'ConditionalCheckFailedException':
        return {
            "error": "TARGET_ACCOUNT_NOT_FOUND",
            "message": f"Target account {target_account_id} not found"
        }
    elif error_code == 'ProvisionedThroughputExceededException':
        # Implement exponential backoff retry
        time.sleep(2 ** retry_count)
        return retry_operation()
    else:
        logger.exception("DynamoDB error")
        raise
```

**Concurrent Query Failures:**
```python
def query_account_with_error_handling(account_config):
    try:
        return query_account_capacity(account_config)
    except Exception as e:
        logger.error(f"Failed to query account {account_config['accountId']}: {str(e)}")
        return {
            "accountId": account_config["accountId"],
            "accountName": account_config.get("accountName", "Unknown"),
            "status": "ERROR",
            "error": str(e),
            "replicatingServers": 0,
            "accessible": False
        }

# Use in parallel queries
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(query_account_with_error_handling, account)
        for account in all_accounts
    ]
    results = [future.result() for future in as_completed(futures)]
```

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests:**
- Specific examples demonstrating correct behavior
- Edge cases (empty staging accounts list, single account, maximum accounts)
- Error conditions (role assumption failures, DRS uninitialized, network errors)
- Integration points (API Gateway to Lambda, Lambda to DynamoDB)
- UI component rendering with specific data

**Property-Based Tests:**
- Universal properties across all inputs (see Correctness Properties section)
- Comprehensive input coverage through randomization
- Minimum 100 iterations per property test
- Each test references its design document property

### Property-Based Testing Configuration

**Framework:** Use `hypothesis` for Python backend tests, `fast-check` for TypeScript frontend tests

**Test Configuration:**
```python
# Python (pytest + hypothesis)
from hypothesis import given, strategies as st, settings

@settings(max_examples=100)
@given(
    staging_accounts=st.lists(
        st.fixed_dictionaries({
            'accountId': st.from_regex(r'\d{12}', fullmatch=True),
            'accountName': st.text(min_size=1, max_size=50),
            'roleArn': st.from_regex(r'arn:aws:iam::\d{12}:role/[\w+=,.@-]+', fullmatch=True),
            'externalId': st.text(min_size=1, max_size=100)
        }),
        min_size=0,
        max_size=10
    )
)
def test_property_1_staging_account_round_trip(staging_accounts):
    """
    Feature: staging-accounts-management
    Property 1: For any valid staging account configuration, adding it to a 
    target account then retrieving the target account should return the staging 
    account with all original fields intact.
    """
    # Test implementation
    pass
```

```typescript
// TypeScript (vitest + fast-check)
import fc from 'fast-check';
import { describe, it, expect } from 'vitest';

describe('Property 4: Per-Account Status Calculation', () => {
  it('should calculate correct status for any server count', () => {
    /**
     * Feature: staging-accounts-management
     * Property 4: For any account with a given number of replicating servers,
     * the status should match the defined thresholds.
     */
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 300 }),
        (serverCount) => {
          const status = calculateAccountStatus(serverCount);
          
          if (serverCount < 200) {
            expect(status).toBe('OK');
          } else if (serverCount < 225) {
            expect(status).toBe('INFO');
          } else if (serverCount < 250) {
            expect(status).toBe('WARNING');
          } else if (serverCount < 280) {
            expect(status).toBe('CRITICAL');
          } else {
            expect(status).toBe('HYPER-CRITICAL');
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

### Unit Test Examples

**Backend Unit Tests:**
```python
def test_add_staging_account_success():
    """Test adding a staging account to target account."""
    event = {
        "operation": "add_staging_account",
        "targetAccountId": "160885257264",
        "stagingAccount": {
            "accountId": "664418995426",
            "accountName": "STAGING_01",
            "roleArn": "arn:aws:iam::664418995426:role/DRSOrchestrationRole-test",
            "externalId": "drs-orchestration-test-664418995426"
        }
    }
    
    result = handle_add_staging_account(event)
    
    assert result["success"] is True
    assert "STAGING_01" in result["message"]
    assert len(result["stagingAccounts"]) == 1

def test_add_duplicate_staging_account():
    """Test adding a staging account that already exists."""
    # Setup: Add staging account first
    # Then: Try to add same account again
    # Assert: Error returned
    pass

def test_remove_staging_account_with_servers():
    """Test removing staging account with active servers shows warning."""
    # Setup: Staging account with 150 replicating servers
    # When: Remove staging account
    # Assert: Warning about capacity impact is included
    pass
```

**Frontend Unit Tests:**
```typescript
describe('AddStagingAccountModal', () => {
  it('should validate account ID format', () => {
    render(<AddStagingAccountModal {...props} />);
    
    const accountIdInput = screen.getByLabelText('Account ID');
    fireEvent.change(accountIdInput, { target: { value: 'invalid' } });
    fireEvent.blur(accountIdInput);
    
    expect(screen.getByText(/must be 12 digits/i)).toBeInTheDocument();
  });
  
  it('should display validation results after successful validation', async () => {
    const mockValidate = vi.fn().mockResolvedValue({
      valid: true,
      roleAccessible: true,
      drsInitialized: true,
      currentServers: 42,
      replicatingServers: 42
    });
    
    render(<AddStagingAccountModal {...props} onValidate={mockValidate} />);
    
    // Fill form and click validate
    // Assert validation results are displayed
  });
  
  it('should disable Add button until validation succeeds', () => {
    render(<AddStagingAccountModal {...props} />);
    
    const addButton = screen.getByText('Add Account');
    expect(addButton).toBeDisabled();
    
    // After successful validation
    // Assert button is enabled
  });
});

describe('CapacityDashboard', () => {
  it('should display combined capacity with correct status', () => {
    const capacityData = {
      combined: {
        totalReplicating: 267,
        maxReplicating: 1200,
        percentUsed: 22,
        status: 'OK',
        message: 'Capacity OK'
      },
      accounts: [],
      recoveryCapacity: {},
      warnings: []
    };
    
    render(<CapacityDashboard capacityData={capacityData} />);
    
    expect(screen.getByText(/267.*1,200/)).toBeInTheDocument();
    expect(screen.getByText(/OK/)).toBeInTheDocument();
  });
  
  it('should display warnings when capacity exceeds thresholds', () => {
    const capacityData = {
      combined: { status: 'WARNING', /* ... */ },
      warnings: ['STAGING_01 at 50% capacity']
    };
    
    render(<CapacityDashboard capacityData={capacityData} />);
    
    expect(screen.getByText(/STAGING_01 at 50%/)).toBeInTheDocument();
  });
});
```

### Integration Tests

**API Integration Tests:**
```python
def test_add_staging_account_api_integration():
    """Test complete flow from API Gateway to DynamoDB."""
    # Setup: Create target account in DynamoDB
    # When: POST to /api/accounts/{id}/staging-accounts
    # Assert: Staging account added to DynamoDB
    # Assert: Response contains updated staging accounts list
    pass

def test_capacity_query_with_multiple_staging_accounts():
    """Test capacity query with target + 3 staging accounts."""
    # Setup: Configure target account with 3 staging accounts
    # Mock: DRS responses for all accounts
    # When: GET /api/accounts/{id}/capacity
    # Assert: Combined capacity calculated correctly
    # Assert: All 4 accounts in breakdown
    pass
```

### CLI Script Tests

**CLI Operation Tests:**
```bash
#!/bin/bash
# test-cli-operations.sh

# Test add staging account
echo "Testing add staging account..."
./scripts/add-staging-account.sh 160885257264 664418995426 STAGING_01
if [ $? -eq 0 ]; then
    echo "✅ Add staging account succeeded"
else
    echo "❌ Add staging account failed"
    exit 1
fi

# Test list staging accounts
echo "Testing list staging accounts..."
./scripts/list-staging-accounts.sh 160885257264 | grep "STAGING_01"
if [ $? -eq 0 ]; then
    echo "✅ List staging accounts succeeded"
else
    echo "❌ List staging accounts failed"
    exit 1
fi

# Test remove staging account
echo "Testing remove staging account..."
./scripts/remove-staging-account.sh 160885257264 664418995426
if [ $? -eq 0 ]; then
    echo "✅ Remove staging account succeeded"
else
    echo "❌ Remove staging account failed"
    exit 1
fi
```

### Performance Tests

**Concurrent Query Performance:**
```python
def test_capacity_query_performance_with_10_accounts():
    """Test that querying 10 accounts completes within 5 seconds."""
    # Setup: Target account with 9 staging accounts
    # Mock: DRS responses with 100ms delay per region
    # When: Query combined capacity
    # Assert: Completes in < 5 seconds (parallel execution)
    pass
```

### Test Coverage Goals

- **Backend Code Coverage:** Minimum 80%
- **Frontend Code Coverage:** Minimum 75%
- **Property Tests:** All 15 correctness properties implemented
- **Unit Tests:** All edge cases and error conditions covered
- **Integration Tests:** All API endpoints tested end-to-end
