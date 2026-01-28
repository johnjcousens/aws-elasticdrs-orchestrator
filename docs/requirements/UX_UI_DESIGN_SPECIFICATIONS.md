# UX/UI Design Specifications
# AWS DRS Orchestration System

**Version**: 4.0  
**Status**: Production Ready

---

## Document Purpose

This document serves as the master index for the complete UX/UI specification of the AWS DRS Orchestration platform. It provides an overview of the design system and links to detailed specifications for pages, components, visual design, and technology stack.

---

## Design System Overview

The application uses **React 19.1.1 + TypeScript 5.9.3 + AWS CloudScape Design System 3.0.1148** for AWS Console consistency.

### Key Principles
- AWS Console visual consistency with CloudScape components
- Progressive disclosure (simple → complex workflows)
- Real-time feedback and status updates with optimized polling
- WCAG 2.1 AA accessibility compliance
- Permission-aware UI with RBAC integration
- Multi-account context switching with enforcement

---

## Application Structure

### Pages (8 Total)
1. **Login Page** - Cognito authentication with password reset
2. **Dashboard** - Real-time metrics, donut chart, DRS capacity with tag sync
3. **Getting Started** - 3-step onboarding guide
4. **Protection Groups** - Tag-based or explicit server selection with launch config
5. **Recovery Plans** - Multi-wave configuration with dependencies
6. **Executions** - Active/History tabs with date filtering and bulk operations
7. **Execution Details** - Collapsible waves, server status, DRS job events
8. **Execution Details Minimal** - Simplified embedded view

### Components (40+ Total)
- **7 Modal Dialogs**: ProtectionGroupDialog, RecoveryPlanDialog, SettingsModal, ConfirmDialog, TerminateInstancesDialog, ImportResultsDialog, ExistingInstancesDialog
- **8 Form Components**: WaveConfigEditor, ServerSelector, ServerDiscoveryPanel, LaunchConfigSection, TagSyncConfigPanel, ConfigExportPanel, ConfigImportPanel, PasswordChangeForm
- **15 Interactive Components**: StatusBadge, InvocationSourceBadge, DRSQuotaStatusPanel, WaveProgress, PermissionAwareButton, AccountSelector, RegionSelector, DateTimeDisplay, ServerListItem, and more
- **5 Data Visualization**: PieChart, ProgressBar, StatusIndicator, Badge, ExpandableSection
- **10 Layout Components**: ContentLayout, PageTransition, ErrorState, CardSkeleton, DataTableSkeleton, and more
- **6 Context Providers**: AccountContext, AuthContext, NotificationContext, PermissionsContext, SettingsContext, ApiContext

---

## Detailed Documentation

### [Page Specifications](./UX_PAGE_SPECIFICATIONS.md)
Complete specifications for all 8 pages including:
- Detailed wireframes and layouts
- Feature lists and behaviors
- Interactive elements and controls
- API integration requirements
- Component usage

**Key Pages**:
- **Dashboard**: Real-time metrics with donut chart, DRS capacity panel, tag sync button
- **Protection Groups**: Tag-based selection, launch configuration, server enrichment
- **Recovery Plans**: Wave configuration with dependencies, pause/resume controls
- **Executions**: Active/History tabs, date filtering, bulk operations, live updates
- **Execution Details**: Collapsible waves, DRS job events, pause/resume/cancel/terminate

### [Component Library](./UX_COMPONENT_LIBRARY.md)
Complete specifications for all 40+ components including:
- Modal dialogs with full feature lists
- Form components with validation rules
- Interactive components with state management
- Data visualization components
- Layout and utility components

**Key Components**:
- **ProtectionGroupDialog**: Tag-based or explicit server selection, launch config management
- **RecoveryPlanDialog**: Multi-wave configuration with WaveConfigEditor
- **SettingsModal**: Account Management, Tag Sync, Export/Import tabs
- **WaveConfigEditor**: Add/remove/reorder waves, protection group selection
- **DRSQuotaStatusPanel**: Capacity monitoring with progress bars
- **ServerSelector**: Multi-select with enriched server data

### [Visual Design System](./UX_VISUAL_DESIGN_SYSTEM.md)
Complete visual design specifications including:
- Color palette (AWS brand colors)
- Typography (Amazon Ember font family)
- Spacing and layout grid
- Component styling
- Icon usage
- Accessibility guidelines

### [Technology Stack](./UX_TECHNOLOGY_STACK.md)
Complete technology specifications including:
- Frontend dependencies and versions
- Build tools and configuration
- Development setup
- Testing frameworks
- Deployment process

---

## Key Features

### Dashboard
- **Real-time Metrics**: 4-column cards (Active, Completed, Failed, Success Rate)
- **Execution Status Chart**: Interactive donut chart with hover details
- **DRS Capacity Panel**: Progress bars showing quota utilization per region
- **Tag Sync Button**: Trigger EC2 → DRS tag synchronization
- **Auto-refresh**: 30-second intervals for live updates

### Protection Groups
- **Tag-based Selection**: Define server groups using AWS tags
- **Explicit Selection**: Choose specific servers via ServerDiscoveryPanel
- **Launch Configuration**: Complete EC2 launch settings (subnet, security groups, instance type, etc.)
- **Server Enrichment**: Display server details (ID, state, IP, replication status)
- **Conflict Detection**: Warn if servers are in active execution

### Recovery Plans
- **Multi-wave Configuration**: Define sequential recovery phases
- **Wave Dependencies**: Control execution order
- **Pause Before Wave**: Manual validation points
- **Protection Group Selection**: Multi-select from available groups
- **Server Preview**: View servers in each wave
- **Execution Actions**: Run Drill, Run Recovery (future)

### Executions
- **Active Tab**: Container cards with progress bars and wave status
- **History Tab**: Full table with date filtering and bulk operations
- **Date Filtering**: Quick filters (Last Hour, Last 6 Hours, Today, etc.) and custom range
- **Live Updates**: Auto-polling every 3 seconds for active executions
- **Bulk Deletion**: Multi-select for clearing execution history
- **Invocation Source**: Badge showing how execution was triggered (UI/API/Scheduled)

### Execution Details
- **Wave Progress**: Collapsible sections for each wave with server status
- **Server Status**: Individual server progress with icons (✓ Completed, ⟳ Running, ⏸ Pending, ✗ Failed)
- **DRS Job Events**: Collapsible event logs per server with timestamps
- **Action Controls**: Pause, Resume, Cancel, Terminate Instances
- **Real-time Updates**: Auto-refresh every 3 seconds
- **Duration Tracking**: Live duration calculation

### Settings Modal
- **Account Management**: Add/edit/delete target accounts with cross-account role configuration
- **Tag Sync Configuration**: Enable/disable, schedule (1-24 hours), manual trigger
- **Export Configuration**: Download protection groups and recovery plans as JSON
- **Import Configuration**: Upload and import configuration with preview and validation

---

## Interactive Patterns

### Permission-Based UI
All action buttons check permissions and show disabled state with tooltip for insufficient permissions.

### Real-time Updates
Dashboard and Executions pages implement auto-refresh with configurable intervals (30s for dashboard, 3s for active executions).

### Error Handling
All pages implement error boundaries, loading states, and user-friendly error messages with retry options.

### Multi-Account Context
All pages (except Login) require account selection and display current account in header with account switcher.

### Collapsible Sections
Wave progress and DRS job events use expandable sections for progressive disclosure.

### Bulk Operations
Executions History tab supports multi-select for bulk deletion of execution records.

### Date Filtering
Quick filter buttons (Last Hour, Last 6 Hours, Today, Last 3 Days, Last Week, Last Month) and custom date range picker.

---

## Technology Stack Summary

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.1.1 | UI framework with concurrent features |
| TypeScript | 5.9.3 | Type safety and compile-time optimization |
| CloudScape Design System | 3.0.1148 | AWS-native UI components |
| Vite | 7.1.7 | Build tool and development server |
| React Router | 7.9.5 | Client-side routing with code splitting |
| AWS Amplify | 6.15.8 | Cognito authentication with auto token refresh |
| Axios | 1.13.2 | HTTP client with request/response interceptors |
| react-hot-toast | 2.6.0 | Toast notifications |
| date-fns | 4.1.0 | Date formatting and manipulation |

---

## Related Documentation

- **Requirements**:
  - [Product Requirements Document](./PRODUCT_REQUIREMENTS_DOCUMENT.md)
  - [Software Requirements Specification](./SOFTWARE_REQUIREMENTS_SPECIFICATION.md)
  - [Codebase Analysis](./CODEBASE_ANALYSIS.md)

- **Architecture**:
  - [Architecture Guide](../architecture/ARCHITECTURE.md)
  - [API Endpoints](../reference/API_ENDPOINTS_CURRENT.md)

- **Development**:
  - [Developer Guide](../guides/DEVELOPER_GUIDE.md)
  - [Deployment Guide](../deployment/QUICK_START_GUIDE.md)

---

**Document Version**: 4.0 - Comprehensive UX/UI specification with all pages, components, and interactive features
