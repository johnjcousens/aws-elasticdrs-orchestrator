# CloudFormation UPDATE_ROLLBACK_COMPLETE Troubleshooting Guide

## Overview

When CloudFormation stacks enter `UPDATE_ROLLBACK_COMPLETE` state, they cannot be updated further and must be deleted and recreated. This guide identifies common causes and prevention strategies.

## Common Causes

### 1. DynamoDB Permission Issues
**Symptom**: CodeBuild projects fail during deployment with DynamoDB access errors.

**Root Cause**: Missing `dynamodb:ListTagsOfResource` permission in CodeBuild service role.

**Fix Applied**: Added to `cfn/codebuild-projects-stack.yaml`:
```yaml
- Effect: Allow
  Action:
    - dynamodb:ListTagsOfResource
  Resource: '*'
```

### 2. Resource Naming Conflicts
**Symptom**: Resources fail to create during stack updates due to naming conflicts.

**Root Cause**: 
- Hardcoded resource names conflict with existing resources
- IAM roles/policies with duplicate names
- DynamoDB tables with conflicting names

**Prevention**:
- Use CloudFormation intrinsic functions for naming: `!Sub '${ProjectName}-${Environment}-resource'`
- Avoid hardcoded resource names
- Use unique prefixes for each environment

### 3. Parameter Changes Requiring Replacement
**Symptom**: Stack updates fail when parameter changes require resource replacement.

**Root Cause**: CloudFormation cannot replace resources due to:
- Dependencies preventing deletion of old resources
- New resources conflicting with existing ones
- Service limits preventing creation of replacement resources

**Prevention**:
- Review CloudFormation documentation for properties that require replacement
- Use `UpdateReplacePolicy: Delete` for resources that can be safely replaced
- Test parameter changes in development environment first

### 4. IAM Role Update Conflicts
**Symptom**: IAM roles fail to update while services are actively using them.

**Root Cause**: Active Lambda functions or other services prevent IAM role updates.

**Prevention**:
- Use separate IAM roles for different services
- Avoid updating IAM roles during active deployments
- Use CloudFormation conditions to control IAM role creation/updates

### 5. S3 Bucket Deletion Failures
**Symptom**: S3 buckets fail to delete due to versioned objects or delete markers.

**Root Cause**: Versioned S3 buckets cannot be deleted until all versions and delete markers are removed.

**Fix**:
```bash
# Empty versioned bucket completely
aws s3api list-object-versions --bucket BUCKET_NAME --output json | \
jq -r '.Versions[]? | "--version-id \(.VersionId) \(.Key)"' | \
xargs -I {} aws s3api delete-object --bucket BUCKET_NAME {}

aws s3api list-object-versions --bucket BUCKET_NAME --output json | \
jq -r '.DeleteMarkers[]? | "--version-id \(.VersionId) \(.Key)"' | \
xargs -I {} aws s3api delete-object --bucket BUCKET_NAME {}

# Force delete bucket
aws s3 rb s3://BUCKET_NAME --force
```

## Prevention Strategies

### 1. Use Unique Resource Names
```yaml
# Good - uses intrinsic functions
UserPool:
  Type: AWS::Cognito::UserPool
  Properties:
    UserPoolName: !Sub '${ProjectName}-users-${Environment}'

# Bad - hardcoded name
UserPool:
  Type: AWS::Cognito::UserPool
  Properties:
    UserPoolName: 'aws-drs-orchestrator-users'
```

### 2. Set Appropriate Deletion Policies
```yaml
DatabaseStack:
  Type: AWS::CloudFormation::Stack
  DeletionPolicy: Delete
  UpdateReplacePolicy: Delete
```

### 3. Use Conditions for Optional Resources
```yaml
Conditions:
  EnableCICDCondition: !Equals [!Ref EnableAutomatedDeployment, 'true']

CodeCommitStack:
  Type: AWS::CloudFormation::Stack
  Condition: EnableCICDCondition
```

### 4. Test in Development Environment
- Always test parameter changes in development environment first
- Use separate environments (dev, test, prod) with unique naming
- Validate CloudFormation templates before deployment

## Recovery Procedures

### When Stack is in UPDATE_ROLLBACK_COMPLETE State

1. **Identify Failed Resources**:
```bash
aws cloudformation describe-stack-events --stack-name STACK_NAME \
  --query 'StackEvents[?ResourceStatus==`UPDATE_FAILED`]'
```

2. **Check for S3 Bucket Issues**:
```bash
# List all buckets for the project
aws s3 ls | grep PROJECT_NAME

# Empty versioned buckets
aws s3api list-object-versions --bucket BUCKET_NAME
```

3. **Delete and Recreate Stack**:
```bash
# Delete stack (may require manual S3 bucket cleanup)
aws cloudformation delete-stack --stack-name STACK_NAME

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name STACK_NAME

# Deploy fresh stack
aws cloudformation create-stack --stack-name STACK_NAME \
  --template-url https://s3.amazonaws.com/BUCKET/cfn/master-template.yaml \
  --parameters ParameterKey=AdminEmail,ParameterValue=admin@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

## Monitoring and Alerts

### CloudWatch Alarms for Stack Failures
```yaml
StackFailureAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub '${ProjectName}-stack-failure-${Environment}'
    AlarmDescription: 'Alert when CloudFormation stack fails'
    MetricName: 'StackUpdateFailure'
    Namespace: 'AWS/CloudFormation'
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 1
    ComparisonOperator: GreaterThanOrEqualToThreshold
```

### SNS Notifications for Stack Events
```yaml
StackEventsTopic:
  Type: AWS::SNS::Topic
  Properties:
    TopicName: !Sub '${ProjectName}-stack-events-${Environment}'
    Subscription:
      - Protocol: email
        Endpoint: !Ref AdminEmail
```

## Best Practices

1. **Always use unique resource names with environment prefixes**
2. **Set appropriate deletion and update policies**
3. **Test all changes in development environment first**
4. **Monitor CloudFormation events and set up alerts**
5. **Keep S3 buckets clean and empty versioned buckets before deletion**
6. **Use CloudFormation conditions for optional resources**
7. **Avoid hardcoded resource names and ARNs**
8. **Review CloudFormation documentation for properties requiring replacement**

## Emergency Contacts

- **AWS Support**: For critical production issues
- **DevOps Team**: For deployment and infrastructure issues
- **Development Team**: For application-specific problems

## Related Documentation

- [CloudFormation Troubleshooting Guide](CLOUDFORMATION_TROUBLESHOOTING.md)
- [S3 Bucket Management Guide](S3_BUCKET_MANAGEMENT.md)
- [IAM Role Management Guide](IAM_ROLE_MANAGEMENT.md)
- [Development Workflow Guide](../DEVELOPMENT_WORKFLOW_GUIDE.md)