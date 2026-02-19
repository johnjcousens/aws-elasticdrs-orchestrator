# DRS Agent Cross-Account Deployment Scripts

## Overview

These scripts automate the installation of AWS DRS agents on Windows EC2 instances with support for cross-account replication.

## Files

- **install-drs-agent-cross-account.ps1** - PowerShell script that runs on Windows instances
- **deploy-drs-agent-cross-account.sh** - Bash script that deploys via SSM from your local machine

## Prerequisites

### In Target/Staging Account (891376951562)
1. DRS initialized: `aws drs initialize-service --region us-east-1`
2. Source account (160885257264) added as "Trusted Account" with "Failback and in-AWS right-sizing roles"

### In Source Account (160885257264)
1. IAM role with `AWSElasticDisasterRecoveryEc2InstancePolicy` managed policy
2. Instance profile created and attached to EC2 instances
3. SSM Agent running on instances (pre-installed on Windows Server 2016+)

### Local Machine
1. AWS CLI configured with credentials for source account
2. Permissions to:
   - Upload to S3 bucket (hrp-drs-tech-adapter-dev)
   - Execute SSM commands
   - Read SSM command results

## Quick Start

### Option 1: Deploy via SSM (Recommended)

Deploy to all HRP instances:
```bash
./scripts/deploy-drs-agent-cross-account.sh \
  --instance-ids "i-00c5c7b3cf6d8abeb,i-04d81abd203126050,i-0b5fcf61e94e9f599,i-0b40c1c713cfdeac8,i-0d780c0fa44ba72e9,i-0117a71b9b09d45f7" \
  --account-id 891376951562 \
  --region us-east-1
```

Deploy to specific instances:
```bash
./scripts/deploy-drs-agent-cross-account.sh \
  --instance-ids "i-00c5c7b3cf6d8abeb,i-04d81abd203126050" \
  --account-id 891376951562
```

Use custom S3 bucket (optional):
```bash
./scripts/deploy-drs-agent-cross-account.sh \
  --instance-ids "i-00c5c7b3cf6d8abeb" \
  --account-id 891376951562 \
  --s3-bucket my-custom-bucket
```

Dry run (preview without executing):
```bash
./scripts/deploy-drs-agent-cross-account.sh \
  --instance-ids "i-00c5c7b3cf6d8abeb" \
  --account-id 891376951562 \
  --dry-run
```

### Option 2: Manual Installation via RDP

1. RDP to Windows instance
2. Copy `install-drs-agent-cross-account.ps1` to instance
3. Open PowerShell as Administrator
4. Run:
```powershell
.\install-drs-agent-cross-account.ps1 -AccountId 891376951562
```

## HRP Instance Reference

| Instance Name | Instance ID | Type | Purpose |
|--------------|-------------|------|---------|
| hrp-core-web03 | i-00c5c7b3cf6d8abeb | Web | Web Server 03 |
| hrp-core-web04 | i-04d81abd203126050 | Web | Web Server 04 |
| hrp-core-app03 | i-0b5fcf61e94e9f599 | App | Application Server 03 |
| hrp-core-app04 | i-0b40c1c713cfdeac8 | App | Application Server 04 |
| hrp-core-db03 | i-0d780c0fa44ba72e9 | DB | Database Server 03 |
| hrp-core-db04 | i-0117a71b9b09d45f7 | DB | Database Server 04 |

## Script Details

### PowerShell Script (install-drs-agent-cross-account.ps1)

**Parameters:**
- `-Region` - AWS region (default: us-east-1)
- `-AccountId` - Target account for cross-account replication (optional)
- `-NoPrompt` - Run without prompts (default: true)
- `-TempDir` - Temp directory for installer (default: C:\Temp)

**What it does:**
1. Checks administrator privileges
2. Verifies instance profile
3. Downloads DRS agent installer from S3
4. Installs agent with `--account-id` parameter
5. Verifies service status
6. Provides next steps

**Example output:**
```
=== AWS DRS Agent Installation ===
Region: us-east-1
Target Account: 891376951562 (Cross-Account Replication)

[1/5] Checking prerequisites...
✓ Instance profile detected: DRS-EC2-CrossAccount-Profile

[2/5] Creating temporary directory...
✓ Created: C:\Temp

[3/5] Downloading DRS agent installer...
✓ Downloaded successfully (45.23 MB)

[4/5] Preparing installation...
Cross-account replication enabled
Installer arguments: --region us-east-1 --account-id 891376951562 --no-prompt

[5/5] Installing DRS agent...
This may take several minutes...

✓ DRS agent installed successfully!

Service Status: Running
Service Name: AWS Replication Agent
```

### Bash Script (deploy-drs-agent-cross-account.sh)

**Parameters:**
- `--instance-ids` - Comma-separated instance IDs (required)
- `--region` - AWS region (default: us-east-1)
- `--account-id` - Target account for cross-account replication (optional)
- `--s3-bucket` - S3 bucket for script storage (default: hrp-drs-tech-adapter-dev)
- `--dry-run` - Preview without executing

**What it does:**
1. Uploads PowerShell script to S3
2. Checks SSM connectivity for each instance
3. Executes PowerShell script via SSM Run Command
4. Polls for completion and displays results
5. Shows SSM console link for detailed logs

**Example output:**
```
=== DRS Agent Deployment via SSM ===
Region: us-east-1
S3 Bucket: hrp-drs-tech-adapter-dev
Instance Count: 2
Instance IDs:
  - i-00c5c7b3cf6d8abeb
  - i-04d81abd203126050
Cross-Account Replication: Enabled (Target: 891376951562)

[1/4] Uploading PowerShell script to S3...
✓ Uploaded to: s3://hrp-drs-tech-adapter-dev/scripts/drs/install-drs-agent-cross-account.ps1

[2/4] Checking SSM connectivity...
✓ i-00c5c7b3cf6d8abeb: Online
✓ i-04d81abd203126050: Online

[3/4] Preparing SSM command...

[4/4] Executing installation via SSM...
✓ SSM Command initiated
Command ID: 12345678-1234-1234-1234-123456789012

Waiting for command to complete...
This may take 5-10 minutes...

Instance: i-00c5c7b3cf6d8abeb
✓ Installation completed successfully
```

## Verification

### Check Source Servers in Target Account
```bash
# Switch to target account credentials
export AWS_PROFILE=staging-account

# List source servers
aws drs describe-source-servers --region us-east-1

# Expected output shows servers from source account (160885257264)
```

### Check Replication Status
```bash
aws drs describe-source-servers \
  --region us-east-1 \
  --query 'items[*].[sourceServerID,hostname,dataReplicationInfo.dataReplicationState]' \
  --output table
```

### Check Agent Service on Instance
```powershell
# Via RDP or SSM
Get-Service "AWS Replication Agent"

# Expected output:
# Status   Name                           DisplayName
# ------   ----                           -----------
# Running  AWS Replication Agent          AWS Replication Agent
```

## Troubleshooting

### SSM Command Fails
**Check SSM connectivity:**
```bash
aws ssm describe-instance-information \
  --region us-east-1 \
  --filters "Key=InstanceIds,Values=i-00c5c7b3cf6d8abeb" \
  --query 'InstanceInformationList[0].PingStatus'
```

**View SSM logs on instance:**
```powershell
Get-Content "C:\ProgramData\Amazon\SSM\Logs\amazon-ssm-agent.log" -Tail 50
```

### Agent Installation Fails
**Check instance profile:**
```bash
aws ec2 describe-iam-instance-profile-associations \
  --filters "Name=instance-id,Values=i-00c5c7b3cf6d8abeb"
```

**Check agent logs on instance:**
```powershell
Get-Content "C:\ProgramData\Amazon\AWS Replication Agent\logs\agent.log" -Tail 50
```

### Source Servers Not Appearing in Target Account
1. Verify trusted account configuration in target account
2. Ensure "Failback and in-AWS right-sizing roles" is enabled
3. Check network connectivity to DRS endpoints
4. Wait 5-10 minutes for initial registration

### Permission Errors
**Verify IAM policy on instance role:**
```bash
aws iam get-role-policy \
  --role-name DRS-EC2-CrossAccount-Role \
  --policy-name AWSElasticDisasterRecoveryEc2InstancePolicy
```

**Verify trusted account role in target account:**
```bash
# In target account
aws iam get-role \
  --role-name DRSFailbackRole_160885257264
```

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Access Denied" during installation | Missing instance profile | Attach instance profile with `AWSElasticDisasterRecoveryEc2InstancePolicy` |
| Source servers not appearing | Trusted account not configured | Add source account as trusted with failback roles |
| SSM command timeout | Instance not reachable | Check SSM agent status and network connectivity |
| Agent service won't start | Installation incomplete | Reinstall agent with `--no-prompt` flag |

## Security Considerations

1. **S3 Bucket Access**: Ensure S3 bucket has appropriate access controls
2. **SSM Permissions**: Limit SSM command execution to authorized users
3. **Instance Profile**: Use least-privilege IAM policies
4. **Cross-Account Trust**: Regularly audit trusted account configurations
5. **Logging**: Enable CloudTrail for DRS API calls

## Related Documentation

- [DRS Cross-Account Setup Guide](../DRS_CROSS_ACCOUNT_SETUP.md)
- [DRS Cross-Account Quick Start](../docs/guides/DRS_CROSS_ACCOUNT_QUICK_START.md)
- [AWS DRS Agent Installation](https://docs.aws.amazon.com/drs/latest/userguide/agent-installation.html)
- [AWS DRS Installer Parameters](https://docs.aws.amazon.com/drs/latest/userguide/installer-parameters.html)

## Support

For issues or questions:
1. Check CloudWatch Logs for Lambda functions
2. Review SSM command output in Systems Manager console
3. Check DRS service events in target account
4. Review CloudTrail logs for API errors
