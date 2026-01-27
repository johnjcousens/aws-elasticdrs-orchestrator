# Frontend Rebuild Mechanism - Design

## Overview

Add a `FrontendBuildVersion` parameter to the frontend stack that automatically increments on `--frontend-only` deployments, triggering CloudFormation UPDATE events to the Custom::FrontendDeployer resource.

## Design Principles

1. **Minimal Changes**: Add only what's needed - one parameter, one property
2. **Automatic**: No manual version management required
3. **Traceable**: Version visible in CloudFormation parameters and events
4. **Safe**: Backward compatible, no stack recreation needed
5. **Standard**: Follows CloudFormation best practices for custom resources

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ deploy.sh --frontend-only                                   │
│                                                              │
│ 1. Generate timestamp version: YYYYMMDD-HHMM               │
│ 2. Pass to CloudFormation: FrontendBuildVersion=20260120   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ CloudFormation: frontend-stack.yaml                         │
│                                                              │
│ Parameters:                                                  │
│   FrontendBuildVersion: "20260120-1045"  ← NEW             │
│                                                              │
│ Resources:                                                   │
│   FrontendDeploymentResource:                               │
│     Type: Custom::FrontendDeployer                          │
│     Properties:                                              │
│       BucketName: !Ref FrontendBucket                       │
│       DistributionId: !Ref CloudFrontDistribution           │
│       FrontendBuildVersion: !Ref FrontendBuildVersion ← NEW │
│       ... (other properties)                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼ UPDATE event (version changed)
┌─────────────────────────────────────────────────────────────┐
│ frontend-deployer Lambda                                    │
│                                                              │
│ @helper.update                                              │
│ def create_or_update(event, context):                       │
│     version = properties.get('FrontendBuildVersion', 'v1')  │
│     print(f"Deploying frontend version: {version}")         │
│     # ... rebuild and deploy ...                            │
└─────────────────────────────────────────────────────────────┘
```

## Component Changes

### Component 1: frontend-stack.yaml

**Add Parameter:**
```yaml
Parameters:
  FrontendBuildVersion:
    Type: String
    Description: 'Frontend build version - auto-generated timestamp to trigger rebuilds'
    Default: 'v1'
```

**Update Custom Resource:**
```yaml
Resources:
  FrontendDeploymentResource:
    Type: Custom::FrontendDeployer
    Properties:
      ServiceToken: !Ref FrontendDeployerFunctionArn
      BucketName: !Ref FrontendBucket
      DistributionId: !Ref CloudFrontDistribution
      SourceBucket: !Ref SourceBucket
      ApiEndpoint: !Ref ApiEndpoint
      UserPoolId: !Ref UserPoolId
      UserPoolClientId: !Ref UserPoolClientId
      IdentityPoolId: !Ref IdentityPoolId
      Region: !Ref AWS::Region
      FrontendBuildVersion: !Ref FrontendBuildVersion  # NEW
```

**Add Output (for visibility):**
```yaml
Outputs:
  FrontendBuildVersion:
    Description: 'Current frontend build version'
    Value: !Ref FrontendBuildVersion
    Export:
      Name: !Sub '${AWS::StackName}-FrontendBuildVersion'
```

### Component 2: deploy.sh

**Add Version Generation Function:**
```bash
generate_frontend_version() {
    # Generate timestamp-based version: YYYYMMDD-HHMM
    date +"%Y%m%d-%H%M"
}
```

**Update --frontend-only Block:**
```bash
elif [ "$FRONTEND_ONLY" = true ]; then
    echo "  Syncing CFN templates to S3..."
    aws s3 sync cfn/ "s3://${DEPLOYMENT_BUCKET}/cfn/" --delete --quiet
    echo -e "${GREEN}  ✓ CFN templates synced${NC}"
    
    # Generate new frontend version to trigger rebuild
    FRONTEND_VERSION=$(generate_frontend_version)
    echo "  Triggering frontend rebuild (version: $FRONTEND_VERSION)..."
    
    aws cloudformation deploy \
        --template-file cfn/master-template.yaml \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            ProjectName="$PROJECT_NAME" \
            Environment="$ENVIRONMENT" \
            SourceBucket="$DEPLOYMENT_BUCKET" \
            AdminEmail="$ADMIN_EMAIL" \
            CrossAccountRoleName="$CROSS_ACCOUNT_ROLE_NAME" \
            EnableNotifications="$ENABLE_NOTIFICATIONS" \
            DeployFrontend="$DEPLOY_FRONTEND" \
            OrchestrationRoleArn="$ORCHESTRATION_ROLE_ARN" \
            FrontendBuildVersion="$FRONTEND_VERSION" \  # NEW
        --capabilities CAPABILITY_NAMED_IAM \
        --no-fail-on-empty-changeset \
        --region "$AWS_REGION" > /dev/null 2>&1
    echo -e "${GREEN}  ✓ Frontend rebuild triggered (version: $FRONTEND_VERSION)${NC}"
```

### Component 3: master-template.yaml

**Add Parameter:**
```yaml
Parameters:
  FrontendBuildVersion:
    Type: String
    Description: 'Frontend build version - auto-generated to trigger rebuilds'
    Default: 'v1'
```

**Pass to Nested Stack:**
```yaml
Resources:
  FrontendStack:
    Type: AWS::CloudFormation::Stack
    Condition: DeployFrontendCondition
    Properties:
      TemplateURL: !Sub 'https://s3.amazonaws.com/${SourceBucket}/cfn/frontend-stack.yaml'
      Parameters:
        ProjectName: !Ref ProjectName
        Environment: !Ref Environment
        BucketSuffix: !Ref BucketSuffix
        UserPoolId: !GetAtt ApiAuthStack.Outputs.UserPoolId
        UserPoolClientId: !GetAtt ApiAuthStack.Outputs.UserPoolClientId
        IdentityPoolId: !GetAtt ApiAuthStack.Outputs.IdentityPoolId
        ApiEndpoint: !GetAtt ApiGatewayDeploymentStack.Outputs.ApiEndpoint
        FrontendDeployerFunctionArn: !GetAtt LambdaStack.Outputs.FrontendDeployerFunctionArn
        SourceBucket: !Ref SourceBucket
        FrontendBuildVersion: !Ref FrontendBuildVersion  # NEW
```

### Component 4: frontend-deployer Lambda (index.py)

**Update create_or_update function:**
```python
@helper.create
@helper.update
def create_or_update(event, context):
    """Deploy pre-built frontend to S3 and invalidate CloudFront cache."""
    properties = event["ResourceProperties"]

    # Security validation for CloudFormation inputs
    bucket_name = sanitize_string_input(properties["BucketName"])
    distribution_id = sanitize_string_input(properties["DistributionId"])
    frontend_version = sanitize_string_input(
        properties.get("FrontendBuildVersion", "v1")
    )

    # Stable PhysicalResourceId prevents CloudFormation replacement behavior
    helper.PhysicalResourceId = get_physical_resource_id(bucket_name)

    log_security_event(
        "frontend_deployment_started",
        {
            "bucket_name": bucket_name,
            "distribution_id": distribution_id,
            "frontend_version": frontend_version,  # NEW
            "request_id": context.aws_request_id,
            "physical_resource_id": helper.PhysicalResourceId,
        },
    )

    print(
        f"Frontend Deployer: Deploying frontend version {frontend_version} "
        f"to bucket: {bucket_name}"
    )

    # ... rest of deployment logic ...

    return {
        "BucketName": bucket_name,
        "FilesDeployed": len(uploaded_files),
        "InvalidationId": invalidation_id,
        "BuildType": "pre-built-react",
        "ConfigFiles": "aws-config.json + aws-config.js",
        "FrontendVersion": frontend_version,  # NEW
    }
```

## Version Format

**Format:** `YYYYMMDD-HHMM`

**Examples:**
- `20260120-1045` - January 20, 2026 at 10:45 AM
- `20260120-1523` - January 20, 2026 at 3:23 PM

**Properties:**
- Human-readable
- Sortable (lexicographic order = chronological order)
- Unique per minute (sufficient for deployment frequency)
- Timezone-agnostic (uses local time of deployer)

## Deployment Flows

### Flow 1: Frontend-Only Deployment
```
1. Developer: ./scripts/deploy.sh dev --frontend-only
2. deploy.sh: Generate version "20260120-1045"
3. deploy.sh: aws cloudformation deploy --parameter-overrides FrontendBuildVersion=20260120-1045
4. CloudFormation: Detect parameter change
5. CloudFormation: Send UPDATE event to Custom::FrontendDeployer
6. frontend-deployer: Rebuild and deploy frontend
7. frontend-deployer: Invalidate CloudFront cache
8. Complete: Frontend updated with version 20260120-1045
```

### Flow 2: Full Stack Deployment
```
1. Developer: ./scripts/deploy.sh dev
2. deploy.sh: Use default FrontendBuildVersion (or omit parameter)
3. CloudFormation: Deploy all stacks
4. CloudFormation: Send CREATE/UPDATE to Custom::FrontendDeployer
5. frontend-deployer: Deploy frontend (version from parameter or default "v1")
6. Complete: Full stack deployed
```

### Flow 3: Lambda-Only Deployment
```
1. Developer: ./scripts/deploy.sh dev --lambda-only
2. deploy.sh: Update Lambda function code directly
3. No CloudFormation deployment
4. Frontend NOT rebuilt (as expected)
```

## Backward Compatibility

### Existing Stacks
- Default value "v1" ensures existing stacks work without changes
- First `--frontend-only` deployment will change "v1" → "20260120-HHMM"
- No stack recreation required
- No manual intervention needed

### Migration Path
1. Deploy code changes (adds parameter with default "v1")
2. Existing stacks continue working with "v1"
3. Next `--frontend-only` deployment auto-increments to timestamp
4. All future deployments use timestamp versions

## Error Handling

### Scenario 1: CloudFormation "No updates to perform"
**Cause:** Version didn't change (unlikely with timestamp)  
**Handling:** deploy.sh logs warning, exits successfully  
**Impact:** None - frontend already at latest version

### Scenario 2: Frontend deployment fails
**Cause:** S3 upload error, CloudFront invalidation error  
**Handling:** Lambda raises exception, CloudFormation rollback  
**Impact:** Stack remains at previous version, no data loss

### Scenario 3: Concurrent deployments
**Cause:** Two developers run `--frontend-only` simultaneously  
**Handling:** CloudFormation serializes updates, second waits  
**Impact:** Both deployments succeed sequentially

## Testing Strategy

### Unit Tests
- Test version generation format
- Test parameter passing to nested stack
- Test Lambda version logging

### Integration Tests
1. Deploy stack with default version "v1"
2. Run `--frontend-only`, verify version changes to timestamp
3. Run `--frontend-only` again, verify new timestamp
4. Verify CloudFormation events show version changes
5. Verify frontend content updated in S3

### Validation Checks
- CloudFormation parameter visible in console
- CloudFormation events show UPDATE with version
- Lambda logs show version being deployed
- Stack outputs include version

## Security Considerations

1. **Input Validation**: Version string sanitized in Lambda
2. **No User Input**: Version auto-generated, not user-provided
3. **Audit Trail**: Version logged in CloudWatch and CloudFormation
4. **No Secrets**: Version is non-sensitive metadata

## Performance Impact

- Version generation: < 1 second
- CloudFormation parameter update: ~10-30 seconds
- Frontend rebuild: ~2-3 minutes (unchanged)
- Total overhead: ~10-30 seconds

## Documentation Updates

### Deployment Guide
- Document `--frontend-only` behavior
- Explain version format
- Show how to check current version

### Troubleshooting Guide
- How to verify version in CloudFormation
- How to check Lambda logs for version
- What to do if version doesn't increment

## Success Metrics

1. ✅ `--frontend-only` triggers rebuild 100% of the time
2. ✅ Version visible in CloudFormation parameters
3. ✅ Version logged in Lambda execution
4. ✅ No manual intervention required
5. ✅ Backward compatible with existing stacks
