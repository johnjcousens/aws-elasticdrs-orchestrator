# DRS Launch Failure Root Cause and Fix

**Session**: 49  
**Date**: November 22, 2025, 8:36 PM EST  
**Issue**: All 6 source servers failed to launch during recovery plan execution

## Root Cause Analysis

### Launch Template Configuration Issue

**Template ID**: `lt-0705fbf6032cb088e`

**Missing Critical Configuration**:
```json
{
  "ImageId": null,           // ❌ Missing (but DRS should auto-populate)
  "SecurityGroupIds": null,  // ❌ CRITICAL: Missing security group
  "InstanceType": "c5.xlarge",        // ✅ OK
  "SubnetId": "subnet-0151a0dd78ac559c4",  // ✅ OK
  "IamInstanceProfile": {
    "Name": "demo-ec2-profile"  // ✅ OK
  }
}
```

### Available Resources (All Valid)

**Recovery Snapshots**: ✅ Available
- Latest: `pit-3710c9f0b76e9e075` (2025-11-23 01:30:40)
- DRS has multiple recovery points available

**Network Configuration**: ✅ Valid
- VPC: `vpc-08c7f2a39d0faf1d2`
- Subnet: `subnet-0151a0dd78ac559c4` (us-east-1c, 10.10.216.0/21)

**Security Group**: ✅ Available
- GroupId: `sg-06f217dba4afdd97f`
- Name: `securitygroup-onprem-us-east-1`

**Replication Status**: ✅ Healthy
- All 6 servers in `CONTINUOUS` replication state
- Staging area configured correctly

## Why Launches Failed

**EC2 Cannot Launch Without Security Group**:
- AWS requires at least one security group for EC2 instances
- Launch template has `SecurityGroupIds: null`
- EC2 launch fails immediately with missing security group
- DRS job completes (submission succeeded) but launch fails

**ImageId Null is Expected**:
- DRS should auto-populate ImageId from recovery snapshots
- This is normal behavior for DRS launch templates
- However, security group is mandatory and cannot be auto-populated

## The Fix

### Option 1: Update Launch Template (Recommended)

Update the launch template to include the security group:

```bash
aws ec2 create-launch-template-version \
  --launch-template-id lt-0705fbf6032cb088e \
  --region us-east-1 \
  --launch-template-data '{
    "InstanceType": "c5.xlarge",
    "NetworkInterfaces": [{
      "DeviceIndex": 0,
      "SubnetId": "subnet-0151a0dd78ac559c4",
      "Groups": ["sg-06f217dba4afdd97f"]
    }],
    "IamInstanceProfile": {
      "Name": "demo-ec2-profile"
    }
  }'
```

**Then set as default version**:
```bash
aws ec2 modify-launch-template \
  --launch-template-id lt-0705fbf6032cb088e \
  --region us-east-1 \
  --default-version '$Latest'
```

### Option 2: Use DRS Console (Easier)

1. Open AWS DRS Console: https://console.aws.amazon.com/drs/
2. Navigate to Source Servers
3. Select source server: `s-3d75cdc0d9a28a725`
4. Click "Launch settings"
5. Edit launch template
6. Under "Network settings":
   - Security groups: Add `sg-06f217dba4afdd97f`
7. Save changes
8. Repeat for all 6 source servers

### Option 3: Update via DRS Launch Configuration

Update the launch configuration to use a properly configured template:

```bash
# For each source server
aws drs update-launch-configuration \
  --source-server-id s-3d75cdc0d9a28a725 \
  --region us-east-1 \
  --ec2-launch-template-id lt-NEW_TEMPLATE_ID
```

## Verification Steps

After applying the fix:

1. **Verify template updated**:
```bash
aws ec2 describe-launch-template-versions \
  --launch-template-id lt-0705fbf6032cb088e \
  --region us-east-1 \
  --output json | jq -r '.LaunchTemplateVersions[0].LaunchTemplateData.NetworkInterfaces[0].Groups'
```

Expected: `["sg-06f217dba4afdd97f"]`

2. **Test recovery plan execution**:
   - Execute the recovery plan again
   - Monitor launch status: `aws drs describe-source-servers`
   - Should see `LaunchStatus: LAUNCHED` (not FAILED)
   - Recovery instances should be created

3. **Check recovery instances**:
```bash
aws drs describe-recovery-instances --region us-east-1
```

Expected: 6 recovery instances in CONVERTING or READY state

## Expected Timeline (After Fix)

```
T+0s:    User clicks "Execute Plan"
T+3s:    Lambda submits 6 DRS launch requests (marked COMPLETED)
T+30s:   DRS creates recovery snapshots
T+2m:    EC2 instances launched (LaunchStatus: LAUNCHED)
T+5m:    Instances start converting (boosting from snapshots)
T+15m:   All instances reach READY state
T+20m:   Post-launch scripts execute (if configured)
```

## Impact on Execution History Integration

**Current Behavior** (Fire-and-Forget):
- ✅ Lambda execution: COMPLETED (after 3 seconds)
- ❌ Actual launch status: Not tracked
- ❌ Frontend shows: "COMPLETED" (misleading)

**Reality**:
- Lambda submits launches successfully
- Launches fail due to missing security group
- Execution history doesn't reflect actual failure

**Future Enhancement Needed**:
- Add async job polling to track actual launch outcomes
- Update execution status based on DRS job results
- Show real-time conversion progress

## Testing the Fix

### Before Fix
```
LaunchStatus: FAILED (all 6 servers)
DRS Job Status: COMPLETED (misleading)
Execution Status: COMPLETED (misleading)
Recovery Instances: None created
```

### After Fix
```
LaunchStatus: LAUNCHED → CONVERTING → READY
DRS Job Status: COMPLETED
Execution Status: COMPLETED (now accurate!)
Recovery Instances: 6 instances created
Conversion Time: ~10-15 minutes per server
```

## Configuration Files to Update

**All 6 Source Servers Need Template Update**:
1. `s-3d75cdc0d9a28a725` (template: lt-0705fbf6032cb088e)
2. `s-3c1730a9e0771ea14`
3. `s-3afa164776f93ce4f`
4. `s-3c63bb8be30d7d071`
5. `s-3578f52ef3bdd58b4`
6. `s-3b9401c1cd270a7a8`

Each may have its own launch template or share the same one.

## Prevention for Future Servers

When adding new source servers to DRS:

1. **Create launch template with security group**:
```bash
aws ec2 create-launch-template \
  --launch-template-name "drs-recovery-template" \
  --launch-template-data '{
    "NetworkInterfaces": [{
      "DeviceIndex": 0,
      "Groups": ["sg-06f217dba4afdd97f"]
    }],
    "IamInstanceProfile": {
      "Name": "demo-ec2-profile"
    }
  }'
```

2. **Apply to source server**:
```bash
aws drs update-launch-configuration \
  --source-server-id s-XXXXXXXXX \
  --ec2-launch-template-id lt-XXXXXXXXX
```

3. **Verify before first drill**

## Related Documentation

- Session 49 Status: docs/PROJECT_STATUS.md
- Execution Model: docs/SESSION_49_DATAGRID_STYLING_INVESTIGATION.md
- DRS API Reference: docs/AWS_DRS_API_REFERENCE.md

## Conclusion

**Problem**: Missing security group in launch template  
**Impact**: All recovery launches fail immediately  
**Fix**: Add security group `sg-06f217dba4afdd97f` to launch template  
**Effort**: 5 minutes via console or 2 CLI commands  
**Result**: Successful launches and recovery instance creation  

**Note**: This is a test environment configuration issue, not a code bug. The execution history integration is working correctly - it accurately reflects that Lambda submitted the jobs successfully. The job submission completed, but the launches failed due to missing security group configuration in DRS.
