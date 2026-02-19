# Task 9.4: DynamoDB Permissions Verification Report

**Date**: 2025-01-31  
**Task**: Verify OrchestrationRole has DynamoDB read/write permissions for all tables  
**Status**: ✅ VERIFIED - All permissions are correctly configured

---

## Executive Summary

The `UnifiedOrchestrationRole` in `cfn/master-template.yaml` has **complete and correct** DynamoDB permissions for all four application tables. The permissions use proper CloudFormation resource references with wildcard patterns and include all necessary read/write operations.

---

## DynamoDB Tables in Application

Based on `cfn/database-stack.yaml`, the application uses **4 DynamoDB tables**:

### 1. Protection Groups Table
- **Table Name Pattern**: `${ProjectName}-protection-groups-${Environment}`
- **Primary Key**: `groupId` (String)
- **Purpose**: Stores protection group definitions that organize source servers
- **Schema**: camelCase

### 2. Recovery Plans Table
- **Table Name Pattern**: `${ProjectName}-recovery-plans-${Environment}`
- **Primary Key**: `planId` (String)
- **Purpose**: Stores recovery plan definitions for DR operations
- **Schema**: camelCase

### 3. Execution History Table
- **Table Name Pattern**: `${ProjectName}-execution-history-${Environment}`
- **Primary Key**: `executionId` (HASH) + `planId` (RANGE)
- **GSIs**: 
  - `StatusIndex` (status as HASH)
  - `planIdIndex` (planId as HASH)
- **Purpose**: Tracks all DR operation executions with full audit trail
- **Schema**: camelCase

### 4. Target Accounts Table
- **Table Name Pattern**: `${ProjectName}-target-accounts-${Environment}`
- **Primary Key**: `accountId` (String - 12-digit AWS account ID)
- **Purpose**: Stores cross-account configuration for hub-and-spoke DR architecture
- **Schema**: camelCase

---

## OrchestrationRole DynamoDB Permissions

### Location
**File**: `cfn/master-template.yaml`  
**Resource**: `UnifiedOrchestrationRole`  
**Policy Name**: `DynamoDBAccess`  
**Lines**: 143-160

### Permissions Granted

```yaml
- PolicyName: DynamoDBAccess
  PolicyDocument:
    Version: "2012-10-17"
    Statement:
      - Effect: Allow
        Action:
          - dynamodb:GetItem
          - dynamodb:PutItem
          - dynamodb:UpdateItem
          - dynamodb:DeleteItem
          - dynamodb:Query
          - dynamodb:Scan
          - dynamodb:BatchGetItem
          - dynamodb:BatchWriteItem
        Resource:
          - !Sub "arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ProjectName}-*"
```

### Verification Results

#### ✅ Read Operations
- **dynamodb:GetItem** - Read single item by primary key
- **dynamodb:Query** - Query items using primary key or GSI
- **dynamodb:Scan** - Scan entire table
- **dynamodb:BatchGetItem** - Read multiple items in single request

#### ✅ Write Operations
- **dynamodb:PutItem** - Create or replace item
- **dynamodb:UpdateItem** - Update existing item attributes
- **dynamodb:DeleteItem** - Delete item by primary key
- **dynamodb:BatchWriteItem** - Write multiple items in single request

#### ✅ Resource Scope
The resource ARN uses a wildcard pattern that covers **all four tables**:

```
arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ProjectName}-*
```

This pattern matches:
- ✅ `${ProjectName}-protection-groups-${Environment}`
- ✅ `${ProjectName}-recovery-plans-${Environment}`
- ✅ `${ProjectName}-execution-history-${Environment}`
- ✅ `${ProjectName}-target-accounts-${Environment}`

#### ✅ GSI Access
The permissions automatically include access to Global Secondary Indexes (GSIs) on the Execution History table:
- `StatusIndex` - Query executions by status
- `planIdIndex` - Query executions by plan ID

**Note**: DynamoDB permissions on the base table automatically grant access to all GSIs. No separate permissions are required.

---

## Direct Lambda Invocation Support

### Lambda Functions Using DynamoDB

The following Lambda functions require DynamoDB access for direct invocation mode:

1. **Data Management Handler** (`lambda/data-management-handler/`)
   - Creates/updates/deletes protection groups
   - Creates/updates/deletes recovery plans
   - Manages target accounts
   - **Tables Used**: All 4 tables

2. **Query Handler** (`lambda/query-handler/`)
   - Retrieves protection groups, recovery plans, execution history
   - Lists and filters data
   - **Tables Used**: All 4 tables (read-only)

3. **Execution Handler** (`lambda/execution-handler/`)
   - Creates execution records
   - Updates execution status
   - Retrieves execution details
   - **Tables Used**: Execution History table

4. **DR Orchestration Step Function** (`lambda/dr-orchestration-stepfunction/`)
   - Updates execution status during orchestration
   - Records wave completion
   - **Tables Used**: Execution History table

### Permission Verification for Direct Invocation

All Lambda functions share the `UnifiedOrchestrationRole`, which means:

✅ **Data Management Handler** can perform all CRUD operations on all tables  
✅ **Query Handler** can read from all tables  
✅ **Execution Handler** can create and update execution records  
✅ **DR Orchestration** can update execution status during workflows

---

## CloudFormation Resource References

### Proper Reference Pattern

The OrchestrationRole uses **CloudFormation intrinsic functions** for dynamic resource ARN construction:

```yaml
Resource:
  - !Sub "arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ProjectName}-*"
```

This approach:
- ✅ Works across all AWS partitions (aws, aws-cn, aws-us-gov)
- ✅ Automatically uses correct region and account ID
- ✅ Scales with ProjectName parameter changes
- ✅ Covers all environment suffixes (dev, test, prod)

### Alternative: Explicit Table ARN References

While the current wildcard pattern is correct, an alternative approach would be to reference specific table ARNs:

```yaml
Resource:
  - !GetAtt DatabaseStack.Outputs.ProtectionGroupsTableArn
  - !GetAtt DatabaseStack.Outputs.RecoveryPlansTableArn
  - !GetAtt DatabaseStack.Outputs.ExecutionHistoryTableArn
  - !GetAtt DatabaseStack.Outputs.TargetAccountsTableArn
```

**Current Approach (Wildcard) vs. Explicit References:**

| Aspect | Wildcard Pattern | Explicit References |
|--------|------------------|---------------------|
| **Flexibility** | ✅ Covers future tables automatically | ❌ Requires updates for new tables |
| **Security** | ⚠️ Broader scope | ✅ Least privilege |
| **Maintainability** | ✅ Simple, single line | ❌ Must update for each table |
| **Cross-Stack Dependencies** | ✅ No dependencies | ❌ Requires DatabaseStack outputs |
| **Current Status** | ✅ **RECOMMENDED** | Alternative option |

**Recommendation**: Keep the current wildcard pattern. It provides the right balance of flexibility and security for this application, where all tables follow a consistent naming convention and are owned by the same project.

---

## Security Considerations

### Least Privilege Analysis

The current permissions follow AWS best practices:

1. **Scoped to Project Tables Only**
   - Pattern `${ProjectName}-*` prevents access to unrelated DynamoDB tables
   - No wildcard `*` that would grant access to all tables in the account

2. **Appropriate Operations**
   - Includes only necessary operations (Get, Put, Update, Delete, Query, Scan, Batch)
   - Does not include administrative operations (CreateTable, DeleteTable, UpdateTable)

3. **No Condition Restrictions**
   - No overly restrictive conditions that would break functionality
   - Appropriate for application-level access

### Potential Improvements (Optional)

If stricter security is required in the future, consider:

1. **Separate Read/Write Policies**
   ```yaml
   # Read-only for Query Handler
   - PolicyName: DynamoDBReadAccess
     Actions: [GetItem, Query, Scan, BatchGetItem]
   
   # Write access for Data Management Handler
   - PolicyName: DynamoDBWriteAccess
     Actions: [PutItem, UpdateItem, DeleteItem, BatchWriteItem]
   ```

2. **Table-Specific Permissions**
   - Different roles for different Lambda functions
   - Query Handler: Read-only access
   - Data Management Handler: Full access

**Current Status**: The unified role approach is appropriate for this application's architecture and simplifies IAM management.

---

## Compliance with Task Requirements

### ✅ Requirement 1: Verify Read/Write Permissions
**Status**: VERIFIED

The OrchestrationRole includes all required DynamoDB operations:
- ✅ `dynamodb:GetItem` - Read single item
- ✅ `dynamodb:PutItem` - Create/replace item
- ✅ `dynamodb:UpdateItem` - Update item
- ✅ `dynamodb:DeleteItem` - Delete item
- ✅ `dynamodb:Query` - Query with keys/indexes
- ✅ `dynamodb:Scan` - Full table scan
- ✅ `dynamodb:BatchGetItem` - Batch read
- ✅ `dynamodb:BatchWriteItem` - Batch write

### ✅ Requirement 2: Check Coverage of All Tables
**Status**: VERIFIED

The resource ARN pattern covers all 4 application tables:
- ✅ Protection Groups Table
- ✅ Recovery Plans Table
- ✅ Execution History Table (including GSIs)
- ✅ Target Accounts Table

### ✅ Requirement 3: Identify Tables from Database Stack
**Status**: COMPLETED

All tables identified from `cfn/database-stack.yaml`:
- ✅ Table names documented
- ✅ Primary keys documented
- ✅ GSIs documented (Execution History)
- ✅ Schema convention documented (camelCase)

### ✅ Requirement 4: Confirm Proper CloudFormation References
**Status**: VERIFIED

The OrchestrationRole uses proper CloudFormation intrinsic functions:
- ✅ `!Sub` for dynamic ARN construction
- ✅ `${AWS::Partition}` for multi-partition support
- ✅ `${AWS::Region}` for region-specific ARNs
- ✅ `${AWS::AccountId}` for account-specific ARNs
- ✅ `${ProjectName}` parameter for naming consistency

---

## Recommendations

### 1. No Changes Required ✅
The current DynamoDB permissions configuration is **correct and complete**. No modifications are needed to support direct Lambda invocation mode.

### 2. Documentation Enhancement (Optional)
Consider adding inline comments to the DynamoDBAccess policy to document which Lambda functions use which operations:

```yaml
- PolicyName: DynamoDBAccess
  PolicyDocument:
    Version: "2012-10-17"
    Statement:
      - Effect: Allow
        Action:
          # Read operations (Query Handler, Data Management Handler, Execution Handler)
          - dynamodb:GetItem
          - dynamodb:Query
          - dynamodb:Scan
          - dynamodb:BatchGetItem
          # Write operations (Data Management Handler, Execution Handler, DR Orchestration)
          - dynamodb:PutItem
          - dynamodb:UpdateItem
          - dynamodb:DeleteItem
          - dynamodb:BatchWriteItem
        Resource:
          # Covers all 4 tables: protection-groups, recovery-plans, execution-history, target-accounts
          - !Sub "arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ProjectName}-*"
```

### 3. Future Considerations
If the application grows to include tables outside the `${ProjectName}-*` pattern, update the resource ARN list accordingly.

---

## Conclusion

**Task 9.4 Status**: ✅ **COMPLETE**

The OrchestrationRole has comprehensive DynamoDB read/write permissions for all four application tables. The permissions are correctly scoped using CloudFormation intrinsic functions and follow AWS security best practices. No changes are required to support direct Lambda invocation mode.

### Key Findings
1. ✅ All required DynamoDB operations are granted
2. ✅ All four application tables are covered by the resource pattern
3. ✅ Proper CloudFormation references are used
4. ✅ GSI access is automatically included
5. ✅ Security follows least privilege principles
6. ✅ Direct Lambda invocation mode is fully supported

### Next Steps
Proceed to Task 9.5: Verify OrchestrationRole has Step Functions execution permissions.
