# DRS Source Server Management Features

## Executive Summary

This document consolidates all DRS source server configuration and management features into a comprehensive implementation guide. These features provide complete lifecycle management of DRS source servers from initial setup through ongoing configuration management.

---

## Feature Overview

### Consolidated Features

| Feature | Current Status | Priority | LOE |
|---------|----------------|----------|-----|
| **DRS Server Info Dashboard** | Planned | High | 2-3 weeks |
| **DRS Launch Settings Management** | Planned | High | 3-4 weeks |
| **DRS Disk Settings Configuration** | Planned | Medium | 2-3 weeks |
| **DRS Replication Settings** | Planned | Medium | 2-3 weeks |
| **DRS Post-Launch Settings** | Planned | Medium | 2-3 weeks |
| **DRS Tags Management** | Planned | Low | 1-2 weeks |
| **EC2 Launch Template Integration** | Planned | Medium | 2-3 weeks |
| **DRS Source Servers Page** | Planned | High | 3-4 weeks |
| **DRS Agent Installation Monitoring** | Planned | Low | 2-3 weeks |

### Implementation Approach

Rather than implementing 9 separate features, consolidate into **3 major releases**:

1. **DRS Server Dashboard & Info** (4-5 weeks)
2. **DRS Configuration Management** (6-8 weeks) 
3. **DRS Advanced Features** (4-6 weeks)

---

## Release 1: DRS Server Dashboard & Info (4-5 weeks)

### Scope
Comprehensive server information display and basic management capabilities.

#### Components
- **DRS Server Info Dashboard** (from DRS_SERVER_INFO_MVP_PLAN.md)
- **DRS Source Servers Page** (from DRS_SOURCE_SERVERS_PAGE_PLAN.md)
- **DRS Agent Installation Monitoring** (from DRS_AGENT_INSTALLATION_REPLICATION_MONITORING.md)

#### Key Features
- **Server Overview Dashboard**: Real-time status, replication health, recovery readiness
- **Server Details Panel**: Hardware specs, network configuration, replication metrics
- **Agent Status Monitoring**: Installation status, version tracking, health checks
- **Replication Status**: Data transfer rates, lag metrics, staging area health
- **Recovery Readiness**: Point-in-time recovery options, launch readiness indicators

#### UI Components
```typescript
// New page components
- DRSSourceServersPage.tsx
- DRSServerDetailsPage.tsx
- DRSServerInfoPanel.tsx
- DRSAgentStatusPanel.tsx
- DRSReplicationStatusPanel.tsx

// New shared components
- DRSServerCard.tsx
- DRSHealthIndicator.tsx
- DRSMetricsChart.tsx
- DRSServerTable.tsx
```

#### API Extensions
```python
# New API endpoints
GET /drs/source-servers
GET /drs/source-servers/{server-id}
GET /drs/source-servers/{server-id}/replication-status
GET /drs/source-servers/{server-id}/agent-status
GET /drs/source-servers/{server-id}/recovery-readiness
```

---

## Release 2: DRS Configuration Management (6-8 weeks)

### Scope
Complete DRS source server configuration management with UI-driven settings.

#### Components
- **DRS Launch Settings Management** (from DRS_LAUNCH_SETTINGS_IMPLEMENTATION_PLAN.md + DRS_LAUNCH_SETTINGS_MVP_PLAN.md)
- **DRS Disk Settings Configuration** (from DRS_DISK_SETTINGS_MVP_PLAN.md)
- **DRS Replication Settings** (from DRS_REPLICATION_SETTINGS_MVP_PLAN.md)
- **DRS Post-Launch Settings** (from DRS_POST_LAUNCH_MVP_PLAN.md)

#### Key Features

##### DRS Launch Settings
- **Instance Type Selection**: Right-sizing recommendations, cost optimization
- **Launch Disposition**: Test/Drill vs Recovery mode configuration
- **Network Configuration**: Subnet selection, security group assignment
- **IAM Instance Profile**: Role assignment for recovery instances
- **Copy Settings**: Private IP preservation, tag copying options

##### DRS Disk Settings
- **Per-Disk Configuration**: EBS volume type, size, IOPS, throughput
- **Encryption Settings**: KMS key selection, encryption at rest
- **Performance Optimization**: GP3 vs io2 recommendations
- **Cost Optimization**: Volume type recommendations based on workload

##### DRS Replication Settings
- **Staging Area Configuration**: Instance type, subnet, security groups
- **Bandwidth Throttling**: Network utilization controls
- **Replication Frequency**: RPO configuration, snapshot scheduling
- **Data Compression**: Bandwidth optimization settings

##### DRS Post-Launch Settings
- **SSM Automation**: Document selection, parameter configuration
- **Deployment Type**: In-place vs blue/green deployment
- **S3 Log Configuration**: Log bucket, prefix, retention settings
- **Custom Scripts**: User data, startup scripts, health checks

#### UI Architecture
```typescript
// Configuration management components
- DRSLaunchSettingsEditor.tsx
- DRSDiskSettingsEditor.tsx
- DRSReplicationSettingsEditor.tsx
- DRSPostLaunchSettingsEditor.tsx

// Shared configuration components
- DRSInstanceTypeSelector.tsx
- DRSSubnetSelector.tsx
- DRSSecurityGroupSelector.tsx
- DRSVolumeTypeSelector.tsx
- DRSSSMDocumentSelector.tsx
```

#### API Extensions
```python
# Configuration management endpoints
PUT /drs/source-servers/{server-id}/launch-settings
PUT /drs/source-servers/{server-id}/disk-settings
PUT /drs/source-servers/{server-id}/replication-settings
PUT /drs/source-servers/{server-id}/post-launch-settings

# Validation endpoints
POST /drs/source-servers/{server-id}/validate-launch-settings
POST /drs/source-servers/{server-id}/validate-disk-settings
```

---

## Release 3: DRS Advanced Features (4-6 weeks)

### Scope
Advanced DRS management features and EC2 integration.

#### Components
- **DRS Tags Management** (from DRS_TAGS_MVP_PLAN.md)
- **EC2 Launch Template Integration** (from EC2_LAUNCH_TEMPLATE_MVP_PLAN.md)

#### Key Features

##### DRS Tags Management
- **Tag Synchronization**: EC2 → DRS source server tag sync
- **Bulk Tag Operations**: Apply tags to multiple servers
- **Tag Templates**: Predefined tag sets for different environments
- **Tag Validation**: Required tags, format validation
- **Tag History**: Audit trail for tag changes

##### EC2 Launch Template Integration
- **Template Selection**: Choose from existing EC2 launch templates
- **Template Validation**: Compatibility checks with DRS requirements
- **Template Customization**: DRS-specific overrides
- **Version Management**: Track template versions, rollback capability
- **Template Sharing**: Cross-account template access

#### UI Components
```typescript
// Advanced feature components
- DRSTagsEditor.tsx
- DRSTagSyncPanel.tsx
- DRSLaunchTemplateSelector.tsx
- DRSLaunchTemplateEditor.tsx

// Bulk operation components
- DRSBulkTagEditor.tsx
- DRSBulkConfigurationPanel.tsx
```

#### API Extensions
```python
# Tags management
GET /drs/source-servers/{server-id}/tags
PUT /drs/source-servers/{server-id}/tags
POST /drs/source-servers/bulk-tag-update
POST /drs/source-servers/{server-id}/sync-tags-from-ec2

# Launch template integration
GET /drs/launch-templates
GET /drs/launch-templates/{template-id}
PUT /drs/source-servers/{server-id}/launch-template
POST /drs/source-servers/{server-id}/validate-launch-template
```

---

## Technical Architecture

### Data Models

#### DRS Source Server Extended
```json
{
  "ServerId": "s-1234567890abcdef0",
  "Hostname": "web-server-01",
  "SourceProperties": {
    "InstanceId": "i-1234567890abcdef0",
    "InstanceType": "t3.medium",
    "Platform": "LINUX",
    "Architecture": "x86_64"
  },
  "ReplicationInfo": {
    "Status": "HEALTHY",
    "DataReplicationState": "CONTINUOUS",
    "EtaDateTime": "2025-12-30T10:00:00Z",
    "ReplicatedStorageBytes": 107374182400,
    "TotalStorageBytes": 107374182400
  },
  "LaunchConfiguration": {
    "InstanceType": "t3.medium",
    "LaunchDisposition": "STARTED",
    "CopyPrivateIp": true,
    "CopyTags": true,
    "TargetInstanceTypeRightSizingMethod": "BASIC"
  },
  "AgentInfo": {
    "Version": "1.2.3",
    "Status": "HEALTHY",
    "LastSeenDateTime": "2025-12-30T09:55:00Z"
  }
}
```

#### DRS Configuration Settings
```json
{
  "ServerId": "s-1234567890abcdef0",
  "LaunchSettings": {
    "InstanceType": "t3.medium",
    "SubnetId": "subnet-12345678",
    "SecurityGroupIds": ["sg-12345678"],
    "IamInstanceProfileName": "DRSRecoveryInstanceProfile"
  },
  "DiskSettings": [
    {
      "DeviceName": "/dev/sda1",
      "VolumeType": "gp3",
      "VolumeSize": 100,
      "Iops": 3000,
      "Throughput": 125,
      "Encrypted": true,
      "KmsKeyId": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
    }
  ],
  "ReplicationSettings": {
    "StagingAreaSubnetId": "subnet-87654321",
    "BandwidthThrottling": 100,
    "CreatePublicIP": false,
    "DataPlaneRouting": "PRIVATE_IP"
  },
  "PostLaunchSettings": {
    "SsmDocumentName": "AWSConfigRemediation-RemoveUnrestrictedSourceInSecurityGroup",
    "DeploymentType": "IN_PLACE",
    "S3LogBucket": "drs-recovery-logs",
    "S3KeyPrefix": "recovery-logs/"
  }
}
```

### UI State Management

#### DRS Server Context
```typescript
interface DRSServerContextType {
  servers: DRSSourceServer[];
  selectedServer: DRSSourceServer | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  fetchServers: () => Promise<void>;
  selectServer: (serverId: string) => void;
  updateServerConfiguration: (serverId: string, config: DRSConfiguration) => Promise<void>;
  syncTagsFromEC2: (serverId: string) => Promise<void>;
  validateConfiguration: (serverId: string, config: Partial<DRSConfiguration>) => Promise<ValidationResult>;
}
```

#### Configuration Form State
```typescript
interface DRSConfigurationFormState {
  launchSettings: DRSLaunchSettings;
  diskSettings: DRSDiskSettings[];
  replicationSettings: DRSReplicationSettings;
  postLaunchSettings: DRSPostLaunchSettings;
  tags: DRSTag[];
  
  // Validation
  errors: Record<string, string>;
  warnings: Record<string, string>;
  isValid: boolean;
  
  // UI State
  activeTab: string;
  saving: boolean;
  hasUnsavedChanges: boolean;
}
```

---

## Implementation Strategy

### Development Phases

#### Phase 1: Foundation (Week 1-2)
- **DRS API Integration**: Core DRS service integration
- **Data Models**: Define TypeScript interfaces and API contracts
- **Base Components**: Shared UI components for DRS management
- **Navigation**: Add DRS servers section to main navigation

#### Phase 2: Server Dashboard (Week 3-5)
- **Server List Page**: Comprehensive server overview with filtering/search
- **Server Details Page**: Detailed server information and status
- **Agent Monitoring**: Real-time agent status and health metrics
- **Replication Status**: Visual replication progress and health indicators

#### Phase 3: Configuration Management (Week 6-11)
- **Launch Settings**: Instance type, network, IAM configuration
- **Disk Settings**: Per-disk EBS configuration with cost optimization
- **Replication Settings**: Staging area and bandwidth configuration
- **Post-Launch Settings**: SSM automation and logging configuration

#### Phase 4: Advanced Features (Week 12-15)
- **Tags Management**: Comprehensive tag operations and synchronization
- **Launch Template Integration**: EC2 launch template compatibility
- **Bulk Operations**: Multi-server configuration management
- **Validation & Testing**: Comprehensive configuration validation

### Testing Strategy

#### Unit Testing
- **Component Testing**: All React components with Jest/RTL
- **API Testing**: Lambda function unit tests with moto mocking
- **Validation Testing**: Configuration validation logic

#### Integration Testing
- **DRS API Integration**: Real DRS service integration tests
- **Cross-Component Testing**: End-to-end configuration workflows
- **Performance Testing**: Large server list handling (1000+ servers)

#### User Acceptance Testing
- **Configuration Workflows**: Complete server configuration scenarios
- **Bulk Operations**: Multi-server management workflows
- **Error Handling**: Invalid configuration and error recovery

---

## Success Metrics

### Functional Metrics
- **Server Management**: Successfully manage 500+ DRS source servers
- **Configuration Time**: < 5 minutes to configure a server completely
- **Bulk Operations**: Configure 50+ servers simultaneously
- **Validation**: 100% configuration validation before deployment

### Performance Metrics
- **Page Load Time**: < 3 seconds for server list (500+ servers)
- **Configuration Save**: < 2 seconds for configuration updates
- **Real-time Updates**: < 5 seconds for status refresh
- **Search Performance**: < 1 second for server search/filtering

### User Experience Metrics
- **Task Completion**: 95% success rate for configuration tasks
- **Error Recovery**: < 30 seconds to resolve configuration errors
- **Learning Curve**: < 1 hour to configure first server
- **User Satisfaction**: > 4.5/5 rating for DRS management experience

---

## Migration from Individual Plans

### Consolidation Benefits
- **67% Reduction**: 9 individual plans → 3 major releases
- **Unified UX**: Consistent interface across all DRS management features
- **Shared Components**: Reusable UI components across features
- **Integrated Testing**: Comprehensive testing across related features

### Implementation Order
1. **Release 1** enables basic DRS server visibility and monitoring
2. **Release 2** provides complete configuration management capabilities
3. **Release 3** adds advanced features and bulk operations

### Backward Compatibility
- All existing DRS functionality remains unchanged
- New features are additive enhancements
- Gradual rollout with feature flags for controlled deployment

---

## Conclusion

This consolidated approach to DRS source server management provides a comprehensive solution while reducing implementation complexity. By grouping related features into logical releases, we can deliver value incrementally while maintaining a cohesive user experience.

The three-release approach enables faster delivery of core functionality while building toward advanced enterprise features in a structured manner.