# Frontend Design Consistency Rules

## CRITICAL: Always Follow AWS CloudScape Design System

**NEVER deviate from CloudScape components and patterns. This ensures AWS console-style consistency.**

## Layout Structure Rules

### 1. App Layout Pattern (MANDATORY)
```typescript
// ALWAYS wrap protected routes with AppLayout
<ProtectedRoute>
  <AppLayout>
    <YourPageComponent />
  </AppLayout>
</ProtectedRoute>

// NEVER use AppLayout for login/public pages
<Route path="/login" element={<LoginPage />} />
```

### 2. Page Structure Pattern (MANDATORY)
```typescript
// ALWAYS use ContentLayout for page content
<ContentLayout
  header={
    <Header
      variant="h1"
      description="Page description"
      actions={<Button>Action</Button>}
    >
      Page Title
    </Header>
  }
>
  <SpaceBetween size="l">
    {/* Page content */}
  </SpaceBetween>
</ContentLayout>
```

### 3. Container Usage (MANDATORY)
```typescript
// ALWAYS wrap content sections in Container
<Container
  header={<Header variant="h2">Section Title</Header>}
>
  {/* Section content */}
</Container>
```

## AWS Branding Rules

### 1. Top Navigation (NEVER CHANGE)
```typescript
// ALWAYS use this exact AWS logo and branding
<TopNavigation
  identity={{
    href: '/',
    title: 'Elastic Disaster Recovery Orchestrator',
    logo: {
      src: 'https://a0.awsstatic.com/libra-css/images/logos/aws_smile-header-desktop-en-white_59x35.png',
      alt: 'AWS',
    },
  }}
/>
```

### 2. Navigation Items (MAINTAIN ORDER)
```typescript
// ALWAYS use this exact navigation structure and order
const navigationItems = [
  { type: 'link', text: 'Dashboard', href: '/' },
  { type: 'divider' },
  { type: 'link', text: 'Getting Started', href: '/getting-started' },
  { type: 'link', text: 'Protection Groups', href: '/protection-groups' },
  { type: 'link', text: 'Recovery Plans', href: '/recovery-plans' },
  { type: 'link', text: 'History', href: '/executions' },
];
```

### 3. User Menu (STANDARD PATTERN)
```typescript
// ALWAYS include these user menu items
utilities={[
  {
    type: 'menu-dropdown',
    text: user?.email || user?.username || 'User',
    iconName: 'user-profile',
    items: [
      { id: 'profile', text: 'Profile', disabled: true },
      { id: 'preferences', text: 'Preferences', disabled: true },
      { id: 'signout', text: 'Sign out' },
    ],
  },
]}
```

## Color Scheme Rules (AWS STANDARD)

### 1. Status Colors (NEVER CHANGE)
```typescript
// ALWAYS use these exact status colors
const STATUS_COLORS = {
  completed: '#037f0c',    // AWS Green
  in_progress: '#0972d3',  // AWS Blue
  pending: '#5f6b7a',      // AWS Grey
  failed: '#d91515',       // AWS Red
  rolled_back: '#ff9900',  // AWS Orange
  cancelled: '#5f6b7a',    // AWS Grey
  paused: '#5f6b7a',       // AWS Grey
};
```

### 2. Badge Colors (CLOUDSCAPE STANDARD)
```typescript
// ALWAYS use CloudScape badge colors
<Badge color="green">Completed</Badge>    // Success states
<Badge color="red">Failed</Badge>         // Error states
<Badge color="blue">In Progress</Badge>   // Active states
<Badge color="grey">Pending</Badge>       // Inactive states
```

### 3. StatusIndicator Types (CLOUDSCAPE STANDARD)
```typescript
// ALWAYS use correct StatusIndicator types
const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success';
    case 'failed': return 'error';
    case 'rolled_back': return 'warning';
    case 'cancelled':
    case 'paused': return 'stopped';
    default: return 'in-progress';
  }
};
```

## Icon Usage Rules

### 1. Standard Icons (ALWAYS USE THESE)
```typescript
// ALWAYS use these CloudScape icons for consistency
const STANDARD_ICONS = {
  create: 'add-plus',
  edit: 'edit',
  delete: 'remove',
  refresh: 'refresh',
  search: 'search',
  settings: 'settings',
  info: 'status-info',
  warning: 'status-warning',
  external: 'external',
  copy: 'copy',
  success: 'check',
  cancel: 'close',
  user: 'user-profile',
  notification: 'notification',
};
```

### 2. Button Icon Pattern
```typescript
// ALWAYS include iconName for action buttons
<Button variant="primary" iconName="add-plus">
  Create Protection Group
</Button>
```

## Spacing Rules (CLOUDSCAPE TOKENS)

### 1. SpaceBetween Sizes (STANDARD PATTERN)
```typescript
// ALWAYS use these spacing sizes consistently
<SpaceBetween size="l">     // Between major sections
<SpaceBetween size="m">     // Between related items
<SpaceBetween size="s">     // Between form fields
<SpaceBetween size="xs">    // Between inline elements
```

### 2. Container Padding (CLOUDSCAPE DEFAULT)
```typescript
// NEVER override container padding - use CloudScape defaults
<Container>  // Uses CloudScape default padding
  {/* Content */}
</Container>

// For custom spacing, use Box component
<Box padding="l">
  {/* Content */}
</Box>
```

## Form Design Rules

### 1. Form Field Pattern (MANDATORY)
```typescript
// ALWAYS wrap inputs with FormField
<FormField
  label="Field Label"
  description="Optional description"
  errorText={error}
  constraintText="Optional constraint"
>
  <Input
    value={value}
    onChange={({ detail }) => setValue(detail.value)}
    placeholder="Placeholder text"
  />
</FormField>
```

### 2. Form Actions Pattern (STANDARD)
```typescript
// ALWAYS use this form actions pattern
<Form
  actions={
    <SpaceBetween direction="horizontal" size="xs">
      <Button variant="link" onClick={onCancel}>
        Cancel
      </Button>
      <Button variant="primary" loading={loading} onClick={onSubmit}>
        {isEdit ? 'Update' : 'Create'}
      </Button>
    </SpaceBetween>
  }
>
```

## Table Design Rules

### 1. Table Structure (MANDATORY)
```typescript
// ALWAYS use this table structure
<Table
  items={items}
  columnDefinitions={columnDefinitions}
  loading={loading}
  loadingText="Loading..."
  empty={
    <Box textAlign="center" color="inherit">
      <b>No items</b>
      <Box padding={{ bottom: 's' }} variant="p" color="inherit">
        No items to display.
      </Box>
    </Box>
  }
  header={
    <Header
      counter={`(${items.length})`}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={onRefresh} />
          <Button variant="primary" iconName="add-plus" onClick={onCreate}>
            Create
          </Button>
        </SpaceBetween>
      }
    >
      Table Title
    </Header>
  }
/>
```

### 2. Column Definition Pattern (STANDARD)
```typescript
// ALWAYS include these standard column properties
const columnDefinitions = [
  {
    id: 'name',
    header: 'Name',
    cell: (item) => item.name,
    sortingField: 'name',
    isRowHeader: true,
  },
  {
    id: 'status',
    header: 'Status',
    cell: (item) => <StatusBadge status={item.status} />,
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: (item) => (
      <SpaceBetween direction="horizontal" size="xs">
        <Button variant="icon" iconName="edit" onClick={() => onEdit(item)} />
        <Button variant="icon" iconName="remove" onClick={() => onDelete(item)} />
      </SpaceBetween>
    ),
  },
];
```

## Modal/Dialog Rules

### 1. Modal Structure (MANDATORY)
```typescript
// ALWAYS use this modal structure
<Modal
  visible={visible}
  onDismiss={onDismiss}
  header="Modal Title"
  footer={
    <Box float="right">
      <SpaceBetween direction="horizontal" size="xs">
        <Button variant="link" onClick={onDismiss}>
          Cancel
        </Button>
        <Button variant="primary" loading={loading} onClick={onSubmit}>
          Confirm
        </Button>
      </SpaceBetween>
    </Box>
  }
  size="medium"
>
  {/* Modal content */}
</Modal>
```

## Loading State Rules

### 1. Loading Patterns (CONSISTENT)
```typescript
// ALWAYS use these loading patterns
// Page loading
<Box textAlign="center" padding="xxl">
  <Spinner size="large" />
</Box>

// Button loading
<Button loading={loading} variant="primary">
  Submit
</Button>

// Table loading
<Table loading={loading} loadingText="Loading items..." />
```

### 2. Skeleton Loading (WHEN APPROPRIATE)
```typescript
// USE skeleton loaders for cards and tables
<CardSkeleton />
<DataTableSkeleton />
```

## Error Handling Rules

### 1. Error Display Pattern (STANDARD)
```typescript
// ALWAYS use StatusIndicator for errors
<StatusIndicator type="error">
  {errorMessage}
</StatusIndicator>

// For form field errors
<FormField errorText={fieldError}>
  <Input />
</FormField>
```

### 2. Empty State Pattern (CONSISTENT)
```typescript
// ALWAYS use this empty state pattern
<Box textAlign="center" padding="l" color="text-body-secondary">
  No items yet.{' '}
  <Link onFollow={() => navigate('/create')}>
    Create one
  </Link>{' '}
  to get started.
</Box>
```

## Notification Rules

### 1. Toast Notifications (REACT-HOT-TOAST)
```typescript
// ALWAYS use these toast configurations
import toast from 'react-hot-toast';

// Success
toast.success('Operation completed successfully');

// Error
toast.error('Operation failed');

// Loading
const toastId = toast.loading('Processing...');
toast.success('Done!', { id: toastId });
```

### 2. Flashbar Notifications (CLOUDSCAPE)
```typescript
// USE Flashbar for persistent notifications
<Flashbar
  items={[
    {
      type: 'success',
      dismissible: true,
      header: 'Success',
      content: 'Operation completed successfully',
    },
  ]}
/>
```

## Typography Rules

### 1. Header Variants (CLOUDSCAPE STANDARD)
```typescript
// ALWAYS use correct header variants
<Header variant="h1">Page Title</Header>      // Page headers
<Header variant="h2">Section Title</Header>   // Section headers
<Header variant="h3">Subsection</Header>     // Subsections
```

### 2. Text Variants (CLOUDSCAPE TOKENS)
```typescript
// ALWAYS use CloudScape text variants
<Box variant="awsui-key-label">Label</Box>
<Box variant="awsui-value-large">Value</Box>
<Box color="text-body-secondary">Secondary text</Box>
```

## Region Selector Rules

### 1. DRS Regions (COMPLETE LIST - 30 TOTAL: 28 COMMERCIAL + 2 GOVCLOUD)
```typescript
// ALWAYS use this complete DRS regions list (verified December 2025)
// Note: GovCloud regions (us-gov-east-1, us-gov-west-1) require separate accounts
const DRS_REGIONS = [
  // Americas (6)
  { value: 'us-east-1', label: 'us-east-1 (N. Virginia)' },
  { value: 'us-east-2', label: 'us-east-2 (Ohio)' },
  { value: 'us-west-1', label: 'us-west-1 (N. California)' },
  { value: 'us-west-2', label: 'us-west-2 (Oregon)' },
  { value: 'ca-central-1', label: 'ca-central-1 (Canada)' },
  { value: 'sa-east-1', label: 'sa-east-1 (São Paulo)' },
  // Europe (8)
  { value: 'eu-west-1', label: 'eu-west-1 (Ireland)' },
  { value: 'eu-west-2', label: 'eu-west-2 (London)' },
  { value: 'eu-west-3', label: 'eu-west-3 (Paris)' },
  { value: 'eu-central-1', label: 'eu-central-1 (Frankfurt)' },
  { value: 'eu-central-2', label: 'eu-central-2 (Zurich)' },
  { value: 'eu-north-1', label: 'eu-north-1 (Stockholm)' },
  { value: 'eu-south-1', label: 'eu-south-1 (Milan)' },
  { value: 'eu-south-2', label: 'eu-south-2 (Spain)' },
  // Asia Pacific (10)
  { value: 'ap-northeast-1', label: 'ap-northeast-1 (Tokyo)' },
  { value: 'ap-northeast-2', label: 'ap-northeast-2 (Seoul)' },
  { value: 'ap-northeast-3', label: 'ap-northeast-3 (Osaka)' },
  { value: 'ap-southeast-1', label: 'ap-southeast-1 (Singapore)' },
  { value: 'ap-southeast-2', label: 'ap-southeast-2 (Sydney)' },
  { value: 'ap-southeast-3', label: 'ap-southeast-3 (Jakarta)' },
  { value: 'ap-southeast-4', label: 'ap-southeast-4 (Melbourne)' },
  { value: 'ap-south-1', label: 'ap-south-1 (Mumbai)' },
  { value: 'ap-south-2', label: 'ap-south-2 (Hyderabad)' },
  { value: 'ap-east-1', label: 'ap-east-1 (Hong Kong)' },
  // Middle East & Africa (4)
  { value: 'me-south-1', label: 'me-south-1 (Bahrain)' },
  { value: 'me-central-1', label: 'me-central-1 (UAE)' },
  { value: 'af-south-1', label: 'af-south-1 (Cape Town)' },
  { value: 'il-central-1', label: 'il-central-1 (Tel Aviv)' },
];
```

## Event Handler Rules

### 1. CloudScape Event Pattern (MANDATORY)
```typescript
// ALWAYS use detail property for CloudScape events
onChange={({ detail }) => setValue(detail.value)}
onSelectionChange={({ detail }) => setSelected(detail.selectedItems)}
onFollow={(event) => {
  event.preventDefault();
  navigate(event.detail.href);
}}
```

## Import Rules

### 1. CloudScape Import Pattern (ORGANIZED)
```typescript
// ALWAYS organize imports by category
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
  Badge,
  Spinner,
} from '@cloudscape-design/components';
```

## CSS Rules

### 1. Minimal Custom CSS (AVOID OVERRIDES)
```css
/* ONLY override when absolutely necessary */
/* CloudScape handles 99% of styling */

/* AWS Console-style scrollbar (APPROVED) */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f2f3f3;
}

::-webkit-scrollbar-thumb {
  background: #879596;
  border-radius: 4px;
}
```

### 2. NO Custom Component Styling
```typescript
// NEVER add custom CSS classes to CloudScape components
// BAD:
<Button className="custom-button">Submit</Button>

// GOOD:
<Button variant="primary">Submit</Button>
```

## Theme Rules

### 1. CloudScape Theme Only (MANDATORY)
```typescript
// ALWAYS use CloudScape light mode theme
import { applyMode, Mode } from '@cloudscape-design/global-styles';

export const initializeTheme = () => {
  applyMode(Mode.Light);  // AWS Console standard
};
```

### 2. NO Custom Themes
```typescript
// NEVER create custom themes or override CloudScape tokens
// CloudScape provides complete AWS-branded design system
```

## Responsive Design Rules

### 1. CloudScape Responsive (AUTOMATIC)
```typescript
// CloudScape components are responsive by default
// NEVER add custom responsive CSS

// USE ColumnLayout for responsive grids
<ColumnLayout columns={4} variant="text-grid">
  {/* Automatically responsive */}
</ColumnLayout>
```

## Accessibility Rules

### 1. CloudScape Accessibility (BUILT-IN)
```typescript
// CloudScape components include accessibility by default
// ALWAYS provide proper labels and descriptions

<FormField
  label="Required field label"
  description="Helpful description"
>
  <Input ariaLabel="Descriptive label" />
</FormField>
```

## Performance Rules

### 1. Component Optimization
```typescript
// ALWAYS use React.memo for expensive components
export const ExpensiveComponent = React.memo<Props>(({ data }) => {
  // Component logic
});

// ALWAYS use useCallback for event handlers
const handleClick = useCallback(() => {
  // Handler logic
}, [dependencies]);
```

## Validation Rules

### 1. Form Validation Pattern
```typescript
// ALWAYS show validation errors in FormField
<FormField
  label="Email"
  errorText={errors.email}
  constraintText="Must be a valid email address"
>
  <Input
    value={email}
    onChange={({ detail }) => setEmail(detail.value)}
    invalid={!!errors.email}
  />
</FormField>
```

## NEVER DO These Things

### 1. Design System Violations
- ❌ NEVER use custom CSS frameworks (Bootstrap, Tailwind, etc.)
- ❌ NEVER override CloudScape component styles
- ❌ NEVER use non-CloudScape UI components
- ❌ NEVER change AWS branding colors or logos
- ❌ NEVER create custom themes

### 2. Layout Violations
- ❌ NEVER skip AppLayout wrapper for protected pages
- ❌ NEVER skip ContentLayout for page content
- ❌ NEVER use custom navigation components
- ❌ NEVER change navigation structure or order

### 3. Pattern Violations
- ❌ NEVER ignore CloudScape event patterns (detail property)
- ❌ NEVER use non-standard status colors
- ❌ NEVER create custom loading states (use CloudScape)
- ❌ NEVER skip error boundaries and error handling

## ALWAYS DO These Things

### 1. Follow CloudScape Patterns
- ✅ ALWAYS use CloudScape components exclusively
- ✅ ALWAYS follow AWS console design patterns
- ✅ ALWAYS use standard status colors and icons
- ✅ ALWAYS wrap content in proper layout components

### 2. Maintain Consistency
- ✅ ALWAYS use the same navigation structure
- ✅ ALWAYS use the same form patterns
- ✅ ALWAYS use the same table patterns
- ✅ ALWAYS use the same modal patterns

### 3. Follow AWS Standards
- ✅ ALWAYS use AWS branding and logos
- ✅ ALWAYS use CloudScape light mode theme
- ✅ ALWAYS follow AWS console interaction patterns
- ✅ ALWAYS maintain AWS console look and feel

## Quick Reference Checklist

Before creating any new component or page:

- [ ] Uses CloudScape components exclusively
- [ ] Follows AppLayout → ContentLayout → Container structure
- [ ] Uses standard AWS status colors and icons
- [ ] Implements proper loading and error states
- [ ] Follows CloudScape event handling patterns
- [ ] Includes proper accessibility attributes
- [ ] Uses standard spacing and typography
- [ ] Maintains AWS console look and feel
- [ ] No custom CSS overrides
- [ ] Responsive by default (CloudScape handles this)