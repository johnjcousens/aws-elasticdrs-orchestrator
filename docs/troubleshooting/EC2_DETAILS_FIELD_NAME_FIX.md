# EC2 Instance Details Field Name Fix

## Issue
After wave completion, the server table was missing EC2 instance details:
- Instance ID showed as "—"
- Instance Type showed as "—"  
- Private IP showed as "—"

Only Launch Time was displayed correctly.

## Root Cause
**Field name mismatch between Lambda backend and frontend TypeScript interface:**

- **Lambda stored**: `instanceId`, `instanceType`, `privateIp`
- **Frontend expected**: `recoveredInstanceId`, `instanceType`, `privateIp`

The frontend WaveProgress component (line 437) was looking for `server.recoveredInstanceId`, but the Lambda orchestration function was storing the EC2 instance ID as `instanceId`.

## Code Analysis

### Lambda Backend (orchestration-stepfunctions/index.py)
```python
# Lines 1015-1035: EC2 details were being fetched correctly
ri_response = drs_client.describe_recovery_instances(...)
for ri in ri_response.get("items", []):
    ss["instanceId"] = ri.get("ec2InstanceID", "")  # ❌ Wrong field name

# Lines 1040-1065: EC2 describe_instances was working
ec2_response = ec2_client.describe_instances(InstanceIds=ec2_ids)
ss["privateIp"] = instance_details[ec2_id].get("privateIp", "")
ss["instanceType"] = instance_details[ec2_id].get("instanceType", "")
```

### Frontend TypeScript Interface (types/index.ts)
```typescript
export interface ServerExecution {
  serverId: string;
  serverName?: string;
  hostname?: string;
  recoveredInstanceId?: string;  // ✅ Expected field name
  instanceType?: string;
  privateIp?: string;
  launchTime?: string | number;
  // ...
}
```

### Frontend Component (WaveProgress.tsx)
```typescript
// Line 437: Looking for recoveredInstanceId
const instanceId = server.recoveredInstanceId;  // ✅ Correct expectation
```

## Solution
Changed Lambda to use `recoveredInstanceId` to match the frontend TypeScript interface.

### Changes Made (3 locations in orchestration-stepfunctions/index.py)

**1. Server status initialization (line ~865)**
```python
# Before:
"instanceId": existing.get("instanceId", ""),

# After:
"recoveredInstanceId": existing.get("recoveredInstanceId", ""),
```

**2. Recovery instance details fetch (line ~1023)**
```python
# Before:
ss["instanceId"] = ri.get("ec2InstanceID", "")

# After:
ss["recoveredInstanceId"] = ri.get("ec2InstanceID", "")
```

**3. EC2 details fetch (line ~1040)**
```python
# Before:
ec2_ids = [ss.get("instanceId") for ss in server_statuses if ss.get("instanceId")]
ec2_id = ss.get("instanceId")

# After:
ec2_ids = [ss.get("recoveredInstanceId") for ss in server_statuses if ss.get("recoveredInstanceId")]
ec2_id = ss.get("recoveredInstanceId")
```

**4. State-level recovery instance IDs (line ~1035)**
```python
# Before:
ec2_id = ss.get("instanceId")

# After:
ec2_id = ss.get("recoveredInstanceId")
```

## Verification
After deployment, the server table should display:
- ✅ Instance ID with AWS console link
- ✅ Instance Type (e.g., t3.medium)
- ✅ Private IP address
- ✅ Launch Time

## Related Issues Fixed
This fix also resolves:
1. SNS notification IAM policy (using `!Sub` instead of `!Ref`)
2. Completed wave display showing "Wave 3 of 3" instead of "Wave 1 of 3"

## Deployment
- **Commit**: `30a31d19` - EC2 instance details field name fix
- **Commit**: `1f63816d` - SNS notification and wave display fixes
- **Deployment**: GitHub Actions pipeline (main branch)
- **Status**: Deployed to test environment

## Testing
After deployment completes:
1. Start a new recovery execution
2. Wait for wave to complete
3. Verify server table shows all EC2 details
4. Confirm Instance ID links to AWS console
5. Verify Instance Type and Private IP are populated
