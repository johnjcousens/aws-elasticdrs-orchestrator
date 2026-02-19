# DRS Cross-Account Replication - Implementation Complete

## Summary

Successfully implemented cross-account DRS replication support in the DRS Agent Deployer Lambda function. The function now supports deploying agents in a source account that replicate data to a separate staging account.

## Implementation Date

January 30, 2026

## What Was Implemented

### 1. Lambda Function Updates

**File**: `lambda/drs-agent-deployer/index.py`

#### Key Changes:

- **Updated `lambda_handler()`** to accept new parameters:
  - `source_account_id` - Account where agents are installed
  - `staging_account_id` - Account where data replicates to
  - `source_role_arn` - Role in source account
  - `staging_role_arn` - Role in staging account
  - Maintains backward compatibility with old parameter names

- **Added deployment pattern detection**:
  - `same-account` - Agents replicate to same account
  - `cross-account` - Agents replicate to different staging account

- **Refactored `DRSAgentDeployer` class**:
  - Accepts both source and staging account parameters
  - Assumes separate roles for source and staging accounts
  - Uses source credentials for EC2/SSM operations
  - Uses staging credentials for DRS operations
  - Enhanced logging to show cross-account flow

- **Updated `_assume_role()` method**:
  - Accepts role ARN and session name as parameters
  - Supports assuming multiple roles (source and staging)
  - Better error messages with account ID extraction

- **Updated `_get_client()` method**:
  - Accepts credentials as parameter
  - Allows different credentials for different services

- **Enhanced `deploy_agents()` method**:
  - Prints deployment pattern and account information
  - Includes staging account ID in SSM command parameters
  - Updates result structure with both account IDs
  - Better status messages for cross-account flow

- **Updated `_get_source_servers()` method**:
  - Queries staging account's DRS service
  - Verifies agents registered in correct account
  - Enhanced logging for cross-account verification

### 2. Test Events

Created three test event files:

#### `test-events/single-account.json`
```json
{
  "source_account_id": "160885257264",
  "source_region": "us-east-1",
  "target_region": "us-west-2",
  "source_role_arn": "arn:aws:iam::160885257264:role/DRSOrchestrationRole"
}
```

#### `test-events/cross-account.json`
```json
{
  "source_account_id": "160885257264",
  "staging_account_id": "664418995426",
  "source_region": "us-east-1",
  "target_region": "us-west-2",
  "source_role_arn": "arn:aws:iam::160885257264:role/DRSOrchestrationRole",
  "staging_role_arn": "arn:aws:iam::664418995426:role/DRSOrchestrationRole"
}
```

#### `test-events/multi-account.json`
Updated to use new parameter names for consistency.

### 3. Documentation

Created comprehensive documentation:

#### `docs/guides/DRS_CROSS_ACCOUNT_REPLICATION.md`

Complete guide covering:
- Architecture patterns (same-account vs cross-account)
- Prerequisites for source and staging accounts
- Step-by-step deployment workflow
- Verification and monitoring procedures
- Troubleshooting common issues
- Security considerations
- Cost optimization tips
- Best practices

Key sections:
- Mermaid diagram showing cross-account flow
- CloudFormation templates for IAM roles
- AWS CLI commands for setup and verification
- Python SDK examples
- Monitoring and alerting guidance

#### `lambda/drs-agent-deployer/README.md`

Updated README with:
- Both deployment patterns documented
- Event parameter reference table
- Prerequisites for each account type
- Architecture diagram
- How it works explanation
- Links to detailed documentation

## Deployment Patterns Supported

### Pattern 1: Same-Account Replication

**Use Case**: Single-account DR with regional failover

**Example**: Production in us-east-1 replicates to us-west-2 in same account

**Event**:
```json
{
  "source_account_id": "160885257264",
  "source_region": "us-east-1",
  "target_region": "us-west-2"
}
```

### Pattern 2: Cross-Account Replication

**Use Case**: Multi-account DR with dedicated DR account

**Example**: Production in account A replicates to staging in account B

**Event**:
```json
{
  "source_account_id": "160885257264",
  "staging_account_id": "664418995426",
  "source_region": "us-east-1",
  "target_region": "us-west-2",
  "source_role_arn": "arn:aws:iam::160885257264:role/DRSOrchestrationRole",
  "staging_role_arn": "arn:aws:iam::664418995426:role/DRSOrchestrationRole"
}
```

## How Cross-Account Replication Works

```
1. Orchestration Lambda (Account 891376951562)
   ↓
2. Assume role in Source Account (160885257264)
   ↓
3. Discover EC2 instances with DR tags
   ↓
4. Send SSM command to install DRS agents
   ↓ (agents include staging account ID)
5. DRS agents register with Staging Account (664418995426)
   ↓
6. Assume role in Staging Account
   ↓
7. Verify source servers appear in DRS console
   ↓
8. Return deployment results
```

## Prerequisites

### Source Account (160885257264)

- EC2 instances with DR tags
- EC2 instance profile with SSM + DRS permissions
- Cross-account role for orchestration
- SSM agents online on instances

### Staging Account (664418995426)

- DRS service initialized in target region
- Replication configuration template created
- Cross-account role for orchestration
- Network connectivity for replication

### Orchestration Account (891376951562)

- Lambda function deployed
- UnifiedOrchestrationRole with STS AssumeRole permissions
- Environment variables configured

## Testing

### Test Same-Account Replication

```bash
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-drs-agent-deployer-dev \
  --payload file://lambda/drs-agent-deployer/test-events/single-account.json \
  response.json

cat response.json | jq .
```

### Test Cross-Account Replication

```bash
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-drs-agent-deployer-dev \
  --payload file://lambda/drs-agent-deployer/test-events/cross-account.json \
  response.json

cat response.json | jq .
```

### Verify Source Servers in Staging Account

```bash
AWS_PROFILE=staging aws drs describe-source-servers \
  --region us-west-2 \
  --query 'items[*].[sourceServerID,tags.Name,dataReplicationInfo.dataReplicationState]' \
  --output table
```

## Backward Compatibility

The implementation maintains backward compatibility:

- Old parameter names (`account_id`, `role_arn`) still work
- Automatically detects deployment pattern
- Defaults to same-account replication if staging account not specified
- Existing test events and API calls continue to work

## Next Steps

### 1. Deploy to Dev Environment

```bash
# Commit changes
git add .
git commit -m "feat: add cross-account DRS replication support"

# Deploy using CI/CD script
./scripts/deploy.sh dev --lambda-only
```

### 2. Test in Dev Environment

```bash
# Test same-account
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-drs-agent-deployer-dev \
  --payload file://lambda/drs-agent-deployer/test-events/single-account.json \
  response.json

# Test cross-account
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-drs-agent-deployer-dev \
  --payload file://lambda/drs-agent-deployer/test-events/cross-account.json \
  response.json
```

### 3. Update API Gateway (Optional)

If exposing via API, update API Gateway integration to accept new parameters:

```yaml
# cfn/api-gateway-operations-methods-stack.yaml
/drs/agents/deploy:
  post:
    parameters:
      - source_account_id
      - staging_account_id (optional)
      - source_region
      - target_region
      - source_role_arn (optional)
      - staging_role_arn (optional)
```

### 4. Update Frontend (Optional)

Add UI fields for cross-account deployment:

- Source account selector
- Staging account selector (optional)
- Deployment pattern indicator
- Cross-account status display

See `docs/guides/DRS_AGENT_DEPLOYMENT_FRONTEND_INTEGRATION.md` for details.

### 5. Setup Cross-Account Roles

Deploy DRSOrchestrationRole to both accounts:

```bash
# Source account
AWS_PROFILE=source aws cloudformation deploy \
  --template-file cfn/cross-account-role-stack.yaml \
  --stack-name drs-orchestration-role \
  --capabilities CAPABILITY_NAMED_IAM

# Staging account
AWS_PROFILE=staging aws cloudformation deploy \
  --template-file cfn/cross-account-role-stack.yaml \
  --stack-name drs-orchestration-role \
  --capabilities CAPABILITY_NAMED_IAM
```

## Files Modified/Created

### Modified
- `lambda/drs-agent-deployer/index.py` - Core implementation

### Created
- `lambda/drs-agent-deployer/test-events/single-account.json` - Same-account test
- `lambda/drs-agent-deployer/test-events/cross-account.json` - Cross-account test
- `lambda/drs-agent-deployer/test-events/multi-account.json` - Updated for new params
- `lambda/drs-agent-deployer/README.md` - Function documentation
- `docs/guides/DRS_CROSS_ACCOUNT_REPLICATION.md` - Complete guide
- `docs/DRS_CROSS_ACCOUNT_REPLICATION_COMPLETE.md` - This summary

## Related Documentation

- [DRS Agent Deployment Guide](guides/DRS_AGENT_DEPLOYMENT_GUIDE.md) - Complete deployment guide
- [DRS Cross-Account Orchestration](DRS_CROSS_ACCOUNT_ORCHESTRATION.md) - Orchestration patterns
- [DRS Agent Deployer Integration Summary](DRS_AGENT_DEPLOYER_INTEGRATION_SUMMARY.md) - Integration overview
- [DRS Agent Deployment Frontend Integration](guides/DRS_AGENT_DEPLOYMENT_FRONTEND_INTEGRATION.md) - UI integration plan

## Status

✅ **Implementation Complete** - Ready for deployment and testing

**No AWS deployments performed** - All code changes are local and ready for CI/CD pipeline.
