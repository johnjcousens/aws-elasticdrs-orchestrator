# Phase 2: Security Hardening Integration Guide

## Overview

This guide explains how to integrate Phase 2 security hardening enhancements into the AWS DRS Orchestration CloudFormation template.

## Security Features Added

### 1. AWS Secrets Manager
- **Purpose**: Secure storage for DRS credentials and cross-account role ARNs
- **Benefits**: 
  - Encrypted credential storage
  - Automatic rotation capability
  - Audit trail of access
  - Integration with IAM policies

### 2. AWS WAF (Web Application Firewall)
- **Purpose**: Protect API Gateway from common web exploits
- **Rules Implemented**:
  - **Rate Limiting**: 2,000 requests per 5 minutes per IP
  - **IP Allowlist**: Restrict access to specific IP ranges (configurable)
  - **AWS Managed Rules**: 
    - Core Rule Set (XSS, LFI, RFI protection)
    - Known Bad Inputs
    - SQL Injection protection
  - **Geo-Blocking**: Block requests from high-risk countries (CN, RU, KP)
- **Monitoring**: CloudWatch Logs for blocked requests

### 3. CloudTrail
- **Purpose**: Comprehensive audit trail for compliance
- **Scope**:
  - Management events (API calls)
  - Data events (DynamoDB, S3, Lambda invocations)
  - Multi-region support
  - Log file validation
- **Storage**: S3 bucket with 90-day retention, 30-day IA transition

### 4. API Gateway Request Validation
- **Purpose**: Input validation at API layer
- **Models**:
  - **ProtectionGroup**: Validates name, description, tag filters
  - **RecoveryPlan**: Validates waves, dependencies, actions
  - **ExecutionRequest**: Validates execution type, dry run flag
- **Benefits**: Prevent malformed requests, reduce Lambda processing

### 5. Cross-Account IAM Policies
- **Purpose**: Secure multi-account DRS operations
- **Implementation**: 
  - IAM managed policy for STS AssumeRole
  - Configurable role ARNs via parameters
  - Least privilege access

### 6. Enhanced CloudWatch Alarms
- **Metrics Monitored**:
  - API Gateway 4XX errors (>10 in 5 minutes)
  - API Gateway 5XX errors (>1 in 1 minute)
  - DynamoDB throttling
- **Action**: Send notifications to operations team

## Integration Steps

### Step 1: Add Parameters to master-template.yaml

Add these parameters to the existing Parameters section:

```yaml
  CrossAccountRoleArns:
    Type: CommaDelimitedList
    Default: ''
    Description: 'Optional: Comma-separated list of cross-account role ARNs for DRS operations'

  EnableWAF:
    Type: String
    Default: 'true'
    Description: 'Enable AWS WAF for API Gateway protection'
    AllowedValues:
      - 'true'
      - 'false'

  EnableCloudTrail:
    Type: String
    Default: 'true'
    Description: 'Enable CloudTrail logging for audit trail'
    AllowedValues:
      - 'true'
      - 'false'

  AllowedIPRanges:
    Type: CommaDelimitedList
    Default: '0.0.0.0/0'
    Description: 'Comma-separated list of allowed IP ranges for API access (CIDR notation)'
```

### Step 2: Add Conditions

Add these conditions to the Conditions section:

```yaml
  HasCrossAccountRoles: !Not [!Equals [!Select [0, !Ref CrossAccountRoleArns], '']]
  EnableWAFCondition: !Equals [!Ref EnableWAF, 'true']
  EnableCloudTrailCondition: !Equals [!Ref EnableCloudTrail, 'true']
```

### Step 3: Add Security Resources

Insert all resources from `security-additions.yaml` into the Resources section, organized by category:

1. **AWS Secrets Manager** (lines 41-90 of security-additions.yaml)
2. **AWS WAF** (lines 92-260 of security-additions.yaml)
3. **CloudTrail** (lines 262-392 of security-additions.yaml)
4. **API Gateway Models** (lines 394-520 of security-additions.yaml)
5. **Cross-Account IAM** (lines 522-548 of security-additions.yaml)
6. **CloudWatch Alarms** (lines 550-620 of security-additions.yaml)

### Step 4: Update Existing Resources

#### API Gateway Methods

Update POST methods to use request models:

```yaml
  ProtectionGroupsPostMethod:
    Type: AWS::ApiGateway::Method
    Properties:
      # ... existing properties ...
      RequestModels:
        application/json: !Ref ProtectionGroupModel
```

### Step 5: Add Security Outputs

Add these outputs to the Outputs section:

```yaml
  DRSCredentialsSecretArn:
    Description: 'Secrets Manager ARN for DRS credentials'
    Value: !Ref DRSCredentialsSecret
    Export:
      Name: !Sub '${AWS::StackName}-DRSCredentialsSecret'

  WAFWebACLArn:
    Description: 'WAF Web ACL ARN'
    Condition: EnableWAFCondition
    Value: !GetAtt WAFWebACL.Arn
    Export:
      Name: !Sub '${AWS::StackName}-WAFWebACL'

  CloudTrailArn:
    Description: 'CloudTrail ARN'
    Condition: EnableCloudTrailCondition
    Value: !GetAtt CloudTrail.Arn
    Export:
      Name: !Sub '${AWS::StackName}-CloudTrail'

  CloudTrailBucketName:
    Description: 'CloudTrail S3 Bucket Name'
    Condition: EnableCloudTrailCondition
    Value: !Ref CloudTrailBucket
    Export:
      Name: !Sub '${AWS::StackName}-CloudTrailBucket'
```

## Deployment Instructions

### Prerequisites

1. Ensure Lambda functions are packaged and uploaded to S3
2. Have admin access to AWS account
3. Prepare cross-account role ARNs (if applicable)

### Deployment Command

```bash
aws cloudformation update-stack \
  --stack-name drs-orchestration \
  --template-body file://cfn/master-template.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=drs-orchestration \
    ParameterKey=Environment,ParameterValue=prod \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
    ParameterKey=EnableWAF,ParameterValue=true \
    ParameterKey=EnableCloudTrail,ParameterValue=true \
    ParameterKey=AllowedIPRanges,ParameterValue="10.0.0.0/8\,172.16.0.0/12" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

### Validation Steps

After deployment:

1. **Verify WAF**:
   ```bash
   aws wafv2 list-web-acls --scope REGIONAL --region us-west-2
   ```

2. **Verify CloudTrail**:
   ```bash
   aws cloudtrail describe-trails --region us-west-2
   ```

3. **Verify Secrets Manager**:
   ```bash
   aws secretsmanager describe-secret \
     --secret-id drs-orchestration/drs-credentials \
     --region us-west-2
   ```

4. **Test API with WAF**:
   ```bash
   # Should succeed
   curl -X GET https://<api-id>.execute-api.us-west-2.amazonaws.com/prod/protection-groups
   
   # Rate limit test (should block after 2000 requests)
   for i in {1..2100}; do
     curl -X GET https://<api-id>.execute-api.us-west-2.amazonaws.com/prod/protection-groups
   done
   ```

5. **Verify CloudWatch Alarms**:
   ```bash
   aws cloudwatch describe-alarms \
     --alarm-names "drs-orchestration-api-4xx-errors" \
     --region us-west-2
   ```

## Security Best Practices

### 1. IP Allowlist Configuration

For production environments, restrict API access to specific IP ranges:

```yaml
AllowedIPRanges: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
```

### 2. WAF Rule Tuning

Monitor WAF logs and adjust rules as needed:

```bash
aws wafv2 get-logging-configuration \
  --resource-arn <web-acl-arn> \
  --region us-west-2
```

### 3. Secrets Rotation

Implement automatic secret rotation for DRS credentials:

```bash
aws secretsmanager rotate-secret \
  --secret-id drs-orchestration/drs-credentials \
  --rotation-lambda-arn <lambda-arn> \
  --rotation-rules AutomaticallyAfterDays=30
```

### 4. CloudTrail Analysis

Regularly review CloudTrail logs for suspicious activity:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=PutObject \
  --region us-west-2
```

### 5. Alarm Response

Configure SNS topics for alarm notifications:

```yaml
  ApiGateway5xxAlarm:
    Properties:
      AlarmActions:
        - !Ref NotificationTopic
```

## GuardDuty Integration (Manual Step)

GuardDuty cannot be enabled via CloudFormation and requires manual console configuration:

### Steps:

1. Navigate to GuardDuty console: https://console.aws.amazon.com/guardduty
2. Click "Get Started" or "Enable GuardDuty"
3. Review permissions and click "Enable GuardDuty"
4. Configure findings export to S3 (optional):
   - Go to Settings > Findings export options
   - Configure S3 bucket: `drs-orchestration-guardduty-findings-<account-id>`
   - Set KMS encryption

### GuardDuty Monitoring

GuardDuty will automatically monitor:
- CloudTrail logs for suspicious API activity
- VPC Flow Logs for network anomalies
- DNS logs for malicious domain requests

### Findings Integration

Consider integrating GuardDuty findings with:
- AWS Security Hub
- Amazon SNS for notifications
- AWS Lambda for automated response

## Cost Considerations

### Estimated Monthly Costs (us-west-2)

| Service | Usage | Cost |
|---------|-------|------|
| WAF | 2 Web ACLs, 6 rules, 1M requests | ~$10-15 |
| CloudTrail | 10K data events/month | ~$2-5 |
| Secrets Manager | 1 secret, 720 API calls | ~$0.50 |
| CloudWatch Logs | 1 GB ingested, 30-day retention | ~$1-2 |
| CloudWatch Alarms | 3 alarms | ~$0.30 |
| GuardDuty | 1 account, standard monitoring | ~$5-10 |
| **Total** | | **~$19-33/month** |

### Cost Optimization Tips

1. **Disable WAF in dev environments**: Set `EnableWAF: false`
2. **Reduce CloudTrail retention**: Use lifecycle policies
3. **Filter CloudWatch Logs**: Reduce log ingestion
4. **Use S3 Intelligent-Tiering**: For CloudTrail bucket

## Troubleshooting

### Issue: WAF blocking legitimate traffic

**Solution**: 
1. Check WAF logs in CloudWatch
2. Identify blocked rule
3. Add exception or adjust rule
4. Update IP allowlist if needed

### Issue: CloudTrail not logging

**Solution**:
1. Verify S3 bucket policy allows CloudTrail writes
2. Check trail status: `aws cloudtrail get-trail-status`
3. Verify IAM role permissions

### Issue: Secrets Manager access denied

**Solution**:
1. Verify Lambda execution role has SecretsManager permissions
2. Check resource-based policy on secret
3. Ensure KMS key policy allows decryption

## Next Steps

After Phase 2 completion:

1. **Phase 3: Operational Excellence**
   - Enhanced CloudWatch dashboards
   - X-Ray tracing
   - Automated backup strategies

2. **Phase 4: Performance Optimization**
   - DynamoDB DAX caching
   - API Gateway caching
   - Lambda memory tuning

3. **Phases 5-7: React Frontend Development**
   - Authentication flow
   - Management UI
   - Real-time execution dashboard

## References

- [AWS WAF Documentation](https://docs.aws.amazon.com/waf/)
- [CloudTrail User Guide](https://docs.aws.amazon.com/awscloudtrail/)
- [Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/)
- [API Gateway Request Validation](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-method-request-validation.html)
- [GuardDuty User Guide](https://docs.aws.amazon.com/guardduty/)
