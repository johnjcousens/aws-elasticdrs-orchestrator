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

### Components

- **Frontend**: React 18.3+ SPA with Material-UI, hosted on S3/CloudFront
- **API**: API Gateway REST API with Cognito authentication
- **Backend**: Python 3.12 Lambda functions for API and orchestration
- **Orchestration**: Step Functions for wave-based recovery execution
- **Data**: DynamoDB tables for Protection Groups, Recovery Plans, and Execution History
- **Automation**: SSM Documents for post-launch actions
- **Notifications**: SNS for execution status notifications

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

### Quick Start

1. **Clone the repository and navigate to the project directory**:
   ```bash
   cd AWS-DRS-Orchestration
   ```

2. **Update parameters**:
   Edit `parameters.json` and set your admin email:
   ```json
   {
     "ParameterKey": "AdminEmail",
     "ParameterValue": "your-email@example.com"
   }
   ```

3. **Deploy the stack**:
   ```bash
   aws cloudformation create-stack \
     --stack-name drs-orchestration \
     --template-body file://cfn/master-template.yaml \
     --parameters file://parameters.json \
     --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
     --region us-west-2
   ```

4. **Monitor deployment**:
   ```bash
   aws cloudformation wait stack-create-complete --stack-name drs-orchestration
   aws cloudformation describe-stacks --stack-name drs-orchestration --query 'Stacks[0].Outputs'
   ```

5. **Access the application**:
   - Get the CloudFront URL from stack outputs
   - Check your email for Cognito temporary password
   - Log in and change your password

### Manual Deployment

For detailed step-by-step deployment instructions, see [docs/deployment-guide.md](docs/deployment-guide.md).

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

**Status**: Phase 6 Complete (90% MVP) - Production-ready UI with full CRUD operations
