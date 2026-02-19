# CamelCase Validation Tests

## Overview

Tests to ensure camelCase validation properly distinguishes between:
1. **Internal application fields** (should be camelCase)
2. **AWS API response fields** (legitimately PascalCase)
3. **AWS API request parameters** (legitimately PascalCase)

## The Challenge

AWS APIs return PascalCase fields by default, but our internal application uses camelCase for consistency. The validation must:
- ✅ **Allow** AWS API PascalCase (e.g., `PrivateIpAddress`, `InstanceId`)
- ❌ **Block** internal PascalCase (e.g., `GroupId` should be `groupId`)

## Test File

**test_camelcase_validation.py** - 17 tests covering:

### 1. AWS API PascalCase Exceptions (4 tests)
Tests that AWS service APIs legitimately return PascalCase:

**EC2 API Fields:**
- `InstanceId`, `InstanceIds`, `InstanceType`
- `PrivateIpAddress`, `PublicIpAddress`
- `PrivateDnsName`, `PublicDnsName`
- `SecurityGroups`, `SubnetId`, `VpcId`
- `ImageId`, `KeyName`, `LaunchTime`
- `State`, `Tags`, `Reservations`, `Instances`

**DRS API Fields:**
- `sourceServerID` (mixed case)
- `recoveryInstanceID` (mixed case)
- `participatingServers`
- `postLaunchActionsStatus`
- `sourceProperties`, `identificationHints`
- `launchConfiguration`, `replicationConfiguration`

**IAM API Fields:**
- `InstanceProfiles`, `InstanceProfile`
- `InstanceProfileName`, `Arn`
- `RoleName`, `PolicyName`

**CloudWatch API Fields:**
- `MetricName`, `Namespace`, `Dimensions`
- `Timestamp`, `Value`, `Unit`

### 2. Internal Fields Should Be CamelCase (2 tests)
Tests that internal application fields use camelCase:

**DynamoDB Fields:**
- `groupId`, `planId`, `executionId`
- `sourceServerId`, `waveName`
- `protectionGroupId`, `recoveryPlanName`
- `serverSelectionTags`, `sourceServerIds`
- `launchConfig`, `subnetId`, `securityGroupIds`
- `instanceType`, `instanceProfileName`
- `copyPrivateIp`, `copyTags`
- `targetInstanceTypeRightSizingMethod`
- `launchDisposition`, `licensing`
- `createdAt`, `updatedAt`, `startTime`, `endTime`
- `createdDate`, `lastModifiedDate`

**API Request Fields:**
- `groupName`, `region`, `accountId`
- `assumeRoleName`, `owner`, `description`
- `waveNumber`, `priority`, `manualApprovalRequired`

### 3. AWS API Context Detection (3 tests)
Tests detection of AWS API context vs internal context:

**EC2 API Context Indicators:**
```python
instance.get("PrivateIpAddress")  # AWS API
instance["PrivateIpAddress"]      # AWS API
response["Reservations"]          # AWS API
ec2.describe_instances            # AWS API call
```

**DRS API Context Indicators:**
```python
drs_server.get("recoveryInstanceID")  # AWS API
server.get("sourceProperties")        # AWS API
drs_client.describe_source_servers    # AWS API call
```

**Internal Context Indicators:**
```python
item["groupId"]           # Internal field
body.get("groupName")     # Internal field
wave.get("waveNumber")    # Internal field
execution["executionId"]  # Internal field
```

### 4. Validation Script Patterns (2 tests)
Tests patterns used in validation script:

**AWS API Exclusion Patterns:**
```bash
instance.get("PrivateIpAddress")  # Should be excluded
instance["PrivateIpAddress"]      # Should be excluded
response["Reservations"]          # Should be excluded
ec2.describe_instances            # Should be excluded
subnet["SubnetId"]                # Should be excluded
sg["GroupId"]                     # Should be excluded
```

**Internal Field Detection:**
```python
item["GroupId"]           # Should trigger error (use groupId)
body.get("GroupName")     # Should trigger error (use groupName)
wave["WaveName"]          # Should trigger error (use waveName)
```

### 5. Legacy Cleanup Patterns (1 test)
Tests that legacy PascalCase cleanup code is allowed:

```python
if "ServerSelectionTags" in existing_group:  # Allowed
update_expression += " REMOVE ServerSelectionTags"  # Allowed
remove_clauses.append("ServerSelectionTags")  # Allowed
```

### 6. Real-World Code Patterns (3 tests)
Tests actual code patterns from the codebase:

**EC2 Instance Details:**
```python
instance = response["Reservations"][0]["Instances"][0]  # AWS API
tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}  # AWS API
hostname = tags.get("Name", "")
return {
    "hostname": hostname,  # Internal camelCase
    "privateIp": instance.get("PrivateIpAddress", ""),  # AWS API → camelCase
}
```

**DRS Server Enrichment:**
```python
# AWS DRS API returns PascalCase by default - transform to camelCase for internal use
recovery_instance_id = drs_server.get("recoveryInstanceID")  # AWS API
if recovery_instance_id:
    server_data["instanceId"] = recovery_instance_id  # Internal camelCase
```

**DynamoDB Operations:**
```python
item = {
    "groupId": group_id,        # Internal camelCase
    "groupName": name,          # Internal camelCase
    "createdDate": timestamp,   # Internal camelCase
}
```

### 7. Validation Script Accuracy (2 tests)
Tests that validation script patterns match actual code:

**Required Exclusions:**
- `instance\[` - EC2 instance access
- `response\[` - API response access
- `ec2\.describe` - EC2 API calls
- `drs_client\.` - DRS API calls
- `iam\.list` - IAM API calls
- `subnet\[` - EC2 subnet access
- `sg\[` - Security group access
- `profile\[` - Instance profile access
- `paginator\.paginate` - AWS pagination

## Running Tests

### Run camelCase validation tests
```bash
pytest tests/python/unit/test_camelcase_validation.py -v
```

### Run specific test class
```bash
pytest tests/python/unit/test_camelcase_validation.py::TestAWSAPIPascalCaseExceptions -v
```

### Run with coverage
```bash
pytest tests/python/unit/test_camelcase_validation.py --cov=scripts --cov-report=term-missing
```

## Test Results

**Total Tests**: 17
**Status**: ✅ All passing
**Coverage**: CamelCase validation patterns comprehensively tested
**Performance**: Tests complete in < 0.02 seconds

## Validation Script Integration

The validation script (`scripts/validate-camelcase-consistency.sh`) uses these patterns to:

1. **Scan TypeScript files** for PascalCase field violations
2. **Scan Python Lambda files** for PascalCase field violations
3. **Exclude AWS API patterns** from validation
4. **Exclude legacy cleanup patterns** from validation
5. **Report errors** for internal PascalCase usage

### Validation Script Exclusions

The script properly excludes:
```bash
# AWS API response access
grep -v "instance\["
grep -v "response\["
grep -v "subnet\["
grep -v "sg\["
grep -v "profile\["

# AWS API calls
grep -v "ec2\.describe"
grep -v "drs_client\."
grep -v "iam\.list"
grep -v "paginator\.paginate"

# Legacy cleanup
grep -v "REMOVE"
grep -v "remove_clauses"
grep -v "in existing_group:"
```

## Key Findings

### What Works Well
1. **AWS API PascalCase properly handled** - EC2, DRS, IAM, CloudWatch APIs
2. **Internal camelCase enforced** - DynamoDB, API requests, responses
3. **Context detection accurate** - Distinguishes AWS API vs internal fields
4. **Legacy cleanup allowed** - Old PascalCase removal code excluded

### What to Watch
1. **New AWS services** - Add their PascalCase patterns to exclusions
2. **Mixed case APIs** - DRS uses `sourceServerID` (mixed case)
3. **Validation script updates** - Keep exclusions in sync with code patterns

## Common Patterns

### ✅ Correct: AWS API → Internal CamelCase
```python
# AWS API returns PascalCase
instance = response["Reservations"][0]["Instances"][0]
private_ip = instance.get("PrivateIpAddress", "")

# Transform to internal camelCase
return {
    "privateIp": private_ip,  # Internal field
    "hostname": hostname,     # Internal field
}
```

### ❌ Incorrect: Internal PascalCase
```python
# BAD: Internal fields should be camelCase
item = {
    "GroupId": group_id,      # Should be groupId
    "GroupName": name,        # Should be groupName
    "CreatedDate": timestamp, # Should be createdDate
}
```

### ✅ Correct: Internal CamelCase
```python
# GOOD: Internal fields use camelCase
item = {
    "groupId": group_id,
    "groupName": name,
    "createdDate": timestamp,
}
```

## Maintenance

### When to Update Tests
- Adding new AWS service integrations
- Discovering new AWS API PascalCase patterns
- Modifying validation script exclusions
- Finding edge cases in production

### Test Coverage Goals
- ✅ All AWS service APIs tested
- ✅ All internal field patterns tested
- ✅ All validation exclusions tested
- ✅ All real-world code patterns tested

## Related Documentation

- [Validation Script](../../../scripts/validate-camelcase-consistency.sh)
- [CamelCase Migration Plan](../../../docs/implementation/camelcase-migration-plan.md)
- [API Handler](../../../lambda/api-handler/index.py)
- [Execution Poller](../../../lambda/execution-poller/index.py)

## Summary

The camelCase validation tests ensure that:
1. ✅ AWS API PascalCase is properly allowed
2. ✅ Internal camelCase is properly enforced
3. ✅ Context detection works correctly
4. ✅ Validation script patterns are accurate
5. ✅ Real-world code patterns are validated

This prevents deployment failures caused by PascalCase/camelCase mismatches while allowing legitimate AWS API PascalCase responses.
