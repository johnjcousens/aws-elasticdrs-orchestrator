# Page Specifications
# AWS DRS Orchestration System

**Version**: 4.0  
**Status**: Production Ready

---

## Overview

This document provides complete specifications for all 8 pages in the AWS DRS Orchestration system. Each page specification includes detailed layouts, wireframes, required components, behaviors, and implementation requirements.

**Technology Stack**: React 19.1.1 + TypeScript 5.9.3 + AWS CloudScape Design System 3.0.1148

---

## 1. Login Page (`/login`)

### Purpose
Cognito-based authentication with password reset capability for new users.

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    [AWS Logo]                               │
│              AWS DRS Orchestration                          │
│                                                             │
│     ┌───────────────────────────────────────────┐           │
│     │  Sign In                                  │           │
│     │                                           │           │
│     │  Username                                 │           │
│     │  [_________________________________]      │           │
│     │                                           │           │
│     │  Password                                 │           │
│     │  [_________________________________]      │           │
│     │                                           │           │
│     │  [Sign In]                                │           │
│     │                                           │           │
│     │  Forgot password? [Reset]                 │           │
│     └───────────────────────────────────────────┘           │
│                                                             │
│  © 2024 Amazon Web Services, Inc. or its affiliates        │
└─────────────────────────────────────────────────────────────┘
```

### Features
- Cognito User Pool authentication
- Password reset for temporary passwords
- Auto-redirect for authenticated users
- Error handling with CloudScape Alert
- Session management with 45-minute timeout

### Components Used
- CloudScape: Form, FormField, Input, Button, Alert
- PasswordChangeForm (for password reset workflow)

---

## 2. Dashboard Page (`/`)

### Purpose
Operational dashboard showing real-time execution status, metrics, and system health.

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Dashboard                                    [Refresh]      │
│ Real-time execution status and system metrics              │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │ Active   │ │Completed │ │ Failed   │ │ Success  │        │
│ │Executions│ │    15    │ │    2     │ │  Rate    │        │
│ │    3     │ │          │ │          │ │   88%    │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────────────┐ ┌──────────────────────┐          │
│ │ Execution Status     │ │ Active Executions    │          │
│ │                      │ │                      │          │
│ │   [Donut Chart]      │ │ ● Plan A (Running)   │          │
│ │                      │ │   Wave 2/5           │          │
│ │ Completed: 15 (75%)  │ │                      │          │
│ │ Failed: 2 (10%)      │ │ ● Plan B (Paused)    │          │
│ │ In Progress: 3 (15%) │ │   Wave 1/3           │          │
│ │                      │ │                      │          │
│ │                      │ │ [View all →]         │          │
│ └──────────────────────┘ └──────────────────────┘          │
├─────────────────────────────────────────────────────────────┤
│ DRS Capacity                    [Sync Tags] [Region: All ▼]│
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Replicating Servers: 45/300 (15%)  [████░░░░░░░░░░░░]  │ │
│ │ Concurrent Jobs: 2/20 (10%)        [██░░░░░░░░░░░░░░]  │ │
│ │ Servers in Jobs: 12/500 (2%)       [█░░░░░░░░░░░░░░░]  │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Features
- **Real-time Metrics**: 4-column metric cards (Active, Completed, Failed, Success Rate)
- **Execution Status Chart**: Interactive donut chart with hover details
- **Active Executions List**: 5 most recent with wave progress
- **DRS Capacity Panel**: Progress bars showing quota utilization
- **Tag Sync Button**: Trigger EC2 → DRS tag synchronization
- **Auto-refresh**: 30-second intervals for live updates
- **Region Selector**: Filter capacity by region or view all

### Interactive Elements
- Refresh button (manual refresh)
- Sync Tags button (triggers tag sync)
- Region selector dropdown
- Clickable execution items (navigate to details)
- View all link (navigate to Executions page)

### Components Used
- CloudScape: Container, Header, ColumnLayout, PieChart, ProgressBar, Button
- StatusBadge, DateTimeDisplay, DRSQuotaStatusPanel
- RegionSelector, AccountSelector

---

## 3. Getting Started Page (`/getting-started`)

### Purpose
3-step onboarding guide for new users.

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Getting Started                                             │
│ Follow these steps to set up your DR orchestration          │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Step 1: Configure Account                               │ │
│ │ Set up your AWS account for DRS orchestration           │ │
│ │ [Configure Account →]                                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Step 2: Create Protection Groups                        │ │
│ │ Group your servers for coordinated recovery             │ │
│ │ [Create Protection Group →]                             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Step 3: Build Recovery Plans                            │ │
│ │ Define wave-based recovery strategies                   │ │
│ │ [Create Recovery Plan →]                                │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Features
- Interactive step-by-step guide
- Progress tracking
- Direct links to setup actions
- Account setup wizard integration

---

## 4. Protection Groups Page (`/protection-groups`)

### Purpose
Manage DRS protection groups (logical server groupings).

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Protection Groups                          [Create Group]   │
│ Logical groupings of DRS source servers                    │
├─────────────────────────────────────────────────────────────┤
│ [Search groups...                                        ]  │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Actions ▼│ Name        │ Region    │ Tags │ Created    │ │
│ ├──────────┼─────────────┼───────────┼──────┼────────────┤ │
│ │ [Edit ▼] │ Web-Tier    │ us-east-1 │  3   │ Dec 1      │ │
│ │ [Edit ▼] │ App-Tier    │ us-east-1 │  2   │ Dec 2      │ │
│ │ [Edit ▼] │ DB-Primary  │ us-west-2 │  4   │ Dec 3      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Showing 3 of 3 groups                    [1] [2] [3] [>]   │
└─────────────────────────────────────────────────────────────┘
```

### Features
- **Table View**: Full-page table with protection groups
- **CRUD Operations**: Create, Edit, Delete with permission checks
- **Tag-based Selection**: Support for tag criteria or explicit server IDs
- **Search/Filter**: Real-time text filtering
- **Pagination**: 10 items per page
- **Conflict Detection**: Warn if group is in active execution
- **Usage Tracking**: Show which recovery plans use each group

### Table Columns
- Actions (Edit/Delete dropdown)
- Name
- Description
- Region
- Selection Tags (count)
- Server Count
- Created Date

### Interactive Elements
- Create Group button (opens ProtectionGroupDialog)
- Edit button (opens dialog with group data)
- Delete button (shows confirmation dialog)
- Text filter input
- Pagination controls

### Components Used
- CloudScape: Table, Header, Button, TextFilter, Pagination, ButtonDropdown
- ProtectionGroupDialog, ConfirmDialog
- PermissionAwareButton, DateTimeDisplay

---

## 5. Recovery Plans Page (`/recovery-plans`)

### Purpose
Define multi-wave recovery strategies with protection group orchestration.

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Recovery Plans                              [Create Plan]   │
│ Wave-based recovery orchestration strategies               │
├─────────────────────────────────────────────────────────────┤
│ [Search plans...                                         ]  │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Actions ▼│ Plan Name │ Plan ID │ Waves │ Status │ Last │ │
│ ├──────────┼───────────┼─────────┼───────┼────────┼──────┤ │
│ │ [Run ▼]  │ DR-Prod   │ abc123  │ 3/5   │ Ready  │ 2h   │ │
│ │ [Run ▼]  │ DR-Test   │ def456  │ 2/3   │ ⚠ Conf │ 1d   │ │
│ │ [Run ▼]  │ DR-Dev    │ ghi789  │ 5/5   │ Ready  │ 3d   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Showing 3 of 3 plans                     [1] [2] [3] [>]   │
└─────────────────────────────────────────────────────────────┘
```

### Features
- **Table View**: Full-page table with recovery plans
- **CRUD Operations**: Create, Edit, Delete, Execute
- **Wave Configuration**: Multi-wave setup with dependencies
- **Execution Actions**: Run Drill, Run Recovery (future)
- **Status Tracking**: Last execution status and timestamp
- **Conflict Detection**: Warn if servers are in active execution
- **Existing Instances Check**: Confirm before drill if instances exist
- **Wave Progress**: Show current/total waves during execution
- **Plan ID Copy**: Copy-to-clipboard for plan ID

### Table Columns
- Actions (Run Drill/Recovery, Edit, Delete)
- Plan Name
- Plan ID (with copy button)
- Waves (current/total with progress)
- Status (with conflict warnings)
- Last Start time
- Last End time
- Created Date

### Interactive Elements
- Create Plan button (opens RecoveryPlanDialog)
- Run Drill button (checks for existing instances, then executes)
- Run Recovery button (disabled - future feature)
- Edit button (opens dialog with plan data)
- Delete button (shows confirmation)
- Copy Plan ID button
- Text filter input
- Pagination controls

### Components Used
- CloudScape: Table, Header, Button, TextFilter, Pagination, ButtonDropdown, Badge, CopyToClipboard
- RecoveryPlanDialog, ConfirmDialog, Modal
- PermissionAwareButton, StatusBadge, DateTimeDisplay

---

## 6. Executions Page (`/executions`)

### Purpose
Real-time monitoring and historical records of DR executions.

### Layout - Active Tab
```
┌─────────────────────────────────────────────────────────────┐
│ Executions                                    [Refresh]     │
│ Monitor active and historical DR executions                │
├─────────────────────────────────────────────────────────────┤
│ [Active] [History]                                          │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ DR-Prod Execution                          [View Details]│ │
│ │ Status: Running  │  Wave: 2/5  │  Started: 10:30 AM     │ │
│ │ Duration: 15m 32s                                        │ │
│ │ [████████████░░░░░░░░░░░░░░░░░░] 40%                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ DR-Test Execution                          [View Details]│ │
│ │ Status: Paused   │  Wave: 1/3  │  Started: 9:15 AM      │ │
│ │ Duration: 1h 45m                                         │ │
│ │ [████████░░░░░░░░░░░░░░░░░░░░░░] 33%                    │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Layout - History Tab
```
┌─────────────────────────────────────────────────────────────┐
│ Executions                                    [Refresh]     │
│ Monitor active and historical DR executions                │
├─────────────────────────────────────────────────────────────┤
│ [Active] [History]                                          │
├─────────────────────────────────────────────────────────────┤
│ [Last Hour] [Last 6 Hours] [Today] [Last 3 Days] [Custom]  │
│                                                             │
│ From: [2024-12-01] To: [2024-12-15]  [Clear] [Clear History]│
│                                                             │
│ [Search executions...                                    ]  │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ☐│Plan Name│Status   │Source│Type │Waves│Started│Ended │ │
│ ├──┼─────────┼─────────┼──────┼─────┼─────┼───────┼──────┤ │
│ │ ☐│DR-Prod  │Completed│UI    │Drill│ 5/5 │10:30  │11:45 │ │
│ │ ☐│DR-Test  │Failed   │API   │Drill│ 2/3 │09:15  │09:30 │ │
│ │ ☐│DR-Dev   │Completed│UI    │Drill│ 3/3 │08:00  │08:45 │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ 3 selected                               [1] [2] [3] [>]   │
└─────────────────────────────────────────────────────────────┘
```

### Features
- **Tabbed Interface**: Active / History tabs
- **Active Executions**: Container cards with progress bars
- **History Table**: Full-page table with execution records
- **Date Filtering**: Quick filters (Last Hour, Last 6 Hours, Today, Last 3 Days, Last Week, Last Month)
- **Custom Date Range**: Date picker for custom ranges
- **Bulk Deletion**: Multi-select for deleting execution records
- **Live Updates**: Auto-polling every 3 seconds for active executions
- **Wave Progress**: Current/total waves with percentage
- **Duration Calculation**: Real-time duration display
- **Invocation Source**: Badge showing how execution was triggered (UI, API, Scheduled)

### Active Tab Features
- Container cards for each execution
- Status badge (Running, Paused, Pending)
- Wave progress (2/5)
- Start time and duration
- Progress bar with percentage
- View Details button

### History Tab Features
- Full-page table
- Multi-select checkboxes
- Quick filter buttons
- Custom date range inputs
- Clear filter button
- Clear History button (bulk delete)
- Text search
- Pagination (10 items per page)

### Table Columns (History)
- Checkbox (multi-select)
- Plan Name
- Status
- Invocation Source (UI/API/Scheduled)
- Recovery Type (Drill/Recovery)
- Waves (current/total)
- Started timestamp
- Completed timestamp

### Interactive Elements
- Refresh button (manual refresh)
- Quick filter buttons
- Date range inputs
- Clear filter button
- Clear History button
- View Details links
- Multi-select checkboxes
- Text filter input
- Pagination controls

### Components Used
- CloudScape: Tabs, Container, Table, Button, DateInput, FormField, ProgressBar, Badge, TextFilter, Pagination
- StatusBadge, InvocationSourceBadge, DateTimeDisplay
- PermissionAwareButton, ConfirmDialog

---

## 7. Execution Details Page (`/executions/:id`)

### Purpose
Detailed view of a specific execution with full wave and server monitoring.

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to Executions                                        │
│                                                             │
│ DR-Prod Execution                                           │
│ Execution ID: abc-123-def-456                               │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │ Status   │ │ Wave     │ │ Started  │ │ Duration │        │
│ │ Running  │ │  2/5     │ │ 10:30 AM │ │  15m 32s │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
├─────────────────────────────────────────────────────────────┤
│ Actions: [Pause] [Cancel] [Terminate Instances]            │
├─────────────────────────────────────────────────────────────┤
│ Wave Progress                                               │
│                                                             │
│ ▼ Wave 1: Web Tier (Completed)                             │
│   ├─ web-server-01 ✓ Completed (5m 23s)                    │
│   ├─ web-server-02 ✓ Completed (5m 45s)                    │
│   └─ web-server-03 ✓ Completed (6m 12s)                    │
│                                                             │
│ ▼ Wave 2: Application Tier (Running)                       │
│   ├─ app-server-01 ⟳ Running (2m 15s)                      │
│   ├─ app-server-02 ⟳ Running (2m 18s)                      │
│   └─ app-server-03 ⏸ Pending                               │
│                                                             │
│ ▶ Wave 3: Database Tier (Pending)                          │
│ ▶ Wave 4: Cache Tier (Pending)                             │
│ ▶ Wave 5: Load Balancer (Pending)                          │
├─────────────────────────────────────────────────────────────┤
│ DRS Job Events                                              │
│                                                             │
│ ▼ app-server-01 (Job: job-abc123)                          │
│   10:32:15 - Job started                                    │
│   10:32:45 - Launching recovery instance                    │
│   10:33:12 - Instance launched: i-xyz789                    │
│   10:34:30 - Replication in progress (45%)                  │
│                                                             │
│ ▼ app-server-02 (Job: job-def456)                          │
│   10:32:18 - Job started                                    │
│   10:32:50 - Launching recovery instance                    │
│   10:33:15 - Instance launched: i-abc456                    │
└─────────────────────────────────────────────────────────────┘
```

### Features
- **Execution Overview**: Status, wave progress, timing, duration
- **Action Controls**: Pause, Resume, Cancel, Terminate Instances
- **Wave Progress**: Collapsible sections for each wave
- **Server Status**: Individual server progress with icons
- **DRS Job Events**: Collapsible event logs per server
- **Real-time Updates**: Auto-refresh every 3 seconds
- **Duration Tracking**: Live duration calculation
- **Error Display**: Show errors and failure reasons

### Wave Display
- Expandable/collapsible sections
- Wave name and status
- Server list with status icons:
  - ✓ Completed (green)
  - ⟳ Running (blue spinner)
  - ⏸ Pending (grey)
  - ✗ Failed (red)
- Duration per server

### DRS Job Events
- Collapsible per server
- Chronological event list
- Timestamps
- Event descriptions
- Job IDs

### Interactive Elements
- Back button (navigate to Executions page)
- Pause button (pause execution)
- Resume button (resume paused execution)
- Cancel button (cancel execution with confirmation)
- Terminate Instances button (terminate recovery instances with confirmation)
- Expand/collapse wave sections
- Expand/collapse job event sections
- Refresh button

### Components Used
- CloudScape: Container, Header, ColumnLayout, Button, ExpandableSection, StatusIndicator, Spinner
- StatusBadge, DateTimeDisplay
- PermissionAwareButton, ConfirmDialog, TerminateInstancesDialog

---

## 8. Execution Details Page - Minimal (`/executions/:id/minimal`)

### Purpose
Simplified view of execution details for embedded or minimal UI contexts.

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│ DR-Prod Execution                                           │
│ Status: Running  │  Wave: 2/5  │  Duration: 15m 32s         │
├─────────────────────────────────────────────────────────────┤
│ Wave 1: Web Tier ✓                                          │
│ Wave 2: Application Tier ⟳                                  │
│ Wave 3: Database Tier ⏸                                     │
│ Wave 4: Cache Tier ⏸                                        │
│ Wave 5: Load Balancer ⏸                                     │
└─────────────────────────────────────────────────────────────┘
```

### Features
- Compact execution summary
- Wave status list
- No collapsible sections
- No action buttons
- Suitable for embedding

---

## Modal Dialogs

### Protection Group Dialog

See detailed specification in [Component Library](./UX_COMPONENT_LIBRARY.md#protectiongroupdialog).

### Recovery Plan Dialog

See detailed specification in [Component Library](./UX_COMPONENT_LIBRARY.md#recoveryp
landialog).

### Settings Modal

See detailed specification in [Component Library](./UX_COMPONENT_LIBRARY.md#settingsmodal).

---

## Cross-Page Features

### Account Context
All pages (except Login) require account selection and display current account in header.

### Permission-Based UI
All action buttons check permissions and show disabled state with tooltip for insufficient permissions.

### Real-time Updates
Dashboard and Executions pages implement auto-refresh with configurable intervals.

### Error Handling
All pages implement error boundaries, loading states, and user-friendly error messages.

### Navigation
Breadcrumbs and back buttons provide clear navigation paths.

---

## Related Documentation

- [Component Library](./UX_COMPONENT_LIBRARY.md) - Complete component specifications
- [Visual Design System](./UX_VISUAL_DESIGN_SYSTEM.md) - Colors, typography, spacing
- [Technology Stack](./UX_TECHNOLOGY_STACK.md) - Dependencies and setup

---

**Document Version**: 4.0 - Comprehensive update with all 8 pages, modal dialogs, and interactive features
