# HRP DRS Deployment Strategy

## Overview

The HRP environment uses a **split deployment strategy** for DRS agent installation:

- **01/02 instances**: Same-account replication (160885257264 → 160885257264)
- **03/04 instances**: Cross-account replication (160885257264 → 891376951562)

## Architecture

```
Source Account: 160885257264
├── 01/02 Instances (Production)
│   ├── hrp-core-web01, hrp-core-web02
│   ├── hrp-core-app01, hrp-core-app02
│   └── hrp-core-db01, hrp-core-db02
│   └─→ DRS Replication → Same Account (160885257264)
│
└── 03/04 Instances (Test/Dev)
    ├── hrp-core-web03, hrp-core-web04
    ├── hrp-core-app03, hrp-core-app04
    └── hrp-core-db03, hrp-core-db04
    └─→ DRS Replication → Staging Account (891376951562)
```

## Rationale

### Same-Account (01/02)
- Production instances remain within the same AWS account
- Simpler IAM permissions (no cross-account trust required)
- Faster recovery within the same account
- Standard DRS agent installation (no `--account-id` parameter)

### Cross-Account (03/04)
- Test/Dev instances replicate to staging account
- Isolates staging resources from production account
- Enables testing of cross-account recovery workflows
- Requires `--account-id` parameter during agent installation

## Instance Reference

### 01/02 Instances (Same-Account)

| Instance Name | Instance ID | Type | Target Account |
|--------------|-------------|------|----------------|
| hrp-core-web01 | TODO | Web | 160885257264 |
| hrp-core-web02 | TODO | Web | 160885257264 |
| hrp-core-app01 | TODO | App | 160885257264 |
| hrp-core-app02 | TODO | App | 160885257264 |
| hrp-core-db01 | TODO | DB | 160885257264 |
| hrp-core-db02 | TODO | DB | 160885257264 |

### 03/04 Instances (Cross-Account)

| Instance Name | Instance ID | Type | Target Account |
|--------------|-------------|------|----------------|
| hrp-core-web03 | i-00c5c7b3cf6d8abeb | Web | 891376951562 |
| hrp-core-web04 | i-04d81abd203126050 | Web | 891376951562 |
| hrp-core-app03 | i-0b5fcf61e94e9f599 | App | 891376951562 |
| hrp-core-app04 | i-0b40c1c713cfdeac8 | App | 891376951562 |
| hrp-core-db03 | i-0d780c0fa44ba72e9 | DB | 891376951562 |
| hrp-core-db04 | i-0117a71b9b09d45f7 | DB | 891376951562 |

## Deployment Commands

### Deploy All Instances (Recommended)
```bash
./scripts/deploy-hrp-instances.sh all
```

This will:
1. Deploy 01/02 instances with same-account replication
2. Deploy 03/04 instances with cross-account replication

### Deploy by Strategy

**Same-Account (01/02):**
```bash
./scripts/deploy-hrp-instances.sh all-01-02
```

**Cross-Account (03/04):**
```bash
./scripts/deploy-hrp-instances.sh all-03-04
```

### Deploy by Tier

**Web Servers:**
```bash
./scripts/deploy-hrp-instances.sh web-01-02  # Same-account
./scripts/deploy-hrp-instances.sh web-03-04  # Cross-account
```

**App Servers:**
```bash
./scripts/deploy-hrp-instances.sh app-01-02  # Same-account
./scripts/deploy-hrp-instances.sh app-03-04  # Cross-account
```

**Database Servers:**
```bash
./scripts/deploy-hrp-instances.sh db-01-02   # Same-account
./scripts/deploy-hrp-instances.sh db-03-04   # Cross-account
```

## Prerequisites

### For Same-Account (01/02)

**In Source Account (160885257264):**
1. DRS initialized: `aws drs initialize-service --region us-east-1`
2. IAM role with `AWSElasticDisasterRecoveryEc2InstancePolicy`
3. Instance profile attached to 01/02 instances
4. SSM Agent running on instances

### For Cross-Account (03/04)

**In Staging Account (891376951562):**
1. DRS initialized: `aws drs initialize-service --region us-east-1`
2. Source account (160885257264) added as "Trusted Account"
3. "Failback and in-AWS right-sizing roles" enabled

**In Source Account (160885257264):**
1. IAM role with `AWSElasticDisasterRecoveryEc2InstancePolicy`
2. Instance profile attached to 03/04 instances
3. SSM Agent running on instances

## Agent Installation Details

### Same-Account Installation (01/02)
```powershell
# No --account-id parameter
AwsReplicationWindowsInstaller.exe --region us-east-1 --no-prompt
```

The agent uses the instance profile to register with DRS in the same account.

### Cross-Account Installation (03/04)
```powershell
# With --account-id parameter
AwsReplicationWindowsInstaller.exe --region us-east-1 --account-id 891376951562 --no-prompt
```

The agent uses the instance profile to assume a role in the staging account and registers there.

## Verification

### Check Same-Account Source Servers (01/02)
```bash
# In source account (160885257264)
aws drs describe-source-servers --region us-east-1 \
  --query 'items[?contains(hostname, `01`) || contains(hostname, `02`)]'
```

### Check Cross-Account Source Servers (03/04)
```bash
# In staging account (891376951562)
aws drs describe-source-servers --region us-east-1 \
  --query 'items[?contains(hostname, `03`) || contains(hostname, `04`)]'
```

## Troubleshooting

### 01/02 Instances Not Appearing in Source Account
1. Verify DRS is initialized in source account
2. Check instance profile is attached
3. Verify agent service is running
4. Check agent logs: `C:\ProgramData\Amazon\AWS Replication Agent\logs\agent.log`

### 03/04 Instances Not Appearing in Staging Account
1. Verify trusted account configuration in staging account
2. Ensure "Failback and in-AWS right-sizing roles" is enabled
3. Check instance profile is attached
4. Verify agent was installed with `--account-id 891376951562`
5. Check agent logs for cross-account errors

## Recovery Testing

### Same-Account Recovery (01/02)
```bash
# In source account (160885257264)
aws drs start-recovery \
  --source-servers sourceServerID=s-1234567890abcdef0 \
  --is-drill true
```

### Cross-Account Recovery (03/04)
```bash
# In staging account (891376951562)
aws drs start-recovery \
  --source-servers sourceServerID=s-1234567890abcdef0 \
  --is-drill true
```

## Cost Considerations

### Same-Account (01/02)
- Staging area resources in source account
- EBS snapshots in source account
- Data transfer within same account (no cross-account charges)

### Cross-Account (03/04)
- Staging area resources in staging account
- EBS snapshots in staging account
- Cross-account data transfer charges apply
- Separate billing for staging resources

## Security Considerations

### Same-Account (01/02)
- Standard DRS IAM permissions
- No cross-account trust required
- Simpler security model

### Cross-Account (03/04)
- Cross-account IAM trust relationship
- Trusted account configuration required
- Additional audit logging for cross-account access
- Separate CloudTrail logs in each account

## Related Documentation

- [DRS Cross-Account Setup Guide](../../DRS_CROSS_ACCOUNT_SETUP.md)
- [DRS Cross-Account Quick Start](DRS_CROSS_ACCOUNT_QUICK_START.md)
- [DRS Agent Deployment README](../../scripts/README-DRS-AGENT-DEPLOYMENT.md)
- [AWS DRS Documentation](https://docs.aws.amazon.com/drs/)

## TODO

- [ ] Obtain instance IDs for 01/02 instances
- [ ] Update `scripts/deploy-hrp-instances.sh` with actual 01/02 instance IDs
- [ ] Test same-account deployment on 01/02 instances
- [ ] Test cross-account deployment on 03/04 instances
- [ ] Document recovery procedures for both strategies
- [ ] Create runbooks for failover scenarios
