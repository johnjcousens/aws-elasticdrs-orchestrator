# CamelCase Database Schema Migration Plan

## Field Name Mappings

### Protection Groups Table
- `GroupId` → `groupId`
- `GroupName` → `groupName`
- `Region` → `region`
- `SourceServerIds` → `sourceServerIds`
- `ServerSelectionTags` → `serverSelectionTags`
- `CreatedAt` → `createdAt`
- `UpdatedAt` → `updatedAt`
- `CreatedBy` → `createdBy`
- `AccountId` → `accountId`
- `AssumeRoleName` → `assumeRoleName`

### Recovery Plans Table
- `PlanId` → `planId`
- `PlanName` → `planName`
- `Description` → `description`
- `Waves` → `waves`
  - `WaveNumber` → `waveNumber`
  - `WaveName` → `waveName`
  - `ProtectionGroupId` → `protectionGroupId`
  - `ProtectionGroupIds` → `protectionGroupIds`
  - `Region` → `region`
  - `WaitTime` → `waitTime`
- `CreatedAt` → `createdAt`
- `UpdatedAt` → `updatedAt`
- `CreatedBy` → `createdBy`
- `TotalWaves` → `totalWaves`

### Execution History Table
- `ExecutionId` → `executionId`
- `PlanId` → `planId`
- `PlanName` → `planName`
- `RecoveryPlanName` → `recoveryPlanName`
- `ExecutionType` → `executionType`
- `Status` → `status`
- `StartTime` → `startTime`
- `EndTime` → `endTime`
- `InitiatedBy` → `initiatedBy`
- `Waves` → `waves`
  - `WaveNumber` → `waveNumber`
  - `WaveName` → `waveName`
  - `ProtectionGroupId` → `protectionGroupId`
  - `Region` → `region`
  - `Status` → `status`
  - `StartTime` → `startTime`
  - `EndTime` → `endTime`
  - `JobId` → `jobId`
  - `ServerStatuses` → `serverStatuses`
    - `SourceServerId` → `sourceServerId`
    - `LaunchStatus` → `launchStatus`
    - `RecoveryInstanceID` → `recoveryInstanceId`
    - `Error` → `error`
  - `ServerIds` → `serverIds`
  - `Servers` → `servers`
    - `SourceServerId` → `sourceServerId`
    - `InstanceId` → `instanceId`
    - `Status` → `status`
    - `LaunchTime` → `launchTime`
    - `Error` → `error`
    - `InstanceType` → `instanceType`
    - `PrivateIp` → `privateIp`
    - `Ec2State` → `ec2State`
  - `EnrichedServers` → `enrichedServers`
- `CurrentWave` → `currentWave`
- `TotalWaves` → `totalWaves`
- `ErrorMessage` → `errorMessage`
- `PausedBeforeWave` → `pausedBeforeWave`
- `SelectionMode` → `selectionMode`
- `HasActiveDrsJobs` → `hasActiveDrsJobs`

### Target Accounts Table
- `AccountId` → `accountId`
- `AccountName` → `accountName`
- `AssumeRoleName` → `assumeRoleName`
- `CrossAccountRoleArn` → `crossAccountRoleArn`
- `CreatedAt` → `createdAt`
- `UpdatedAt` → `updatedAt`
- `CreatedBy` → `createdBy`

## Benefits of CamelCase Migration

1. **Performance**: Eliminates expensive transform functions completely
2. **Consistency**: Database matches frontend field names exactly
3. **Maintainability**: No more dual field name management
4. **Scalability**: Performance stays constant as data grows
5. **Simplicity**: Direct JSON serialization without transformation

## Implementation Steps

1. Clear existing data (DONE)
2. Update Lambda functions to use camelCase field names
3. Remove all transform functions
4. Update frontend TypeScript interfaces (if needed)
5. Test end-to-end functionality
6. Deploy via GitHub Actions