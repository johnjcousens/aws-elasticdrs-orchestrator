# UX/UI Design Specifications
# AWS DRS Orchestration System

**Version**: 3.0  
**Status**: Production Ready  
**Scope**: Complete frontend specification for React 19 + CloudScape implementation

---

## Document Purpose

This document serves as the complete specification for the UX/UI system based on the actual implemented React frontend. It provides detailed specifications for all 7 pages, 32+ components, and 6 React contexts that comprise the AWS DRS Orchestration platform.

---

## Design System Overview

The application uses React 19.1.1 + TypeScript 5.9.3 + AWS CloudScape Design System 3.0.1148 for AWS Console consistency.

**Key Principles**:
- AWS Console visual consistency with CloudScape components
- Progressive disclosure (simple → complex workflows)
- Real-time feedback and status updates with optimized polling
- WCAG 2.1 AA accessibility compliance
- Permission-aware UI with RBAC integration
- Multi-account context switching with enforcement

**Related Documentation**:
- [Visual Design System](./UX_VISUAL_DESIGN_SYSTEM.md) - Complete color palette, typography, spacing, and branding guidelines
- [Technology Stack](./UX_TECHNOLOGY_STACK.md) - Detailed setup instructions and dependency versions

---

## Technology Stack

### Frontend Dependencies
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

## Application Architecture

**For detailed page specifications with complete layouts, features, and API integration requirements, see [Page Specifications](./UX_PAGE_SPECIFICATIONS.md).**

### Page Structure (7 Pages)

#### 1. LoginPage
**Route**: `/login`
**Purpose**: Cognito authentication with password reset capability

**Features**:
- Cognito User Pool authentication
- Password reset functionality for new users
- Error handling with user-friendly messages
- Automatic redirect after successful authentication
- Support for temporary passwords with forced password change

**Components Used**:
- CloudScape Form, Input, Button components
- PasswordChangeForm for password reset workflow
- Toast notifications for feedback

#### 2. Dashboard
**Route**: `/`
**Purpose**: Executive dashboard with metrics, charts, and real-time monitoring

**Layout**: 4-column metrics grid + 2-column charts/lists

**Features**:
- **Metrics Cards**: Active Executions, Completed, Failed, Success Rate
- **Pie Chart**: Execution status distribution with interactive segments
- **Active Executions List**: 5 most recent with real-time updates
- **Recent Activity List**: 5 most recent actions with timestamps
- **DRS Capacity Panel**: Region selector + quota status with tag sync button
- **Real-time Updates**: 30-second auto-refresh for executions and DRS quotas

**Components Used**:
- CloudScape Cards, ColumnLayout, PieChart
- StatusBadge, DateTimeDisplay, DRSQuotaStatus
- RegionSelector, AccountSelector

#### 3. GettingStartedPage
**Route**: `/getting-started`
**Purpose**: 3-step onboarding guide for new users

**Features**:
- Interactive tutorial with step-by-step guidance
- Account setup wizard integration
- Links to create first Protection Group and Recovery Plan
- Progress tracking through onboarding steps

#### 4. ProtectionGroupsPage
**Route**: `/protection-groups`
**Purpose**: CRUD management for Protection Groups with server selection

**Layout**: Full-page table with header actions and filtering

**Features**:
- **Table Columns**: Actions, Name, Description, Region, Selection Mode, Server Count, Created
- **Actions**: Create Group button (permission-aware)
- **Row Actions**: Edit/Delete dropdown (permission-aware, conflict detection)
- **Filtering**: Text filter with real-time match count
- **Pagination**: CloudScape pagination with configurable page sizes
- **Server Selection**: Dual-mode (Tags vs Explicit Servers) with preview

**Components Used**:
- CloudScape Table with full CRUD operations
- ProtectionGroupDialog with tabbed interface
- ServerDiscoveryPanel, ServerSelector
- RegionSelector, LaunchConfigSection
- PermissionAware components for access control

#### 5. RecoveryPlansPage
**Route**: `/recovery-plans`
**Purpose**: Wave-based Recovery Plan management with execution controls

**Layout**: Full-page table with execution status tracking

**Features**:
- **Table Columns**: Actions, Plan Name, ID (copyable), Waves, Status, Last Execution, Created
- **Actions**: Create Plan button (permission-aware)
- **Row Actions**: Run Drill/Recovery, Edit, Delete (permission-aware, conflict detection)
- **Real-time Updates**: 5-second execution progress updates
- **Existing Instances Detection**: Performance-optimized check with scalable dialog
- **Conflict Detection**: Server conflict validation with detailed information

**Components Used**:
- CloudScape Table with advanced filtering
- RecoveryPlanDialog with WaveConfigEditor
- ExecutionDetails for inline progress
- ConfirmDialog for existing instances warning
- StatusBadge, InvocationSourceBadge

#### 6. ExecutionsPage
**Route**: `/executions`
**Purpose**: Active and historical execution monitoring

**Layout**: Tabbed interface (Active vs History) with bulk operations

**Features**:
- **Active Executions**: Real-time monitoring with 3-second updates
- **Execution History**: Paginated historical view with filtering
- **Bulk Operations**: Selective deletion with confirmation
- **Status Filtering**: Filter by execution status and type
- **Real-time Progress**: Wave-by-wave progress indicators
- **Action Controls**: Pause/Resume/Cancel/Terminate (permission-aware)

**Components Used**:
- CloudScape Tabs, Table with selection
- ExecutionDetails, WaveProgress
- StatusBadge, DateTimeDisplay
- ConfirmDialog for bulk operations

#### 7. ExecutionDetailsPage
**Route**: `/executions/{id}`
**Purpose**: Detailed execution view with wave progress and controls

**Layout**: Header with controls + wave progress + job events timeline

**Features**:
- **Execution Controls**: Pause/Resume, Cancel, Terminate Instances (permission-aware)
- **Wave Progress**: Real-time wave-by-wave status with server details
- **Job Events Timeline**: DRS job events with auto-refresh
- **Real-time Updates**: 3-second status polling for active executions
- **Instance Management**: Terminate recovery instances with progress tracking

**Components Used**:
- CloudScape Header, ColumnLayout
- WaveProgress, ExecutionDetails
- StatusBadge, DateTimeDisplay
- PermissionAware buttons and controls

---

## Component Library (32+ Components)

**For complete component specifications with detailed layouts and implementation requirements, see [Component Library](./UX_COMPONENT_LIBRARY.md).**

### CloudScape Wrappers (2)

#### AppLayout
**Purpose**: Main application layout with navigation
**Features**:
- Consistent AWS Console navigation patterns
- Breadcrumb integration
- Account selector in top navigation
- Responsive sidebar with collapsible sections

#### ContentLayout
**Purpose**: Page content wrapper with consistent spacing
**Features**:
- Standard page header patterns
- Action button placement
- Content area with proper margins

### Multi-Account Management (4)

#### AccountSelector
**Purpose**: Account context switching dropdown
**Features**:
- Top navigation integration
- Real-time account switching
- Visual indication of current account
- Auto-selection for single accounts

#### AccountRequiredWrapper
**Purpose**: Feature enforcement wrapper for multi-account scenarios
**Features**:
- Blocks protected pages when no account selected
- Shows account selection prompt
- Integrates with AccountSelector

#### AccountRequiredGuard
**Purpose**: Route-level account enforcement
**Features**:
- Protects specific routes requiring account context
- Redirects to account selection when needed

#### AccountManagementPanel
**Purpose**: Account configuration and management
**Features**:
- Target account registration
- Cross-account role configuration
- Account health monitoring

### RBAC & Security (3)

#### PermissionAware
**Purpose**: Permission-based conditional rendering
**Features**:
- Wraps components with permission checks
- Supports multiple permission requirements
- Graceful degradation for insufficient permissions

#### PasswordChangeForm
**Purpose**: Secure password change with Cognito integration
**Features**:
- Current password validation
- New password strength requirements
- Cognito API integration
- Error handling and user feedback

#### ProtectedRoute
**Purpose**: Route-level permission enforcement
**Features**:
- Checks user permissions before rendering routes
- Redirects to appropriate error pages
- Integrates with RBAC system

### Server Management (4)

#### ServerSelector
**Purpose**: Server selection with conflict detection
**Features**:
- Checkbox-based server selection
- Real-time conflict detection
- Assignment status indicators (Available/Assigned)
- Hardware details display

#### ServerDiscoveryPanel
**Purpose**: Real-time DRS server discovery
**Features**:
- Region-based server discovery
- Search and filtering capabilities
- Real-time status updates
- Assignment conflict prevention

#### ServerListItem
**Purpose**: Individual server display with hardware details
**Features**:
- Hostname, IP, and hardware information
- Replication status indicators
- Tag display and management
- Expandable details section

#### RegionSelector
**Purpose**: AWS region selection for all 30 DRS regions
**Features**:
- Dropdown with all DRS-supported regions
- Regional grouping (Americas, Europe, Asia Pacific, etc.)
- Real-time region switching

### Execution Management (3)

#### ExecutionDetails
**Purpose**: Real-time execution monitoring
**Features**:
- Wave-by-wave progress tracking
- Server status indicators
- Job ID and timeline integration
- Real-time status updates

#### WaveProgress
**Purpose**: Wave-by-wave progress tracking
**Features**:
- Visual progress indicators
- Server launch status tracking
- Timeline integration
- Error state handling

#### WaveConfigEditor
**Purpose**: Multi-wave configuration editor
**Features**:
- Expandable wave sections
- Protection Group selection per wave
- Dependency configuration
- Validation and error handling

### Configuration Management (4)

#### ConfigExportPanel
**Purpose**: Configuration export functionality
**Features**:
- Export Protection Groups and Recovery Plans
- Portable JSON format generation
- Download functionality
- Export metadata inclusion

#### ConfigImportPanel
**Purpose**: Configuration import with validation
**Features**:
- File upload with drag-and-drop
- JSON validation and preview
- Conflict detection and resolution
- Progress tracking during import

#### TagSyncConfigPanel
**Purpose**: EventBridge tag synchronization configuration
**Features**:
- Schedule configuration (15 minutes to 24 hours)
- Manual trigger capability
- Progress monitoring
- EventBridge rule management

#### LaunchConfigSection
**Purpose**: DRS launch settings configuration
**Features**:
- Instance type right-sizing options
- Launch disposition settings
- Copy private IP and tags options
- OS licensing configuration

### Status & Display (4)

#### StatusBadge
**Purpose**: Execution and server status indicators
**Features**:
- Color-coded status display
- Consistent status mapping
- Tooltip information
- Real-time status updates

#### InvocationSourceBadge
**Purpose**: Execution source tracking
**Features**:
- Visual indicators for execution sources (UI, CLI, API, EventBridge)
- Color-coded source types
- Tooltip with source details

#### DateTimeDisplay
**Purpose**: Consistent date/time formatting
**Features**:
- Relative time display (e.g., "2 hours ago")
- Absolute timestamp on hover
- Timezone handling
- Consistent formatting across application

#### DRSQuotaStatus
**Purpose**: Real-time service limits monitoring
**Features**:
- Current usage vs limits display
- Color-coded status indicators (OK, Warning, Critical)
- Regional quota tracking
- Real-time updates

### Dialogs & Modals (5)

#### ProtectionGroupDialog
**Purpose**: Protection Group CRUD with tabbed interface
**Features**:
- Tabbed server selection (Tags vs Servers)
- Real-time server preview
- Launch configuration section
- Validation and error handling

#### RecoveryPlanDialog
**Purpose**: Recovery Plan CRUD with wave editor
**Features**:
- Wave configuration editor
- Protection Group selection per wave
- Dependency management
- Validation against DRS limits

#### ConfirmDialog
**Purpose**: Confirmation dialogs with context
**Features**:
- Customizable confirmation messages
- Context-specific information
- Action button customization
- Keyboard navigation support

#### ImportResultsDialog
**Purpose**: Configuration import results display
**Features**:
- Import summary with success/failure counts
- Detailed results per item
- Error messages and resolution suggestions
- Export functionality for results

#### SettingsModal
**Purpose**: Application settings management
**Features**:
- Three-tab interface (Export, Import, Tag Sync)
- Account preferences
- Tag synchronization configuration
- Application preferences

### Layout & Utility (6)

#### ErrorBoundary
**Purpose**: Error boundary with fallback UI
**Features**:
- Catches JavaScript errors in component tree
- Displays user-friendly error messages
- Error reporting integration
- Recovery suggestions

#### ErrorFallback
**Purpose**: Error display component
**Features**:
- Consistent error message formatting
- Action buttons for error recovery
- Error details for debugging
- User-friendly error descriptions

#### ErrorState
**Purpose**: Error state display for components
**Features**:
- Empty state handling
- Error message display
- Retry functionality
- Consistent styling

#### LoadingState
**Purpose**: Loading state indicators
**Features**:
- Spinner with customizable size
- Loading messages
- Skeleton loading patterns
- Consistent loading experience

#### CardSkeleton
**Purpose**: Loading skeleton for card components
**Features**:
- Animated loading placeholders
- Card-specific skeleton patterns
- Responsive design
- Smooth loading transitions

#### DataTableSkeleton
**Purpose**: Loading skeleton for table components
**Features**:
- Table-specific skeleton patterns
- Row and column placeholders
- Animated loading effects
- Responsive table skeletons

#### PageTransition
**Purpose**: Smooth page transitions
**Features**:
- Fade-in/fade-out transitions
- Loading state management
- Route change animations
- Performance optimization

### React Contexts (6)

#### AuthContext
**Purpose**: Authentication state management
**Features**:
- Cognito authentication state
- Token management and refresh
- User profile information
- Authentication status tracking

#### PermissionsContext
**Purpose**: RBAC permissions caching
**Features**:
- User permissions caching
- Role-based access control
- Permission checking utilities
- Real-time permission updates

#### NotificationContext
**Purpose**: Toast notification management
**Features**:
- Centralized notification system
- Success, error, warning, info notifications
- Auto-dismiss functionality
- Queue management for multiple notifications

#### ApiContext
**Purpose**: API client configuration
**Features**:
- Axios client configuration
- Request/response interceptors
- Error handling
- Authentication token injection

#### AccountContext
**Purpose**: Multi-account state management
**Features**:
- Current account tracking
- Account switching functionality
- Account validation
- Cross-account context propagation

#### SettingsContext
**Purpose**: Application settings persistence
**Features**:
- User preferences storage
- Settings synchronization
- Default value management
- Settings validation

---

## Performance Optimizations

### Frontend Performance Features

#### Memoization Strategy
- **React.memo**: Applied to all functional components to prevent unnecessary re-renders
- **useMemo**: Used for expensive calculations and data transformations
- **useCallback**: Applied to event handlers and function props

#### Optimized Polling
- **Reduced Frequencies**: Plans (60s), Executions (10s), Active Executions (3s)
- **Smart Polling**: Only poll when data is visible and relevant
- **Conditional Polling**: Stop polling when user is inactive

#### State Management
- **Efficient Data Structures**: Use Map and Set for large datasets
- **Local State**: Keep component state local when possible
- **Context Optimization**: Split contexts to minimize re-renders

#### Asset Optimization
- **Local Assets**: AWS logos served locally to avoid CORS issues
- **Code Splitting**: Route-based code splitting with React Router
- **Bundle Optimization**: Vite-based build optimization

#### Activity Tracking
- **4-Hour Timeout**: Activity-based session timeout
- **Comprehensive Tracking**: Mouse, keyboard, and API activity
- **Automatic Token Refresh**: 50-minute token refresh cycle

---

## Accessibility Compliance

### WCAG 2.1 AA Compliance

#### Keyboard Navigation
- All interactive elements accessible via keyboard
- Logical tab order throughout application
- Keyboard shortcuts for common actions
- Focus indicators on all focusable elements

#### Screen Reader Support
- Semantic HTML structure
- ARIA labels and descriptions
- Role attributes for custom components
- Live regions for dynamic content updates

#### Color and Contrast
- CloudScape design system ensures proper contrast ratios
- Color is not the only means of conveying information
- High contrast mode support
- Consistent color usage throughout application

#### Responsive Design
- Mobile-friendly responsive layout
- Touch-friendly interactive elements
- Scalable text and UI elements
- Consistent experience across devices

---

## User Experience Patterns

### Progressive Disclosure
- Simple workflows with optional advanced features
- Expandable sections for detailed information
- Step-by-step wizards for complex operations
- Contextual help and tooltips

### Real-Time Feedback
- Immediate validation feedback
- Progress indicators for long-running operations
- Real-time status updates
- Toast notifications for user actions

### Error Handling
- User-friendly error messages
- Contextual error information
- Recovery suggestions
- Graceful degradation for failures

### Consistency
- AWS Console design patterns
- Consistent terminology and labeling
- Standardized interaction patterns
- Uniform spacing and typography

---

## Build Configuration

**For complete setup instructions, dependency versions, and configuration files, see [Technology Stack](./UX_TECHNOLOGY_STACK.md).**

### Vite Configuration
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    target: 'es2020',
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          cloudscape: ['@cloudscape-design/components'],
          aws: ['@aws-amplify/auth', 'aws-amplify']
        }
      }
    }
  },
  server: {
    port: 5173,
    host: true
  }
})
```

### TypeScript Configuration
- Strict type checking enabled
- Path mapping for clean imports
- Component prop type validation
- API response type definitions

---

## Testing Strategy

### Component Testing
- Unit tests for all components
- Integration tests for complex workflows
- Accessibility testing with automated tools
- Visual regression testing

### User Experience Testing
- Usability testing with real users
- Performance testing on various devices
- Cross-browser compatibility testing
- Mobile responsiveness validation

---

## References

**Related UX Documentation**:
- [Component Library](./UX_COMPONENT_LIBRARY.md) - Complete specifications for all 32+ components with detailed layouts
- [Page Specifications](./UX_PAGE_SPECIFICATIONS.md) - Detailed page layouts, features, and API integration requirements
- [Technology Stack](./UX_TECHNOLOGY_STACK.md) - Setup instructions, dependency versions, and configuration
- [Visual Design System](./UX_VISUAL_DESIGN_SYSTEM.md) - Color palette, typography, spacing, and branding guidelines

**Project Documentation**:
- [Product Requirements Document](./PRODUCT_REQUIREMENTS_DOCUMENT.md)
- [Software Requirements Specification](./SOFTWARE_REQUIREMENTS_SPECIFICATION.md)

**External Resources**:
- [CloudScape Design System Documentation](https://cloudscape.design/)
- [React 19 Documentation](https://react.dev/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)