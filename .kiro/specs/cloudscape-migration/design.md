# CloudScape Migration - Design Document

## Overview

This document describes the technical design for migrating the AWS DRS Orchestration frontend from Material-UI 7.3.5 to AWS CloudScape Design System. The migration maintains all existing functionality while adopting AWS-native design patterns and components.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Application                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           CloudScape AppLayout Wrapper                │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │         ContentLayout (Page Container)          │  │  │
│  │  │  ┌───────────────────────────────────────────┐  │  │  │
│  │  │  │         Page Components                   │  │  │  │
│  │  │  │  - LoginPage                              │  │  │  │
│  │  │  │  - Dashboard                              │  │  │  │
│  │  │  │  - ProtectionGroupsPage                   │  │  │  │
│  │  │  │  - RecoveryPlansPage                      │  │  │  │
│  │  │  │  - ExecutionsPage                         │  │  │  │
│  │  │  └───────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Shared CloudScape Components                │  │
│  │  - Dialogs (Modal-based)                              │  │
│  │  - Selectors (Select, Table)                          │  │
│  │  - Display (Badge, ProgressIndicator)                 │  │
│  │  - Utilities (Spinner, EmptyState)                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              CloudScape Theme Layer                   │  │
│  │  - Global Styles                                      │  │
│  │  - Design Tokens                                      │  │
│  │  - AWS Branding                                       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

**Before (Material-UI):**
```
App
├── ThemeProvider (Material-UI)
│   ├── CssBaseline
│   └── Router
│       ├── LoginPage
│       └── Authenticated Routes
│           ├── Dashboard
│           ├── ProtectionGroupsPage
│           ├── RecoveryPlansPage
│           └── ExecutionsPage
```

**After (CloudScape):**
```
App
├── CloudScape Global Styles (imported)
├── Router
│   ├── LoginPage (standalone)
│   └── Authenticated Routes
│       └── AppLayout (CloudScape wrapper)
│           ├── TopNavigation
│           ├── SideNavigation
│           └── ContentLayout
│               ├── Dashboard
│               ├── ProtectionGroupsPage
│               ├── RecoveryPlansPage
│               └── ExecutionsPage
```

## Components and Interfaces

### 1. Layout Components

#### AppLayout Wrapper
**Purpose:** Provides consistent AWS console-style layout with navigation

**Interface:**
```typescript
interface AppLayoutProps {
  children: React.ReactNode;
  navigationOpen?: boolean;
  onNavigationChange?: (open: boolean) => void;
}
```

**Responsibilities:**
- Render CloudScape AppLayout component
- Manage TopNavigation with user info and logout
- Manage SideNavigation with route links
- Handle breadcrumbs
- Manage Flashbar notifications

**Key Features:**
- Persistent navigation state
- User profile display
- Logout functionality
- Active route highlighting

#### ContentLayout Wrapper
**Purpose:** Standardizes page content layout and spacing

**Interface:**
```typescript
interface ContentLayoutProps {
  header: string;
  description?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}
```

**Responsibilities:**
- Render page header with consistent styling
- Provide action button area
- Apply consistent spacing
- Handle loading states

### 2. Dialog Components

#### ConfirmDialog
**Migration:** Material-UI Dialog → CloudScape Modal

**Interface:**
```typescript
interface ConfirmDialogProps {
  visible: boolean;
  onDismiss: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'primary' | 'danger';
}
```

**Key Changes:**
- `open` → `visible`
- `onClose` → `onDismiss`
- Explicit footer with SpaceBetween layout
- Button variants for visual hierarchy

#### ProtectionGroupDialog
**Migration:** Material-UI Dialog + TextField → CloudScape Modal + FormField

**Interface:**
```typescript
interface ProtectionGroupDialogProps {
  visible: boolean;
  onDismiss: () => void;
  onSave: (data: ProtectionGroupData) => Promise<void>;
  initialData?: ProtectionGroup;
  mode: 'create' | 'edit';
}
```

**Key Changes:**
- Form fields wrapped in FormField components
- Input onChange uses `event.detail.value`
- Alert → Flashbar for error messages
- Server discovery integrated with CloudScape Table

#### RecoveryPlanDialog
**Migration:** Similar to ProtectionGroupDialog with wave configuration

**Interface:**
```typescript
interface RecoveryPlanDialogProps {
  visible: boolean;
  onDismiss: () => void;
  onSave: (data: RecoveryPlanData) => Promise<void>;
  initialData?: RecoveryPlan;
  mode: 'create' | 'edit';
}
```

**Key Changes:**
- Complex wave configuration with CloudScape ExpandableSection
- Dependency validation with visual feedback
- Multi-step form with CloudScape Wizard (future enhancement)

### 3. Selector Components

#### RegionSelector
**Migration:** Material-UI Select → CloudScape Select

**Interface:**
```typescript
interface RegionSelectorProps {
  value: string;
  onChange: (region: string) => void;
  disabled?: boolean;
}
```

**Key Changes:**
- MenuItem → option objects with `{ value, label }`
- onChange receives `event.detail.selectedOption`
- Built-in search/filter functionality

#### ServerSelector
**Migration:** Material-UI DataGrid → CloudScape Table

**Interface:**
```typescript
interface ServerSelectorProps {
  region: string;
  selectedServers: string[];
  onSelectionChange: (servers: string[]) => void;
  assignedServers: Record<string, string>; // serverId → groupName
}
```

**Key Changes:**
- Manual selection state management
- Built-in checkbox selection
- Custom cell renderers for badges
- Real-time search with TextFilter
- Assignment status visualization

### 4. Display Components

#### StatusBadge
**Migration:** Material-UI Chip → CloudScape Badge

**Interface:**
```typescript
interface StatusBadgeProps {
  status: ExecutionStatus | ServerStatus;
  size?: 'small' | 'medium';
}
```

**Key Changes:**
- Color mapping: success, error, warning, info
- Simplified API (no onClick, no delete)
- Consistent sizing

#### WaveProgress
**Migration:** Material-UI Stepper → CloudScape ProgressIndicator

**Interface:**
```typescript
interface WaveProgressProps {
  waves: Wave[];
  currentWaveIndex: number;
}
```

**Key Changes:**
- Step → ProgressIndicator.Step
- Status mapping: pending, in-progress, complete, error
- Vertical layout for better mobile support

### 5. Table Components

#### Table Wrapper Pattern
**Purpose:** Reusable table component with collection hooks

**Interface:**
```typescript
interface TableWrapperProps<T> {
  items: T[];
  columnDefinitions: TableProps.ColumnDefinition<T>[];
  loading?: boolean;
  selectionType?: 'single' | 'multi';
  onSelectionChange?: (items: T[]) => void;
  filteringPlaceholder?: string;
  emptyMessage?: string;
}
```

**Implementation:**
```typescript
import { useCollection } from '@cloudscape-design/collection-hooks';

function TableWrapper<T>({ items, columnDefinitions, ...props }: TableWrapperProps<T>) {
  const { items: filteredItems, collectionProps, filterProps, paginationProps } = 
    useCollection(items, {
      filtering: {
        empty: <EmptyState message={props.emptyMessage} />,
        noMatch: <EmptyState message="No matches found" />
      },
      pagination: { pageSize: 25 },
      sorting: {}
    });

  return (
    <Table
      {...collectionProps}
      columnDefinitions={columnDefinitions}
      items={filteredItems}
      loading={props.loading}
      filter={<TextFilter {...filterProps} placeholder={props.filteringPlaceholder} />}
      pagination={<Pagination {...paginationProps} />}
    />
  );
}
```

## Data Models

### Component State Models

#### Table Collection State
```typescript
interface TableCollectionState<T> {
  items: T[];
  filteredItems: T[];
  selectedItems: T[];
  currentPageIndex: number;
  sortingColumn: TableProps.SortingColumn<T>;
  sortingDescending: boolean;
  filteringText: string;
}
```

#### Form State
```typescript
interface FormState<T> {
  data: T;
  errors: Record<keyof T, string>;
  touched: Record<keyof T, boolean>;
  isSubmitting: boolean;
  isDirty: boolean;
}
```

#### Notification State
```typescript
interface FlashbarMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  header: string;
  content?: string;
  dismissible: boolean;
  onDismiss?: () => void;
}
```

### Migration Mapping Models

#### Component Mapping
```typescript
interface ComponentMapping {
  materialUI: string;
  cloudscape: string;
  apiChanges: string[];
  notes: string;
}

const componentMappings: ComponentMapping[] = [
  {
    materialUI: 'Button',
    cloudscape: 'Button',
    apiChanges: ['variant: contained → primary', 'variant: outlined → normal'],
    notes: 'Similar API, minor prop name changes'
  },
  {
    materialUI: 'TextField',
    cloudscape: 'FormField + Input',
    apiChanges: [
      'Requires FormField wrapper',
      'onChange: e.target.value → e.detail.value',
      'error + helperText → errorText in FormField'
    ],
    notes: 'Significant structural change'
  },
  // ... more mappings
];
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Component API Compatibility
*For any* migrated component, all props from the original Material-UI component should have equivalent functionality in the CloudScape version, ensuring no loss of features during migration.

**Validates: Requirements 1.1, 1.2**

### Property 2: Visual Consistency Preservation
*For any* page or component, the visual spacing, alignment, and color contrast should match or exceed the original Material-UI implementation, maintaining the AWS-branded theme.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Functionality Preservation
*For any* user interaction (CRUD operation, search, filter, sort), the behavior should be identical to the Material-UI version, with no regression in functionality.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 4: Accessibility Compliance
*For any* interactive element, keyboard navigation, screen reader compatibility, and WCAG 2.1 AA compliance should be maintained or improved from the Material-UI version.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 5: Performance Parity
*For any* page load or interaction, the performance (bundle size, load time, runtime) should not regress compared to the Material-UI version, with target bundle size <3MB.

**Validates: Requirements 5.1, 5.2**

### Property 6: Type Safety
*For any* component, TypeScript types should be correctly defined with no `any` types, ensuring compile-time type checking for all props and state.

**Validates: Requirements 6.1**

### Property 7: Build Success
*For any* code change, the build process should complete without TypeScript errors or warnings, ensuring production readiness.

**Validates: Requirements 6.2**

## Error Handling

### Form Validation Errors

**Pattern:**
```typescript
interface FormFieldError {
  field: string;
  message: string;
}

function validateForm(data: FormData): FormFieldError[] {
  const errors: FormFieldError[] = [];
  
  if (!data.name?.trim()) {
    errors.push({ field: 'name', message: 'Name is required' });
  }
  
  if (data.name && data.name.length > 255) {
    errors.push({ field: 'name', message: 'Name must be less than 255 characters' });
  }
  
  return errors;
}
```

**Display:**
```typescript
<FormField
  label="Name"
  errorText={errors.find(e => e.field === 'name')?.message}
>
  <Input value={name} onChange={e => setName(e.detail.value)} />
</FormField>
```

### API Errors

**Pattern:**
```typescript
interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

async function handleApiCall<T>(
  apiCall: () => Promise<T>
): Promise<{ data?: T; error?: ApiError }> {
  try {
    const data = await apiCall();
    return { data };
  } catch (error) {
    return {
      error: {
        message: error.message || 'An unexpected error occurred',
        code: error.code,
        details: error.response?.data
      }
    };
  }
}
```

**Display:**
```typescript
const [flashbarItems, setFlashbarItems] = useState<FlashbarMessage[]>([]);

function showError(error: ApiError) {
  setFlashbarItems([
    ...flashbarItems,
    {
      id: Date.now().toString(),
      type: 'error',
      header: 'Operation Failed',
      content: error.message,
      dismissible: true,
      onDismiss: () => removeFlashbarItem(id)
    }
  ]);
}
```

### Component Error Boundaries

**Pattern:**
```typescript
class ErrorBoundary extends React.Component<Props, State> {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Component error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Alert type="error" header="Something went wrong">
          {this.state.error?.message || 'An unexpected error occurred'}
        </Alert>
      );
    }

    return this.props.children;
  }
}
```

## Testing Strategy

### Unit Testing

**Component Tests:**
- Test each migrated component in isolation
- Verify prop handling and event callbacks
- Test error states and edge cases
- Ensure TypeScript types are correct

**Example:**
```typescript
describe('StatusBadge', () => {
  it('should render success badge for COMPLETED status', () => {
    const { getByText } = render(<StatusBadge status="COMPLETED" />);
    const badge = getByText('COMPLETED');
    expect(badge).toHaveAttribute('data-color', 'success');
  });

  it('should render error badge for FAILED status', () => {
    const { getByText } = render(<StatusBadge status="FAILED" />);
    const badge = getByText('FAILED');
    expect(badge).toHaveAttribute('data-color', 'error');
  });
});
```

### Integration Testing

**Page Tests:**
- Test complete user workflows
- Verify CRUD operations
- Test navigation and routing
- Verify real-time updates

**Example:**
```typescript
describe('ProtectionGroupsPage', () => {
  it('should create a new protection group', async () => {
    const { getByText, getByLabelText } = render(<ProtectionGroupsPage />);
    
    // Click create button
    fireEvent.click(getByText('Create Protection Group'));
    
    // Fill form
    fireEvent.change(getByLabelText('Name'), { target: { value: 'Test Group' } });
    
    // Save
    fireEvent.click(getByText('Save'));
    
    // Verify success
    await waitFor(() => {
      expect(getByText('Protection Group created successfully')).toBeInTheDocument();
    });
  });
});
```

### Visual Regression Testing

**Approach:**
- Capture screenshots before migration (Material-UI)
- Capture screenshots after migration (CloudScape)
- Compare pixel-by-pixel differences
- Verify spacing, alignment, colors

**Tools:**
- Playwright for screenshot capture
- Percy or Chromatic for visual diff
- Manual review for subjective elements

### Accessibility Testing

**Automated Tests:**
- axe-core for WCAG compliance
- Lighthouse accessibility audit
- WAVE browser extension

**Manual Tests:**
- Keyboard navigation (Tab, Enter, Escape)
- Screen reader testing (VoiceOver, NVDA)
- Focus management verification
- Color contrast verification

### Performance Testing

**Metrics:**
- Bundle size comparison (before/after)
- Initial load time
- Time to interactive
- Runtime performance (table rendering)
- Memory usage

**Tools:**
- Webpack Bundle Analyzer
- Lighthouse performance audit
- Chrome DevTools Performance tab

## Implementation Notes

### Migration Order

**Phase 1: Foundation**
1. Install CloudScape dependencies
2. Remove Material-UI dependencies
3. Create theme configuration
4. Create layout wrappers

**Phase 2: Bottom-Up Component Migration**
1. Utility components (StatusBadge, LoadingSpinner)
2. Display components (WaveProgress, InfoPanel)
3. Form components (ConfirmDialog, selectors)
4. Complex dialogs (ProtectionGroupDialog, RecoveryPlanDialog)

**Phase 3: Top-Down Page Migration**
1. Simple pages (LoginPage, Dashboard)
2. Complex pages (ProtectionGroupsPage, RecoveryPlansPage, ExecutionsPage)

**Phase 4: Testing & Refinement**
1. Visual regression testing
2. Functionality testing
3. Accessibility testing
4. Performance testing

### Key Technical Decisions

#### Decision 1: Use Collection Hooks for Tables
**Rationale:** CloudScape Table requires manual state management for sorting, filtering, and pagination. The `@cloudscape-design/collection-hooks` package provides battle-tested utilities for this.

**Alternative Considered:** Custom state management
**Rejected Because:** Reinventing the wheel, more maintenance burden

#### Decision 2: Explicit FormField Wrappers
**Rationale:** CloudScape separates form field labels/errors from input components, requiring explicit FormField wrappers.

**Alternative Considered:** Custom wrapper component to hide complexity
**Rejected Because:** Less flexible, harder to customize per-field

#### Decision 3: Flashbar for Notifications
**Rationale:** CloudScape uses Flashbar for stacked notifications, matching AWS console patterns.

**Alternative Considered:** Toast notifications
**Rejected Because:** Not AWS-native, inconsistent with console UX

#### Decision 4: AppLayout for All Authenticated Pages
**Rationale:** Provides consistent AWS console-style navigation and layout.

**Alternative Considered:** Custom layout component
**Rejected Because:** Missing AWS console features, more maintenance

### Breaking Changes

#### API Changes
- `onChange` events use `event.detail.value` instead of `event.target.value`
- `open` prop renamed to `visible` for modals
- `onClose` renamed to `onDismiss` for modals
- Table selection requires explicit state management

#### Structural Changes
- Form fields require FormField wrapper
- Modal footer requires explicit layout
- Table requires separate Filter and Pagination components
- Navigation requires AppLayout wrapper

#### Styling Changes
- Global styles imported instead of ThemeProvider
- Design tokens used instead of theme object
- CSS-in-JS removed (Emotion)
- CloudScape CSS classes used

## Deployment Considerations

### Build Process
1. TypeScript compilation with zero errors
2. Vite build with CloudScape components
3. Bundle size verification (<3MB target)
4. Asset optimization (minification, compression)

### Deployment Steps
1. Build production bundle: `npm run build`
2. Sync to S3: `aws s3 sync dist/ s3://bucket/ --delete`
3. Invalidate CloudFront: `aws cloudfront create-invalidation`
4. Verify deployment: Test critical user flows

### Rollback Plan
1. Revert to previous S3 version
2. Invalidate CloudFront cache
3. Verify Material-UI version working
4. Investigate migration issues

## Future Enhancements

### Phase 5: Advanced Features (Post-Migration)
1. **Wizard Component:** Multi-step forms for complex workflows
2. **Board Component:** Kanban-style execution tracking
3. **Split Panel:** Side-by-side comparison views
4. **Property Filter:** Advanced filtering with facets
5. **Code Editor:** Inline JSON/YAML editing

### Performance Optimizations
1. Code splitting by route
2. Lazy loading for heavy components
3. Virtual scrolling for large tables
4. Memoization for expensive computations

### Accessibility Improvements
1. Enhanced keyboard shortcuts
2. High contrast mode support
3. Screen reader announcements for dynamic content
4. Focus indicators for all interactive elements

---

**Design Document Status:** ✅ Complete
**Next Step:** Begin Phase 4 Testing & Refinement
