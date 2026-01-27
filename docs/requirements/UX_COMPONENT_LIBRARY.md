# Component Library

## AWS DRS Orchestration System

**Version**: 2.2  
**Status**: Production Ready

---

## Overview

This document specifies all 37 custom components required to build the AWS DRS Orchestration application. Each component must follow CloudScape design patterns and AWS Console conventions for consistent user experience.

---

## Layout Components (2)

### AppLayout (`cloudscape/AppLayout.tsx`)
**Build Requirements**: Create wrapper for CloudScape AppLayout component
- Must handle navigation, breadcrumbs, notifications
- Integrate with AuthContext and routing
- Provide consistent layout structure for all pages

### ContentLayout (`cloudscape/ContentLayout.tsx`)
**Build Requirements**: Create page content wrapper with header
- Must provide consistent spacing and structure
- Required by all protected pages
- Include proper CloudScape header integration

---

## Account Management (4)

### AccountSelector (`AccountSelector.tsx`)
**Build Requirements**: Create multi-account switching dropdown
- Must integrate with AccountContext
- Show current account or "Select Account" placeholder
- Handle account switching with proper state management

### AccountManagementPanel (`AccountManagementPanel.tsx`)
**Build Requirements**: Create complete account setup interface
- Must support add/edit/delete target accounts
- Include cross-account role configuration
- Provide validation and error handling

### AccountRequiredGuard (`AccountRequiredGuard.tsx`)
**Build Requirements**: Create conditional rendering component
- Must detect account configuration status
- Show setup instructions when no accounts configured
- Handle loading and error states

### AccountRequiredWrapper (`AccountRequiredWrapper.tsx`)
**Build Requirements**: Create wrapper for account-dependent features
- Must handle loading states and error conditions
- Provide fallback UI for missing account configuration
- Integrate with account management flow

---

## Server Management (4)

### ServerDiscoveryPanel (`ServerDiscoveryPanel.tsx`)
**Build Requirements**: Create DRS server discovery interface
- Must support discovery across all AWS regions
- Implement real-time search and filtering
- Include server selection with conflict detection

### ServerSelector (`ServerSelector.tsx`)
**Build Requirements**: Create advanced server selection interface with multi-mode support

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Server Selection                                            │
├─────────────────────────────────────────────────────────────┤
│ 3 of 12 servers selected          [Select All] [Deselect] │
│                                                             │
│ [Search servers by hostname, ID, or tags...              ] │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ☑ web-server-01 (i-abc123)                             │ │
│ │   🏷 Environment: Production  🏷 Tier: Web              │ │
│ │                                                         │ │
│ │ ☐ app-server-01 (i-def456)                             │ │
│ │   🏷 Environment: Production  🏷 Tier: Application      │ │
│ │                                                         │ │
│ │ ☑ db-server-01 (i-ghi789)                              │ │
│ │   🏷 Environment: Production  🏷 Tier: Database         │ │
│ │   🏷 Protection Group: DB-Primary                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Multi-Protection Group Mode:                                │
│ Servers from: DB-Primary (4), DB-Secondary (3), Web (5)    │
└─────────────────────────────────────────────────────────────┘
```

**Required Features**:
- **Multi-protection-group support**: Handle servers from multiple protection groups
- **Search and filtering**: Real-time search by hostname, ID, or tag values
- **Bulk selection**: Select All/Deselect All functionality
- **Server metadata display**: Show server details, tags, and protection group assignment
- **Conflict detection**: Prevent selection of servers already assigned elsewhere
- **Tag-based mode detection**: Automatic handling of tag-based vs explicit selection
- **Loading states**: Handle async server loading with proper error handling
- **Readonly mode**: Support read-only display for review purposes

### ServerListItem (`ServerListItem.tsx`)
**Build Requirements**: Create individual server display component
- Must show server details, status, region information
- Include action buttons for server operations
- Provide consistent server representation

### LaunchConfigSection (`LaunchConfigSection.tsx`)
**Build Requirements**: Create DRS launch configuration management
- Must handle instance type, subnet, security group settings
- Integrate with DRS API for configuration updates
- Provide form validation and error handling

---

## Dialog Components (4)

### ProtectionGroupDialog (`ProtectionGroupDialog.tsx`)
**Build Requirements**: Create protection group creation/editing modal with advanced server selection

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Create Protection Group                           [✕ Close] │
├─────────────────────────────────────────────────────────────┤
│ Name: [________________________________]                   │
│ Description: [________________________]                     │
│ Region: [us-east-1 ▼] (disabled in edit mode)             │
│                                                             │
│ Server Selection:                                           │
│ [Select Servers] [Select by Tags] ← Tabbed Interface       │
│                                                             │
│ ┌─ Select Servers Tab ─────────────────────────────────────┐│
│ │ [ServerDiscoveryPanel with search and selection]        ││
│ │ ☐ server-1 (i-abc123) - Available                      ││
│ │ ☐ server-2 (i-def456) - Available                      ││
│ │ ☑ server-3 (i-ghi789) - Selected                       ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌─ Select by Tags Tab ─────────────────────────────────────┐│
│ │ Server Selection Tags:                    [+ Add Tag]   ││
│ │ ┌─────────────────────────────────────────────────────┐ ││
│ │ │ Tag Key      │ Tag Value     │ Actions             │ ││
│ │ │ [DR-Tier    ]│ [Database    ]│ [×]                 │ ││
│ │ │ [Environment]│ [Production  ]│ [×]                 │ ││
│ │ │ [_________  ]│ [___________]│ [×]                 │ ││
│ │ └─────────────────────────────────────────────────────┘ ││
│ │                                                         ││
│ │ Matching Servers:                      [🔄 Preview]    ││
│ │ ┌─────────────────────────────────────────────────────┐ ││
│ │ │ • server-db-1 (i-abc123) - Database Tier           │ ││
│ │ │ • server-db-2 (i-def456) - Database Tier           │ ││
│ │ │ 2 servers match these tags                          │ ││
│ │ └─────────────────────────────────────────────────────┘ ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Launch Settings: (Optional)                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [LaunchConfigSection with instance type, subnet, etc.] │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│                                    [Cancel] [Create Group] │
└─────────────────────────────────────────────────────────────┘
```

**Required Features**:
- **Tabbed server selection**: Toggle between explicit server selection and tag-based selection
- **Tag editor**: Dynamic add/remove tag rows with key-value pairs
- **Server preview**: Real-time preview of servers matching tag criteria
- **Launch configuration**: Optional DRS launch settings (instance type, subnet, security groups)
- **Validation**: Form validation with field-specific error messages
- **Conflict detection**: Check for server assignment conflicts with other protection groups
- **Optimistic locking**: Version conflict handling for concurrent edits

### RecoveryPlanDialog (`RecoveryPlanDialog.tsx`)
**Build Requirements**: Create recovery plan creation/editing modal with wave configuration

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Create Recovery Plan                              [✕ Close] │
├─────────────────────────────────────────────────────────────┤
│ Basic Information:                                          │
│ Plan Name: [_________________________________]             │
│ Description: [___________________________]                 │
│                                                             │
│ Wave Configuration:                                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [WaveConfigEditor - see detailed wireframe below]      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Validation Messages:                                        │
│ ⚠ Wave 2 has no servers selected                          │
│ ⚠ Wave 3 exceeds DRS limit (150 servers, max 100)        │
│                                                             │
│                                      [Cancel] [Create Plan] │
└─────────────────────────────────────────────────────────────┘
```

**Required Features**:
- **Basic information form**: Plan name and description with validation
- **Embedded wave editor**: Full WaveConfigEditor component integration
- **Real-time validation**: DRS service limits validation (max 100 servers per wave)
- **Protection group integration**: Load and validate available protection groups
- **Dependency validation**: Prevent circular dependencies between waves
- **Optimistic locking**: Version conflict handling for concurrent edits

### ConfirmDialog (`ConfirmDialog.tsx`)
**Build Requirements**: Create reusable confirmation dialog
- Must support customizable title, message, actions
- Include loading states for async operations
- Provide consistent confirmation pattern

### ImportResultsDialog (`ImportResultsDialog.tsx`)
**Build Requirements**: Create configuration import results display
- Must show success/failure summary
- Include detailed error reporting
- Provide clear feedback on import operations

---

## Authentication Components (1)

### PasswordChangeForm (`PasswordChangeForm.tsx`)
**Build Requirements**: Create Cognito password change interface for NEW_PASSWORD_REQUIRED challenge

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Change Password                          │
├─────────────────────────────────────────────────────────────┤
│ Your password needs to be changed before you can continue. │
│                                                             │
│ User: admin@example.com                                     │
│                                                             │
│ New Password:                                               │
│ [••••••••••••••••••••••••••••••••••••••••••••••••••••••] │
│ Password must be at least 8 characters with uppercase,     │
│ lowercase, number, and special character                    │
│                                                             │
│ Confirm New Password:                                       │
│ [••••••••••••••••••••••••••••••••••••••••••••••••••••••] │
│                                                             │
│ ⚠ Passwords do not match                                   │
│                                                             │
│                                    [Cancel] [Change Password] │
└─────────────────────────────────────────────────────────────┘
```

**Required Features**:
- **Password validation**: Enforce Cognito password policy (8+ chars, uppercase, lowercase, number, special character)
- **Confirmation matching**: Real-time validation that passwords match
- **Cognito integration**: Handle NEW_PASSWORD_REQUIRED challenge with confirmSignIn
- **Error handling**: Display validation errors and API errors
- **Loading states**: Show loading during password change operation
- **Auto-focus**: Focus on new password field when component loads
- **Form submission**: Support both button click and form submit events

---

## Permission Management (4)

### PermissionAwareButton (`PermissionAware.tsx`)
**Build Requirements**: Create permission-controlled button component
- Must integrate with PermissionsContext
- Disable button when user lacks required permissions
- Show tooltip explaining missing permissions
- Support single permission or multiple permission requirements

### PermissionWrapper (`PermissionAware.tsx`)
**Build Requirements**: Create conditional rendering wrapper
- Must show/hide content based on user permissions
- Support fallback content for unauthorized users
- Option to show disabled version instead of hiding
- Handle loading states during permission checks

### PermissionSection (`PermissionAware.tsx`)
**Build Requirements**: Create section-level permission control
- Must hide entire sections when permissions missing
- Support fallback content for unauthorized sections
- Clean conditional rendering without layout shifts
- Integrate with role-based access control

### PermissionAwareButtonDropdown (`PermissionAware.tsx`)
**Build Requirements**: Create permission-controlled dropdown menu
- Must filter menu items based on user permissions
- Disable items when permissions missing
- Show permission tooltips on disabled items
- Support complex permission requirements per item

---

## Configuration Management (3)

### ConfigExportPanel (`ConfigExportPanel.tsx`)
**Build Requirements**: Create configuration export interface
- Must export protection groups and recovery plans
- Support JSON format with metadata
- Include download functionality

### ConfigImportPanel (`ConfigImportPanel.tsx`)
**Build Requirements**: Create configuration import interface
- Must import configuration from JSON files
- Include validation and conflict resolution
- Support batch import with progress tracking

### TagSyncConfigPanel (`TagSyncConfigPanel.tsx`)
**Build Requirements**: Create scheduled tag synchronization configuration interface

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Tag Synchronization                    [Reset] [Save Changes] │
├─────────────────────────────────────────────────────────────┤
│ Configure automatic synchronization of EC2 instance tags   │
│ to DRS source servers                                       │
│                                                             │
│ Scheduled Sync:                    Current Status:          │
│ ● Enabled                          ✅ Active                │
│                                                             │
│ Sync Interval:                     Schedule Expression:     │
│ [4 hours        ▼]                 rate(4 hours)           │
│                                                             │
│                                    EventBridge Rule:        │
│                                    tag-sync-schedule-dev    │
│                                                             │
│                                    Last Modified:           │
│                                    Dec 13, 2025 10:30 AM   │
│                                                             │
│ ℹ About Tag Synchronization                                │
│ Scheduled tag sync automatically copies tags from EC2      │
│ instances to their corresponding DRS source servers.       │
│ Manual tag sync via "Sync Tags" button continues to work   │
│ regardless of scheduled sync settings.                     │
└─────────────────────────────────────────────────────────────┘
```

**Required Features**:
- **Schedule configuration**: Enable/disable scheduled sync with interval selection (1-24 hours)
- **Real-time status**: Display current sync status and EventBridge rule information
- **Form validation**: Validate configuration changes before saving
- **API integration**: Load and save tag sync settings via REST API
- **Error handling**: Display configuration errors with retry options
- **Reset functionality**: Revert changes to current saved settings
- **Loading states**: Show loading during configuration operations

---

## Configuration Management (2)

### ConfigExportPanel (`ConfigExportPanel.tsx`)
**Build Requirements**: Create configuration export interface
- Must export protection groups and recovery plans
- Support JSON format with metadata
- Include download functionality

### ConfigImportPanel (`ConfigImportPanel.tsx`)
**Build Requirements**: Create configuration import interface
- Must import configuration from JSON files
- Include validation and conflict resolution
- Support batch import with progress tracking

---

## Status & Progress (6)

### StatusBadge (`StatusBadge.tsx`)
**Build Requirements**: Create execution status display component
- Must map status to CloudScape badge types with colors
- Provide consistent status representation
- Support all execution status values

### InvocationSourceBadge (`InvocationSourceBadge.tsx`)
**Build Requirements**: Create execution source display component
- Must show execution source (UI, API, CLI, etc.)
- Include color-coded badges for different sources
- Provide tooltip with additional context

### WaveProgress (`WaveProgress.tsx`)
**Build Requirements**: Create wave-by-wave execution progress component
- Must show progress bars and status indicators
- Support real-time updates during execution
- Display wave completion status

### ExecutionDetails (`ExecutionDetails.tsx`)
**Build Requirements**: Create comprehensive execution information component
- Must display metadata, progress, wave details
- Integrate with real-time polling
- Support all execution states

### DRSQuotaStatus (`DRSQuotaStatus.tsx`)
**Build Requirements**: Create DRS service limits monitoring component
- Must show progress bars for capacity usage
- Support region-specific quota display
- Include real-time quota updates

### DateTimeDisplay (`DateTimeDisplay.tsx`)
**Build Requirements**: Create consistent date/time formatting component
- Must provide relative time display (e.g., "2 hours ago")
- Include timezone handling
- Support multiple date formats

---

## Form Components (2)

### WaveConfigEditor (`WaveConfigEditor.tsx`)
**Build Requirements**: Create comprehensive wave configuration interface with expandable sections

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Wave Configuration                            [+ Add Wave]  │
├─────────────────────────────────────────────────────────────┤
│ ▼ Wave 1 [2 PGs] [5 servers]              [↑] [↓] [×]      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Basic Information:                                      │ │
│ │ Wave Name: [Database Tier____________]                  │ │
│ │ Description: [Primary database servers_____________]    │ │
│ │                                                         │ │
│ │ Execution Configuration:                                │ │
│ │ ℹ All servers launch in parallel with 15s delays      │ │
│ │ Depends On Waves: [☐ Wave 0] (multi-select)           │ │
│ │ ☐ Pause execution before starting this wave            │ │
│ │                                                         │ │
│ │ Protection Groups: (Required)                           │ │
│ │ [☑ DB-Primary] [☑ DB-Secondary] [☐ DB-Backup]         │ │
│ │ ℹ Multiple Protection Groups selected                   │ │
│ │                                                         │ │
│ │ Server Selection:                                       │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ Tag-based Protection Groups selected                │ │ │
│ │ │ Servers resolved dynamically at execution time     │ │ │
│ │ │ No manual server selection needed                   │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ▶ Wave 2 [1 PG] [3 servers]               [↑] [↓] [×]      │
│                                                             │
│ ▶ Wave 3 [0 PGs] [0 servers]              [↑] [↓] [×]      │
│                                                             │
│ Validation:                                                 │
│ ⚠ Wave 3 has no Protection Groups selected                 │
│ ⚠ Wave 2 exceeds DRS limit (150 servers, max 100)        │
└─────────────────────────────────────────────────────────────┘
```

**Required Features**:
- **Expandable wave sections**: Click to expand/collapse individual wave configuration
- **Wave management**: Add, remove, reorder waves with up/down arrows
- **Multi-protection-group selection**: Support multiple PGs per wave with multi-select
- **Dependency management**: Visual dependency selection preventing circular dependencies
- **Pause configuration**: Checkbox to pause execution before wave (except Wave 1)
- **Tag-based vs explicit selection**: Automatic detection of tag-based PGs
- **Real-time validation**: DRS service limits and configuration validation
- **Server count display**: Live server count per wave in collapsed headers
- **Progressive disclosure**: Show complex configuration only when expanded

### RegionSelector (`RegionSelector.tsx`)
**Build Requirements**: Create AWS region selection dropdown
- Must include DRS-supported regions only (28 commercial regions)
- Show region display names and codes
- Support region filtering and search

---

## UI State Components (6)

### LoadingState (`LoadingState.tsx`)
**Build Requirements**: Create consistent loading indicators
- Must provide spinner with optional message
- Support different loading sizes
- Use across all async operations

### ErrorState (`ErrorState.tsx`)
**Build Requirements**: Create error display with retry options
- Must provide consistent error messaging
- Include retry functionality
- Integrate with error boundaries

### ErrorBoundary (`ErrorBoundary.tsx`)
**Build Requirements**: Create React error boundary implementation
- Must catch and display component errors
- Provide fallback UI for error recovery
- Include error reporting capabilities

### ErrorFallback (`ErrorFallback.tsx`)
**Build Requirements**: Create error boundary fallback component
- Must show user-friendly error messages
- Include reset functionality
- Provide error details when needed

### CardSkeleton (`CardSkeleton.tsx`)
**Build Requirements**: Create loading skeleton for card components
- Must match card layout structure
- Provide smooth loading transitions
- Support different card sizes

### DataTableSkeleton (`DataTableSkeleton.tsx`)
**Build Requirements**: Create loading skeleton for data tables
- Must match table structure
- Support configurable row count
- Provide realistic loading appearance

---

## Navigation & Routing (3)

### ProtectedRoute (`ProtectedRoute.tsx`)
**Build Requirements**: Create authentication guard for routes
- Must redirect to login if not authenticated
- Handle loading states during authentication check
- Support role-based access control

### PageTransition (`PageTransition.tsx`)
**Build Requirements**: Create smooth page transitions
- Must provide loading states between routes
- Include error handling for route changes
- Support transition animations

### SettingsModal (`SettingsModal.tsx`)
**Build Requirements**: Create comprehensive application settings interface with tabbed configuration

**Required Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Settings                                          [✕ Close] │
├─────────────────────────────────────────────────────────────┤
│ [Account Management] [Tag Sync] [Export] [Import]           │
├─────────────────────────────────────────────────────────────┤
│ Tag Sync Configuration: (Active Tab)                       │
│                                                             │
│ ┌─ Automated Synchronization ─────────────────────────────┐ │
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
│ ┌─ Manual Synchronization ─────────────────────────────────┐ │
│ │ Trigger immediate tag sync across all regions           │ │
│ │                                                         │ │
│ │ [🔄 Sync Now]  [📊 View Sync History]                  │ │
│ │                                                         │ │
│ │ Progress: ████████████████████████████████████ 100%    │ │
│ │ Status: Completed - 28 regions processed               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─ Security Audit Trail ───────────────────────────────────┐ │
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
│                                                             │
│                                    [Cancel] [Save Changes] │
└─────────────────────────────────────────────────────────────┘
```

**Required Features**:
- **Permission-based tabs**: Show Export/Import tabs only if user has appropriate permissions
- **Tag sync configuration**: EventBridge schedule configuration with interval selection
- **Manual sync triggers**: Immediate synchronization with progress tracking
- **Security audit display**: Show EventBridge security validation status and logs
- **Real-time status**: Display current sync schedule and next execution time
- **Progress tracking**: Live progress bars during manual sync operations
- **Settings persistence**: Save configuration changes immediately
- **Error handling**: Comprehensive error display with retry options

**API Integration**:
- `PUT /settings/tag-sync-schedule` - Configure sync schedule
- `POST /tag-sync/trigger` - Manual sync trigger with progress tracking
- `GET /settings/tag-sync-status` - Get current sync status and history
- `GET /settings/security-audit` - Get EventBridge security audit trail

---

## Component Implementation Patterns

### Required CloudScape Integration
All components must use CloudScape design system:
```typescript
import { Button, Modal, FormField } from '@cloudscape-design/components';
```

### Required Event Handling
CloudScape event pattern must be used:
```typescript
onChange={({ detail }) => setValue(detail.value)}
```

### Required Error Handling
Consistent error display pattern:
```typescript
{error && <Alert type="error">{error}</Alert>}
```

### Required Loading States
Standard loading pattern must be implemented:
```typescript
{loading ? <Spinner /> : <Content />}
```

---

## Build Requirements Summary

**Component Development**: Build all 37 components with the following requirements:
- CloudScape design system integration
- Consistent error handling and loading states
- Real-time updates and polling capabilities where needed
- TypeScript type safety throughout
- AWS Console-consistent user experience

---

## Development Guidelines

When building components:
1. Follow CloudScape design patterns exactly
2. Include proper TypeScript types for all props
3. Add error boundaries where appropriate
4. Implement loading states for async operations
5. Use consistent naming conventions
6. Ensure accessibility compliance
7. Include comprehensive error handling