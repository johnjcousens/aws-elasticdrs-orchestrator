# CodeBuild Permissions Fix

## Issue Description

The CI/CD pipeline was failing during the infrastructure deployment phase with the following error:

```
User: arn:aws:sts::777788889999:assumed-role/aws-elasticdrs-orchestrator-codebuild-service-role-dev/AWSCodeBuild-52d8b7fe-4f3f-4f77-ab87-c6317f3885d5 is not authorized to perform: cloudformation:GetTemplateSummary on resource: arn:aws:cloudformation:us-east-1:777788889999:stack/aws-elasticdrs-orchestrator-dev/94d7f0d0-e90a-11f0-818d-12b117807b41 because no identity-based policy allows the cloudformation:GetTemplateSummary action
```

## Root Cause Analysis

**PRIMARY ISSUE**: The CI/CD infrastructure (CodeBuild projects, CodePipeline, CodeCommit) was **disabled** in the CloudFormation deployment.

### Investigation Steps

1. **CodeBuild Projects Missing**: No CodeBuild projects exist in the account
   ```bash
   aws codebuild list-projects --output table
   # Returns empty - no projects found
   ```

2. **CI/CD Stacks Missing**: The nested CI/CD stacks are not deployed
   ```bash
   aws cloudformation describe-stack-resources --stack-name aws-elasticdrs-orchestrator-dev \
     --query 'StackResources[?ResourceType==`AWS::CloudFormation::Stack`]'
   # Missing: CodeCommitStack, CodeBuildProjectsStack, CodePipelineStack
   ```

3. **Parameter Issue**: The master template was deployed with `EnableAutomatedDeployment=false`
   - This disables the `EnableCICDCondition` in the CloudFormation template
   - All CI/CD nested stacks are conditional on this parameter

### Technical Details

The master template (`cfn/master-template.yaml`) contains conditional CI/CD infrastructure:

```yaml
Conditions:
  EnableCICDCondition: !Equals [!Ref EnableAutomatedDeployment, 'true']

Resources:
  CodeCommitStack:
    Type: AWS::CloudFormation::Stack
    Condition: EnableCICDCondition  # Only created when EnableAutomatedDeployment=true
    
  CodeBuildProjectsStack:
    Type: AWS::CloudFormation::Stack
    Condition: EnableCICDCondition  # Only created when EnableAutomatedDeployment=true
    
  CodePipelineStack:
    Type: AWS::CloudFormation::Stack
    Condition: EnableCICDCondition  # Only created when EnableAutomatedDeployment=true
```

When `EnableAutomatedDeployment=false`, these stacks are not created, resulting in:
- No CodeBuild projects
- No CodeBuild service roles
- No CI/CD pipeline
- The error occurs because the pipeline tries to use non-existent CodeBuild projects

## Solution

### Option 1: Enable CI/CD Infrastructure (Recommended)

The proper solution is to enable the CI/CD infrastructure by setting `EnableAutomatedDeployment=true`:

```bash
# Deploy with CI/CD infrastructure enabled
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --parameter-overrides \
    ProjectName=aws-elasticdrs-orchestrator \
    Environment=dev \
    SourceBucket=aws-elasticdrs-orchestrator \
    AdminEmail=admin@example.com \
    EnableAutomatedDeployment=true \
    GitHubRepositoryURL=https://github.com/johnjcousens/aws-elasticdrs-orchestrator \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset
```

**Note**: If the CI/CD artifacts bucket already exists, you may need to handle the conflict:

1. **Check if artifacts bucket exists**:
   ```bash
   aws s3 ls | grep cicd-artifacts
   ```

2. **If bucket exists, either**:
   - Delete the existing bucket (if safe to do so)
   - Or modify the CloudFormation template to use the existing bucket

### Option 2: Manual Deployment Without CI/CD

If you want to deploy without CI/CD infrastructure:

```bash
# Deploy without CI/CD (not recommended for production)
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --parameter-overrides \
    ProjectName=aws-elasticdrs-orchestrator \
    Environment=dev \
    SourceBucket=aws-elasticdrs-orchestrator \
    AdminEmail=admin@example.com \
    EnableAutomatedDeployment=false \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset
```

Then use manual deployment scripts:
```bash
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

### Option 3: Fix Existing CI/CD Artifacts Conflict

If the CI/CD artifacts bucket already exists and causes deployment conflicts:

1. **Identify the existing bucket**:
   ```bash
   aws s3 ls | grep elasticdrs.*cicd
   ```

2. **Check bucket contents**:
   ```bash
   aws s3 ls s3://aws-elasticdrs-orchestrator-cicd-artifacts-777788889999-dev/
   ```

3. **Either delete the bucket** (if safe):
   ```bash
   aws s3 rb s3://aws-elasticdrs-orchestrator-cicd-artifacts-777788889999-dev --force
   ```

4. **Or modify the CodeCommit stack template** to use existing bucket instead of creating new one

## Deployment Steps

### Immediate Fix: Use Manual Deployment (Recommended)

Since the CI/CD artifacts bucket conflict prevents enabling CI/CD infrastructure, use manual deployment:

1. **Deploy without CI/CD infrastructure**:
   ```bash
   aws cloudformation deploy \
     --template-file cfn/master-template.yaml \
     --stack-name aws-elasticdrs-orchestrator-dev \
     --parameter-overrides \
       ProjectName=aws-elasticdrs-orchestrator \
       Environment=dev \
       SourceBucket=aws-elasticdrs-orchestrator \
       AdminEmail=admin@example.com \
       EnableAutomatedDeployment=false \
     --capabilities CAPABILITY_NAMED_IAM \
     --no-fail-on-empty-changeset
   ```

2. **Use manual deployment scripts for updates**:
   ```bash
   # Sync code to S3 and deploy infrastructure
   ./scripts/sync-to-deployment-bucket.sh --deploy-cfn
   
   # For Lambda code updates only (faster)
   ./scripts/sync-to-deployment-bucket.sh --update-lambda-code
   ```

3. **Verify the deployment**:
   ```bash
   # Check that the main stack is deployed
   aws cloudformation describe-stacks --stack-name aws-elasticdrs-orchestrator-dev
   
   # Check API Gateway endpoint
   aws cloudformation describe-stacks --stack-name aws-elasticdrs-orchestrator-dev \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text
   ```

### Future: Enable CI/CD Infrastructure (When Needed)

To enable CI/CD infrastructure later (requires resolving bucket conflict):

1. **Resolve the artifacts bucket conflict**:
   ```bash
   # Option A: Delete existing bucket (if safe)
   aws s3 rb s3://aws-elasticdrs-orchestrator-cicd-artifacts-777788889999-dev --force
   
   # Option B: Modify CloudFormation template to use existing bucket
   # (requires template changes in cfn/codecommit-stack.yaml)
   ```

2. **Deploy with CI/CD enabled**:
   ```bash
   aws cloudformation deploy \
     --template-file cfn/master-template.yaml \
     --stack-name aws-elasticdrs-orchestrator-dev \
     --parameter-overrides \
       ProjectName=aws-elasticdrs-orchestrator \
       Environment=dev \
       SourceBucket=aws-elasticdrs-orchestrator \
       AdminEmail=admin@example.com \
       EnableAutomatedDeployment=true \
       GitHubRepositoryURL=https://github.com/johnjcousens/aws-elasticdrs-orchestrator \
     --capabilities CAPABILITY_NAMED_IAM \
     --no-fail-on-empty-changeset
   ```

## Verification

After deploying with manual deployment:

1. **Check that the main infrastructure exists**:
   ```bash
   # Main stack status
   aws cloudformation describe-stacks --stack-name aws-elasticdrs-orchestrator-dev \
     --query 'Stacks[0].StackStatus' --output text
   
   # List all nested stacks
   aws cloudformation describe-stack-resources --stack-name aws-elasticdrs-orchestrator-dev \
     --query 'StackResources[?ResourceType==`AWS::CloudFormation::Stack`].[LogicalResourceId,ResourceStatus]' \
     --output table
   ```

2. **Verify API Gateway is working**:
   ```bash
   # Get API endpoint
   API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name aws-elasticdrs-orchestrator-dev \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
   echo "API Endpoint: $API_ENDPOINT"
   
   # Test API health check (if available)
   curl -s "$API_ENDPOINT/health" || echo "API endpoint not yet available"
   ```

3. **Check Lambda functions are deployed**:
   ```bash
   # List Lambda functions
   aws lambda list-functions --query 'Functions[?contains(FunctionName, `elasticdrs`)].FunctionName' --output table
   ```

4. **Verify DynamoDB tables exist**:
   ```bash
   # List DynamoDB tables
   aws dynamodb list-tables --query 'TableNames[?contains(@, `elasticdrs`)]' --output table
   ```

If CI/CD infrastructure is enabled later:

1. **Check that all CI/CD components exist**:
   ```bash
   # CodeBuild projects
   aws codebuild list-projects --query 'projects[?contains(@, `elasticdrs`)]'
   
   # CodePipeline
   aws codepipeline get-pipeline --name aws-elasticdrs-orchestrator-pipeline-dev
   
   # CodeCommit repository
   aws codecommit get-repository --repository-name aws-elasticdrs-orchestrator-dev
   ```

2. **Test the pipeline**:
   ```bash
   # Trigger pipeline manually
   aws codepipeline start-pipeline-execution \
     --name aws-elasticdrs-orchestrator-pipeline-dev
   ```

## Prevention

To prevent similar issues in the future:

1. **Always Enable CI/CD**: Deploy with `EnableAutomatedDeployment=true` for production environments
2. **Parameter Validation**: Verify CloudFormation parameters before deployment
3. **Infrastructure Monitoring**: Regularly check that all expected AWS resources exist
4. **Documentation**: Keep deployment parameters documented and consistent
5. **Testing**: Test CI/CD pipeline functionality after any infrastructure changes

## Related Files

- `cfn/master-template.yaml` - Master CloudFormation template with CI/CD conditions
- `cfn/codecommit-stack.yaml` - CodeCommit repository and artifacts bucket
- `cfn/codebuild-projects-stack.yaml` - CodeBuild projects and service roles
- `cfn/codepipeline-stack.yaml` - CodePipeline configuration
- `buildspecs/deploy-infra-buildspec.yml` - Infrastructure deployment buildspec
- `docs/guides/troubleshooting/CODEBUILD_PERMISSIONS_FIX.md` - This documentation

## Key Learnings

1. **Conditional Infrastructure**: The CI/CD components are conditional in the CloudFormation template
2. **Parameter Dependencies**: `EnableAutomatedDeployment=false` disables all CI/CD infrastructure
3. **Resource Conflicts**: Existing S3 buckets can cause CloudFormation deployment failures
4. **Proper Diagnosis**: Always check if resources exist before assuming permission issues

## Security Considerations

When CI/CD infrastructure is enabled:

- **CodeBuild Service Role**: Has comprehensive permissions for infrastructure deployment
- **Artifact Bucket**: Stores build artifacts and deployment packages
- **CodeCommit Repository**: Contains source code with proper access controls
- **Pipeline Notifications**: SNS notifications for deployment status

All permissions follow the principle of least privilege while ensuring comprehensive deployment capabilities.