# CFN-Lint W2001 Detailed Analysis

## Summary

**Total W2001 Warnings: 47**
**Total W3005 Warnings: 121** (redundant DependsOn - separate issue)

**cfn-lint version: 1.44.0** (upgraded from 1.43.4)

## Breakdown by File

### 1. api-auth-stack.yaml (2 warnings)
- `AdminEmail` - NOT USED
- `ExecutionHistoryTableArn` - NOT USED

### 2. api-gateway-core-methods-stack.yaml (2 warnings)
- `ProjectName` - NOT USED
- `Environment` - NOT USED

### 3. api-gateway-core-stack.yaml (1 warning)
- `UserPoolClientId` - NOT USED

### 4. api-gateway-infrastructure-methods-stack.yaml (29 warnings)
- `ProjectName` - NOT USED
- `Environment` - NOT USED
- `DrsStartReplicationResourceId` - NOT USED
- `DrsStopReplicationResourceId` - NOT USED
- `DrsPauseReplicationResourceId` - NOT USED
- `DrsResumeReplicationResourceId` - NOT USED
- `DrsRetryDataReplicationResourceId` - NOT USED
- `DrsReplicationConfigurationResourceId` - NOT USED
- `DrsReplicationConfigurationTemplateResourceId` - NOT USED
- `DrsSourceServerResourceId` - NOT USED
- `DrsSourceServerByIdResourceId` - NOT USED
- `DrsDisconnectSourceServerResourceId` - NOT USED
- `DrsMarkAsArchivedResourceId` - NOT USED
- `DrsExtendedSourceServersResourceId` - NOT USED
- `DrsExtensibleSourceServersResourceId` - NOT USED
- `DrsSourceNetworksResourceId` - NOT USED
- `DrsSourceNetworkByIdResourceId` - NOT USED
- `DrsSourceNetworkRecoveryResourceId` - NOT USED
- `DrsSourceNetworkReplicationResourceId` - NOT USED
- `DrsSourceNetworkStackResourceId` - NOT USED
- `DrsSourceNetworkTemplateResourceId` - NOT USED
- `DrsLaunchConfigurationResourceId` - NOT USED
- `DrsLaunchConfigurationTemplateResourceId` - NOT USED
- `DrsLaunchActionsResourceId` - NOT USED
- `DrsLaunchActionByIdResourceId` - NOT USED
- `DrsInitializeServiceResourceId` - NOT USED
- `DrsRecoveryInstancesResourceId` - NOT USED
- `DrsRecoveryInstanceByIdResourceId` - NOT USED
- `DrsRecoverySnapshotsResourceId` - NOT USED

### 5. api-gateway-operations-methods-stack.yaml (11 warnings)
- `ProjectName` - NOT USED
- `Environment` - NOT USED
- `DrsTerminateRecoveryInstancesResourceId` - NOT USED
- `DrsDisconnectRecoveryInstanceResourceId` - NOT USED
- `DrsFailbackResourceId` - NOT USED
- `DrsReverseReplicationResourceId` - NOT USED
- `DrsStartFailbackResourceId` - NOT USED
- `DrsStopFailbackResourceId` - NOT USED
- `DrsFailbackConfigurationResourceId` - NOT USED
- `DrsJobByIdResourceId` - NOT USED
- `DrsJobLogsResourceId` - NOT USED

### 6. api-gateway-resources-stack.yaml (2 warnings)
- `ProjectName` - NOT USED
- `Environment` - NOT USED

## Analysis

### Why These Warnings Appeared

These warnings appeared after upgrading cfn-lint from 1.43.4 to 1.44.0. The new version has stricter parameter usage detection.

### Pattern Recognition

1. **ProjectName and Environment** appear in 4 files but are never used in Resources sections
2. **DRS Resource IDs** (29 in infrastructure, 11 in operations) are passed from master template but never referenced
3. **Auth parameters** (AdminEmail, ExecutionHistoryTableArn, UserPoolClientId) are passed but not used

### Next Steps

Need to determine for each parameter:
1. Is it genuinely unused? → Remove from both master template and nested stack
2. Is it used but cfn-lint can't detect it? → Verify with grep search for `!Ref ParameterName`
3. Is it planned for future use? → Add comment explaining why it's declared

## Verification Commands

```bash
# Check if a parameter is actually used
grep -r "!Ref ProjectName" cfn/api-gateway-core-methods-stack.yaml
grep -r "!Ref Environment" cfn/api-gateway-core-methods-stack.yaml

# Check all DRS parameters in infrastructure stack
for param in DrsStartReplicationResourceId DrsStopReplicationResourceId; do
    echo "Checking $param:"
    grep "!Ref $param" cfn/api-gateway-infrastructure-methods-stack.yaml
done
```
