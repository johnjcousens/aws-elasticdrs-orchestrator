# Deployment Flexibility Guide

## Overview

The AWS DRS Orchestration Solution supports **3 flexible deployment modes** to accommodate different use cases, from standalone deployments to external platform integration.

This guide covers:
- Deployment mode selection
- Configuration parameters
- Use cases and scenarios
- Migration from existing deployments
- Troubleshooting

## Architecture Overview

### Full-Stack Architecture (Mode 1)

![AWS DRS Orchestration - Comprehensive Architecture](../architecture/AWS-DRS-Orchestration-Architecture-Comprehensive.png)

**Components**: CloudFront CDN, S3 Static Hosting, Cognito User Pool, API Gateway, 6 Lambda Functions, Step Functions, DynamoDB (4 tables), EventBridge, CloudWatch, SNS, AWS DRS, Cross-Account IAM Roles

### Backend-Only Architecture (Modes 2 & 3)

![AWS DRS Orchestration - Backend Only](../architecture/AWS-DRS-Orchestration-Backend-Only.png)

**Components**: Direct Lambda invocation via CLI/SDK, 6 Lambda Functions, Step Functions, DynamoDB (4 tables), EventBridge, CloudWatch, SNS, AWS DRS, Cross-Account IAM Roles

**Benefits**: 60% lower cost (no API Gateway), simpler architecture, native AWS authentication

## Deployment Modes

### Mode 1: Default Standalone (Full Stack)

**Configuration:**
- `OrchestrationRoleArn`: empty (default)
- `DeployFrontend`: true (default)

**What Gets Deployed:**
- ✅ Unified orchestration IAM role (consolidates individual roles)
- ✅ All 6 Lambda functions
- ✅ API Gateway (REST API)
- ✅ Frontend (S3 + CloudFront)
- ✅ DynamoDB tables
- ✅ Step Functions
- ✅ Cognito authentication

**Use Cases:**
- Standalone DRS orchestration deployment
- Complete self-contained solution
- Organizations not using external platforms
- Development and testing

**Deployment Command:**
```bash
# Default deployment (no parameter overrides needed)
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    DeploymentBucket=aws-drs-orchestration-dev
```

**Benefits:**
- ✅ Complete solution out-of-the-box
- ✅ Simplified IAM management (1 role vs. 7)
- ✅ Full frontend UI included
- ✅ No external dependencies

---

### Mode 2: API-Only Standalone

**Configuration:**
- `OrchestrationRoleArn`: empty (default)
- `DeployFrontend`: false

**What Gets Deployed:**
- ✅ Unified orchestration IAM role
- ✅ All 6 Lambda functions
- ✅ API Gateway (REST API)
- ❌ Frontend (S3 + CloudFront) - NOT deployed
- ✅ DynamoDB tables
- ✅ Step Functions
- ✅ Cognito authentication

**Use Cases:**
- Custom frontend development with Cognito RBAC API calls
- Direct Lambda invocation via AWS SDK/CLI (using OrchestrationRole)
- Microservices architecture with API Gateway
- API integration with existing systems
- Programmatic access with RBAC security

**Deployment Command:**
```bash
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    DeploymentBucket=aws-drs-orchestration-dev \
    DeployFrontend=false
```

**Benefits:**
- ✅ Full backend functionality
- ✅ API endpoint available for Cognito-authenticated custom UIs
- ✅ Direct Lambda invocation option with OrchestrationRole
- ✅ Reduced infrastructure costs (no S3/CloudFront)
- ✅ Flexible integration: API Gateway OR direct Lambda
- ✅ RBAC security with Cognito User Pool

**Integration Options:**

**Option A: Cognito-Authenticated API Calls (RBAC)**
```javascript
// Custom frontend calling DRS orchestration API with Cognito JWT
const response = await fetch(`${API_ENDPOINT}/protection-groups`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${cognitoJwtToken}`,
    'Content-Type': 'application/json'
  }
});
```

**Option B: Direct Lambda Invocation (OrchestrationRole)**
```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Direct invocation using OrchestrationRole permissions
response = lambda_client.invoke(
    FunctionName='drs-orch-data-management-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'operation': 'list_protection_groups',
        'parameters': {}
    })
)

result = json.loads(response['Payload'].read())
```

---

### Mode 3: Lambda-Only Integration (Direct Invocation)

**Configuration:**
- `OrchestrationRoleArn`: provided (External IAM role ARN)
- `DynamoDBTableArns`: provided (External DynamoDB table ARNs)
- `StateMachineArn`: provided (External Step Functions ARN)
- `DeployFrontend`: false
- `DeployAPI`: false
- `DeployDatabase`: false
- `DeployStepFunctions`: false

**What Gets Deployed:**
- ❌ Unified orchestration IAM role - NOT created (uses external role)
- ✅ 6 Lambda functions ONLY (configured for direct invocation)
- ❌ API Gateway - NOT deployed
- ❌ Frontend (S3 + CloudFront) - NOT deployed
- ❌ DynamoDB tables - NOT created (uses external tables)
- ❌ Step Functions - NOT created (uses external state machine)
- ❌ Cognito authentication - NOT deployed

**Use Cases:**
- External platform with existing DynamoDB tables and Step Functions
- Direct Lambda invocation via AWS SDK/CLI
- Microservices architecture with shared data layer
- Maximum cost optimization ($1-5/month for Lambda only)
- Integration with external orchestration systems

**Deployment Command:**
```bash
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-lambda-only \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    DeploymentBucket=aws-drs-orchestration-dev \
    OrchestrationRoleArn=arn:aws:iam::ACCOUNT_ID:role/ExternalOrchestrationRole \
    DynamoDBTableArns=arn:aws:dynamodb:REGION:ACCOUNT_ID:table/protection-groups,arn:aws:dynamodb:REGION:ACCOUNT_ID:table/recovery-plans,arn:aws:dynamodb:REGION:ACCOUNT_ID:table/execution-history,arn:aws:dynamodb:REGION:ACCOUNT_ID:table/target-accounts \
    StateMachineArn=arn:aws:states:REGION:ACCOUNT_ID:stateMachine:drs-orchestration \
    DeployFrontend=false \
    DeployAPI=false \
    DeployDatabase=false \
    DeployStepFunctions=false
```

**Benefits:**
- ✅ Minimal infrastructure footprint (Lambda functions only)
- ✅ Maximum cost optimization ($1-5/month)
- ✅ Shared data layer with external systems
- ✅ Direct Lambda invocation (no API Gateway overhead)
- ✅ Integration with existing orchestration platforms

**Direct Lambda Invocation Example:**
```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Invoke data-management-handler directly
response = lambda_client.invoke(
    FunctionName='drs-orch-data-management-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'operation': 'list_protection_groups',
        'parameters': {}
    })
)

result = json.loads(response['Payload'].read())
print(result)
```

**External Platform Integration Architecture:**
```
┌─────────────────────────────────────────────┐
│      External Platform                      │
│  ┌──────────────┬──────────────────────┐   │
│  │  DynamoDB    │  Step Functions      │   │
│  │  (4 tables)  │  (State Machine)     │   │
│  └──────┬───────┴──────────┬───────────┘   │
│         │                  │               │
│         │  ┌───────────────▼──────────┐    │
│         │  │  IAM Orchestration Role  │    │
│         │  └───────────────┬──────────┘    │
└─────────┼──────────────────┼───────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────┐
│   DRS Orchestration Lambda Functions        │
│   (Direct Invocation - No API Gateway)      │
│   - data-management-handler                 │
│   - execution-handler                       │
│   - query-handler                           │
│   - dr-orchestration-stepfunction           │
│   - frontend-deployer                       │
│   - notification-formatter                  │
└─────────────────────────────────────────────┘
```

---

## Deployment Mode Comparison

| Feature | Default | API-Only | Lambda-Only Integration |
|---------|---------|----------|----------|
| **IAM Role** | Created | Created | External Provided |
| **Lambda Functions** | ✅ | ✅ | ✅ |
| **API Gateway** | ✅ | ✅ | ❌ |
| **Frontend** | ✅ | ❌ | ❌ |
| **DynamoDB** | ✅ | ✅ | ❌ (External) |
| **Step Functions** | ✅ | ✅ | ❌ (External) |
| **Monthly Cost** | $12-40 | $8-30 | $1-5 |
| **Use Case** | Standalone | Custom UI / RBAC API | Direct Lambda Invocation |

---

## External Platform Role Requirements

When using Lambda-Only Integration (Mode 3), the external IAM role must include all permissions from the unified orchestration role.

### Required Permissions (16 Policies)

1. **DynamoDBAccess** - Table operations
2. **StepFunctionsAccess** - Execution management (includes `states:SendTaskHeartbeat`)
3. **DRSReadAccess** - DRS describe operations
4. **DRSWriteAccess** - DRS recovery operations (includes `drs:CreateRecoveryInstanceForDrs`)
5. **EC2Access** - Instance and launch template operations (includes `ec2:CreateLaunchTemplateVersion`)
6. **IAMAccess** - PassRole for DRS/EC2
7. **STSAccess** - Cross-account role assumption
8. **KMSAccess** - Encrypted volume operations
9. **CloudFormationAccess** - Stack operations
10. **S3Access** - Frontend bucket operations
11. **CloudFrontAccess** - Cache invalidation
12. **LambdaInvokeAccess** - Cross-function invocation
13. **EventBridgeAccess** - Schedule rule management
14. **SSMAccess** - Automation execution (includes `ssm:CreateOpsItem`)
15. **SNSAccess** - Notification publishing
16. **CloudWatchAccess** - Metrics and logging

### Managed Policy

- **AWSLambdaBasicExecutionRole** - CloudWatch Logs

### Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Complete External Platform Role Example

See the complete policy definitions in [master-template.yaml](../../cfn/master-template.yaml) (UnifiedOrchestrationRole resource).

**External Platform Role Creation (CloudFormation):**
```yaml
ExternalOrchestrationRole:
  Type: AWS::IAM::Role
  Properties:
    RoleName: ExternalOrchestrationRole
    AssumeRolePolicyDocument:
      Version: "2012-10-17"
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    Policies:
      # Copy all 16 policies from UnifiedOrchestrationRole
      # See master-template.yaml lines 127-388
```

---

## Migration from Existing Deployments

### Migrating from Individual Roles to Unified Role

If you have an existing deployment with individual IAM roles per Lambda, you can seamlessly migrate to the unified role architecture.

**Migration Process:**
1. Update stack with default parameters (no overrides needed)
2. CloudFormation automatically:
   - Creates UnifiedOrchestrationRole
   - Updates all 6 Lambda functions to use new role
   - Deletes 7 old individual roles
3. Zero downtime during migration
4. Automatic rollback on failure

**Migration Command:**
```bash
# Update stack with unified role (no parameter overrides needed)
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    DeploymentBucket=aws-drs-orchestration-dev
```

**Migration Timeline:**
- Create UnifiedOrchestrationRole: 30-60 seconds
- Update Lambda functions: 2-4 minutes
- Delete old roles: 1-2 minutes
- **Total: 5-10 minutes**
- **Downtime: 0 seconds**

**What Happens:**
```
Time T0: Old State
  - Each Lambda had its own IAM role

Time T1: Create UnifiedOrchestrationRole
  - New role created with all permissions
  - Old roles still in use

Time T2: Update Lambda Functions (rolling)
  - Functions updated one at a time
  - Each function operational during update
  - New invocations use new role immediately

Time T3: Delete Old Roles
  - All functions now use UnifiedOrchestrationRole
  - CloudFormation deletes old roles
  - Migration complete
```

**Rollback:**
If migration fails, CloudFormation automatically rolls back to previous state (individual roles).

---

## Parameter Reference

### OrchestrationRoleArn

**Type:** String  
**Default:** '' (empty)  
**Pattern:** `^(arn:aws:iam::[0-9]{12}:role/.+)?$`

**Description:**
Optional ARN of an existing orchestration role for all Lambda functions. If empty (default), the stack creates a unified role with all required permissions. If provided (e.g., from External Platform), all Lambdas use that role instead.

**Valid Values:**
- `''` (empty) - Creates unified role
- `arn:aws:iam::123456789012:role/ExternalOrchestrationRole` - Uses provided role

**Invalid Values:**
- `invalid-arn` - Not an ARN format
- `arn:aws:s3:::bucket` - Wrong service
- `arn:aws:iam::123:role/Role` - Invalid account ID

### DeployFrontend

**Type:** String  
**Default:** 'true'  
**Allowed Values:** 'true', 'false'

**Description:**
Set to 'false' to skip frontend deployment (S3, CloudFront, frontend-builder). Use 'false' for API-only deployments or External Platform integration.

**Valid Values:**
- `'true'` - Deploys frontend (default)
- `'false'` - Skips frontend deployment

---

## Stack Outputs

### Always Present Outputs (19 total)

These outputs are always present regardless of deployment mode:

1. **ApiEndpoint** - API Gateway endpoint URL (CRITICAL for integrations)
2. **OrchestrationRoleArn** - ARN of orchestration role (created or provided)
3. **ProtectionGroupsTableName** - DynamoDB table name
4. **RecoveryPlansTableName** - DynamoDB table name
5. **ExecutionHistoryTableName** - DynamoDB table name
6. **TargetAccountsTableName** - DynamoDB table name
7. **ProtectionGroupsTableArn** - DynamoDB table ARN
8. **RecoveryPlansTableArn** - DynamoDB table ARN
9. **ExecutionHistoryTableArn** - DynamoDB table ARN
10. **TargetAccountsTableArn** - DynamoDB table ARN
11. **DataManagementHandlerArn** - Lambda function ARN
12. **ExecutionHandlerArn** - Lambda function ARN
13. **QueryHandlerArn** - Lambda function ARN
14. **UserPoolId** - Cognito User Pool ID
15. **UserPoolClientId** - Cognito User Pool Client ID
15. **IdentityPoolId** - Cognito Identity Pool ID
16. **ApiId** - API Gateway ID
17. **StateMachineArn** - Step Functions state machine ARN
18. **EventBridgeRoleArn** - EventBridge role ARN
19. **Region** - AWS region
20. **DeploymentBucket** - S3 deployment bucket name

### Conditional Outputs (3 total)

These outputs are only present when `DeployFrontend=true`:

21. **CloudFrontUrl** - CloudFront distribution URL
22. **CloudFrontDistributionId** - CloudFront distribution ID
23. **FrontendBucketName** - S3 frontend bucket name

---

## Troubleshooting

### Issue: Invalid OrchestrationRoleArn

**Symptom:**
```
Parameter validation failed:
Invalid value for parameter OrchestrationRoleArn
```

**Cause:**
OrchestrationRoleArn doesn't match IAM ARN pattern.

**Solution:**
Ensure ARN format is correct:
```
arn:aws:iam::[12-digit-account-id]:role/[role-name]
```

**Valid Example:**
```
arn:aws:iam::123456789012:role/ExternalOrchestrationRole
```

---

### Issue: Lambda Function Permission Errors

**Symptom:**
```
AccessDeniedException: User is not authorized to perform: drs:StartRecovery
```

**Cause:**
External Platform role missing required permissions.

**Solution:**
Verify External Platform role includes all 16 policies from UnifiedOrchestrationRole. See [External Platform Role Requirements](#hrp-role-requirements).

**Check Role Permissions:**
```bash
aws iam get-role --role-name ExternalOrchestrationRole
aws iam list-role-policies --role-name ExternalOrchestrationRole
aws iam list-attached-role-policies --role-name ExternalOrchestrationRole
```

---

### Issue: Frontend Not Deployed

**Symptom:**
CloudFront outputs missing from stack.

**Cause:**
DeployFrontend parameter set to 'false'.

**Solution:**
If frontend is needed, update stack with DeployFrontend='true':
```bash
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    DeploymentBucket=aws-drs-orchestration-dev \
    DeployFrontend=true
```

---

### Issue: Migration Rollback

**Symptom:**
Stack update rolled back during migration.

**Cause:**
Migration failed (e.g., permission issue, resource limit).

**Solution:**
1. Check CloudFormation events:
```bash
aws cloudformation describe-stack-events \
  --stack-name aws-drs-orchestration-dev \
  --max-items 20
```

2. Identify failure reason
3. Fix issue (e.g., increase IAM role limit)
4. Retry deployment:
```bash
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    DeploymentBucket=aws-drs-orchestration-dev
```

**Note:** Stack automatically returns to previous state (individual roles) on rollback.

---

### Issue: API Gateway 403 Forbidden

**Symptom:**
API calls return 403 Forbidden after deployment.

**Cause:**
Cognito authentication not configured correctly.

**Solution:**
1. Verify Cognito User Pool and Client ID in frontend configuration
2. Check JWT token validity
3. Verify API Gateway authorizer configuration

**Get Stack Outputs:**
```bash
aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-dev \
  --query 'Stacks[0].Outputs'
```

---

## Cost Optimization

### Cost by Deployment Mode

| Mode | Monthly Cost | Savings vs. Default |
|------|--------------|---------------------|
| Default Standalone | $12-40 | Baseline |
| API-Only Standalone | $8-30 | 33% savings |
| External Platform + Frontend | $12-40 | Baseline |
| Full External Platform Integration | $8-30 | 33% savings |

**Cost Breakdown:**

**Default/External Platform+Frontend:**
- Lambda: $1-5
- API Gateway: $3-10
- DynamoDB: $1-5
- CloudFront: $1-5
- S3: <$1
- Step Functions: $1-5
- Cognito: Free tier

**API-Only:**
- Lambda: $1-5
- API Gateway: $3-10
- DynamoDB: $1-5
- CloudFront: $0 (not deployed)
- S3: <$1 (deployment bucket only)
- Step Functions: $1-5
- Cognito: Free tier

---

## Best Practices

### 1. Choose the Right Deployment Mode

- **Standalone organization?** → Default Standalone (Mode 1)
- **Custom frontend?** → API-Only Standalone (Mode 2)
- **External platform with existing infrastructure?** → Lambda-Only Integration (Mode 3)

### 2. External Platform Role Management

- Create External Platform role in separate CloudFormation stack
- Version control External Platform role policies
- Regular permission audits
- Document all permission changes

### 3. Migration Planning

- Test migration in dev environment first
- Schedule migration during maintenance window
- Monitor CloudWatch Logs during migration
- Have rollback plan ready

### 4. API Integration

- Use ApiEndpoint output for API calls
- Implement proper error handling
- Cache Cognito tokens appropriately
- Monitor API Gateway metrics

### 5. Security

- Enable CloudTrail for audit logging
- Regular IAM permission reviews
- Use least privilege principle
- Monitor for unauthorized access

---

## Related Documentation

- [API and Integration Guide](API_AND_INTEGRATION_GUIDE.md) - Complete REST API documentation
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Deployment procedures
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) - Common issues and solutions

---

## Support

For issues or questions:
1. Check [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
2. Review CloudFormation events
3. Check CloudWatch Logs

---

**Version:** 4.0
