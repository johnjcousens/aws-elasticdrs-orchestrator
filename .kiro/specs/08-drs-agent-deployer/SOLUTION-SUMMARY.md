# DRS Agent Cross-Account Deployment - Solution Summary

## Problem

AWS's official SSM document `AWSDisasterRecovery-InstallDRAgentOnInstance` does not support the `--account-id` parameter needed for cross-account DRS replication.

## Solution

Created a **custom SSM document** based on AWS's official one with added `AccountId` parameter support.

## Implementation

### 1. Custom SSM Document

**File**: `ssm-documents/DRS-InstallAgentCrossAccount.yaml`

**Key Addition**: Added `AccountId` parameter that gets passed to the DRS agent installer:

```yaml
parameters:
  AccountId:
    type: String
    description: (Optional) Target AWS Account ID for cross-account replication
    default: ""
    allowedPattern: "^(\\d{12})?$"
```

**PowerShell (Windows)**:
```powershell
$requestedAccountId="{{AccountId}}"
$baseArgs = "--no-prompt --region {{Region}}"
if ( $requestedAccountId ) { $baseArgs = $baseArgs + " --account-id $requestedAccountId" }
```

**Python (Linux)**:
```python
account_id = '{{ AccountId }}'
if account_id:
  raw_cmd += "--account-id {0} ".format(account_id)
```

### 2. Deployment Scripts

**Deploy SSM Document**: `scripts/deploy-ssm-document.sh`
- Creates/updates the custom SSM document in your AWS account
- One-time setup

**Deploy Agents**: `scripts/deploy-using-ssm-document.sh`
- Uses the custom SSM document to install agents
- Supports both same-account and cross-account deployment
- Pre-configured for HRP environment

## Usage

### One-Time Setup

Deploy the custom SSM document:
```bash
.kiro/specs/drs-agent-deployer/scripts/deploy-ssm-document.sh
```

### Deploy Agents

**Web servers 03/04 (cross-account)**:
```bash
.kiro/specs/drs-agent-deployer/scripts/deploy-using-ssm-document.sh web-03-04
```

**All 03/04 instances (cross-account)**:
```bash
.kiro/specs/drs-agent-deployer/scripts/deploy-using-ssm-document.sh all-03-04
```

**All 01/02 instances (same-account)**:
```bash
.kiro/specs/drs-agent-deployer/scripts/deploy-using-ssm-document.sh all-01-02
```

**Everything**:
```bash
.kiro/specs/drs-agent-deployer/scripts/deploy-using-ssm-document.sh all
```

### Manual Usage

**Same-account replication**:
```bash
aws ssm send-command \
  --document-name DRS-InstallAgentCrossAccount \
  --instance-ids i-xxxxx \
  --parameters Region=us-east-1
```

**Cross-account replication**:
```bash
aws ssm send-command \
  --document-name DRS-InstallAgentCrossAccount \
  --instance-ids i-xxxxx \
  --parameters Region=us-east-1,AccountId=123456789012
```

## Advantages

1. **Clean & Simple**: Uses native SSM document approach
2. **No JSON Escaping Issues**: SSM handles parameter passing
3. **Reusable**: Document can be used for any DRS deployment
4. **Maintainable**: Based on AWS's official document structure
5. **Supports Both Platforms**: Windows and Linux
6. **Parallel Execution**: SSM runs on all instances simultaneously
7. **Built-in Monitoring**: Use SSM Console to track progress

## Architecture

```
Custom SSM Document (DRS-InstallAgentCrossAccount)
    ↓
SSM Send Command (with AccountId parameter)
    ↓
EC2 Instances (01/02 and 03/04)
    ↓
DRS Agent Installation
    ↓
├─ 01/02: Same-account replication (111111111111 → 111111111111)
└─ 03/04: Cross-account replication (111111111111 → 123456789012)
```

## Files Created

```
.kiro/specs/drs-agent-deployer/
├── ssm-documents/
│   └── DRS-InstallAgentCrossAccount.yaml    # Custom SSM document
├── scripts/
│   ├── deploy-ssm-document.sh               # Deploy the SSM document
│   └── deploy-using-ssm-document.sh         # Deploy agents using document
└── SOLUTION-SUMMARY.md                      # This file
```

## Monitoring

**SSM Console**:
```
https://console.aws.amazon.com/systems-manager/run-command?region=us-east-1
```

**Check command status**:
```bash
aws ssm list-command-invocations \
  --command-id <command-id> \
  --region us-east-1
```

**Get command output**:
```bash
aws ssm get-command-invocation \
  --command-id <command-id> \
  --instance-id <instance-id> \
  --region us-east-1
```

## Verification

### Same-Account (01/02)
```bash
# In source account (111111111111)
aws drs describe-source-servers --region us-east-1
```

### Cross-Account (03/04)
```bash
# In staging account (123456789012)
aws drs describe-source-servers --region us-east-1
```

## Troubleshooting

### Document Not Found
```bash
# Redeploy the SSM document
.kiro/specs/drs-agent-deployer/scripts/deploy-ssm-document.sh
```

### Installation Failed
Check SSM command output in the console or via CLI:
```bash
aws ssm get-command-invocation \
  --command-id <command-id> \
  --instance-id <instance-id> \
  --region us-east-1 \
  --query 'StandardErrorContent' \
  --output text
```

### Agent Not Appearing in Target Account
1. Verify trusted account configuration in target account
2. Ensure "Failback and in-AWS right-sizing roles" is enabled
3. Check instance profile has `AWSElasticDisasterRecoveryEc2InstancePolicy`
4. Wait 5-10 minutes for initial registration

## Related Documentation

- [DRS Cross-Account Setup](DRS_CROSS_ACCOUNT_SETUP.md)
- [HRP Deployment Strategy](docs/HRP_DRS_DEPLOYMENT_STRATEGY.md)
- [AWS DRS Agent Installation](https://docs.aws.amazon.com/drs/latest/userguide/agent-installation.html)
- [AWS DRS Installer Parameters](https://docs.aws.amazon.com/drs/latest/userguide/installer-parameters.html)
