# Python Examples for AWS DRS Orchestration Platform

This directory contains Python examples demonstrating how to use the AWS DRS Orchestration Platform with direct Lambda invocation (headless mode).

## Overview

These examples show how to interact with the DRS Orchestration Platform programmatically using the AWS SDK (boto3) without requiring API Gateway or Cognito authentication. This is ideal for:

- **Infrastructure as Code**: Integrate DR operations into Terraform, CDK, or CloudFormation
- **CI/CD Pipelines**: Automate disaster recovery testing in deployment workflows
- **Automation Scripts**: Build custom DR automation and monitoring tools
- **Scheduled Operations**: Run DR drills on a schedule using EventBridge or cron

## Prerequisites

### 1. Python Environment

- Python 3.8 or higher
- boto3 library

Install dependencies:

```bash
pip install boto3
```

### 2. AWS Credentials

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

**Option C: IAM Role (Recommended for EC2/ECS/Lambda)**

Attach an IAM role with the required permissions to your compute resource. No credentials needed in code.

### 3. IAM Permissions

Your IAM principal (user, role, or service) needs permission to invoke the DRS Orchestration Lambda functions.

**Required IAM Policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": [
        "arn:aws:lambda:*:*:function:aws-drs-orchestration-query-handler-*",
        "arn:aws:lambda:*:*:function:aws-drs-orchestration-execution-handler-*",
        "arn:aws:lambda:*:*:function:aws-drs-orchestration-data-management-handler-*"
      ]
    }
  ]
}
```

**Attach Policy to IAM User:**

```bash
aws iam put-user-policy \
  --user-name dr-automation-user \
  --policy-name DRSOrchestrationInvoke \
  --policy-document file://iam-policy.json
```

**Attach Policy to IAM Role:**

```bash
aws iam put-role-policy \
  --role-name dr-automation-role \
  --policy-name DRSOrchestrationInvoke \
  --policy-document file://iam-policy.json
```

## Examples

### 1. Complete DR Workflow (`complete_dr_workflow.py`)

A comprehensive example demonstrating a full disaster recovery workflow from start to finish.

**Features:**
- List protection groups and recovery plans
- Start a recovery execution (DRILL or RECOVERY mode)
- Monitor execution progress in real-time
- Get recovery instance details
- Terminate recovery instances after testing

**Usage:**

```bash
# List available recovery plans
python complete_dr_workflow.py --list-plans

# Run complete DR drill workflow
python complete_dr_workflow.py --plan-id 550e8400-e29b-41d4-a716-446655440000

# Run in different environment
python complete_dr_workflow.py --plan-id <plan-id> --environment dev

# Run actual recovery (not drill)
python complete_dr_workflow.py --plan-id <plan-id> --execution-type RECOVERY

# Enable debug logging
python complete_dr_workflow.py --plan-id <plan-id> --debug
```

**Example Output:**

```
================================================================================
STARTING COMPLETE DR WORKFLOW - DRILL MODE
================================================================================

[Step 1/6] Getting recovery plan details...
✓ Plan: Production DR Plan
  Protection Group: Production Servers
  Waves: 3
    - Wave 1: Database Tier (2 servers)
    - Wave 2: Application Tier (5 servers)
    - Wave 3: Web Tier (3 servers)

[Step 2/6] Starting DRILL execution...
✓ Execution started: 7c9e6679-7425-40de-944b-e07fc1f90ae7
  Status: PENDING

[Step 3/6] Monitoring execution progress...
  (Press Ctrl+C to stop monitoring and continue to next step)
  [12:00:15] Status: RUNNING, Wave: 1/3
  [12:00:45] Status: RUNNING, Wave: 2/3
  [12:01:15] Status: RUNNING, Wave: 3/3
  [12:01:45] Status: COMPLETED, Wave: 3/3
  Execution finished with status: COMPLETED

[Step 4/6] Getting final execution status...
✓ Execution Status: COMPLETED
  Current Wave: 3/3
    - Wave 1 - Database Tier: COMPLETED (2/2 servers)
    - Wave 2 - Application Tier: COMPLETED (5/5 servers)
    - Wave 3 - Web Tier: COMPLETED (3/3 servers)

[Step 5/6] Getting recovery instance details...
✓ Found 10 recovery instances:

  Instance: db-server-01
    EC2 ID: i-0123456789abcdef0
    State: running
    Type: r5.large
    Region: us-east-1
    Private IP: 10.0.1.100
    Public IP: N/A
    Wave: Wave 1 - Database Tier

  [... additional instances ...]

[Step 6/6] Terminating recovery instances...
  Terminate 10 recovery instances? (yes/no): yes
✓ Termination initiated: TERMINATING
  Total instances: 10
    - Job drsjob-abc123: 10 instances in us-east-1

================================================================================
WORKFLOW COMPLETED SUCCESSFULLY
================================================================================
```

**Command-Line Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--plan-id` | Recovery plan ID to execute | Required (unless --list-plans) |
| `--list-plans` | List all available recovery plans | - |
| `--environment` | Deployment environment (dev, test, staging, prod) | test |
| `--region` | AWS region | us-east-1 |
| `--execution-type` | DRILL or RECOVERY | DRILL |
| `--debug` | Enable debug logging | False |

## Using the DROrchestrationClient Class

The `complete_dr_workflow.py` script includes a reusable `DROrchestrationClient` class that you can import into your own scripts:

```python
from complete_dr_workflow import DROrchestrationClient

# Initialize client
client = DROrchestrationClient(environment='test', region='us-east-1')

# List protection groups
groups = client.list_protection_groups()
for group in groups:
    print(f"{group['name']}: {group['serverCount']} servers")

# List recovery plans
plans = client.list_recovery_plans()
for plan in plans:
    print(f"{plan['name']}: {len(plan.get('waves', []))} waves")

# Start execution
result = client.start_execution(
    plan_id='550e8400-e29b-41d4-a716-446655440000',
    execution_type='DRILL',
    initiated_by='my-automation-script'
)
execution_id = result['executionId']

# Monitor execution
while True:
    execution = client.get_execution(execution_id)
    status = execution['status']
    print(f"Status: {status}")
    
    if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
        break
    
    time.sleep(30)

# Get recovery instances
instances = client.get_recovery_instances(execution_id)
print(f"Launched {instances['instanceCount']} instances")

# Terminate instances
client.terminate_instances(execution_id)
```

## Available Client Methods

### Query Operations

| Method | Description | Returns |
|--------|-------------|---------|
| `list_protection_groups()` | List all protection groups | List of protection groups |
| `get_protection_group(group_id)` | Get protection group details | Protection group dict |
| `list_recovery_plans()` | List all recovery plans | List of recovery plans |
| `get_recovery_plan(plan_id)` | Get recovery plan details | Recovery plan dict with waves |
| `list_executions(status=None)` | List executions (optionally filtered) | List of executions |
| `get_execution(execution_id)` | Get execution details | Execution dict with wave status |

### Execution Operations

| Method | Description | Returns |
|--------|-------------|---------|
| `start_execution(plan_id, execution_type, initiated_by)` | Start new execution | Execution start response |
| `cancel_execution(execution_id, reason='')` | Cancel running execution | Cancellation response |
| `pause_execution(execution_id, reason='')` | Pause execution at next wave | Pause response |
| `resume_execution(execution_id)` | Resume paused execution | Resume response |
| `get_recovery_instances(execution_id)` | Get recovery instance details | Instances dict |
| `terminate_instances(execution_id)` | Terminate recovery instances | Termination response |

## Error Handling

All client methods raise exceptions on errors. Wrap calls in try-except blocks:

```python
try:
    result = client.start_execution(
        plan_id='invalid-plan-id',
        execution_type='DRILL',
        initiated_by='test'
    )
except Exception as e:
    print(f"Failed to start execution: {str(e)}")
    # Handle error appropriately
```

Common error scenarios:

- **NOT_FOUND**: Resource (plan, execution, group) doesn't exist
- **INVALID_PARAMETER**: Invalid parameter value
- **INVALID_STATE**: Operation not valid for current state (e.g., can't pause completed execution)
- **ALREADY_EXISTS**: Plan already has active execution
- **AUTHORIZATION_FAILED**: IAM principal lacks lambda:InvokeFunction permission

## Integration Examples

### CI/CD Pipeline (GitHub Actions)

```yaml
name: DR Drill Test

on:
  schedule:
    - cron: '0 2 * * 1'  # Every Monday at 2 AM
  workflow_dispatch:

jobs:
  dr-drill:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install Dependencies
        run: pip install boto3
      
      - name: Run DR Drill
        run: |
          python examples/python/complete_dr_workflow.py \
            --plan-id ${{ secrets.DR_PLAN_ID }} \
            --execution-type DRILL \
            --environment test
```

### Terraform Data Source

```hcl
# Use external data source to invoke Lambda
data "external" "recovery_plans" {
  program = ["python3", "${path.module}/get_recovery_plans.py"]
}

# get_recovery_plans.py
import boto3
import json

client = boto3.client('lambda', region_name='us-east-1')
response = client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    Payload=json.dumps({"operation": "list_recovery_plans"})
)

result = json.loads(response['Payload'].read())
print(json.dumps({"plans": json.dumps(result['recoveryPlans'])}))
```

### AWS Lambda Function

```python
import boto3
import json

def lambda_handler(event, context):
    """
    Lambda function to start DR drill on schedule.
    """
    lambda_client = boto3.client('lambda')
    
    # Start DR drill
    response = lambda_client.invoke(
        FunctionName='aws-drs-orchestration-execution-handler-prod',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "operation": "start_execution",
            "parameters": {
                "planId": "550e8400-e29b-41d4-a716-446655440000",
                "executionType": "DRILL",
                "initiatedBy": "scheduled-lambda"
            }
        })
    )
    
    result = json.loads(response['Payload'].read())
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'executionId': result['executionId'],
            'status': result['status']
        })
    }
```

## Troubleshooting

### Issue: "AccessDeniedException" or "User is not authorized"

**Cause**: IAM principal lacks lambda:InvokeFunction permission

**Solution**:
1. Verify IAM policy is attached to your user/role
2. Check Lambda resource-based policy allows your principal
3. Test with AWS CLI:

```bash
aws lambda get-policy \
  --function-name aws-drs-orchestration-query-handler-test \
  --query 'Policy' --output text | jq .
```

### Issue: "Function not found"

**Cause**: Lambda function doesn't exist or wrong environment/region

**Solution**:
1. Verify environment parameter matches your deployment (dev, test, staging, prod)
2. Verify region parameter matches where Lambda functions are deployed
3. List Lambda functions:

```bash
aws lambda list-functions \
  --query 'Functions[?contains(FunctionName, `drs-orchestration`)].FunctionName'
```

### Issue: "NOT_FOUND: Recovery plan not found"

**Cause**: Plan ID doesn't exist or is in different environment

**Solution**:
1. List available plans:

```bash
python complete_dr_workflow.py --list-plans --environment test
```

2. Verify plan ID is correct
3. Check you're using the correct environment

### Issue: "ALREADY_EXISTS: Plan already has active execution"

**Cause**: Recovery plan already has a running execution

**Solution**:
1. Wait for current execution to complete
2. Or cancel the current execution:

```python
client.cancel_execution(execution_id='current-execution-id')
```

3. Check active executions:

```python
executions = client.list_executions(status='RUNNING')
```

## Best Practices

1. **Use DRILL mode for testing**: Always use `execution_type='DRILL'` for testing. Use `RECOVERY` only for actual disaster recovery.

2. **Monitor execution progress**: Don't assume execution completes immediately. Monitor status until terminal state.

3. **Terminate instances after drills**: Always terminate recovery instances after drill completion to avoid unnecessary costs.

4. **Handle errors gracefully**: Wrap all API calls in try-except blocks and handle errors appropriately.

5. **Use IAM roles over access keys**: When running on AWS compute (EC2, ECS, Lambda), use IAM roles instead of hardcoded credentials.

6. **Log all operations**: Enable logging to track DR operations for audit and troubleshooting.

7. **Test in non-production first**: Always test DR workflows in dev/test environments before running in production.

## Additional Resources

- [API Reference Documentation](../../docs/api-reference/QUERY_HANDLER_API.md)
- [Execution Handler API](../../docs/api-reference/EXECUTION_HANDLER_API.md)
- [Migration Guide](../../docs/guides/MIGRATION_GUIDE.md)
- [IAM Policy Documentation](../../docs/iam/ORCHESTRATION_ROLE_POLICY.md)
- [Developer Guide](../../docs/guides/DEVELOPER_GUIDE.md)

## Support

For issues or questions:
1. Check CloudWatch Logs for Lambda execution details
2. Enable debug logging with `--debug` flag
3. Review error messages and consult API documentation
4. Check IAM permissions and Lambda resource policies
