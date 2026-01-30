# AWS Accounts Overview

## Account Summary

You have access to **3 AWS accounts** with AdministratorAccess:

| Account ID | Profile Name | User | Purpose |
|------------|--------------|------|---------|
| 777788889999 | 777788889999_AdministratorAccess | jocousen@amazon.com | Source Account (Production) |
| 111122223333 | 111122223333_AdministratorAccess | jocousen@amazon.com | Target Account (DR/Recovery) |
| 444455556666 | 444455556666_AdministratorAccess | jocousen@amazon.com | New Account (Empty) |

## Account 1: 777788889999 (Source/Production)

**Role**: Source account with production workloads

### EC2 Instances (us-east-1)
6 Windows Server 2022 instances (01/02 series):

**Database Servers (Wave 1 - Critical)**
- i-08079c6d44888cd37 - hrp-core-db01-az1 (10.10.220.132)
- i-0ead3f8fb7d6a6745 - hrp-core-db02-az1 (10.10.220.13)

**Application Servers (Wave 2 - High)**
- i-053654498d177ea0d - hrp-core-app01-az1 (10.10.219.147)
- i-0284e604b2cb3d9a4 - hrp-core-app02-az1 (10.10.219.65)

**Web Servers (Wave 3 - Medium)**
- i-0a24e3429ec060c7e - hrp-core-web01-az1 (10.10.222.81)
- i-0f46d8897d2b98824 - hrp-core-web02-az1 (10.10.220.111)

### Configuration
- **VPC**: vpc-08c7f2a39d0faf1d2
- **Subnet**: subnet-0151a0dd78ac559c4
- **Security Group**: sg-06f217dba4afdd97f
- **Key Pair**: awsdemo-keypair-RSA-PEM
- **IAM Profile**: demo-ec2-profile

### DR Configuration
All instances tagged with:
- `dr:enabled=true`
- `dr:recovery-strategy=drs`
- `dr:wave=1/2/3`
- `dr:priority=critical/high/medium`
- `AWSDRS=AllowLaunchingIntoThisInstance`

## Account 2: 111122223333 (Target/DR)

**Role**: Disaster recovery target account

### EC2 Instances (us-east-1)
6 Windows Server 2022 instances (03/04 series) - **NEWLY CREATED**:

**Database Servers (Wave 1 - Critical)**
- i-0d780c0fa44ba72e9 - hrp-core-db03-az1 (10.10.189.130) ✅
- i-0117a71b9b09d45f7 - hrp-core-db04-az1 (10.10.187.143) ✅

**Application Servers (Wave 2 - High)**
- i-0b5fcf61e94e9f599 - hrp-core-app03-az1 (10.10.186.182) ✅
- i-0b40c1c713cfdeac8 - hrp-core-app04-az1 (10.10.187.61) ✅

**Web Servers (Wave 3 - Medium)**
- i-00c5c7b3cf6d8abeb - hrp-core-web03-az1 (10.10.189.235) ✅
- i-04d81abd203126050 - hrp-core-web04-az1 (10.10.187.32) ✅

### Configuration
- **VPC**: vpc-08c7f2a39d0faf1d2 (same as source)
- **Subnet**: subnet-0de127c19dc67593e (different from source)
- **Security Group**: sg-021589d4447675144
- **Key Pair**: RSA-PEM-TARGET-us-east-1
- **IAM Profile**: demo-ec2-profile ✅ Attached

### Current Status
- ✅ Instances created and running
- ✅ IAM profiles attached
- ⏳ Waiting for SSM agents to come online (5-10 min for Windows)
- ⏳ Ready for DRS agent installation

### Available IAM Profiles
- demo-ec2-profile
- demo-ec2-profile-west2
- dr-automation-role
- AWSElasticDisasterRecoveryRecoveryInstanceRole
- AWSElasticDisasterRecoveryReplicationServerRole
- AWSElasticDisasterRecoveryConversionServerRole

## Account 3: 444455556666 (New/Empty)

**Role**: Available for additional workloads or testing

### Current State
- ✅ Credentials configured
- ✅ Access verified
- 📭 No EC2 instances in us-east-1
- 📭 No EC2 instances in us-west-2
- 🆕 Clean slate for new deployments

### Potential Uses
1. **Additional DR target** for cross-account replication
2. **Testing environment** for DR procedures
3. **Isolated workload** deployment
4. **Multi-region DR** architecture

## DRS Replication Architecture

### Current Setup (In Progress)

```
Source Account (777788889999)          Target Account (111122223333)
us-east-1                              us-west-2 (DRS Replication)
├─ db01/02 (existing)         ──DRS──> [Recovery Instances]
├─ app01/02 (existing)        ──DRS──> [Recovery Instances]
└─ web01/02 (existing)        ──DRS──> [Recovery Instances]

Target Account (111122223333)
us-east-1 (New Instances)
├─ db03/04 (ready for DRS)    ──DRS──> us-west-2
├─ app03/04 (ready for DRS)   ──DRS──> us-west-2
└─ web03/04 (ready for DRS)   ──DRS──> us-west-2
```

## Next Steps

### Immediate (Account 111122223333)
1. **Monitor SSM agents**: Run `./check_ssm_status.sh` every 2-3 minutes
2. **Deploy DRS agents**: Run `./deploy_drs_agents.sh` when SSM is online
3. **Configure replication**: Set up DRS to replicate to us-west-2
4. **Monitor initial sync**: Wait for data replication to complete

### Future (Account 444455556666)
1. **Decide purpose**: DR target, testing, or new workloads?
2. **Set up networking**: Create VPCs, subnets, security groups
3. **Configure IAM**: Set up instance profiles and roles
4. **Deploy resources**: Based on chosen purpose

## Quick Commands

### Switch Between Accounts
```bash
# Source account (777788889999)
export AWS_PROFILE="777788889999_AdministratorAccess"

# Target account (111122223333)
export AWS_PROFILE="111122223333_AdministratorAccess"

# New account (444455556666)
export AWS_PROFILE="444455556666_AdministratorAccess"
```

### Check Current Account
```bash
AWS_PAGER="" aws sts get-caller-identity
```

### List Instances by Account
```bash
# Account 777788889999
AWS_PAGER="" AWS_PROFILE="777788889999_AdministratorAccess" \
  aws ec2 describe-instances --region us-east-1 \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name]' \
  --output table

# Account 111122223333
AWS_PAGER="" AWS_PROFILE="111122223333_AdministratorAccess" \
  aws ec2 describe-instances --region us-east-1 \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name]' \
  --output table

# Account 444455556666
AWS_PAGER="" AWS_PROFILE="444455556666_AdministratorAccess" \
  aws ec2 describe-instances --region us-east-1 \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name]' \
  --output table
```

## Scripts Available

All scripts are configured for account 111122223333:
- `check_ssm_status.sh` - Monitor SSM agent registration
- `deploy_drs_agents.sh` - Install DRS agents and configure replication
- `attach_iam_profile.sh` - Attach IAM profiles (completed)
- `create_target_instances.sh` - Create EC2 instances (completed)

## Documentation

- `DRS_DEPLOYMENT_SUMMARY.md` - Detailed deployment status and troubleshooting
- `AWS_ACCOUNTS_OVERVIEW.md` - This file
