# AWS CDK Example for DR Orchestration Platform

This directory contains a complete AWS CDK (Cloud Development Kit) example demonstrating how to deploy the AWS DRS Orchestration Platform in **headless mode** (without API Gateway, Cognito, or frontend) using TypeScript.

## Overview

This CDK application deploys the complete DR Orchestration Platform infrastructure as code, enabling:

- **Infrastructure as Code**: Define and version your DR infrastructure using TypeScript
- **Programmatic DR Operations**: Invoke Lambda functions directly via AWS SDK/CLI
- **CI/CD Integration**: Automate disaster recovery testing in deployment pipelines
- **Cost Optimization**: Deploy only the components you need (no API Gateway, Cognito, or frontend)
- **Repeatable Deployments**: Deploy identical infrastructure across multiple environments

## What Gets Deployed

### Core Infrastructure

**Lambda Functions (3):**
- `query-handler`: Read-only operations (list protection groups, recovery plans, executions)
- `execution-handler`: Recovery execution lifecycle (start, cancel, pause, resume, terminate)
- `data-management-handler`: CRUD operations (create/update/delete protection groups and plans)

**DynamoDB Tables (4):**
- `protection-groups`: Stores protection group configurations
- `recovery-plans`: Stores recovery plan definitions with waves
- `executions`: Tracks recovery execution history and status
- `target-accounts`: Manages cross-account DRS configurations

**Step Functions:**
- Wave-based orchestration state machine for coordinated recovery

**EventBridge Rules:**
- Scheduled tag synchronization (every 1 hour)
- Execution status polling (every 5 minutes)

**IAM Roles:**
- Unified orchestration role with permissions for DRS, DynamoDB, Step Functions, EC2, and cross-account operations

**SNS Topics:**
- Notification topic for execution events (optional email subscriptions)

### What's NOT Deployed (Headless Mode)

- ❌ API Gateway REST API
- ❌ Cognito User Pool
- ❌ CloudFront distribution
- ❌ S3 frontend bucket
- ❌ Web UI

## Prerequisites

### 1. Node.js and npm

Install Node.js 18.x or higher:

```bash
# Check Node.js version
node --version  # Should be v18.0.0 or higher

# Check npm version
npm --version   # Should be 9.0.0 or higher
```

**Install Node.js:**
- macOS: `brew install node`
- Ubuntu: `sudo apt install nodejs npm`
- Windows: Download from [nodejs.org](https://nodejs.org/)

### 2. AWS CDK CLI

Install the AWS CDK CLI globally:

```bash
npm install -g aws-cdk

# Verify installation
cdk --version  # Should be 2.100.0 or higher
```

### 3. AWS Credentials

Configure AWS credentials using one of these methods:

**Option A: AWS CLI Profile**
```bash
aws configure --profile dr-automation
export AWS_PROFILE=dr-automation
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1
```

**Option C: IAM Role (for EC2/ECS)**

Attach an IAM role with appropriate permissions to your compute resource.

### 4. AWS Account Bootstrap

Bootstrap your AWS account for CDK (one-time setup per account/region):

```bash
cdk bootstrap aws://ACCOUNT-ID/REGION

# Example:
cdk bootstrap aws://123456789012/us-east-1
```

This creates an S3 bucket and IAM roles needed for CDK deployments.

### 5. Lambda Function Code

The CDK stack expects Lambda function code to be available at:

```
../../lambda/query-handler/
../../lambda/execution-handler/
../../lambda/data-management-handler/
../../lambda/dr-orchestration-stepfunction/
```

Ensure these directories exist with the Lambda handler code before deploying.

## Installation

### 1. Install Dependencies

```bash
cd examples/cdk
npm install
```

This installs:
- `aws-cdk-lib`: AWS CDK library
- `constructs`: CDK constructs framework
- TypeScript and type definitions

### 2. Build TypeScript

```bash
npm run build
```

This compiles TypeScript to JavaScript in preparation for deployment.

## Configuration

### Environment Variables

Configure deployment using environment variables or CDK context:

```bash
# Set environment variables
export ENVIRONMENT=dev
export PROJECT_NAME=aws-drs-orchestration
export ADMIN_EMAIL=admin@example.com

# Or use CDK context
cdk deploy -c environment=dev -c projectName=aws-drs-orchestration -c adminEmail=admin@example.com
```

### Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Environment name (dev, test, staging, prod) | dev | No |
| `PROJECT_NAME` | Project name for resource naming | aws-drs-orchestration | No |
| `ADMIN_EMAIL` | Email for notifications | admin@example.com | Yes |
| `CDK_DEFAULT_REGION` | AWS region for deployment | us-east-1 | No |

### Customizing the Stack

Edit `bin/dr-orchestration.ts` to customize stack configuration:

```typescript
new DROrchestrationStack(app, `${projectName}-${environment}`, {
  // ... existing config ...
  
  // Enable/disable features
  enableTagSync: true,           // Enable scheduled tag sync
  enableNotifications: false,    // Enable email notifications
  
  // Add custom tags
  tags: {
    Project: 'DROrchestration',
    Environment: environment,
    CostCenter: 'IT-DR',
    Owner: 'platform-team',
  },
});
```

## Deployment

### 1. Synthesize CloudFormation Template

Preview the CloudFormation template that will be generated:

```bash
npm run synth
```

This creates a CloudFormation template in `cdk.out/` directory.

### 2. Preview Changes

See what changes will be made before deploying:

```bash
npm run diff
```

This shows a diff between your current stack and the new configuration.

### 3. Deploy Stack

Deploy the stack to AWS:

```bash
npm run deploy
```

**What happens during deployment:**
1. CDK synthesizes CloudFormation template
2. Uploads Lambda function code to S3
3. Creates/updates CloudFormation stack
4. Provisions all resources (Lambda, DynamoDB, Step Functions, etc.)
5. Outputs resource ARNs and example commands

**Deployment time:** 5-10 minutes

### 4. Verify Deployment

After deployment completes, verify resources were created:

```bash
# List Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `drs-orchestration`)].FunctionName'

# List DynamoDB tables
aws dynamodb list-tables --query 'TableNames[?contains(@, `drs-orchestration`)]'

# Describe Step Functions state machine
aws stepfunctions list-state-machines --query 'stateMachines[?contains(name, `drs-orchestration`)]'
```

## Usage Examples

### Invoking Lambda Functions Directly

After deployment, invoke Lambda functions using AWS CLI or SDK:

#### Example 1: List Protection Groups

```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-dev \
  --payload '{"operation":"list_protection_groups"}' \
  response.json

cat response.json | jq .
```

#### Example 2: Start Recovery Execution

```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-dev \
  --payload '{
    "operation": "start_execution",
    "parameters": {
      "planId": "550e8400-e29b-41d4-a716-446655440000",
      "executionType": "DRILL",
      "initiatedBy": "cdk-automation"
    }
  }' \
  response.json

cat response.json | jq .
```

#### Example 3: Create Protection Group

```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-dev \
  --payload '{
    "operation": "create_protection_group",
    "body": {
      "name": "Production Servers",
      "region": "us-east-1",
      "serverSelectionMode": "tags",
      "serverSelectionTags": {
        "Environment": "production"
      }
    }
  }' \
  response.json

cat response.json | jq .
```

### Using TypeScript SDK

```typescript
import { LambdaClient, InvokeCommand } from '@aws-sdk/client-lambda';

const lambda = new LambdaClient({ region: 'us-east-1' });

// List protection groups
const response = await lambda.send(new InvokeCommand({
  FunctionName: 'aws-drs-orchestration-query-handler-dev',
  Payload: JSON.stringify({
    operation: 'list_protection_groups'
  })
}));

const result = JSON.parse(Buffer.from(response.Payload!).toString());
console.log('Protection Groups:', result.protectionGroups);
```

### Integration with CI/CD

#### GitHub Actions Example

```yaml
name: DR Drill Test

on:
  schedule:
    - cron: '0 2 * * 1'  # Every Monday at 2 AM

jobs:
  deploy-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
      
      - name: Install CDK
        run: npm install -g aws-cdk
      
      - name: Deploy DR Infrastructure
        working-directory: examples/cdk
        run: |
          npm install
          npm run build
          cdk deploy --require-approval never
      
      - name: Run DR Drill
        run: |
          aws lambda invoke \
            --function-name aws-drs-orchestration-execution-handler-dev \
            --payload '{"operation":"start_execution","parameters":{"planId":"${{ secrets.DR_PLAN_ID }}","executionType":"DRILL","initiatedBy":"github-actions"}}' \
            response.json
          cat response.json
```

## Stack Outputs

After deployment, the stack outputs important resource information:

```bash
# View stack outputs
aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-dev \
  --query 'Stacks[0].Outputs'
```

**Example outputs:**

| Output | Description | Example Value |
|--------|-------------|---------------|
| `QueryHandlerArn` | Query Handler Lambda ARN | arn:aws:lambda:us-east-1:123456789012:function:aws-drs-orchestration-query-handler-dev |
| `ExecutionHandlerArn` | Execution Handler Lambda ARN | arn:aws:lambda:us-east-1:123456789012:function:aws-drs-orchestration-execution-handler-dev |
| `DataManagementHandlerArn` | Data Management Handler Lambda ARN | arn:aws:lambda:us-east-1:123456789012:function:aws-drs-orchestration-data-management-handler-dev |
| `OrchestrationRoleArn` | Orchestration IAM Role ARN | arn:aws:iam::123456789012:role/aws-drs-orchestration-orchestration-role-dev |
| `ExampleInvocationCommand` | Example AWS CLI command | aws lambda invoke --function-name ... |

## Updating the Stack

### Modify Configuration

Edit `bin/dr-orchestration.ts` or `lib/dr-orchestration-stack.ts` to change configuration.

### Preview Changes

```bash
npm run diff
```

### Deploy Updates

```bash
npm run deploy
```

CDK automatically detects changes and updates only modified resources.

## Destroying the Stack

### Remove All Resources

```bash
npm run destroy
```

**Warning:** This deletes all resources including DynamoDB tables. Data will be lost unless you have backups.

### Selective Deletion

To keep DynamoDB tables (data retention), modify the stack before destroying:

```typescript
// In lib/dr-orchestration-stack.ts
this.protectionGroupsTable = new dynamodb.Table(this, 'ProtectionGroupsTable', {
  // ... existing config ...
  removalPolicy: cdk.RemovalPolicy.RETAIN,  // Keep table on stack deletion
});
```

Then run:

```bash
npm run deploy  # Update stack with RETAIN policy
npm run destroy # Delete stack (tables remain)
```

## Troubleshooting

### Issue: "Cannot find module 'aws-cdk-lib'"

**Cause:** Dependencies not installed

**Solution:**
```bash
npm install
```

### Issue: "Stack is in UPDATE_ROLLBACK_FAILED state"

**Cause:** Previous deployment failed and stack is in bad state

**Solution:**
```bash
# Continue rollback
aws cloudformation continue-update-rollback \
  --stack-name aws-drs-orchestration-dev

# Wait for rollback to complete
aws cloudformation wait stack-rollback-complete \
  --stack-name aws-drs-orchestration-dev

# Retry deployment
npm run deploy
```

### Issue: "Lambda function code not found"

**Cause:** Lambda function directories don't exist at expected paths

**Solution:**

Ensure Lambda code exists at:
```
../../lambda/query-handler/index.py
../../lambda/execution-handler/index.py
../../lambda/data-management-handler/index.py
../../lambda/dr-orchestration-stepfunction/index.py
```

Or modify the stack to point to correct paths:

```typescript
this.queryHandler = new lambda.Function(this, 'QueryHandler', {
  // ... existing config ...
  code: lambda.Code.fromAsset('/path/to/your/lambda/query-handler'),
});
```

### Issue: "AccessDeniedException" when invoking Lambda

**Cause:** IAM principal lacks lambda:InvokeFunction permission

**Solution:**

Add IAM policy to your user/role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:*:*:function:aws-drs-orchestration-*"
    }
  ]
}
```

### Issue: CDK bootstrap required

**Cause:** AWS account not bootstrapped for CDK

**Solution:**
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

## Best Practices

### 1. Use Separate Environments

Deploy separate stacks for dev, test, and prod:

```bash
# Development
cdk deploy -c environment=dev

# Test
cdk deploy -c environment=test

# Production
cdk deploy -c environment=prod
```

### 2. Version Control

Commit your CDK code to version control:

```bash
git add examples/cdk/
git commit -m "feat(cdk): add DR orchestration CDK example"
```

### 3. Use CDK Context

Store environment-specific configuration in `cdk.context.json`:

```json
{
  "dev": {
    "projectName": "aws-drs-orchestration",
    "adminEmail": "dev-team@example.com",
    "enableNotifications": false
  },
  "prod": {
    "projectName": "aws-drs-orchestration",
    "adminEmail": "ops-team@example.com",
    "enableNotifications": true
  }
}
```

### 4. Monitor Costs

Tag resources for cost tracking:

```typescript
cdk.Tags.of(this).add('CostCenter', 'IT-DR');
cdk.Tags.of(this).add('Project', 'DROrchestration');
```

### 5. Enable CloudWatch Logs

Lambda functions automatically log to CloudWatch. View logs:

```bash
aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-dev --follow
```

### 6. Test Before Production

Always test in dev/test environments before deploying to production:

```bash
# Deploy to dev
cdk deploy -c environment=dev

# Test operations
aws lambda invoke --function-name aws-drs-orchestration-query-handler-dev ...

# Deploy to prod only after validation
cdk deploy -c environment=prod
```

## Cost Estimation

### Monthly Cost Breakdown (Headless Mode)

**Lambda Functions:**
- 3 functions × $0.20/million requests = ~$5-10/month
- Execution time charges: ~$10-20/month

**DynamoDB Tables:**
- 4 tables × Pay-per-request pricing = ~$5-15/month

**Step Functions:**
- State transitions: ~$5-10/month

**EventBridge:**
- Scheduled rules: Free tier covers most usage

**Total Estimated Cost:** $25-55/month

**Cost Savings vs Full Mode:** ~$100-200/month (no API Gateway, Cognito, CloudFront)

### Cost Optimization Tips

1. **Use Reserved Capacity** for DynamoDB if usage is predictable
2. **Reduce Lambda memory** if functions don't need 512 MB
3. **Adjust EventBridge schedules** to reduce invocation frequency
4. **Enable DynamoDB auto-scaling** for variable workloads
5. **Use CloudWatch Logs retention** to control log storage costs

## Additional Resources

### Documentation

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS CDK TypeScript Reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-construct-library.html)
- [DR Orchestration API Reference](../../docs/api-reference/QUERY_HANDLER_API.md)
- [Migration Guide](../../docs/guides/MIGRATION_GUIDE.md)
- [Developer Guide](../../docs/guides/DEVELOPER_GUIDE.md)

### CDK Resources

- [CDK Workshop](https://cdkworkshop.com/)
- [CDK Patterns](https://cdkpatterns.com/)
- [AWS CDK Examples](https://github.com/aws-samples/aws-cdk-examples)
- [CDK Best Practices](https://docs.aws.amazon.com/cdk/latest/guide/best-practices.html)

### DR Orchestration Resources

- [Python Examples](../python/README.md)
- [Bash Examples](../bash/README.md)
- [CloudFormation Templates](../../cfn/)
- [Lambda Function Code](../../lambda/)

## Support

For issues or questions:

1. **Check CloudWatch Logs** for Lambda execution details
2. **Review CDK synthesis output** with `npm run synth`
3. **Enable CDK debug mode** with `cdk deploy --debug`
4. **Check CloudFormation events** for deployment failures
5. **Consult API documentation** for operation details

## Contributing

To contribute improvements to this CDK example:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly in dev environment
5. Submit a pull request with detailed description

## License

This example is provided under the MIT License. See the main repository LICENSE file for details.

---

**Next Steps:**

1. ✅ Install prerequisites (Node.js, AWS CDK CLI, AWS credentials)
2. ✅ Bootstrap AWS account for CDK
3. ✅ Install dependencies with `npm install`
4. ✅ Build TypeScript with `npm run build`
5. ✅ Deploy stack with `npm run deploy`
6. ✅ Test Lambda invocations
7. ✅ Integrate with your CI/CD pipeline

For complete DR workflow examples, see the [Python examples](../python/README.md) directory.
