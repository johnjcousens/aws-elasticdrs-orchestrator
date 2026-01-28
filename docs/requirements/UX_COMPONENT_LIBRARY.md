# Component Library - Comprehensive
# AWS DRS Orchestration System

**Version**: 4.0  
**Status**: Production Ready

---

## Overview

This document specifies all 40+ components required for the AWS DRS Orchestration application, including modal dialogs, forms, interactive controls, and data visualization components.

---

## Modal Dialogs (7)

### 1. ProtectionGroupDialog

**Purpose**: Create/Edit protection groups with tag-based or explicit server selection.

**Tabs**:
1. **Select Servers Tab**: Explicit server selection via ServerDiscoveryPanel
2. **Select by Tags Tab**: Tag-based selection with preview

**Form Fields**:
- Name (required, 1-128 characters)
- Description (optional, textarea)
- Region (required, immutable after creation)
- Server selection mode (tabs)
- Launch configuration (expandable section)

**Tag Selection Features**:
- Add/Remove tag key-value pairs
- Preview matching servers button
- Shows server details (ID, state, IP, replication status)
- Validates at least one tag required

**Launch Configuration Section**:
- Subnet selection (dropdown)
- Security groups (multi-select)
- Instance type (dropdown)
- Instance profile (dropdown)
- Copy private IP (checkbox)
- Copy tags (checkbox)
- Licensing (BYOL checkbox)

**Validation**:
- Name required and unique
- Region required
- At least one tag or server required
- Conflict detection for duplicate names
- Server conflict detection (in active execution)

**Buttons**:
- Cancel
- Create Group / Update Group (primary, permission-gated)

---

### 2. RecoveryPlanDialog

**Purpose**: Create/Edit recovery plans with multi-wave configuration.

**Sections**:
1. **Basic Information**:
   - Plan Name (required, 1-128 characters)
   - Description (optional, textarea)

2. **Wave Configuration**:
   - WaveConfigEditor component
   - Add Wave button
   - Wave list with expandable sections

**Wave Configuration Features** (via WaveConfigEditor):
- Wave name and description
- Protection group multi-select
- Server selection (if non-tag-based PGs)
- Wave dependencies
- Pause before wave checkbox
- Move wave up/down buttons
- Remove wave button
- Expandable sections per wave

**Validation**:
- Plan name required and unique
- At least one wave required
- All waves must have protection group
- Wave size limits (max 100 servers per wave)
- DRS concurrent job limits (max 20)

**Buttons**:
- Cancel
- Create Plan / Update Plan (primary, permission-gated)

---

### 3. SettingsModal

**Purpose**: Configuration and account management hub.

**Tabs** (permission-gated):
1. **Account Management**: Multi-account configuration (always visible)
2. **Tag Sync**: EC2 tag synchronization settings (always visible)
3. **Export Configuration**: Export protection groups and recovery plans (requires export permission)
4. **Import Configuration**: Import configuration from JSON (requires import permission)

**Account Management Tab**:
- AccountManagementPanel component
- Add/Edit/Delete target accounts
- Cross-account role configuration
- Account validation

**Tag Sync Tab**:
- TagSyncConfigPanel component
- Enable/disable tag sync
- Schedule configuration (1-24 hours)
- Last sync status
- Manual sync trigger

**Export Tab**:
- ConfigExportPanel component
- Select items to export
- Download as JSON

**Import Tab**:
- ConfigImportPanel component
- Upload JSON file
- Preview import
- Confirm import
- Show results dialog

**Buttons**: Varies by tab (Save, Export, Import, etc.)

---

### 4. ConfirmDialog

**Purpose**: Generic confirmation dialog for destructive actions.

**Props**:
- title (string)
- message (string)
- confirmLabel (string, default: "Confirm")
- cancelLabel (string, default: "Cancel")
- onConfirm (function)
- onDismiss (function)
- loading (boolean)

**Used For**:
- Delete confirmations
- Cancel execution
- Clear history
- Destructive actions

---

### 5. TerminateInstancesDialog

**Purpose**: Confirm termination of recovery instances.

**Features**:
- Lists instances to be terminated
- Shows instance IDs and states
- Confirmation required
- Warning message about data loss

**Buttons**:
- Cancel
- Terminate Instances (destructive, red)

---

### 6. ImportResultsDialog

**Purpose**: Show results of configuration import.

**Features**:
- Summary of imported items
- Success/failure counts
- Error messages for failed imports
- List of successfully imported items

**Buttons**:
- Close

---

### 7. ExistingInstancesDialog

**Purpose**: Warn about existing recovery instances before drill execution.

**Features**:
- Lists existing recovery instances
- Shows instance IDs and states
- Warning about potential conflicts
- Option to terminate existing instances first

**Buttons**:
- Cancel
- Continue Anyway
- Terminate and Continue

---

## Form Components (8)

### 1. WaveConfigEditor

**Purpose**: Configure recovery waves within a plan.

**Features**:
- Add/Remove waves
- Move waves up/down (reorder)
- Wave name and description
- Protection group multi-select
- Server selection (conditional on PG type)
- Wave dependencies
- Pause before wave toggle
- Expandable sections for each wave

**Wave Fields**:
- Wave Name (required)
- Description (optional)
- Protection Groups (multi-select, required)
- Servers (multi-select, conditional)
- Pause Before Wave (checkbox)

**Validation**:
- Wave name required
- Protection group required
- Servers required (if non-tag-based PG)
- Wave size limits (max 100 servers)

---

### 2. ServerSelector

**Purpose**: Select servers for a wave from protection groups.

**Features**:
- Server list from selected protection groups
- Multi-select checkboxes
- Server status indicators
- Replication state display
- Lag duration display
- Assigned protection group display
- Search/filter by hostname or ID

**Server Display**:
- Checkbox
- Server ID
- Hostname
- Replication state (icon + text)
- Lag duration
- Protection group badge
- IP addresses

---

### 3. ServerDiscoveryPanel

**Purpose**: Discover and select DRS servers in a region.

**Features**:
- Auto-discovery of servers
- Region-specific
- Server status filtering
- Replication state indicators
- Multi-select checkboxes
- Pagination
- Search/filter
- Refresh button

**Server Display**:
- Checkbox
- Server ID
- Hostname
- State (icon + text)
- Replication state
- Lag duration
- IP addresses
- Instance type

---

### 4. LaunchConfigSection

**Purpose**: Configure EC2 launch settings for recovery instances.

**Fields**:
- Subnet (dropdown, required)
- Security Groups (multi-select, required)
- Instance Type (dropdown, optional - uses source if not specified)
- Instance Profile (dropdown, optional)
- Copy Private IP (checkbox)
- Copy Tags (checkbox)
- Licensing (BYOL checkbox)

**Features**:
- Expandable section
- EC2 resource discovery (subnets, security groups, instance profiles)
- Validation
- Help text for each field

---

### 5. TagSyncConfigPanel

**Purpose**: Configure EC2 tag synchronization.

**Fields**:
- Enable Tag Sync (toggle)
- Sync Schedule (dropdown: 1h, 6h, 12h, 24h)
- Last Sync Status (read-only)
- Last Sync Time (read-only)

**Features**:
- Manual sync trigger button
- Status indicators
- Error display
- Schedule validation

---

### 6. ConfigExportPanel

**Purpose**: Export configuration to JSON.

**Features**:
- Select items to export (checkboxes):
  - Protection Groups
  - Recovery Plans
  - Target Accounts
  - Tag Sync Configuration
- Select All / Deselect All
- Export button
- Download as JSON file

---

### 7. ConfigImportPanel

**Purpose**: Import configuration from JSON.

**Features**:
- File upload (drag-and-drop or browse)
- JSON validation
- Preview import (shows items to be imported)
- Conflict detection
- Import button
- Results dialog after import

---

### 8. PasswordChangeForm

**Purpose**: User password change form.

**Fields**:
- Current Password (password input, required)
- New Password (password input, required)
- Confirm Password (password input, required)

**Validation**:
- Current password required
- New password requirements (8+ chars, uppercase, lowercase, number, special char)
- Passwords must match

---

## Interactive Components (15)

### 1. StatusBadge

**Purpose**: Display execution/plan/server status with color coding.

**Statuses**:
- completed (green)
- failed (red)
- in_progress / running / polling (blue)
- paused (orange)
- cancelled (grey)
- pending (grey)

**Features**:
- Color-coded background
- Status text
- Icon (optional)

---

### 2. InvocationSourceBadge

**Purpose**: Show how execution was triggered.

**Sources**:
- UI (user-initiated from web interface)
- API (triggered via API call)
- Scheduled (EventBridge scheduled trigger)
- Manual (direct Lambda invocation)

**Features**:
- Icon for each source type
- Tooltip with details (user, timestamp, trigger info)
- Color coding

---

### 3. DRSQuotaStatusPanel

**Purpose**: Display DRS capacity and quota information.

**Features**:
- Capacity per region or account-wide
- Progress bars for each quota:
  - Replicating Servers (current/limit)
  - Concurrent Jobs (current/limit)
  - Servers in Jobs (current/limit)
- Usage percentage
- Quota warnings (>80% usage)
- Region selector
- Refresh button

---

### 4. WaveProgress

**Purpose**: Show wave execution progress.

**Features**:
- Current wave number
- Total waves
- Progress percentage
- Progress bar
- Status indicator

---

### 5. PermissionAwareButton

**Purpose**: Button with permission checking.

**Features**:
- Disabled state for insufficient permissions
- Tooltip explaining required permission
- Permission prop (DRSPermission enum)
- All standard button props

---

### 6. PermissionAwareButtonDropdown

**Purpose**: Dropdown with permission-gated items.

**Features**:
- Filter items by permission
- Disabled items with tooltip
- Permission per item
- All standard dropdown props

---

### 7. AccountSelector

**Purpose**: Select AWS account for multi-account support.

**Features**:
- Dropdown with account list
- Current account display
- "Select Account" placeholder
- Account switching with state management
- Integration with AccountContext

---

### 8. RegionSelector

**Purpose**: Select AWS region.

**Features**:
- Dropdown with available regions
- All 30 DRS-enabled regions
- Current region display
- Region switching

---

### 9. DateTimeDisplay

**Purpose**: Format and display timestamps.

**Formats**:
- Full: "December 15, 2024 10:30:45 AM"
- Short: "Dec 15, 10:30 AM"
- Relative: "2 hours ago"
- Date only: "December 15, 2024"

**Features**:
- Timezone handling
- Relative time updates
- Tooltip with full timestamp

---

### 10. ServerListItem

**Purpose**: Display individual server information.

**Fields**:
- Server ID
- Hostname
- State (icon + text)
- Replication state
- Lag duration
- IP addresses (private, public)
- Instance type
- Protection group (if assigned)

**Features**:
- Expandable details
- Status icons
- Color coding

---

### 11. AccountRequiredWrapper

**Purpose**: Wrapper for account-dependent features.

**Features**:
- Detects account configuration
- Shows setup instructions if no account
- Loading state
- Error state
- Children rendered when account available

---

### 12. AccountRequiredGuard

**Purpose**: Conditional rendering based on account.

**Features**:
- Renders children only if account selected
- Shows message if no account
- Integration with AccountContext

---

### 13. ProtectedRoute

**Purpose**: Route protection based on authentication.

**Features**:
- Redirects to login if not authenticated
- Preserves intended destination
- Integration with AuthContext

---

### 14. ErrorBoundary

**Purpose**: Catch React errors.

**Features**:
- Error display
- Stack trace (dev mode)
- Recovery options
- Fallback UI

---

### 15. LoadingState

**Purpose**: Loading indicator.

**Features**:
- Spinner
- Loading message (optional)
- Centered layout

---

## Data Visualization Components (5)

### 1. PieChart (CloudScape)

**Used in**: Dashboard

**Features**:
- Donut variant
- Interactive segments
- Hover details
- Legend
- Percentage display
- Color coding

**Data**: Execution status breakdown

---

### 2. ProgressBar (CloudScape)

**Used in**: Executions page, wave progress, DRS quotas

**Features**:
- Percentage display
- Variant options (default, flash, success, error)
- Label
- Description

---

### 3. StatusIndicator (CloudScape)

**Used in**: Throughout app

**Types**:
- success (green checkmark)
- error (red X)
- warning (orange exclamation)
- in-progress (blue spinner)
- stopped (grey circle)
- pending (grey clock)

---

### 4. Badge (CloudScape)

**Used in**: Status displays, counts, tags

**Colors**:
- Green (success, completed)
- Blue (info, in-progress)
- Red (error, failed)
- Orange (warning, paused)
- Grey (neutral, cancelled)

---

### 5. ExpandableSection (CloudScape)

**Used in**: Wave progress, DRS job events, launch config

**Features**:
- Expand/collapse animation
- Header with count/status
- Nested content
- Default expanded/collapsed state

---

## Layout Components (10)

### 1. ContentLayout

**Purpose**: Main page layout wrapper.

**Features**:
- Header with title and description
- Breadcrumbs
- Content area
- Consistent spacing

---

### 2. PageTransition

**Purpose**: Page transition animations.

**Features**:
- Fade-in animation on page load
- Smooth transitions
- Configurable duration

---

### 3. ErrorState

**Purpose**: Error display component.

**Features**:
- Error message
- Error icon
- Retry button (optional)
- Centered layout

---

### 4. CardSkeleton

**Purpose**: Skeleton loading for cards.

**Features**:
- Placeholder animation
- Matches card dimensions
- Multiple variants

---

### 5. DataTableSkeleton

**Purpose**: Skeleton loading for tables.

**Features**:
- Placeholder rows and columns
- Animation
- Configurable row count

---

### 6. ErrorFallback

**Purpose**: Error boundary fallback UI.

**Features**:
- Error message
- Stack trace (dev mode)
- Reload button
- Report error button

---

### 7. AccountManagementPanel

**Purpose**: Multi-account configuration interface.

**Features**:
- Add/Edit/Delete accounts
- Cross-account role configuration
- Account validation
- Table view of accounts
- Form for account details

---

### 8. ConfirmDialog

**Purpose**: Generic confirmation dialog.

**Features**:
- Customizable title and message
- Confirm/Cancel buttons
- Loading state
- Destructive variant (red confirm button)

---

### 9. ImportResultsDialog

**Purpose**: Show import results.

**Features**:
- Success/failure counts
- Error messages
- List of imported items
- Close button

---

### 10. TerminateInstancesDialog

**Purpose**: Confirm instance termination.

**Features**:
- List of instances
- Warning message
- Confirm/Cancel buttons
- Loading state

---

## Context Providers (6)

### 1. AccountContext

**Provides**:
- selectedAccount
- accountList
- setSelectedAccount
- getCurrentAccountId
- refreshAccounts

**Purpose**: Multi-account management

---

### 2. AuthContext

**Provides**:
- user
- isAuthenticated
- login
- logout
- refreshSession

**Purpose**: Authentication state

---

### 3. NotificationContext

**Provides**:
- addNotification (success, error, info, warning)

**Purpose**: Toast notifications

---

### 4. PermissionsContext

**Provides**:
- hasPermission(permission)
- userRoles
- userPermissions

**Purpose**: RBAC permission checking

---

### 5. SettingsContext

**Provides**:
- settings
- updateSettings
- resetSettings

**Purpose**: User settings management

---

### 6. ApiContext

**Provides**:
- apiClient

**Purpose**: API client configuration

---

## Utility Components (5)

### 1. CopyToClipboard (CloudScape)

**Purpose**: Copy text to clipboard.

**Features**:
- Copy button
- Success feedback
- Tooltip

---

### 2. DateInput (CloudScape)

**Purpose**: Date picker input.

**Features**:
- Calendar popup
- Date validation
- Format: YYYY-MM-DD

---

### 3. Multiselect (CloudScape)

**Purpose**: Multi-select dropdown.

**Features**:
- Search/filter
- Select all/none
- Token display
- Placeholder

---

### 4. Textarea (CloudScape)

**Purpose**: Multi-line text input.

**Features**:
- Resizable
- Character count
- Validation

---

### 5. Checkbox (CloudScape)

**Purpose**: Checkbox input.

**Features**:
- Label
- Description
- Disabled state
- Indeterminate state

---

## Related Documentation

- [Page Specifications](./UX_PAGE_SPECIFICATIONS.md) - Complete page layouts and wireframes
- [Visual Design System](./UX_VISUAL_DESIGN_SYSTEM.md) - Colors, typography, spacing
- [Technology Stack](./UX_TECHNOLOGY_STACK.md) - Dependencies and setup

---

**Document Version**: 4.0 - Comprehensive component library with all 40+ components, modal dialogs, and interactive features
