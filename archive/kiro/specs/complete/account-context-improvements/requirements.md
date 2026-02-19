# Account Context Improvements and Notification System Activation

## ⚠️ CRITICAL IMPLEMENTATION REQUIREMENTS

**This spec has THREE equally critical requirements that MUST all be fully implemented:**

1. **Account Context Management** - Include `targetAccountId` directly in Protection Groups and Recovery Plans
2. **Notification System Activation** - Make the existing notification infrastructure fully operational
3. **Interactive Pause/Resume** - Enable email-based execution control using AWS Step Functions task tokens

**The notification system and pause/resume functionality are NOT secondary goals or placeholders. They MUST be:**
- ✅ Fully integrated with Step Functions and Lambda handlers
- ✅ Publishing events to SNS topics on all execution state changes
- ✅ Creating and managing SNS subscriptions per Recovery Plan
- ✅ Delivering email notifications end-to-end
- ✅ Filtering messages by Recovery Plan context
- ✅ Handling subscription lifecycle (create, update, delete)
- ✅ Implementing task token callback pattern for pause/resume
- ✅ Providing API Gateway endpoints for resume/cancel actions
- ✅ Validating task tokens and handling security considerations

**Current State**: Notification infrastructure exists (SNS topics, formatter Lambda) but is NOT being used. This spec activates it AND adds interactive pause/resume capability.

## Overview

This spec addresses THREE EQUALLY CRITICAL requirements that must all be fully implemented:

1. **Account Context Management**: Improve how TargetAccountID is handled when creating Protection Groups and Recovery Plans, ensuring account context is automatically applied from the frontend's current account selection and properly included in export/import configurations.

2. **Notification System Activation** (CRITICAL - MUST BE FULLY FUNCTIONAL): Implement and activate the email notification system for Recovery Plans, enabling real-time alerts for execution events, status changes, and issues requiring attention. The existing notification infrastructure (SNS topics, formatter Lambda) must be integrated and made operational.

3. **Interactive Pause/Resume** (CRITICAL - MUST BE FULLY FUNCTIONAL): Implement AWS Step Functions task token callback pattern to enable users to resume or cancel paused executions directly from email notifications, without requiring console access.

## Problem Statement

Currently, the system has two critical gaps:

### Account Context Issues

1. **Protection Groups**: Accept optional `accountId` and `assumeRoleName` in the request body, but the frontend doesn't automatically populate these from the current account context
2. **Recovery Plans**: Don't store `accountId` directly - they derive it from referenced Protection Groups at execution time
3. **Export/Import**: Protection Groups include account context, but Recovery Plans don't have direct account association
4. **Query/Filter**: No efficient way to query "all Recovery Plans for account X" without scanning all plans and resolving Protection Group references
5. **Direct Lambda Invocation**: No clear guidance on required fields when invoking Lambda functions directly without API Gateway or frontend

### Notification System Issues

1. **Infrastructure Exists But Unused**: SNS topics, notification formatter Lambda, and CloudFormation templates are in place but not integrated with actual events
2. **No Event Triggering**: Step Functions and Lambda handlers don't publish to SNS topics
3. **Single Admin Email**: Current design uses one admin email for all notifications instead of per-Recovery-Plan targeting
4. **No Subscription Management**: No mechanism to create/update/delete SNS subscriptions dynamically
5. **Missing Integration**: Execution events (start, complete, fail, pause) don't trigger notifications

### Deployment Mode Support

The system must support two deployment modes:

1. **Full Stack Mode** (API Gateway + Frontend + Lambda):
   - Frontend provides account context automatically
   - API Gateway handles authentication and routing
   - Account context can be optional in requests (defaults from frontend)

2. **Direct Lambda Invocation Mode** (Lambda only, no API Gateway/Frontend):
   - Used for programmatic access, automation, and CLI tools
   - Account context MUST be explicitly provided in event payload
   - All required fields must be present in Lambda event
   - No frontend or API Gateway available to provide defaults

## User Stories

This spec includes 6 user stories with detailed acceptance criteria:

1. **Auto-Apply Account Context on Creation** - Automatically populate account context from frontend
2. **Direct Account Association for Recovery Plans** - Store account context directly on Recovery Plans
3. **Export Configuration with Account Context** - Include complete account context in exports
4. **Account Context Validation** - Validate account consistency across resources
5. **Recovery Plan Notifications** - Email notifications for execution events (CRITICAL)
6. **Interactive Execution Pause/Resume** - Resume/cancel executions from email (CRITICAL)

### User Story 1: Auto-Apply Account Context on Creation

**As a** DR administrator  
**I want** the system to automatically apply the current account context when I create Protection Groups or Recovery Plans  
**So that** I don't have to manually specify the account for every resource I create

**Acceptance Criteria:**
- 1.1 Protection Group schema includes `accountId` field (REQUIRED, string, 12-digit AWS account ID)
- 1.2 Recovery Plan schema includes `accountId` field (REQUIRED, string, 12-digit AWS account ID)
- 1.3 Recovery Plan schema includes `assumeRoleName` field (OPTIONAL, string, IAM role name for cross-account access)
- 1.4 Recovery Plan schema includes `notificationEmail` field (OPTIONAL, string, valid email format)
- 1.5 Recovery Plan schema includes `snsSubscriptionArn` field (OPTIONAL, string, ARN of SNS subscription)
- 1.6 **API Gateway Mode**: When creating Protection Group via API Gateway, `accountId` is optional and defaults to authenticated user's account from Cognito identity
- 1.7 **Direct Lambda Invocation Mode**: When creating Protection Group via direct Lambda invocation, `accountId` is REQUIRED in event payload and validation error is returned if missing
- 1.8 **API Gateway Mode**: When creating Recovery Plan via API Gateway, `accountId` is optional and defaults to authenticated user's account from Cognito identity
- 1.9 **Direct Lambda Invocation Mode**: When creating Recovery Plan via direct Lambda invocation, `accountId` is REQUIRED in event payload and validation error is returned if missing
- 1.10 Backend detects invocation source (API Gateway vs direct Lambda) by checking for `requestContext` in event
- 1.11 Validation error message clearly indicates that `accountId` is required for direct Lambda invocation
- 1.12 Frontend passes the current account context (`accountId`, `assumeRoleName`) in all create requests
- 1.13 Backend validates that provided `accountId` matches an account the user has access to

### User Story 2: Direct Account Association for Recovery Plans

**As a** DR administrator  
**I want** Recovery Plans to have direct account association  
**So that** I can efficiently query and filter plans by account without resolving Protection Group references

**Acceptance Criteria:**
- 2.1 Recovery Plans store `accountId` and `assumeRoleName` fields directly in DynamoDB
- 2.2 Recovery Plans validate that all waves reference Protection Groups from the same account
- 2.3 Query operations can filter Recovery Plans by `accountId` without scanning Protection Groups
- 2.4 Existing Recovery Plans are migrated to include account context from their Protection Groups

### User Story 3: Export Configuration with Account Context

**As a** DR administrator  
**I want** exported configurations to include complete account context  
**So that** I can import configurations into other environments with proper account associations

**Acceptance Criteria:**
- 3.1 Exported Protection Groups include `accountId`, `assumeRoleName`, and `externalId`
- 3.2 Exported Recovery Plans include `accountId` and `assumeRoleName` at the plan level
- 3.3 Export format is backward compatible with existing exports
- 3.4 Import validates account context and provides clear error messages for mismatches

### User Story 4: Account Context Validation

**As a** DR administrator  
**I want** the system to validate account context consistency  
**So that** I don't create invalid configurations that will fail at execution time

**Acceptance Criteria:**
- 4.1 When creating a Recovery Plan, validate that all referenced Protection Groups exist and belong to the same account
- 4.2 When adding waves to a Recovery Plan, validate that new Protection Groups match the plan's account
- 4.3 Provide clear error messages when account mismatches are detected
- 4.4 Allow cross-account Recovery Plans only if explicitly enabled (future enhancement)

## Current Implementation Analysis

### Protection Group Creation
```python
# Current: Optional accountId in request body
item = {
    "groupId": group_id,
    "groupName": name,
    "accountId": body.get("accountId", ""),  # Optional, defaults to empty
    "assumeRoleName": body.get("assumeRoleName", ""),
    # ... other fields
}
```

### Recovery Plan Creation
```python
# Current: No accountId stored directly
item = {
    "planId": plan_id,
    "planName": plan_name,
    "waves": waves,  # References Protection Groups via protectionGroupId
    # Missing: accountId, assumeRoleName
}
```

### Account Context Extraction (Execution Time)
```python
# Current: Derived from Protection Group at execution time
def get_account_context(state: Dict) -> Dict:
    return state.get("accountContext") or state.get("account_context", {})
```

## Proposed Changes

### 1. Frontend Changes
- Pass current account context in all create/update requests
- Include `accountId` and `assumeRoleName` from the selected account
- Validate account selection before allowing resource creation

### 2. Backend Changes

#### Protection Group Creation
- Make `accountId` required when invoked directly (Lambda invocation mode)
- Make `accountId` optional when invoked via API Gateway (defaults from frontend context)
- Detect invocation source to determine validation rules
- Validate account access permissions
- Add `notificationEmail` field (optional, validated)
- Create SNS subscription when notification email provided

#### Recovery Plan Creation
- Add `accountId` and `assumeRoleName` fields to DynamoDB schema
- Make `accountId` required for direct Lambda invocation
- Make `accountId` optional for API Gateway invocation (defaults from frontend)
- Validate that all waves reference Protection Groups from the same account
- Store account context directly on the plan

#### Query Operations
- Add efficient account filtering for Recovery Plans
- Support `accountId` query parameter for both Protection Groups and Recovery Plans
- Optimize queries to avoid scanning Protection Groups

#### Export/Import
- Include account context in all exported configurations
- Include notification email in exported Protection Groups
- Validate account context during import
- Provide migration path for existing data

#### Notification Integration
- Integrate Step Functions with SNS topics for execution events
- Update Lambda handlers to publish notifications on key events
- Implement SNS subscription management (create, update, delete)
- Handle email confirmation workflow
- Format notification messages with Protection Group context

### 3. Data Backfill Strategy (NOT Schema Migration)

**CRITICAL CLARIFICATION**: This is NOT a schema migration. The DynamoDB schema is already camelCase and will remain camelCase.

**What We're Actually Doing:**
1. **Adding New Fields** to existing items (Protection Groups and Recovery Plans)
2. **Backfilling Data** for existing records that don't have the new fields
3. **NO Field Renaming** - all existing field names stay exactly the same
4. **NO Data Type Changes** - all existing data types stay the same

**New Fields Being Added:**
- Protection Groups: `notificationEmail` (optional string), `snsSubscriptionArn` (optional string)
- Recovery Plans: `accountId` (required string), `assumeRoleName` (optional string)

**Backfill Process:**
1. Scan existing Protection Groups - add empty `notificationEmail` and `snsSubscriptionArn` if missing
2. Scan existing Recovery Plans - derive and add `accountId` from their Protection Groups
3. Validate data integrity after backfill
4. Handle edge cases where Protection Groups have different accounts
5. Provide backfill script for production data

**Schema Remains Unchanged:**
- All field names: camelCase (groupId, planId, accountId, etc.)
- All data structures: unchanged
- All indexes: unchanged
- All queries: backward compatible

## IAM Permission Requirements

### Current SNS Permissions in UnifiedOrchestrationRole

The `UnifiedOrchestrationRole` (defined in `cfn/master-template.yaml` lines 467-477) currently has basic SNS permissions:

```yaml
- PolicyName: SNSAccess
  PolicyDocument:
    Version: "2012-10-17"
    Statement:
      - Effect: Allow
        Action:
          - sns:Publish
        Resource:
          - !Sub "arn:${AWS::Partition}:sns:${AWS::Region}:${AWS::AccountId}:${ProjectName}-*"
```

### Required SNS Permission Updates

To support per-Protection-Group email subscriptions and notification management, the following additional SNS permissions are required:

**Subscription Management:**
- `sns:Subscribe` - Create email subscriptions for Protection Groups
- `sns:Unsubscribe` - Remove email subscriptions when Protection Groups are deleted
- `sns:ListSubscriptionsByTopic` - Query existing subscriptions for a topic
- `sns:GetSubscriptionAttributes` - Retrieve subscription details (confirmation status, filter policy)
- `sns:SetSubscriptionAttributes` - Update subscription attributes (filter policies for message filtering)

**Topic Management (Read-Only):**
- `sns:GetTopicAttributes` - Retrieve topic configuration
- `sns:ListTopics` - Discover available notification topics

**Updated SNS Policy:**

```yaml
- PolicyName: SNSAccess
  PolicyDocument:
    Version: "2012-10-17"
    Statement:
      # Publish notifications to topics
      - Effect: Allow
        Action:
          - sns:Publish
        Resource:
          - !Sub "arn:${AWS::Partition}:sns:${AWS::Region}:${AWS::AccountId}:${ProjectName}-*"
      
      # Manage email subscriptions for Protection Groups
      - Effect: Allow
        Action:
          - sns:Subscribe
          - sns:Unsubscribe
          - sns:ListSubscriptionsByTopic
          - sns:GetSubscriptionAttributes
          - sns:SetSubscriptionAttributes
          - sns:GetTopicAttributes
          - sns:ListTopics
        Resource:
          - !Sub "arn:${AWS::Partition}:sns:${AWS::Region}:${AWS::AccountId}:${ProjectName}-*"
```

**Security Considerations:**
- All SNS permissions are scoped to project-specific topics only (`${ProjectName}-*`)
- No wildcard resource access - follows least privilege principle
- Email subscriptions require confirmation by recipient (AWS SNS security feature)
- Filter policies prevent unauthorized access to notifications from other Recovery Plans

## Technical Considerations

### Reusing Existing Lambda Shared Utilities

**CRITICAL**: The lambda/shared directory contains extensive utilities that MUST be reused to avoid code duplication. Do NOT reimplement this functionality in Lambda handlers.

#### account_utils.py - Account Management (REUSE THIS)
```python
# Existing functions to reuse:
validate_account_id(account_id: str) -> bool
    # Validates 12-digit AWS account ID format
    # Use for: Protection Group and Recovery Plan validation

construct_role_arn(account_id: str, role_name: str, partition: str = "aws") -> str
    # Constructs IAM role ARN from account ID and role name
    # Use for: Cross-account role ARN construction

get_account_name(account_id: str) -> str
    # Retrieves account alias/name from AWS Organizations
    # Use for: Display names in UI and notifications
```

#### cross_account.py - Cross-Account Operations (REUSE THIS)
```python
# Existing functions to reuse:
determine_target_account_context(plan: Dict) -> Dict
    # Determines target account for cross-account DR operations
    # Located in cross_account.py (NOT account_utils.py)
    # Use for: Deriving account context from Recovery Plan's Protection Groups
    # Returns: {"accountId": "...", "assumeRoleName": "...", "isCurrentAccount": bool}

assume_cross_account_role(account_id: str, role_name: str, external_id: Optional[str] = None) -> Dict
    # Assumes IAM role in target account and returns temporary credentials
    # Use for: Cross-account DRS operations

create_drs_client(account_id: str, role_name: str, region: str) -> boto3.client
    # Creates DRS client with cross-account credentials
    # Use for: DRS API calls in target account

validate_cross_account_access(account_id: str, role_name: str) -> bool
    # Validates that cross-account role is assumable
    # Use for: Pre-flight validation before creating Protection Groups
```

#### notifications.py - SNS Notification Helpers (EXTEND THIS)
```python
# Existing functions to reuse:
publish_execution_notification(topic_arn: str, message: Dict, attributes: Dict) -> str
    # Publishes formatted notification to SNS topic
    # Use for: Step Functions and Lambda event publishing

format_notification_message(event_type: str, context: Dict) -> Dict
    # Formats raw event data into notification message structure
    # Use for: Standardized message formatting

# NEW functions to add (extend existing pattern):
manage_recovery_plan_subscription(plan_id: str, email: str, action: str) -> Optional[str]
    # Create/update/delete SNS subscription for Recovery Plan
    # Follow existing notification.py patterns

publish_recovery_plan_notification(plan_id: str, event_type: str, details: Dict) -> None
    # Publish notification for Recovery Plan execution events
    # Reuse existing publish_execution_notification() internally
```

#### security_utils.py - Input Validation (REUSE THIS)
```python
# Existing functions to reuse:
validate_email(email: str) -> bool
    # RFC 5322 compliant email validation
    # Use for: notificationEmail validation

sanitize_string(input_str: str, max_length: int = 255) -> str
    # Sanitizes user input to prevent injection attacks
    # Use for: All user-provided strings (names, descriptions)

validate_arn(arn: str, resource_type: Optional[str] = None) -> bool
    # Validates AWS ARN format and optionally resource type
    # Use for: SNS subscription ARN validation

# Exception classes to reuse:
InputValidationError(Exception)
    # Raise for validation failures
    # Use for: Consistent error handling across handlers
```

### Implementation Guidelines for Lambda Handlers

**DO:**
- ✅ Import and use functions from lambda/shared utilities
- ✅ Extend existing utility modules with new functions following same patterns
- ✅ Reuse existing validation, sanitization, and error handling
- ✅ Follow existing naming conventions and code style

**DON'T:**
- ❌ Reimplement account validation in Lambda handlers
- ❌ Create duplicate email validation functions
- ❌ Write new cross-account role assumption logic
- ❌ Duplicate notification publishing code

**Example: Recovery Plan Creation with Shared Utilities**
```python
# lambda/data-management-handler/index.py
from shared.account_utils import validate_account_id, determine_target_account_context
from shared.security_utils import validate_email, sanitize_string, InputValidationError
from shared.notifications import manage_recovery_plan_subscription

def create_recovery_plan(event, body):
    # Reuse account context extraction
    account_context = determine_target_account_context(event, body)
    account_id = account_context["accountId"]
    
    # Reuse account validation
    if not validate_account_id(account_id):
        raise InputValidationError(f"Invalid account ID: {account_id}")
    
    # Reuse email validation
    notification_email = body.get("notificationEmail")
    if notification_email and not validate_email(notification_email):
        raise InputValidationError(f"Invalid email format: {notification_email}")
    
    # Reuse string sanitization
    plan_name = sanitize_string(body["planName"], max_length=255)
    
    # Create Recovery Plan in DynamoDB
    item = {
        "planId": str(uuid.uuid4()),
        "planName": plan_name,
        "accountId": account_id,
        "notificationEmail": notification_email,
        # ... other fields
    }
    dynamodb.put_item(TableName=table_name, Item=item)
    
    # Reuse notification subscription management
    if notification_email:
        subscription_arn = manage_recovery_plan_subscription(
            plan_id=item["planId"],
            email=notification_email,
            action="create"
        )
        # Update item with subscription ARN
        dynamodb.update_item(
            TableName=table_name,
            Key={"planId": item["planId"]},
            UpdateExpression="SET snsSubscriptionArn = :arn",
            ExpressionAttributeValues={":arn": subscription_arn}
        )
    
    return item
```

## Technical Considerations

### DynamoDB Schema Additions (NOT Migration)

**CRITICAL**: This is NOT a schema migration. We are ONLY adding new fields to existing items. All existing field names and data types remain unchanged.

```python
# Protection Group (existing camelCase schema)
{
    "groupId": "uuid",
    "accountId": "123456789012",  # EXISTING: Make required (currently optional)
    "assumeRoleName": "DRSOrchestrationRole",  # EXISTING
    # ... all other existing fields remain unchanged
}

# Recovery Plan (add new fields to existing camelCase schema)
{
    "planId": "uuid",
    "accountId": "123456789012",  # NEW FIELD: Backfill from Protection Groups
    "assumeRoleName": "DRSOrchestrationRole",  # NEW FIELD: Backfill from Protection Groups
    "notificationEmail": "team@example.com",  # NEW: Optional email for notifications
    "snsSubscriptionArn": "arn:aws:sns:...",  # NEW: Track SNS subscription
    "waves": [...],  # EXISTING: unchanged
    # ... all other existing fields remain unchanged
}
```

**What's Changing:**
- Protection Groups: `accountId` becomes required (currently optional)
- Recovery Plans: Adding 4 new fields (`accountId`, `assumeRoleName`, `notificationEmail`, `snsSubscriptionArn`) and backfilling from Protection Groups
- NO field renaming, NO data type changes, NO schema restructuring

### Deployment Mode Support

The system supports two deployment modes with different account context handling:

**1. Full Stack Mode (API Gateway + Frontend)**
- **Deployment**: `DeployApiGateway=true` (default)
- **Components**: API Gateway, Cognito, Frontend (S3/CloudFront), Lambda functions
- **Account Context Source**: Frontend application context (current account selector)
- **API Behavior**: 
  - `accountId` parameter is OPTIONAL in API requests
  - If omitted, backend defaults to authenticated user's account from Cognito identity
  - Frontend automatically includes `accountId` from current account context
- **Use Cases**: 
  - Web UI access for operators
  - Multi-account management with visual interface
  - Interactive Protection Group and Recovery Plan management

**2. Direct Lambda Invocation Mode (Headless)**
- **Deployment**: `DeployApiGateway=false`
- **Components**: Lambda functions only (no API Gateway, no Cognito, no Frontend)
- **Account Context Source**: Event payload (caller responsibility)
- **Lambda Behavior**:
  - `accountId` parameter is REQUIRED in event payload
  - No default account context available (no Cognito identity)
  - Backend validates presence of `accountId` before processing
  - Returns validation error if `accountId` is missing
- **Invocation Methods**:
  - AWS SDK: `lambda.invoke()` with explicit event payload
  - AWS CLI: `aws lambda invoke --function-name ... --payload '{"accountId": "123456789012", ...}'`
  - Step Functions: Direct Lambda task invocation
  - EventBridge: Event-driven Lambda triggers
- **Use Cases**:
  - Automated DR orchestration pipelines
  - CI/CD integration
  - Infrastructure-as-Code deployments
  - Serverless event-driven architectures
  - Cost optimization (no API Gateway/CloudFront charges)

**Invocation Source Detection Logic:**

The backend must detect the invocation source to apply appropriate validation rules:

```python
def detect_invocation_source(event: Dict[str, Any]) -> str:
    """
    Detect whether Lambda was invoked via API Gateway or directly.
    
    Returns:
        "api_gateway" - Invoked via API Gateway (has requestContext)
        "direct" - Direct Lambda invocation (no requestContext)
    """
    if "requestContext" in event:
        return "api_gateway"
    return "direct"

def validate_account_context(event: Dict[str, Any], body: Dict[str, Any]) -> None:
    """
    Validate account context based on invocation source.
    
    API Gateway Mode:
        - accountId is optional
        - Defaults to Cognito identity if missing
    
    Direct Invocation Mode:
        - accountId is REQUIRED
        - Raises ValidationError if missing
    """
    invocation_source = detect_invocation_source(event)
    
    if invocation_source == "direct":
        # Direct invocation - accountId REQUIRED
        if "accountId" not in body or not body["accountId"]:
            raise ValidationError(
                "accountId is required for direct Lambda invocation. "
                "When invoking Lambda directly (without API Gateway), "
                "you must explicitly provide accountId in the event payload."
            )
    elif invocation_source == "api_gateway":
        # API Gateway - accountId optional, default from Cognito
        if "accountId" not in body or not body["accountId"]:
            # Extract from Cognito identity
            cognito_identity = event["requestContext"]["identity"]
            body["accountId"] = extract_account_from_cognito(cognito_identity)
```

**Event Payload Structure for Direct Invocation:**

```json
{
  "operation": "createProtectionGroup",
  "accountId": "123456789012",
  "body": {
    "name": "Production Web Servers",
    "description": "Critical web tier servers",
    "sourceServerIds": ["s-1234567890abcdef0"]
  }
}
```

**Error Response for Missing accountId (Direct Invocation):**

```json
{
  "statusCode": 400,
  "body": {
    "error": "ValidationError",
    "message": "accountId is required for direct Lambda invocation. When invoking Lambda directly (without API Gateway), you must explicitly provide accountId in the event payload.",
    "invocationMode": "direct",
    "requiredFields": ["accountId"]
  }
}
```

### API Changes
```python
# POST /protection-groups
{
    "groupName": "Web Servers",
    "accountId": "123456789012",  # Auto-populated from frontend context
    "assumeRoleName": "DRSOrchestrationRole",
    # ... other fields
}

# POST /recovery-plans
{
    "name": "DR Plan 1",
    "accountId": "123456789012",  # NEW: Direct account association
    "assumeRoleName": "DRSOrchestrationRole",  # NEW
    "notificationEmail": "team@example.com",  # NEW: Optional notification email
    "waves": [...],
    # ... other fields
}

# PUT /recovery-plans/{planId}
{
    "notificationEmail": "newteam@example.com",  # Update notification email
    # ... other fields
}
```

### Validation Logic
```python
def validate_recovery_plan_account_consistency(plan_data: Dict) -> Optional[str]:
    """
    Validate that all Protection Groups in waves belong to the same account.
    
    Returns:
        Error message if validation fails, None if valid
    """
    plan_account_id = plan_data.get("accountId")
    if not plan_account_id:
        return "Recovery Plan must have accountId"
    
    for wave in plan_data.get("waves", []):
        pg_id = wave.get("protectionGroupId")
        if pg_id:
            pg = get_protection_group(pg_id)
            if pg.get("accountId") != plan_account_id:
                return f"Protection Group {pg_id} belongs to different account"
    
    return None


def validate_notification_email(email: str) -> bool:
    """
    Validate email format for notifications.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def manage_sns_subscription(
    plan_id: str, 
    email: str, 
    action: str = "create"
) -> Optional[str]:
    """
    Manage SNS subscription for Recovery Plan notifications.
    
    Args:
        plan_id: Recovery Plan ID
        email: Notification email address
        action: "create", "update", or "delete"
        
    Returns:
        SNS subscription ARN if created/updated, None if deleted
    """
    topic_arn = os.environ.get("EXECUTION_NOTIFICATIONS_TOPIC_ARN")
    
    if action == "create":
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email,
            Attributes={
                "FilterPolicy": json.dumps({
                    "recoveryPlanId": [plan_id]
                })
            }
        )
        return response["SubscriptionArn"]
    
    elif action == "delete":
        # Delete existing subscription
        # Implementation details...
        return None
```

## Success Metrics

### Account Context Metrics
1. **Consistency**: 100% of Protection Groups and Recovery Plans have valid account context
2. **Usability**: Users don't need to manually specify account for resources created in current account context
3. **Query Performance**: Recovery Plan queries by account complete in <100ms without scanning Protection Groups
4. **Export/Import**: All exported configurations include complete account context and can be imported successfully

### Notification System Metrics (CRITICAL)
5. **Email Delivery**: 95%+ of notifications delivered within 30 seconds of event occurrence
6. **Subscription Success**: 100% of Recovery Plans with notification emails have active SNS subscriptions
7. **Event Coverage**: All execution events (start, complete, fail, pause) trigger notifications
8. **Message Accuracy**: 100% of notifications contain correct Recovery Plan context and execution details
9. **Zero Missed Events**: No execution events are lost without notification delivery

## Dependencies

### Account Context Dependencies
- Frontend account context management
- DynamoDB schema additions (new fields only, NO renaming)
- Data backfill for existing records (NOT schema migration)
- Backward compatibility with existing API clients
- Data backfill script for existing Recovery Plans

### Notification System Dependencies (CRITICAL)
- SNS topic ARNs from notification stack
- IAM permissions for Lambda/Step Functions to publish to SNS
- Email validation library (Python `email-validator`)
- Step Functions state machine updates to publish events
- Lambda handler updates to trigger notifications
- Notification formatter Lambda deployment and configuration
- SNS subscription confirmation workflow
- Message filtering policy implementation

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes to API | High | Maintain backward compatibility, make accountId optional with default |
| Data backfill failures | High | Test backfill thoroughly, provide rollback mechanism |
| Performance impact on queries | Medium | Add DynamoDB indexes for accountId filtering |
| Existing integrations break | Medium | Version API, provide migration guide |

## User Story 5: Recovery Plan Notifications (CRITICAL)

**As a** DR administrator  
**I want** to receive email notifications for Recovery Plan execution events  
**So that** I'm immediately informed of status changes, issues, and actions requiring my attention

**Priority**: CRITICAL - Must be fully implemented and functional in this spec

**Acceptance Criteria:**
- 5.1 Recovery Plans have a `notificationEmail` field that accepts a valid email address
- 5.2 When a Recovery Plan is created with a notification email, an SNS subscription is created automatically
- 5.3 Notifications are sent for: execution start, completion, failure, pause events
- 5.4 Notification emails include: Recovery Plan name, event type, timestamp, execution details, console links
- 5.5 Users can update or remove notification email from existing Recovery Plans
- 5.6 Email validation ensures proper format before accepting (RFC 5322 compliant)
- 5.7 SNS subscription confirmation is handled gracefully (pending confirmation state)
- 5.8 Step Functions publishes events to SNS topics on state transitions
- 5.9 Lambda handlers publish events to SNS topics on key operations
- 5.10 Notification formatter Lambda transforms events into human-readable messages
- 5.11 Message filtering ensures notifications only go to the relevant Recovery Plan subscriber
- 5.12 Subscription cleanup when Recovery Plan is deleted or email is removed

### Current Notification Infrastructure

The system already has notification infrastructure in place but it's not actively being used:

**Existing Components:**
- Three SNS Topics (defined in `cfn/notification-stack.yaml`):
  - `ExecutionNotificationsTopic` - DR execution lifecycle events
  - `DRSOperationalAlertsTopic` - Real-time DRS service alerts  
  - `ExecutionPauseTopic` - Human approval gates
- Notification Formatter Lambda (`lambda/notification-formatter/index.py`)
- Email subscriptions using single `AdminEmail` parameter

**What's Missing:**
- Integration between Step Functions/Lambda and SNS topics
- Triggering notifications on actual events
- Per-Recovery-Plan email subscriptions
- Dynamic SNS subscription management

**Implementation Scope:**
1. Add `notificationEmail` field to Recovery Plan schema
2. Implement email validation on create/update
3. Create SNS subscriptions when Recovery Plan has notification email
4. Integrate Step Functions to publish events to SNS topics
5. Update Lambda handlers to trigger notifications on key events
6. Handle SNS subscription confirmation workflow

## Notification System Implementation Checklist (CRITICAL)

### Phase 1: Schema and Validation
- [ ] Add `notificationEmail` field to Recovery Plan DynamoDB schema (optional string)
- [ ] Add `snsSubscriptionArn` field to track subscription status
- [ ] Implement RFC 5322 email validation in data-management-handler
- [ ] Add email validation tests (unit and property-based)

### Phase 2: SNS Subscription Management
- [ ] Create `manage_recovery_plan_subscription()` function in shared utilities
- [ ] Implement subscription creation with message filtering by Recovery Plan ID
- [ ] Implement subscription update when email changes
- [ ] Implement subscription deletion when email removed or Recovery Plan deleted
- [ ] Handle SNS subscription confirmation workflow (pending state)
- [ ] Add IAM permissions for Lambda to manage SNS subscriptions

### Phase 3: Event Publishing - Step Functions
- [ ] Update Step Functions state machine to publish to ExecutionNotificationsTopic
- [ ] Publish event on execution start (include Recovery Plan ID, plan name, timestamp)
- [ ] Publish event on execution complete (include duration, success count)
- [ ] Publish event on execution failure (include error details, failed resources)
- [ ] Publish event on execution pause (include pause reason, approval required)
- [ ] Add IAM permissions for Step Functions to publish to SNS

### Phase 4: Event Publishing - Lambda Handlers
- [ ] Update execution-handler to publish notifications on key operations
- [ ] Update dr-orchestration-stepfunction to publish state transition events
- [ ] Ensure all published messages include Recovery Plan ID for filtering
- [ ] Add error handling for SNS publish failures (log but don't fail execution)

### Phase 5: Message Formatting
- [ ] Verify notification-formatter Lambda is deployed and configured
- [ ] Test message transformation from raw events to human-readable emails
- [ ] Ensure messages include: Recovery Plan name, event type, timestamp, execution details, console links
- [ ] Test message filtering by Recovery Plan ID

### Phase 6: Integration Testing
- [ ] Test end-to-end: Create Recovery Plan with email → Receive confirmation → Execute plan → Receive notifications
- [ ] Test email update: Change email → Old subscription deleted → New subscription created
- [ ] Test email removal: Remove email → Subscription deleted → No more notifications
- [ ] Test Recovery Plan deletion: Delete plan → Subscription cleaned up
- [ ] Test notification delivery timing (95%+ within 30 seconds)
- [ ] Test message filtering (only relevant Recovery Plan subscriber receives notifications)

### Phase 7: Error Handling and Edge Cases
- [ ] Handle invalid email format gracefully
- [ ] Handle SNS subscription failures (log and retry)
- [ ] Handle pending subscription confirmations
- [ ] Handle duplicate subscriptions
- [ ] Handle SNS topic not found errors
- [ ] Handle rate limiting from SNS

## User Story 6: Interactive Execution Pause/Resume (CRITICAL)

**As a** DR administrator  
**I want** to resume or cancel paused executions directly from email notifications  
**So that** I can respond quickly to execution pauses without accessing the console

**Priority**: CRITICAL - Must be fully implemented and functional in this spec

**Acceptance Criteria:**
- 6.1 When execution reaches a pause state, Step Functions uses `waitForTaskToken` integration pattern
- 6.2 Pause notification email includes task token embedded in action URLs
- 6.3 Email contains two action buttons: "Resume Execution" and "Cancel Execution"
- 6.4 API Gateway provides endpoints: `/execution?action=resume&taskToken={token}` and `/execution?action=cancel&taskToken={token}`
- 6.5 Lambda callback handler validates task token format and expiration
- 6.6 Resume action invokes `stepfunctions.sendTaskSuccess()` with task token
- 6.7 Cancel action invokes `stepfunctions.sendTaskFailure()` with task token and reason
- 6.8 Step Functions resumes execution after receiving callback
- 6.9 Task tokens expire after 1 year (AWS Step Functions maximum)
- 6.10 Invalid or expired task tokens return clear error messages
- 6.11 Task token replay protection prevents duplicate resume/cancel actions
- 6.12 Callback handler logs all resume/cancel actions for audit trail
- 6.13 Email action URLs are mobile-friendly and work from any device
- 6.14 Success/error pages displayed after clicking action links
- 6.15 IAM permissions include `states:SendTaskSuccess` and `states:SendTaskFailure` for callback Lambda

**Security Considerations:**
- Task tokens are cryptographically signed by AWS Step Functions (cannot be forged)
- Task tokens are single-use (replay protection via Step Functions)
- Task tokens expire automatically (AWS enforces 1-year maximum)
- No additional authentication required (task token is the credential)
- Callback Lambda validates token format before invoking Step Functions API
- All actions logged to CloudWatch for audit trail

**Implementation Notes:**
- Use AWS Step Functions official task token pattern
- Follow AWS best practices from "Deploying a workflow that waits for human approval" tutorial
- Email template must clearly indicate action consequences (resume vs cancel)
- Success page should include link to console for viewing execution status
- Error page should provide troubleshooting guidance (expired token, already processed, etc.)

## Out of Scope

- Cross-account Recovery Plans (all waves in different accounts)
- Account context for other resource types (tags, configurations)
- Multi-region account context handling
- Account permission validation beyond basic format checks
- Advanced notification features (SMS, Slack, custom webhooks)
- Notification templates and customization
- Notification history and audit logs
- Multi-step approval workflows with multiple approvers
- Approval delegation and escalation
- Interactive approvals for non-pause events (start, complete, failure)

## Reference Architecture Patterns

### AWS RDS Recommendations Automation Pattern
Based on AWS's official blog post "Automating Amazon RDS and Amazon Aurora recommendations via notification with AWS Lambda, Amazon EventBridge, and Amazon SES", we can apply similar patterns:

**Key Architecture Components:**
1. **EventBridge/Step Functions** → Triggers notification events
2. **Lambda Function** → Retrieves data, formats messages, publishes to SNS
3. **SNS Topics** → Routes notifications to subscribers
4. **Email Subscriptions** → Delivers formatted notifications to users

**Implementation Patterns to Apply:**
- **Event-Driven Architecture**: Step Functions publishes events → Lambda processes → SNS delivers
- **Message Filtering**: Use SNS FilterPolicy to route notifications by Recovery Plan ID
- **HTML Email Formatting**: Format execution details into readable HTML emails
- **Batch Processing**: Handle multiple notifications efficiently
- **Error Handling**: Log failures but don't block execution flow
- **IAM Permissions**: Lambda needs `sns:Publish`, `sns:Subscribe`, `sns:Unsubscribe`

**Email Content Structure:**
```html
<html>
  <head><style>/* Formatting styles */</style></head>
  <body>
    <h1>Recovery Plan: {planName}</h1>
    <h2>Event: {eventType}</h2>
    <table>
      <tr><th>Attribute</th><th>Value</th></tr>
      <tr><td>Status</td><td>{status}</td></tr>
      <tr><td>Timestamp</td><td>{timestamp}</td></tr>
      <tr><td>Execution ID</td><td>{executionId}</td></tr>
    </table>
    <h3>Details:</h3>
    <p>{details}</p>
    <h3>Actions:</h3>
    <ul><li>{action1}</li><li>{action2}</li></ul>
    <p><a href="{consoleLink}">View in Console</a></p>
  </body>
</html>
```

**SNS Message Attributes for Filtering:**
```python
sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps(message),
    MessageAttributes={
        'recoveryPlanId': {
            'DataType': 'String',
            'StringValue': plan_id
        },
        'eventType': {
            'DataType': 'String',
            'StringValue': event_type  # 'start', 'complete', 'fail', 'pause'
        }
    }
)
```

**SNS Subscription with Filter Policy:**
```python
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint=email,
    Attributes={
        'FilterPolicy': json.dumps({
            'recoveryPlanId': [plan_id]
        })
    }
)
```

## Cross-Account DRS Patterns from AWS

Based on AWS's official blog post "Cross-account disaster recovery setup using AWS Elastic Disaster Recovery in secured networks", we can apply these proven patterns:

### Account Context Best Practices

1. **Explicit Account Association**: Always store account ID directly on resources rather than deriving it at runtime
   - Protection Groups should have `accountId` as a required field
   - Recovery Plans should store `accountId` directly (not just via Protection Group references)
   - This enables efficient querying and filtering without cross-referencing

2. **Cross-Account IAM Role Pattern**: Use consistent role naming across accounts
   - Store `assumeRoleName` with each resource
   - Validate role exists and has proper trust relationships
   - Support role chaining for multi-account scenarios

3. **Account Validation**: Validate account context at creation time, not execution time
   - Check that user has access to specified account
   - Verify IAM role exists and is assumable
   - Fail fast with clear error messages

### Notification Patterns from AWS DRS Operations

1. **Event-Driven Notifications**: Publish events at key state transitions
   - Replication initiation started
   - Replication status changed (healthy, stalled, error)
   - Recovery drill initiated
   - Recovery job started/completed/failed
   - Reverse replication started
   - Failback completed

2. **Multi-Channel Notification Support**: While email is primary, architecture should support:
   - SNS for email delivery (current implementation)
   - Future: CloudWatch Events for automation triggers
   - Future: EventBridge for cross-account notifications

3. **Notification Context**: Include comprehensive context in notifications
   - Account ID and region
   - Recovery Plan name and ID
   - Protection Group names (from waves)
   - Execution ID for tracking
   - Timestamp and duration
   - Status and error details
   - Console deep links for quick access

### DRS Plan Automation Insights

From the aws-samples/drs-tools repository, the DRS Plan Automation solution demonstrates:

1. **Wave-Based Orchestration**: Sequential recovery with ordered waves
   - Each wave has PreWave and PostWave automation actions
   - SSM Automation runbooks for flexible automation
   - Support for managed services (RDS, Lambda, Route 53, S3)
   - Our implementation already follows this pattern

2. **Step Functions Orchestration**: State machine coordinates execution
   - Lambda functions implement control logic
   - DynamoDB for data capture/retrieval
   - Our implementation already uses this architecture

3. **Authentication and Access Control**: 
   - Cognito for user authentication
   - WAF for IP-based access control
   - API Gateway + Lambda for backend
   - Our implementation already has this infrastructure

4. **Multi-Account Support**: Configuration-based approach for cross-account operations
   - Launch template synchronization across accounts
   - Replication settings management
   - Default settings with per-server overrides
   - **Key Insight**: Account context must be explicit, not implicit

## Implementation Priorities

Based on AWS patterns and our current architecture:

### Phase 1: Account Context (Foundation)
1. Make `accountId` required on Protection Groups
2. Add `accountId` to Recovery Plans
3. Implement account validation at creation time
4. Add efficient querying by account

### Phase 2: Notification System (Critical)
1. Add `notificationEmail` to Recovery Plans
2. Implement SNS subscription management
3. Integrate Step Functions with SNS topics
4. Publish events on all state transitions
5. Format notifications with full context

### Phase 3: Data Backfill (NOT Schema Migration)
1. Backfill account context for existing Recovery Plans
2. Add new fields to existing Protection Groups if missing
3. Validate data integrity after backfill
4. **CRITICAL**: Schema remains camelCase - NO field renaming

## Serverless Notification Pattern (API Gateway + SQS + Lambda + SNS)

Based on the common AWS serverless pattern `apigw-http-api-fifo-sqs-lambda-sns-sam`, we can apply these architectural principles:

### Pattern Architecture
```
API Gateway → FIFO SQS → Lambda (Processor) → SNS → Email Subscribers
```

### Key Benefits for Our Use Case

1. **Decoupling**: SQS decouples event producers (Step Functions, Lambda handlers) from notification delivery
2. **Ordering**: FIFO SQS ensures notifications are delivered in order for each Recovery Plan
3. **Reliability**: SQS provides retry logic and dead-letter queue for failed notifications
4. **Scalability**: Lambda scales automatically to process notification queue
5. **Fan-out**: SNS handles fan-out to multiple subscribers per Recovery Plan

### Adaptation for DRS Orchestration

**Current Direct Approach** (simpler, recommended for MVP):
```
Step Functions/Lambda → SNS (with message filtering) → Email Subscribers
```

**Future Enhanced Approach** (if needed for scale/reliability):
```
Step Functions/Lambda → FIFO SQS → Notification Processor Lambda → SNS → Email Subscribers
```

### When to Use SQS Buffer

Consider adding SQS buffer if:
- Notification volume exceeds 100/second
- Need guaranteed ordering of notifications per Recovery Plan
- Need to batch multiple events before sending notifications
- Need to implement notification throttling or rate limiting
- Need advanced retry logic with exponential backoff

### Implementation Decision

**For this spec, use direct SNS publishing** because:
- Simpler architecture with fewer moving parts
- Lower latency (no SQS polling delay)
- Sufficient for expected notification volume (<10/second)
- SNS message filtering provides adequate targeting
- Can add SQS buffer later if needed without API changes

**Reserve SQS pattern for future enhancement** if:
- Notification volume grows significantly
- Need guaranteed ordering guarantees
- Need batch processing of notifications
- Need advanced retry/DLQ handling

### Pattern Insights Applied

1. **Message Deduplication**: Use Recovery Plan ID + Execution ID + Event Type as deduplication key
2. **Message Grouping**: Use Recovery Plan ID as message group ID for FIFO ordering
3. **Error Handling**: Implement dead-letter queue for failed notifications
4. **Monitoring**: CloudWatch metrics for queue depth, processing time, delivery success rate

## Human-in-the-Loop Pattern Analysis (AWS Step Functions)

Based on AWS Step Functions official tutorial "Deploying a workflow that waits for human approval", we analyzed the task token callback pattern for interactive approval workflows.

### Task Token Pattern Architecture

**Official AWS Pattern:**
```
Step Functions (waitForTaskToken) → Lambda sends email with task token → 
User clicks approve/reject link → API Gateway → Lambda callback → 
Step Functions receives SendTaskSuccess/SendTaskFailure → Execution continues
```

**Key Components:**
1. **Task Token**: Step Functions generates unique token using `arn:aws:states:::lambda:invoke.waitForTaskToken`
2. **Email with Action URLs**: Lambda formats email with approve/reject links containing encoded task token
3. **API Gateway Endpoints**: `/execution?action=approve&taskToken={token}` and `/execution?action=reject&taskToken={token}`
4. **Callback Lambda**: Receives user action, calls `stepfunctions.sendTaskSuccess()` or `sendTaskFailure()` with task token
5. **State Machine Continuation**: Step Functions resumes execution based on callback result

**CloudFormation Template Components:**
- API Gateway REST API with GET method
- Lambda function to handle approval/rejection callbacks
- Step Functions state machine with `waitForTaskToken` resource
- SNS topic for email delivery
- IAM roles with `states:SendTaskSuccess` and `states:SendTaskFailure` permissions

### Application to DRS Orchestration

**Current Scope (This Spec) - Informational + Interactive Pause/Resume:**
- ✅ Execution start notifications (informational)
- ✅ Execution complete notifications (informational)
- ✅ Execution failure notifications (informational)
- ✅ **Execution pause notifications with resume action (INTERACTIVE - CRITICAL)**
- ✅ Task token callback pattern for pause/resume workflow
- ✅ API Gateway endpoints for resume/cancel actions
- ✅ Lambda callback handler for `SendTaskSuccess`/`SendTaskFailure`
- ✅ Email with action links (Resume Execution, Cancel Execution)
- ✅ Console links for viewing execution details

**Future Enhancement (Out of Scope):**
- ⏭️ Interactive approval for high-risk operations (production failovers)
- ⏭️ Multi-step approval workflows with multiple approvers
- ⏭️ Approval delegation and escalation
- ⏭️ Approval audit trail and history

### Why Pause/Resume is In Scope

**Critical Business Requirement:**
1. **Execution Control**: Operators must be able to resume paused executions without accessing console
2. **Mobile Access**: Email-based resume enables mobile operators to respond quickly
3. **Reduced Latency**: Direct email action is faster than console login
4. **User Experience**: Seamless workflow from notification to action
5. **AWS Best Practice**: Follows official AWS Step Functions human approval pattern

**Implementation Approach:**
- Use AWS Step Functions `waitForTaskToken` integration pattern
- Lambda sends email with task token embedded in action URLs
- API Gateway endpoints handle resume/cancel actions
- Lambda callback invokes `stepfunctions.sendTaskSuccess()` or `sendTaskFailure()`
- Step Functions resumes execution based on callback

### Implementation Decision

**For this spec, implement two notification types:**

1. **Informational Notifications** (no task tokens):
   - Execution start, complete, failure events
   - Use direct SNS publishing
   - Include console deep links only

2. **Interactive Pause Notifications** (with task tokens):
   - Execution pause events requiring human decision
   - Use task token callback pattern
   - Include action links: Resume Execution, Cancel Execution
   - API Gateway + Lambda callback handler
   - Step Functions waits for callback before continuing

### Email Notification Best Practices

From AWS Step Functions human approval tutorial and AWS RDS automation patterns, apply these email formatting principles:

1. **Clear Subject Lines**: `Required approval from AWS Step Functions` → Adapt to `[DRS] Recovery Plan: {name} - {eventType}`
2. **Actionable Content**: Include console deep links for immediate access (not approval links in current scope)
3. **Context-Rich**: Recovery Plan name, execution ID, timestamp, status, duration
4. **Visual Hierarchy**: Use HTML formatting for readability (AWS uses plain text, we'll use HTML)
5. **Mobile-Friendly**: Responsive design for mobile email clients
6. **Unsubscribe Instructions**: Include footer with instructions to update Recovery Plan settings

**Example Email Structure:**
```html
<html>
  <head>
    <style>
      body { font-family: Arial, sans-serif; }
      .header { background-color: #232f3e; color: white; padding: 20px; }
      .content { padding: 20px; }
      .status-success { color: #037f0c; }
      .status-error { color: #d13212; }
      .action-button { 
        background-color: #ff9900; 
        color: white; 
        padding: 10px 20px; 
        text-decoration: none; 
        border-radius: 4px; 
      }
    </style>
  </head>
  <body>
    <div class="header">
      <h1>DRS Orchestration Notification</h1>
    </div>
    <div class="content">
      <h2>Recovery Plan: {planName}</h2>
      <p><strong>Event:</strong> <span class="status-{statusClass}">{eventType}</span></p>
      <p><strong>Execution ID:</strong> {executionId}</p>
      <p><strong>Timestamp:</strong> {timestamp}</p>
      <p><strong>Duration:</strong> {duration}</p>
      
      <h3>Details:</h3>
      <p>{details}</p>
      
      <h3>Actions:</h3>
      <a href="{consoleLink}" class="action-button">View in Console</a>
      
      <hr>
      <p style="color: #666; font-size: 12px;">
        This is an automated notification from AWS DRS Orchestration Platform.
        To stop receiving these notifications, update your Recovery Plan settings.
      </p>
    </div>
  </body>
</html>
```

### Implementation Notes

**For This Spec:**
- Focus on informational notifications with console links
- Use SNS for email delivery (no task tokens needed)
- Format emails with clear context and actionable links
- Include unsubscribe instructions in footer

**Future Enhancements:**
- Add task token support for approval workflows
- Implement API Gateway endpoints for interactive actions
- Add approval/rejection callback handling
- Support pause/resume via email links

## References

- Current implementation: `lambda/data-management-handler/index.py`
- Account utilities: `lambda/shared/account_utils.py`
- Execution handler: `lambda/execution-handler/index.py`
- Query handler: `lambda/query-handler/index.py`
- AWS DRS Tools Repository: https://github.com/aws-samples/drs-tools
- AWS DRS Cross-Account Blog: https://aws.amazon.com/blogs/storage/cross-account-disaster-recovery-setup-using-aws-elastic-disaster-recovery-in-secured-networks-part-2-failover-and-failback-implementation/
- AWS RDS Automation Pattern: https://aws.amazon.com/blogs/database/automating-amazon-rds-and-amazon-aurora-recommendations-via-notification-with-aws-lambda-amazon-eventbridge-and-amazon-ses/
- AWS Serverless Patterns: API Gateway + FIFO SQS + Lambda + SNS pattern
