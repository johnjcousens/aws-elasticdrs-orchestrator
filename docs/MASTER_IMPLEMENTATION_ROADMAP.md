# AWS DRS Orchestration - Master Implementation Roadmap

**Version**: 2.0 - UI-Driven Architecture  
**Created**: November 28, 2025  
**Principle**: 100% UI-driven, zero manual configuration  
**Status**: Ready for Implementation

---

## 🎯 Executive Summary

This roadmap consolidates features from 5 AWS DRS tools into a **UI-first architecture** where all configuration is managed through the web interface and stored in DynamoDB.

**Key Principle**: Users configure everything through the UI - no YAML files, no tags, no CI/CD pipelines.

**Source Tools Analyzed**:
1. `drs-plan-automation` - SSM automation, SNS notifications, job logging
2. `drs-template-manager` - Launch template management
3. `drs-configuration-synchronizer` - Configuration-as-code, subnet assignment
4. `drs-synch-ec2-tags-and-instance-type` - Tag/instance type sync
5. `drs-observability` - CloudWatch monitoring, EventBridge alerts

---

## 📊 Feature Prioritization Matrix

| Feature | Source Tool | Value | Effort | Priority | UI Complexity |
|---------|-------------|-------|--------|----------|---------------|
| **SNS Notifications** | drs-plan-automation | CRITICAL | 3h | P0 | LOW |
| **DRS Job Logging** | drs-plan-automation | HIGH | 2h | P0 | NONE |
| **CloudWatch Metrics** | drs-observability | HIGH | 2d | P0 | LOW |
| **Instance Type Sync** | drs-synch-tags | CRITICAL | 1d | P1 | MEDIUM |
| **Tag Sync** | drs-synch-tags | HIGH | 2d | P1 | MEDIUM |
| **Launch Config UI** | drs-config-sync | HIGH | 3d | P1 | HIGH |
| **SSM Automation** | drs-plan-automation | CRITICAL | 1w | P2 | HIGH |
| **Subnet Auto-Assignment** | drs-config-sync | HIGH | 2d | P2 | MEDIUM |
| **CloudWatch Dashboard** | drs-observability | MEDIUM | 1d | P3 | LOW |
| **EventBridge Alerts** | drs-observability | HIGH | 1d | P3 | LOW |

---

## 🏗️ UI-Driven Architecture

### **Core Principle**: Configuration in DynamoDB, Not Files

```
User Interface (React)
    ↓ (API calls)
Backend Lambda (Python)
    ↓ (Store config)
DynamoDB Tables
    ↓ (Apply config)
DRS Service
```

**No YAML/JSON files** - All configuration stored in DynamoDB  
**No tags** - Configuration linked by Protection Group ID  
**No CI/CD** - Changes applied immediately via API

---

## 📅 Implementation Timeline

### **Phase 0: Foundation** (Week 1 - 5 days)

**Goal**: Add observability and notifications without UI changes

#### **Day 1: SNS Notifications** (3 hours) ✅ ZERO UI CHANGES
- Backend-only implementation
- Users receive email notifications automatically
- Configuration via CloudFormation parameter

#### **Day 2: DRS Job Logging** (2 hours) ✅ ZERO UI CHANGES
- Enhanced logging with `describe_job_log_items`
- Logs appear in CloudWatch automatically
- No UI changes required

#### **Day 3-4: CloudWatch Metrics** (2 days) ✅ ZERO UI CHANGES
- Metrics collection in execution poller
- Visible in CloudWatch console
- No UI changes required

#### **Day 5: Testing & Validation**
- Test SNS notifications
- Verify CloudWatch metrics
- Validate job logging

**Deliverable**: Production-ready observability with zero UI changes

---

### **Phase 1: Protection Group Enhancements** (Week 2 - 5 days)

**Goal**: Add launch configuration and tag sync to Protection Groups

#### **Day 1-2: Launch Configuration UI** (2 days)

**New UI Component**: `LaunchConfigurationPanel.tsx`

Features:
- Copy Private IP checkbox
- Copy Tags checkbox
- Launch Disposition dropdown (STARTED/STOPPED)
- Instance Type Right-Sizing dropdown (BASIC/NONE)

**Backend Schema**:
```python
protection_group = {
    'GroupId': 'pg-123',
    'LaunchConfiguration': {
        'copyPrivateIp': True,
        'copyTags': True,
        'launchDisposition': 'STARTED',
        'targetInstanceTypeRightSizingMethod': 'BASIC'
    }
}
```

#### **Day 3: Tag Sync UI** (1 day)

**New UI Component**: `TagSyncPanel.tsx`

Features:
- Enable Tag Sync checkbox
- Add Source Metadata Tags checkbox
- "Sync Tags Now" button

#### **Day 4: Instance Type Sync** (1 day)

**UI Enhancement**: Server configuration table

Features:
- Display source vs. DRS instance types
- Mismatch indicators
- "Sync Instance Type" button per server
- "Sync All Instance Types" button

#### **Day 5: Testing & Integration**

**Deliverable**: Protection Groups with full launch configuration management

---

### **Phase 2: Wave-Level Configuration** (Week 3 - 5 days)

**Goal**: Add SSM automation and subnet assignment to waves

#### **Day 1-2: SSM Automation UI** (2 days)

**New UI Component**: `WaveAutomationPanel.tsx`

Features:
- Pre-Wave Actions list with add/edit/delete
- Post-Wave Actions list with add/edit/delete
- SSM Document autocomplete
- Parameters JSON editor
- Timeout configuration
- Continue-on-failure checkbox

**Backend Schema**:
```python
wave = {
    'WaveId': 'wave-1',
    'PreWaveActions': [
        {
            'name': 'Create Snapshot',
            'documentName': 'AWS-CreateSnapshot',
            'parameters': {'VolumeId': ['vol-123']},
            'maxWaitTime': 300,
            'continueOnFailure': False
        }
    ]
}
```

#### **Day 3: Subnet Auto-Assignment UI** (1 day)

**New UI Component**: `SubnetMappingPanel.tsx`

Features:
- Enable auto-subnet mapping checkbox
- Server-to-subnet mapping table
- Auto-detect status indicators
- Manual subnet override dropdown

#### **Day 4-5: Testing & Integration**

**Deliverable**: Waves with SSM automation and auto-subnet assignment

---

### **Phase 3: Monitoring & Alerting** (Week 4 - 5 days)

**Goal**: Add CloudWatch dashboard and EventBridge alerts

#### **Day 1-2: CloudWatch Dashboard** (2 days)

**New UI Page**: `MonitoringDashboard.tsx`

Features:
- Active Executions metric chart
- Servers by Status pie chart
- Recent Errors log insights
- Embedded CloudWatch widgets

#### **Day 3: EventBridge Alerts UI** (1 day)

**New UI Component**: `AlertConfigurationPanel.tsx`

Features:
- Notification email field
- Alert on failure checkbox
- Alert on warnings checkbox
- Alert on success checkbox

#### **Day 4-5: Testing & Documentation**

**Deliverable**: Complete monitoring and alerting system

---

## 📋 Complete Feature List (UI-Driven)

### **Protection Group Features**

| Feature | UI Component | Backend Storage | User Action |
|---------|--------------|-----------------|-------------|
| Launch Configuration | Checkboxes + Dropdowns | DynamoDB | Click checkboxes |
| Tag Sync | Button "Sync Tags Now" | DynamoDB | Click button |
| Instance Type Sync | Button "Sync Instance Types" | DynamoDB | Click button |
| Subnet Auto-Assignment | Checkbox "Enable Auto-Mapping" | DynamoDB | Enable checkbox |

### **Recovery Plan Features**

| Feature | UI Component | Backend Storage | User Action |
|---------|--------------|-----------------|-------------|
| Pre-Wave Actions | Dialog + List | DynamoDB | Add/Edit/Delete actions |
| Post-Wave Actions | Dialog + List | DynamoDB | Add/Edit/Delete actions |
| SSM Document Selection | Autocomplete | DynamoDB | Select from dropdown |
| Action Parameters | JSON TextField | DynamoDB | Enter JSON |

### **Monitoring Features**

| Feature | UI Component | Backend Storage | User Action |
|---------|--------------|-----------------|-------------|
| CloudWatch Dashboard | Embedded Charts | CloudFormation | View dashboard |
| Alert Configuration | Email TextField | DynamoDB | Enter email |
| Notification Preferences | Checkboxes | DynamoDB | Select preferences |

---

## 💾 Data Model (DynamoDB Schema)

### **Protection Groups Table**
```python
{
    'GroupId': 'pg-123',
    'GroupName': 'Web Tier',
    'SourceServerIds': ['s-abc', 's-def'],
    'Region': 'us-east-1',
    # Launch configuration (UI-driven)
    'LaunchConfiguration': {
        'copyPrivateIp': True,
        'copyTags': True,
        'launchDisposition': 'STARTED',
        'targetInstanceTypeRightSizingMethod': 'BASIC'
    },
    # Tag sync settings (UI-driven)
    'TagSyncEnabled': True,
    'AddMetadataTags': True,
    # Subnet mapping (UI-driven)
    'EnableAutoSubnetMapping': True,
    'TargetSubnetId': 'subnet-123'  # Manual override if auto disabled
}
```

### **Recovery Plans Table**
```python
{
    'PlanId': 'plan-123',
    'PlanName': 'Production Failover',
    'Waves': [
        {
            'WaveId': 'wave-1',
            'WaveName': 'Database Tier',
            'ProtectionGroupId': 'pg-123',
            # SSM automation (UI-driven)
            'PreWaveActions': [
                {
                    'name': 'Create Snapshot',
                    'documentName': 'AWS-CreateSnapshot',
                    'parameters': {'VolumeId': ['vol-123']},
                    'maxWaitTime': 300,
                    'continueOnFailure': False
                }
            ],
            'PostWaveActions': [...]
        }
    ]
}
```

### **Alert Configuration Table** (NEW)
```python
{
    'UserId': 'user-123',
    'NotificationEmail': 'user@example.com',
    'AlertOnFailure': True,
    'AlertOnWarnings': True,
    'AlertOnSuccess': False
}
```

---

## 🎨 UI Component Hierarchy

```
App
├── Navigation
├── Dashboard (NEW - Monitoring)
│   ├── MetricCharts
│   ├── ActiveExecutions
│   └── RecentErrors
├── ProtectionGroups
│   ├── ProtectionGroupList
│   └── ProtectionGroupDialog
│       ├── ServerSelection
│       ├── LaunchConfigurationPanel (NEW)
│       ├── TagSyncPanel (NEW)
│       └── SubnetMappingPanel (NEW)
├── RecoveryPlans
│   ├── RecoveryPlanList
│   └── RecoveryPlanDialog
│       ├── WaveConfiguration
│       ├── WaveAutomationPanel (NEW)
│       │   ├── PreWaveActionsDialog
│       │   └── PostWaveActionsDialog
│       └── SubnetMappingPanel (NEW)
├── Executions
│   ├── ExecutionList
│   └── ExecutionDetails
│       ├── WaveProgress
│       ├── ServerStatus
│       └── SSMActionStatus (NEW)
└── Settings (NEW)
    ├── AlertConfiguration
    └── NotificationPreferences
```

---

## ✅ Success Criteria

### **Week 1 Complete**
- ✅ Users receive email notifications on execution completion
- ✅ CloudWatch metrics visible in AWS console
- ✅ Enhanced job logging in CloudWatch Logs

### **Week 2 Complete**
- ✅ Users can configure launch settings via UI checkboxes
- ✅ Users can sync tags with one button click
- ✅ Users can sync instance types with one button click
- ✅ All configuration stored in DynamoDB (no YAML/JSON files)

### **Week 3 Complete**
- ✅ Users can add SSM automation actions via UI dialog
- ✅ Users can enable auto-subnet mapping via checkbox
- ✅ SSM actions execute before/after wave recovery
- ✅ Subnets automatically assigned based on source IP

### **Week 4 Complete**
- ✅ Users can view CloudWatch dashboard in UI
- ✅ Users can configure alerts via UI form
- ✅ EventBridge sends alerts based on user preferences
- ✅ Complete UI-driven solution with zero manual configuration

---

## 📚 Related Documentation

### **Implementation Guides**
- [AWS DRS Tools Integration Guide](AWS_DRS_TOOLS_INTEGRATION_GUIDE.md) - Detailed implementation patterns
- [DRS Plan Automation Analysis](DRS_PLAN_AUTOMATION_ANALYSIS.md) - SSM automation patterns
- [DRS Configuration Synchronizer Analysis](DRS_CONFIGURATION_SYNCHRONIZER_ANALYSIS.md) - Configuration management
- [DRS Tag & Instance Type Sync Analysis](DRS_TAG_INSTANCE_TYPE_SYNC_ANALYSIS.md) - Tag synchronization
- [DRS Observability Analysis](DRS_OBSERVABILITY_ANALYSIS.md) - Monitoring and alerting

### **Architecture Documentation**
- [Architectural Design Document](architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md) - System architecture
- [Software Requirements Specification](requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md) - Functional requirements
- [UX/UI Design Specifications](requirements/UX_UI_DESIGN_SPECIFICATIONS.md) - UI design patterns

---

## 🚀 Getting Started

### **Immediate Next Steps**

1. **Review this roadmap** with stakeholders
2. **Begin Week 1 implementation** (SNS + CloudWatch) - zero UI changes
3. **Prepare UI mockups** for Week 2 features
4. **Set up development environment** for frontend changes

### **Development Workflow**

```bash
# Week 1: Backend only
cd lambda/poller
# Edit execution_poller.py
# Add SNS notifications
# Add CloudWatch metrics
# Deploy with deploy_lambda.py

# Week 2: Frontend + Backend
cd frontend/src/components
# Create LaunchConfigurationPanel.tsx
# Create TagSyncPanel.tsx
# Update ProtectionGroupDialog.tsx

cd lambda
# Update index.py with new endpoints
# Deploy changes
```

---

## 📞 Support & Questions

For questions about this roadmap:
- Review the detailed implementation guides linked above
- Check the AWS DRS Tools analysis documents
- Refer to the main [README.md](../README.md) for deployment instructions

---

**Document Owner**: AWS DRS Orchestration Team  
**Last Updated**: November 28, 2025  
**Version**: 2.0 - UI-Driven Architecture  
**Status**: Ready for Implementation
