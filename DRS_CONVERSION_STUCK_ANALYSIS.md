# DRS Conversion Phase Stuck - Root Cause Analysis

**Date**: December 8, 2025, 4:43 AM  
**Job ID**: `drsjob-3be07047c5f2f5f48`  
**Issue**: Recovery job stuck in CONVERSION phase, no recovery instances created

## Timeline

```
04:43:28 - JOB_START
04:43:28 - SNAPSHOT_START (s-3d75cdc0d9a28a725)
04:43:28 - SNAPSHOT_END (s-3d75cdc0d9a28a725)
04:44:25 - CONVERSION_START (s-3d75cdc0d9a28a725)
04:44:28 - Conversion Server launched (i-0fdd67f29bb1a793b)
[STUCK HERE - No CONVERSION_END event]
```

## Current State

### Job Status
- **Status**: STARTED
- **Type**: LAUNCH
- **Participating Servers**: 1 (s-3d75cdc0d9a28a725)
- **Launch Status**: PENDING

### Conversion Server
- **Instance ID**: i-0fdd67f29bb1a793b
- **State**: running
- **Type**: m4.large
- **IAM Role**: AWSElasticDisasterRecoveryConversionServerRole
- **Launch Time**: 04:44:28

### Recovery Instances
- **Count**: 0
- **Status**: NONE CREATED

## Root Cause

The job is **stuck in the CONVERSION phase**. The conversion server was launched but:

1. ✅ Snapshot created successfully
2. ✅ Conversion server launched
3. ❌ Conversion NOT completing
4. ❌ No recovery instance created

## Why This Matters

**The `ec2:StartInstances` permission fix was a red herring.**

The real issue is:
- DRS service creates the conversion server
- Conversion server should convert the snapshot to an AMI
- Then DRS should launch the recovery instance
- **But conversion is failing/hanging**

## Possible Causes

### 1. Conversion Server Can't Access Snapshots
- IAM role permissions issue
- KMS key access for encrypted snapshots
- Cross-region snapshot access

### 2. Conversion Server Software Issue
- DRS agent on conversion server failing
- Network connectivity issues
- Disk space or resource constraints

### 3. Source Server Configuration
- Incompatible OS or disk configuration
- Missing drivers or boot configuration
- Encryption settings mismatch

### 4. Launch Template Issues
- Invalid launch template configuration
- Missing required parameters
- Network/subnet configuration problems

## Investigation Steps

### Check Conversion Server IAM Role
```bash
aws iam get-role --role-name AWSElasticDisasterRecoveryConversionServerRole
aws iam list-attached-role-policies --role-name AWSElasticDisasterRecoveryConversionServerRole
```

### Check Conversion Server Logs
```bash
# Get console output
aws ec2 get-console-output --instance-id i-0fdd67f29bb1a793b --region us-east-1

# Check CloudWatch Logs if available
aws logs describe-log-groups --log-group-name-prefix /aws/drs --region us-east-1
```

### Check Source Server Configuration
```bash
aws drs describe-source-servers --region us-east-1 \
  --filters sourceServerIDs=s-3d75cdc0d9a28a725
```

### Check Launch Configuration
```bash
aws drs get-launch-configuration --source-server-id s-3d75cdc0d9a28a725 --region us-east-1
```

## Hypothesis

**The conversion phase requires specific permissions or configurations that are missing.**

Possible issues:
1. Conversion server can't create AMI from snapshot
2. Conversion server can't access KMS keys for encrypted volumes
3. Launch template has invalid configuration preventing instance launch
4. Network configuration prevents conversion server from communicating with DRS service

## Next Steps

1. **Terminate stuck job**:
```bash
aws drs terminate-recovery-instances --region us-east-1 \
  --recovery-instance-ids $(aws drs describe-recovery-instances --region us-east-1 --query 'items[*].recoveryInstanceID' --output text)
```

2. **Check conversion server console output** for errors

3. **Review source server launch configuration** for issues

4. **Test with simplified launch configuration** (no custom settings)

5. **Check if this is a known DRS service issue** (AWS Support)

## Comparison with Working Drill

**Previous successful drill** (drsjob-3949c80becf56a075):
- Both servers launched successfully
- Conversion completed
- Recovery instances created

**What changed?**
- Need to compare launch configurations
- Need to compare source server states
- Need to check if DRS service had updates

## Conclusion

The `ec2:StartInstances` permission was NOT the root cause. The actual issue is:

**DRS conversion phase is failing/hanging, preventing recovery instances from being created.**

This requires deeper investigation into:
- Conversion server IAM permissions
- Source server configuration
- Launch template settings
- DRS service health

The fix in commit 242b696c may have been coincidental timing with a DRS service issue resolution, or there's a more complex interaction we haven't identified yet.
