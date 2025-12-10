---
inclusion: manual
---

# CloudScape Component Quick Reference

## Purpose

Quick reference for CloudScape components used in this application. Use this when building new UI features.

## Application Components

**Total: 32 Components (23 MVP + 9 Phase 2)**

### Page Components (7 MVP)

| Component | File | Purpose |
|-----------|------|---------|
| LoginPage | `pages/LoginPage.tsx` | Cognito authentication with error handling |
| Dashboard | `pages/Dashboard.tsx` | Metrics cards, pie chart, active executions, DRS quota status |
| GettingStartedPage | `pages/GettingStartedPage.tsx` | 3-step onboarding guide with quick links |
| ProtectionGroupsPage | `pages/ProtectionGroupsPage.tsx` | CRUD table with server counts and DRS limits validation |
| RecoveryPlansPage | `pages/RecoveryPlansPage.tsx` | CRUD table with execution status, conflict detection |
| ExecutionsPage | `pages/ExecutionsPage.tsx` | Active/History tabs with 3-second polling |
| ExecutionDetailsPage | `pages/ExecutionDetailsPage.tsx` | Wave progress, DRS events, pause/resume/terminate |

### MVP Reusable Components (23)

**Layout Components:**

| Component | File | Purpose |
|-----------|------|---------|
| AppLayout | `components/cloudscape/AppLayout.tsx` | CloudScape app shell wrapper |
| ContentLayout | `components/cloudscape/ContentLayout.tsx` | CloudScape page content wrapper |
| ErrorBoundary | `components/ErrorBoundary.tsx` | React error boundary wrapper |
| ErrorFallback | `components/ErrorFallback.tsx` | Error display component |
| ErrorState | `components/ErrorState.tsx` | Error state with retry button |
| LoadingState | `components/LoadingState.tsx` | Loading spinner with message |
| CardSkeleton | `components/CardSkeleton.tsx` | Loading skeleton for cards |
| DataTableSkeleton | `components/DataTableSkeleton.tsx` | Loading skeleton for tables |
| PageTransition | `components/PageTransition.tsx` | Page transition animations |
| ProtectedRoute | `components/ProtectedRoute.tsx` | Auth route wrapper |

**Dialog Components:**

| Component | File | Purpose |
|-----------|------|---------|
| ProtectionGroupDialog | `components/ProtectionGroupDialog.tsx` | Create/Edit Protection Groups |
| RecoveryPlanDialog | `components/RecoveryPlanDialog.tsx` | Create/Edit Recovery Plans |
| ConfirmDialog | `components/ConfirmDialog.tsx` | Confirmation with loading state |

**Server Management Components:**

| Component | File | Purpose |
|-----------|------|---------|
| ServerSelector | `components/ServerSelector.tsx` | Visual server selection with assignment status |
| ServerDiscoveryPanel | `components/ServerDiscoveryPanel.tsx` | DRS server discovery interface |
| ServerListItem | `components/ServerListItem.tsx` | Individual server display |

**Form Control Components:**

| Component | File | Purpose |
|-----------|------|---------|
| RegionSelector | `components/RegionSelector.tsx` | AWS region dropdown (30 DRS regions) |
| WaveConfigEditor | `components/WaveConfigEditor.tsx` | Wave configuration form |

**Status Display Components:**

| Component | File | Purpose |
|-----------|------|---------|
| StatusBadge | `components/StatusBadge.tsx` | Status indicators with color coding |
| WaveProgress | `components/WaveProgress.tsx` | Wave execution timeline with DRS events |
| DateTimeDisplay | `components/DateTimeDisplay.tsx` | Timestamp formatting |
| DRSQuotaStatus | `components/DRSQuotaStatus.tsx` | DRS service quota/capacity display |

**Execution Components:**

| Component | File | Purpose |
|-----------|------|---------|
| ExecutionDetails | `components/ExecutionDetails.tsx` | Execution detail display |

### Phase 2 Components (9) - DRS Source Server Management

| Component | File | Purpose |
|-----------|------|---------|
| LaunchSettingsDialog | `components/LaunchSettingsDialog.tsx` | DRS launch configuration |
| EC2TemplateEditor | `components/EC2TemplateEditor.tsx` | EC2 launch template editing |
| TagsEditor | `components/TagsEditor.tsx` | Server tag management |
| DiskSettingsEditor | `components/DiskSettingsEditor.tsx` | Per-disk configuration |
| ReplicationSettingsEditor | `components/ReplicationSettingsEditor.tsx` | Replication settings |
| PostLaunchSettingsEditor | `components/PostLaunchSettingsEditor.tsx` | Post-launch actions |
| ServerInfoPanel | `components/ServerInfoPanel.tsx` | Read-only server details |
| PitPolicyEditor | `components/PitPolicyEditor.tsx` | Point-in-time policy editor |
| JobEventsTimeline | `components/JobEventsTimeline.tsx` | DRS job events display |


## CloudScape Components Used

### Layout Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `AppLayout` | Main app shell | `navigation`, `content`, `breadcrumbs`, `notifications` |
| `ContentLayout` | Page wrapper | `header` |
| `Container` | Content section | `header`, `footer` |
| `SpaceBetween` | Spacing | `direction`, `size` |
| `ColumnLayout` | Columns | `columns`, `variant` |
| `Box` | Generic container | `padding`, `margin`, `textAlign`, `color` |
| `Grid` | CSS Grid | `gridDefinition` |

### Form Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `FormField` | Input wrapper | `label`, `description`, `errorText`, `constraintText` |
| `Input` | Text input | `value`, `onChange`, `placeholder`, `type` |
| `Textarea` | Multi-line input | `value`, `onChange`, `rows` |
| `Select` | Dropdown | `selectedOption`, `onChange`, `options` |
| `Multiselect` | Multi-select | `selectedOptions`, `onChange`, `options` |
| `Checkbox` | Checkbox | `checked`, `onChange` |
| `Toggle` | On/off switch | `checked`, `onChange` |
| `Form` | Form container | `actions` |

### Table Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `Table` | Data table | `items`, `columnDefinitions`, `loading`, `empty` |
| `TextFilter` | Search filter | `filteringText`, `onChange`, `filteringPlaceholder` |
| `Pagination` | Page controls | `currentPageIndex`, `pagesCount`, `onChange` |

### Button Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `Button` | Standard button | `variant`, `onClick`, `loading`, `iconName` |
| `ButtonDropdown` | Dropdown menu | `items`, `onItemClick` |

**Button Variants**: `primary`, `normal`, `link`, `icon`

### Modal Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `Modal` | Dialog window | `visible`, `onDismiss`, `header`, `footer`, `size` |

**Modal Sizes**: `small`, `medium`, `large`, `max`


### Notification Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `Flashbar` | Notification stack | `items` |
| `Alert` | Inline alert | `type`, `dismissible`, `onDismiss`, `header` |

**Alert Types**: `success`, `error`, `warning`, `info`

### Status Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `StatusIndicator` | Status with icon | `type` |
| `Badge` | Status badge | `color` |
| `ProgressBar` | Progress indicator | `value`, `status` |
| `Spinner` | Loading spinner | `size` |

**StatusIndicator Types**: `success`, `error`, `warning`, `info`, `stopped`, `pending`, `in-progress`, `loading`

### Navigation Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `SideNavigation` | Side menu | `items`, `activeHref`, `onFollow` |
| `BreadcrumbGroup` | Breadcrumbs | `items`, `onFollow` |
| `Tabs` | Tab navigation | `tabs`, `activeTabId`, `onChange` |

### Display Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `Header` | Section header | `variant`, `description`, `actions`, `counter` |
| `Link` | Hyperlink | `href`, `external`, `onFollow` |
| `Icon` | Icon display | `name`, `size`, `variant` |
| `KeyValuePairs` | Key-value display | `columns`, `items` |
| `ExpandableSection` | Collapsible | `header`, `defaultExpanded` |

## Common Import Pattern

```typescript
import {
  // Layout
  AppLayout,
  ContentLayout,
  Container,
  SpaceBetween,
  Box,
  Header,
  
  // Form
  FormField,
  Input,
  Select,
  Button,
  
  // Table
  Table,
  TextFilter,
  Pagination,
  
  // Modal
  Modal,
  
  // Notifications
  Flashbar,
  Alert,
  
  // Status
  StatusIndicator,
  Spinner,
} from '@cloudscape-design/components';

import { useCollection } from '@cloudscape-design/collection-hooks';
```


## Event Handler Pattern

All CloudScape events use `detail` property:

```typescript
// Input
onChange={({ detail }) => setValue(detail.value)}

// Select
onChange={({ detail }) => setSelected(detail.selectedOption)}

// Checkbox
onChange={({ detail }) => setChecked(detail.checked)}

// Table
onSelectionChange={({ detail }) => setSelected(detail.selectedItems)}

// Navigation
onFollow={(event) => {
  event.preventDefault();
  navigate(event.detail.href);
}}
```

## Spacing Sizes

| Size | Pixels |
|------|--------|
| `xxxs` | 2px |
| `xxs` | 4px |
| `xs` | 8px |
| `s` | 12px |
| `m` | 16px |
| `l` | 20px |
| `xl` | 24px |
| `xxl` | 32px |

## Common Icons Used

| Icon Name | Usage |
|-----------|-------|
| `add-plus` | Create/Add |
| `edit` | Edit |
| `remove` | Delete |
| `refresh` | Refresh |
| `search` | Search |
| `settings` | Settings |
| `status-info` | Info |
| `status-warning` | Warning |
| `external` | External link |
| `copy` | Copy |
| `check` | Success/Complete |
| `close` | Cancel/Close |

## Resources

- [Component Docs](https://cloudscape.design/components/)
- [Icons](https://cloudscape.design/foundation/visual-foundation/icons/)
- [Design Tokens](https://cloudscape.design/foundation/visual-foundation/design-tokens/)
- [Collection Hooks](https://cloudscape.design/get-started/dev-guides/collection-hooks/)
