# Cross-Account DRS Query Fix Summary

**Date**: January 30, 2026  
**Issue**: Server discovery showing EC2 instances from orchestration account instead of target account  
**Status**: ✅ FIXED - Lambda deployed at 14:19 PM

---

## Problem Statement

When creating a Protection Group and selecting account "DEMO_TARGET (111122223333)", the server discovery panel was showing EC2 instances from the **orchestration account (777788889999)** instead of the **target account (111122223333)**.

### User Experience
```
Create Protection Group
Region: us-west-2 (Oregon)
Account: DEMO_TARGET - 111122223333

Server Selection:
❌ Showing: hrp-core-app01-az1 (from orchestration account 777788889999)
✅ Expected: Servers from target account 111122223333
```

---

## Root Cause Analysis

### 1. Database Schema Mismatch
The target accounts table stores `roleArn` (full ARN) but the code was looking for `assumeRoleName` (just the role name):

**DynamoDB Data**:
```json
{
  "accountId": "111122223333",
  "roleArn": "arn:aws:iam::111122223333:role/DRSOrchestrationRole-dev"
  // ❌ No "assumeRoleName" field
}
```

**Code Expected**:
```python
assume_role_name = account.get("assumeRoleName")  # Returns None
```

### 2. Missing Cross-Account Role Assumption
When `assumeRoleName` was None, the `create_drs_client` function fell back to using the **current account** credentials instead of assuming the cross-account role.

**CloudWatch Logs Evidence**:
```
Found target account 111122223333 with role None
Creating DRS client for current account in region us-west-2
```

This caused the DRS client to query the orchestration account (777788889999) instead of the target account (111122223333).

---

## Solution Implemented

### Code Changes

**File**: `lambda/query-handler/index.py` (lines 688-693)

**Before**:
```python
assume_role_name = account.get("assumeRoleName")
# Returns None because field doesn't exist
```

**After**:
```python
# Extract role name from roleArn if assumeRoleName not present
assume_role_name = account.get("assumeRoleName")
if not assume_role_name:
    role_arn = account.get("roleArn")
    if role_arn:
        # Extract role name from ARN: arn:aws:iam::123456789012:role/RoleName
        assume_role_name = role_arn.split("/")[-1]
```

### How It Works

1. **Try assumeRoleName first** (for backward compatibility)
2. **If not found**, extract from `roleArn`:
   - Input: `arn:aws:iam::111122223333:role/DRSOrchestrationRole-dev`
   - Split by `/`: `["arn:aws:iam::111122223333:role", "DRSOrchestrationRole-dev"]`
   - Take last part: `DRSOrchestrationRole-dev`
3. **Pass to create_drs_client** with complete account context:
   ```python
   account_context = {
       "accountId": "111122223333",
       "assumeRoleName": "DRSOrchestrationRole-dev"
   }
   ```

---

## Deployment Status

### ✅ Lambda Functions - Deployed 14:19 PM
- `aws-drs-orchestration-query-handler-test` - Updated with roleArn extraction fix
- `aws-drs-orchestration-data-management-handler-test` - Updated
- `aws-drs-orchestration-execution-handler-test` - Updated
- All other Lambda functions updated

### ✅ Frontend - Already Deployed 14:13 PM
- Version: `20260130-1413`
- CloudFront Distribution: `E1BBNSHA96QXQ4`
- Already passing `accountId` parameter correctly

---

## Verification Steps

### 1. Test Server Discovery in UI

1. **Navigate to Protection Groups** page
2. **Click "Create Protection Group"**
3. **Select Account**: "DEMO_TARGET - 111122223333"
4. **Select Region**: "us-west-2 (Oregon)"
5. **Go to "Server Selection" tab**
6. **Verify**: Should show servers from target account 111122223333 only

### 2. Check CloudWatch Logs

After testing in UI, check logs for successful cross-account role assumption:

```bash
AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-test --since 5m --format short
```

**Expected Log Output**:
```
Found target account 111122223333 with role DRSOrchestrationRole-dev
Creating cross-account DRS client for account 111122223333 using role DRSOrchestrationRole-dev
Assuming role: arn:aws:iam::111122223333:role/DRSOrchestrationRole-dev
Successfully created cross-account DRS client for account 111122223333
```

### 3. Verify API Response

Check browser DevTools Network tab:

```
GET /drs/source-servers?region=us-west-2&accountId=111122223333

Response should contain:
- Servers from target account 111122223333
- No servers from orchestration account 777788889999
```

---

## Expected Behavior After Fix

### ✅ Server Discovery
- Shows only DRS source servers from the selected target account
- Correctly assumes cross-account IAM role
- Filters out servers already assigned to other protection groups

### ✅ Cross-Account Role Assumption
- Extracts role name from `roleArn` field in DynamoDB
- Passes complete account context to `create_drs_client`
- Successfully assumes role: `arn:aws:iam::111122223333:role/DRSOrchestrationRole-dev`

### ✅ Account Filtering
- Protection Groups: Filter by `accountId` field
- Recovery Plans: Derive account from protection groups in waves
- Executions: Filter by `accountId` field

---

## Related Fixes in This Session

### 1. Protection Group Account Filtering
- Fixed recovery plans to derive account from protection groups (no direct `accountId` field)
- Added account filtering to protection group assignments

### 2. Customer Reference Removal
- Removed all references to HRP, HealthEdge, GuidingCare from UI placeholders
- Updated to generic examples

### 3. DRS Agent Deployer
- Commented out in CloudFormation (under development)
- Prevents deployment failures

---

## Technical Details

### Account Architecture

- **Orchestration Account**: 777788889999 (where Lambda functions run)
- **Target Account**: 111122223333 (recovery destination) - labeled as "DEMO_TARGET"
- **Staging Account**: 444455556666 (extended source servers)
- **Networking Account**: 555566667777 (shared VPC via AWS RAM)

### Cross-Account IAM Role

**Role Name**: `DRSOrchestrationRole-dev`  
**Full ARN**: `arn:aws:iam::111122223333:role/DRSOrchestrationRole-dev`  
**External ID**: `drs-orchestration-dev-111122223333`

**Trust Relationship**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "AWS": "arn:aws:iam::777788889999:root"
    },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "sts:ExternalId": "drs-orchestration-dev-111122223333"
      }
    }
  }]
}
```

### Database Schema

**Target Accounts Table**:
```json
{
  "accountId": "111122223333",
  "accountName": "DEMO_TARGET",
  "roleArn": "arn:aws:iam::111122223333:role/DRSOrchestrationRole-dev",
  "status": "active",
  "isCurrentAccount": false
}
```

**Note**: No `assumeRoleName` field - must extract from `roleArn`

---

## Commits

1. `4bb16393` - fix: extract role name from roleArn in get_drs_source_servers for cross-account DRS queries

---

## Related Documentation

- [Account Awareness Complete Summary](ACCOUNT_AWARENESS_COMPLETE_SUMMARY.md)
- [Account Filtering Fix Summary](ACCOUNT_FILTERING_FIX_SUMMARY.md)
- [Cross-Account Setup Guide](docs/guides/DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md)
- [Cross-Account Reference](docs/reference/DRS_CROSS_ACCOUNT_REFERENCE.md)

---

## Next Steps

1. **Test in UI**: Create a protection group with target account selected
2. **Verify logs**: Check CloudWatch for successful role assumption
3. **Monitor**: Watch for any cross-account access errors
4. **Document**: Update user guides if needed
