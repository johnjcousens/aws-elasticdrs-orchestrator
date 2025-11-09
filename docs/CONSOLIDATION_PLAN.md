# CloudFormation Template Consolidation Plan

## Objective
Consolidate three CloudFormation templates into a single S3-hosted deployment solution where users can deploy with a single CloudFormation command.

## Current State

### Files to Consolidate
1. **master-template.yaml** (1,170 lines) - Main template with nested stack reference
2. **lambda-stack.yaml** (SAM template, 300+ lines) - Lambda functions and IAM roles
3. **security-additions.yaml** (650+ lines) - Security resources (WAF, CloudTrail, etc.)

### Current Deployment Flow
```
User must:
1. Upload Lambda code to S3 manually
2. Upload lambda-stack.yaml to S3
3. Deploy master-template.yaml
```

## Target State

### Single Consolidated Template
**File**: `cfn/master-template-consolidated.yaml` (~2,500 lines)

### New Deployment Flow
```
Developer:
1. Upload solution package to S3 bucket (one-time):
   - master-template-consolidated.yaml
   - lambda/api-handler.zip
   - lambda/orchestration.zip
   - lambda/s3-cleanup.zip
   - lambda/frontend-builder.zip
   - frontend/frontend-source.zip

User:
1. Run single CloudFormation command pointing to S3-hosted template
```

## Key Changes Required

### 1. Parameter Changes

**Remove**:
```yaml
LambdaCodeBucket
LambdaCodeKey
FrontendCodeBucket
FrontendCodeKey
```

**Add**:
```yaml
SourceBucket:
  Type: String
  Description: 'S3 bucket containing deployment artifacts'
  Default: ''  # User provides or uses default
```

### 2. Lambda Function Resources

**Current** (nested stack):
```yaml
LambdaStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    TemplateURL: !Sub 'https://s3.../${LambdaCodeBucket}/lambda-stack.yaml'
```

**New** (inline):
```yaml
# Inline all IAM roles from lambda-stack.yaml
ApiHandlerRole:
  Type: AWS::IAM::Role
  # ... (110 lines)

OrchestrationRole:
  Type: AWS::IAM::Role
  # ... (150 lines)

CustomResourceRole:
  Type: AWS::IAM::Role
  # ... (50 lines)

# Inline all Lambda functions
ApiHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: lambda/api-handler.zip
    # ... rest of config

OrchestrationFunction:
  Type: AWS::Lambda::Function
  Properties:
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: lambda/orchestration.zip

S3CleanupFunction:
  Type: AWS::Lambda::Function
  Properties:
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: lambda/s3-cleanup.zip

FrontendBuilderFunction:
  Type: AWS::Lambda::Function
  Properties:
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: lambda/frontend-builder.zip

# Inline CloudWatch Log Groups
ApiHandlerLogGroup:
  Type: AWS::Logs::LogGroup
  # ...
```

### 3. Frontend Builder Custom Resource

**Update Properties**:
```yaml
FrontendBuildResource:
  Type: Custom::FrontendBuild
  Properties:
    ServiceToken: !GetAtt FrontendBuilderFunction.Arn
    BucketName: !Ref FrontendBucket
    DistributionId: !Ref CloudFrontDistribution
    FrontendCodeBucket: !Ref SourceBucket  # NEW
    FrontendCodeKey: frontend/frontend-source.zip  # NEW
    ApiEndpoint: !Sub 'https://${RestApi}.execute-api.${AWS::Region}.amazonaws.com/${ApiStage}'
    UserPoolId: !Ref UserPool
    UserPoolClientId: !Ref UserPoolClient
    IdentityPoolId: !Ref IdentityPool
    Region: !Ref AWS::Region
```

### 4. Security Resources Integration

**Merge from security-additions.yaml**:
- Add new parameters (CrossAccountRoleArns, EnableWAF, EnableCloudTrail, AllowedIPRanges)
- Add conditions (HasCrossAccountRoles, EnableWAFCondition, EnableCloudTrailCondition)
- Inline all security resources:
  - DRSCredentialsSecret (Secrets Manager)
  - WAFWebACL and related resources
  - CloudTrail and CloudTrailBucket
  - API Gateway request validation models
  - Enhanced CloudWatch alarms

### 5. Remove Nested Stack Dependencies

**Delete**:
```yaml
LambdaStack:
  Type: AWS::CloudFormation::Stack
  # ... entire resource
```

**Replace all references**:
```yaml
# Old
!GetAtt LambdaStack.Outputs.ApiHandlerFunctionArn

# New
!GetAtt ApiHandlerFunction.Arn
```

## Implementation Checklist

- [ ] Create backup of current templates
- [ ] Create new `master-template-consolidated.yaml`
- [ ] Copy master-template.yaml as base
- [ ] Add SourceBucket parameter
- [ ] Remove LambdaCodeBucket/Key, FrontendCodeBucket/Key parameters
- [ ] Inline all Lambda IAM roles from lambda-stack.yaml
- [ ] Inline all Lambda functions from lambda-stack.yaml
- [ ] Update Lambda Code properties to use SourceBucket
- [ ] Inline CloudWatch Log Groups
- [ ] Remove LambdaStack nested stack resource
- [ ] Update all !GetAtt LambdaStack.Outputs references
- [ ] Merge security-additions.yaml parameters
- [ ] Merge security-additions.yaml conditions
- [ ] Merge security-additions.yaml resources
- [ ] Merge security-additions.yaml outputs
- [ ] Update FrontendBuildResource to use SourceBucket
- [ ] Test template syntax validation
- [ ] Create deployment artifact packaging script
- [ ] Update deployment documentation

## File Structure After Consolidation

```
AWS-DRS-Orchestration/
├── cfn/
│   ├── master-template-consolidated.yaml  # NEW - Single template (~2,500 lines)
│   ├── master-template.yaml              # OLD - Keep for reference
│   ├── lambda-stack.yaml                 # OLD - No longer used
│   └── security-additions.yaml           # OLD - No longer used
├── lambda/
│   ├── api-handler/
│   ├── orchestration/
│   ├── custom-resources/
│   └── frontend-builder/
├── frontend/
│   └── src/
├── scripts/
│   ├── package-deployment.sh             # NEW - Creates deployment package
│   └── upload-to-s3.sh                   # NEW - Uploads to source bucket
└── docs/
    ├── DEPLOYMENT_GUIDE_V2.md            # NEW - Updated for consolidated template
    └── CONSOLIDATION_PLAN.md             # This file
```

## Deployment Package Structure

```
drs-orchestration-deployment/
├── master-template-consolidated.yaml
├── lambda/
│   ├── api-handler.zip
│   ├── orchestration.zip
│   ├── s3-cleanup.zip
│   └── frontend-builder.zip
└── frontend/
    └── frontend-source.zip
```

## User Deployment Commands

### Option 1: AWS CLI (Cross-Platform)
```bash
aws cloudformation create-stack \
  --stack-name drs-orchestration \
  --template-url https://my-solution-bucket.s3.amazonaws.com/master-template-consolidated.yaml \
  --parameters \
    ParameterKey=SourceBucket,ParameterValue=my-solution-bucket \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

### Option 2: AWS Console
1. CloudFormation → Create Stack
2. Specify template URL: `https://my-solution-bucket.s3.amazonaws.com/master-template-consolidated.yaml`
3. Parameters:
   - SourceBucket: `my-solution-bucket`
   - AdminEmail: `admin@example.com`
4. Capabilities: Check CAPABILITY_NAMED_IAM
5. Create Stack

## Benefits of Consolidation

✅ **Single Template** - No nested stack complexity  
✅ **S3-Hosted** - Professional deployment pattern  
✅ **Cross-Platform** - Works on Windows/Mac/Linux  
✅ **No Scripts Required** - Pure CloudFormation  
✅ **Console Compatible** - Can deploy via web console  
✅ **Version Controlled** - All infrastructure in one file  
✅ **Easy Distribution** - Share S3 bucket URL with users  

## Estimated Timeline

- Template consolidation: 2-3 hours
- Testing and validation: 1 hour
- Documentation updates: 1 hour
- **Total**: 4-5 hours

## Next Steps

1. Create `scripts/package-deployment.sh` to automate artifact packaging
2. Consolidate templates into `master-template-consolidated.yaml`
3. Test deployment with consolidated template
4. Update all documentation
5. Create user-friendly deployment guide
