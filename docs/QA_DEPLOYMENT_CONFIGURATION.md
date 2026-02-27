# QA Environment Deployment Configuration

**Document Version**: 1.0  
**Last Updated**: 2026-02-27  
**Environment**: QA  
**Stack Name**: `aws-drs-orchestration-qa`  
**Region**: us-east-2  
**Account**: 438465159935

## Table of Contents

1. [Overview](#overview)
2. [Stack Configuration](#stack-configuration)
3. [Function-Specific IAM Roles](#function-specific-iam-roles)
4. [Infrastructure Components](#infrastructure-components)
5. [Deployment Commands](#deployment-commands)
6. [Verification Results Summary](#verification-results-summary)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Access and Authentication](#access-and-authentication)
9. [Troubleshooting](#troubleshooting)

## Overview

The QA environment is deployed with **function-specific IAM roles** enabled, implementing the principle of least privilege for all Lambda functions. This configuration represents the production-ready architecture with enhanced security controls.

### Key Features

- ✅ Function-specific IAM roles (5 dedicated roles)
- ✅ CloudWatch monitoring and alerting
- ✅ SNS notifications enabled
- ✅ EventBridge rule consolidation
- ✅ WAF disabled (region us-east-2, WAF requires us-east-1)
- ✅ 7-day log retention
- ✅ Email notifications to jocousen@amazon.com

## Stack Configuration

### CloudFormation Stack Details

| Parameter | Value |
|-----------|-------|
| **Stack Name** | aws-drs-orchestration-qa |
| **Region** | us-east-2 |
| **Account ID** | 438465159935 |
| **Stack Status** | UPDATE_COMPLETE |
| **Created** | 2026-02-26T14:35:18.496000+00:00 |
| **Last Updated** | 2026-02-27T02:14:49.731000+00:00 |

### Stack Parameters

```yaml
ProjectName: aws-drs-orchestration
Environment: qa
UseFunctionSpecificRoles: true
DeploymentBucket: aws-drs-orchestration-438465159935-qa
FrontendBuildVersion: 20260226-2114
AdminEmail: jocousen@amazon.com
```

### S3 Deployment Bucket

**Bucket Name**: `aws-drs-orchestration-438465159935-qa`

**Structure**:
```
s3://aws-drs-orchestration-438465159935-qa/
├── cfn/                    # CloudFormation templates
├── lambda/                 # Lambda deployment packages
└── frontend/               # Frontend build artifacts
```

## Function-Specific IAM Roles

The QA environment implements five dedicated IAM roles, each scoped to specific Lambda function responsibilities:

### 1. Query Handler Role

**Role ARN**: `arn:aws:iam::438465159935:role/aws-drs-orchestration-query-handler-role-qa`

**Permissions**:
- DynamoDB: Read-only (GetItem, Query, Scan, BatchGetItem)
- DRS: Describe* operations (read-only)
- EC2: Describe* operations (read-only)
- CloudWatch: Metrics (GetMetricData, PutMetricData)
- Lambda: InvokeFunction (execution-handler only)
- STS: AssumeRole (with ExternalId condition)

**Security Boundaries**:
- ❌ Cannot write to DynamoDB
- ❌ Cannot start DRS recovery operations
- ❌ Cannot execute Step Functions

### 2. Data Management Handler Role

**Role ARN**: `arn:aws:iam::438465159935:role/aws-drs-orchestration-data-management-role-qa`

**Permissions**:
- DynamoDB: Full CRUD operations
- DRS: Describe*, TagResource, UntagResource, CreateExtendedSourceServer
- Lambda: InvokeFunction (self-invocation)
- EventBridge: DescribeRule, PutRule
- STS: AssumeRole (with ExternalId condition)

**Security Boundaries**:
- ❌ Cannot start DRS recovery operations
- ❌ Cannot terminate recovery instances
- ❌ Cannot execute Step Functions

### 3. Execution Handler Role

**Role ARN**: `arn:aws:iam::438465159935:role/aws-drs-orchestration-execution-handler-role-qa`

**Permissions**:
- DynamoDB: Full CRUD operations
- DRS: Full recovery operations (StartRecovery, TerminateRecoveryInstances, CreateRecoveryInstanceForDrs)
- EC2: Full instance operations (RunInstances, TerminateInstances, CreateLaunchTemplate)
- Step Functions: SendTaskSuccess, SendTaskFailure
- SNS: Publish
- STS: AssumeRole (with ExternalId condition)

**Security Boundaries**:
- ✅ Full DRS recovery permissions (authorized for recovery operations)
- ✅ EC2 operations for recovery instance management

### 4. Orchestration Role

**Role ARN**: `arn:aws:iam::438465159935:role/aws-drs-orchestration-orchestration-role-qa`

**Permissions**:
- Step Functions: StartExecution, DescribeExecution
- Lambda: InvokeFunction (all project functions)
- CloudWatch: Logs and Metrics
- DynamoDB: Read-only operations

**Security Boundaries**:
- ❌ Cannot perform DRS operations directly
- ❌ Cannot write to DynamoDB

### 5. Frontend Deployer Role

**Role ARN**: `arn:aws:iam::438465159935:role/aws-drs-orchestration-frontend-deployer-role-qa`

**Permissions**:
- S3: Full access to frontend bucket only
- CloudFront: CreateInvalidation, GetInvalidation
- CloudFormation: DescribeStacks (read-only)
- CloudWatch: PutMetricData

**Security Boundaries**:
- ❌ No DynamoDB access
- ❌ No DRS access
- ❌ No Lambda invocation permissions

## Infrastructure Components

### API Gateway

**API Endpoint**: `https://vsz2tr3950.execute-api.us-east-2.amazonaws.com/qa`

**Features**:
- Cognito authentication
- Request validation
- CORS enabled
- CloudWatch access logging

### Lambda Functions

| Function | ARN | Role |
|----------|-----|------|
| Query Handler | arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-query-handler-qa | QueryHandlerRole |
| Data Management | arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-data-management-handler-qa | DataManagementRole |
| Execution Handler | arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-execution-handler-qa | ExecutionHandlerRole |
| DR Orchestration | arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-dr-orch-sf-qa | OrchestrationRole |
| Frontend Deployer | arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-frontend-deployer-qa | FrontendDeployerRole |

### Step Functions

**State Machine ARN**: `arn:aws:states:us-east-2:438465159935:stateMachine:aws-drs-orchestration-orchestration-qa`

**Features**:
- Wave-based recovery orchestration
- Pause/resume capability
- State ownership pattern
- CloudWatch Logs integration

### DynamoDB Tables

| Table | Purpose |
|-------|---------|
| aws-drs-orchestration-protection-groups-qa | Protection group definitions |
| aws-drs-orchestration-recovery-plans-qa | Recovery plan configurations |
| aws-drs-orchestration-execution-history-qa | Execution tracking and history |

### CloudFront Distribution

**Domain**: `d2cbda60q0i38a.cloudfront.net`  
**URL**: `https://d2cbda60q0i38a.cloudfront.net`

**Features**:
- S3 origin (frontend bucket)
- HTTPS only
- WAF: Not enabled (requires us-east-1)

### Cognito

**User Pool ID**: `us-east-2_HuKd2h8UN`  
**User Pool Client ID**: `7ka8cve8i15ulkm75uqdhmtne`  
**Identity Pool ID**: `us-east-2:69e5c3a7-0b12-45a1-bc84-ba296e532a98`

### SNS Topics

| Topic | ARN | Purpose |
|-------|-----|---------|
| Execution Notifications | arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-execution-notifications-qa | DR execution events |
| DRS Operational Alerts | arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-drs-alerts-qa | DRS alerts and security events |
| Execution Pause | arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-execution-pause-qa | Pause notifications |

**Email Subscriptions**: All topics subscribed to `jocousen@amazon.com` (confirmed)

## Deployment Commands

### Initial Deployment

```bash
# Deploy QA stack with function-specific roles
./scripts/deploy-main-stack.sh qa \
  --use-function-specific-roles \
  --admin-email jocousen@amazon.com
```

### Update Deployment

```bash
# Full stack update
./scripts/deploy-main-stack.sh qa

# Lambda-only update
./scripts/deploy-main-stack.sh qa --lambda-only

# Frontend-only update
./scripts/deploy-main-stack.sh qa --frontend-only
```

### Verification Commands

```bash
# Check stack status
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2 \
  --query 'Stacks[0].StackStatus'

# List Lambda functions
AWS_PAGER="" aws lambda list-functions \
  --region us-east-2 \
  --query 'Functions[?contains(FunctionName, `qa`)].{Name:FunctionName,Role:Role}'

# Check CloudWatch alarms
AWS_PAGER="" aws cloudwatch describe-alarms \
  --region us-east-2 \
  --alarm-name-prefix aws-drs-orchestration \
  --query 'MetricAlarms[?contains(AlarmName, `qa`)].{Name:AlarmName,State:StateValue}'
```

## Verification Results Summary

### Task 19.4: Lambda Function Role Verification

**Status**: ✅ PASSED

All Lambda functions correctly configured with function-specific IAM roles:
- Query Handler → QueryHandlerRole ✅
- Data Management → DataManagementRole ✅
- Execution Handler → ExecutionHandlerRole ✅
- DR Orchestration → OrchestrationRole ✅
- Frontend Deployer → FrontendDeployerRole ✅

### Task 19.6: SNS Notification Verification

**Status**: ✅ PASSED

- 3 SNS topics configured
- All email subscriptions confirmed
- Test alarm successfully triggered and reset
- Notifications delivered to jocousen@amazon.com

### Task 19.8: Negative Security Tests

**Status**: ✅ PASSED

Security boundaries validated via IAM policy analysis:
- Query Handler: Cannot write to DynamoDB ✅
- Query Handler: Cannot start DRS recovery ✅
- Data Management: Cannot execute recovery operations ✅
- Frontend Deployer: No DRS access ✅
- Frontend Deployer: No DynamoDB access ✅

### Task 19.9: Monitoring and Alerting Verification

**Status**: ✅ PASSED

- CloudWatch Log Groups: 6 log groups with 7-day retention ✅
- Metric Filters: 5 AccessDenied filters configured ✅
- CloudWatch Alarms: 5 alarms monitoring security events ✅
- SNS Integration: All alarms publish to drs-alerts-qa topic ✅
- Real-time Monitoring: Operational ✅

### Task 19.10: EventBridge Rules Verification

**Status**: ✅ PASSED

- ExecutionPollingScheduleRule exists and enabled ✅
- Schedule: rate(1 minute) ✅
- Target: ExecutionHandlerFunction with correct input ✅
- No duplicate ExecutionFinderScheduleRule ✅
- Rule consolidation successfully implemented ✅

## Monitoring and Alerting

### CloudWatch Alarms

All Lambda functions have CloudWatch Alarms monitoring for AccessDenied errors:

| Alarm | Threshold | Evaluation Period | SNS Action |
|-------|-----------|-------------------|------------|
| query-handler-access-denied-qa | ≥5 errors | 5 minutes | drs-alerts-qa |
| data-management-handler-access-denied-qa | ≥5 errors | 5 minutes | drs-alerts-qa |
| execution-handler-access-denied-qa | ≥5 errors | 5 minutes | drs-alerts-qa |
| dr-orch-sf-access-denied-qa | ≥5 errors | 5 minutes | drs-alerts-qa |
| frontend-deployer-access-denied-qa | ≥5 errors | 5 minutes | drs-alerts-qa |

### Metric Filters

Each Lambda function has a metric filter capturing AccessDenied errors:

**Filter Pattern**: `[..., msg="*AccessDenied*"]`  
**Metric Namespace**: `aws-drs-orchestration/Security`  
**Metric Name**: `AccessDeniedErrors`

### Log Retention

All Lambda function log groups configured with **7-day retention**:
- /aws/lambda/aws-drs-orchestration-query-handler-qa
- /aws/lambda/aws-drs-orchestration-data-management-handler-qa
- /aws/lambda/aws-drs-orchestration-execution-handler-qa
- /aws/lambda/aws-drs-orchestration-dr-orch-sf-qa
- /aws/lambda/aws-drs-orchestration-frontend-deployer-qa
- /aws/lambda/aws-drs-orchestration-deployment-orchestrator-qa

## Access and Authentication

### Cognito User Pool

**Admin User**: jocousen@amazon.com

**Authentication Flow**:
1. User authenticates via Cognito User Pool
2. Receives JWT ID token
3. Token used for API Gateway authorization
4. API Gateway validates token with Cognito authorizer

### API Access

```bash
# Get authentication token
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id 7ka8cve8i15ulkm75uqdhmtne \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=jocousen@amazon.com,PASSWORD=<password> \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Test API endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://vsz2tr3950.execute-api.us-east-2.amazonaws.com/qa/health
```

## Troubleshooting

### Common Issues

#### 1. AccessDenied Errors

**Symptom**: Lambda function logs show AccessDenied errors

**Diagnosis**:
```bash
# Check CloudWatch Logs
AWS_PAGER="" aws logs filter-log-events \
  --region us-east-2 \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-qa \
  --filter-pattern "AccessDenied" \
  --start-time $(($(date +%s) - 3600))000

# Check CloudWatch Alarms
AWS_PAGER="" aws cloudwatch describe-alarms \
  --region us-east-2 \
  --alarm-names aws-drs-orchestration-query-handler-access-denied-qa
```

**Resolution**: Review IAM role policies and ensure function has required permissions

#### 2. SNS Notification Not Received

**Symptom**: CloudWatch alarm triggered but no email received

**Diagnosis**:
```bash
# Check subscription status
AWS_PAGER="" aws sns list-subscriptions-by-topic \
  --region us-east-2 \
  --topic-arn arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-drs-alerts-qa

# Check subscription confirmation
AWS_PAGER="" aws sns get-subscription-attributes \
  --subscription-arn <subscription-arn> \
  --region us-east-2 \
  --query 'Attributes.PendingConfirmation'
```

**Resolution**: Confirm SNS subscription via email link

#### 3. Lambda Function Not Using Correct Role

**Symptom**: Function using wrong IAM role

**Diagnosis**:
```bash
# Check Lambda function role
AWS_PAGER="" aws lambda get-function \
  --function-name aws-drs-orchestration-query-handler-qa \
  --region us-east-2 \
  --query 'Configuration.Role'
```

**Resolution**: Update CloudFormation stack with correct role ARN

### Support Contacts

**Admin Email**: jocousen@amazon.com  
**Stack Owner**: DR Orchestration Team  
**Region**: us-east-2  
**Account**: 438465159935

## Related Documentation

- [Function-Specific IAM Roles Design](.kiro/specs/function-specific-iam-roles/design.md)
- [Requirements Document](.kiro/specs/function-specific-iam-roles/requirements.md)
- [Task List](.kiro/specs/function-specific-iam-roles/tasks.md)
- [Deployment Guide](deployment-guide.md)
- [AWS Stack Protection](aws-stack-protection.md)

## Appendix: Stack Outputs

Complete list of CloudFormation stack outputs:

```json
{
  "ApiEndpoint": "https://vsz2tr3950.execute-api.us-east-2.amazonaws.com/qa",
  "CloudFrontDomain": "d2cbda60q0i38a.cloudfront.net",
  "CloudFrontUrl": "https://d2cbda60q0i38a.cloudfront.net",
  "DataManagementHandlerFunctionArn": "arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-data-management-handler-qa",
  "DataManagementRoleArn": "arn:aws:iam::438465159935:role/aws-drs-orchestration-data-management-role-qa",
  "DRSOperationalAlertsTopicArn": "arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-drs-alerts-qa",
  "ExecutionHandlerFunctionArn": "arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-execution-handler-qa",
  "ExecutionHandlerRoleArn": "arn:aws:iam::438465159935:role/aws-drs-orchestration-execution-handler-role-qa",
  "ExecutionHistoryTableName": "aws-drs-orchestration-execution-history-qa",
  "ExecutionNotificationsTopicArn": "arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-execution-notifications-qa",
  "FrontendBucketName": "aws-drs-orchestration-fe-438465159935-qa",
  "FrontendDeployerFunctionArn": "arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-frontend-deployer-qa",
  "FrontendDeployerRoleArn": "arn:aws:iam::438465159935:role/aws-drs-orchestration-frontend-deployer-role-qa",
  "IdentityPoolId": "us-east-2:69e5c3a7-0b12-45a1-bc84-ba296e532a98",
  "OrchestrationFunctionArn": "arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-dr-orch-sf-qa",
  "OrchestrationRoleArn": "arn:aws:iam::438465159935:role/aws-drs-orchestration-orchestration-role-qa",
  "ProtectionGroupsTableName": "aws-drs-orchestration-protection-groups-qa",
  "QueryHandlerFunctionArn": "arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-query-handler-qa",
  "QueryHandlerRoleArn": "arn:aws:iam::438465159935:role/aws-drs-orchestration-query-handler-role-qa",
  "RecoveryPlansTableName": "aws-drs-orchestration-recovery-plans-qa",
  "StackStatus": "Deployed",
  "StateMachineArn": "arn:aws:states:us-east-2:438465159935:stateMachine:aws-drs-orchestration-orchestration-qa",
  "UserPoolClientId": "7ka8cve8i15ulkm75uqdhmtne",
  "UserPoolId": "us-east-2_HuKd2h8UN"
}
```

---

**Document Status**: Complete  
**Verification Date**: 2026-02-27  
**Next Review**: Before production deployment
