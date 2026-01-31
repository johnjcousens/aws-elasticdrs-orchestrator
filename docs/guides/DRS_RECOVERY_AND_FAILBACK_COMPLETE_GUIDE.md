# AWS DRS Recovery and Failback Complete Guide

**Complete reference for AWS Elastic Disaster Recovery (DRS) recovery process, failback procedures, API calls, and IAM permissions**

## Table of Contents

1. [Overview](#overview)
2. [DRS Recovery Process](#drs-recovery-process)
3. [API Call Sequences](#api-call-sequences)
4. [Complete IAM Permissions](#complete-iam-permissions)
5. [Failback Process](#failback-process)
6. [Agent Installation](#agent-installation)
7. [Troubleshooting](#troubleshooting)

---

## Overview

AWS Elastic Disaster Recovery (DRS) provides continuous block-level replication from source servers to AWS. This guide covers the complete recovery and failback lifecycle.

### Key Concepts

- **Source Server**: Original server being protected (on-premises, VMware, cloud)
- **Staging Server**: Lightweight EC2 instance that receives replicated data
- **Recovery Instance**: Full EC2 instance launched during recovery/drill
- **Replication Server**: AWS-managed server handling data replication
- **Recovery Point Objective (RPO)**: Sub-second with continuous replication
- **Recovery Time Objective (RTO)**: Minutes (typically 5-15 minutes)

### Recovery Types

| Type | Purpose | Impact | Cleanup |
|------|---------|--------|---------|
| **Drill** | Test DR without production impact | Creates isolated recovery instances | Automatic termination after drill |
| **Recovery** | Actual disaster recovery | Launches production recovery instances | Manual cleanup after failback |

---

## DRS Recovery Process

### Phase 1: Pre-Recovery (Continuous)

**Ongoing Replication**
```
Source Server → DRS Agent → Staging Area (EBS) → Point-in-Time Snapshots
```

**API Monitoring**:
```python
# Check replication status
response = drs_client.describe_source_servers(
    filters={'sourceServerIDs': [server_id]}
)

for server in response['items']:
    replication_state = server['dataReplicationInfo']['dataReplicationState']
    # States: STOPPED, INITIATING, INITIAL_SYNC, BACKLOG, CREATING_SNAPSHOT,
    #         CONTINUOUS, PAUSED, RESCAN, STALLED, DISCONNECTED
    
    lag_duration = server['dataReplicationInfo']['lagDuration']  # ISO 8601 duration
    replicated_disks = server['dataReplicationInfo']['replicatedDisks']
```

**Required State**: `CONTINUOUS` with low lag (<60 seconds recommended)

### Phase 2: Recovery Initiation

**API Call**: `start_recovery()`

```python
response = drs_client.start_recovery(
    isDrill=True,  # or False for actual recovery
    sourceServers=[
        {
            'sourceServerID': 's-1234567890abcdef0',
            'recoveryInstanceID': 'i-optional-existing'  # Optional for re-launch
        }
    ],
    tags={  # CAUTION: Tags can cause conversion phase to be skipped
        'Environment': 'Production',
        'Application': 'WebApp'
    }
)

job_id = response['job']['jobID']
job_status = response['job']['status']  # PENDING, STARTED, COMPLETED
```

**CRITICAL**: Do NOT include `tags` parameter if you need full EC2 conversion. Tags can cause DRS to skip the conversion phase.

### Phase 3: Recovery Job Execution

**Job Phases**:

1. **Launch Phase** (1-3 minutes)
   - Creates launch template from replication settings
   - Launches EC2 instance from latest snapshot
   - Attaches EBS volumes
   - Configures networking (VPC, subnet, security groups)

2. **Conversion Phase** (2-10 minutes)
   - Installs boot loader
   - Configures network adapters
   - Installs AWS drivers
   - Prepares OS for AWS environment

3. **Completion Phase** (<1 minute)
   - Marks instance as LAUNCHED
   - Updates recovery instance metadata

**Polling Pattern**:
```python
def poll_recovery_job(job_id: str, timeout: int = 1800) -> Dict:
    """Poll DRS job until completion or timeout"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = drs_client.describe_jobs(
            filters={'jobIDs': [job_id]}
        )
        
        job = response['items'][0]
        status = job['status']
        
        if status == 'COMPLETED':
            return {'status': 'SUCCESS', 'job': job}
        elif status == 'FAILED':
            return {'status': 'FAILED', 'error': job.get('error')}
        
        # Check per-server status
        for server in job.get('participatingServers', []):
            launch_status = server.get('launchStatus')
            # States: PENDING, IN_PROGRESS, LAUNCHED, FAILED, TERMINATED
            
            if launch_status == 'LAUNCHED':
                recovery_instance_id = server.get('recoveryInstanceID')
                print(f"Server {server['sourceServerID']} launched: {recovery_instance_id}")
        
        time.sleep(30)  # Poll every 30 seconds
    
    return {'status': 'TIMEOUT'}
```

### Phase 4: Post-Recovery Validation

**Verify Recovery Instance**:
```python
# Get recovery instance details
response = drs_client.describe_recovery_instances(
    filters={'recoveryInstanceIDs': [recovery_instance_id]}
)

recovery_instance = response['items'][0]

# Key fields
ec2_instance_id = recovery_instance['ec2InstanceID']
point_in_time = recovery_instance['pointInTime']  # Recovery point timestamp
is_drill = recovery_instance['isDrill']
failback_info = recovery_instance.get('failback')  # Failback status if applicable

# Verify EC2 instance is running
ec2_response = ec2_client.describe_instances(
    InstanceIds=[ec2_instance_id]
)

instance_state = ec2_response['Reservations'][0]['Instances'][0]['State']['Name']
# States: pending, running, stopping, stopped, shutting-down, terminated
```

**Health Checks**:
- EC2 instance status checks (system + instance)
- Application-specific health endpoints
- Network connectivity tests
- Data integrity validation

---

## API Call Sequences

### Complete Recovery Workflow

```python
# 1. Validate source servers are ready
def validate_servers_ready(server_ids: List[str]) -> bool:
    response = drs_client.describe_source_servers(
        filters={'sourceServerIDs': server_ids}
    )
    
    for server in response['items']:
        state = server['dataReplicationInfo']['dataReplicationState']
        if state != 'CONTINUOUS':
            print(f"Server {server['sourceServerID']} not ready: {state}")
            return False
        
        lag = server['dataReplicationInfo']['lagDuration']
        if parse_duration(lag) > 300:  # 5 minutes
            print(f"Server {server['sourceServerID']} lag too high: {lag}")
            return False
    
    return True

# 2. Start recovery
def start_recovery_job(server_ids: List[str], is_drill: bool) -> str:
    source_servers = [{'sourceServerID': sid} for sid in server_ids]
    
    response = drs_client.start_recovery(
        sourceServers=source_servers,
        isDrill=is_drill
    )
    
    return response['job']['jobID']

# 3. Poll job status
def wait_for_recovery_completion(job_id: str) -> Dict:
    while True:
        response = drs_client.describe_jobs(
            filters={'jobIDs': [job_id]}
        )
        
        job = response['items'][0]
        if job['status'] in ['COMPLETED', 'FAILED']:
            return job
        
        time.sleep(30)

# 4. Get recovery instances
def get_recovery_instances(job_id: str) -> List[str]:
    response = drs_client.describe_jobs(
        filters={'jobIDs': [job_id]}
    )
    
    job = response['items'][0]
    recovery_instance_ids = []
    
    for server in job.get('participatingServers', []):
        if server.get('launchStatus') == 'LAUNCHED':
            recovery_instance_ids.append(server['recoveryInstanceID'])
    
    return recovery_instance_ids

# 5. Terminate drill (if drill mode)
def terminate_drill_instances(recovery_instance_ids: List[str]):
    response = drs_client.terminate_recovery_instances(
        recoveryInstanceIDs=recovery_instance_ids
    )
    
    job_id = response['job']['jobID']
    return job_id
```

### Wave-Based Recovery Pattern

```python
def execute_wave_based_recovery(waves: List[Dict], is_drill: bool):
    """Execute recovery in waves with dependencies"""
    
    for wave_num, wave in enumerate(waves, 1):
        print(f"Starting Wave {wave_num}: {wave['name']}")
        
        # 1. Validate dependencies completed
        if wave.get('dependsOn'):
            for dep_wave in wave['dependsOn']:
                if not is_wave_complete(dep_wave):
                    raise Exception(f"Dependency wave {dep_wave} not complete")
        
        # 2. Start recovery for all servers in wave
        server_ids = wave['serverIds']
        job_id = start_recovery_job(server_ids, is_drill)
        
        # 3. Wait for wave completion
        job = wait_for_recovery_completion(job_id)
        
        if job['status'] == 'FAILED':
            raise Exception(f"Wave {wave_num} failed: {job.get('error')}")
        
        # 4. Run post-wave validation
        if wave.get('postWaveScript'):
            run_validation_script(wave['postWaveScript'])
        
        print(f"Wave {wave_num} completed successfully")
```

---

## Complete IAM Permissions

### Orchestration Role (Lambda Execution Role)

**CRITICAL**: When Lambda calls `drs:StartRecovery`, DRS uses the **calling role's IAM permissions** to perform EC2 operations, not the DRS service-linked role.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DRSRecoveryOperations",
      "Effect": "Allow",
      "Action": [
        "drs:DescribeSourceServers",
        "drs:DescribeRecoveryInstances",
        "drs:DescribeRecoverySnapshots",
        "drs:DescribeJobs",
        "drs:StartRecovery",
        "drs:TerminateRecoveryInstances",
        "drs:StopReplication",
        "drs:StartReplication",
        "drs:ReverseReplication",
        "drs:DisconnectRecoveryInstance",
        "drs:GetReplicationConfiguration",
        "drs:UpdateReplicationConfiguration",
        "drs:GetLaunchConfiguration",
        "drs:UpdateLaunchConfiguration"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EC2LaunchOperations",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeImages",
        "ec2:DescribeSnapshots",
        "ec2:DescribeVolumes",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeLaunchTemplateVersions",
        "ec2:CreateLaunchTemplate",
        "ec2:CreateLaunchTemplateVersion",
        "ec2:ModifyLaunchTemplate",
        "ec2:DeleteLaunchTemplate",
        "ec2:RunInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:TerminateInstances",
        "ec2:CreateVolume",
        "ec2:AttachVolume",
        "ec2:DetachVolume",
        "ec2:DeleteVolume",
        "ec2:CreateSnapshot",
        "ec2:DeleteSnapshot",
        "ec2:CreateTags",
        "ec2:DeleteTags",
        "ec2:ModifyInstanceAttribute",
        "ec2:ModifyNetworkInterfaceAttribute"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMPassRole",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::*:role/AWSElasticDisasterRecovery*",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "ec2.amazonaws.com"
        }
      }
    },
    {
      "Sid": "DynamoDBOperations",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/protection-groups-*",
        "arn:aws:dynamodb:*:*:table/recovery-plans-*",
        "arn:aws:dynamodb:*:*:table/execution-history-*"
      ]
    },
    {
      "Sid": "StepFunctionsOperations",
      "Effect": "Allow",
      "Action": [
        "states:StartExecution",
        "states:DescribeExecution",
        "states:StopExecution"
      ],
      "Resource": "arn:aws:states:*:*:stateMachine:drs-orchestration-*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/drs-orchestration-*"
    }
  ]
}
```

### DRS Service-Linked Role

**Automatically created by AWS DRS** - `AWSServiceRoleForElasticDisasterRecovery`

This role is used by DRS for:
- Managing staging servers
- Replication infrastructure
- Snapshot management
- Internal DRS operations

**You cannot modify this role** - it's managed by AWS.

### Common Permission Issues

| Error | Missing Permission | Solution |
|-------|-------------------|----------|
| `UnauthorizedOperation: You are not authorized to perform this operation` | `ec2:CreateLaunchTemplate` | Add EC2 launch template permissions |
| `User is not authorized to perform: iam:PassRole` | `iam:PassRole` for DRS role | Add IAM PassRole with condition |
| `Access Denied` on recovery | `drs:StartRecovery` | Add DRS recovery permissions |
| Launch template creation fails | `ec2:CreateLaunchTemplateVersion` | Add launch template version permissions |

---

## Failback Process

### Overview

Failback returns workloads from AWS recovery instances back to the original source environment after a disaster recovery event.

**IMPORTANT**: Failback is only available for **Recovery** mode, not **Drill** mode.

### Failback Prerequisites

1. **Recovery instance must be running** in AWS
2. **Source environment must be available** and ready to receive data
3. **DRS agent must be installed** on recovery instance (if not already present)
4. **Network connectivity** from AWS to source environment
5. **Sufficient bandwidth** for reverse replication

### Failback Phases

#### Phase 1: Initiate Failback

**API Call**: `reverse_replication()`

```python
response = drs_client.reverse_replication(
    recoveryInstanceID='i-1234567890abcdef0'
)

# Response includes job information
job_id = response['job']['jobID']
```

**What Happens**:
- DRS installs agent on recovery instance (if needed)
- Begins reverse replication: AWS → Source Environment
- Creates staging area in source environment
- Starts continuous block-level replication

#### Phase 2: Monitor Reverse Replication

```python
def monitor_reverse_replication(recovery_instance_id: str):
    """Monitor failback replication progress"""
    
    while True:
        response = drs_client.describe_recovery_instances(
            filters={'recoveryInstanceIDs': [recovery_instance_id]}
        )
        
        recovery_instance = response['items'][0]
        failback = recovery_instance.get('failback', {})
        
        state = failback.get('failbackReplicationState')
        # States: NOT_STARTED, INITIATING, BACKLOG, CONTINUOUS, PAUSED, DISCONNECTED
        
        if state == 'CONTINUOUS':
            lag = failback.get('failbackLagDuration')
            print(f"Failback replication continuous, lag: {lag}")
            
            if parse_duration(lag) < 60:  # Less than 60 seconds
                print("Ready for failback finalization")
                break
        
        elif state in ['PAUSED', 'DISCONNECTED']:
            print(f"Failback replication issue: {state}")
            break
        
        time.sleep(60)
```

#### Phase 3: Finalize Failback

**When to Finalize**:
- Reverse replication state is `CONTINUOUS`
- Replication lag is acceptably low (<60 seconds)
- Source environment is ready
- Maintenance window is scheduled

**API Call**: `disconnect_recovery_instance()`

```python
response = drs_client.disconnect_recovery_instance(
    recoveryInstanceID='i-1234567890abcdef0'
)

# This stops reverse replication and marks failback complete
```

**What Happens**:
- Stops reverse replication
- Finalizes data sync to source
- Marks recovery instance for termination
- Source server resumes as primary

#### Phase 4: Cleanup

```python
# Terminate recovery instance
response = drs_client.terminate_recovery_instances(
    recoveryInstanceIDs=['i-1234567890abcdef0']
)

# Verify source server is back to normal replication
response = drs_client.describe_source_servers(
    filters={'sourceServerIDs': ['s-original-server-id']}
)

replication_state = response['items'][0]['dataReplicationInfo']['dataReplicationState']
# Should return to CONTINUOUS (AWS-bound replication)
```

### Failback Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Initiate | 5-15 minutes | Agent installation, reverse replication setup |
| Initial Sync | 1-24 hours | Full data sync (depends on data size and bandwidth) |
| Continuous | Ongoing | Continuous replication until finalization |
| Finalize | 5-15 minutes | Final sync and cutover |
| Cleanup | 5-10 minutes | Terminate AWS resources |

### Failback Best Practices

1. **Test failback in drill mode first** (if possible with test data)
2. **Monitor replication lag** before finalizing
3. **Schedule maintenance window** for finalization
4. **Verify source environment health** before initiating
5. **Have rollback plan** in case of issues
6. **Document network requirements** (ports, bandwidth)
7. **Test application functionality** after failback

---

## Agent Installation

### DRS Agent Overview

The AWS DRS agent is required on source servers to enable replication to AWS.

**Agent Functions**:
- Captures block-level changes
- Compresses and encrypts data
- Transmits to AWS staging area
- Monitors replication health

### Installation Methods

#### Method 1: AWS Console (Recommended for Testing)

1. Navigate to AWS DRS console
2. Click "Add servers"
3. Download agent installer for your OS
4. Run installer on source server

#### Method 2: Command Line (Linux)

```bash
# Download installer
wget -O ./aws-replication-installer-init.py https://aws-elastic-disaster-recovery-<region>.s3.<region>.amazonaws.com/latest/linux/aws-replication-installer-init.py

# Run installer
sudo python3 aws-replication-installer-init.py \
  --region us-east-1 \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \  # pragma: allowlist secret
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \  # pragma: allowlist secret
  --no-prompt
```

#### Method 3: Command Line (Windows)

```powershell
# Download installer
Invoke-WebRequest -Uri "https://aws-elastic-disaster-recovery-<region>.s3.<region>.amazonaws.com/latest/windows/AwsReplicationWindowsInstaller.exe" -OutFile "AwsReplicationWindowsInstaller.exe"

# Run installer
.\AwsReplicationWindowsInstaller.exe `
  --region us-east-1 `
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE `  # pragma: allowlist secret
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY `  # pragma: allowlist secret
  --no-prompt
```

### Agent Installation via API

**Create IAM User for Agent**:

```python
# Create IAM user for DRS agent
iam_client = boto3.client('iam')

response = iam_client.create_user(
    UserName='drs-agent-user'
)

# Attach DRS agent policy
policy_arn = 'arn:aws:iam::aws:policy/AWSElasticDisasterRecoveryAgentInstallationPolicy'
iam_client.attach_user_policy(
    UserName='drs-agent-user',
    PolicyArn=policy_arn
)

# Create access keys
keys_response = iam_client.create_access_key(
    UserName='drs-agent-user'
)

access_key_id = keys_response['AccessKey']['AccessKeyId']
secret_access_key = keys_response['AccessKey']['SecretAccessKey']
```

**Deploy Agent via SSM** (for EC2 instances):

```python
ssm_client = boto3.client('ssm')

# Send command to install agent
response = ssm_client.send_command(
    InstanceIds=['i-source-instance-id'],
    DocumentName='AWS-RunShellScript',
    Parameters={
        'commands': [
            'wget -O /tmp/aws-replication-installer-init.py https://aws-elastic-disaster-recovery-us-east-1.s3.us-east-1.amazonaws.com/latest/linux/aws-replication-installer-init.py',
            f'sudo python3 /tmp/aws-replication-installer-init.py --region us-east-1 --aws-access-key-id {access_key_id} --aws-secret-access-key {secret_access_key} --no-prompt'
        ]
    }
)

command_id = response['Command']['CommandId']
```

### Agent Configuration

**Configuration File Location**:
- Linux: `/etc/aws-replication/agent_config.json`
- Windows: `C:\Program Files\AWS Replication Agent\agent_config.json`

**Key Configuration Options**:

```json
{
  "region": "us-east-1",
  "stagingAreaSubnetId": "subnet-12345678",
  "replicationServerInstanceType": "t3.small",
  "ebsEncryption": "DEFAULT",
  "dataRoutingPolicy": "PRIVATE_IP",
  "defaultLargeStagingDiskType": "GP3",
  "bandwidthThrottling": 0,
  "useDedicatedReplicationServer": false
}
```

### Agent Monitoring

```python
def check_agent_status(source_server_id: str):
    """Check DRS agent status"""
    
    response = drs_client.describe_source_servers(
        filters={'sourceServerIDs': [source_server_id]}
    )
    
    server = response['items'][0]
    
    # Agent status
    agent_version = server.get('sourceProperties', {}).get('agentVersion')
    last_seen = server.get('sourceProperties', {}).get('lastSeenByServiceDateTime')
    
    # Replication status
    replication_info = server['dataReplicationInfo']
    state = replication_info['dataReplicationState']
    lag = replication_info.get('lagDuration')
    
    print(f"Agent Version: {agent_version}")
    print(f"Last Seen: {last_seen}")
    print(f"Replication State: {state}")
    print(f"Lag: {lag}")
    
    # Disk replication status
    for disk in replication_info.get('replicatedDisks', []):
        print(f"Disk {disk['deviceName']}: {disk['replicationStatus']}")
```

### Agent Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Agent not connecting | Network/firewall | Open TCP 443, 1500 outbound |
| High replication lag | Bandwidth throttling | Adjust `bandwidthThrottling` setting |
| Agent offline | Service stopped | Restart agent service |
| Disk not replicating | Unsupported filesystem | Check DRS supported filesystems |

**Agent Service Commands**:

Linux:
```bash
# Check status
sudo systemctl status aws-replication-agent

# Restart
sudo systemctl restart aws-replication-agent

# View logs
sudo journalctl -u aws-replication-agent -f
```

Windows:
```powershell
# Check status
Get-Service "AWS Replication Agent"

# Restart
Restart-Service "AWS Replication Agent"

# View logs
Get-EventLog -LogName Application -Source "AWS Replication Agent" -Newest 50
```

---

## Troubleshooting

### Recovery Issues

#### Issue: Recovery Job Fails with "UnauthorizedOperation"

**Cause**: Missing EC2 permissions on orchestration role

**Solution**:
```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:CreateLaunchTemplate",
    "ec2:CreateLaunchTemplateVersion",
    "ec2:RunInstances",
    "ec2:CreateVolume",
    "ec2:AttachVolume"
  ],
  "Resource": "*"
}
```

#### Issue: Recovery Instance Stuck in "Pending"

**Cause**: EC2 capacity issues or subnet configuration

**Solution**:
1. Check EC2 capacity in target AZ
2. Verify subnet has available IPs
3. Check security group rules
4. Review launch template configuration

#### Issue: Conversion Phase Skipped

**Cause**: Tags parameter passed to `start_recovery()`

**Solution**: Remove `tags` parameter from API call

### Failback Issues

#### Issue: Reverse Replication Not Starting

**Cause**: Agent not installed on recovery instance

**Solution**:
```python
# DRS automatically installs agent during reverse_replication()
# If it fails, check:
# 1. Recovery instance has internet access
# 2. Security groups allow outbound HTTPS
# 3. IAM instance profile has DRS permissions
```

#### Issue: High Failback Lag

**Cause**: Insufficient bandwidth or high change rate

**Solution**:
1. Increase bandwidth allocation
2. Reduce application write activity
3. Schedule during low-traffic window
4. Consider Direct Connect for large datasets

### Agent Issues

#### Issue: Agent Installation Fails

**Cause**: Missing dependencies or permissions

**Solution**:
```bash
# Linux - Install dependencies
sudo yum install -y python3 python3-pip

# Verify IAM credentials
aws sts get-caller-identity

# Check agent logs
sudo cat /var/log/aws-replication-agent-install.log
```

#### Issue: Replication Lag Increasing

**Cause**: High change rate or bandwidth constraints

**Solution**:
1. Check network bandwidth utilization
2. Adjust bandwidth throttling settings
3. Verify staging server size is adequate
4. Consider using dedicated replication server

---

## Reference Links

- [AWS DRS Documentation](https://docs.aws.amazon.com/drs/)
- [DRS API Reference](https://docs.aws.amazon.com/drs/latest/APIReference/)
- [DRS IAM Permissions](https://docs.aws.amazon.com/drs/latest/userguide/security-iam.html)
- [Project IAM Analysis](../reference/DRS_COMPLETE_IAM_ANALYSIS.md)
- [Project API Reference](AWS_DRS_API_REFERENCE.md)
- [Deployment Guide](DEPLOYMENT_AND_OPERATIONS_GUIDE.md)

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Maintained By**: AWS DRS Orchestration Project
