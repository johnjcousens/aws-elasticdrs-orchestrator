# UX/UI Design Specifications

## AWS DRS Orchestration System

**Version**: 2.3  
**Date**: January 6, 2026  
**Status**: Production Ready - API Gateway 6-Nested-Stack Architecture Complete  
**Scope**: Complete system specification including API Gateway modular architecture and 42+ endpoint support

---

## Document Purpose

This document serves as the master specification for building the complete UX/UI system. Each section provides detailed specifications that contain all information needed to implement the AWS DRS Orchestration platform from the ground up.

Use this specification to:
- Build a complete React + TypeScript + CloudScape application
- Implement all 32 required components with exact behaviors
- Create all 7 pages with specified layouts and functionality
- Ensure AWS Console consistency and accessibility compliance

---

## Design System Overview

The application uses React 19.1.1 + TypeScript 5.9.3 + AWS CloudScape Design System 3.0.1148 for AWS Console consistency.

**Key Principles**:
- AWS Console visual consistency
- Progressive disclosure (simple → complex)
- Real-time feedback and status updates
- WCAG 2.1 AA accessibility compliance

---

## Specification Documents

### Core Design System
- **[Visual Design System](UX_VISUAL_DESIGN_SYSTEM.md)** - Colors, typography, spacing, icons
- **[Technology Stack](UX_TECHNOLOGY_STACK.md)** - Dependencies, versions, build tools
- **[Component Library](UX_COMPONENT_LIBRARY.md)** - Reusable UI components (32 total)

### Application Architecture
- **[Application Layout](UX_APPLICATION_LAYOUT.md)** - Navigation, routing, authentication flow
- **[Page Specifications](UX_PAGE_SPECIFICATIONS.md)** - All 7 pages with wireframes and behavior

### Implementation Guides
- **[CloudScape Patterns](UX_CLOUDSCAPE_PATTERNS.md)** - AWS-specific UI patterns and best practices
- **[Accessibility Guidelines](UX_ACCESSIBILITY_GUIDELINES.md)** - WCAG compliance and keyboard navigation

---

## Implementation Requirements

| Component | Count | Specification |
|-----------|-------|---------------|
| **Pages** | 7 | Complete page layouts with all functionality |
| **Components** | 36 | Reusable UI components with CloudScape integration |
| **CloudScape Wrappers** | 2 | AppLayout, ContentLayout |
| **Contexts** | 6 | React context providers for state management |
| **Routes** | 7 | React Router configuration with authentication |
| **Technology Stack** | 14 dependencies | Exact versions and build configuration |

## Page Wireframes (From TSX Implementation)

### Dashboard Page
- **Layout**: 4-column metrics grid + 2-column charts/lists
- **Metrics Cards**: Active Executions, Completed, Failed, Success Rate
- **Charts**: Pie chart for execution status distribution
- **Lists**: Active executions (5 items), Recent activity (5 items)
- **DRS Capacity**: Region selector + quota status panel with tag sync button
- **Real-time Updates**: 30-second auto-refresh for executions, DRS quotas

### Protection Groups Page
- **Layout**: Full-page table with header actions
- **Table Columns**: Actions, Name, Description, Region, Selection Tags, Created
- **Actions**: Create Group button (permission-aware)
- **Row Actions**: Edit/Delete dropdown (permission-aware, conflict detection)
- **Filtering**: Text filter with match count
- **Pagination**: CloudScape pagination component
- **Dialog**: ProtectionGroupDialog with tabs (Select Servers vs Select by Tags)

### Recovery Plans Page
- **Layout**: Full-page table with execution status tracking
- **Table Columns**: Actions, Plan Name, ID (copyable), Waves, Status, Last Start/End, Created
- **Actions**: Create Plan button (permission-aware)
- **Row Actions**: Run Drill/Recovery, Edit, Delete (permission-aware, conflict detection)
- **Real-time**: 5-second execution progress updates, existing instances detection
- **Dialog**: RecoveryPlanDialog with wave configuration editor
- **Modals**: Existing instances warning with instance details

### Execution Details Page
- **Layout**: Header with controls + wave progress + job events timeline
- **Controls**: Pause/Resume, Cancel, Terminate Instances (permission-aware)
- **Progress**: Wave-by-wave status with server details
- **Timeline**: DRS job events with auto-refresh
- **Real-time**: 3-second status polling

### Component Wireframes

#### ProtectionGroupDialog
- **Tabs**: "Select Servers" vs "Select by Tags"
- **Server Tab**: Region selector + server discovery panel with checkboxes
- **Tags Tab**: Tag key/value editor + server preview panel
- **Launch Config**: Collapsible section with EC2 settings
- **Validation**: Real-time form validation with error states

#### RecoveryPlanDialog
- **Sections**: Basic Information + Wave Configuration
- **Wave Editor**: Expandable wave cards with PG selection, server assignment
- **Dependencies**: Wave dependency configuration
- **Validation**: DRS limits validation (100 servers/wave)

#### ServerDiscoveryPanel
- **Layout**: Search bar + server list with status indicators
- **Server Items**: Hostname, IP, status badges, hardware details
- **Selection**: Checkboxes with assignment conflict detection
- **Status Colors**: Green (available), Red (assigned), Gray (unavailable)

**Required Pages**: Login, Dashboard, Getting Started, Protection Groups, Recovery Plans, Executions, Execution Details

**Key Components to Build**: AccountSelector, ServerDiscoveryPanel, WaveConfigEditor, ExecutionDetails, DRSQuotaStatus, StatusBadge, InvocationSourceBadge

**React Contexts**: AuthContext, PermissionsContext, NotificationContext, ApiContext, AccountContext, SettingsContext

---

## Build Status

✅ **Specification Complete**: All requirements defined for full system implementation  
✅ **MVP Drill Only Prototype**: Core drill functionality fully specified  
✅ **Build Ready**: Contains all detail needed to implement from scratch  
✅ **Component Count**: 36 components + 2 CloudScape wrappers + 6 contexts fully specified  
✅ **CI/CD**: GitHub Actions with OIDC authentication (migrated from GitLab January 2026)  

---

## Maintenance

Each specification document contains complete implementation details. When building the system:

1. Follow the detailed specification documents in order
2. Implement each component and page as specified
3. Use the exact technology versions and configurations provided
4. Test against the specified behaviors and requirements

This modular approach ensures all specifications are complete and self-contained for implementation.