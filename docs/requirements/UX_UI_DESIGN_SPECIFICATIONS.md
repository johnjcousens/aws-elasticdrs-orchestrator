# UX/UI Design Specifications
# AWS DRS Orchestration System

**Version**: 2.0  
**Date**: December 2025  
**Status**: Production Release

---

## Document Purpose

This document defines the user interface design for the AWS DRS Orchestration system, including page layouts, component specifications, user flows, and design guidelines.

---

## Design System

### Framework
- **UI Library**: AWS CloudScape Design System
- **React Version**: 18.3
- **TypeScript**: 5.5
- **Build Tool**: Vite 5.4

### Design Principles
1. **AWS Console Consistency**: Match AWS Console patterns for familiarity
2. **Progressive Disclosure**: Simple views by default, reveal complexity on demand
3. **Error Prevention**: Validate inputs proactively, provide clear feedback
4. **Accessibility**: WCAG 2.1 AA compliance, keyboard navigation, screen reader support

### CloudScape Components Used
- AppLayout (page structure with navigation)
- Table (data display with sorting, filtering, pagination)
- Form, FormField, Input, Select (form controls)
- Modal (dialogs)
- Button, SpaceBetween, Box (layout)
- StatusIndicator, Badge (status display)
- Wizard, Steps (multi-step flows)
- Alert, Flashbar (notifications)
- Header, BreadcrumbGroup (navigation)

---

## Application Structure

### Navigation
```
┌─────────────────────────────────────────────────────────────┐
│  [Logo] DR Orchestrator    Dashboard | Protection Groups |  │
│                            Recovery Plans | Executions      │
│                                              [User Menu ▼]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    [Page Content]                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Routes
| Route | Page | Description |
|-------|------|-------------|
| `/login` | LoginPage | Cognito authentication |
| `/` | GettingStartedPage | Onboarding guide |
| `/dashboard` | Dashboard | Overview metrics |
| `/protection-groups` | ProtectionGroupsPage | Protection Group management |
| `/recovery-plans` | RecoveryPlansPage | Recovery Plan management |
| `/executions` | ExecutionsPage | Execution list |
| `/executions/:id` | ExecutionDetailsPage | Execution details |

---

## Page Specifications

### 1. Login Page

**Purpose**: Authenticate users via AWS Cognito

**Layout**:
```
┌─────────────────────────────────────────┐
│                                         │
│         DR Orchestrator                 │
│         AWS DRS Orchestration           │
│                                         │
│     ┌───────────────────────────┐      │
│     │  Username                 │      │
│     │  [__________________]     │      │
│     │                           │      │
│     │  Password                 │      │
│     │  [__________________]     │      │
│     │                           │      │
│     │    [Sign In]              │      │
│     └───────────────────────────┘      │
│                                         │
└─────────────────────────────────────────┘
```

**Components**:
- CloudScape Container with centered layout
- CloudScape Input for username/password
- CloudScape Button (variant="primary")
- CloudScape Alert for error messages

**Behavior**:
- Submit on Enter key
- Show loading spinner during authentication
- Display error message on failure
- Redirect to Dashboard on success

### 2. Getting Started Page

**Purpose**: Onboarding guide for new users

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  Getting Started                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Welcome to DR Orchestrator                                 │
│                                                             │
│  Step 1: Create Protection Groups                           │
│  [Description and link to Protection Groups page]           │
│                                                             │
│  Step 2: Create Recovery Plans                              │
│  [Description and link to Recovery Plans page]              │
│                                                             │
│  Step 3: Execute Recovery                                   │
│  [Description and link to Executions page]                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Components**:
- CloudScape ContentLayout with Header
- CloudScape Container for each step
- CloudScape Link for navigation

### 3. Dashboard Page

**Purpose**: Overview of system status

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard                                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Protection  │  │ Recovery    │  │ Recent      │        │
│  │ Groups: 12  │  │ Plans: 8    │  │ Executions  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  Quick Actions                                              │
│  [Create Protection Group]  [Create Recovery Plan]          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Components**:
- CloudScape Cards for metrics
- CloudScape Button for quick actions

### 4. Protection Groups Page

**Purpose**: CRUD operations for Protection Groups

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  Protection Groups                      [Create] [Refresh]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Name          Region      Servers  Created   Actions │   │
│  │ ─────────────────────────────────────────────────── │   │
│  │ Prod-DB       us-east-1   5        2d ago    [E][D] │   │
│  │ Web-Tier      us-west-2   12       1w ago    [E][D] │   │
│  │ App-Servers   eu-west-1   8        3w ago    [E][D] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Components**:
- CloudScape Table with collection hooks
- CloudScape Header with action buttons
- CloudScape Modal for create/edit dialog
- CloudScape StatusIndicator for server count

**Table Columns**:
| Column | Type | Sortable | Width |
|--------|------|----------|-------|
| Name | Text | Yes | 200px |
| Region | Text | Yes | 120px |
| Servers | Badge | Yes | 100px |
| Created | Date | Yes | 150px |
| Actions | Buttons | No | 100px |

**Create/Edit Dialog**:
```
┌─────────────────────────────────────────────────────────────┐
│  Create Protection Group                              [X]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Name *                                                     │
│  [__________________________]                               │
│                                                             │
│  Region *                                                   │
│  [us-east-1                              ▼]                │
│                                                             │
│  Description                                                │
│  [__________________________]                               │
│                                                             │
│  Select Servers                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [Search servers...]                                  │   │
│  │ ☑ db-prod-01 (s-abc123)           Available         │   │
│  │ ☑ db-prod-02 (s-def456)           Available         │   │
│  │ ☐ app-prod-01 (s-ghi789)          Assigned: Web-PG  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                              [Cancel]  [Create]             │
└─────────────────────────────────────────────────────────────┘
```

**Server Selector Features**:
- Real-time search by hostname or server ID
- Visual assignment status (Available/Assigned)
- Checkbox selection for available servers
- Disabled selection for assigned servers
- 30-second auto-refresh

### 5. Recovery Plans Page

**Purpose**: CRUD operations for Recovery Plans

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  Recovery Plans                         [Create] [Refresh]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Name          PGs  Waves  Servers  Created  Actions │   │
│  │ ─────────────────────────────────────────────────── │   │
│  │ 3-Tier-App    3    3      18       1d ago   [▶][E][D]│   │
│  │ DB-Only       1    1      4        1w ago   [▶][E][D]│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Table Columns**:
| Column | Type | Description |
|--------|------|-------------|
| Name | Text | Plan name |
| PGs | Badge | Protection Group count |
| Waves | Badge | Wave count |
| Servers | Badge | Total server count |
| Created | Date | Creation date |
| Actions | Buttons | Execute, Edit, Delete |

**Create/Edit Dialog**:
- Plan name and description fields
- Protection Group multi-select
- Wave configuration editor
- Server assignment per wave
- Execution type selection (Sequential/Parallel)
- Wait time configuration

### 6. Executions Page

**Purpose**: List and monitor recovery executions

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  Executions                                      [Refresh]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Filters: [Status ▼] [Type ▼]                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Plan          Type    Status      Started   Duration │   │
│  │ ─────────────────────────────────────────────────── │   │
│  │ 3-Tier-App    DRILL   ● Running   5m ago    --      │   │
│  │ DB-Only       DRILL   ✓ Complete  2h ago    15m     │   │
│  │ 3-Tier-App    RECOV   ✗ Failed    1d ago    8m      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Status Indicators**:
| Status | Color | Icon |
|--------|-------|------|
| PENDING | Gray | Clock |
| POLLING | Blue | Refresh |
| LAUNCHING | Blue | Rocket |
| COMPLETED | Green | Checkmark |
| FAILED | Red | X |
| CANCELLED | Gray | Stop |

**Row Click**: Navigate to Execution Details page

### 7. Execution Details Page

**Purpose**: Real-time execution monitoring

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Executions                                       │
│                                                             │
│  Execution: 3-Tier-App                                      │
│  Type: DRILL  |  Status: ● Running  |  Started: 5 min ago  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Wave Progress                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ✓ Wave 1: Database        ● Wave 2: App    ○ Wave 3│   │
│  │    Complete (2/2)            Running (1/3)    Pending│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Server Status                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Server          Wave    Status      Instance ID      │   │
│  │ ─────────────────────────────────────────────────── │   │
│  │ db-prod-01      1       ✓ Complete  i-abc123        │   │
│  │ db-prod-02      1       ✓ Complete  i-def456        │   │
│  │ app-prod-01     2       ● Launching --              │   │
│  │ app-prod-02     2       ○ Pending   --              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [Cancel Execution]                                         │
└─────────────────────────────────────────────────────────────┘
```

**Components**:
- CloudScape Steps for wave progress
- CloudScape Table for server status
- CloudScape StatusIndicator for status display
- Auto-refresh every 5 seconds during execution

---

## Component Library

### Shared Components

| Component | Purpose | Location |
|-----------|---------|----------|
| ProtectionGroupDialog | Create/Edit Protection Groups | components/ |
| RecoveryPlanDialog | Create/Edit Recovery Plans | components/ |
| ServerSelector | Visual server selection | components/ |
| RegionSelector | AWS region dropdown | components/ |
| StatusBadge | Status indicators | components/ |
| WaveProgress | Wave execution timeline | components/ |
| WaveConfigEditor | Wave configuration form | components/ |
| ConfirmDialog | Confirmation dialogs | components/ |
| DateTimeDisplay | Timestamp formatting | components/ |
| ErrorBoundary | Error handling wrapper | components/ |
| LoadingState | Loading indicators | components/ |
| ErrorState | Error display | components/ |
| ProtectedRoute | Auth route wrapper | components/ |

### CloudScape Layout Components

| Component | Purpose | Location |
|-----------|---------|----------|
| AppLayout | Page shell with navigation | components/cloudscape/ |
| ContentLayout | Page content wrapper | components/cloudscape/ |

---

## User Flows

### Flow 1: Create Protection Group
1. Navigate to Protection Groups page
2. Click "Create" button
3. Enter name and select region
4. System discovers DRS servers
5. Select available servers
6. Click "Create"
7. Success notification displayed
8. Table refreshes with new Protection Group

### Flow 2: Create Recovery Plan
1. Navigate to Recovery Plans page
2. Click "Create" button
3. Enter name and select Protection Groups
4. Configure waves (add servers, set execution type)
5. Set wait times between waves
6. Click "Create"
7. Success notification displayed

### Flow 3: Execute Recovery
1. Navigate to Recovery Plans page
2. Click Execute button on plan row
3. Select execution type (DRILL/RECOVERY)
4. Confirm execution
5. Redirect to Execution Details page
6. Monitor wave progress in real-time
7. View completion status

### Flow 4: Monitor Execution
1. Navigate to Executions page
2. Click on execution row
3. View wave progress stepper
4. View server status table
5. Auto-refresh updates status
6. Cancel if needed

---

## Responsive Design

### Breakpoints
| Size | Width | Layout |
|------|-------|--------|
| Desktop | >1200px | Full layout with sidebar |
| Tablet | 768-1200px | Collapsed sidebar |
| Mobile | <768px | Stacked layout, hamburger menu |

### Mobile Adaptations
- Tables scroll horizontally
- Dialogs become full-screen
- Navigation collapses to hamburger menu
- Touch-friendly button sizes (44px minimum)

---

## Accessibility

### WCAG 2.1 AA Compliance
- Color contrast ratio: 4.5:1 minimum
- Focus indicators on all interactive elements
- Keyboard navigation for all functionality
- Screen reader announcements for status changes
- Form labels associated with inputs
- Error messages linked to form fields

### Keyboard Navigation
| Key | Action |
|-----|--------|
| Tab | Move focus forward |
| Shift+Tab | Move focus backward |
| Enter | Activate button/link |
| Space | Toggle checkbox |
| Escape | Close dialog |
| Arrow keys | Navigate within components |

---

## State Management

### React Context
- **AuthContext**: User authentication state, JWT tokens, login/logout functions

### Component State
- Page-level state for data fetching and UI state
- Dialog state (open/close, form values)
- Table state (sorting, filtering, pagination)

### Data Fetching
- API calls via axios with JWT token
- Loading states during fetch
- Error handling with user-friendly messages
- Optimistic updates where appropriate
