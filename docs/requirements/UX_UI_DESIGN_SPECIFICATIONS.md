# UX/UI Design Specifications

## AWS DRS Orchestration System

**Version**: 2.0  
**Date**: December 2025  
**Status**: Production Release

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
- Tabs (content organization)
- ProgressBar (execution progress)
- ColumnLayout, Container (content structure)

---

## Application Structure

### Navigation

The application uses CloudScape AppLayout with a top navigation bar:

- Logo and application name (DR Orchestrator)
- Main navigation links: Dashboard, Protection Groups, Recovery Plans, History
- User menu with sign out option

### Routes

| Route | Page | Description |
|-------|------|-------------|
| /login | LoginPage | Cognito authentication |
| / | Dashboard | Overview metrics and quick actions (default landing) |
| /getting-started | GettingStartedPage | Onboarding guide with quick links |
| /protection-groups | ProtectionGroupsPage | Protection Group management |
| /protection-groups/new | ProtectionGroupsPage | Create new Protection Group |
| /recovery-plans | RecoveryPlansPage | Recovery Plan management |
| /recovery-plans/new | RecoveryPlansPage | Create new Recovery Plan |
| /executions | ExecutionsPage | Execution list with Active/History tabs |
| /executions/:executionId | ExecutionDetailsPage | Real-time execution monitoring |

---

## Page Specifications

### 1. Login Page

**Purpose**: Authenticate users via AWS Cognito

**Components**:

- CloudScape Container with centered layout
- CloudScape Input for username/password
- CloudScape Button (variant primary)
- CloudScape Alert for error messages

**Behavior**:

- Submit on Enter key
- Show loading spinner during authentication
- Display error message on failure
- Redirect to Getting Started page on success

### 2. Getting Started Page

**Purpose**: Onboarding guide for new users

**Layout**: Three-column grid with quick links plus Quick Start Guide

**Components**:

- CloudScape ContentLayout with Header
- CloudScape ColumnLayout (3 columns)
- CloudScape Container for each section
- Quick Start Guide container with 3-step workflow

**Content**:

- Step 1: Create a Protection Group
- Step 2: Design a Recovery Plan
- Step 3: Execute Recovery

### 3. Dashboard Page

**Purpose**: Overview of system status and quick actions

**Components**:

- CloudScape Cards for metrics
- CloudScape Button for quick actions
- Recent executions summary

### 4. Protection Groups Page

**Purpose**: CRUD operations for Protection Groups

**Components**:

- CloudScape Table with collection hooks
- CloudScape Header with Create and Refresh buttons
- CloudScape Modal for create/edit dialog

**Table Columns**: Name, Region, Servers, Created, Actions

**Create/Edit Dialog**:

- Name input field (required)
- Region selector dropdown (13 AWS regions)
- Description field (optional)
- Server selector with real-time search and assignment status

### 5. Recovery Plans Page

**Purpose**: CRUD operations for Recovery Plans

**Components**:

- CloudScape Table with collection hooks
- CloudScape Header with Create and Refresh buttons
- CloudScape Modal for create/edit dialog

**Table Columns**: Name, Protection Groups, Waves, Servers, Created, Actions

**Create/Edit Dialog**:

- Plan name and description fields
- Protection Group multi-select
- Wave configuration editor

### 6. Executions Page (History)

**Purpose**: List and monitor recovery executions

**Components**:

- CloudScape Tabs (Active / History)
- CloudScape Table for history list
- CloudScape Container cards for active executions
- CloudScape ProgressBar for in-progress executions
- CloudScape Badge for live updates indicator

**Status Indicators**: PENDING, POLLING, LAUNCHING, COMPLETED, FAILED, CANCELLED

### 7. Execution Details Page

**Purpose**: Real-time execution monitoring

**Components**:

- CloudScape Header with back navigation
- CloudScape Container for execution summary
- WaveProgress component showing wave timeline
- CloudScape Table for server status
- CloudScape Button for cancel execution

---

## Component Library (20 components)

| Component | Purpose |
|-----------|---------|
| ProtectionGroupDialog | Create/Edit Protection Groups modal |
| RecoveryPlanDialog | Create/Edit Recovery Plans modal |
| ServerSelector | Visual server selection with assignment status |
| ServerDiscoveryPanel | DRS server discovery interface |
| ServerListItem | Individual server display in lists |
| RegionSelector | AWS region dropdown |
| StatusBadge | Status indicators with color coding |
| WaveProgress | Wave execution timeline visualization |
| WaveConfigEditor | Wave configuration form |
| ConfirmDialog | Confirmation dialogs |
| DateTimeDisplay | Timestamp formatting |
| ExecutionDetails | Execution detail display |
| ErrorBoundary | React error boundary wrapper |
| ErrorFallback | Error display component |
| ErrorState | Error state with retry button |
| LoadingState | Loading spinner with message |
| CardSkeleton | Loading skeleton for cards |
| DataTableSkeleton | Loading skeleton for tables |
| PageTransition | Page transition animations |
| ProtectedRoute | Auth route wrapper |

### CloudScape Layout Components

| Component | Purpose |
|-----------|---------|
| AppLayout | Page shell with navigation |
| ContentLayout | Page content wrapper with header |

---

## User Flows

### Flow 1: Create Protection Group

1. Navigate to Protection Groups page
2. Click Create button
3. Enter name and select region
4. System discovers DRS servers
5. Select available servers
6. Click Create
7. Success notification displayed

### Flow 2: Create Recovery Plan

1. Navigate to Recovery Plans page
2. Click Create button
3. Enter name and description
4. Select Protection Groups
5. Configure waves
6. Click Create

### Flow 3: Execute Recovery

1. Navigate to Recovery Plans page
2. Click Execute button on plan row
3. Select execution type (DRILL or RECOVERY)
4. Confirm execution
5. Redirect to Execution Details page
6. Monitor wave progress

### Flow 4: Monitor Execution

1. Navigate to History page
2. View Active tab for in-progress executions
3. Click View Details
4. View wave progress timeline
5. Auto-refresh updates status every 3 seconds

---

## Responsive Design

| Size | Width | Layout |
|------|-------|--------|
| Desktop | >1200px | Full layout with sidebar |
| Tablet | 768-1200px | Collapsed sidebar |
| Mobile | <768px | Stacked layout, hamburger menu |

---

## Accessibility

### WCAG 2.1 AA Compliance

- Color contrast ratio: 4.5:1 minimum
- Focus indicators on all interactive elements
- Keyboard navigation for all functionality
- Screen reader announcements for status changes

### Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move focus forward |
| Shift+Tab | Move focus backward |
| Enter | Activate button/link |
| Space | Toggle checkbox |
| Escape | Close dialog |

---

## State Management

### React Context

- AuthContext: User authentication state, JWT tokens, login/logout functions

### Data Fetching

- API calls via axios with JWT token
- Loading states during fetch
- Error handling with toast notifications
- Auto-refresh for active executions (3-second interval)
