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
├── lambda/                        # Lambda source code and packages
│   ├── index.py                  # API handler
│   ├── orchestration_stepfunctions.py  # Step Functions orchestrator
│   ├── drs_orchestrator.py       # Legacy orchestrator
│   ├── build_and_deploy.py       # Frontend builder
│   ├── poller/
│   │   ├── execution_finder.py   # Polling scheduler
│   │   └── execution_poller.py   # Status updates
│   ├── requirements.txt          # Python dependencies
│   └── deployment-package.zip    # Built package with all functions
├── frontend/                      # React application
│   ├── src/
│   ├── dist/                     # Built frontend (after npm run build)
│   └── package.json
├── scripts/                       # Deployment automation
│   └── sync-to-deployment-bucket.sh
└── docs/                         # Documentation
```

### 2. Critical Lambda Function Mapping

| CloudFormation Function | S3 Artifact | Handler | Purpose |
|-------------------------|-------------|---------|---------|
| `ApiHandlerFunction` | `deployment-package.zip` | `index.lambda_handler` | REST API endpoints |
| `OrchestrationFunction` | `deployment-package.zip` | `drs_orchestrator.lambda_handler` | Legacy orchestrator |
| `OrchestrationStepFunctionsFunction` | `deployment-package.zip` | `orchestration_stepfunctions.handler` | **ACTIVE Step Functions handler** |
| `FrontendBuilderFunction` | `deployment-package.zip` | `build_and_deploy.lambda_handler` | Frontend deployment |
| `ExecutionFinderFunction` | `deployment-package.zip` | `poller.execution_finder.lambda_handler` | Polling scheduler |
| `ExecutionPollerFunction` | `deployment-package.zip` | `poller.execution_poller.lambda_handler` | Status updates |

**Note**: All functions now use a single `deployment-package.zip` containing all code and dependencies.

### 3. Step Functions Configuration

**State Machine ARN Pattern**: `arn:aws:states:us-east-1:ACCOUNT:stateMachine:aws-drs-orchestrator-state-machine-ENV`

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
};
```

> **Important**: The structure must match exactly. Common mistakes:
> - Using `cognito` instead of `Auth.Cognito`
> - Using `clientId` instead of `userPoolClientId`
> - Missing `loginWith.email` property

### 5. Complete Redeployment Process

#### Step 1: Prepare Deployment Artifacts (Automated)

```bash
# Use automated sync script to prepare all artifacts
./scripts/sync-to-deployment-bucket.sh --build-frontend

# This automatically:
# - Packages all Lambda functions with dependencies
# - Builds frontend with correct configuration
# - Syncs CloudFormation templates to S3
# - Uploads all artifacts to aws-drs-orchestration bucket
```

**Manual Process (if needed)**:
```bash
# 1. Build Lambda packages
cd lambda
pip install -r requirements.txt -t package/

# Create deployment package
cd package && zip -r ../deployment-package.zip . && cd ..
zip -g deployment-package.zip index.py
if [ -d "poller" ]; then
    zip -rg deployment-package.zip poller/
fi

# Upload to S3
aws s3 cp deployment-package.zip s3://aws-drs-orchestration/lambda/
```

#### Step 2: Deploy CloudFormation (Automated)

```bash
# Use automated deployment script
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

**Manual Process (if needed)**:
```bash
aws cloudformation deploy \
  --template-url https://s3.amazonaws.com/aws-drs-orchestration/cfn/master-template.yaml \
  --stack-name aws-drs-orchestrator-dev \
  --parameter-overrides \
    ProjectName=aws-drs-orchestrator \
    Environment=dev \
    SourceBucket=aws-drs-orchestration \
    AdminEmail=admin@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

#### Step 3: Deploy Frontend (Automated)

```bash
# Frontend is automatically built and deployed by CloudFormation custom resource
# No manual steps required - configuration is injected at deployment time
```

**Manual Process (if needed)**:
```bash
# Build frontend with environment file
cd frontend
cp ../.env.dev .env.local  # Contains API endpoint and Cognito config
npm install
npm run build

# Deploy to S3 (CloudFormation custom resource handles this automatically)
# Manual deployment only needed for troubleshooting
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
  --function-name aws-drs-orchestrator-orchestration-stepfunctions-dev \
  --query 'Environment.Variables'
```

### 7. Validation Commands

```bash
# Verify Step Functions state machine
aws stepfunctions describe-state-machine \
  --state-machine-arn $(aws stepfunctions list-state-machines \
    --query 'stateMachines[?name==`aws-drs-orchestrator-state-machine-dev`].stateMachineArn' --output text)

# Test Lambda function
aws lambda invoke \
  --function-name aws-drs-orchestrator-orchestration-stepfunctions-dev \
  --payload '{"action":"begin","execution":"test","plan":{"PlanId":"test"},"isDrill":true}' \
  response.json && cat response.json

# Verify frontend config
curl -s https://CLOUDFRONT_URL/aws-config.js

# Check DRS source servers
aws drs describe-source-servers --region us-east-1
```

### 8. GitLab CI/CD Integration

The GitLab pipeline automatically handles this process:

1. **Validate Stage**: CloudFormation validation, TypeScript type checking
2. **Lint Stage**: Python (pylint, black, flake8), Frontend (ESLint)
3. **Build Stage**: Creates Lambda ZIP files and builds React frontend
4. **Deploy Infrastructure**: Uploads artifacts to S3 and deploys CloudFormation
5. **Deploy Frontend**: Generates `aws-config.js` from CloudFormation outputs and deploys to S3/CloudFront

**Required CI/CD Variables** (Settings > CI/CD > Variables):

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key (masked) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key (masked) |
| `ADMIN_EMAIL` | Admin email for Cognito |

**Built-in Variables**:
- `DEPLOYMENT_BUCKET`: `aws-drs-orchestration`
- `AWS_DEFAULT_REGION`: `us-east-1`
- `ENVIRONMENT`: `test`

See [CICD_PIPELINE_GUIDE.md](./CICD_PIPELINE_GUIDE.md) for complete CI/CD documentation.

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

**Recovery Time**: ~30 minutes for complete redeployment (using automated scripts)