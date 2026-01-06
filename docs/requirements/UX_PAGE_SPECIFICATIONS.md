# Page Specifications

## AWS DRS Orchestration System

**Version**: 2.2  
**Date**: January 6, 2026  
**Status**: Production Ready - GitHub Actions CI/CD Migration Complete  
**Build Scope**: Complete page implementation specifications including tag synchronization and security features

---

## Overview

This document provides complete specifications for building all 7 pages required for the AWS DRS Orchestration system. Each page specification includes detailed layouts, required components, behaviors, and implementation requirements needed to build a fully functional application from the ground up.

**Build Requirements**: All pages must use React + TypeScript + AWS CloudScape Design System for AWS Console consistency.

---

## Implementation Guidelines

When building each page:
1. Follow the exact layout specifications provided
2. Implement all listed features and behaviors
3. Use the specified CloudScape components and patterns
4. Include all error handling and loading states
5. Implement real-time updates where specified

**Important**: These specifications contain all detail needed to build production-ready pages without additional reference materials.

---

## 1. Login Page (`/login`)

**Build Requirements**: Create authentication page with AWS Cognito integration and console-style branding

**Required Layout**:
- Dark background (#232f3e)
- Centered white card (400px max width)
- AWS logo and app title
- Username/password form
- 3D isometric cube decorations
- Disclaimer footer

**Key Features**:
- Auto-redirect for authenticated users
- Error handling with CloudScape Alert
- AWS IAM Identity Center styling

---

## 2. Dashboard Page (`/`)

**Build Requirements**: Create operational dashboard with real-time metrics and system health monitoring

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Dashboard                                        [Refresh]  │
│ Real-time execution status and system metrics              │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐             │
│ │ Active  │ │Completed│ │ Failed  │ │Success  │             │
│ │Executions│ │   15    │ │   2     │ │ Rate    │             │
│ │    3    │ │         │ │         │ │  88%    │             │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘             │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────┐             │
│ │ Execution Status    │ │ Active Executions   │             │
│ │                     │ │                     │             │
│ │   [Pie Chart]       │ │ ● Plan A (Running)  │             │
│ │                     │ │ ● Plan B (Paused)   │             │
│ │ 18 total            │ │ ● Plan C (Pending)  │             │
│ │                     │ │                     │             │
│ │                     │ │ [View all]          │             │
│ └─────────────────────┘ └─────────────────────┘             │
├─────────────────────────────────────────────────────────────┤
│ DRS Capacity by Region        [Sync Tags] [Region Selector] │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [DRSQuotaStatusPanel with progress bars]               │ │
│ │ - Replicating Servers: 45/300 (15%)                   │ │
│ │ - Concurrent Jobs: 2/20 (10%)                         │ │
│ │ - Servers in Jobs: 12/500 (2%)                        │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Recent Activity                              [View history] │
│                                                             │
│ ● Plan A - Completed - Dec 13, 10:30 AM                    │
│ ● Plan B - Failed - Dec 12, 2:15 PM                        │
│ ● Plan C - Completed - Dec 11, 9:45 AM                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Required Features**:
- **Auto-region detection**: Must detect busiest region (most replicating servers) on page load
- **Real-time updates**: Implement 30-second refresh intervals for executions and DRS quotas
- **Tag sync functionality**: Build EC2 → DRS server tag synchronization capability
- **Account-aware filtering**: Filter all data by currently selected account
- **Interactive pie chart**: Implement donut chart with hover details and percentages
- **Status color coding**: Use Success (green), Error (red), Warning (orange), Active (blue)

---

## 3. Getting Started Page (`/getting-started`)

**Build Requirements**: Create onboarding and account setup wizard with conditional rendering

**Required Conditional Logic**:
- **No Accounts**: Display account setup instructions + AccountManagementPanel
- **Accounts Configured**: Show 3-column navigation cards + Quick Start Guide

**Required Features**:
- Account configuration detection
- Step-by-step onboarding guide
- Best practices checklist
- Navigation shortcuts to main features

---

## 4. Protection Groups Page (`/protection-groups`)

**Build Requirements**: Create DRS protection groups management interface with server discovery

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Protection Groups                        [Create Group]     │
│ Organize DRS servers for coordinated recovery              │
├─────────────────────────────────────────────────────────────┤
│ [Find protection groups...                    ] X matches   │
│                                                             │
│ Actions │ Name        │ ID  │ Region    │ Servers │ Created │
│ [▼]     │ Database    │ 📋  │ us-east-1 │ 3       │ Jan 5   │
│ [▼]     │ Application │ 📋  │ us-east-1 │ 5       │ Jan 4   │
│ [▼]     │ Web Tier    │ 📋  │ us-west-2 │ 2       │ Jan 3   │
│                                                             │
│ [< 1 2 3 >]                                                │
└─────────────────────────────────────────────────────────────┘
```

**Required Features**:
- CloudScape Table with collection hooks (filtering, pagination, sorting)
- Real-time server conflict checking
- Tag-based server selection display with preview
- Auto-refresh with dialog pause logic (30-second intervals)
- Copy-to-clipboard for Group IDs
- Permission-aware action buttons (Edit, Delete)

**ProtectionGroupDialog Modal**:
- Tabbed interface: Tags vs Servers selection modes
- RegionSelector with all 30 DRS regions
- ServerDiscoveryPanel with search and filtering
- ServerSelector with checkbox selection and assignment status badges
- LaunchConfigSection for DRS launch settings configuration
- Server validation against DRS API

**API Integration**:
- `GET /protection-groups` - List all groups with server details
- `POST /protection-groups` - Create group with tag-based or explicit server selection
- `GET /protection-groups/{id}` - Get single group with enriched server details
- `PUT /protection-groups/{id}` - Update group (blocked during active executions)
- `DELETE /protection-groups/{id}` - Delete group (blocked if referenced by Recovery Plans)
- `POST /protection-groups/resolve` - Preview servers matching specified tags
- `GET /drs/source-servers?region={region}` - Discover DRS servers with assignment status

---

## 5. Recovery Plans Page (`/recovery-plans`)

**Build Requirements**: Create recovery plans management with wave-based execution capabilities

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Recovery Plans                            [Create Plan]     │
│ Define recovery strategies with wave-based orchestration   │
├─────────────────────────────────────────────────────────────┤
│ [Find recovery plans...                       ] X matches   │
│                                                             │
│ Actions │ Plan Name   │ ID  │ Waves │ Status    │ Last Start │ Last End   │ Created │
│ [▼]     │ HRP-Full    │ 📋  │ 3     │ ✅ Comp   │ Jan 6 10AM │ Jan 6 11AM │ Jan 1   │
│ [▼]     │ Web-Only    │ 📋  │ 1     │ ❌ Failed │ Jan 5 2PM  │ Jan 5 3PM  │ Jan 2   │
│ [▼]     │ DB-Tier     │ 📋  │ 2     │ Not Run   │ Never      │ Never      │ Jan 3   │
│                                                             │
│ [< 1 2 3 >]                                                │
└─────────────────────────────────────────────────────────────┘
```

**Required Features**:
- CloudScape Table with collection hooks (filtering, pagination, sorting)
- Run Drill/Recovery actions with conflict detection
- Existing recovery instance warnings before drill execution
- Real-time execution progress (5-second polling)
- Copy-to-clipboard for Plan IDs
- Permission-aware action buttons (Run Drill, Run Recovery, Edit, Delete)
- Server conflict detection with detailed error messages

**RecoveryPlanDialog Modal**:
- Plan name and description fields
- WaveConfigEditor with expandable wave sections
- Multi-select Protection Groups per wave
- ServerSelector for wave-specific server selection
- Pause-before-wave toggle for each wave
- Wave dependency configuration

**Existing Instances Warning Dialog**:
- Alert showing count of existing recovery instances
- Instance details: Name, IP, instance type, launch time
- Source execution and plan name tracking
- Options: Cancel or Continue with Drill

**API Integration**:
- `GET /recovery-plans` - List all plans with execution status
- `POST /recovery-plans` - Create plan with wave configuration
- `GET /recovery-plans/{id}` - Get plan with full wave details
- `PUT /recovery-plans/{id}` - Update plan (blocked during active executions)
- `DELETE /recovery-plans/{id}` - Delete plan (blocked during active executions)
- `POST /executions` - Start execution (PlanId, ExecutionType: DRILL|RECOVERY)
- `GET /recovery-plans/{id}/check-existing-instances` - Check for existing recovery instances

---

## 6. Executions Page (`/executions`)

**Build Requirements**: Create execution monitoring interface with advanced filtering and real-time updates

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ History                          🟢 Live Updates [Refresh]  │
│ Real-time monitoring and historical records of DRS recoveries │
│                                          Updated 2m ago     │
├─────────────────────────────────────────────────────────────┤
│ [Active (2)] [History (15)]                                 │
├─────────────────────────────────────────────────────────────┤
│ Active Tab:                                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Web Tier Recovery                                       │ │
│ │ 🔵 IN_PROGRESS  Wave 2 of 3  Started 30m ago           │ │
│ │ Progress: ████████████████████░░░░░░░░░░░░░░░░░░░░ 67%  │ │
│ │ [View Details]                                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ History Tab:                                                │
│ [Clear History (2)] [Quick Filters ▼] [Clear Filter]       │
│                                                             │
│ Date Range Filter:                                          │
│ From: [MM-dd-yyyy] To: [MM-dd-yyyy]                        │
│                                                             │
│ [Find executions...                        ] X matches     │
│                                                             │
│ ☑ Actions │ Plan │ Status │ Source │ Type │ Waves │ Started │ Completed │
│ ☑ [View]  │ Web  │ ✓ Comp │ UI     │ DRILL│ 3     │ 2h ago  │ 1h ago    │
│ ☐ [View]  │ App  │ ❌ Fail│ API    │ DRILL│ 2     │ 1d ago  │ 1d ago    │
└─────────────────────────────────────────────────────────────┘
```

**Active Tab Requirements**:
- **Real-time progress cards**: Implement live updates every 3 seconds for active executions
- **Progress visualization**: Build progress bars with percentage and wave tracking
- **Duration tracking**: Calculate and display live elapsed time
- **Status indicators**: Create color-coded status badges with real-time updates

**History Tab Requirements**:
- **Multi-select table**: Build bulk operations with checkbox selection
- **Advanced date filtering**: 
  - Quick filters: Last Hour, Last 6 Hours, Today, Last 3 Days, Last Week, Last Month
  - Custom date range picker (MM-dd-yyyy format)
  - Timezone-aware filtering with start/end of day boundaries
- **Text search**: Implement filtering by plan name, execution ID, or other fields
- **Bulk delete**: Multi-select deletion with detailed confirmation dialog
- **Source tracking**: Display execution origin (UI, API, CLI, EventBridge, SSM, Step Functions)
- **Recovery type badges**: Show Tag-Based vs Plan-Based execution types
- **Execution type badges**: Display DRILL vs RECOVERY mode indicators

**Required Implementation Details**:
- **Smart polling**: Only poll when active executions exist
- **Session persistence**: Maintain active execution tracking across page refreshes
- **Error handling**: Comprehensive error states with retry options
- **Performance optimization**: Efficient filtering and pagination with collection hooks

---

## 7. Execution Details Page (`/executions/:executionId`)

**Build Requirements**: Create real-time monitoring interface for individual execution progress

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Execution Details                                           │
│ [← Back to Executions] [Refresh] [Resume*] [Cancel*] [Terminate*] │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ⚠️ Execution Paused (when applicable)                   │ │
│ │ Execution is paused before starting Wave 2.            │ │
│ │ Click Resume to continue.              [Resume]        │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Recovery Plan                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Web Tier Recovery                                       │ │
│ │ 🔵 IN_PROGRESS  [Wave 2 of 3]  [By: admin@example.com] │ │
│ │                                                         │ │
│ │ Started          Ended           Duration    Execution ID │
│ │ Jan 6, 10:30 AM  -              45m 23s     exec-abc123  │
│ │                                                         │ │
│ │ Overall Progress                                   67%  │ │
│ │ ████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░  │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Wave Progress                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Wave 1: Database Tier                    ✅ COMPLETED   │ │
│ │ ├─ s-abc123 (db-primary)      LAUNCHED   i-xxx         │ │
│ │ └─ s-def456 (db-replica)      LAUNCHED   i-yyy         │ │
│ │                                                         │ │
│ │ Wave 2: Application Tier                 🔵 IN_PROGRESS │ │
│ │ ├─ s-ghi789 (app-server-1)    LAUNCHING  -             │ │
│ │ └─ s-jkl012 (app-server-2)    PENDING    -             │ │
│ │                                                         │ │
│ │ Wave 3: Web Tier                         ⏳ PENDING     │ │
│ │ ├─ s-mno345 (web-server-1)    PENDING    -             │ │
│ │ └─ s-pqr678 (web-server-2)    PENDING    -             │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Required Features**:
- **Real-time progress updates**: 3-second polling for active executions
- **Pause/Resume functionality**: Resume button when execution is paused
- **Cancel execution**: Cancel button (disabled on final wave)
- **Terminate instances**: Available only for terminal states (COMPLETED, FAILED, CANCELLED)
- **Wave progress visualization**: WaveProgress component with server-level status
- **Progress calculation**: Based on DRS job phases (JOB_START 5% → SNAPSHOT 15% → CONVERSION 75% → LAUNCHED 100%)
- **Duration tracking**: Live elapsed time calculation
- **Error handling**: Alert components for cancel/resume/terminate errors
- **Termination progress**: Real-time progress bar during instance termination

**Action Button States**:
- **Resume**: Visible only when status is PAUSED
- **Cancel**: Visible for active statuses, disabled on final wave
- **Terminate Instances**: Visible only for terminal states with jobId, hidden if already terminated
- **Instances Terminated Badge**: Shown when instances have been terminated

**API Integration**:
- `GET /executions/{id}` - Get execution details with wave progress
- `POST /executions/{id}/resume` - Resume paused execution
- `DELETE /executions/{id}` - Cancel running execution
- `POST /executions/{id}/terminate-instances` - Terminate recovery instances
- `GET /executions/{id}/termination-status` - Poll termination job status

---

## Settings Modal (Accessible from Top Navigation)

**Build Requirements**: Create comprehensive application settings interface with tag synchronization configuration

**Trigger**: Gear icon in top navigation bar opens modal

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Settings                                          [✕ Close] │
├─────────────────────────────────────────────────────────────┤
│ [General] [Tag Sync] [Account Management]                   │
├─────────────────────────────────────────────────────────────┤
│ Tag Sync Configuration:                                     │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Automated Synchronization                               │ │
│ │                                                         │ │
│ │ Schedule: [Every 1 hour        ▼]                      │ │
│ │ Options: 15min, 30min, 1hr, 2hr, 4hr, 8hr, 12hr, 24hr │ │
│ │                                                         │ │
│ │ Status: ✅ Enabled - Next sync in 23 minutes           │ │
│ │ Last sync: Dec 13, 2025 10:30 AM (6 servers updated)   │ │
│ │                                                         │ │
│ │ EventBridge Rule: aws-drs-orchestrator-tag-sync-dev    │ │
│ │ Security Status: ✅ Multi-layer validation active      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Manual Synchronization                                  │ │
│ │                                                         │ │
│ │ Trigger immediate tag sync across all regions           │ │
│ │                                                         │ │
│ │ [🔄 Sync Now]  [📊 View Sync History]                  │ │
│ │                                                         │ │
│ │ Progress: ████████████████████████████████████ 100%    │ │
│ │ Status: Completed - 28 regions processed               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Security Audit Trail                                    │ │
│ │                                                         │ │
│ │ EventBridge Security Validation: ✅ Active              │ │
│ │ - Source IP validation                                  │ │
│ │ - Request structure validation                          │ │
│ │ - Authentication header validation                      │ │
│ │ - Rule name validation                                  │ │
│ │                                                         │ │
│ │ Last 5 EventBridge Requests:                           │ │
│ │ • 10:30 AM - SUCCESS - Rule: tag-sync-schedule-dev     │ │
│ │ • 09:30 AM - SUCCESS - Rule: tag-sync-schedule-dev     │ │
│ │ • 08:30 AM - SUCCESS - Rule: tag-sync-schedule-dev     │ │
│ │                                                         │ │
│ │ [📋 View Full Audit Log]                               │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                                    [Cancel] [Save Changes] │
└─────────────────────────────────────────────────────────────┘
```

**Tag Sync Tab Requirements**:
- **Schedule Configuration**: Dropdown with predefined intervals (15min to 24hr)
- **Real-time Status**: Display current schedule status, next execution time, last sync results
- **Manual Trigger**: Immediate sync button with progress tracking and loading states
- **Security Validation Display**: Show EventBridge security validation status and audit trail
- **Sync History**: Access to detailed sync operation history and results
- **Progress Tracking**: Real-time progress bars during manual sync operations
- **Error Handling**: Comprehensive error display with retry options

**Security Features**:
- **Multi-layer Validation Status**: Display active security validation layers
- **Audit Trail Access**: Show recent EventBridge requests with security validation results
- **Rule Status Monitoring**: Display EventBridge rule health and configuration
- **Attack Prevention Logging**: Show blocked invalid requests (if any)

**API Integration**:
- `PUT /settings/tag-sync-schedule` - Configure sync schedule
- `POST /tag-sync/trigger` - Manual sync trigger with progress tracking
- `GET /settings/tag-sync-status` - Get current sync status and history
- `GET /settings/security-audit` - Get EventBridge security audit trail

**Required Implementation Details**:
- **Real-time Updates**: Poll sync status every 3 seconds during active operations
- **Form Validation**: Validate schedule intervals and configuration
- **Loading States**: Show loading indicators for all async operations
- **Error Recovery**: Provide retry mechanisms for failed operations
- **Settings Persistence**: Save configuration changes immediately
- **Security Monitoring**: Display security validation status in real-time

---

## Common Implementation Patterns

### Required Layout Structure
All protected pages must use:
```typescript
<ProtectedRoute>
  <AppLayout>
    <ContentLayout header={<Header>}>
      <SpaceBetween size="l">
        {/* Page content */}
      </SpaceBetween>
    </ContentLayout>
  </AppLayout>
</ProtectedRoute>
```

### Required Error Handling
- CloudScape Alert components for errors
- Toast notifications for success/failure
- Loading states with Spinner components

### Required Real-time Updates
- Active executions: 3-second polling
- Dashboard metrics: 30-second refresh
- Auto-pause during user interactions (dialogs)

### Required Navigation
- React Router with programmatic navigation
- Breadcrumbs for deep pages
- Back buttons where appropriate

---

## Build Status

**Build Requirements**: Implement all 7 pages with the following specifications:
- Responsive design with CloudScape components
- Real-time updates and polling capabilities
- Comprehensive error handling and loading states
- AWS Console-consistent user experience