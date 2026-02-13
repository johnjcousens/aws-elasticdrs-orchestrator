# Account Context Improvements and Notification System Activation - Design Document

## Document Status
- **Status**: Draft
- **Version**: 1.0
- **Last Updated**: 2026-02-11
- **Related Requirements**: [requirements.md](./requirements.md)

## Executive Summary

This design document specifies the implementation approach for three equally critical features:

1. **Account Context Management**: Direct storage of `accountId` in Protection Groups and Recovery Plans
2. **Notification System Activation**: Full integration of existing SNS infrastructure
3. **Interactive Pause/Resume**: AWS Step Functions task token callback pattern

The design maintains backward compatibility and supports both API Gateway and direct Lambda invocation modes.

## Architecture Overview

### High-Level System Architecture

The system consists of five main layers:

1. **Frontend Layer**: React application with CloudScape components
2. **API Layer**: API Gateway with Cognito authentication
3. **Backend Services**: Lambda functions for business logic
4. **Orchestration Layer**: Step Functions state machines
5. **Notification Infrastructure**: SNS topics with email subscriptions


### Component Interaction Patterns

**Pattern 1: Recovery Plan Creation with Notification**
1. Frontend retrieves current account context
2. User fills form including optional notification email
3. Frontend sends request with auto-populated accountId
4. Backend validates account access and email format
5. Backend stores Recovery Plan in DynamoDB
6. Backend creates SNS subscription if email provided
7. SNS sends confirmation email to user
8. Backend updates Recovery Plan with subscription ARN

**Pattern 2: Execution with Interactive Pause/Resume**
1. Step Functions reaches pause state using waitForTaskToken
2. Step Functions publishes pause event to SNS with task token
3. SNS delivers email with Resume/Cancel action links
4. User clicks action link (opens API Gateway endpoint)
5. API Gateway invokes callback Lambda with task token
6. Callback Lambda validates token and calls SendTaskSuccess/SendTaskFailure
7. Step Functions resumes or cancels execution based on callback
8. SNS sends confirmation notification

**Pattern 3: Direct Lambda Invocation (No API Gateway)**
1. External system invokes Lambda directly with event payload
2. Lambda detects no requestContext (direct invocation mode)
3. Lambda requires accountId in event payload (validation error if missing)
4. Lambda processes request with explicit account context
5. Lambda publishes notifications to SNS if configured

## Component Design

### 1. Frontend Changes

#### 1.1 Account Context Provider Enhancement

**File**: `frontend/src/contexts/AccountContext.tsx`

**Purpose**: Provide account context to all components for automatic population

**New Interface**:
```typescript
interface AccountContext {
  accountId: string;
  assumeRoleName?: string;
  externalId?: string;
}

interface AccountContextType {
  currentAccount: Account | null;
  accounts: Account[];
  setCurrentAccount: (account: Account) => void;
  getAccountContext: () => AccountContext;  // NEW
}
```

**Implementation**:
```typescript
const getAccountContext = useCallback((): AccountContext => {
  if (!currentAccount) {
    throw new Error("No account selected");
  }
  return {
    accountId: currentAccount.accountId,
    assumeRoleName: currentAccount.assumeRoleName,
    externalId: currentAccount.externalId,
  };
}, [currentAccount]);
```

#### 1.2 Protection Group Form Enhancement

**File**: `frontend/src/components/ProtectionGroups/CreateProtectionGroupForm.tsx`

**New Fields**:
- `accountId` (auto-populated, read-only display)

**Validation Rules**:
- Account ID: 12-digit numeric string

**Form Layout**:
```typescript
<FormField label="Target Account" description="Auto-populated from current account">
  <Input
    value={accountContext.accountId}
    disabled
    readOnly
  />
</FormField>
```

#### 1.3 Recovery Plan Form Enhancement

**File**: `frontend/src/components/RecoveryPlans/CreateRecoveryPlanForm.tsx`

**Changes**:
- Display account ID from current context (read-only)
- Add optional `notificationEmail` field (validated)
- Validate all selected Protection Groups belong to same account
- Show warning if Protection Groups from different accounts

**Form Layout**:
```typescript
<FormField label="Notification Email" description="Receive email alerts for executions of this Recovery Plan">
  <Input
    value={notificationEmail}
    onChange={({ detail }) => setNotificationEmail(detail.value)}
    placeholder="team@example.com"
    type="email"
  />
</FormField>
```

**Validation Logic**:
```typescript
const validateProtectionGroupAccounts = (selectedGroups: ProtectionGroup[]): boolean => {
  const accountContext = useAccountContext().getAccountContext();
  const currentAccountId = accountContext.accountId;
  
  const mismatchedGroups = selectedGroups.filter(
    group => group.accountId !== currentAccountId
  );
  
  if (mismatchedGroups.length > 0) {
    setError(`Protection Groups must belong to account ${currentAccountId}`);
    return false;
  }
  
  return true;
};
```

### 2. Backend Changes

#### 2.1 Invocation Source Detection

**File**: `lambda/shared/account_utils.py` (EXTEND EXISTING)

**Purpose**: Add invocation source detection to the existing account utilities module

**NOTE**: The existing handlers (`data-management-handler`, `query-handler`) already split routing between `handle_api_gateway_request()` and `handle_direct_invocation()` based on the presence of `requestContext`. These new utility functions centralize that detection logic into a reusable function and add metadata extraction for logging/audit. The existing handler routing functions should be updated to use this utility internally.

**New Functions Added to `account_utils.py`**:
```python
from typing import Dict, Any, Literal

InvocationSource = Literal["api_gateway", "direct"]

def detect_invocation_source(event: Dict[str, Any]) -> InvocationSource:
    """
    Detect Lambda invocation source.
    
    Args:
        event: Lambda event object
        
    Returns:
        "api_gateway" if invoked via API Gateway (has requestContext)
        "direct" if invoked directly (no requestContext)
    """
    if "requestContext" in event:
        return "api_gateway"
    return "direct"

def get_invocation_metadata(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract invocation metadata for logging and audit.
    
    Returns:
        Dictionary with source, timestamp, request_id, etc.
    """
    source = detect_invocation_source(event)
    
    metadata = {
        "invocation_source": source,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if source == "api_gateway":
        metadata.update({
            "request_id": event["requestContext"]["requestId"],
            "api_id": event["requestContext"]["apiId"],
            "cognito_identity": event["requestContext"]["identity"].get("cognitoIdentityId"),
        })
    else:
        metadata.update({
            "request_id": event.get("requestId", "unknown"),
        })
    
    return metadata
```

#### 2.2 Account Context Validation

**File**: `lambda/shared/account_utils.py` (EXTEND EXISTING)

**New Functions**:
```python
from typing import Dict, Any, Optional
from .security_utils import InputValidationError

def validate_account_context_for_invocation(
    event: Dict[str, Any],
    body: Dict[str, Any]
) -> Dict[str, str]:
    """
    Validate and extract account context based on invocation source.
    
    API Gateway Mode:
        - accountId is optional
        - Defaults to Cognito identity if missing
    
    Direct Invocation Mode:
        - accountId is REQUIRED
        - Raises ValidationError if missing
    
    Args:
        event: Lambda event object
        body: Request body
        
    Returns:
        Dictionary with accountId, assumeRoleName, externalId
        
    Raises:
        InputValidationError: If validation fails
    """
    invocation_source = detect_invocation_source(event)
    
    if invocation_source == "direct":
        # Direct invocation - accountId REQUIRED
        account_id = body.get("accountId")
        if not account_id:
            raise InputValidationError(
                "accountId is required for direct Lambda invocation. "
                "When invoking Lambda directly (without API Gateway), "
                "you must explicitly provide accountId in the event payload."
            )
    else:
        # API Gateway - accountId optional, default from Cognito
        account_id = body.get("accountId")
        if not account_id:
            account_id = extract_account_from_cognito(event)
    
    # Validate account ID format
    if not validate_account_id(account_id):
        raise InputValidationError(f"Invalid account ID format: {account_id}")
    
    return {
        "accountId": account_id,
        "assumeRoleName": body.get("assumeRoleName", ""),
        "externalId": body.get("externalId", ""),
    }

def extract_account_from_cognito(event: Dict[str, Any]) -> str:
    """
    Extract account ID from Cognito identity in API Gateway event.
    
    Args:
        event: API Gateway event with requestContext
        
    Returns:
        Account ID from Cognito custom attributes
        
    Raises:
        InputValidationError: If account ID cannot be extracted
    """
    try:
        cognito_identity = event["requestContext"]["identity"]
        # Extract from Cognito custom attributes
        # Implementation depends on Cognito configuration
        account_id = cognito_identity.get("cognitoAuthenticationProvider", "").split(":")[-1]
        return account_id
    except (KeyError, IndexError) as e:
        raise InputValidationError(f"Cannot extract account ID from Cognito: {e}")
```


#### 2.3 Protection Group Creation Handler

**File**: `lambda/data-management-handler/index.py` (MODIFY EXISTING)

**Changes to `create_protection_group()` function**:

```python
from shared.account_utils import validate_account_context_for_invocation, validate_account_id
from shared.security_utils import sanitize_string, InputValidationError

def create_protection_group(event, body):
    """
    Create Protection Group with account context.
    
    Changes from current implementation:
    1. Use validate_account_context_for_invocation() for account validation
    """
    try:
        # Validate and extract account context (handles both invocation modes)
        account_context = validate_account_context_for_invocation(event, body)
        
        # Sanitize user inputs
        group_name = sanitize_string(body["groupName"], max_length=255)
        description = sanitize_string(body.get("description", ""), max_length=1000)
        
        # Generate group ID
        group_id = str(uuid.uuid4())
        
        # Create Protection Group item
        item = {
            "groupId": group_id,
            "groupName": group_name,
            "description": description,
            "accountId": account_context["accountId"],  # REQUIRED
            "assumeRoleName": account_context.get("assumeRoleName", ""),
            "externalId": account_context.get("externalId", ""),
            "sourceServerIds": body.get("sourceServerIds", []),
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
            "createdBy": get_user_identity(event),
        }
        
        # Store in DynamoDB
        dynamodb.put_item(
            TableName=os.environ["PROTECTION_GROUPS_TABLE"],
            Item=item
        )
        
        return {
            "statusCode": 200,
            "body": json.dumps(item)
        }
        
    except InputValidationError as e:
        logger.error(f"Validation error: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
    except Exception as e:
        logger.exception(f"Unexpected error creating Protection Group: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```

**Update Protection Group Handler**:

```python
def update_protection_group(event, body, group_id):
    """
    Update Protection Group.
    
    Changes from current implementation:
    1. Account context validation for invocation mode
    """
    try:
        # Get existing Protection Group
        existing_group = get_protection_group(group_id)
        if not existing_group:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Protection Group not found"})
            }
        
        # Update DynamoDB
        update_expression = "SET "
        expression_values = {}
        
        for key, value in body.items():
            update_expression += f"{key} = :{key}, "
            expression_values[f":{key}"] = value
        
        update_expression += "updatedAt = :updatedAt"
        expression_values[":updatedAt"] = datetime.utcnow().isoformat()
        
        dynamodb.update_item(
            TableName=os.environ["PROTECTION_GROUPS_TABLE"],
            Key={"groupId": group_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Protection Group updated"})
        }
        
    except InputValidationError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
    except Exception as e:
        logger.exception(f"Error updating Protection Group: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```

**Delete Protection Group Handler**:

```python
def delete_protection_group(event, group_id):
    """
    Delete Protection Group.
    
    No notification cleanup needed - notifications are scoped to Recovery Plans.
    """
    try:
        # Get existing Protection Group
        existing_group = get_protection_group(group_id)
        if not existing_group:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Protection Group not found"})
            }
        
        # Delete from DynamoDB
        dynamodb.delete_item(
            TableName=os.environ["PROTECTION_GROUPS_TABLE"],
            Key={"groupId": group_id}
        )
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Protection Group deleted"})
        }
        
    except Exception as e:
        logger.exception(f"Error deleting Protection Group: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```

#### 2.4 Recovery Plan Creation Handler

**File**: `lambda/data-management-handler/index.py` (MODIFY EXISTING)

**Changes to `create_recovery_plan()` function**:

```python
def create_recovery_plan(event, body):
    """
    Create Recovery Plan with direct account association and optional notifications.
    
    Changes from current implementation:
    1. Add accountId and assumeRoleName fields
    2. Validate all Protection Groups belong to same account
    3. Use validate_account_context_for_invocation() for account validation
    4. Add notificationEmail validation and SNS subscription creation
    """
    try:
        # Validate and extract account context
        account_context = validate_account_context_for_invocation(event, body)
        
        # Validate notification email if provided
        notification_email = body.get("notificationEmail")
        if notification_email:
            if not validate_email(notification_email):
                raise InputValidationError(f"Invalid email format: {notification_email}")
        
        # Validate waves and Protection Groups
        waves = body.get("waves", [])
        if not waves:
            raise InputValidationError("Recovery Plan must have at least one wave")
        
        # Validate all Protection Groups belong to same account
        for wave in waves:
            pg_id = wave.get("protectionGroupId")
            if not pg_id:
                raise InputValidationError("Wave must reference a Protection Group")
            
            pg = get_protection_group(pg_id)
            if not pg:
                raise InputValidationError(f"Protection Group {pg_id} not found")
            
            if pg.get("accountId") != account_context["accountId"]:
                raise InputValidationError(
                    f"Protection Group {pg_id} belongs to account {pg.get('accountId')}, "
                    f"but Recovery Plan is for account {account_context['accountId']}"
                )
        
        # Generate plan ID
        plan_id = str(uuid.uuid4())
        
        # Create Recovery Plan item
        item = {
            "planId": plan_id,
            "planName": sanitize_string(body["planName"], max_length=255),
            "description": sanitize_string(body.get("description", ""), max_length=1000),
            "accountId": account_context["accountId"],  # NEW
            "assumeRoleName": account_context.get("assumeRoleName", ""),  # NEW
            "notificationEmail": notification_email or "",  # NEW
            "snsSubscriptionArn": "",  # NEW - updated after subscription
            "waves": waves,
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
            "createdBy": get_user_identity(event),
        }
        
        # Store in DynamoDB
        dynamodb.put_item(
            TableName=os.environ["RECOVERY_PLANS_TABLE"],
            Item=item
        )
        
        # Create SNS subscription if notification email provided
        if notification_email:
            try:
                subscription_arn = manage_recovery_plan_subscription(
                    plan_id=plan_id,
                    email=notification_email,
                    action="create"
                )
                
                # Update item with subscription ARN
                dynamodb.update_item(
                    TableName=os.environ["RECOVERY_PLANS_TABLE"],
                    Key={"planId": plan_id},
                    UpdateExpression="SET snsSubscriptionArn = :arn",
                    ExpressionAttributeValues={":arn": subscription_arn}
                )
                
                item["snsSubscriptionArn"] = subscription_arn
                
            except Exception as e:
                logger.error(f"Failed to create SNS subscription: {e}")
                # Don't fail Recovery Plan creation if subscription fails
        
        return {
            "statusCode": 200,
            "body": json.dumps(item)
        }
        
    except InputValidationError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
    except Exception as e:
        logger.exception(f"Error creating Recovery Plan: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```

**Update Recovery Plan Handler**:

```python
def update_recovery_plan(event, body, plan_id):
    """
    Update Recovery Plan including notification email changes.
    
    Changes from current implementation:
    1. Handle notificationEmail updates
    2. Manage SNS subscription lifecycle (create/update/delete)
    3. Update snsSubscriptionArn in DynamoDB
    """
    try:
        # Get existing Recovery Plan
        existing_plan = get_recovery_plan(plan_id)
        if not existing_plan:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Recovery Plan not found"})
            }
        
        # Validate new notification email if provided
        new_email = body.get("notificationEmail")
        old_email = existing_plan.get("notificationEmail")
        
        if new_email and not validate_email(new_email):
            raise InputValidationError(f"Invalid email format: {new_email}")
        
        # Handle SNS subscription changes
        if new_email != old_email:
            # Delete old subscription if exists
            if old_email and existing_plan.get("snsSubscriptionArn"):
                try:
                    manage_recovery_plan_subscription(
                        plan_id=plan_id,
                        email=old_email,
                        action="delete"
                    )
                except Exception as e:
                    logger.error(f"Failed to delete old subscription: {e}")
            
            # Create new subscription if email provided
            if new_email:
                try:
                    subscription_arn = manage_recovery_plan_subscription(
                        plan_id=plan_id,
                        email=new_email,
                        action="create"
                    )
                    body["snsSubscriptionArn"] = subscription_arn
                except Exception as e:
                    logger.error(f"Failed to create new subscription: {e}")
                    body["snsSubscriptionArn"] = ""
            else:
                body["snsSubscriptionArn"] = ""
        
        # Update DynamoDB (existing update logic)
        # ...
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Recovery Plan updated"})
        }
        
    except InputValidationError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
    except Exception as e:
        logger.exception(f"Error updating Recovery Plan: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```

**Delete Recovery Plan Handler**:

```python
def delete_recovery_plan(event, plan_id):
    """
    Delete Recovery Plan and clean up SNS subscription.
    
    Changes from current implementation:
    1. Delete SNS subscription before deleting Recovery Plan
    2. Handle subscription cleanup errors gracefully
    """
    try:
        # Get existing Recovery Plan
        existing_plan = get_recovery_plan(plan_id)
        if not existing_plan:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Recovery Plan not found"})
            }
        
        # Delete SNS subscription if exists
        if existing_plan.get("notificationEmail") and existing_plan.get("snsSubscriptionArn"):
            try:
                manage_recovery_plan_subscription(
                    plan_id=plan_id,
                    email=existing_plan["notificationEmail"],
                    action="delete"
                )
            except Exception as e:
                logger.error(f"Failed to delete SNS subscription: {e}")
                # Continue with deletion even if subscription cleanup fails
        
        # Delete from DynamoDB
        dynamodb.delete_item(
            TableName=os.environ["RECOVERY_PLANS_TABLE"],
            Key={"planId": plan_id}
        )
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Recovery Plan deleted"})
        }
        
    except Exception as e:
        logger.exception(f"Error deleting Recovery Plan: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```


#### 2.5 SNS Subscription Management

**File**: `lambda/shared/notifications.py` (EXTEND EXISTING)

**NOTE**: `notifications.py` already contains these functions that publish to SNS:
- `send_execution_started()` - Publishes execution start events
- `send_execution_completed()` - Publishes execution completion events
- `send_execution_failed()` - Publishes execution failure events
- `send_execution_paused()` - Publishes execution pause events
- `send_wave_completed()` - Publishes wave completion events
- `send_wave_failed()` - Publishes wave failure events

The new functions below extend the existing module to add per-Recovery-Plan subscription management and Recovery-Plan-scoped notification publishing. The existing `send_*` functions should be updated to call `publish_recovery_plan_notification()` internally so that message attributes (for SNS filter policies) are included.

**New Functions**:

```python
import boto3
import json
import os
from typing import Optional
from .security_utils import validate_email, InputValidationError

sns = boto3.client("sns")

def manage_recovery_plan_subscription(
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
        
    Raises:
        InputValidationError: If email is invalid
        Exception: If SNS operation fails
    """
    topic_arn = os.environ.get("EXECUTION_NOTIFICATIONS_TOPIC_ARN")
    if not topic_arn:
        raise ValueError("EXECUTION_NOTIFICATIONS_TOPIC_ARN not configured")
    
    if action == "create":
        # Validate email format
        if not validate_email(email):
            raise InputValidationError(f"Invalid email format: {email}")
        
        # Create subscription with message filtering by Recovery Plan ID
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email,
            Attributes={
                "FilterPolicy": json.dumps({
                    "recoveryPlanId": [plan_id]
                }),
                "FilterPolicyScope": "MessageAttributes"
            },
            ReturnSubscriptionArn=True
        )
        
        subscription_arn = response.get("SubscriptionArn", "")
        
        logger.info(f"Created SNS subscription for Recovery Plan {plan_id}: {subscription_arn}")
        
        return subscription_arn
    
    elif action == "delete":
        subscription_arn = get_subscription_arn_for_plan(plan_id)
        
        if subscription_arn and subscription_arn != "PendingConfirmation":
            try:
                sns.unsubscribe(SubscriptionArn=subscription_arn)
                logger.info(f"Deleted SNS subscription for Recovery Plan {plan_id}")
            except Exception as e:
                logger.error(f"Failed to delete subscription {subscription_arn}: {e}")
                raise
        
        return None
    
    elif action == "update":
        # Update = delete old + create new
        manage_recovery_plan_subscription(plan_id, email, action="delete")
        return manage_recovery_plan_subscription(plan_id, email, action="create")
    
    else:
        raise ValueError(f"Invalid action: {action}")

def get_subscription_arn_for_plan(plan_id: str) -> Optional[str]:
    """
    Get SNS subscription ARN for Recovery Plan from DynamoDB.
    
    Args:
        plan_id: Recovery Plan ID
        
    Returns:
        Subscription ARN or None if not found
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["RECOVERY_PLANS_TABLE"])
    
    try:
        response = table.get_item(Key={"planId": plan_id})
        item = response.get("Item", {})
        return item.get("snsSubscriptionArn")
    except Exception as e:
        logger.error(f"Failed to get subscription ARN for plan {plan_id}: {e}")
        return None

def publish_recovery_plan_notification(
    plan_id: str,
    event_type: str,
    details: dict
) -> None:
    """
    Publish notification for Recovery Plan execution events.
    
    Args:
        plan_id: Recovery Plan ID
        event_type: Event type (start, complete, fail, pause, resume, cancel)
        details: Event details dictionary
    """
    topic_arn = os.environ.get("EXECUTION_NOTIFICATIONS_TOPIC_ARN")
    if not topic_arn:
        logger.warning("EXECUTION_NOTIFICATIONS_TOPIC_ARN not configured, skipping notification")
        return
    
    # Format message
    message = format_notification_message(event_type, details)
    
    # Publish with message attributes for filtering by Recovery Plan ID
    try:
        sns.publish(
            TopicArn=topic_arn,
            Message=json.dumps(message),
            Subject=f"[DRS] Recovery Plan: {details.get('planName', 'Unknown')} - {event_type}",
            MessageAttributes={
                "recoveryPlanId": {
                    "DataType": "String",
                    "StringValue": plan_id
                },
                "eventType": {
                    "DataType": "String",
                    "StringValue": event_type
                }
            }
        )
        logger.info(f"Published notification for Recovery Plan {plan_id}, event {event_type}")
    except Exception as e:
        logger.error(f"Failed to publish notification: {e}")
        # Don't raise - notification failure shouldn't block execution
```

#### 2.6 Step Functions Integration

**File**: `lambda/dr-orchestration-stepfunction/index.py` (MODIFY EXISTING)

**Add Notification Publishing to State Transitions**:

```python
from shared.notifications import publish_recovery_plan_notification

def handle_execution_start(event, context):
    """
    Handle execution start event.
    
    Changes from current implementation:
    1. Publish notification to SNS after starting execution
    """
    try:
        # Existing execution start logic...
        execution_id = event.get("executionId")
        plan_id = event.get("planId")
        
        # Get Recovery Plan
        plan = get_recovery_plan(plan_id)
        
        # Start execution (existing logic)
        # ...
        
        # NEW: Publish notification for the Recovery Plan
        publish_recovery_plan_notification(
            plan_id=plan_id,
            event_type="start",
            details={
                "executionId": execution_id,
                "planId": plan_id,
                "planName": plan.get("planName"),
                "accountId": plan.get("accountId"),
                "waveCount": len(plan.get("waves", [])),
                "timestamp": datetime.utcnow().isoformat(),
                "consoleLink": f"https://console.aws.amazon.com/drs/executions/{execution_id}"
            }
        )
        
        return event
        
    except Exception as e:
        logger.exception(f"Error handling execution start: {e}")
        raise

def handle_execution_complete(event, context):
    """
    Handle execution complete event.
    
    Changes from current implementation:
    1. Publish notification to SNS after execution completes
    """
    try:
        # Existing completion logic...
        execution_id = event.get("executionId")
        plan_id = event.get("planId")
        
        # Get execution results
        results = event.get("results", {})
        
        # NEW: Publish notification
        plan = get_recovery_plan(plan_id)
        publish_recovery_plan_notification(
            plan_id=plan_id,
            event_type="complete",
            details={
                "executionId": execution_id,
                "planId": plan_id,
                "planName": plan.get("planName"),
                "accountId": plan.get("accountId"),
                "timestamp": datetime.utcnow().isoformat(),
                "duration": results.get("duration"),
                "successCount": results.get("successCount"),
                "failureCount": results.get("failureCount"),
                "consoleLink": f"https://console.aws.amazon.com/drs/executions/{execution_id}"
            }
        )
        
        return event
        
    except Exception as e:
        logger.exception(f"Error handling execution complete: {e}")
        raise

def handle_execution_failure(event, context):
    """
    Handle execution failure event.
    
    Changes from current implementation:
    1. Publish notification to SNS after execution fails
    """
    try:
        # Existing failure logic...
        execution_id = event.get("executionId")
        plan_id = event.get("planId")
        error = event.get("error", {})
        
        # NEW: Publish notification
        plan = get_recovery_plan(plan_id)
        publish_recovery_plan_notification(
            plan_id=plan_id,
            event_type="fail",
            details={
                "executionId": execution_id,
                "planId": plan_id,
                "planName": plan.get("planName"),
                "accountId": plan.get("accountId"),
                "timestamp": datetime.utcnow().isoformat(),
                "errorMessage": error.get("message"),
                "errorType": error.get("type"),
                "consoleLink": f"https://console.aws.amazon.com/drs/executions/{execution_id}"
            }
        )
        
        return event
        
    except Exception as e:
        logger.exception(f"Error handling execution failure: {e}")
        raise
```

**Add Pause State with Task Token**:

```python
def handle_execution_pause(event, context):
    """
    Handle execution pause event with task token for resume/cancel.
    
    NEW FUNCTION for interactive pause/resume workflow.
    
    This function is called when Step Functions reaches a pause state.
    It publishes a notification with the task token embedded in action URLs.
    """
    try:
        execution_id = event.get("executionId")
        plan_id = event.get("planId")
        task_token = event.get("taskToken")  # Provided by Step Functions waitForTaskToken
        pause_reason = event.get("pauseReason", "Manual pause requested")
        
        if not task_token:
            raise ValueError("Task token is required for pause notifications")
        
        # Get Recovery Plan
        plan = get_recovery_plan(plan_id)
        
        # Publish pause notification with task token at Recovery Plan level
        publish_recovery_plan_notification(
            plan_id=plan_id,
            event_type="pause",
            details={
                "executionId": execution_id,
                "planId": plan_id,
                "planName": plan.get("planName"),
                "accountId": plan.get("accountId"),
                "timestamp": datetime.utcnow().isoformat(),
                "pauseReason": pause_reason,
                "taskToken": task_token,  # Include task token for callback
                "resumeUrl": f"{os.environ['API_GATEWAY_URL']}/execution?action=resume&taskToken={task_token}",
                "cancelUrl": f"{os.environ['API_GATEWAY_URL']}/execution?action=cancel&taskToken={task_token}",
                "consoleLink": f"https://console.aws.amazon.com/drs/executions/{execution_id}"
            }
        )
        
        # Return event unchanged - Step Functions will wait for callback
        return event
        
    except Exception as e:
        logger.exception(f"Error handling execution pause: {e}")
        raise
```



#### 2.7 Callback Handler for Pause/Resume

**File**: `lambda/execution-handler/index.py` (EXTEND EXISTING)

**Purpose**: Add task token callback handling to the existing execution handler

**Why extend `execution-handler` instead of creating a new Lambda?**
The existing `execution-handler` already has `pause_execution()` and `resume_execution()` functions, and already manages execution lifecycle. Adding callback handling here:
- Keeps all execution-related logic in one place
- Reuses existing DynamoDB table references and boto3 clients
- Avoids a new Lambda deployment, CloudFormation resource, and IAM role
- The handler already routes between API Gateway and direct invocation modes

**How it integrates**: The existing `lambda_handler` already routes based on HTTP method and path. The callback endpoint is a GET request to `/execution` with query parameters, which can be routed alongside existing execution operations. The handler detects callback requests by checking for `action` and `taskToken` query parameters.

**NOTE**: The callback endpoint uses `AuthorizationType: NONE` in API Gateway (task token is the credential). The execution-handler's `lambda_handler` must detect this unauthenticated callback path and skip Cognito validation for it.

**New Functions Added to `execution-handler/index.py`**:
```python
def handle_execution_callback(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle execution resume/cancel callbacks from email links.
    
    This is invoked via unauthenticated GET requests from email action links.
    The task token itself serves as authorization.
    
    Query Parameters:
        action: "resume" or "cancel"
        taskToken: Step Functions task token
        
    Returns:
        HTTP response with HTML success/error page
    """
    try:
        params = event.get("queryStringParameters", {})
        action = params.get("action")
        task_token = params.get("taskToken")
        
        if not action or action not in ["resume", "cancel"]:
            return _callback_error_response(
                400, "Invalid action. Must be 'resume' or 'cancel'"
            )
        
        if not task_token:
            return _callback_error_response(400, "Missing task token")
        
        if not _validate_task_token(task_token):
            return _callback_error_response(
                400, "Invalid or expired task token"
            )
        
        if action == "resume":
            result = _resume_via_task_token(task_token)
            message = "Execution resumed successfully"
        else:
            result = _cancel_via_task_token(task_token)
            message = "Execution cancelled successfully"
        
        _log_callback_action(task_token, action, result)
        
        return _callback_success_response(message, action)
        
    except Exception as e:
        logger.exception(f"Error handling callback: {e}")
        return _callback_error_response(
            500, f"Internal server error: {str(e)}"
        )

def _validate_task_token(task_token: str) -> bool:
    """Validate task token format."""
    try:
        if not task_token or len(task_token) < 100:
            return False
        return True
    except Exception as e:
        logger.error(f"Task token validation error: {e}")
        return False

def _resume_via_task_token(task_token: str) -> Dict[str, Any]:
    """Resume paused execution via Step Functions task token."""
    try:
        stepfunctions = boto3.client("stepfunctions")
        response = stepfunctions.send_task_success(
            taskToken=task_token,
            output=json.dumps({
                "action": "resume",
                "timestamp": datetime.utcnow().isoformat(),
                "resumedBy": "email_callback"
            })
        )
        logger.info("Execution resumed via task token")
        return response
    except stepfunctions.exceptions.InvalidToken:
        raise ValueError("Task token is invalid or expired")
    except stepfunctions.exceptions.TaskTimedOut:
        raise ValueError("Task has timed out")

def _cancel_via_task_token(task_token: str) -> Dict[str, Any]:
    """Cancel paused execution via Step Functions task token."""
    try:
        stepfunctions = boto3.client("stepfunctions")
        response = stepfunctions.send_task_failure(
            taskToken=task_token,
            error="ExecutionCancelled",
            cause="User cancelled execution via email notification"
        )
        logger.info("Execution cancelled via task token")
        return response
    except stepfunctions.exceptions.InvalidToken:
        raise ValueError("Task token is invalid or expired")
    except stepfunctions.exceptions.TaskTimedOut:
        raise ValueError("Task has timed out")

def _log_callback_action(
    task_token: str, action: str, result: Dict[str, Any]
) -> None:
    """Log callback action to DynamoDB for audit trail."""
    try:
        table = get_execution_history_table()
        table.put_item(
            Item={
                "callbackId": f"callback-{datetime.utcnow().timestamp()}",
                "taskToken": task_token[:50],
                "action": action,
                "timestamp": datetime.utcnow().isoformat(),
                "result": "success" if result else "failure"
            }
        )
    except Exception as e:
        logger.error(f"Failed to log callback action: {e}")

def _callback_success_response(
    message: str, action: str
) -> Dict[str, Any]:
    """Generate success HTML response for email callback."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Execution {action.capitalize()}</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
        .success {{ color: #037f0c; font-size: 24px; margin-bottom: 20px; }}
        .message {{ color: #16191f; font-size: 16px; }}
    </style>
</head>
<body>
    <div class="success">✓ Success</div>
    <div class="message">{message}</div>
    <p>You can close this window.</p>
</body>
</html>"""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": html
    }

def _callback_error_response(
    status_code: int, message: str
) -> Dict[str, Any]:
    """Generate error HTML response for email callback."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
        .error {{ color: #d13212; font-size: 24px; margin-bottom: 20px; }}
        .message {{ color: #16191f; font-size: 16px; }}
    </style>
</head>
<body>
    <div class="error">✗ Error</div>
    <div class="message">{message}</div>
    <p>Please contact support if this issue persists.</p>
</body>
</html>"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "text/html"},
        "body": html
    }
```

**Routing in `lambda_handler`**: The existing `lambda_handler` should add a check early in the routing logic:
```python
def lambda_handler(event, context):
    # Check for unauthenticated callback request (email action links)
    params = event.get("queryStringParameters", {})
    if params and params.get("action") and params.get("taskToken"):
        return handle_execution_callback(event)
    
    # ... existing routing logic ...
```

**Security Considerations**:
- Task tokens are cryptographically signed by Step Functions
- Tokens expire after execution completes or times out
- No additional authentication required (token itself is proof of authorization)
- Log all callback actions for audit trail
- Rate limiting via API Gateway throttling



#### 2.8 Notification Formatter Lambda

**File**: `lambda/notification-formatter/index.py` (MODIFY EXISTING)

**Changes**: Add support for interactive pause notifications with action buttons

**New Email Template for Pause Notifications**:

```python
def format_pause_notification(details: Dict[str, Any]) -> str:
    """
    Format pause notification email with interactive action buttons.
    
    Args:
        details: Event details including taskToken, resumeUrl, cancelUrl
        
    Returns:
        HTML email body with action buttons
    """
    execution_id = details.get("executionId", "Unknown")
    plan_name = details.get("planName", "Unknown")
    group_name = details.get("groupName", "Unknown")
    pause_reason = details.get("pauseReason", "Manual pause requested")
    resume_url = details.get("resumeUrl", "")
    cancel_url = details.get("cancelUrl", "")
    console_link = details.get("consoleLink", "")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #16191f; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #232f3e; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #ffffff; padding: 20px; border: 1px solid #d5dbdb; }}
            .info {{ background-color: #f2f3f3; padding: 15px; margin: 15px 0; border-left: 4px solid #0972d3; }}
            .actions {{ text-align: center; margin: 30px 0; }}
            .button {{ display: inline-block; padding: 12px 24px; margin: 0 10px; text-decoration: none; border-radius: 4px; font-weight: bold; }}
            .button-primary {{ background-color: #0972d3; color: white; }}
            .button-secondary {{ background-color: #d13212; color: white; }}
            .footer {{ text-align: center; color: #5f6b7a; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛑 DR Execution Paused</h1>
            </div>
            <div class="content">
                <p>The disaster recovery execution has been paused and requires your action.</p>
                
                <div class="info">
                    <strong>Execution ID:</strong> {execution_id}<br>
                    <strong>Recovery Plan:</strong> {plan_name}<br>
                    <strong>Protection Group:</strong> {group_name}<br>
                    <strong>Pause Reason:</strong> {pause_reason}
                </div>
                
                <p>Please choose an action:</p>
                
                <div class="actions">
                    <a href="{resume_url}" class="button button-primary">▶ Resume Execution</a>
                    <a href="{cancel_url}" class="button button-secondary">✕ Cancel Execution</a>
                </div>
                
                <p style="text-align: center; margin-top: 30px;">
                    <a href="{console_link}">View in AWS Console</a>
                </p>
            </div>
            <div class="footer">
                <p>This is an automated notification from AWS DRS Orchestration Platform.</p>
                <p>If you did not expect this email, please contact your administrator.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def format_notification_message(event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format notification message based on event type.
    
    Changes from current implementation:
    1. Add "pause" event type with interactive HTML
    2. Include task token in pause notifications
    """
    if event_type == "pause":
        # Interactive pause notification
        return {
            "default": f"DR Execution Paused: {details.get('planName')}",
            "email": format_pause_notification(details)
        }
    elif event_type == "start":
        return {
            "default": f"DR Execution Started: {details.get('planName')}",
            "email": format_start_notification(details)
        }
    elif event_type == "complete":
        return {
            "default": f"DR Execution Completed: {details.get('planName')}",
            "email": format_complete_notification(details)
        }
    elif event_type == "fail":
        return {
            "default": f"DR Execution Failed: {details.get('planName')}",
            "email": format_failure_notification(details)
        }
    else:
        return {
            "default": f"DR Event: {event_type}",
            "email": f"Event: {event_type}\nDetails: {json.dumps(details, indent=2)}"
        }
```



### 3. DynamoDB Schema Changes

#### 3.1 Protection Groups Table

**Table Name**: `hrp-drs-tech-adapter-protection-groups-{environment}`

**New Attributes** (added to existing schema):

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `accountId` | String | Yes | AWS account ID (12 digits) - currently optional, make required |

**Updated Item Structure**:
```json
{
  "groupId": "uuid",
  "groupName": "string",
  "description": "string",
  "accountId": "123456789012",
  "assumeRoleName": "string",
  "externalId": "string",
  "sourceServerIds": ["s-xxx", "s-yyy"],
  "createdAt": "ISO-8601",
  "updatedAt": "ISO-8601",
  "createdBy": "string"
}
```

**Migration Strategy**:
- Existing items remain valid (new field `accountId` is required)
- Backfill script adds `accountId` to existing items

**GSI Requirements**: No new GSI needed for this phase

#### 3.2 Recovery Plans Table

**Table Name**: `hrp-drs-tech-adapter-recovery-plans-{environment}`

**New Attributes** (added to existing schema):

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `accountId` | String | Yes | AWS account ID (12 digits) |
| `assumeRoleName` | String | No | Cross-account role name |
| `notificationEmail` | String | No | Email for execution notifications |
| `snsSubscriptionArn` | String | No | SNS subscription ARN |

**Updated Item Structure**:
```json
{
  "planId": "uuid",
  "planName": "string",
  "description": "string",
  "accountId": "123456789012",
  "assumeRoleName": "string",
  "notificationEmail": "team@example.com",
  "snsSubscriptionArn": "arn:aws:sns:region:account:topic:subscription-id",
  "waves": [
    {
      "waveNumber": 1,
      "protectionGroupId": "uuid",
      "protectionGroupName": "string",
      "pauseBeforeExecution": false
    }
  ],
  "createdAt": "ISO-8601",
  "updatedAt": "ISO-8601",
  "createdBy": "string"
}
```

**NOTE**: Notification fields (`notificationEmail`, `snsSubscriptionArn`) are on Recovery Plans because executions are scoped to plans. A single notification per execution event is sent to the plan subscriber, covering all waves and Protection Groups within that plan.

**Migration Strategy**:
- Existing items remain valid
- Backfill script derives `accountId` from first Protection Group in plan
- If Protection Groups have different accounts, mark plan as invalid
- `notificationEmail` and `snsSubscriptionArn` default to empty string for existing items

#### 3.3 Executions Table (No Changes)

**Table Name**: `hrp-drs-tech-adapter-executions-{environment}`

**Note**: No schema changes needed. Account context is derived from Recovery Plan.

### 4. API Gateway Changes

#### 4.1 New Endpoint: Execution Callback

**Path**: `/execution-callback`
**Method**: GET
**Authentication**: None (task token provides authorization)

**Query Parameters**:
- `action`: "resume" or "cancel" (required)
- `taskToken`: Step Functions task token (required)

**Integration**: Lambda proxy integration to existing `execution-handler` (which routes callback requests internally)

**Response**:
- 200: HTML success page
- 400: HTML error page (invalid parameters)
- 500: HTML error page (internal error)

**CloudFormation Resource**:
```yaml
ExecutionCallbackResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    RestApiId: !Ref RestApi
    ParentId: !GetAtt RestApi.RootResourceId
    PathPart: execution-callback

ExecutionCallbackMethod:
  Type: AWS::ApiGateway::Method
  Properties:
    RestApiId: !Ref RestApi
    ResourceId: !Ref ExecutionCallbackResource
    HttpMethod: GET
    AuthorizationType: NONE
    Integration:
      Type: AWS_PROXY
      IntegrationHttpMethod: POST
      Uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ExecutionHandlerArn}/invocations
```

#### 4.2 Existing Endpoints (No Changes)

All existing endpoints remain unchanged:
- `/protection-groups` (POST, GET, PUT, DELETE)
- `/recovery-plans` (POST, GET, PUT, DELETE)
- `/executions` (POST, GET)
- `/query` (POST)



### 5. CloudFormation Changes

#### 5.1 Master Template Updates

**File**: `cfn/master-template.yaml`

**Changes**:

1. **Add Environment Variables to Existing Lambda Functions** (execution-handler, data-management-handler, dr-orchestration-stepfunction):
```yaml
Environment:
  Variables:
    EXECUTION_NOTIFICATIONS_TOPIC_ARN: !GetAtt NotificationStack.Outputs.ExecutionNotificationsTopicArn
    API_GATEWAY_URL: !Sub https://${RestApi}.execute-api.${AWS::Region}.amazonaws.com/${Environment}
```

**NOTE**: No new Lambda functions are created. The callback handler is added to the existing `execution-handler` Lambda. The existing Lambda permission for API Gateway already covers the new callback endpoint.

#### 5.2 IAM Role Updates

**File**: `cfn/master-template.yaml`

**Add to UnifiedOrchestrationRole Policies**:

```yaml
# SNS Subscription Management
- Effect: Allow
  Action:
    - sns:Subscribe
    - sns:Unsubscribe
    - sns:ListSubscriptionsByTopic
    - sns:GetSubscriptionAttributes
    - sns:SetSubscriptionAttributes
  Resource:
    - !GetAtt NotificationStack.Outputs.ExecutionNotificationsTopicArn
    - !GetAtt NotificationStack.Outputs.DRSOperationalAlertsTopicArn

# SNS Publishing
- Effect: Allow
  Action:
    - sns:Publish
  Resource:
    - !GetAtt NotificationStack.Outputs.ExecutionNotificationsTopicArn
    - !GetAtt NotificationStack.Outputs.DRSOperationalAlertsTopicArn

# Step Functions Task Token Callbacks
- Effect: Allow
  Action:
    - states:SendTaskSuccess
    - states:SendTaskFailure
    - states:SendTaskHeartbeat
  Resource: "*"
```

#### 5.3 Notification Stack Updates

**File**: `cfn/notification-stack.yaml`

**Changes**: No structural changes needed, but ensure outputs are exported:

```yaml
Outputs:
  ExecutionNotificationsTopicArn:
    Description: ARN of Execution Notifications Topic
    Value: !Ref ExecutionNotificationsTopic
    Export:
      Name: !Sub ${AWS::StackName}-ExecutionNotificationsTopicArn
  
  DRSOperationalAlertsTopicArn:
    Description: ARN of DRS Operational Alerts Topic
    Value: !Ref DRSOperationalAlertsTopic
    Export:
      Name: !Sub ${AWS::StackName}-DRSOperationalAlertsTopicArn
```

#### 5.4 API Gateway Stack Updates

**File**: `cfn/api-gateway-deployment-stack.yaml`

**Add Execution Callback Endpoint** (unauthenticated GET routed to existing execution-handler):

```yaml
ExecutionCallbackResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    RestApiId: !Ref RestApi
    ParentId: !GetAtt RestApi.RootResourceId
    PathPart: execution-callback

ExecutionCallbackMethod:
  Type: AWS::ApiGateway::Method
  Properties:
    RestApiId: !Ref RestApi
    ResourceId: !Ref ExecutionCallbackResource
    HttpMethod: GET
    AuthorizationType: NONE
    RequestParameters:
      method.request.querystring.action: true
      method.request.querystring.taskToken: true
    Integration:
      Type: AWS_PROXY
      IntegrationHttpMethod: POST
      Uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ExecutionHandlerArn}/invocations
    MethodResponses:
      - StatusCode: 200
        ResponseModels:
          text/html: Empty
      - StatusCode: 400
        ResponseModels:
          text/html: Empty
      - StatusCode: 500
        ResponseModels:
          text/html: Empty
```

#### 5.5 Step Functions State Machine Updates

**File**: `cfn/step-functions-stack.yaml`

**Add Pause State with Task Token**:

```yaml
States:
  # ... existing states ...
  
  CheckPauseRequired:
    Type: Choice
    Choices:
      - Variable: $.pauseBeforeExecution
        BooleanEquals: true
        Next: PauseForApproval
    Default: ExecuteWave
  
  PauseForApproval:
    Type: Task
    Resource: arn:aws:states:::lambda:invoke.waitForTaskToken
    Parameters:
      FunctionName: !Ref OrchestrationStepFunctionHandler
      Payload:
        action: pause
        executionId.$: $.executionId
        planId.$: $.planId
        taskToken.$: $$.Task.Token
    TimeoutSeconds: 86400  # 24 hours
    Catch:
      - ErrorEquals: ["States.Timeout"]
        Next: HandleTimeout
      - ErrorEquals: ["ExecutionCancelled"]
        Next: HandleCancellation
    Next: ExecuteWave
  
  HandleTimeout:
    Type: Fail
    Error: ExecutionTimeout
    Cause: Execution paused for more than 24 hours without action
  
  HandleCancellation:
    Type: Fail
    Error: ExecutionCancelled
    Cause: User cancelled execution via email notification
  
  ExecuteWave:
    Type: Task
    Resource: !GetAtt OrchestrationStepFunctionHandler.Arn
    # ... rest of wave execution logic ...
```



### 6. Data Backfill Strategy

#### 6.1 Backfill Script for Protection Groups

**File**: `scripts/backfill-protection-groups.py` (NEW)

**Purpose**: Add `accountId` to existing Protection Groups (no notification fields needed)

**Implementation**:
```python
#!/usr/bin/env python3
"""
Backfill accountId for existing Protection Groups.

This script adds the accountId field to Protection Groups that don't have it.
For Protection Groups with assumeRoleName, we can derive the account ID.
For others, we'll need to query DRS to find the account.
"""

import boto3
import sys
from typing import Dict, Any, Optional

dynamodb = boto3.resource("dynamodb")
drs = boto3.client("drs")

def get_account_from_source_servers(source_server_ids: list) -> Optional[str]:
    """
    Derive account ID from source servers.
    
    Args:
        source_server_ids: List of DRS source server IDs
        
    Returns:
        Account ID or None if cannot be determined
    """
    if not source_server_ids:
        return None
    
    try:
        # Describe first source server to get account context
        response = drs.describe_source_servers(
            filters={"sourceServerIDs": [source_server_ids[0]]}
        )
        
        if response.get("items"):
            server = response["items"][0]
            # Extract account ID from ARN
            arn = server.get("arn", "")
            if arn:
                # ARN format: arn:aws:drs:region:account-id:source-server/server-id
                parts = arn.split(":")
                if len(parts) >= 5:
                    return parts[4]
        
        return None
    except Exception as e:
        print(f"Error querying DRS: {e}")
        return None

def backfill_protection_groups(table_name: str, dry_run: bool = True) -> None:
    """
    Backfill accountId for Protection Groups.
    
    Args:
        table_name: DynamoDB table name
        dry_run: If True, only print changes without applying
    """
    table = dynamodb.Table(table_name)
    
    # Scan all Protection Groups
    response = table.scan()
    items = response.get("Items", [])
    
    # Handle pagination
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))
    
    print(f"Found {len(items)} Protection Groups")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for item in items:
        group_id = item.get("groupId")
        group_name = item.get("groupName")
        
        # Skip if accountId already exists
        if item.get("accountId"):
            print(f"✓ {group_name} ({group_id}): Already has accountId")
            skipped_count += 1
            continue
        
        # Try to derive accountId
        account_id = None
        
        # Method 1: From assumeRoleName (if it contains account ID)
        assume_role = item.get("assumeRoleName", "")
        if assume_role and ":" in assume_role:
            # Format: arn:aws:iam::123456789012:role/RoleName
            parts = assume_role.split(":")
            if len(parts) >= 5:
                account_id = parts[4]
        
        # Method 2: Query DRS source servers
        if not account_id:
            source_server_ids = item.get("sourceServerIds", [])
            account_id = get_account_from_source_servers(source_server_ids)
        
        if account_id:
            print(f"→ {group_name} ({group_id}): Will add accountId={account_id}")
            
            if not dry_run:
                try:
                    table.update_item(
                        Key={"groupId": group_id},
                        UpdateExpression="SET accountId = :aid",
                        ExpressionAttributeValues={
                            ":aid": account_id
                        }
                    )
                    print(f"  ✓ Updated")
                    updated_count += 1
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    error_count += 1
            else:
                updated_count += 1
        else:
            print(f"✗ {group_name} ({group_id}): Cannot determine accountId")
            error_count += 1
    
    print(f"\nSummary:")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    
    if dry_run:
        print(f"\nDRY RUN - No changes applied. Run with --apply to update.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill accountId for Protection Groups")
    parser.add_argument("--table", required=True, help="DynamoDB table name")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry run)")
    
    args = parser.parse_args()
    
    backfill_protection_groups(args.table, dry_run=not args.apply)
```

**Usage**:
```bash
# Dry run (preview changes)
python scripts/backfill-protection-groups.py --table hrp-drs-tech-adapter-protection-groups-dev

# Apply changes
python scripts/backfill-protection-groups.py --table hrp-drs-tech-adapter-protection-groups-dev --apply
```

#### 6.2 Backfill Script for Recovery Plans

**File**: `scripts/backfill-recovery-plans.py` (NEW)

**Purpose**: Add `accountId` and notification fields to existing Recovery Plans

**Implementation**:
```python
#!/usr/bin/env python3
"""
Backfill accountId for existing Recovery Plans.

This script derives accountId from the first Protection Group in each plan.
"""

import boto3
import sys
from typing import Optional

dynamodb = boto3.resource("dynamodb")

def get_protection_group_account(pg_table_name: str, group_id: str) -> Optional[str]:
    """
    Get account ID from Protection Group.
    
    Args:
        pg_table_name: Protection Groups table name
        group_id: Protection Group ID
        
    Returns:
        Account ID or None
    """
    table = dynamodb.Table(pg_table_name)
    
    try:
        response = table.get_item(Key={"groupId": group_id})
        item = response.get("Item", {})
        return item.get("accountId")
    except Exception as e:
        print(f"Error getting Protection Group {group_id}: {e}")
        return None

def backfill_recovery_plans(
    plans_table: str,
    groups_table: str,
    dry_run: bool = True
) -> None:
    """
    Backfill accountId for Recovery Plans.
    
    Args:
        plans_table: Recovery Plans table name
        groups_table: Protection Groups table name
        dry_run: If True, only print changes without applying
    """
    table = dynamodb.Table(plans_table)
    
    # Scan all Recovery Plans
    response = table.scan()
    items = response.get("Items", [])
    
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))
    
    print(f"Found {len(items)} Recovery Plans")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for item in items:
        plan_id = item.get("planId")
        plan_name = item.get("planName")
        
        # Skip if accountId already exists
        if item.get("accountId"):
            print(f"✓ {plan_name} ({plan_id}): Already has accountId")
            skipped_count += 1
            continue
        
        # Get accountId from first Protection Group
        waves = item.get("waves", [])
        if not waves:
            print(f"✗ {plan_name} ({plan_id}): No waves defined")
            error_count += 1
            continue
        
        first_pg_id = waves[0].get("protectionGroupId")
        if not first_pg_id:
            print(f"✗ {plan_name} ({plan_id}): First wave has no Protection Group")
            error_count += 1
            continue
        
        account_id = get_protection_group_account(groups_table, first_pg_id)
        
        if account_id:
            print(f"→ {plan_name} ({plan_id}): Will add accountId={account_id}")
            
            if not dry_run:
                try:
                    table.update_item(
                        Key={"planId": plan_id},
                        UpdateExpression="SET accountId = :aid, assumeRoleName = :role, notificationEmail = :email, snsSubscriptionArn = :arn",
                        ExpressionAttributeValues={
                            ":aid": account_id,
                            ":role": "",
                            ":email": "",
                            ":arn": ""
                        }
                    )
                    print(f"  ✓ Updated")
                    updated_count += 1
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    error_count += 1
            else:
                updated_count += 1
        else:
            print(f"✗ {plan_name} ({plan_id}): Cannot determine accountId")
            error_count += 1
    
    print(f"\nSummary:")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    
    if dry_run:
        print(f"\nDRY RUN - No changes applied. Run with --apply to update.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill accountId for Recovery Plans")
    parser.add_argument("--plans-table", required=True, help="Recovery Plans table name")
    parser.add_argument("--groups-table", required=True, help="Protection Groups table name")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    
    args = parser.parse_args()
    
    backfill_recovery_plans(args.plans_table, args.groups_table, dry_run=not args.apply)
```

**Usage**:
```bash
# Dry run
python scripts/backfill-recovery-plans.py \
  --plans-table hrp-drs-tech-adapter-recovery-plans-dev \
  --groups-table hrp-drs-tech-adapter-protection-groups-dev

# Apply changes
python scripts/backfill-recovery-plans.py \
  --plans-table hrp-drs-tech-adapter-recovery-plans-dev \
  --groups-table hrp-drs-tech-adapter-protection-groups-dev \
  --apply
```



### 7. Correctness Properties

#### 7.1 Account Context Properties

**Property 1: Account ID Consistency**
```python
@given(protection_groups=st.lists(protection_group_strategy(), min_size=1))
def test_recovery_plan_account_consistency(protection_groups):
    """
    Property: All Protection Groups in a Recovery Plan must have the same accountId.
    
    Validates: Requirements 1.1, 2.1
    """
    # Create Recovery Plan with multiple Protection Groups
    plan = create_recovery_plan(protection_groups)
    
    # Extract all account IDs
    account_ids = [pg.accountId for pg in protection_groups]
    
    # Assert all account IDs are the same
    assert len(set(account_ids)) == 1, "All Protection Groups must belong to same account"
```

**Property 2: Account ID Format Validation**
```python
@given(account_id=st.text())
def test_account_id_format_validation(account_id):
    """
    Property: accountId must be exactly 12 digits.
    
    Validates: Requirements 1.2, 2.2
    """
    is_valid = validate_account_id(account_id)
    
    # Valid if and only if 12 digits
    expected_valid = (
        len(account_id) == 12 and
        account_id.isdigit()
    )
    
    assert is_valid == expected_valid
```

**Property 3: Invocation Source Detection**
```python
@given(event=api_gateway_event_strategy())
def test_api_gateway_invocation_detection(event):
    """
    Property: Events with requestContext are detected as API Gateway invocations.
    
    Validates: Requirements 1.3
    """
    source = detect_invocation_source(event)
    
    if "requestContext" in event:
        assert source == "api_gateway"
    else:
        assert source == "direct"
```

**Property 4: Direct Invocation Requires Account ID**
```python
@given(event=direct_lambda_event_strategy())
def test_direct_invocation_requires_account_id(event):
    """
    Property: Direct Lambda invocation must include accountId in payload.
    
    Validates: Requirements 1.4
    """
    body = json.loads(event.get("body", "{}"))
    
    if "accountId" not in body:
        with pytest.raises(InputValidationError):
            validate_account_context_for_invocation(event, body)
    else:
        # Should succeed
        context = validate_account_context_for_invocation(event, body)
        assert context["accountId"] == body["accountId"]
```

#### 7.2 Notification Properties

**Property 5: Email Format Validation**
```python
@given(email=st.text())
def test_email_format_validation(email):
    """
    Property: Email validation follows RFC 5322 format.
    
    Validates: Requirements 4.1
    """
    is_valid = validate_email(email)
    
    # Valid emails must have @ and domain
    if is_valid:
        assert "@" in email
        assert "." in email.split("@")[1]
    
    # Invalid emails should not pass
    if not ("@" in email and "." in email.split("@")[-1]):
        assert not is_valid
```

**Property 6: SNS Subscription Lifecycle**
```python
@given(plan_id=st.uuids(), email=valid_email_strategy())
def test_sns_subscription_lifecycle(plan_id, email):
    """
    Property: SNS subscription create → delete leaves no subscription.
    
    Validates: Requirements 5.2, 5.12
    """
    # Create subscription
    arn = manage_recovery_plan_subscription(
        plan_id=str(plan_id),
        email=email,
        action="create"
    )
    
    assert arn is not None
    assert arn.startswith("arn:aws:sns:")
    
    # Delete subscription
    result = manage_recovery_plan_subscription(
        plan_id=str(plan_id),
        email=email,
        action="delete"
    )
    
    assert result is None
    
    # Verify subscription is gone
    subscriptions = list_subscriptions_for_topic()
    assert arn not in [s["SubscriptionArn"] for s in subscriptions]
```

**Property 7: Notification Delivery**
```python
@given(event_type=st.sampled_from(["start", "complete", "fail", "pause"]))
def test_notification_published_for_all_event_types(event_type):
    """
    Property: All execution events trigger notifications.
    
    Validates: Requirements 5.3
    """
    plan_id = str(uuid.uuid4())
    details = {
        "executionId": str(uuid.uuid4()),
        "planId": plan_id,
        "planName": "Test Plan",
        "accountId": "123456789012"
    }
    
    # Publish notification
    publish_recovery_plan_notification(plan_id, event_type, details)
    
    # Verify SNS publish was called
    # (This would use mocking in actual test)
    assert sns_publish_called_with(
        TopicArn=TOPIC_ARN,
        MessageAttributes={"recoveryPlanId": plan_id, "eventType": event_type}
    )
```

#### 7.3 Pause/Resume Properties

**Property 8: Task Token Callback Success**
```python
@given(task_token=valid_task_token_strategy())
def test_resume_callback_succeeds(task_token):
    """
    Property: Valid task token allows resume callback.
    
    Validates: Requirements 6.1, 6.2
    """
    # Resume execution
    result = resume_execution(task_token)
    
    # Verify SendTaskSuccess was called
    assert stepfunctions_send_task_success_called_with(
        taskToken=task_token,
        output=contains({"action": "resume"})
    )
```

**Property 9: Task Token Callback Failure**
```python
@given(task_token=valid_task_token_strategy())
def test_cancel_callback_succeeds(task_token):
    """
    Property: Valid task token allows cancel callback.
    
    Validates: Requirements 6.3, 6.4
    """
    # Cancel execution
    result = cancel_execution(task_token)
    
    # Verify SendTaskFailure was called
    assert stepfunctions_send_task_failure_called_with(
        taskToken=task_token,
        error="ExecutionCancelled"
    )
```

**Property 10: Invalid Task Token Rejection**
```python
@given(task_token=st.text())
def test_invalid_task_token_rejected(task_token):
    """
    Property: Invalid task tokens are rejected.
    
    Validates: Requirements 6.5
    """
    assume(not is_valid_task_token_format(task_token))
    
    # Attempt resume with invalid token
    with pytest.raises(ValueError):
        resume_execution(task_token)
    
    # Attempt cancel with invalid token
    with pytest.raises(ValueError):
        cancel_execution(task_token)
```



### 8. Testing Strategy

#### 8.1 Unit Tests

**Frontend Tests**:
- `AccountContext.test.tsx`: Test account context provider
- `CreateProtectionGroupForm.test.tsx`: Test form validation and submission
- `CreateRecoveryPlanForm.test.tsx`: Test account consistency validation and notification email

**Backend Tests**:
- `test_account_utils.py`: Test invocation source detection and account context validation
- `test_notifications.py`: Test SNS subscription management
- `test_execution_handler.py`: Test pause/resume callbacks (extend existing)

**Test Coverage Target**: 90% for new code

#### 8.2 Integration Tests

**Test Scenarios**:

1. **Recovery Plan Creation with Notification**:
   - Create Recovery Plan with notification email
   - Verify DynamoDB item has accountId and notificationEmail
   - Verify SNS subscription created
   - Verify confirmation email sent

2. **Recovery Plan Creation with Account Validation**:
   - Create Protection Groups in different accounts
   - Attempt to create Recovery Plan with mixed accounts
   - Verify validation error returned

3. **Execution with Pause/Resume**:
   - Start execution with pause enabled
   - Verify pause notification sent with action links
   - Click resume link
   - Verify execution continues

4. **Direct Lambda Invocation**:
   - Invoke Lambda directly without API Gateway
   - Verify accountId required in payload
   - Verify error if accountId missing

#### 8.3 End-to-End Tests

**Test Flow 1: Complete Execution with Notifications**:
```
1. Create Protection Group
2. Create Recovery Plan with notification email
3. Confirm SNS subscription via email
4. Start execution
5. Verify start notification received
6. Wait for completion
7. Verify completion notification received
```

**Test Flow 2: Pause and Resume**:
```
1. Create Protection Group
2. Create Recovery Plan with notification email and pause enabled
3. Confirm SNS subscription via email
4. Start execution
5. Verify pause notification with action buttons
6. Click "Resume Execution" link
7. Verify execution continues
8. Verify completion notification received
```

**Test Flow 3: Export and Import**:
```
1. Create Protection Group with accountId
2. Create Recovery Plan
3. Export configuration
4. Verify JSON includes accountId for all resources
5. Import configuration in new environment
6. Verify accountId preserved
```

#### 8.4 Property-Based Tests

**Test Generators**:

```python
# Hypothesis strategies for property-based testing

@st.composite
def protection_group_strategy(draw):
    """Generate valid Protection Group data."""
    return {
        "groupName": draw(st.text(min_size=1, max_size=255)),
        "accountId": draw(st.from_regex(r"^\d{12}$")),
        "sourceServerIds": draw(st.lists(st.from_regex(r"^s-[a-f0-9]{17}$"), min_size=1))
    }

@st.composite
def recovery_plan_strategy(draw):
    """Generate valid Recovery Plan data."""
    return {
        "planName": draw(st.text(min_size=1, max_size=255)),
        "accountId": draw(st.from_regex(r"^\d{12}$")),
        "notificationEmail": draw(st.emails()),
        "waves": draw(st.lists(st.dictionaries(
            keys=st.sampled_from(["waveNumber", "protectionGroupId", "pauseBeforeExecution"]),
            values=st.one_of(st.integers(min_value=1), st.uuids(), st.booleans())
        ), min_size=1))
    }

@st.composite
def api_gateway_event_strategy(draw):
    """Generate API Gateway event."""
    return {
        "requestContext": {
            "requestId": draw(st.uuids()).hex,
            "apiId": draw(st.text(min_size=10, max_size=10)),
            "identity": {
                "cognitoIdentityId": draw(st.uuids()).hex
            }
        },
        "body": json.dumps({
            "groupName": draw(st.text(min_size=1, max_size=255))
        })
    }

@st.composite
def direct_lambda_event_strategy(draw):
    """Generate direct Lambda invocation event."""
    include_account = draw(st.booleans())
    body = {"groupName": draw(st.text(min_size=1, max_size=255))}
    
    if include_account:
        body["accountId"] = draw(st.from_regex(r"^\d{12}$"))
    
    return {"body": json.dumps(body)}

@st.composite
def valid_task_token_strategy(draw):
    """Generate valid Step Functions task token."""
    # Task tokens are base64-encoded JSON
    # Simplified for testing
    return draw(st.text(min_size=100, max_size=500))
```

#### 8.5 Security Tests

**Test Cases**:

1. **SQL Injection Prevention**:
   - Test with malicious input in groupName, description
   - Verify sanitization applied

2. **XSS Prevention**:
   - Test with script tags in notification emails
   - Verify HTML escaping applied

3. **Task Token Tampering**:
   - Test with modified task tokens
   - Verify rejection by Step Functions

4. **Email Validation Bypass**:
   - Test with invalid email formats
   - Verify validation catches all invalid formats

#### 8.6 Performance Tests

**Load Testing**:
- 100 concurrent Protection Group creations
- 50 concurrent Recovery Plan executions
- 1000 notifications per minute

**Latency Requirements**:
- Protection Group creation: < 500ms
- Recovery Plan creation: < 1s
- Notification delivery: < 30s
- Callback processing: < 200ms



### 9. Deployment Strategy

#### 9.1 Phased Rollout

**Phase 1: Infrastructure Updates (Week 1)**
- Deploy CloudFormation changes (IAM permissions, API Gateway callback endpoint)
- Update existing Lambda environment variables (SNS topic ARN, API Gateway URL)
- No new Lambda functions — all changes extend existing handlers
- No functional changes yet

**Phase 2: Backend Implementation (Week 2)**
- Deploy updated Lambda handlers with account context validation
- Deploy SNS subscription management (in `notifications.py`)
- Deploy notification publishing (in `notifications.py`)
- Run backfill scripts for existing data

**Phase 3: Frontend Updates (Week 3)**
- Deploy frontend with account context auto-population
- Deploy Recovery Plan form with notification email field
- Deploy Recovery Plan form with account validation

**Phase 4: Pause/Resume Feature (Week 4)**
- Deploy Step Functions state machine updates
- Deploy pause notification handler (in `dr-orchestration-stepfunction`)
- Deploy callback handler (in `execution-handler`)
- Enable pause feature for new executions

**Phase 5: Validation and Monitoring (Week 5)**
- Monitor notification delivery rates
- Monitor callback success rates
- Validate data consistency
- Performance testing

#### 9.2 Deployment Commands

**Deploy to Test Environment**:
```bash
# Full deployment
./scripts/deploy.sh test

# Backend only (Lambda + CloudFormation)
./scripts/deploy.sh test --lambda-only

# Frontend only
./scripts/deploy.sh test --frontend-only

# Validation only (no deployment)
./scripts/deploy.sh test --validate-only
```

**Run Backfill Scripts**:
```bash
# Activate Python virtual environment
source .venv/bin/activate

# Backfill Protection Groups (dry run)
python scripts/backfill-protection-groups.py \
  --table hrp-drs-tech-adapter-protection-groups-dev

# Backfill Protection Groups (apply)
python scripts/backfill-protection-groups.py \
  --table hrp-drs-tech-adapter-protection-groups-dev \
  --apply

# Backfill Recovery Plans (dry run)
python scripts/backfill-recovery-plans.py \
  --plans-table hrp-drs-tech-adapter-recovery-plans-dev \
  --groups-table hrp-drs-tech-adapter-protection-groups-dev

# Backfill Recovery Plans (apply)
python scripts/backfill-recovery-plans.py \
  --plans-table hrp-drs-tech-adapter-recovery-plans-dev \
  --groups-table hrp-drs-tech-adapter-protection-groups-dev \
  --apply
```

#### 9.3 Deployment Verification

**Post-Deployment Checks**:

1. **CloudFormation Stack Status**:
```bash
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name hrp-drs-tech-adapter-dev \
  --query 'Stacks[0].StackStatus'
```

2. **Lambda Function Updates**:
```bash
AWS_PAGER="" aws lambda get-function \
  --function-name hrp-drs-tech-adapter-data-management-handler-dev \
  --query 'Configuration.LastModified'
```

3. **DynamoDB Schema Verification**:
```bash
AWS_PAGER="" aws dynamodb scan \
  --table-name hrp-drs-tech-adapter-protection-groups-dev \
  --limit 1 \
  --query 'Items[0]'
```

4. **SNS Topic Configuration**:
```bash
AWS_PAGER="" aws sns list-subscriptions-by-topic \
  --topic-arn $(aws cloudformation describe-stacks \
    --stack-name hrp-drs-tech-adapter-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`ExecutionNotificationsTopicArn`].OutputValue' \
    --output text)
```

5. **API Gateway Endpoint**:
```bash
curl -X GET "https://cbpdf7d52d.execute-api.us-east-2.amazonaws.com/dev/execution?action=resume&taskToken=test"
```

#### 9.4 Feature Flags

**Environment Variables for Gradual Rollout**:

```yaml
# Lambda Environment Variables
ENABLE_ACCOUNT_CONTEXT_VALIDATION: "true"
ENABLE_NOTIFICATION_PUBLISHING: "true"
ENABLE_PAUSE_RESUME: "true"
REQUIRE_ACCOUNT_ID_FOR_DIRECT_INVOCATION: "true"
```

**Feature Flag Strategy**:
- Start with all flags disabled in production
- Enable one feature at a time
- Monitor for 24 hours before enabling next feature
- Rollback if error rate exceeds 1%

#### 9.5 Monitoring and Alerts

**CloudWatch Metrics**:
- `ProtectionGroupCreationCount`: Count of Protection Groups created
- `RecoveryPlanCreationCount`: Count of Recovery Plans created
- `NotificationDeliverySuccess`: Count of successful notifications
- `NotificationDeliveryFailure`: Count of failed notifications
- `CallbackSuccessCount`: Count of successful pause/resume callbacks
- `CallbackFailureCount`: Count of failed callbacks
- `AccountValidationErrors`: Count of account validation failures

**CloudWatch Alarms**:
```yaml
NotificationFailureAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub ${ProjectName}-notification-failures-${Environment}
    MetricName: NotificationDeliveryFailure
    Namespace: DRSOrchestration
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 10
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref AlertTopic

CallbackFailureAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub ${ProjectName}-callback-failures-${Environment}
    MetricName: CallbackFailureCount
    Namespace: DRSOrchestration
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref AlertTopic
```

**Log Insights Queries**:

```sql
-- Account validation errors
fields @timestamp, @message
| filter @message like /account.*validation.*error/i
| sort @timestamp desc
| limit 100

-- Notification delivery failures
fields @timestamp, @message
| filter @message like /notification.*failed/i
| stats count() by bin(5m)

-- Callback processing times
fields @timestamp, @message, @duration
| filter @message like /callback.*processed/i
| stats avg(@duration), max(@duration), min(@duration)
```

