# Bash Examples for AWS DRS Orchestration Platform

This directory contains Bash scripts demonstrating how to integrate the AWS DRS Orchestration Platform into CI/CD pipelines for automated disaster recovery testing.

## Overview

These examples show how to use AWS CLI and direct Lambda invocation to automate DR operations in CI/CD workflows. This is ideal for:

- **Automated DR Testing**: Run DR drills as part of deployment pipelines
- **Pre-Deployment Validation**: Verify DR readiness before production releases
- **Scheduled DR Drills**: Automate regular DR testing with cron or CI/CD schedulers
- **Infrastructure Validation**: Ensure DR infrastructure is functional and up-to-date

## Prerequisites

### 1. System Requirements

- **Bash**: Version 4.0 or higher
- **AWS CLI**: Version 2.x (recommended)
- **jq**: JSON processor for parsing responses

**Install AWS CLI:**

```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
```

**Install jq:**

```bash
# macOS
brew install jq

# Linux (Ubuntu/Debian)
sudo apt-get install jq

# Linux (RHEL/CentOS)
sudo yum install jq

# Verify installation
jq --version
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

**Option C: IAM Role (Recommended for CI/CD)**

For GitHub Actions, GitLab CI, Jenkins, or other CI/CD systems running on AWS, use IAM roles with OIDC or instance profiles.

### 3. IAM Permissions

Your IAM principal needs permission to invoke the DRS Orchestration Lambda functions.

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

**Attach to IAM User:**

```bash
aws iam put-user-policy \
  --user-name dr-automation-user \
  --policy-name DRSOrchestrationInvoke \
  --policy-document file://iam-policy.json
```

**Attach to IAM Role:**

```bash
aws iam put-role-policy \
  --role-name dr-automation-role \
  --policy-name DRSOrchestrationInvoke \
  --policy-document file://iam-policy.json
```

## Scripts

### 1. DR CI/CD Pipeline Script (`dr_ci_pipeline.sh`)

A comprehensive script for integrating DR testing into CI/CD pipelines.

**Features:**
- List available recovery plans
- Start DR drill or recovery execution
- Monitor execution progress with real-time status updates
- Get recovery instance details
- Terminate instances after testing
- Configurable timeouts and polling intervals
- Colored output for better readability
- Proper exit codes for CI/CD integration

**Basic Usage:**

```bash
# Make script executable
chmod +x dr_ci_pipeline.sh

# List available recovery plans
./dr_ci_pipeline.sh --list-plans

# Run DR drill
./dr_ci_pipeline.sh --plan-id 550e8400-e29b-41d4-a716-446655440000

# Run in different environment
./dr_ci_pipeline.sh --plan-id <plan-id> --environment dev

# Run with custom timeout
./dr_ci_pipeline.sh --plan-id <plan-id> --max-wait-time 7200

# Keep instances running (don't terminate)
./dr_ci_pipeline.sh --plan-id <plan-id> --no-terminate

# Enable verbose output
./dr_ci_pipeline.sh --plan-id <plan-id> --verbose
```

**Command-Line Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--plan-id ID` | Recovery plan ID to execute | Required (unless --list-plans) |
| `--list-plans` | List all available recovery plans | - |
| `--environment ENV` | Deployment environment (dev, test, staging, prod) | test |
| `--region REGION` | AWS region | us-east-1 |
| `--execution-type TYPE` | DRILL or RECOVERY | DRILL |
| `--poll-interval SEC` | Seconds between status checks | 30 |
| `--max-wait-time SEC` | Maximum time to wait for completion | 3600 (1 hour) |
| `--no-terminate` | Don't terminate instances after drill | false |
| `--verbose` | Enable verbose output | false |
| `--help` | Show help message | - |

**Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `DR_ENVIRONMENT` | Default environment | test |
| `AWS_REGION` | Default AWS region | us-east-1 |
| `AWS_PROFILE` | AWS CLI profile to use | default |

**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | DR drill completed successfully |
| 1 | General error |
| 2 | DR drill failed |
| 3 | Invalid arguments |
| 4 | AWS CLI error |
| 5 | Timeout waiting for execution |

**Example Output:**

```
[INFO] Checking prerequisites...
[SUCCESS] Prerequisites check passed

================================================================================
DR CI/CD PIPELINE - DRILL MODE
================================================================================
Environment: test
Region: us-east-1
Plan ID: 550e8400-e29b-41d4-a716-446655440000
================================================================================

[INFO] [Step 1/6] Getting recovery plan details...
[SUCCESS] Plan: Production DR Plan
[INFO]   Protection Group: Production Servers
[INFO]   Waves: 3
    - Wave 1: Database Tier (2 servers)
    - Wave 2: Application Tier (5 servers)
    - Wave 3: Web Tier (3 servers)

[INFO] [Step 2/6] Starting DRILL execution...
[SUCCESS] Execution started: 7c9e6679-7425-40de-944b-e07fc1f90ae7
[INFO]   Initial Status: PENDING

[INFO] [Step 3/6] Monitoring execution progress...
[INFO] Poll interval: 30s, Max wait: 3600s
[INFO] [12:00:15] Status: RUNNING, Wave: 1/3, Elapsed: 15s
[INFO] [12:00:45] Status: RUNNING, Wave: 2/3, Elapsed: 45s
[INFO] [12:01:15] Status: RUNNING, Wave: 3/3, Elapsed: 75s
[INFO] [12:01:45] Status: COMPLETED, Wave: 3/3, Elapsed: 105s
[SUCCESS] Execution finished with status: COMPLETED

[INFO] [Step 4/6] Execution completed

================================================================================
EXECUTION SUMMARY
================================================================================

Execution ID: 7c9e6679-7425-40de-944b-e07fc1f90ae7
Status: COMPLETED
Waves: 3/3

Wave Status:
  - Wave 1 - Database Tier: COMPLETED (2/2 servers)
  - Wave 2 - Application Tier: COMPLETED (5/5 servers)
  - Wave 3 - Web Tier: COMPLETED (3/3 servers)

[INFO] [Step 5/6] Getting recovery instance details...

================================================================================
RECOVERY INSTANCES (10)
================================================================================

Instance: db-server-01
  EC2 ID: i-0123456789abcdef0
  State: running
  Type: r5.large
  Region: us-east-1
  Private IP: 10.0.1.100
  Public IP: N/A
  Wave: Wave 1 - Database Tier

[... additional instances ...]

[INFO] [Step 6/6] Terminating recovery instances...
[SUCCESS] Termination initiated: TERMINATING
[INFO]   Total instances: 10
    - Job drsjob-abc123: 10 instances in us-east-1

================================================================================
[SUCCESS] DR DRILL COMPLETED SUCCESSFULLY
================================================================================
```

## CI/CD Integration Examples

### GitHub Actions

Create `.github/workflows/dr-drill.yml`:

```yaml
name: DR Drill Test

on:
  # Run on schedule (every Monday at 2 AM)
  schedule:
    - cron: '0 2 * * 1'
  
  # Allow manual trigger
  workflow_dispatch:
    inputs:
      plan_id:
        description: 'Recovery Plan ID'
        required: true
        default: '550e8400-e29b-41d4-a716-446655440000'
      environment:
        description: 'Environment'
        required: true
        default: 'test'
        type: choice
        options:
          - dev
          - test
          - staging

jobs:
  dr-drill:
    name: Run DR Drill
    runs-on: ubuntu-latest
    
    permissions:
      id-token: write  # Required for OIDC
      contents: read
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
      
      - name: Install Dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y jq
      
      - name: Run DR Drill
        id: dr-drill
        run: |
          chmod +x examples/bash/dr_ci_pipeline.sh
          ./examples/bash/dr_ci_pipeline.sh \
            --plan-id ${{ github.event.inputs.plan_id || '550e8400-e29b-41d4-a716-446655440000' }} \
            --environment ${{ github.event.inputs.environment || 'test' }} \
            --verbose
      
      - name: Upload Logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: dr-drill-logs
          path: |
            *.log
            *.json
      
      - name: Notify on Failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "text": "DR Drill Failed",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": ":x: DR Drill failed in ${{ github.event.inputs.environment || 'test' }} environment"
                  }
                }
              ]
            }
```

**Setup GitHub OIDC:**

1. Create IAM OIDC provider for GitHub:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

2. Create IAM role with trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:your-org/your-repo:*"
        }
      }
    }
  ]
}
```

3. Attach Lambda invoke policy to the role

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - deploy

variables:
  DR_ENVIRONMENT: "test"
  AWS_REGION: "us-east-1"
  DR_PLAN_ID: "550e8400-e29b-41d4-a716-446655440000"

dr-drill:
  stage: test
  image: amazon/aws-cli:latest
  
  before_script:
    # Install jq
    - yum install -y jq
    
    # Assume IAM role (if using OIDC)
    - |
      export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s" \
      $(aws sts assume-role-with-web-identity \
      --role-arn ${AWS_ROLE_ARN} \
      --role-session-name "gitlab-${CI_PIPELINE_ID}" \
      --web-identity-token ${CI_JOB_JWT_V2} \
      --duration-seconds 3600 \
      --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
      --output text))
  
  script:
    - chmod +x examples/bash/dr_ci_pipeline.sh
    - |
      ./examples/bash/dr_ci_pipeline.sh \
        --plan-id ${DR_PLAN_ID} \
        --environment ${DR_ENVIRONMENT} \
        --region ${AWS_REGION} \
        --verbose
  
  artifacts:
    when: always
    paths:
      - "*.log"
      - "*.json"
    expire_in: 7 days
  
  rules:
    # Run on schedule
    - if: $CI_PIPELINE_SOURCE == "schedule"
    # Run on manual trigger
    - if: $CI_PIPELINE_SOURCE == "web"
    # Run before production deployment
    - if: $CI_COMMIT_BRANCH == "main" && $CI_PIPELINE_SOURCE == "push"
  
  retry:
    max: 2
    when:
      - runner_system_failure
      - stuck_or_timeout_failure

deploy-production:
  stage: deploy
  dependencies:
    - dr-drill
  script:
    - echo "Deploying to production..."
    - ./deploy.sh production
  only:
    - main
  when: on_success
```

**Setup GitLab OIDC:**

1. Create IAM OIDC provider for GitLab:

```bash
aws iam create-open-id-connect-provider \
  --url https://gitlab.com \
  --client-id-list https://gitlab.com \
  --thumbprint-list <gitlab-thumbprint>
```

2. Create IAM role with trust policy for GitLab

3. Set `AWS_ROLE_ARN` as GitLab CI/CD variable

### Jenkins

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['test', 'dev', 'staging'],
            description: 'Environment to run DR drill'
        )
        string(
            name: 'PLAN_ID',
            defaultValue: '550e8400-e29b-41d4-a716-446655440000',
            description: 'Recovery Plan ID'
        )
        booleanParam(
            name: 'TERMINATE_INSTANCES',
            defaultValue: true,
            description: 'Terminate instances after drill'
        )
    }
    
    environment {
        AWS_REGION = 'us-east-1'
        AWS_CREDENTIALS = credentials('aws-dr-automation-credentials')
    }
    
    stages {
        stage('Prerequisites') {
            steps {
                sh '''
                    # Check AWS CLI
                    aws --version
                    
                    # Check jq
                    jq --version
                    
                    # Verify AWS credentials
                    aws sts get-caller-identity
                '''
            }
        }
        
        stage('Run DR Drill') {
            steps {
                script {
                    def terminateFlag = params.TERMINATE_INSTANCES ? '' : '--no-terminate'
                    
                    sh """
                        chmod +x examples/bash/dr_ci_pipeline.sh
                        ./examples/bash/dr_ci_pipeline.sh \\
                            --plan-id ${params.PLAN_ID} \\
                            --environment ${params.ENVIRONMENT} \\
                            --region ${AWS_REGION} \\
                            --verbose \\
                            ${terminateFlag}
                    """
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '*.log, *.json', allowEmptyArchive: true
        }
        
        success {
            echo 'DR Drill completed successfully'
            // Send notification
            emailext(
                subject: "DR Drill Success - ${params.ENVIRONMENT}",
                body: "DR drill completed successfully in ${params.ENVIRONMENT} environment",
                to: 'dr-team@example.com'
            )
        }
        
        failure {
            echo 'DR Drill failed'
            // Send notification
            emailext(
                subject: "DR Drill Failed - ${params.ENVIRONMENT}",
                body: "DR drill failed in ${params.ENVIRONMENT} environment. Check logs for details.",
                to: 'dr-team@example.com'
            )
        }
    }
}
```

**Jenkins Setup:**

1. Install required plugins:
   - AWS Credentials Plugin
   - Pipeline Plugin
   - Email Extension Plugin

2. Configure AWS credentials in Jenkins:
   - Go to "Manage Jenkins" → "Manage Credentials"
   - Add AWS credentials with ID `aws-dr-automation-credentials`

3. Create pipeline job:
   - New Item → Pipeline
   - Configure → Pipeline script from SCM
   - Point to your repository

### CircleCI

Create `.circleci/config.yml`:

```yaml
version: 2.1

orbs:
  aws-cli: circleci/aws-cli@4.0

jobs:
  dr-drill:
    docker:
      - image: cimg/base:stable
    
    parameters:
      environment:
        type: string
        default: "test"
      plan_id:
        type: string
        default: "550e8400-e29b-41d4-a716-446655440000"
    
    steps:
      - checkout
      
      - aws-cli/setup:
          role_arn: "arn:aws:iam::123456789012:role/CircleCIRole"
          region: "us-east-1"
      
      - run:
          name: Install Dependencies
          command: |
            sudo apt-get update
            sudo apt-get install -y jq
      
      - run:
          name: Run DR Drill
          command: |
            chmod +x examples/bash/dr_ci_pipeline.sh
            ./examples/bash/dr_ci_pipeline.sh \
              --plan-id << parameters.plan_id >> \
              --environment << parameters.environment >> \
              --verbose
      
      - store_artifacts:
          path: "*.log"
      
      - store_artifacts:
          path: "*.json"

workflows:
  scheduled-dr-drill:
    triggers:
      - schedule:
          cron: "0 2 * * 1"  # Every Monday at 2 AM
          filters:
            branches:
              only:
                - main
    jobs:
      - dr-drill:
          environment: "test"
  
  manual-dr-drill:
    jobs:
      - dr-drill:
          environment: "test"
```

## Best Practices

### 1. Use DRILL Mode for Testing

Always use `--execution-type DRILL` for automated testing. Only use `RECOVERY` for actual disaster recovery scenarios.

```bash
# Good - automated testing
./dr_ci_pipeline.sh --plan-id <plan-id> --execution-type DRILL

# Dangerous - only for actual DR
./dr_ci_pipeline.sh --plan-id <plan-id> --execution-type RECOVERY
```

### 2. Terminate Instances After Drills

Always terminate recovery instances after drill completion to avoid unnecessary costs:

```bash
# Good - terminates instances (default)
./dr_ci_pipeline.sh --plan-id <plan-id>

# Only use --no-terminate for debugging
./dr_ci_pipeline.sh --plan-id <plan-id> --no-terminate
```

### 3. Set Appropriate Timeouts

Configure timeouts based on your recovery plan complexity:

```bash
# Small plan (1-2 waves, few servers)
./dr_ci_pipeline.sh --plan-id <plan-id> --max-wait-time 1800  # 30 minutes

# Large plan (5+ waves, many servers)
./dr_ci_pipeline.sh --plan-id <plan-id> --max-wait-time 7200  # 2 hours
```

### 4. Use IAM Roles Over Access Keys

For CI/CD systems running on AWS or supporting OIDC, use IAM roles instead of access keys:

```bash
# Good - uses IAM role (no credentials in code)
export AWS_ROLE_ARN=arn:aws:iam::123456789012:role/CIRole

# Avoid - hardcoded credentials
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### 5. Test in Non-Production First

Always test DR workflows in dev/test environments before running in production:

```bash
# Step 1: Test in dev
./dr_ci_pipeline.sh --plan-id <dev-plan-id> --environment dev

# Step 2: Test in test
./dr_ci_pipeline.sh --plan-id <test-plan-id> --environment test

# Step 3: Only then run in production
./dr_ci_pipeline.sh --plan-id <prod-plan-id> --environment prod
```

### 6. Enable Verbose Logging for Debugging

Use `--verbose` flag when troubleshooting issues:

```bash
./dr_ci_pipeline.sh --plan-id <plan-id> --verbose
```

### 7. Handle Exit Codes Properly

Check exit codes in CI/CD pipelines:

```bash
#!/bin/bash
set -e  # Exit on error

./dr_ci_pipeline.sh --plan-id <plan-id>

if [ $? -eq 0 ]; then
    echo "DR drill passed - proceeding with deployment"
    ./deploy.sh production
else
    echo "DR drill failed - blocking deployment"
    exit 1
fi
```

### 8. Archive Logs and Artifacts

Save logs for troubleshooting and compliance:

```bash
# Run with output redirection
./dr_ci_pipeline.sh --plan-id <plan-id> 2>&1 | tee dr-drill-$(date +%Y%m%d-%H%M%S).log

# Archive in CI/CD
# GitHub Actions: uses: actions/upload-artifact@v4
# GitLab CI: artifacts: paths: ["*.log"]
# Jenkins: archiveArtifacts artifacts: '*.log'
```

## Troubleshooting

### Issue: "AWS CLI is not installed"

**Solution:**
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Issue: "jq is not installed"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install jq

# RHEL/CentOS
sudo yum install jq

# macOS
brew install jq
```

### Issue: "AWS credentials are not configured"

**Solution:**
```bash
# Configure credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1

# Or use IAM role (recommended)
export AWS_ROLE_ARN=arn:aws:iam::123456789012:role/YourRole
```

### Issue: "AccessDeniedException" or "User is not authorized"

**Cause**: IAM principal lacks lambda:InvokeFunction permission

**Solution:**
1. Verify IAM policy is attached
2. Check Lambda resource-based policy
3. Test with AWS CLI:

```bash
aws lambda get-policy \
  --function-name aws-drs-orchestration-query-handler-test \
  --query 'Policy' --output text | jq .
```

### Issue: "Function not found"

**Cause**: Lambda function doesn't exist or wrong environment/region

**Solution:**
```bash
# List Lambda functions
aws lambda list-functions \
  --query 'Functions[?contains(FunctionName, `drs-orchestration`)].FunctionName'

# Verify environment and region
./dr_ci_pipeline.sh --list-plans --environment test --region us-east-1
```

### Issue: "Timeout waiting for execution"

**Cause**: Execution taking longer than max-wait-time

**Solution:**
```bash
# Increase timeout
./dr_ci_pipeline.sh --plan-id <plan-id> --max-wait-time 7200  # 2 hours

# Or check execution status manually
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_execution","executionId":"<execution-id>"}' \
  response.json
cat response.json | jq .
```

### Issue: "DR drill failed with status: FAILED"

**Cause**: Execution failed during recovery

**Solution:**
1. Check execution details:

```bash
./dr_ci_pipeline.sh --plan-id <plan-id> --verbose
```

2. Review CloudWatch Logs for Lambda functions
3. Check DRS console for job failures
4. Verify source servers are healthy

## Additional Resources

- [Python Examples](../python/README.md) - Python SDK examples
- [API Reference](../../docs/api-reference/QUERY_HANDLER_API.md) - Complete API documentation
- [Migration Guide](../../docs/guides/MIGRATION_GUIDE.md) - Migrating from API Gateway mode
- [IAM Policy Documentation](../../docs/iam/ORCHESTRATION_ROLE_POLICY.md) - IAM permissions
- [Developer Guide](../../docs/guides/DEVELOPER_GUIDE.md) - Development workflow

## Support

For issues or questions:
1. Check script output with `--verbose` flag
2. Review CloudWatch Logs for Lambda execution details
3. Verify IAM permissions and Lambda resource policies
4. Check AWS CLI configuration and credentials
5. Consult API documentation for error codes
