# DRS Deployment - COMPLETE ✅

## Summary

Successfully deployed AWS Elastic Disaster Recovery (DRS) agents to 6 Windows Server 2022 instances in account **160885257264**, replicating to **us-west-2**.

## Deployment Timeline

- **Created**: 6 EC2 instances (db03/04, app03/04, web03/04)
- **Configured**: IAM instance profiles for SSM and DRS
- **Installed**: DRS agents via SSM Run Command
- **Status**: All 6 source servers registered and replicating

## DRS Source Servers (us-west-2)

| Source Server ID | Hostname | Replication State | Launch Status |
|------------------|----------|-------------------|---------------|
| s-5320cefb1068ac94f | EC2AMAZ-56UDGUH | INITIAL_SYNC | NOT_STARTED |
| s-57bba8f3802416ac0 | EC2AMAZ-9BGSU7T | INITIAL_SYNC | NOT_STARTED |
| s-5929c8c0ba951b420 | EC2AMAZ-8LTU1H7 | INITIAL_SYNC | NOT_STARTED |
| s-5a267999040232be4 | EC2AMAZ-SB7FLCG | INITIAL_SYNC | NOT_STARTED |
| s-5818e09d74691299e | EC2AMAZ-MI0EQFF | INITIATING | NOT_STARTED |
| s-5f3d4ff875a576744 | EC2AMAZ-JUS0S3A | INITIAL_SYNC | NOT_STARTED |

## Source Instances (us-east-1)

### Database Servers (Wave 1 - Critical)
- **i-0d780c0fa44ba72e9** - hrp-core-db03-az1 (10.10.189.130)
- **i-0117a71b9b09d45f7** - hrp-core-db04-az1 (10.10.187.143)

### Application Servers (Wave 2 - High)
- **i-0b5fcf61e94e9f599** - hrp-core-app03-az1 (10.10.186.182)
- **i-0b40c1c713cfdeac8** - hrp-core-app04-az1 (10.10.187.61)

### Web Servers (Wave 3 - Medium)
- **i-00c5c7b3cf6d8abeb** - hrp-core-web03-az1 (10.10.189.235)
- **i-04d81abd203126050** - hrp-core-web04-az1 (10.10.187.32)

## Replication Status

**Current State**: INITIAL_SYNC (First-time data replication in progress)

Initial sync duration depends on:
- Data volume on each instance
- Network bandwidth
- Disk I/O performance

Typical timeline:
- Small instances (<100GB): 1-4 hours
- Medium instances (100-500GB): 4-12 hours
- Large instances (>500GB): 12+ hours

## Next Steps

### 1. Monitor Replication Progress

**DRS Console**: https://us-west-2.console.aws.amazon.com/drs/home?region=us-west-2#/sourceServers

**CLI Command**:
```bash
AWS_PAGER="" AWS_PROFILE="160885257264_AdministratorAccess" \
  aws drs describe-source-servers --region us-west-2 \
  --query 'items[*].[sourceServerID,tags.Name,dataReplicationInfo.dataReplicationState,dataReplicationInfo.replicatedDisks[0].backloggedStorageBytes]' \
  --output table
```

Watch for state progression:
1. INITIATING → Initial connection
2. INITIAL_SYNC → First-time data copy
3. CONTINUOUS_REPLICATION → Ongoing replication (ready for recovery)

### 2. Configure Launch Settings

Once replication reaches **CONTINUOUS_REPLICATION**, configure launch settings for each source server:

```bash
# Example: Configure launch settings for a source server
AWS_PAGER="" AWS_PROFILE="160885257264_AdministratorAccess" \
  aws drs update-launch-configuration \
  --region us-west-2 \
  --source-server-id s-5320cefb1068ac94f \
  --target-instance-type-right-sizing-method BASIC \
  --copy-private-ip false \
  --copy-tags true
```

**Key Settings to Configure**:
- Instance type (match or adjust for DR environment)
- Subnet placement (target VPC/subnet in us-west-2)
- Security groups
- IAM instance profile
- Private IP handling
- Licensing (Windows BYOL vs AWS-provided)

### 3. Test Recovery (Drill)

After reaching CONTINUOUS_REPLICATION:

```bash
# Initiate recovery drill (non-disruptive test)
AWS_PAGER="" AWS_PROFILE="160885257264_AdministratorAccess" \
  aws drs start-recovery \
  --region us-west-2 \
  --source-servers sourceServerID=s-5320cefb1068ac94f \
  --is-drill true \
  --tags Environment=Test,Purpose=DR-Drill
```

**Drill Benefits**:
- Tests recovery process without affecting production
- Validates launch settings
- Confirms application functionality
- Identifies configuration issues

### 4. Production Recovery (When Needed)

For actual disaster recovery:

```bash
# Initiate production recovery
AWS_PAGER="" AWS_PROFILE="160885257264_AdministratorAccess" \
  aws drs start-recovery \
  --region us-west-2 \
  --source-servers sourceServerID=s-5320cefb1068ac94f \
  --is-drill false
```

## Monitoring Commands

### Check Replication Status
```bash
AWS_PAGER="" AWS_PROFILE="160885257264_AdministratorAccess" \
  aws drs describe-source-servers --region us-west-2 \
  --query 'items[*].[sourceServerID,tags.Name,dataReplicationInfo.dataReplicationState]' \
  --output table
```

### Check Replication Lag
```bash
AWS_PAGER="" AWS_PROFILE="160885257264_AdministratorAccess" \
  aws drs describe-source-servers --region us-west-2 \
  --query 'items[*].[sourceServerID,tags.Name,dataReplicationInfo.lagDuration]' \
  --output table
```

### List Recovery Jobs
```bash
AWS_PAGER="" AWS_PROFILE="160885257264_AdministratorAccess" \
  aws drs describe-jobs --region us-west-2 \
  --query 'items[*].[jobID,type,status,creationDateTime]' \
  --output table
```

## Cost Considerations

### DRS Pricing (us-west-2)
- **Per server**: ~$0.028/hour (~$20/month per server)
- **6 servers**: ~$120/month for continuous replication
- **Storage**: EBS snapshots in staging area (minimal cost)
- **Data transfer**: Replication traffic (typically covered by AWS)

### Recovery Costs (Only During DR Event)
- EC2 instances in us-west-2 (only when recovered)
- EBS volumes for recovered instances
- Data transfer out (if accessing from internet)

## Architecture Overview

```
Account: 160885257264

Source Region (us-east-1)              Target Region (us-west-2)
┌─────────────────────────┐           ┌──────────────────────────┐
│ VPC: vpc-08c7f2a39d0faf1d2│           │ DRS Staging Area         │
│ Subnet: subnet-0de127c19dc67593e     │ - Replication Servers    │
│                         │           │ - EBS Snapshots          │
│ Database Servers (2)    │──DRS────▶ │ - Conversion Servers     │
│ Application Servers (2) │ Replicate │                          │
│ Web Servers (2)         │           │ Recovery Instances       │
│                         │           │ (Created on demand)      │
└─────────────────────────┘           └──────────────────────────┘
```

## Automated Deployment Script

The `deploy_drs_agents.sh` script has been enhanced to support multiple accounts:

```bash
# Usage
./deploy_drs_agents.sh [account_id] [source_region] [target_region]

# Examples
./deploy_drs_agents.sh                                    # Use defaults (160885257264)
./deploy_drs_agents.sh 891376951562 us-east-1 us-west-2  # Different account
./deploy_drs_agents.sh 664418995426 us-east-1 eu-west-1  # New account, different region
```

**Features**:
- Auto-discovers instances with `dr:enabled=true` tag
- Validates AWS credentials
- Checks SSM agent status
- Installs DRS agents via SSM
- Non-interactive (fully automated)

## Troubleshooting

### Replication Stuck in INITIATING
- Check network connectivity from source to us-west-2
- Verify security groups allow outbound HTTPS (443)
- Check DRS service endpoints are reachable

### High Replication Lag
- Check source instance disk I/O
- Verify network bandwidth
- Review CloudWatch metrics for DRS

### Agent Installation Failed
- Check SSM agent is online
- Verify IAM instance profile has DRS permissions
- Review SSM Run Command output

## Documentation

- **AWS DRS Console**: https://us-west-2.console.aws.amazon.com/drs/home?region=us-west-2
- **AWS DRS Documentation**: https://docs.aws.amazon.com/drs/
- **SSM Fleet Manager**: https://us-east-1.console.aws.amazon.com/systems-manager/fleet-manager

## Files Created

- `create_target_instances.sh` - EC2 instance creation script
- `attach_iam_profile.sh` - IAM profile attachment script
- `check_ssm_status.sh` - SSM agent status checker
- `deploy_drs_agents.sh` - DRS agent deployment script (enhanced)
- `DRS_DEPLOYMENT_SUMMARY.md` - Initial deployment guide
- `AWS_ACCOUNTS_OVERVIEW.md` - Multi-account overview
- `DRS_DEPLOYMENT_COMPLETE.md` - This file

## Success Criteria ✅

- [x] 6 EC2 instances created in account 160885257264
- [x] IAM instance profiles attached
- [x] SSM agents online
- [x] DRS agents installed
- [x] Source servers registered in us-west-2
- [x] Initial sync started
- [ ] Initial sync completed (in progress)
- [ ] Launch settings configured (next step)
- [ ] Recovery drill performed (next step)

## Deployment Complete! 🎉

All DRS agents are successfully installed and replicating. Monitor the initial sync progress and configure launch settings once replication reaches CONTINUOUS_REPLICATION state.
