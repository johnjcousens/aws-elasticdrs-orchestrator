---
inclusion: manual
---

# CloudScape Best Practices

## Purpose
Provide best practices and patterns for using CloudScape Design System effectively in the AWS DRS Orchestration frontend.

## Layout & Structure

### Use AppLayout for All Pages
```typescript
import { AppLayout } from '@cloudscape-design/components';

<AppLayout
  navigation={<SideNavigation />}
  content={<YourPageContent />}
  breadcrumbs={<BreadcrumbGroup />}
  notifications={<Flashbar />}
  toolsHide={true}
/>
```

**Benefits:**
- Consistent AWS console experience
- Built-in responsive behavior
- Proper spacing and alignment
- Accessibility features included

### Use ContentLayout for Page Content
```typescript
import { ContentLayout, Header } from '@cloudscape-design/components';

<ContentLayout
  header={
    <Header
      variant="h1"
      actions={<Button>Create</Button>}
    >
      Page Title
    </Header>
  }
>
  <Container>
    Page content here
  </Container>
</ContentLayout>
```

**Benefits:**
- Standardized page headers
- Consistent spacing
- Action button placement
- Responsive design

### Use SpaceBetween for Layouts
```typescript
import { SpaceBetween } from '@cloudscape-design/components';

// Vertical spacing
<SpaceBetween direction="vertical" size="l">
  <Component1 />
  <Component2 />
  <Component3 />
</SpaceBetween>

// Horizontal spacing
<SpaceBetween direction="horizontal" size="xs">
  <Button>Cancel</Button>
  <Button variant="primary">Save</Button>
</SpaceBetween>
```

**Benefits:**
- Consistent spacing
- No manual margin/padding
- Responsive behavior
- Easy to maintain

## Forms & Inputs

### Always Wrap Inputs in FormField
```typescript
import { FormField, Input } from '@cloudscape-design/components';

<FormField
  label="Server Name"
  description="Enter a unique name for this server"
  errorText={errors.name}
  constraintText="Must be 3-50 characters"
>
  <Input
    value={name}
    onChange={({ detail }) => setName(detail.value)}
    placeholder="e.g., web-server-01"
  />
</FormField>
```

**Benefits:**
- Consistent label styling
- Error message display
- Helper text support
- Accessibility labels

### Use Form for Complex Forms
```typescript
import { Form, SpaceBetween } from '@cloudscape-design/components';

<Form
  actions={
    <SpaceBetween direction="horizontal" size="xs">
      <Button onClick={onCancel}>Cancel</Button>
      <Button variant="primary" onClick={onSubmit}>Submit</Button>
    </SpaceBetween>
  }
>
  <SpaceBetween direction="vertical" size="l">
    <FormField label="Name">
      <Input value={name} onChange={handleNameChange} />
    </FormField>
    <FormField label="Description">
      <Textarea value={description} onChange={handleDescriptionChange} />
    </FormField>
  </SpaceBetween>
</Form>
```

**Benefits:**
- Consistent form layout
- Action button placement
- Keyboard navigation
- Form submission handling

### Validate on Blur, Not on Change
```typescript
const [name, setName] = useState('');
const [nameError, setNameError] = useState('');

const validateName = (value: string) => {
  if (!value.trim()) {
    return 'Name is required';
  }
  if (value.length < 3) {
    return 'Name must be at least 3 characters';
  }
  return '';
};

<FormField label="Name" errorText={nameError}>
  <Input
    value={name}
    onChange={({ detail }) => setName(detail.value)}
    onBlur={() => setNameError(validateName(name))}
  />
</FormField>
```

**Benefits:**
- Better user experience
- Less intrusive validation
- Validates before submission

## Tables

### Use Collection Hooks for State Management
```typescript
import { useCollection } from '@cloudscape-design/collection-hooks';
import { Table, TextFilter, Pagination } from '@cloudscape-design/components';

const { items, collectionProps, filterProps, paginationProps } = useCollection(
  allItems,
  {
    filtering: {
      empty: <EmptyState title="No items" />,
      noMatch: <EmptyState title="No matches" />,
    },
    pagination: { pageSize: 25 },
    sorting: {
      defaultState: {
        sortingColumn: columnDefinitions[0],
        isDescending: false,
      },
    },
    selection: {},
  }
);

<Table
  {...collectionProps}
  columnDefinitions={columnDefinitions}
  items={items}
  loading={loading}
  loadingText="Loading items..."
  filter={
    <TextFilter
      {...filterProps}
      filteringPlaceholder="Search items"
    />
  }
  pagination={<Pagination {...paginationProps} />}
  preferences={<CollectionPreferences />}
/>
```

**Benefits:**
- Automatic sorting/filtering/pagination
- Consistent behavior
- Less boilerplate code
- Built-in state management

### Define Column Definitions Properly
```typescript
const columnDefinitions = [
  {
    id: 'name',
    header: 'Name',
    cell: (item) => item.name,
    sortingField: 'name',
    width: 200,
    minWidth: 150,
  },
  {
    id: 'status',
    header: 'Status',
    cell: (item) => <StatusBadge status={item.status} />,
    sortingField: 'status',
    width: 120,
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: (item) => (
      <SpaceBetween direction="horizontal" size="xs">
        <Button onClick={() => handleEdit(item)}>Edit</Button>
        <Button onClick={() => handleDelete(item)}>Delete</Button>
      </SpaceBetween>
    ),
    width: 150,
  },
];
```

**Benefits:**
- Type-safe column definitions
- Consistent cell rendering
- Sortable columns
- Responsive widths

### Use Empty States
```typescript
<Table
  items={items}
  columnDefinitions={columnDefinitions}
  empty={
    <Box textAlign="center" color="inherit">
      <SpaceBetween size="m">
        <b>No items</b>
        <Button onClick={handleCreate}>Create item</Button>
      </SpaceBetween>
    </Box>
  }
/>
```

**Benefits:**
- Better user experience
- Clear call-to-action
- Consistent messaging

## Modals & Dialogs

### Use Modal for Dialogs
```typescript
import { Modal, Box, SpaceBetween, Button } from '@cloudscape-design/components';

<Modal
  visible={visible}
  onDismiss={onDismiss}
  header="Create Protection Group"
  size="large"
  footer={
    <Box float="right">
      <SpaceBetween direction="horizontal" size="xs">
        <Button variant="link" onClick={onDismiss}>
          Cancel
        </Button>
        <Button variant="primary" onClick={onSave} loading={saving}>
          Create
        </Button>
      </SpaceBetween>
    </Box>
  }
>
  <SpaceBetween direction="vertical" size="l">
    <FormField label="Name">
      <Input value={name} onChange={handleNameChange} />
    </FormField>
    <FormField label="Description">
      <Textarea value={description} onChange={handleDescriptionChange} />
    </FormField>
  </SpaceBetween>
</Modal>
```

**Benefits:**
- Consistent modal styling
- Proper focus management
- Keyboard navigation
- Accessibility features

### Use Appropriate Modal Sizes
- `small` - Simple confirmations (300px)
- `medium` - Standard forms (600px)
- `large` - Complex forms (900px)
- `max` - Full-width content (1200px)

### Always Provide Dismiss Handler
```typescript
<Modal
  visible={visible}
  onDismiss={() => {
    // Clean up state
    setName('');
    setDescription('');
    setErrors({});
    // Close modal
    setVisible(false);
  }}
>
  Content
</Modal>
```

## Notifications

### Use Flashbar for Notifications
```typescript
import { Flashbar } from '@cloudscape-design/components';

const [notifications, setNotifications] = useState([]);

const addNotification = (type, message) => {
  setNotifications([
    ...notifications,
    {
      type,
      content: message,
      dismissible: true,
      onDismiss: () => removeNotification(id),
      id: Date.now().toString(),
    },
  ]);
};

<Flashbar items={notifications} />
```

**Benefits:**
- Stack of notifications
- Auto-dismiss support
- Type-based styling
- Consistent positioning

### Use Appropriate Notification Types
- `success` - Operation completed successfully
- `error` - Operation failed
- `warning` - Potential issue
- `info` - Informational message

### Auto-Dismiss Success Notifications
```typescript
const addSuccessNotification = (message) => {
  const id = Date.now().toString();
  setNotifications([
    ...notifications,
    {
      type: 'success',
      content: message,
      dismissible: true,
      onDismiss: () => removeNotification(id),
      id,
    },
  ]);
  
  // Auto-dismiss after 5 seconds
  setTimeout(() => removeNotification(id), 5000);
};
```

## Loading States

### Use Spinner for Loading
```typescript
import { Spinner, Box } from '@cloudscape-design/components';

{loading ? (
  <Box textAlign="center" padding="xxl">
    <Spinner size="large" />
  </Box>
) : (
  <Content />
)}
```

### Use Loading Prop on Components
```typescript
<Table
  items={items}
  columnDefinitions={columnDefinitions}
  loading={loading}
  loadingText="Loading items..."
/>

<Button
  onClick={handleSave}
  loading={saving}
>
  Save
</Button>
```

**Benefits:**
- Built-in loading states
- Consistent behavior
- Accessibility support

## Error Handling

### Display Errors Inline
```typescript
<FormField
  label="Name"
  errorText={errors.name}
>
  <Input value={name} onChange={handleNameChange} />
</FormField>
```

### Use Alert for Page-Level Errors
```typescript
import { Alert } from '@cloudscape-design/components';

{error && (
  <Alert
    type="error"
    dismissible
    onDismiss={() => setError(null)}
  >
    {error}
  </Alert>
)}
```

### Provide Actionable Error Messages
```typescript
// ❌ Bad
setError('Error occurred');

// ✅ Good
setError('Failed to save protection group. Please check your inputs and try again.');
```

## Accessibility

### Use Semantic HTML
```typescript
// ✅ Good - semantic structure
<Header variant="h1">Page Title</Header>
<Container header={<Header variant="h2">Section</Header>}>
  Content
</Container>

// ❌ Bad - div soup
<div className="title">Page Title</div>
<div className="section">
  <div className="section-title">Section</div>
  Content
</div>
```

### Provide ARIA Labels
```typescript
<Button
  iconName="edit"
  ariaLabel="Edit protection group"
  onClick={handleEdit}
/>

<Input
  value={search}
  onChange={handleSearch}
  ariaLabel="Search protection groups"
  placeholder="Search..."
/>
```

### Test Keyboard Navigation
- Tab through all interactive elements
- Enter/Space activates buttons
- Escape closes modals
- Arrow keys navigate lists

## Performance

### Memoize Column Definitions
```typescript
const columnDefinitions = useMemo(() => [
  {
    id: 'name',
    header: 'Name',
    cell: (item) => item.name,
  },
  // ... more columns
], []);
```

### Virtualize Large Lists
```typescript
import { Table } from '@cloudscape-design/components';

<Table
  items={items}
  columnDefinitions={columnDefinitions}
  variant="embedded"
  stickyHeader
  // CloudScape handles virtualization automatically for large datasets
/>
```

### Lazy Load Data
```typescript
const [items, setItems] = useState([]);
const [loading, setLoading] = useState(false);

const loadMore = async () => {
  setLoading(true);
  const newItems = await fetchItems(page);
  setItems([...items, ...newItems]);
  setLoading(false);
};
```

## Responsive Design

### Use Responsive Containers
```typescript
import { ColumnLayout } from '@cloudscape-design/components';

<ColumnLayout columns={3} variant="text-grid">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</ColumnLayout>
```

**Behavior:**
- 3 columns on desktop
- 2 columns on tablet
- 1 column on mobile

### Test Multiple Breakpoints
- Desktop: 1280px+
- Tablet: 768px - 1279px
- Mobile: < 768px

## Code Organization

### Group Related Imports
```typescript
// CloudScape components
import {
  Button,
  Modal,
  FormField,
  Input,
  SpaceBetween,
} from '@cloudscape-design/components';

// Hooks
import { useState, useEffect, useMemo } from 'react';
import { useCollection } from '@cloudscape-design/collection-hooks';

// Local components
import { StatusBadge } from '../components/StatusBadge';
import { DateTimeDisplay } from '../components/DateTimeDisplay';

// Services
import apiClient from '../services/api';

// Types
import type { ProtectionGroup } from '../types';
```

### Extract Complex Logic to Hooks
```typescript
// hooks/useProtectionGroups.ts
export const useProtectionGroups = () => {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchGroups = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listProtectionGroups();
      setGroups(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, []);

  return { groups, loading, error, refetch: fetchGroups };
};
```

### Create Reusable Components
```typescript
// components/cloudscape/TableWrapper.tsx
export const TableWrapper = ({ items, columnDefinitions, ...props }) => {
  const { items: filteredItems, collectionProps, filterProps, paginationProps } = 
    useCollection(items, {
      filtering: {},
      pagination: { pageSize: 25 },
      sorting: {},
    });

  return (
    <Table
      {...collectionProps}
      {...props}
      items={filteredItems}
      columnDefinitions={columnDefinitions}
      filter={<TextFilter {...filterProps} />}
      pagination={<Pagination {...paginationProps} />}
    />
  );
};
```

## Testing

### Test Component Rendering
```typescript
import { render, screen } from '@testing-library/react';
import { ProtectionGroupDialog } from './ProtectionGroupDialog';

test('renders dialog with title', () => {
  render(<ProtectionGroupDialog visible={true} />);
  expect(screen.getByText('Create Protection Group')).toBeInTheDocument();
});
```

### Test User Interactions
```typescript
import { render, screen, fireEvent } from '@testing-library/react';

test('calls onSave when save button clicked', () => {
  const onSave = jest.fn();
  render(<ProtectionGroupDialog visible={true} onSave={onSave} />);
  
  fireEvent.click(screen.getByText('Save'));
  expect(onSave).toHaveBeenCalled();
});
```

### Test Accessibility
```typescript
import { render } from '@testing-library/react';
import { axe } from 'jest-axe';

test('has no accessibility violations', async () => {
  const { container } = render(<ProtectionGroupDialog visible={true} />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

## Common Mistakes to Avoid

### ❌ Don't: Forget event.detail
```typescript
// Wrong
<Input onChange={(e) => setValue(e.target.value)} />

// Correct
<Input onChange={({ detail }) => setValue(detail.value)} />
```

### ❌ Don't: Use inline styles
```typescript
// Wrong
<Box style={{ marginTop: '20px' }}>Content</Box>

// Correct
<SpaceBetween direction="vertical" size="l">
  <Box>Content</Box>
</SpaceBetween>
```

### ❌ Don't: Skip FormField wrapper
```typescript
// Wrong
<Input label="Name" value={name} />

// Correct
<FormField label="Name">
  <Input value={name} />
</FormField>
```

### ❌ Don't: Hardcode colors
```typescript
// Wrong
<Box color="#FF0000">Error</Box>

// Correct
<Alert type="error">Error</Alert>
```

## Resources

- CloudScape Components: https://cloudscape.design/components/
- CloudScape Patterns: https://cloudscape.design/patterns/
- Design Tokens: https://cloudscape.design/foundation/visual-foundation/design-tokens/
- Collection Hooks: https://cloudscape.design/get-started/dev-guides/collection-hooks/
- Accessibility: https://cloudscape.design/foundation/core-principles/accessibility/
