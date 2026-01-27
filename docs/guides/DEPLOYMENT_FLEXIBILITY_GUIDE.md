# Deployment Flexibility Guide

## Overview

The AWS DRS Orchestration Solution supports **4 flexible deployment modes** to accommodate different use cases, from standalone deployments to external platform integration.

This guide covers:
- Deployment mode selection
- Configuration parameters
- Use cases and scenarios
- Migration from existing deployments
- Troubleshooting

## Architecture Overview

### Full-Stack Architecture (Modes 1 & 3)

![AWS DRS Orchestration - Comprehensive Architecture](../architecture/AWS-DRS-Orchestration-Architecture-Comprehensive.png)

**Components**: CloudFront CDN, S3 Static Hosting, Cognito User Pool, API Gateway, 5 Lambda Functions, Step Functions, DynamoDB (4 tables), EventBridge, CloudWatch, SNS, AWS DRS, Cross-Account IAM Roles

### Backend-Only Architecture (Modes 2 & 4)

![AWS DRS Orchestration - Backend Only](../architecture/AWS-DRS-Orchestration-Backend-Only.png)

**Components**: Direct Lambda invocation via CLI/SDK, 5 Lambda Functions, Step Functions, DynamoDB (4 tables), EventBridge, CloudWatch, SNS, AWS DRS, Cross-Account IAM Roles

**Benefits**: 60% lower cost (no API Gateway), simpler architecture, native AWS authentication

## Deployment Modes

### Mode 1: Default Standalone (Full Stack)

**Configuration:**
- `OrchestrationRoleArn`: empty (default)
- `DeployFrontend`: true (default)

**What Gets Deployed:**
- ✅ Unified orchestration IAM role (consolidates 7 individual roles)
- ✅ All 8 Lambda functions
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
./scripts/deploy.sh dev
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
- ✅ All 8 Lambda functions
- ✅ API Gateway (REST API)
- ❌ Frontend (S3 + CloudFront) - NOT deployed
- ✅ DynamoDB tables
- ✅ Step Functions
- ✅ Cognito authentication

**Use Cases:**
- Custom frontend development
- CLI/SDK-only operations
- Microservices architecture
- API integration with existing systems

**Deployment Command:**
```bash
./scripts/deploy.sh dev --parameter-overrides DeployFrontend=false
```

**Benefits:**
- ✅ Full backend functionality
- ✅ API endpoint available for custom UIs
- ✅ Reduced infrastructure costs (no S3/CloudFront)
- ✅ Flexible integration options

**Integration Example:**
```javascript
// Custom frontend calling DRS orchestration API
const response = await fetch(`${API_ENDPOINT}/protection-groups`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  }
});
```

---

### Mode 3: External Integration with Frontend

**Configuration:**
- `OrchestrationRoleArn`: provided (external role ARN)
- `DeployFrontend`: true (default)

**What Gets Deployed:**
- ❌ Unified orchestration IAM role - NOT created (uses External Platform role)
- ✅ All 8 Lambda functions (using External Platform role)
- ✅ API Gateway (REST API)
- ✅ Frontend (S3 + CloudFront)
- ✅ DynamoDB tables
- ✅ Step Functions
- ✅ Cognito authentication

**Use Cases:**
- External Platform platform integration with DRS orchestration frontend
- Centralized IAM management by External Platform
- Organizations using External Platform for multiple services
- Consistent permission model across External Platform platform

**Deployment Command:**
```bash
./scripts/deploy.sh dev \
  --parameter-overrides OrchestrationRoleArn=arn:aws:iam::123456789012:role/ExternalOrchestrationRole
```

**External Platform Role Requirements:**
The External Platform role must include all permissions from the unified orchestration role. See [External Platform Role Requirements](#hrp-role-requirements) section below.

**Benefits:**
- ✅ Centralized IAM management
- ✅ Consistent permissions across External Platform
- ✅ Simplified compliance auditing
- ✅ Full frontend functionality

---

### Mode 4: Full External Platform Integration (API-Only)

**Configuration:**
- `OrchestrationRoleArn`: provided (External Platform role ARN)
- `DeployFrontend`: false

**What Gets Deployed:**
- ❌ Unified orchestration IAM role - NOT created (uses External Platform role)
- ✅ All 8 Lambda functions (using External Platform role)
- ✅ API Gateway (REST API)
- ❌ Frontend (S3 + CloudFront) - NOT deployed
- ✅ DynamoDB tables
- ✅ Step Functions
- ✅ Cognito authentication

**Use Cases:**
- Full External Platform platform integration
- External Platform provides unified frontend across all services
- DRS orchestration as backend-only service
- Maximum integration with External Platform platform

**Deployment Command:**
```bash
./scripts/deploy.sh dev \
  --parameter-overrides \
    OrchestrationRoleArn=arn:aws:iam::123456789012:role/ExternalOrchestrationRole \
    DeployFrontend=false
```

**Benefits:**
- ✅ Centralized IAM management
- ✅ Unified External Platform frontend
- ✅ Minimal infrastructure footprint
- ✅ Maximum cost optimization
- ✅ Consistent UI/UX across External Platform

**External Platform Integration Architecture:**
```
┌─────────────────────────────────────┐
│      External Platform Unified Frontend           │
│  ┌──────────┬──────────┬─────────┐ │
│  │ Compute  │ Storage  │   DR    │ │
│  │   Mgmt   │   Mgmt   │  Orch   │ │
│  └──────────┴──────────┴────┬────┘ │
└───────────────────────────────┼──────┘
                                │
                                ▼
┌─────────────────────────────────────┐
│   DRS Orchestration API Gateway     │
│   (Backend Service)                 │
└─────────────────────────────────────┘
```

---

## Deployment Mode Comparison

| Feature | Default | API-Only | External Platform + Frontend | Full External Platform |
|---------|---------|----------|----------------|----------|
| **IAM Role** | Created | Created | External Platform Provided | External Platform Provided |
| **Lambda Functions** | ✅ | ✅ | ✅ | ✅ |
| **API Gateway** | ✅ | ✅ | ✅ | ✅ |
| **Frontend** | ✅ | ❌ | ✅ | ❌ |
| **DynamoDB** | ✅ | ✅ | ✅ | ✅ |
| **Step Functions** | ✅ | ✅ | ✅ | ✅ |
| **Monthly Cost** | $12-40 | $8-30 | $12-40 | $8-30 |
| **Use Case** | Standalone | Custom UI | External Platform + UI | External Platform Backend |

---

## External Platform Role Requirements

When using External Platform integration (Modes 3 & 4), the External Platform role must include all permissions from the unified orchestration role.

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

See the complete policy definitions in the [design document](.kiro/specs/deployment-flexibility/design.md) or [master-template.yaml](../../cfn/master-template.yaml) (UnifiedOrchestrationRole resource).

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

### Migrating from 7 Individual Roles to Unified Role

If you have an existing deployment with 7 individual IAM roles, you can seamlessly migrate to the unified role architecture.

**Migration Process:**
1. Update stack with default parameters (no overrides needed)
2. CloudFormation automatically:
   - Creates UnifiedOrchestrationRole
   - Updates all 8 Lambda functions to use new role
   - Deletes 7 old individual roles
3. Zero downtime during migration
4. Automatic rollback on failure

**Migration Command:**
```bash
# Same command as normal deployment
./scripts/deploy.sh dev
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
  - ApiHandlerFunction uses ApiHandlerRole
  - OrchestrationFunction uses OrchestrationRole
  - ... (7 individual roles)

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
If migration fails, CloudFormation automatically rolls back to previous state (7 individual roles).

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
11. **ApiHandlerFunctionArn** - Lambda function ARN
12. **OrchestrationFunctionArn** - Lambda function ARN
13. **UserPoolId** - Cognito User Pool ID
14. **UserPoolClientId** - Cognito User Pool Client ID
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
./scripts/deploy.sh dev --parameter-overrides DeployFrontend=true
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
  --stack-name aws-drs-orch-dev \
  --max-items 20
```

2. Identify failure reason
3. Fix issue (e.g., increase IAM role limit)
4. Retry deployment:
```bash
./scripts/deploy.sh dev
```

**Note:** Stack automatically returns to previous state (7 individual roles) on rollback.

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
  --stack-name aws-drs-orch-dev \
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
- **External Platform with DRS UI?** → External Platform + Frontend (Mode 3)
- **External Platform unified UI?** → Full External Platform Integration (Mode 4)

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
- [Design Document](.kiro/specs/deployment-flexibility/design.md) - Technical design details
- [Requirements Document](.kiro/specs/deployment-flexibility/requirements.md) - Feature requirements

---

## Support

For issues or questions:
1. Check [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
2. Review CloudFormation events
3. Check CloudWatch Logs
4. Consult validation documents in `.kiro/specs/deployment-flexibility/`

---

**Last Updated:** January 2026  
**Version:** 1.0.0
