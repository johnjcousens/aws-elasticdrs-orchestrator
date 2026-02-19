# DRS Cross-Account Quick Start

## TL;DR

Install DRS agents on instances in account **160885257264** that replicate to account **891376951562**:

```powershell
AwsReplicationWindowsInstaller.exe --region us-east-1 --account-id 891376951562 --no-prompt
```

## Prerequisites Checklist

### In Staging Account (891376951562)
- [ ] DRS initialized: `aws drs initialize-service --region us-east-1`
- [ ] Source account (160885257264) added as "Trusted Account" with "Failback and in-AWS right-sizing roles"

### In Source Account (160885257264)
- [ ] IAM role created with `AWSElasticDisasterRecoveryEc2InstancePolicy`
- [ ] Instance profile created and attached to EC2 instances

## Quick Setup Commands

### 1. Staging Account (891376951562)
```bash
# Initialize DRS
aws drs initialize-service --region us-east-1

# Add trusted account via console:
# DRS Console → Settings → Trusted Accounts → Add trusted accounts
# Account ID: 160885257264
# Role type: "Failback and in-AWS right-sizing roles"
```

### 2. Source Account (160885257264)
```bash
# Create IAM role
aws iam create-role \
  --role-name DRS-EC2-CrossAccount-Role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach managed policy
aws iam attach-role-policy \
  --role-name DRS-EC2-CrossAccount-Role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSElasticDisasterRecoveryEc2InstancePolicy

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name DRS-EC2-CrossAccount-Profile

aws iam add-role-to-instance-profile \
  --instance-profile-name DRS-EC2-CrossAccount-Profile \
  --role-name DRS-EC2-CrossAccount-Role

# Attach to instances
aws ec2 associate-iam-instance-profile \
  --region us-east-1 \
  --instance-id i-00c5c7b3cf6d8abeb \
  --iam-instance-profile Name=DRS-EC2-CrossAccount-Profile
```

### 3. Install Agent (PowerShell on Windows)
```powershell
# Download installer
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::tls12
$webClient = New-Object System.Net.WebClient
$webClient.DownloadFile(
  'https://aws-elastic-disaster-recovery-us-east-1.s3.us-east-1.amazonaws.com/latest/windows/AwsReplicationWindowsInstaller.exe',
  'C:\Temp\AwsReplicationWindowsInstaller.exe'
)

# Install with cross-account parameter
C:\Temp\AwsReplicationWindowsInstaller.exe --region us-east-1 --account-id 891376951562 --no-prompt
```

## Verification

### Check Source Servers in Staging Account
```bash
# In staging account (891376951562)
aws drs describe-source-servers --region us-east-1
```

You should see source servers from account 160885257264 registered in account 891376951562.

## HRP Instance IDs

| Instance | ID | Type |
|----------|-----|------|
| hrp-core-web03 | i-00c5c7b3cf6d8abeb | Web |
| hrp-core-web04 | i-04d81abd203126050 | Web |
| hrp-core-app03 | i-0b5fcf61e94e9f599 | App |
| hrp-core-app04 | i-0b40c1c713cfdeac8 | App |
| hrp-core-db03 | i-0d780c0fa44ba72e9 | DB |
| hrp-core-db04 | i-0117a71b9b09d45f7 | DB |

## Common Issues

### Agent Fails to Connect
- Verify instance profile is attached: `aws ec2 describe-iam-instance-profile-associations`
- Check trusted account configuration in staging account
- Ensure "Failback and in-AWS right-sizing roles" is selected

### Source Servers Not Appearing
- Wait 5-10 minutes for initial replication to start
- Check agent logs on source instance
- Verify network connectivity to DRS endpoints

### Permission Errors
- Ensure `AWSElasticDisasterRecoveryEc2InstancePolicy` is attached to role
- Verify trusted account role exists in staging account

## References
- Full guide: [DRS_CROSS_ACCOUNT_SETUP.md](../../DRS_CROSS_ACCOUNT_SETUP.md)
- AWS Docs: [Agent Installer Parameters](https://docs.aws.amazon.com/drs/latest/userguide/installer-parameters.html)
