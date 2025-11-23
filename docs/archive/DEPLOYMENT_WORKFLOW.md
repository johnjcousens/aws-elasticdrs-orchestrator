# Deployment Workflow - CloudFormation Sync Guide

**Last Updated**: November 22, 2025 (Session 46)

## Overview

This guide ensures local CloudFormation templates and AWS deployments stay synchronized, following infrastructure-as-code best practices.

## Core Principle

**CloudFormation is the single source of truth for infrastructure**
- All IAM permissions, resources, and configurations defined in CloudFormation templates
- Direct AWS console/CLI changes should be avoided
- Template updates trigger stack updates to maintain sync

## Deployment Workflow

### 1. Code-Only Changes (Fast Iteration)

**When**: Updating Lambda function code without infrastructure changes

**Process**:
```bash
# Update lambda/index.py
cd lambda
python3 build_and_deploy.py

# Deploys Lambda code directly
# Infrastructure remains unchanged
```

**Pros**: Fast iteration during development
**Cons**: Doesn't update CloudFormation template
**Use Case**: Bug fixes, feature development, rapid testing

### 2. Infrastructure Changes (IAM, Resources, Config)

**When**: Adding IAM permissions, changing resources, updating configurations

**Process**:
```bash
# 1. Update local CloudFormation template
# Example: cfn/lambda-stack.yaml (add DRS permissions)

# 2. Update CloudFormation stack
aws cloudformation update-stack \
  --stack-name drs-orchestration-test \
  --template-body file://cfn/master-template.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=Environment,UsePreviousValue=true \
    ParameterKey=ProjectName,UsePreviousValue=true \
    ParameterKey=AdminEmail,UsePreviousValue=true \
    ParameterKey=NotificationEmail,UsePreviousValue=true \
    ParameterKey=SourceBucket,UsePreviousValue=true \
    ParameterKey=CognitoDomainPrefix,UsePreviousValue=true \
    ParameterKey=EnableWAF,UsePreviousValue=true \
    ParameterKey=EnableCloudTrail,UsePreviousValue=true \
    ParameterKey=EnableSecretsManager,UsePreviousValue=true

# 3. Wait for completion
aws cloudformation wait stack-update-complete --stack-name drs-orchestration-test

# 4. Verify changes applied
aws cloudformation describe-stack-events --stack-name drs-orchestration-test \
  --max-items 20 --output table
```

**Pros**: Maintains IaC, audit trail, drift detection
**Cons**: Slower than direct updates
**Use Case**: IAM changes, resource additions, configuration updates

### 3. Full Stack Update (Production Releases)

**When**: Major releases, ensuring complete sync

**Process**:
```bash
# Update ALL CloudFormation templates
# Update Lambda code
# Deploy via CloudFormation stack update
# Verify all resources updated
```

**Use Case**: Production deployments, quarterly releases, major versions

## Session 46 Example - DRS Integration

**What We Did**:
1. ✅ Updated `lambda/index.py` with DRS integration code
2. ✅ Updated `cfn/lambda-stack.yaml` with DRS IAM permissions
3. ✅ Deployed Lambda code directly (`python3 build_and_deploy.py`)
4. ✅ Updated CloudFormation stack to apply IAM permissions
5. ✅ Verified DRS permissions in Lambda execution role

**Result**: Local templates and AWS deployment fully synchronized

## Best Practices

### ✅ DO
- Update CloudFormation templates for infrastructure changes
- Use CloudFormation stack updates for IAM permission changes
- Verify changes applied after stack updates
- Document deployment decisions
- Commit template changes to git before deploying

### ❌ DON'T
- Update IAM permissions manually in AWS console
- Skip CloudFormation updates for infrastructure changes
- Assume direct Lambda deployments update templates
- Ignore CloudFormation drift detection warnings

## Verification Commands

### Check Stack Status
```bash
aws cloudformation describe-stacks --stack-name drs-orchestration-test \
  --query 'Stacks[0].StackStatus' --output text
```

### List Stack Resources
```bash
aws cloudformation list-stack-resources --stack-name drs-orchestration-test \
  --output table
```

### Check IAM Permissions
```bash
# Get Lambda role name
ROLE_NAME=$(aws lambda get-function \
  --function-name drs-orchestration-orchestration-test \
  --query 'Configuration.Role' --output text | awk -F'/' '{print $NF}')

# List inline policies
aws iam list-role-policies --role-name $ROLE_NAME --output table

# Get specific policy
aws iam get-role-policy --role-name $ROLE_NAME --policy-name DRSAccess
```

### Detect Template Drift
```bash
# Initiate drift detection
DETECTION_ID=$(aws cloudformation detect-stack-drift \
  --stack-name drs-orchestration-test \
  --query 'StackDriftDetectionId' --output text)

# Check results
aws cloudformation describe-stack-drift-detection-status \
  --stack-drift-detection-id $DETECTION_ID
```

## Current Stack Parameters

```
Environment          = test
ProjectName          = drs-orchestration
AdminEmail           = test-admin@example.com
NotificationEmail    = (empty)
SourceBucket         = aws-drs-orchestration
CognitoDomainPrefix  = (empty)
EnableWAF            = true
EnableCloudTrail     = true
EnableSecretsManager = true
```

## Troubleshooting

### "No updates are to be performed"
- CloudFormation detected no changes
- Templates match deployed stack
- This is expected if no infrastructure changes

### "Parameter validation failed"
- Check all parameter keys exist in template
- Use `UsePreviousValue=true` for unchanged parameters
- Verify parameter constraints in template

### Stack Update Rollback
- Check CloudFormation events for error details
- Review IAM permissions for CloudFormation role
- Verify template syntax with `aws cloudformation validate-template`

## Future Enhancements

- **CI/CD Pipeline**: Automate CloudFormation updates on git push
- **Change Sets**: Preview changes before applying
- **Blue/Green Deployments**: Zero-downtime updates
- **Automated Drift Detection**: Scheduled drift checks

## Related Documentation

- `docs/DEPLOYMENT_AND_OPERATIONS_GUIDE.md` - Operations guide
- `docs/ARCHITECTURAL_DESIGN_DOCUMENT.md` - System architecture
- `cfn/master-template.yaml` - Main CloudFormation template
- `lambda/build_and_deploy.py` - Lambda deployment script
