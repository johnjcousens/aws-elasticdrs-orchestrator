# Lambda Security Implementation Plan & Rollback Strategy

## Executive Summary

**Objective**: Implement security standards compliance across all Lambda functions while maintaining system stability and providing safe rollback procedures.

**Risk Level**: MEDIUM - Changes affect core orchestration logic  
**Rollback Strategy**: Git-based with automated testing validation  
**Implementation Approach**: Incremental with validation at each step

## Current State Analysis

### Compliance Status
- **api-handler**: ✅ Fully compliant (reference implementation)
- **orchestration-stepfunctions**: ❌ CRITICAL - Zero security implementation
- **execution-finder**: ⚠️ Partial - Missing comprehensive security
- **execution-poller**: ⚠️ Partial - Conditional security implementation
- **frontend-builder**: ⚠️ Partial - Limited security scope
- **notification-formatter**: ⚠️ Partial - Basic security only
- **bucket-cleaner**: ✅ N/A - CloudFormation custom resource

### Risk Assessment

| Function | Risk Level | Impact if Broken | Rollback Complexity |
|----------|------------|------------------|-------------------|
| orchestration-stepfunctions | 🔴 HIGH | Complete execution failure | Medium |
| execution-finder | 🟡 MEDIUM | Polling system failure | Low |
| execution-poller | 🟡 MEDIUM | Status update failure | Low |
| frontend-builder | 🟢 LOW | Deployment failure only | Low |
| notification-formatter | 🟢 LOW | Notification failure only | Low |

## Implementation Strategy

### Phase 1: Preparation & Backup (MANDATORY)

#### 1.1 Create Implementation Branch
```bash
# Create feature branch for security implementation
git checkout -b feature/lambda-security-compliance
git push -u origin feature/lambda-security-compliance
```

#### 1.2 Backup Current Working State
```bash
# Tag current working state for easy rollback
git tag -a v1.3.0-pre-security-fixes -m "Backup before Lambda security implementation"
git push origin v1.3.0-pre-security-fixes

# Create backup of critical files
mkdir -p backup/lambda-functions
cp -r lambda/ backup/lambda-functions/
```

#### 1.3 Validate Current System Health
```bash
# Test current system functionality
curl -H "Authorization: Bearer $TOKEN" "https://***REMOVED***.execute-api.us-east-1.amazonaws.com/dev/health"

# Verify execution polling is working
curl -H "Authorization: Bearer $TOKEN" "https://***REMOVED***.execute-api.us-east-1.amazonaws.com/dev/executions"
```

### Phase 2: Low-Risk Functions First

#### 2.1 notification-formatter (Lowest Risk)

**Current Issues**:
- Limited security utilities usage
- No comprehensive input validation

**Implementation**:
```python
# Enhanced security imports
from shared.security_utils import (
    create_response_with_security_headers,
    log_security_event,
    safe_aws_client_call,
    sanitize_string_input,
    validate_event_structure,  # New function to add
)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # Enhanced security logging
        log_security_event(
            "notification_formatter_invoked",
            {
                "function_name": context.function_name,
                "request_id": context.aws_request_id,
                "event_source": event.get("source", "unknown"),
                "event_detail_type": event.get("detail-type", "unknown"),
            },
        )

        # Input validation and sanitization
        detail = event.get("detail", {})
        source = sanitize_string_input(event.get("source", ""))
        detail_type = sanitize_string_input(event.get("detail-type", ""))
        
        # Validate EventBridge event structure
        if not source or not detail_type:
            log_security_event("invalid_eventbridge_event", {
                "missing_source": not source,
                "missing_detail_type": not detail_type
            })
            return create_response_with_security_headers(
                400, {"error": "Invalid EventBridge event structure"}
            )

        # Continue with existing logic...
```

**Rollback Plan**:
```bash
# If notification-formatter breaks
git checkout HEAD~1 -- lambda/notification-formatter/index.py
./scripts/sync-to-deployment-bucket.sh --update-lambda-code
```

#### 2.2 frontend-builder (Low Risk)

**Current Issues**:
- Limited security validation scope
- Could enhance file path validation

**Implementation**:
```python
# Enhanced security for CloudFormation custom resource
from shared.security_utils import (
    log_security_event,
    safe_aws_client_call,
    sanitize_string_input,
    validate_file_path,
    validate_cloudformation_event,  # New function to add
)

@helper.create
@helper.update
def create_or_update(event, context):
    try:
        # Enhanced CloudFormation event validation
        properties = event["ResourceProperties"]
        
        # Validate and sanitize all CloudFormation inputs
        bucket_name = sanitize_string_input(properties["BucketName"])
        distribution_id = sanitize_string_input(properties["DistributionId"])
        
        # Enhanced security logging
        log_security_event(
            "frontend_deployment_started",
            {
                "bucket_name": bucket_name,
                "distribution_id": distribution_id,
                "request_id": context.aws_request_id,
                "stack_id": event.get("StackId", "unknown"),
            },
        )

        # Continue with existing logic...
```

### Phase 3: Medium-Risk Background Services

#### 3.1 execution-finder (Medium Risk)

**Current Issues**:
- Limited security utilities usage
- No input validation for EventBridge events

**Implementation**:
```python
# Enhanced security imports
from shared.security_utils import (
    log_security_event,
    sanitize_string_input,
    validate_dynamodb_input,
    safe_aws_client_call,
    validate_eventbridge_event,  # New function to add
)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # Enhanced security logging
        log_security_event(
            "execution_finder_invoked",
            {
                "function_name": context.function_name,
                "event_source": event.get("source", "eventbridge"),
                "context_request_id": context.aws_request_id,
                "event_detail_type": event.get("detail-type", "Scheduled Event"),
            },
        )

        # Validate EventBridge event structure
        if not validate_eventbridge_event(event):
            log_security_event("invalid_eventbridge_event", {"event_keys": list(event.keys())})
            return {"statusCode": 400, "body": "Invalid EventBridge event"}

        # Enhanced DynamoDB operations with safety
        def query_polling_executions_safe():
            return query_polling_executions()

        polling_executions = safe_aws_client_call(query_polling_executions_safe)

        # Continue with existing logic...
```

**Rollback Plan**:
```bash
# If execution-finder breaks (affects polling system)
git checkout HEAD~1 -- lambda/execution-finder/index.py
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Verify polling system recovery
aws logs tail /aws/lambda/aws-elasticdrs-orchestrator-execution-finder-dev --since 5m
```

#### 3.2 execution-poller (Medium Risk)

**Current Issues**:
- Conditional security implementation
- Should be mandatory, not optional

**Implementation**:
```python
# Remove conditional imports - make security mandatory
from shared.security_utils import (
    create_response_with_security_headers,
    log_security_event,
    safe_aws_client_call,
    sanitize_string_input,
    validate_dynamodb_input,
)

# Remove SECURITY_ENABLED flag - always use security
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # Mandatory security logging
        log_security_event(
            "execution_poller_invoked",
            {
                "function_name": context.function_name,
                "request_id": context.aws_request_id,
                "event_keys": list(event.keys()) if event else [],
            },
        )

        # Mandatory input validation and sanitization
        execution_id = sanitize_string_input(event.get("ExecutionId", ""))
        plan_id = sanitize_string_input(event.get("PlanId", ""))
        
        if not execution_id or not plan_id:
            log_security_event(
                "invalid_input_detected",
                {
                    "error": "Missing required parameters",
                    "execution_id": bool(execution_id),
                    "plan_id": bool(plan_id),
                },
            )
            return create_response_with_security_headers(
                400, {"error": "Missing required parameters: ExecutionId and PlanId"}
            )

        # Continue with existing logic but remove all SECURITY_ENABLED conditionals...
```

### Phase 4: High-Risk Critical Function

#### 4.1 orchestration-stepfunctions (HIGHEST RISK)

**Current Issues**:
- ZERO security implementation
- Handles critical Step Functions orchestration
- Direct AWS API calls without validation

**Implementation Strategy**: Incremental with extensive testing

**Step 4.1.1: Add Basic Security Infrastructure**
```python
# Add security imports at top of file
from shared.security_utils import (
    log_security_event,
    sanitize_string_input,
    sanitize_dynamodb_input,
    validate_dynamodb_input,
    safe_aws_client_call,
)

def lambda_handler(event, context):
    """Step Functions orchestration handler with security"""
    try:
        # Security logging
        log_security_event(
            "stepfunctions_orchestration_invoked",
            {
                "function_name": context.function_name,
                "request_id": context.aws_request_id,
                "action": event.get("action", "unknown"),
                "execution_id": event.get("execution_id", "unknown"),
            },
        )

        # Input validation
        action = event.get("action")
        if not action or not isinstance(action, str):
            log_security_event("invalid_stepfunctions_action", {"action": action})
            raise ValueError("Invalid or missing action parameter")

        # Sanitize the entire event
        sanitized_event = sanitize_dynamodb_input(event)
        
        # Continue with existing logic using sanitized_event...
```

**Step 4.1.2: Secure DynamoDB Operations**
```python
# Replace direct DynamoDB calls with safe wrappers
def get_protection_groups_table():
    global _protection_groups_table
    if _protection_groups_table is None:
        _protection_groups_table = dynamodb.Table(PROTECTION_GROUPS_TABLE)
    return _protection_groups_table

# Secure table operations
def safe_get_protection_group(group_id: str):
    """Safely get protection group with validation"""
    validate_dynamodb_input("GroupId", group_id)
    group_id = sanitize_string_input(group_id)
    
    def get_operation():
        return get_protection_groups_table().get_item(Key={"GroupId": group_id})
    
    return safe_aws_client_call(get_operation)
```

**Step 4.1.3: Secure DRS Operations**
```python
# Secure DRS client creation and operations
def create_drs_client_safe(region: str, account_context: Dict = None):
    """Create DRS client with input validation"""
    region = sanitize_string_input(region)
    
    # Validate region format
    if not re.match(r'^[a-z]{2}-[a-z]+-\d{1}$', region):
        raise ValueError(f"Invalid AWS region format: {region}")
    
    log_security_event("drs_client_creation", {
        "region": region,
        "cross_account": bool(account_context)
    })
    
    return create_drs_client(region, account_context)

# Secure DRS operations
def start_wave_recovery_safe(state: Dict, wave_number: int) -> None:
    """Start DRS recovery with comprehensive security"""
    try:
        # Validate inputs
        if not isinstance(state, dict):
            raise ValueError("Invalid state object")
        if not isinstance(wave_number, int) or wave_number < 0:
            raise ValueError("Invalid wave number")
        
        # Sanitize state
        state = sanitize_dynamodb_input(state)
        
        # Log security event
        log_security_event("wave_recovery_start", {
            "wave_number": wave_number,
            "execution_id": state.get("execution_id", "unknown"),
            "plan_id": state.get("plan_id", "unknown")
        })
        
        # Continue with existing logic...
```

**Rollback Plan for orchestration-stepfunctions**:
```bash
# CRITICAL: This function handles Step Functions - have multiple rollback options

# Option 1: Quick rollback (recommended)
git checkout HEAD~1 -- lambda/orchestration-stepfunctions/index.py
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Option 2: Full rollback to tagged version
git checkout v1.3.0-pre-security-fixes -- lambda/orchestration-stepfunctions/index.py
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Option 3: Emergency rollback with backup
cp backup/lambda-functions/orchestration-stepfunctions/index.py lambda/orchestration-stepfunctions/
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Verify Step Functions are working
aws stepfunctions list-executions --state-machine-arn $STATE_MACHINE_ARN --max-items 5
```

## Testing Strategy

### Pre-Implementation Testing
```bash
# 1. Verify current system health
curl -H "Authorization: Bearer $TOKEN" "https://***REMOVED***.execute-api.us-east-1.amazonaws.com/dev/health"

# 2. Test execution creation
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ExecutionType":"DRILL","InitiatedBy":"security-test"}' \
  "https://***REMOVED***.execute-api.us-east-1.amazonaws.com/dev/recovery-plans/test-plan/execute"

# 3. Verify polling system
aws logs tail /aws/lambda/aws-elasticdrs-orchestrator-execution-finder-dev --since 5m
```

### Post-Implementation Testing
```bash
# 1. Test each function individually
aws lambda invoke --function-name aws-elasticdrs-orchestrator-notification-formatter-dev \
  --payload '{"source":"test","detail-type":"test"}' response.json

# 2. Test Step Functions orchestration
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{"action":"begin","execution":"test-security","plan":{"PlanId":"test"}}'

# 3. Monitor CloudWatch logs for security events
aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-elasticdrs-orchestrator-orchestration-stepfunctions-dev \
  --filter-pattern "security_event" \
  --start-time $(date -d '5 minutes ago' +%s)000
```

## New Security Utilities to Add

### validate_eventbridge_event
```python
def validate_eventbridge_event(event: Dict[str, Any]) -> bool:
    """Validate EventBridge event structure"""
    required_fields = ["source", "detail-type", "detail"]
    return all(field in event for field in required_fields)
```

### validate_stepfunctions_event
```python
def validate_stepfunctions_event(event: Dict[str, Any]) -> bool:
    """Validate Step Functions event structure"""
    if "action" not in event:
        return False
    
    action = event["action"]
    if action == "begin":
        return "plan" in event and "execution" in event
    elif action in ["update_wave_status", "store_task_token", "resume_wave"]:
        return "execution_id" in event or "application" in event
    
    return False
```

### validate_cloudformation_event
```python
def validate_cloudformation_event(event: Dict[str, Any]) -> bool:
    """Validate CloudFormation custom resource event"""
    required_fields = ["RequestType", "ResourceProperties", "StackId", "RequestId"]
    return all(field in event for field in required_fields)
```

## Rollback Decision Matrix

| Scenario | Rollback Method | Recovery Time | Risk Level |
|----------|----------------|---------------|------------|
| Single function failure | `git checkout HEAD~1 -- lambda/function/` | < 5 minutes | Low |
| Multiple function failure | `git checkout feature-branch` | < 10 minutes | Medium |
| Step Functions broken | `git checkout v1.3.0-pre-security-fixes` | < 15 minutes | High |
| Complete system failure | Restore from backup + redeploy | < 30 minutes | Critical |

## Monitoring & Validation

### Security Event Monitoring
```bash
# Monitor security events across all functions
aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-elasticdrs-orchestrator-api-handler-dev \
  --filter-pattern "security_event" \
  --start-time $(date -d '1 hour ago' +%s)000

# Check for security violations
aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-elasticdrs-orchestrator-orchestration-stepfunctions-dev \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000
```

### System Health Validation
```bash
# Comprehensive system health check
./scripts/validate-system-health.sh

# Check execution polling system
curl -H "Authorization: Bearer $TOKEN" \
  "https://***REMOVED***.execute-api.us-east-1.amazonaws.com/dev/executions" | jq '.executions | length'

# Verify Step Functions state machine
aws stepfunctions describe-state-machine --state-machine-arn $STATE_MACHINE_ARN
```

## Implementation Timeline

### Day 1: Preparation
- [ ] Create feature branch
- [ ] Create backup tags
- [ ] Validate current system health
- [ ] Add new security utility functions

### Day 2: Low-Risk Functions
- [ ] Implement notification-formatter security
- [ ] Test and validate
- [ ] Implement frontend-builder security
- [ ] Test and validate

### Day 3: Medium-Risk Functions
- [ ] Implement execution-finder security
- [ ] Test polling system thoroughly
- [ ] Implement execution-poller security
- [ ] Validate execution status updates

### Day 4: High-Risk Function
- [ ] Implement orchestration-stepfunctions security (incremental)
- [ ] Extensive testing of Step Functions
- [ ] Monitor for any execution failures
- [ ] Performance validation

### Day 5: Integration & Validation
- [ ] Full system integration testing
- [ ] Security event monitoring validation
- [ ] Performance impact assessment
- [ ] Documentation updates

## Success Criteria

### Functional Requirements
- [ ] All Lambda functions implement security utilities
- [ ] No regression in existing functionality
- [ ] Security events properly logged
- [ ] Input validation working correctly

### Performance Requirements
- [ ] No significant latency increase (< 100ms per function)
- [ ] Memory usage increase < 10%
- [ ] No timeout issues

### Security Requirements
- [ ] All inputs validated and sanitized
- [ ] Security events logged for audit
- [ ] Safe AWS client calls implemented
- [ ] Error handling with security context

## Emergency Procedures

### If System Becomes Unstable
1. **Immediate**: Stop all deployments
2. **Assess**: Identify failing component
3. **Rollback**: Use appropriate rollback method from matrix
4. **Validate**: Confirm system recovery
5. **Investigate**: Analyze logs to identify root cause

### If Step Functions Fail
1. **Critical Priority**: Restore orchestration-stepfunctions immediately
2. **Use**: `git checkout v1.3.0-pre-security-fixes -- lambda/orchestration-stepfunctions/`
3. **Deploy**: `./scripts/sync-to-deployment-bucket.sh --update-lambda-code`
4. **Monitor**: AWS Step Functions console for execution recovery

### Communication Plan
- **Internal**: Slack notification for any rollbacks
- **Stakeholders**: Email notification for system-wide issues
- **Documentation**: Update incident log with lessons learned

This comprehensive plan ensures safe implementation of security standards while maintaining system stability and providing multiple rollback options for any issues that arise.