# CloudFormation Template Organization Guide

## Overview

This guide documents the service-based directory structure for CloudFormation templates in the DR Orchestration Platform. The new architecture uses nested stacks organized by AWS service, improving maintainability and navigation as the platform grows.

## Directory Structure

```
cfn/
├── main-stack.yaml                    # Root orchestrator (new architecture)
├── master-template.yaml               # Legacy root template (old architecture, preserved for backward compatibility)
├── iam/
│   └── roles-stack.yaml              # IAM roles (unified + function-specific)
├── lambda/
│   └── functions-stack.yaml          # Lambda functions with conditional role assignment
├── dynamodb/
│   └── tables-stack.yaml             # DynamoDB tables (Protection Groups, Recovery Plans, etc.)
├── stepfunctions/
│   └── statemachine-stack.yaml       # Step Functions state machine
├── sns/
│   └── topics-stack.yaml             # SNS notification topics
├── eventbridge/
│   └── rules-stack.yaml              # EventBridge scheduled rules
├── s3/
│   └── buckets-stack.yaml            # S3 buckets (deployment, frontend)
├── cloudfront/
│   └── distribution-stack.yaml       # CloudFront distribution
├── apigateway/
│   ├── auth-stack.yaml               # Cognito authorizer
│   ├── core-stack.yaml               # REST API definition
│   ├── resources-stack.yaml          # API resources (/accounts, /protection-groups, etc.)
│   ├── core-methods-stack.yaml       # Core API methods
│   ├── infrastructure-methods-stack.yaml  # Infrastructure API methods
│   ├── operations-methods-stack.yaml # Operations API methods
│   └── deployment-stack.yaml         # API deployment and stage
├── cognito/
│   └── auth-stack.yaml               # Cognito user pool and identity pool
├── monitoring/
│   └── alarms-stack.yaml             # CloudWatch alarms and metric filters
└── waf/
    └── webacl-stack.yaml             # WAF web ACL
```

## Service-Based Organization Principles

### 1. One Service Per Directory

Each AWS service has its own directory containing related CloudFormation templates:

- **IAM**: All IAM roles (unified and function-specific)
- **Lambda**: All Lambda functions
- **DynamoDB**: All DynamoDB tables
- **Step Functions**: State machine definitions
- **SNS**: Notification topics
- **EventBridge**: Scheduled rules
- **S3**: Buckets for deployment and frontend
- **CloudFront**: Frontend distribution
- **API Gateway**: 7 nested stacks for complete API definition
- **Cognito**: User pool and identity pool
- **Monitoring**: CloudWatch alarms and metric filters
- **WAF**: Web ACL for API Gateway protection

### 2. Nested Stack Architecture

The `main-stack.yaml` orchestrates all nested stacks:

```yaml
Resources:
  IAMStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: !Sub "https://${DeploymentBucket}.s3.amazonaws.com/cfn/iam/roles-stack.yaml"
      Parameters:
        ProjectName: !Ref ProjectName
        Environment: !Ref Environment
        UseFunctionSpecificRoles: !Ref UseFunctionSpecificRoles
  
  LambdaStack:
    Type: AWS::CloudFormation::Stack
    DependsOn:
      - IAMStack
      - DynamoDBStack
      - SNSStack
    Properties:
      TemplateURL: !Sub "https://${DeploymentBucket}.s3.amazonaws.com/cfn/lambda/functions-stack.yaml"
      Parameters:
        ProjectName: !Ref ProjectName
        Environment: !Ref Environment
        DeploymentBucket: !Ref DeploymentBucket
        UseFunctionSpecificRoles: !Ref UseFunctionSpecificRoles
        UnifiedRoleArn: !GetAtt IAMStack.Outputs.UnifiedRoleArn
        QueryHandlerRoleArn: !GetAtt IAMStack.Outputs.QueryHandlerRoleArn
        # ... other role ARNs
```

### 3. Dependency Management

Nested stacks are created in dependency order:

1. **Independent stacks** (no dependencies):
   - IAM Stack
   - DynamoDB Stack
   - SNS Stack
   - S3 Stack
   - Cognito Stack
   - WAF Stack

2. **Lambda Stack** depends on:
   - IAM Stack (role ARNs)
   - DynamoDB Stack (table names)
   - SNS Stack (topic ARNs)

3. **Step Functions Stack** depends on:
   - Lambda Stack (function ARNs)

4. **EventBridge Stack** depends on:
   - Lambda Stack (function ARNs)

5. **CloudFront Stack** depends on:
   - S3 Stack (bucket name)

6. **API Gateway Stacks** depend on:
   - Lambda Stack (function ARNs)
   - Cognito Stack (user pool ARN)

7. **Monitoring Stack** depends on:
   - Lambda Stack (function ARNs)
   - SNS Stack (topic ARNs)

## Parameter Passing Patterns

### Standard Parameters

All nested stacks accept these standard parameters:

```yaml
Parameters:
  ProjectName:
    Type: String
    Description: Project identifier for resource naming
    Default: aws-drs-orchestration
  
  Environment:
    Type: String
    Description: Environment name
    AllowedValues:
      - dev
      - test
      - qa
      - staging
      - prod
    Default: test
```

### Service-Specific Parameters

Each nested stack accepts additional parameters specific to its service:

**IAM Stack**:
```yaml
Parameters:
  UseFunctionSpecificRoles:
    Type: String
    Description: Use function-specific IAM roles instead of unified role
    AllowedValues:
      - 'true'
      - 'false'
    Default: 'false'
```

**Lambda Stack**:
```yaml
Parameters:
  DeploymentBucket:
    Type: String
    Description: S3 bucket containing Lambda packages
  
  UnifiedRoleArn:
    Type: String
    Description: ARN of unified orchestration role
  
  QueryHandlerRoleArn:
    Type: String
    Description: ARN of query handler role
  
  # ... other role ARNs
  
  ProtectionGroupsTableName:
    Type: String
    Description: Name of Protection Groups DynamoDB table
  
  # ... other table names
  
  ExecutionAlertTopicArn:
    Type: String
    Description: ARN of execution alert SNS topic
```

**CloudFront Stack**:
```yaml
Parameters:
  FrontendBucketName:
    Type: String
    Description: Name of frontend S3 bucket
```

### Parameter Passing from Main Stack

The main stack passes parameters to nested stacks using `!Ref` and `!GetAtt`:

```yaml
LambdaStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    Parameters:
      # Standard parameters
      ProjectName: !Ref ProjectName
      Environment: !Ref Environment
      
      # Service-specific parameters
      DeploymentBucket: !Ref DeploymentBucket
      
      # Outputs from other stacks
      UnifiedRoleArn: !GetAtt IAMStack.Outputs.UnifiedRoleArn
      QueryHandlerRoleArn: !GetAtt IAMStack.Outputs.QueryHandlerRoleArn
      ProtectionGroupsTableName: !GetAtt DynamoDBStack.Outputs.ProtectionGroupsTableName
      ExecutionAlertTopicArn: !GetAtt SNSStack.Outputs.ExecutionAlertTopicArn
```

## Output Usage Patterns

### Nested Stack Outputs

Each nested stack exports outputs for use by other stacks:

**IAM Stack Outputs**:
```yaml
Outputs:
  UnifiedRoleArn:
    Description: ARN of unified orchestration role
    Value: !If [UseUnifiedRole, !GetAtt UnifiedOrchestrationRole.Arn, '']
    Export:
      Name: !Sub "${ProjectName}-unified-role-arn-${Environment}"
  
  QueryHandlerRoleArn:
    Description: ARN of query handler role
    Value: !If [UseFunctionSpecificRoles, !GetAtt QueryHandlerRole.Arn, '']
    Export:
      Name: !Sub "${ProjectName}-query-handler-role-arn-${Environment}"
```

**Lambda Stack Outputs**:
```yaml
Outputs:
  QueryHandlerFunctionArn:
    Description: ARN of query handler function
    Value: !GetAtt QueryHandlerFunction.Arn
    Export:
      Name: !Sub "${ProjectName}-query-handler-arn-${Environment}"
```

**DynamoDB Stack Outputs**:
```yaml
Outputs:
  ProtectionGroupsTableName:
    Description: Name of Protection Groups table
    Value: !Ref ProtectionGroupsTable
    Export:
      Name: !Sub "${ProjectName}-protection-groups-table-${Environment}"
  
  ProtectionGroupsTableArn:
    Description: ARN of Protection Groups table
    Value: !GetAtt ProtectionGroupsTable.Arn
    Export:
      Name: !Sub "${ProjectName}-protection-groups-table-arn-${Environment}"
```

### Main Stack Outputs

The main stack aggregates outputs from nested stacks:

```yaml
Outputs:
  ApiGatewayEndpoint:
    Description: API Gateway endpoint URL
    Value: !GetAtt APIGatewayDeploymentStack.Outputs.ApiEndpoint
    Export:
      Name: !Sub "${ProjectName}-api-endpoint-${Environment}"
  
  CloudFrontDomain:
    Description: CloudFront distribution domain name
    Value: !GetAtt CloudFrontStack.Outputs.DistributionDomain
    Export:
      Name: !Sub "${ProjectName}-cloudfront-domain-${Environment}"
  
  QueryHandlerRoleArn:
    Description: ARN of query handler role
    Value: !GetAtt IAMStack.Outputs.QueryHandlerRoleArn
    Export:
      Name: !Sub "${ProjectName}-query-handler-role-arn-${Environment}"
```

### Cross-Stack References

Stacks can reference outputs from other stacks using `!GetAtt`:

```yaml
# In main-stack.yaml
LambdaStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    Parameters:
      ProtectionGroupsTableName: !GetAtt DynamoDBStack.Outputs.ProtectionGroupsTableName
```

Or using `!ImportValue` for exported values:

```yaml
# In any template
Resources:
  MyResource:
    Type: AWS::SomeService::Resource
    Properties:
      TableName: !ImportValue
        Fn::Sub: "${ProjectName}-protection-groups-table-${Environment}"
```

## Clean Architecture Principles

### No Unused Parameters

All parameters MUST be used in the template. CloudFormation linter (cfn-lint) enforces this with rule W2001:

```yaml
# ❌ BAD: Unused parameter
Parameters:
  UnusedParameter:
    Type: String
    Description: This parameter is never referenced

# ✅ GOOD: All parameters are used
Parameters:
  ProjectName:
    Type: String
    Description: Project identifier
  
Resources:
  MyResource:
    Type: AWS::SomeService::Resource
    Properties:
      Name: !Sub "${ProjectName}-resource"
```

### No Unused Outputs

All outputs MUST be consumed by other stacks or external systems. CloudFormation linter (cfn-lint) enforces this with rule W3010:

```yaml
# ❌ BAD: Unused output
Outputs:
  UnusedOutput:
    Description: This output is never consumed
    Value: !Ref SomeResource

# ✅ GOOD: All outputs are consumed
Outputs:
  ResourceArn:
    Description: ARN of resource (consumed by main stack)
    Value: !GetAtt SomeResource.Arn
    Export:
      Name: !Sub "${ProjectName}-resource-arn-${Environment}"
```

### Minimal Parameter Passing

Only pass parameters that are actually needed by the nested stack:

```yaml
# ❌ BAD: Passing unnecessary parameters
LambdaStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    Parameters:
      ProjectName: !Ref ProjectName
      Environment: !Ref Environment
      DeploymentBucket: !Ref DeploymentBucket
      AdminEmail: !Ref AdminEmail  # Not used by Lambda stack

# ✅ GOOD: Only pass required parameters
LambdaStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    Parameters:
      ProjectName: !Ref ProjectName
      Environment: !Ref Environment
      DeploymentBucket: !Ref DeploymentBucket
```

### Consistent Naming Conventions

All resources follow consistent naming patterns:

- **IAM Roles**: `{ProjectName}-{function}-role-{Environment}`
- **Lambda Functions**: `{ProjectName}-{function}-handler-{Environment}`
- **DynamoDB Tables**: `{ProjectName}-{table-name}-{Environment}`
- **SNS Topics**: `{ProjectName}-{topic-name}-{Environment}`
- **S3 Buckets**: `{ProjectName}-{bucket-purpose}-{AccountId}-{Environment}`
- **CloudFormation Stacks**: `{ProjectName}-{Environment}`
- **Nested Stacks**: `{ProjectName}-{service}-stack-{Environment}`

### Export Name Patterns

All exports follow consistent naming patterns:

```yaml
Export:
  Name: !Sub "${ProjectName}-{resource-type}-{resource-name}-${Environment}"

# Examples:
# ${ProjectName}-query-handler-role-arn-${Environment}
# ${ProjectName}-protection-groups-table-${Environment}
# ${ProjectName}-api-endpoint-${Environment}
```

## Template Validation

All templates MUST pass validation before deployment:

### cfn-lint Validation

```bash
cfn-lint cfn/**/*.yaml
```

Common suppressions:
- **W2001**: Unused parameter (only suppress if parameter is intentionally unused for future use)
- **W3005**: Explicit DependsOn (suppress when dependency is intentional for ordering)

### cfn_nag Security Scanning

```bash
cfn_nag_scan --input-path cfn/
```

Common suppressions:
- **W11**: IAM wildcard resource (suppress for services that don't support resource-level permissions)
- **W12**: IAM wildcard action (suppress for Describe* operations)
- **W76**: IAM policy with high privilege (suppress with justification)

### Checkov Infrastructure Security Scanning

```bash
checkov -d cfn/ --framework cloudformation
```

Common suppressions:
- **CKV_AWS_158**: CloudWatch log group encryption (suppress if not required)
- **CKV_AWS_119**: DynamoDB table encryption (suppress if using default encryption)
- **CKV_AWS_173**: Lambda environment variable encryption (suppress if no sensitive data)

## Deployment Workflow

### 1. Sync Templates to S3

```bash
aws s3 sync cfn/ s3://aws-drs-orchestration-438465159935-qa/cfn/ \
  --region us-east-2 \
  --exclude "master-template.yaml" \
  --exclude "lambda-stack.yaml" \
  --exclude "eventbridge-stack.yaml"
```

### 2. Deploy Main Stack

```bash
./scripts/deploy-main-stack.sh qa --use-function-specific-roles
```

### 3. Monitor Deployment

```bash
aws cloudformation describe-stack-events \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2 \
  --max-items 20
```

### 4. Verify Nested Stacks

```bash
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --region us-east-2 \
  --query 'StackSummaries[?contains(StackName, `aws-drs-orchestration-qa`)].StackName'
```

## Troubleshooting

### Nested Stack Creation Failed

**Symptom**: Nested stack shows CREATE_FAILED status

**Diagnosis**:
```bash
aws cloudformation describe-stack-events \
  --stack-name <nested-stack-name> \
  --region us-east-2 \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
```

**Common Causes**:
- Template URL not accessible (check S3 bucket permissions)
- Invalid parameter value passed from main stack
- Resource limit exceeded (IAM roles, Lambda functions, etc.)
- Missing dependency (DependsOn not specified)

### Parameter Not Found

**Symptom**: CloudFormation error "Parameter 'X' not found"

**Diagnosis**:
- Check parameter is defined in nested stack template
- Check parameter is passed from main stack
- Check parameter name matches exactly (case-sensitive)

**Resolution**:
```yaml
# In nested stack template
Parameters:
  MyParameter:
    Type: String
    Description: My parameter description

# In main stack
MyNestedStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    Parameters:
      MyParameter: !Ref MyParameter  # Must match exactly
```

### Output Not Found

**Symptom**: CloudFormation error "Output 'X' not found"

**Diagnosis**:
- Check output is defined in nested stack template
- Check output name matches exactly (case-sensitive)
- Check nested stack completed successfully

**Resolution**:
```yaml
# In nested stack template
Outputs:
  MyOutput:
    Description: My output description
    Value: !Ref MyResource

# In main stack
MyOtherStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    Parameters:
      MyParameter: !GetAtt MyNestedStack.Outputs.MyOutput  # Must match exactly
```

### Circular Dependency

**Symptom**: CloudFormation error "Circular dependency between resources"

**Diagnosis**:
- Check DependsOn relationships form a cycle
- Check parameter passing creates a cycle

**Resolution**:
- Remove unnecessary DependsOn
- Restructure stacks to break the cycle
- Use CloudFormation exports instead of direct references

## Best Practices

### 1. Keep Templates Focused

Each template should focus on a single service or logical grouping:

- ✅ `iam/roles-stack.yaml` contains all IAM roles
- ✅ `lambda/functions-stack.yaml` contains all Lambda functions
- ❌ Don't mix IAM roles and Lambda functions in the same template

### 2. Use Consistent Parameter Names

Use the same parameter names across all templates:

- ✅ `ProjectName`, `Environment`, `DeploymentBucket`
- ❌ Don't use `Project`, `Env`, `Bucket` in some templates

### 3. Document All Parameters

Every parameter should have a clear description:

```yaml
Parameters:
  ProjectName:
    Type: String
    Description: Project identifier for resource naming (e.g., aws-drs-orchestration)
    Default: aws-drs-orchestration
```

### 4. Export Important Outputs

Export outputs that other stacks or external systems need:

```yaml
Outputs:
  ApiEndpoint:
    Description: API Gateway endpoint URL
    Value: !Sub "https://${RestApi}.execute-api.${AWS::Region}.amazonaws.com/${Environment}"
    Export:
      Name: !Sub "${ProjectName}-api-endpoint-${Environment}"
```

### 5. Use Conditions for Optional Resources

Use conditions to create resources conditionally:

```yaml
Conditions:
  UseFunctionSpecificRoles: !Equals [!Ref UseFunctionSpecificRoles, 'true']
  UseUnifiedRole: !Not [!Condition UseFunctionSpecificRoles]

Resources:
  UnifiedRole:
    Type: AWS::IAM::Role
    Condition: UseUnifiedRole
    Properties: ...
  
  QueryHandlerRole:
    Type: AWS::IAM::Role
    Condition: UseFunctionSpecificRoles
    Properties: ...
```

### 6. Validate Before Deployment

Always validate templates before deploying:

```bash
# Syntax validation
cfn-lint cfn/**/*.yaml

# Security scanning
cfn_nag_scan --input-path cfn/

# Infrastructure security
checkov -d cfn/ --framework cloudformation
```

### 7. Test in Non-Production First

Always test changes in dev/test/qa environments before production:

```bash
# Deploy to QA
./scripts/deploy-main-stack.sh qa --use-function-specific-roles

# Verify functionality
# Run integration tests
# Monitor CloudWatch Logs

# Deploy to production (only after QA validation)
./scripts/deploy-main-stack.sh prod --use-function-specific-roles
```

## Migration from Old Architecture

### Old Architecture (Flat Structure)

```
cfn/
├── master-template.yaml    # Monolithic root template
├── lambda-stack.yaml       # Lambda functions (with duplicate EventBridge rule)
├── eventbridge-stack.yaml  # EventBridge rules
└── ...                     # Other flat templates
```

### New Architecture (Service-Based Structure)

```
cfn/
├── main-stack.yaml         # Root orchestrator
├── iam/
│   └── roles-stack.yaml
├── lambda/
│   └── functions-stack.yaml  # No duplicate EventBridge rule
├── eventbridge/
│   └── rules-stack.yaml      # Consolidated EventBridge rules
└── ...                       # Service-specific directories
```

### Migration Steps

1. **Sync new templates to S3**:
   ```bash
   aws s3 sync cfn/ s3://aws-drs-orchestration-438465159935-qa/cfn/ --region us-east-2
   ```

2. **Deploy new architecture to QA**:
   ```bash
   ./scripts/deploy-main-stack.sh qa
   ```

3. **Test functionality**:
   - Run integration tests
   - Verify all Lambda functions work
   - Check CloudWatch Logs for errors

4. **Switch to function-specific roles**:
   ```bash
   ./scripts/deploy-main-stack.sh qa --use-function-specific-roles
   ```

5. **Test again**:
   - Run integration tests
   - Compare results with unified role baseline
   - Verify no AccessDenied errors

6. **Deploy to production** (after QA validation):
   ```bash
   ./scripts/deploy-main-stack.sh prod --use-function-specific-roles
   ```

### Rollback Procedure

If issues occur, rollback to unified role:

```bash
./scripts/deploy-main-stack.sh qa  # Removes --use-function-specific-roles flag
```

Or rollback to old architecture:

```bash
./scripts/deploy.sh qa  # Uses old master-template.yaml
```

## Related Documentation

- [IAM Role Reference](IAM_ROLE_REFERENCE.md) - Detailed IAM role permissions
- [QA Deployment Configuration](QA_DEPLOYMENT_CONFIGURATION.md) - QA environment setup
- [Architecture Decision Record](architecture/ADR-001-function-specific-iam-roles.md) - Design rationale
- [Deployment Guide](../docs/deployment-guide.md) - Deployment procedures
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) - Common issues and resolutions
