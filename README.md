# AWS DRS Orchestration Solution

A comprehensive serverless disaster recovery orchestration platform that provides VMware SRM-like capabilities for AWS Elastic Disaster Recovery (DRS).

## Overview

This solution enables you to define, execute, and monitor complex failover/failback procedures through a modern React-based web interface. It provides wave-based recovery orchestration with dependency management, automated health checks, and post-recovery actions.

## Key Features

- **Protection Groups**: Organize DRS source servers by tags or explicit selection
- **Recovery Plans**: Define multi-wave recovery sequences with dependencies
- **Wave Orchestration**: Execute recovery in ordered waves with automatic dependency handling
- **Automation Actions**: Pre-wave and post-wave SSM automation for health checks and application startup
- **Real-time Monitoring**: Live execution dashboard with wave progress and logs
- **Execution History**: Complete audit trail of all recovery executions
- **Cross-Account Support**: Execute recovery across multiple AWS accounts
- **Drill Mode**: Test recovery procedures without impacting production

## Architecture

### Modular CloudFormation Architecture

The solution uses a **modular nested stack architecture** for better maintainability and scalability:

| Stack | Lines | Purpose |
|-------|-------|---------|
| **master-template.yaml** | 336 | Root orchestrator coordinating all nested stacks |
| **database-stack.yaml** | 130 | DynamoDB tables (3) with encryption & PITR |
| **lambda-stack.yaml** | 408 | Lambda functions (4) + IAM roles + CloudWatch Log Groups |
| **api-stack.yaml** | 696 | Cognito User Pool, API Gateway REST API, Step Functions |
| **security-stack.yaml** | 648 | WAF, CloudTrail, Secrets Manager (optional) |
| **frontend-stack.yaml** | 361 | S3 bucket, CloudFront distribution, Custom Resources |

**Benefits**: Each template under 750 lines, single-command deployment, modular updates, professional AWS patterns.

### Components

- **Frontend**: React 18.3+ SPA with Material-UI, hosted on S3/CloudFront
- **API**: API Gateway REST API with Cognito authentication
- **Backend**: Python 3.12 Lambda functions for API and orchestration
- **Orchestration**: Step Functions for wave-based recovery execution
- **Data**: DynamoDB tables for Protection Groups, Recovery Plans, and Execution History
- **Automation**: SSM Documents for post-launch actions
- **Notifications**: SNS for execution status notifications (optional)
- **Security**: WAF for API protection, CloudTrail for audit logging (optional)

### AWS Services Used

- Amazon DynamoDB
- AWS Lambda
- AWS Step Functions
- Amazon API Gateway
- Amazon Cognito
- Amazon S3
- Amazon CloudFront
- AWS Systems Manager
- Amazon SNS
- AWS CloudFormation
- AWS IAM

## Prerequisites

- AWS CLI v2.x installed and configured
- Python 3.12+ installed locally
- Node.js 18+ and npm installed
- AWS account with appropriate permissions
- AWS DRS initialized in target region(s)
- DRS source servers configured and replicating

## Deployment

The solution uses **S3-hosted deployment** with nested CloudFormation stacks for a professional, scalable architecture.

### Deployment Methods

**Choose One**:
1. **S3-Hosted Deployment** (Recommended for production) - Professional, supports nested stacks
2. **Local Deployment** (For development/testing) - Direct deployment from local files

### Option 1: S3-Hosted Deployment (Recommended)

**Best for**: Production environments, team collaboration, repeatable deployments

#### Step 1: Package Deployment Artifacts

```bash
cd AWS-DRS-Orchestration

# Create deployment package
./scripts/package-deployment.sh

# Output: deployment-package/ directory with all templates and code
```

#### Step 2: Upload to S3

```bash
# Create S3 bucket for deployment artifacts
aws s3 mb s3://my-drs-solution-bucket --region us-west-2

# Upload deployment package
aws s3 sync deployment-package/ s3://my-drs-solution-bucket/ \
  --exclude "README.md" \
  --region us-west-2

# Verify upload
aws s3 ls s3://my-drs-solution-bucket/ --recursive
```

#### Step 3: Deploy Stack

```bash
# Deploy using S3-hosted template
aws cloudformation create-stack \
  --stack-name drs-orchestration \
  --template-url https://my-drs-solution-bucket.s3.amazonaws.com/master-template.yaml \
  --parameters \
    ParameterKey=SourceBucket,ParameterValue=my-drs-solution-bucket \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

#### Step 4: Monitor Deployment

```bash
# Wait for completion (20-30 minutes)
aws cloudformation wait stack-create-complete --stack-name drs-orchestration

# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs' \
  --output table
```

#### Step 5: Access Application

```bash
# Get CloudFront URL
aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text
```

- Open the CloudFront URL in your browser
- Check email for temporary Cognito password
- Log in and change your password

### Option 2: Local Deployment (Development/Testing)

**Best for**: Quick testing, development iterations, single deployments

```bash
cd AWS-DRS-Orchestration

# Package Lambda functions
./scripts/package-lambdas.sh

# Deploy directly from local files
aws cloudformation create-stack \
  --stack-name drs-orchestration-dev \
  --template-body file://cfn/master-template-local.yaml \
  --parameters \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

**Note**: Local deployment requires all Lambda code to be packaged locally and uploaded during stack creation.

### Detailed Deployment Instructions

For comprehensive step-by-step deployment instructions, troubleshooting, and advanced configurations, see:
- **[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[docs/MODULAR_ARCHITECTURE_COMPLETED.md](docs/MODULAR_ARCHITECTURE_COMPLETED.md)** - Architecture details

## Configuration

### DynamoDB Tables

The solution creates three DynamoDB tables:

- **Protection Groups Table**: Stores server groupings and tag-based selections
- **Recovery Plans Table**: Stores recovery plans with wave configurations
- **Execution History Table**: Stores execution results and audit logs

### IAM Roles

The solution creates the following IAM roles:

- **API Handler Role**: DynamoDB and Step Functions access
- **Orchestration Role**: DRS, EC2, SSM, and DynamoDB access
- **Custom Resource Role**: S3 and CloudFront access
- **Cognito Auth Role**: Read-only Cognito access

### Cross-Account Setup

To execute recovery in a different AWS account:

1. Create an IAM role in the target account with DRS permissions
2. Configure trust relationship to allow orchestration Lambda to assume the role
3. Use the role ARN when creating Protection Groups

Example trust policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::SOURCE_ACCOUNT:role/drs-orchestration-orchestration-role"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Usage

### Creating a Protection Group

1. Navigate to **Protection Groups** in the UI
2. Click **Create Protection Group**
3. Enter a name and description
4. Select source servers by tags or explicit selection
5. Click **Save**

### Creating a Recovery Plan

1. Navigate to **Recovery Plans**
2. Click **Create Recovery Plan**
3. Enter plan metadata (name, RPO, RTO)
4. Add waves:
   - Select Protection Group for each wave
   - Configure pre-wave actions (health checks)
   - Configure post-wave actions (application startup)
   - Set wave dependencies
5. Click **Save**

### Executing a Recovery Plan

1. Navigate to **Recovery Plans**
2. Select a plan
3. Click **Execute**
4. Choose execution type:
   - **Drill**: Test recovery without impacting production
   - **Recovery**: Actual failover to AWS
   - **Failback**: Return to source environment
5. Monitor progress in **Execution Dashboard**

### Monitoring Execution

The **Execution Dashboard** provides:

- Real-time wave progress
- Instance recovery status
- Action execution results
- CloudWatch Logs links
- Execution timeline

### Viewing History

The **Execution History** page shows:

- All past executions
- Execution status and duration
- Wave-by-wave results
- Error details for failed executions

## SSM Documents

The solution includes pre-built SSM documents:

- **post-launch-health-check**: Validates instance health post-recovery
- **application-startup**: Starts application services
- **network-validation**: Validates network connectivity

Custom SSM documents can be added and referenced in wave configurations.

## Testing

### Unit Tests

Run Lambda function unit tests:
```bash
cd tests
pytest unit/ -v --cov=../lambda
```

### Integration Tests

Test API endpoints:
```bash
pytest integration/ -v
```

### End-to-End Tests

Execute complete recovery drill:
```bash
pytest e2e/ -v
```

## Monitoring and Logging

### CloudWatch Logs

All Lambda functions log to CloudWatch:
- `/aws/lambda/drs-orchestration-api-handler`
- `/aws/lambda/drs-orchestration-orchestration`
- `/aws/lambda/drs-orchestration-s3-cleanup`
- `/aws/lambda/drs-orchestration-frontend-builder`

### CloudWatch Metrics

Monitor via CloudWatch metrics:
- Lambda invocations and errors
- API Gateway requests and latency
- DynamoDB read/write capacity
- Step Functions executions

### Alarms

Recommended CloudWatch alarms:
- API Gateway 4xx/5xx error rates
- Lambda function errors
- Step Functions execution failures
- DynamoDB throttling

## Troubleshooting

### Common Issues

**Issue**: CloudFormation stack fails during deployment
- **Solution**: Check CloudWatch Logs for Lambda errors
- **Validation**: Verify IAM permissions and service quotas

**Issue**: API Gateway returns 403 Forbidden
- **Solution**: Verify Cognito token is valid and not expired
- **Validation**: Test with `aws cognito-idp initiate-auth`

**Issue**: DRS recovery fails
- **Solution**: Verify source servers are ready for recovery
- **Validation**: Check DRS console for replication status

**Issue**: Frontend build fails
- **Solution**: Verify Node.js 18+ is available
- **Validation**: Check frontend-builder Lambda logs

### Debug Mode

Enable verbose logging in Lambda functions:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Security

### Authentication

- Cognito User Pools for user authentication
- Email verification for user registration
- Password policies enforced (8+ chars, mixed case, numbers, symbols)

### Authorization

- API Gateway Cognito authorizer validates tokens
- IAM roles follow least privilege principle
- Resource-level permissions for DynamoDB operations

### Encryption

- DynamoDB tables encrypted at rest (AWS managed keys)
- S3 buckets encrypted with AES256
- CloudWatch Logs encrypted
- All data in transit uses TLS 1.2+

### Best Practices

- Use MFA for admin users
- Rotate Cognito user passwords regularly
- Review IAM role permissions quarterly
- Enable CloudTrail for API audit logging
- Use VPC endpoints for private API access

## Cost Optimization

### Estimated Monthly Costs

For typical usage (10 executions/month):
- DynamoDB: $1-5 (on-demand pricing)
- Lambda: $5-10 (based on execution time)
- Step Functions: $0.25 per 1000 state transitions
- API Gateway: $3.50 per million requests
- CloudFront: $0.085 per GB + $0.01 per 10K requests
- S3: $0.023 per GB storage
- Cognito: Free tier covers up to 50K MAUs

**Total estimated cost**: $10-30/month for typical usage

### Cost Reduction Tips

1. Use DynamoDB on-demand pricing for variable workloads
2. Set CloudWatch Logs retention to 7-30 days
3. Enable CloudFront caching to reduce S3 requests
4. Use Step Functions Express workflows for high-volume scenarios
5. Clean up old execution history records

## Roadmap

### Planned Features

- [ ] Automated failback orchestration
- [ ] Multi-region recovery support
- [ ] Recovery plan templates
- [ ] Custom metrics and dashboards
- [ ] Slack/Teams integration for notifications
- [ ] Recovery time analytics
- [ ] Automated compliance reporting
- [ ] Integration with AWS Backup

## Support

For issues, questions, or feature requests:
- Check the troubleshooting guide above
- Review CloudWatch Logs for error details
- Open an issue in the repository

## License

This solution is provided as-is for use in AWS environments.

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Acknowledgments

Built with:
- AWS CloudFormation
- AWS SAM (Serverless Application Model)
- React and Material-UI
- Python 3.12 and boto3

---

**Version**: 1.0.0-beta  
**Last Updated**: November 8, 2025

**Status**: **Modular Architecture Complete** - Production-ready nested stack architecture with S3-hosted deployment
