# DRS Agent Deployer Spec

## Overview

This spec contains all documentation and scripts for deploying AWS DRS agents to EC2 instances with support for both same-account and cross-account replication strategies.

## Quick Start

### Deploy to External Environment
```bash
# Deploy all instances (both strategies)
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh all

# Deploy only 01/02 (same-account)
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh all-01-02

# Deploy only 03/04 (cross-account)
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh all-03-04
```

## Directory Structure

```
.kiro/specs/drs-agent-deployer/
├── README.md                              # This file
├── DRS_CROSS_ACCOUNT_SETUP.md            # Complete cross-account setup guide
├── README-DRS-AGENT-DEPLOYMENT.md        # Detailed deployment documentation
├── EXTERNAL-DEPLOYMENT-QUICK-REFERENCE.md     # Quick reference card
├── scripts/
│   ├── install-drs-agent-cross-account.ps1    # PowerShell installer (runs on Windows)
│   ├── deploy-drs-agent-cross-account.sh      # Bash orchestrator (runs via SSM)
│   └── deploy-hrp-instances.sh                # External-specific deployment wrapper
└── docs/
    ├── DRS_CROSS_ACCOUNT_QUICK_START.md       # Quick start guide
    └── EXTERNAL_DRS_DEPLOYMENT_STRATEGY.md         # External deployment strategy
```

## Documentation

### Main Guides
- **[DRS_CROSS_ACCOUNT_SETUP.md](DRS_CROSS_ACCOUNT_SETUP.md)** - Complete setup guide for cross-account DRS
- **[README-DRS-AGENT-DEPLOYMENT.md](README-DRS-AGENT-DEPLOYMENT.md)** - Detailed deployment documentation
- **[EXTERNAL-DEPLOYMENT-QUICK-REFERENCE.md](EXTERNAL-DEPLOYMENT-QUICK-REFERENCE.md)** - Quick reference for External deployment

### Additional Documentation
- **[docs/DRS_CROSS_ACCOUNT_QUICK_START.md](docs/DRS_CROSS_ACCOUNT_QUICK_START.md)** - Quick start guide
- **[docs/EXTERNAL_DRS_DEPLOYMENT_STRATEGY.md](docs/EXTERNAL_DRS_DEPLOYMENT_STRATEGY.md)** - External deployment strategy

## Scripts

### PowerShell Script (Windows)
**[scripts/install-drs-agent-cross-account.ps1](scripts/install-drs-agent-cross-account.ps1)**
- Runs on Windows EC2 instances
- Downloads and installs DRS agent
- Supports `--account-id` parameter for cross-account replication

### Bash Orchestrator
**[scripts/deploy-drs-agent-cross-account.sh](scripts/deploy-drs-agent-cross-account.sh)**
- Runs from local machine
- Uploads PowerShell script to S3
- Executes via SSM Run Command
- Monitors progress and displays results

### External Deployment Wrapper
**[scripts/deploy-hrp-instances.sh](scripts/deploy-hrp-instances.sh)**
- Pre-configured for External environment
- Handles split deployment strategy:
  - 01/02 instances → Same-account (160885257264)
  - 03/04 instances → Cross-account (123456789012)

## Deployment Strategies

### Same-Account Replication
- **Target**: 01/02 instances
- **Source Account**: 160885257264
- **Target Account**: 160885257264 (same)
- **Agent Installation**: No `--account-id` parameter

### Cross-Account Replication
- **Target**: 03/04 instances
- **Source Account**: 160885257264
- **Target Account**: 123456789012 (staging)
- **Agent Installation**: With `--account-id 123456789012`

## Prerequisites

### For Same-Account (01/02)
- DRS initialized in source account (160885257264)
- IAM instance profile with `AWSElasticDisasterRecoveryEc2InstancePolicy`
- SSM Agent running on instances

### For Cross-Account (03/04)
- DRS initialized in staging account (123456789012)
- Source account (160885257264) added as "Trusted Account"
- "Failback and in-AWS right-sizing roles" enabled
- IAM instance profile with `AWSElasticDisasterRecoveryEc2InstancePolicy`
- SSM Agent running on instances

## Usage Examples

### Deploy All External Instances
```bash
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh all
```

### Deploy by Strategy
```bash
# Same-account (01/02)
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh all-01-02

# Cross-account (03/04)
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh all-03-04
```

### Deploy by Tier
```bash
# Web servers
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh web-01-02
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh web-03-04

# App servers
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh app-01-02
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh app-03-04

# Database servers
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh db-01-02
.kiro/specs/drs-agent-deployer/scripts/deploy-hrp-instances.sh db-03-04
```

### Manual Deployment (Custom Instances)
```bash
# Same-account replication
.kiro/specs/drs-agent-deployer/scripts/deploy-drs-agent-cross-account.sh \
  --instance-ids "i-1234567890abcdef0,i-1234567890abcdef1" \
  --region us-east-1

# Cross-account replication
.kiro/specs/drs-agent-deployer/scripts/deploy-drs-agent-cross-account.sh \
  --instance-ids "i-1234567890abcdef0,i-1234567890abcdef1" \
  --account-id 123456789012 \
  --region us-east-1
```

## Verification

### Check Same-Account Source Servers
```bash
# In source account (160885257264)
aws drs describe-source-servers --region us-east-1
```

### Check Cross-Account Source Servers
```bash
# In staging account (123456789012)
aws drs describe-source-servers --region us-east-1
```

## Troubleshooting

See [README-DRS-AGENT-DEPLOYMENT.md](README-DRS-AGENT-DEPLOYMENT.md#troubleshooting) for detailed troubleshooting steps.

Common issues:
- SSM connectivity problems
- Instance profile not attached
- Trusted account not configured
- Agent installation failures

## Related Documentation

- [AWS DRS Documentation](https://docs.aws.amazon.com/drs/)
- [DRS Agent Installation](https://docs.aws.amazon.com/drs/latest/userguide/agent-installation.html)
- [DRS Installer Parameters](https://docs.aws.amazon.com/drs/latest/userguide/installer-parameters.html)
- [Adding Trusted Accounts](https://docs.aws.amazon.com/drs/latest/userguide/adding-trusted-account.html)

## TODO

- [ ] Obtain instance IDs for 01/02 instances
- [ ] Update `scripts/deploy-hrp-instances.sh` with actual 01/02 instance IDs
- [ ] Test same-account deployment on 01/02 instances
- [ ] Test cross-account deployment on 03/04 instances
- [ ] Document recovery procedures
- [ ] Create runbooks for failover scenarios
