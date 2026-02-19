# DRS Agent Deployment Summary

## Instance Creation - ✅ COMPLETE

Successfully created 6 Windows Server 2022 instances in account **160885257264**:

### Database Servers (Wave 1 - Critical)
- **i-0d780c0fa44ba72e9** - hrp-core-db03-az1 (10.10.189.130)
- **i-0117a71b9b09d45f7** - hrp-core-db04-az1 (10.10.187.143)

### Application Servers (Wave 2 - High)
- **i-0b5fcf61e94e9f599** - hrp-core-app03-az1 (10.10.186.182)
- **i-0b40c1c713cfdeac8** - hrp-core-app04-az1 (10.10.187.61)

### Web Servers (Wave 3 - Medium)
- **i-00c5c7b3cf6d8abeb** - hrp-core-web03-az1 (10.10.189.235)
- **i-04d81abd203126050** - hrp-core-web04-az1 (10.10.187.32)

## Configuration Details

- **AMI**: ami-043cc489b5239c3de (Windows Server 2022 English Full Base)
- **Instance Type**: t3.large
- **VPC**: vpc-08c7f2a39d0faf1d2
- **Subnet**: subnet-0de127c19dc67593e
- **Security Group**: sg-021589d4447675144
- **Key Pair**: RSA-PEM-TARGET-us-east-1
- **IAM Profile**: demo-ec2-profile ✅ Attached

## Current Status - ⏳ WAITING FOR SSM

Windows instances typically take **5-10 minutes** to fully boot and register SSM agents.

### Timeline
- **00:00** - Instances launched
- **00:30** - Instances running
- **01:00** - IAM profiles attached
- **02:00** - Current time
- **05:00-10:00** - Expected SSM agent registration (Windows boot time)

## Next Steps

### 1. Monitor SSM Agent Registration
```bash
./check_ssm_status.sh
```

Run this every 2-3 minutes until all 6 agents show "Online" status.

### 2. Deploy DRS Agents
Once all SSM agents are online:
```bash
./deploy_drs_agents.sh
```

This will:
- Install AWS DRS agents on all 6 instances
- Configure replication to **us-west-2**
- Monitor installation progress
- Verify DRS source server registration

### 3. Monitor DRS Replication
After DRS agents are installed:
- Console: https://us-west-2.console.aws.amazon.com/drs/home?region=us-west-2#/sourceServers
- Wait for "Initial Sync" to complete (can take hours depending on data size)
- Configure launch settings for each source server
- Test recovery when ready

## Troubleshooting

### If SSM Agents Don't Come Online After 15 Minutes

1. **Check VPC Endpoints** (for private subnet):
   ```bash
   AWS_PAGER="" AWS_PROFILE="160885257264_AdministratorAccess" \
     aws ec2 describe-vpc-endpoints --region us-east-1 \
     --filters "Name=vpc-id,Values=vpc-08c7f2a39d0faf1d2" \
     --query 'VpcEndpoints[*].[ServiceName,State]' --output table
   ```
   
   Required endpoints for SSM in private subnet:
   - com.amazonaws.us-east-1.ssm
   - com.amazonaws.us-east-1.ssmmessages
   - com.amazonaws.us-east-1.ec2messages

2. **Check Security Group** allows outbound HTTPS (443):
   ```bash
   AWS_PAGER="" AWS_PROFILE="160885257264_AdministratorAccess" \
     aws ec2 describe-security-groups --region us-east-1 \
     --group-ids sg-021589d4447675144 \
     --query 'SecurityGroups[*].IpPermissionsEgress' --output table
   ```

3. **Check Instance Console Output**:
   ```bash
   AWS_PAGER="" AWS_PROFILE="160885257264_AdministratorAccess" \
     aws ec2 get-console-output --region us-east-1 \
     --instance-id i-0d780c0fa44ba72e9 --latest
   ```

4. **Manual SSM Agent Installation** (if needed):
   - Connect via RDP using key pair
   - Download: https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/windows_amd64/AmazonSSMAgentSetup.exe
   - Install and restart service

## DRS Agent Installation Details

The SSM document `AWSDisasterRecovery-InstallDRAgentOnInstance` will:
1. Download DRS agent installer
2. Install agent with replication region parameter
3. Configure agent to replicate to us-west-2
4. Start replication service
5. Register with DRS in target region

Installation typically takes **5-10 minutes** per instance.

## Tags Applied

All instances have identical tags to their 01/02 counterparts:
- `dr:enabled=true`
- `dr:recovery-strategy=drs`
- `dr:wave=1/2/3` (based on tier)
- `dr:priority=critical/high/medium`
- `AWSDRS=AllowLaunchingIntoThisInstance`
- `Application=HRP-Core-Platform`
- `BusinessUnit=HRP`
- `Customer=CustomerA`
- Plus service-specific tags

## Scripts Available

- `check_ssm_status.sh` - Check SSM agent registration status
- `deploy_drs_agents.sh` - Deploy DRS agents to all instances
- `attach_iam_profile.sh` - Attach IAM profile (already completed)
- `create_target_instances.sh` - Create instances (already completed)
