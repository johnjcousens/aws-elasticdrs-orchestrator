# AWS DRS Cross-Account Setup Guide

## Overview

To install DRS agents on EC2 instances in **Source Account** (160885257264) that replicate to **Staging Account** (891376951562):

**Use the `--account-id` parameter during agent installation to specify the staging account.**

## Architecture

```
Source Account (160885257264)
├── EC2 Instances (hrp-core-03, hrp-core-04)
├── DRS Agents installed with --account-id 891376951562
└── Replication flows TO →

Staging Account (891376951562)
├── DRS Staging Resources (replication servers, EBS snapshots)
├── Source servers registered here
└── Recovery instances launched here
```

## Key Concept: Cross-Account Replication with --account-id

### The --account-id Parameter
When installing the DRS agent, you can use the `--account-id` parameter to replicate to a DIFFERENT AWS account.

**Requirements:**
1. EC2 instance must have an instance profile with `AWSElasticDisasterRecoveryEc2InstancePolicy`
2. Staging account (891376951562) must define source account (160885257264) as a "Trusted Account"
3. Staging account must create "Failback and in-AWS right-sizing roles"

### How It Works
```bash
# On EC2 instance in account 160885257264
AwsReplicationWindowsInstaller.exe --region us-east-1 --account-id 891376951562 --no-prompt
```

This tells the agent: "Replicate this server to account 891376951562 instead of the local account"

## Setup Steps

### 1. In Staging Account (891376951562)

#### A. Initialize DRS
```bash
aws drs initialize-service --region us-east-1
```

#### B. Configure Default Replication Settings
- Define staging area subnet
- Configure EBS encryption (can use default or custom KMS key)
- Set replication server instance type

#### C. Add Source Account as Trusted Account
In DRS Console → Settings → Trusted Accounts:
1. Click "Add trusted accounts and create roles"
2. Enter source account ID: **160885257264**
3. Select **"Failback and in-AWS right-sizing roles"** (REQUIRED for --account-id)
4. This creates IAM role: `DRSFailbackRole_160885257264`

### 2. In Source Account (160885257264)

#### A. Create IAM Instance Profile
Create an instance profile with the `AWSElasticDisasterRecoveryEc2InstancePolicy` managed policy:

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

# Attach AWS managed policy
aws iam attach-role-policy \
  --role-name DRS-EC2-CrossAccount-Role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSElasticDisasterRecoveryEc2InstancePolicy

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name DRS-EC2-CrossAccount-Profile

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name DRS-EC2-CrossAccount-Profile \
  --role-name DRS-EC2-CrossAccount-Role
```

#### B. Attach Instance Profile to EC2 Instances
```bash
# Attach to hrp-core-web03
aws ec2 associate-iam-instance-profile \
  --region us-east-1 \
  --instance-id i-00c5c7b3cf6d8abeb \
  --iam-instance-profile Name=DRS-EC2-CrossAccount-Profile

# Attach to hrp-core-web04
aws ec2 associate-iam-instance-profile \
  --region us-east-1 \
  --instance-id i-04d81abd203126050 \
  --iam-instance-profile Name=DRS-EC2-CrossAccount-Profile

# Repeat for app03, app04, db03, db04...
```

#### C. Install DRS Agents with --account-id

**Option 1: Using SSM (Modified Document)**

You'll need to create a custom SSM document since the AWS-provided one doesn't support `--account-id`. Here's the PowerShell command:

```powershell
# Download installer
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::tls12
$webClient = New-Object System.Net.WebClient
$webClient.DownloadFile(
  'https://aws-elastic-disaster-recovery-us-east-1.s3.us-east-1.amazonaws.com/latest/windows/AwsReplicationWindowsInstaller.exe',
  'C:\Temp\AwsReplicationWindowsInstaller.exe'
)

# Install with --account-id parameter
C:\Temp\AwsReplicationWindowsInstaller.exe --region us-east-1 --account-id 891376951562 --no-prompt
```

**Option 2: Manual Installation via RDP**
1. RDP to each instance
2. Download installer from S3
3. Run: `AwsReplicationWindowsInstaller.exe --region us-east-1 --account-id 891376951562 --no-prompt`

## Important Notes

### The --account-id Parameter
- **This is the key to cross-account replication**
- Tells the agent to replicate to a DIFFERENT account
- Requires EC2 instance profile with `AWSElasticDisasterRecoveryEc2InstancePolicy`
- Requires staging account to have "Failback and in-AWS right-sizing roles" configured

### Agent Installation
- **With --account-id**: Agent replicates to specified account (891376951562)
- **Without --account-id**: Agent replicates to local account (160885257264)
- The agent uses the EC2 instance profile to assume a role in the staging account

### SSM Document Limitation
The AWS-provided `AWSDisasterRecovery-InstallDRAgentOnInstance` SSM document does NOT support the `--account-id` parameter. You must either:
1. Create a custom SSM document with --account-id support
2. Install manually via RDP/SSH
3. Use user data scripts during instance launch

### Replication Flow
```
Source EC2 Instance (Account 160885257264)
    ↓ (DRS Agent with --account-id 891376951562)
    ↓ (Uses instance profile to assume role)
Staging Area (Account 891376951562)
    ↓ (Replication Servers, EBS Snapshots)
Recovery Instances (Account 891376951562)
```

## For Your HRP Environment

### Current Setup
- **Source Account**: 160885257264 (where HRP instances 03/04 are)
- **Staging Account**: 891376951562 (where you want them to replicate)
- **Instances to protect**: hrp-core-web03/04, hrp-core-app03/04, hrp-core-db03/04

### Step-by-Step Implementation

#### 1. In Staging Account (891376951562)
```bash
# Initialize DRS
aws drs initialize-service --region us-east-1

# Add source account as trusted with failback role
# Do this in DRS Console → Settings → Trusted Accounts
# Add account 160885257264 with "Failback and in-AWS right-sizing roles"
```

#### 2. In Source Account (160885257264)
```bash
# Create and attach instance profile (run once)
aws iam create-role --role-name DRS-EC2-CrossAccount-Role \
  --assume-role-policy-document file://trust-policy.json

aws iam attach-role-policy \
  --role-name DRS-EC2-CrossAccount-Role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSElasticDisasterRecoveryEc2InstancePolicy

aws iam create-instance-profile --instance-profile-name DRS-EC2-CrossAccount-Profile
aws iam add-role-to-instance-profile \
  --instance-profile-name DRS-EC2-CrossAccount-Profile \
  --role-name DRS-EC2-CrossAccount-Role

# Attach to instances 03/04
for instance in i-00c5c7b3cf6d8abeb i-04d81abd203126050 i-0b5fcf61e94e9f599 i-0b40c1c713cfdeac8 i-0d780c0fa44ba72e9 i-0117a71b9b09d45f7; do
  aws ec2 associate-iam-instance-profile \
    --region us-east-1 \
    --instance-id $instance \
    --iam-instance-profile Name=DRS-EC2-CrossAccount-Profile
done
```

#### 3. Install DRS Agents
Create custom SSM document or use this PowerShell script via SSM:

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::tls12
$tmpDir = New-Item -ItemType Directory -Path (Join-Path $env:TEMP ([System.Guid]::NewGuid()))
cd $tmpDir
$webClient = New-Object System.Net.WebClient
$webClient.DownloadFile(
  'https://aws-elastic-disaster-recovery-us-east-1.s3.us-east-1.amazonaws.com/latest/windows/AwsReplicationWindowsInstaller.exe',
  (Join-Path $tmpDir 'AwsReplicationWindowsInstaller.exe')
)
.\AwsReplicationWindowsInstaller.exe --region us-east-1 --account-id 891376951562 --no-prompt
cd ..
Remove-Item -Force -Recurse $tmpDir
```

## References
- [AWS DRS Agent Installer Parameters](https://docs.aws.amazon.com/drs/latest/userguide/installer-parameters.html)
- [DRS Agent Installation](https://docs.aws.amazon.com/drs/latest/userguide/agent-installation.html)
- [Adding Trusted Accounts](https://docs.aws.amazon.com/drs/latest/userguide/adding-trusted-account.html)
- [AWSElasticDisasterRecoveryEc2InstancePolicy](https://docs.aws.amazon.com/drs/latest/userguide/security-iam-awsmanpol-AWSElasticDisasterRecoveryEc2InstancePolicy.html)

---
**Key Takeaway**: Use the `--account-id` parameter during agent installation to replicate EC2 instances from source account (160885257264) to staging account (891376951562). This requires an EC2 instance profile and proper trusted account configuration in the staging account.
