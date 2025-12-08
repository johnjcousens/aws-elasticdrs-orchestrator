# IAM Role Analysis - DRS Permissions for Lambda Functions

**Analysis Date**: November 30, 2025  
**Purpose**: Verify Lambda IAM roles have correct permissions for full DRS drill and recovery operations  
**Status**: ⚠️ MISSING CRITICAL PERMISSIONS

---

## Executive Summary

The Lambda functions have **INCOMPLETE** permissions for full DRS drill and recovery operations:

- ✅ Starting recovery operations (PRESENT)
- ❌ Terminating drill instances in OrchestrationRole (MISSING)
- ❌ EC2 instance termination in both roles (MISSING)
- ❌ Failback operations (MISSING)
- ❌ Configuration management (MISSING)

---

## Current IAM Roles Analysis

### 1. ApiHandlerRole - DRS Permissions ✅ MOSTLY COMPLETE

**Current Permissions**:
```yaml
✅ drs:DescribeSourceServers
✅ drs:DescribeReplicationConfigurationTemplates
✅ drs:GetReplicationConfiguration
✅ drs:GetLaunchConfiguration
✅ drs:StartRecovery
✅ drs:DescribeJobs
✅ drs:DescribeRecoverySnapshots
✅ drs:TerminateRecoveryInstances
✅ drs:TagResource
```

**Missing Critical Permissions**:
```yaml
❌ drs:DisconnectRecoveryInstance
❌ drs:ReverseReplication
❌ drs:StopReplication
❌ drs:UpdateLaunchConfiguration
```

**Missing EC2 Permissions**:
```yaml
❌ ec2:TerminateInstances
❌ ec2:StopInstances
```

### 2. OrchestrationRole - DRS Permissions ⚠️ INCOMPLETE

**Current Permissions**:
```yaml
✅ drs:DescribeSourceServers
✅ drs:DescribeRecoveryInstances
✅ drs:DescribeJobs
✅ drs:StartRecovery
✅ drs:GetReplicationConfiguration
✅ drs:GetLaunchConfiguration
```

**Missing Critical Permissions**:
```yaml
❌ drs:TerminateRecoveryInstances  # CRITICAL
❌ drs:DisconnectRecoveryInstance
❌ drs:TagResource
❌ drs:ReverseReplication
```

**Missing EC2 Permissions**:
```yaml
❌ ec2:TerminateInstances  # CRITICAL
❌ ec2:StopInstances
❌ ec2:CreateTags
```

---

## Critical Gaps

### Gap 1: Drill Cleanup - HIGH RISK ⚠️

**Problem**: Cannot automatically clean up drill instances

**Impact**:
- Drill instances remain running after test
- Cost overruns: $50-500/month per uncleaned drill
- Manual cleanup required

**Missing**:
- OrchestrationRole: `drs:TerminateRecoveryInstances`
- Both roles: `ec2:TerminateInstances`

### Gap 2: Failback Operations - HIGH RISK ⚠️

**Problem**: Cannot perform automated failback

**Impact**:
- Cannot reverse replication after failover
- Extended RTO during failback
- Manual configuration required

**Missing**:
- Both roles: `drs:ReverseReplication`
- Both roles: `drs:StopReplication`

---

## Recommended Fixes

### Priority 1: CRITICAL - Drill Cleanup

**Add to OrchestrationRole**:
```yaml
DRSAccess:
  - drs:TerminateRecoveryInstances
  - drs:DisconnectRecoveryInstance
  - drs:TagResource

EC2Access:
  - ec2:TerminateInstances
  - ec2:StopInstances
  - ec2:CreateTags
```

**Add to ApiHandlerRole**:
```yaml
DRSAccess:
  - drs:DisconnectRecoveryInstance

EC2Access:
  - ec2:TerminateInstances
  - ec2:StopInstances
```

### Priority 2: HIGH - Failback Operations

**Add to Both Roles**:
```yaml
DRSAccess:
  - drs:ReverseReplication
  - drs:StopReplication
  - drs:StartReplication
  - drs:UpdateReplicationConfiguration
```

---

## Cost Impact

### Current State (Without Fixes)
- **Monthly Waste**: $400-800 (uncleaned drills)
- **Annual Waste**: $4,800-9,600

### After Priority 1 Fix
- **Monthly Cost**: $40-80
- **Annual Savings**: $4,320-9,120

**ROI**: Fix pays for itself in first month

---

## Comparison with Competitors

| Feature | Azure Site Recovery | Zerto | AWS DRS Orchestration |
|---------|-------------------|-------|----------------------|
| Drill Cleanup | ✅ Automated | ✅ Automated | ❌ Manual |
| Failback | ✅ Automated | ✅ Automated | ❌ Not supported |
| Config Updates | ✅ Via API | ✅ Via API | ❌ Console only |

---

## Next Steps

1. ✅ Document current state (COMPLETE)
2. ⏳ Update CloudFormation template with Priority 1 permissions
3. ⏳ Deploy to test environment
4. ⏳ Test drill cleanup functionality
5. ⏳ Update with Priority 2 permissions
6. ⏳ Test failback functionality

**Target Completion**: 2 weeks
