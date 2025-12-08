# AWS DRS Orchestration - Deployment Recovery Guide

## Critical Configuration Capture

This guide ensures all configurations are preserved for reliable redeployment from scratch.

### 1. Deployment Bucket Structure

**Primary Bucket**: `aws-drs-orchestration`

```
aws-drs-orchestration/
├── cfn/                           # CloudFormation templates
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
│   ├── step-functions-stack.yaml
│   ├── frontend-stack.yaml
│   └── security-stack.yaml
└── lambda/                        # Pre-built Lambda packages
    ├── api-handler.zip           # index.py + dependencies
    ├── orchestration.zip         # drs_orchestrator.py + dependencies
    ├── orchestration-stepfunctions.zip  # orchestration_stepfunctions.py
    ├── execution-finder.zip      # poller/execution_finder.py
    ├── execution-poller.zip      # poller/execution_poller.py
    └── frontend-builder.zip      # build_and_deploy.py
```

### 2. Critical Lambda Function Mapping

| CloudFormation Function | S3 Artifact | Handler | Purpose |
|-------------------------|-------------|---------|---------|
| `ApiHandlerFunction` | `api-handler.zip` | `index.lambda_handler` | REST API endpoints |
| `OrchestrationFunction` | `orchestration.zip` | `drs_orchestrator.lambda_handler` | Legacy orchestrator |
| `OrchestrationStepFunctionsFunction` | `orchestration-stepfunctions.zip` | `orchestration_stepfunctions.handler` | **ACTIVE Step Functions handler** |
| `FrontendBuilderFunction` | `frontend-builder.zip` | `build_and_deploy.lambda_handler` | Frontend deployment |
| `ExecutionFinderFunction` | `execution-finder.zip` | `execution_finder.lambda_handler` | Polling scheduler |
| `ExecutionPollerFunction` | `execution-poller.zip` | `execution_poller.lambda_handler` | Status updates |

### 3. Step Functions Configuration

**State Machine ARN Pattern**: `arn:aws:states:us-east-1:ACCOUNT:stateMachine:drs-orchestration-state-machine-ENV`

**Critical**: Step Functions calls `OrchestrationStepFunctionsFunction`, NOT `OrchestrationFunction`

```yaml
# cfn/master-template.yaml
StepFunctionsStack:
  Parameters:
    OrchestrationLambdaArn: !GetAtt LambdaStack.Outputs.OrchestrationStepFunctionsFunctionArn
```

### 4. Frontend Configuration Structure

**Required Format** (must match `frontend/src/aws-config.ts`):

```javascript
window.AWS_CONFIG = {
  Auth: {
    Cognito: {
      region: 'us-east-1',
      userPoolId: 'us-east-1_XXXXXXX',
      userPoolClientId: 'XXXXXXXXXXXXXXXXXXXXXXXXXX',
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
}
```

### 5. Complete Redeployment Process

#### Step 1: Prepare Deployment Artifacts

```bash
# 1. Build Lambda packages
cd lambda
pip install -r requirements.txt -t package/

# API Handler
cd package && zip -r ../api-handler.zip . && cd ..
zip -g api-handler.zip index.py

# Orchestration (Step Functions)
cd package && zip -r ../orchestration-stepfunctions.zip . && cd ..
zip -g orchestration-stepfunctions.zip orchestration_stepfunctions.py

# Legacy Orchestration
cd package && zip -r ../orchestration.zip . && cd ..
zip -g orchestration.zip drs_orchestrator.py

# Upload to S3
aws s3 cp api-handler.zip s3://aws-drs-orchestration/lambda/
aws s3 cp orchestration.zip s3://aws-drs-orchestration/lambda/
aws s3 cp orchestration-stepfunctions.zip s3://aws-drs-orchestration/lambda/
```

#### Step 2: Deploy CloudFormation

```bash
aws cloudformation deploy \
  --template-url https://aws-drs-orchestration.s3.us-east-1.amazonaws.com/cfn/master-template.yaml \
  --stack-name drs-orchestration-dev \
  --parameter-overrides \
    ProjectName=drs-orchestration \
    Environment=dev \
    SourceBucket=aws-drs-orchestration \
    AdminEmail=admin@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

#### Step 3: Build and Deploy Frontend

```bash
# Build frontend
cd frontend
npm install
npm run build

# Get CloudFormation outputs
BUCKET=$(aws cloudformation describe-stacks --stack-name drs-orchestration-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' --output text)
DIST_ID=$(aws cloudformation describe-stacks --stack-name drs-orchestration-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' --output text)
API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name drs-orchestration-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name drs-orchestration-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text)
CLIENT_ID=$(aws cloudformation describe-stacks --stack-name drs-orchestration-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' --output text)

# Create aws-config.js
cat > aws-config.js <<EOF
window.AWS_CONFIG = {
  Auth: {
    Cognito: {
      region: 'us-east-1',
      userPoolId: '${USER_POOL_ID}',
      userPoolClientId: '${CLIENT_ID}',
      loginWith: {
        email: true
      }
    }
  },
  API: {
    REST: {
      DRSOrchestration: {
        endpoint: '${API_ENDPOINT}',
        region: 'us-east-1'
      }
    }
  }
}
EOF

# Deploy frontend
aws s3 sync dist/ s3://${BUCKET}/ --delete --exclude "aws-config.js"
aws s3 cp aws-config.js s3://${BUCKET}/aws-config.js
aws cloudfront create-invalidation --distribution-id ${DIST_ID} --paths "/*"
```

#### Step 4: Create Admin User

```bash
# Create admin user
aws cognito-idp admin-create-user \
  --user-pool-id ${USER_POOL_ID} \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com Name=email_verified,Value=true \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id ${USER_POOL_ID} \
  --username admin@example.com \
  --password "YourSecurePassword123!" \
  --permanent
```

### 6. Troubleshooting Common Issues

#### Issue: Step Functions Timeout (3 seconds)
**Cause**: Wrong Lambda function called
**Fix**: Ensure `OrchestrationStepFunctionsFunctionArn` is used in Step Functions stack

#### Issue: Frontend Authentication Error
**Cause**: Incorrect `aws-config.js` structure
**Fix**: Use exact structure from Section 4, ensure CloudFront cache invalidation

#### Issue: Stale Lambda Code
**Cause**: CloudFormation uses S3 artifacts, not local code
**Fix**: Update S3 artifacts first, then redeploy CloudFormation

#### Issue: Missing Environment Variables
**Check Lambda environment variables**:
```bash
aws lambda get-function-configuration \
  --function-name drs-orchestration-orchestration-stepfunctions-dev \
  --query 'Environment.Variables'
```

### 7. Validation Commands

```bash
# Verify Step Functions state machine
aws stepfunctions describe-state-machine \
  --state-machine-arn $(aws stepfunctions list-state-machines \
    --query 'stateMachines[?name==`drs-orchestration-state-machine-dev`].stateMachineArn' --output text)

# Test Lambda function
aws lambda invoke \
  --function-name drs-orchestration-orchestration-stepfunctions-dev \
  --payload '{"action":"begin","execution":"test","plan":{"PlanId":"test"},"isDrill":true}' \
  response.json && cat response.json

# Verify frontend config
curl -s https://CLOUDFRONT_URL/aws-config.js

# Check DRS source servers
aws drs describe-source-servers --region us-east-1
```

### 8. GitLab CI/CD Integration

The GitLab pipeline automatically handles this process:

1. **Build Stage**: Creates Lambda ZIP files
2. **Deploy Infrastructure**: Uploads artifacts and deploys CloudFormation
3. **Deploy Frontend**: Generates correct `aws-config.js` and deploys

**Key Variables**:
- `DEPLOYMENT_BUCKET`: `aws-drs-orchestration`
- `ADMIN_EMAIL`: Admin email for Cognito
- `AWS_DEFAULT_REGION`: `us-east-1`

### 9. Critical Files to Preserve

1. **CloudFormation Templates**: All files in `cfn/`
2. **Lambda Source Code**: `lambda/index.py`, `lambda/orchestration_stepfunctions.py`
3. **Frontend Source**: All files in `frontend/src/`
4. **Deployment Scripts**: `.gitlab-ci.yml`, `lambda/requirements.txt`
5. **This Guide**: `DEPLOYMENT_RECOVERY_GUIDE.md`

### 10. Emergency Recovery

If everything is lost, this guide + the Git repository contains everything needed to rebuild from scratch. The key is ensuring:

1. S3 deployment bucket exists with correct artifacts
2. CloudFormation templates reference correct S3 paths
3. Frontend configuration matches expected structure
4. Step Functions calls the correct Lambda function

**Recovery Time**: ~45 minutes for complete redeployment