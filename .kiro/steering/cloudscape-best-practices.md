# CloudScape Design System Guide

## Overview

AWS CloudScape is the open-source design system used across AWS Console. This guide covers best practices for building React applications with CloudScape.

## Why CloudScape?

- **AWS Console Consistency**: Native AWS look and feel
- **Accessibility Built-in**: WCAG 2.1 AA compliant
- **Responsive Design**: Works across desktop, tablet, mobile
- **Collection Hooks**: Powerful table state management
- **TypeScript Support**: Full type definitions

## Installation

```bash
npm install @cloudscape-design/components \
  @cloudscape-design/collection-hooks \
  @cloudscape-design/global-styles \
  @cloudscape-design/design-tokens
```

## Application Setup

### Main Entry Point
```typescript
// main.tsx
import '@cloudscape-design/global-styles/index.css';
import { createRoot } from 'react-dom/client';
import App from './App';

createRoot(document.getElementById('root')!).render(<App />);
```

### App Layout
```typescript
// App.tsx
import { AppLayout, SideNavigation, BreadcrumbGroup, Flashbar } from '@cloudscape-design/components';

export const App: React.FC = () => {
  const [notifications, setNotifications] = useState([]);

  return (
    <AppLayout
      navigation={<Navigation />}
      content={<Routes />}
      breadcrumbs={<Breadcrumbs />}
      notifications={<Flashbar items={notifications} />}
      toolsHide={true}
    />
  );
};
```

## Layout Components

### AppLayout
Main application shell with navigation, content, and tools panels.

```typescript
<AppLayout
  navigation={<SideNavigation />}      // Left sidebar
  content={<YourContent />}            // Main content area
  breadcrumbs={<BreadcrumbGroup />}    // Breadcrumb navigation
  notifications={<Flashbar />}         // Notification area
  tools={<HelpPanel />}                // Right sidebar (optional)
  toolsHide={true}                     // Hide tools panel
  navigationWidth={280}                // Navigation width
/>
```

### ContentLayout
Page content wrapper with header.

```typescript
<ContentLayout
  header={
    <Header
      variant="h1"
      description="Page description"
      actions={<Button variant="primary">Create</Button>}
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

### SpaceBetween
Consistent spacing between elements.

```typescript
// Vertical layout
<SpaceBetween direction="vertical" size="l">
  <Component1 />
  <Component2 />
</SpaceBetween>

// Horizontal layout (for buttons)
<SpaceBetween direction="horizontal" size="xs">
  <Button>Cancel</Button>
  <Button variant="primary">Save</Button>
</SpaceBetween>
```

**Sizes**: `xxxs`, `xxs`, `xs`, `s`, `m`, `l`, `xl`, `xxl`

### Container
Content container with optional header.

```typescript
<Container
  header={<Header variant="h2">Section Title</Header>}
  footer="Footer content"
>
  Container content
</Container>
```

### ColumnLayout
Responsive column layout.

```typescript
<ColumnLayout columns={3} variant="text-grid">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</ColumnLayout>
```

## Form Components

### FormField + Input Pattern
Always wrap inputs in FormField for labels and error handling.

```typescript
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

### Select
```typescript
<FormField label="Region">
  <Select
    selectedOption={selectedRegion}
    onChange={({ detail }) => setSelectedRegion(detail.selectedOption)}
    options={[
      { value: 'us-east-1', label: 'US East (N. Virginia)' },
      { value: 'us-west-2', label: 'US West (Oregon)' },
    ]}
    placeholder="Select a region"
  />
</FormField>
```

### Multiselect
```typescript
<FormField label="Servers">
  <Multiselect
    selectedOptions={selectedServers}
    onChange={({ detail }) => setSelectedServers(detail.selectedOptions)}
    options={servers.map(s => ({ value: s.id, label: s.hostname }))}
    placeholder="Select servers"
    filteringType="auto"
  />
</FormField>
```

### Form Container
```typescript
<Form
  actions={
    <SpaceBetween direction="horizontal" size="xs">
      <Button onClick={onCancel}>Cancel</Button>
      <Button variant="primary" onClick={onSubmit} loading={saving}>
        Submit
      </Button>
    </SpaceBetween>
  }
>
  <SpaceBetween direction="vertical" size="l">
    <FormField label="Name">
      <Input value={name} onChange={({ detail }) => setName(detail.value)} />
    </FormField>
    <FormField label="Description">
      <Textarea value={description} onChange={({ detail }) => setDescription(detail.value)} />
    </FormField>
  </SpaceBetween>
</Form>
```

## Table Components

### Table with Collection Hooks
Use `@cloudscape-design/collection-hooks` for table state management.

```typescript
import { useCollection } from '@cloudscape-design/collection-hooks';
import { Table, TextFilter, Pagination, Header } from '@cloudscape-design/components';

const MyTable: React.FC<{ items: Item[] }> = ({ items }) => {
  const { items: filteredItems, collectionProps, filterProps, paginationProps } = useCollection(
    items,
    {
      filtering: {
        empty: <EmptyState title="No items" />,
        noMatch: <EmptyState title="No matches" />,
      },
      pagination: { pageSize: 25 },
      sorting: {
        defaultState: {
          sortingColumn: { sortingField: 'name' },
          isDescending: false,
        },
      },
      selection: {},
    }
  );

  const columnDefinitions = [
    {
      id: 'name',
      header: 'Name',
      cell: (item) => item.name,
      sortingField: 'name',
      width: 200,
    },
    {
      id: 'status',
      header: 'Status',
      cell: (item) => <StatusIndicator type={item.status}>{item.status}</StatusIndicator>,
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

  return (
    <Table
      {...collectionProps}
      columnDefinitions={columnDefinitions}
      items={filteredItems}
      loading={loading}
      loadingText="Loading items..."
      header={
        <Header
          counter={`(${items.length})`}
          actions={<Button variant="primary">Create</Button>}
        >
          Items
        </Header>
      }
      filter={
        <TextFilter
          {...filterProps}
          filteringPlaceholder="Search items"
          countText={`${filteredItems.length} matches`}
        />
      }
      pagination={<Pagination {...paginationProps} />}
      empty={
        <Box textAlign="center" color="inherit">
          <SpaceBetween size="m">
            <b>No items</b>
            <Button onClick={handleCreate}>Create item</Button>
          </SpaceBetween>
        </Box>
      }
    />
  );
};
```

### Column Definitions
```typescript
const columnDefinitions = [
  {
    id: 'name',           // Unique identifier
    header: 'Name',       // Column header text
    cell: (item) => item.name,  // Cell renderer
    sortingField: 'name', // Field to sort by
    width: 200,           // Column width
    minWidth: 150,        // Minimum width
  },
];
```

## Modal Components

### Modal Dialog
```typescript
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
    <FormField label="Name" errorText={errors.name}>
      <Input value={name} onChange={({ detail }) => setName(detail.value)} />
    </FormField>
    <FormField label="Region">
      <Select
        selectedOption={region}
        onChange={({ detail }) => setRegion(detail.selectedOption)}
        options={regionOptions}
      />
    </FormField>
  </SpaceBetween>
</Modal>
```

**Modal Sizes**:
- `small` - 300px (simple confirmations)
- `medium` - 600px (standard forms)
- `large` - 900px (complex forms)
- `max` - 1200px (full-width content)

### Confirmation Dialog Pattern
```typescript
const ConfirmDialog: React.FC<{
  visible: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}> = ({ visible, title, message, onConfirm, onCancel, loading }) => (
  <Modal
    visible={visible}
    onDismiss={onCancel}
    header={title}
    footer={
      <Box float="right">
        <SpaceBetween direction="horizontal" size="xs">
          <Button onClick={onCancel}>Cancel</Button>
          <Button variant="primary" onClick={onConfirm} loading={loading}>
            Confirm
          </Button>
        </SpaceBetween>
      </Box>
    }
  >
    {message}
  </Modal>
);
```

## Notification Components

### Flashbar
```typescript
const [notifications, setNotifications] = useState<FlashbarProps.MessageDefinition[]>([]);

const addNotification = (type: 'success' | 'error' | 'warning' | 'info', content: string) => {
  const id = Date.now().toString();
  setNotifications(prev => [
    ...prev,
    {
      type,
      content,
      dismissible: true,
      onDismiss: () => removeNotification(id),
      id,
    },
  ]);

  // Auto-dismiss success notifications
  if (type === 'success') {
    setTimeout(() => removeNotification(id), 5000);
  }
};

const removeNotification = (id: string) => {
  setNotifications(prev => prev.filter(n => n.id !== id));
};

// Usage
<Flashbar items={notifications} />
```

### Alert
```typescript
{error && (
  <Alert
    type="error"
    dismissible
    onDismiss={() => setError(null)}
    header="Error"
  >
    {error}
  </Alert>
)}
```

## Status Components

### StatusIndicator
```typescript
<StatusIndicator type="success">Completed</StatusIndicator>
<StatusIndicator type="error">Failed</StatusIndicator>
<StatusIndicator type="warning">Warning</StatusIndicator>
<StatusIndicator type="info">Info</StatusIndicator>
<StatusIndicator type="pending">Pending</StatusIndicator>
<StatusIndicator type="in-progress">In Progress</StatusIndicator>
<StatusIndicator type="loading">Loading</StatusIndicator>
```

### Badge
```typescript
<Badge color="green">Active</Badge>
<Badge color="red">Inactive</Badge>
<Badge color="blue">New</Badge>
<Badge color="grey">Unknown</Badge>
```

### ProgressBar
```typescript
<ProgressBar
  value={75}
  label="Progress"
  description="75% complete"
  status="in-progress"
/>
```

## Navigation Components

### SideNavigation
```typescript
<SideNavigation
  activeHref={location.pathname}
  items={[
    { type: 'link', text: 'Dashboard', href: '/' },
    { type: 'link', text: 'Protection Groups', href: '/protection-groups' },
    { type: 'link', text: 'Recovery Plans', href: '/recovery-plans' },
    { type: 'link', text: 'Executions', href: '/executions' },
    { type: 'divider' },
    { type: 'link', text: 'Settings', href: '/settings' },
  ]}
  onFollow={(event) => {
    event.preventDefault();
    navigate(event.detail.href);
  }}
/>
```

### BreadcrumbGroup
```typescript
<BreadcrumbGroup
  items={[
    { text: 'Home', href: '/' },
    { text: 'Protection Groups', href: '/protection-groups' },
    { text: 'Edit', href: '#' },
  ]}
  onFollow={(event) => {
    event.preventDefault();
    navigate(event.detail.href);
  }}
/>
```

### Tabs
```typescript
<Tabs
  activeTabId={activeTab}
  onChange={({ detail }) => setActiveTab(detail.activeTabId)}
  tabs={[
    { id: 'details', label: 'Details', content: <DetailsTab /> },
    { id: 'servers', label: 'Servers', content: <ServersTab /> },
    { id: 'history', label: 'History', content: <HistoryTab /> },
  ]}
/>
```

## Event Handling

CloudScape components use `detail` property in events:

```typescript
// Input
<Input onChange={({ detail }) => setValue(detail.value)} />

// Select
<Select onChange={({ detail }) => setSelected(detail.selectedOption)} />

// Checkbox
<Checkbox onChange={({ detail }) => setChecked(detail.checked)} />

// Table selection
<Table onSelectionChange={({ detail }) => setSelected(detail.selectedItems)} />

// Link/Navigation
<Link onFollow={(event) => {
  event.preventDefault();
  navigate(event.detail.href);
}} />
```

## Common Patterns

### Loading State
```typescript
{loading ? (
  <Box textAlign="center" padding="xxl">
    <Spinner size="large" />
  </Box>
) : (
  <Content />
)}
```

### Empty State
```typescript
<Box textAlign="center" color="inherit">
  <SpaceBetween size="m">
    <b>No items found</b>
    <p>Create your first item to get started.</p>
    <Button variant="primary" onClick={handleCreate}>
      Create item
    </Button>
  </SpaceBetween>
</Box>
```

### Error State
```typescript
{error && (
  <Alert type="error" dismissible onDismiss={() => setError(null)}>
    {error}
  </Alert>
)}
```

### Form Validation
```typescript
const [errors, setErrors] = useState<Record<string, string>>({});

const validate = () => {
  const newErrors: Record<string, string> = {};
  
  if (!name.trim()) {
    newErrors.name = 'Name is required';
  } else if (name.length < 3) {
    newErrors.name = 'Name must be at least 3 characters';
  }
  
  if (!region) {
    newErrors.region = 'Region is required';
  }
  
  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};

const handleSubmit = () => {
  if (validate()) {
    onSave({ name, region });
  }
};
```

## Accessibility

### ARIA Labels
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

### Keyboard Navigation
- Tab through all interactive elements
- Enter/Space activates buttons
- Escape closes modals
- Arrow keys navigate lists and menus

## Resources

- [CloudScape Components](https://cloudscape.design/components/)
- [CloudScape Patterns](https://cloudscape.design/patterns/)
- [Design Tokens](https://cloudscape.design/foundation/visual-foundation/design-tokens/)
- [Collection Hooks](https://cloudscape.design/get-started/dev-guides/collection-hooks/)
- [Accessibility](https://cloudscape.design/foundation/core-principles/accessibility/)
